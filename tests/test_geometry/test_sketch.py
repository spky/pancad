import unittest
from math import radians

from pancad.geometry import (
    Sketch, CoordinateSystem, Plane, Line, LineSegment, Point, Circle, Ellipse,
)
from pancad.geometry.constraints import (
    Coincident, Vertical, Horizontal, Equal, Angle,
    Distance, HorizontalDistance, VerticalDistance, Diameter
)
from pancad.geometry.constants import SketchConstraint, ConstraintReference

from tests.sample_pancad_objects import sample_sketches

class TestSketchInit(unittest.TestCase):
    
    def setUp(self):
        self.cs = CoordinateSystem((0, 0, 0))
    
    def test_plane_reference(self):
        sketch = Sketch(self.cs, ConstraintReference.XY)
        self.assertEqual(sketch.plane_reference, ConstraintReference.XY)
    
    def test_plane_reference_exception(self):
        with self.assertRaises(ValueError):
            sketch = Sketch(self.cs, ConstraintReference.CORE)
    
    def test_get_plane(self):
        sketch = Sketch(self.cs, ConstraintReference.YZ)
        plane = sketch.get_plane()
        self.assertEqual(plane, Plane((0, 0, 0), (1, 0, 0)))

class TestDunder(unittest.TestCase):
    def setUp(self):
        cs = CoordinateSystem((0, 0, 0))
        geom = [Point(1,1), LineSegment((-1,-1),(-1,1))]
        cons = [Coincident(geom[0], geom[1])]
        self.sketch = Sketch(cs, geometry=geom, constraints=cons)
    
    def test_repr(self):
        # Checks whether repr errors out
        sketch_repr = repr(self.sketch)

class TestSummary(unittest.TestCase):
    
    def make_ellipse_sketch(self) -> Sketch:
        geometry = [
            Ellipse.from_angle((0, 0), 2, 1, radians(45))
        ]
        sketch = Sketch(geometry=geometry, uid="test_sketch")
        return sketch
    
    def test_square_sketch_summary(self):
        sketch = sample_sketches.square()
        sketch_str = str(sketch)
        # print(); print(sketch_str)
    
    def test_ellipse_sketch_summary(self):
        sketch = self.make_ellipse_sketch()
        sketch_str = str(sketch)
        # print(); print(sketch_str)
    
    def test_rounded_square_summary(self):
        sketch = sample_sketches.rounded_square()
        sketch_str = str(sketch)

class TestGeometrySetting(unittest.TestCase):
    def setUp(self):
        cs = CoordinateSystem((0, 0, 0))
        self.sketch = Sketch(cs)
    
    def test_geometry_setting(self):
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


class TestConstraints(unittest.TestCase):
    
    def setUp(self):
        self.cs = CoordinateSystem((0, 0, 0))
        self.geo = [
            Point(0, 0, uid="Point1"),
            Point(1, 1, uid="Point2"),
            LineSegment((0, 0), (1, 0), uid="horizontal_line"),
            LineSegment((0, 0), (0, 1), uid="vertical_line"),
        ]
    
    def test_constraint_validation_success(self):
        constraints = [Coincident(self.geo[0], self.geo[1])]
        sketch = Sketch(self.cs, geometry=self.geo, constraints=constraints)
    
    def test_constraint_validation_failure(self):
        constraints = [Coincident(self.geo[0], Point(2, 2))]
        with self.assertRaises(LookupError):
            sketch = Sketch(self.cs, geometry=self.geo, constraints=constraints)

class TestConstruction(unittest.TestCase):
    
    def setUp(self):
        self.cs = CoordinateSystem((0, 0, 0))
        self.geo = [
            LineSegment((0, 0), (1, 1)),
            LineSegment((1, 1), (1, 0)),
        ]
        self.construction = [
            False,
            True,
        ]
        self.uid = "TestSketch"
    
    def test_init(self):
        sketch = Sketch(self.cs, uid=self.uid,
                        geometry=self.geo, construction=self.construction)
    
    def test_get_construction_geometry(self):
        sketch = Sketch(self.cs, uid=self.uid,
                        geometry=self.geo, construction=self.construction)
        self.assertCountEqual(
            sketch.get_construction_geometry(),
            [g for g, c in zip(self.geo, self.construction) if c]
        )
    
    def test_get_non_construction_geometry(self):
        sketch = Sketch(self.cs, uid=self.uid,
                        geometry=self.geo, construction=self.construction)
        self.assertCountEqual(
            sketch.get_non_construction_geometry(),
            [g for g, c in zip(self.geo, self.construction) if not c]
        )

if __name__ == "__main__":
    unittest.main()