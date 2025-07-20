import unittest

from PanCAD.geometry import (
    Sketch, CoordinateSystem, Plane, Line, LineSegment, Point, Circle
)
from PanCAD.geometry.constraints import (
    Coincident, Vertical, Horizontal, Equal, Angle,
    Distance, HorizontalDistance, VerticalDistance, Diameter
)
from PanCAD.geometry.constants import SketchConstraint, ConstraintReference

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
        cons = [Coincident(geom[0], ConstraintReference.CORE, geom[1], ConstraintReference.CORE)]
        uid = "TestSketch"
        self.sketch = Sketch(cs, geometry=geom, constraints=cons, uid=uid)
    
    def test_repr(self):
        # Checks whether repr errors out
        sketch_repr = repr(self.sketch)

class TestSummary(unittest.TestCase):
    
    def make_square_sketch(self) -> Sketch:
        side_length = 2
        unit = "in"
        geometry = [
            LineSegment((0, 0), (side_length, 0)),
            LineSegment((side_length, 0), (side_length, side_length)),
            LineSegment((side_length, side_length), (0, side_length)),
            LineSegment((0, side_length), (0, 0)),
            Circle((1, 1), 1),
            Line.from_two_points((0, 1), (1, 0)),
            Point(.5, .5),
        ]
        sketch = Sketch(geometry=geometry, uid="test_sketch")
        constraints = [
            Coincident(geometry[0], ConstraintReference.START,
                       geometry[3], ConstraintReference.END),
            Coincident(geometry[0], ConstraintReference.END,
                       geometry[1], ConstraintReference.START),
            Coincident(geometry[1], ConstraintReference.END,
                       geometry[2], ConstraintReference.START),
            Coincident(geometry[2], ConstraintReference.END,
                       geometry[3], ConstraintReference.START),
            Horizontal(geometry[0], ConstraintReference.CORE),
            Vertical(geometry[1], ConstraintReference.CORE),
            Horizontal(geometry[2], ConstraintReference.CORE),
            Vertical(geometry[3], ConstraintReference.CORE),
            Equal(geometry[0], ConstraintReference.CORE,
                  geometry[1], ConstraintReference.CORE),
            Distance(geometry[0], ConstraintReference.START,
                     geometry[0], ConstraintReference.END,
                     value=side_length, unit=unit),
            Coincident(geometry[0], ConstraintReference.START,
                       sketch.get_sketch_coordinate_system(),
                       ConstraintReference.ORIGIN),
            Diameter(geometry[4], ConstraintReference.CORE, 1, unit=unit),
            Angle(geometry[0], ConstraintReference.CORE,
                  geometry[1], ConstraintReference.CORE,
                  value=90, quadrant=2)
        ]
        sketch.constraints = constraints
        return sketch
    
    def test_square_sketch_summary(self):
        sketch = self.make_square_sketch()
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

class TestUID(unittest.TestCase):
    
    def setUp(self):
        self.cs = CoordinateSystem((0, 0, 0))
        self.sketch_uid = "TestSketch"
        self.special_uid = "Special"
        self.test_geo = [
            Point(1, 1),
            Line.from_two_points((0, 0), (0, 1)),
            Line.from_two_points((0, 0), (0, 1)),
            LineSegment((-1, -1), (-1, 1)),
            LineSegment((-1, -1), (-1, 1), uid=self.special_uid),
            LineSegment((-1, -1), (-1, 1), uid="2"),
            LineSegment((-1, -1), (-1, 1), uid=""),
        ]
    
    def test_uid_sync(self):
        expected = [Sketch.UID_SEPARATOR.join([self.sketch_uid, str(i)])
                    for i, _ in enumerate(self.test_geo)]
        expected[4] = self.special_uid
        sketch = Sketch(self.cs, geometry=self.test_geo, uid=self.sketch_uid)
        uids = [g.uid for g in sketch.geometry]
        self.assertCountEqual(uids, expected)
    
    def test_uid_update_sync(self):
        sketch = Sketch(self.cs, geometry=self.test_geo, uid=self.sketch_uid)
        uid = "ModifiedSketch"
        sketch.uid = uid
        uids = [g.uid for g in sketch.geometry]
        expected = [Sketch.UID_SEPARATOR.join([uid, str(i)])
                    for i, _ in enumerate(self.test_geo)]
        expected[4] = self.special_uid
        self.assertCountEqual(uids, expected)

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
        constraints = [
            Coincident(self.geo[0], ConstraintReference.CORE, self.geo[1], ConstraintReference.CORE)
        ]
        sketch = Sketch(self.cs, geometry=self.geo, constraints=constraints)
    
    def test_constraint_validation_failure(self):
        constraints = [
            Coincident(self.geo[0], ConstraintReference.CORE, Point(2, 2), ConstraintReference.CORE)
        ]
        with self.assertRaises(ValueError):
            sketch = Sketch(self.cs, geometry=self.geo, constraints=constraints)
    
    def test_add_constraint_by_uid(self):
        sketch = Sketch(self.cs, geometry=self.geo)
        expected_constraint = Coincident(self.geo[0], ConstraintReference.CORE,
                                         self.geo[1], ConstraintReference.CORE)
        sketch.add_constraint_by_uid(SketchConstraint.COINCIDENT,
                                     self.geo[0].uid, ConstraintReference.CORE,
                                     self.geo[1].uid, ConstraintReference.CORE)
        self.assertEqual(sketch.constraints[0], expected_constraint)
    
    def test_add_constraint_by_uid_vertical(self):
        sketch = Sketch(self.cs, geometry=self.geo)
        expected_constraint = Vertical(self.geo[2], ConstraintReference.CORE,
                                       uid=self.geo[2].uid)
        sketch.add_constraint_by_uid(SketchConstraint.VERTICAL,
                                     self.geo[2].uid, ConstraintReference.CORE)
        self.assertEqual(sketch.constraints[0], expected_constraint)
    
    def test_add_constraint_by_uid_horizontal(self):
        sketch = Sketch(self.cs, geometry=self.geo)
        expected_constraint = Horizontal(self.geo[2], ConstraintReference.CORE,
                                         uid=self.geo[2].uid)
        sketch.add_constraint_by_uid(SketchConstraint.HORIZONTAL,
                                     self.geo[2].uid, ConstraintReference.CORE)
        self.assertEqual(sketch.constraints[0], expected_constraint)
    
    def test_add_constraint_by_uid_distance(self):
        sketch = Sketch(self.cs, geometry=self.geo)
        distance = 10
        expected_constraint = Distance(self.geo[0], ConstraintReference.CORE,
                                       self.geo[1], ConstraintReference.CORE,
                                       uid="test_pt_distance",
                                       value=distance)
        sketch.add_constraint_by_uid(SketchConstraint.DISTANCE,
                                     self.geo[0].uid, ConstraintReference.CORE,
                                     self.geo[1].uid, ConstraintReference.CORE,
                                     value=distance)
        self.assertEqual(sketch.constraints[0], expected_constraint)
    
    def test_add_constraint_by_uid_horizontal_distance(self):
        sketch = Sketch(self.cs, geometry=self.geo)
        distance = 10
        expected_constraint = HorizontalDistance(self.geo[0], ConstraintReference.CORE,
                                                 self.geo[1], ConstraintReference.CORE,
                                                 uid="test_pt_distance",
                                                 value=distance)
        sketch.add_constraint_by_uid(SketchConstraint.DISTANCE_HORIZONTAL,
                                     self.geo[0].uid, ConstraintReference.CORE,
                                     self.geo[1].uid, ConstraintReference.CORE,
                                     value=distance)
        self.assertEqual(sketch.constraints[0], expected_constraint)
    
    def test_add_constraint_by_index(self):
        sketch = Sketch(self.cs, geometry=self.geo)
        expected_constraint = Coincident(self.geo[0], ConstraintReference.CORE,
                                         self.geo[1], ConstraintReference.CORE)
        sketch.add_constraint_by_index(SketchConstraint.COINCIDENT,
                                       0, ConstraintReference.CORE, 1, ConstraintReference.CORE)
        self.assertEqual(sketch.constraints[0], expected_constraint)
    
    def test_add_constraint_to_sketch_cs(self):
        sketch = Sketch(self.cs, geometry=self.geo)
        expected_constraint = Coincident(
            sketch.get_sketch_coordinate_system(), ConstraintReference.ORIGIN,
            self.geo[0], ConstraintReference.CORE
        )
        sketch.add_constraint_by_uid(SketchConstraint.COINCIDENT,
                                     ConstraintReference.COORDINATE_SYSTEM, ConstraintReference.ORIGIN,
                                     self.geo[0].uid, ConstraintReference.CORE)
        self.assertEqual(sketch.constraints[0], expected_constraint)

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
        self.assertCountEqual(sketch.get_geometry_status(),
                              zip(self.geo, self.construction))
    
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