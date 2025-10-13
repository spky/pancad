import sys
from pathlib import Path
import unittest
import math
from math import radians, degrees

import numpy as np

sys.path.append('src')

from pancad.utils import trigonometry as trig
from pancad.graphics.svg import parsers as sp
from pancad.constants import AngleConvention as AC

class TestTrigonometry(unittest.TestCase):
    
    def test_pt2list(self):
        tests = [
            [trig.point_2d([0, 0]), [0, 0]],
            [[0, 0], [0, 0]],
        ]
        for t in tests:
            with self.subTest(t=t):
                out = trig.pt2list(t[0])
                self.assertCountEqual(out, t[1])
    
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
    
    def test_three_point_angle(self):
        dec = 6
        tests = [
            [[trig.point_2d([1, 0]), trig.point_2d([0, 1]), trig.point_2d([0,0])], round(np.radians(90), dec)],
            [[trig.point_2d([0, 1]), trig.point_2d([1, 0]), trig.point_2d([0,0])], round(np.radians(-90), dec)],
            [[trig.point_2d([0, 1.5]), trig.point_2d([1.5, 0]), trig.point_2d([0,0])], round(np.radians(-90), dec)],
            [[trig.point_2d([1, 1]), trig.point_2d([1, 0]), trig.point_2d([0,0])], round(np.radians(-45), dec)],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                angle = trig.three_point_angle(i[0], i[1], i[2], dec)
                self.assertEqual(angle, t[1])
    
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
    
    def test_ellipse_point(self):
        dec = 4
        tests = [
            [[trig.point_2d([0,0]), 4, 3, math.radians(0), math.radians(0)], [4, 0]],
            [[trig.point_2d([0,0]), 4, 3, math.radians(90), math.radians(0)], [0, 4]],
            [[trig.point_2d([0,0]), 4, 3, math.radians(-90), math.radians(0)], [0, -4]],
            [[trig.point_2d([0,0]), 4, 3, math.radians(180), math.radians(0)], [-4, 0]],
            [[trig.point_2d([0,0]), 4, 3, math.radians(-180), math.radians(0)], [-4, 0]],
            [[trig.point_2d([1,0]), 4, 3, math.radians(0), math.radians(0)], [5, 0]],
            [[trig.point_2d([0,0]), 4, 3, math.radians(0), math.radians(270)], [0, -3]],
            [[trig.point_2d([0,0]), 4, 3, math.radians(0), math.radians(345)], [3.7668, -1.0093]],
            [[trig.point_2d([3.80397, -.92726]), 4, 3, math.radians(10), math.radians(146.636)], [.5, .5]],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.ellipse_point(i[0], i[1], i[2], i[3], i[4], dec)
                self.assertCountEqual(out.reshape(2).tolist(), t[1])
    
    def test_circle_point(self):
        dec = 4
        tests = [
            [[trig.point_2d([0,0]), 4, math.radians(0)], [4, 0]],
            [[trig.point_2d([0,0]), 4, math.radians(90)], [0, 4]],
            [[trig.point_2d([0,0]), 4, math.radians(180)], [-4, 0]],
            [[trig.point_2d([0,0]), 4, math.radians(-180)], [-4, 0]],
            [[trig.point_2d([0,0]), 4, math.radians(-90)], [0, -4]],
            [[trig.point_2d([1,0]), 4, math.radians(0)], [5, 0]],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.circle_point(i[0], i[1], i[2], dec)
                self.assertCountEqual(out.reshape(2).tolist(), t[1])
    
    def test_elliptical_arc_endpoint_to_center(self):
        # Test input order: [[pt1, pt2, laf, sf, major r, minor r, major angle], center pt, theta 1, delta theta]
        # [-2.3039, 2.4273]
        # [3.8039, -.9273]
        #sp.circular_arc("path1", 0, [0, 0], [1.2, 0.6],
        #                    0.3, False, True),
        dec = 4
        tests = [
            [
                [
                    trig.point_2d([.5, .5]), trig.point_2d([1, 1]), # start, end
                    False, False, 4, 3, # large arc, sweep, major r, minor r
                    math.radians(10) # major axis angle
                ],
                [3.8039, -.9273], # center point
                round(math.radians(146.636), dec), # start angle
                round(math.radians(-11.1386), dec) # sweep angle
            ],
            [
                [
                    trig.point_2d([.5, .5]), trig.point_2d([1, 1]),
                    False, True, 4, 3,
                    math.radians(10)
                ],
                [-2.3039, 2.4273],
                round(math.radians(-44.5023), dec),
                round(math.radians(11.1386), dec)
            ],
            [
                [
                    trig.point_2d([.5, .5]), trig.point_2d([1, 1]),
                    True, False, 4, 3,
                    math.radians(10)
                ],
                [-2.3039, 2.4273],
                round(math.radians(-44.5023), dec),
                round(math.radians(-348.8614), dec)
            ],
            [
                [
                    trig.point_2d([.5, .5]), trig.point_2d([1, 1]),
                    True, True, 4, 3,
                    math.radians(10)
                ],
                [3.8039, -.9273],
                round(math.radians(146.636), dec),
                round(math.radians(348.8614), dec)
            ],
            [
                [
                    trig.point_2d([0, 0]), trig.point_2d([1.2, 0.6]),
                    False, True, 3, 3,
                    math.radians(0)
                ],
                [-0.7077, 2.9153],
                round(math.radians(-76.355915), dec), # start angle
                round(math.radians(25.841933), dec), # start angle
            ],
        ]
        
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.elliptical_arc_endpoint_to_center(i[0], i[1], i[2], i[3], i[4], i[5], i[6], decimals=dec)
                self.assertCountEqual(out[0].reshape(2).tolist(), t[1])
                self.assertEqual(out[1], t[2])
                self.assertEqual(out[2], t[3])
    
    def test_circle_arc_endpoint_to_center(self):
        dec = 4
        # [3.567357, -2.067357]
        tests = [
            [[trig.point_2d([.5, .5]), trig.point_2d([1, 1]), False, False, 4], [round(3.567357, dec), round(-2.067357, dec)], round(math.radians(140.070897), dec), round(math.radians(-10.141793), dec)],
            #[[trig.point_2d([.5, .5]), trig.point_2d([1, 1]), False, True, 4], [round(3.567357, dec), round(-2.067357, dec)], round(math.radians(140.070897), dec), round(math.radians(-10.141793), dec)],
            #[[trig.point_2d([.5, .5]), trig.point_2d([1, 1]), True, False, 4], [round(3.567357, dec), round(-2.067357, dec)], round(math.radians(140.070897), dec), round(math.radians(-10.141793), dec)],
            #[[trig.point_2d([.5, .5]), trig.point_2d([1, 1]), True, True, 4], [round(3.567357, dec), round(-2.067357, dec)], round(math.radians(140.070897), dec), round(math.radians(-10.141793), dec)],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.circle_arc_endpoint_to_center(i[0], i[1], i[2], i[3], i[4], dec)
                self.assertCountEqual(out[0].reshape(2).tolist(), t[1])
                self.assertEqual(out[1], t[2])
                self.assertEqual(out[2], t[3])
    
    def test_elliptical_arc_center_to_endpoint(self):
        dec = 5
        tests = [
            [[trig.point_2d([3.80397, -.92726]), 4, 3, math.radians(10), round(math.radians(146.63598), 6), round(math.radians(-11.13865), 6)], [0.5, 0.5], [1, 1], False, False]
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.elliptical_arc_center_to_endpoint(i[0], i[1], i[2], i[3], i[4], i[5], dec)
                self.assertAlmostEqual(out[0].reshape(2).tolist()[0], t[1][0],3)
                self.assertAlmostEqual(out[0].reshape(2).tolist()[1], t[1][1],3)
                self.assertAlmostEqual(out[1].reshape(2).tolist()[0], t[2][0],3)
                self.assertAlmostEqual(out[1].reshape(2).tolist()[1], t[2][1],3)
                self.assertEqual(out[2], t[3])
                self.assertEqual(out[3], t[4])
    
    def test_circle_arc_center_to_endpoint(self):
        dec = 5
        tests = [
            [[trig.point_2d([round(3.567357, dec), round(-2.067357, dec)]), 4, round(math.radians(140.070897), dec), round(math.radians(-10.141793), dec)], [0.5, 0.5], [1, 1], False, False],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.circle_arc_center_to_endpoint(i[0], i[1], i[2], i[3], dec)
                self.assertAlmostEqual(out[0].reshape(2).tolist()[0], t[1][0],3)
                self.assertAlmostEqual(out[0].reshape(2).tolist()[1], t[1][1],3)
                self.assertAlmostEqual(out[1].reshape(2).tolist()[0], t[2][0],3)
                self.assertAlmostEqual(out[1].reshape(2).tolist()[1], t[2][1],3)
                self.assertEqual(out[2], t[3])
                self.assertEqual(out[3], t[4])
    
    def test_line_fit_box(self):
        tests = [
            [
                [trig.point_2d([0,0]), trig.point_2d([1,1])],
                [[0,0], [1,1]]
            ],
            [
                [trig.point_2d([0,0]), trig.point_2d([-1,-1])],
                [[-1,-1], [0,0]]
            ],
            [
                [trig.point_2d([0,1]), trig.point_2d([1,0])],
                [[0,0], [1,1]]
            ],
            [
                [trig.point_2d([-0.1,1.1]), trig.point_2d([1.1,-0.1])],
                [[-0.1,-0.1], [1.1,1.1]]
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.line_fit_box(i[0], i[1])
                out_list = [out[0].reshape(2).tolist(),
                            out[1].reshape(2).tolist()]
                self.assertCountEqual(out_list, t[1])
    
    def test_circle_fit_box(self):
        tests = [
            [
                [trig.point_2d([0,0]), 1],
                [[-1,-1], [1,1]]
            ],
            [
                [trig.point_2d([1,1]), 1],
                [[0,0], [2,2]]
            ],
            [
                [trig.point_2d([-1,-1]), 1],
                [[-2,-2], [0,0]]
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.circle_fit_box(i[0], i[1])
                out_list = [out[0].reshape(2).tolist(),
                            out[1].reshape(2).tolist()]
                self.assertCountEqual(out_list, t[1])
    
    def test_ellipse_fit_box(self):
        tests = [
            [
                [trig.point_2d([0,0]), 1, 0.5, math.radians(0)],
                [[-1,-.5], [1,.5]]
            ],
            [
                [trig.point_2d([0,0]), 1, 0.5, math.radians(20)],
                [[-0.955127,-0.581148], [0.955127,0.581148]]
            ],
            [
                [trig.point_2d([1,1]), 1, 0.5, math.radians(20)],
                [[round(-0.955127+1,6),round(-0.581148+1,6)], [round(0.955127+1,6),round(0.581148+1,6)]]
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.ellipse_fit_box(i[0], i[1], i[2], i[3])
                out_list = [out[0].reshape(2).tolist(),
                            out[1].reshape(2).tolist()]
                out_list = [[round(out_list[0][0],6), round(out_list[0][1],6)],
                            [round(out_list[1][0],6), round(out_list[1][1],6)]]
                self.assertCountEqual(out_list, t[1])
    
    def test_elliptical_arc_fit_box(self):
        # Base Ellipses
        e0 = [trig.point_2d([0,0]), 4, 3, math.radians(30)]
        tests = [
            [
                [e0[0], e0[1], e0[2], e0[3], math.radians(15), math.radians(20)],
                [[1.508462, 2.757504], [2.757506, 3.234904]]
            ],
            [
                [e0[0], e0[1], e0[2], e0[3], math.radians(15), math.radians(60)],
                [[-.788091, 2.757504], [2.757506, 3.278719]]
            ],
            [
                [e0[0], e0[1], e0[2], e0[3], math.radians(-25), math.radians(345)],
                [[-3.774917, -3.278719], [3.774917, 3.278719]]
            ],
            [
                [e0[0], e0[1], e0[2], e0[3], math.radians(-5), math.radians(-25)],
                [[3.614569, 0.000002], [3.774917, 1.685502]] # Manually set to .000002 since the accuracy for a fit box doesn't need to be that close
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
            out = trig.elliptical_arc_fit_box(i[0], i[1], i[2], i[3], i[4], i[5])
            out_list = [out[0].reshape(2).tolist(),
                        out[1].reshape(2).tolist()]
            out_list = [[round(out_list[0][0],6), round(out_list[0][1],6)],
                        [round(out_list[1][0],6), round(out_list[1][1],6)]]
            self.assertCountEqual(out_list, t[1])
    
    def test_multi_fit_box(self):
        tests = [
            [ # Test 1 - line, circular arc, elliptical arc, circle
                [ # Input geometry
                    sp.line("path1", 0, [1.0, 1.0], [3.0, 3.0]),
                    sp.circular_arc("path1", 0, [0, 0], [1.2, 0.6],
                                    3, False, True),
                    sp.elliptical_arc("path1", 0, [0, 0], [4, 3],
                                      4, 3, 0, False, True),
                    sp.circle("circle1", 1.5, [0,0]),
                ],
                [[-1.5, -1.5], [4.0, 3.0]],
            ],
        ]
        for t in tests:
            with self.subTest(t=t):
                i = t[0]
                out = trig.multi_fit_box(i)
                check = [trig.pt2list(out[0]), trig.pt2list(out[1])]
                self.assertCountEqual(check, t[1])

class TestVectors(unittest.TestCase):
    
    def test_get_unit_vector(self):
        tests = [
            (np.array((0, 0, 0)), np.array((0, 0, 0))),
            (np.array((1, 0, 0)), np.array((1, 0, 0))),
            (np.array((0, 1, 0)), np.array((0, 1, 0))),
            (np.array((0, 0, 1)), np.array((0, 0, 1))),
            (np.array((0, 0)), np.array((0, 0))),
            (np.array((1, 0)), np.array((1, 0))),
            (np.array((0, 1)), np.array((0, 1))),
            (np.array((0, 0, 0)).reshape(3,1), np.array((0, 0, 0)).reshape(3,1)),
            (np.array((1, 0, 0)).reshape(3,1), np.array((1, 0, 0)).reshape(3,1)),
            (np.array((0, 1, 0)).reshape(3,1), np.array((0, 1, 0)).reshape(3,1)),
            (np.array((0, 0, 1)).reshape(3,1), np.array((0, 0, 1)).reshape(3,1)),
            (np.array((0, 0)).reshape(2,1), np.array((0, 0)).reshape(2,1)),
            (np.array((1, 0)).reshape(2,1), np.array((1, 0)).reshape(2,1)),
            (np.array((0, 1)).reshape(2,1), np.array((0, 1)).reshape(2,1)),
        ]
        for vector, unit_vector in tests:
            with self.subTest(vector=vector, unit_vector=unit_vector):
                result = trig.get_unit_vector(vector)
                self.assertCountEqual(result, unit_vector)
                self.assertCountEqual(result.shape, unit_vector.shape)
    
    def test_get_unit_vector_exceptions(self):
        tests = [
            np.array([[1,1],[1,1]]),
        ]
        for vector in tests:
            with self.subTest(vector=vector):
                with self.assertRaises(ValueError):
                    result = trig.get_unit_vector(vector)

class TestVectorUtilities(unittest.TestCase):
    
    def test_is_iterable(self):
        tests = [
            ([0, 1], True),
            ((0, 1), True),
            (1, False),
            (1.0, False),
            (True, False),
            (ValueError, False),
            ("fake", True),
            (np.array([0, 1]), True),
        ]
        for value, expected_bool in tests:
            with self.subTest(value=value, expected_bool=expected_bool):
                self.assertEqual(trig.is_iterable(value), expected_bool)
    
    def test_to_1D_tuple(self):
        tests = [
            # 2D Tests #
            ([0, 1], (0, 1)),
            ((0, 1), (0, 1)),
            (np.array([0, 1]), (0.0, 1.0)),
            (np.array([0, 1]).reshape(2,1), (0.0, 1.0)),
            # 3D Tests #
            ([0, 1, 2], (0, 1, 2)),
            ((0, 1, 2), (0, 1, 2)),
            (np.array([0, 1, 2]), (0.0, 1.0, 2.0)),
            (np.array([0, 1, 2]).reshape(3,1), (0.0, 1.0, 2.0)),
        ]
        for value, expected_tuple in tests:
            with self.subTest(value=value, expected_tuple=expected_tuple):
                self.assertCountEqual(trig.to_1D_tuple(value), expected_tuple)
                self.assertEqual(str(trig.to_1D_tuple(value)), str(expected_tuple))
    
    def test_to_1D_numpy(self):
        tests = [
            # 2D Tests #
            ([0, 1], np.array((0, 1))),
            ((0, 1), np.array((0, 1))),
            (np.array([0, 1]), np.array((0, 1))),
            (np.array([0, 1]).reshape(2,1), np.array((0, 1))),
            # 3D Tests #
            ([0, 1, 2], np.array((0, 1, 2))),
            ((0, 1, 2), np.array((0, 1, 2))),
            (np.array([0, 1, 2]), np.array((0, 1, 2))),
            (np.array([0, 1, 2]).reshape(3,1), np.array((0, 1, 2))),
        ]
        for value, expected_tuple in tests:
            with self.subTest(value=value, expected_tuple=expected_tuple):
                self.assertCountEqual(trig.to_1D_np(value), expected_tuple)
                self.assertEqual(str(trig.to_1D_np(value)), str(expected_tuple))
    
    def test_is_clockwise_2d(self):
        v1 = (1, 0)
        v2 = (0, 1)
        self.assertFalse(trig.is_clockwise(v1, v2))
        self.assertTrue(trig.is_clockwise(v2, v1))
    
    def test__get_angle_between_2d_vectors_tau(self):
        v1 = (1, 0)
        for phi in range(0, 360, 45):
            v2 = trig.polar_to_cartesian((1, radians(phi)))
            with self.subTest(vector1=v1, vector2=v2,
                              phi=f"R: {radians(phi)}, D: {phi}"):
                angle = trig.get_vector_angle(v1, v2, convention=AC.PLUS_TAU)
                self.assertAlmostEqual(angle, radians(phi))
    
    def test__get_angle_between_2d_vectors_2pi_explementary(self):
        v1 = (1, 0)
        for phi in range(0, 360, 45):
            v2 = trig.polar_to_cartesian((1, radians(phi)))
            with self.subTest(vector1=v1, vector2=v2,
                              phi=f"R: {radians(phi)}, D: {phi}"):
                angle = trig.get_vector_angle(
                    v1, v2, opposite=True, convention=AC.PLUS_TAU
                )
                self.assertAlmostEqual(angle, math.tau-radians(phi))
    
    def test__get_angle_between_3d_vectors_pi(self):
        theta = 90
        v1 = trig.spherical_to_cartesian((1, 0, radians(theta)))
        for phi in range(0, 180+1, 45):
            v2 = trig.spherical_to_cartesian((1, radians(phi), radians(theta)))
            angle = trig.get_vector_angle(v1, v2)
            self.assertAlmostEqual(angle, radians(phi))

class TestRotation(unittest.TestCase):
    
    def setUp(self):
        self.t = radians(45)
        self.cost = math.cos(self.t)
        self.sint = math.sin(self.t)
    
    def test_x(self):
        matrix = trig.rotation(self.t, (1, 0, 0))
        expected = [
            [1, 0, 0],
            [0, self.cost, -self.sint],
            [0, self.sint, self.cost],
        ]
        self.assertTrue(
            np.allclose(matrix, np.array(expected))
        )
    
    def test_y(self):
        matrix = trig.rotation(self.t, (0, 1, 0))
        expected = [
            [self.cost, 0, self.sint],
            [0, 1, 0],
            [-self.sint, 0, self.cost],
        ]
        self.assertTrue(
            np.allclose(matrix, np.array(expected))
        )
    
    def test_z(self):
        matrix = trig.rotation(self.t, (0, 0, 1))
        expected = [
            [self.cost, -self.sint, 0],
            [self.sint, self.cost, 0],
            [0, 0, 1],
        ]
        self.assertTrue(
            np.allclose(matrix, np.array(expected))
        )
    
    def test_2(self):
        matrix = trig.rotation(self.t, "2")
        expected = [
            [self.cost, -self.sint],
            [self.sint, self.cost],
        ]
        self.assertTrue(
            np.allclose(matrix, np.array(expected))
        )
    
    def test_arbitrary_negative_z(self):
        matrix = trig.rotation(self.t, (0, 0, -1))
        expected = trig.rotation(-self.t, (0, 0, 1))
        self.assertTrue(
            np.allclose(matrix, np.array(expected))
        )
    
    def test_multi_rotation(self):
        matrix = trig.multi_rotation("xyz", 0, 0, radians(90))
        expected = trig.rotation_z(radians(90))
        self.assertTrue(np.allclose(matrix, expected))

if __name__ == "__main__":
    with open("tests/logs/"
              + Path(sys.modules[__name__].__file__).stem
              +".log", "w") as f:
        f.write("finished")
    unittest.main()