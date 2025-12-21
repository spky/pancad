"""A module providing a constraint classes for snapto constraints in 2D 
geometry contexts. pancad defines a snapto constraint as one that can be applied 
to geometry with no additional arguments but still meaningfully constrain the 
geometry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pancad.geometry.constraints import AbstractConstraint
from pancad.geometry.constraints.utils import constraint_args
from pancad.geometry import (
    AbstractGeometry,
    Circle,
    CircularArc,
    CoordinateSystem,
    Ellipse,
    Line,
    LineSegment,
    Point,
)

if TYPE_CHECKING:
    from typing import NoReturn
    from pancad.geometry.constraints.utils import GeometryReference
    from pancad.geometry.constants import ConstraintReference

class AbstractSnapTo(AbstractConstraint):
    """An abstract class of constraints that can be applied to a set of **one 
    or two** geometries without any further definition.
    
    :param reference_pairs: The (AbstractGeometry, ConstraintReference) pairs of
        the geometry to be constrained.
    :param uid: The unique id of the constraint.
    """
    # Type Tuples for checking with isinstance()
    CONSTRAINED_TYPES = (
        Circle,
        CircularArc,
        CoordinateSystem,
        Ellipse,
        Line,
        LineSegment,
        Point,
    )
    ONE_GEOMETRY_TYPES = (Line, LineSegment)
    TWO_GEOMETRY_TYPES = (Point,)
    GEOMETRY_TYPES = ONE_GEOMETRY_TYPES + TWO_GEOMETRY_TYPES
    # Type Hints
    def __init__(self,
                 *reference_pairs: GeometryReference,
                 uid: str=None) -> None:
        self.uid = uid
        self._pairs = constraint_args(*reference_pairs)
        self._validate()
    # Properties
    @property
    def _pairs(self) -> list[tuple[AbstractGeometry, ConstraintReference]]:
        return self.__pairs
    @_pairs.setter
    def _pairs(self, value: list[tuple[AbstractGeometry,
                                       ConstraintReference]]) -> None:
        self.__pairs = value
    # Public Methods
    def get_constrained(self) -> tuple[AbstractGeometry]:
        return tuple(geometry for geometry, _ in self._pairs)
    def get_geometry(self) -> tuple[AbstractGeometry]:
        return tuple(geometry.get_reference(reference)
                     for geometry, reference in self._pairs)
    def get_references(self) -> tuple[ConstraintReference]:
        return tuple(reference for _, reference in self._pairs)
    # Private Methods #
    def _validate(self) -> None:
        if any(len(geometry.get_reference(reference)) != 2
               for geometry, reference in self._pairs):
            raise ValueError("subgeometry must be 2D to be constrained")
        if len(self._pairs) not in [1, 2]:
            raise ValueError("Expected 1 or 2 reference_pairs,"
                             f" provided {len(self._pairs)}")
        iterator = iter(len(geometry.get_reference(reference))
                        for geometry, reference in self._pairs)
        first_length = next(iterator)
        if not all(first_length == length for length in iterator):
            raise ValueError("Not all subgeometry are the same dimension")
    # Python Dunders #
    def __eq__(self, other: AbstractSnapTo) -> bool:
        """Checks whether two snapto relations are functionally the same by 
        comparing the memory ids of their constrained geometries.
        
        :param other: Another SnapTo relationship of the same type.
        :returns: Whether the relations are the same.
        """
        geometry_zip = zip(self.get_geometry(), other.get_geometry())
        if isinstance(other, self.__class__):
            return all(g is other_g for g, other_g in geometry_zip)
        return NotImplemented

class Horizontal(AbstractSnapTo):
    """A constraint that sets either a single geometry horizontal or a pair of 
    geometries horizontal relative to each other in a 2D coordinate system. Can 
    constrain:
    
    - :class:`~pancad.geometry.CoordinateSystem`
    - :class:`~pancad.geometry.Circle`
    - :class:`~pancad.geometry.CircularArc`
    - :class:`~pancad.geometry.Ellipse`
    - :class:`~pancad.geometry.Line`
    - :class:`~pancad.geometry.LineSegment`
    - :class:`~pancad.geometry.Point`
    """

class Vertical(AbstractSnapTo):
    """A constraint that sets either a single geometry vertical or a pair of 
    geometries vertical relative to each other in a 2D coordinate system. Can 
    constrain:
    
    - :class:`~pancad.geometry.CoordinateSystem`
    - :class:`~pancad.geometry.Circle`
    - :class:`~pancad.geometry.CircularArc`
    - :class:`~pancad.geometry.Ellipse`
    - :class:`~pancad.geometry.Line`
    - :class:`~pancad.geometry.LineSegment`
    - :class:`~pancad.geometry.Point`
    """
