"""
Functions related to session handling.

About the implementation:

Sessions are implemented as server side sessions. (Flask defaults to client side sessions.)
The only item stored in client side is the sessionid, 256 bit key in hex format.

Every user is linked to a single session. When user is not authenticated, the
user_id in the session is 0. When user is authenticated, the anonymus session is
ended and a new session is started. When logging out, the authenticated session is ended
and new anonymous session is created.

CSRF-tokens are linked to the session, not single forms.
The session is always stored in the flask.g object.

Author: Valtteri Rajalainen
"""

import hashlib
import os
import flask
import codecs
import hmac

from blog.common import Timestamp, Session
from blog.security.utils import *
import blog.models as models


__all__ = [
    'create_new_session',
    'end_session',
    'load_user_session'
]


def create_new_session(userid = 0):
    """
    Create and store new session linked to the given userid.
    Returns a Session object.
    """
    app = flask.current_app
    secret_key = app.config['SECRET_KEY']
    
    if not isinstance(secret_key, bytes):
        secret_key = codecs.encode(secret_key, encoding='ascii', errors='surrogateescape')
    
    
    while True:
        session_id = os.urandom(SESSIONID_RAND_BYTES)
        if models.sessions.get(session_id = session_id) is None:
            break

    csrf_token = hashlib.pbkdf2_hmac(PBKDF2_HASH, session_id, secret_key, PBKDF2_ITERATIONS)
    expires = Timestamp(SESSION_LIFETIME)

    params = {
        'session_id': session_id,
        'csrf_token': csrf_token,
        'expires': str(expires),
        'user_id': userid,
        }
    models.sessions.insert(**params)
    
    return Session(session_id, csrf_token, expires, userid)


def get_session_by_id(session_id):
    row = models.sessions.get(session_id = session_id)
    if not row:
        return None
    
    session = Session(
        row.session_id,
        row.csrf_token,
        Timestamp.from_str(row.expires),
        row.user_id
        )
    return session


def end_session(session_id):
    models.sessions.delete(session_id = session_id)


def load_user_session(raw_session_id):
    """
    Always returns a Session object.

    If the raw session id is None, invalid type, non existing or the corresponding session
    is expired, a new anonymus session is created.
    """
    if raw_session_id is None:
        return create_new_session()
    
    try:
        session_id = bytes.fromhex(raw_session_id)
    
    except (ValueError, TypeError):
        session = create_new_session()

    else:
        session = get_session_by_id(session_id)
        if session is None or session.is_expired:
            session = create_new_session()

    return session
