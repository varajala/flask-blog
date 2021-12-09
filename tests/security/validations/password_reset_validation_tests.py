import microtest
import flask
import blog.security as security
import blog.security.auth as auth

from blog.common import Session, Timestamp
from blog.security import generate_password_hash


reset_token = b'\x00\x03'
username = 'test'
email = 'test@mail.com'

session = Session(
    session_id = b'\x00\x01',
    csrf_token = b'\x00\x02',
    expires = Timestamp(1),
    user_id = 0
    )
    

@microtest.reset
def reset(db):
    db.reset()

@microtest.cleanup
def cleanup(db, app):
    db.reset()


@microtest.test
def test_valid_reset_request(app, db):
    with app.app_context():
        db.users.insert(username=username, email=email, password='123', is_verified = 1)
        form =  {
            'username': username,
            'email': email,
            'csrf_token': session.csrf_token.hex()
            }

        is_valid =  auth.is_valid_password_reset_request(form, session)
        assert is_valid


@microtest.test
def test_reset_request_invalid_username(app, db):
    with app.app_context():
        db.users.insert(username=username, email=email, password='123', is_verified = 1)
        form =  {
            'username': 'some_user',
            'email': email,
            'csrf_token': session.csrf_token.hex()
            }

        is_valid =  auth.is_valid_password_reset_request(form, session)
        assert not is_valid


@microtest.test
def test_reset_request_invalid_email(app, db):
    with app.app_context():
        db.users.insert(username=username, email=email, password='123', is_verified = 1)
        form =  {
            'username': username,
            'email': 'someemail@gmail.com',
            'csrf_token': session.csrf_token.hex()
            }

        is_valid =  auth.is_valid_password_reset_request(form, session)
        assert not is_valid


@microtest.test
def test_reset_request_invalid_csrf_token(app, db):
    with app.app_context():
        db.users.insert(username=username, email=email, password='123', is_verified = 1)
        form =  {
            'username': username,
            'email': email,
            'csrf_token': 'asd'
            }

        is_valid =  auth.is_valid_password_reset_request(form, session)
        assert not is_valid


@microtest.test
def test_reset_request_logged_in(app, db):
    with app.app_context():
        db.users.insert(username=username, email=email, password='123', is_verified = 1)
        form =  {
            'username': username,
            'email': email,
            'csrf_token': session.csrf_token.hex()
            }

        session.user_id = 1
        is_valid =  auth.is_valid_password_reset_request(form, session)
        session.user_id = 0
        assert not is_valid


@microtest.test
def test_reset_request_not_verified(app, db):
    with app.app_context():
        db.users.insert(username=username, email=email, password='123')
        form =  {
            'username': username,
            'email': email,
            'csrf_token': session.csrf_token.hex()
            }

        is_valid =  auth.is_valid_password_reset_request(form, session)
        assert not is_valid


@microtest.test
def test_reset_request_empty_form(app, db):
    with app.app_context():
        db.users.insert(username=username, email=email, password='123', is_verified = 1)
        form =  {
            'username': '',
            'email': '',
            'csrf_token': ''
            }

        is_valid =  auth.is_valid_password_reset_request(form, session)
        assert not is_valid


@microtest.test
def test_reset_request_missing_values(app, db):
    with app.app_context():
        db.users.insert(username=username, email=email, password='123', is_verified = 1)
        form =  {}

        is_valid =  auth.is_valid_password_reset_request(form, session)
        assert not is_valid
