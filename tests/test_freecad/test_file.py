import os
import unittest

import PanCAD
from PanCAD.cad.freecad import File

TESTS = os.path.abspath(
    os.path.join(PanCAD.__file__, "..", "..", "..", "tests")
)
SAMPLE_FREECAD = os.path.join(TESTS, "sample_freecad")

class TestInit(unittest.TestCase):
    
    def setUp(self):
        self.fp = os.path.join(SAMPLE_FREECAD, "cube_1x1x1.FCStd")
    
    def test_nominal_init(self):
        file = File(self.fp, "r")

class TestProperties(unittest.TestCase):
    
    def setUp(self):
        self.fp = os.path.join(SAMPLE_FREECAD, "cube_1x1x1.FCStd")
        self.file = File(self.fp, "r")
    
    def test_filename_get(self):
        self.assertEqual(self.file.filename, "cube_1x1x1")
    
    def test_filename_set(self):
        new_name = "new_cube_1x1x1"
        self.file.mode = "w"
        self.file.filename = new_name
        self.assertEqual(self.file.filename, new_name)
    
    def test_get_creation_date(self):
        # Checking if it errors out
        dt = self.file.get_creation_date()
    
    def test_get_last_modified_date(self):
        # Checking if it errors out
        dt = self.file.get_last_modified_date()
    
    def test_get_metadata(self):
        metadata = self.file.get_metadata()
        # from pprint import pprint; pprint(metadata)

if __name__ == "__main__":
    unittest.main()