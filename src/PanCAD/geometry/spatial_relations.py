"""A module providing functions to check for spatial relations between objects. 
PanCAD defines a spatial relation to be a relation that defines how an object 
is located in space relative to another object. Many of these also exist as 
constraints in CAD programs.

Example Relations: Coincident, Parallel, Perpendicular, Skew
"""
from functools import singledispatch, partial
import math

import numpy as np

from PanCAD.constants.angle_convention import AngleConvention as AC
from PanCAD.geometry import Point, Line, LineSegment, Plane, conversion
from PanCAD.utils import trigonometry as trig
from PanCAD.utils import comparison

RELATIVE_TOLERANCE = 1e-9
ABSOLUTE_TOLERANCE = 1e-9
isclose = partial(comparison.isclose, nan_equal=True)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=True)

###############################################################################
# Single Dispatches
###############################################################################

@singledispatch
def coincident(geometry_a, geometry_b) -> bool:
    """Returns whether geometry a is coincident to geometry b.
    
    :param geometry_a: A Point, Line, LineSegment, or Plane
    :param geometry_b: One or more Points, Lines, LineSegments or Planes.
    :returns: Whether the geometries are coincident to geometry a
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@singledispatch
def collinear(geometry_a, geometry_b) -> bool:
    """Returns whether the geometry a and b can lie on the same line.
    
    :param geometry_a: A Point, Line, or LineSegment
    :param geometry_b: One or more Points, Lines, or LineSegments. All have to be 
        the same type.
    :returns: Whether the geometries can all lie on the same line
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@singledispatch
def coplanar(geometry_a, geometry_b) -> bool:
    """Returns whether the geometry a and b can lie on the same plane. If you 
    want to check whether a geometry is on an existing plane, use coincident.
    
    :param geometry_a: A Point, Line, or LineSegment
    :param geometry_b: One or more Points, Lines, or LineSegments. All have to be 
        the same type.
    :returns: Whether the geometries can all lie on the same plane
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

def crosses():
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@singledispatch
def equal(geometry_a, geometry_b):
    """Returns whether geometry a and geometry b are equal lengths
    
    :param geometry_a: A LineSegment
    :param geometry_b: One or more other LineSegments
    :returns: Whether geometry a and b are equal length
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@singledispatch
def parallel(geometry_a, geometry_b) -> bool:
    """Returns whether the geometry a and b are parallel.
    
    :param geometry_a: A Line, LineSegment, or Plane
    :param geometry_b: Another Line, LineSegment or Plane
    :returns: Whether the geometries are parallel
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@singledispatch
def perpendicular(geometry_a, geometry_b) -> bool:
    """Returns whether the geometry a and b intersects and are oriented 90 degrees 
    to each other.
    
    :param geometry_a: A Line, LineSegment, or Plane
    :param geometry_b: Another Line, LineSegment, or Plane
    :returns: Whether the geometries are perpendicular to each other
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@singledispatch
def project(non_plane, plane):
    """Returns the projection of the non_plane geometry onto the plane.
    
    :param non_plane: A Point, Line, or LineSegment
    :param plane: A Plane
    :returns: The geometry representing the projection of the non plane geometry 
        onto the plane
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

def symmetric():
    raise NotImplementedError(f"TODO: Future work, not implemented")

def tangent():
    raise NotImplementedError(f"TODO: Future work, not implemented")

def touches():
    raise NotImplementedError(f"TODO: Future work, not implemented")

def get_distance_between():
    raise NotImplementedError(f"TODO: Future work, not implemented")

@singledispatch
def get_intersect(geometry_a, geometry_b) -> Point | Line | LineSegment:
    """Returns the intersection of geometry a and b as a Point, Line, LineSegment 
    or None depending on the input types. Note: LineSegments are treated as 
    infinitely long to find the intersection, if you want to know whether the 
    finite line actually crosses the other geometry use crosses() instead.
    
    :param geometry_a: A Line, LineSegment, or Plane
    :param geometry_b: Another Line, LineSegment, or Plane
    :returns: The intersection if it exists, otherwise None
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@singledispatch
def get_angle_between(geometry_a, geometry_b) -> float | None:
    """Returns the value of the angle between geometry a and b. This function 
    dispatches to a more specific function based on the type of the first 
    argument.
    
    :param geometry_a: A Line, LineSegment, or Plane
    :param other: Another Line, LineSegment, or Plane
    :param supplement: If False, the angle's magnitude is the angle 
        clockwise of this element and counterclockwise of the other element 
        (which is equal to the angle counterclockwise of this element and 
        clockwise of the other element). If True, the angle's magnitude will 
        be the supplement of the False angle which is the angle of 
        the other two quadrants. Note: If the elements are parallel, this 
        will cause the function to return pi
    :param signed: If False, the absolute value of the angle will be 
        returned. If True and the element is 2D, angle will be negative if the 
        angle between this element's direction and the other element's 
        direction is clockwise
    :returns: The value of the angle between the geometries in radians. If the 
        elements (usually lines) are skew, returns None.
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@singledispatch
def skew(geometry_a, geometry_b) -> bool:
    """Returns whether geometry a and b are skew.
    
    :param geometry_a: A Line or LineSegment
    :param geometry_b: Another Line or LineSegment
    :returns: Whether the geometries are skew to one another
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

###############################################################################
# Registers
###############################################################################

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
        return coincident(other, point)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@coincident.register
def coincident_line(line: Line,
                    other: Point | Line | LineSegment | Plane) -> bool:
    if isinstance(other, Point):
        return coincident(other, line)
    elif isinstance(other, Line):
        return line == other
    elif isinstance(other, LineSegment):
        return line == other.get_line()
    elif isinstance(other, Plane):
        return coincident(other, line)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@coincident.register
def coincident_linesegment(linesegment: LineSegment,
                           other: Point | Line | LineSegment | Plane) -> bool:
    if isinstance(other, Point):
        return coincident(other, linesegment.get_line())
    elif isinstance(other, (LineSegment, Line)):
        return coincident(linesegment.get_line(), other)
    elif isinstance(other, Plane):
        return coincident(line_segment.get_line(), other)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@coincident.register
def coincident_plane(plane: Plane,
                     other: Point | Line | LineSegment | Plane) -> bool:
    if isinstance(other, (Point, Line, LineSegment)):
        return coplanar(other, *conversion.get_3_points_on_plane(plane))
    elif isinstance(other, Line):
        points = [*conversion.get_3_points_on_plane(plane),
                  *conversion.get_2_points_on_line(other)]
        return coplanar(*points)
    elif isinstance(other, Plane):
        if plane.reference_point == other.reference_point == Point(0, 0, 0):
            return isclose(plane.normal, other.normal)
        else:
            return plane.reference_point == other.reference_point
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@collinear.register
def collinear_point(point: Point, *other: Point | Line | LineSegment) -> bool:
    if all(isinstance(g, Point) for g in other):
        if len(other) == 1:
            # 2 Points are always collinear
            return True
        else:
            coordinates = []
            coordinates.append(tuple(point))
            coordinates.extend(map(tuple, other))
            check_matrix = np.column_stack(coordinates)
            return True if np.linalg.matrix_rank(check_matrix) < 2 else False
    elif all(isinstance(g, (Line, LineSegment)) for g in other):
        points = [point]
        for line in other:
            points.append(line.reference_point)
            points.append(Point(np.array(line.reference_point) + line.direction))
        return collinear(*points)
    elif all(isinstance(g, LineSegment) for g in other):
        return collinear(point, *list(map(conversion.to_line, other)))
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@collinear.register
def collinear_line(line: Line, *other: Point | Line | LineSegment) -> bool:
    if all(isinstance(g, Point) for g in other):
        points = [line.reference_point,
                  Point(np.array(line.reference_point) + line.direction),
                  *other]
        return collinear(*points)
    elif all(isinstance(g, Line) for g in other):
        for l in other:
            if line != l:
                return False
        return True
    elif all(isinstance(g, LineSegment) for g in other):
        return collinear(line, *list(map(conversion.to_line, other)))
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@collinear.register
def collinear_linesegment(line_segment: LineSegment,
                          *other: Point | Line | LineSegment) -> bool:
    return collinear(line_segment.get_line(), *other)

@coplanar.register
def coplanar_line(line: Line, *other: Point | Line | LineSegment) -> bool:
    if all(isinstance(g, Point) for g in other):
        points = [*conversion.get_2_points_on_line(line),
                  *other]
        return coplanar(*points)
    elif all(isinstance(g, Line) for g in other):
        points = conversion.get_2_points_on_line(line)
        for l in other:
            points.append(l.reference_point)
            points.append(Point(np.array(l.reference_point)
                          + l.direction))
        return coplanar(*points)
    elif all(isinstance(g, LineSegment) for g in other):
        return coplanar(line, *[g.get_line() for g in other])
    else:
        types = [g.__class__ for g in other]
        raise NotImplementedError(f"Unsupported 2nd types: {types}")

@coplanar.register
def coplanar_linesegment(line_segment: LineSegment,
                         *other: Point | Line | LineSegment) -> bool:
    if all(isinstance(g, Point) for g in other):
        return coplanar(line_segment.get_line(), *other)
    elif all(isinstance(g, Line) for g in other):
        return coplanar(line_segment.get_line(), *other)
    elif all(isinstance(g, LineSegment) for g in other):
        return coplanar(line_segment.get_line(), *other)
    else:
        types = [g.__class__ for g in other]
        raise NotImplementedError(f"Unsupported 2nd types: {types}")

@coplanar.register
def coplanar_point(point: Point, *other: Point | Line | LineSegment) -> bool:
    if all(isinstance(g, Point) for g in other):
        if len(other) in [1, 2]:
            return True # Any set of 2 or 3 points are always coplanar
        else:
            coord_matrix = np.stack([point, *other])
            return np.linalg.matrix_rank(coord_matrix) == 2
    elif all(isinstance(g, (Line, LineSegment)) for g in other):
        if len(other) == 1:
            return True # Any point and line by themselves are always coplanar
        raise ValueError("A point would only be coplanar with multiple lines if "
                         "all the lines intersected at the point or if all the "
                         "lines were collinear, so this is a redundant case that "
                         "collinear or coincident should be used for")
    else:
        types = [g.__class__ for g in other]
        raise NotImplementedError(f"Unsupported 2nd type combo: {types}")

@equal.register
def equal_linesegment(line_segment: LineSegment, *other: LineSegment) -> bool:
    if all(isinstance(g, LineSegment) for g in other):
        length = line_segment.length
        for other_linesegment in other:
            if not isclose(length, other_linesegment.length):
                return False
        return True
    else:
        types = [g.__class__ for g in other]
        raise NotImplementedError(f"Unsupported 2nd type combo: {types}")

@parallel.register
def parallel_line(line: Line, other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        return isclose(line.direction, other.direction)
    elif isinstance(other, LineSegment):
        return isclose(line.direction, other.get_line().direction)
    elif isinstance(other, Plane):
        return parallel(other, line)
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
        return parallel(other, line_segment)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@parallel.register
def parallel_plane(plane: Plane, other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        return isclose(np.dot(other.direction, plane.normal), 0)
    elif isinstance(other, LineSegment):
        return parallel(plane, other.get_line())
    elif isinstance(other, Plane):
        return isclose(plane.normal, other.normal)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@perpendicular.register
def perpendicular_line(line: Line, other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        if skew(line, other):
            return False
        else:
            return isclose(np.dot(line.direction, other.direction), 0)
    elif isinstance(other, LineSegment):
        return perpendicular(line, other.get_line())
    elif isinstance(other, Plane):
        return perpendicular(other, line)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@perpendicular.register
def perpendicular_line_segment(line_segment: LineSegment,
                               other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        return perpendicular(line_segment.get_line(), other)
    elif isinstance(other, LineSegment):
        return perpendicular(line_segment.get_line(), other.get_line())
    elif isinstance(other, Plane):
        return perpendicular(other, line_segment)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@perpendicular.register
def perpendicular_plane(plane: Plane, other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        vector_1, vector_2 = conversion.get_2_vectors_on_plane(plane)
        
        plane_x = trig.rotation_x(math.pi/2) @ plane.normal
        plane_y = trig.rotation_y(math.pi/2) @ plane.normal
        
        dot_x = np.dot(vector_1, other.direction)
        dot_y = np.dot(vector_2, other.direction)
        
        return isclose0(dot_x) and isclose0(dot_y)
    elif isinstance(other, LineSegment):
        return perpendicular(plane, other.get_line())
    elif isinstance(other, Plane):
        return isclose(np.dot(other.normal, plane.normal), 0)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@project.register
def project_point(point: Point, plane: Plane) -> Point:
    r_project = point - np.dot(plane.normal, point) * np.array(plane.normal)
    return Point(r_project + plane.reference_point)

@project.register
def project_line(line: Line, plane: Plane) -> Point | Line:
    if perpendicular(line, plane):
        return project(line.reference_point, plane)
    else:
        point1, point2 = conversion.get_2_points_on_line(line)
        return Line.from_two_points(project(point1, plane),
                                    project(point2, plane))

@project.register
def project_line_segment(line_segment: LineSegment,
                         plane: Plane) -> Point | LineSegment:
    if perpendicular(line_segment, plane):
        return project(line_segment.point_a, plane)
    else:
        return LineSegment(project(line_segment.point_a, plane),
                           project(line_segment.point_b, plane))

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

@get_angle_between.register
def get_angle_between_line(line: Line,
                           other: Line | LineSegment | Plane, *,
                           opposite: bool=False,
                           convention: AC=AC.PLUS_PI) -> float | None:
    if isinstance(other, Line):
        if parallel(line, other):
            if opposite:
                return math.pi
            else:
                return 0
        elif skew(line, other):
            return None
        return trig.get_vector_angle(line.direction, other.direction,
                                     opposite=opposite, convention=convention)
    elif isinstance(other, LineSegment):
        return get_angle_between(line, other.get_line(),
                                 opposite=opposite, convention=convention)
    elif isinstance(other, Plane):
        if perpendicular(line, other):
            if convention in (AC.SIGN_PI, AC.SIGN_180):
                raise NotImplementedError("Signed perpendicular angle between"
                                          " lines and planes not yet implemented")
            else:
                return math.pi/2
        else:
            projected_line = project(line, other)
            return get_angle_between(line, projected_line,
                                     opposite=opposite, convention=convention)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_angle_between.register
def get_angle_between_line_segment(line_segment: LineSegment,
                                   other: Line | LineSegment | Plane,
                                   opposite: bool=False,
                                   convention: AC=AC.PLUS_PI) -> float | None:
    if isinstance(other, Line):
        return get_angle_between(line_segment.get_line(), other,
                                 opposite=opposite, convention=convention)
    elif isinstance(other, LineSegment):
        return trig.get_vector_angle(
            line_segment.get_vector_ab(), other.get_vector_ab(),
            opposite=opposite, convention=convention
        )
    elif isinstance(other, Plane):
        raise NotImplementedError(f"{other.__class__} not implemented yet")
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_angle_between.register
def get_angle_between_plane(plane: Plane,
                            other: Line | LineSegment | Plane, *,
                            opposite: bool=False,
                            convention: AC=AC.PLUS_PI) -> float:
    if isinstance(other, Line):
        if perpendicular(plane, other):
            if convention in (AC.SIGN_PI, AC.SIGN_180):
                raise NotImplementedError("Signed perpendicular angle between"
                                          " lines and planes not yet implemented")
            else:
                return math.pi/2
        else:
            projected_line = project(other, plane)
            return get_angle_between(projected_line, other, opposite, convention)
    elif isinstance(other, LineSegment):
        raise NotImplementedError(f"{other.__class__} not implemented yet")
    elif isinstance(other, Plane):
        # Also called the "Dihedral Angle"
        return trig.get_vector_angle(plane.normal, other.normal,
                                     opposite=opposite, convention=convention)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_intersect.register
def get_intersect_line(line: Line,
                       other: Line | LineSegment | Plane
                       ) -> Point | Line | LineSegment | None:
    if isinstance(other, Line):
        if parallel(line, other) or skew(line, other):
            return None
        
        pt1_to_pt2 = (line.reference_point.vector() 
                      - other.reference_point.vector())
        matrix_a = np.column_stack(
            (np.array(other.direction), -np.array(line.direction))
        )
        
        non_zero_rows = []
        for c1, c2 in zip(line.direction, other.direction):
            non_zero_rows.append(not (isclose(c1, 0) and isclose(c2, 0)))
        
        if len(line) == 2:
            pass # 2D will always intersect since they are not parallel
        elif non_zero_rows[0] and non_zero_rows[1] and not non_zero_rows[2]:
            matrix_a = np.delete(matrix_a, (2), axis=0)
            pt1_to_pt2 = np.delete(pt1_to_pt2, (2), axis=0)
        elif non_zero_rows[0] and not non_zero_rows[1] and non_zero_rows[2]:
            matrix_a = np.delete(matrix_a, (1), axis=0)
            pt1_to_pt2 = np.delete(pt1_to_pt2, (1), axis=0)
        elif all(non_zero_rows):
            matrix_a_yz = np.delete(matrix_a, (0), axis=0)
            if isclose(np.det(matrix_a_yz), 0):
                return None
            matrix_a = np.delete(matrix_a, (2), axis=0)
        else:
            matrix_a = np.delete(matrix_a, (0), axis=0)
            pt1_to_pt2 = np.delete(pt1_to_pt2, (0), axis=0)
        
        if isclose(np.linalg.det(matrix_a), 0):
            return None
        else:
            _, t = np.linalg.inv(matrix_a) @ pt1_to_pt2
            return line.get_parametric_point(t)
    elif isinstance(other, LineSegment):
        return get_intersect(line, other.get_line())
    elif isinstance(other, Plane):
        return get_intersect(other, line)
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_intersect.register
def get_intersect_line_segment(line_segment: LineSegment,
                               other: Line | LineSegment | Plane
                               ) -> Point | Line | LineSegment | None:
    if isinstance(other, (Line, LineSegment)):
        return get_intersect(line_segment.get_line(), other)
    elif isinstance(other, Plane):
        return get_intersect(other, line_segment.get_line())
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_intersect.register
def get_intersect_plane(plane: Plane,
                        other: Line | LineSegment | Plane
                        ) -> Point | Line | None:
    if isinstance(other, Line):
        if parallel(plane, other):
            return None
        else:
            t_intersect = (
                np.dot(plane.normal,
                       plane.reference_point - other.reference_point)
                / np.dot(plane.normal, other.direction)
            )
            return other.get_parametric_point(t_intersect)
    elif isinstance(other, LineSegment):
        return get_intersect(plane, other.get_line())
    elif isinstance(other, Plane):
        if parallel(plane, other):
            return None
        else:
            nr_vector = np.array(
                [np.dot(plane.normal, plane.reference_point),
                 np.dot(other.normal, other.reference_point)]
            )
            n_matrix = np.array([plane.normal, other.normal])
            zeros = [list(map(isclose0, c)) for c in n_matrix]
            zero_cols = np.all(zeros, axis=0).tolist()
            zero_index = zero_cols.index(True) if np.any(zero_cols) else 2
            
            n_matrix = np.delete(n_matrix, zero_index, axis=1)
            coordinates = np.linalg.inv(n_matrix) @ nr_vector
            coordinates = np.insert(coordinates, zero_index, 0)
            return Line(Point(coordinates),
                        np.cross(plane.normal, other.normal))
        
    else:
        raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")
