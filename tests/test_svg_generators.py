import sys
from pathlib import Path
import unittest

sys.path.append('src')

from enum_svg_color_keywords import ColorKey

import svg_generators as sg

class TestSVGgenerators(unittest.TestCase):
    
    def test_make_moveto(self):
        coordinates = [[100, 150], [200, 250], [300, 350]]
        relative = True
        ans = "m 100 150 200 250 300 350"
        test = sg.make_moveto(coordinates, relative)
        self.assertEqual(test, ans)
    
    def test_make_arc(self):
        ans = "a 0.31844541 0.31844541 0 0 1 1.2957424 0.67649852"
        relative = True
        test = sg.make_arc(
            0.31844541,
            0.31844541,
            0,
            0,
            1,
            1.2957424,
            0.67649852,
            relative)
        self.assertEqual(test, ans)
    
    def test_make_lineto(self):
        coordinates = [[100, 150], [200, 250], [300, 350]]
        relative = True
        ans = "l 100 150 200 250 300 350"
        test = sg.make_lineto(coordinates, relative)
        self.assertEqual(test, ans)
    
    def test_make_horizontal(self):
        lengths = [100, 150, 200, 250, 300, 350]
        relative = True
        ans = "h 100 150 200 250 300 350"
        test = sg.make_horizontal(lengths, relative)
        self.assertEqual(test, ans)
    
    def test_make_vertical(self):
        lengths = [100, 150, 200, 250, 300, 350]
        relative = True
        ans = "v 100 150 200 250 300 350"
        test = sg.make_vertical(lengths, relative)
        self.assertEqual(test, ans)
    
    def test_make_path_data(self):
        commands = [
            "M 100 150 200 250 300 350",
            "a 0.31844541 0.31844541 0 0 1 1.2957424 0.67649852",
        ]
        delimiter = "\n"
        ans = "M 100 150 200 250 300 350\na 0.31844541 0.31844541 0 0 1 1.2957424 0.67649852"
        test = sg.make_path_data(commands, delimiter)
        self.assertEqual(test, ans)

class TestStyle(unittest.TestCase):
    
    def test_set_property(self):
        style = sg.SVGStyle()
        style.set_property("color-interpolation", "auto")
        style.set_property("color-interpolation-filters", "auto")
        style.set_property("color-profile", "auto")
        style.set_property("color-rendering", "auto")
        style.set_property("color-rendering", "auto")
        style.set_property("fill", "black")
        style.set_property("fill-opacity", 0.5)
        style.set_property("fill-rule", "nonzero")
        style.set_property("image-rendering", "auto")
        style.set_property("shape-rendering", "auto")
        style.set_property("stroke", "black")
        style.set_property("stroke-linecap", "butt")
        style.set_property("stroke-linejoin", "miter")
        style.set_property("stroke-miterlimit", 1)
        style.set_property("stroke-opacity", 0.5)
        style.set_property("stroke-width", 0.5)
        style.set_property("text-rendering", "auto")
    
    def test_string(self):
        style = sg.SVGStyle()
        style.set_property("fill", "black")
        style.set_property("stroke", "black")
        style.set_property("stroke-width", 0.5)
        self.assertEqual(style.string, "fill:black;stroke:black;stroke-width:0.5")

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()