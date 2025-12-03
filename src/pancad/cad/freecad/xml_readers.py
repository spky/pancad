"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import logging
import tomllib
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree
from zipfile import ZipFile

from pancad import data as pancad_data

from .xml_properties import (
    read_properties, read_property, read_sketch_geometry_common
)
from .xml_appearance import read_shape_appearance
from .constants.archive_constants import (
    SubFile, Tag, Attr, XMLObjectType, PropertyType, Sketcher, Part
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

def read_sub_attrib(element: Element,
                    tag: Tag=None) -> tuple[tuple[str], list[tuple[str]]]:
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

def tuples_to_dicts(titles: tuple[str],
                    values: list[tuple[str]]) -> list[dict[str, str]]:
    """Converts a tuple of field titles and a list of value tuples to a list of 
    dictionaries with each value mapped to its respective title.
    """
    return [{name: value for name, value in zip(titles, row)} for row in values]

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
    file_uid = tree.find(FILE_UID_XPATH).get("value")
    data = []
    
    for element in tree.findall("./Properties/Property"):
        name = element.get(Attr.NAME)
        type_ = element.get(Attr.TYPE)
        status = element.get(Attr.STATUS)
        match type_:
            case XMLPropertyType.APP_STRING:
                value = element.find(Tag.STRING).get(Attr.VALUE)
            case XMLPropertyType.APP_BOOL:
                value = element.find(Tag.BOOL).get(Attr.VALUE)
            case XMLPropertyType.APP_UUID:
                value = element.find(Tag.UUID).get(Attr.VALUE)
            case XMLPropertyType.APP_ENUM:
                index = int(element.find(Tag.INTEGER).get(Attr.VALUE))
                enum_list = element.find(Tag.CUSTOM_ENUM_LIST)
                value = enum_list[index].get(Attr.VALUE)
            case _:
                logger.warning(f"Could not read metadata type {type_}")
                value = None
        data.append((file_uid, name, type_, status, value))
    FIELDS = [Attr.NAME, Attr.TYPE, Attr.STATUS, Attr.VALUE]
    return FIELDS, data

def read_dependencies(tree: str) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a dict of object name to a list of its dependencies from FCStd 
    files. The lists of dependencies may have duplicates.
    """
    file_uid = tree.find(FILE_UID_XPATH).get("value")
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
    file_uid = tree.find(FILE_UID_XPATH).get("value")
    STATIC_FIELDS = ("FileUid", "SketchName", "ListName", "ListIndex")
    dynamic_fields = []
    data = []
    sketch_xpath = OBJ_TYPE_XPATH.format(Sketcher.SKETCH)
    list_xpath = PROP_TYPE_REL_XPATH.format(Sketcher.CONSTRAINT_LIST)
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(OBJ_DATA_XPATH.format(sketch_name))
        for property_ in sketch_data.findall(list_xpath):
            list_name = property_.get(Attr.NAME)
            constraint_list = property_.find(Tag.CONSTRAINT_LIST)
            fields, values = read_sub_attrib(constraint_list, Tag.CONSTRAINT)
            # Ensure that all fields are in the same order by mapping them first
            attribs = tuples_to_dicts(fields, values)
            dynamic_fields.extend(f for f in fields if f not in dynamic_fields)
            for list_index, attrib in enumerate(attribs):
                static = (file_uid, sketch_name, list_name, list_index)
                dynamic = tuple(attrib.setdefault(f) for f in dynamic_fields)
                data.append(static + dynamic)
    return STATIC_FIELDS + tuple(dynamic_fields), data

def read_sketch_geometry_info(tree: ElementTree) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a tuple of field names and a tuple of values in common for each 
    sketch geometry element in the tree.
    """
    sketch_geometry = []
    file_uid = tree.find(FILE_UID_XPATH).get("value")
    sketch_xpath = OBJ_TYPE_XPATH.format(Sketcher.SKETCH)
    geo_list_xpath = PROP_TYPE_REL_XPATH.format(Part.GEOMETRY_LIST)
    sketch_ext_xpath = GEO_EXT_REL_XPATH.format(Sketcher.GEOMETRY_EXT)
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(OBJ_DATA_XPATH.format(sketch_name))
        for property_ in sketch_data.findall(geo_list_xpath):
            list_name = property_.get(Attr.NAME)
            geometry_list = property_.find(Tag.GEOMETRY_LIST)
            for list_index, geometry in enumerate(geometry_list):
                construction = geometry.find(Tag.CONSTRUCTION)
                sketch_ext = geometry.find(sketch_ext_xpath)
                sketch_geometry.append(
                    (
                        file_uid, sketch_name, list_name, list_index,
                        geometry.get(Attr.TYPE),
                        geometry.get(Attr.ID),
                        geometry.get(Attr.MIGRATED),
                        construction.get(Attr.VALUE),
                        sketch_ext.get(Attr.INTERNAL_GEOMETRY_TYPE)
                    )
                )
    FIELDS = ("FileUid", "SketchName", "ListName", "ListIndex",
              Attr.ID, Attr.TYPE, Attr.MIGRATED, Tag.CONSTRUCTION,
              Attr.INTERNAL_GEOMETRY_TYPE)
    return FIELDS, sketch_geometry

def read_object_info(tree: ElementTree) -> tuple[tuple[str], list[tuple[str]]]:
    """Returns a tuple of field names and a tuple of values for fields common to 
    all objects in an FCStd document.xml tree.
    """
    info = []
    file_uid = tree.find(FILE_UID_XPATH).get("value")
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
            properties.append(
                tree.find(PROPERTY_XPATH % (name, prop, tag)).get(Attr.VALUE)
            )
        info.append((file_uid,) + tuple(properties))
    return ("FileUid",) + tuple(fields), info

def get_sketch_geometry_types(tree: ElementTree) -> list[tuple[str, str]]:
    """Returns the types and tags of each geometry type in the file."""
    types = set()
    sketch_xpath = OBJ_TYPE_XPATH.format(Sketcher.SKETCH)
    geo_list_xpath = PROP_TYPE_REL_XPATH.format(Part.GEOMETRY_LIST)
    GEOMETRY_XPATH = "./GeometryList/Geometry"
    NON_GEOMETRY_TAGS = {Tag.GEOMETRY_EXTENSIONS, Tag.CONSTRUCTION}
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(OBJ_DATA_XPATH.format(sketch_name))
        for property_ in sketch_data.findall(geo_list_xpath):
            for geometry in property_.findall(GEOMETRY_XPATH):
                type_ = geometry.get(Attr.TYPE)
                tags = {element.tag for element in geometry} - NON_GEOMETRY_TAGS
                if len(tags) == 1:
                    types.add((geometry.get(Attr.TYPE), tags.pop()))
                else:
                    raise ValueError("Found multiple non-geometry tags!")
    return list(types)

def read_sketch_geometry(tree: ElementTree,
                         type_: Part,
                         tag: Tag) -> tuple[tuple[str], list[tuple[str]]]:
    """Returns the fields and dimensions of all sketch geometries in an FCStd file.
    
    :param tree: An ElementTree of the document.xml file.
    :param type_: A type attribute value of a parent Geometry tag.
    :param tag: A tag name of an element under the parent Geometry tag.
    """
    ELEMENT_XPATH = "./GeometryList/Geometry[@type='%s']"
    file_uid = tree.find(FILE_UID_XPATH).get("value")
    data = []
    STATIC_FIELDS = ("FileUid", "SketchName", "ListName", Attr.ID)
    dynamic_fields = []
    sketch_xpath = OBJ_TYPE_XPATH.format(Sketcher.SKETCH)
    geo_list_xpath = PROP_TYPE_REL_XPATH.format(Part.GEOMETRY_LIST)
    element_xpath = GEOMETRY_TYPE_XPATH.format(type_)
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(OBJ_DATA_XPATH.format(sketch_name))
        for property_ in sketch_data.findall(geo_list_xpath):
            list_name = property_.get(Attr.NAME)
            for geometry in property_.findall(element_xpath):
                id_ = geometry.get(Attr.ID)
                element = geometry.find(tag)
                dynamic_fields.extend(name for name in element.attrib
                                      if name not in dynamic_fields)
                static = (file_uid, sketch_name, list_name, id_)
                dynamic = tuple(element.attrib[name] for name in dynamic_fields)
                data.append(static + dynamic)
    return STATIC_FIELDS + tuple(dynamic_fields), data

def write_fcstd_sql(fcstd: str, database: str):
    OBJECTS_TABLE = "FreecadObjects"
    SHARED_PROPERTIES = ["Label", "Label2", "Visibility"]
    
    with ZipFile(fcstd) as file:
        with file.open(SubFile.DOCUMENT_XML) as document:
            doc_tree = ElementTree.fromstring(document.read())
        with file.open(SubFile.GUI_DOCUMENT_XML) as gui_document:
            gui_tree = ElementTree.fromstring(gui_document.read())
    
    sketch_geometry = read_sketch_geometry_info(doc_tree)
    object_ids = read_sub_attrib(doc_tree.find(Tag.OBJECTS), Tag.OBJECT)
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