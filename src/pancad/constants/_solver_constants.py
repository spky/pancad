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
    FIXED_POINT = auto()
    """A point that must be placed at a constant location."""
    LINE_REF_POINT = auto()
    """Axis/Line Reference Point position vector must be perpendicular to the
    Axis/Line direction to be the point closest to the origin.
    """
    UNIT_VECTOR = auto()
    """This vector must be a unit vector."""
