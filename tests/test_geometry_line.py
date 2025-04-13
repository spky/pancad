import sys
from pathlib import Path
import unittest
import math

import numpy as np

sys.path.append('src')
from PanCAD.utils import trigonometry as trig
from PanCAD.geometry.point import Point
from PanCAD.geometry.line import Line

class TestLineInit(unittest.TestCase):
    
    def setUp(self):
        self.pt_a = Point((1,0,0))
        self.pt_b = Point((1,10,0))
    
    def test_line_init_no_arg(self):
        l = Line()
    
    def test_from_two_points(self):
        test = Line.from_two_points(self.pt_a, self.pt_b)
        expected = ("PanCAD Line with a point closest to the origin at"
                    + " (1.0, 0.0, 0.0) and in the direction (0.0, 1.0, 0.0)")
        self.assertEqual(str(test), expected)

class TestLineVectorMethods(unittest.TestCase):
    
    def test_unique_direction(self):
        tests = [
            ## 2D Tests ##
            ((0, 0), (0, 0)),
            # Positive Unit Vector
            ((1, 0), (1, 0)),
            ((0, 1), (0, 1)),
            # Negative Unit Vector
            ((-1, 0), (1, 0)),
            ((0, -1), (0, 1)),
            # 2 Direction Positive and Negative
            ((1, 1), trig.get_unit_vector(np.array((1, 1)))),
            ((-1, -1), trig.get_unit_vector(np.array((1, 1)))),
            ## 3D Tests ##
            # Zero Vector
            ((0, 0, 0), (0, 0, 0)),
            # Positive Unit Vector
            ((1, 0, 0), (1, 0, 0)),
            ((0, 1, 0), (0, 1, 0)),
            ((0, 0, 1), (0, 0, 1)),
            # Negative Unit Vector
            ((-1, 0, 0), (1, 0, 0)),
            ((0, -1, 0), (0, 1, 0)),
            ((0, 0, -1), (0, 0, 1)),
            # 2 Direction Positive
            ((1, 1, 0), trig.get_unit_vector(np.array((1,1,0)))),
            ((0, 1, 1), trig.get_unit_vector(np.array((0,1,1)))),
            # 2 Direction Negative
            ((-1, -1, 0), trig.get_unit_vector(np.array((1,1,0)))),
            ((0, -1, -1), trig.get_unit_vector(np.array((0, 1, 1)))),
            # 3 Direction Positive and Negative
            ((1, 1, 1), trig.get_unit_vector(np.array((1,1,1)))),
            ((-1, -1, -1), trig.get_unit_vector(np.array([1,1,1]))),
        ]
        tests_np = []
        for test in tests:
            test_np = []
            for element in test:
                test_np.append(np.array(element))
            tests_np.append(test_np)
        
        for vector, unit_vector in tests_np:
            with self.subTest(vector=vector, unit_vector=unit_vector):
                self.assertCountEqual(Line.unique_direction(vector),
                                      unit_vector)

class TestLineClassMethods(unittest.TestCase):
    
    def setUp(self):
        # Point A, Point B, Expected Point Closest to Origin, Expected Direction
        tests = [
            ((0, 4), (4, 0), (2, 2), (-math.sqrt(2), math.sqrt(2))),
        ]
        

if __name__ == "__main__":
    with open("tests/logs/" + Path(sys.modules[__name__].__file__).stem
              +".log", "w") as f:
        f.write("finished")
    unittest.main()