"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

from functools import cache
from pathlib import Path
import logging
import tomllib
from typing import TYPE_CHECKING

from pancad import resources

from .xml_properties import (
    read_property_value,
    FreecadPropertyValueType,
    FreecadUnsupportedPropertyError,
)
from .constants.archive_constants import Attr, Part, Sketcher, Tag

if TYPE_CHECKING:
    from typing import Any
    from xml.etree.ElementTree import Element, ElementTree
    from .constants.archive_constants import App, PartDesign

@cache
def _xml_config() -> dict[str, str]:
    """Returns the xml configuration dict of the freecad.toml file"""
    with open(Path(resources.__file__).parent / FREECAD_TOML, "rb") as file:
        return tomllib.load(file)["xml"]

logger = logging.getLogger(__name__)
FREECAD_TOML = "freecad.toml"
XML_CONFIG = _xml_config()
XPATHS = XML_CONFIG["xpaths"]
FIELDS = XML_CONFIG["pancad"]["fields"]
SHARED = XML_CONFIG["shared"]
SKETCH_XPATH = XPATHS["OBJECT_TYPE"].format(Sketcher.SKETCH)
GEO_LIST_XPATH = XPATHS["PROPERTY_TYPE"].format(Part.GEOMETRY_LIST)
GEO_EXT_XPATH = XPATHS["GEOMETRY_EXT"].format(Sketcher.GEOMETRY_EXT)

def camera(tree: ElementTree) -> dict[str, str]:
    """Reads the camera settings of an FCStd file from the GuiDocument.xml."""
    type_field = XML_CONFIG["pancad"]["fields"]["camera_type"]
    element = tree.find(Tag.CAMERA)
    settings = element.get(Attr.SETTINGS)
    lines = settings.split("\n")
    lines = [line.strip() for line in settings.split("\n")
             if line not in ["", "}"]]
    data = {}
    data[type_field] = lines.pop(0).split()[0]
    for line in lines:
        line_list = line.split()
        name = line_list.pop(0)
        data[name] = " ".join(line_list)
    return data

def dependencies(tree: str) -> list[dict[str, str]]:
    """Returns a list of all object dependency relations in the tree as dicts."""
    file_uid = tree.find(XPATHS["FILE_UID"]).get(Attr.VALUE)
    data = []
    for deps in tree.findall(XPATHS["OBJECT_DEPENDENCIES"]):
        name = deps.get(Attr.NAME_CAPITALIZED)
        for dep in deps.iter(Tag.DEP):
            data.append(
                {
                    FIELDS["file_uid"]: file_uid,
                    Attr.NAME: name,
                    FIELDS["depends_on"]: dep.get(Attr.NAME_CAPITALIZED),
                }
            )
    return data

def expand(element: Element) -> set[str]:
    """Recursively reads the names that are expanded in an expand xml element."""
    all_expanded = set()
    if name := element.get(Attr.NAME):
        all_expanded.add(name)
    for sub in element.findall(Tag.EXPAND):
        for sub_name in expand(sub):
            all_expanded.add(sub_name)
    return all_expanded

def metadata(tree: ElementTree) -> list[dict[str, FreecadPropertyValueType]]:
    """Returns a tuple of field names and a tuple of values for FCStd metadata."""
    file_uid = tree.find(XPATHS["FILE_UID"]).get(Attr.VALUE)
    data = []
    for element in tree.findall(XPATHS["PROPERTY"]):
        try:
            value = read_property_value(element)
        except FreecadUnsupportedPropertyError as err:
            logger.warning("Unsupported metadata %s", err)
            continue
        data.append(
            {
                FIELDS["file_uid"]: file_uid,
                Attr.NAME: element.get(Attr.NAME),
                Attr.TYPE: element.get(Attr.TYPE),
                Attr.STATUS: element.get(Attr.STATUS),
                Attr.VALUE: value
            }
        )
    return data

def object_info(tree: ElementTree) -> list[dict[str, FreecadPropertyValueType]]:
    """Returns a tuple of field names and a tuple of values for fields common to 
    all objects in an FCStd document.xml tree.
    """
    file_uid = tree.find(XPATHS["FILE_UID"]).get(Attr.VALUE)
    info = []
    for object_ in tree.findall(XPATHS["OBJECTS"]):
        object_name = object_.get(Attr.NAME)
        properties = {attr: object_.get(attr)
                      for attr in SHARED["object_attributes"]}
        object_data = tree.find(XPATHS["OBJECT_DATA"].format(object_name))
        for name in SHARED["object_properties"]:
            property_ = object_data.find(XPATHS["PROPERTY_NAME"].format(name))
            value = read_property_value(property_)
            properties[name] = value
        info.append({FIELDS["file_uid"]: file_uid, **properties})
    return info

def object_type(tree: ElementTree,
                type_: App | Sketcher | PartDesign
                ) -> list[dict[str, FreecadPropertyValueType]]:
    """Reads the properties all objects of a type from a FCStd file."""
    # These types will be read by other functions
    static_fields = (FIELDS["file_uid"], *SHARED["object_attributes"])
    file_uid = tree.find(XPATHS["FILE_UID"]).get(Attr.VALUE)
    # Read data into dicts
    data = []
    for object_ in tree.findall(XPATHS["OBJECT_TYPE"].format(type_)):
        object_name = object_.attrib[Attr.NAME]
        properties = {FIELDS["file_uid"]: file_uid,
                      Attr.NAME: object_name,
                      Attr.ID: object_.attrib[Attr.ID]}
        properties.update({attr: object_.get(attr) for attr in static_fields
                           if attr not in properties})
        object_data = tree.find(XPATHS["OBJECT_DATA"].format(object_name))
        for property_ in object_data.findall(XPATHS["PROPERTY"]):
            if property_.get(Attr.TYPE) in [Part.GEOMETRY_LIST,
                                            Sketcher.CONSTRAINT_LIST]:
                continue
            property_name = property_.get(Attr.NAME)
            try:
                properties[property_name] = read_property_value(property_)
            except FreecadUnsupportedPropertyError as err:
                logger.warning("Skip %s on %s: %s",
                               property_name, object_name, err)
                properties[property_name] = err.__class__.__name__
        data.append(properties)
    return data

def object_types(tree: ElementTree) -> list[str]:
    """Returns the types of each object type in the file."""
    xpath = _xml_config()["xpaths"]["OBJECTS"]
    return list({obj.get(Attr.TYPE) for obj in tree.findall(xpath)})

def sketch_constraints(tree: ElementTree) -> list[dict[str, str]]:
    """Returns a tuple of field names and a tuple of values for each constraint"""
    file_uid = tree.find(XPATHS["FILE_UID"]).get(Attr.VALUE)
    list_xpath = XPATHS["PROPERTY_TYPE"].format(Sketcher.CONSTRAINT_LIST)
    data = []
    for sketch in tree.findall(SKETCH_XPATH):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(XPATHS["OBJECT_DATA"].format(sketch_name))
        static = {FIELDS["file_uid"]: file_uid,
                  FIELDS["sketch_name"]: sketch_name}
        for property_ in sketch_data.findall(list_xpath):
            constraints = read_property_value(property_)
            for info in constraints:
                data.append({**static, **info})
    return data

def sketch_geometry(tree: ElementTree, type_: Part) -> list[dict[str, str]]:
    """Returns the fields and dimensions of all sketch geometry elements in an 
    FCStd file.
    
    :param tree: An ElementTree of the document.xml file.
    :param type_: A type attribute value of a parent Geometry tag.
    """
    file_uid = tree.find(XPATHS["FILE_UID"]).get(Attr.VALUE)
    geo_type_xpath = XPATHS["GEOMETRY_TYPE"].format(type_)
    data = []
    for sketch in tree.findall(SKETCH_XPATH):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(XPATHS["OBJECT_DATA"].format(sketch_name))
        static = {FIELDS["file_uid"]: file_uid,
                  FIELDS["sketch_name"]: sketch_name}
        for property_ in sketch_data.findall(GEO_LIST_XPATH):
            for info in read_property_value(property_):
                if info[Attr.TYPE] != type_:
                    continue
                geometry = property_.find(geo_type_xpath)
                extension = geometry.find(GEO_EXT_XPATH)
                ignore_fields = set(geometry.attrib) | set(extension.attrib)
                ignore_fields.remove(Attr.ID)
                for field in ignore_fields:
                    info.pop(field, None)
                data.append({**static, **info})
    return data

def sketch_geometry_info(tree: ElementTree) -> list[dict[str, str]]:
    """Returns a tuple of field names and a tuple of values in common for each 
    sketch geometry element in the tree.
    """
    file_uid = tree.find(XPATHS["FILE_UID"]).get(Attr.VALUE)
    shared_fields = (
        FIELDS["list_name"],
        FIELDS["list_index"],
        Attr.ID,
        Attr.TYPE,
        Attr.MIGRATED,
        Tag.CONSTRUCTION,
        Attr.INTERNAL_GEOMETRY_TYPE,
    )
    info = []
    for sketch in tree.findall(SKETCH_XPATH):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(XPATHS["OBJECT_DATA"].format(sketch_name))
        static = {FIELDS["file_uid"]: file_uid,
                  FIELDS["sketch_name"]: sketch_name}
        for property_ in sketch_data.findall(GEO_LIST_XPATH):
            geometry_info = read_property_value(property_)
            for geometry in geometry_info:
                geometry = {key: geometry[key] for key in geometry
                            if key in shared_fields}
                info.append({**static, **geometry})
    return info

def sketch_geometry_types(tree: ElementTree) -> list[str]:
    """Returns the types of each sketch geometry type in the file."""
    types = set()
    for sketch in tree.findall(SKETCH_XPATH):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(XPATHS["OBJECT_DATA"].format(sketch_name))
        for property_ in sketch_data.findall(GEO_LIST_XPATH):
            for geometry in property_.findall(XPATHS["GEOMETRY_LIST"]):
                types.add(geometry.attrib[Attr.TYPE])
    return list(types)

def view_provider_properties(tree: ElementTree, name: str
                             ) -> dict[str, FreecadPropertyValueType]:
    """Reads the view provider properties associated with the object named 'name'
    
    :param tree: The ElementTree of a FCStd GuiDocument.xml
    :param name: The name of an object in the FCStd file
    """
    provider = tree.find(XPATHS["VIEW_PROVIDER"].format(name))
    data = dict(provider.attrib)
    for property_ in provider.findall(XPATHS["PROPERTY"]):
        data[property_.get(Attr.NAME)] = read_property_value(property_)
    return data
