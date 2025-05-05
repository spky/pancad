"""A module to provide functions used to verify that PanCAD is operating 
correctly."""
from functools import singledispatch
import math

from PanCAD.geometry.point import Point
from PanCAD.geometry.line import Line
from PanCAD.geometry.line_segment import LineSegment

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
                            line_a: Point, line_b: Point, places: int = 7):
    line_a_tuple = tuple(line_a.reference_point) + line_a.direction
    line_b_tuple = tuple(line_b.reference_point) + line_b.direction
    assertTupleAlmostEqual(self_input, line_a_tuple, line_b_tuple, places)

def assertPanCADAlmostEqual(self_input, object_a, object_b, places):
    if isinstance(object_a, Point) and isinstance(object_b, Point):
        assertPointsAlmostEqual(self_input, object_a, object_b, places)
    elif isinstance(object_a, Line) and isinstance(object_b, Line):
        assertLinesAlmostEqual(self_input, object_a, object_b)
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

@singledispatch
def isclose(value_a, value_b,
            abs_tol: float, rel_tol: float, nan_equal: bool = False):
    raise NotImplementedError(f"Unsupported 1st type {value_a.__class__}")

@isclose.register
def isclose_number(value_a: int | float, value_b: int | float,
                   rel_tol: float, abs_tol: float, nan_equal: bool = False):
    if isinstance(value_a, float) or isinstance(value_b, float):
        if nan_equal and math.isnan(value_a) and math.isnan(value_b):
            return True
        else:
            return math.isclose(value_a, value_b,
                                rel_tol=rel_tol, abs_tol=abs_tol)
    else:
        return value_a == value_b

@isclose.register
def isclose_tuple(tuple_a: tuple, tuple_b: tuple,
                  rel_tol: float, abs_tol: float, nan_equal: bool = False):
    comparisons = []
    for val1, val2 in zip(tuple_a, tuple_b):
        if isinstance(val1, float) or isinstance(val2, float):
            if nan_equal and math.isnan(val1) and math.isnan(val2):
                comparisons.append(True)
            else:
                comparisons.append(
                    math.isclose(val1, val2, rel_tol=rel_tol, abs_tol=abs_tol)
                )
        else:
            comparisons.append(val1 == val2)
    return all(comparisons)