import sys
import unittest

sys.path.append('../src')

from text2freecad.svg_interface import SVGPath

class TestSVGPath(unittest.TestCase):
    
    def test_d_M_spaces_with_cooordinate_commas(self):
        c = SVGPath._parse_path_data("M 100,150 200,250 L 200,200")[0]
        self.assertEqual(c["type"], "M")
        self.assertEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L 200,200")
    
    def test_d_M_min_spaces_no_commas(self):
        c = SVGPath._parse_path_data("M100 150 200 250L200 200")[0]
        self.assertEqual(c["type"], "M")
        self.assertEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L200 200")
    
    def test_d_M_no_spaces_all_commas(self):
        c = SVGPath._parse_path_data("M100,150,200,250L200,200")[0]
        self.assertEqual(c["type"], "M")
        self.assertEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L200,200")
    
    def test_d_M_no_spaces_all_commas_float(self):
        c = SVGPath._parse_path_data("M100.1,150.2,200.3,250.4L200.1,200.2")[0]
        self.assertEqual(c["type"], "M")
        self.assertEqual(c["coordinates"], [[100.1, 150.2], [200.3, 250.4]])
        self.assertEqual(c["leftover"], "L200.1,200.2")
    
    def test_d_low_m_spaces_with_cooordinate_commas(self):
        c = SVGPath._parse_path_data("m 100,150 200,250 L 200,200")[0]
        self.assertEqual(c["type"], "m")
        self.assertEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L 200,200")
    
    def test_d_low_m_min_spaces_no_commas(self):
        c = SVGPath._parse_path_data("m100 150 200 250L200 200")[0]
        self.assertEqual(c["type"], "m")
        self.assertEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L200 200")
    
    def test_d_low_m_no_spaces_all_commas(self):
        c = SVGPath._parse_path_data("m100,150,200,250L200,200")[0]
        self.assertEqual(c["type"], "m")
        self.assertEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L200,200")
    
    def test_absolute_move_to(self):
        coordinate_list = [[100, 150], [200, 250]]
        move_to = SVGPath.absolute_move_to(coordinate_list)
        self.assertEqual(move_to, "M 100 150\nM 200 250")

if __name__ == "__main__":
    unittest.main()