"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

import dataclasses
from functools import partialmethod
from collections import namedtuple
from typing import TYPE_CHECKING
import logging
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from pathlib import Path
import graphlib

import numpy as np

from pancad.cad.freecad import xml_utils
from pancad.cad.freecad.constants.archive_constants import (
    ConstraintTypeNum, ConstraintSubPart, InternalGeometryType,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, NoReturn
    from os import PathLike
    from xml.etree.ElementTree import Element, ElementTree

    import quaternion

    from pancad.cad.freecad.xml_utils import FreeCADUID
    from pancad.cad.freecad.constants.archive_constants import App, PartDesign

logger = logging.getLogger(__name__)

ObjectIdInfo = namedtuple("ObjectIdInfo", ["name", "id_", "type_"])


class FCStd:
    """A class providing interfaces to a FreeCAD FCStd file."""
    def __init__(self, zip_file: ZipFile):
        self._archive = zip_file
        self._document = FreeCADDocumentXML.from_fcstd(self)

    @classmethod
    def from_path(cls, path: PathLike) -> FCStd:
        """Returns a new FCStd object from the path."""
        return cls(ZipFile(path))

    @property
    def path(self) -> Path:
        """The path to the FCStd zipped file."""
        return Path(self._archive.filename)

    @property
    def archive(self) -> ZipFile:
        """The zipfile containing the data in the FCStd file."""
        return self._archive

    @property
    def document(self) -> FreeCADDocumentXML:
        """The parsed xml data object with the file's parametric info."""
        return self._document

    @property
    def metadata(self) -> FCMetadata:
        """The subset of file metadata that is always available."""
        doc_props = {
            "Label": "label",
            "Uid": "uid",
            "UnitSystem": "unit_system",
            "LastModifiedDate": "last_modified_date",
            "Id": "user_id",
        }
        inputs = {i: self.document.get_property(p).value
                  for p, i in doc_props.items()}
        return FCMetadata(**inputs)

    @property
    def uid(self) -> FreeCADUID:
        """The has-to-be-unique pancad calculated id for the file. This uid
        is the same as the uid of the file as a whole.
        """
        return self._document.uid

    def get_topo_uids(self) -> list[FreeCADUID]:
        """Returns the topologically ordered (roughly the required creation
        order) uids of the objects inside the file.
        """
        names = self.document.get_topo_order()
        return [self.document.get_object(n).uid for n in names]

    def get_by_uid(self, uid: FreeCADUID | str
                   ) -> (FCStd | FreeCADObjectXML
                         | FreeCADGeometryXML | FreeCADConstraintXML):
        """Returns an object in this file corresponding to the uid.

        :param uid: A FreeCADUID compatible string to search for.
        :raises LookupError: When the uid cannot be found in the file.
        """
        if not isinstance(uid, xml_utils.FreeCADUID):
            uid = xml_utils.FreeCADUID(uid)
        data = uid.data
        if self.uid.file_uid != data.file_uid:
            msg = f"UID not found: Document uid '{self.uid.file_uid}' mismatch"
            raise LookupError(msg, uid)
        if data.type_ == "document":
            return self
        # All uids that get past this point are inside a feature.
        try:
            feature = self.document.get_object(data.feature_id)
        except LookupError as exc:
            msg = f"UID not found: No feature id '{data.feature_id}' found"
            raise LookupError(msg, uid) from exc
        if data.type_ == "feature":
            return feature
        # All uids that get past this point are either geometry or constraints
        try:
            element_list = feature.get_property(data.list_name).value
        except LookupError as exc:
            msg = (f"UID not found: Feature with id {data.feature_id}"
                   f" did not have a '{data.list_name}' list")
            raise LookupError(msg, uid) from exc
        try:
            return next(e for e in element_list if e.uid == uid)
        except StopIteration as exc:
            msg = (f"UID not found: No {data.type_} with the uid found in"
                   f" feature '{feature.name}' {data.list_name} list")
            raise LookupError(msg, uid) from exc

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.metadata.label}'>"

@dataclasses.dataclass
class FCMetadata:
    """Dataclass tracking metadata that is available on all FreeCAD files.

    :param label: The name of the file.
    :param uid: The internally generated unique id for the file.
    :param unit_system: The units for the file's dimensions.
    :param last_modified_date: The date the file was modified last.
    :param user_id: The id for the file entered by the designer.
    """
    label: str
    uid: str
    unit_system: str
    last_modified_date: str
    user_id: str

@dataclasses.dataclass(frozen=True)
class FreeCADLink:
    """A class for tracking FreeCAD App::PropertyLinkSub data. See
    https://freecad.github.io/SourceDoc/d3/d76/classApp_1_1PropertyLinkSub.html

    :param name: The object the link is to.
    :param subs: The linked subelement name of the object. Empty strings are
        converted to None.
    :param shadows: Not certain, but appears to be "shadow subname references"
        in FreeCAD documentation. Likely connected to topological naming.
    :raises ValueError: Raised if sub is an empty string or when sub is None but
        shadow is not None.
    """
    name: str
    sub: str = None
    shadow: str = None

    def __post_init__(self):
        if self.sub == "":
            # Blank sub strings indicate the link is just to the object.
            # Blank subs cannot be converted to None here without unfreezing the
            # dataclass, so it just raises an error.
            raise ValueError("sub cannot be an empty string")
        if self.sub is None and self.shadow is not None:
            raise ValueError("Unexpected LinkSub format: sub is None,"
                             f" but shadow is '{self.shadow}'")

class FreeCADDocumentXML:
    """A class providing an interface to FCStd Document.xml files.

    :param tree: An xml ElementTree read from a FCStd Document.xml file.
    :param file: The FCStd file this document is part of. Supports being None so
        this object can be used in the API.
    :raises ValueError: When the xml tree is an invalid Document.xml format.
    """
    tag = "Document"
    """The nominal tag of the element in xml."""

    def __init__(self, tree: ElementTree, file: FCStd=None):
        schema_version_name = "SchemaVersion"
        self._tree = tree
        self._file = file
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
            logger.warning("SchemaVersion %s not recognized,"
                           " invalid translation behavior may occur",
                           self.schema_version)
        self._objects = self._read_all_objectdata()
        self._properties = self._read_properties()

    @classmethod
    def from_string(cls, string: str) -> FreeCADDocumentXML:
        """Returns a FreeCADDocumentFile from an already read Document.xml
        string. Example use: FreeCAD API docs have a string Content property.
        """
        return cls(ET.fromstring(string))

    @classmethod
    def from_zip(cls, file: ZipFile) -> FreeCADDocumentXML:
        """Creates a document from a zipped file structured like an FCStd file.
        """
        with file.open("Document.xml") as document:
            return cls.from_string(document.read())

    @classmethod
    def from_fcstd(cls, fcstd: FCStd) -> FreeCADDocumentXML:
        """Creates a document from the FCStd object and sets it as the document's
        file.
        """
        with fcstd.archive.open("Document.xml") as document:
            return cls(ET.fromstring(document.read()), fcstd)

    # Properties
    @property
    def schema_version(self) -> int:
        """The xml schema version of the FreeCAD xml."""
        return self._schema_version

    @property
    def file(self) -> FCStd:
        """The file this document is inside of."""
        return self._file

    @property
    def objects(self) -> list[FreeCADObjectXML]:
        """Returns all objects inside this document."""
        return self._objects

    @property
    def properties(self) -> list[FreeCADPropertyXML]:
        """The list of document properties read from the xml Properties list."""
        return self._properties

    @property
    def uid(self) -> FreeCADUID:
        """The has-to-be-unique pancad calculated id for this element. This uid
        is the same as the uid of the file as a whole.
        """
        return xml_utils.FreeCADUID(f"{self.get_property('Uid').value}_document")

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

    def get_topo_order(self) -> list[str]:
        """Returns the non-unique (as in, multiple orders theoretically exist)
        list of topologically ordered object names in the document. The
        non-unique orders will only matter for version control. An example
        would be if there are two independent sketches then the order that
        they appear in the document is arbitrary.
        """
        child_graph = {obj.name: self.get_object_parents(obj.name)
                       for obj in self.objects}
        sorter = graphlib.TopologicalSorter(child_graph)
        return list(sorter.static_order())

    def get_object_parents(self, id_: str | int) -> list[str]:
        """Returns the direct parents of the object by its name or id. Does not
        return all parents recursively up the tree.
        """
        obj = self.get_object(id_)
        parents = obj.get_parent_names()
        all_parents = {o.name: o.get_child_names() for o in self.objects}
        for parent, children_by_parent in all_parents.items():
            if obj.name in children_by_parent:
                parents.add(parent)
        return parents

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
        obj = xml_utils.find_single(self._tree, xpath)
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
            try:
                properties.append(FreeCADPropertyXML(prop, self))
            except (ValueError, NotImplementedError) as exc:
                filename = self.file.path.name
                exc.add_note(f"In file '{filename}'")
                logger.warning("Document property read failed. Reason:\n%s",
                               str(exc.__reduce__()))
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

    def __init__(self, element: Element, id_: int | str, type_: str,
                 document: FreeCADDocumentXML):
        self._document = document
        self._name = xml_utils.read_attr(element, "name")
        self._id = int(id_)
        self._type = type_
        self._element = element
        # Some properties depend on others (Constraints), so initialize the list
        self._properties = []
        self._read_properties()

    @property
    def id_(self) -> int:
        """The file-unique FreeCAD integer id of the object."""
        return self._id

    @property
    def label(self) -> str:
        """The human-visible name of the Object in the FreeCAD GUI."""
        try:
            return self.get_property("Label").value
        except LookupError:
            logger.warning("Object %s of type %s does not have a Label.",
                           self.name, self.type_)
            return f"NO LABEL, NAME: {self.name}"

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
    def uid(self) -> FreeCADUID:
        """The has-to-be-unique pancad calculated id for this element."""
        string = f"{self.document.uid.file_uid}_feature_{self.id_}"
        return xml_utils.FreeCADUID(string)

    def has_property(self, name: str) -> bool:
        """Returns whether the object has a property with the given name."""
        return name in {p.name for p in self.properties}

    def get_property(self, name: str) -> FreeCADPropertyXML:
        """Returns the FreeCADPropertyXML object with the provided name."""
        try:
            return next(p for p in self.properties if p.name == name)
        except StopIteration as exc:
            msg = f"Could not find property '{name}' on Object '{self.name}'"
            raise LookupError(msg, name) from exc

    def get_child_names(self) -> set[str]:
        """Returns the set of child object names that this object defines
        in the xml file.
        """
        names = set()
        for prop in self.properties:
            if prop.is_private:
                continue
            if prop.type_ == "App::PropertyLink" and prop.value is not None:
                names.add(prop.value.name)
            if prop.type_ == "App::PropertyLinkList":
                names.update(p.name for p in prop.value)
        return names

    def get_parent_names(self) -> set[str]:
        """Returns the set of parent object names that this object defines
        in the xml file.
        """
        names = set()
        link_sub_names = ["App::PropertyLinkSubList", "App::PropertyLinkSub"]
        for prop in self.properties:
            if prop.type_ in link_sub_names:
                names.update(p.name for p in prop.value)
        return names

    def _read_properties(self) -> list[FreeCADPropertyXML]:
        """Reads the properties of the object into a list of interfacing
        objects.
        """
        self._properties = [] # Clear the property list
        try:
            property_list = list(self._element.find("Properties"))
        except TypeError as exc:
            msg = "Unexpected Object format: could not find Properties element"
            raise ValueError(msg, self._element) from exc
        property_list.sort(key=self._property_read_sort_key)
        for prop in property_list:
            try:
                self._properties.append(FreeCADPropertyXML(prop, self))
            except (ValueError, NotImplementedError) as exc:
                filename = self.document.file.path.name
                exc.add_note(f"On Object '{self.name}' in file '{filename}'")
                logger.warning("Object '%s' property read failed. Reason:\n%s",
                               self.name, str(exc.__reduce__()))
        return self._properties

    @staticmethod
    def _property_read_sort_key(element: Element) -> int:
        """A sorting key function to ensure properties are in a valid order.
        Example: The geometry needs to be read before the constraints in a
        sketch.
        """
        try:
            type_ = element.attrib["type"]
        except KeyError as exc:
            msg = "Invalid Property element, could not find 'type' attribute"
            raise ValueError(msg, element) from exc
        must_read_last = {"Sketcher::PropertyConstraintList",}
        if type_ in must_read_last:
            return 1
        return 0

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.name}'>"

@dataclasses.dataclass
class FreeCADPlacement:
    """Dataclass tracking a FreeCAD Placement object's properties from FCStd xml
    """
    location: tuple[float, float, float]
    quat: quaternion.quaternion
    o_vector: tuple[float, float, float]

    @classmethod
    def from_element(cls, element: Element) -> FreeCADPlacement:
        """Creates Placement directly from an xml element"""
        xyz = ["x", "y", "z"]
        location = xml_utils.read_vector(element, xyz, "P", False)
        o_vector = xml_utils.read_vector(element, xyz, "O", False)
        quat_vector = xml_utils.read_vector(element, ["Q0", "Q1", "Q2", "Q3"],
                                            is_2d=False)
        return cls(location, np.quaternion(*quat_vector), o_vector)

@dataclasses.dataclass
class FreeCADExpression:
    """Dataclass for tracking the definition of FreeCAD expressions that define
    derived properties in the model.
    """
    path: str
    expression: str

@dataclasses.dataclass
class PropertyPartShape:
    """Dataclass for tracking the definition of FreeCAD PropertyPartShape
    elements
    """
    element_map: str
    brp: str
    txt: str = None
    hash_index: int = None
    elements: list[tuple[str, str]] = dataclasses.field(default_factory=list)

    @classmethod
    def from_element(cls, element: Element) -> PropertyPartShape:
        """Creates PropertyPartShape directly from an xml element"""
        inputs = {}
        part = xml_utils.find_single(element, "Part")
        inputs["element_map"] = xml_utils.read_attr(part, "ElementMap")
        inputs["brp"] = xml_utils.read_attr(part, "file")
        if part.get("HasherIndex") is not None:
            inputs["hash_index"] = xml_utils.read_attr(part, "HasherIndex", int)
        for sub in xml_utils.find_single(element, "ElementMap"):
            values = []
            for name in ("key", "value"):
                value = xml_utils.read_attr(sub, name)
                if value != "Dummy": # Have not found any non-Dummy cases so far
                    msg = ("Expected 'Dummy' for ElementMap element"
                           f" value {name}, got {value}")
                    raise ValueError(msg)
                values.append(value)
            inputs.setdefault("elements", []).append(tuple(values))
        ele_map_2 = element.find("ElementMap2")
        if ele_map_2 is not None:
            inputs["txt"] = xml_utils.read_attr(ele_map_2, "file")
        return cls(**inputs)

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
            self._read_single_str: ["App::PropertyUUID", "App::PropertyString"],
            self._read_single_uuid: ["Materials::PropertyMaterial"],
            self._read_single_bool: ["App::PropertyBool"],
            self._read_single_float: [
                "App::PropertyPrecision",
                "App::PropertyAngle",
                "App::PropertyLength",
                "App::PropertyFloat",
            ],
            self._read_property_part_shape: ["Part::PropertyPartShape"],
            self._read_value_vector: ["App::PropertyVector"],
            self._read_link_list: [
                "App::PropertyLinkList",
                "App::PropertyLinkListHidden",
            ],
            self._read_link: ["App::PropertyLink", "App::PropertyLinkHidden"],
            self._read_link_sub: ["App::PropertyLinkSub"],
            self._read_enum: ["App::PropertyEnumeration"],
            self._read_link_sub_list: ["App::PropertyLinkSubList"],
            self._read_geometry: ["Part::PropertyGeometryList"],
            self._read_constraints: ["Sketcher::PropertyConstraintList"],
            self._read_expressions: ["App::PropertyExpressionEngine"],
            self._read_placement: ["App::PropertyPlacement"],
            self._read_property_map: ["App::PropertyMap"],
        }
        self._type_func_dispatch = {}
        for func, types in func_to_types.items():
            self._type_func_dispatch.update({t: func for t in types})

        try:
            value_func = self._type_func_dispatch[self.type_]
        except KeyError as exc:
            msg = f"Property type '{self.type_}' has not been implemented."
            not_imp_exc = NotImplementedError(msg)
            not_imp_exc.add_note(f"On Property '{self.name}'")
            raise not_imp_exc from exc
        try:
            if self.is_private:
                # Private properties appear to be derived from elsewhere.
                self._value = None
            else:
                self._value = value_func()
        except (ValueError, NotImplementedError) as exc:
            exc.add_note(f"While reading values on Property '{self.name}'")
            raise

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
        return self._value

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

    def _read_single_attr(self, name: str,
                          converter: Callable[str, Any]=str) -> Any:
        """Read property type that has a single element with a value attr."""
        return xml_utils.read_attr(self._read_first(), name, converter)

    _read_single_str = partialmethod(_read_single_attr, "value")
    _read_single_uuid = partialmethod(_read_single_attr, "uuid")
    _read_single_bool = partialmethod(_read_single_attr, "value",
                                      xml_utils.read_bool)
    _read_single_float = partialmethod(_read_single_attr, "value", float)

    def _read_single_vector(self, names: tuple[str, str, str],
                            prefix: str=None, is_2d: bool=False
                            ) -> tuple[float, float, float]:
        """Reads the vector inside the first subelement."""
        element = self._read_first()
        return xml_utils.read_vector(element, names, prefix, is_2d)

    _read_value_vector = partialmethod(_read_single_vector,
                                       ("X", "Y", "Z"), "value")

    def _read_enum(self) -> int | str:
        """Reads enumerations. If there's a custom list it converts the option to
        its selected string.
        """
        select = xml_utils.find_single(self._element, "Integer")
        selection = xml_utils.read_attr(select, "value", int)
        is_custom = select.get("CustomEnum")
        if is_custom is not None and xml_utils.read_bool(is_custom):
            options = xml_utils.find_single(self._element, "CustomEnumList")
            return xml_utils.read_attr(options[selection], "value")
        return selection

    def _read_nested_attr_list(self, attr: str) -> list[str]:
        """Read property type that has a list of value attr subelements."""
        return [xml_utils.read_attr(e, attr) for e in self._read_first()]

    _read_str_list = partialmethod(_read_nested_attr_list, "value")

    def _read_property_part_shape(self) -> PropertyPartShape:
        return PropertyPartShape.from_element(self._element)

    def _read_link_sub(self) -> list[FreeCADLink]:
        """Read property type with child-to-parent links to one object."""
        links = []
        element = self._read_first()
        obj_name = xml_utils.read_attr(element, "value")
        if obj_name == "": # Empty element means no links
            return links
        for subelement in element:
            sub_name = xml_utils.read_attr(subelement, "value")
            shadow = subelement.get("shadow")
            if sub_name == "":
                sub_name = None
            links.append(FreeCADLink(obj_name, sub_name, shadow))
        if len(links) == 0: # Name is not empty, so just the link to the object.
            links.append(FreeCADLink(obj_name))
        return links

    def _read_link(self) -> FreeCADLink | None:
        """Read property type with parent-to-child link to one object."""
        element = self._read_first()
        name = xml_utils.read_attr(element, "value")
        if name == "":
            return None
        return FreeCADLink(name)

    def _read_link_list(self) -> list[FreeCADLink]:
        """Read property type with parent-to-child links to one object."""
        links = []
        element = self._read_first()
        for subelement in element:
            name = xml_utils.read_attr(subelement, "value")
            links.append(FreeCADLink(name))
        return links

    def _read_placement(self) -> FreeCADPlacement:
        element = self._read_first()
        return FreeCADPlacement.from_element(element)

    def _read_property_map(self) -> list:
        """If any property maps add elements, this will raise a better
        NotImplementedError to make it clear that it's something to
        implement.
        """
        if len(self._read_first()) > 0:
            num = len(self._read_first())
            msg = (f"Expected PropertyMap to have 0 elements, found {num}. any"
                  " Nested Map elements have not been implemented.")
            raise NotImplementedError(msg)
        return [] # element = self._read_first() # Not used since always empty

    def _read_link_sub_list(self) -> list[FreeCADLink]:
        """Read property type with child-to-parent links to multiple objects."""
        links = []
        element = self._read_first()
        for subelement in element:
            obj_name = xml_utils.read_attr(subelement, "obj")
            if obj_name == "":
                continue
            sub_name = xml_utils.read_attr(subelement, "sub")
            shadow = subelement.get("shadow")
            if sub_name == "":
                sub_name = None
            links.append(FreeCADLink(obj_name, sub_name, shadow))
        return links

    def _read_geometry(self) -> list[FreeCADGeometryXML]:
        geometry = []
        for element in self._read_first():
            try:
                geometry.append(FreeCADGeometryXML(element, self))
            except NotImplementedError as exc:
                logger.warning("Failed to read geometry element: %s", exc)
        return geometry

    def _read_expressions(self) -> list[FreeCADExpression]:
        element = self._read_first()
        expressions = []
        attrs = ["path", "expression"]
        for exp in element:
            inputs = {name: xml_utils.read_attr(exp, name) for name in attrs}
            expressions.append(FreeCADExpression(**inputs))
        return expressions

    def _read_constraints(self) -> list[FreeCADConstraintXML]:
        constraints = []
        for element in self._read_first():
            constraints.append(FreeCADConstraintXML(element, self))
        return constraints

    def __repr__(self) -> str:
        type_wo_ns = self.type_.split("::")[-1]
        return f"<FreeCADPropertyXML {self.name} {type_wo_ns}>"

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
                exc.add_note(f"Exception occurred on GeoExtension type {type_}")
                raise
        try:
            intern_type = attrs["internal_geometry_type"]
            attrs["internal_geometry_type"] = InternalGeometryType(intern_type)
        except ValueError as exc:
            msg = f"Unsupported internalGeometryType value: {intern_type}"
            raise NotImplementedError(msg) from exc
        return cls(parent, type_, **attrs)

@dataclasses.dataclass
class GeomData:
    """Dataclass for tracking data common to all FreeCAD Geometry."""
    parent: FreeCADGeometryXML = dataclasses.field(repr=False)
    type_: str = dataclasses.field(repr=False)
    tag: str

@dataclasses.dataclass
class GeomPoint(GeomData):
    """Dataclass for tracking FreeCAD Sketch Point info."""
    location: tuple[float, float]

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomPoint:
        """Returns a GeomPoint from a GeomPoint xml element."""
        point = xml_utils.read_vector(element, ("X", "Y", "Z"))
        return cls(parent, parent.type_, element.tag, point)

@dataclasses.dataclass
class GeomLineSegment(GeomData):
    """Dataclass for tracking FreeCAD Sketch Line Segment info."""
    start: tuple[float, float]
    end: tuple[float, float]

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomLineSegment:
        """Returns a GeomLineSegment from a LineSegment xml element."""
        xyz = ("X", "Y", "Z")
        point_to_input_name = [("Start", "start"), ("End", "end")]
        points = {}
        for point, input_name in point_to_input_name:
            try:
                points[input_name] = xml_utils.read_vector(element, xyz, point)
            except ValueError as exc:
                exc.add_note(f"Occurred on LineSegment {point} point")
                raise
        return cls(parent, parent.type_, element.tag, **points)

@dataclasses.dataclass
class GeomCircle(GeomData):
    """Dataclass for tracking FreeCAD Sketch Circle info."""
    center: tuple[float, float]
    radius: float

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomCircle:
        """Returns a GeomCircle from a Circle xml element."""
        xyz = ("X", "Y", "Z")
        center = xml_utils.read_vector(element, xyz, "Center")
        normal = xml_utils.read_vector(element, xyz, "Normal", False)
        attrs = xml_utils.read_float_attrs(
            element, {"AngleXU": "angle", "Radius": "radius"}
        )
        extras = [(normal, (0, 0, 1), "Normal"), (attrs["angle"], 0, "AngleXU")]
        for value, expected, extra_name in extras:
            try:
                xml_utils.check_constant(value, expected)
            except ValueError as exc:
                exc.add_note(f"Occurred on Circle {extra_name}")
                raise
        return cls(parent, parent.type_, element.tag, center, attrs["radius"])

@dataclasses.dataclass
class GeomEllipse(GeomData):
    """Dataclass for tracking FreeCAD Sketch Ellipse info."""
    center: tuple[float, float]
    major_radius: float
    minor_radius: float
    major_axis_angle: float

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomEllipse:
        """Returns a GeomEllipse from a Ellipse xml element."""
        xyz = ("X", "Y", "Z")
        center = xml_utils.read_vector(element, xyz, "Center")
        normal = xml_utils.read_vector(element, xyz, "Normal", False)
        try:
            xml_utils.check_constant(normal, (0, 0, 1))
        except ValueError as exc:
            exc.add_note("Occurred on Ellipse Normal")
            raise
        attrs = xml_utils.read_float_attrs(
            element,
            {
                "MajorRadius": "major_radius",
                "MinorRadius": "minor_radius",
                "AngleXU": "major_axis_angle",
            }
        )
        return cls(parent, parent.type_, element.tag, center, **attrs)

@dataclasses.dataclass
class GeomArcOfCircle(GeomData):
    """Dataclass for tracking FreeCAD Sketch Ellipse info."""
    center: tuple[float, float]
    radius: float
    start_angle: float
    end_angle: float

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
                     ) -> GeomArcOfCircle:
        """Returns a GeomArcOfCircle from a ArcOfCircle xml element."""
        xyz = ("X", "Y", "Z")
        center = xml_utils.read_vector(element, xyz, "Center")
        normal = xml_utils.read_vector(element, xyz, "Normal", False)
        attrs = xml_utils.read_float_attrs(
            element,
            {
                "Radius": "radius",
                "StartAngle": "start_angle",
                "EndAngle": "end_angle",
                "AngleXU": "angle",
            }
        )
        extras = [(normal, (0, 0, 1), "Normal"), (attrs["angle"], 0, "AngleXU")]
        for value, expected, extra_name in extras:
            try:
                xml_utils.check_constant(value, expected)
            except ValueError as exc:
                exc.add_note(f"Occurred on ArcOfCircle {extra_name}")
                raise
        del attrs["angle"]
        return cls(parent, parent.type_, element.tag, center, **attrs)



class FreeCADGeometryXML:
    """A class providing interfaces to FCStd Document.xml sketch geometry
    elements.

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
    def internal_type(self) -> InternalGeometryType:
        """The internal alignment type of the geometry specified in the xml."""
        return self._sketch_ext.internal_geometry_type

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

    @property
    def uid(self) -> FreeCADUID:
        """The has-to-be-unique pancad calculated id for this element."""
        feature = self.parent.parent
        document = feature.document
        parts = [
            document.get_property('Uid').value,
            "sketchgeo",
            feature.id_,
            int(self.id_ < 0), # 0 for Geometry, 1 for ExternalGeo
            self.id_,
        ]
        return xml_utils.FreeCADUID("_".join(map(str, parts)))

    @property
    def geometry(self) -> GeomData:
        """The geometric data of the geometry represented by this xml element."""
        return self._geometry

    def get_defining_geometry(self) -> FreeCADGeometryXML:
        """Returns the geometry defining this geometry. If non-internal
        geometry, this echos the geometry. If this is internal geometry
        (e.g. an Ellipse major axis), this returns the Ellipse.
        """
        if self.internal_type == InternalGeometryType.NOT_INTERNAL:
            return self
        sketch = self.parent.parent
        constraints = sketch.get_property("Constraints").value
        id_type = (self.id_, self.internal_type)
        for constraint in constraints:
            cons_id_type = (constraint.data.pairs.first.id_, self.internal_type)
            if id_type == cons_id_type:
                geo, _ = constraint.data.pairs.second.get_geometry()
                return geo
        msg = (f"Could not find the internal aligning constraint for"
               f" id, type: {id_type} in {sketch.name}")
        raise ValueError(msg)

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
            "Circle": GeomCircle,
            "Ellipse": GeomEllipse,
            "ArcOfCircle": GeomArcOfCircle,
        }
        try:
            geom_class = tag_to_dataclass[tag]
        except KeyError as exc:
            msg = f"Reading func for {exc.args[0]} types not yet implemented"
            raise NotImplementedError(msg) from exc
        return geom_class.from_element(self, element)

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

    def __repr__(self) -> str:
        geo_type = self.geometry.__class__.__name__
        sketch_name = self.parent.parent.name
        return f"<{self.__class__.__name__} {geo_type} {sketch_name} {self.id_}>"

@dataclasses.dataclass
class ConstraintGeoRef:
    """A dataclass tracking the index and subpart of a FreeCAD constraint's
    reference to geometry.

    :param index: The index of the geometry as entered in the constraint xml.
        Negative numbers are in the ExternalGeo list.
    :param part: The sub part integer for the part of the geometry being
        constrained.
    :param id_: The integer id of the geometry.
    :param constraint:
    """
    index: int
    part: ConstraintSubPart
    constraint: FreeCADConstraintXML
    id_: int | None = dataclasses.field(init=False)
    list_name: str | None = dataclasses.field(init=False)

    def __post_init__(self):
        if self.index == -2000:
            self.list_name = None
        elif self.index < 0:
            self.list_name = "ExternalGeo"
        else:
            self.list_name = "Geometry"
        geo = self._get_geometry_by_index()
        if geo is None:
            self.id_ = None
        else:
            self.id_ = geo.id_

    @property
    def list_index(self) -> int | None:
        """The index of the geometry inside the list it resides in. Updates
        dynamically if the list changes. This is None when the reference is
        empty and just to fill out the 3 required for FreeCAD constraints.

        :raises LookupError: When the geometry id cannot be found in the sketch
            list. This would mean there's unexpected FreeCAD behavior or that
            the geometry has been deleted.
        """
        if self.id_ is None:
            return None
        sketch = self.constraint.parent.parent
        list_geo = sketch.get_property(self.list_name).value
        try:
            return next(i for i, g in enumerate(list_geo) if g.id_ == self.id_)
        except StopIteration as exc:
            msg = (f"Geometry id {self.id_} not found in sketch '{sketch.name}'"
                   f" {self.list_name} list")
            raise LookupError(msg) from exc

    def get_geometry(self) -> tuple[FreeCADGeometryXML, ConstraintSubPart] | None:
        """Returns the geometry from the sketch based on the ids of the
        constrained geometry.
        """
        if self.id_ is None:
            return None
        sketch = self.constraint.parent.parent
        list_geo = sketch.get_property(self.list_name).value
        try:
            return (next(g for g in list_geo if g.id_ == self.id_), self.part)
        except StopIteration as exc:
            msg = (f"Geometry id {self.id_} not found in sketch '{sketch.name}'"
                   f" {self.list_name} list")
            raise LookupError(msg) from exc

    def _get_list_index_from_index(self) -> int | None:
        """Returns the list index from the index stored in the xml."""
        if self.index == -2000:
            return None
        if self.index < 0:
            return -1 - self.index
        return self.index

    def _get_geometry_by_index(self) -> FreeCADGeometryXML | None:
        list_index = self._get_list_index_from_index()
        if list_index is None:
            return None
        sketch = self.constraint.parent.parent
        return sketch.get_property(self.list_name).value[list_index]

@dataclasses.dataclass
class InternalAlignment:
    """Dataclass for tracking how a constraint is used for interally aligning
    geometry like Ellipse subgeometry.
    """
    type_: InternalGeometryType
    index: int

@dataclasses.dataclass
class ConstraintState:
    """Dataclass for tracking the sketch-specific state data of a FreeCAD
    constraint.
    """
    label_distance: float
    label_position: float
    driving: bool
    virtual_space: bool
    active: bool

@dataclasses.dataclass
class ConstraintPairs:
    """Class tracking the three pairs of ConstraintGeoRef integers in FreeCAD
    constraints.
    """
    first: ConstraintGeoRef
    second: ConstraintGeoRef
    third: ConstraintGeoRef

    def get_geometry(self) -> list[tuple[FreeCADGeometryXML, ConstraintSubPart]]:
        """Returns a list of the filled geometry references, tuples of
        (geometry, subpart).
        """
        references = []
        for pair in [self.first, self.second, self.third]:
            if pair.list_index is not None:
                references.append(pair.get_geometry())
        return references

    def as_list(self) -> list[ConstraintGeoRef]:
        """Returns the non-empty geometry references in a list."""
        return  [r for r in [self.first, self.second, self.third]
                 if r.id_ is not None]

@dataclasses.dataclass
class ConstraintData:
    """A dataclass tracking all xml data stored for a FreeCAD sketch
    constraint.
    """
    parent: FreeCADConstraintXML = dataclasses.field(repr=False)
    name: str | None
    type_: ConstraintTypeNum
    value: float
    pairs: ConstraintPairs
    state: ConstraintState
    internal_alignment: InternalAlignment = None

    @classmethod
    def from_element(cls, parent: FreeCADConstraintXML, element: Element
                     ) -> ConstraintData:
        """Returns a ConstraintData dataclass from a Constrain xml element."""
        name = xml_utils.read_attr(element, "Name")
        if name == "":
            name = None
        attrs = cls._read_element_data(element)
        # Consolidate the data into smaller structures
        state_attrs = ["label_distance", "label_position",
                       "driving", "virtual_space", "active"]
        state = ConstraintState(**{a: attrs[a] for a in state_attrs})
        attrs = {k: v for k, v in attrs.items() if k not in state_attrs}
        pairs = {}
        pair_nums =["First", "Second", "Third"]
        for num, pos in zip(pair_nums, map(lambda x: f"{x}Pos", pair_nums)):
            pairs[num.lower()] = ConstraintGeoRef(attrs[num],
                                                  ConstraintSubPart(attrs[pos]),
                                                  parent)
            del attrs[num], attrs[pos]
        pairs = ConstraintPairs(**pairs)
        return cls(parent, name, pairs=pairs, state=state, **attrs)

    @staticmethod
    def _read_element_data(element: Element) -> dict[str, float | int | bool]:
        # Get always there attributes first
        floats = {"Value": "value",
                  "LabelDistance": "label_distance",
                  "LabelPosition": "label_position"}
        bools = {"IsDriving": "driving",
                 "IsInVirtualSpace": "virtual_space",
                 "IsActive": "active"}
        ints = {"Type": "type_"} # Actually an int enumeration for the type
        numbers =["First", "Second", "Third"]
        for num in numbers:
            ints.update({num: num, f"{num}Pos": f"{num}Pos"})
        converts =[(floats, float), (bools, xml_utils.read_bool), (ints, int)]
        attrs = {}
        for names, converter in converts:
            try:
                attrs.update(xml_utils.read_attrs(element, names, converter))
            except ValueError as exc:
                exc.add_note("Occurred while reading ConstraintData")
                raise
        # Get the sometimes there attributes
        internal_names = {"InternalAlignmentType": "type_",
                          "InternalAlignmentIndex": "index"}
        if any(name in element.attrib for name in internal_names):
            align_data = xml_utils.read_int_attrs(element, internal_names)
            try:
                align_data["type_"] = InternalGeometryType(align_data["type_"])
            except ValueError as exc:
                exc.add_note("Unrecognized internal alignment type number"
                             f" {align_data['type_']}")
                raise
            attrs["internal_alignment"] = InternalAlignment(**align_data)
        try:
            attrs["type_"] = ConstraintTypeNum(attrs["type_"])
        except ValueError as exc:
            exc.add_note(f"Unrecognized type number {attrs['type_']}")
            raise
        return attrs


class FreeCADConstraintXML:
    """A class providing interfaces to FCStd Document.xml geometry elements.

    :param element: The xml Constrain element inside an FCStd
        Sketcher::PropertyConstraintList type xml property list.
    :param parent: The FreeCADPropertyXML this constraint is inside of.
    """
    tag = "Constrain"

    def __init__(self, element: Element, parent: FreeCADPropertyXML):
        self._parent = parent
        self._element = element
        self._data = ConstraintData.from_element(self, element)

    @property
    def parent(self) -> FreeCADPropertyXML:
        """The object this constraint is inside of."""
        return self._parent

    @property
    def data(self) -> ConstraintData:
        """The detailed constraint data structure."""
        return self._data

    @property
    def type_(self) -> ConstraintTypeNum:
        """The constraint type number."""
        return self.data.type_

    @property
    def value(self) -> float:
        """The value of the constraint stored in xml. All FreeCAD constraints
        have a value, but it's normally 0 unless the constraint actually
        uses it (distance, diameter, etc).
        """
        return self.data.value

    @property
    def internal_type(self) -> InternalGeometryType:
        """The internal alignment type of the constraint."""
        if self.data.internal_alignment is None:
            return InternalGeometryType.NOT_INTERNAL
        return self.data.internal_alignment.type_

    @property
    def uid(self) -> FreeCADUID:
        """The has-to-be-unique pancad calculated id for this element."""
        feature = self.parent.parent
        document = feature.document
        parts = [document.get_property('Uid').value, "sketchcons",
                 feature.id_, self.type_]
        pairs = self._data.pairs
        for pair in [pairs.first, pairs.second, pairs.third]:
            if pair.id_ is None:
                id_ = -2000
            else:
                id_ = pair.id_
            list_int_map = {None: 0, "Geometry": 0, "ExternalGeo": 1}
            try:
                list_int = list_int_map[pair.list_name]
            except KeyError as exc:
                msg = f"Unexpected value for list_name: {pair.list_name}"
                raise ValueError(msg) from exc
            parts.extend([list_int, id_, pair.part])
        return xml_utils.FreeCADUID("_".join(map(str, parts)))

    def get_references(self) -> list[ConstraintGeoRef]:
        """Returns the geometry and subpart references constrained by this
        constraint.
        """
        return self.data.pairs.as_list()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.data.type_.human_name}>"
