import xml.etree.ElementTree as ET

class SVGPath:
    
    def __init__(self, element):
        self.element = element
        self.ID = element.get("id")
        self.style = element.get("style")
        self.d = element.get("d")

class InkscapeLayer:
    
    def __init__(self, element, document):
        self.root = element
        self._document = document
        ns = self._document.NAMESPACES
        
        label_search = document._xpath("label", ns["inkscape"])
        self._label = self.root.get(label_search)
        self._id = self.root.get("id")
        
        self.paths = {}
        for element in self.root.findall("default:path", ns):
            path = SVGPath(element)
            self.paths[path.ID] = path
    
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
        self._svg_tree = ET.parse(filepath)
        
        self._svg_element = self._svg_tree.getroot()
        named_views = self.xpath_find_all('./sodipodi:namedview')
        if len(named_views) == 1:
            self._named_view = named_views[0]
        else:
            print("Warning: more than one page in document, only the first \
                  page will be read")
            self._named_view = named_views[0]
        
        self._unit = self._named_view.get(
            self._xpath("document-units", self.NAMESPACES["inkscape"])
        )
        
        self.width = self._svg_element.get("width")
        self.height = self._svg_element.get("height")
        
        self.layers = {}
        layer_search = './svg:g[@inkscape:groupmode="layer"]'
        for element in self.xpath_find_all(layer_search):
            layer = InkscapeLayer(element, self)
            self.layers[layer.label] = layer
        
        self._elements = []
        for element in self._svg_tree.iter():
            self._elements.append(element)
    
    @property
    def elements(self):
        return self._elements
    
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value):
        string, number = self._parse_float_set_value(value)
        self._svg_element.set("width", string)
        self._width = number
    
    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self, value):
        string, number = self._parse_float_set_value(value)
        self._svg_element.set("height", string)
        self._height = number
    
    @property
    def unit(self):
        return self._unit
    
    @unit.setter
    def unit(self, value):
        # To-Do: make it so that when the unit is set all numbers get 
        # converted to the corresponding unit
        print("unit conversion not yet supported")
    
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