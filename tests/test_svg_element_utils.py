import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

sys.path.append('src')

import svg.svg_element_utils as seu

class TestSVGElementUtils(unittest.TestCase):
    
    def setUp(self):
        self.root = ET.Element("svg")
        self.root.set("id","svg1")
        for i in range(0, 3):
            group = ET.Element("g")
            group.set("id", "group" + str(i))
            for j in range(0, 3):
                path_element = ET.Element("path")
                path_element.set("id", "path" + str(i) + "_" + str(j))
                group.append(path_element)
            self.root.append(group)
    
    def test_upgrade_element(self):
        tests = [
            ET.Element("svg"),
            ET.Element("g"),
            ET.Element("path"),
            ET.Element("circle", {"cx": "1in", "cy": "1in", "r": "1in"}),
            ET.Element("defs"),
        ]
        for t in tests:
            with self.subTest(t=t):
                new = seu.upgrade_element(t)
    
    def test_upgrade_element_deep(self):
        new = seu.upgrade_element(self.root)

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()