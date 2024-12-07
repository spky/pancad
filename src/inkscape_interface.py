import xml.etree.ElementTree as ET
import xml.dom.minidom as mdom
from text2freecad.svg_interface import SVGPath


class InkscapeLayer:
    
    def __init__(self, element, document):
        self.root = element
        self._document = document
        ns = self._document.NAMESPACES
        
        label_search = document._xpath("label", ns["inkscape"])
        self._label = self.root.getAttributeNS(ns["inkscape"], "label")
        self._id = self.root.getAttribute("id")
        
        self.paths = {}
        for element in self.root.getElementsByTagName("path"):
            path = SVGPath(element)
            self.paths[path.svg_id] = path
    
    @property
    def label(self):
        return self._label

class InkscapeDocument:
    NAMESPACES = {
    "inkscape": "http://www.inkscape.org/namespaces/inkscape",
    "svg": "http://www.w3.org/2000/svg",
    "default": "http://www.w3.org/2000/svg",
    "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
    }
    def __init__(self, filepath):
        self.document = mdom.parse(filepath)
        self._svg_element = self.document.documentElement
        named_views = self.document.getElementsByTagNameNS(
                          self.NAMESPACES["sodipodi"], "namedview")
        if len(named_views) == 1:
            self._named_view = named_views[0]
        else:
            print("Warning: more than one page in document, only the first \
                  page will be read")
            self._named_view = named_views[0]
        
        self._unit = self._named_view.getAttributeNS(
            self.NAMESPACES["inkscape"], "document-units")
        
        self.width = self._svg_element.getAttribute("width")
        self.height = self._svg_element.getAttribute("height")
        
        self.layers = {}
        layer_search = './svg:g[@inkscape:groupmode="layer"]'
        for element in self._svg_element.getElementsByTagNameNS(
                           self.NAMESPACES["svg"],
                           "g"
                           ):
            layer = InkscapeLayer(element, self)
            self.layers[layer.label] = layer
    
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value):
        string, number = self._parse_float_set_value(value)
        self._svg_element.setAttribute("width", string)
        self._width = number
    
    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self, value):
        string, number = self._parse_float_set_value(value)
        self._svg_element.setAttribute("height", string)
        self._height = number
    
    @property
    def unit(self):
        return self._unit
    
    @unit.setter
    def unit(self, value):
        # To-Do: make it so that when the unit is set all numbers get 
        # converted to the corresponding unit
        print("unit conversion not yet supported")
    
    def write(self, filename):
        with open(filename, "w") as xmlfile:
            prettyxml = self.document.toprettyxml(encoding="UTF-8", 
                                                  indent='  ',
                                                  newl="",
                                                  standalone="no"
                                                  )
            output_text = prettyxml.decode("UTF-8")
            output_text = output_text.replace("\" ","\"\n")
            output_text = output_text.replace("><",">\n<")
            xmlfile.write(output_text)
    
    def xpath_find_all(self, search):
        list_ = []
        for item in self._svg_element.findall(search, self.NAMESPACES):
            list_.append(item)
        return list_
    
    def _xpath(self, local_tag, namespace):
        return "{" + namespace + "}" + local_tag
    
    def _parse_float_set_value(self, value):
        """ returns a string with default unit and number parsed out of 
        the given value """
        if isinstance(value, str):
            # To-Do: add unit conversion to the document's unit
            # To-Do: make sure that the string has a unit to begin with
            string = value
            number = self._remove_number_text(value)
        elif isinstance(value, (float, int)):
            string = str(value) + self._unit
            number = float(value)
        else:
            # To-Do: add error checking for datatypes to set width to
            print("Wrong datatype given to setter")
        return string, number
    
    def _remove_number_text(self, text):
        """ Returns the numeric part of a string as a float. Assumes 
        there's only one number in the string """
        no_text_number = ''
        for char in text:
            if char.isdecimal() or char == ".":
                no_text_number = ''.join([no_text_number, char])
        return float(no_text_number)