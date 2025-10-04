import os
from pathlib import Path
import unittest

import PanCAD
from PanCAD.cad.freecad import FreeCADFile
from PanCAD.filetypes import PartFile

class TestReadSample(unittest.TestCase):
    
    def setUp(self):
        self.tests = os.path.abspath(
            os.path.join(PanCAD.__file__, "..", "..", "..", "tests")
        )
        self.sample_freecad = os.path.join(self.tests, "sample_freecad")

class TestReadFile(TestReadSample):
    
    def setUp(self):
        super().setUp()
        self.filepath = os.path.join(self.sample_freecad, "cube_1x1x1.FCStd")
        self.filename = "cube_1x1x1"
        self.sketch_label = "cube_profile"
        
        self.feature_count = 2
        # Sketch and Pad
        
        self.sketch_geometry_count = 4
        # 4 Lines
        
        self.sketch_constraint_count = 11
        # 5 Coincident, 2 Vertical, 2 Horizontal,
        # 1 HorizontalDistance, 1 VerticalDistance
    
    def test_read_cube(self):
        file = FreeCADFile(self.filepath)
        part_file = file.to_pancad()
    
    @unittest.skip
    def test_read_cube_direct(self):
        file = PartFile.from_freecad(self.filepath)
        with self.subTest("Filename mismatch"):
            self.assertEqual(file.filename, self.filename)
        
        with self.subTest("Feature Count !=", geometry=file.get_features()):
            self.assertEqual(len(file.get_features()), self.feature_count)
        
        sketch = file.get_feature(self.sketch_label)
        
        with self.subTest("Sketch Geometry Count !=", geometry=sketch.geometry):
            self.assertEqual(len(sketch.geometry), self.sketch_geometry_count)
        
        with self.subTest("Sketch Constraint Count !=",
                          geometry=sketch.constraints):
            self.assertEqual(len(sketch.constraints),
                             self.sketch_constraint_count)
    
    @unittest.skip
    def test_set_path_with_fcstd(self):
        file = FreeCADFile(self.filepath)
        self.assertEqual(file.filepath, self.filepath)
        self.assertEqual(file.stem, Path(self.filepath).stem)
    
    @unittest.skip
    def test_set_path_without_fcstd(self):
        file = FreeCADFile(self.filepath)
        with self.assertRaises(ValueError):
            file.filepath = Path(self.filepath).with_suffix(".pdf")
    
    @unittest.skip
    def test_set_stem_with_fcstd(self):
        file = FreeCADFile(self.filepath)
        file.stem = "fake.FCStd"
        self.assertEqual(file.stem, "fake")
        self.assertEqual(file.filepath,
                         str(Path(self.filepath).with_name("fake.FCStd")))
    
    @unittest.skip
    def test_set_stem_without_fcstd(self):
        file = FreeCADFile(self.filepath)
        file.stem = "fake"
        self.assertEqual(file.stem, "fake")
        self.assertEqual(file.filepath,
                         str(Path(self.filepath).with_name("fake.FCStd")))
    
    @unittest.skip
    def test_set_stem_without_fcstd(self):
        file = FreeCADFile(self.filepath)
        with self.assertRaises(ValueError):
            file.stem = "fake.pdf"

if __name__ == "__main__":
    unittest.main()