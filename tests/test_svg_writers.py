import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

sys.path.append('src')

from svg_writers import (
    xml_properties,
    xml_declaration,
    svg_top,
    write_xml,
    svg_property_defaults,
    inkscape_svg_property_defaults,
    make_svg_element,
    make_g_element,
    make_path_element,
    make_circle_element,
)

class TestGenerators(unittest.TestCase):
    def setUp(self):
        self.svg = ET.Element("svg")
        self.declaration = xml_declaration()
        self.layer = ET.Element("g")
        self.path = path = ET.Element("path")
        self.path.set("id", "path1")
        
        self.svg.append(self.layer)
        self.layer.append(self.path)
    
    def test_xml_properties(self):
        properties_dict = {
            "version": "1.0",
            "encoding": "UTF-8",
            "standalone": "yes",
        }
        ans = 'version="1.0" encoding="UTF-8" standalone="yes"'
        test = xml_properties(properties_dict)
        self.assertEqual(test, ans)
    
    def test_xml_declaration_default(self):
        self.assertEqual(xml_declaration().text,
                         'xml version="1.0" encoding="UTF-8" standalone="yes"')
    
    def test_svg_top(self):
        top_element = svg_top([self.svg], None)
        ans = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<svg><g><path id="path1" /></g></svg>'
        self.assertEqual(ET.tostring(top_element, encoding="UTF-8"), ans)
    
    def test_svg_property_defaults(self):
        test = svg_property_defaults("svg1", "1.0in", "2.1in")
        ans = {
            "id": "svg1",
            "width": "1.0in",
            "height": "2.1in",
            "xmlns": "http://www.w3.org/2000/svg",
            "xmlns:svg": "http://www.w3.org/2000/svg",
        }
        self.assertDictEqual(test,ans)
    
    def test_inkscape_svg_property_defaults(self):
        test = inkscape_svg_property_defaults("inkscape_svg.svg")
        ans = {
            "xmlns:inkscape": "http://www.inkscape.org/namespaces/inkscape",
            "xmlns:sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
            "sodipodi:docname": "inkscape_svg.svg",
        }
        self.assertDictEqual(test,ans)
    
    def test_make_svg_element(self):
        test = make_svg_element("svg1", "1.0in", "2.1in")
        test_text = ET.tostring(test, encoding="UTF-8")
        ans = b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" width="1.0in" height="2.1in" viewBox="0 0 1.0 2.1" id="svg1" />'
        self.assertEqual(test_text, ans)
    
    def test_make_g_element(self):
        test = make_g_element("layer1")
        test_text = ET.tostring(test, encoding="UTF-8")
        ans = b'<g id="layer1" />'
        self.assertEqual(test_text, ans)
    
    def test_make_path_element(self):
        test = make_path_element("path1", "fill:none", "M 1.01 2.02")
        test_text = ET.tostring(test, encoding="UTF-8")
        ans = b'<path style="fill:none" d="M 1.01 2.02" id="path1" />'
        self.assertEqual(test_text, ans)
    
    def test_make_circle_element(self):
        test = make_circle_element("circle1", "fill:none", ["1in", "1in"], "0.5in")
        test_text = ET.tostring(test, encoding="UTF-8")
        ans = b'<circle style="fill:none" cx="1" cy="1" r="0.5" id="circle1" />'
        self.assertEqual(test_text,ans)
    

class TestWriters(unittest.TestCase):
    def setUp(self):
        self.svg = ET.Element("svg")
        self.declaration = xml_declaration()
        self.layer = ET.Element("g")
        self.path = path = ET.Element("path")
        self.path.set("id", "path1")
        
        self.svg.append(self.layer)
        self.layer.append(self.path)
    
    def test_write_xml(self):
        filename = "tests/test_output_dump/test_write_xml_out.svg"
        top_element = svg_top([self.svg], "  ")
        write_xml(filename, top_element)


if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()