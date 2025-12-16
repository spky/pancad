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
    
    def test_to_1d_tuple(self):
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
                self.assertCountEqual(trig.to_1d_tuple(value), expected_tuple)
                self.assertEqual(str(trig.to_1d_tuple(value)), str(expected_tuple))
    
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
                self.assertCountEqual(trig.to_1d_np(value), expected_tuple)
                self.assertEqual(str(trig.to_1d_np(value)), str(expected_tuple))
    
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