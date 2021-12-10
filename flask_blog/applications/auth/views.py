import flask
from flask_blog.security.utils import *
from flask_blog.security.auth import *
from flask_blog.common import path_relative_to_file
import flask_blog.typing as types
import flask_blog.notifications as notifications
import flask_blog.security.sessions as sessions


if types.TYPE_CHECKING:
    import flask_blog.models
    models = types.cast(flask_blog.models.Module, flask_blog.models)
else:
    import flask_blog.models as models


__all__ = [
    'blueprint',
    'register',
    'login',
    'logout',
    'verify',
    'unlock',
]


blueprint = flask.Blueprint(
    'auth', __name__,
    url_prefix='/auth',
    template_folder=path_relative_to_file(__file__, 'templates')
    )


@blueprint.route('/register', methods=('GET', 'POST'))
def register() -> types.Response:
    request = flask.request
    session = flask.g.session
    
    if request.method == 'GET':
        if not session.is_anonymous:
            logout_url = flask.url_for('auth.logout')
            return flask.redirect(logout_url)
        return flask.render_template('register.html')

    credentials, error = validate_registration_form(request.form, session)

    if error is not None:
        flask.flash(error)
        return flask.render_template('register.html')

    if credentials is None:
        raise TypeError()

    models.users.insert(
        username = credentials.username,
        email = credentials.email,
        password = generate_password_hash(credentials.password)
        )
    
    user = models.users.get(username = credentials.username)
    otp, expires = generate_otp(user.id, OTP.EMAIL, EMAIL_VERIFICATION_TOKEN_LIFETIME)
    send_verification_email(user.email, otp, expires, request.url_root)

    login_url = flask.url_for('auth.login')
    return flask.redirect(login_url)


@blueprint.route('/login', methods=('GET', 'POST'))
def login() -> types.Response:
    request = flask.request
    session = flask.g.session
    
    if request.method == 'GET':
        if not session.is_anonymous:
            user = flask.g.user
            url = flask.url_for('auth.verify')
            if user.is_verified:
                url = flask.url_for('index')
            return flask.redirect(url)
        
        csrf_token = session.csrf_token.hex()
        return flask.render_template('login.html', csrf_token=csrf_token)
    
    user, error = validate_login_form(request.form, session)

    if error:
        user, maxed_attempts = record_login_attempt(request.form)
        if maxed_attempts:
            otp, expires = generate_otp(user.id, OTP.ACCOUNT_LOCK, ACCOUNT_LOCK_DURATION)
            send_account_lock_email(user.email, otp, expires, request.url_root)
        
        csrf_token = session.csrf_token.hex()
        flask.flash(error)
        return flask.render_template('login.html', csrf_token=csrf_token)
    
    login_user(user)
    index_url = flask.url_for('index')
    return flask.redirect(index_url)


@blueprint.route('/logout', methods=('GET', 'POST'))
def logout() -> types.Response:
    session = flask.g.session
    request = flask.request
    if request.method == 'GET':
        csrf_token = session.csrf_token.hex()
        return flask.render_template('logout.html', csrf_token=csrf_token)

    if not valid_form_csrf_token(request.form, session.csrf_token):
        csrf_token = session.csrf_token.hex()
        return flask.render_template('logout.html', csrf_token=csrf_token)

    if not session.is_anonymous:
        logout_user(session)

    login_url = flask.url_for('auth.login')
    return flask.redirect(login_url)


@blueprint.route('/verify', methods=('GET', 'POST'))
@only_login_required
def verify() -> types.Response:
    request = flask.request
    session = flask.g.session
    user = flask.g.user
    
    if request.method == 'GET':
        csrf_token = session.csrf_token.hex()
        return flask.render_template('verify_email.html', csrf_token=csrf_token)

    error = validate_email_verification(request.form, session)
    if error:
        csrf_token = session.csrf_token.hex()
        flask.flash(error)
        return flask.render_template('verify_email.html', csrf_token=csrf_token)

    verify_user(user.id)
    index_url = flask.url_for('index')
    return flask.redirect(index_url)


@blueprint.route('/unlock', methods=('GET', 'POST'))
def unlock() -> types.Response:
    request = flask.request
    session = flask.g.session
    
    if request.method == 'GET':
        csrf_token = session.csrf_token.hex()
        return flask.render_template('unlock_account.html', csrf_token=csrf_token)

    error = unlock_user_account(request.form, session)
    if error:
        csrf_token = session.csrf_token.hex()
        flask.flash(error)
        return flask.render_template('unlock_account.html', csrf_token=csrf_token)

    login_url = flask.url_for('auth.login')
    return flask.redirect(login_url)


@blueprint.route('/reset-password/request', methods=('GET', 'POST'))
def request_password_reset() -> types.Response:
    request = flask.request
    session = flask.g.session
    
    if request.method == 'POST':
        if is_valid_password_reset_request(request.form, session):
            email = request.form['email']
            username = request.form['username']
            user = models.users.get(username = username, email = email)
            otp, expires = generate_otp(user.id, OTP.PASSWORD_RESET, PASSWORD_RESET_TOKEN_LIFETIME)
            send_password_reset_email(email, otp, expires, request.url_root)
    
    csrf_token = session.csrf_token.hex()
    return flask.render_template('request_password_reset.html', csrf_token=csrf_token)


@blueprint.route('/reset-password', methods=('GET', 'POST'))
def reset_password() -> types.Response:
    request = flask.request
    session = flask.g.session
    
    if request.method == 'GET':
        csrf_token = session.csrf_token.hex()
        return flask.render_template('reset_password.html', csrf_token=csrf_token)

    err = validate_password_reset(request.form, session)
    if err:
        flask.flash(err)
        csrf_token = session.csrf_token.hex()
        return flask.render_template('reset_password.html', csrf_token=csrf_token)

    username = request.form.get('username', '')
    email = request.form.get('email', '')
    user = models.users.get(username = username, email = email) if session.is_anonymous else flask.g.user

    with models.users.update(id = user.id) as user_model:
        user_model.password = generate_password_hash(request.form['new-password1'])

    next_view = 'auth.login' if session.is_anonymous else 'index'
    return flask.redirect(flask.url_for(next_view))


@blueprint.before_app_request
def load_user_session():
    session_id = flask.session.pop(SESSIONID, None)
    session = sessions.load_user_session(session_id)
    
    flask.session[SESSIONID] = session.id.hex()
    flask.g.session = session
    
    if not session.is_anonymous:
        flask.g.user = models.users.get(id = session.user_id)
