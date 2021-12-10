import microtest
import flask
import flask_blog.orm.main as orm
import flask_blog.models as models


@microtest.test
def test_models(app):
    with app.app_context():
        users = models.users
        posts = models.posts
        assert isinstance(users, orm.Table)
        assert isinstance(posts, orm.Table)
