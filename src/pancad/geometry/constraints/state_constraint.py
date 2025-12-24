"""A module providing constraint classes for state constraints between strictly 
two geometry elements. pancad defines state constraints to be constraints 
between 2 elements that have a constant implied value or no value associated 
with them. Perpendicular constraints that force lines to be angled 90 degrees to 
each other and equal constraints that force lines to be the same length are 
examples of state constraints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pancad.geometry.constraints import AbstractConstraint
from pancad.utils.constraints import constraint_args
from pancad.geometry import (
    Circle,
    CircularArc,
    CoordinateSystem,
    Line,
    LineSegment,
    Plane,
)

if TYPE_CHECKING:
    from typing import Type
    from pancad.geometry import AbstractGeometry
    from pancad.geometry.constants import ConstraintReference
    from pancad.utils.constraints import GeometryReference

class AbstractStateConstraint(AbstractConstraint):
    """An abstract class for constraints that force **exactly two** geometry 
    elements to share a constant implied value or some state.
    
    :param reference_pairs: The (AbstractGeometry, ConstraintReference) pairs of
        the geometry to be constrained.
    :param uid: The unique id of the constraint.
    """
    def __init__(self,
                 *reference_pairs: GeometryReference,
                 uid: str=None) -> None:
        self.uid = uid
        self._pairs = constraint_args(*reference_pairs)
        self._validate()
    # Private Methods #
    def _validate(self) -> None:
        if len(self._pairs) != 2:
            raise ValueError("Expected 2 reference_pairs,"
                             f" provided {len(self._pairs)}")
        iterator = iter(len(geometry.get_reference(reference))
                        for geometry, reference in self._pairs)
        first_length = next(iterator)
        if not all(first_length == length for length in iterator):
            raise ValueError("Not all subgeometry are the same dimension")
    # Abstract Shared Static Private Methods
    def _is_combination(self,
                        one_parent_type: Type | tuple[Type],
                        one_reference_geometry: Type | tuple[Type],
                        other_parent_type: Type | tuple[Type],
                        other_reference_geometry: Type | tuple[Type]) -> bool:
        """Returns whether the combination of parents and references in the 
        constraint matches the given combination of types. The order of the 
        parents does not matter.
        
        :param one_parent_type: One of the parent types.
        :param one_reference_geometry: The reference geometry type of the parent 
            found with the first type.
        :param other_parent_type: The other parent type.
        :param other_reference_geometry: The reference geometry type of the parent 
            found with the second type.
        :returns: Whether the relation matches the combination.
        """
        constrained = list(self.get_constrained())
        references = list(self.get_references())
        iterator = iter(self._pairs)
        first, _ = next(iterator)
        second, _ = next(iterator)
        # Check parent types and order them to check against the other.
        if isinstance(first, one_parent_type):
            one_parent, other_parent = constrained
            one_reference, other_reference = references
        elif isinstance(second, one_parent_type):
            other_parent, one_parent = constrained
            other_reference, one_reference = references
        else:
            return False
        if isinstance(one_parent.get_reference(one_reference),
                      one_reference_geometry):
            if isinstance(other_parent, other_parent_type):
                return isinstance(other_parent.get_reference(other_reference),
                                  other_reference_geometry)
        return False
    # Python Dunders #
    def __eq__(self, other: AbstractStateConstraint) -> bool:
        """Checks whether two state constraints are functionally the same by 
        comparing the memory ids of their geometries.
        
        :param other: Another constraint of the same type.
        :returns: Whether the relations are the same.
        """
        geometry_zip = zip(self.get_geometry(), other.get_geometry())
        if isinstance(other, self.__class__):
            return all(g is other_g for g, other_g in geometry_zip)
        return NotImplemented

class Coincident(AbstractStateConstraint):
    """A constraint that forces two geometry elements to occupy the same 
    location.
    """
    def _validate(self) -> None:
        super()._validate()
        if self._is_combination((CoordinateSystem, Line, LineSegment),
                                (LineSegment, Line),
                                (Circle, CircularArc),
                                (Circle, CircularArc)):
            raise TypeError("Line edges cannot be made coincident with"
                            " circle edges.")

class Equal(AbstractStateConstraint):
    """A constraint that forces two geometry elements to have the same 
    context-specific value, such as two line segments sharing the same length. 
    """
    def _validate(self) -> None:
        super()._validate()
        if self._is_combination(LineSegment,
                                LineSegment,
                                (Circle, CircularArc),
                                (Circle, CircularArc)):
            raise TypeError("Line Segments cannot be made equal to circles.")

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
    def _validate(self) -> None:
        super()._validate()
        if self._is_combination((CoordinateSystem, Line, LineSegment, Plane),
                                (LineSegment, Line, Plane),
                                (CoordinateSystem, Line, LineSegment, Plane),
                                (LineSegment, Line, Plane)):
            # NOTE: CAD programs like FreeCAD do allow the line-line tangent
            # condition. This may have some limited use cases, but does not
            # match the mathematical definition of tangent. This case is
            # protected against to limit ambiguities between CAD programs, but
            # may still be translated to coincident in application specific
            # contexts.
            raise TypeError("Lines/Planes cannot be made tangent with"
                            " other Lines/Planes. Use coincident if you mean to"
                            " make the elements occupy the same location")
