import itertools
import math
import os
import unittest

from PanCAD.geometry import Point, Line, LineSegment, Plane, spatial_relations
from PanCAD.utils import verification

ROUNDING_PLACES = 10

class TestCoincidentSingles(unittest.TestCase):
    
    def test_generic_error(self):
        with self.assertRaises(NotImplementedError):
            spatial_relations.coincident(1, 1)
    
    def test_point_point(self):
        coordinates = [(0, 0), (1, 1)]
        pairs = list(itertools.product(coordinates, repeat=2))
        truths = map(lambda x : x[0] == x[1], pairs)
        points = [map(Point, coordinate) for coordinate in pairs]
        for (pt1, pt2), truth in zip(points, truths):
            with self.subTest(point1=pt1, point2=pt2, coincident=truth):
                self.assertEqual(spatial_relations.coincident(pt1, pt2), truth)

class TestCoincidentPointAndLine2D(unittest.TestCase):
    
    def setUp(self):
        self.tests = [
            ((0, 0), (1, 1), (2, 2), True),
            ((0, 0), (1, 1), (0, 0), True),
            ((0, 0), (1, 1), (-2, -2), True),
            ((0, 0), (1, 1), (0, 1), False),
            ((-4, 0), (0, 4), (-2, 2), True),
            ((-4, 0), (0, 4), (-4, 0), True),
            ((-4, 0), (0, 4), (0, 4), True),
            ((-4, 0), (0, 4), (0, 0), False),
            ((0, -4), (4, 0), (0, 0), False),
            ((0, -4), (4, 0), (2, -2), True),
        ]
    
    def test_coincident_point_with_line(self):
        tests = [
            (Line.from_two_points(line_pt1, line_pt2), Point(pt), truth)
            for line_pt1, line_pt2, pt, truth in self.tests
        ]
        for line, point, truth in tests:
            with self.subTest(line=line, point=point, coincident=truth):
                self.assertEqual(spatial_relations.coincident(point, line), truth)
    
    def test_coincident_point_with_linesegment(self):
        tests = [
            (LineSegment(line_pt1, line_pt2), Point(pt), truth)
            for line_pt1, line_pt2, pt, truth in self.tests
        ]
        for line, point, truth in tests:
            with self.subTest(linesegment=line, point=point, coincident=truth):
                self.assertEqual(spatial_relations.coincident(point, line), truth)
    
    def test_coincident_linesegment_with_point(self):
        tests = [
            (LineSegment(line_pt1, line_pt2), Point(pt), truth)
            for line_pt1, line_pt2, pt, truth in self.tests
        ]
        for line, point, truth in tests:
            with self.subTest(linesegment=line, point=point, coincident=truth):
                self.assertEqual(spatial_relations.coincident(line, point), truth)
    
    def test_coincident_line_with_point(self):
        tests = [
            (Line.from_two_points(line_pt1, line_pt2), Point(pt), truth)
            for line_pt1, line_pt2, pt, truth in self.tests
        ]
        for line, point, truth in tests:
            with self.subTest(line=line, point=point, coincident=truth):
                self.assertEqual(spatial_relations.coincident(line, point), truth)

class TestParallelLines2D(unittest.TestCase):
    def setUp(self):
        line1s = [
            ((0, 0), (1, 1)),
            ((0, 1), (0, 2)),
            ((0, 0), (1, 0)),
            ((0, 0), (1, 0)),
        ]
        line2s = [
            ((0, 1), (1, 2)),
            ((1, 1), (1, 2)),
            ((0, 1), (1, 1)),
            ((1, 0), (1, 2)),
        ]
        is_parallels = [
            True,
            True,
            True,
            False
        ]
        geometry_constructors = [Line.from_two_points, LineSegment]
        self.tests = []
        for gf1, gf2 in itertools.product(geometry_constructors, repeat=2):
            self.tests.extend(
                zip(itertools.starmap(gf1, line1s),
                    itertools.starmap(gf2, line2s),
                    is_parallels)
            )
    
    def test_parallel(self):
        for line1, line2, is_parallel in self.tests:
            with self.subTest(line1=line1, line2=line2, parallel=is_parallel):
                self.assertEqual(spatial_relations.parallel(line1, line2),
                                 is_parallel)

class TestSkewLines(unittest.TestCase):
    def setUp(self):
        line1s = [
            ((0, 0, 0), (1, 1, 0)),
            ((0, 1, 0), (0, 2, 0)),
            ((0, 0, 0), (1, 0, 0)),
            ((0, 0, 0), (1, 0, 0)),
            ((0, 0, 0), (1, 1, 1)),
        ]
        line2s = [
            ((0, 1, 0), (1, 2, 0)),
            ((1, 1, 0), (1, 2, 0)),
            ((0, 1, 0), (1, 1, 0)),
            ((1, 0, 0), (1, 2, 0)),
            ((0, 1, 0), (1, 1, 0)),
        ]
        is_skews = [
            False,
            False,
            False,
            False,
            True,
        ]
        geometry_constructors = [Line.from_two_points, LineSegment]
        self.tests = []
        for gf1, gf2 in itertools.product(geometry_constructors, repeat=2):
            self.tests.extend(
                zip(itertools.starmap(gf1, line1s),
                    itertools.starmap(gf2, line2s),
                    is_skews)
            )
    
    def test_skew(self):
        for line1, line2, is_skew in self.tests:
            with self.subTest(line1=line1, line2=line2, skew=is_skew):
                self.assertEqual(spatial_relations.skew(line1, line2),
                                 is_skew)

class TestGetAngleBetweenLines(unittest.TestCase):
    
    def setUp(self):
        line1s = [
            ((0, 0), (0, 1)),
            ((0, 0), (1, 0)),
            ((0, 0), (1, 0)),
            ((0, 0), (1, 0)),
            ((0, 0), (1, 0)),
            ((0, 0), (1, 1)),
        ]
        line2s = [
            ((0, 0), (1, 0)),
            ((0, 0), (0, 1)),
            ((0, 0), (-1, 1)),
            ((0, 1), (1, 1)),
            ((0, 0), (1, 1)),
            ((0, 0), (1, 0)),
        ]
        signed_angles = [
            (-90, 90),
            (90, -90),
            (135, -45),
            (0, 180),
            (45, -135),
            (-45, 135),
        ]
        angles = [math.radians(a[0]) for a in signed_angles]
        supplements = [math.radians(a[1]) for a in signed_angles]
        line_constructors = [Line.from_two_points, LineSegment] #, LineSegment]
        
        line_input_iters = [
            (map(abs, iter(angles)),
             itertools.repeat(False), itertools.repeat(False)),
            (map(abs, iter(supplements)),
             itertools.repeat(True), itertools.repeat(False)),
            (iter(angles), itertools.repeat(False), itertools.repeat(True)),
            (iter(supplements), itertools.repeat(True), itertools.repeat(True)),
        ]
        
        self.tests = []
        for lc1, lc2 in itertools.product(line_constructors, repeat=2):
            for angle_iter, supplement, signed in line_input_iters:
                self.tests.extend(
                    zip(itertools.starmap(lc1, line1s),
                        itertools.starmap(lc2, line2s),
                        map(abs, iter(angles)),
                        itertools.repeat(False), itertools.repeat(False)
                    )
                )
    
    def test_get_angle_between_line(self):
        for line1, line2, angle, supplement, signed in self.tests:
            with self.subTest(line1=line1, line2=line2,
                              angle=(f"Radians: {angle}, "
                                     f"Degrees: {math.degrees(angle)}"),
                              supplement=supplement,
                              signed=signed):
                self.assertAlmostEqual(
                    spatial_relations.get_angle_between(line1, line2,
                                                        supplement, signed),
                    angle
                )

class TestCoplanarPoints(unittest.TestCase):
    
    def setUp(self):
        point_sets = [
            [(0, 0, 0), (1, 0, 0)],
            [(0, 0, 0), (1, 0, 0), (0, 1, 0)],
            [(0, 0, 1), (1, 0, 1), (0, 1, 1)],
            [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, -1, 0)],
            [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, -1, 5)],
            [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, -1, 5), (0, -1, 6)],
        ]
        points = [list(map(Point, points)) for points in point_sets]
        coplanar = [
            True,
            True,
            True,
            True,
            False,
            False,
        ]
        self.tests = zip(points, iter(coplanar))
    
    def test_coplanar_point(self):
        for points, coplanar in self.tests:
            with self.subTest(points=points, coplanar=coplanar):
                self.assertEqual(spatial_relations.coplanar(*points), coplanar)

class TestCoplanarLinePoints(unittest.TestCase):
    
    def setUp(self):
        lines = [
            [(0, 0, 0), (1, 0, 0)],
            [(0, 0, 0), (1, 1, 1)],
        ]
        lines = list(itertools.starmap(Line.from_two_points, lines))
        point_sets = [
            [(1, 1, 0), (2, 3, 0), (-1, -4, 0)],
            [(1, 1, 0), (2, 3, 0), (-1, -4, 0)],
        ]
        points = [list(map(Point, points)) for points in point_sets]
        coplanar = [
            True,
            False,
        ]
        self.tests = zip(lines, points, coplanar)
    
    def test_coplanar_line_points(self):
        for line, points, coplanar in self.tests:
            with self.subTest(line=line, points=points, coplanar=coplanar):
                self.assertEqual(spatial_relations.coplanar(line, *points),
                                 coplanar)

class TestCoplanarLineLineSegment(unittest.TestCase):
    
    def setUp(self):
        line1s = [
            [(0, 0, 0), (1, 1, 0)],
            [(0, 0, 0), (1, 0, 0)],
        ]
        line2s = [
            [(0, 0, 0), (1, 0, 0)],
            [(0, 1, 0), (0, 1, 1)],
        ]
        coplanar = [
            True,
            False
        ]
        geometry_constructors = [Line.from_two_points, LineSegment]
        self.tests = []
        for gf1, gf2 in itertools.product(geometry_constructors, repeat=2):
            self.tests.extend(
                zip(itertools.starmap(gf1, line1s),
                    itertools.starmap(gf2, line2s),
                    coplanar)
            )
    
    def test_coplanar_line_linesegment(self):
        for line1, line2, coplanar in self.tests:
            with self.subTest(line1=line1, line2=line2, coplanar=coplanar):
                self.assertEqual(spatial_relations.coplanar(line1, line2),
                                 coplanar)

class TestGetIntersectionLineLineSegment(unittest.TestCase):
    
    def setUp(self):
        tests = [
            # 2D
            ((0, 0), (1, 1), (0, 4), (4, 0), (2, 2)),
            ((0, 0), (1, 1), (0, 0), (-1, 1), (0, 0)),
            ((0, 0), (1, 1), (0, 1), (1, 2), None), # Parallel
            # 3D
            ((0, 0, 0), (1, 1, 0), (0, 4, 0), (4, 0, 0), (2, 2, 0)),
            ((0, 0, 0), (1, 1, 0), (0, 4, 1), (4, 0, 1), None), # Skew
            ((0, 0, 0), (1, 1, 0), (0, 0, 0), (-1, 1, 0), (0, 0, 0)),
            ((0, 0, 0), (1, 1, 0), (0, 0, 1), (-1, 1, 1), None),
        ]
        line1_pts = [[pt1, pt2] for pt1, pt2, *_ in tests]
        line2_pts = [[pt1, pt2] for _, _, pt1, pt2, *_ in tests]
        intersection_coordinates = [pt for *_, pt in tests]
        constructors = [Line.from_two_points, LineSegment]
        intersections = []
        
        for i in intersection_coordinates:
            intersections.append(None if i is None else Point(i))
        self.tests = []
        for func1, func2 in itertools.product(constructors, repeat=2):
            self.tests.extend(
                zip(itertools.starmap(func1, line1_pts),
                    itertools.starmap(func2, line2_pts),
                    intersections)
            )
    
    def test_get_intersection(self):
        for line1, line2, intersection in self.tests:
            if intersection is None:
                expected = "No Intersection"
            else:
                expected = tuple(intersection)
            with self.subTest(line1=str(line1), line2=str(line2),
                              intersection=expected):
                result_pt = spatial_relations.get_intersect(line1, line2)
                if intersection is None:
                    self.assertEqual(result_pt, intersection)
                else:
                    verification.assertPointsAlmostEqual(self, result_pt,
                                                         intersection)

class TestPerpendicularLineLineSegment(unittest.TestCase):
    def setUp(self):
        tests = [
            ((0, 0), (0, 1), (0, 0), (1, 0), True),
            ((0, 0), (0, 1), (0, 0), (1, 1), False),
        ]
        line1_pts = [[pt1, pt2] for pt1, pt2, *_ in tests]
        line2_pts = [[pt1, pt2] for _, _, pt1, pt2, *_ in tests]
        perpendicular = [truth for *_, truth in tests]
        constructors = [Line.from_two_points, LineSegment]
        
        self.tests = []
        for func1, func2 in itertools.product(constructors, repeat=2):
            self.tests.extend(
                zip(itertools.starmap(func1, line1_pts),
                    itertools.starmap(func2, line2_pts),
                    perpendicular)
            )
    
    def test_is_perpendicular(self):
        for line1, line2, perpendicular in self.tests:
            with self.subTest(
                        line1=line1, line2=line2, perpendicular=perpendicular
                    ):
                self.assertEqual(spatial_relations.perpendicular(line1, line2),
                                 perpendicular)

class TestCollinear(unittest.TestCase):
    def setUp(self):
        tests = [
            [(0, 0), (1, 1), (2, 2), True],
            [(0, 0), (1, 1), (0, 1), False],
            [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), True],
        ]
        self.constructors = [Line.from_two_points, LineSegment]
        self.tests = [
            (list(map(Point, c)), collinear) for *c, collinear in tests
        ]
    
    def test_collinear_points(self):
        for points, collinear in self.tests:
            with self.subTest(points = list(map(tuple, points)),
                              collinear=collinear):
                self.assertEqual(spatial_relations.collinear(*points), collinear)
    
    def test_collinear_line_points(self):
        tests = []
        for func in self.constructors:
            tests.extend([
                (func(pt1, pt2), *pts, collinear)
                for [pt1, pt2, *pts], collinear in self.tests
            ])
        for line, *pts, collinear in tests:
            with self.subTest(line=line, points=pts, collinear=collinear):
                self.assertEqual(spatial_relations.collinear(line, *pts),
                                 collinear)

class TestEqualLineSegment(unittest.TestCase):
    
    def setUp(self):
        line1s = [
            [(0, 0), (0, 1)],
            [(0, 0), (0, 1)],
            [(0, 0), (0, 1)],
        ]
        line2s = [
            [(0, 0), (0, 1)],
            [(1, 0), (1, 1)],
            [(0, 0), (0, 2)],
        ]
        equal = [
            True,
            True,
            False
        ]
        self.tests = zip(itertools.starmap(LineSegment, line1s),
                         itertools.starmap(LineSegment, line2s),
                         equal)
    
    def test_is_equal_length(self):
        truths = [
            True,
            True,
            False,
        ]
        for line1, line2, equal in self.tests:
            with self.subTest(line1=line1, line2=line2, equal=equal):
                self.assertEqual(spatial_relations.equal(line1, line2), equal)

if __name__ == "__main__":
    unittest.main()