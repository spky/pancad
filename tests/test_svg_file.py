import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


sys.path.append('src')

import svg_file as sf

class TestSVGFile(unittest.TestCase):
    
    def setUp(self):
        file_name = "init_test.svg"
        self.file = sf.SVGFile(file_name)
        self.folder = "tests/test_output_dump"
    
    def test_add_svg(self):
        self.file.add_svg()
        self.file.add_svg()
        texts = []
        for s in self.file.svgs:
            texts.append(ET.tostring(self.file.svgs[s], encoding="UTF-8"))
        ans = [
            b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" width="0in" height="0in" viewBox="0 0 0 0" id="svg1" />',
            b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" width="0in" height="0in" viewBox="0 0 0 0" id="svg2" />',
        ]
        self.assertCountEqual(texts, ans)
    
    def test_activate_svg(self):
        self.file.add_svg()
        self.file.activate_svg("svg1")
        self.assertEqual(self.file.active_svg, "svg1")
        self.assertEqual(self.file.active_g, None)
    
    def test_activate_svg_exist_except(self):
        self.file.add_svg()
        ans = "should not exist"
        with self.assertRaises(ValueError, msg="Value given: "+str(ans)):
            self.file.activate_svg(ans)
    
    def test_add_g(self):
        self.file.add_svg()
        self.file.add_g("layer1")
        svg = self.file.svgs[self.file.active_svg]
        self.assertEqual(self.file.active_g, "layer1")
    
    def test_add_path(self):
        self.file.add_svg()
        self.file.add_g("layer1")
        self.file.add_path("path1", "M 1.1 2.2", "fill:none")
        test = ET.tostring(self.file.svgs["svg1"])
        ans = b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" width="0in" height="0in" viewBox="0 0 0 0" id="svg1"><g id="layer1"><path style="fill:none" d="M 1.1 2.2" id="path1" /></g></svg>'
        self.assertEqual(test, ans)
    
    def test_write_single_svg(self):
        svg_id = "svg1"
        self.file.name = "test_write_single_svg.svg"
        self.file.add_svg(id_=svg_id, width="1in", height="1in")
        self.file.add_g("layer1")
        self.file.add_path("path1",
                           "M 0.1 0.1 0.9 0.9 0.1 0.9")
        folder = "tests/test_output_dump"
        self.file.write_single_svg(svg_id, folder)
    
    def test_write(self):
        self.file.name = "test_write_svg.svg"
        self.file.add_svg(id_="svg1", width="1in", height="1in")
        self.file.add_g("layer1")
        self.file.add_path("path1",
                           "M 0.1 0.1 0.9 0.9 0.1 0.9")
        self.file.add_svg(id_="svg2", width="1in", height="1in")
        self.file.add_g("layer1")
        self.file.add_path("path1",
                           "M 0.1 0.1 0.9 0.9 0.1 0.9 z")
        self.file.write(self.folder)
    
    def test_auto_size_view(self):
        self.file.name = "test_write_svg.svg"
        self.file.add_svg(id_="svg1", width="1in", height="1in")
        self.file.add_g("layer1")
        self.file.add_path("path1",
                           "M 0.1 0.1 0.9 0.9")
        self.file.add_path("path2",
                           "M 0 1.5 A 1.5 1.5 0 0 0 1.5 0")
        self.file.add_circle("circle1", ["0.5in", "0.5in"], "0.25in")
        self.file.auto_size_view()
    
    def test_write_circle(self):
        self.file.name = "test_write_circle_svg.svg"
        self.file.add_svg(id_="svg1", width="1in", height="1in")
        self.file.add_g("layer1")
        self.file.add_circle("circle1", ["0.5in", "0.5in"], "0.25in")
        self.file.write(self.folder)

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()