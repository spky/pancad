"""A module providing independent utilities for interacting with the FreeCAD 
API.
"""
from __future__ import annotations

from collections import namedtuple
from typing import TYPE_CHECKING
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

if TYPE_CHECKING:
    from typing import NamedTuple

GEO_EXT_TYPE_XPATH = "GeoExtensions/GeoExtension[@type='{type_}']"
GEO_LIST_XPATH = "Properties/Property[@name='Geometry']/GeometryList"
CONSTRAINT_LIST_XPATH = "Properties/Property[@name='Constraints']/ConstraintList"

FeatureUidInfo = namedtuple(
    "FeatureUidInfo",
    ["file_uid", "type_", "feature_id"]
)
SketchGeometryUidInfo = namedtuple(
    "SketchGeometryUidInfo",
    ["file_uid", "type_", "feature_id", "geometry_id"]
)
SketchConstraintUidInfo = namedtuple(
    "SketchConstraintUidInfo",
    [
        "file_uid", "type_", "feature_id", "constraint_type",
        "id_1", "pos_1", "id_2", "pos_2", "id_3", "pos_3"
    ]
)

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
        "sketchcons": SketchConstraintUidInfo,
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
        except TypeError as exc:
            expected = len(cls.type_info_types[new._type]._fields)
            all_parts = string.split(cls.delim)
            got = len(all_parts)
            msg = (f"Expected {expected} parts for '{new.type_}'"
                   f" type uid, got {got}")
            raise ValueError(msg, all_parts) from exc
        except KeyError as exc:
            raise ValueError("Invalid uid type", exc.args[0]) from exc
        return new

    @classmethod
    def from_feature(cls, feature, document):
        """Returns a feature type FreeCADUID from FreeCAD api objects."""
        parts = [document.Uid, "feature", feature.ID]
        return cls(cls.delim.join(map(str, parts)))

    @classmethod
    def from_sketch_geometry(cls, geometry, sketch, document):
        """Returns a sketchgeo type FreeCADUID from FreeCAD api objects."""
        id_ = get_geometry_sketch_id(geometry, sketch)
        parts = [document.Uid, "sketchgeo", sketch.ID, id_]
        return cls(cls.delim.join(map(str, parts)))

    @classmethod
    def from_sketch_constraint(cls, constraint, sketch, document):
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
            if index == -2000: # FreeCAD labels empty indices with -2000
                geometry_id = -2000
            else:
                geometry_id = get_geometry_sketch_id(sketch.Geometry[index],
                                                     sketch)
            parts.extend([geometry_id, element.attrib[constrained + "Pos"]])
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


def read_element_xml(element) -> ElementTree:
    """Reads the xml Content of a FreeCAD element in an ElementTree."""
    content = f"<element>{element.Content}</element>"
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

def get_sketch_geometry_list_xml(sketch) -> Element:
    """Returns the sketch's GeometryList element."""
    tree = read_element_xml(sketch)
    geo_list = tree.find(GEO_LIST_XPATH)
    if geo_list is None:
        raise TypeError("sketch does not contain a GeometryList", sketch)
    return geo_list

def get_sketch_constraint_list_xml(sketch) -> Element:
    """Returns the sketch's GeometryList element."""
    tree = read_element_xml(sketch)
    constraint_list = tree.find(CONSTRAINT_LIST_XPATH)
    if constraint_list is None:
        raise TypeError("sketch does not contain a ConstraintList", sketch)
    return constraint_list

def get_geometry_sketch_id(geometry, sketch) -> int:
    """Returns the id of the geometry inside its xml 
    Sketcher::SketchGeometryExtension GeoExtension contents.
    """
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
        geo_list = get_sketch_geometry_list_xml(sketch)
        try:
            geo_element = next(ele for ele in geo_list
                               if details == get_geometry_details(ele).attrib)
        except StopIteration as exc:
            raise ValueError("Geometry not in sketch", geometry) from exc
        if (ext := geo_element.find(ext_match)) is None:
            msg = ("FreeCAD Bug: Even sketch geometry element"
                   f" does not have '{ext_type}' extension")
            raise TypeError(msg, sketch)
    try:
        return int(ext.attrib["id"])
    except KeyError as exc:
        msg = "Invalid geometry, no 'id' found in extension"
        raise TypeError(msg, ext) from exc

def get_geometry_by_sketch_id(id_: int, sketch):
    """Returns the api geometry object corresponding to the id from the sketch.
    """
    index = get_geometry_index_by_sketch_id(id_, sketch)
    return sketch.Geometry[index]

def get_geometry_index_by_sketch_id(id_: int, sketch) -> int:
    """Returns the index of geometry corresponding to the id from the sketch."""
    ext_type = "Sketcher::SketchGeometryExtension"
    ext_match = GEO_EXT_TYPE_XPATH.format(type_=ext_type)

    for index, element in enumerate(get_sketch_geometry_list_xml(sketch)):
        ext = element.find(ext_match)
        try:
            element_id = int(ext.attrib["id"])
        except (AttributeError, KeyError) as exc:
            msg = "Could not read id from sketch geometry xml"
            raise TypeError(msg, element) from exc
        if id_ == element_id:
            return index
    raise LookupError("Could not find geometry in sketch", geometry)

def get_geometry_sketch_index(geometry, sketch) -> int:
    """Returns the index of the element in the sketch."""
    id_ = get_geometry_sketch_id(geometry, sketch)
    return get_geometry_index_by_sketch_id(id_, sketch)

def get_constraint_sketch_index(constraint, sketch) -> int:
    ext_type = "Sketcher::SketchGeometryExtension"
    ext_match = GEO_EXT_TYPE_XPATH.format(type_=ext_type)

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

    if uid.type_ == "feature":
        return feature
    if uid.type_ == "sketchgeo":
        index = get_geometry_index_by_sketch_id(uid.data.geometry_id, feature)
        return feature.Geometry[index]
    msg = f"uid type '{uid.type_}' is not yet supported"
    raise NotImplementedError(msg, uid)
