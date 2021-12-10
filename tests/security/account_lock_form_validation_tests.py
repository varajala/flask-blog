import microtest
import flask
import blog.security as security
import blog.security.auth as auth

from blog.common import Session, Timestamp
from blog.security import generate_password_hash


unlock_token = b'\x00\x03'
user_id = 1
username = 'test'

session = Session(
    session_id = b'\x00\x01',
    csrf_token = b'\x00\x02',
    expires = Timestamp(1),
    user_id = user_id
    )


@microtest.reset
def reset(db):
    db.reset()
    db.get_table('users').insert(
        id = user_id,
        username = username,
        email = 'test@mail.com',
        password = '123',
        is_locked = 1
        )

@microtest.cleanup
def cleanup(db, app):
    db.reset()


@microtest.test
def test_valid_unlock_token(app, db):
    with app.app_context():
        otps_table = db.get_table('otps')
        users_table = db.get_table('users')
        
        otps_table.insert(value=unlock_token, expires=str(Timestamp(1)), user_id=user_id, type=auth.OTP.ACCOUNT_LOCK)
        form =  {
            'unlock_token': unlock_token.hex(),
            'csrf_token': session.csrf_token.hex(),
            'username': username,
            }

        err = auth.unlock_user_account(form, session)
        assert err is None
        assert otps_table.get(user_id = user_id, type = auth.OTP.ACCOUNT_LOCK) is None
        
        user = users_table.get(id = user_id)
        assert not user.is_locked


@microtest.test
def test_expired_unlock_token(app, db):
    with app.app_context():
        otps_table = db.get_table('otps')
        users_table = db.get_table('users')

        otps_table.insert(value=unlock_token, expires=str(Timestamp(-1)), user_id=user_id, type=auth.OTP.ACCOUNT_LOCK)
        form =  {
            'unlock_token': unlock_token.hex(),
            'csrf_token': session.csrf_token.hex(),
            'username': username,
            }

        err = auth.unlock_user_account(form, session)
        assert err is None
        assert otps_table.get(user_id = user_id, type = auth.OTP.ACCOUNT_LOCK) is None
        
        user = users_table.get(id = user_id)
        assert not user.is_locked


@microtest.test
def test_invalid_unlock_token(app, db):
    with app.app_context():
        otps_table = db.get_table('otps')
        users_table = db.get_table('users')

        otps_table.insert(value=unlock_token, expires=str(Timestamp(1)), user_id=user_id, type=auth.OTP.ACCOUNT_LOCK)
        form =  {
            'unlock_token': '123',
            'csrf_token': session.csrf_token.hex(),
            'username': username,
            }

        err = auth.unlock_user_account(form, session)
        assert err is not None
        assert otps_table.get(user_id = user_id, type = auth.OTP.ACCOUNT_LOCK) is not None
        
        user = users_table.get(id = user_id)
        assert user.is_locked


@microtest.test
def test_invalid_csrf_token(app, db):
    with app.app_context():
        otps_table = db.get_table('otps')
        users_table = db.get_table('users')

        otps_table.insert(value=unlock_token, expires=str(Timestamp(1)), user_id=user_id, type=auth.OTP.ACCOUNT_LOCK)
        form =  {
            'unlock_token': unlock_token.hex(),
            'csrf_token': '123',
            'username': username,
            }

        err = auth.unlock_user_account(form, session)
        assert err is not None
        assert otps_table.get(user_id = user_id, type = auth.OTP.ACCOUNT_LOCK) is not None
        
        user = users_table.get(id = user_id)
        assert user.is_locked


@microtest.test
def test_invalid_username(app, db):
    with app.app_context():
        otps_table = db.get_table('otps')
        users_table = db.get_table('users')
        
        otps_table.insert(value=unlock_token, expires=str(Timestamp(1)), user_id=user_id, type=auth.OTP.ACCOUNT_LOCK)
        form =  {
            'unlock_token': unlock_token.hex(),
            'csrf_token': session.csrf_token.hex(),
            'username': 'some_user',
            }

        err = auth.unlock_user_account(form, session)
        assert err is not None
        assert otps_table.get(user_id = user_id, type = auth.OTP.ACCOUNT_LOCK) is not None
        
        user = users_table.get(id = user_id)
        assert user.is_locked


@microtest.test
def test_missing_values(app, db):
    with app.app_context():
        otps_table = db.get_table('otps')
        users_table = db.get_table('users')
        
        otps_table.insert(value=unlock_token, expires=str(Timestamp(1)), user_id=user_id, type=auth.OTP.ACCOUNT_LOCK)
        form = {
            'unlock_token': '',
            'csrf_token': '',
            'username': '',
        }

        err = auth.unlock_user_account(form, session)
        assert err is not None
        assert otps_table.get(user_id = user_id, type = auth.OTP.ACCOUNT_LOCK) is not None
        
        user = users_table.get(id = user_id)
        assert user.is_locked


@microtest.test
def test_empty_form(app, db):
    with app.app_context():
        otps_table = db.get_table('otps')
        users_table = db.get_table('users')
        
        otps_table.insert(value=unlock_token, expires=str(Timestamp(1)), user_id=user_id, type=auth.OTP.ACCOUNT_LOCK)
        form =  {}

        err = auth.unlock_user_account(form, session)
        assert err is not None
        assert otps_table.get(user_id = user_id, type = auth.OTP.ACCOUNT_LOCK) is not None
        
        user = users_table.get(id = user_id)
        assert user.is_locked
