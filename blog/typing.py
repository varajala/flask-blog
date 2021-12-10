import flask.typing as flask_types
from blog.orm import Table, Database

from types import ModuleType
from typing import (
    List,
    Dict,
    Tuple,
    Callable,
    Any,
    
    Union, 
    Optional,
    Generic,
    NewType,
    
    TYPE_CHECKING,
    cast,
)


Response = flask_types.ResponseValue
ViewFunction = Union[Callable[[], Response], Callable[[Any], Response]]

Module = ModuleType

DatabaseTable = Table
DatabaseObject = Database
