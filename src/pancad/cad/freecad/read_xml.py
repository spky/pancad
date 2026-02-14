"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

import dataclasses
from functools import singledispatchmethod
from collections import namedtuple
from functools import cache
from pathlib import Path
import logging
import tomllib
from typing import TYPE_CHECKING
import warnings

from pancad import resources

from .xml_properties import (
    read_property_value,
    FreecadPropertyValueType,
    FreecadUnsupportedPropertyError,
)
from .constants.archive_constants import Attr, Part, Sketcher, Tag
from xml.etree import ElementTree as ET

if TYPE_CHECKING:
    from typing import Any, NoReturn
    from os import PathLike
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

ObjectIdInfo = namedtuple("ObjectIdInfo", ["name", "id_", "type_"])
LinkSubSub = namedtuple("LinkSubSub", ["name", "shadow"])

@dataclasses.dataclass
class FreeCADLinkSubSub:
    """A class for tracking the sub names and shadows of a FreeCAD LinkSub."""
    name: str
    shadow: str = None

@dataclasses.dataclass
class FreeCADLinkSub:
    """A class for tracking FreeCAD App::PropertyLinkSub data. See 
    https://freecad.github.io/SourceDoc/d3/d76/classApp_1_1PropertyLinkSub.html

    :param name: The object the link is to.
    :param subs: The linked subelement names of the object.
    :param shadows: Not certain, but appears to be "shadow subname references" 
        in FreeCAD documentation.
    """
    name: str
    subs: list[LinkSubSub] = dataclasses.field(default_factory=list)


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

def dependencies(tree: ElementTree) -> list[dict[str, str]]:
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

def get_objectdata(tree: ElementTree, name: str) -> Element:
    """Returns an ObjectData element based on its name.

    :param tree: A FCStd document xml ElementTree.
    :param name: The name of the object.
    :raises LookupError: When no object with the name is found.
    """
    xpath = XPATHS["OBJECT_DATA"].format(name)
    data = tree.find(xpath)
    if data is None:
        raise LookupError(f"No ObjectData named '{name}' was found", name)
    return data

def get_linked_parents(tree: ElementTree, name: str) -> list[str]:
    """Returns the list of parent object names required to create the object by 
    its name. Due to the structure of FCStds this is not a complete list.
    """
    xpath = r"./Properties/Property[@type='App::PropertyLinkSubList']"
    # parent_link_sublist_names = [
        # "AttachmentSupport",
        # "ExternalGeometry",
    # ]
    # xpaths = [template.format(name) for name in parent_link_sublist_names]
    # link_groups = [data.find(x) for x in xpaths]
    data = get_objectdata(tree, name)
    links = []
    links.extend(data.findall(xpath))
    if name.startswith("Sketch"):
        breakpoint()
    # for group in link_groups:
        # if group is None:
            # continue
        # breakpoint()
        # links.append(group)
    return links

def get_linked_children(tree: ElementTree, name: str) -> list[str]:
    """Returns the list of children object names that require the object by its 
    name. Due to the structure of FCStds this is not a complete list.
    """

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

class FreeCADDocumentXML:
    """A class providing an interface to FCStd Document.xml files.

    :param tree: An xml ElementTree read from a FCStd Document.xml file.
    :raises ValueError: When the xml tree is an invalid Document.xml format.
    """
    tag = "Document"
    """The nominal tag of the element in xml."""

    def __init__(self, tree: ElementTree):
        schema_version = "SchemaVersion"
        self._tree = tree
        try:
            self._schema_version = int(tree.attrib[schema_version])
        except KeyError as exc:
            msg = f"Invalid Document.xml, could not find {schema_version}"
            raise ValueError(msg, tree) from exc
        except (ValueError, TypeError) as exc:
            raw_schema_version = tree.get(schema_version)
            msg = (f"Document.xml {schema_version} is not int-like. Either"
                   " invalid Document.xml or FreeCAD changed their format")
            raise ValueError(msg, tree) from exc
        if self.schema_version != 4:
            warnings.warn(f"SchemaVersion {self.schema_version} not recognized,"
                          " invalid translation behavior may occur")
        self._objects = self._read_all_objectdata()
        self._properties = self._read_properties()

    @classmethod
    def from_string(cls, string: str) -> FreeCADDocumentXML:
        """Returns a FreeCADDocumentFile from an already read Document.xml 
        string. Example use: FreeCAD API docs have a string Content property.
        """
        return cls(ET.fromstring(string))

    # Properties
    @property
    def schema_version(self) -> int:
        return self._schema_version

    @property
    def objects(self) -> list[FreeCADObjectXML]:
        """Returns all objects inside this document."""
        return self._objects

    @property
    def properties(self) -> list[FreeCADPropertyXML]:
        """The list of document properties read from the xml Properties list."""
        return self._properties

    @property
    def uid(self) -> str:
        """The has-to-be-unique pancad calculated id for this element."""
        return f"{self.get_property('Uid').value}_document"

    def get_object(self, id_: str | int) -> FreeCADObjectXML:
        """Returns the FreeCADObjectXML object with the provided id.

        :param id_: The unique name or integer id of the object. The integer id 
            can be a string.
        :raises LookupError: When the id_ is not in the document.
        """
        try:
            id_info = self._get_object_id_info(id_)
        except LookupError as exc:
            exc.add_note(f"Could not find Object id '{id_}' the document")
            raise
        # If this gets a StopIteration error, the xml and object are out of sync
        return next(obj for obj in self.objects if obj.name == id_info.name)

    def get_property(self, name: str) -> FreeCADPropertyXML:
        """Returns the FreeCADPropertyXML object with the provided name."""
        try:
            return next(p for p in self.properties if p.name == name)
        except StopIteration as exc:
            raise LookupError(f"Could not find property '{name}'", name)

    # Private Methods
    def _get_object_id_info(self, id_: str | int=None
                           ) -> ObjectIdInfo | list[ObjectIdInfo]:
        """Finds one or all object info tuples in the document

        :param id_: Either the integer id or the string unique name of an
            object. The integer id can be a string digit.
        :returns: The ObjectIdInfo of all objects in the document when id_ is 
            None, or the one ObjectIdInfo when id_ is not None.
        :raises LookupError: When the id could not be found in the document.
        """
        xpath = "Objects/Object"
        props = ["name", "id", "type"]
        if id_ is None:
            all_info = []
            for obj in self._tree.findall(xpath):
                all_info.append(ObjectIdInfo(*[obj.attrib[p] for p in props]))
            return all_info
        # Single ObjectIdInfo
        if isinstance(id_, int) or (isinstance(id_, str) and id_.isdigit()):
            xpath = xpath + f"[@id='{id_}']"
        else:
            xpath = xpath + f"[@name='{id_}']"
        obj = self._tree.find(xpath)
        if obj is None:
            raise LookupError("Could not find object id in tree", id_)
        return ObjectIdInfo(*[obj.attrib[p] for p in props])

    def _read_all_objectdata(self) -> FreeCADObjectXML:
        """Reads all objects from the ObjectData/Object list into 
        FreeCADObjectXML objects.
        """
        name_map = {info.name: info for info in self._get_object_id_info()}
        objects = []
        for obj in self._tree.findall("ObjectData/Object"):
            info = name_map[obj.attrib["name"]]
            objects.append(FreeCADObjectXML(obj, info.id_, info.type_, self))
        return objects

    def _read_properties(self) -> list[FreeCADPropertyXML]:
        """Reads the properties of the document into a list of interfacing 
        objects.
        """
        properties = []
        property_list = self._tree.find("Properties")
        if property_list is None:
            msg = "Unexpected Document format: could not find Properties element"
            raise ValueError(msg, self._tree)
        for prop in property_list:
            properties.append(FreeCADPropertyXML(prop, self))
        return properties

class FreeCADObjectXML:
    """A class providing an interface to FCStd Document.xml xml object elements.

    :param element: The xml ObjectData Object element for the object from the 
        Document.xml tree.
    :param id_: The id from the Document.xml tree Objects list.
    :param type_: The type from the Document.xml tree Objects list.
    :param document: The document this object is inside of.
    """
    tag = "Object"
    """The nominal tag of the element in xml."""

    def __init__(self, element: Element, id_: int, type_: str,
                 document: FreeCADDocumentXML):
        try:
            self._name = element.attrib["name"]
        except KeyError as exc:
            msg = "Invalid ObjectData element, could not find name attribute"
            raise ValueError(msg, element) from exc
        self._id = id_
        self._type = type_
        self._element = element
        self._properties = self._read_properties()
        self._document = document
        # child_link_types = ["PropertyLinkList", "PropertyLink"]
        # parent_link_types = ["PropertyLinkSubList", "PropertyLinkSub"]

    @property
    def id_(self) -> int:
        """The file-unique FreeCAD integer id of the object."""
        return self._id

    @property
    def name(self) -> str:
        """The file-unique FreeCAD string name of the object."""
        return self._name

    @property
    def type_(self) -> str:
        """The TypeId string of the object."""
        return self._type

    @property
    def properties(self) -> list[FreeCADPropertyXML]:
        """The list of object properties read from xml."""
        return self._properties

    @property
    def document(self) -> FreeCADDocumentFile:
        """The document this object is inside of."""
        return self._document

    @property
    def uid(self) -> str:
        """The has-to-be-unique pancad calculated id for this element."""
        return f"{self.document.get_property('Uid').value}_feature_{self.id_}"

    def get_property(self, name: str) -> FreeCADPropertyXML:
        """Returns the FreeCADPropertyXML object with the provided name."""
        try:
            return next(p for p in self.properties if p.name == name)
        except StopIteration as exc:
            raise LookupError(f"Could not find property '{name}'", name)

    def _read_properties(self) -> list[FreeCADPropertyXML]:
        """Reads the properties of the object into a list of interfacing 
        objects.
        """
        properties = []
        property_list = self._element.find("Properties")
        if property_list is None:
            msg = "Unexpected Object format: could not find Properties element"
            raise ValueError(msg, self._element)
        for prop in property_list:
            properties.append(FreeCADPropertyXML(prop, self))
        return properties

    def _read_links(self, types: list[str]) -> list[str]:
        """Reads the unique list object names in the links under properties with 
        the provided types.

        :param types: The names of the list types without the App:: namespace.
        :raises ValueError: When a link is found with no value attribute.
        """
        names = set()
        list_xpaths = [f"Properties/Property[@type='App::{t}']" for t in types]
        for xpath in list_xpaths:
            for link_list in self._element.findall(xpath):
                for link_element in link_list.findall(".//Link"):
                    try:
                        value = link_element.attrib["value"]
                    except KeyError as exc:
                        msg = "Unexpected FCStd link format: no 'value' found"
                        raise ValueError(msg, link_element) from exc
                    if value != "": # Skip blank values
                        names.add(value)
        return list(names)

class FreeCADPropertyXML:
    """A class providing interfaces to FCStd Document.xml element properties.

    :param element: The xml Property element inside a FCStd Properties xml 
        element list.
    :param parent: The object this property is inside of.
    """
    tag = "Property"
    """The nominal tag of the element in xml. If is_private is True, then it's 
    actually _Property, but if that matters in a specific application then 
    properties should be filtered based on that boolean rather than depending on 
    the specific tag format.
    """

    def __init__(self, element: Element, parent: FreeCADObjectXML):
        try:
            self._name = element.attrib["name"]
        except KeyError as exc:
            msg = "Invalid Property element, could not find 'name' attribute"
            raise ValueError(msg, element) from exc
        try:
            self._type = element.attrib["type"]
        except KeyError as exc:
            msg = "Invalid Property element, could not find 'type' attribute"
            raise ValueError(msg, element) from exc
        self._is_private = element.tag.startswith("_")
        self._element = element
        self._parent = parent
        func_to_types = {
            self._read_single_str_value: [
                "App::PropertyUUID",
                "App::PropertyLink",
            ],
            self._read_nested_str_value_list: [
                "App::PropertyLinkList",
            ],
            self._read_single_link_sub: [
                "App::PropertyLinkSub",
            ],
        }
        self._type_func_dispatch = {}
        for func, types in func_to_types.items():
            self._type_func_dispatch.update({t: func for t in types})

    @property
    def name(self) -> str:
        """The name attribute of the property in the file's xml."""
        return self._name

    @property
    def type_(self) -> str:
        """The type attribute of the property in the file's xml."""
        return self._type

    @property
    def is_private(self) -> bool:
        """Whether the property tag is marked with a private underscore in the 
        xml file.
        """
        return self._is_private

    @property
    def parent(self) -> FreeCADObjectXML:
        """The object this property is inside of."""
        return self._parent

    @property
    def value(self) -> Any:
        """The value of the property in its xml."""
        return self._type_func_dispatch[self.type_]()

    @singledispatchmethod
    def _raise_read_error(self, exc: Exception) -> NoReturn:
        raise

    @_raise_read_error.register(KeyError)
    def _missing_attr(self, exc: KeyError, element: Element) -> NoReturn:
        msg = (f"Unexpected Property format for {self.type_}:"
               f" Could not find the '{exc.args[0]}' attribute")
        raise ValueError(msg, element) from exc

    @_raise_read_error.register(IndexError)
    def _missing_sub(self, exc: IndexError, element: Element) -> NoReturn:
        msg = (f"Unexpected Property format for {self.type_}:"
               f" Expected 1 subelement but found {len(element)}")
        raise ValueError(msg, element) from exc

    @_raise_read_error.register(ValueError)
    def _custom_msg(self, exc: ValueError, *args) -> NoReturn:
        msg = f"Unexpected Property format for {self.type_}: " + exc.args[0]
        raise ValueError(msg, *args) from exc

    def _more_than_one_subelement(self, element: Element) -> None:
        if (no_subs := len(element)) > 1:
            raise ValueError(f"Expected 1 subelement but found {no_subs}")

    def _read_single_str_value(self) -> str:
        try:
            return self._element[0].attrib["value"]
        except KeyError as exc:
            self._raise_read_error(exc, self._element[0])
        except IndexError as exc:
            self._raise_read_error(exc, self._element)

    def _read_nested_str_value_list(self) -> list[str]:
        try:
            self._more_than_one_subelement(self._element)
            return [e.attrib["value"] for e in self._element[0]]
        except (KeyError, ValueError) as exc:
            self._raise_read_error(exc, self._element)
        except IndexError as exc:
            self._raise_read_error(exc, self._element[0])

    def _read_single_link_sub(self) -> FreeCADLinkSub | None:
        try:
            element = self._element[0]
            obj_name = element.attrib["value"]
            sub_count = int(element.attrib["count"])
        except (KeyError, ValueError) as exc:
            self._raise_read_error(exc, self._element)
        except IndexError as exc:
            self._raise_read_error(exc, self._element[0])
        if obj_name == "":
            return None
        if sub_count == 0:
            return FreeCADLinkSub(obj_name)
        subs = []
        for subelement in element:
            try:
                sub_name = subelement.attrib["value"]
            except KeyError as exc:
                self._raise_read_error(exc, sub)
            if sub_name == "":
                continue
            shadow = subelement.get("shadow")
            subs.append(FreeCADLinkSubSub(sub_name, shadow))
        return FreeCADLinkSub(obj_name, subs)


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
                for i_field in ignore_fields:
                    info.pop(i_field, None)
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
