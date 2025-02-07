import sys
from pathlib import Path
import unittest

sys.path.append('src')

import svg_readers as sr
import svg_file as sf

class TestSVGReaders(unittest.TestCase):
    
    def setUp(self):
        self.SAMPLE_FOLDER = "tests/sample_svgs/"
        self.OUTPUT_DUMP_FOLDER = "tests/test_output_dump/"
        self.file = sf.SVGFile()
        root = sf.svg("svg1")
        
        for i in range(0, 3):
            group = sf.g("group" + str(i))
            for j in range(0, 3):
                path_element = sf.path("path" + str(i) + "_" + str(j))
                group.append(path_element)
            root.append(group)
        
        self.file.svg = root
    
    def test_read_subelements(self):
        subelements = sr.read_subelements(self.file.svg)

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()