import microtest
import flask
import flask_tutorial.orm.manage as manage


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
    
    items['init'] = dummy_init

    with microtest.patch(manage, models = microtest.Namespace(items)):
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

    assert db.users.get(username = 'user') is not None
