"""
Interface between the included ORM package and the flask application.

Author Valtteri Rajalainen
"""

import sys
import flask
import blog.orm as orm
import blog.typing as types
from blog.common import Namespace


def create_and_store_database_object() -> types.DatabaseObject:
    database = flask.g.get('database', None)
    if database is None:
        database_path = flask.current_app.config['DATABASE']
        database = orm.Database(database_path)
        database.store_connection()
        flask.g.database = database
    return database


def get_database_table(table_name: str) -> types.DatabaseTable:
    database = create_and_store_database_object()
    return database.get_table(table_name)


class Module(types.Module):

    sessions:   types.DatabaseTable = property(fget=lambda args: get_database_table('sessions'))
    users:      types.DatabaseTable = property(fget=lambda args: get_database_table('users'))
    otps:       types.DatabaseTable = property(fget=lambda args: get_database_table('otps'))
    posts:      types.DatabaseTable = property(fget=lambda args: get_database_table('posts'))


    def init_database(self, schema_module: str):
        database = create_and_store_database_object()
        database.init(schema_module)


    def close_connection(self, *args, **kwargs):
        database = flask.g.pop('database', None)
        if database is not None:
            database.close_connection()


module = Module(__name__)
module.__file__ = __file__
sys.modules[__name__] = module
