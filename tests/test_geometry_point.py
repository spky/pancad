import sys
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
import os
import math

import numpy as np

sys.path.append('src')

from PanCAD.geometry.point import Point

class TestPointInit(unittest.TestCase):
    
    def setUp(self):
        self.coordinate1 = (1, 1, 1)
        self.coordinates = coordinates = [
            (0, 0, 0),
            (1, 1, 1),
            (1, 1),
        ]
    
    def test_point_init_no_arg(self):
        pt = Point()
    
    def test_point_init_tuple(self):
        for coordinate in self.coordinates:
            with self.subTest(coordinate=coordinate):
                pt = Point(coordinate)
                self.assertCountEqual(coordinate, pt.position)
    
    def test_point_tuple_iter(self):
        for coordinate in self.coordinates:
            with self.subTest(coordinate=coordinate):
                pt = Point(coordinate)
                self.assertCountEqual(tuple(pt), pt.position)
    
    def test_point_numpy_array(self):
        pt = Point(self.coordinate1)
        self.assertCountEqual(np.array(pt), np.array(self.coordinate1))
    
    def test_str_dunder(self):
        pt = Point(self.coordinate1)
        self.assertEqual(str(pt), "PanCAD Point at position (1, 1, 1)")
    
    def test_vector(self):
        pass

class TestPointPropertiesFunctions(unittest.TestCase):
    
    def setUp(self):
        self.pt = Point()
        self.coordinates = [
            ((0, 0, 0), 0, math.nan, math.nan),
            ((1, 1, 0), math.sqrt(2), math.radians(45), math.radians(90)),
            ((-1, 1, 0), math.sqrt(2), math.radians(135), math.radians(90)),
            ((-1, -1, 0), math.sqrt(2), -math.radians(135), math.radians(90)),
            ((1, -1, 0), math.sqrt(2), -math.radians(45), math.radians(90)),
            ((1, 0, 0), 1, math.radians(0), math.radians(90)), 
            ((0, 1, 0), 1, math.radians(90), math.radians(90)), 
            ((-1, 0, 0), 1, math.radians(180), math.radians(90)), 
            ((0, -1, 0), 1, -math.radians(90), math.radians(90)),
            ((1, 1, 1), math.sqrt(3), math.radians(45), math.atan(math.hypot(1,1)/1)),
            ((1, 1, -1), math.sqrt(3), math.radians(45), math.pi + math.atan(math.hypot(1,1)/-1)),
            ((0, 0, 1), math.sqrt(1), math.nan, math.atan(math.hypot(0,0)/1)),
            ((0, 0, -1), math.sqrt(1), math.nan, math.pi + math.atan(math.hypot(0,0)/-1)),
        ]
        
        self.coordinates2d = []
        for coordinate in self.coordinates:
            self.coordinates2d.append(
                (coordinate[0][:2],
                 math.hypot(coordinate[0][0], coordinate[0][1]),
                 coordinate[2])
            )
        self.coordinates_polar = []
        for coordinate in self.coordinates2d:
            self.coordinates_polar.append(
                (
                    (self.coordinates2d[1], self.coordinates2d[2]),
                    self.coordinates2d[0]
                )
            )
        self.coordinates_spherical = []
        for coordinate in self.coordinates:
            self.coordinates_spherical.append(
                ((coordinate[1], coordinate[2], coordinate[3]), coordinate[0])
            )
        
    def test_position_setter(self):
        for coordinate, *_ in self.coordinates:
            with self.subTest(coordinate = coordinate):
                self.pt.position = coordinate
                self.assertCountEqual(self.pt.position, coordinate)
    
    def test_xy_getters(self):
        for coordinate, *_ in self.coordinates2d:
            with self.subTest(coordinate = coordinate):
                self.pt.position = coordinate
                xy = (self.pt.x, self.pt.y)
                self.assertCountEqual(xy, coordinate)
    
    def test_xyz_getters(self):
        for coordinate, *_ in self.coordinates:
            with self.subTest(coordinate = coordinate):
                self.pt.position = coordinate
                xyz = (self.pt.x, self.pt.y, self.pt.z)
                self.assertCountEqual(xyz, coordinate)
    
    def test_r_getter(self):
        for coordinate, expected_r, *_ in self.coordinates:
            with self.subTest(test=[coordinate, expected_r]):
                self.pt.position = coordinate
                self.assertEqual(self.pt.r, expected_r)
    
    def test_phi_getter(self):
        for coordinate, _, expected_phi in self.coordinates2d:
            with self.subTest(test=[
                    coordinate,
                    f"{math.degrees(expected_phi)}°, {expected_phi} radians"
                ]):
                self.pt.position = coordinate
                if coordinate == (0, 0):
                    self.assertTrue(math.isnan(self.pt.phi))
                else:
                    self.assertEqual(self.pt.phi, expected_phi)
    
    def test_theta_getter(self):
        for coordinate, _, _, expected_theta in self.coordinates:
            with self.subTest(test=[
                    coordinate,
                    f"{math.degrees(expected_theta)}°, {expected_theta} radians"
                ]):
                self.pt.position = coordinate
                if coordinate == (0, 0, 0):
                    self.assertTrue(math.isnan(self.pt.theta))
                else:
                    self.assertEqual(self.pt.theta, expected_theta)
    
    def test_polar_getter(self):
        for coordinate, expected_r, expected_phi, *_ in self.coordinates2d:
            with self.subTest(test=[
                    coordinate,
                    expected_r,
                    f"{math.degrees(expected_phi)}°, {expected_phi} radians"
                ]):
                self.pt.position = coordinate
                if coordinate == (0, 0):
                    self.assertTrue(math.isnan(self.pt.phi))
                    self.assertEqual(self.pt.r, expected_r)
                else:
                    self.assertEqual(self.pt.polar, (expected_r, expected_phi))
    
    def test_spherical_getter(self):
        for (coordinate, expected_r,
             expected_phi, expected_theta) in self.coordinates:
            with self.subTest(test=[
                    coordinate,
                    expected_r,
                    f"{math.degrees(expected_phi)}°, {expected_phi} radians",
                    f"{math.degrees(expected_theta)}°, {expected_theta} radians"
                ]):
                self.pt.position = coordinate
                if coordinate == (0, 0, 0):
                    self.assertTrue(math.isnan(self.pt.phi))
                    self.assertTrue(math.isnan(self.pt.theta))
                    self.assertEqual(self.pt.r, expected_r)
                elif coordinate[:2] == (0, 0):
                    self.assertTrue(math.isnan(self.pt.phi))
                    self.assertEqual(
                        (self.pt.spherical[0], None, self.pt.spherical[2]),
                        (expected_r, None, expected_theta)
                    )
                else:
                    self.assertEqual(
                        self.pt.spherical,
                        (expected_r, expected_phi, expected_theta)
                    )
    
    def test_xy_setters(self):
        new_coordinate = (1, 2)
        self.pt.position = (0, 0)
        self.pt.x, self.pt.y = new_coordinate[0], new_coordinate[1]
        self.assertCountEqual(self.pt.position, new_coordinate)
    
    def test_xyz_setters(self):
        new_coordinate = (1, 2, 3)
        self.pt.position = (0, 0)
        self.pt.x = new_coordinate[0]
        self.pt.y = new_coordinate[1]
        self.pt.z = new_coordinate[2]
        self.assertCountEqual(self.pt.position, new_coordinate)
    
    def test_vector(self):
        tests = []
        HORIZONTAL, VERTICAL = False, True
        for coordinate, *_ in self.coordinates: 
            tests.append(
                (coordinate,
                 HORIZONTAL,
                 np.array(coordinate))
            )
            tests.append(
                (coordinate,
                 VERTICAL,
                 np.array(coordinate).reshape(len(coordinate), 1))
            )
        
        for coordinate, orientation, expected in tests:
            with self.subTest(test = [coordinate, orientation, expected]):
                self.pt.position = coordinate
                self.assertTrue(
                    self.pt.vector(orientation).shape == expected.shape
                )
    
    # def test_polar_setter(self):
        # for polar_coordinate, xy_coordinate in self.coordinates_polar:
            # with self.subTest(test=[polar_coordinate, xy_coordinate]):
                # self.pt.polar


if __name__ == "__main__":
    with open("tests/logs/" + Path(sys.modules[__name__].__file__).stem
              +".log", "w") as f:
        f.write("finished")
    unittest.main()