"""
A simple 'ORM' implemented ontop of Python's builtin sqlite3 library.

This module generates sql from Python objects.
The SQL generated is always in the form of parameterized queries.

This module only supports very basic CRUD operations.

Author: Valtteri Rajalainen
"""

import io
import re
import typing


NAME_LENGTH = 32
NAME_RE = r'[a-zA-Z][a-zA-Z0-9_]+[a-zA-Z0-9]*'
DECIMAL_RE = r'[0-9]+(\.[0-9]+)?'
SQLITE_PREFIX = 'sqlite'

EQ = '='

OPERATORS = (
    EQ,
    )


__namespace__ = dict()

def export(func: typing.Callable) -> typing.Callable:
    __namespace__[func.__name__] = func
    return func


def valid_name(name: str) -> bool:
    if len(name) > NAME_LENGTH:
        return False
    if name.startswith(SQLITE_PREFIX):
        return False
    return re.fullmatch(re.compile(NAME_RE), name) is not None

def is_decimal(string: str) -> bool:
    return re.fullmatch(re.compile(DECIMAL_RE), string) is not None


class DataType:
    def __init__(self, value, *,
        unique=False,
        primary_key=False,
        auto_increment=False,
        not_null=False,
        foreign_key=None,
        default=None
        ):
        
        if not valid_name(value):
            raise ValueError('Invalid value for a DataType object')
        
        self.value = value
        self.unique = unique
        self.primary_key = primary_key
        self.auto_increment = auto_increment
        self.foreign_key = foreign_key
        self.not_null = not_null
        self.default = default


    def resolve(self) -> str:
        """
        Generate the actual SQL for this datatype.
        No checks are made for validating the combinations of the modifiers.

        When creating a schema the column with the foreign_key - modifier must be the last column.
        """
        stream = io.StringIO()
        stream.write(self.value)

        if self.primary_key:
            stream.write(' PRIMARY KEY')
        
        if self.auto_increment:
            stream.write(' AUTOINCREMENT')

        if self.unique:
            stream.write(' UNIQUE')

        if self.not_null:
            stream.write(' NOT NULL')

        if self.default is not None:
            valid_types = (str, int, float)
            if type(self.default) not in valid_types:
                raise TypeError('Invalid type. Excpected int, float or str.')
            
            value = str(self.default)
            if not is_decimal(value) and not valid_name(value):
                raise ValueError(f'Possibly harmful value: {value}')
            
            stream.write(f' DEFAULT {value}')

        if self.foreign_key:
            col, table, table_col = self.foreign_key
            if not all((valid_name(name) for name in (col, table, table_col))):
                raise ValueError('Invalid name')
            
            stream.write(', ')
            stream.write(f'FOREIGN KEY({col}) REFERENCES {table}({table_col})')
        
        stream.seek(0)
        sql = stream.read()
        return sql


@export
def integer(**kwargs) -> DataType:
    return DataType('INTEGER', **kwargs)

@export
def real(**kwargs) -> DataType:
    return DataType('REAL', **kwargs)

@export
def text(**kwargs) -> DataType:
    return DataType('TEXT', **kwargs)

@export
def blob(**kwargs) -> DataType:
    return DataType('BLOB', **kwargs)


def valid_schema(schema: typing.Dict[str, typing.Any]):
    if not isinstance(schema, dict):
        return False
    valid_types = [ isinstance(item, DataType) for item in schema.values() ]
    valid_names = [ valid_name(item) for item in schema.keys() ]
    return all(valid_types) and all(valid_names)


def valid_query(query: typing.Dict[str, typing.Any]) -> bool:
    return all((valid_name(name) for name in query.keys()))


def create_table(name_: str, **schema) -> str:
    if not valid_name(name_):
        raise ValueError('Invalid table name')

    if not valid_schema(schema):
        raise ValueError('Invalid table schema')
    
    stream = io.StringIO()
    columns = list(schema.keys())
    i = 0
    stream.write(f'CREATE TABLE {name_} ')
    stream.write('(')
    for col, attr in schema.items():
        stream.write(col)
        stream.write(' ')
        stream.write(attr.resolve())
        if i + 1 < len(columns):
            stream.write(', ')
        i += 1
    stream.write(')')
    
    stream.seek(0)
    sql = stream.read()
    stream.close()

    return sql


def drop_table(name_):
    if not valid_name(name_):
        raise ValueError('Invalid table name')

    sql = f'DROP TABLE {name_}'
    return sql


def insert(table: str, columns: typing.List[str]) -> str:
    if not valid_name(table):
        raise ValueError('Invalid table name')
    
    if not all([ valid_name(col) for col in columns ]):
        raise ValueError('Invalid column name')
    
    stream = io.StringIO()
    stream.write(f'INSERT INTO {table} (')
    for i, col in enumerate(columns):
        stream.write(col)
        if i + 1 < len(columns):
            stream.write(', ')
    stream.write(')')

    stream.write(' VALUES ')

    stream.write('(')
    for i in range(len(columns)):
        stream.write('?')
        if i + 1 < len(columns):
            stream.write(', ')
    stream.write(')')

    stream.seek(0)
    sql = stream.read()
    stream.close()
    return sql


def select(table: str, columns: typing.Optional[typing.List[str]] = None, **kwargs) -> str:
    if not valid_name(table):
        raise ValueError('Invalid table name')
    
    if columns and not all([ valid_name(col) for col in columns ]):
        raise ValueError('Invalid column name')
    
    if not valid_query(kwargs):
        raise ValueError('Invalid query')
    
    stream = io.StringIO()
    columns_str = '*' if columns is None else '(' + ', '.join(columns) + ')'
    stream.write(f'SELECT {columns_str} FROM {table}')

    if kwargs:
        stream.write(' WHERE')
        keys = list(kwargs.keys())
        for i, key in enumerate(keys):
            operator = kwargs[key]
            if operator not in OPERATORS:
                stream.close()
                raise ValueError('Invalid operator')
            
            stream.write(f' {key} {operator} ?')
            if i + 1 < len(keys):
                stream.write(' AND')

    stream.seek(0)
    sql = stream.read()
    stream.close()
    return sql


def update(table: str, columns: typing.List[str], **kwargs) -> str:
    if not valid_name(table):
        raise ValueError('Invalid table name')
    
    if columns and not all([ valid_name(col) for col in columns ]):
        raise ValueError('Invalid column name')

    if not valid_query(kwargs):
        raise ValueError('Invalid query')
    

    stream = io.StringIO()
    stream.write(f'UPDATE {table} SET')

    for i, column in enumerate(columns):
        stream.write(f' {column} = ?')
        if i + 1 < len(columns):
            stream.write(',')

    if kwargs:
        keys = list(kwargs.keys())
        stream.write(' WHERE')
        for i, key in enumerate(keys):
            operator = kwargs[key]
            if operator not in OPERATORS:
                stream.close()
                raise ValueError('Invalid operator')
            
            stream.write(f' {key} {operator} ?')
            if i + 1 < len(keys):
                stream.write(' AND')

    stream.seek(0)
    sql = stream.read()
    stream.close()
    return sql


def delete(table: str, **kwargs) -> str:
    if not valid_name(table):
        raise ValueError('Invalid table name')

    if not valid_query(kwargs):
        raise ValueError('Invalid query')
    
    stream = io.StringIO()
    stream.write(f'DELETE FROM {table}')

    if kwargs:
        stream.write(' WHERE')
        keys = list(kwargs.keys())
        for i, key in enumerate(keys):
            operator = kwargs[key]
            if operator not in OPERATORS:
                stream.close()
                raise ValueError('Invalid operator')
            
            stream.write(f' {key} {operator} ?')
            if i + 1 < len(keys):
                stream.write(' AND')

    stream.seek(0)
    sql = stream.read()
    stream.close()
    return sql


def list_tables() -> str:
    return 'SELECT name FROM sqlite_master WHERE type = \'table\' AND name NOT LIKE \'sqlite%\';'