import sys
from pathlib import Path
import unittest

sys.path.append('src')

from svg_interface import SVGPath
from svg_parsers import (
    split_path_data, 
    parse_moveto, 
    create_sublists, 
    parse_arc, 
    parse_lineto,
    parse_horizontal,
)

class TestSVGPath(unittest.TestCase):
    
    def test_d_M_spaces_with_cooordinate_commas(self):
        c = SVGPath._parse_path_data("M 100,150 200,250 L 200,200")[0]
        self.assertEqual(c["type"], "M")
        self.assertCountEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L 200,200")
    
    def test_d_M_min_spaces_no_commas(self):
        c = SVGPath._parse_path_data("M100 150 200 250L200 200")[0]
        self.assertEqual(c["type"], "M")
        self.assertCountEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L200 200")
    
    def test_d_M_no_spaces_all_commas(self):
        c = SVGPath._parse_path_data("M100,150,200,250L200,200")[0]
        self.assertEqual(c["type"], "M")
        self.assertCountEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L200,200")
    
    def test_d_M_no_spaces_all_commas_float(self):
        c = SVGPath._parse_path_data("M100.1,150.2,200.3,250.4L200.1,200.2")[0]
        self.assertEqual(c["type"], "M")
        self.assertCountEqual(c["coordinates"], [[100.1, 150.2], [200.3, 250.4]])
        self.assertEqual(c["leftover"], "L200.1,200.2")
    
    def test_d_low_m_spaces_with_cooordinate_commas(self):
        c = SVGPath._parse_path_data("m 100,150 200,250 L 200,200")[0]
        self.assertEqual(c["type"], "m")
        self.assertCountEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L 200,200")
    
    def test_d_low_m_min_spaces_no_commas(self):
        c = SVGPath._parse_path_data("m100 150 200 250L200 200")[0]
        self.assertEqual(c["type"], "m")
        self.assertCountEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L200 200")
    
    def test_d_low_m_no_spaces_all_commas(self):
        c = SVGPath._parse_path_data("m100,150,200,250L200,200")[0]
        self.assertEqual(c["type"], "m")
        self.assertCountEqual(c["coordinates"], [[100, 150], [200, 250]])
        self.assertEqual(c["leftover"], "L200,200")
    
    def test_absolute_move_to(self):
        coordinate_list = [[100, 150], [200, 250]]
        move_to = SVGPath.absolute_move_to(coordinate_list)
        self.assertEqual(move_to, "M 100 150\nM 200 250")
    
    def test_split_path_data(self):
        path_data = "M 1.4429557,0.40800819 A 0.31844541,0.31844541 0 0 1 1.2957424,0.67649852 0.31844541,0.31844541 0 0 1 0.99021212,0.6967494 M 1.4429557,0.40800819z"
        ans = [
            "M 1.4429557,0.40800819", 
            "A 0.31844541,0.31844541 0 0 1 1.2957424,0.67649852 0.31844541,0.31844541 0 0 1 0.99021212,0.6967494",
            "M 1.4429557,0.40800819",
            "z",
        ]
        cmds = split_path_data(path_data)
        self.assertCountEqual(cmds, ans)
    
    def test_parse_moveto(self):
        cmd = "M 1.4429557,0.40800819 0.31844541,0.31844541"
        ans = [
            [1.4429557, 0.40800819],
            [0.31844541,0.31844541],
        ]
        test = parse_moveto(cmd)
        self.assertCountEqual(test, ans)
    
    def test_create_sublists(self):
        list_ = [100, 150, 200, 250, 300, 350]
        no_parameters = 2
        test = create_sublists(list_, no_parameters)
        ans = [[100, 150], [200, 250], [300, 350]]
        self.assertCountEqual(test, ans)
    
    def test_create_sublists_single_element(self):
        list_ = [100, 150]
        no_parameters = 2
        test = create_sublists(list_, no_parameters)
        ans = [[100, 150]]
        self.assertCountEqual(test, ans)
    
    def test_parse_arc(self):
        cmd = "A 0.31844541,0.31844541 0 0 1 1.2957424,0.67649852 0.31844541,0.31844541 0 0 1 0.99021212,0.6967494"
        ans = [
            [0.31844541,0.31844541, 0, 0, 1, 1.2957424, 0.67649852],
            [0.31844541,0.31844541, 0, 0, 1, 0.99021212, 0.6967494],
        ]
        test = parse_arc(cmd)
        self.assertCountEqual(test, ans)
    
    def test_parse_lineto(self):
        cmd = "L 1.4429557,0.40800819 0.31844541,0.31844541"
        ans = [
            [1.4429557, 0.40800819],
            [0.31844541,0.31844541],
        ]
        test = parse_lineto(cmd)
        self.assertCountEqual(test, ans)
    
    def test_parse_horizontal(self):
        cmd = "H 1.4429557,0.40800819"
        ans = [1.4429557, 0.40800819]
        test = parse_horizontal(cmd)
        self.assertCountEqual(test, ans)

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()