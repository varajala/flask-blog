import os
import sys
from flask import Flask

import flask_blog.applications.auth as auth_application
import flask_blog.applications.admin as admin_application
import flask_blog.applications.blog as blog_application

import flask_blog.models as models
import flask_blog.cli as cli


def create_app(test_config = None):
    app = Flask(__name__)
    app.config.from_object('flask_blog.config')

    if test_config:
        for key, value in test_config.items():
            app.config[key] = value

    app.teardown_appcontext(models.close_connection)

    app.register_blueprint(auth_application.blueprint)
    app.register_blueprint(admin_application.blueprint)
    app.register_blueprint(blog_application.blueprint)
    
    app.add_url_rule('/', endpoint='index')

    for command in cli.commands:
        app.cli.add_command(command)

    if not os.path.exists(app.config['EMAIL_CREDENTIALS']):
        sys.stdout.write('[ WARNING ]: Email credentials not found.\n')
        sys.stdout.write('A placeholder file is created into: ')
        sys.stdout.write(app.config['EMAIL_CREDENTIALS'] + '.\n\n')

        with open(app.config['EMAIL_CREDENTIALS'], 'wb') as file:
            file.write(b'email-address')
            file.write(b'\n')
            file.write(b'password')

        app.config['EMAIL_HOST'] = (None, sys.stdout)
    
    return app
