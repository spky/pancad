"""A module providing convenience functions for reading FreeCAD xml files."""
from __future__ import annotations

import dataclasses
from collections import namedtuple
from itertools import islice
from functools import wraps, partialmethod, singledispatch, partial
from typing import TYPE_CHECKING, ClassVar
from math import isclose
import re

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, NoReturn
    from xml.etree.ElementTree import Element, ElementTree

EMPTY_CONSTRAINED = -2000
"""The integer that FreeCAD uses to indicate a sketch constraint reference is 
unused/empty.
"""
GEOMETRY_LIST_INT = 0
"""Integer indicating to look in the Geometry list of a sketch"""
EXTERNAL_GEO_LIST_INT = 1
"""Integer indicating to look in the ExternalGeo list of a sketch"""
LIST_INT_XML_MAP = {
    GEOMETRY_LIST_INT: "Geometry",
    EXTERNAL_GEO_LIST_INT: "ExternalGeo",
}
"""Mapping from a list integer to the name of the list in a sketch's xml."""
LIST_NAME_INT_MAP = {v: k for k, v in LIST_INT_XML_MAP.items()}
"""Mapping from the name of the list in a sketch's xml to a list integer."""

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

def get_map_name(raw_name: str) -> str:
    """Returns the unique part of the name that sometimes identifies what the
    feature is used for. That name can then be used to map the object. For
    example: 'X_Axis001' will return 'X_Axis'
    """
    regex = re.compile(r".*[^0-9](?=[0-9]|$)")
    match = regex.match(raw_name)
    if match is None:
        raise ValueError(f"No mapping name found in '{raw_name}", raw_name)
    return match.group(0)

def read_attr(element: Element, name: str,
              converter: Callable[str, Any]=str) -> Any:
    """Reads an attribute from an element that is expected to always be there.

    :param element: An xml Element.
    :param name: The attribute name.
    :param converter: The function used to convert the string to another type. 
        Defaults to leaving the value as a string.
    :raises ValueError: When the attribute is not on the element.
    """
    try:
        return converter(element.attrib[name])
    except KeyError as exc:
        tag = element.tag
        msg = f"Unexpected {tag} format: could not find '{name}' attribute"
        raise ValueError(msg, element) from exc
    except ValueError as exc:
        tag = element.tag
        value = element.attrib[name]
        func = converter.__name__
        msg = f"Unexpected {tag} format: could not convert {value} with {func}"
        raise ValueError(msg) from exc

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

def read_attrs(element: Element,
               name_map: dict[str, str],
               converter: Callable[str, Any]) -> dict[str, Any]:
    """Reads multiple attributes from an xml element into a internal name 
    mapping dict.

    :param element: An xml element
    :param name_map: A dict of xml attribute names to new internal names.
    :param converter: The function used to convert the attribute strings into 
        other datatypes.
    """
    out = {}
    for attr, name in name_map.items():
        value = read_attr(element, attr)
        try:
            out[name] = converter(value)
        except ValueError as exc:
            tag = element.tag
            msg = (f"Unexpected {tag} format: Could not convert"
                   f" {attr} value '{value}' using {converter.__name__}")
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

read_float_attrs = partial(read_attrs, converter=float)
read_int_attrs = partial(read_attrs, converter=int)
read_bool_attrs = partial(read_attrs, converter=read_bool)

def read_vector(element: Element,
                names: tuple[str, str, str] | tuple[str, str, str, str],
                prefix: str=None,
                is_2d: bool=True,
                ) -> (tuple[float, float]
                      | tuple[float, float, float]
                      | tuple[float, float, float, float]):
    """Reads a geometry vector tuple of floats from the xml element.

    :param element: An xml element with point data.
    :param names: The attribute names of the point in the order you want.
                  An example order would be x, y, z.
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

@dataclasses.dataclass(frozen=True)
class DocumentUidInfo:
    """Class for keeping track of document info inside a uid string.

    :param file_uid: The uuid generated by FreeCAD for the file.
    :param type_: The uid type. For documents it's 'document'
    """
    file_uid: str
    type_: str

@dataclasses.dataclass(frozen=True)
class FeatureUidInfo:
    """Class for keeping track of feature info inside a uid string.

    :param file_uid: The uuid generated by FreeCAD for a file.
    :param type_: The uid type. For features it's 'feature'
    :param feature_id: The unique int generated by freecad for the feature.
    """
    file_uid: str
    type_: str
    feature_id: int

@dataclasses.dataclass(frozen=True)
class SketchGeometryUidInfo:
    """Class for keeping track of geometry in inside a uid string.

    :param file_uid: The uuid generated by FreeCAD for a file.
    :param type_: The uid type. For sketch geometry it's 'sketchgeo'
    :param feature_id: The unique int generated by freecad for the feature the 
        geometry is inside of, usually a sketch.
    :param list_: The integer for the list (0 for Geometry, 1 for ExternalGeo).
    :param geometry_id: The integer generated by the FreeCAD sketch for this 
        geometry element in its list.
    """
    file_uid: str
    type_: str
    feature_id: int
    list_: int
    geometry_id: int

    @property
    def list_name(self) -> str:
        """The name of the sketch list the geometry is in."""
        return LIST_INT_XML_MAP[self.list_]

    @property
    def sketch_uid(self) -> FreeCADUID:
        """The uid of the FreeCAD sketch the geometry is in"""
        sketch_parts = [self.file_uid, "feature", str(self.feature_id)]
        return FreeCADUID(FreeCADUID.delim.join(sketch_parts))

SketchGeometryReference = namedtuple("SketchGeometryReference",
                                     ["list_int", "id_", "part"])

@dataclasses.dataclass(frozen=True)
class SketchConstraintUidInfo:
    """Class for keeping track of constraint info inside a uid string.

    :param file_uid: The uuid generated by FreeCAD for a file.
    :param type_: The uid type. For sketch constraints it's 'sketchcons'
    :param feature_id: The unique int generated by freecad for the feature the 
        geometry is inside of, usually a sketch.
    :param constraint_type: The integer corresponding to the constraint type.
    :param first: The first geometry reference.
    :param second: The second geometry reference.
    :param third: The third geometry reference.
    """
    file_uid: str
    type_: str
    feature_id: int
    constraint_type: int
    first: SketchGeometryReference
    second: SketchGeometryReference
    third: SketchGeometryReference

    list_name: ClassVar[str] = "Constraints"

    @classmethod
    def from_parts(cls,
                   file_uid: str,
                   type_: str,
                   feature_id: int,
                   constraint_type: int,
                   *parts: list[int]):
        """Returns a SketchConstraintUidInfo from a series of integer parts.

        :param file_uid: The uuid generated by FreeCAD for a file.
        :param type_: The uid type. For sketch constraints it's 'sketchcons'
        :param feature_id: The unique int generated by freecad for the feature the 
            geometry is inside of, usually a sketch.
        :param constraint_type: The integer corresponding to the constraint type.
        :param parts: 3 batches of 3 integer parts structured as (list int, 
            geometry id, geometry position).
        """
        parts_iter = iter(parts)
        batch_n = 3
        references = []
        while batch := tuple(islice(parts_iter, batch_n)):
            if len(batch) != batch_n:
                msg = ("incomplete batch of parts,"
                       f" expected {batch_n}, got: {batch}")
                raise ValueError(msg, parts)
            references.append(SketchGeometryReference(*batch))
        if (no_references := len(references)) != 3:
            msg = f"Expected 3 sets of references, got {no_references}"
            raise TypeError(msg, references)
        return cls(file_uid, type_, feature_id, constraint_type,
                   references[0], references[1], references[2])

    @property
    def references(self) -> list[SketchGeometryReference]:
        """Returns a list of the geometry references used by the constraint."""
        return [self.first, self.second, self.third]

    @property
    def reference_map(self) -> dict[str, SketchGeometryReference]:
        """Returns a dict of the freecad names to the geometry references used by 
        the constraint.
        """
        return {"First": self.first, "Second": self.second, "Third": self.third}

    @property
    def sketch_uid(self) -> FreeCADUID:
        """The uid of the FreeCAD sketch the constraint is in"""
        sketch_parts = [self.file_uid, "feature", str(self.feature_id)]
        return FreeCADUID(FreeCADUID.delim.join(sketch_parts))

class FreeCADUID(str):
    """A class to make it easy to access freecad uid information from their 
    strings. All attributes of this class should stay constant after 
    initialization.

    :raises ValueError: When the number/type of uid parts are invalid for the uid 
        type.
    """
    delim = "_"
    """Delimiter between information parts in the uid."""
    _type_info_types = {
        "document": DocumentUidInfo,
        "feature": FeatureUidInfo,
        "sketchgeo": SketchGeometryUidInfo,
        "sketchcons": SketchConstraintUidInfo.from_parts,
    }
    """Mapping from type names to their namedtuple types."""

    def __new__(cls, string: str) -> FreeCADUID:
        new = super().__new__(cls, string)
        parts = string.split(cls.delim)
        try:
            new._file_uid, new._type, *parts = parts
        except ValueError as exc:
            exc.add_note("Invalid number of parts for any available uid types")
            raise
        try:
            for i, part in enumerate(parts):
                parts[i] = int(part)
        except ValueError as exc:
            exc.add_note("Could not convert all parts into ints")
            raise
        try:
            new._data = cls._type_info_types[new._type](new.file_uid, new._type,
                                                       *parts)
        except KeyError as exc:
            raise ValueError("Invalid uid type", exc.args[0]) from exc
        return new

    @property
    def file_uid(self) -> str:
        """The uid of the file that the FreeCAD object is inside of. Common to 
        all FreeCAD uids.
        """
        return self._file_uid

    @property
    def type_(self) -> str:
        """The type of FreeCAD object this uid is for. Common to all FreeCAD 
        uids.
        """
        return self._type

    @property
    def data(self) -> NamedTuple:
        """The data represented inside the string of the uid."""
        return self._data
