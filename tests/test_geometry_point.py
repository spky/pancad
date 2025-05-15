import unittest
import math

import numpy as np

from PanCAD.geometry import Point
from PanCAD.utils import verification

ROUNDING_PLACES = 10

class TestPointInit(unittest.TestCase):
    """Tests whether Point successfully initializes when expected to"""
    def setUp(self):
        self.coordinate1 = (1, 1, 1)
        self.coordinates = coordinates = [
            (0, 0, 0),
            (1, 1, 1),
            (1, 1),
        ]
        self.np_coordinates = [(np.array(c), c) for c in self.coordinates]
        self.np_coordinates.extend(
            [(np.array(c).reshape(-1,1), c) for c in self.coordinates]
        )
        for i, (numpy_coordinate, expected) in enumerate(self.np_coordinates):
            # Convert expected coordinates to float
            self.np_coordinates[i] = (
                numpy_coordinate, tuple([float(c) for c in expected])
            )
    
    def test_point_init_no_arg(self):
        pt = Point()
    
    def test_point_init_tuple(self):
        for coordinate in self.coordinates:
            with self.subTest(coordinate=coordinate):
                pt = Point(coordinate)
                self.assertCountEqual(coordinate, pt.cartesian)
    
    def test_point_init_numpy(self):
        for np_coordinate, expected_cartesian in self.np_coordinates:
            with self.subTest(numpy_coordinate=np_coordinate,
                              expected_cartesian=expected_cartesian):
                pt = Point(np_coordinate)
                self.assertCountEqual(pt.cartesian, expected_cartesian)
                self.assertEqual(str(pt.cartesian), str(expected_cartesian))
    
    def test_point_init_xyz(self):
        for coordinate in self.coordinates:
            with self.subTest(coordinate=coordinate):
                if len(coordinate) == 2:
                    x, y = coordinate
                    pt = Point(x, y)
                else:
                    x, y, z = coordinate
                    pt = Point(x, y, z)
                self.assertEqual(pt.cartesian, coordinate)
    
    def test_point_tuple_iter(self):
        for coordinate in self.coordinates:
            with self.subTest(coordinate=coordinate):
                pt = Point(coordinate)
                self.assertCountEqual(tuple(pt), pt.cartesian)
    
    def test_point_numpy_array(self):
        pt = Point(self.coordinate1)
        self.assertCountEqual(np.array(pt), np.array(self.coordinate1))
    
    def test_point_str_dunder(self):
        pt = Point(self.coordinate1)
        self.assertEqual(str(pt), "PanCAD Point at cartesian (1, 1, 1)")
    
    def test_point_len_dunder(self):
        tests = [
            ((0, 0, 0), 3),
            ((0, 0), 2),
        ]
        for coordinate, expected_length in tests:
            with self.subTest(coordinate=coordinate,
                              expected_length=expected_length):
                pt = Point(coordinate)
                self.assertEqual(len(pt), expected_length)
    
    def test_from_polar(self):
        tests = [
            (1, 0),
            (1, 45),
        ]
        tests = [(r, math.radians(phi)) for r, phi in tests]
        
        for r, phi in tests:
            with self.subTest(r=r, phi=(f"Degrees: {math.degrees(phi)} "
                                        f"Radians: {phi}")):
                verification.assertTupleAlmostEqual(
                    self, Point.from_polar((r, phi)).polar, (r, phi),
                    ROUNDING_PLACES
                )
                verification.assertTupleAlmostEqual(
                    self, Point.from_polar(r, phi).polar, (r, phi),
                    ROUNDING_PLACES
                )
    
    def test_from_spherical(self):
        tests = [
            (1, math.nan, 0),
            (1, 45, 90),
        ]
        tests = [(r, math.radians(phi), math.radians(theta))
                 for r, phi, theta in tests]
        
        for r, phi, theta in tests:
            with self.subTest(r=r,
                              phi=(f"Degrees: {math.degrees(phi)} "
                                   f"Radians: {phi}"),
                              theta=(f"Degrees: {math.degrees(theta)} "
                                     f"Radians: {theta}")):
                spherical = (r, phi, theta)
                verification.assertTupleAlmostEqual(
                    self, Point.from_spherical(spherical).spherical, spherical,
                    ROUNDING_PLACES
                )
                verification.assertTupleAlmostEqual(
                    self, Point.from_spherical(r, phi, theta).spherical,
                    spherical,
                    ROUNDING_PLACES
                )

class TestPointCartesianToPolarSphericalConversions(unittest.TestCase):
    """Tests the Point for whether it correctly converts cartesian coordinates to 
    and from polar/spherical coordinates"""
    def setUp(self):
        self.pt = Point()
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
        
        
    def test_cartesian_setter(self):
        for coordinate, *_ in self.coordinates:
            with self.subTest(coordinate = coordinate):
                self.pt.cartesian = coordinate
                self.assertCountEqual(self.pt.cartesian, coordinate)
    
    def test_2D_cartesian_getters(self):
        for coordinate, *_ in self.coordinates2d:
            with self.subTest(coordinate = coordinate):
                self.pt.cartesian = coordinate
                xy = (self.pt.x, self.pt.y)
                self.assertCountEqual(xy, coordinate)
    
    def test_3D_cartesian_getters(self):
        for coordinate, *_ in self.coordinates:
            with self.subTest(coordinate = coordinate):
                self.pt.cartesian = coordinate
                xyz = (self.pt.x, self.pt.y, self.pt.z)
                self.assertCountEqual(xyz, coordinate)
    
    def test_r_getter(self):
        for coordinate, expected_r, *_ in self.coordinates:
            with self.subTest(test=[coordinate, expected_r]):
                self.pt.cartesian = coordinate
                self.assertEqual(self.pt.r, expected_r)
    
    def test_phi_getter(self):
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
    
    def test_theta_getter(self):
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
    
    def test_polar_getter(self):
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
                        (expected_r, expected_phi, expected_theta)
                    )
    
    def test_2D_cartesian_setters(self):
        new_coordinate = (1, 2)
        self.pt.cartesian = (0, 0)
        self.pt.x, self.pt.y = new_coordinate[0], new_coordinate[1]
        self.assertCountEqual(self.pt.cartesian, new_coordinate)
    
    def test_3D_cartesian_setters(self):
        new_coordinate = (1, 2, 3)
        self.pt.cartesian = (0, 0)
        self.pt.x = new_coordinate[0]
        self.pt.y = new_coordinate[1]
        self.pt.z = new_coordinate[2]
        self.assertCountEqual(self.pt.cartesian, new_coordinate)
    
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
                self.pt.cartesian = coordinate
                self.assertTrue(
                    self.pt.vector(orientation).shape == expected.shape
                )
    
    def test_polar_setter(self):
        for polar_coordinate, xy_coordinate in self.coordinates_polar:
            with self.subTest(test=[polar_coordinate, xy_coordinate]):
                self.pt.polar = polar_coordinate
                verification.assertTupleAlmostEqual(
                    self,
                    self.pt.cartesian,
                    xy_coordinate,
                    self.default_places
                )
    
    def test_spherical_setter(self):
        for spherical_coordinate, xy_coordinate in self.coordinates_spherical:
            with self.subTest(test=[spherical_coordinate, xy_coordinate]):
                self.pt.spherical = spherical_coordinate
                verification.assertTupleAlmostEqual(
                    self,
                    self.pt.cartesian,
                    xy_coordinate,
                    self.default_places
                )

class TestRSetterSphericalEdgeCases(unittest.TestCase):
    """Tests whether the r setter in Point correctly updates the point's position 
    and identifies when it cannot with errors in spherical coordinates"""
    def setUp(self):
        self.pt = Point()
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
    
    def test_nominal_r_setter(self):
        for initial_spherical, r, expected_spherical in self.change_tests:
            if isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, r=r,
                                  expected_polar=expected_spherical):
                    self.pt.spherical = initial_spherical
                    self.pt.r = r
                    verification.assertTupleAlmostEqual(self, self.pt.spherical,
                                                        expected_spherical,
                                                        self.default_places)
    
    def test_exceptions_r_setter(self):
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
    def setUp(self):
        self.pt = Point()
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
    
    def test_nominal_r_setter(self):
        for initial_polar, r, expected_polar in self.change_tests:
            if isinstance(expected_polar, tuple):
                with self.subTest(initial_polar=initial_polar, r=r,
                                  expected_polar=expected_polar):
                    self.pt.polar = initial_polar
                    self.pt.r = r
                    verification.assertTupleAlmostEqual(self, self.pt.polar,
                                                        expected_polar,
                                                        self.default_places)
    
    def test_exceptions_r_setter(self):
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
    def setUp(self):
        self.pt = Point()
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
    
    def test_nominal_phi_setter(self):
        for initial_spherical, phi, expected_spherical in self.change_tests:
            if isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, phi=phi,
                                  expected_spherical=expected_spherical):
                    self.pt.spherical = initial_spherical
                    self.pt.phi = phi
                    verification.assertTupleAlmostEqual(self, self.pt.spherical,
                                                        expected_spherical,
                                                        self.default_places)
    
    def test_exceptions_phi_setter(self):
        for initial_spherical, phi, expected_spherical in self.change_tests:
            if not isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, phi=phi,
                                  expected_error_type=expected_spherical):
                    self.pt.spherical = initial_spherical
                    with self.assertRaises(expected_spherical):
                        self.pt.phi = phi

class TestPhiSetterpolarEdgeCases(unittest.TestCase):
    """Tests whether the phi setter in Point correctly updates the point's 
    position and identifies when it cannot with errors in polar coordinates"""
    def setUp(self):
        self.pt = Point()
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
    
    def test_nominal_phi_setter(self):
        for initial_polar, phi, expected_polar in self.change_tests:
            if isinstance(expected_polar, tuple):
                with self.subTest(initial_polar=initial_polar, phi=phi,
                                  expected_polar=expected_polar):
                    self.pt.polar = initial_polar
                    self.pt.phi = phi
                    verification.assertTupleAlmostEqual(self, self.pt.polar,
                                                        expected_polar,
                                                        self.default_places)
    
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
    def setUp(self):
        self.pt = Point()
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
    
    def test_nominal_theta_setter(self):
        for initial_spherical, theta, expected_spherical in self.change_tests:
            if isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, theta=theta,
                                  expected_spherical=expected_spherical):
                    self.pt.spherical = initial_spherical
                    self.pt.theta = theta
                    verification.assertTupleAlmostEqual(self, self.pt.spherical,
                                                        expected_spherical,
                                                        self.default_places)
    
    def test_exceptions_theta_setter(self):
        for initial_spherical, theta, expected_spherical in self.change_tests:
            if not isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, theta=theta,
                                  expected_error_type=expected_spherical):
                    self.pt.spherical = initial_spherical
                    with self.assertRaises(expected_spherical):
                        self.pt.theta = theta

class TestPointRichComparison(unittest.TestCase):
    
    def setUp(self):
        # Point A, Point B, expected equality result
        self.tests = [
            ((0, 0), (0, 0), True),
            ((1, 1), (0, 0), False),
            ((0, 0, 0), (0, 0, 0), True),
            ((1, 1, 1), (0, 0, 0), False),
            ((0, 0, 0), (0, 0), False),
        ]
    
    def test_point_equality(self):
        for point_a, point_b, expected_result in self.tests:
            with self.subTest(point_a=point_a, point_b=point_b,
                              expected_result=expected_result):
                pt_a, pt_b = Point(point_a), Point(point_b)
                self.assertEqual(pt_a == pt_b, expected_result)
    
    def test_point_inequality(self):
        for point_a, point_b, expected_equality in self.tests:
            expected_result = not expected_equality
            with self.subTest(point_a=point_a, point_b=point_b,
                              expected_result=expected_result):
                pt_a, pt_b = Point(point_a), Point(point_b)
                self.assertEqual(pt_a != pt_b, expected_result)

if __name__ == "__main__":
    unittest.main()