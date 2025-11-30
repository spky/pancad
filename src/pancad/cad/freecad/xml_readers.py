"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
from uuid import UUID
import logging
import sqlite3
import tomllib
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree
from zipfile import ZipFile

from pancad import data as pancad_data

from .xml_properties import (
    read_properties, read_property, read_sketch_geometry_common
)
from .xml_appearance import read_shape_appearance
from .constants import SubFile, XMLTag, XMLAttr, XMLObjectType, XMLPropertyType

if TYPE_CHECKING:
    from pathlib import Path
    from xml.etree.ElementTree import Element

sqlite3.register_adapter(UUID, lambda u: str(u))
sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))

logger = logging.getLogger(__name__)

def read_objects(objects: Element) -> list[tuple[str, str, int]]:
    """Reads the objects inside an Objects element
    
    :param element: The Objects element with Object elements underneath.
    :returns: A list of (Name, Type, ID) tuples for each object.
    """
    data = []
    for object_ in objects.iter(XMLTag.OBJECT):
        name = object_.get(XMLAttr.NAME)
        type_ = object_.get(XMLAttr.TYPE)
        id_ = int(object_.get(XMLAttr.ID))
        data.append((name, type_, id_))
    return data

def read_sub_attrib(element: Element,
                    tag: XMLTag=None) -> tuple[tuple[str], list[tuple[str]]]:
    """Reads the attributes of the subelements the element.
    
    :param element: An xml element.
    :param tag: The tag to filter subelements by. Defaults to None.
    :returns: A tuple of attribute names and a list of value tuples of the same 
        length and order as the names tuple.
    """
    sub_attrs = []
    names = []
    for sub in element.iter(tag):
        # Extend to maintain tuple ordering throughout iteration
        names.extend(key for key in list(sub.attrib) if key not in names)
        sub_attrs.append(tuple(sub.get(key) for key in names))
    return tuple(names), sub_attrs

def read_expand(expand: Element) -> set[str]:
    """Recursively reads the names that are expanded in an expand xml element."""
    all_expanded = set()
    if name := expand.get(XMLAttr.NAME):
        all_expanded.add(name)
    for sub in expand.findall(XMLTag.EXPAND):
        for sub_name in read_expand(sub):
            all_expanded.add(sub_name)
    return all_expanded

def read_extensions(extensions: Element) -> list[tuple[str, str]]:
    """Finds and reads an Extensions element and provides a list of (type, name) 
    tuples for each one.
    """
    data = []
    if not (extensions := extendable.find(XMLTag.EXTENSIONS)):
        return data # Return empty list of no extensions found
    for ext in extensions.iter(XMLTag.EXTENSION):
        data.append((ext.get(XMLAttr.TYPE), ext.get(XMLAttr.NAME)))
    return data

def read_view_provider_data(view_provider_data: Element
                            ) -> list[tuple[dict[str, str], list, list]]:
    """Reads ViewProvider elements from a ViewProviderData element as a list of 
    (attributes, extensions, properties) tuples.
    """
    data = []
    for provider in view_provider_data.iter(XMLTag.VIEW_PROVIDER):
        extensions = read_extensions(provider)
        properties = read_properties(provider.find(XMLTag.PROPERTIES))
        attributes = dict(provider.attrib)
        data.append((attributes, extensions, properties))
    return data

def read_metadata(tree: ElementTree) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a tuple of field names and a tuple of values for FCStd metadata."""
    file_uid = tree.find("./Properties/Property[@name='Uid']/Uuid").get("value")
    data = []
    
    for element in tree.findall("./Properties/Property"):
        name = element.get(XMLAttr.NAME)
        type_ = element.get(XMLAttr.TYPE)
        status = element.get(XMLAttr.STATUS)
        match type_:
            case XMLPropertyType.APP_STRING:
                value = element.find(XMLTag.STRING).get(XMLAttr.VALUE)
            case XMLPropertyType.APP_BOOL:
                value = element.find(XMLTag.BOOL).get(XMLAttr.VALUE)
            case XMLPropertyType.APP_UUID:
                value = element.find(XMLTag.UUID).get(XMLAttr.VALUE)
            case XMLPropertyType.APP_ENUM:
                index = int(element.find(XMLTag.INTEGER).get(XMLAttr.VALUE))
                enum_list = element.find(XMLTag.CUSTOM_ENUM_LIST)
                value = enum_list[index].get(XMLAttr.VALUE)
            case _:
                logger.warning(f"Could not read metadata type {type_}")
                value = None
        data.append((file_uid, name, type_, status, value))
    FIELDS = [XMLAttr.NAME, XMLAttr.TYPE, XMLAttr.STATUS, XMLAttr.VALUE]
    return FIELDS, data

def read_dependencies(tree: str) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a dict of object name to a list of its dependencies from FCStd 
    files. The lists of dependencies may have duplicates.
    """
    file_uid = tree.find("./Properties/Property[@name='Uid']/Uuid").get("value")
    OBJECT_DEPS_XPATH = f"./{XMLTag.OBJECTS}/{XMLTag.OBJECT_DEPENDENCIES}"
    FIELDS = ["FileUid", "Object", "Dependency"]
    data = []
    for deps in tree.findall(OBJECT_DEPS_XPATH):
        name = deps.get(XMLAttr.NAME_CAPITALIZED)
        depends_on = [
            dep.get(XMLAttr.NAME_CAPITALIZED) for dep in deps.iter(XMLTag.DEP)
        ]
        data.extend([(file_uid, name, dep) for dep in depends_on])
    return FIELDS, data

def read_sketch_constraints(tree: ElementTree) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a tuple of field names and a tuple of values for each constraint"""
    TYPE_NAME_XPATH = "./Objects/Object[@type='Sketcher::SketchObject']"
    DATA_XPATH = (
        "./ObjectData/Object[@name='%s']"
        "/Properties/Property[@type='Sketcher::PropertyConstraintList']"
    )
    file_uid = tree.find("./Properties/Property[@name='Uid']/Uuid").get("value")
    ADDED_FIELDS = ("FileUid", "SketchName", "ListName", "ListIndex")
    field_names = list(ADDED_FIELDS)
    constraint_dicts = []
    for sketch in tree.findall(TYPE_NAME_XPATH):
        sketch_name = sketch.get(XMLAttr.NAME)
        for property_ in tree.findall(DATA_XPATH % sketch_name):
            list_name = property_.get(XMLAttr.NAME)
            constraint_list = property_.find(XMLTag.CONSTRAINT_LIST)
            fields, values = read_sub_attrib(constraint_list, XMLTag.CONSTRAINT)
            
            # Ensure that all fields are in the same order by mapping them first
            fields = ADDED_FIELDS + fields
            constraints = [(file_uid, sketch_name, list_name, list_index)
                           + constraint
                           for list_index, constraint in enumerate(values)]
            constraint_dicts.extend(
                [{field: attr for field, attr in zip(fields, constraint)}
                 for constraint in constraints]
             )
            field_names.extend(name for name in fields
                               if name not in field_names)
    sketch_constraints = [tuple(constraint.setdefault(field)
                                for field in field_names)
                          for constraint in constraint_dicts]
    return tuple(field_names), sketch_constraints

def read_sketch_geometry_info(tree: ElementTree
                              ) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a tuple of field names and a tuple of values in common for each 
    sketch geometry element in the tree.
    """
    sketch_geometry = []
    file_uid = tree.find("./Properties/Property[@name='Uid']/Uuid").get("value")
    TYPE_NAME_XPATH = "./Objects/Object[@type='Sketcher::SketchObject']"
    DATA_XPATH = (
        "./ObjectData/Object[@name='%s']"
        "/Properties/Property[@type='Part::PropertyGeometryList']"
    )
    GEO_EXT_XPATH = (
        "./GeoExtensions"
        "/GeoExtension[@type='Sketcher::SketchGeometryExtension']"
    )
    for sketch in tree.findall(TYPE_NAME_XPATH):
        sketch_name = sketch.get(XMLAttr.NAME)
        for property_ in tree.findall(DATA_XPATH % sketch_name):
            list_name = property_.get(XMLAttr.NAME)
            geometry_list = property_.find(XMLTag.GEOMETRY_LIST)
            for list_index, geometry in enumerate(geometry_list):
                construction = geometry.find(XMLTag.CONSTRUCTION)
                sketch_ext = geometry.find(GEO_EXT_XPATH)
                sketch_geometry.append(
                    (
                        file_uid,
                        sketch_name,
                        list_name,
                        list_index,
                        geometry.get(XMLAttr.TYPE),
                        geometry.get(XMLAttr.ID),
                        geometry.get(XMLAttr.MIGRATED),
                        construction.get(XMLAttr.VALUE),
                        sketch_ext.get(XMLAttr.INTERNAL_GEOMETRY_TYPE)
                    )
                )
    FIELDS = ("FileUid", "SketchName", "ListName", "ListIndex",
              XMLAttr.ID, XMLAttr.TYPE, XMLAttr.MIGRATED, XMLTag.CONSTRUCTION,
              XMLAttr.INTERNAL_GEOMETRY_TYPE)
    return FIELDS, sketch_geometry

def read_object_info(tree: ElementTree) -> tuple[tuple[str], list[tuple[str]]]:
    """Returns a tuple of field names and a tuple of values for fields common to 
    all objects in an FCStd document.xml tree.
    """
    info = []
    file_uid = tree.find("./Properties/Property[@name='Uid']/Uuid").get("value")
    PROPERTY_XPATH = ("./ObjectData/Object[@name='%s']"
                      "/Properties/Property[@name='%s']/%s")
    SHARED_ATTR = [XMLAttr.NAME, XMLAttr.ID, XMLAttr.TYPE]
    SHARED_DATA = [
        ("Label", XMLTag.STRING),
        ("Label2", XMLTag.STRING),
        ("Visibility", XMLTag.BOOL),
    ]
    fields = SHARED_ATTR + [name for name, _ in SHARED_DATA]
    for obj in tree.findall("./Objects/Object"):
        name = obj.get(XMLAttr.NAME)
        properties = [obj.get(attr) for attr in SHARED_ATTR]
        for prop, tag in SHARED_DATA:
            properties.append(
                tree.find(PROPERTY_XPATH % (name, prop, tag)).get(XMLAttr.VALUE)
            )
        info.append((file_uid,) + tuple(properties))
    return ("FileUid",) + tuple(fields), info

def read_line_segments(tree: ElementTree) -> tuple[tuple[str], list[tuple[str]]]:
    """Returns the fields and values of all LineSegments in the tree."""
    SKETCH_XPATH = ("./ObjectData/Object/Properties/Property[@name='Geometry']"
                    "/../..")
    GEO_LIST_XPATH = "./Properties/Property[@type='Part::PropertyGeometryList']"
    GEO_XPATH = "./GeometryList/Geometry[@type='Part::GeomLineSegment']"
    GEO_FIELDS = ("StartX", "StartY", "StartZ", "EndX", "EndY", "EndZ")
    FIELDS = ("FileUid", "SketchName", "ListName", "Id",) + GEO_FIELDS
    
    file_uid = tree.find("./Properties/Property[@name='Uid']/Uuid").get("value")
    data = []
    for sketch in tree.findall(SKETCH_XPATH):
        sketch_name = sketch.get(XMLAttr.NAME)
        for property_ in sketch.findall(GEO_LIST_XPATH):
            list_name = property_.get(XMLAttr.NAME)
            for geometry in property_.findall(GEO_XPATH):
                id_ = geometry.get(XMLAttr.ID)
                geo_element = geometry.find(XMLTag.LINE_SEGMENT)
                data.append(
                    (file_uid, sketch_name, list_name, id_)
                    + tuple(geo_element.get(field) for field in GEO_FIELDS)
                )
    return FIELDS, data

def read_circles(tree: ElementTree) -> tuple[tuple[str], list[tuple[str]]]:
    """Returns the fields and values of all Circles in the tree."""
    SKETCH_XPATH = ("./ObjectData/Object/Properties/Property[@name='Geometry']"
                    "/../..")
    GEO_LIST_XPATH = "./Properties/Property[@type='Part::PropertyGeometryList']"
    GEO_XPATH = "./GeometryList/Geometry[@type='Part::GeomCircle']"
    GEO_FIELDS = ("CenterX", "CenterY", "CenterZ",
                  "NormalX", "NormalY", "NormalZ",
                  "AngleXU", "Radius")
    FIELDS = ("FileUid", "SketchName", "ListName", "Id",) + GEO_FIELDS
    
    file_uid = tree.find("./Properties/Property[@name='Uid']/Uuid").get("value")
    data = []
    for sketch in tree.findall(SKETCH_XPATH):
        sketch_name = sketch.get(XMLAttr.NAME)
        for property_ in sketch.findall(GEO_LIST_XPATH):
            list_name = property_.get(XMLAttr.NAME)
            for geometry in property_.findall(GEO_XPATH):
                id_ = geometry.get(XMLAttr.ID)
                geo_element = geometry.find(XMLTag.CIRCLE)
                data.append(
                    (file_uid, sketch_name, list_name, id_)
                    + tuple(geo_element.get(field) for field in GEO_FIELDS)
                )
    return FIELDS, data

def write_fcstd_sql(fcstd: str, database: str):
    OBJECTS_TABLE = "FreecadObjects"
    SHARED_PROPERTIES = ["Label", "Label2", "Visibility"]
    
    with ZipFile(fcstd) as file:
        with file.open(SubFile.DOCUMENT_XML) as document:
            doc_tree = ElementTree.fromstring(document.read())
        with file.open(SubFile.GUI_DOCUMENT_XML) as gui_document:
            gui_tree = ElementTree.fromstring(gui_document.read())
    
    sketch_geometry = read_sketch_geometry_info(doc_tree)
    object_ids = read_sub_attrib(doc_tree.find(XMLTag.OBJECTS), XMLTag.OBJECT)
    dependencies = read_dependencies(doc_tree)
    constraints = read_sketch_constraints(doc_tree)
    metadata = read_metadata(doc_tree)
    object_info = read_object_info(doc_tree)
    breakpoint()
    
    # object_data = []
    # for name, id_ in object_ids.items():
        # shared = []
        # for property_name in SHARED_PROPERTIES:
            # *_, value = read_object_property(fcstd, name, property_name)
            # shared.append(value)
        # type_ = object_types[name]
        # object_data.append((name, id_, type_, *shared))
    
    # write_metadata(database, metadata)
    # write_constraints(database, constraints, file_uid)
    # write_objects_common(database, object_data, file_uid)
    # write_sketch_geometry(database, sketch_geometry, file_uid)
    # write_object_dependencies(database, dependencies, file_uid)