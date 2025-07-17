import os
import unittest
from functools import partial
from inspect import stack

import PanCAD
from PanCAD.filetypes import PartFile
from PanCAD.filetypes.constants import SoftwareName

from PanCAD.geometry import (
    CoordinateSystem, Sketch, Extrude, LineSegment, Circle
)
from PanCAD.geometry.constraints import (
    Coincident, Vertical, Horizontal,
    Distance, HorizontalDistance, VerticalDistance,
    Diameter, Radius, Equal, Perpendicular, Parallel
)
from PanCAD.geometry.constants import ConstraintReference

from PanCAD.cad.freecad import to_freecad



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
    
    def square_sketch(self, uid: str,
                      plane_ref: ConstraintReference=ConstraintReference.XY):
        length = 1
        width = 2
        unit = "mm"
        geometry = [ # A 1x1 square
            LineSegment((0, 0), (width, 0)),
            LineSegment((width, 0), (width, length)),
            LineSegment((width, length), (0, length)),
            LineSegment((0, length), (0, 0)),
        ]
        # Constrain geometry to each other
        constraints = [
            Horizontal(geometry[0], ConstraintReference.CORE),
            Vertical(geometry[1], ConstraintReference.CORE),
            Horizontal(geometry[2], ConstraintReference.CORE),
            Vertical(geometry[3], ConstraintReference.CORE),
            Coincident(geometry[0], ConstraintReference.START,
                       geometry[3], ConstraintReference.END),
            Coincident(geometry[0], ConstraintReference.END,
                       geometry[1], ConstraintReference.START),
            Coincident(geometry[1], ConstraintReference.END,
                       geometry[2], ConstraintReference.START),
            Coincident(geometry[2], ConstraintReference.END,
                       geometry[3], ConstraintReference.START),
            Distance(geometry[0], ConstraintReference.CORE,
                     geometry[2], ConstraintReference.CORE,
                     length, unit="mm"),
            Distance(geometry[1], ConstraintReference.CORE,
                     geometry[3], ConstraintReference.CORE,
                     width, unit="mm"),
        ]
        sketch = Sketch(plane_reference=plane_ref,
                        geometry=geometry,
                        constraints=constraints,
                        uid=uid)
        # Constrain bottom left corner to origin
        sketch.add_constraint(
            Coincident(geometry[0], ConstraintReference.START,
                       sketch.get_sketch_coordinate_system(),
                       ConstraintReference.ORIGIN)
        )
        return sketch
    
    def circle_sketch(self, uid: str,
                      plane_ref: ConstraintReference=ConstraintReference.XY):
        radius = 5
        unit = "mm"
        geometry = [
            Circle((0, 0), radius),
        ]
        constraints = [
            Diameter(geometry[0], ConstraintReference.CORE, radius, unit=unit),
        ]
        sketch = Sketch(plane_reference=plane_ref,
                        geometry=geometry,
                        constraints=constraints,
                        uid=uid)
        sketch.add_constraint(
            Coincident(geometry[0], ConstraintReference.CENTER,
                       sketch.get_sketch_coordinate_system(),
                       ConstraintReference.ORIGIN)
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
        self.sketch = self.square_sketch("TestSquareSketch")
        self.height = 3
    
    def test_add_sketch(self):
        self.file.add_feature(self.sketch)
        self.assertEqual(self.file.get_features()[0].uid, self.sketch.uid)
    
    def test_add_extrude(self):
        self.file.add_feature(self.sketch)
        test_extrude = Extrude.from_length(self.sketch, 1, "test_extrude")
        self.file.add_feature(test_extrude)
    
    def test_add_extrude_missing_dependency(self):
        test_extrude = Extrude.from_length(self.sketch, self.height,
                                           "test_extrude")
        with self.assertRaises(LookupError):
            self.file.add_feature(test_extrude)

class TestWritePartFileToFreeCADFeatures(TestPartFile):
    def setUp(self):
        super().setUp()
        self.file_gen = partial(PartFile,
                                original_software=SoftwareName.FREECAD,
                                metadata=self.metadata,
                                metadata_map=self.metadata_map)
        self.sketch_uid = "TestSketch"
        self.extrude_uid = "TestExtrude"
        self.extrude_length = 1
        tests_folder = os.path.abspath(
            os.path.join(PanCAD.__file__, "..", "..", "..", "tests")
        )
        self.dump_folder = os.path.join(tests_folder, "test_output_dump")
    
    def tearDown(self):
        os.remove(self.filepath)
    
    def test_to_freecad_create_body(self):
        # Name the file after the function its in
        filename = stack()[0].function + ".FCStd"
        self.file = self.file_gen(filename)
        self.filepath = os.path.join(self.dump_folder, filename)
        to_freecad(self.filepath, self.file)
    
    def test_to_freecad_create_cube(self):
        filename = stack()[0].function + ".FCStd"
        self.file = self.file_gen(filename)
        sketch = self.square_sketch(self.sketch_uid, ConstraintReference.XZ)
        extrude = Extrude.from_length(sketch,
                                      self.extrude_length, self.extrude_uid)
        self.file.add_feature(sketch)
        self.file.add_feature(extrude)
        self.filepath = os.path.join(self.dump_folder,
                                     stack()[0].function + ".FCStd")
        to_freecad(self.filepath, self.file)
    
    def test_to_freecad_create_cylinder(self):
        filename = stack()[0].function + ".FCStd"
        self.file = self.file_gen(filename)
        sketch = self.circle_sketch(self.sketch_uid, ConstraintReference.XZ)
        extrude = Extrude.from_length(sketch,
                                      self.extrude_length, self.extrude_uid)
        self.file.add_feature(sketch)
        self.file.add_feature(extrude)
        self.filepath = os.path.join(self.dump_folder,
                                     stack()[0].function + ".FCStd")
        to_freecad(self.filepath, self.file)

class TestPartFileSketches(unittest.TestCase):
    
    def setUp(self):
        self.dump_dir = os.path.join(os.path.dirname(__file__), "dump")
    
    def init_filename(self, function_name: str):
        self.filename = function_name + ".FCStd"
        self.filepath = os.path.join(self.dump_dir, self.filename)
        self.file = PartFile(self.filename)
    
    def finish_to_freecad(self):
        self.sketch.constraints = self.constraints
        self.file.add_feature(self.sketch)
        to_freecad(self.filepath, self.file)

class TestPartFileSquareSketchVariations(TestPartFileSketches):
    
    def tearDown(self):
        os.remove(self.filepath)
    
    def setUp(self):
        super().setUp()
        self.side = 2
        self.unit = "in"
        self.geometry = [
            LineSegment((0, 0), (self.side, 0)),
            LineSegment((self.side, 0), (self.side, self.side)),
            LineSegment((self.side, self.side), (0, self.side)),
            LineSegment((0, self.side), (0, 0)),
        ]
        self.constraints = [ # Constraints that are always there
            Coincident(self.geometry[0], ConstraintReference.START,
                       self.geometry[3], ConstraintReference.END),
            Coincident(self.geometry[0], ConstraintReference.END,
                       self.geometry[1], ConstraintReference.START),
            Coincident(self.geometry[1], ConstraintReference.END,
                       self.geometry[2], ConstraintReference.START),
            Coincident(self.geometry[2], ConstraintReference.END,
                       self.geometry[3], ConstraintReference.START),
        ]
        self.sketch = Sketch(geometry=self.geometry, uid="test_sketch")
    
    def test_two_equal_square_with_horizontal_vertical(self):
        self.init_filename(stack()[0].function + ".FCStd")
        self.constraints.extend(
            [
                Horizontal(self.geometry[0], ConstraintReference.CORE),
                Vertical(self.geometry[1], ConstraintReference.CORE),
                Horizontal(self.geometry[2], ConstraintReference.CORE),
                Vertical(self.geometry[3], ConstraintReference.CORE),
                Equal(self.geometry[0], ConstraintReference.CORE,
                      self.geometry[1], ConstraintReference.CORE),
                Distance(self.geometry[0], ConstraintReference.START,
                         self.geometry[0], ConstraintReference.END,
                         value=self.side, unit=self.unit),
                Coincident(self.geometry[0], ConstraintReference.START,
                           self.sketch.get_sketch_coordinate_system(),
                           ConstraintReference.ORIGIN)
            ]
        )
        self.finish_to_freecad()
    
    def test_all_equal_square_with_horizontal_vertical(self):
        self.init_filename(stack()[0].function)
        self.constraints.extend(
            [
                Horizontal(self.geometry[0], ConstraintReference.CORE),
                Vertical(self.geometry[3], ConstraintReference.CORE),
                Equal(self.geometry[0], ConstraintReference.CORE,
                      self.geometry[1], ConstraintReference.CORE),
                Equal(self.geometry[0], ConstraintReference.CORE,
                      self.geometry[2], ConstraintReference.CORE),
                Equal(self.geometry[0], ConstraintReference.CORE,
                      self.geometry[3], ConstraintReference.CORE),
                Distance(self.geometry[0], ConstraintReference.START,
                         self.geometry[0], ConstraintReference.END,
                         value=self.side, unit=self.unit),
                Coincident(self.geometry[0], ConstraintReference.START,
                           self.sketch.get_sketch_coordinate_system(),
                           ConstraintReference.ORIGIN)
            ]
        )
        self.finish_to_freecad()
    
    def test_all_equal_square_with_perpendicular(self):
        self.init_filename(stack()[0].function)
        self.constraints.extend(
            [
                Horizontal(self.geometry[0], ConstraintReference.CORE),
                Equal(self.geometry[0], ConstraintReference.CORE,
                      self.geometry[1], ConstraintReference.CORE),
                Equal(self.geometry[0], ConstraintReference.CORE,
                      self.geometry[2], ConstraintReference.CORE),
                Equal(self.geometry[0], ConstraintReference.CORE,
                      self.geometry[3], ConstraintReference.CORE),
                Perpendicular(self.geometry[0], ConstraintReference.CORE,
                              self.geometry[3], ConstraintReference.CORE),
                Distance(self.geometry[0], ConstraintReference.START,
                         self.geometry[0], ConstraintReference.END,
                         value=self.side, unit=self.unit),
                Coincident(self.geometry[0], ConstraintReference.START,
                           self.sketch.get_sketch_coordinate_system(),
                           ConstraintReference.ORIGIN)
            ]
        )
        self.finish_to_freecad()
    
    def test_all_equal_square_with_perpendicular_and_parallel(self):
        self.init_filename(stack()[0].function)
        self.constraints.extend(
            [
                Horizontal(self.geometry[0], ConstraintReference.CORE),
                
                Equal(self.geometry[0], ConstraintReference.CORE,
                      self.geometry[3], ConstraintReference.CORE),
                Perpendicular(self.geometry[0], ConstraintReference.CORE,
                              self.geometry[3], ConstraintReference.CORE),
                Parallel(self.geometry[1], ConstraintReference.CORE,
                         self.geometry[3], ConstraintReference.CORE),
                Parallel(self.geometry[0], ConstraintReference.CORE,
                         self.geometry[2], ConstraintReference.CORE),
                Distance(self.geometry[0], ConstraintReference.START,
                         self.geometry[0], ConstraintReference.END,
                         value=self.side, unit=self.unit),
                Coincident(self.geometry[0], ConstraintReference.START,
                           self.sketch.get_sketch_coordinate_system(),
                           ConstraintReference.ORIGIN)
            ]
        )
        self.finish_to_freecad()


if __name__ == "__main__":
    unittest.main()