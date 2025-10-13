import sys
from pathlib import Path
import unittest

sys.path.append('src')

from pancad.translators import freecad_sketcher_to_svg as fc_to_svg

class TestTranslators(unittest.TestCase):
    
    def test_line(self):
        tests = [
            [
                {"id": 1, "start": [0, 0], "end": [1, 1]},
                {"id": "line1", "d": "M 0 0 1 1", "geometry_type": "line"}
            ],
            [
                {"id": 2, "start": [1, 1], "end": [-1, -1]},
                {"id": "line2", "d": "M 1 1 -1 -1", "geometry_type": "line"}
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                out = fc_to_svg.line(t[0])
                self.assertDictEqual(out, t[1])
    
    def test_point(self):
        tests = [
            [
                {"location": [0, 0]}, 
                {"id": "point_0_0", "cx": 0, "cy": 0, "r": 0, "geometry_type": "point"}
            ],
            [
                {"location": [1, 1]}, 
                {"id": "point_1_1", "cx": 1, "cy": 1, "r": 0, "geometry_type": "point"}
            ],
            [
                {"location": [-1, -1]}, 
                {"id": "point_-1_-1", "cx": -1, "cy": -1, "r": 0, "geometry_type": "point"}
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                out = fc_to_svg.point(t[0])
                self.assertDictEqual(out, t[1])
    
    def test_circle(self):
        tests = [
            [
                { "id": 1, "location": [0, 0], "radius": 1}, 
                {"id": "circle1", "cx": 0, "cy": 0, "r": 1, "geometry_type": "circle"}
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                out = fc_to_svg.circle(t[0])
                self.assertDictEqual(out, t[1])
    
    def test_circular_arc(self):
        tests = [
            [
                {"id": 1, "location": [0, 0], "radius": 1.5, "start": [0, 1.5], "end": [1.5, 0]},
                {"id": "circular_arc1", "d": "M 0 1.5 A 1.5 1.5 0 0 0 1.5 0", "geometry_type": "circular_arc"}
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                out = fc_to_svg.circular_arc(t[0])
                self.assertDictEqual(out, t[1])
    
    def test_translate_geometry(self):
        # Checks whether this errors out, mediocre test
        test = [
            {'id': 1, 'start': [19.05, 25.4], 'end': [57.15, 25.4], 'geometry_type': 'line'},
            {'id': 2, 'start': [63.5, 31.75], 'end': [63.5, 44.45], 'geometry_type': 'line'},
            {'id': 3, 'start': [57.15, 50.8], 'end': [19.05, 50.8], 'geometry_type': 'line'},
            {'id': 4, 'start': [12.7, 44.45], 'end': [12.7, 31.75], 'geometry_type': 'line'},
            {'id': 5, 'location': [19.05, 31.75], 'radius': 6.35, 'start': [12.7, 31.75], 'end': [19.05, 25.4], 'geometry_type': 'circular_arc'},
            {'id': 6, 'location': [57.15, 31.75], 'radius': 6.35, 'start': [57.15, 25.4], 'end': [63.5, 31.75], 'geometry_type': 'circular_arc'},
            {'id': 7, 'location': [57.15, 44.45], 'radius': 6.35, 'start': [63.5, 44.45], 'end': [57.15, 50.8], 'geometry_type': 'circular_arc'},
            {'id': 8, 'location': [19.05, 44.45], 'radius': 6.35, 'start': [19.05, 50.8], 'end': [12.7, 44.45], 'geometry_type': 'circular_arc'},
            {'location': [12.700000000000003, 25.400000000000002], 'geometry_type': 'point'},
            {'location': [63.499999999999986, 50.8], 'geometry_type': 'point'},
            {'id': 11, 'location': [38.1, 38.1], 'radius': 6.35, 'geometry_type': 'circle'},
        ]
        out = fc_to_svg.translate_geometry(test)

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()