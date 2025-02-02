"""A module providing a class to represent the svg element and collect xml 
elements to be written to files.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET

import svg_writers as sw
import svg_generators as sg
import svg_parsers as sp
import svg_validators as sv
import svg_readers as sr
import trigonometry as trig

class SVGFile(ET.ElementTree):
    """A class for svg files with a single svg element at the top that 
    contains multiple other elements. Is not intended to make xml 
    documents with multiple separate svg elements
    """
    mode_options = ["r", "w", "x", "+"]
    def __init__(self, filepath: str = None, mode: str = "r") -> None:
        self._mode = mode
        self._declaration = None
        self._svg = None
        self.filepath = filepath
        super().__init__(ET.Element(None))
    
    @property
    def filepath(self) -> str:
        return self._filepath
    
    @property
    def mode(self) -> str:
        return self._mode
    
    @property
    def svg(self) -> ET.Element:
        return self._svg
    
    @svg.setter
    def svg(self, element: svg) -> None:
        """Sets the file's main svg element, while also adding the 
        default properties like xmlns to it. If an existing root svg 
        has already been set, it has its default properties removed and 
        then is replaced in the element tree.
        :param svg: an svg element, which is a child class of
                    xml.etree.ElementTree.Element
        """
        if self._svg is not None:
            del self._svg.attrib["xmlns"]
            del self._svg.attrib["xmlns:svg"]
            self.getroot().remove(self._svg)
        self._svg = element
        self._svg.set("xmlns", "http://www.w3.org/2000/svg")
        self._svg.set("xmlns:svg", "http://www.w3.org/2000/svg")
        self.getroot().insert(1, self._svg)
    
    @filepath.setter
    def filepath(self, filepath: str) -> None:
        """Sets the filepath of the svg and checks whether it can be 
        written to
        :param filepath: a string of the name and location of the file
        """
        if filepath is None:
            self._exists = False
            self._filepath = None
        elif os.path.isfile(filepath):
            self._exists = True
            self._filepath = os.path.realpath(filepath)
        elif (os.path.isdir(os.path.dirname(filepath))
              and os.path.basename(filepath) != ""):
            self._exists = False
            root, ext = os.path.splitext(filepath)
            if ext == "":
                filepath = filepath + ".svg"
            self._filepath = os.path.realpath(filepath)
        elif os.path.isdir(filepath):
            raise ValueError(filepath + " is a folder, please provide a"
                       + "filepath as the 1st argument")
        else:
            raise FileNotFoundError(filepath + " is not a valid filepath")
        self._validate_mode()
    
    @mode.setter
    def mode(self, mode: str) -> None:
        """Checks the access mode controlling this file session. Can be r 
        (read-only), w (write-only), x (exclusive creation), and + 
        (reading and writing)
        :param access_mode: a string of one character describing the 
                            access mode of the session
        """
        self._mode = mode
        self._validate_mode()
    
    def set_declaration(self, tail: str = "\n", version: str = "1.0",
                        encoding: str = "UTF-8",
                        standalone: str = "no") -> None:
        """Sets the xml declaration for the file. Will remove the 
        previous declaration if there was one already set.
        :param tail: the string to appear at the end of the 
                     declaration, defaults to a newline
        :param version: the xml version
        :param encoding: the encoding of the file
        :param standalone: whether the svg file will be standalone
        """
        instructions = {"version": version,
                        "encoding": encoding,
                        "standalone": standalone}
        if self._declaration is not None:
            self.getroot().remove(self._declaration)
        self._declaration = sw.xml_PI(instructions, tail)
        self.getroot().insert(0, self._declaration)
    
    def _read(self):
        pass
    
    def write(self, filepath: str = None, indent: str = None):
        """Writes the svg file to either a given filepath or, if given 
        None, to the initializing filepath
        """
        if filepath is None:
            filepath = self.filepath
        if self._declaration is None:
            self.set_declaration()
        if indent is not None:
            ET.indent(self.svg, indent)
        super().write(filepath)
    
    def _validate_mode(self) -> None:
        """Checks whether the file mode is being violated and will 
        raise an error if it is
        """
        if self._mode not in self.mode_options:
            raise ValueError("Provided "
                             + str(access_mode)
                             + " is not valid, must be one of these: "
                             + str(options))
        if self._filepath is None:
            self._mode = "w"
        elif self._mode == "x" and self._exists:
            raise FileExistsError("Exclusive creation (x) access chosen, "
                                  + self.filepath
                                  + " already exists!")
        elif self._mode == "r" and not self._exists:
            raise FileNotFoundError("Cannot read "
                                    + str(self.filepath)
                                    + ", file not found")

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
    
    def to_string(self) -> str:
        return ET.tostring(self)
    
    @classmethod
    def from_element(cls, element: ET.Element):
        if cls.tags is None:
            new = cls(element.tag)
        elif element.tag in cls.tags:
            new = cls()
        else:
            raise ValueError("Wrong element tag provided: "
                             + str(element.tag)
                             + " -- must be one of: "
                             + str(cls.tags))
        new.attrib = element.attrib
        return new

class svg(SVGElement):
    tags = ["svg", "svg:svg"]
    def __init__(self, id_: str = None) -> None:
        super().__init__("svg", id_)
    
    @property
    def width(self) -> str:
        return self._width
    
    @property
    def height(self):
        return self._height
    
    @property
    def viewBox(self):
        return self._viewBox
    
    @width.setter
    def width(self, width: str) -> None:
        self._width = sv.length(width)
        self._width_value = sv.length_value(self._width)
        super().set("width", self._width)
    
    @height.setter
    def height(self, height: str) -> str:
        self._height = sv.length(height)
        self._height_value = sv.length_value(self._height)
        super().set("height", self._height)
    
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
            case _:
                super().set(key, value)
    """
    def auto_size_view(self, margin = 0):
        \"""Sizes the svg viewbox based on the active g element's 
        subelements
        \"""
        if self.active_g is None:
            raise ValueError("No g element is active, "
                             + "svg cannot be auto-sized")
        find_term = "./g[@id='" + self.active_g + "']"
        g = self.svgs[self.active_svg].find(find_term)
        paths = g.findall("./path")
        circles = g.findall("./circle")
        geometry = []
        for p in paths:
            geometry.extend(
                sp.path_data_to_dicts(p.get("d"), p.get("id"))
            )
        for c in circles:
            geometry.append(sr.read_circle_to_dict(c))
        if geometry is not None:
            corners = trig.multi_fit_box(geometry)
            min_x, min_y = corners[0][0] - margin, corners[0][1] - margin
            max_x, max_y = corners[1][0] + margin, corners[1][1] + margin
            width = str(max_x - min_x)
            height = str(max_y - min_y)
            self.set_viewbox(width + self.unit, height + self.unit,
                             min_x, min_y)
        else:
            raise ValueError("g element has no geometry to be auto-sized")
    
    def write(self, filename: str, folder: str = None,
              indent: str = "  ", svg_id: str = None) -> None:
        \"""Writes svg tree to a file in the given folder.
        
        :param filename: The name of the new svg file. Can also be the 
                         full path and name of the file.
        :param folder: The folder the file should be written to
        :param indent: The way the file should be indented, two spaces is 
                       default.
        :param svg_id: The single svg id to write. Will write all by 
                       default.
        \"""
        if os.path.isfile(filename) and folder is None:
            filepath = os.path.realpath(filename)
        elif os.path.isdir(path.dirname(filename)) and os.path.basename != "":
            filepath = os.path.realpath(filename)
        elif os.path.isdir(filename):
            raise ValueError(filename + " is a folder, please provide a"
                       + "filename or filepath as the 1st argument")
        elif folder is not None and os.path.isdir(folder):
            filepath = os.path.join(folder, filename)
            filepath = os.path.realpath(filepath)
        else:
            raise ValueError(str(filename) + " is not a filepath and "
                             + str(folder) + " is not a folder")
        
        root, ext = os.path.splitext(filepath)
        if ext == "":
            filepath = filepath + ".svg"
        
        if svg_id is None:
            svg_elements = []
            for s in self.svgs:
                svg_elements.append(self.svgs[s])
        else:
            svg_elements = [self.svgs[s]]
        
        top = sw.svg_top(svg_elements, sw.xml_declaration())
        sw.write_xml(filepath, top)
    """

class g(SVGElement):
    tags = ["g", "svg:g"]
    def __init__(self, id_: str = None):
        super().__init__("g", id_)

class path(SVGElement):
    tags = ["path", "svg:path"]
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
    tags = ["circle", "svg:circle"]
    def __init__(self, cx: float, cy: float, r: float, id_: str = None):
        super().__init__("circle", id_)
        self.cx = cx
        self.cy = cy
        self.r = r
    
    @property
    def cx(self) -> float:
        return self._cx
    
    @property
    def cy(self) -> float:
        return self._cy
    
    @property
    def r(self) -> float:
        return self._r
    
    @property
    def geometry(self) -> dict:
        return sp.circle(self.id_, self.r, [self.cx, self.cy])
    
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

class defs:
    tags = ["defs", "svg:defs"]
    def __init__(self, id_: str = None):
        super().__init__("defs", id_)