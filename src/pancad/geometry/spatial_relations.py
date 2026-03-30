"""A module providing functions to check for spatial relations between objects.
pancad defines a spatial relation to be a relation that defines how an object
is located in space relative to another object. Many of these also exist as
constraints in CAD programs.

Example Relations: Coincident, Parallel, Perpendicular, Skew
"""
from functools import singledispatch
import math

import numpy as np

from pancad.constants import AngleConvention as AC
from pancad.geometry import conversion
from pancad.geometry.line import Line
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.plane import Plane
from pancad.geometry.point import Point
from pancad.utils import trigonometry as trig

RELATIVE_TOLERANCE = 1e-9
ABSOLUTE_TOLERANCE = 1e-9

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
def collinear(geometry_a, *geometry_b) -> bool:
    """Returns whether the geometry a and b can lie on the same line.

    :param geometry_a: A Point, Line, or LineSegment
    :param geometry_b: One or more Points, Lines, or LineSegments. All have to be
        the same type.
    :returns: Whether the geometries can all lie on the same line
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

@singledispatch
def coplanar(geometry_a, *geometry_b) -> bool:
    """Returns whether the geometry a and b can lie on the same plane. If you
    want to check whether a geometry is on an existing plane, use coincident.

    :param geometry_a: A Point, Line, or LineSegment
    :param geometry_b: One or more Points, Lines, or LineSegments. All have to be
        the same type.
    :returns: Whether the geometries can all lie on the same plane
    """
    raise NotImplementedError(f"Unsupported 1st type {geometry_a.__class__}")

def crosses():
    """Returns whether the geometry crosses the other."""
    raise NotImplementedError("crosses relation has not yet been implemented.")

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
    raise NotImplementedError(f"Unsupported 1st type {non_plane}")

def symmetric():
    """Returns whether geometry is symmetric about a center geometry."""
    raise NotImplementedError("TODO: Future work, not implemented")

def tangent():
    """Returns whether geometry is tangent to another geometry."""
    raise NotImplementedError("TODO: Future work, not implemented")

def touches():
    """Returns whether geometries are touching."""
    raise NotImplementedError("TODO: Future work, not implemented")

def get_distance_between():
    """Returns the distance between two geometries."""
    raise NotImplementedError("TODO: Future work, not implemented")

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
    :param geometry_b: Another Line, LineSegment, or Plane
    :param opposite: If False, the angle's magnitude is the angle
        clockwise of this element and counterclockwise of the other element
        (which is equal to the angle counterclockwise of this element and
        clockwise of the other element). If True, the angle's magnitude will
        be the supplement/explement of the False angle which is the angle of
        the other two/four quadrants. Note: If the elements are parallel, this
        will cause the function to return pi/tau
    :param convention: The angle convention selection from the
        pancad.constants.angle_convention.AngleConvention enumeration. Used to
        select how the returned angle should be represented (0 to 2pi, -pi to pi,
        etc).
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
def _coincident_point(point: Point,
                      other: Point | Line | LineSegment | Plane) -> bool:
    if isinstance(other, Point):
        return point.is_equal(other)
    if isinstance(other, Line):
        if other.reference_point.is_equal(point):
            # Cover the edge cases where point is the zero vector or if the
            # point is the reference_point
            return True

        point_vector = np.array(point)
        reference_vector = np.array(other.reference_point)
        direction_vector = np.array(other.direction)

        ref_pt_to_pt = (np.dot(point_vector, direction_vector)
                        * direction_vector)
        check_point_tuple = trig.to_1d_tuple(ref_pt_to_pt + reference_vector)

        return np.allclose(check_point_tuple, tuple(point))
    if isinstance(other, LineSegment):
        return coincident(point, other.get_line())
    if isinstance(other, Plane):
        return coincident(other, point)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@coincident.register
def _coincident_line(line: Line,
                     other: Point | Line | LineSegment | Plane) -> bool:
    if isinstance(other, Point):
        return coincident(other, line)
    if isinstance(other, Line):
        return line.is_equal(other)
    if isinstance(other, LineSegment):
        return line.is_equal(other.get_line())
    if isinstance(other, Plane):
        return coincident(other, line)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@coincident.register
def _coincident_linesegment(line_segment: LineSegment,
                            other: Point | Line | LineSegment | Plane) -> bool:
    if isinstance(other, Point):
        return coincident(other, line_segment.get_line())
    if isinstance(other, (LineSegment, Line)):
        return coincident(line_segment.get_line(), other)
    if isinstance(other, Plane):
        return coincident(line_segment.get_line(), other)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@coincident.register
def _coincident_plane(plane: Plane,
                      other: Point | Line | LineSegment | Plane) -> bool:
    if isinstance(other, (Point, Line, LineSegment)):
        return coplanar(other, *conversion.get_3_points_on_plane(plane))
    if isinstance(other, Line):
        points = [*conversion.get_3_points_on_plane(plane),
                  *conversion.get_2_points_on_line(other)]
        return coplanar(*points)
    if isinstance(other, Plane):
        if (plane.reference_point.is_equal(other.reference_point)
                and plane.reference_point.is_equal(Point(0, 0, 0))):
            return np.allclose(plane.normal, other.normal)
        return plane.reference_point.is_equal(other.reference_point)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@collinear.register
def _collinear_point(point: Point, *other: Point | Line | LineSegment) -> bool:
    if all(isinstance(g, Point) for g in other):
        if len(other) == 1:
            # 2 Points are always collinear
            return True
        coordinates = []
        coordinates.append(tuple(point))
        coordinates.extend(map(tuple, other))
        check_matrix = np.column_stack(coordinates)
        return np.linalg.matrix_rank(check_matrix) < 2
    if all(isinstance(g, (Line, LineSegment)) for g in other):
        points = [point]
        for line in other:
            points.append(line.reference_point)
            points.append(Point(np.array(line.reference_point) + line.direction))
        return collinear(*points)
    if all(isinstance(g, LineSegment) for g in other):
        return collinear(point, *list(map(conversion.to_line, other)))
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@collinear.register
def _collinear_line(line: Line, *other: Point | Line | LineSegment) -> bool:
    if all(isinstance(g, Point) for g in other):
        points = [line.reference_point,
                  Point(np.array(line.reference_point) + line.direction),
                  *other]
        return collinear(*points)
    if all(isinstance(g, Line) for g in other):
        for l in other:
            if line != l:
                return False
        return True
    if all(isinstance(g, LineSegment) for g in other):
        return collinear(line, *list(map(conversion.to_line, other)))
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@collinear.register
def _collinear_linesegment(line_segment: LineSegment,
                           *other: Point | Line | LineSegment) -> bool:
    return collinear(line_segment.get_line(), *other)

@coplanar.register
def _coplanar_line(line: Line, *other: Point | Line | LineSegment) -> bool:
    if all(isinstance(g, Point) for g in other):
        points = [*conversion.get_2_points_on_line(line),
                  *other]
        return coplanar(*points)
    if all(isinstance(g, Line) for g in other):
        points = conversion.get_2_points_on_line(line)
        for l in other:
            points.append(l.reference_point)
            points.append(Point(np.array(l.reference_point)
                          + l.direction))
        return coplanar(*points)
    if all(isinstance(g, LineSegment) for g in other):
        return coplanar(line, *[g.get_line() for g in other])
    types = [g.__class__ for g in other]
    raise NotImplementedError(f"Unsupported 2nd types: {types}")

@coplanar.register
def _coplanar_linesegment(line_segment: LineSegment,
                          *other: Point | Line | LineSegment) -> bool:
    if all(isinstance(g, Point) for g in other):
        return coplanar(line_segment.get_line(), *other)
    if all(isinstance(g, Line) for g in other):
        return coplanar(line_segment.get_line(), *other)
    if all(isinstance(g, LineSegment) for g in other):
        return coplanar(line_segment.get_line(), *other)
    types = [g.__class__ for g in other]
    raise NotImplementedError(f"Unsupported 2nd types: {types}")

@coplanar.register
def _coplanar_point(point: Point, *other: Point | Line | LineSegment) -> bool:
    if all(isinstance(g, Point) for g in other):
        if len(other) in [1, 2]:
            return True # Any set of 2 or 3 points are always coplanar
        coord_matrix = np.stack([point, *other])
        return np.linalg.matrix_rank(coord_matrix) == 2
    if all(isinstance(g, (Line, LineSegment)) for g in other):
        if len(other) == 1:
            return True # Any point and line by themselves are always coplanar
        raise ValueError("A point would only be coplanar with multiple lines if "
                         "all the lines intersected at the point or if all the "
                         "lines were collinear, so this is a redundant case that "
                         "collinear or coincident should be used for")
    types = [g.__class__ for g in other]
    raise NotImplementedError(f"Unsupported 2nd type combo: {types}")

@equal.register
def _equal_linesegment(line_segment: LineSegment, *other: LineSegment) -> bool:
    if all(isinstance(g, LineSegment) for g in other):
        length = line_segment.length
        for other_linesegment in other:
            if not np.isclose(length, other_linesegment.length):
                return False
        return True
    types = [g.__class__ for g in other]
    raise NotImplementedError(f"Unsupported 2nd type combo: {types}")

@parallel.register
def _parallel_line(line: Line, other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        return np.allclose(line.direction, other.direction)
    if isinstance(other, LineSegment):
        return np.allclose(line.direction, other.get_line().direction)
    if isinstance(other, Plane):
        return parallel(other, line)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@parallel.register
def _parallel_linesegment(line_segment: LineSegment,
                          other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        return parallel(other, line_segment)
    if isinstance(other, LineSegment):
        return parallel(line_segment.get_line(), other)
    if isinstance(other, Plane):
        return parallel(other, line_segment)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@parallel.register
def _parallel_plane(plane: Plane, other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        return np.isclose(np.dot(other.direction, plane.normal), 0)
    if isinstance(other, LineSegment):
        return parallel(plane, other.get_line())
    if isinstance(other, Plane):
        return np.allclose(plane.normal, other.normal)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@perpendicular.register
def _perpendicular_line(line: Line, other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        if skew(line, other):
            return False
        return np.isclose(np.dot(line.direction, other.direction), 0)
    if isinstance(other, LineSegment):
        return perpendicular(line, other.get_line())
    if isinstance(other, Plane):
        return perpendicular(other, line)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@perpendicular.register
def _perpendicular_line_segment(line_segment: LineSegment,
                               other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        return perpendicular(line_segment.get_line(), other)
    if isinstance(other, LineSegment):
        return perpendicular(line_segment.get_line(), other.get_line())
    if isinstance(other, Plane):
        return perpendicular(other, line_segment)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@perpendicular.register
def _perpendicular_plane(plane: Plane, other: Line | LineSegment | Plane) -> bool:
    if isinstance(other, Line):
        vector_1, vector_2 = conversion.get_2_vectors_on_plane(plane)
        dot_x = np.dot(vector_1, other.direction)
        dot_y = np.dot(vector_2, other.direction)
        return np.isclose(dot_x, 0) and np.isclose(dot_y, 0)
    if isinstance(other, LineSegment):
        return perpendicular(plane, other.get_line())
    if isinstance(other, Plane):
        return np.isclose(np.dot(other.normal, plane.normal), 0)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@project.register
def _project_point(point: Point, plane: Plane) -> Point:
    r_project = point - np.dot(plane.normal, point) * np.array(plane.normal)
    return Point(r_project + plane.reference_point)

@project.register
def _project_line(line: Line, plane: Plane) -> Point | Line:
    if perpendicular(line, plane):
        return project(line.reference_point, plane)
    point1, point2 = conversion.get_2_points_on_line(line)
    return Line.from_two_points(project(point1, plane),
                                project(point2, plane))

@project.register
def _project_line_segment(line_segment: LineSegment,
                         plane: Plane) -> Point | LineSegment:
    if perpendicular(line_segment, plane):
        return project(line_segment.start, plane)
    return LineSegment(project(line_segment.start, plane),
                       project(line_segment.end, plane))

@skew.register
def _skew_line(line: Line, other: Line | LineSegment) -> bool:
    if isinstance(other, Line):
        if parallel(line, other):
            return False
        if len(line) != len(other):
            raise ValueError("Both lines must have the same number of dimensions")
        if len(line) == 2:
            return False
        pt1_to_pt2 = (np.array(line.reference_point)
                      - np.array(other.reference_point))
        cross_product = np.cross(line.direction, other.direction)
        return not np.isclose(np.dot(pt1_to_pt2, cross_product), 0)
    if isinstance(other, LineSegment):
        return skew(line, other.get_line())
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@skew.register
def _skew_line_segment(line_segment: LineSegment,
                       other: Line | LineSegment) -> bool:
    if isinstance(other, Line):
        return skew(other, line_segment)
    if isinstance(other, LineSegment):
        return skew(line_segment.get_line(), other)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_angle_between.register
def _get_angle_between_line(line: Line,
                            other: Line | LineSegment | Plane, *,
                            opposite: bool=False,
                            convention: AC=AC.PLUS_PI) -> float | None:
    if isinstance(other, Line):
        if parallel(line, other):
            if opposite:
                return math.pi
            return 0
        if skew(line, other):
            return None
        return trig.get_vector_angle(line.direction, other.direction,
                                     opposite=opposite, convention=convention)
    if isinstance(other, LineSegment):
        if skew(line, other):
            return None
        return trig.get_vector_angle(
            line.direction, other.direction,
            opposite=opposite, convention=convention
        )
    if isinstance(other, Plane):
        if perpendicular(line, other):
            if convention in (AC.SIGN_PI, AC.SIGN_180):
                raise NotImplementedError("Signed perpendicular angle between"
                                          " lines and planes not yet implemented")
            return math.pi/2
        projected_line = project(line, other)
        return get_angle_between(line, projected_line,
                                 opposite=opposite, convention=convention)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_angle_between.register
def _get_angle_between_line_segment(line_segment: LineSegment,
                                    other: Line | LineSegment | Plane,
                                    opposite: bool=False,
                                    convention: AC=AC.PLUS_PI) -> float | None:
    if isinstance(other, Line):
        if skew(line_segment, other):
            return None
        return trig.get_vector_angle(
            line_segment.direction, other.direction,
            opposite=opposite, convention=convention
        )
    if isinstance(other, LineSegment):
        if skew(line_segment, other):
            return None
        return trig.get_vector_angle(
            line_segment.direction, other.direction,
            opposite=opposite, convention=convention
        )
    if isinstance(other, Plane):
        if perpendicular(line_segment, other):
            if convention in (AC.SIGN_PI, AC.SIGN_180):
                raise NotImplementedError("Signed perpendicular angle between"
                                          " lines and planes not yet implemented")
            return math.pi/2
        projected_line = project(line_segment.get_line(), other)
        return get_angle_between(line_segment, projected_line,
                                 opposite=opposite, convention=convention)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_angle_between.register
def _get_angle_between_plane(plane: Plane,
                             other: Line | LineSegment | Plane, *,
                             opposite: bool=False,
                             convention: AC=AC.PLUS_PI) -> float:
    if isinstance(other, Line):
        if perpendicular(plane, other):
            if convention in (AC.SIGN_PI, AC.SIGN_180):
                raise NotImplementedError("Signed perpendicular angle between"
                                          " lines and planes not yet implemented")
            return math.pi/2
        projected_line = project(other, plane)
        return get_angle_between(projected_line, other, opposite, convention)
    if isinstance(other, LineSegment):
        if perpendicular(plane, other):
            if convention in (AC.SIGN_PI, AC.SIGN_180):
                raise NotImplementedError("Signed perpendicular angle between"
                                          " lines and planes not yet implemented")
            return math.pi/2
        projected_line = project(other.get_line(), plane)
        return get_angle_between(projected_line, other,
                                 opposite=opposite, convention=convention)
    if isinstance(other, Plane):
        # Also called the "Dihedral Angle"
        return trig.get_vector_angle(plane.normal, other.normal,
                                     opposite=opposite, convention=convention)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_intersect.register
def _get_intersect_line(line: Line,
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
            non_zero_rows.append(not (np.isclose(c1, 0) and np.isclose(c2, 0)))

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
            if np.isclose(np.linalg.det(matrix_a_yz), 0):
                return None
            matrix_a = np.delete(matrix_a, (2), axis=0)
        else:
            matrix_a = np.delete(matrix_a, (0), axis=0)
            pt1_to_pt2 = np.delete(pt1_to_pt2, (0), axis=0)

        if np.isclose(np.linalg.det(matrix_a), 0):
            return None
        _, t = np.linalg.inv(matrix_a) @ pt1_to_pt2
        return line.get_parametric_point(t)
    if isinstance(other, LineSegment):
        return get_intersect(line, other.get_line())
    if isinstance(other, Plane):
        return get_intersect(other, line)
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_intersect.register
def _get_intersect_line_segment(line_segment: LineSegment,
                                other: Line | LineSegment | Plane
                                ) -> Point | Line | LineSegment | None:
    if isinstance(other, (Line, LineSegment)):
        return get_intersect(line_segment.get_line(), other)
    if isinstance(other, Plane):
        return get_intersect(other, line_segment.get_line())
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")

@get_intersect.register
def _get_intersect_plane(plane: Plane,
                         other: Line|LineSegment|Plane) -> Point|Line|None:
    if isinstance(other, Line):
        if parallel(plane, other):
            return None
        t_intersect = (
            np.dot(plane.normal,
                   plane.reference_point - other.reference_point)
            / np.dot(plane.normal, other.direction)
        )
        return other.get_parametric_point(t_intersect)
    if isinstance(other, LineSegment):
        return get_intersect(plane, other.get_line())
    if isinstance(other, Plane):
        if parallel(plane, other):
            return None
        nr_vector = np.array(
            [np.dot(plane.normal, plane.reference_point),
             np.dot(other.normal, other.reference_point)]
        )
        n_matrix = np.array([plane.normal, other.normal])
        zeros = [list(map(lambda x: np.isclose(x, 0), c)) for c in n_matrix]
        zero_cols = np.all(zeros, axis=0).tolist()
        zero_index = zero_cols.index(True) if np.any(zero_cols) else 2

        n_matrix = np.delete(n_matrix, zero_index, axis=1)
        coordinates = np.linalg.inv(n_matrix) @ nr_vector
        coordinates = np.insert(coordinates, zero_index, 0)
        return Line(Point(coordinates),
                    np.cross(plane.normal, other.normal))
    raise NotImplementedError(f"Unsupported 2nd type: {other.__class__}")
