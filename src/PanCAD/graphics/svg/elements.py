"""A module containing classes and subclasses of SVGElements, 
representing the different elements in the SVG Element 1.1 
specification https://www.w3.org/TR/2011/REC-SVG11-20110816/
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

from PanCAD.graphics.svg import validators as sv
from PanCAD.graphics.svg import parsers as sp
from PanCAD.utils import trigonometry as trig

class SVGElement(ET.Element):
    """A class representing the common properties and methods of all SVG 
    1.1 elements. Elements in svg files will default to this class if a 
    more specific subclass has not been made for that element type.
    
    :param tag: The name of the element's tag.
    :param id_: The id of the element, defaults to None.
    """
    
    tags = None
    def __init__(self, tag: str, id_: str = None) -> None:
        """Constructor method"""
        super().__init__(tag)
        self.ownerSVGElement = None
        if id_ is not None:
            self.id_ = id_
    
    @property
    def id_(self) -> str:
        """The id attribute of the element.
        
        :getter: Returns the id as a string.
        :setter: Sets the element attribute and more accessible id_ property
        """
        return self._id
    
    @property
    def attrib(self):
        """The element's attribute dictionary. Extends ElementTree.Element 
        to ensure that public facing properties get synced when attrib is set.
        
        :getter: Returns a dictionary of the element's attributes
        :setter: Sets the dictionary and properties of the element attributes
        """
        return super().attrib
    
    @id_.setter
    def id_(self, id_: str) -> None:
        super().set("id", id_)
        self._id = id_
    
    @attrib.setter
    def attrib(self, attribute_dictionary: dict) -> None:
        
        for attribute in attribute_dictionary:
            self.set(attribute, attribute_dictionary[attribute])
    
    def append(self, subelement: SVGElement) -> None:
        """Extends ElementTree.Element.append to add a reference to 
        the element's owner to the subelement.
        
        :param subelement: the element to be added to this element
        """
        subelement.ownerSVGElement = self
        super().append(subelement)
    
    def remove(self, subelement: SVGElement) -> None:
        """Extends ElementTree.Element.remove to remove the reference 
        to the element's owner that was added during append
        
        :param subelement: the element to be removed from this element
        """
        subelement.ownerSVGElement = None
        super().remove(subelement)
    
    def set(self, key: str, value: str | ET.Element) -> None:
        """Extends ElementTree.Element.set to allow for some key svg 
        attributes to be available as properties while still 
        maintaining base functionality
        
        :param key: the name of the attribute to be set
        :param value: the value of the attribute to be set
        """
        match key:
            case "id":
                self.id_ = value
            case "ownerSVGElement":
                self.ownerSVGElement = value
            case _:
                super().set(key, value)
    
    def to_string(self, indent: str = None) -> str:
        """Returns the string representation of the element.
        
        :param indent: The indent of the subelements in the string. 
                       Defaults to None
        :returns: the element string representation with optional indent
        """
        if indent is not None:
            ET.indent(self, indent)
        return ET.tostring(self)
    
    def sub(self, id_: str) -> SVGElement:
        """Returns a subelement by a given id.
        
        :param id_: the xml id of the desired element
        :returns: The element if it exists, otherwise None
        """
        for sub in self.iter():
            if sub.id_ == id_:
                return sub
        return None
    
    @classmethod
    def from_element(cls, element: ET.Element) -> SVGElement:
        """Creates a new SVGElement from an existing ElementTree.Element object.
        
        :param element: the ElementTree.Element to be upgraded
        :returns: the new SVGElement
        """
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
    """A class representing a SVG 1.1 svg tagged element.
    
    :param id_: The id of the element, defaults to None.
    """
    
    tags = ["svg", "svg:svg", "{http://www.w3.org/2000/svg}svg"]
    def __init__(self, id_: str = None) -> None:
        """Constructor method"""
        super().__init__("svg", id_)
        self._unit = ""
        self._width = None
        self._height = None
        self._width_value = None
        self._height_value = None
    
    @property
    def height(self) -> str:
        """The height of the svg element.
        
        :getter: Returns the height string of the svg element.
        :setter: Sets the height and height_value of the element. Will 
                 also set the unit if the unit is in the input string.
        """
        return self._height
    
    @property
    def width(self) -> str:
        """The width of the svg element.
        
        :getter: Returns the width string of the svg file.
        :setter: Sets the width and width_value of the element. Will 
                 also set the unit if the unit is in the input string.
        """
        return self._width
    
    @property
    def unit(self):
        """The unit of the svg element. The unit is not an xml property on 
        the svg element, it just appears in properties like width and 
        height.
        
        :getter: Returns the unit's name
        :setter: Sets the unit and appends it to the width and height. 
                 Does not convert the values in the element, just replaces the 
                 text
        """
        return self._unit
    
    @property
    def viewBox(self) -> str:
        """The viewBox of the svg element.
        
        :getter: Returns the svg viewBox string
        :setting: Takes either a 4 element float list or a viewBox 
                  string and sets it to the viewBox attribute
        """
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
        if unit != sv.length_unit(unit):
            raise ValueError(f"Provided '{unit}' can only contain an "
                             + f"svg unit string, nothing else")
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
                raise ValueError(f"{viewBox} must have 4 elements")
            elif viewBox[2] < 0 or viewBox[3] < 0:
                raise ValueError(f"{viewBox} elements 2 and 3 must be >0")
            self._viewBox = " ".join([str(viewBox[0]), str(viewBox[1]),
                                      str(viewBox[2]), str(viewBox[3])])
        else:
            raise ValueError(f"{viewBox} viewBox must be a list or str")
        super().set("viewBox", self._viewBox)
    
    def set(self, key: str, value: str) -> None:
        """Extends the SVGElement set function to sync svg element 
        specific attributes as properties.
        
        :param key: the name of the attribute to be set
        :param value: the value of the attribute to be set
        """
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
        based on a given scope element's sub elements.
        
        :param margin: The margin around the minimum shape, has the 
                       same units as the svg file, defaults to 0.
        :param scope: Which element should be considered the scope of 
                      the autosize, defaults to self.
        """
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
    """A class representing a SVG 1.1 g tagged element.
    
    :param id_: The id of the element, defaults to None.
    """
    
    tags = ["g", "svg:g", "{http://www.w3.org/2000/svg}g"]
    def __init__(self, id_: str = None):
        """Constructor method"""
        super().__init__("g", id_)

class path(SVGElement):
    """A class representing a SVG 1.1 path tagged element.
    
    :param id_: The id of the element, defaults to None.
    :param d: The path data string of the element, defaults to None
    """
    
    tags = ["path", "svg:path", "{http://www.w3.org/2000/svg}path"]
    def __init__(self, id_: str = None, d: str = None):
        """Constructor method"""
        super().__init__("path", id_)
        if d is not None:
            self.d = d
    
    @property
    def d(self) -> str:
        """The svg path data for the path element.
        
        :getter: Returns the path data string.
        :setter: Sets both the d property and the element's d attribute
        """
        return self._d
    
    @property
    def geometry(self) -> list[dict]:
        """The geometry held in the element's path data. Read-only.
        
        :getter: Returns a list of dictionaries containing geometry info.
        """
        return sp.path_data_to_dicts(self.d, self.id_)
    
    @d.setter
    def d(self, d: str) -> None:
        self._d = d
        super().set("d", self._d)
    
    def set(self, key: str, value: str) -> None:
        """Extends the SVGElement set function to include the path 
        element specific attributes as properties.
        
        :param key: the name of the attribute to be set
        :param value: the value of the attribute to be set
        """
        match key:
            case "d":
                self.d = value
            case _:
                super().set(key, value)

class circle(SVGElement):
    """A class representing a SVG 1.1 circle tagged element
    
    :param id_: The id of the element, defaults to None.
    :param cx: The center x coordinate
    :param cy: The center y coordinate
    :param r: The circle radius
    """
    
    tags = ["circle", "svg:circle", "{http://www.w3.org/2000/svg}circle"]
    def __init__(self, id_: str = None,
                 cx: float = None, cy: float = None, r: float = None):
        """Constructor method"""
        super().__init__("circle", id_)
        if cx is not None:
            self.cx = cx
        if cy is not None:
            self.cy = cy
        if r is not None:
            self.r = r
    
    @property
    def cx(self) -> float:
        """The x coordinate of the circle center.
        
        :getter: returns the x coordinate of the circle center as a float
        :setter: sets the x coordinate with either a float or string. 
                 If a string is passed the unit is checked for 
                 validity, but is ignored.
        """
        return float(self._cx)
    
    @property
    def cy(self) -> float:
        """The y coordinate of the circle center.
        
        :getter: returns the y coordinate of the circle center as a float
        :setter: sets the y coordinate with either a float or string. 
                 If a string is passed the unit is checked for 
                 validity, but is ignored.
        """
        return float(self._cy)
    
    @property
    def r(self) -> float:
        """The radius of the circle.
        
        :getter: returns the radius of the circle center as a float
        :setter: sets the radius with either a float or string after 
        checking that it is greater than 0. If a string is passed 
        the unit is checked for validity, but is ignored.
        """
        return float(self._r)
    
    @property
    def geometry(self) -> list[dict]:
        """The geometry held in the element, read-only.
        
        :getter: Returns a list of one dictionary containing geometry 
                 info.
        """
        return [sp.circle(self.id_, self.r, [self.cx, self.cy])]
    
    @cx.setter
    def cx(self, center_x: float | str) -> None:
        self._cx = str(sv.length_value(center_x))
        super().set("cx", self._cx)
    
    @cy.setter
    def cy(self, center_y: float | str) -> None:
        self._cy = str(sv.length_value(center_y))
        super().set("cy", self._cy)
    
    @r.setter
    def r(self, radius: float | str) -> None:
        r = sv.length_value(radius)
        if r >= 0:
            self._r = str(r)
        else:
            raise ValueError(f"r must be greater than 0, given: {r}")
        super().set("r", self._r)
    
    def set(self, key: str, value: str | float):
        """Extends the SVGElement set function to include the circle 
        element specific attributes as properties.
        
        :param key: the name of the attribute to be set
        :param value: the value of the attribute to be set
        """
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
    """A class representing a SVG 1.1 defs tagged element
    
    :param id_: The id of the element, defaults to None.
    """
    
    tags = ["defs", "svg:defs", "{http://www.w3.org/2000/svg}defs"]
    def __init__(self, id_: str = None):
        """Constructor method"""
        super().__init__("defs", id_)