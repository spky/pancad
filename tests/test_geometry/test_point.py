"""Tests for the pancad Point class."""
from __future__ import annotations

import unittest
import math
from math import radians, nan
from typing import TYPE_CHECKING

import numpy as np
import pytest

from pancad.geometry.point import Point
from pancad.utils.pancad_types import PolarVector, SphericalVector

if TYPE_CHECKING:
    from pancad.utils.pancad_types import SpaceVector, Numpy1D, Space2DVector, Space3DVector

ROUNDING_PLACES = 10

@pytest.mark.parametrize("coordinate", [(0, 0, 0), (1, 1, 1), (1, 1)])
class TestPointInitialization:
    def test_point_tuple_init(self, coordinate: SpaceVector) -> None:
        """Tests Point can initialize with a tuple."""
        assert Point(coordinate).cartesian == coordinate

    def test_point_list_init(self, coordinate: SpaceVector) -> None:
        """Tests Point can initialize with a list."""
        assert Point(list(coordinate)).cartesian == coordinate

    def test_point_component_init(self, coordinate: SpaceVector) -> None:
        """Tests Point can initialize with individual components."""
        assert Point(*coordinate).cartesian == coordinate

    def test_point_numpy_init(self, coordinate: SpaceVector) -> None:
        """Tests Point can initialize with a numpy vector."""
        assert Point(np.array(coordinate, dtype=np.float64)).cartesian == coordinate

    def test_point_tuple_iter(self, coordinate: SpaceVector) -> None:
        """Test Point can be turned into a tuple of its components."""
        assert tuple(Point(coordinate)) == coordinate

    def test_point_numpy_array(self, coordinate: SpaceVector) -> None:
        """Test Point can be turned into a numpy array of its components."""
        np.testing.assert_array_equal(np.array(Point(coordinate)), coordinate)

    def test_point_len_dunder(self, coordinate: SpaceVector) -> None:
        """Test Point length matches the length of the vector used to initialize it."""
        assert len(Point(coordinate)) == len(coordinate)

    def test_point_str_dunder(self, coordinate: SpaceVector) -> None:
        """Test Point string dunder correctly reports the point location."""
        coord_str = ",".join(map(str, coordinate))
        assert str(Point(coordinate)) == f"<Point({coord_str})>"

@pytest.mark.parametrize("polar_coordinate", [(1, 0), (1, 45)])
class TestPolarPoint:
    """Tests for how Point handles being initialized by a polar vector."""

    def test_from_polar_tuple(self, polar_coordinate: Space2DVector) -> None:
        """Test that a point can initialize from a polar vector as a tuple."""
        radius, phi = polar_coordinate
        coordinate_radians = (radius, radians(phi))
        assert tuple(Point.from_polar(coordinate_radians).polar) == coordinate_radians

    def test_from_polar_components(self, polar_coordinate: Space2DVector) -> None:
        """Test that a point can initialize from a polar vector as individual components."""
        radius, phi = polar_coordinate
        coordinate_radians = (radius, radians(phi))
        assert Point.from_polar(*coordinate_radians).polar == coordinate_radians

@pytest.mark.parametrize("spherical_coordinate", [(1, nan, 0), (1, 45, 90)])
class TestSphericalPoint:
    """Tests for how Point handles being initialized by a spherical vector."""

    def test_from_spherical_tuple(self, spherical_coordinate: Space3DVector) -> None:
        """Test that a point can initialize from a spherical vector as a tuple."""
        radius, phi, theta = spherical_coordinate
        coordinate_radians = (radius, radians(phi), radians(theta))
        np.testing.assert_array_equal(tuple(Point.from_spherical(coordinate_radians).spherical),
                                      coordinate_radians)

    def test_from_spherical_components(self, spherical_coordinate: Space3DVector) -> None:
        """Test that a point can initialize from a spherical vector as individual components."""
        radius, phi, theta = spherical_coordinate
        coordinate_radians = (radius, radians(phi), radians(theta))
        np.testing.assert_array_equal(Point.from_spherical(*coordinate_radians).spherical,
                                      coordinate_radians)

class TestPointUpdate(unittest.TestCase):
    
    def test_update(self) -> None:
        pt = Point(0, 0, 0)
        new = Point(1, 1, 1)
        pt.update(new)
        np.testing.assert_allclose(pt.cartesian, new.cartesian)

class TestPointCartesianToPolarSphericalConversions(unittest.TestCase):
    """Tests the Point for whether it correctly converts cartesian coordinates to 
    and from polar/spherical coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)
        self.default_places = ROUNDING_PLACES
        
        # From Left to Right:
        # Cartesian Coordinate, Equivalent r, Equivalent phi, Equivalent theta
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
                    (coordinate[1], coordinate[2]),
                    (coordinate[0])
                )
            )
        self.coordinates_spherical = []
        for coordinate in self.coordinates:
            self.coordinates_spherical.append(
                ((coordinate[1], coordinate[2], coordinate[3]), coordinate[0])
            )
        
    def test_cartesian_setter(self) -> None:
        for coordinate, *_ in self.coordinates:
            with self.subTest(coordinate = coordinate):
                self.pt.cartesian = coordinate
                self.assertCountEqual(self.pt.cartesian, coordinate)
    
    def test_2D_cartesian_getters(self) -> None:
        for coordinate, *_ in self.coordinates2d:
            with self.subTest(coordinate = coordinate):
                self.pt.cartesian = coordinate
                xy = (self.pt.x, self.pt.y)
                self.assertCountEqual(xy, coordinate)
    
    def test_3D_cartesian_getters(self) -> None:
        for coordinate, *_ in self.coordinates:
            with self.subTest(coordinate = coordinate):
                self.pt.cartesian = coordinate
                xyz = (self.pt.x, self.pt.y, self.pt.z)
                self.assertCountEqual(xyz, coordinate)
    
    def test_r_getter(self) -> None:
        for coordinate, expected_r, *_ in self.coordinates:
            with self.subTest(test=[coordinate, expected_r]):
                self.pt.cartesian = coordinate
                self.assertEqual(self.pt.r, expected_r)
    
    def test_phi_getter(self) -> None:
        for coordinate, _, expected_phi in self.coordinates2d:
            with self.subTest(test=[
                    coordinate,
                    f"{math.degrees(expected_phi)}°, {expected_phi} radians"
                ]):
                self.pt.cartesian = coordinate
                if coordinate == (0, 0):
                    self.assertTrue(math.isnan(self.pt.phi))
                else:
                    self.assertEqual(self.pt.phi, expected_phi)
    
    def test_theta_getter(self) -> None:
        for coordinate, _, _, expected_theta in self.coordinates:
            with self.subTest(test=[
                    coordinate,
                    f"{math.degrees(expected_theta)}°, {expected_theta} radians"
                ]):
                self.pt.cartesian = coordinate
                if coordinate == (0, 0, 0):
                    self.assertTrue(math.isnan(self.pt.theta))
                else:
                    self.assertEqual(self.pt.theta, expected_theta)
    
    def test_polar_getter(self) -> None:
        for coordinate, expected_r, expected_phi, *_ in self.coordinates2d:
            with self.subTest(test=[
                    coordinate,
                    expected_r,
                    f"{math.degrees(expected_phi)}°, {expected_phi} radians"
                ]):
                self.pt.cartesian = coordinate
                if coordinate == (0, 0):
                    self.assertTrue(math.isnan(self.pt.phi))
                    self.assertEqual(self.pt.r, expected_r)
                else:
                    self.assertEqual(self.pt.polar, PolarVector(expected_r, expected_phi))
    
    def test_spherical_getter(self) -> None:
        for (coordinate, expected_r,
             expected_phi, expected_theta) in self.coordinates:
            with self.subTest(test=[
                    coordinate,
                    expected_r,
                    f"{math.degrees(expected_phi)}°, {expected_phi} radians",
                    f"{math.degrees(expected_theta)}°, {expected_theta} radians"
                ]):
                self.pt.cartesian = coordinate
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
                        SphericalVector(expected_r, expected_phi, expected_theta)
                    )
    
    def test_2D_cartesian_setters(self) -> None:
        new_coordinate = (1, 2)
        self.pt.cartesian = (0, 0)
        self.pt.x, self.pt.y = new_coordinate[0], new_coordinate[1]
        self.assertCountEqual(self.pt.cartesian, new_coordinate)
    
    def test_3D_cartesian_setters(self) -> None:
        new_coordinate = (1, 2, 3)
        self.pt.cartesian = (0, 0)
        self.pt.x = new_coordinate[0]
        self.pt.y = new_coordinate[1]
        self.pt.z = new_coordinate[2]
        self.assertCountEqual(self.pt.cartesian, new_coordinate)
    
    def test_vector(self) -> None:
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
                self.pt.cartesian = coordinate
                self.assertTrue(
                    self.pt.vector(orientation).shape == expected.shape
                )
    
    def test_polar_setter(self) -> None:
        for polar_coordinate, xy_coordinate in self.coordinates_polar:
            with self.subTest(test=[polar_coordinate, xy_coordinate]):
                self.pt.polar = polar_coordinate
                np.testing.assert_allclose(self.pt.cartesian, xy_coordinate, atol=1e-15)
    
    def test_spherical_setter(self) -> None:
        for spherical_coordinate, xy_coordinate in self.coordinates_spherical:
            with self.subTest(test=[spherical_coordinate, xy_coordinate]):
                self.pt.spherical = spherical_coordinate
                np.testing.assert_allclose(self.pt.cartesian, xy_coordinate, atol=1e-15)

class TestRSetterSphericalEdgeCases(unittest.TestCase):
    """Tests whether the r setter in Point correctly updates the point's position 
    and identifies when it cannot with errors in spherical coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)
        self.default_places = ROUNDING_PLACES
        
        # tests: initial spherical, new r, expected new spherical
        self.change_tests = [ 
            (
                (0, math.nan, math.nan), 0,
                (0, math.nan, math.nan)
            ),
            (
                (1, math.radians(45), math.radians(45)), 0,
                (0, math.nan, math.nan)
            ),
            (
                (1, math.radians(45), math.radians(45)), 2,
                (2, math.radians(45), math.radians(45)),
            ),
            (
                (1, math.radians(45), math.radians(45)), -1,
                ValueError
            ),
            (
                (0, math.nan, math.nan), 1,
                ValueError
            ),
            (
                (0, math.nan, math.nan), math.nan,
                ValueError
            ),
        ]
    
    def test_nominal_r_setter(self) -> None:
        for initial_spherical, r, expected_spherical in self.change_tests:
            if isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, r=r,
                                  expected_polar=expected_spherical):
                    self.pt.spherical = initial_spherical
                    self.pt.r = r
                    np.testing.assert_allclose(self.pt.spherical, expected_spherical, atol=1e-15)
    
    def test_exceptions_r_setter(self) -> None:
        for initial_spherical, r, expected_spherical in self.change_tests:
            if not isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, r=r,
                                  expected_error_type=expected_spherical):
                    self.pt.spherical = initial_spherical
                    with self.assertRaises(expected_spherical):
                        self.pt.r = r

class TestRSetterPolarEdgeCases(unittest.TestCase):
    """Tests whether the r setter in Point correctly updates the point's position 
    and identifies when it cannot with errors in polar coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)
        self.default_places = ROUNDING_PLACES
        
        # tests: initial spherical, new r, expected new spherical
        self.change_tests = [ 
            (
                (0, math.nan), 0,
                (0, math.nan)
            ),
            (
                (1, math.radians(45)), 0,
                (0, math.nan)
            ),
            (
                (1, math.radians(45)), 2,
                (2, math.radians(45)),
            ),
            (
                (1, math.radians(45)), -1,
                ValueError
            ),
            (
                (0, math.nan), 1,
                ValueError
            ),
            (
                (0, math.nan), math.nan,
                ValueError
            ),
        ]
    
    def test_nominal_r_setter(self) -> None:
        for initial_polar, r, expected_polar in self.change_tests:
            if isinstance(expected_polar, tuple):
                with self.subTest(initial_polar=initial_polar, r=r,
                                  expected_polar=expected_polar):
                    self.pt.polar = initial_polar
                    self.pt.r = r
                    np.testing.assert_allclose(self.pt.polar, expected_polar, atol=1e-15)
    
    def test_exceptions_r_setter(self) -> None:
        for initial_polar, r, expected_polar in self.change_tests:
            if not isinstance(expected_polar, tuple):
                with self.subTest(initial_polar=initial_polar, r=r,
                                  expected_error_type=expected_polar):
                    self.pt.polar = initial_polar
                    with self.assertRaises(expected_polar):
                        self.pt.r = r

class TestPhiSetterSphericalEdgeCases(unittest.TestCase):
    """Tests whether the phi setter in Point correctly updates the point's 
    position and identifies when it cannot with errors in spherical coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)
        self.default_places = ROUNDING_PLACES
        
        # tests: initial spherical, new r, expected new spherical
        self.change_tests = [ 
            (
                (0, math.nan, math.nan), math.nan,
                (0, math.nan, math.nan)
            ),
            (
                (1, math.radians(45), math.radians(45)), math.nan,
                ValueError
            ),
            (
                (1, math.radians(45), math.radians(135)), math.nan,
                ValueError
            ),
            (
                (1, math.radians(45), math.radians(45)), math.radians(0),
                (1, math.radians(0), math.radians(45)),
            ),
            (
                (0, math.nan, math.nan), 1,
                ValueError
            ),
        ]
    
    def test_nominal_phi_setter(self) -> None:
        for initial_spherical, phi, expected_spherical in self.change_tests:
            if isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, phi=phi,
                                  expected_spherical=expected_spherical):
                    self.pt.spherical = initial_spherical
                    self.pt.phi = phi
                    np.testing.assert_allclose(self.pt.spherical, expected_spherical, atol=1e-15)
    
    def test_exceptions_phi_setter(self):
        for initial_spherical, phi, expected_spherical in self.change_tests:
            if not isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, phi=phi,
                                  expected_error_type=expected_spherical):
                    self.pt.spherical = initial_spherical
                    with self.assertRaises(expected_spherical):
                        self.pt.phi = phi

class TestPhiSetterPolarEdgeCases(unittest.TestCase):
    """Tests whether the phi setter in Point correctly updates the point's 
    position and identifies when it cannot with errors in polar coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)
        self.default_places = ROUNDING_PLACES
        
        # tests: initial polar, new r, expected new polar
        self.change_tests = [ 
            (
                (0, math.nan), math.nan,
                (0, math.nan)
            ),
            (
                (1, math.radians(45)), math.nan,
                ValueError
            ),
            (
                (1, math.radians(45)), math.nan,
                ValueError
            ),
            (
                (1, math.radians(45)), math.radians(0),
                (1, math.radians(0)),
            ),
            (
                (0, math.nan), 1,
                ValueError
            ),
        ]
    
    def test_nominal_phi_setter(self) -> None:
        for initial_polar, phi, expected_polar in self.change_tests:
            if isinstance(expected_polar, tuple):
                with self.subTest(initial_polar=initial_polar, phi=phi,
                                  expected_polar=expected_polar):
                    self.pt.polar = initial_polar
                    self.pt.phi = phi
                    np.testing.assert_allclose(self.pt.polar, expected_polar, atol=1e-15)
    
    def test_exceptions_phi_setter(self):
        for initial_polar, phi, expected_polar in self.change_tests:
            if not isinstance(expected_polar, tuple):
                with self.subTest(initial_polar=initial_polar, phi=phi,
                                  expected_error_type=expected_polar):
                    self.pt.polar = initial_polar
                    with self.assertRaises(expected_polar):
                        self.pt.phi = phi

class TestThetaSetterSphericalEdgeCases(unittest.TestCase):
    """Tests whether the theta setter in Point correctly updates the point's 
    position and identifies when it cannot with errors in spherical coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)
        self.default_places = ROUNDING_PLACES
        
        # tests: initial spherical, new r, expected new spherical
        self.change_tests = [ 
            (
                (0, math.nan, math.nan), math.nan,
                (0, math.nan, math.nan)
            ),
            (
                (1, math.radians(45), math.radians(45)), math.nan,
                ValueError
            ),
            (
                (1, math.nan, math.radians(0)), math.radians(0),
                (1, math.nan, math.radians(0))
            ),
            (
                (1, math.nan, math.pi), math.pi,
                (1, math.nan, math.pi)
            ),
            (
                (1, math.radians(45), math.radians(45)), math.radians(90),
                (1, math.radians(45), math.radians(90)),
            ),
            (
                (0, math.nan, math.nan), 1,
                ValueError
            ),
        ]
    
    def test_nominal_theta_setter(self) -> None:
        for initial_spherical, theta, expected_spherical in self.change_tests:
            if isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, theta=theta,
                                  expected_spherical=expected_spherical):
                    self.pt.spherical = initial_spherical
                    self.pt.theta = theta
                    np.testing.assert_allclose(self.pt.spherical, expected_spherical, atol=1e-15)
    
    def test_exceptions_theta_setter(self) -> None:
        for initial_spherical, theta, expected_spherical in self.change_tests:
            if not isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, theta=theta,
                                  expected_error_type=expected_spherical):
                    self.pt.spherical = initial_spherical
                    with self.assertRaises(expected_spherical):
                        self.pt.theta = theta

class TestPointNumericDunders(unittest.TestCase):
    def setUp(self) -> None:
        self.coordinates = [
            [(0, 0), (0, 0)],
            [(1, 1), (0, 0)],
            [(0, 0, 0), (0, 0, 0)],
            [(1, 1, 1), (0, 0, 0)],
            [(0, 0, 0), (0, 0)],
            [(0, 0, 0), (1.2, 2.3, 1.2)],
        ]
    
    def test_add(self) -> None:
        coords = list(filter(lambda x: len(x[0]) == len(x[1]), self.coordinates))
        results = map(
            lambda x : tuple(map(lambda x: x.item(), np.array(x[0]) + np.array(x[1]))),
            coords
        )
        pts = [[Point(a), Point(b)] for a, b in coords]
        for (pt1, pt2), result in zip(pts, results):
            with self.subTest(point1=pt1, point2=pt2, result=result):
                np.testing.assert_allclose(pt1 + pt2, result, atol=1e-15)
                self.assertEqual(str(pt1+pt2), str(result))    
    
    def test_sub(self) -> None:
        coords = list(filter(lambda x: len(x[0]) == len(x[1]), self.coordinates))
        results = map(
            lambda x : tuple(map(lambda x: x.item(), np.array(x[0]) - np.array(x[1]))),
            coords
        )
        pts = [[Point(a), Point(b)] for a, b in coords]
        for (pt1, pt2), result in zip(pts, results):
            with self.subTest(point1=pt1, point2=pt2, result=result):
                np.testing.assert_allclose(pt1 - pt2, result, atol=1e-15)
                self.assertEqual(str(pt1-pt2), str(result))
        

if __name__ == "__main__":
    unittest.main()