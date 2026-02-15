"""A module providing convenience functions for reading FreeCAD xml files."""
from __future__ import annotations

from functools import wraps, partialmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, NoReturn
    from xml.etree.ElementTree import Element, ElementTree

def read_bool(string: str) -> bool:
    """Converts a boolean string value into a bool"""
    return string.lower() == "true"

def convert_str(func: Callable[..., str], converter: Callable[str, Any]):
    """A wrapper function to convert property string outputs to another type
    using the converter function.

    :param func: The function to wrapper
    :param converter: A function that takes a string and outputs some other
        data type.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if isinstance(func, partialmethod):
            # Handle cases with partialmethods - without using
            # make_unbound_method the partialmethod raises a TypeError saying
            # it's not callable
            return converter(func._make_unbound_method()(*args, **kwargs))
        return converter(func(*args, **kwargs))
    return wrapper
