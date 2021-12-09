import sys
import flask
from types import ModuleType
import blog.orm as orm


class Module(ModuleType):

    def __connect(self):
        if 'database' not in flask.g:
            database_path = flask.current_app.config['DATABASE']
            database = orm.Database(database_path)
            database.store_connection()
            flask.g.database = database


    def close_connection(self, *args, **kwargs):
        database = flask.g.pop('database', None)
        if database is not None:
            database.close_connection()


    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        
        except AttributeError as err:
            self.__connect()
            return getattr(flask.g.database, attr)


module = Module(__name__)
module.__file__ = __file__
sys.modules[__name__] = module
