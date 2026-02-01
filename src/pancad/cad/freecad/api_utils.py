"""A module providing independent utilities for interacting with the FreeCAD 
API.
"""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from itertools import islice
from typing import TYPE_CHECKING, Literal
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

if TYPE_CHECKING:
    from typing import NamedTuple

################################################################################
# Constant Definitions
################################################################################
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


GEO_EXT_TYPE_XPATH = "GeoExtensions/GeoExtension[@type='{type_}']"
GEO_LIST_XPATH = "Properties/Property[@name='{list_name}']/GeometryList"
CONSTRAINT_LIST_XPATH = "Properties/Property[@name='Constraints']/ConstraintList"

################################################################################
# Data Structure Definitions
################################################################################

@dataclass(frozen=True)
class FeatureUidInfo:
    """Class for keeping track of feature info inside a uid string."""
    file_uid: str
    type_: str
    feature_id: int

@dataclass(frozen=True)
class SketchGeometryReference:
    """Integers describing where a geometry element is inside of a sketch API 
    object context.

    :param list_: int for which sketch list to look in. 0 for Geometry, 1 for 
        ExternalGeo.
    :param id_: int for the id of the geometry inside the sketch's xml.
    :param pos: The edge subpart integer corresponding to the geometry portion 
        being constrained.
    """
    list_: int
    id_: int
    pos: int

    @property
    def list_name(self) -> str:
        return LIST_INT_XML_MAP[self.list_]

@dataclass(frozen=True)
class SketchGeometryUidInfo:
    """Class for keeping track of geometry in inside a uid string."""
    file_uid: str
    type_: str
    feature_id: int
    list_: int
    geometry_id: int

    @property
    def list_name(self) -> str:
        """The name of the sketch list the geometry is in."""
        return LIST_INT_XML_MAP[self.list_]

@dataclass(frozen=True)
class SketchConstraintUidInfo:
    """Class for keeping track of constraint info inside a uid string."""
    file_uid: str
    type_: str
    feature_id: int
    constraint_type: int
    first: SketchGeometryReference
    second: SketchGeometryReference
    third: SketchGeometryReference

    @classmethod
    def from_parts(cls, file_uid: str, type_: str,
                   feature_id: int, constraint_type: int,
                   *parts: list[int]):
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
        return cls(file_uid, type_, feature_id, constraint_type, *references)

    @property
    def references(self) -> list[SketchGeometryReference]:
        return [self.first, self.second, self.third]

    @property
    def reference_map(self) -> dict[str, SketchGeometryReference]:
        return {"First": self.first, "Second": self.second, "Third": self.third}

class FreeCADUID(str):
    """A class to make it easy to access freecad uid information from their 
    strings. All attributes of this class should stay constant after 
    initialization.

    :raises ValueError: When the number/type of uid parts are invalid for the uid 
        type.
    """
    delim = "_"
    """Delimiter between information parts in the uid."""
    type_info_types = {
        "feature": FeatureUidInfo,
        "sketchgeo": SketchGeometryUidInfo,
        "sketchcons": SketchConstraintUidInfo.from_parts,
    }
    """Mapping from type names to their namedtuple types."""

    def __new__(cls, string):
        new = super().__new__(cls, string)
        parts = string.split(cls.delim)
        try:
            new._file_uid, new._type, *parts = parts
        except ValueError as exc:
            msg = "Invalid number of parts for any available uid types"
            raise ValueError(msg, parts) from exc
        try:
            for i, part in enumerate(parts):
                parts[i] = int(part)
        except ValueError as exc:
            exc.add_note("Could not convert all parts into ints")
            raise
        try:
            new._data = cls.type_info_types[new._type](new.file_uid, new._type,
                                                       *parts)
        except KeyError as exc:
            raise ValueError("Invalid uid type", exc.args[0]) from exc
        return new

    @classmethod
    def from_feature(cls, feature, document):
        """Returns a feature type FreeCADUID from FreeCAD api objects.

        :param feature: A FreeCAD API feature object.
        :param document: A FreeCAD API document object containing the feature.
        """
        parts = [document.Uid, "feature", feature.ID]
        return cls(cls.delim.join(map(str, parts)))

    @classmethod
    def from_sketch_geometry(cls,
                             geometry,
                             list_: Literal["Geometry", "ExternalGeo"],
                             sketch, document):
        """Returns a sketchgeo type FreeCADUID from FreeCAD api objects.

        :param geometry: A FreeCAD API sketch geometry object.
        :param list_: The name of the list the geometry is in.
        :param sketch: A FreeCAD API sketch object containing the geometry.
        :param document: A FreeCAD API document object containing the sketch.
        """
        id_ = get_geometry_sketch_id(geometry, list_, sketch)
        list_int = LIST_NAME_INT_MAP[list_]
        parts = [document.Uid, "sketchgeo", sketch.ID, list_int, id_]
        return cls(cls.delim.join(map(str, parts)))

    @classmethod
    def from_sketch_constraint(cls, constraint, sketch, document):
        """Returns a sketchcons type FreeCADUID from FreeCAD api objects.

        :param constraint: A FreeCAD API sketch constraint object.
        :param sketch: A FreeCAD API sketch object containing the constraint.
        :param document: A FreeCAD API document object containing the sketch.
        """
        constraint_xml = read_element_xml(constraint)
        element = constraint_xml.find("Constrain")
        if element is None:
            msg = "Could not read Constrain element from the constraint xml"
            raise TypeError(msg, element)
        parts = [document.Uid, "sketchcons", sketch.ID, element.attrib["Type"]]
        # Get the geometry ids for each constrained geometry since indexes
        # can/will change.
        for constrained in ["First", "Second", "Third"]:
            index = int(element.attrib[constrained])
            if index == EMPTY_CONSTRAINED:
                list_name = "Geometry"
                geo_id = EMPTY_CONSTRAINED
            elif index < 0:
                geometry = sketch.ExternalGeo[-1 - index]
                list_name = "ExternalGeo"
            else:
                list_name = "Geometry"
                geometry = sketch.Geometry[index]
            if index != EMPTY_CONSTRAINED:
                geo_id = get_geometry_sketch_id(geometry, list_name, sketch)
            parts.extend(
                [
                    LIST_NAME_INT_MAP[list_name],
                    geo_id,
                    element.attrib[constrained + "Pos"]
                ]
            )
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

################################################################################
# Reading API Element XML
################################################################################

def read_element_xml(element) -> ElementTree:
    """Reads the xml Content of a FreeCAD element in an ElementTree."""
    try:
        content = f"<element>{element.Content}</element>"
    except:
        breakpoint()
    return ElementTree.fromstring(content)

def get_geometry_details(geometry) -> Element:
    """Returns the geometry details element from its content."""
    filter_tags = ["GeoExtensions", "Construction"]
    if not isinstance(geometry, Element):
        # Try to read the api version
        tree = read_element_xml(geometry)
    else:
        tree = geometry
    candidates = [element for element in tree if element.tag not in filter_tags]
    if len(candidates) > 1:
        raise ValueError("Multiple details candidates found", candidates)
    if not candidates:
        raise ValueError("No candidates found in geometry content", tree)
    return candidates.pop()

def get_sketch_geometry_list_xml(sketch,
                                 list_: Literal["Geometry", "ExternalGeo"]
                                 ) -> Element:
    """Returns the sketch's GeometryList element."""
    list_xpath = GEO_LIST_XPATH.format(list_name=list_)
    tree = read_element_xml(sketch)
    geo_list = tree.find(list_xpath)
    if geo_list is None:
        msg = f"sketch does not contain a {list_} GeometryList"
        raise TypeError(msg, sketch)
    return geo_list

def get_sketch_constraint_list_xml(sketch) -> Element:
    """Returns the sketch's GeometryList element."""
    tree = read_element_xml(sketch)
    constraint_list = tree.find(CONSTRAINT_LIST_XPATH)
    if constraint_list is None:
        raise TypeError("sketch does not contain a ConstraintList", sketch)
    return constraint_list

################################################################################
# Getting Geometry information
################################################################################

def get_geometry_sketch_id(geometry, list_: Literal["Geometry", "ExternalGeo"],
                           sketch) -> int:
    """Returns the id of the geometry inside its xml GeoExtension contents."""
    ext_type = "Sketcher::SketchGeometryExtension"
    ext_match = GEO_EXT_TYPE_XPATH.format(type_=ext_type)

    tree = read_element_xml(geometry)
    ext = tree.find(ext_match)
    if ext is None:
        # For cases like GeomPoints that don't have ids in their content.
        try:
            details = get_geometry_details(geometry).attrib
        except ValueError as exc:
            raise TypeError("Invalid geometry element", geometry) from exc
        # Read Sketch content instead
        geo_list = get_sketch_geometry_list_xml(sketch, list_)
        try:
            geo_element = next(ele for ele in geo_list
                               if details == get_geometry_details(ele).attrib)
        except StopIteration as exc:
            msg = f"Geometry not in sketch {list_} Geometry List"
            raise ValueError(msg, geometry) from exc
        if (ext := geo_element.find(ext_match)) is None:
            msg = ("FreeCAD Bug: Even sketch geometry element"
                   f" does not have '{ext_type}' extension")
            raise TypeError(msg, sketch)
    try:
        return int(ext.attrib["id"])
    except KeyError as exc:
        msg = "Invalid geometry, no 'id' found in extension"
        raise TypeError(msg, ext) from exc

def get_geometry_index_by_sketch_id(id_: int,
                                    list_: Literal["Geometry", "ExternalGeo"],
                                    sketch) -> int:
    """Returns the index of geometry corresponding to the id from the sketch."""
    ext_type = "Sketcher::SketchGeometryExtension"
    ext_match = GEO_EXT_TYPE_XPATH.format(type_=ext_type)

    for index, element in enumerate(get_sketch_geometry_list_xml(sketch, list_)):
        ext = element.find(ext_match)
        try:
            element_id = int(ext.attrib["id"])
        except (AttributeError, KeyError) as exc:
            msg = "Could not read id from sketch geometry xml"
            raise TypeError(msg, element) from exc
        if id_ == element_id:
            return index
    raise LookupError("Could not find geometry with id in sketch", id_)

def get_geometry_sketch_index(geometry,
                              list_: Literal["Geometry", "ExternalGeo"],
                              sketch) -> int:
    """Returns the index of the element in the sketch."""
    id_ = get_geometry_sketch_id(geometry, list_, sketch)
    return get_geometry_index_by_sketch_id(id_, list_, sketch)

def get_geometry_by_sketch_id(id_: int,
                              list_: Literal["Geometry", "ExternalGeo"],
                              sketch):
    """Returns the api geometry object corresponding to the id from the sketch.
    """
    index = get_geometry_index_by_sketch_id(id_, list_, sketch)
    match list_:
        case "Geometry":
            geometry = sketch.Geometry[index]
        case "ExternalGeo":
            geometry = sketch.ExternalGeo[index]
        case _:
            raise TypeError("Unexpected list_", list_)
    return geometry

################################################################################
# Getting Constraint information
################################################################################

def get_constraint_sketch_index(constraint, sketch) -> int:
    # Get constraint xml
    constraint_xml = read_element_xml(constraint)
    constraint_ele = constraint_xml.find("Constrain")
    if constraint_ele is None:
        msg = "Could not read Constrain element from the constraint xml"
        raise TypeError(msg, constraint)

    # Check through sketch xml for constraint xml's attrib
    for index, element in enumerate(get_sketch_constraint_list_xml(sketch)):
        if element.attrib == constraint_ele.attrib:
            return index
    raise LookupError("Could not find constraint in sketch", constraint)

def get_by_uid(uid: str | FreeCADUID, document):
    """Returns the corresponding FreeCAD API object from the document."""
    if not isinstance(uid, FreeCADUID):
        uid = FreeCADUID(uid)
    if uid.file_uid != document.Uid:
        raise LookupError("uid is not in the document", uid)

    try:
        feature = next(o for o in document.Objects if o.ID == uid.data.feature_id)
    except StopIteration as exc:
        msg = f"uid's feature id '{uid.data.feature_id}' is not in the document"
        raise LookupError(msg, uid) from exc

    data = uid.data
    if data.type_ == "feature":
        return feature
    if data.type_ == "sketchgeo":
        return get_geometry_by_sketch_id(data.geometry_id, data.list_name,
                                         feature)
    if data.type_ == "sketchcons":
        return _get_constraint_by_uid(data, feature)
    msg = f"uid type '{data.type_}' is not yet supported"
    raise NotImplementedError(msg, uid)

def _get_constraint_by_uid(data: SketchConstraintUidInfo, sketch):
    """Returns the constraint api object from a sketch api object."""
    attribs = {"Type": str(data.constraint_type)}
    for name, reference in data.reference_map.items():
        if reference.id_ == -2000:
            geo_index = -2000
        else:
            geo_index = get_geometry_index_by_sketch_id(reference.id_,
                                                        reference.list_name,
                                                        sketch)
            if reference.list_name == "ExternalGeo":
                geo_index = -1 - geo_index
        attribs.update({name: str(geo_index), name + "Pos": str(reference.pos)})
    for index, constraint in enumerate(get_sketch_constraint_list_xml(sketch)):
        constraint_attribs = {name: constraint.attrib[name] for name in attribs}
        if constraint_attribs == attribs:
            return sketch.Constraints[index]
    raise LookupError("Could not find constraint in sketch", data)
