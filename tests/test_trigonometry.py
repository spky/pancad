import sys
from pathlib import Path
import unittest
import math

import numpy as np

sys.path.append('src')

import trigonometry as trig

class TestTrigonometry(unittest.TestCase):
    
    def test_point_distance(self):
        tests = [
            [[trig.point_2d([0, 0]), trig.point_2d([0, 0])], 0],
            [[trig.point_2d([1, 1]), trig.point_2d([4, 5])], 5],
            [[trig.point_2d([-1, -1]), trig.point_2d([4, 5])], 7.810250],
        ]
        for test in tests:
            with self.subTest(test=test):
                distance = trig.distance_2d(test[0][0], test[0][1])
                self.assertEqual(distance, test[1])
    
    def test_point_line_angle(self):
        tests = [
            [[trig.point_2d([0, 0]), trig.point_2d([1, 1])], round(math.pi/4,6)],
            [[trig.point_2d([0, 0]), trig.point_2d([0, 1])], round(math.pi/2,6)],
            [[trig.point_2d([0, 0]), trig.point_2d([-1, 1])], round(3*math.pi/4,6)],
            [[trig.point_2d([0, 0]), trig.point_2d([-1, -1])], round(-3*math.pi/4,6)],
            [[trig.point_2d([0, 0]), trig.point_2d([0, -1])], round(-math.pi/2,6)],
            [[trig.point_2d([0, 0]), trig.point_2d([1, -1])], round(-math.pi/4,6)],
            [[trig.point_2d([0, 0]), trig.point_2d([1, 0])], 0],
            [[trig.point_2d([0, 0]), trig.point_2d([-1, 0])], round(math.pi,6)],
        ]
        for test in tests:
            with self.subTest(test=test):
                angle = trig.point_line_angle(test[0][0], test[0][1])
                self.assertEqual(angle, test[1])
    
    def test_point_line_angle_degrees(self):
        tests = [
            [[trig.point_2d([0, 0]), trig.point_2d([1, 1])], 45],
            [[trig.point_2d([0, 0]), trig.point_2d([0, 1])], 90],
            [[trig.point_2d([0, 0]), trig.point_2d([-1, 1])], 135],
            [[trig.point_2d([0, 0]), trig.point_2d([-1, -1])], -135],
            [[trig.point_2d([0, 0]), trig.point_2d([0, -1])], -90],
            [[trig.point_2d([0, 0]), trig.point_2d([1, -1])], -45],
            [[trig.point_2d([0, 0]), trig.point_2d([1, 0])], 0],
            [[trig.point_2d([0, 0]), trig.point_2d([-1, 0])], 180],
        ]
        for test in tests:
            with self.subTest(test=test):
                angle = trig.point_line_angle(test[0][0], test[0][1],
                                              radians = False)
                self.assertEqual(angle, test[1])
    
    def test_rotation_2d(self):
        dec = 6
        tests = [
            [
                0,
                [
                    [1, 0],
                    [0, 1]
                ]
            ],
            [
                math.radians(45),
                [
                    [round(1/math.sqrt(2),dec), round(-1/math.sqrt(2),dec)],
                    [round(1/math.sqrt(2),dec), round(1/math.sqrt(2),dec)]
                ]
            ],
            [
                math.radians(10),
                [
                    [0.984808, -0.173648],
                    [0.173648, 0.984808]
                ]
            ],
            [
                math.radians(-10),
                [
                    [0.984808, 0.173648],
                    [-0.173648, 0.984808]
                ]
            ],
        ]
        for test in tests:
            with self.subTest(test=test):
                matrix = trig.rotation_2d(test[0],dec)
                self.assertCountEqual(matrix.tolist(), test[1])
    
    def test_midpoint_2d(self):
        tests = [
            [trig.point_2d([0, 0]), trig.point_2d([1, 1]), [0.5, 0.5]],
            [trig.point_2d([1, 1]), trig.point_2d([2, 2]), [1.5, 1.5]],
            [trig.point_2d([-1, -1]), trig.point_2d([1, 1]), [0, 0]],
        ]
        for test in tests:
            with self.subTest(test=test):
                midpt = trig.midpoint_2d(test[0], test[1]).reshape(2)
                self.assertCountEqual(midpt.tolist(), test[2])
    
    def test_angle_between_vectors_2d(self):
        dec = 6
        tests = [
            [trig.point_2d([0,1]), trig.point_2d([1,0]), round(math.radians(-90), dec)],
            [trig.point_2d([0,40]), trig.point_2d([30,0]), round(math.radians(-90), dec)],
            [trig.point_2d([1,0]), trig.point_2d([0,1]), round(math.radians(90), dec)],
            [trig.point_2d([1,0]), trig.point_2d([1,1]), round(math.radians(45), dec)],
            [trig.point_2d([1,0]), trig.point_2d([-1,1]), round(math.radians(135), dec)],
            [trig.point_2d([1,0]), trig.point_2d([-1,-1]), round(math.radians(-135), dec)],
            [trig.point_2d([1,0]), trig.point_2d([-1,0]), round(math.radians(180), dec)],
            [trig.point_2d([-1,0]), trig.point_2d([1,0]), round(math.radians(180), dec)],
            [trig.point_2d([-20,0]), trig.point_2d([30,0]), round(math.radians(180), dec)],
            [trig.point_2d([10,10]), trig.point_2d([-20,-20]), round(math.radians(180), dec)],
            [trig.point_2d([100,100]), trig.point_2d([-20,-20]), round(math.radians(180), dec)],
        ]
        
        for test in tests:
            with self.subTest(test=test):
                angle = trig.angle_between_vectors_2d(test[0], test[1])
                self.assertEqual(angle, test[2])
    
    def test_angle_between_vectors_2d_degrees(self):
        dec = 6
        tests = [
            [trig.point_2d([0,1]), trig.point_2d([1,0]), -90],
            [trig.point_2d([0,40]), trig.point_2d([30,0]), -90],
            [trig.point_2d([1,0]), trig.point_2d([0,1]), 90],
            [trig.point_2d([1,0]), trig.point_2d([1,1]), 45],
            [trig.point_2d([1,0]), trig.point_2d([-1,1]), 135],
            [trig.point_2d([1,0]), trig.point_2d([-1,-1]), -135],
            [trig.point_2d([1,0]), trig.point_2d([-1,0]), 180],
            [trig.point_2d([-1,0]), trig.point_2d([1,0]), 180],
            [trig.point_2d([-20,0]), trig.point_2d([30,0]), 180],
            [trig.point_2d([10,10]), trig.point_2d([-20,-20]), 180],
            [trig.point_2d([100,100]), trig.point_2d([-20,-20]), 180],
        ]
        
        for test in tests:
            with self.subTest(test=test):
                angle = trig.angle_between_vectors_2d(test[0], test[1], radians=False)
                self.assertEqual(angle, test[2])
    
    def test_elliptical_arc_endpoint_to_center(self):
        # Test input order: [[pt1, pt2, laf, sf, major r, minor r, major angle], center pt, theta 1, delta theta]
        # [-2.3039, 2.4273]
        # [3.8039, -.9273]
        dec = 4
        tests = [
            [[trig.point_2d([.5, .5]), trig.point_2d([1, 1]), True, True, 4, 3, math.radians(10)], [-2.3039, 2.4273], round(math.radians(-44.5023), dec), round(math.radians(348.8614), dec)],
            [[trig.point_2d([.5, .5]), trig.point_2d([1, 1]), False, True, 4, 3, math.radians(10)], [3.8039, -.9273], round(math.radians(146.636), dec), round(math.radians(11.1386), dec)],
            [[trig.point_2d([.5, .5]), trig.point_2d([1, 1]), True, False, 4, 3, math.radians(10)], [3.8039, -.9273], round(math.radians(146.636), dec), round(math.radians(-348.8614), dec)],
            [[trig.point_2d([.5, .5]), trig.point_2d([1, 1]), False, False, 4, 3, math.radians(10)], [-2.3039, 2.4273], round(math.radians(-44.5023), dec), round(math.radians(-11.1386), dec)],
        ]
        
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.elliptical_arc_endpoint_to_center(i[0], i[1], i[2], i[3], i[4], i[5], i[6], decimals=dec)
                self.assertCountEqual(out[0].reshape(2).tolist(), t[1])
                self.assertEqual(out[1], t[2])
                self.assertEqual(out[2], t[3])


if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()