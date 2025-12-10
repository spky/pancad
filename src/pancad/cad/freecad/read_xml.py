"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

from pathlib import Path
import logging
import tomllib
from typing import TYPE_CHECKING

from pancad import resources

from .xml_properties import read_property_value, FreecadUnsupportedPropertyError
from .constants.archive_constants import Attr, Part, Sketcher, Tag

if TYPE_CHECKING:
    from typing import Any
    from xml.etree.ElementTree import Element, ElementTree
    from .constants.archive_constants import App, PartDesign

logger = logging.getLogger(__name__)

def _xml_config() -> dict[str, str]:
    """Returns the xml configuration dict of the freecad.toml file"""
    FREECAD_TOML = Path(resources.__file__).parent / "freecad.toml"
    with open(FREECAD_TOML, "rb") as file:
        return tomllib.load(file)["xml"]

def camera(tree: ElementTree) -> dict[str, str]:
    """Reads the camera settings of an FCStd file from the GuiDocument.xml."""
    type_field = _xml_config()["pancad"]["fields"]["camera_type"]
    
    element = tree.find(Tag.CAMERA)
    settings = element.get(Attr.SETTINGS)
    lines = settings.split("\n")
    IGNORE = ["", "}"]
    lines = [line.strip() for line in settings.split("\n") if line not in IGNORE]
    data = {}
    data[type_field] = lines.pop(0).split()[0]
    for line in lines:
        line_list = line.split()
        name = line_list.pop(0)
        data[name] = " ".join(line_list)
    return data

def dependencies(tree: str) -> list[dict[str, str]]:
    """Returns a list of all object dependency relations in the tree as dicts."""
    config = _xml_config()
    xpaths = config["xpaths"]
    fields = config["pancad"]["fields"]
    
    file_uid = tree.find(xpaths["FILE_UID"]).get(Attr.VALUE)
    
    data = []
    for deps in tree.findall(xpaths["OBJECT_DEPENDENCIES"]):
        name = deps.get(Attr.NAME_CAPITALIZED)
        for dep in deps.iter(Tag.DEP):
            data.append(
                {
                    fields["file_uid"]: file_uid,
                    Attr.NAME: name,
                    fields["depends_on"]: dep.get(Attr.NAME_CAPITALIZED),
                }
            )
    return data

def expand(expand: Element) -> set[str]:
    """Recursively reads the names that are expanded in an expand xml element."""
    all_expanded = set()
    if name := expand.get(Attr.NAME):
        all_expanded.add(name)
    for sub in expand.findall(Tag.EXPAND):
        for sub_name in read_expand(sub):
            all_expanded.add(sub_name)
    return all_expanded

def extensions(element: Element) -> list[tuple[str, str]]:
    """Finds and reads an Extensions element and provides a list of (type, name) 
    tuples for each one.
    """
    data = []
    if not (element := extendable.find(Tag.EXTENSIONS)):
        return data # Return empty list of no extensions found
    for ext in element.iter(Tag.EXTENSION):
        data.append((ext.get(Attr.TYPE), ext.get(Attr.NAME)))
    return data

def metadata(tree: ElementTree) -> list[dict[str, str]]:
    """Returns a tuple of field names and a tuple of values for FCStd metadata."""
    config = _xml_config()
    xpaths = config["xpaths"]
    fields = config["pancad"]["fields"]
    
    file_uid = tree.find(xpaths["FILE_UID"]).get(Attr.VALUE)
    
    data = []
    for element in tree.findall(xpaths["PROPERTY"]):
        try:
            value = read_property_value(element)
        except FreecadUnsupportedPropertyError as err:
            logger.warning(f"Unsupported metadata {err}")
            continue
        data.append(
            {
                fields["file_uid"]: file_uid,
                Attr.NAME: element.get(Attr.NAME),
                Attr.TYPE: element.get(Attr.TYPE),
                Attr.STATUS: element.get(Attr.STATUS),
                Attr.VALUE: value
            }
        )
    return data

def object_info(tree: ElementTree) -> list[dict[str, str]]:
    """Returns a tuple of field names and a tuple of values for fields common to 
    all objects in an FCStd document.xml tree.
    """
    config = _xml_config()
    xpaths = config["xpaths"]
    
    file_uid_field = config["pancad"]["fields"]["file_uid"]
    file_uid = tree.find(xpaths["FILE_UID"]).get(Attr.VALUE)
    shared_attributes = tuple(config["shared"]["object_attributes"])
    shared_properties = tuple(config["shared"]["object_properties"])
    
    info = []
    for object_ in tree.findall(xpaths["OBJECTS"]):
        object_name = object_.get(Attr.NAME)
        properties = {attr: object_.get(attr) for attr in shared_attributes}
        object_data = tree.find(xpaths["OBJECT_DATA"].format(object_name))
        for name in shared_properties:
            property_ = object_data.find(xpaths["PROPERTY_NAME"].format(name))
            value = read_property_value(property_)
            properties[name] = value
        info.append({file_uid_field: file_uid, **properties})
    return info

def object_type(tree: ElementTree,
                type_: App | Sketcher | PartDesign
                ) -> list[dict[str, str | dict[str, str] | list[str]]]:
    """Reads the properties all objects of a type from a FCStd file."""
    SKIP_TYPES = [Part.GEOMETRY_LIST, Sketcher.CONSTRAINT_LIST]
    # These types will be read by other functions
    
    config = _xml_config()
    xpaths = config["xpaths"]
    file_uid_field = config["pancad"]["fields"]["file_uid"]
    
    static_fields = (file_uid_field, *config["shared"]["object_attributes"])
    file_uid = tree.find(xpaths["FILE_UID"]).get(Attr.VALUE)
    
    # Read data into dicts
    data = []
    for object_ in tree.findall(xpaths["OBJECT_TYPE"].format(type_)):
        object_name = object_.attrib[Attr.NAME]
        properties = {file_uid_field: file_uid,
                      Attr.NAME: object_name,
                      Attr.ID: object_.attrib[Attr.ID]}
        properties.update({attr: object_.get(attr) for attr in static_fields
                           if attr not in properties})
        
        object_data = tree.find(xpaths["OBJECT_DATA"].format(object_name))
        for property_ in object_data.findall(xpaths["PROPERTY"]):
            if property_.get(Attr.TYPE) in SKIP_TYPES:
                continue
            property_name = property_.get(Attr.NAME)
            try:
                properties[property_name] = read_property_value(property_)
            except FreecadUnsupportedPropertyError as err:
                logger.warning(f"Skip {property_name} on {object_name}: {err}")
                properties[property_name] = err.__class__.__name__
        data.append(properties)
    return data

def object_types(tree: ElementTree) -> list[str]:
    """Returns the types of each object type in the file."""
    xpath = _xml_config()["xpaths"]["OBJECTS"]
    return list({obj.get(Attr.TYPE) for obj in tree.findall(xpath)})

def sketch_constraints(tree: ElementTree) -> list[dict[str, str]]:
    """Returns a tuple of field names and a tuple of values for each constraint"""
    fields = _xml_config()["pancad"]["fields"]
    static_fields = (fields["file_uid"], fields["sketch_name"])
    
    xpaths = _xml_config()["xpaths"]
    file_uid = tree.find(xpaths["FILE_UID"]).get(Attr.VALUE)
    sketch_xpath = xpaths["OBJECT_TYPE"].format(Sketcher.SKETCH)
    list_xpath = xpaths["PROPERTY_TYPE"].format(Sketcher.CONSTRAINT_LIST)
    
    dynamic_fields = []
    data = []
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(xpaths["OBJECT_DATA"].format(sketch_name))
        static = {fields["file_uid"]: file_uid,
                  fields["sketch_name"]: sketch_name}
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
    config = _xml_config()
    xpaths = config["xpaths"]
    fields = config["pancad"]["fields"]
    
    sketch_xpath = xpaths["OBJECT_TYPE"].format(Sketcher.SKETCH)
    geo_list_xpath = xpaths["PROPERTY_TYPE"].format(Part.GEOMETRY_LIST)
    geo_ext_xpath = xpaths["GEOMETRY_EXT"].format(Sketcher.GEOMETRY_EXT)
    geo_type_xpath = xpaths["GEOMETRY_TYPE"].format(type_)
    
    file_uid = tree.find(xpaths["FILE_UID"]).get(Attr.VALUE)
    
    dynamic_fields = []
    data = []
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(xpaths["OBJECT_DATA"].format(sketch_name))
        static = {fields["file_uid"]: file_uid,
                  fields["sketch_name"]: sketch_name}
        for property_ in sketch_data.findall(geo_list_xpath):
            
            for info in read_property_value(property_):
                if info[Attr.TYPE] != type_:
                    continue
                
                geometry = property_.find(geo_type_xpath)
                extension = geometry.find(geo_ext_xpath)
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
    config = _xml_config()
    xpaths = config["xpaths"]
    fields = config["pancad"]["fields"]
    
    file_uid = tree.find(xpaths["FILE_UID"]).get(Attr.VALUE)
    sketch_xpath = xpaths["OBJECT_TYPE"].format(Sketcher.SKETCH)
    geo_list_xpath = xpaths["PROPERTY_TYPE"].format(Part.GEOMETRY_LIST)
    STATIC_FIELDS = (fields["file_uid"], fields["sketch_name"])
    SHARED_FIELDS = (
        fields["list_name"],
        fields["list_index"],
        Attr.ID,
        Attr.TYPE,
        Attr.MIGRATED,
        Tag.CONSTRUCTION,
        Attr.INTERNAL_GEOMETRY_TYPE,
    )
    
    info = []
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(xpaths["OBJECT_DATA"].format(sketch_name))
        static = {fields["file_uid"]: file_uid,
                  fields["sketch_name"]: sketch_name}
        for property_ in sketch_data.findall(geo_list_xpath):
            geometry_info = read_property_value(property_)
            for geometry in geometry_info:
                geometry = {key: geometry[key] for key in geometry
                            if key not in SHARED_FIELDS}
                info.append({**static, **geometry})
    return info

def sketch_geometry_types(tree: ElementTree) -> list[str]:
    """Returns the types of each sketch geometry type in the file."""
    xpaths = _xml_config()["xpaths"]
    sketch_xpath = xpaths["OBJECT_TYPE"].format(Sketcher.SKETCH)
    geo_list_xpath = xpaths["PROPERTY_TYPE"].format(Part.GEOMETRY_LIST)
    
    types = set()
    for sketch in tree.findall(sketch_xpath):
        sketch_name = sketch.get(Attr.NAME)
        sketch_data = tree.find(xpaths["OBJECT_DATA"].format(sketch_name))
        for property_ in sketch_data.findall(geo_list_xpath):
            for geometry in property_.findall(xpaths["GEOMETRY_LIST"]):
                types.add(geometry.attrib[Attr.TYPE])
    return list(types)

def view_provider_properties(tree: ElementTree, name: str
                             ) -> dict[str, str | dict[str, str]]:
    """Reads the view provider properties associated with the object named 'name'
    
    :param tree: The ElementTree of a FCStd GuiDocument.xml
    :param name: The name of an object in the FCStd file
    """
    xpaths = _xml_config()["xpaths"]
    provider = tree.find(xpaths["VIEW_PROVIDER"].format(name))
    data = dict(provider.attrib)
    for property_ in provider.findall(xpaths["PROPERTY"]):
        data[property_.get(Attr.NAME)] = read_property_value(property_)
    return data