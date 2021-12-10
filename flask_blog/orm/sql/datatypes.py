from flask_blog.orm.sql import DataType


__all__ = [
    'integer',
    'real',
    'text',
    'blob',
]


def integer(**kwargs) -> DataType:
    return DataType('INTEGER', **kwargs)


def real(**kwargs) -> DataType:
    return DataType('REAL', **kwargs)


def text(**kwargs) -> DataType:
    return DataType('TEXT', **kwargs)


def blob(**kwargs) -> DataType:
    return DataType('BLOB', **kwargs)
