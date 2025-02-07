import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import os

sys.path.append('src')

import svg_file as sf
import svg_generators as sg
import svg_element_utils as seu


class TestSVGFile(unittest.TestCase):
    
    def setUp(self):
        self.SAMPLE_FOLDER = "tests/sample_svgs"
        self.DUMP_FOLDER = "tests/test_output_dump"
        self.default_style = sg.SVGStyle()
        self.default_style.set_property("fill", "none")
        self.default_style.set_property("stroke", "black")
        self.default_style.set_property("stroke-width", "0.010467px")
        self.default_style.set_property("stroke-linecap", "butt")
        self.default_style.set_property("stroke-linejoin", "miter")
    
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
    
    def test_write(self):
        filepath = os.path.join(self.DUMP_FOLDER, "test_svg_file_write")
        file = sf.SVGFile(filepath, "w")
        svg = sf.svg("svg1")
        svg.width = "1in"
        svg.height = "2in"
        svg.viewBox = [0, 0, 1, 2]
        group = sf.g("group1")
        group.append(sf.path("path1", "M 0 0 1 1"))
        group.set("style", self.default_style.string)
        svg.append(group)
        file.svg = svg
        file.write(indent="  ")
    
    def test_parse(self):
        filepath = os.path.join(self.SAMPLE_FOLDER, "input_sketch_test.svg")
        file = sf.SVGFile(filepath, "r")
        file.parse()
        # print(file.svg.to_string())
        # seu.debug_print_all_elements(file)
    
    @unittest.SkipTest
    def test_auto_size_view(self):
        self.file.add_svg(id_="svg1")
        self.file.add_g("layer1")
        self.file.add_path("path1",
                           "M 0.1 0.1 0.9 0.9")
        self.file.add_path("path2",
                           "M 0 1.5 A 1.5 1.5 0 0 0 1.5 0")
        self.file.add_circle("circle1", ["0.5in", "0.5in"], "0.25in")
        self.file.auto_size_view(0.25)
        out_svg = self.file.svgs[self.file.active_svg]
        check = ["2.0in", "2.0in", "-0.25 -0.25 2.0 2.0"]
        answer = [out_svg.get("width"), 
                  out_svg.get("height"),
                  out_svg.get("viewBox")]
        self.assertCountEqual(answer, check)
    
    @unittest.SkipTest
    def test_write_circle(self):
        self.file.add_svg(id_="svg1")
        self.file.set_viewbox("1in", "1in")
        self.file.add_g("layer1")
        self.file.add_circle("circle1", ["0.5in", "0.5in"], "0.25in")
        self.file.write("test_write_circle_svg.svg", self.folder)
    
    @unittest.SkipTest
    def test_read_file(self):
        filepath = os.path.join(self.SAMPLE_FOLDER,
                                "input_sketch_test.svg")
        self.file.read_file(filepath)


        
if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()