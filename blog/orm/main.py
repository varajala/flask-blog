"""
A simple 'ORM' implemented ontop of Python's builtin sqlite3 library.

This module is the actual 'ORM' part, the orm.sql module performs
all input validation and SQL generation.

Author: Valtteri Rajalainen
"""

import sqlite3
import os
import runpy
import blog.orm.sql as sql
from blog.common import Namespace


class Table:
    """
    Mapping a database table to an object.
    A new connection is created with every method call.
    To reuse the connection between many queries,
    use the Table object as a context manager.

    Example:

        database.people.insert(first_name = 'Foo', last_name = 'Bar')
        database.people.get(fist_name = 'Foo', last_name = 'Bar')
        database.people.query(first_name = 'Spam')
        
        -> 3 separate connetions opened and closed.

        with database.people as people:
            people.insert(first_name = 'Foo', last_name = 'Bar')
            people.get(fist_name = 'Foo', last_name = 'Bar')
            people.query(first_name = 'Spam')

        -> 1 connection, changes commited if no exceptions thrown.

    All returned values are 'Namespace objects'.
    They are thin wrappers on the builtin dict - object, so you can
    access the columns with the dotted notation: value = row.column.
    """
    
    def __init__(self, database, name):
        self.database = database
        self.name = name
        self.updated_obj = None
        self.logging = False


    def get_all(self):
        conn = self.database.conn
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql.select(self.name))
            return cursor.fetchall()

        with self.database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql.select(self.name))
            return cursor.fetchall()


    def get(self, **kwargs):
        """
        Perform SELECT - queries. Returns a single row or None if no results.

        database.table.get(name='Dave', hobby='reading')
        
        translates to:
        
        cursor.execute('SELECT * FROM table WHERE name = ?, hobby = ?', ('Dave', 'reading'))
        return cursor.fetchone()
        """
        query = { col: sql.EQ for col in kwargs.keys() }
        
        conn = self.database.conn
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql.select(self.name, **query), tuple(kwargs.values()))
            return cursor.fetchone()

        with self.database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql.select(self.name, **query), tuple(kwargs.values()))
            return cursor.fetchone()


    def query(self, **kwargs):
        """
        Perform SELECT - queries. Returns a list of results.
        Use the .get_all() - method to retieve all rows from a table.

        database.table.query(hobby='reading')
        
        translates to:
        
        cursor.execute('SELECT * FROM table WHERE hobby = ?', ('reading',))
        return cursor.fetchall()
        """
        query = { col: sql.EQ for col in kwargs.keys() }
        
        conn = self.database.conn
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql.select(self.name, **query), tuple(kwargs.values()))
            return cursor.fetchall()

        with self.database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql.select(self.name, **query), tuple(kwargs.values()))
            return cursor.fetchall()


    def delete(self, **kwargs):
        """
        Perform DELETE - actions.

        database.people.delete(hobby='reading')
        
        translates to:
        
        cursor.execute('DELETE FROM people WHERE hobby = ?', ('reading',))
        return cursor.fetchall()

        If no argmuents are provided all rows are deleted.
        """
        query = { col: sql.EQ for col in kwargs.keys() }
        
        conn = self.database.conn
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql.delete(self.name, **query), tuple(kwargs.values()))
            conn.commit()
            return

        with self.database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql.delete(self.name, **query), tuple(kwargs.values()))
            conn.commit()


    def update(self, **kwargs):
        """
        Perform UPDATE - actions. Use the context manager api:

        with database.messages.update(sent=0) as messages:
            messages.sent = 1
        
        translates to:
        
        cursor.execute('UPDATE messages SET sent = ? WHERE sent = ?', (0,))

        The context manager records the changes made to the returned object and
        these changes are made to all items matching the original update keywords.
        """
        return Transaction(self, kwargs)


    def _make_updates(self, restrictions, changes):
        """
        Commit updates made within the context manager.
        Use the context manager api instead of this.
        """
        query = { col: sql.EQ for col in restrictions.keys() }
        columns = tuple(changes.keys())
        params = tuple(list(changes.values()) + list(restrictions.values()))

        conn = self.database.conn
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql.update(self.name, columns, **query), params)
            conn.commit()
            return
        
        with self.database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql.update(self.name, columns, **query), params)
            conn.commit()


    def insert(self, **kwargs):
        """
        Perform INSERT - actions.

        database.users.insert(
            username = 'foobar1',
            email = 'spam@mail.com',
            password_hash = b'some bytes'
        )
        
        translates to:
        
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            ('foobar1', 'spam@mail.com', b'some bytes')
            )
        """
        conn = self.database.conn
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql.insert(self.name, kwargs.keys()), tuple(kwargs.values()))
            conn.commit()
            return
        
        with self.database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql.insert(self.name, kwargs.keys()), tuple(kwargs.values()))
            conn.commit()


class Database:

    def __init__(self, path):
        self.path = path
        self.conn = None
        self.tables = { name: Table(self, name) for name in self.list_tables() }


    def init(self, schema_module):
        """
        Create tables specified inside .py - file.
        The schema_module param must be string in form of 'pkg.module'.

        Like in the .create_table - method, the schema must be a dictionary in the form of:

        table_name = {
            'column_name': sql.datatype(**kwargs),
            'column_name': sql.datatype(**kwargs),
            ...
            }
        
        The schema file is executed with the sql module datatypes injected into the global namespace.
        See the orm.sql module for info on the datatypes.
        """
        schemas = runpy.run_module(schema_module, sql.__namespace__)
        globals_ = globals()
        results = {}
        for key, value in schemas.items():
            if key not in globals_ and key not in sql.__namespace__:
                results[key] = value

        if self.conn:
            for name, schema in results.items():
                self.create_table(name, schema)
        
        else:
            try:
                self.conn = self.connect()
                for name, schema in results.items():
                    self.create_table(name, schema)
            finally:
                self.close_connection()

    
    def store_connection(self):
        if self.conn is None:
            self.conn = self.connect()


    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = row_factory
        return conn


    def create_table(self, name, schema):
        """
        Create a new table.

        Schema must be a dict object in the following format:
        
        {
            'column_name': sql.datatype(**kwargs),
            'column_name': sql.datatype(**kwargs),
            ...
        }

        Raises an error if the table already exists.
        """
        if name in self.tables:
            raise ValueError(f'Table {repr(name)} already exists')
        
        if not sql.valid_schema(schema):
            raise ValueError('Invalid schema')

        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute(sql.create_table(name, **schema))
            self.conn.commit()
        
        else:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(sql.create_table(name, **schema))
                conn.commit()
        
        table = Table(self, name)
        self.tables[name] = table
        return table


    def list_tables(self):
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute(sql.list_tables())
            tables = cursor.fetchall()
        
        else:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(sql.list_tables())
                tables = cursor.fetchall()
        
        return [ row.name for row in tables ]


    def drop_table(self, name):
        if name not in self.tables:
            raise ValueError(f'No such table: "{name}"')

        self.tables.pop(name)

        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute(sql.drop_table(name))
            self.conn.commit()
            return

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql.drop_table(name))
            conn.commit()
        

    def close_connection(self, *args, **kwargs):
        if self.conn:
            self.conn.close()
            self.conn = None


    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            tables = object.__getattribute__(self, 'tables')
            table = tables.get(attr, None)
            if table is None:
                raise AttributeError('No such table')
            return table


class Transaction:
    def __init__(self, table, query):
        object.__setattr__(self, 'table', table)
        object.__setattr__(self, 'query', query)
        object.__setattr__(self, 'changes', dict())
    
    def __getattribute__(self, attr):
        raise AttributeError()

    def __setattr__(self, attr, value):
        changes = object.__getattribute__(self, 'changes')
        changes[attr] = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc is None:
            query = object.__getattribute__(self, 'query')
            changes = object.__getattribute__(self, 'changes')
            table = object.__getattribute__(self, 'table')
            table._make_updates(query, changes)


def row_factory(cursor, row_data):
    result = dict()
    for i, col in enumerate(cursor.description):
        col_name = col[0]
        result[col_name] = row_data[i]
    return Namespace(result)