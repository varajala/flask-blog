import flask

import blog.security as security
import blog.models as models
from blog.common import Timestamp

blueprint = flask.Blueprint('blog', __name__)


@blueprint.route('/', methods=('GET',))
@security.authentication_required
def index():
    user = flask.g.user
    session = flask.g.session
    csrf_token = session.csrf_token.hex()
    post_list = models.posts.query(author_id = user.id)
    return flask.render_template('blog.html', posts=post_list, csrf_token=csrf_token)


@blueprint.route('/create', methods=('POST',))
@security.authentication_required
def create():
    request = flask.request
    user = flask.g.user
    session = flask.g.session
    blog_url = flask.url_for('index')
    
    csrf_token = request.form.get('csrf_token', None)
    if csrf_token is None:
        return flask.redirect(blog_url)
    
    try:
        src = bytes.fromhex(csrf_token)
    except ValueError:
        src = b'\x00'

    cmp = session.csrf_token
    if not security.matching_tokens(src, cmp):
        return flask.redirect(blog_url)

    content = request.form['text']
    if content and not content.isspace():
        models.posts.insert(author_id = user.id, content = content, created = str(Timestamp()))

    return flask.redirect(blog_url)


@blueprint.route('/update/<int:postid>', methods=('POST',))
@security.authentication_required
def update(postid):
    blog_url = flask.url_for('index')
    session = flask.g.session
    request = flask.request
    
    csrf_token = request.form.get('csrf_token', None)
    if csrf_token is None:
        return flask.redirect(blog_url)
    
    try:
        src = bytes.fromhex(csrf_token)
    except ValueError:
        src = b'\x00'
    
    cmp = session.csrf_token
    if not security.matching_tokens(src, cmp):
        return flask.redirect(blog_url)
    
    content = None
    if 'new-content' in flask.request.form:
        content = flask.request.form['new-content']

    if content and not content.isspace():
        with models.posts.update(id = postid) as post:
            post.content = content
    
    return flask.redirect(blog_url)


@blueprint.route('/delete/<int:postid>', methods=('POST',))
@security.authentication_required
def delete(postid):
    blog_url = flask.url_for('index')
    session = flask.g.session
    request = flask.request
    
    csrf_token = request.form.get('csrf_token', None)
    if csrf_token is None:
        return flask.redirect(blog_url)
    
    try:
        src = bytes.fromhex(csrf_token)
    except ValueError:
        src = b'\x00'
    
    cmp = session.csrf_token
    if not security.matching_tokens(src, cmp):
        return flask.redirect(blog_url)
    
    models.posts.delete(id = postid)
    return flask.redirect(blog_url)