"""A module providing functions to check for spatial relations between objects. 
PanCAD defines a spatial relation to be a relation that defines how an object 
is located in space relative to another object. Many of these also exist as 
constraints in CAD programs.

Example Relations: Coincident, Parallel, Perpendicular, Skew, Intersecting
"""
from functools import singledispatch, partial
import math

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
def parallel_linesegment(line_segment: LineSegment,
                         other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        return parallel(other, line_segment)
    elif isinstance(other, LineSegment):
        return parallel(line_segment.get_line(), other)
    elif isinstance(other, Plane):
        raise NotImplementedError(f"{other.__class__} not implemented yet")
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

def perpendicular():
    pass

@singledispatch
def skew(geometry_a, geometry_b):
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@skew.register
def skew_line(line: Line, other: Line | LineSegment) -> bool:
    if isinstance(other, Line):
        if parallel(line, other):
            return False
        elif len(line) != len(other):
            raise ValueError("Both lines must have the same number of dimensions")
        elif len(line) == 2:
            return False
        
        pt1_to_pt2 = (np.array(line.reference_point)
                      - np.array(other.reference_point))
        cross_product = np.cross(line.direction, other.direction)
        
        if isclose(np.dot(pt1_to_pt2, cross_product), 0):
            return False
        else:
            return True
    elif isinstance(other, LineSegment):
        return skew(line, other.get_line())
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@skew.register
def skew_line_segment(line_segment: LineSegment, other: Line | LineSegment) -> bool:
    if isinstance(other, Line):
        return skew(other, line_segment)
    elif isinstance(other, LineSegment):
        return skew(line_segment.get_line(), other)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

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

@singledispatch
def get_angle_between(geometry_a, geometry_b):
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@get_angle_between.register
def get_angle_between_line(line: Line, other: Line | LineSegment | Plane,
                           supplement: bool=False, signed: bool=False):
    """Returns the value of the angle between this line and the 
    other Line, LineSegment, or Plane.
    
    :param other: A geometry element to find the angle of relative to this line
    :param supplement: If False, the angle's magnitude is the angle 
        clockwise of this line and counterclockwise of the other line 
        (which is equal to the angle counterclockwise of this line and 
        clockwise of the other line). If True, the angle's magnitude will 
        be the supplement of the False angle which is the angle of 
        the other two quadrants. Note: If the lines are parallel, this 
        will cause the function to return pi
    :param signed: If False, the absolute value of the angle will be 
        returned. If True and the line is 2D, angle will be negative the 
        angle between this line's direction and the other line's 
        direction is clockwise
    :returns: The value of the angle between the lines in radians. If the 
        lines are skew, returns None.
    """
    if isinstance(other, Line):
        if parallel(line, other):
            return math.pi if supplement else 0
        elif skew(line, other):
            return None
        
        dot_angle = math.acos(np.dot(line.direction, other.direction))
        magnitude = math.pi - dot_angle if supplement else dot_angle
        
        if len(line) == 2 and signed:
            direction_90_ccw = (-line.direction[1], line.direction[0])
            is_clockwise = np.dot(direction_90_ccw, other.direction) < 0
            return -magnitude if is_clockwise ^ supplement else magnitude
        elif len(line) == 3 and signed:
            raise NotImplementedError("Signed angle between 3D lines not yet"
                                      " implemented")
        else:
            return magnitude
    elif isinstance(other, LineSegment):
        return get_angle_between(line, other.get_line(), supplement, signed)
    elif isinstance(other, Plane):
        raise NotImplementedError(f"{other.__class__} not implemented yet")
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_angle_between.register
def get_angle_between_line_segment(line_segment: LineSegment,
                                   other: Line | LineSegment | Plane,
                                   supplement: bool=False, signed: bool=False):
    if isinstance(other, Line):
        return get_angle_between(line_segment.get_line(), other,
                                 supplement, signed)
    elif isinstance(other, LineSegment):
        return get_angle_between(line_segment.get_line(), other.get_line(),
                                 supplement, signed)
    elif isinstance(other, Plane):
        raise NotImplementedError(f"{other.__class__} not implemented yet")
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")