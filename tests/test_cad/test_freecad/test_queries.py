from unittest import TestCase
from pathlib import Path
from pprint import pp

from tests import sample_freecad

from pancad.cad.freecad import App, queries, constants
from pancad.cad.freecad.constants import ListName

class Cube1x1x1(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.filepath = sample_dir / "cube_1x1x1.FCStd"
        self.document = App.open(str(self.filepath))
        sketch_name = "cube_profile"
        for object_ in self.document.Objects:
            if object_.Label == sketch_name:
                self.sketch = object_
                self.sketch_id = object_.ID
                break
    
    def test_get_constraints_on_left_line(self):
        geo_id = (self.sketch_id, ListName.GEOMETRY, 0)
        test = queries.get_constraints_on(self.sketch, geo_id)
        print("\nConstraint IDs")
        pp(test)
        self.assertEqual([t[2] for t in test], [0, 3, 4, 10])
    
    def test_get_constraints_on_left_line_end(self):
        geo_id = (self.sketch_id, ListName.GEOMETRY, 0)
        test = queries.get_constraints_on(self.sketch, geo_id,
                                          constants.EdgeSubPart.END)
        print("\nConstraint IDs")
        pp(test)
        self.assertEqual([t[2] for t in test], [0, 10])
    
    def test_get_constraints_on_top_line(self):
        geo_id = (self.sketch_id, ListName.GEOMETRY, 3)
        test = queries.get_constraints_on(self.sketch, geo_id)
        print("\nConstraint IDs")
        pp(test)
        self.assertEqual([t[2] for t in test], [2, 3, 7, 8])
    
    def test_get_constraints_on_x_axis(self):
        geo_id = (self.sketch_id, ListName.EXTERNALS, 0)
        test = queries.get_constraints_on(self.sketch, geo_id)
        print("\nConstraint IDs")
        pp(test)
        self.assertEqual([t[2] for t in test], [10])
    
    def test_get_constraints_on_y_axis(self):
        geo_id = (self.sketch_id, ListName.EXTERNALS, 1)
        test = queries.get_constraints_on(self.sketch, geo_id)
        print("\nConstraint IDs")
        pp(test)
        self.assertEqual([t[2] for t in test], [])
    
    def test_get_constraint_pairs_0(self):
        constraint_id = (self.sketch_id, ListName.CONSTRAINTS, 0)
        test = queries.get_constraint_pairs(self.sketch, constraint_id)
        print("\nPairs:")
        pp(test)
        prefix = (self.sketch_id, ListName.GEOMETRY)
        self.assertEqual(test, ((prefix + (0,), 2), (prefix + (1,), 1)))

class ConstraintMappingSpecialCases(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.filepath = sample_dir / "constraint_mapping_special_cases.FCStd"
        self.document = App.open(str(self.filepath))
    
    def get_sketch(self, name: str):
        for object_ in self.document.Objects:
            if object_.Label == name:
                return object_
    
    def test_get_internal_constraints_ellipse(self):
        sketch = self.get_sketch("internal_alignment_ellipse")
        geo_id = (sketch.ID, ListName.GEOMETRY, 0)
        constraints = queries.get_internal_constraints(sketch, geo_id)
        print("\nInternal Constraints:")
        pp(constraints)
    
    def test_get_internal_geometry_ellipse(self):
        sketch = self.get_sketch("internal_alignment_ellipse")
        geo_id = (sketch.ID, ListName.GEOMETRY, 0)
        geometry = queries.get_internal_geometry(sketch, geo_id)
        print("\nInternal Geometry:")
        pp(geometry)
    
    def test_is_internal_geometry_ellipse(self):
        sketch = self.get_sketch("internal_alignment_ellipse")
        ellipse_id = (sketch.ID, ListName.GEOMETRY, 0)
        major_axis_id = (sketch.ID, ListName.GEOMETRY, 1)
        self.assertFalse(queries.is_internal_geometry(sketch, ellipse_id))
        self.assertTrue(queries.is_internal_geometry(sketch, major_axis_id))
    
    def test_get_internal_constraints_no_special(self):
        sketch = self.get_sketch("no_special")
        for i in range(0, 4):
            geo_id = (sketch.ID, ListName.GEOMETRY, i)
            self.assertEqual(queries.get_internal_geometry(sketch, geo_id), {})
    
    def test_is_internal_geometry_control_no_special(self):
        sketch = self.get_sketch("no_special")
        for i in range(0, 4):
            geo_id = (sketch.ID, ListName.GEOMETRY, i)
            self.assertFalse(queries.is_internal_geometry(sketch, geo_id))