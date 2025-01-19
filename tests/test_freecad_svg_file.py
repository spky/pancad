import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


sys.path.append('src')

import freecad_svg_file as fcsf

class TestFreeCADSVGFile(unittest.TestCase):
    
    def setUp(self):
        self.FOLDER = 'tests/sample_freecad/'
        self.FILENAME = 'test_sketch_readers.FCStd'
        self.path = self.FOLDER + self.FILENAME
        self.out_folder = "tests/test_output_dump"
    
    def test_init(self):
        obj = fcsf.FreeCADSVGFile(self.path)
        obj.set_viewbox("100mm", "100mm")
        test = [obj.freecad_file_name, obj.name]
        self.assertCountEqual(test, ['test_sketch_readers.FCStd', 'test_sketch_readers.svg'])
    
    def test_add_sketch_by_label(self):
        obj = fcsf.FreeCADSVGFile(self.path, "test_add_sketch_by_label")
        obj.add_sketch_by_label("xz_rounded_rectangle_with_circle")
        obj.auto_size_view(3)
        obj.write(self.out_folder)

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()