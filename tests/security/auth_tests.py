import microtest
import flask
import blog.security as security
import blog.security.auth as auth

from blog.common import Session, Timestamp
from blog.security import generate_password_hash


username = 'test'
email = 'test@email.com'
password = '12345678'


@microtest.reset
def reset(db):
    db.reset()
    db.users.insert(username=username, email=email, password=generate_password_hash(password))


@microtest.group('slow')
@microtest.test
def test_user_login(app, db):
    with app.app_context():
        with app.test_request_context():
            user = db.users.get(username = username)
            session_id = '0123'

            flask.session = {auth.SESSIONID: session_id}
            auth.login_user(user)

            session = db.sessions.get(user_id = user.id)

            assert flask.session[auth.SESSIONID] != session_id
            assert isinstance(session.csrf_token, bytes)
            assert isinstance(session.expires, str)
            assert Timestamp.from_str(session.expires) is not None
            assert 'user' in flask.g
            assert db.sessions.get(user_id = 0) is None


@microtest.group('slow')
@microtest.test
def test_user_logout(app, db):
    with app.app_context():
        with app.test_request_context():
            user = db.users.get(username = username)

            session_id = b'\x01\x01'
            csrf_token = b'\x11\x11'

            db.sessions.insert(
                session_id = session_id,
                csrf_token = csrf_token,
                user_id = user.id,
                expires = '12:00 01.01.2030',
                )
            row = db.sessions.get(user_id = user.id)
            session = Session(
                row.session_id,
                row.csrf_token,
                row.expires,
                row.user_id
                )

            flask.session = {auth.SESSIONID: session_id.hex()}
            auth.logout_user(session)

            assert 'user' not in flask.g
            assert flask.session[auth.SESSIONID] != session_id.hex()

            assert db.sessions.get(user_id = 0) is not None
            assert db.sessions.get(user_id = user.id) is None


@microtest.test
def test_csrf_validation(app, db):
    token = b'\x01\x01'
    assert auth.valid_form_csrf_token({'csrf_token': token.hex()}, token)

    assert not auth.valid_form_csrf_token({'csrf_token': b'\x00\x00'}, token)
    assert not auth.valid_form_csrf_token({'csrf_token': 123}, token)
    assert not auth.valid_form_csrf_token({}, token)


@microtest.test
def test_creating_email_tokens(app, db):
    with app.app_context():
        userid = 1
        lifetime = 1
            
        token, expires = auth.generate_otp(userid, auth.OTP.EMAIL, lifetime)
        assert isinstance(token, bytes)
        assert isinstance(expires, Timestamp)

        otp = db.otps.get(user_id = userid)
        assert otp is not None
        assert otp.value == token
        assert otp.expires == str(expires)


@microtest.group('slow')
@microtest.test
def test_login_attempt_recording(app, db):
    with app.app_context():
        with app.test_request_context():
            form = {'username': username}
            with microtest.patch(auth, MAX_LOGIN_ATTEMPTS = 1):
                user, maxed_out = auth.record_login_attempt(form)
                assert user is not None
                assert user.login_attempts == 1
                assert not maxed_out

                user, maxed_out = auth.record_login_attempt(form)
                assert user is not None
                assert user.login_attempts == 2
                assert user.is_locked
                assert maxed_out

                assert db.users.get(username = username).is_locked
                db.otps.insert(user_id = user.id, type = auth.OTP.ACCOUNT_LOCK, value = b'\x00\x01', expires = str(Timestamp(1)))

                user, maxed_out = auth.record_login_attempt(form)
                assert user is None
                assert not maxed_out
                
                user, maxed_out = auth.record_login_attempt({'username': ''})
                assert user is None
                assert not maxed_out
                