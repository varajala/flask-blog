import microtest
import flask
import blog.security as security
import blog.security.auth as auth

from blog.common import Session, Timestamp


username = 'user001'
email = 'user0001@mail.com'

session = Session(
    session_id = b'\x00\x01',
    csrf_token = b'\x00\x02',
    expires = Timestamp(1),
    user_id = 1
    )


@microtest.setup
def setup(db, app):
    db.get_table('users').insert(username=username, email=email, password='')


@microtest.cleanup
def cleanup(db, app):
    db.reset()


@microtest.test
def test_valid_form(app):
    with app.app_context():
        form = {
            'username': 'user',
            'email': 'user@mail.com',
            'password1': '12345678',
            'password2': '12345678',
        }

        credentials, err = auth.validate_registration_form(form, session)
        assert err is None
        assert credentials is not None
        
        assert 'password' in credentials
        assert 'username' in credentials
        assert 'email' in credentials


@microtest.test
def test_invalid_username(app):
    with app.app_context():
        form = {
            'username': 'Test?',
            'email': 'test@mail.com',
            'password1': '12345678',
            'password2': '12345678',
        }

        credentials, err = auth.validate_registration_form(form, session)
        assert credentials is None
        assert 'Invalid username' in err


@microtest.test
def test_invalid_email(app):
    with app.app_context():
        form = {
            'username': 'test',
            'email': 'test',
            'password1': '12345678',
            'password2': '12345678',
        }

        credentials, err = auth.validate_registration_form(form, session)
        assert credentials is None
        assert 'Invalid email' in err


@microtest.test
def test_used_username(app, db):
    with app.app_context():
        db.get_table('users').insert(username = 'user', email = 'user@mail.com', password = 'hash')
        
        form = {
            'username': username,
            'email': 'test',
            'password1': '12345678',
            'password2': '12345678',
        }

        credentials, err = auth.validate_registration_form(form, session)
        assert credentials is None
        assert 'in use' in err


@microtest.test
def test_used_email(app):
    with app.app_context():
        form = {
            'username': 'test',
            'email': email,
            'password1': '12345678',
            'password2': '12345678',
        }

        credentials, err = auth.validate_registration_form(form, session)
        assert credentials is None
        assert 'in use' in err


@microtest.test
def test_invalid_password(app):
    with app.app_context():
        form = {
            'username': 'test',
            'email': 'test@mail.com',
            'password1': 'asd',
            'password2': 'asd',
        }

        credentials, err = auth.validate_registration_form(form, session)
        assert credentials is None
        assert 'Invalid password' in err


@microtest.test
def test_non_matching_passwords(app):
    with app.app_context():
        form = {
            'username': 'test',
            'email': 'test@mail.com',
            'password1': '12345678',
            'password2': '87654321',
        }

        credentials, err = auth.validate_registration_form(form, session)
        assert credentials is None
        assert 'passwords don\'t match' in err


@microtest.test
def test_empty_values(app):
    with app.app_context():
        form = {
            'username': '',
            'email': '',
            'password1': '',
            'password2': '',
        }

        credentials, err = auth.validate_registration_form(form, session)
        assert credentials is None
        assert err is not None


@microtest.test
def test_empty_form(app):
    with app.app_context():
        form = dict()

        credentials, err = auth.validate_registration_form(form, session)
        assert credentials is None
        assert err is not None
