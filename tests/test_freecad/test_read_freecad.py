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
    
    def test_read_cube(self):
        file = FreeCADFile(self.filepath)
        part_file = file.to_pancad()
    
    def test_read_cube_direct(self):
        part_file = PartFile.from_freecad(self.filepath)
    
    def test_set_path_with_fcstd(self):
        file = FreeCADFile(self.filepath)
        self.assertEqual(file.filepath, self.filepath)
    
    def test_set_path_without_fcstd(self):
        file = FreeCADFile(self.filepath)
        with self.assertRaises(ValueError):
            file.filepath = Path(self.filepath).with_suffix(".pdf")

if __name__ == "__main__":
    unittest.main()