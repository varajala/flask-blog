"""
Functions related to session handling.

Author: Valtteri Rajalainen
"""

import hashlib
import os
import flask
import codecs
import hmac

import blog.typing as types
from blog.common import Timestamp, Session
from blog.security.utils import *

if types.TYPE_CHECKING:
    import blog.models
    models = types.cast(blog.models.Module, blog.models)
else:
    import blog.models as models


__all__ = [
    'create_new_session',
    'end_session',
    'load_user_session'
]


def create_new_session(userid: int = 0) -> Session:
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


def get_session_by_id(session_id: bytes) -> types.Optional[Session]:
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


def end_session(session_id: bytes):
    models.sessions.delete(session_id = session_id)


def load_user_session(raw_session_id: str) -> Session:
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
        return create_new_session()

    else:
        session = get_session_by_id(session_id)
        if session is None:
            return create_new_session()
        if session.is_expired:
            return create_new_session()
        return session