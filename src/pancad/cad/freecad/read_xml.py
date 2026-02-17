"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

import dataclasses
from functools import partialmethod
from collections import namedtuple
from typing import TYPE_CHECKING
import warnings
from xml.etree import ElementTree as ET
import graphlib

from . import xml_utils

if TYPE_CHECKING:
    from typing import Any, NoReturn
    from os import PathLike
    from xml.etree.ElementTree import Element, ElementTree
    from .constants.archive_constants import App, PartDesign

ObjectIdInfo = namedtuple("ObjectIdInfo", ["name", "id_", "type_"])

@dataclasses.dataclass
class FreeCADLink:
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

    def get_child_names(self) -> set[str]:
        """Returns the set of child object names that this object defines
        in the xml file.
        """
        names = set()
        for prop in self.properties:
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
        properties = []
        property_list = self._element.find("Properties")
        if property_list is None:
            msg = "Unexpected Object format: could not find Properties element"
            raise ValueError(msg, self._element)
        for prop in property_list:
            properties.append(FreeCADPropertyXML(prop, self))
        return properties


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
            self._read_single_bool: ["App::PropertyBool"],
            self._read_link_list: ["App::PropertyLinkList"],
            self._read_link: ["App::PropertyLink"],
            self._read_link_sub: ["App::PropertyLinkSub"],
            self._read_link_sub_list: ["App::PropertyLinkSubList"],
            self._read_geometry: ["Part::PropertyGeometryList"],
            self._read_constraints: ["Sketcher::PropertyConstraintList"],
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

    def _read_single_attr(self, name: str):
        """Read property type that has a single element with a value attr."""
        return xml_utils.read_attr(self._read_first(), name)

    _read_single_str = partialmethod(_read_single_attr, "value")
    _read_single_bool = xml_utils.convert_str(_read_single_str,
                                              xml_utils.read_bool)

    def _read_nested_attr_list(self, attr: str) -> list[str]:
        """Read property type that has a list of value attr subelements."""
        try:
            return [xml_utils.read_attr(e, attr) for e in self._read_first()]
        except ValueError as exc:
            exc.add_note(f"On Property {self.name}")
            raise

    _read_str_list = partialmethod(_read_nested_attr_list, "value")

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
        if self.is_private:
            return links # Private properties do not have any nested links
        try:
            element = self._read_first()
        except ValueError as exc:
            exc.add_note(f"On Property {self.name}")
            raise
        for subelement in element:
            try:
                name = xml_utils.read_attr(subelement, "value")
            except ValueError as exc:
                exc.add_note(f"On Property {self.name}")
                raise
            links.append(FreeCADLink(name))
        return links

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
            links.append(FreeCADLink(obj_name, sub_name, shadow))
        return links

    def _read_geometry(self) -> list[FreeCADGeometryXML]:
        geometry = []
        for element in self._read_first():
            try:
                geometry.append(FreeCADGeometryXML(element, self))
            except NotImplementedError as exc:
                warnings.warn(f"Failed to read geometry element: {exc}")
        return geometry

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

    @property
    def uid(self) -> str:
        """The has-to-be-unique pancad calculated id for this element."""
        feature = self.parent.parent
        document = feature.document
        parts = [
            document.get_property('Uid').value,
            feature.id_,
            "sketchgeo",
            int(self.id_ < 0), # 0 for Geometry, 1 for ExternalGeo
            self.id_,
        ]
        return "_".join(map(str, parts))

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

@dataclasses.dataclass
class ConstraintGeoRef:
    """A dataclass tracking the index and subpart of a FreeCAD constraint's
    reference to geometry.
    """
    index: int
    part: int

    @property
    def list_index(self) -> int:
        """The index of the geometry inside the list it resides in."""
        if self.index < 0:
            return -1 - self.index
        return self.index

@dataclasses.dataclass
class InternalAlignment:
    """Dataclass for tracking how a constraint is used for interally aligning
    geometry like Ellipse subgeometry.
    """
    type_: int
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

@dataclasses.dataclass
class ConstraintData:
    """A dataclass tracking all xml data stored for a FreeCAD sketch
    constraint.
    """
    parent: FreeCADConstraintXML = dataclasses.field(repr=False)
    name: str | None
    type_: int
    value: float
    pairs: ConstraintPairs
    state: ConstraintState
    internal_alignment: InternalAlignment = None

    @classmethod
    def from_element(cls, parent: FreeCADGeometryXML, element: Element
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
            pairs[num.lower()] = ConstraintGeoRef(attrs[num], attrs[pos])
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
        ints = {"Type": "type_"}
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
        # Get the sometimes there attributes
        internal_names = {"InternalAlignmentType": "type_",
                          "InternalAlignmentIndex": "index"}
        if any(name in element.attrib for name in internal_names):
            align_data = xml_utils.read_int_attrs(element, internal_names)
            attrs["internal_alignment"] = InternalAlignment(**align_data)
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
        self._data = ConstraintData.from_element(parent, element)

    @property
    def parent(self) -> FreeCADPropertyXML:
        """The object this constraint is inside of."""
        return self._parent

    @property
    def uid(self) -> str:
        """The has-to-be-unique pancad calculated id for this element."""
        feature = self.parent.parent
        document = feature.document
        parts = [document.get_property('Uid').value, feature.id_, "sketchcons"]
        geometry = feature.get_property("Geometry").value
        ext_geometry = feature.get_property("ExternalGeo").value
        pairs = self._data.pairs
        for pair in [pairs.first, pairs.second, pairs.third]:
            if pair.index == -2000:
                geo_id = -2000
            elif pair.index < 0:
                geo_id = ext_geometry[pair.list_index].id_
            else:
                geo_id = geometry[pair.list_index].id_
            parts.extend([geo_id, pair.part])
        return "_".join(map(str, parts))
