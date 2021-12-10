"""
Database schema implemented using the included ORM package.
This module is executed with all datatype objects in its namespace.

Author: Valtteri Rajalainen
"""


users = {
    'id': integer(primary_key = True, auto_increment = True),
    'username': text(unique = True, not_null = True),
    'email': text(unique = True, not_null = True),
    'password': text(not_null = True),

    'login_attempts': integer(not_null = True, default = 0),
    'is_locked': integer(not_null = True, default = 0),
    
    'is_verified': integer(not_null = True, default = 0),
    'is_admin': integer(not_null = True, default = 0)
}


sessions = {
    'session_id': blob(),
    'csrf_token': blob(),
    'expires': text(not_null = True),
    'user_id': integer(not_null = True, default = 0),
}


otps = {
    'id': integer(primary_key = True, auto_increment = True),
    'value': blob(),
    'expires': text(not_null = True),
    'type': text(not_null = True),
    'user_id': integer(not_null = True, foreign_key = ('user_id', 'users', 'id')),
}


posts = {
    'id': integer(primary_key = True, auto_increment = True),
    'created': text(not_null = True),
    'content': text(not_null = True),
    'author_id': integer(not_null = True, foreign_key = ('author_id', 'users', 'id')),
}
