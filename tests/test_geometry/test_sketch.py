import unittest

from PanCAD.geometry import (
    Sketch, CoordinateSystem, Plane, Line, LineSegment, Point
)
from PanCAD.geometry.constants import PlaneName

class TestSketchInit(unittest.TestCase):
    
    def setUp(self):
        self.cs = CoordinateSystem((0, 0, 0))
    
    def test_plane_name(self):
        sketch = Sketch(self.cs, "yx")
        self.assertEqual(sketch.plane_name, PlaneName.XY)
    
    def test_plane_name_exception(self):
        with self.assertRaises(ValueError):
            sketch = Sketch(self.cs, "fake")
    
    def test_get_plane(self):
        sketch = Sketch(self.cs, "YZ")
        plane = sketch.get_plane()
        self.assertEqual(plane, Plane((0, 0, 0), (1, 0, 0)))

class TestGeometry(unittest.TestCase):
    def setUp(self):
        cs = CoordinateSystem((0, 0, 0))
        self.sketch = Sketch(cs)
    
    def test_geometry_set(self):
        geometry = [
            Point(1, 1),
            Line.from_two_points((0, 0), (0, 1)),
            LineSegment((-1, -1), (-1, 1)),
        ]
        self.sketch.geometry = geometry
    
    def test_3d_geometry_exception(self):
        geometry = [
            Point(1, 1, 1),
            Line.from_two_points((0, 0, 0), (0, 1, 0)),
            LineSegment((-1, -1, 0), (0, -2, 0)),
            LineSegment((-1, -1), (0, -2)),
        ]
        with self.assertRaises(ValueError):
            self.sketch.geometry = geometry

if __name__ == "__main__":
    unittest.main()