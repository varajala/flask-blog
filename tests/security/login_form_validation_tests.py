import microtest
import flask
import blog.security as security
import blog.security.auth as auth

from blog.common import Session, Timestamp
from blog.security import generate_password_hash


username = 'user0001'
email = 'user0001@mail.com'
password = '12345678'

session = Session(
    session_id = b'\x00\x01',
    csrf_token = b'\x00\x02',
    expires = Timestamp(1),
    user_id = 1
    )


@microtest.setup
def setup(db, app):
    db.users.insert(username=username, email=email, password=security.generate_password_hash(password))


@microtest.cleanup
def cleanup(db, app):
    db.reset()


@microtest.test
def test_valid_form(app):
    with app.app_context():
        form = {
            'username': username,
            'password': password,
            'csrf_token': session.csrf_token.hex()
        }

        user, err = auth.validate_login_form(form, session)
        
        assert err is None
        assert user is not None

        assert 'id' in user
        assert 'username' in user
        assert 'email' in user


@microtest.test
def test_wrong_username(app):
    with app.app_context():
        form = {
            'username': 'test',
            'password': password,
            'csrf_token': session.csrf_token.hex()
        }

        user, err = auth.validate_login_form(form, session)
        
        assert err is not None
        assert user is None


@microtest.test
def test_wrong_password(app):
    with app.app_context():
        form = {
            'username': username,
            'password': 'asd',
            'csrf_token': session.csrf_token.hex()
        }

        user, err = auth.validate_login_form(form, session)
        
        assert err is not None
        assert user is None


@microtest.test
def test_non_existing_csrf_token(app):
    with app.app_context():
        form = {
            'username': username,
            'password': password,
        }

        user, err = auth.validate_login_form(form, session)
        
        assert err is not None
        assert user is None


@microtest.test
def test_non_existing_fields(app):
    with app.app_context():
        form = {
            'username': '',
            'password': '',
            'csrf_token': '',
        }

        user, err = auth.validate_login_form(form, session)
        
        assert err is not None
        assert user is None


@microtest.test
def test_empty_form(app):
    with app.app_context():
        form = dict()

        user, err = auth.validate_login_form(form, session)
        
        assert err is not None
        assert user is None
