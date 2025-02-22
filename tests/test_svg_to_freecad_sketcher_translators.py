import sys
from pathlib import Path
import unittest

sys.path.append('src')

import translators.svg_to_freecad_sketcher as sfst

class TestTranslators(unittest.TestCase):
    
    def test_line(self):
        tests = [
            [
                {"id": "line1_0", "start": [0, 0], "end": [1, 1], "geometry_type": "line"},
                {"id": 1, "start": [0, 0], "end": [1, 1], "geometry_type": "line"},
            ],
            [
                {"id": "line2_0",  "start": [1, 1], "end": [-1, -1], "geometry_type": "line"},
                {"id": 2, "start": [1, 1], "end": [-1, -1], "geometry_type": "line"},
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                out = sfst.line(t[0])
                self.assertDictEqual(out, t[1])
    
    def test_point(self):
        tests = [
            [
                {"id": "point_0_0", "center": [0, 0], "radius": 0, "geometry_type": "point"},
                {"location": [0, 0], "geometry_type": "point"}, 
            ],
            [
                {"id": "point_1_1", "center": [1, 1], "radius": 0, "geometry_type": "point"},
                {"location": [1, 1], "geometry_type": "point"}, 
            ],
            [
                {"id": "point_-1_-1", "center": [-1, -1], "radius": 0, "geometry_type": "point"},
                {"location": [-1, -1], "geometry_type": "point"}, 
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                out = sfst.point(t[0])
                self.assertDictEqual(out, t[1])
    
    def test_circle(self):
        tests = [
            [
                {"id": "circle1", "center": [0, 0], "radius": 1, "geometry_type": "circle"},
                { "id": 1, "location": [0, 0], "radius": 1, "geometry_type": "circle"}, 
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                out = sfst.circle(t[0])
                self.assertDictEqual(out, t[1])
    
    def test_circular_arc(self):
        tests = [
            [
                {
                    "id": "circular_arc1_0",
                    "start": [0, 1.5],
                    "end": [1.5, 0],
                    "radius": 1.5,
                    "large_arc_flag": 0,
                    "sweep_flag": 0,
                    "geometry_type": "circular_arc"
                },
                {
                    "id": 1,
                    "location": [0, 0],
                    "radius": 1.5,
                    "start": 0,
                    "end": 1.570796,
                    "geometry_type": "circular_arc"
                },
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                out = sfst.circular_arc(t[0])
                self.assertDictEqual(out, t[1])

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()