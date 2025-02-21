"""A module providing a class to represent the svg file and collect xml 
elements to be written to files.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET

import svg.svg_writers as sw
import svg.svg_element_utils as seu
import file_handlers as fh

from file_handlers import InvalidAccessModeError

from svg.svg_elements import (
    SVGElement,
    svg,
    g,
    path,
    circle,
    defs
)

class SVGFile(ET.ElementTree):
    """A class for svg files with a single svg element at the top that 
    contains multiple other elements. Is not intended to make xml 
    documents with multiple separate svg elements
    """
    def __init__(self, filepath: str = None, mode: str = "r") -> None:
        self._mode = mode
        self._declaration = None
        self._svg = None
        self.filepath = filepath
        super().__init__(SVGElement(None))
        if self.filepath is not None and mode == "r":
            self.parse()
    
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
        else:
            self._filepath = fh.filepath(filepath)
            self._exists = fh.exists(filepath)
            if not self._exists and not self._filepath.endswith(".svg"):
                # if the file doesn't already exist, ensure .svg extension
                self._filepath = self._filepath + ".svg"
        self._validate_mode()
    
    @mode.setter
    def mode(self, mode: str) -> None:
        """Checks the access mode controlling this file session. Can be r 
        (read-only), w (write-only), x (exclusive creation), and + 
        (reading and writing)
        :param mode: a string of one character describing the 
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
    
    def parse(self, filepath: str = None) -> None:
        """Extends the ElementTree parse method to upgrade the 
        elements into SVGElements
        :param filepath: The name and location of the file to parse
        """
        if filepath is None:
            filepath = self.filepath 
        else: 
            filepath = fh.filepath(filepath)
        fh.validate_operation(filepath, self.mode, "r")
        with open(filepath, self.mode) as file:
            raw_tree = ET.parse(file)
            self.svg = seu.upgrade_element(raw_tree.getroot())
    
    def write(self, filepath: str = None, indent: str = None):
        """Writes the svg file to either a given filepath or, if given 
        None, to the initializing filepath. Will not update the 
        internal filepath so the file can be written to other locations.
        :param filepath: The name and location of the file to parse
        :param indent: The set of characters to place before xml levels
        """
        if filepath is None:
            filepath = self.filepath
        else:
            filepath = fh.filepath(filepath)
        if self._declaration is None:
            self.set_declaration()
        if indent is not None:
            ET.indent(self.svg, indent)
        fh.validate_operation(filepath, self.mode, "w")
        super().write(filepath)
    
    def _validate_mode(self) -> None:
        """Checks whether the file mode is being violated and will 
        raise an error if it is
        """
        if self._filepath is not None:
            # filepath is allowed to be None during initialization
            fh.validate_mode(self.filepath, self.mode)
        elif self._mode not in fh.ACCESS_MODE_OPTIONS:
            raise InvalidAccessModeError(f"Invalid Mode: '{self._mode}'")