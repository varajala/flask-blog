"""
Functions related to authentication and authorization.

Author: Valtteri Rajalainen
"""

import re
import flask
import functools
import os
import hmac
import werkzeug.security
from werkzeug.security import check_password_hash

from blog.common import *
from blog.security.utils import *
import blog.notifications as notifications
import blog.security.sessions as sessions
import blog.models as models



def admin_only(view):
    """
    Check if the session is authenticated (userid > 0),
    user is verified and the user is marked as admin.
    
    Redirect to login if user is not authenticated.
    Redirect to verification if user is not verified.
    Redirect to home page if user is not admin.
    """
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        session = flask.g.session
        if session.is_anonymous:
            login_url = flask.url_for('auth.login')
            return flask.redirect(login_url)

        user = flask.g.user
        if not user.is_verified:
            verify_url = flask.url_for('auth.verify')
            return flask.redirect(verify_url)
        
        if not user.is_admin:
            index_url = flask.url_for('index')
            return flask.redirect(index_url)
        
        return view(*args, **kwargs)
    return wrapper


def authentication_required(view):
    """
    Check if the session is authenticated (userid > 0)
    and that the user is verified.
    
    Redirect to login if user is not authentiacted.
    Redirect to verification if user is not verified.
    """
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        session = flask.g.session
        if session.is_anonymous:
            login_url = flask.url_for('auth.login')
            return flask.redirect(login_url)

        user = flask.g.user
        if not user.is_verified:
            verify_url = flask.url_for('auth.verify')
            return flask.redirect(verify_url)
        
        return view(*args, **kwargs)
    return wrapper


def only_login_required(view):
    """
    Check if the session is authenticated (userid > 0).
    Redirect to login if not.
    """
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        session = flask.g.session
        if session.is_anonymous:
            login_url = flask.url_for('auth.login')
            return flask.redirect(login_url)

        return view(*args, **kwargs)
    return wrapper


def login_user(user):
    """
    End the anonymous session and create new session with the given userid.
    Set the flask.g.user to the user namespace object. Resets the login attempts.
    """
    session_id = flask.session[SESSIONID]
    try:
        sessions.end_session(bytes.fromhex(session_id))
    except ValueError:
        pass

    session = sessions.create_new_session(user.id)
    flask.session[SESSIONID] = session.id.hex()
    flask.g.user = user
    
    with models.users.update(id = user.id) as user_model:
        user_model.login_attempts = 0


def logout_user(user_session):
    """
    End the authenticated session and create new anonymous session.
    Remove the user namespace object from flask.g.
    """
    sessions.end_session(user_session.id)
    flask.g.pop('user', None)
        
    session = sessions.create_new_session()
    flask.g.session = session
    flask.session[SESSIONID] = session.id.hex()


def verify_user(userid):
    with models.users.update(id = userid) as user:
        user.is_verified = 1


def valid_form_csrf_token(form, cmp):
    csrf_token = form.get('csrf_token', '00')
    try:
        src = bytes.fromhex(csrf_token)
    except (ValueError, TypeError):
        src = b'\x00'
    return matching_tokens(src, cmp)


def validate_registration_form(form, session) -> tuple:
    """
    Validate the form user sent for registering.

    Checks/validates:
    > username is valid
    > username is not in use
    > email is valid
    > email is not in use
    > password is valid
    > passwords match

    Returns a Namespace object representing the provided credentials.
    This object contains username, email and the plain-text password
    provided in the form.

    If no errors occur returns (credentials, None)
    If form is not valid returns (None, error)

    For UX the error message in NOT GENERIC. This enables
    possible attacker to perform user enumeration on this site.
    """
    error = None
    username = form.get('username', '')
    email = form.get('email', '')
    password = form.get('password1', '')
    password_confirm = form.get('password2', '')
    
    if not valid_username(username):
        error = 'Invalid username.'
        error += ' Username must only contain lowercase letters a-z, numbers and underscores.'

    elif models.users.get(username = username) is not None:
        error = 'Username is in use.'

    elif not valid_email(email):
        error = 'Invalid email address.'
    
    elif models.users.get(email = email):
        error = 'Email is in use.'

    elif not valid_password(password):
        parts = [
            'Invalid password.',
            f'Password must be atleast {PASSWORD_MIN_LENGTH} characters long',
            'and it cannot contain any whitespace characters (spaces, tabs, etc...)'
        ]
        error = ' '.join(parts)

    elif password != password_confirm:
        error = 'The passwords don\'t match.'
    
    credentials = None if error else Namespace({'username': username, 'email': email, 'password': password})
    return credentials, error


def validate_login_form(form, session) -> tuple:
    """
    Validate the form user sent for login.

    Checks/validates:
    > csrf token is correct
    > user exists
    > password hash matches

    Returns a Namespace object representing the user and an error message in a tuple.
    If no errors occur returns (user, None)
    If form is not valid returns (None, error)
    """
    error = None
    username = form.get('username', '')
    password = form.get('password', '')
    csrf_token = form.get('csrf_token', '00')
    
    if not valid_form_csrf_token(form, session.csrf_token):
        error = 'Authentication failed'

    user = models.users.get(username = username)
    user_password_hash = '' if user is None else user.password
    if user is None:
        error = 'Authentication failed'

    if not check_password_hash(user_password_hash, password):
        error = 'Authentication failed'

    if user is not None and user.is_locked:
        error = 'Authentication failed'

    return (None, error) if error else (user, None)


def validate_email_verification(form, session) -> str:
    """
    Validate the email verification token provided in the form.

    Checks/validates:
    > csrf token is correct
    > verification token exists
    > verification token is not expired
    > verification token is correct

    returns None if all checks are OK, else a generic error message.
    """
    email_token = models.otps.get(user_id=session.user_id, type=OTP.EMAIL)
    if email_token is None:
        attrs = {'value': b'\x00\x01', 'id': 0, 'type': OTP.ACCOUNT_LOCK, 'expires': str(Timestamp())}
        email_token = Namespace(attrs)

    is_expired = Timestamp() > Timestamp.from_str(email_token.expires)

    sent_token = form.get('verification_token', '00')
    try:
        src = bytes.fromhex(sent_token)
    except ValueError:
        src = b'\x00'

    valid_token = matching_tokens(src, email_token.value) and not is_expired
    success = valid_form_csrf_token(form, session.csrf_token) and valid_token
    if success or is_expired:
        models.otps.delete(id=email_token.id)
    return None if success else 'Verification failed.'


def validate_password_reset(form, session) -> str:
    def when_anonymous(form, session):
        username = form.get('username', '')
        email = form.get('email', '')

        new_password = form.get('new-password1', '')
        new_password_confirm = form.get('new-password2', '')
        
        user = models.users.get(username = username, email = email)
        if user is None:
            attrs = {'id': 0, 'username': username, 'email': email, 'is_locked': 1, 'is_verified': 0}
            user = Namespace(attrs)
        
        reset_token = models.otps.get(user_id = user.id, type = OTP.PASSWORD_RESET)
        if reset_token is None:
            attrs = {'value': b'\x00\x01', 'id': 0, 'type': OTP.ACCOUNT_LOCK, 'expires': str(Timestamp())}
            reset_token = Namespace(attrs)

        is_expired = Timestamp() > Timestamp.from_str(reset_token.expires)

        sent_token = form.get('otp', '00')
        try:
            src = bytes.fromhex(sent_token)
        except ValueError:
            src = b'\x00'
        
        conditions = [
            matching_tokens(src, reset_token.value),
            valid_form_csrf_token(form, session.csrf_token),
            not is_expired,
            not user.is_locked,
            user.is_verified,
            valid_password(new_password),
            new_password == new_password_confirm,
        ]
        success = all(conditions)
        if success or is_expired:
            models.otps.delete(id = reset_token.id)
        return None if success else 'Failed to reset the password'

    if session.is_anonymous:
        return when_anonymous(form, session)
    
    password = form.get('password', '')
    new_password = form.get('new-password1', '')
    new_password_confirm = form.get('new-password2', '')

    user = flask.g.user

    conditions = [
        check_password_hash(user.password, password),
        valid_password(new_password),
        new_password == new_password_confirm,
        valid_form_csrf_token(form, session.csrf_token),
        user.is_verified,
    ]
    return None if all(conditions) else 'Failed to reset the password'


def unlock_user_account(form, session) -> str:
    """
    Validate the account unlock token provided in the form.

    Checks/validates:
    > csrf token is correct
    > unlock token exists
    > unlock token is not expired (user is not locked)
    > unlock token is correct

    returns None if all checks are OK, else a generic error message.
    """
    message = 'Account unlocking failed. '
    message += 'You might have wrong username, wrong token or your account is not locked anymore.'

    username = form.get('username', '')
    user = models.users.get(username = username)
    
    user_id = 0 if user is None else user.id
    unlock_token = models.otps.get(user_id = user_id, type = OTP.ACCOUNT_LOCK)
    if unlock_token is None:
        attrs = {'value': b'\x00\x01', 'id': 0, 'type': OTP.ACCOUNT_LOCK, 'expires': str(Timestamp())}
        unlock_token = Namespace(attrs)

    sent_token = form.get('unlock_token', '00')
    try:
        src = bytes.fromhex(sent_token)
    except ValueError:
        src = b'\x00'

    valid_token = matching_tokens(src, unlock_token.value)
    is_expired = Timestamp() > Timestamp.from_str(unlock_token.expires)

    conditions = [
        user is not None,
        valid_form_csrf_token(form, session.csrf_token),
        valid_token or is_expired
    ]
    if all(conditions):
        models.otps.delete(id=unlock_token.id)
        with models.users.update(username = username) as user_model:
            user_model.is_locked = 0
        return None
    
    if is_expired:
        models.otps.delete(id=unlock_token.id)
    return message


def record_login_attempt(form) -> int:
    username = form.get('username', '')
    user = models.users.get(username = username)
    maxed_out = False

    if user is None:
        return None, False

    if user.is_locked:
        lock = models.otps.get(user_id = user.id, type = OTP.ACCOUNT_LOCK)
        if Timestamp() < Timestamp.from_str(lock.expires):
            return None, False
        
        user.is_locked = 0
        user.login_attempts = 0
        models.otps.delete(id = lock.id)

    user.login_attempts += 1
    if user.login_attempts > MAX_LOGIN_ATTEMPTS:
        user.is_locked = 1
        maxed_out = True
    
    with models.users.update(username = username) as user_model:
        user_model.login_attempts = user.login_attempts
        user_model.is_locked = user.is_locked

    return user, maxed_out


def is_valid_password_reset_request(form, session):
    username = form.get('username', '')
    email = form.get('email', '')

    user = models.users.get(username = username, email = email)
    is_verified = False if user is None else user.is_verified
    account_locked = True if user is None else user.is_locked

    conditions = [
        valid_form_csrf_token(form, session.csrf_token),
        is_verified,
        not account_locked,
        session.is_anonymous,
    ]
    return all(conditions)


def generate_otp(user_id, otp_type, lifetime):
    if otp_type not in OTP_TYPES:
        raise TypeError('Invalid OTP type.')
    
    otp = os.urandom(OTP_LENGTH)
    while models.otps.get(value = otp) is not None:
        otp = os.urandom(OTP_LENGTH)

    expires = Timestamp(lifetime)
    models.otps.insert(
        value = otp,
        expires = str(expires),
        type = otp_type,
        user_id = user_id
        )
    return otp, expires


def send_verification_email(reciever: str, otp: bytes, expires: Timestamp, base_url: str):
    context = {
        'reciever':reciever,
        'token':otp.hex(),
        'expires':str(expires),
        'verify_url':base_url + flask.url_for('auth.verify')
    }
    data = flask.render_template('emails/verify_email_message.html', context=context)
    message = {
        'subject':'Your one time email verificatcion token',
        'content':(data, 'html')
    }
    host = flask.current_app.config['EMAIL_HOST']
    use_ssl = flask.current_app.config['EMAIL_USE_SSL']
    credentials_path = flask.current_app.config['EMAIL_CREDENTIALS']
    notifications.send_email(message, reciever, host, credentials_path, use_ssl)


def send_account_lock_email(reciever: str, otp: bytes, expires: Timestamp, base_url: str):
    context = {
        'reciever':reciever,
        'token':otp.hex(),
        'expires':str(expires),
        'unlock_url':base_url + flask.url_for('auth.unlock')
    }
    data = flask.render_template('emails/account_locked_message.html', context=context)
    message = {
        'subject':'Your account has been locked',
        'content':(data, 'html')
    }
    host = flask.current_app.config['EMAIL_HOST']
    use_ssl = flask.current_app.config['EMAIL_USE_SSL']
    credentials_path = flask.current_app.config['EMAIL_CREDENTIALS']
    notifications.send_email(message, reciever, host, credentials_path, use_ssl)


def send_password_reset_email(reciever: str, otp: bytes, expires: Timestamp, base_url: str):
    context = {
        'reciever':reciever,
        'token':otp.hex(),
        'expires':str(expires),
        'password_reset_url':base_url + flask.url_for('auth.reset_password')
    }
    data = flask.render_template('emails/account_locked_message.html', context=context)
    message = {
        'subject':'Your account has been locked',
        'content':(data, 'html')
    }
    host = flask.current_app.config['EMAIL_HOST']
    use_ssl = flask.current_app.config['EMAIL_USE_SSL']
    credentials_path = flask.current_app.config['EMAIL_CREDENTIALS']
    notifications.send_email(message, reciever, host, credentials_path, use_ssl)