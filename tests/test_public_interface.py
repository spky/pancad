import sys
import unittest
import os

from pathlib import Path

sys.path.append('src')

import PanCAD

class TestSVGInterface(unittest.TestCase):
    
    def setUp(self):
        TESTS = "tests"
        SAMPLE_SVGS = os.path.join(TESTS, "sample_svgs")
        SAMPLE_FC = os.path.join(TESTS, "sample_freecad")
        self.OUT_DIR = os.path.join(TESTS,
                                    "test_output_dump", "public_interface")
        
        # Test *.svg Files
        self.SVG_0 = os.path.join(SAMPLE_SVGS,
                                  "rounded_rect_with_center_circle.svg")
        
        # Test *.FCStd Files
        self.FC_0 = os.path.join(SAMPLE_FC,
                                 "rounded_rect_with_center_circle.FCStd")
    
    def test_read_write_svg(self):
        """Read an svg file and then write it to a folder."""
        svg_file = PanCAD.read_svg(self.SVG_0)
        out_path = os.path.join(self.OUT_DIR, "test_read_write_svg.svg")
        svg_file.write(out_path)
    
    def test_read_write_svg_defaulted_format(self):
        """Read an svg file and override its styles with the configuration file 
        format."""
        pass
    
    def test_export_freecad_sketch_to_svg(self):
        """Read a freecad model and write one of its sketches as a svg file."""
        sketch_label = "xz_rounded_rectangle_with_circle"
        out_path = os.path.join(self.OUT_DIR,
                                "test_export_freecad_sketch_to_svg.svg")
        sketch_svg_file = PanCAD.read_freecad_sketch(sketch_label, self.FC_0)
        sketch_svg_file.write(out_path)
    
    def test_import_svg_to_freecad_sketch(self):
        """Read a svg file and add it to a freecad model as a sketch."""
        pass
    
    def test_sync_freecad_sketch_and_svg_file(self):
        """Read both a freecad sketch and svg file, compare them, and update the 
        oldest one to the newer one."""
        pass

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()