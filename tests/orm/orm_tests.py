import microtest
import tempfile
import os
import random

from flask_blog.orm.main import *
from flask_blog.orm.sql import *


fd = None
path = None
db = None


@microtest.setup
def setup():
    global fd, path, db
    fd, path = tempfile.mkstemp()
    db = Database(path)
    db.store_connection()


@microtest.cleanup
def cleanup():
    db.close_connection()
    os.close(fd)
    os.unlink(path)


@microtest.test
def test_table_creation():
    users_schema = {
        'id':integer(primary_key=True, auto_increment=True),
        'name':text(unique=True),
        'bio':text(),
        'is_admin': integer(not_null=True, default=0),
    }
    posts_schema = {
        'id':integer(primary_key=True, auto_increment=True),
        'content':text(),
        'created':text(),
        'user_id':integer(foreign_key=('user_id', 'users', 'id')),
    }
    users = db.create_table('users', users_schema)
    posts = db.create_table('posts', posts_schema)


@microtest.test
def test_loading_tables():
    db = Database(path)
    users = db.get_table('users')
    posts = db.get_table('posts')
    
    assert isinstance(users, Table)
    assert isinstance(posts, Table)

    assert microtest.raises(lambda: users.sometable, (), AttributeError)


@microtest.test
def test_queries():
    db = Database(path)
    users = db.get_table('users')

    usernames = ['user', 'tester', 'hacker']
    user_data = [ (f'user{i}', random.choice(usernames)) for i in range(99) ]
    
    for data in user_data:
        name, bio = data
        users.insert(name=name, bio=bio)
    
    users.insert(name='user', bio='hacker')
    
    user = users.get(name='user')
    assert isinstance(user, Namespace)
    assert user.bio == 'hacker'

    assert len(users.get_all()) == 100

    matches = users.query(bio='hacker')
    assert matches

    matches = users.query(bio='hacker', id=100)
    assert len(matches) == 1


@microtest.test
def test_updates():
    users = db.get_table('users')

    users.insert(name='testuser', bio='testing')
    user = users.get(name='testuser')

    with users.update(name='testuser') as results:
        results.bio = 'hacker'

    assert users.get(name='testuser').bio == 'hacker'


    posts = db.get_table('posts')
    posts.insert(content='test1', created='12:00 1.1.2021')
    posts.insert(content='test2', created='12:00 1.1.2021')
    posts.insert(content='test3', created='12:00 1.1.2021')
    posts.insert(content='test4', created='Monday')

    with posts.update(created='12:00 1.1.2021') as results:
        results.content = 'Created on the same day!'

    modified = posts.query(created='12:00 1.1.2021')
    assert len(modified) == 3
    for post in modified:
        assert post.content == 'Created on the same day!'


@microtest.test
def test_deletions():
    users = db.get_table('users')

    users.insert(name='deltest', bio='testing')
    matches = users.query(name='deltest')
    assert matches

    users.delete(name='deltest')
    matches = users.query(name='deltest')
    assert not matches

    matches = users.query(bio='hacker')
    assert matches

    users.delete(bio='hacker')
    matches = users.query(bio='hacker')
    assert not matches

    assert len(users.get_all()) > 0
    users.delete()
    assert len(users.get_all()) == 0



@microtest.test
def test_drop_table():
    users = db.get_table('users')
    assert isinstance(users, Table)

    db.drop_table('users')
    assert 'users' not in db.tables
    assert 'users' not in db.list_tables()


if __name__ == '__main__':
    microtest.run()