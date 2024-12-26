import sys
from pathlib import Path
import unittest

sys.path.append('src')

import freecad_sketch_readers as fsr
FREECADPATH = 'C:/Users/George/Documents/FreeCAD1/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/bin' 
sys.path.append(FREECADPATH) 

import FreeCAD as App

class TestFreeCADSketchReaders(unittest.TestCase):
    
    def setUp(self):
        self.FOLDER = 'tests/sample_freecad/'
        self.FILENAME = 'test_sketch_readers.FCStd'
        self.path = self.FOLDER + self.FILENAME
        self.document = App.open(self.path)
    
    def test_read_2d_vector(self):
        coordinates = [
            [[1, 1, 0], [1, 1]],
            [[1.0, 1.0, 0], [1.0, 1.0]],
            [[-1, -1, 0], [-1, -1]],
            [[0, 0, 0], [0, 0]],
            [[1e-7, 1e-7, 1e-7], [0, 0]],
        ]
        for xyz in coordinates:
            with self.subTest(xyz=xyz):
                vector = App.Vector(xyz[0])
                self.assertEqual(fsr.read_2d_vector(vector), xyz[1])
    
    def test_read_2d_vector_exceptions(self):
        coordinates = [
            [1, 1, 1],
            [1.0, 1.0, 1.0],
        ]
        for xyz in coordinates:
            vector = App.Vector(xyz)
            with self.subTest(vector=vector):
                with self.assertRaises(ValueError):
                    fsr.read_2d_vector(vector)
    
    def test_read_line_segment(self):
        sketch = self.document.getObjectsByLabel("xy_origin_angled_line")[0]
        geometry = sketch.Geometry
        line_segment = sketch.Geometry[0]
        test = fsr.read_line_segment(line_segment)
        ans = {
            "id": 1,
            "start": [0.0, 0.0],
            "end": [25.4, 25.4],
        }
        self.assertDictEqual(test, ans)
    
    def test_read_point(self):
        sketch = self.document.getObjectsByLabel("xy_point")[0]
        geometry = sketch.Geometry
        point = sketch.Geometry[0]
        test = fsr.read_point(point)
        ans = {
            "location": [50.8, 50.8]
        }
        self.assertDictEqual(test, ans)
    
    def test_read_circle(self):
        sketch = self.document.getObjectsByLabel("xy_origin_circle")[0]
        geometry = sketch.Geometry
        circle = sketch.Geometry[0]
        test = fsr.read_circle(circle)
        ans = {
            "id": 1,
            "location": [0, 0],
            "radius": 12.7,
        }
        self.assertDictEqual(test, ans)
    
    def test_read_circle_arc(self):
        sketch = self.document.getObjectsByLabel("xy_origin_upper_right_arc")[0]
        geometry = sketch.Geometry
        arc = sketch.Geometry[0]
        test = fsr.read_circle_arc(arc)
        ans = {
            "id": 1,
            "location": [0, 0],
            "radius": 38.1,
            "start": [38.1, 0],
            "end": [0, 38.1],
        }
        self.assertDictEqual(test, ans)

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()