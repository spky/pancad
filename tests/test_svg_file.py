import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import os

sys.path.append('src')

import svg_file as sf
import svg_generators as sg
import svg_element_utils as seu

from file_handlers import InvalidAccessModeError


class TestSVGFileInternal(unittest.TestCase):
    
    def setUp(self):
        self.SAMPLE_FOLDER = "tests/sample_svgs"
        self.DUMP_FOLDER = "tests/test_output_dump"
    
    def test_init(self):
        tests = [
            [os.path.join(self.SAMPLE_FOLDER,"input_sketch_test.svg"), "r"],
            [os.path.join(self.DUMP_FOLDER, "should_not_exist.svg"), "w"],
            [os.path.join(self.DUMP_FOLDER, "should_not_exist.svg"), "x"],
            [os.path.join(self.DUMP_FOLDER, "should_not_exist.svg"), "+"],
            [None, "r"],
        ]
        for t in tests:
            with self.subTest(t=t):
                file = sf.SVGFile(t[0], t[1])
    
    def test_set_declaration(self):
        file = sf.SVGFile()
        file.set_declaration()
        test = ET.tostring(file._declaration)
        ans = b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        self.assertEqual(test, ans)
    
    def test_setting_svg(self):
        file = sf.SVGFile()
        svg = sf.svg("svg1")
        file.svg = svg
    
    def test_resetting_svg(self):
        # Checks whether the default properties get removed from original
        file = sf.SVGFile()
        svg1 = sf.svg("svg1")
        svg2 = sf.svg("svg2")
        file.svg = svg1
        file.svg = svg2
        self.assertEqual(ET.tostring(svg1), b'<svg id="svg1" />')
    
    def test_parse(self):
        filepath = os.path.join(self.SAMPLE_FOLDER, "input_sketch_test.svg")
        file = sf.SVGFile(filepath, "r")
        file.parse()
    
    def test_validate_mode_InvalidAccessModeError(self):
        file = sf.SVGFile()
        with self.assertRaises(InvalidAccessModeError):
            file.mode = "bad"
    

class TestSVGFileWriting(unittest.TestCase):
    
    def setUp(self):
        self.DUMP_FOLDER = "tests/test_output_dump"
        self.default_style = sg.SVGStyle()
        self.default_style.set_property("fill", "none")
        self.default_style.set_property("stroke", "black")
        self.default_style.set_property("stroke-width", "0.010467px")
        self.default_style.set_property("stroke-linecap", "butt")
        self.default_style.set_property("stroke-linejoin", "miter")
        self.svg = sf.svg("svg1")
        self.svg.unit = "in"
    
    def test_write(self):
        filepath = os.path.join(self.DUMP_FOLDER, "test_svg_file_write")
        file = sf.SVGFile(filepath, "w")
        self.svg.append(sf.g("g1"))
        self.svg.sub("g1").set("style", self.default_style.string)
        
        self.svg.sub("g1").append(sf.path("path1", "M 0 0 1 1"))
        
        self.svg.auto_size()
        file.svg = self.svg
        file.write(indent="  ")
    
    def test_write_circle(self):
        filepath = os.path.join(self.DUMP_FOLDER, "test_svg_file_write_circle")
        file = sf.SVGFile(filepath, "w")
        self.svg.append(sf.g("g1"))
        self.svg.sub("g1").set("style", self.default_style.string)
        
        self.svg.sub("g1").append(sf.circle("c1", 0.5, 0.5, 0.5))
        
        self.svg.auto_size()
        file.svg = self.svg
        file.write(indent="  ")

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()