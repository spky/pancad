"""A module to provide functions used to verify that pancad is operating
correctly."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pancad.geometry.point import Point
from pancad.geometry.line import Line
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.plane import Plane
from pancad.geometry.coordinate_system import CoordinateSystem

if TYPE_CHECKING:
    from pancad.abstract import AbstractGeometry

def assertTupleAlmostEqual(self_input,
                           tuple_a: tuple, tuple_b: tuple,
                           places: int = 7) -> None:
    """Raises an AssertionError when the tuples are not equal."""
    for val1, val2 in zip(tuple_a, tuple_b):
        if isinstance(val1, float) or isinstance(val2, float):
            if math.isnan(val1) and math.isnan(val2):
                self_input.assertTrue(math.isnan(val1) and math.isnan(val2))
            else:
                self_input.assertAlmostEqual(val1, val2, places)
        else:
            self_input.assertEqual(val1, val2)

def assertPointsAlmostEqual(self_input,
                            point_a: Point, point_b: Point,
                            places: int = 7) -> None:
    """Raises an AssertionError when the points are not equal"""
    assertTupleAlmostEqual(self_input, tuple(point_a), tuple(point_b), places)

def assertLinesAlmostEqual(self_input,
                            line_a: Line, line_b: Line,
                            places: int = 7) -> None:
    """Raises an AssertionError when the Lines are not equal"""
    a = tuple(line_a.reference_point) + line_a.direction
    b = tuple(line_b.reference_point) + line_b.direction
    assertTupleAlmostEqual(self_input, a, b, places)

def assertLineSegmentsAlmostEqual(self_input,
                                  line_a: LineSegment, line_b: LineSegment,
                                  places: int = 7) -> None:
    """Raises an AssertionError when the LineSegments are not equal"""
    a = tuple(line_a.start) + tuple(line_a.end)
    b = tuple(line_b.start) + tuple(line_b.end)
    assertTupleAlmostEqual(self_input, a, b, places)

def assertPlanesAlmostEqual(self_input, plane_a: Plane, plane_b: Plane,
                            places: int = 7) -> None:
    """Raises an AssertionError when the Planes are not equal"""
    a = tuple(plane_a.reference_point) + plane_a.normal
    b = tuple(plane_b.reference_point) + plane_b.normal
    assertTupleAlmostEqual(self_input, a, b, places)

def assertCoordinateSystemsAlmostEqual(self_input, cs_a: CoordinateSystem,
                                       cs_b: CoordinateSystem,
                                       places: int = 7) -> None:
    """Raises an AssertionError when the CoordinateSystems are not equal"""
    a_x, a_y, a_z = cs_a.get_axis_vectors()
    b_x, b_y, b_z = cs_b.get_axis_vectors()
    a = tuple(cs_a.origin) + a_x + a_y + a_z
    b = tuple(cs_a.origin) + b_x + b_y + b_z
    assertTupleAlmostEqual(self_input, a, b, places)

def assertPancadAlmostEqual(self_input,
                            object_a: AbstractGeometry,
                            object_b: AbstractGeometry,
                            places: int) -> None:
    """Raises an AssertionError when two pancad geometry objects are not equal"""
    if isinstance(object_a, Point) and isinstance(object_b, Point):
        assertPointsAlmostEqual(self_input, object_a, object_b, places)
    elif isinstance(object_a, Line) and isinstance(object_b, Line):
        assertLinesAlmostEqual(self_input, object_a, object_b, places)
    elif isinstance(object_a, LineSegment) and isinstance(object_b, LineSegment):
        assertLineSegmentsAlmostEqual(self_input, object_a, object_b, places)
    elif isinstance(object_a, Plane) and isinstance(object_b, Plane):
        assertPlanesAlmostEqual(self_input, object_a, object_b, places)
    elif (isinstance(object_a, CoordinateSystem)
            and isinstance(object_b, CoordinateSystem)):
        assertCoordinateSystemsAlmostEqual(self_input, object_a, object_b,
                                           places)
    elif isinstance(object_a, tuple) and isinstance(object_b, tuple):
        assertTupleAlmostEqual(self_input, object_a, object_b, places)
    else:
        raise ValueError(f"""Provided object Classes not supported. A:
                         {object_a.__class__}, B: {object_b.__class__}""")

def isTupleAlmostEqual(tuple_a: tuple, tuple_b: tuple, places: int = 7) -> bool:
    """Returns whether two tuples are equal. Assumes nans are equal."""
    checks = []
    for val1, val2 in zip(tuple_a, tuple_b):
        if isinstance(val1, float) or isinstance(val2, float):
            if math.isnan(val1) and math.isnan(val2):
                is_equal = math.isnan(val1) and math.isnan(val2)
            else:
                is_equal = math.isclose(val1, val2,
                                        rel_tol=1/(10**places),
                                        abs_tol=1/(10**places))
            checks.append(is_equal)
        else:
            checks.append(val1 == val2)
    return all(checks)
