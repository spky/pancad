"""A module providing convenience functions for reading FreeCAD xml files."""
from __future__ import annotations

from functools import wraps, partialmethod, singledispatch
from typing import TYPE_CHECKING
from math import isclose

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, NoReturn
    from xml.etree.ElementTree import Element, ElementTree

@singledispatch
def check_constant(value: float | int, expected: float | int) -> None:
    """Checks that the read in xml value matches the expected constant value. 
    The intended goal is to check if this does not match to provide a warning 
    for when pancad's implementation of the xml file is missing functionality.

    :param value: The as-read value.
    :param expected: The expected value.
    :raises ValueError: When the value does not match.
    """
    if not isclose(value, expected):
        msg = f"Unexpected value: got {value} expected {expected}"
        raise ValueError(msg, value)

@check_constant.register
def _check_vector(value: tuple, expected: tuple) -> None:
    if not np.allclose(value, expected):
        msg = f"Unexpected value: got {value} expected {expected}"
        raise ValueError(msg, value)

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

    :param context: An xml Element or ElementTree.
    :param xpath: An xpath search string.
    :raises LookupError: When no element was found at the xpath.
    """
    element = context.find(xpath)
    if element is None:
        raise LookupError("No element was found using the xpath", xpath)
    return element

def read_float_attrs(element: Element, name_map: dict[str, str] | list[str]
                     ) -> dict[str, float]:
    """Reads multiple float attributes from an xml element into a dict.

    :param element: An xml element.
    :param name_map: A dict of xml attribute names to new internal names.
    :returns: A dict of new internal names to the float values.
    :raises ValueError: When one of the attributes cannot be converted to float.
    """
    out = {}
    for attr, name in name_map.items():
        value = read_attr(element, attr)
        try:
            out[name] = float(value)
        except ValueError as exc:
            tag = element.tag
            msg = (f"Unexpected {tag} format:"
                   f" Could not convert {attr} value '{value}' to float")
            raise ValueError(msg, element) from exc
    return out

def read_float_attr_list(element: Element, names: list[str]) -> list[float]:
    """A wrapper function for read_float_attrs to take a list of attribute names 
    and just return the values of those names in the same order as a list. The 
    goal is to make sure that all float reading happens in the same function.
    """
    name_map = {n: n for n in names}
    return list(read_float_attrs(element, name_map).values())

def read_bool(string: str) -> bool:
    """Converts a boolean string value read from xml into a bool"""
    return string.lower() in ["true", "1"]

def read_vector(element: Element,
                names: tuple[str, str, str],
                prefix: str=None,
                is_2d: bool=True,
                ) -> tuple[float, float] | tuple[float, float, float]:
    """Reads a geometry vector tuple of floats from the xml element.

    :param element: An xml element with point data.
    :param names: The attribute names of the point in the order x, y, z.
    :param prefix: When give, this prefix is added to each of the names.
    :param is_2d: Sets whether to drop the Z component of the point. Defaults to 
        True.
    :raises ValueError: When is_2d is True and the Z component is non-zero.
    """
    if prefix is not None:
        names = tuple(prefix + c for c in names)
    components = read_float_attr_list(element, names)
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
