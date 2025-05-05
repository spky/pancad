"""A module providing functions to check for spatial relations between objects. 
PanCAD defines a spatial relation to be a relation that defines how an object 
is located in space relative to another object. Many of these also exist as 
constraints in CAD programs.

Example Relations: Coincident, Parallel, Perpendicular, Skew, Intersecting
"""
from functools import singledispatch, partial

import numpy as np

from PanCAD.geometry import Point, Line, LineSegment, Plane
from PanCAD.utils import trigonometry as trig
from PanCAD.utils import verification

RELATIVE_TOLERANCE = 1e-9
ABSOLUTE_TOLERANCE = 1e-9
isclose = partial(verification.isclose,
                  abs_tol=ABSOLUTE_TOLERANCE, rel_tol=RELATIVE_TOLERANCE,
                  nan_equal=True)

@singledispatch
def coincident(geometry_a, geometry_b):
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@coincident.register
def coincident_point(point: Point,
                     other: Point | Line | LineSegment | Plane) -> bool:
    if isinstance(other, Point):
        return point == other
    elif isinstance(other, Line):
        if other.reference_point == point:
            # Cover the edge cases where point is the zero vector or if the 
            # point is the reference_point
            return True
        
        point_vector = np.array(point)
        reference_vector = np.array(other.reference_point)
        direction_vector = np.array(other.direction)
        
        ref_pt_to_pt = (np.dot(point_vector, direction_vector)
                        * direction_vector)
        check_point_tuple = trig.to_1D_tuple(ref_pt_to_pt + reference_vector)
        
        return True if isclose(check_point_tuple, tuple(point)) else False
    elif isinstance(other, LineSegment):
        return coincident(point, other.get_line())
    elif isinstance(other, Plane):
        raise NotImplementedError(f"{other.__class__} not implemented yet")
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@coincident.register
def coincident_line(line: Line,
                    other: Point | Line | LineSegment | Plane) -> bool:
    if isinstance(other, Point):
        return coincident(other, line)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@coincident.register
def coincident_linesegment(linesegment: LineSegment,
                           other: Point | Line | LineSegment | Plane) -> bool:
    if isinstance(other, Point):
        return coincident(other, linesegment.get_line())
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

def collinear():
    pass

def coplanar():
    pass

def crosses():
    pass

def equal():
    pass

def equal_length():
    pass

def intersect():
    pass

@singledispatch
def parallel(geometry_a, geometry_b):
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@parallel.register
def parallel_line(line: Line, other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        return isclose(line.direction, other.direction)
    elif isinstance(other, LineSegment):
        return isclose(line.direction, other.get_line().direction)
    elif isinstance(other, Plane):
        raise NotImplementedError(f"{other.__class__} not implemented yet")
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@parallel.register
def parallel_linesegment(line: LineSegment,
                         other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        return parallel(other, line)
    elif isinstance(other, LineSegment):
        return parallel(line.get_line(), other)
    elif isinstance(other, Plane):
        raise NotImplementedError("Planes not implemented yet")

def perpendicular():
    pass

def skew():
    pass

def symmetric():
    pass

def tangent():
    pass

def touches():
    pass

def get_distance_between():
    pass

def get_intersection():
    pass

def get_angle_between():
    pass