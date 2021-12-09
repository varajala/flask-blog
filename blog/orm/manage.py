import click
import flask
from flask.cli import with_appcontext

import flask_tutorial.cli as cli
import flask_tutorial.security as security
import flask_tutorial.models as models


@cli.register
@click.command('init-db')
@with_appcontext
def init_database():
    try:
        models.init('flask_tutorial.schema')
    
    except Exception as err:
        print(err)
        click.secho('ERROR ', fg='red', nl=False)
        click.echo('Failed to initialize the database.\n')
        click.echo(str(err) + '\n')
    
    else:
        click.secho('OK ', fg='green', nl=False)
        click.echo('Database initialized.\n')



@cli.register
@click.command('create-user')
@click.option('--username', prompt='Username')
@click.option('--email', prompt='Email address')
@click.option('--password', prompt='Password', hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_user(username, email, password):
    if not security.valid_username(username):
        click.secho('ERROR ', fg='red', nl=False)
        info = f'Failed to create a new user. Username {username} is invalid.\n'
        click.echo(info)
        return
    
    if models.users.get(username = username) is not None:
        click.secho('ERROR ', fg='red', nl=False)
        info = f'Failed to create a new user. Username {username} is already in use.\n'
        click.echo(info)    
        return

    if not security.valid_email(email):
        click.secho('ERROR ', fg='red', nl=False)
        info = f'Failed to create a new user. Email address {email} is invalid.\n'
        click.echo(info)
        return
    
    if models.users.get(email = email) is not None:
        click.secho('ERROR ', fg='red', nl=False)
        info = f'Failed to create a new user. Email address {email} is already in use.\n'
        click.echo(info)    
        return
    
    password_hash = security.generate_password_hash(password)
    models.users.insert(username = username, email = email, password = password_hash, is_verified = 1)

    click.secho('OK ', fg='green', nl=False)
    click.echo(f'Created a new user: {username}\n')
