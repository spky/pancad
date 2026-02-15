"""A module providing convenience functions for reading FreeCAD xml files."""
from __future__ import annotations

from functools import wraps, partialmethod
from typing import TYPE_CHECKING
from math import isclose

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, NoReturn
    from xml.etree.ElementTree import Element, ElementTree

def read_attr(element: Element, name: str) -> str:
    """Reads an attribute from an element that is expected to always be there.

    :raises ValueError: When the attribute is not on the element.
    """
    try:
        return element.attrib[name]
    except KeyError as exc:
        tag = element.tag
        msg = f"Unexpected {tag} format, could not find '{name}' attribute"
        raise ValueError(msg, element) from exc

def find_single(context: Element | ElementTree, xpath: str) -> Element:
    """Reads an element from an xpath that is always expected to be there.

    :raises LookupError: When no element was found at the xpath.
    """
    element = context.find(xpath)
    if element is None:
        raise LookupError("No element was found using the xpath", xpath)
    return element

def read_bool(string: str) -> bool:
    """Converts a boolean string value read from xml into a bool"""
    return string.lower() in ["true", "1"]

def read_vector(element: Element, names: tuple[str, str, str], is_2d: bool=True
                ) -> tuple[float, float] | tuple[float, float, float]:
    """Reads a geometry vector tuple of floats from the xml element.

    :param element: An xml element with point data.
    :param names: The attribute names of the point in the order x, y, z.
    :param is_2d: Sets whether to drop the Z component of the point. Defaults to 
        True.
    :raises ValueError: When is_2d is True and the Z component is non-zero.
    """
    components = []
    for attr in names:
        components.append(float(read_attr(element, attr)))
    if is_2d:
        if not isclose(components[-1], 0):
            attr_names = ", ".join(map(lambda x: f"'{x}'", names))
            msg = f"Unexpected non-zero Z for vector with attrs: {attr_names}"
            raise ValueError(msg, element)
        del components[-1]
    return tuple(components)

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
