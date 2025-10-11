import unittest
from inspect import stack

from PanCAD import PartFile
from PanCAD.filetypes import PartFile
from PanCAD.geometry import Extrude

from tests.sample_pancad_objects import sample_sketches

class TestPartFileInitialization(unittest.TestCase):
    
    def test_init(self):
        # Check if it errors out
        f = PartFile()
    
    def test_filename_parsing(self):
        tests = [r"C:\Users\Username\Documents\trunk\fake_part.FCStd",
                 r"fake_part",
                 r"fake_part.FCStd",]
        expected = "fake_part"
        for filename in tests:
            with self.subTest(string_in=filename, expected=expected):
                file = PartFile(filename)
                self.assertEqual(file.filename, expected)

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

class TestAddGeometry(TestPartFile):
    def setUp(self):
        self.file = PartFile()
        self.sketch = sample_sketches.square()
        self.height = 3
    
    def test_add_sketch(self):
        self.file.add_feature(self.sketch)
        self.assertTrue(self.sketch in self.file)
    
    def test_add_extrude(self):
        self.file.add_feature(self.sketch)
        test_extrude = Extrude.from_length(self.sketch, self.height,
                                           "test_extrude")
        self.file.add_feature(test_extrude)
        self.assertTrue(test_extrude in self.file)
    
    def test_add_extrude_missing_dependency(self):
        test_extrude = Extrude.from_length(self.sketch, self.height,
                                           "test_extrude")
        with self.assertRaises(LookupError):
            self.file.add_feature(test_extrude)

if __name__ == "__main__":
    unittest.main()