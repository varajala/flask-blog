import os
import sys
from pathlib import Path
from flask import Flask

import blog.applications.auth as auth_application
import blog.applications.admin as admin_application
import blog.applications.blog as blog_application

import blog.models as models
import blog.cli as cli


def create_app(test_config = None):
    app = Flask(__name__)
    app.config.from_object('blog.config')

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
    return app
