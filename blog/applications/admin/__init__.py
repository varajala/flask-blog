import flask
import blog.security as security
import blog.security.sessions as sessions
import blog.models as models
from blog.common import path_relative_to_file



blueprint = flask.Blueprint(
    'admin', __name__,
    url_prefix='/admin',
    template_folder=path_relative_to_file(__file__, 'templates')
    )


@blueprint.route('/', methods=('GET',))
@security.admin_only
def index():
    session = flask.g.session
    user_list = models.users.get_all()
    csrf_token = session.csrf_token.hex()
    return flask.render_template('admin.html', users=user_list, csrf_token=csrf_token)


@blueprint.route('/users/<int:userid>/manage', methods=('GET',))
@security.admin_only
def manage_user(userid):
    session = flask.g.session
    csrf_token = session.csrf_token.hex()
    user = models.users.get(id = userid)    
    if user is None:
        return flask.redirect(flask.url_for('admin.index'))
    return flask.render_template('manage_user.html', user=user, csrf_token=csrf_token)


@blueprint.route('/users/<int:userid>/edit/username', methods=('POST',))
@security.admin_only
def edit_username(userid):
    request = flask.request
    session = flask.g.session
    manage_url = flask.url_for('admin.manage_user', userid=userid)
    csrf_token = session.csrf_token.hex()

    csrf_token = request.form.get('csrf_token', None)
    if csrf_token is None:
        return flask.redirect(manage_url)
    
    try:
        src = bytes.fromhex(csrf_token)
    except ValueError:
        src = b'\x00'

    cmp = session.csrf_token
    if not security.matching_tokens(src, cmp):
        return flask.redirect(manage_url)    
    
    username = request.form.get('username', '')
    if not security.valid_username(username) or models.users.get(username = username) is not None:
        return flask.redirect(manage_url)

    with models.users.update(id = userid) as row:
        row.username = username
    
    return flask.redirect(manage_url)


@blueprint.route('/users/<int:userid>/edit/email', methods=('POST',))
@security.admin_only
def edit_email(userid):
    request = flask.request
    session = flask.g.session
    manage_url = flask.url_for('admin.manage_user', userid=userid)
    csrf_token = session.csrf_token.hex()

    csrf_token = request.form.get('csrf_token', None)
    if csrf_token is None:
        return flask.redirect(manage_url)
    
    try:
        src = bytes.fromhex(csrf_token)
    except ValueError:
        src = b'\x00'

    cmp = session.csrf_token
    if not security.matching_tokens(src, cmp):
        return flask.redirect(manage_url)    
    
    email = request.form.get('email', '')
    if not security.valid_email(email) or models.users.get(email = email) is not None:
        return flask.redirect(manage_url)

    with models.users.update(id = userid) as row:
        row.email = email
    
    return flask.redirect(manage_url)


@blueprint.route('/users/<int:userid>/delete', methods=('POST',))
@security.admin_only
def delete_user(userid):
    request = flask.request
    session = flask.g.session
    manage_url = flask.url_for('admin.manage_user', userid=userid)
    csrf_token = session.csrf_token.hex()
    
    csrf_token = request.form.get('csrf_token', None)
    if csrf_token is None:
        return flask.redirect(manage_url)
    
    try:
        src = bytes.fromhex(csrf_token)
    except ValueError:
        src = b'\x00'

    cmp = session.csrf_token
    if not security.matching_tokens(src, cmp):
        return flask.redirect(manage_url)

    row = models.sessions.get(user_id = userid)
    if row is not None:
        sessions.end_session(row.session_id)

    models.users.delete(id = userid)
    return flask.redirect(flask.url_for('admin.index'))


@blueprint.route('/users/<int:userid>/verify', methods=('POST',))
@security.admin_only
def verify_user(userid):
    request = flask.request
    session = flask.g.session
    manage_url = flask.url_for('admin.manage_user', userid=userid)
    csrf_token = session.csrf_token.hex()

    csrf_token = request.form.get('csrf_token', None)
    if csrf_token is None:
        return flask.redirect(manage_url)
    
    try:
        src = bytes.fromhex(csrf_token)
    except ValueError:
        src = b'\x00'

    cmp = session.csrf_token
    if not security.matching_tokens(src, cmp):
        return flask.redirect(manage_url)
    
    with models.users.update(id = userid) as row:
        row.is_verified = 1
    
    return flask.redirect(manage_url)


@blueprint.route('/users/<int:userid>/promote', methods=('POST',))
@security.admin_only
def make_admin(userid):
    request = flask.request
    session = flask.g.session
    manage_url = flask.url_for('admin.manage_user', userid=userid)
    csrf_token = session.csrf_token.hex()
    
    csrf_token = request.form.get('csrf_token', None)
    if csrf_token is None:
        return flask.redirect(manage_url)
    
    try:
        src = bytes.fromhex(csrf_token)
    except ValueError:
        src = b'\x00'

    cmp = session.csrf_token
    if not security.matching_tokens(src, cmp):
        return flask.redirect(manage_url)

    row = models.sessions.get(user_id = userid)
    if row is not None:
        sessions.end_session(row.session_id)

    with models.users.update(id = userid) as row:
        row.is_admin = 1

    return flask.redirect(flask.url_for('admin.index'))


@blueprint.route('/users/create', methods=('POST',))
@security.admin_only
def create_user():
    request = flask.request
    session = flask.g.session
    index_url = flask.url_for('admin.index')

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

    username = request.form.get('username', '')
    email = request.form.get('email', '')
    password = request.form.get('password', '')

    checks = (
        security.valid_username(username),
        security.valid_email(email),
        security.valid_password(password)
    )

    if not all(checks):
        flask.flash('Invalid user data.')
        return flask.redirect(index_url)
    
    models.users.insert(
        username = username,
        email = email,
        password = security.generate_password_hash(password),
        is_verified = 1
        )
    flask.flash('Created user.')
    return flask.redirect(index_url)
