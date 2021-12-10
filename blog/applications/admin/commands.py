import click
import flask
from flask.cli import with_appcontext

import blog.cli as cli
import blog.security.utils as utils
import blog.typing as types

if types.TYPE_CHECKING:
    import blog.models
    models = types.cast(blog.models.Module, blog.models)
else:
    import blog.models as models



@cli.register
@click.command('create-admin')
@click.option('--username', prompt='Username')
@click.option('--email', prompt='Email address')
@click.option('--password', prompt='Password', hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_admin_user(username: str, email: str, password: str):
    if not utils.valid_username(username):
        click.secho('ERROR ', fg='red', nl=False)
        info = f'Failed to create a new user. Username {username} is invalid.\n'
        click.echo(info)
        return
    
    if models.users.get(username = username) is not None:
        click.secho('ERROR ', fg='red', nl=False)
        info = f'Failed to create a new user. Username {username} is already in use.\n'
        click.echo(info)    
        return

    if not utils.valid_email(email):
        click.secho('ERROR ', fg='red', nl=False)
        info = f'Failed to create a new user. Email address {email} is invalid.\n'
        click.echo(info)
        return
    
    if models.users.get(email = email) is not None:
        click.secho('ERROR ', fg='red', nl=False)
        info = f'Failed to create a new user. Email address {email} is already in use.\n'
        click.echo(info)    
        return
    
    password_hash = utils.generate_password_hash(password)
    models.users.insert(
        username = username,
        email = email,
        password = password_hash,
        is_verified = 1,
        is_admin = 1
        )

    click.secho('OK ', fg='green', nl=False)
    click.echo(f'Created a new admin user: {username}\n')
