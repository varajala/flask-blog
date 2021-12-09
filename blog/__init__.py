import os
import sys
from pathlib import Path
from flask import Flask

import flask_tutorial.security as security
import flask_tutorial.blog as blog
import flask_tutorial.admin as admin
import flask_tutorial.models as models

import flask_tutorial.orm.manage
import flask_tutorial.security.manage
from flask_tutorial.cli import commands


def create_app(test_config = None):
    global database
    app = Flask(__name__)
    app.config.from_object('flask_tutorial.config')

    if test_config:
        for key, value in test_config.items():
            app.config[key] = value

    app.teardown_appcontext(models.close_connection)

    app.register_blueprint(security.blueprint)
    app.register_blueprint(blog.blueprint)
    app.register_blueprint(admin.blueprint)
    
    app.add_url_rule('/', endpoint='index')

    for command in commands:
        app.cli.add_command(command)
    return app
    