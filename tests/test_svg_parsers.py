import sys
from pathlib import Path
import unittest

sys.path.append('src')

import svg.parsers as sp

class TestSVGPath(unittest.TestCase):
    
    def test_split_path_data(self):
        path_data = "M 1.4429557,0.40800819 A 0.31844541,0.31844541 0 0 1 1.2957424,0.67649852 0.31844541,0.31844541 0 0 1 0.99021212,0.6967494 M 1.4429557,0.40800819z"
        ans = [
            "M 1.4429557,0.40800819", 
            "A 0.31844541,0.31844541 0 0 1 1.2957424,0.67649852 0.31844541,0.31844541 0 0 1 0.99021212,0.6967494",
            "M 1.4429557,0.40800819",
            "z",
        ]
        cmds = sp.split_path_data(path_data)
        self.assertCountEqual(cmds, ans)
    
    def test_clean_command(self):
        tests = [
            ["A 0.3 0.3 0 0 1 2 2", "0.3,0.3,0,0,1,2,2"],
            ["A 0.3,0.3,0,0,1,2,2", "0.3,0.3,0,0,1,2,2"],
            ["A 0.3,0.3,0,0,1,2,2 ", "0.3,0.3,0,0,1,2,2"],
            ["A 0.3,0.3 0 0 1 2, 2", "0.3,0.3,0,0,1,2,2"],
            ["M 0.3,0.3 0 0 ", "0.3,0.3,0,0"],
        ]
        for t in tests:
            with self.subTest(t=t):
                out = sp.clean_command(t[0])
                self.assertEqual(out, t[1])
    
    def test_length_unit(self):
        tests = [
            ["1.0in", "in"],
            ["1mm", "mm"],
            ["1", ""],
            [1, ""],
            [1.1, ""],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = sp.length_unit(i)
                self.assertEqual(out, t[1])
    
    def test_parse_moveto(self):
        cmd = "M 1.4429557,0.40800819 0.31844541,0.31844541"
        ans = [
            [1.4429557, 0.40800819],
            [0.31844541,0.31844541],
        ]
        test = sp.parse_moveto(cmd)
        self.assertCountEqual(test, ans)
    
    def test_create_sublists(self):
        list_ = [100, 150, 200, 250, 300, 350]
        no_parameters = 2
        test = sp.create_sublists(list_, no_parameters)
        ans = [[100, 150], [200, 250], [300, 350]]
        self.assertCountEqual(test, ans)
    
    def test_create_sublists_single_element(self):
        list_ = [100, 150]
        no_parameters = 2
        test = sp.create_sublists(list_, no_parameters)
        ans = [[100, 150]]
        self.assertCountEqual(test, ans)
    
    def test_parse_arc(self):
        cmd = "A 0.31844541,0.31844541 0 0 1 1.2957424,0.67649852 0.31844541,0.31844541 0 0 1 0.99021212,0.6967494"
        ans = [
            [0.31844541,0.31844541, 0, 0, 1, 1.2957424, 0.67649852],
            [0.31844541,0.31844541, 0, 0, 1, 0.99021212, 0.6967494],
        ]
        test = sp.parse_arc(cmd)
        self.assertCountEqual(test, ans)
    
    def test_parse_lineto(self):
        cmd = "L 1.4429557,0.40800819 0.31844541,0.31844541"
        ans = [
            [1.4429557, 0.40800819],
            [0.31844541,0.31844541],
        ]
        test = sp.parse_lineto(cmd)
        self.assertCountEqual(test, ans)
    
    def test_parse_horizontal(self):
        cmd = "H 1.4429557,0.40800819"
        ans = [1.4429557, 0.40800819]
        test = sp.parse_horizontal(cmd)
        self.assertCountEqual(test, ans)
    
    def test_path_cmd_type(self):
        tests = [
            ["M 1.4429557,0.40800819", "absolute_moveto"],
            ["m 1.4429557,0.40800819", "relative_moveto"],
            ["A 0.31844541,0.31844541 0 0 1 1.2957424,0.67649852 0.31844541,0.31844541 0 0 1 0.99021212,0.6967494", "absolute_arc"],
            ["a 0.31844541,0.31844541 0 0 1 1.2957424,0.67649852 0.31844541,0.31844541 0 0 1 0.99021212,0.6967494", "relative_arc"],
            ["z", "closepath"],
            ["Z", "closepath"],
            ["L 1.4429557,0.40800819 0.31844541,0.31844541", "absolute_lineto"],
            ["l 1.4429557,0.40800819 0.31844541,0.31844541", "relative_lineto"],
            ["H 1.4429557,0.40800819", "absolute_horizontal"],
            ["h 1.4429557,0.40800819", "relative_horizontal"],
            ["V 1.4429557,0.40800819", "absolute_vertical"],
            ["v 1.4429557,0.40800819", "relative_vertical"],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = sp.path_cmd_type(i)
                self.assertEqual(out, t[1])
    
    def test_path_data_to_dicts(self):
        tests = [
            [["M 1.0,1.0 2.0,2.0 3.0,3.0", "path1"], None],
            [["m 1.0,1.0 2.0,2.0 3.0,3.0", "path2"], None],
            [["m 0.1 0.1 0.9 0.9", "path3"], None],
            [["M 0.1,0.1 0.9,0.9 0.1,0.9z", "path4"], None],
            [["M 1.0,1.0", "path5"], None],
            [["m 1.0,1.0", "path6"], None],
            [["m 0.1,0.1 0.9,0.9 -0.9,0z", "path7"], None],
            [["A 0.3,0.3 0 0 1 1.2,0.6 0.3,0.3 0 0 1 0.9,0.6", "path8"], None],
            [["A 0.3,0.3 0 0 1 1.2,0.6", "path8"], None],
            [["M 1.0 1.0 A 0.3,0.3 0 0 1 2, 2", "path9a"], None],
            [["M 1.0 1.0 A 0.4,0.3 0 0 1 2, 2", "path9b"], None],
            [["M 1.0 1.0 a 0.3,0.3 0 0 1 2, 2", "path10a"], None],
            [["M 1.0 1.0 a 0.4,0.3 0 0 1 2, 2", "path10b"], None],
            [["L 1.0,1.0", "path11"], None],
            [["M 1.0 1.0 l 1.0,1.0", "path12"], None],
            [["M 1.0 1.0 H 2.0", "path13"], None],
            [["M 1.0 1.0 h 2.0", "path14"], None],
            [["M 1.0 1.0 V 2.0", "path15"], None],
            [["M 1.0 1.0 v 2.0", "path16"], None],
            [["M 1.0 1.0 H 2.0 v 1.0", "path13"], None],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = sp.path_data_to_dicts(i[0], i[1])
    
    def test_absolute_moveto_to_dict(self):
        tests = [
            [
                ["M 1.0 1.0", "path1", 0],
                [[1.0, 1.0], [], None, 0]
            ],
            [
                ["M 1.0 1.0 2.0 2.0", "path1", 0], # Input
                [
                    [2.0, 2.0], # Current Point
                    [
                        sp.line("path1", 0, [1.0, 1.0], [2.0, 2.0]),
                    ], # Lines
                    [1.0, 1.0], # Subpath Initial Point
                    1 # Shape Count
                ] # Output
            ],
            [
                ["M 1.0 1.0 2.0 2.0 3.0 3.0", "path1", 0], # Input
                [
                    [3.0, 3.0], # Current Point
                    [
                        sp.line("path1", 0, [1.0, 1.0], [2.0, 2.0]),
                        sp.line("path1", 1, [2.0, 2.0], [3.0, 3.0]),
                    ], # Lines
                    [1.0, 1.0], # Subpath Initial Point
                    2 # Shape Count
                ] # Output
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = sp.absolute_moveto_to_dict(i[0], i[1], i[2])
                self.assertCountEqual(out, t[1])
        
    def test_relative_moveto_to_dict(self):
        tests = [
            [
                ["m 1.0 1.0",[0, 0], 0, "path1", 0],
                [[1.0, 1.0], [], None, 0]
            ],
            [
                ["m 1.0 1.0",[1, 1], 1, "path1", 0],
                [[2.0, 2.0], [], None, 0]
            ],
            [
                ["m 1.0 1.0 2.0 2.0", [0, 0], 0, "path1", 0], # Input
                [
                    [3.0, 3.0], # Current Point
                    [
                        sp.line("path1", 0, [1.0, 1.0], [3.0, 3.0]),
                    ], # Lines
                    [1.0, 1.0], # Subpath Initial Point
                    1 # Shape Count
                ] # Output
            ],
            [
                ["m 1.0 1.0 2.0 2.0 3.0 3.0",[0, 0], 0, "path1", 0], # Input
                [
                    [6.0, 6.0], # Current Point
                    [
                        sp.line("path1", 0, [1.0, 1.0], [3.0, 3.0]),
                        sp.line("path1", 1, [3.0, 3.0], [6.0, 6.0]),
                    ], # Lines
                    [1.0, 1.0], # Subpath Initial Point
                    2 # Shape Count
                ] # Output
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = sp.relative_moveto_to_dict(i[0], i[1], i[2], i[3], i[4])
                self.assertCountEqual(out, t[1])
    
    def test_arc_to_dict(self):
        tests = [
            [
                [
                    "A 0.3,0.3 0 0 1 1.2,0.6", # Command
                    [0, 0], # Current Point
                    "path1", # Path Id
                    0, # Shape Count
                    False, # relative
                ], # Input
                [
                    [1.2, 0.6], # Current Point
                    [
                        sp.circular_arc("path1", 0, [0, 0], [1.2, 0.6],
                                        0.3, False, True),
                    ], # Arcs
                    [0, 0], # Subpath Initial Point
                    1, # Shape Count
                ], # Output
                [
                    "A 0.4,0.3 0 0 1 1.2,0.6", # Command
                    [0, 0], # Current Point
                    "path1", # Path Id
                    0, # Shape Count
                    False, # relative
                ], # Input
                [
                    [1.2, 0.6], # Current Point
                    [
                        sp.elliptical_arc("path1", 0, [0, 0], [1.2, 0.6],
                                          0.4, 0.3, 0, False, True),
                    ], # Arcs
                    [0, 0], # Subpath Initial Point
                    1, # Shape Count
                ], # Output
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = sp.arc_to_dict(i[0], i[1], i[2], i[3], i[4])
                self.assertCountEqual(out, t[1])
    
    def test_lineto_to_dict(self):
        pass

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()