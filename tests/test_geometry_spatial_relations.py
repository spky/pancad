import itertools
import math
import os
import unittest

from PanCAD.geometry import Point, Line, LineSegment, Plane, spatial_relations

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

if __name__ == "__main__":
    unittest.main()