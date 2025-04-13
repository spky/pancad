import sys
from pathlib import Path
import unittest
import math

import numpy as np

sys.path.append('src')
from PanCAD.utils import trigonometry as trig
from PanCAD.geometry.point import Point
from PanCAD.geometry.line import Line
from PanCAD.utils import verification

ROUNDING_PLACES = 10

class TestLineInit(unittest.TestCase):
    
    def setUp(self):
        self.pt_a = Point((1,0,0))
        self.pt_b = Point((1,10,0))
    
    def test_line_init_no_arg(self):
        l = Line()
    
    def test_line_str_dunder(self):
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
        # Point A, Point B, Expected Point Closest to Origin,
        # Vector in Expected Direction (subsequently converted to unit vector)
        self.tests = [
            # Set 1: Diagonal Off-Origin
            ((0, 4), (4, 0), (2, 2), (-1, 1)),
            ((0, 4), (-4, 0), (-2, 2), (1, 1)),
            ((0, -4), (-4, 0), (-2, -2), (-1, 1)),
            ((0, -4), (4, 0), (2, -2), (1, 1)),
            # Set 2: Vertical +, -, and 0
            ((2, 0), (2, 2), (2, 0), (0, 1)),
            ((-2, 0), (-2, 2), (-2, 0), (0, 1)),
            ((0, 0), (0, 2), (0, 0), (0, 1)),
            # Set 3: Horizontal +, -, and 0
            ((0, 2), (2, 2), (0, 2), (1, 0)),
            ((0, -2), (2, -2), (0, -2), (1, 0)),
            ((0, 0), (2, 0), (0, 0), (1, 0)),
            # Set 4: Diagonal On-Origin Per Quadrant
            ((1, 1), (2, 2), (0, 0), (1, 1)),
            ((-1, 1), (-2, 2), (0, 0), (-1, 1)),
            ((-1, -1), (-2, -2), (0, 0), (1, 1)),
            ((1, -1), (2, -2), (0, 0), (-1, 1)),
            # Set 5: Diagonal On-Origin Across Quadrant
            ((-1, -1), (1, 1), (0, 0), (1, 1)),
            ((-1, 1), (1, -1), (0, 0), (-1, 1)),
            # Set 6: Horizontal/Vertical On-Origin Across Quadrant
            ((-1, 0), (1, 0), (0, 0), (1, 0)),
            ((0, -1), (0, 1), (0, 0), (0, 1)),
        ]
        for i, (pt_a, pt_b, e_pt, vector) in enumerate(self.tests):
            # Convert expected direction to unit vector
            np_vector = trig.to_1D_np(vector)
            unit_vector = trig.get_unit_vector(np_vector)
            self.tests[i] = (pt_a, pt_b, e_pt, trig.to_1D_tuple(unit_vector))
    
    def test_from_two_points_point_closest_to_origin(self):
        for point_a, point_b, expected_point, _ in self.tests:
            with self.subTest(point_a=point_a, point_b=point_b,
                              expected_point=expected_point):
                pt_a, pt_b = Point(point_a), Point(point_b)
                e_pt = Point(expected_point)
                test_line = Line.from_two_points(pt_a, pt_b)
                verification.assertPointsAlmostEqual(
                    self, test_line._point_closest_to_origin, e_pt,
                    ROUNDING_PLACES
                )
    
    def test_from_two_points_direction(self):
        for point_a, point_b, _, expected_direction in self.tests:
            with self.subTest(point_a=point_a, point_b=point_b,
                              expected_direction=expected_direction):
                pt_a, pt_b = Point(point_a), Point(point_b)
                test_line = Line.from_two_points(pt_a, pt_b)
                verification.assertTupleAlmostEqual(
                    self, test_line.direction, expected_direction,
                    ROUNDING_PLACES
                )
    
    def test_from_two_points_same_point(self):
        pt_a = Point((1, 1))
        pt_b = Point((1, 1))
        with self.assertRaises(ValueError):
            test_line = Line.from_two_points(pt_a, pt_b)

class TestLineRichComparison(unittest.TestCase):
    
    def setUp(self):
        self.tests = [
            ((0, 0), (1, 1), (0, 0), (1, 1), True),
            ((1, 0), (1, 1), (0, 0), (1, 1), False),
            ((0, 0, 0), (1, 1, 1), (0, 0, 0), (1, 1, 1), True),
            ((1, 0, 0), (1, 1, 0), (0, 0, 0), (1, 1, 0), False),
        ]
        for i, (pt1a, pt1b, pt2a, pt2b, equality) in enumerate(self.tests):
            self.tests[i] = (Point(pt1a), Point(pt1b),
                             Point(pt2a), Point(pt2b),
                             equality)
    
    def test_line_equality(self):
        for pt1a, pt1b, pt2a, pt2b, expected_equality in self.tests:
            with self.subTest(point1a=tuple(pt1a), point1b=tuple(pt1b),
                              point2a=tuple(pt2a), point2b=tuple(pt2b),
                              expected_equality=expected_equality):
                line1 = Line.from_two_points(pt1a, pt1b)
                line2 = Line.from_two_points(pt2a, pt2b)
                self.assertEqual(line1 == line2, expected_equality)
    
    def test_line_inequality(self):
        for pt1a, pt1b, pt2a, pt2b, expected_equality in self.tests:
            with self.subTest(point1a=tuple(pt1a), point1b=tuple(pt1b),
                              point2a=tuple(pt2a), point2b=tuple(pt2b),
                              expected_equality= not expected_equality):
                line1 = Line.from_two_points(pt1a, pt1b)
                line2 = Line.from_two_points(pt2a, pt2b)
                self.assertEqual(line1 != line2, not expected_equality)

if __name__ == "__main__":
    with open("tests/logs/" + Path(sys.modules[__name__].__file__).stem
              +".log", "w") as f:
        f.write("finished")
    unittest.main()