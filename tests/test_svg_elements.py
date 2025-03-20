import sys
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
import os

sys.path.append('src')

from PanCAD.graphics.svg import elements as se

class TestSVG(unittest.TestCase):
    
    def setUp(self):
        self.svg = se.svg()
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
    
    def test_width_change(self):
        tests = [
            ["1", "1in", "1in"], # Start, Input, Result
            ["1", "1mm", "1mm"],
            ["1in", "1mm", "1mm"],
            [1, "1mm", "1mm"],
        ]
        for t in tests:
            with self.subTest(t=t):
                self.svg.width = t[0]
                self.svg.width = t[1]
                self.assertEqual(self.svg.width, t[2])
    
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
    
    def test_unit(self):
        tests = [
            ["in", ["in", "1in", "1in"]],
            ["", ["", "1", "1"]],
            ["mm", ["mm", "1mm", "1mm"]],
        ]
        self.svg.width = "1"
        self.svg.height = "1"
        for t in tests:
            with self.subTest(t=t):
                input_ = t[0]
                check = t[1]
                self.svg.unit = input_
                answer = [self.svg.unit, self.svg.width, self.svg.height]
                self.assertCountEqual(answer, check)
    
    def test_auto_size(self):
        group = se.g("group1")
        group.append(se.path("path1", "M 0.1 0.1 0.9 0.9"))
        group.append(se.path("path2", "M 0 1.5 A 1.5 1.5 0 0 0 1.5 0"))
        group.append(se.circle("circle1", 0.5, 0.5, 0.25))
        self.svg.unit = "in"
        self.svg.append(group)
        self.svg.auto_size(margin=0.25)
        check = ["2.0in", "2.0in", "-0.25 -0.25 2.0 2.0"]
        answer = [self.svg.width, 
                  self.svg.height,
                  self.svg.viewBox]
        self.assertCountEqual(answer, check)

class TestSVGElement(unittest.TestCase):
    
    def test_from_element(self):
        element = ET.Element("blah", {"id": "bleh"})
        test = se.SVGElement.from_element(element)
        self.assertEqual(ET.tostring(test), b'<blah id="bleh" />')
    
    def test_sub(self):
        element = se.SVGElement("test", "test1")
        element.append(se.SVGElement("test", "test2"))
        self.assertEqual(element.sub("test2").id_, "test2")

class TestSVGPath(unittest.TestCase):
    
    def test_init(self):
        path_test_1 = se.path("path1", "M 1 1")
        path_test_2 = se.path("path2")
    
    def test_from_element(self):
        basic_path = ET.Element("path", {"id": "path1", "d": "M 1 1"})
        test = se.path.from_element(basic_path)
        self.assertEqual(ET.tostring(test), b'<path id="path1" d="M 1 1" />')
    
    def test_geometry(self):
        path_test = se.path("path1", "M 0.1,0.1 0.9,0.9 0.1,0.9z")
        geo = path_test.geometry

class TestSVGCircle(unittest.TestCase):
    
    def test_init(self):
        test_circle = se.circle("circle1", 1.0, 1.0, 1.0)
        self.assertEqual(
            test_circle.to_string(),
            b'<circle id="circle1" cx="1.0" cy="1.0" r="1.0" />'
        )
    
    def test_geometry(self):
        test_circle = se.circle("circle1", 1.0, 1.0, 1.0)
        geo = test_circle.geometry

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()