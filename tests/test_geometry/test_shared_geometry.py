"""Tests for methods shared by all pancad geometry."""

import pytest

from pancad.api import(
    Axis,
    Circle,
    CircularArc,
    CoordinateSystem,
    Ellipse,
    Line,
    LineSegment,
    Plane,
    Point,
    TwoDSketchSystem,
)

EQ = True # Equal
NOT_EQ = False # Not Equal
CW = True # Clockwise
CCW = False # Counter-Clockwise

@pytest.mark.parametrize(
    "geometry, other, expected",
    [
        (Axis((0, 0, 0), (1, 0, 0)), Axis((0, 0, 0), (1, 0, 0)), EQ),
        (Axis((0, 0, 0), (1, 0, 0)), Axis((0, 1, 0), (1, 0, 0)), NOT_EQ),
        (Axis((0, 0, 0), (1, 0, 0)), Axis((0, 0, 0), (0, 1, 0)), NOT_EQ),
        (Circle((0, 0), 1), Circle((0, 0), 1), EQ),
        (Circle((0, 0), 1), Circle((0, 0), 2), NOT_EQ),
        (Circle((0, 0), 1), Circle((1, 1), 1), NOT_EQ),
        (
            CircularArc((0, 0), 1, (1, 0), (0, 1), CW),
            CircularArc((0, 0), 1, (1, 0), (0, 1), CW),
            EQ
        ),
        (
            CircularArc((0, 0), 1, (1, 0), (0, 1), CW),
            CircularArc((0, 0), 1, (1, 0), (0, 1), CCW),
            NOT_EQ
        ),
        (CoordinateSystem((0, 0, 0)), CoordinateSystem((0, 0, 0)), EQ),
        (CoordinateSystem((0, 0, 0)), CoordinateSystem((1, 1, 1)), NOT_EQ),
        (Line(Point(0, 0), (1, 0)), Line(Point(0, 0), (1, 0)), EQ),
        (Line(Point(0, 0), (1, 0)), Line(Point(0, 0), (1, 1)), NOT_EQ),
        (Line(Point(0, 0, 0), (1, 0, 0)), Line(Point(0, 0, 0), (1, 0, 0)), EQ),
        (Line(Point(0, 0, 0), (1, 0, 0)), Line(Point(0, 0, 0), (0, 1, 0)), NOT_EQ),
        (LineSegment((0, 0), (1, 1)), LineSegment((0, 0), (1, 1)), EQ),
        (LineSegment((0, 0, 0), (1, 1, 1)), LineSegment((0, 0, 0), (1, 1, 1)), EQ),
        (Plane((0, 0, 0), (1, 0, 0)), Plane((0, 0, 0), (1, 0, 0)), EQ),
        (Plane((0, 0, 0), (1, 0, 0)), Plane((0, 0, 0), (0, 1, 0)), NOT_EQ),
        (Point(0, 0, 0), Point(0, 0, 0), EQ),
        (Point(0, 0, 0), Point(1, 1, 1), NOT_EQ),
        (Ellipse.from_angle((0, 0), 2, 1, 0), Ellipse.from_angle((0, 0), 2, 1, 0), EQ),
        (Ellipse.from_angle((0, 0), 2, 1, 0), Ellipse.from_angle((1, 1), 2, 1, 0), NOT_EQ),
        (TwoDSketchSystem([Point(0,0,0)]), TwoDSketchSystem([Point(0,0,0)]), EQ),
        (TwoDSketchSystem([Point(0,0,0)]), TwoDSketchSystem([Point(1,1,1)]), NOT_EQ),
        (TwoDSketchSystem([Point(0,0,0)]), TwoDSketchSystem(), NOT_EQ),
    ]
)
def test_is_equal(geometry, other, expected):
    assert geometry.is_equal(other) == expected