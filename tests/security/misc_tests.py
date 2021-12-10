import microtest
import flask
import blog.security as security


ignore_in_csrf_check = [
    '/auth/register',
    ]

username = 'test_user'
password = '12345678'


@microtest.setup
def setup(db):
    db.get_table('users').insert(
        username=username,
        email='test.user@mail.com',
        password=security.generate_password_hash(password),
        is_verified=1,
        is_admin=1
    )

@microtest.cleanup
def cleanup(db):
    db.reset()

    
@microtest.test
def test_csrf_protection(app):
    client = TestClient(app)
    client.login_as(username, password)

    with app.app_context():
        rules = app.url_map.iter_rules()
        include_rule = lambda rule: str(rule).find('<') == -1 and str(rule) not in ignore_in_csrf_check
        endpoints = [ str(rule) for rule in rules if include_rule(rule) ]

    with client:
        for url in endpoints:
            res = client.get(url)
            forms = res.data.count(b'<form')
            if forms:
                count = res.data.count(b'"csrf_token"')
                if count != forms:
                    info = f'There are some forms without a csrf_token. URL: "{url}"'
                    raise AssertionError(info)
