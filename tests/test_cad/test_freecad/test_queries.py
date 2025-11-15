from unittest import TestCase
from pathlib import Path
from pprint import pp

from tests import sample_freecad

from pancad.cad.freecad import App, queries, constants

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
        geo_id = (self.sketch_id, constants.ListName.GEOMETRY, 0)
        test = queries.get_constraints_on(self.sketch, geo_id)
        print("\nConstraint IDs")
        pp(test)
        self.assertEqual([t[2] for t in test], [0, 3, 4, 10])
    
    def test_get_constraints_on_left_line_end(self):
        geo_id = (self.sketch_id, constants.ListName.GEOMETRY, 0)
        test = queries.get_constraints_on(self.sketch, geo_id,
                                          constants.EdgeSubPart.END)
        print("\nConstraint IDs")
        pp(test)
        self.assertEqual([t[2] for t in test], [0, 10])
    
    def test_get_constraints_on_top_line(self):
        geo_id = (self.sketch_id, constants.ListName.GEOMETRY, 3)
        test = queries.get_constraints_on(self.sketch, geo_id)
        print("\nConstraint IDs")
        pp(test)
        self.assertEqual([t[2] for t in test], [2, 3, 7, 8])
    
    def test_get_constraints_on_x_axis(self):
        geo_id = (self.sketch_id, constants.ListName.EXTERNALS, 0)
        test = queries.get_constraints_on(self.sketch, geo_id)
        print("\nConstraint IDs")
        pp(test)
        self.assertEqual([t[2] for t in test], [10])
    
    def test_get_constraints_on_y_axis(self):
        geo_id = (self.sketch_id, constants.ListName.EXTERNALS, 1)
        test = queries.get_constraints_on(self.sketch, geo_id)
        print("\nConstraint IDs")
        pp(test)
        self.assertEqual([t[2] for t in test], [])
