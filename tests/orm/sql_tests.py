import microtest
import blog.orm.sql as sql


@microtest.test
def test_insert():
    result = sql.insert('tests', ('data',))
    assert result.lower() == 'insert into tests (data) values (?)'

    result = sql.insert('users', ('id', 'password', 'username'))
    assert result.lower() == 'insert into users (id, password, username) values (?, ?, ?)'


@microtest.test
def test_select():
    result = sql.select('users')
    assert result.lower() == 'select * from users'

    result = sql.select('users', id=sql.EQ)
    assert result.lower() == 'select * from users where id = ?'

    result = sql.select('users', ('id', 'username'))
    assert result.lower() == 'select (id, username) from users'

    result = sql.select('users', ('username',), id=sql.EQ)
    assert result.lower() == 'select (username) from users where id = ?'

    result = sql.select('users', ('bio',), id=sql.EQ, username=sql.EQ)
    assert result.lower() == 'select (bio) from users where id = ? and username = ?'

    invalid_param = lambda: sql.select('users', ('username',), name='; DROP TABLE users')
    invalid_query = lambda: sql.select('users', ('username',), **{'; DROP TABLE users':sql.EQ})
    
    assert microtest.raises(invalid_param, (), ValueError)
    assert microtest.raises(invalid_query, (), ValueError)


@microtest.test
def test_update():
    result = sql.update('users', ('bio',))
    assert result.lower() == 'update users set bio = ?'

    result = sql.update('users', ('bio', 'name'))
    assert result.lower() == 'update users set bio = ?, name = ?'

    result = sql.update('users', ('bio', 'name'), id=sql.EQ)
    assert result.lower() == 'update users set bio = ?, name = ? where id = ?'

    result = sql.update('users', ('bio', 'name'), name=sql.EQ, bio=sql.EQ)
    assert result.lower() == 'update users set bio = ?, name = ? where name = ? and bio = ?'

    invalid_param = lambda: sql.update('users', ('bio', 'name'), id='; DROP TABLE user')
    invalid_query = lambda: sql.update('users', ('bio', 'name'), **{'name':sql.EQ, '; DROP TABLE user':sql.EQ})
    
    assert microtest.raises(invalid_param, (), ValueError)
    assert microtest.raises(invalid_query, (), ValueError)


@microtest.test
def test_delete():
    result = sql.delete('users')
    assert result.lower() == 'delete from users'

    result = sql.delete('users', id=sql.EQ)
    assert result.lower() == 'delete from users where id = ?'

    result = sql.delete('users', name=sql.EQ, bio=sql.EQ)
    assert result.lower() == 'delete from users where name = ? and bio = ?'

    invalid_param = lambda: sql.delete('users', id='; DROP TABLE users')
    invalid_query = lambda: sql.delete('users', **{'; DROP TABLE users':sql.EQ})
    
    assert microtest.raises(invalid_param, (), ValueError)
    assert microtest.raises(invalid_query, (), ValueError)


@microtest.test
def test_datatypes():
    dt = sql.integer()
    assert dt.resolve() == 'INTEGER'

    dt = sql.integer(primary_key=True, auto_increment=True)
    assert dt.resolve() == 'INTEGER PRIMARY KEY AUTOINCREMENT'

    dt = sql.integer(foreign_key=('user_id', 'users', 'id'))
    assert dt.resolve() == 'INTEGER, FOREIGN KEY(user_id) REFERENCES users(id)'

    dt = sql.text(unique=True, not_null=True)
    assert dt.resolve() == 'TEXT UNIQUE NOT NULL'

    dt = sql.real()
    assert dt.resolve() == 'REAL'

    dt = sql.blob()
    assert dt.resolve() == 'BLOB'

    assert microtest.raises(sql.DataType, ('; DROP TABLE users',), ValueError)
    
    make_datatype = lambda: sql.DataType('integer', default='; DROP TABLE users').resolve()
    assert microtest.raises(make_datatype, (), ValueError)

    make_datatype = lambda: sql.DataType('integer', foreign_key=('user_id', '; DROP TABLE users', 'users')).resolve()
    assert microtest.raises(make_datatype, (), ValueError)


@microtest.test
def test_creating_tables():
    result = sql.create_table('users',
        id = sql.integer(primary_key=True, auto_increment=True),
        name = sql.text(unique=True, not_null=True)
        )
    assert result.lower() == 'create table users (id integer primary key autoincrement, name text unique not null)'

    result = sql.create_table('posts',
        id = sql.integer(primary_key=True, auto_increment=True),
        user_id = sql.integer(foreign_key=('user_id', 'users', 'id')),
        content = sql.text()
        )
    assert result.lower() == 'create table posts (id integer primary key autoincrement, user_id integer, foreign key(user_id) references users(id), content text)'


@microtest.test
def test_dropping_tables():
    result = sql.drop_table('users')
    assert result.lower() == 'drop table users'

    def wrapper():
        result = sql.drop_table('; SELECT password FROM users')
    
    assert microtest.raises(wrapper, (), ValueError)


@microtest.test
def test_name_validation():
    valid_names = [
        'users',
        'user_profiles',
        'Users',
        'users001',
    ]
    for name in valid_names:
        assert sql.valid_name(name), (f'Valid name {name} failed validation',)

    invalid_names = [
        'users!',
        'users?',
        'users; DROP TABLE posts',
        '_users',
        '1users',
        'sqlite_users',
    ]
    for name in invalid_names:
        assert not sql.valid_name(name), (f'Invalid name {name} passed validation',)