"""A module containing classes and subclasses of SVGElements, 
representing the different elements in the SVG Element 1.1 
specification https://www.w3.org/TR/2011/REC-SVG11-20110816/
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import svg.validators as sv
import svg.parsers as sp
import trigonometry as trig


class SVGElement(ET.Element):
    tags = None
    def __init__(self, tag: str, id_: str = None) -> None:
        super().__init__(tag)
        self.ownerSVGElement = None
        if id_ is not None:
            self.id_ = id_
    
    @property
    def id_(self) -> str:
        return self._id
    
    @property
    def attrib(self):
        return super().attrib
    
    @id_.setter
    def id_(self, id_: str) -> None:
        super().set("id", id_)
        self._id = id_
    
    @attrib.setter
    def attrib(self, attribute_dictionary: dict) -> None:
        """Extends ElementTree.Element to ensure that public facing
        properties get set when attrib is set
        """
        for attribute in attribute_dictionary:
            self.set(attribute, attribute_dictionary[attribute])
    
    def append(self, subelement: SVGElement) -> None:
        subelement.ownerSVGElement = self
        super().append(subelement)
    
    def remove(self, subelement: SVGElement) -> None:
        subelement.ownerSVGElement = None
        super().remove(subelement)
    
    def set(self, key: str, value: str | ET.Element) -> None:
        match key:
            case "id":
                self.id_ = value
            case "ownerSVGElement":
                self.ownerSVGElement = value
            case _:
                super().set(key, value)
    
    def to_string(self, indent: str = None) -> str:
        if indent is not None:
            ET.indent(self, indent)
        return ET.tostring(self)
    
    def sub(self, id_: str) -> SVGElement:
        """Returns a subelement by a given id. Returns None if the id 
        does not exist"""
        for sub in self.iter():
            if sub.id_ == id_:
                return sub
        return None
    
    @classmethod
    def from_element(cls, element: ET.Element):
        if cls.tags is None:
            new_element = cls(element.tag)
        elif element.tag in cls.tags:
            new_element = cls()
        else:
            raise ValueError("Wrong element tag provided: "
                             + str(element.tag)
                             + " -- must be one of: "
                             + str(cls.tags))
        new_element.attrib = element.attrib
        return new_element

class svg(SVGElement):
    tags = ["svg", "svg:svg", "{http://www.w3.org/2000/svg}svg"]
    def __init__(self, id_: str = None) -> None:
        super().__init__("svg", id_)
        self._unit = ""
        self._width = None
        self._height = None
        self._width_value = None
        self._height_value = None
    
    @property
    def height(self) -> str:
        return self._height
    
    @property
    def width(self) -> str:
        return self._width
    
    @property
    def unit(self):
        return self._unit
    
    @property
    def viewBox(self):
        return self._viewBox
    
    @height.setter
    def height(self, height: str) -> None:
        self._height = sv.length(height)
        self._height_value = sv.length_value(self._height)
        unit_in = sv.length_unit(self._height)
        if unit_in != self.unit and self._width_value is not None:
            self.width = str(self._width_value) + self.unit
            self.unit = unit_in
        super().set("height", self._height)
    
    @width.setter
    def width(self, width: str) -> None:
        self._width = sv.length(width)
        self._width_value = sv.length_value(self._width)
        unit_in = sv.length_unit(self._width)
        if unit_in != self.unit and self._height_value is not None:
            self.height = str(self._height_value) + self.unit
            self.unit = unit_in
        super().set("width", self._width)
    
    @unit.setter
    def unit(self, unit: str) -> None:
        """Sets the unit of the svg file. Only replaces the text, 
        this does not convert all the values in the file. The unit is 
        not an actual property on the svg element, it just 
        appears in properties like width and height"""
        if unit != sv.length_unit(unit):
            raise ValueError("Provided unit: " + str(unit) + " can only "
                             + "contain a unit string, not anything else")
        self._unit = unit
        if self._width_value is not None:
            self.width = str(self._width_value) + self._unit
        if self._height_value is not None:
            self.height = str(self._height_value) + self._unit
    
    @viewBox.setter
    def viewBox(self, viewBox: str | list[float, float, float, float]):
        if isinstance(viewBox, str):
            self._viewBox = viewBox
        elif isinstance(viewBox, list):
            if len(viewBox) != 4:
                raise ValueError(str(viewBox) + " must have 4 elements")
            elif viewBox[2] < 0 or viewBox[3] < 0:
                raise ValueError(
                    str(viewBox)
                    + " must have positive numbers in positions 2 and 3"
                )
            self._viewBox = " ".join([str(viewBox[0]), str(viewBox[1]),
                                      str(viewBox[2]), str(viewBox[3])])
        else:
            raise ValueError(
                str(viewBox)
                + " needs to be a list or str to be set as a viewBox"
            )
        super().set("viewBox", self._viewBox)
    
    def set(self, key: str, value: str) -> None:
        match key:
            case "width":
                self.width = value
            case "height":
                self.height = value
            case "viewBox":
                self.viewBox = value
            case "unit":
                self.unit = value
            case _:
                super().set(key, value)
    
    def auto_size(self, margin: float = 0, scope: SVGElement = None) -> None:
        """Sizes the view of the svg based on all its subelements or 
        based on a given scope element's sub elements"""
        if scope is None:
            scope = self
        geometry = []
        for sub in scope.iter():
            if hasattr(sub, "geometry"):
                geometry.extend(sub.geometry)
        if geometry is not None:
            corners = trig.multi_fit_box(geometry)
            min_x, min_y = corners[0][0] - margin, corners[0][1] - margin
            max_x, max_y = corners[1][0] + margin, corners[1][1] + margin
            self.width = str(max_x - min_x) + self.unit
            self.height = str(max_y - min_y) + self.unit
            self.viewBox = [min_x, min_y,
                            self._width_value, self._height_value]
        else:
            raise ValueError("element has no geometry to be auto-sized")

class g(SVGElement):
    tags = ["g", "svg:g", "{http://www.w3.org/2000/svg}g"]
    def __init__(self, id_: str = None):
        super().__init__("g", id_)

class path(SVGElement):
    tags = ["path", "svg:path", "{http://www.w3.org/2000/svg}path"]
    def __init__(self, id_: str = None, d: str = None):
        super().__init__("path", id_)
        if d is not None:
            self.d = d
    
    @property
    def d(self) -> str:
        return self._d
    
    @property
    def geometry(self) -> list[dict]:
        return sp.path_data_to_dicts(self.d, self.id_)
    
    @d.setter
    def d(self, d: str) -> None:
        self._d = d
        super().set("d", self._d)
    
    def set(self, key: str, value: str) -> None:
        match key:
            case "d":
                self.d = value
            case _:
                super().set(key, value)

class circle(SVGElement):
    tags = ["circle", "svg:circle", "{http://www.w3.org/2000/svg}circle"]
    def __init__(self, id_: str = None,
                 cx: float = None, cy: float = None, r: float = None):
        super().__init__("circle", id_)
        if cx is not None:
            self.cx = cx
        if cy is not None:
            self.cy = cy
        if r is not None:
            self.r = r
    
    @property
    def cx(self) -> float:
        return float(self._cx)
    
    @property
    def cy(self) -> float:
        return float(self._cy)
    
    @property
    def r(self) -> float:
        return float(self._r)
    
    @property
    def geometry(self) -> list[dict]:
        return [sp.circle(self.id_, self.r, [self.cx, self.cy])]
    
    @cx.setter
    def cx(self, center_x: float) -> None:
        self._cx = str(sv.length_value(center_x))
        super().set("cx", self._cx)
    
    @cy.setter
    def cy(self, center_y: float) -> None:
        self._cy = str(sv.length_value(center_y))
        super().set("cy", self._cy)
    
    @r.setter
    def r(self, radius: float) -> None:
        r = sv.length_value(radius)
        if r >= 0:
            self._r = str(r)
        else:
            raise ValueError("r must be greater than 0, given: " + str(r))
        super().set("r", self._r)
    
    def set(self, key: str, value: str | float):
        match key:
            case "cx":
                self.cx = value
            case "cy":
                self.cy = value
            case "r":
                self.r = value
            case _:
                super().set(key, value)

class defs(SVGElement):
    tags = ["defs", "svg:defs", "{http://www.w3.org/2000/svg}defs"]
    def __init__(self, id_: str = None):
        super().__init__("defs", id_)