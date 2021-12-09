import os
import sys
from pathlib import Path
from flask import Flask

import blog.security as security
import blog.blog_app as blog_app
import blog.admin as admin
import blog.models as models

import blog.orm.manage
import blog.security.manage
from blog.cli import commands


def create_app(test_config = None):
    global database
    app = Flask(__name__)
    app.config.from_object('blog.config')

    if test_config:
        for key, value in test_config.items():
            app.config[key] = value

    app.teardown_appcontext(models.close_connection)

    app.register_blueprint(security.blueprint)
    app.register_blueprint(blog_app.blueprint)
    app.register_blueprint(admin.blueprint)
    
    app.add_url_rule('/', endpoint='index')

    for command in commands:
        app.cli.add_command(command)
    return app
    