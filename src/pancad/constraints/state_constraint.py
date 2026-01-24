"""A module providing constraint classes for state constraints between strictly
two geometry elements. pancad defines state constraints to be constraints
between 2 elements that have a constant implied value or no value associated
with them. Perpendicular constraints that force lines to be angled 90 degrees to
each other and equal constraints that force lines to be the same length are
examples of state constraints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pancad.abstract import AbstractConstraint

if TYPE_CHECKING:
    from pancad.abstract import AbstractGeometry, AbstractGeometrySystem

class AbstractStateConstraint(AbstractConstraint):
    """An abstract class for constraints that force **exactly two** geometry
    elements to share a constant implied value or some state.

    :param geometry: The geometries to be constrained.
    :param uid: The unique id of the constraint.
    """
    def __init__(self, *geometry: AbstractGeometry,
                 uid: str=None, system: AbstractGeometrySystem=None) -> None:
        self.uid = uid
        super().__init__(system)
        if len(geometry) != 2:
            raise ValueError(f"Expected 2 geometries, provided {geometry}")
        self._geometry = geometry

class Coincident(AbstractStateConstraint):
    """A constraint that forces two geometry elements to occupy the same
    location.
    """

class Equal(AbstractStateConstraint):
    """A constraint that forces two geometry elements to have the same
    context-specific value, such as two line segments sharing the same length.
    """

class Parallel(AbstractStateConstraint):
    """A constraint that forces two geometry elements to be side by side and
    have the same distance continuously between them.
    """

class Perpendicular(AbstractStateConstraint):
    """A constraint that forces two geometry elements to be angled 90 degrees
    relative to each other.
    """

class Tangent(AbstractStateConstraint):
    """A constraint that forces a line to touch a curve at a point while not
    also crossing the curve at that point.
    """

class AlignAxes(AbstractStateConstraint):
    """A constraint that forces two coordinate systems to share the same
    location and the same respective axis directions.
    """