"""A module providing functions to convert parts of pancad geometry into other 
representations while avoiding the need for circular imports. Example: a 
LineSegment can be used to define a Line.
"""
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import numpy as np

from pancad.utils import trigonometry
from pancad.geometry import Point
from pancad.utils import comparison

if TYPE_CHECKING:
    from pancad.geometry import Line, LineSegment, Plane

isclose = partial(comparison.isclose, nan_equal=True)

def to_line(line_segment: LineSegment) -> Line:
    return line_segment.get_line()

def get_2_points_on_line(line: Line) -> list[Point, Point]:
    """Returns 3 points on the plane, useful for comparisons based around 
    sets of points. The points are the point closest to the origin and 1 point 
    one unit vector away in the from the point closest to the origin."""
    return [line.reference_point,
            Point(np.array(line.reference_point) + line.direction)]

def get_2_vectors_on_plane(plane: Plane) -> tuple[tuple, tuple]:
    """Returns 2 unit vectors that are normal to the plane's normal vector."""
    a, b, c = plane.normal
    if not isclose(c, 0):
        a1 = a + 1
        b1 = b + 1
        c1 = -(a*a1 + b*b1)/c
    elif not isclose(b, 0):
        a1 = a + 1
        b1 = a*a1 / b
        c1 = c + 1
    else: # b and c are close to 0
        a1 = 0
        b1 = b + 1
        c1 = c + 1
    vector_1 = trigonometry.get_unit_vector((a1, b1, c1))
    vector_2 = trigonometry.get_unit_vector(
        np.cross(plane.normal, vector_1)
    )
    return vector_1, vector_2

def get_3_points_on_plane(plane: Plane) -> list[Point, Point, Point]:
    """Returns 3 points on the plane, useful for comparisons based around 
    sets of points. The points are the point closest to the origin and 2 points 
    one unit vector away in the x and y directions from the point closest to 
    the origin."""
    points = []
    vector_1, vector_2 = get_2_vectors_on_plane(plane)
    points.append(plane.reference_point)
    points.append(
        Point(vector_1 + np.array(plane.reference_point))
    )
    points.append(
        Point(vector_2 + np.array(plane.reference_point))
    )
    
    return points