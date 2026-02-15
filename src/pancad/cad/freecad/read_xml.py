"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

import dataclasses
from functools import partialmethod, cache
from collections import namedtuple
from pathlib import Path
import logging
from math import isclose
import tomllib
from typing import TYPE_CHECKING
import warnings
from xml.etree import ElementTree as ET

from pancad import resources

from .xml_properties import (
    read_property_value,
    FreecadPropertyValueType,
    FreecadUnsupportedPropertyError,
)
from . import xml_utils
from .constants.archive_constants import Attr, Part, Sketcher, Tag

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

@dataclasses.dataclass
class FreeCADLinkSub:
    """A class for tracking FreeCAD App::PropertyLinkSub data. See
    https://freecad.github.io/SourceDoc/d3/d76/classApp_1_1PropertyLinkSub.html

    :param name: The object the link is to.
    :param subs: The linked subelement name of the object. Empty strings are
        converted to None.
    :param shadows: Not certain, but appears to be "shadow subname references"
        in FreeCAD documentation. Likely connected to topological naming.
    """
    name: str
    sub: str = None
    shadow: str = None

    def __post_init__(self):
        if self.sub == "":
            # Blank sub strings indicate the link is just to the object.
            self.sub = None
        if self.sub is None and self.shadow is not None:
            raise ValueError("Unexpected LinkSub format: sub is None,"
                             f" but shadow is '{self.shadow}'")

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
        schema_version_name = "SchemaVersion"
        self._tree = tree
        try:
            self._schema_version = int(tree.attrib[schema_version_name])
        except KeyError as exc:
            msg = f"Invalid Document.xml, could not find {schema_version_name}"
            raise ValueError(msg, tree) from exc
        except (ValueError, TypeError) as exc:
            raw_schema_version = tree.get(schema_version_name)
            msg = (f"Document.xml {schema_version_name} is not int-like. Either"
                   " invalid Document.xml or FreeCAD changed their format"
                   f" SchemaVersion value: {raw_schema_version}")
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
        """The xml schema version of the FreeCAD xml."""
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
            msg = f"Could not find property '{name}'"
            raise LookupError(msg, name) from exc

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
    def document(self) -> FreeCADDocumentXML:
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
            msg = f"Could not find property '{name}'"
            raise LookupError(msg, name) from exc

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
            self._read_single_str: [
                "App::PropertyUUID",
                "App::PropertyLink",
                "App::PropertyString",
            ],
            self._read_single_bool: ["App::PropertyBool"],
            self._read_str_list: ["App::PropertyLinkList"],
            self._read_link_sub: ["App::PropertyLinkSub"],
            self._read_link_sub_list: ["App::PropertyLinkSubList"],
            self._read_geometry: ["Part::PropertyGeometryList"],
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

    def _read_single(self, element: Element) -> Element:
        """Reads the first element of an element inside the property when the
        element must have at least one subelement to be possible to read.

        :param element: An xml Element.
        :raises ValueError: When element does not have exactly 1 subelement.
        """
        if (no_subelements := len(element)) != 1:
            msg = (f"Unexpected Property format for {self.type_}:"
                   f"Expected 1 subelement but found {no_subelements}")
            raise ValueError(msg, element)
        return element[0]

    def _read_first(self) -> Element:
        """Reads the first property subelement."""
        return self._read_single(self._element)

    def _read_attr(self, element: Element, attr: str) -> str:
        """Reads the attribute of the element when the property must have this
        attribute on the element this to be possible to read.

        :param element: An xml element.
        :param attr: The name of the attribute.
        :raises ValueError: When the attribute cannot be found.
        """
        try:
            return element.attrib[attr]
        except KeyError as exc:
            msg = (f"Unexpected Property format for {self.type_}:"
                   f" Could not find the '{exc.args[0]}' attribute")
            raise ValueError(msg, element) from exc

    def _read_single_attr(self, name: str):
        """Read property type that has a single element with a value attr."""
        return self._read_attr(self._read_first(), name)

    _read_single_str = partialmethod(_read_single_attr, "value")
    _read_single_bool = xml_utils.convert_str(_read_single_str,
                                              xml_utils.read_bool)

    def _read_nested_attr_list(self, attr: str) -> list[str]:
        """Read property type that has a list of value attr subelements."""
        return [self._read_attr(e, attr) for e in self._read_first()]

    _read_str_list = partialmethod(_read_nested_attr_list, "value")

    def _read_link_sub(self) -> list[FreeCADLinkSub]:
        """Read property type with child-to-parent links to one object."""
        links = []
        element = self._read_first()
        obj_name = self._read_attr(element, "value")
        if obj_name == "": # Empty element means no links
            return links
        for subelement in element:
            sub_name = self._read_attr(subelement, "value")
            shadow = subelement.get("shadow")
            links.append(FreeCADLinkSub(obj_name, sub_name, shadow))
        if len(links) == 0: # Name is not empty, so just the link to the object.
            links.append(FreeCADLinkSub(obj_name))
        return links

    def _read_link_sub_list(self) -> list[FreeCADLinkSub]:
        """Read property type with child-to-parent links to multiple objects."""
        links = []
        element = self._read_first()
        for subelement in element:
            obj_name = self._read_attr(subelement, "obj")
            if obj_name == "":
                continue
            sub_name = self._read_attr(subelement, "sub")
            shadow = subelement.get("shadow")
            links.append(FreeCADLinkSub(obj_name, sub_name, shadow))
        return links

    def _read_geometry(self) -> list[FreeCADGeometryXML]:
        geometry = []
        for element in self._read_first():
            geometry.append(FreeCADGeometryXML(element, self))
        return geometry

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

@dataclasses.dataclass
class GeometryExtension:
    """A dataclass for tracking all FreeCAD GeometryExtensions."""
    geometry: FreeCADGeometryXML
    type_: str

@dataclasses.dataclass
class SketchGeoExt(GeometryExtension):
    """A dataclass tracking Sketcher::SketchGeometryExtension values."""
    id_: int
    internal_geometry_type: int
    geometry_mode_flags: int
    geometry_layer: int

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> SketchGeoExt:
        """Returns a SketchGeoExt from a GeoExtension xml element typed as a 
        Sketch Extension.
        """
        type_ = xml_utils.read_attr(element, "type")
        attr_map = [
            ("id", int, "id_"),
            ("internalGeometryType", int, "internal_geometry_type"),
            ("geometryModeFlags", lambda x: int(x, base=2), "geometry_mode_flags"),
            ("geometryLayer", int, "geometry_layer")
        ]
        attrs = {}
        for name, func, input_name in attr_map:
            try:
                attrs[input_name] = func(xml_utils.read_attr(element, name))
            except ValueError as exc:
                msg ="Exception from reading Sketcher::SketchGeometryExtension"
                exc.add_note(msg)
                raise
        return cls(parent, type_, **attrs)

@dataclasses.dataclass
class GeomData:
    """Dataclass for tracking data common to all FreeCAD Geometry."""
    parent: FreeCADGeometryXML
    type_: str
    tag: str

@dataclasses.dataclass
class GeomPoint(GeomData):
    """Dataclass for tracking FreeCAD Sketch Point info."""
    location: tuple[float, float]

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomPoint:
        """Returns a GeomPoint from a GeomPoint xml element"""
        attr_names = ["X", "Y", "Z"]
        attrs = [float(xml_utils.read_attr(element, a)) for a in attr_names]
        if not isclose(attrs[-1], 0):
            raise ValueError("Unexpected Point Value: Z is not 0", element)
        del attrs[-1]
        return cls(parent, parent.type_, element.tag, tuple(attrs))

@dataclasses.dataclass
class GeomLineSegment(GeomData):
    """Dataclass for tracking FreeCAD Sketch Line Segment info."""
    start: tuple[float, float]
    end: tuple[float, float]

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomLineSegment:
        """Returns a GeomLineSegment from a LineSegment xml element"""
        point_to_input = [("Start", "start"), ("End", "end")]
        points = {}
        for point_name, input_name in point_to_input:
            location = []
            for component in ["X", "Y", "Z"]:
                name = point_name + component
                location.append(float(xml_utils.read_attr(element, name)))
            if not isclose(location[-1], 0):
                msg = f"Unexpected Line {point_name} Value: Z is not 0"
                raise ValueError(msg, element)
            del location[-1]
            points[input_name] = tuple(location)
        return cls(parent, parent.type_, element.tag, **points)

class FreeCADGeometryXML:
    """A class providing interfaces to FCStd Document.xml geometry elements.

    :param element: The xml Geometry element inside an FCStd 
        Part::PropertyGeometryList type xml property list.
    :param parent: The FreeCADPropertyXML this geometry is inside of.
    """
    tag = "Geometry"

    def __init__(self, element: Element, parent: FreeCADPropertyXML):
        self._parent = parent
        self._type = xml_utils.read_attr(element, "type")
        self._id = int(xml_utils.read_attr(element, "id"))
        self._element = element
        self._sketch_ext = self._get_sketch_geometry_extension()
        self._is_construction = self._get_construction()
        self._geometry = self._get_geom()

    @property
    def type_(self) -> str:
        """The TypeId string of the geometry."""
        return self._type

    @property
    def id_(self) -> int:
        """The sketch-unique FreeCAD integer id of the geometry."""
        return self._id

    @property
    def parent(self) -> FreeCADPropertyXML:
        """The object this geometry is inside of."""
        return self._parent

    @property
    def is_construction(self) -> bool:
        """Whether the geometry is sketch construction geometry."""
        return self._is_construction

    def _get_geo_extension(self, type_: str) -> Element:
        """Returns the GeoExtension of the provided type.

        :raises LookupError: When the extension is not found.
        """
        xpath = f"GeoExtensions/GeoExtension[@type='{type_}']"
        return xml_utils.find_single(self._element, xpath)

    def _get_geom(self) -> Element:
        tag = self.type_.removeprefix("Part::")
        if tag != "GeomPoint": # Point is the only one that keeps the 'Geom'
            tag = tag.removeprefix("Geom")
        element = xml_utils.find_single(self._element, tag)
        tag_to_dataclass = {
            "GeomPoint": GeomPoint,
            "LineSegment": GeomLineSegment,
        }
        return tag_to_dataclass[tag].from_element(self, element)

    def _get_sketch_geometry_extension(self) -> SketchGeoExt:
        """Returns the Sketcher::SketchGeometryExtension that all geometry has
        to have.
        """
        type_ = "Sketcher::SketchGeometryExtension"
        try:
            element = self._get_geo_extension(type_)
        except LookupError as exc:
            msg = "Unexpected Geometry format: No SketchGeometryExtension found"
            raise ValueError(msg, self._element) from exc
        return SketchGeoExt.from_element(self, element)

    def _get_construction(self) -> bool:
        try:
            element = xml_utils.find_single(self._element, "Construction")
        except LookupError as exc:
            msg = "Unexpected Geometry format: No Construction element found"
            raise ValueError(msg, self._element) from exc
        try:
            value = xml_utils.read_attr(element, "value")
        except ValueError as exc:
            msg ="Exception from reading Geometry element"
            exc.add_note(msg)
            raise
        return xml_utils.read_bool(value)

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
