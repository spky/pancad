"""A module providing constants for use in solving constraints."""

from enum import StrEnum, auto

class ConstraintVariableName(StrEnum):
    """An enumeration of constraint function variable names."""

    DIRECTION = auto()
    """The unit direction vector of a Line or Axis."""

    LOCATION = auto()
    """The location vector of a Point."""

    NORMAL = auto()
    """The normal vector of a Plane."""

    REF_POINT = auto()
    """The reference point (closest point to the origin) location vector of a Line or Axis."""

    PARAMETER = auto()
    """An arbitrary parameter to represent the parameter of function that must
    be met. For example: A point must exist on a line for it to be coincident,
    but the solver may not care about the exact end result of the location
    parameter, just that it can be solved.
    """

class ConstraintEquationName(StrEnum):
    """An enumeration of constraint equation function names."""

    POINT_POINT_COINCIDENT = auto()
    """Point to Point coincident."""

    POINT_LINE_COINCIDENT = auto()
    """Point to Axis or Axis to Point coincident."""

    POINT_PLANE_COINCIDENT = auto()
    """Point to Plane or Plane to Point coincident."""

    PLANE_PLANE_COINCIDENT = auto()
    """Plane to Plane coincident."""

    POINT_PLANE_DISTANCE = auto()
    """Distance from a plane to a point."""

    PLANE_LINE_DISTANCE = auto()
    """Distance from a plane to a line. Causes the plane and the point """

    PLANE_PLANE_DISTANCE = auto()
    """The distance from one Plane to another Plane. Causes the Planes to have
    an implied parallel constraint so that the distance can be well defined.
    """

    LINE_LINE_COINCIDENT = auto()
    """Line to Line Coincident."""

    FIXED_VECTOR = auto()
    """A vector that must be held in a constant direction."""

    LINE_REF_POINT = auto()
    """Axis/Line Reference Point position vector must be perpendicular to the
    Axis/Line direction to be the point closest to the origin.
    """

    EQUAL_VECTOR = auto()
    """These two vectors must be equal."""

    UNIT_VECTOR = auto()
    """This vector must be a unit vector."""

    CODIRECTIONAL = auto()
    """These two vectors must be codirectional."""

    ANTIPARALLEL = auto()
    """These two vectors must be antiparallel."""

    PARALLEL = auto()
    """These two vectors must be parallel (i.e., codirectional OR antiparallel)."""

    PERPENDICULAR = auto()
    """These two vectors must be perpendicular."""

    PLANE_REF_POINT = auto()
    """Plane Reference Point position vector must be aligned or anti-aligned
    with the plane's normal vector to be the point closest to the origin.
    """

    UNIQUE_VECTOR = auto()
    """This vector must be uniquely representable in pancad. Used for Line definition."""

    NON_ZERO = auto()
    """This vector must be non zero."""
