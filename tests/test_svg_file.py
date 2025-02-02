import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import os

sys.path.append('src')

import svg_file as sf
import svg_generators as sg

class TestSVGElement(unittest.TestCase):
    
    def setUp(self):
        self.svg = sf.svg()
        self.folder = os.path.join("tests","test_output_dump")
        self.SAMPLE_FOLDER = "tests/sample_svgs/"
        self.OUTPUT_DUMP_FOLDER = "tests/test_output_dump/"
    
    def test_id(self):
        goal_id = "svg1"
        self.svg.id_ = goal_id
        test = [self.svg._id, self.svg.id_, self.svg.get("id")]
        check = [goal_id]*3
        self.assertCountEqual(test, check)
    
    def test_width(self):
        goal_width = "1in"
        self.svg.width = goal_width
        test = [self.svg._width, self.svg.width,
                self.svg.get("width"), self.svg._width_value]
        check = [goal_width]*3 + [1]
        self.assertCountEqual(test, check)
    
    def test_height(self):
        goal_height = "1in"
        self.svg.height = goal_height
        test = [self.svg._height, self.svg.height,
                self.svg.get("height"), self.svg._height_value]
        check = [goal_height]*3 + [1]
        self.assertCountEqual(test, check)
    
    def test_viewBox_str(self):
        goal_viewBox = "-1 -2 3 4"
        self.svg.viewBox = goal_viewBox
        test = [self.svg._viewBox, self.svg.viewBox, self.svg.get("viewBox")]
        check = [goal_viewBox]*3
        self.assertCountEqual(test, check)
    
    def test_viewBox_list(self):
        goal_viewBox = [-1, -2, 3, 4]
        self.svg.viewBox = goal_viewBox
        test = [self.svg._viewBox, self.svg.viewBox, self.svg.get("viewBox")]
        check = ["-1 -2 3 4"]*3
        self.assertCountEqual(test, check)

class TestSVGElement(unittest.TestCase):
    
    def test_from_element(self):
        element = ET.Element("blah", {"id": "bleh"})
        test = sf.SVGElement.from_element(element)
        self.assertEqual(ET.tostring(test), b'<blah id="bleh" />')

class TestSVGPath(unittest.TestCase):
    
    def test_init(self):
        path_test_1 = sf.path("path1", "M 1 1")
        path_test_2 = sf.path("path2")
    
    def test_from_element(self):
        basic_path = ET.Element("path", {"id": "path1", "d": "M 1 1"})
        test = sf.path.from_element(basic_path)
        self.assertEqual(ET.tostring(test), b'<path id="path1" d="M 1 1" />')
    
    def test_geometry(self):
        path_test = sf.path("path1", "M 0.1,0.1 0.9,0.9 0.1,0.9z")
        geo = path_test.geometry
        # print(geo)

class TestSVGCircle(unittest.TestCase):
    
    def test_init(self):
        test_circle = sf.circle(1.0, 1.0, 1.0, "circle1")
        self.assertEqual(
            test_circle.to_string(),
            b'<circle id="circle1" cx="1.0" cy="1.0" r="1.0" />'
        )
    
    def test_geometry(self):
        test_circle = sf.circle(1.0, 1.0, 1.0, "circle1")
        geo = test_circle.geometry
        # print(geo)

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