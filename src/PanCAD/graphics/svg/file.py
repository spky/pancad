"""A module providing a class to represent the svg file and collect xml 
elements to be written to files.
"""

import xml.etree.ElementTree as ET

from PanCAD.graphics.svg import element_utils as seu
from PanCAD.graphics.svg.elements import SVGElement
from PanCAD.utils import file_handlers
from PanCAD.utils.file_handlers import InvalidAccessModeError

class SVGFile(ET.ElementTree):
    """A class for svg files with a single svg element at the top that 
    contains multiple other elements. Is not intended to make xml 
    documents with multiple separate svg elements.
    
    :param filepath: The filepath of the svg file, defaults to None
    :param mode: The access mode of the svg file, defaults to r
    """
    def __init__(self, filepath: str = None, mode: str = "r") -> None:
        """Constructor method"""
        self._mode = mode
        self._declaration = None
        self._svg = None
        self.filepath = filepath
        super().__init__(SVGElement(None))
        if self.filepath is not None and mode == "r":
            self.parse()
    
    @property
    def filepath(self) -> str:
        """The filepath of the svg file
        
        :getter: Returns the filepath
        :setter: Sets the filepath after checking that it is a valid path and 
                 that it does not violate the access mode setting
        """
        return self._filepath
    
    @property
    def mode(self) -> str:
        """The access mode of the svg file. Can be r (read-only), w 
        (write-only), x (exclusive creation), and + (reading and writing)
        
        :getter: Returns the access mode
        :setter: Sets the access mode and checks whether it is violated by 
                 the filepath
        """
        return self._mode
    
    @property
    def svg(self) -> ET.Element:
        """The root svg node of the svg file.
        
        :getter: Returns the svg element of the file
        :setter: Sets the root node of the svg file to the new svg. If there 
                 was a previous svg, it will first remove the old one and 
                 replace it with this new one. The new svg will also have the 
                 svg namespace attached to it
        """
        return self._svg
    
    @svg.setter
    def svg(self, element: svg) -> None:
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
        if filepath is None:
            self._exists = False
            self._filepath = None
        else:
            self._filepath = file_handlers.filepath(filepath)
            self._exists = file_handlers.exists(filepath)
            if not self._exists and not self._filepath.endswith(".svg"):
                # if the file doesn't already exist, ensure .svg extension
                self._filepath = self._filepath + ".svg"
        self._validate_mode()
    
    @mode.setter
    def mode(self, mode: str) -> None:
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
        self._declaration = self.xml_PI(instructions, tail)
        self.getroot().insert(0, self._declaration)
    
    def parse(self, filepath: str = None) -> None:
        """Extends the ElementTree parse method to upgrade the 
        elements into SVGElements.
        
        :param filepath: The filepath of the svg file to parse, defaults to 
                         None which will cause it to read the internal filepath
        """
        if filepath is None:
            filepath = self.filepath 
        else: 
            filepath = file_handlers.filepath(filepath)
        file_handlers.validate_operation(filepath, self.mode, "r")
        with open(filepath, self.mode) as file:
            raw_tree = ET.parse(file)
            self.svg = seu.upgrade_element(raw_tree.getroot())
    
    def write(self, filepath: str = None, indent: str = "  "):
        """Writes the svg file to either a given filepath or, if given 
        None, to the initializing filepath. Will not update the 
        internal filepath so the file can be written to other locations.
        
        :param filepath: The filepath to write to. Defaults to None, which 
                         will cause it to write to the internal filepath
        :param indent: The set of characters to place before xml levels. 
                       Defaults to two spaces
        """
        if filepath is None:
            filepath = self.filepath
        else:
            filepath = file_handlers.filepath(filepath)
        if self._declaration is None:
            self.set_declaration()
        if indent is not None:
            ET.indent(self.svg, indent)
        
        if filepath == self.filepath:
            # The mode only needs to be validated if the user is trying to 
            # modify the original file location
            file_handlers.validate_operation(filepath, self.mode, "w")
        super().write(filepath)
    
    def _validate_mode(self) -> None:
        """Checks whether the file mode is being violated and will 
        raise an error if it is.
        """
        if self._filepath is not None:
            # filepath is allowed to be None during initialization
            file_handlers.validate_mode(self.filepath, self.mode)
        elif self._mode not in file_handlers.ACCESS_MODE_OPTIONS:
            raise InvalidAccessModeError(f"Invalid Mode: '{self._mode}'")
    
    @staticmethod
    def xml_PI(properties: dict, tail: str = "\n") -> ET.Element:
        """Returns an processing instruction element to be placed in an xml
        file. The declaration will have a newline 
        appended to the end of it unless it an alternative is provided
        
        :param properties: A dictionary full of key value pairs of the 
                           format 'property_name':'property_value'
        :param tail: A string of what should be placed at the end of the PI
        :returns: A Processing Instruction Element with the given 
                  properties as its text.
        """
        props = []
        for prop in properties:
            props.append(prop + '="' + properties[prop] + '"')
        text = " ".join(props)
        element = ET.ProcessingInstruction("xml", text)
        element.tail = tail
        return element

def read_svg(filepath: str, mode: str = "r") -> SVGFile:
    """Returns a PanCAD SVGFile class instance after reading a svg file.
    
    :param filepath: The filepath of the svg file
    :returns: An SVGFile instance describing the svg file at the filepath
    """
    return SVGFile(filepath, mode)