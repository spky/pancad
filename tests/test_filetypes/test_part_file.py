import unittest

from PanCAD.filetypes import PartFile
from PanCAD.filetypes.constants import SoftwareName

from PanCAD.geometry import CoordinateSystem, Sketch, Extrude, LineSegment
from PanCAD.geometry.constraints import (
    Coincident, Vertical, Horizontal,
    Distance, HorizontalDistance, VerticalDistance
)
from PanCAD.geometry.constants import ConstraintReference as CR

class TestPartFile(unittest.TestCase):
    
    def setUp(self):
        self.filename = "fake_part.FCStd"
        self.metadata = {
            "Id": "PART-0001",
            "Label": "cube_1x1x1",
            "LicenseURL": "https://creativecommons.org/publicdomain/zero/1.0/",
            "Created By": "Bob",
            "CreationDate": "2025-06-21T14:22:37Z",
            "LastModifiedBy": "Other Bob",
            "LastModifiedDate": "2025-06-22T12:51:12Z",
            "Comment": "A companion",
            "UnitSystem": "US customary (in, lb)",
            "Company": "Bob Corp",
            "Uid": "7c2a603d-b250-44ce-8938-f714395e519f",
        }
        self.metadata_map = {
             "dcterms:identifier": "Id",
             "dcterms:title": "Label",
             "dcterms:license": "LicenseURL",
             "dcterms:created": "CreationDate",
             "dcterms:contributor": "LastModifiedBy",
             "dcterms:modified": "LastModifiedDate",
             "dcterms:creator": "Created By",
             "dcterms:description": "Comment",
             "units": "UnitSystem",
        }
    
    def square_sketch(self, uid: str, cs: CoordinateSystem):
        geometry = [ # A 1x1 square
            LineSegment((0, 0), (1, 0)),
            LineSegment((1, 0), (1, 1)),
            LineSegment((1, 1), (0, 1)),
            LineSegment((0, 1), (0, 0)),
        ]
        # Constrain geometry to each other
        constraints = [
            Horizontal(geometry[0], CR.CORE),
            Vertical(geometry[1], CR.CORE),
            Horizontal(geometry[2], CR.CORE),
            Vertical(geometry[3], CR.CORE),
            Coincident(geometry[0], CR.START, geometry[3], CR.END),
            Coincident(geometry[0], CR.END, geometry[1], CR.START),
            Coincident(geometry[1], CR.END, geometry[2], CR.START),
            Coincident(geometry[2], CR.END, geometry[3], CR.START),
            VerticalDistance(geometry[0], CR.CORE, geometry[2], CR.CORE, 1),
            HorizontalDistance(geometry[1], CR.CORE, geometry[3], CR.CORE, 1),
        ]
        sketch = Sketch(cs, geometry=geometry, constraints=constraints, uid=uid)
        # Constrain bottom left corner to origin
        sketch.add_constraint(
            Coincident(geometry[0], CR.START,
                       sketch.get_sketch_coordinate_system(), CR.ORIGIN)
        )
        return sketch

class TestPartFileInitialization(TestPartFile):
    def test_init(self):
        # Check if it errors out
        f = PartFile(filename=self.filename,
                     original_software=SoftwareName.FREECAD,
                     metadata=self.metadata,
                     metadata_map=self.metadata_map)

class TestAddGeometry(TestPartFile):
    def setUp(self):
        super().setUp()
        self.file = PartFile(filename=self.filename,
                             original_software=SoftwareName.FREECAD,
                             metadata=self.metadata,
                             metadata_map=self.metadata_map)
        self.sketch = self.square_sketch("TestSquareSketch",
                                         self.file.get_coordinate_system())
    
    def test_add_sketch(self):
        self.file.add_feature(self.sketch)
        self.assertEqual(self.file.get_features()[0].uid, self.sketch.uid)
    
    def test_add_extrude(self):
        self.file.add_feature(self.sketch)
        test_extrude = Extrude.from_length(self.sketch, 1, "test_extrude")
        self.file.add_feature(test_extrude)
    
    def test_add_sketch_missing_dependency(self):
        sketch = self.square_sketch("TestSquareSketch",
                                    CoordinateSystem((0, 0, 0)))
        with self.assertRaises(LookupError):
            self.file.add_feature(sketch)
    
    def test_add_extrude_missing_dependency(self):
        test_extrude = Extrude.from_length(self.sketch, 1, "test_extrude")
        with self.assertRaises(LookupError):
            self.file.add_feature(test_extrude)


if __name__ == "__main__":
    unittest.main()