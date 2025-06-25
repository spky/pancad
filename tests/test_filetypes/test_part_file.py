import unittest

from PanCAD.filetypes import PartFile
from PanCAD.filetypes.constants import SoftwareName

class TestPartFileInit(unittest.TestCase):
    
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
    
    def test_init(self):
        f = PartFile(filename=self.filename,
                     original_software=SoftwareName.FREECAD,
                     metadata=self.metadata,
                     metadata_map=self.metadata_map)
        from pprint import pprint
        # pprint(f._metadata)
        # pprint(f._metadata_map)
        pprint(f.metadata_to_dict())

if __name__ == "__main__":
    unittest.main()