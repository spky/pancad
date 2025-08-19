"""A module providing constraint classes for state constraints between strictly 
two geometry elements. PanCAD defines state constraints to be constraints 
between 2 elements that have a constant implied value or no value associated 
with them. Perpendicular constraints that force lines to be angled 90 degrees to 
each other and equal constraints that force lines to be the same length are 
examples of state constraints.
"""

from __future__ import annotations

from abc import abstractmethod
from functools import reduce
from typing import NoReturn, Type

from PanCAD.geometry.constraints.abstract_constraint import AbstractConstraint
from PanCAD.geometry import (
    Point, Line, LineSegment, Plane, CoordinateSystem, Circle
)
from PanCAD.geometry.constants import ConstraintReference

class AbstractStateConstraint(AbstractConstraint):
    """An abstract class for constraints that force **exactly two** geometry 
    elements to share a constant implied value or some state.
    
    :param constrain_a: The first geometry to be constrained.
    :param reference_a: The ConstraintReference of the portion of constrain_a to 
        be constrained.
    :param constrain_b: The second geometry to be constrained.
    :param reference_b: The ConstraintReference of the portion of constrain_b to 
        be constrained.
    :param uid: The unique id of the constraint.
    """
    def __init__(self,
                 constrain_a: ConstrainedType,
                 reference_a: ConstraintReference,
                 constrain_b: ConstrainedType,
                 reference_b: ConstraintReference,
                 uid: str=None) -> None:
        self.uid = uid
        
        if len(constrain_a) == len(constrain_b):
            self._a = constrain_a
            self._a_reference = reference_a
            self._b = constrain_b
            self._b_reference = reference_b
        else:
            raise ValueError("Geometry a and b must have the same number"
                             " of dimensions")
        
        self._validate_parent_geometry()
        self._validate_geometry()
        self._validate_combination()
    
    # Public Methods
    def get_constrained(self) -> tuple[ConstrainedType]:
        return (self._a, self._b)
    
    def get_geometry(self) -> tuple[GeometryType]:
        return (self._a.get_reference(self._a_reference),
                self._b.get_reference(self._b_reference))
    
    def get_references(self) -> tuple[ConstraintReference]:
        return (self._a_reference, self._b_reference)
    
    # Private Methods #
    def _validate_geometry(self) -> NoReturn:
        """Raises an error if the geometries are not one of the allowed types.
        """
        if not any([isinstance(g, self.GEOMETRY_TYPES)
                    for g in self.get_geometry()]):
            classes = [g.__class__ for g in self.get_geometry()]
            raise ValueError(
                f"geometry a and b must be one of:\n{self.GEOMETRY_TYPES}\n"
                f"Given: {classes}"
            )
        elif self._a is self._b:
            raise ValueError("Constrained a/b cannot be the same element")
    
    def _validate_parent_geometry(self) -> NoReturn:
        """Raises an error if the parents (Ex: the line of the start point) of 
        the geometries are not one of the allowed types. Also called constrained 
        geometry.
        """
        if not any([isinstance(g, self.CONSTRAINED_TYPES)
                    for g in self.get_constrained()]):
            classes = [g.__class__ for g in self.get_constrained()]
            raise ValueError(
                f"geometry a and b must be one of:\n{self.CONSTRAINED_TYPES}\n"
                f"Given: {classes}"
            )
    
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
        geometry = list(self.get_geometry())
        
        # Check parent types and 
        if isinstance(self._a, one_parent_type):
            one_parent, other_parent = constrained
            one_reference, other_reference = references
        elif isinstance(self._b, one_parent_type):
            other_parent, one_parent = constrained
            other_reference, one_reference = references
        else:
            return False
        
        if isinstance(one_parent.get_reference(one_reference),
                      one_reference_geometry):
            if isinstance(other_parent, other_parent_type):
                return isinstance(other_parent.get_reference(other_reference),
                                  other_reference_geometry)
            else:
                return False
        else:
            return False
    
    # Abstract Shared Private Methods #
    @abstractmethod
    def _validate_combination(self) -> NoReturn:
        """Raises an error if the geometry combination cannot be constrained."""
    
    # Python Dunders #
    def __eq__(self, other: AbstractStateConstraint) -> bool:
        """Checks whether two state constraints are functionally the same by 
        comparing the memory ids of their geometries.
        
        :param other: Another constraint of the same type.
        :returns: Whether the relations are the same.
        """
        geometry_zip = zip(self.get_geometry(), other.get_geometry())
        if isinstance(other, self.__class__):
            return all([g is other_g for g, other_g in geometry_zip])
        else:
            return NotImplemented
    
    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__}'{self.uid}'"
                f"{repr(self._a)}{repr(self._b)}>")
    
    def __str__(self) -> str:
        return (f"PanCAD {self.__class__.__name__} Constraint '{self.uid}'"
                f" with {repr(self._a)} as geometry a and {repr(self._b)}"
                " as geometry b")

class Coincident(AbstractStateConstraint):
    """A constraint that forces two geometry elements to occupy the same 
    location. Can constrain:
    
    - :class:`~PanCAD.geometry.Circle`
    - :class:`~PanCAD.geometry.CoordinateSystem`
    - :class:`~PanCAD.geometry.Line`
    - :class:`~PanCAD.geometry.LineSegment`
    - :class:`~PanCAD.geometry.Plane`
    - :class:`~PanCAD.geometry.Point`
    """
    CONSTRAINED_TYPES = (Circle, CoordinateSystem,
                         Line, LineSegment,
                         Plane, Point)
    GEOMETRY_TYPES = (Circle, Line, LineSegment, Plane, Point)
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    def _validate_combination(self) -> NoReturn:
        if self._is_combination((CoordinateSystem, Line, LineSegment),
                                (LineSegment, Line),
                                Circle,
                                Circle):
            raise TypeError("Line edges cannot be made coincident with"
                            " circle edges.")

class Equal(AbstractStateConstraint):
    """A constraint that forces two geometry elements to have the same 
    context-specific value, such as two line segments sharing the same length. 
    Can constrain:
    
    - :class:`~PanCAD.geometry.Circle`
    - :class:`~PanCAD.geometry.LineSegment`
    """
    CONSTRAINED_TYPES = (LineSegment, Circle)
    GEOMETRY_TYPES = (LineSegment, Circle)
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    def _validate_combination(self) -> NoReturn:
        if self._is_combination(LineSegment, LineSegment, Circle, Circle):
            raise TypeError("Line Segments cannot be made equal to circles.")

class Parallel(AbstractStateConstraint):
    """A constraint that forces two geometry elements to be side by side and 
    have the same distance continuously between them. Can constrain:
    
    - :class:`~PanCAD.geometry.CoordinateSystem`
    - :class:`~PanCAD.geometry.Line`
    - :class:`~PanCAD.geometry.LineSegment`
    - :class:`~PanCAD.geometry.Plane`
    """
    CONSTRAINED_TYPES = (CoordinateSystem, Line, LineSegment, Plane)
    GEOMETRY_TYPES = (Line, LineSegment, Plane)
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    def _validate_combination(self) -> NoReturn:
        """No known invalid combinations available for parallel."""

class Perpendicular(AbstractStateConstraint):
    """A constraint that forces two geometry elements to be angled 90 degrees 
    relative to each other.
    
    - :class:`~PanCAD.geometry.CoordinateSystem`
    - :class:`~PanCAD.geometry.Line`
    - :class:`~PanCAD.geometry.LineSegment`
    - :class:`~PanCAD.geometry.Plane`
    """
    CONSTRAINED_TYPES = (CoordinateSystem, Line, LineSegment, Plane)
    GEOMETRY_TYPES = (Line, LineSegment, Plane)
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    def _validate_combination(self) -> NoReturn:
        """No known invalid combinations available for perpendicular."""

class Tangent(AbstractStateConstraint):
    """A constraint that forces a line to touch a curve at a point while not 
    also crossing the curve at that point.
    
    - :class:`~PanCAD.geometry.Circle`
    - :class:`~PanCAD.geometry.CoordinateSystem`
    - :class:`~PanCAD.geometry.Line`
    - :class:`~PanCAD.geometry.LineSegment`
    - :class:`~PanCAD.geometry.Plane`
    """
    CONSTRAINED_TYPES = (Circle, CoordinateSystem, Line, LineSegment, Plane)
    GEOMETRY_TYPES = (Circle, Line, LineSegment, Plane)
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    def _validate_combination(self) -> NoReturn:
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