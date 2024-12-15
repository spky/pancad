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
        top_element = svg_top(self.svg, "  ")
        print(top_element)

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
        top_element = svg_top(self.svg, "  ")
        write_xml(filename, top_element)


if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()