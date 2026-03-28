"""A module providing independent utilities for interacting with the FreeCAD
API.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element
import logging

from pancad.exceptions import DupeNameError
from pancad.cad.freecad.xml_utils import (
    FreeCADUID,
    EMPTY_CONSTRAINED,
    LIST_INT_XML_MAP,
    LIST_NAME_INT_MAP,
)

if TYPE_CHECKING:
    from typing import NamedTuple

    from pancad.cad.freecad._application_types import (
        FreeCADConstraint,
        FreeCADDocument,
        FreeCADFeature,
        FreeCADGeometry,
        FreeCADSketch,
        FreeCADAPIObject,
    )
    from pancad.cad.freecad.xml_utils import SketchConstraintUidInfo

logger = logging.getLogger(__name__)


################################################################################
# Constant Definitions
################################################################################

GEO_EXT_TYPE_XPATH = "GeoExtensions/GeoExtension[@type='{type_}']"
"""Xpath template to find a GeoExtension by its type."""
GEO_LIST_XPATH = "Properties/Property[@name='{list_name}']/GeometryList"
"""Xpath template to find a GeometryList by its name."""
CONSTRAINT_LIST_XPATH = "Properties/Property[@name='Constraints']/ConstraintList"
"""Xpath to find a sketch's ConstraintList."""


################################################################################
# Modifying API Properties
################################################################################

def relabel_object(object_: FreeCADFeature | FreeCADDocument,
                   label: str, allow_empty: bool=False) -> None:
    """Relabels the object.

    :raises DupeNameError: If FreeCAD says the name already exists.
    :raises ValueError: If new label does not match the expected label for an
        unhandled reason.
    """
    object_.Label = label
    if label == "" and not allow_empty:
        raise ValueError("New label cannot be empty")
    if object_.Label != label:
        if object_.Label.startswith(label):
            msg = ("FreeCAD returned a modified label due to there already"
                   " being an object with the provided label.")
            raise DupeNameError(msg, object_.Label)
        raise ValueError("Unhandled FreeCAD relabel behavior with:", label)

################################################################################
# Querying API Properties
################################################################################

def get_by_uid(uid: str | FreeCADUID,
               document: FreeCADDocument) -> FreeCADAPIObject:
    """Returns the corresponding FreeCAD API object from the document.

    :param uid: A FreeCADUID or a compatible str.
    :param document: The document the uid is in.
    """
    if not isinstance(uid, FreeCADUID):
        uid = FreeCADUID(uid)
    if uid.file_uid != document.Uid:
        raise LookupError("uid is not in the document", uid)
    data = uid.data
    if data.type_ == "document":
        return document

    try:
        feature = next(o for o in document.Objects if o.ID == data.feature_id)
    except StopIteration as exc:
        msg = f"uid's feature id '{data.feature_id}' is not in the document"
        raise LookupError(msg, uid) from exc

    if data.type_ == "feature":
        return feature
    if data.type_ == "sketchgeo":
        return get_geometry_by_sketch_id(data.geometry_id, data.list_name,
                                         feature)
    if data.type_ == "sketchcons":
        return _get_constraint_by_uid(data, feature)
    msg = f"uid type '{data.type_}' is not yet supported"
    raise NotImplementedError(msg, uid)

def _get_constraint_by_uid(data: SketchConstraintUidInfo,
                           sketch: FreeCADSketch) -> FreeCADConstraint:
    """Returns the constraint api object from a sketch api object."""
    attribs = {"Type": str(data.constraint_type)}
    for name, reference in data.reference_map.items():
        if reference.id_ == EMPTY_CONSTRAINED:
            geo_index = EMPTY_CONSTRAINED
        else:
            list_name = LIST_INT_XML_MAP[reference.list_int]
            geo_index = get_geometry_index_by_sketch_id(reference.id_,
                                                        list_name,
                                                        sketch)
            if list_name == "ExternalGeo":
                geo_index = -1 - geo_index
        attribs.update({name: str(geo_index), name + "Pos": str(reference.part)})
    for index, constraint in enumerate(get_sketch_constraint_list_xml(sketch)):
        constraint_attribs = {name: constraint.attrib[name] for name in attribs}
        if constraint_attribs == attribs:
            return sketch.Constraints[index]
    raise LookupError("Could not find constraint in sketch", data)


################################################################################
# Data Structure Definitions
################################################################################

@dataclass(frozen=True)
class FreeCADConstraintGeoRef:
    """Class for keeping track of a FreeCAD constraint's index reference,
    subpart, and geometry type for one geometry.

    :param index: The constraint reference index of the pair. Negative for
        ExternalGeo, positive for Geometry.
    :param part: The edge sub part of the geometry.
    :param geo_type: The geometry type of the geometry at the index, not
        necessarily the same type as the geometry at the index + subpart.
    """
    index: int
    part: int
    geo_type: str

    @property
    def is_point(self) -> bool:
        """Returns whether the reference is to a point, either a standalone
        point or a subpart point. Subparts: 0 (entire edge), 1 (start), 2,
        (end), 3 (center), 4+ (poles of b-spline).
        """
        return self.part > 0

    @property
    def pair(self) -> tuple[int, int]:
        """Returns the pair of index and subpart that constraints are defined
        with in FreeCAD sketches.
        """
        return self.index, self.part


################################################################################
# Reading API Element XML
################################################################################

def read_element_xml(element: FreeCADAPIObject) -> ET:
    """Reads the xml Content of a FreeCAD element in an ElementTree."""
    content = f"<element>{element.Content}</element>"
    return ET.fromstring(content)

def get_geometry_details(geometry: FreeCADGeometry | Element) -> Element:
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

def get_geometry_type(geometry: FreeCADGeometry | Element) -> str:
    """Get the name of the geometry type from its xml content."""
    return get_geometry_details(geometry).tag

def get_sketch_geometry_list_xml(sketch: FreeCADSketch,
                                 list_: Literal["Geometry", "ExternalGeo"]
                                 ) -> Element:
    """Returns the sketch's GeometryList element.

    :param sketch: A sketch FreeCAD API object.
    :param list_: The name of the list to get.
    """
    list_xpath = GEO_LIST_XPATH.format(list_name=list_)
    tree = read_element_xml(sketch)
    geo_list = tree.find(list_xpath)
    if geo_list is None:
        msg = f"sketch does not contain a {list_} GeometryList"
        raise TypeError(msg, sketch)
    return geo_list

def get_sketch_constraint_list_xml(sketch: FreeCADSketch) -> Element:
    """Returns the sketch's GeometryList element."""
    tree = read_element_xml(sketch)
    constraint_list = tree.find(CONSTRAINT_LIST_XPATH)
    if constraint_list is None:
        raise TypeError("sketch does not contain a ConstraintList", sketch)
    return constraint_list


################################################################################
# Read object UIDs
################################################################################

def read_document_uid(document: FreeCADDocument) -> FreeCADUID:
    """Returns a document FreeCADUID from an api document object."""
    return FreeCADUID.from_parts(document.Uid, "document")

def read_feature_uid(feature: FreeCADFeature,
                     document: FreeCADDocument) -> FreeCADUID:
    """Returns a feature type FreeCADUID from FreeCAD api objects.

    :param feature: A FreeCAD API feature object.
    :param document: A FreeCAD API document object containing the feature.
    """
    return FreeCADUID.from_parts(document.Uid, "feature", feature.ID)

def read_geometry_uid(geometry: FreeCADGeometry,
                      list_: Literal["Geometry", "ExternalGeo"],
                      sketch: FreeCADSketch,
                      document: FreeCADDocument) -> FreeCADUID:
    """Returns a sketchgeo type FreeCADUID from FreeCAD api objects.

    :param geometry: A FreeCAD API sketch geometry object.
    :param list_: The name of the list the geometry is in.
    :param sketch: A FreeCAD API sketch object containing the geometry.
    :param document: A FreeCAD API document object containing the sketch.
    """
    id_ = get_geometry_sketch_id(geometry, list_, sketch)
    list_int = LIST_NAME_INT_MAP[list_]
    return FreeCADUID.from_parts(document.Uid, "sketchgeo",
                                 sketch.ID, list_int, id_)

def read_constraint_uid(constraint: FreeCADConstraint,
                        sketch: FreeCADSketch,
                        document: FreeCADDocument) -> FreeCADUID:
    """Returns a sketchcons type FreeCADUID from FreeCAD api objects.

    :param constraint: A FreeCAD API sketch constraint object.
    :param sketch: A FreeCAD API sketch object containing the constraint.
    :param document: A FreeCAD API document object containing the sketch.
    :raises TypeError: When provided an element without Constrain in its xml.
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
        else:
            if index < 0:
                list_name = "ExternalGeo"
                geometry = sketch.ExternalGeo[-1 - index]
            else:
                list_name = "Geometry"
                geometry = sketch.Geometry[index]
            geo_id = get_geometry_sketch_id(geometry, list_name, sketch)
        parts.extend(
            [
                LIST_NAME_INT_MAP[list_name],
                geo_id,
                element.attrib[constrained + "Pos"]
            ]
        )
    return FreeCADUID.from_parts(*parts)


################################################################################
# Getting Geometry information
################################################################################

def get_geometry_sketch_id(geometry: FreeCADGeometry,
                           list_: Literal["Geometry", "ExternalGeo"],
                           sketch: FreeCADSketch) -> int:
    """Returns the id of the geometry inside its xml GeoExtension contents.

    :param geometry: A geoemtry FreeCAD API object.
    :param list_: The name of the list the geometry is in.
    :raises ValueError: If the sketch is not in the list.
    :raises TypeError: If the geometry element is invalid, usually in its xml.
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
    """Returns the index of geometry corresponding to the id from the sketch.

    :param id_: The geometry id integer.
    :param list_: The name of the list the geometry is in.
    :param sketch: A sketch FreeCAD API object.
    """
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

def get_geometry_index_by_uid(uid: FreeCADUID,
                              document: FreeCADDocument) -> int:
    """Returns the sketch index of the geometry corresponding to the uid
    inside of the document.

    :param uid: A sketchgeo FreeCADUID
    :param document: A FreeCAD API document object containing the geometry.
    """
    geometry = get_by_uid(uid, document)
    sketch = get_by_uid(uid.data.sketch_uid, document)
    return get_geometry_sketch_index(geometry, uid.data.list_name, sketch)

def get_geometry_sketch_index(geometry: FreeCADGeometry,
                              list_: Literal["Geometry", "ExternalGeo"],
                              sketch: FreeCADSketch) -> int:
    """Returns the index of the element in the sketch.

    :param geometry: A geoemtry FreeCAD API object.
    :param list_: The name of the list the geometry is in.
    :param sketch: A sketch FreeCAD API object.
    """
    id_ = get_geometry_sketch_id(geometry, list_, sketch)
    return get_geometry_index_by_sketch_id(id_, list_, sketch)

def get_geometry_by_sketch_id(id_: int,
                              list_: Literal["Geometry", "ExternalGeo"],
                              sketch: FreeCADSketch):
    """Returns the api geometry object corresponding to the id from the sketch.

    :param id_: The geometry id integer.
    :param list_: The name of the list the geometry is in.
    :param sketch: A sketch FreeCAD API object.
    """
    index = get_geometry_index_by_sketch_id(id_, list_, sketch)
    match list_:
        case "Geometry":
            geometry = sketch.Geometry[index]
        case "ExternalGeo":
            geometry = sketch.ExternalGeo[index]
        case _:
            msg = "Unexpected list_, expected either Geometry or ExternalGeo"
            raise TypeError(msg, list_)
    return geometry


################################################################################
# Getting Constraint information
################################################################################

def get_constraint_sketch_index(constraint: FreeCADConstraint,
                                sketch: FreeCADSketch) -> int:
    """Returns the index of the constraint API object inside the sketch.

    :param constraint: A FreeCAD API constraint object.
    :param sketch: A FreeCAD API sketch object containing the constraint.
    """
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

def get_reference_index(index: int,
                        list_: Literal["Geometry", "ExternalGeo"]) -> int:
    """Returns the index that FreeCAD constraints use to reference geometry in
    sketch lists. Geometry is positive and zero-indexed, ExternalGeo is negative
    and starts at -1. -1 is the x-axis and origin of the sketch coordinate
    system. -2 is the y-axis of the sketch coordinate system.

    :param index: An index in a FreeCAD geometry list.
    :param list_: The name of the list the geometry is in.
    :raises ValueError: When provided a negative number for index.
    """
    if index < 0:
        raise ValueError("index must be 0 or positive", index)
    match list_:
        case "Geometry":
            return index
        case "ExternalGeo":
            return -1 - index
    msg = f"Expected 'Geometry' or 'ExternalGeo' for list_name got '{list_}'"
    raise TypeError(msg)

def get_reference_index_by_uid(uid: FreeCADUID,
                               document: FreeCADDocument) -> int:
    """Returns the index that FreeCAD constraints use to reference geometry in
    sketch lists.

    :param uid: A sketchgeo FreeCADUID.
    :param document: A FreeCAD API document object containing the geometry.
    """
    index = get_geometry_index_by_uid(uid, document)
    return get_reference_index(index, uid.data.list_name)
