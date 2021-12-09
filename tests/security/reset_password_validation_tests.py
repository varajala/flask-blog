import microtest
import flask
import blog.security as security
import blog.security.auth as auth

from blog.common import Session, Timestamp
from blog.security import generate_password_hash


reset_token = b'\x01\x00'
username = 'test'
email = 'test@mail.com'
password = '123'
password_hash = generate_password_hash(password)

anon_session = Session(
    session_id = b'\x00\x01',
    csrf_token = b'\x00\x0a',
    expires = Timestamp(1),
    user_id = 0
    )

auth_session = Session(
    session_id = b'\x00\x02',
    csrf_token = b'\x00\x0b',
    expires = str(Timestamp(1)),
    user_id = 1
    )
    

@microtest.reset
def reset(app, db):
    with app.app_context():
        db.reset()
        db.users.insert(
            id = 1,
            username = username,
            email = email,
            password = password_hash,
            is_verified = 1,
            )
        db.otps.insert(
            user_id = 1,
            value = reset_token,
            expires = str(Timestamp(1)),
            type = auth.OTP.PASSWORD_RESET,
            )


@microtest.cleanup
def cleanup(db, app):    
    db.reset()


def setup_request_args(db):
    db.sessions.insert(
        session_id = auth_session.id,
        user_id = 1,
        expires = str(auth_session.expires),
        csrf_token = auth_session.csrf_token
        )
    flask.g.user = db.users.get(id = 1)


@microtest.test
def test_valid_password_reset_anon(app, db):
    with app.app_context():
        form =  {
            'username': username,
            'email': email,
            'csrf_token': anon_session.csrf_token.hex(),
            'otp': reset_token.hex(),
            'new-password1': '12345678',
            'new-password2': '12345678',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is None
        assert db.otps.get(user_id = 1, type = auth.OTP.PASSWORD_RESET) is None


@microtest.test
def test_password_reset_anon_invalid_username(app, db):
    with app.app_context():
        form =  {
            'username': 'some_user',
            'email': email,
            'csrf_token': anon_session.csrf_token.hex(),
            'otp': reset_token.hex(),
            'new-password1': '12345678',
            'new-password2': '12345678',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is not None
        assert db.otps.get(user_id = 1, type = auth.OTP.PASSWORD_RESET) is not None


@microtest.test
def test_password_reset_anon_invalid_email(app, db):
    with app.app_context():
        form =  {
            'username': username,
            'email': 'some_user@mail.com',
            'csrf_token': anon_session.csrf_token.hex(),
            'otp': reset_token.hex(),
            'new-password1': '12345678',
            'new-password2': '12345678',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is not None
        assert db.otps.get(user_id = 1, type = auth.OTP.PASSWORD_RESET) is not None


@microtest.test
def test_password_reset_anon_invalid_otp(app, db):
    with app.app_context():
        form =  {
            'username': username,
            'email': email,
            'csrf_token': anon_session.csrf_token.hex(),
            'otp': 'asd',
            'new-password1': '12345678',
            'new-password2': '12345678',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is not None
        assert db.otps.get(user_id = 1, type = auth.OTP.PASSWORD_RESET) is not None


@microtest.test
def test_password_reset_anon_invalid_csrf_token(app, db):
    with app.app_context():
        form =  {
            'username': username,
            'email': email,
            'csrf_token': 'asd',
            'otp': reset_token.hex(),
            'new-password1': '12345678',
            'new-password2': '12345678',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is not None
        assert db.otps.get(user_id = 1, type = auth.OTP.PASSWORD_RESET) is not None


@microtest.test
def test_password_reset_anon_user_locked(app, db):
    with app.app_context():
        with db.users.update(id = 1) as user:
            user.is_locked = 1
        
        form =  {
            'username': username,
            'email': email,
            'csrf_token': anon_session.csrf_token.hex(),
            'otp': reset_token.hex(),
            'new-password1': '12345678',
            'new-password2': '12345678',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is not None
        assert db.otps.get(user_id = 1, type = auth.OTP.PASSWORD_RESET) is not None


@microtest.test
def test_password_reset_anon_user_not_verified(app, db):
    with app.app_context():
        with db.users.update(id = 1) as user:
            user.is_verified = 0
        
        form =  {
            'username': username,
            'email': email,
            'csrf_token': anon_session.csrf_token.hex(),
            'otp': reset_token.hex(),
            'new-password1': '12345678',
            'new-password2': '12345678',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is not None
        assert db.otps.get(user_id = 1, type = auth.OTP.PASSWORD_RESET) is not None


@microtest.test
def test_password_reset_anon_user_no_otp(app, db):
    with app.app_context():
        db.otps.delete()
        form =  {
            'username': username,
            'email': email,
            'csrf_token': anon_session.csrf_token.hex(),
            'otp': reset_token.hex(),
            'new-password1': '12345678',
            'new-password2': '12345678',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is not None


@microtest.test
def test_password_reset_anon_invalid_new_password(app, db):
    with app.app_context():
        with db.otps.update(user_id = 1, type = auth.OTP.PASSWORD_RESET) as otp:
            otp.expires = str(Timestamp(-1))
        
        form =  {
            'username': username,
            'email': email,
            'csrf_token': anon_session.csrf_token.hex(),
            'otp': reset_token.hex(),
            'new-password1': 'asd',
            'new-password2': 'asd',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is not None


@microtest.test
def test_password_reset_anon_passwords_dont_match(app, db):
    with app.app_context():
        with db.otps.update(user_id = 1, type = auth.OTP.PASSWORD_RESET) as otp:
            otp.expires = str(Timestamp(-1))
        
        form =  {
            'username': username,
            'email': email,
            'csrf_token': anon_session.csrf_token.hex(),
            'otp': reset_token.hex(),
            'new-password1': 'asd',
            'new-password2': '123',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is not None


@microtest.test
def test_password_reset_anon_expired_otp(app, db):
    with app.app_context():
        with db.otps.update(user_id = 1, type = auth.OTP.PASSWORD_RESET) as otp:
            otp.expires = str(Timestamp(-1))
        
        form =  {
            'username': username,
            'email': email,
            'csrf_token': anon_session.csrf_token.hex(),
            'otp': reset_token.hex(),
            'new-password1': '12345678',
            'new-password2': '12345678',
            }

        err = auth.validate_password_reset(form, anon_session)
        assert err is not None
        assert db.otps.get(user_id = 1, type = auth.OTP.PASSWORD_RESET) is None


@microtest.test
def test_valid_password_reset_auth(app, db):
    with app.app_context():
        with app.test_request_context():
            form =  {
                'password': password,
                'new-password1': '12345678',
                'new-password2': '12345678',
                'csrf_token': auth_session.csrf_token.hex(),
                }

            setup_request_args(db)
            err = auth.validate_password_reset(form, auth_session)
            assert err is None


@microtest.test
def test_password_reset_auth_wrong_password(app, db):
    with app.app_context():
        with app.test_request_context():
            form =  {
                'password': 'asd',
                'new-password1': '12345678',
                'new-password2': '12345678',
                'csrf_token': auth_session.csrf_token.hex(),
                }

            setup_request_args(db)
            err = auth.validate_password_reset(form, auth_session)
            assert err is not None


@microtest.test
def test_password_reset_auth_invalid_new_password(app, db):
    with app.app_context():
        with app.test_request_context():
            form =  {
                'password': password,
                'new-password1': '123',
                'new-password2': '123',
                'csrf_token': auth_session.csrf_token.hex(),
                }

            setup_request_args(db)
            err = auth.validate_password_reset(form, auth_session)
            assert err is not None


@microtest.test
def test_password_reset_auth_invalid_new_password_confirm(app, db):
    with app.app_context():
        with app.test_request_context():
            form =  {
                'password': password,
                'new-password1': '12345678',
                'new-password2': '123',
                'csrf_token': auth_session.csrf_token.hex(),
                }

            setup_request_args(db)
            err = auth.validate_password_reset(form, auth_session)
            assert err is not None


@microtest.test
def test_password_reset_auth_user_not_verified(app, db):
    with app.app_context():
        with app.test_request_context():
            with db.users.update(id = 1) as user:
                user.is_verified = 0
            
            form =  {
                'password': password,
                'new-password1': '12345678',
                'new-password2': '12345678',
                'csrf_token': auth_session.csrf_token.hex(),
                }

            setup_request_args(db)
            err = auth.validate_password_reset(form, auth_session)
            assert err is not None


@microtest.test
def test_password_reset_auth_invalid_csrf_token(app, db):
    with app.app_context():
        with app.test_request_context():
            form =  {
                'password': password,
                'new-password1': '12345678',
                'new-password2': '12345678',
                'csrf_token': 'asd',
                }

            setup_request_args(db)
            err = auth.validate_password_reset(form, auth_session)
            assert err is not None
