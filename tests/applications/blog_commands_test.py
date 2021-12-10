import microtest
from microtest.utils import Namespace

import flask
import flask_blog.applications.blog as blog_application


@microtest.reset
def reset(db):
    db.reset()


@microtest.test
def test_init_db_cmd(app, db):
    runner = app.test_cli_runner()

    items = {'init_called': False}

    def dummy_init(*args, **kwargs):
        nonlocal items
        items['init_called'] = True
    
    items['init_database'] = dummy_init

    with microtest.patch(blog_application.commands, models = Namespace(items)):
        result = runner.invoke(args=['init-db'])
        assert items['init_called']
        assert 'OK' in result.output


@microtest.test
def test_create_user_cmd(app, db):
    runner = app.test_cli_runner()

    cmd = [
        'create-user',
        '--username', 'user',
        '--email', 'test@mail.com',
        '--password', '12345678'
        ]

    result = runner.invoke(args=cmd)
    assert 'OK' in result.output

    assert db.get_table('users').get(username = 'user') is not None
