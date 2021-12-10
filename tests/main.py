import tempfile
import os
import pathlib
import re
import sys

import microtest
import blog as application
import blog.orm as orm


# Uncomment to exclude tests marked as slow...
# microtest.exclude_groups('slow')


@microtest.utility
class TestClient:

    login_url = '/auth/login'
    logout_url = '/auth/logout'
    register_url = '/auth/register'
    csrf_token_name = 'csrf_token'

    def __init__(self, app):
        self.client = app.test_client()

    
    def login_as(self, username, password, *, find_csrf_token=True):
        res = self.client.get(self.login_url)
        
        form_data = {'username':username, 'password':password}
        
        if find_csrf_token:
            csrf_token = self.find_csrf_token(res.data)
            if csrf_token:
                form_data[self.csrf_token_name] = csrf_token
        
        response = self.client.post(self.login_url, data=form_data)
        return response


    def register_as(self, username, email, password, *, confirm_password=True):
        form_data = {
            'username':username,
            'email':email,
            'password1':password,
            'password2':password
        }
        if not confirm_password:
            form_data['password2'] = password[::-1]
        
        response = self.client.post(self.register_url, data=form_data)
        return response

    
    def logout(self, *, find_csrf_token=True):
        res = self.client.get(self.logout_url)
        
        form_data = dict()
        if find_csrf_token:
            csrf_token = self.find_csrf_token(res.data)
            if csrf_token:
                form_data[self.csrf_token_name] = csrf_token
        
        response = self.client.post(self.logout_url, data=form_data)
        return response


    def find_csrf_token(self, data: bytes) -> str:
        token_name = self.csrf_token_name
        input_tag_exp = re.compile(b'<input.*>')
        matches = re.finditer(input_tag_exp, data)
        if not matches:
            return None

        for match in matches:
            if match[0].find(f'name="{token_name}"'.encode()) != -1:
                token_exp = re.compile(b'(?<=value=").*(?=")')
                token = re.search(token_exp, match[0])
                if token is not None:
                    return token[0].decode()
        return None


    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            client = object.__getattribute__(self, 'client')
            return object.__getattribute__(client, attr)


    def __enter__(self):
        return self.client.__enter__()


    def __exit__(self, exc_type, exc, tb):
        self.client.__exit__(exc_type, exc, tb)


def create_test_app(database_path):
    config = {
        'TESTING':True,
        'DATABASE':database_path,
        'EMAIL_HOST':(None, sys.stdout),
        'EMAIL_USE_SSL':False,
    }
    app = application.create_app(config)

    with app.app_context():
        application.models.init_database('blog.schema')

    return app


@microtest.call
def test_setup():
    fd, path = tempfile.mkstemp()
    
    def reset_database(database):
        for table in database.tables.values():
            table.delete()

    microtest.add_resource('app', create_test_app(path))
    
    database = orm.Database(path)
    database.store_connection()
    setattr(database, 'reset', lambda: reset_database(database))
    microtest.add_resource('db', database)

    @microtest.on_exit
    def terminate(exc_type, exc, tb):
        database.close_connection()
        
        os.unlink(path)
        os.close(fd)
