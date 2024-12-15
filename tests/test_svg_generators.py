import sys
from pathlib import Path
import unittest

sys.path.append('src')

from svg_generators import (
    make_moveto,
    make_arc,
    make_lineto,
    make_horizontal,
    make_vertical,
    make_path_data,
    make_style,
)

class TestSVGgenerators(unittest.TestCase):
    
    def test_make_moveto(self):
        coordinates = [[100, 150], [200, 250], [300, 350]]
        relative = True
        ans = "m 100 150 200 250 300 350"
        test = make_moveto(coordinates, relative)
        self.assertEqual(test, ans)
    
    def test_make_arc(self):
        ans = "a 0.31844541 0.31844541 0 0 1 1.2957424 0.67649852"
        relative = True
        test = make_arc(
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
        test = make_lineto(coordinates, relative)
        self.assertEqual(test, ans)
    
    def test_make_horizontal(self):
        lengths = [100, 150, 200, 250, 300, 350]
        relative = True
        ans = "h 100 150 200 250 300 350"
        test = make_horizontal(lengths, relative)
        self.assertEqual(test, ans)
    
    def test_make_vertical(self):
        lengths = [100, 150, 200, 250, 300, 350]
        relative = True
        ans = "v 100 150 200 250 300 350"
        test = make_vertical(lengths, relative)
        self.assertEqual(test, ans)
    
    def test_make_path_data(self):
        commands = [
            "M 100 150 200 250 300 350",
            "a 0.31844541 0.31844541 0 0 1 1.2957424 0.67649852",
        ]
        delimiter = "\n"
        ans = "M 100 150 200 250 300 350\na 0.31844541 0.31844541 0 0 1 1.2957424 0.67649852"
        test = make_path_data(commands, delimiter)
        self.assertEqual(test, ans)
    
    def test_make_style(self):
        style_dict = {
            "fill": "none",
            "stroke": "#000000",
            "stroke-width": "0.010467px",
            "stroke-linecap": "butt",
            "stroke-linejoin": "miter",
            "stroke-opacity": 1,
        }
        ans = "fill:none;stroke:#000000;stroke-width:0.010467px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
        test = make_style(style_dict)
        self.assertEqual(test, ans)

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()