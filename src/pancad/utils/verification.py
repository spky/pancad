"""A module to provide functions used to verify that pancad is operating 
correctly."""
from functools import singledispatch
import math

from pancad.geometry import Point, Line, LineSegment, Plane, CoordinateSystem

def assertTupleAlmostEqual(self_input, 
                           tuple_a: tuple, tuple_b: tuple, places: int = 7):
    for val1, val2 in zip(tuple_a, tuple_b):
        if type(val1) is float or type(val2) is float:
            if math.isnan(val1) and math.isnan(val2):
                self_input.assertTrue(math.isnan(val1) and math.isnan(val2))
            else:
                self_input.assertAlmostEqual(val1, val2, places)
        else:
            self_input.assertEqual(val1, val2)

def assertPointsAlmostEqual(self_input,
                            point_a: Point, point_b: Point, places: int = 7):
    assertTupleAlmostEqual(self_input, tuple(point_a), tuple(point_b), places)

def assertLinesAlmostEqual(self_input,
                            line_a: Line, line_b: Line, places: int = 7):
    a = tuple(line_a.reference_point) + line_a.direction
    b = tuple(line_b.reference_point) + line_b.direction
    assertTupleAlmostEqual(self_input, a, b, places)

def assertLineSegmentsAlmostEqual(self_input,
                                  line_a: LineSegment, line_b: LineSegment,
                                  places: int = 7):
    a = tuple(line_a.start) + tuple(line_a.end)
    b = tuple(line_b.start) + tuple(line_b.end)
    assertTupleAlmostEqual(self_input, a, b, places)

def assertPlanesAlmostEqual(self_input, plane_a: Plane, plane_b: Plane,
                            places: int = 7):
    a = tuple(plane_a.reference_point) + plane_a.normal
    b = tuple(plane_b.reference_point) + plane_b.normal
    assertTupleAlmostEqual(self_input, a, b, places)

def assertCoordinateSystemsAlmostEqual(self_input, cs_a: CoordinateSystem,
                                       cs_b: CoordinateSystem, places: int = 7):
    a_x, a_y, a_z = cs_a.get_axis_vectors()
    b_x, b_y, b_z = cs_b.get_axis_vectors()
    a = tuple(cs_a.origin) + a_x + a_y + a_z
    b = tuple(cs_a.origin) + b_x + b_y + b_z
    assertTupleAlmostEqual(self_input, a, b, places)

def assertPancadAlmostEqual(self_input, object_a, object_b, places):
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

def isTupleAlmostEqual(tuple_a: tuple, tuple_b: tuple, places: int = 7):
    for val1, val2 in zip(tuple_a, tuple_b):
        if type(val1) is float or type(val2) is float:
            if math.isnan(val1) and math.isnan(val2):
                return math.isnan(val1) and math.isnan(val2)
            else:
                return math.isclose(val1, val2,
                                    rel_tol=1/(10**places),
                                    abs_tol=1/(10**places))
        else:
            return val1 == val2