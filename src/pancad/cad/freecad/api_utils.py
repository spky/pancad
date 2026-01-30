"""A module providing independent utilities for interacting with the FreeCAD 
API.
"""
from __future__ import annotations

from xml.etree import ElementTree
from xml.etree.ElementTree import Element


FEATURE_UID_TEMPLATE = "{document_uid}_feature_{feature_id}"
SKETCH_GEO_UID_TEMPLATE = "{document_uid}_sketchgeo_{feature_id}_{geometry_id}"
SKETCH_CONSTRAINT_UID_TEMPLATE = (
    "{document_uid}_sketchcons_{feature_id}_{type_id}_"
    "{id_1}_{pos_1}_{id_2}_{pos_2}_{id_3}_{pos_3}"
)
"""Unique id calculated for a FreeCAD constraint. The first/second/third id is 
NOT the geoemtry index. It has to be the freecad geometry id of the 
targets.
"""

GEO_EXT_TYPE_XPATH = "GeoExtensions/GeoExtension[@type='{type_}']"
GEO_LIST_XPATH = "Properties/Property[@name='Geometry']/GeometryList"

def feature_uid(feature, document) -> str:
    """Returns a uid for the feature in a freecad file.
    
    :param feature: A FreeCAD object with an ID.
    :param document: The document that the FreeCAD object is in.
    """
    return FEATURE_UID_TEMPLATE.format(document_uid=document.Uid,
                                       feature_id=feature.ID)

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
        tree = read_element_xml(sketch)
        if (geo_list := tree.find(GEO_LIST_XPATH)) is None:
            raise TypeError("sketch does not contain a GeometryList", sketch)
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
        raise TypeError("Invalid geometry, no 'id' found in extension", content)

def get_geometry_sketch_index(geometry, sketch) -> int:
    """Returns the index of the element in the sketch."""
    tree = read_element_xml(sketch)
    ext_type = "Sketcher::SketchGeometryExtension"
    ext_match = GEO_EXT_TYPE_XPATH.format(type_=ext_type)

    id_ = get_geometry_sketch_id(geometry, sketch)

    if (geo_list := tree.find(GEO_LIST_XPATH)) is None:
        raise TypeError("sketch xml does not contain a GeometryList", sketch)
    for index, element in enumerate(geo_list):
        ext = element.find(ext_match)
        try:
            element_id = int(ext.attrib["id"])
        except (AttributeError, KeyError) as exc:
            raise TypeError("Could not read id from sketch geometry xml", element)
        if id_ == element_id:
            return index
    raise KeyError("Could not find geometry in sketch", geometry)

def get_sketch_constraint_uid(constraint, sketch, document) -> str:
    pass

def get_sketch_geometry_uid(geometry, sketch, document) -> str:
    """Returns a uid for the sketch geometry element in a freecad file."""
    id_ = get_geometry_sketch_id(geometry, sketch)
    return SKETCH_GEO_UID_TEMPLATE.format(
        document_uid=document.Uid, feature_id=sketch.ID, geometry_id=id_
    )
