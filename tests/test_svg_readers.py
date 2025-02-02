import sys
from pathlib import Path
import unittest

sys.path.append('src')

import svg_readers as sr

class TestSVGReaders(unittest.TestCase):
    
    def setUp(self):
        self.SAMPLE_FOLDER = "tests/sample_svgs/"
        self.OUTPUT_DUMP_FOLDER = "tests/test_output_dump/"
    """
    def test_svg(self):
        filename = "input_sketch_test.svg"
        path = self.SAMPLE_FOLDER + filename
        sr.read_svg(path)
    """

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()