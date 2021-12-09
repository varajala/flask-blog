import microtest
import flask
from blog.security import *
import blog.security.sessions as sessions
from blog.common import Timestamp


username = 'testing_sessions_and_auth'
password = '12345678'


@microtest.reset
def reset(db):
    db.reset()


@microtest.test
def test_timestamps(app, db):
    ts1 = Timestamp()
    ts2 = Timestamp(5)
    
    assert ts2 > ts1
    assert ts1 < ts2
    assert ts1 != ts2

    assert not ts1 > ts2
    assert not ts2 < ts1
    assert not ts1 == ts2

    ts3 = Timestamp()
    ts4 = Timestamp.from_str(str(ts3))

    assert ts3 == ts4
    assert not ts3 < ts4
    assert not ts3 > ts4

    assert Timestamp() < Timestamp(10)
    assert Timestamp(10) > Timestamp()


@microtest.group('slow')
@microtest.test
def test_creating_sessions(app, db):
    with app.app_context():
        assert len(db.sessions.get_all()) == 0

        session = sessions.create_new_session()

        rows = db.sessions.get_all()
        assert len(rows) == 1
        
        row = rows[0]
        assert row.session_id == session.id
        assert row.user_id == session.user_id == 0
        assert row.csrf_token == session.csrf_token
        assert session.is_anonymous
        
        assert session.expires > Timestamp(sessions.SESSION_LIFETIME - 1)
        assert session.expires < Timestamp(sessions.SESSION_LIFETIME + 1)
        
        assert session.expires > Timestamp()
        assert Timestamp() < session.expires
        assert not session.is_expired


@microtest.group('slow')
@microtest.test
def test_loading_sessions(app, db):
    with app.app_context():
        session_id = b'\x00\x01'
        csrf_token = b'\x00\x02'
        userid = 1
        
        db.sessions.insert(
            session_id = session_id,
            csrf_token = csrf_token,
            expires = str(Timestamp(1)),
            user_id = userid
            )

        session = sessions.load_user_session(session_id.hex())

        assert session.id == session_id
        assert session.csrf_token == csrf_token

        db.sessions.delete()

        session = sessions.load_user_session(None)

        assert len(db.sessions.get_all()) == 1
        assert session.is_anonymous

        db.sessions.delete()

        session = sessions.load_user_session('100')

        assert len(db.sessions.get_all()) == 1
        assert session.is_anonymous

        db.sessions.delete()
        db.sessions.insert(
            session_id = session_id,
            csrf_token = csrf_token,
            expires = str(Timestamp(-1)),
            user_id = userid
            )

        session = sessions.load_user_session(session_id.hex())
        
        assert session_id != session.id
        assert session.is_anonymous


@microtest.group('slow')
@microtest.test
def test_ending_sessions(app, db):
    with app.app_context():
        sid = (1).to_bytes(32, 'big')
        csrf = bytes(bytearray(32))
        uid = 1
        
        db.sessions.insert(session_id=sid, csrf_token=csrf, expires=str(Timestamp(12)),  user_id=uid)

        sessions.end_session(sid)

        rows = db.sessions.get_all()
        assert len(rows) == 0


@microtest.group('slow')
@microtest.test
def test_session_handling(app, db):
    with app.app_context():
        db.users.insert(
            username=username,
            email='test@mail.com',
            password=generate_password_hash(password)
            )
        
        client = TestClient(app)
        response = client.get('/')
        anon_session1 = flask.g.get('session', None)
        user = flask.g.get('user', None)
        
        assert anon_session1 is not None
        assert anon_session1.is_anonymous
        assert user is None

        client.login_as(username, password)
        
        response = client.get('/')
        auth_session = flask.g.get('session', None)
        user = flask.g.get('user', None)
        
        assert auth_session is not None
        assert user is not None
        assert not auth_session.is_anonymous
        assert not auth_session.is_expired
        assert auth_session.id != anon_session1.id

        client.logout()

        response = client.get('/')
        anon_session2 = flask.g.get('session', None)
        user = flask.g.get('user', None)
    
        assert anon_session2 is not None
        assert user is None
        assert auth_session.id != anon_session2.id
        assert anon_session1.id != anon_session2.id


@microtest.group('slow')
@microtest.test
def test_session_expiration(app, db):
    with app.app_context():
        client = TestClient(app)

        db.users.insert(
            username=username,
            email='test@mail.com',
            password=generate_password_hash(password)
            )
        
        with microtest.patch(sessions, SESSION_LIFETIME = -1):
            response = client.get('/')
            session1 = flask.g.get('session', None)
            user = flask.g.get('user', None)
            
            assert session1 is not None
            assert session1.is_anonymous
            assert session1.is_expired
            assert user is None

            client.login_as(username, password)
            
            response = client.get('/')
            session2 = flask.g.get('session', None)
            user = flask.g.get('user', None)
            
            assert session2 is not None
            assert user is None
            assert session2.is_anonymous
            assert session2.is_expired
            assert session2.id != session1.id
