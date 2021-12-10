import microtest
import flask
import blog.security as security
import blog.security.auth as auth

from blog.common import Session, Timestamp
from blog.security import generate_password_hash


email_token = b'\x00\x03'
user_id = 1

session = Session(
    session_id = b'\x00\x01',
    csrf_token = b'\x00\x02',
    expires = Timestamp(1),
    user_id = user_id
    )
    

@microtest.reset
def reset(db):
    db.reset()

@microtest.cleanup
def cleanup(db, app):
    db.reset()


@microtest.test
def test_valid_email_token(app, db):
    with app.app_context():
        db.get_table('otps').insert(
            value=email_token,
            expires=str(Timestamp(1)),
            user_id=user_id,
            type=auth.OTP.EMAIL
            )
        form =  {
            'verification_token': email_token.hex(),
            'csrf_token': session.csrf_token.hex()
            }

        err = auth.validate_email_verification(form, session)
        assert err is None
        assert db.get_table('otps').get(user_id = user_id, type = auth.OTP.EMAIL) is None

    
@microtest.test
def test_invalid_token(app, db):
    with app.app_context():
        db.get_table('otps').insert(value=email_token, expires=str(Timestamp(1)), user_id=user_id, type=auth.OTP.EMAIL)
        form =  {
            'verification_token': '123',
            'csrf_token': session.csrf_token.hex()
            }

        err = auth.validate_email_verification(form, session)
        assert err is not None
        assert db.get_table('otps').get(user_id = user_id, type = auth.OTP.EMAIL) is not None


@microtest.test
def test_non_existing_csrf_token(app, db):
    with app.app_context():
        db.get_table('otps').insert(value=email_token, expires=str(Timestamp(1)), user_id=user_id, type=auth.OTP.EMAIL)
        form =  {'verification_token': email_token.hex()}

        err = auth.validate_email_verification(form, session)
        assert err is not None
        assert db.get_table('otps').get(user_id = user_id, type = auth.OTP.EMAIL) is not None


@microtest.test
def test_expired_token(app, db):
    with app.app_context():
        db.get_table('otps').insert(value=email_token, expires=str(Timestamp(-1)), user_id=user_id, type=auth.OTP.EMAIL)

        form =  {
            'verification_token': email_token.hex(),
            'csrf_token': session.csrf_token.hex()
            }

        err = auth.validate_email_verification(form, session)
        assert err is not None
        assert db.get_table('otps').get(user_id = user_id, type = auth.OTP.EMAIL) is None
