"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import logging
import tomllib
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree
from zipfile import ZipFile

from .xml_properties import (
    read_properties, read_property_value, FreecadUnsupportedPropertyError
)
from .xml_appearance import read_shape_appearance
from .constants.archive_constants import (
    SubFile, Tag, Attr, PropertyType, Sketcher, Part, App
)

if TYPE_CHECKING:
    from pathlib import Path
    from xml.etree.ElementTree import Element

logger = logging.getLogger(__name__)

### Document.xml XPath Templates
FILE_UID_XPATH = "./Properties/Property[@name='Uid']/Uuid"
"""Get the Uuid element in an FCStd's document.xml file."""
OBJ_TYPE_XPATH = "./Objects/Object[@type='{}']"
"""Get all object(s) of a type"""
OBJ_DATA_XPATH = "./ObjectData/Object[@name='{}']"
"""Get object named name."""
PROP_TYPE_REL_XPATH = "./Properties/Property[@type='{}']"
"""Get Property element(s) under an Object element of a type."""
GEO_EXT_REL_XPATH = "./GeoExtensions/GeoExtension[@type='{}']"
"""Get GeoExtension element(s) under a Geometry element of a type."""
GEOMETRY_TYPE_XPATH = "./GeometryList/Geometry[@type='{}']"
"""Gets a Geometry element under a geometry list type element of a type."""

def read_objects(objects: Element) -> list[tuple[str, str, int]]:
    """Reads the objects inside an Objects element
    
    :param element: The Objects element with Object elements underneath.
    :returns: A list of (Name, Type, ID) tuples for each object.
    """
    data = []
    for object_ in objects.iter(Tag.OBJECT):
        name = object_.get(Attr.NAME)
        type_ = object_.get(Attr.TYPE)
        id_ = int(object_.get(Attr.ID))
        data.append((name, type_, id_))
    return data

def read_expand(expand: Element) -> set[str]:
    """Recursively reads the names that are expanded in an expand xml element."""
    all_expanded = set()
    if name := expand.get(Attr.NAME):
        all_expanded.add(name)
    for sub in expand.findall(Tag.EXPAND):
        for sub_name in read_expand(sub):
            all_expanded.add(sub_name)
    return all_expanded

def read_extensions(extensions: Element) -> list[tuple[str, str]]:
    """Finds and reads an Extensions element and provides a list of (type, name) 
    tuples for each one.
    """
    data = []
    if not (extensions := extendable.find(Tag.EXTENSIONS)):
        return data # Return empty list of no extensions found
    for ext in extensions.iter(Tag.EXTENSION):
        data.append((ext.get(Attr.TYPE), ext.get(Attr.NAME)))
    return data

def read_view_provider_data(view_provider_data: Element
                            ) -> list[tuple[dict[str, str], list, list]]:
    """Reads ViewProvider elements from a ViewProviderData element as a list of 
    (attributes, extensions, properties) tuples.
    """
    data = []
    for provider in view_provider_data.iter(Tag.VIEW_PROVIDER):
        extensions = read_extensions(provider)
        properties = read_properties(provider.find(Tag.PROPERTIES))
        attributes = dict(provider.attrib)
        data.append((attributes, extensions, properties))
    return data

def read_metadata(tree: ElementTree) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a tuple of field names and a tuple of values for FCStd metadata."""
    file_uid = tree.find(FILE_UID_XPATH).get(Attr.VALUE)
    data = []
    
    for element in tree.findall("./Properties/Property"):
        name = element.get(Attr.NAME)
        type_ = element.get(Attr.TYPE)
        status = element.get(Attr.STATUS)
        try:
            value = read_property_value(element)
        except FreecadUnsupportedPropertyError as err:
            logger.warning(f"Unsupported metadata {err}")
            continue
        data.append((file_uid, name, type_, status, value))
    FIELDS = [Attr.NAME, Attr.TYPE, Attr.STATUS, Attr.VALUE]
    return FIELDS, data

def read_dependencies(tree: str) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a dict of object name to a list of its dependencies from FCStd 
    files. The lists of dependencies may have duplicates.
    """
    file_uid = tree.find(FILE_UID_XPATH).get(Attr.VALUE)
    OBJECT_DEPS_XPATH = f"./Objects/ObjectDeps"
    FIELDS = ["FileUid", "Object", "Dependency"]
    data = []
    for deps in tree.findall(OBJECT_DEPS_XPATH):
        name = deps.get(Attr.NAME_CAPITALIZED)
        depends_on = [
            dep.get(Attr.NAME_CAPITALIZED) for dep in deps.iter(Tag.DEP)
        ]
        data.extend([(file_uid, name, dep) for dep in depends_on])
    return FIELDS, data

def read_sketch_constraints(tree: ElementTree) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a tuple of field names and a tuple of values for each constraint"""
    file_uid = tree.find(FILE_UID_XPATH).get(Attr.VALUE)
    STATIC_FIELDS = ("FileUid", "SketchName")
    dynamic_fields = []
    data = []
    sketch_xpath = OBJ_TYPE_XPATH.format(Sketcher.SKETCH)
    list_xpath = PROP_TYPE_REL_XPATH.format(Sketcher.CONSTRAINT_LIST)
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(OBJ_DATA_XPATH.format(sketch_name))
        static = (file_uid, sketch_name)
        for property_ in sketch_data.findall(list_xpath):
            constraints = read_property_value(property_)
            for info in constraints:
                dynamic_fields.extend(name for name in info
                                      if name not in dynamic_fields)
            for info in constraints:
                dynamic = tuple(info.setdefault(f) for f in dynamic_fields)
                data.append(static + dynamic)
    return STATIC_FIELDS + tuple(dynamic_fields), data

def read_sketch_geometry_info(tree: ElementTree) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a tuple of field names and a tuple of values in common for each 
    sketch geometry element in the tree.
    """
    file_uid = tree.find(FILE_UID_XPATH).get(Attr.VALUE)
    sketch_xpath = OBJ_TYPE_XPATH.format(Sketcher.SKETCH)
    geo_list_xpath = PROP_TYPE_REL_XPATH.format(Part.GEOMETRY_LIST)
    STATIC_FIELDS = ("FileUid", "SketchName")
    SHARED_FIELDS = (
        "ListName",
        "ListIndex",
        Attr.ID,
        Attr.TYPE,
        Attr.MIGRATED,
        Tag.CONSTRUCTION,
        Attr.INTERNAL_GEOMETRY_TYPE,
    )
    
    sketch_geometry = []
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(OBJ_DATA_XPATH.format(sketch_name))
        sketch_fields = (file_uid, sketch_name)
        for property_ in sketch_data.findall(geo_list_xpath):
            geometry_info = read_property_value(property_)
            for geometry in geometry_info:
                sketch_geometry.append(
                    sketch_fields
                    + tuple(geometry[field] for field in SHARED_FIELDS)
                )
    return STATIC_FIELDS + SHARED_FIELDS, sketch_geometry

def read_object_info(tree: ElementTree) -> tuple[tuple[str], list[tuple[str]]]:
    """Returns a tuple of field names and a tuple of values for fields common to 
    all objects in an FCStd document.xml tree.
    """
    info = []
    file_uid = tree.find(FILE_UID_XPATH).get(Attr.VALUE)
    PROPERTY_XPATH = ("./ObjectData/Object[@name='%s']"
                      "/Properties/Property[@name='%s']/%s")
    SHARED_ATTR = [Attr.NAME, Attr.ID, Attr.TYPE]
    SHARED_DATA = [
        ("Label", Tag.STRING),
        ("Label2", Tag.STRING),
        ("Visibility", Tag.BOOL),
    ]
    fields = SHARED_ATTR + [name for name, _ in SHARED_DATA]
    for obj in tree.findall("./Objects/Object"):
        name = obj.get(Attr.NAME)
        properties = [obj.get(attr) for attr in SHARED_ATTR]
        for prop, tag in SHARED_DATA:
            value = tree.find(PROPERTY_XPATH % (name, prop, tag)).get(Attr.VALUE)
            if tag == Tag.BOOL:
                properties.append(value == "true")
            else:
                properties.append(value)
        info.append((file_uid,) + tuple(properties))
    return ("FileUid",) + tuple(fields), info

def get_sketch_geometry_types(tree: ElementTree) -> list[str]:
    """Returns the types and tags of each geometry type in the file."""
    GEOMETRY_XPATH = "./GeometryList/Geometry"
    sketch_xpath = OBJ_TYPE_XPATH.format(Sketcher.SKETCH)
    geo_list_xpath = PROP_TYPE_REL_XPATH.format(Part.GEOMETRY_LIST)
    
    types = set()
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(OBJ_DATA_XPATH.format(sketch_name))
        for property_ in sketch_data.findall(geo_list_xpath):
            for geometry in property_.findall(GEOMETRY_XPATH):
                types.add(geometry.attrib[Attr.TYPE])
    return list(types)

def read_sketch_geometry(tree: ElementTree,
                         type_: Part) -> tuple[tuple[str], list[tuple[str]]]:
    """Returns the fields and dimensions of all sketch geometries in an FCStd file.
    
    :param tree: An ElementTree of the document.xml file.
    :param type_: A type attribute value of a parent Geometry tag.
    """
    STATIC_FIELDS = ("FileUid", "SketchName")
    sketch_xpath = OBJ_TYPE_XPATH.format(Sketcher.SKETCH)
    geo_list_xpath = PROP_TYPE_REL_XPATH.format(Part.GEOMETRY_LIST)
    geo_ext_xpath = GEO_EXT_REL_XPATH.format(Sketcher.GEOMETRY_EXT)
    
    geo_xpath = GEOMETRY_TYPE_XPATH.format(type_)
    file_uid = tree.find(FILE_UID_XPATH).get(Attr.VALUE)
    
    dynamic_fields = []
    data = []
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(OBJ_DATA_XPATH.format(sketch_name))
        static = (file_uid, sketch_name)
        for property_ in sketch_data.findall(geo_list_xpath):
            
            for info in read_property_value(property_):
                if info[Attr.TYPE] != type_:
                    continue
                
                geometry = property_.find(geo_xpath)
                extension = geometry.find(geo_ext_xpath)
                ignore_fields = set(geometry.attrib) | set(extension.attrib) 
                ignore_fields.remove(Attr.ID)
                
                for field in ignore_fields:
                    info.pop(field, None)
                dynamic_fields.extend(name for name in info
                                      if name not in dynamic_fields)
                dynamic = tuple(info[name] for name in dynamic_fields)
                data.append(static + dynamic)
    return STATIC_FIELDS + tuple(dynamic_fields), data

def read_sketch_info(tree: ElementTree) -> tuple[tuple[str], list[tuple[str]]]:
    """Returns the properties unique to sketches in an FCStd file."""
    sketch_xpath = OBJ_TYPE_XPATH.format(Sketcher.SKETCH)