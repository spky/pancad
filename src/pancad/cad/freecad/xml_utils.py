"""A module providing convenience functions for reading FreeCAD xml files."""
from __future__ import annotations

import dataclasses
from collections import namedtuple
from itertools import islice
from functools import singledispatch, partial
from typing import TYPE_CHECKING, ClassVar, Literal
from math import isclose
import re

import numpy as np

from pancad.cad.freecad.constants import (ConstraintSubPart as CSP,
                                          ConstraintType,
                                          InternalGeometryType)
from pancad.utils.trigonometry import is_clockwise

if TYPE_CHECKING:
    from typing import NamedTuple
    from collections.abc import Callable
    from typing import Any, NoReturn
    from xml.etree.ElementTree import Element, ElementTree

    import quaternion

    from pancad.cad.freecad.read_xml import FreeCADGeometryXML, FreeCADConstraintXML

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


VectorPair = tuple[tuple[float, float], tuple[float, float]]
def read_angle_quadrant(refs: tuple[tuple[VectorPair, CSP],
                                    tuple[VectorPair, CSP]]
                        ) -> Literal[1, 2, 3, 4]:
    """Returns an angle constraint's quadrant number. pancad quadrant numbers
    are relative to the first line and independent of the second line's
    direction.
    """
    (segment_1, pos_1), (segment_2, pos_2) = refs
    vectors = [np.array(s[1]) - np.array(s[0]) for s in (segment_2, segment_1)]
    key = (pos_1, pos_2, is_clockwise(*vectors))
    quadrant_map = {
        # Second Line's direction is counter-clockwise from the First's
        (CSP.START, CSP.START, False): 1,
        (CSP.START, CSP.END, False): 2,
        (CSP.END, CSP.START, False): 3,
        (CSP.END, CSP.END, False): 4,
        # Second Line's direction is clockwise from the First's
        (CSP.START, CSP.END, True): 1,
        (CSP.END, CSP.END, True): 2,
        (CSP.END, CSP.START, True): 3,
        (CSP.START, CSP.START, True): 4,
    }
    try:
        return quadrant_map[key]
    except KeyError as exc:
        msg = f"Unexpected subparts in angle constraint combo: {key}"
        raise ValueError(msg) from exc

################################################################################
# FreeCAD pancad Assigned UID Definition
################################################################################

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
"""A tuple of integers defining which list, what id, and what sub part a
constraint it referring to.

:param list_int: Integer for the list the geometry appears in. 0 for Geometry, 1
    for ExternalGeo.
:param id_: The integer id assigned to the sketch geometry by FreeCAD.
:param part: The integer reference to the subpart of the geometry being
    constrained.
"""

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

    @classmethod
    def from_parts(cls, *parts: str | int) -> FreeCADUID:
        """Creates a FreeCADUID from base string parts."""
        return cls(cls.delim.join(map(str, parts)))

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

@dataclasses.dataclass
class FCMetadata:
    """Dataclass tracking metadata that is available on all FreeCAD files.

    :param label: The name of the file.
    :param uid: The internally generated unique id for the file.
    :param unit_system: The units for the file's dimensions.
    :param last_modified_date: The date the file was modified last.
    :param user_id: The id for the file entered by the designer.
    """
    label: str
    uid: str
    unit_system: str
    last_modified_date: str
    user_id: str

@dataclasses.dataclass(frozen=True)
class FreeCADLink:
    """A class for tracking FreeCAD App::PropertyLinkSub data. See
    https://freecad.github.io/SourceDoc/d3/d76/classApp_1_1PropertyLinkSub.html

    :param name: The object the link is to.
    :param subs: The linked subelement name of the object. Empty strings are
        converted to None.
    :param shadows: Not certain, but appears to be "shadow subname references"
        in FreeCAD documentation. Likely connected to topological naming.
    :raises ValueError: Raised if sub is an empty string or when sub is None but
        shadow is not None.
    """
    name: str
    sub: str = None
    shadow: str = None

    def __post_init__(self):
        if self.sub == "":
            # Blank sub strings indicate the link is just to the object.
            # Blank subs cannot be converted to None here without unfreezing the
            # dataclass, so it just raises an error.
            raise ValueError("sub cannot be an empty string")
        if self.sub is None and self.shadow is not None:
            raise ValueError("Unexpected LinkSub format: sub is None,"
                             f" but shadow is '{self.shadow}'")

@dataclasses.dataclass
class FreeCADExpression:
    """Dataclass for tracking the definition of FreeCAD expressions that define
    derived properties in the model.
    """
    path: str
    expression: str

@dataclasses.dataclass
class FreeCADPlacement:
    """Dataclass tracking a FreeCAD Placement object's properties from FCStd xml
    """
    location: tuple[float, float, float]
    quat: quaternion.quaternion
    o_vector: tuple[float, float, float]

    @classmethod
    def from_element(cls, element: Element) -> FreeCADPlacement:
        """Creates Placement directly from an xml element"""
        xyz = ["x", "y", "z"]
        location = read_vector(element, xyz, "P", False)
        o_vector = read_vector(element, xyz, "O", False)
        quat_vector = read_vector(element, ["Q0", "Q1", "Q2", "Q3"], is_2d=False)
        return cls(location, np.quaternion(*quat_vector), o_vector)

@dataclasses.dataclass
class PropertyPartShape:
    """Dataclass for tracking the definition of FreeCAD PropertyPartShape
    elements
    """
    element_map: str
    brp: str
    txt: str = None
    hash_index: int = None
    elements: list[tuple[str, str]] = dataclasses.field(default_factory=list)

    @classmethod
    def from_element(cls, element: Element) -> PropertyPartShape:
        """Creates PropertyPartShape directly from an xml element"""
        inputs = {}
        part = find_single(element, "Part")
        inputs["element_map"] = read_attr(part, "ElementMap")
        inputs["brp"] = read_attr(part, "file")
        if part.get("HasherIndex") is not None:
            inputs["hash_index"] = read_attr(part, "HasherIndex", int)
        for sub in find_single(element, "ElementMap"):
            values = []
            for name in ("key", "value"):
                value = read_attr(sub, name)
                if value != "Dummy": # Have not found any non-Dummy cases so far
                    msg = ("Expected 'Dummy' for ElementMap element"
                           f" value {name}, got {value}")
                    raise ValueError(msg)
                values.append(value)
            inputs.setdefault("elements", []).append(tuple(values))
        ele_map_2 = element.find("ElementMap2")
        if ele_map_2 is not None:
            inputs["txt"] = read_attr(ele_map_2, "file")
        return cls(**inputs)

@dataclasses.dataclass
class GeomData:
    """Dataclass for tracking data common to all FreeCAD Geometry."""
    parent: FreeCADGeometryXML = dataclasses.field(repr=False)
    type_: str = dataclasses.field(repr=False)
    tag: str

@dataclasses.dataclass
class GeomPoint(GeomData):
    """Dataclass for tracking FreeCAD Sketch Point info."""
    location: tuple[float, float]

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomPoint:
        """Returns a GeomPoint from a GeomPoint xml element."""
        point = read_vector(element, ("X", "Y", "Z"))
        return cls(parent, parent.type_, element.tag, point)

@dataclasses.dataclass
class GeomLineSegment(GeomData):
    """Dataclass for tracking FreeCAD Sketch Line Segment info."""
    start: tuple[float, float]
    end: tuple[float, float]

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomLineSegment:
        """Returns a GeomLineSegment from a LineSegment xml element."""
        xyz = ("X", "Y", "Z")
        point_to_input_name = [("Start", "start"), ("End", "end")]
        points = {}
        for point, input_name in point_to_input_name:
            try:
                points[input_name] = read_vector(element, xyz, point)
            except ValueError as exc:
                exc.add_note(f"Occurred on LineSegment {point} point")
                raise
        return cls(parent, parent.type_, element.tag, **points)

@dataclasses.dataclass
class GeomCircle(GeomData):
    """Dataclass for tracking FreeCAD Sketch Circle info."""
    center: tuple[float, float]
    radius: float

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomCircle:
        """Returns a GeomCircle from a Circle xml element."""
        xyz = ("X", "Y", "Z")
        center = read_vector(element, xyz, "Center")
        normal = read_vector(element, xyz, "Normal", False)
        attrs = read_float_attrs(element, {"AngleXU": "angle", "Radius": "radius"})
        extras = [(normal, (0, 0, 1), "Normal"), (attrs["angle"], 0, "AngleXU")]
        for value, expected, extra_name in extras:
            try:
                check_constant(value, expected)
            except ValueError as exc:
                exc.add_note(f"Occurred on Circle {extra_name}")
                raise
        return cls(parent, parent.type_, element.tag, center, attrs["radius"])

@dataclasses.dataclass
class GeomEllipse(GeomData):
    """Dataclass for tracking FreeCAD Sketch Ellipse info."""
    center: tuple[float, float]
    major_radius: float
    minor_radius: float
    major_axis_angle: float

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomEllipse:
        """Returns a GeomEllipse from a Ellipse xml element."""
        xyz = ("X", "Y", "Z")
        center = read_vector(element, xyz, "Center")
        normal = read_vector(element, xyz, "Normal", False)
        try:
            check_constant(normal, (0, 0, 1))
        except ValueError as exc:
            exc.add_note("Occurred on Ellipse Normal")
            raise
        attrs = read_float_attrs(
            element,
            {
                "MajorRadius": "major_radius",
                "MinorRadius": "minor_radius",
                "AngleXU": "major_axis_angle",
            }
        )
        return cls(parent, parent.type_, element.tag, center, **attrs)

@dataclasses.dataclass
class GeomArcOfCircle(GeomData):
    """Dataclass for tracking FreeCAD Sketch Ellipse info."""
    center: tuple[float, float]
    radius: float
    start_angle: float
    end_angle: float

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomArcOfCircle:
        """Returns a GeomArcOfCircle from a ArcOfCircle xml element."""
        xyz = ("X", "Y", "Z")
        center = read_vector(element, xyz, "Center")
        normal = read_vector(element, xyz, "Normal", False)
        attrs = read_float_attrs(
            element,
            {
                "Radius": "radius",
                "StartAngle": "start_angle",
                "EndAngle": "end_angle",
                "AngleXU": "angle",
            }
        )
        extras = [(normal, (0, 0, 1), "Normal"), (attrs["angle"], 0, "AngleXU")]
        for value, expected, extra_name in extras:
            try:
                check_constant(value, expected)
            except ValueError as exc:
                exc.add_note(f"Occurred on ArcOfCircle {extra_name}")
                raise
        del attrs["angle"]
        return cls(parent, parent.type_, element.tag, center, **attrs)

@dataclasses.dataclass
class GeometryExtension:
    """A dataclass for tracking all FreeCAD GeometryExtensions."""
    geometry: FreeCADGeometryXML
    type_: str

@dataclasses.dataclass
class SketchGeoExt(GeometryExtension):
    """A dataclass tracking Sketcher::SketchGeometryExtension values."""
    id_: int
    internal_geometry_type: int
    geometry_mode_flags: int
    geometry_layer: int

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> SketchGeoExt:
        """Returns a SketchGeoExt from a GeoExtension xml element typed as a
        Sketch Extension.
        """
        type_ = read_attr(element, "type")
        attr_map = [
            ("id", int, "id_"),
            ("internalGeometryType", int, "internal_geometry_type"),
            ("geometryModeFlags", lambda x: int(x, base=2), "geometry_mode_flags"),
            ("geometryLayer", int, "geometry_layer")
        ]
        attrs = {}
        for name, func, input_name in attr_map:
            try:
                attrs[input_name] = func(read_attr(element, name))
            except ValueError as exc:
                exc.add_note(f"Exception occurred on GeoExtension type {type_}")
                raise
        try:
            intern_type = attrs["internal_geometry_type"]
            attrs["internal_geometry_type"] = InternalGeometryType(intern_type)
        except ValueError as exc:
            msg = f"Unsupported internalGeometryType value: {intern_type}"
            raise NotImplementedError(msg) from exc
        return cls(parent, type_, **attrs)

@dataclasses.dataclass
class InternalAlignment:
    """Dataclass for tracking how a constraint is used for interally aligning
    geometry like Ellipse subgeometry.
    """
    type_: InternalGeometryType
    index: int

@dataclasses.dataclass
class ConstraintState:
    """Dataclass for tracking the sketch-specific state data of a FreeCAD
    constraint.
    """
    label_distance: float
    label_position: float
    driving: bool
    virtual_space: bool
    active: bool

@dataclasses.dataclass
class ConstraintPairs:
    """Class tracking the three pairs of ConstraintGeoRef integers in FreeCAD
    constraints.
    """
    first: ConstraintGeoRef
    second: ConstraintGeoRef
    third: ConstraintGeoRef

    def get_geometry(self) -> list[tuple[FreeCADGeometryXML, CSP]]:
        """Returns a list of the filled geometry references, tuples of
        (geometry, subpart).
        """
        references = []
        for pair in [self.first, self.second, self.third]:
            if pair.list_index is not None:
                references.append(pair.get_geometry())
        return references

    def as_list(self) -> list[ConstraintGeoRef]:
        """Returns the non-empty geometry references in a list."""
        return  [r for r in [self.first, self.second, self.third]
                 if r.id_ is not None]

@dataclasses.dataclass
class ConstraintData:
    """A dataclass tracking all xml data stored for a FreeCAD sketch
    constraint.
    """
    parent: FreeCADConstraintXML = dataclasses.field(repr=False)
    name: str | None
    type_: ConstraintType
    value: float
    pairs: ConstraintPairs
    state: ConstraintState
    internal_alignment: InternalAlignment = None

    @classmethod
    def from_element(cls, parent: FreeCADConstraintXML, element: Element
                     ) -> ConstraintData:
        """Returns a ConstraintData dataclass from a Constrain xml element."""
        name = read_attr(element, "Name")
        if name == "":
            name = None
        attrs = cls._read_element_data(element)
        # Consolidate the data into smaller structures
        state_attrs = ["label_distance", "label_position",
                       "driving", "virtual_space", "active"]
        state = ConstraintState(**{a: attrs[a] for a in state_attrs})
        attrs = {k: v for k, v in attrs.items() if k not in state_attrs}
        pairs = {}
        pair_nums =["First", "Second", "Third"]
        for num, pos in zip(pair_nums, map(lambda x: f"{x}Pos", pair_nums)):
            pairs[num.lower()] = ConstraintGeoRef(attrs[num],
                                                  CSP(attrs[pos]),
                                                  parent)
            del attrs[num], attrs[pos]
        pairs = ConstraintPairs(**pairs)
        return cls(parent, name, pairs=pairs, state=state, **attrs)

    @staticmethod
    def _read_element_data(element: Element) -> dict[str, float | int | bool]:
        # Get always there attributes first
        floats = {"Value": "value",
                  "LabelDistance": "label_distance",
                  "LabelPosition": "label_position"}
        bools = {"IsDriving": "driving",
                 "IsInVirtualSpace": "virtual_space",
                 "IsActive": "active"}
        ints = {"Type": "type_"} # Actually an int enumeration for the type
        numbers =["First", "Second", "Third"]
        for num in numbers:
            ints.update({num: num, f"{num}Pos": f"{num}Pos"})
        converts =[(floats, float), (bools, read_bool), (ints, int)]
        attrs = {}
        for names, converter in converts:
            try:
                attrs.update(read_attrs(element, names, converter))
            except ValueError as exc:
                exc.add_note("Occurred while reading ConstraintData")
                raise
        # Get the sometimes there attributes
        internal_names = {"InternalAlignmentType": "type_",
                          "InternalAlignmentIndex": "index"}
        if any(name in element.attrib for name in internal_names):
            align_data = read_int_attrs(element, internal_names)
            try:
                align_data["type_"] = InternalGeometryType(align_data["type_"])
            except ValueError as exc:
                exc.add_note("Unrecognized internal alignment type number"
                             f" {align_data['type_']}")
                raise
            attrs["internal_alignment"] = InternalAlignment(**align_data)
        try:
            attrs["type_"] = ConstraintType(attrs["type_"])
        except ValueError as exc:
            exc.add_note(f"Unrecognized type number {attrs['type_']}")
            raise
        return attrs

@dataclasses.dataclass
class ConstraintGeoRef:
    """A dataclass tracking the index and subpart of a FreeCAD constraint's
    reference to geometry.

    :param index: The index of the geometry as entered in the constraint xml.
        Negative numbers are in the ExternalGeo list.
    :param part: The sub part integer for the part of the geometry being
        constrained.
    :param id_: The integer id of the geometry.
    :param constraint:
    """
    index: int
    part: CSP
    constraint: FreeCADConstraintXML
    id_: int | None = dataclasses.field(init=False)
    list_name: str | None = dataclasses.field(init=False)

    def __post_init__(self):
        if self.index == -2000:
            self.list_name = None
        elif self.index < 0:
            self.list_name = "ExternalGeo"
        else:
            self.list_name = "Geometry"
        geo = self._get_geometry_by_index()
        if geo is None:
            self.id_ = None
        else:
            self.id_ = geo.id_

    @property
    def list_index(self) -> int | None:
        """The index of the geometry inside the list it resides in. Updates
        dynamically if the list changes. This is None when the reference is
        empty and just to fill out the 3 required for FreeCAD constraints.

        :raises LookupError: When the geometry id cannot be found in the sketch
            list. This would mean there's unexpected FreeCAD behavior or that
            the geometry has been deleted.
        """
        if self.id_ is None:
            return None
        sketch = self.constraint.parent.parent
        list_geo = sketch.get_property(self.list_name).value
        try:
            return next(i for i, g in enumerate(list_geo) if g.id_ == self.id_)
        except StopIteration as exc:
            msg = (f"Geometry id {self.id_} not found in sketch '{sketch.name}'"
                   f" {self.list_name} list")
            raise LookupError(msg) from exc

    def get_geometry(self) -> tuple[FreeCADGeometryXML, CSP] | None:
        """Returns the geometry from the sketch based on the ids of the
        constrained geometry.
        """
        if self.id_ is None:
            return None
        sketch = self.constraint.parent.parent
        list_geo = sketch.get_property(self.list_name).value
        try:
            return (next(g for g in list_geo if g.id_ == self.id_), self.part)
        except StopIteration as exc:
            msg = (f"Geometry id {self.id_} not found in sketch '{sketch.name}'"
                   f" {self.list_name} list")
            raise LookupError(msg) from exc

    def _get_list_index_from_index(self) -> int | None:
        """Returns the list index from the index stored in the xml."""
        if self.index == -2000:
            return None
        if self.index < 0:
            return -1 - self.index
        return self.index

    def _get_geometry_by_index(self) -> FreeCADGeometryXML | None:
        list_index = self._get_list_index_from_index()
        if list_index is None:
            return None
        sketch = self.constraint.parent.parent
        return sketch.get_property(self.list_name).value[list_index]
