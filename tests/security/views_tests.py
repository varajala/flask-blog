import microtest
import flask
import tempfile
from threading import Lock

import flask_tutorial.security.sessions as sessions
import flask_tutorial.notifications as notifications
import flask_tutorial.security.auth as auth
from flask_tutorial.security import generate_password_hash
from flask_tutorial.common import Timestamp


mutex = Lock()
default_email_host = None


@microtest.setup
def setup(app):
    global default_email_host
    file = tempfile.TemporaryFile(mode='w+')
    default_email_host = app.config['EMAIL_HOST']
    app.config['EMAIL_HOST'] = (None, file)
    notifications.mutex = mutex


@microtest.reset
def reset(db):
    db.reset()


@microtest.cleanup
def cleanup(app):
    _, file = app.config['EMAIL_HOST']
    file.close()
    app.config['EMAIL_HOST'] = default_email_host
    notifications.mutex = None


@microtest.group('slow')
@microtest.test
def test_registering(app, db):
    client = TestClient(app)

    password = 'strongpassword'
    username = 'register_test'
    email = 'test@mail.com'
    
    db.users.insert(
        username=username,
        email=email,
        password=generate_password_hash(password)
        )
    
    response = client.register_as('some_user', 'some@mail.com', password)
    assert '/auth/login' in response.headers['Location']

    row = db.users.get(username='some_user')
    assert row is not None
    assert not bool(row.is_verified)
    user_email = row.email

    assert db.sessions.get(user_id = row.id) is None

    otp = db.otps.get(user_id = row.id)
    assert otp is not None
    token = otp.value.hex()

    _, file = app.config['EMAIL_HOST']
    file.seek(0)
    email = file.read()

    assert token in email
    assert f'To: {user_email}' in email


@microtest.group('slow')
@microtest.test
def test_authentication(app, db):
    client = TestClient(app)

    password = 'strongpassword'
    username = 'login_test'
    email = 'test@mail.com'
    
    db.users.insert(
        id = 1,
        username=username,
        email=email,
        password=generate_password_hash(password),
        is_verified = 1
        )
    
    response = client.login_as(username, password)
    assert 'http://localhost/' == response.headers['Location']
    assert db.sessions.get(user_id = 1) is not None

    with client:
        response = client.get('/')
        assert response.status_code == 200

        response = client.get('/auth/login')
        assert response.status_code == 302
        assert 'http://localhost/' == response.headers['Location']

        response = client.get('/auth/register')
        assert response.status_code == 302
        assert 'logout' in response.headers['Location']

        with db.users.update(username = username) as user:
            user.is_verified = 0

        response = client.get('/auth/login')
        assert response.status_code == 302
        assert 'verify' in response.headers['Location']


@microtest.group('slow')
@microtest.test
def test_logout(app, db):
    client = TestClient(app)
    
    password = 'strongpassword'
    username = 'logout_test'
    email = 'test@mail.com'
    
    db.users.insert(
        id = 1,
        username=username,
        email=email,
        password=generate_password_hash(password)
        )
    
    client.login_as(username, password)
    assert db.sessions.get(user_id = 1) is not None

    client.logout(find_csrf_token=False)
    assert db.sessions.get(user_id = 1) is not None

    client.logout()
    assert db.sessions.get(user_id = 1) is None


@microtest.group('slow')
@microtest.test
def test_user_verification(app, db):
    client = TestClient(app)
    
    db.users.insert(
        username='user',
        email='test@mail.com',
        password=generate_password_hash('123')
        )
    user = db.users.get(username = 'user')
    client.login_as('user', '123')

    with app.app_context():
        token, expires = auth.generate_otp(user.id, auth.OTP.EMAIL, 1)

    form_data = {'verification_token':token}
    response = client.post('/auth/verify', data=form_data)
    assert b'Verification failed' in response.data

    page = client.get('/auth/verify').data
    csrf_token = client.find_csrf_token(page)

    form_data = {'csrf_token':csrf_token, 'verification_token':token.hex()}
    response = client.post('/auth/verify', data=form_data)
    assert 'http://localhost/' == response.headers['Location']

    assert db.users.get(id = user.id).is_verified


@microtest.group('slow')
@microtest.test
def test_login_attempt_recording(app, db):
    client = TestClient(app)
    db.users.insert(
        id = 1,
        username='user',
        email='test@mail.com',
        password=generate_password_hash('123')
        )

    _, file = app.config['EMAIL_HOST']
    msg_start = file.tell()
    with microtest.patch(auth, MAX_LOGIN_ATTEMPTS = 1):
        client.login_as('user', '')
        user = db.users.get(id = 1)
        assert not user.is_locked
        assert user.login_attempts == 1

        client.login_as('user', '')
        user = db.users.get(id = 1)
        assert user.is_locked
        assert user.login_attempts == 2

        with mutex:
            file.seek(msg_start)
            email = file.read()
        
        assert f'To: {user.email}' in email
        otp = db.otps.get(user_id = user.id, type = auth.OTP.ACCOUNT_LOCK)
        assert otp.value.hex() in email

        client.login_as('user', '123')
        assert db.sessions.get(user_id = 1) is None


@microtest.group('slow')
@microtest.test
def test_account_unlocking(app, db):
    db.users.insert(
        id = 1,
        username='user',
        email='test@mail.com',
        password=generate_password_hash('123'),
        is_locked = 1,
        )

    db.otps.insert(
        user_id = 1,
        value = b'\x00\x01',
        type = auth.OTP.ACCOUNT_LOCK,
        expires = str(Timestamp(1))
        )

    client = TestClient(app)
    with client:
        response = client.get('/auth/unlock')
        csrf_token = client.find_csrf_token(response.data)
        
        data = {
            'csrf_token': csrf_token,
            'unlock_token': '0001',
            'username': 'user'
        }
        response = client.post('/auth/unlock', data=data)
    
    user = db.users.get(id = 1)
    assert not user.is_locked
    
    try:
        redirect_location = response.headers['Location']
    except:
        raise AssertionError('Account unlocking failed. No redirection.')
    assert '/auth/login' in redirect_location


@microtest.group('slow')
@microtest.test
def test_requesting_password_reset(app, db):
    db.users.insert(
        id = 1,
        username='user',
        email='test@mail.com',
        password=generate_password_hash('123'),
        is_verified = 1,
        )

    client = TestClient(app)
    _, file = app.config['EMAIL_HOST']
    msg_start = file.tell()
    
    with client:
        response = client.get('/auth/reset-password/request')
        csrf_token = client.find_csrf_token(response.data)

        data = {
            'username': 'user',
            'email': 'test@mail.com',
            'csrf_token': csrf_token,
        }
        client.post('/auth/reset-password/request', data=data)

    otp = db.otps.get(user_id = 1)
    assert otp is not None

    with mutex:
        file.seek(msg_start)
        email = file.read()

    assert 'To: test@mail.com' in email
    assert otp.value.hex() in email


@microtest.group('slow')
@microtest.test
def test_anonymous_password_reset(app, db):
    password = '123'
    new_password = '12345678'
    db.users.insert(
        id = 1,
        username='user',
        email='test@mail.com',
        password=generate_password_hash(password),
        is_verified = 1,
        )
    db.otps.insert(
        value = b'\x00\x01',
        expires=str(Timestamp(1)),
        user_id = 1,
        type = auth.OTP.PASSWORD_RESET
        )

    client = TestClient(app)
    with client:
        response = client.get('/auth/reset-password')
        csrf_token = client.find_csrf_token(response.data)

        data = {
            'username': 'user',
            'email': 'test@mail.com',
            'otp':  b'\x00\x01'.hex(),
            'csrf_token': csrf_token,
            'new-password1': new_password,
            'new-password2': new_password,
        }
        response = client.post('/auth/reset-password', data=data)
        assert str(response.status_code).startswith('3')
        assert '/auth/login' in response.headers['Location']

        client.login_as('user', new_password)
        response = client.get('/')
        assert response.status_code == 200


@microtest.group('slow')
@microtest.test
def test_authenticated_password_reset(app, db):
    password = '123'
    new_password = '12345678'
    db.users.insert(
        id = 1,
        username='user',
        email='test@mail.com',
        password=generate_password_hash(password),
        is_verified = 1,
        )

    client = TestClient(app)
    with client:
        client.login_as('user', password)
        response = client.get('/auth/reset-password')
        csrf_token = client.find_csrf_token(response.data)

        data = {
            'csrf_token': csrf_token,
            'password': password,
            'new-password1': new_password,
            'new-password2': new_password,
        }
        response = client.post('/auth/reset-password', data=data)
        assert str(response.status_code).startswith('3')
        assert 'http://localhost/' == response.headers['Location']

        client.logout()
        client.login_as('user', new_password)
        response = client.get('/')
        assert response.status_code == 200



@microtest.group('slow')
@microtest.test
def test_login_requirement(app, db):
    client = TestClient(app)
    SESSIONID = auth.SESSIONID

    with client:
        response = client.get('/')
        session_id = flask.session[SESSIONID]
    try:
        redirect_location = response.headers['Location']
    except:
        raise AssertionError('Login requirement failed. No redirection.')
    assert '/auth/login' in redirect_location

    db.users.insert(
        username='user1',
        email='test1@mail.com',
        password=generate_password_hash('123')
        )

    client.login_as('user1', '123')
    with client:
        response = client.get('/')
        assert flask.session[SESSIONID] != session_id
    try:
        redirect_location = response.headers['Location']
    except:
        raise AssertionError('Verification requirement failed. No redirection.')
    assert '/auth/verify' in redirect_location
    client.logout()

    db.users.insert(
        username='user2',
        email='test2@mail.com',
        password=generate_password_hash('123'),
        is_verified=1,
        )
    
    client.login_as('user2', '123')
    with client:
        response = client.get('/')
        assert response.status_code == 200


@microtest.group('slow')
@microtest.test
def test_admin_requirement(app, db):
    client = TestClient(app)

    db.users.insert(
        username='user',
        email='test@mail.com',
        password=generate_password_hash('123'),
        is_verified=1
        )
    db.users.insert(
        username='admin',
        email='admin@mail.com',
        password=generate_password_hash('123'),
        is_verified=1,
        is_admin=1
        )

    with client:
        response = client.get('/admin/')
    try:
        redirect_location = response.headers['Location']
    except:
        raise AssertionError('Verification requirement failed. No redirection.')
    assert '/auth/login' in redirect_location

    client.login_as('user', '123')
    with client:
        response = client.get('/admin/')
    try:
        redirect_location = response.headers['Location']
    except:
        raise AssertionError('Verification requirement failed. No redirection.')
    assert redirect_location == 'http://localhost/'
    client.logout()

    client.login_as('admin', '123')
    with client:
        response = client.get('/admin/')
        assert response.status_code == 200

    with db.users.update(username = 'admin') as user:
        user.is_verified = 0
    
    with client:
        response = client.get('/admin/')
    try:
        redirect_location = response.headers['Location']
    except:
        raise AssertionError('Verification requirement failed. No redirection.')
    assert 'verify' in redirect_location
        