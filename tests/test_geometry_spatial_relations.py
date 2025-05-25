import itertools
from itertools import repeat
import math
from math import radians, degrees
import os
import unittest

from PanCAD.geometry import Point, Line, LineSegment, Plane, spatial_relations
from PanCAD.utils import verification, trigonometry as trig
from PanCAD.constants.angle_convention import AngleConvention as AC

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

class TestCoincidentPlanePoint(unittest.TestCase):
    
    def test_point(self):
        pln = Plane(Point(0, 0, 0), (0, 0, 1))
        points = [
            [Point(1, 1, 0), True],
            [Point(1, 1, 1), False],
        ]
        for pt, coincident in points:
            with self.subTest(plane=pln, point=pt, coincident=coincident):
                self.assertEqual(spatial_relations.coincident(pln, pt),
                                 coincident)
                self.assertEqual(spatial_relations.coincident(pt, pln),
                                 coincident)

class TestCoincidentPlanePlane(unittest.TestCase):
    
    def setUp(self):
        plane1s = [
            [Point(0, 0, 0), (0, 0, 1)], # On origin
            [Point(0, 0, 1), (0, 0, 1)], # Off Origin
        ]
        plane2s = [
            [Point(0, 0, 0), (0, 0, 1)],
            [Point(0, 0, 0), (1, 0, 0)],
            [Point(0, 0, 1), (0, 0, 1)],
        ]
        coincident2to1 = [
            (True, False),
            (False, False),
            (False, True),
        ]
        plane1s = itertools.starmap(Plane, plane1s)
        plane2s = itertools.starmap(Plane, plane2s)
        tests = []
        for i, pln in enumerate(plane2s):
            tests.append([pln, coincident2to1[i][0]])
            tests.append([pln, coincident2to1[i][1]])
        self.tests = zip(itertools.cycle(plane1s), tests)
    
    def test_plane_plane(self):
        for pln1, [pln2, coincident] in self.tests:
            with self.subTest(plane1=pln1, plane2=pln2, coincident=coincident):
                self.assertEqual(spatial_relations.coincident(pln1, pln2),
                                 coincident)

class TestCoincidentPlaneLine(unittest.TestCase):
    
    def test_plane_line(self):
        pln = Plane((0, 0, 0), (0, 0, 1))
        line1 = Line.from_two_points((-1, -1, 0), (1, 1, 0))
        line2 = Line.from_two_points((-1, -1, 1), (1, 1, 1))
        self.assertTrue(spatial_relations.coincident(pln, line1))
        self.assertFalse(spatial_relations.coincident(pln, line2))
    
    def test_plane_linesegment(self):
        pln = Plane((0, 0, 0), (0, 0, 1))
        line1 = LineSegment((-1, -1, 0), (1, 1, 0))
        line2 = LineSegment((-1, -1, 1), (1, 1, 1))
        self.assertTrue(spatial_relations.coincident(pln, line1))
        self.assertFalse(spatial_relations.coincident(pln, line2))


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
        common_pt = (0, 0)
        lines = [Line.from_point_and_angle(common_pt, radians(phi))
                 for phi in range(0, 180+1, 45)]
        self.line_pairs = list(itertools.product(lines, repeat=2))
    
    def test_get_angle_between_lines_convention_plus_pi(self):
        CONVENTION = AC.PLUS_PI
        IS_SUPPLEMENT = False
        for l1, l2 in self.line_pairs:
            angle = abs(l2.phi - l1.phi)
            with self.subTest(line1=l1, line2=l2,
                              angle=f"R:{angle}, D:{degrees(angle)}"):
                test = spatial_relations.get_angle_between(
                    l1, l2, opposite=IS_SUPPLEMENT, convention=CONVENTION
                )
                self.assertAlmostEqual(test, angle)
    
    def test_get_angle_between_lines_convention_sign_pi(self):
        CONVENTION = AC.SIGN_PI
        IS_SUPPLEMENT = False
        for l1, l2 in self.line_pairs:
            angle = abs(l2.phi - l1.phi)
            if trig.is_clockwise(l1.direction, l2.direction):
                angle = -angle
            with self.subTest(line1=l1, line2=l2,
                              angle=f"R:{angle}, D:{degrees(angle)}"):
                test = spatial_relations.get_angle_between(
                    l1, l2, opposite=IS_SUPPLEMENT, convention=CONVENTION
                )
                self.assertAlmostEqual(test, angle)

class TestGetAngleBetweenLineSegments(unittest.TestCase):
    
    def setUp(self):
        common_pt = (0, 0)
        length = 1
        segments = [
            LineSegment.from_point_length_angle(common_pt, length, radians(phi))
            for phi in range(0, 360 + 1, 45)
        ]
        self.segment_pairs = list(itertools.product(segments, repeat=2))
    
    def test_convention_plus_tau(self):
        CONVENTION = AC.PLUS_TAU
        IS_EXPLEMENT = False
        for l1, l2 in self.segment_pairs:
            phi1 = l1.phi
            phi2 = l2.phi
            if phi1 < 0: phi1 += math.tau
            if phi2 < 0: phi2 += math.tau
            
            angle = phi2 - phi1
            if angle < 0: angle += math.tau
            
            with self.subTest(line1=l1, line2=l2,
                              angle=f"R:{angle}, D:{degrees(angle)}"):
                test = spatial_relations.get_angle_between(
                    l1, l2, opposite=IS_EXPLEMENT, convention=CONVENTION
                )
                self.assertAlmostEqual(test, angle)
    
    def test_convention_plus_tau_explement(self):
        CONVENTION = AC.PLUS_TAU
        IS_EXPLEMENT = True
        for l1, l2 in self.segment_pairs:
            phi1 = l1.phi
            phi2 = l2.phi
            if phi1 < 0: phi1 += math.tau
            if phi2 < 0: phi2 += math.tau
            
            angle = phi2 - phi1
            if angle < 0: angle += math.tau
            angle = math.tau - angle
            with self.subTest(line1=l1, line2=l2,
                              angle=f"R:{angle}, D:{degrees(angle)}"):
                test = spatial_relations.get_angle_between(
                    l1, l2, opposite=IS_EXPLEMENT, convention=CONVENTION
                )
                self.assertAlmostEqual(test, angle)
    
    def test_convention_plus_pi(self):
        CONVENTION = AC.PLUS_PI
        IS_SUPPLEMENT = False
        for l1, l2 in self.segment_pairs:
            phi1 = l1.phi
            phi2 = l2.phi
            if phi1 < 0: phi1 += math.tau
            if phi2 < 0: phi2 += math.tau
            
            if phi2 > phi1 and phi2 - phi1 < math.pi:
                angle = phi2 - phi1
            elif phi2 > phi1 and phi2 - phi1 > math.pi:
                angle = math.tau - phi2 + phi1
            elif phi2 < phi1 and phi1 - phi2 < math.pi:
                angle = phi1 - phi2
            elif phi2 < phi1 and phi1 - phi2 > math.pi:
                angle = math.tau - phi1 + phi2
            elif abs(phi1 - phi2) == math.pi:
                angle = math.pi
            else:
                angle = 0
            with self.subTest(line1=l1, line2=l2,
                              angle=f"R:{angle}, D:{degrees(angle)}"):
                test = spatial_relations.get_angle_between(
                    l1, l2, opposite=IS_SUPPLEMENT, convention=CONVENTION
                )
                self.assertAlmostEqual(test, angle)
    
    def test_convention_plus_pi_supplement(self):
        CONVENTION = AC.PLUS_PI
        IS_SUPPLEMENT = True
        for l1, l2 in self.segment_pairs:
            phi1 = l1.phi
            phi2 = l2.phi
            if phi1 < 0: phi1 += math.tau
            if phi2 < 0: phi2 += math.tau
            
            if phi2 > phi1 and phi2 - phi1 < math.pi:
                angle = phi2 - phi1
            elif phi2 > phi1 and phi2 - phi1 > math.pi:
                angle = math.tau - phi2 + phi1
            elif phi2 < phi1 and phi1 - phi2 < math.pi:
                angle = phi1 - phi2
            elif phi2 < phi1 and phi1 - phi2 > math.pi:
                angle = math.tau - phi1 + phi2
            elif abs(phi1 - phi2) == math.pi:
                angle = math.pi
            else:
                angle = 0
            angle = math.pi - angle
            with self.subTest(line1=l1, line2=l2,
                              angle=f"R:{angle}, D:{degrees(angle)}"):
                test = spatial_relations.get_angle_between(
                    l1, l2, opposite=IS_SUPPLEMENT, convention=CONVENTION
                )
                self.assertAlmostEqual(test, angle)
    
    def test_convention_sign_pi(self):
        CONVENTION = AC.SIGN_PI
        IS_SUPPLEMENT = False
        for l1, l2 in self.segment_pairs:
            phi1 = l1.phi
            phi2 = l2.phi
            if phi1 < 0: phi1 += math.tau
            if phi2 < 0: phi2 += math.tau
            
            diff = abs(phi2 - phi1)
            if phi2 > phi1 and diff < math.pi:
                angle = phi2 - phi1
            
            elif phi2 > phi1 and diff > math.pi:
                angle = -(math.tau - phi2 + phi1)
            
            elif phi2 < phi1 and diff < math.pi:
                angle = -(phi1 - phi2)
            
            elif phi2 < phi1 and diff > math.pi:
                angle = math.tau - phi1 + phi2
            elif phi1 - phi2 == math.pi:
                angle = -math.pi
            elif phi1 - phi2 == -math.pi:
                angle = math.pi
            else:
                angle = 0
            with self.subTest(line1=l1, line2=l2,
                              angle=f"R:{angle}, D:{degrees(angle)}"):
                test = spatial_relations.get_angle_between(
                    l1, l2, opposite=IS_SUPPLEMENT, convention=CONVENTION
                )
                self.assertAlmostEqual(test, angle)

class TestGetAngleBetweenPlaneLinePhi0(unittest.TestCase):
    
    def setUp(self):
        phi_zero = 0 # Zero so the test focuses just on theta
        self.line_pre = [
            [(0, 0, 0), phi_zero, 90],
            [(0, 0, 0), phi_zero, 45],
            [(0, 0, 0), phi_zero, 30],
            [(0, 0, 0), phi_zero, 0],
        ]
        self.plane_pre = [
            [(0, 0, 0), phi_zero, 0],
        ]
        
        line_params = [(Point(pt), math.radians(p), math.radians(t))
                       for pt, p, t in self.line_pre]
        plane_params = [(Point(pt), math.radians(p), math.radians(t))
                        for pt, p, t in self.plane_pre]
        
        lines = itertools.starmap(Line.from_point_and_angle, line_params)
        planes = itertools.starmap(Plane.from_point_and_angles, plane_params)
        self.pairs = []
        for p in planes:
            self.pairs.extend(zip(lines, repeat(p)))
    
    def test_line_plane_unsigned(self):
        tests = [(line, pln, math.pi/2 - line.theta - pln.theta)
                 for line, pln in self.pairs]
        for line, plane, angle in tests:
            with self.subTest(line=line, plane=plane,
                              angle=f"R:{angle} D:{math.degrees(angle)}"):
                self.assertAlmostEqual(
                    spatial_relations.get_angle_between(line, plane),
                    angle
                )
    
    def test_line_plane_unsigned_supplement(self):
        tests = [(line, pln, math.pi - (math.pi/2 - line.theta - pln.theta))
                 for line, pln in self.pairs]
        for line, plane, angle in tests:
            with self.subTest(line=line, plane=plane,
                              angle=f"R:{angle} D:{math.degrees(angle)}"):
                self.assertAlmostEqual(
                    spatial_relations.get_angle_between(line, plane,
                                                        opposite=True),
                    angle
                )

class TestGetAngleBetweenPlanes(unittest.TestCase):
    
    def test_perpendicular(self):
        plane_params = [
            [(0, 0, 0), 0, 0],
            [(0, 0, 0), 0, 90],
        ]
        
        plane_params = [(Point(pt), math.radians(phi), math.radians(theta))
                        for pt, phi, theta in plane_params]
        plane1 = Plane.from_point_and_angles(*plane_params[0])
        plane2 = Plane.from_point_and_angles(*plane_params[1])
        result = spatial_relations.get_angle_between(plane1, plane2)
        self.assertAlmostEqual(result, math.radians(90))
    
    def test_45(self):
        plane_params = [
            [(0, 0, 0), 0, 0],
            [(0, 0, 0), 0, 45],
        ]
        plane_params = [(Point(pt), math.radians(phi), math.radians(theta))
                        for pt, phi, theta in plane_params]
        plane1 = Plane.from_point_and_angles(*plane_params[0])
        plane2 = Plane.from_point_and_angles(*plane_params[1])
        result = spatial_relations.get_angle_between(plane1, plane2)
        self.assertAlmostEqual(result, math.radians(45))
    
    def test_135(self):
        plane_params = [
            [(0, 0, 0), 0, 0],
            [(0, 0, 0), 0, 135],
        ]
        plane_params = [(Point(pt), math.radians(phi), math.radians(theta))
                        for pt, phi, theta in plane_params]
        plane1 = Plane.from_point_and_angles(*plane_params[0])
        plane2 = Plane.from_point_and_angles(*plane_params[1])
        result = spatial_relations.get_angle_between(plane1, plane2)
        self.assertAlmostEqual(result, math.radians(135))

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

class TestGetIntersectLineLineSegment(unittest.TestCase):
    
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

class TestGetIntersectLinePlane(unittest.TestCase):
    
    def setUp(self):
        plane_params = [
            [(0, 0, 0), (0, 0, 1)],
            [(0, 0, -1), (0, 0, 1)],
        ]
        planes = itertools.starmap(Plane, plane_params)
        intersections = [coord for coord, *_ in plane_params]
        line_p2s = [
            (0, 0, 1),
            (0, 1, 1),
        ]
        line_params = zip(
            itertools.cycle(intersections),
            [coord for ls in line_p2s for coord in (ls,)*len(intersections)],
        )
        intersections = map(Point, intersections)
        lines = itertools.starmap(Line.from_two_points, line_params)
        self.tests = zip(itertools.cycle(intersections),
                         itertools.cycle(planes),
                         lines)
    
    def test_get_intersect_line_plane(self):
        for intersect, plane, line in self.tests:
            with self.subTest(intersect=intersect, plane=plane, line=line):
                verification.assertPanCADAlmostEqual(
                    self,
                    spatial_relations.get_intersect(plane, line),
                    intersect,
                    ROUNDING_PLACES,
                )
                verification.assertPanCADAlmostEqual(
                    self,
                    spatial_relations.get_intersect(line, plane),
                    intersect,
                    ROUNDING_PLACES,
                )

class TestGetIntersectPlanePlane(unittest.TestCase):
    
    def test_plane_plane_origin(self):
        pln1 = Plane(Point(0, 0, 0), (0, 0, 1))
        pln2 = Plane(Point(0, 0, 0), (0, 1, 0))
        line = Line.from_point_and_angle((0, 0, 0), 0, math.radians(90))
        verification.assertPanCADAlmostEqual(
            self,
            spatial_relations.get_intersect(pln1, pln2),
            line,
            ROUNDING_PLACES
        )
    
    def test_plane_plane_off_origin(self):
        pln1 = Plane(Point(0, 0, 1), (0, 0, 1))
        pln2 = Plane(Point(0, 0, 0), (0, 1, 0))
        line = Line.from_point_and_angle((0, 0, 1), 0, math.radians(90))
        verification.assertPanCADAlmostEqual(
            self,
            spatial_relations.get_intersect(pln1, pln2),
            line,
            ROUNDING_PLACES
        )

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
        for line1, line2, equal in self.tests:
            with self.subTest(line1=line1, line2=line2, equal=equal):
                self.assertEqual(spatial_relations.equal(line1, line2), equal)

class TestPerpendicularPlane(unittest.TestCase):
    
    def setUp(self):
        line_pms = [
            [(0, 0, 0), 0, 0],
            [(0, 0, 0), 0, 90],
        ]
        plane_pms = [
            [(0, 0, 0), 0, 90],
            [(0, 0, 0), 0, 0],
        ]
        
        tests = []
        self.tests = []
        for pms in plane_pms:
            tests.extend(
                zip(
                    itertools.repeat(pms, len(line_pms)),
                    line_pms
                )
            )
        for t in tests:
            [pln_pt, pln_phi, pln_theta], [line_pt, line_phi, line_theta] = t
            self.tests.append(
                [
                    Plane.from_point_and_angles(
                        pln_pt, math.radians(pln_phi), math.radians(pln_theta)
                    ),
                    Line.from_point_and_angle(line_pt,
                        math.radians(line_phi), math.radians(line_theta)
                    ),
                    pln_phi == line_phi and pln_theta == line_theta,
                ]
            )
    
    def test_plane_line(self):
        for plane, line, perpendicular in self.tests:
            with self.subTest(plane=plane, line=line,
                              perpendicular=perpendicular):
                self.assertEqual(spatial_relations.perpendicular(plane, line),
                                 perpendicular)

class TestProjectOntoPlane(unittest.TestCase):
    
    def test_point_to_xz_plane(self):
        pt = Point(1, 1, 0)
        pln = Plane((0, 0, 0), (0, 1, 0))
        pt_project = spatial_relations.project(pt, pln)
        verification.assertPanCADAlmostEqual(self, pt_project, Point(1, 0, 0),
                                             ROUNDING_PLACES)
    
    def test_point_to_offset_xz_plane(self):
        pt = Point(1, 1, 0)
        pln = Plane((0, 20, 0), (0, 1, 0))
        pt_project = spatial_relations.project(pt, pln)
        verification.assertPanCADAlmostEqual(self, pt_project, Point(1, 20, 0),
                                             ROUNDING_PLACES)
    
    def test_line_to_xz_plane(self):
        line = Line.from_two_points((0, 0, 0), (1, 1, 0))
        pln = Plane((0, 0, 0), (0, 1, 0))
        line_project = spatial_relations.project(line, pln)
        verification.assertPanCADAlmostEqual(self, line_project,
                                             Line.from_two_points((0,0,0),(1,0,0)),
                                             ROUNDING_PLACES)
    
    def test_line_to_xz_plane_perpendicular(self):
        line = Line.from_two_points((0, 0, 0), (0, 1, 0))
        pln = Plane((0, 0, 0), (0, 1, 0))
        line_project = spatial_relations.project(line, pln)
        verification.assertPanCADAlmostEqual(self, line_project,
                                             Point(0, 0, 0),
                                             ROUNDING_PLACES)
    
    def test_line_segment_to_xz_plane(self):
        line = LineSegment((0, 0, 0), (1, 1, 0))
        pln = Plane((0, 0, 0), (0, 1, 0))
        line_project = spatial_relations.project(line, pln)
        verification.assertPanCADAlmostEqual(self, line_project,
                                             LineSegment((0,0,0),(1,0,0)),
                                             ROUNDING_PLACES)
    
    def test_line_segment_to_xz_plane_perpendicular(self):
        line = LineSegment((0, 0, 0), (0, 1, 0))
        pln = Plane((0, 0, 0), (0, 1, 0))
        line_project = spatial_relations.project(line, pln)
        verification.assertPanCADAlmostEqual(self, line_project,
                                             Point(0, 0, 0),
                                             ROUNDING_PLACES)

if __name__ == "__main__":
    unittest.main()