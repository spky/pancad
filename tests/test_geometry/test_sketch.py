import unittest

from PanCAD.geometry import (
    Sketch, CoordinateSystem, Plane, Line, LineSegment, Point, Coincident
)
from PanCAD.geometry.constants import (SketchConstraint,
                                       ConstraintReference as CR)

class TestSketchInit(unittest.TestCase):
    
    def setUp(self):
        self.cs = CoordinateSystem((0, 0, 0))
    
    def test_plane_reference(self):
        sketch = Sketch(self.cs, CR.XY)
        self.assertEqual(sketch.plane_reference, CR.XY)
    
    def test_plane_reference_exception(self):
        with self.assertRaises(ValueError):
            sketch = Sketch(self.cs, CR.CORE)
    
    def test_get_plane(self):
        sketch = Sketch(self.cs, CR.YZ)
        plane = sketch.get_plane()
        self.assertEqual(plane, Plane((0, 0, 0), (1, 0, 0)))

class TestDunder(unittest.TestCase):
    def setUp(self):
        cs = CoordinateSystem((0, 0, 0))
        geom = [Point(1,1), LineSegment((-1,-1),(-1,1))]
        cons = [Coincident(geom[0], CR.CORE, geom[1], CR.CORE)]
        uid = "TestSketch"
        self.sketch = Sketch(cs, geometry=geom, constraints=cons, uid=uid)
    
    def test_repr(self):
        # Checks whether repr errors out
        sketch_repr = repr(self.sketch)
    
    def test_str(self):
        # Checks whether str errors out
        sketch_str = str(self.sketch)

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
        ]
    
    def test_constraint_validation_success(self):
        constraints = [
            Coincident(self.geo[0], CR.CORE, self.geo[1], CR.CORE)
        ]
        sketch = Sketch(self.cs, geometry=self.geo, constraints=constraints)
    
    def test_constraint_validation_failure(self):
        constraints = [
            Coincident(self.geo[0], CR.CORE, Point(2, 2), CR.CORE)
        ]
        with self.assertRaises(ValueError):
            sketch = Sketch(self.cs, geometry=self.geo, constraints=constraints)
    
    def test_add_constraint_by_uid(self):
        sketch = Sketch(self.cs, geometry=self.geo)
        expected_constraint = Coincident(self.geo[0], CR.CORE,
                                         self.geo[1], CR.CORE)
        sketch.add_constraint_by_uid(SketchConstraint.COINCIDENT,
                                     self.geo[0].uid, CR.CORE,
                                     self.geo[1].uid, CR.CORE)
        self.assertEqual(sketch.constraints[0], expected_constraint)
    
    def test_add_constraint_by_index(self):
        sketch = Sketch(self.cs, geometry=self.geo)
        expected_constraint = Coincident(self.geo[0], CR.CORE,
                                         self.geo[1], CR.CORE)
        sketch.add_constraint_by_index(SketchConstraint.COINCIDENT,
                                       0, CR.CORE, 1, CR.CORE)
        self.assertEqual(sketch.constraints[0], expected_constraint)
    
    def test_add_constraint_to_sketch_cs(self):
        sketch = Sketch(self.cs, geometry=self.geo)
        expected_constraint = Coincident(
            sketch.get_sketch_coordinate_system(), CR.ORIGIN,
            self.geo[0], CR.CORE
        )
        sketch.add_constraint_by_uid(SketchConstraint.COINCIDENT,
                                     CR.COORDINATE_SYSTEM, CR.ORIGIN,
                                     self.geo[0].uid, CR.CORE)
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