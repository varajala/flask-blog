import os
import sys
from pathlib import Path
from flask import Flask

import blog.applications as applications
import blog.models as models

import blog.orm.manage
import blog.security.manage
import blog.cli as cli


def create_app(test_config = None):
    app = Flask(__name__)
    app.config.from_object('blog.config')

    if test_config:
        for key, value in test_config.items():
            app.config[key] = value

    app.teardown_appcontext(models.close_connection)

    app.register_blueprint(applications.auth.blueprint)
    app.register_blueprint(applications.admin.blueprint)
    app.register_blueprint(applications.blog.blueprint)
    
    app.add_url_rule('/', endpoint='index')

    for command in cli.commands:
        app.cli.add_command(command)
    return app
