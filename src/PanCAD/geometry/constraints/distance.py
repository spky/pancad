"""A module providing classes for horizontal, vertical, and direct distance 
constraints. Distance can be used to force geometry elements to be at set 
distances from specified portions of each other. The horizontal and vertical 
variants can only be applied to 2D geometry and allow the distance 
to be limited to the x or y direction respectively.
"""
from __future__ import annotations

from functools import reduce
from abc import ABC, abstractmethod

from PanCAD.geometry import Point, Line, LineSegment, CoordinateSystem, Plane
from PanCAD.geometry.constants import ConstraintReference

class AbstractDistance(ABC):
    
    def __init__(self,
                 geometry_a: GeometryType, reference_a: ConstraintReference,
                 geometry_b: GeometryType, reference_b: ConstraintReference,
                 value: int | float,
                 uid: str=None):
        self.uid = uid
        self._a = geometry_a
        self._a_reference = reference_a
        self._b = geometry_b
        self._b_reference = reference_b
        self.value = value
    
    # Shared Public Methods #
    def get_a(self) -> GeometryType:
        """Returns geometry a."""
        return self._a
    
    def get_a_reference(self) -> ConstraintReference:
        """Returns the ConstraintReference of geometry a."""
        return self._a_reference
    
    def get_a_constrained(self) -> ReferenceType:
        """Returns the constrained reference geometry of geometry a."""
        return self._a.get_reference(self._a_reference)
    
    def get_b(self) -> GeometryType:
        """Returns geometry a"""
        return self._b
    
    def get_b_reference(self) -> ConstraintReference:
        """Returns the ConstraintReference of geometry b."""
        return self._b_reference
    
    def get_b_constrained(self) -> ReferenceType:
        """Returns the constrained reference geometry of geometry b."""
        return self._b.get_reference(self._b_reference)
    
    def get_constrained(self) -> tuple[GeometryType]:
        """Returns a tuple of the constrained geometry parents"""
        return (self.get_a(), self.get_b())
    
    # Shared Dunder Methods
    def __repr__(self) -> str:
        a = self.get_a()
        b = self.get_b()
        value = self.value
        name = self.__class__.__name__
        return f"<{name}'{self.uid}'{repr(a)}{repr(b)}d{value}>"
    
    def __str__(self) -> str:
        a = self.get_a()
        b = self.get_b()
        value = self.value
        name = self.__class__.__name__
        return (f"PanCAD {name} Constraint '{self.uid}' with {repr(a)} as"
                f" geometry a and {repr(b)} as geometry b and value {value}")
    
    def __eq__(self, other: AbstractDistance) -> bool:
        """Checks whether two distance relations are functionally the same by 
        comparing the memory ids of their geometries and the values of the 
        constraints.
        
        :param other: Another distance relationship of the same type.
        :returns: Whether the relations are functionally the same.
        """
        if isinstance(other, self.__class__):
            return (
                self.get_a_constrained() is other.get_a_constrained()
                and self.get_b_constrained() is other.get_b_constrained()
                and self.value == other.value
            )
        else:
            return NotImplemented
    
    # Abstract Class Variables
    @property
    @abstractmethod
    def GEOMETRY_TYPES(self):
        """Allowable parent geometry types used with with isinstance"""
    
    @property
    @abstractmethod
    def GeometryType(self):
        """Allowable parent geometry type hint"""
    
    @property
    @abstractmethod
    def REFERENCE_TYPES(self):
        """Allowable reference sub geometry types used with isinstance"""
    
    @property
    @abstractmethod
    def ReferenceType(self):
        """Allowable reference geometry type hint"""
    
    # Abstract Methods
    @abstractmethod
    def check(self) -> bool:
        """Returns whether the constraint is met by the geometry."""
    
    @abstractmethod
    def _validate_parent_geometry(self):
        """Raises an error if the geometries are not one of the allowed types"""
    
    @abstractmethod
    def _validate_constrained_geometry(self):
        """Raises an error if the constrained geometries are not one of the 
        allowed types"""

class AbstractDistance2D(AbstractDistance):
    """An abstract class for 2D distance constraints"""
    GEOMETRY_TYPES = (Point, Line, LineSegment, CoordinateSystem)
    REFERENCE_TYPES = (Point, Line, LineSegment)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    ReferenceType = reduce(lambda x, y: x | y, REFERENCE_TYPES)
    
    # Private Methods #
    def _validate_parent_geometry(self):
        """Raises an error if the geometries are not one of the allowed 
        types"""
        a = self.get_a()
        b = self.get_b()
        if (not isinstance(a, self.GEOMETRY_TYPES)
                or not isinstance(b, self.GEOMETRY_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.GEOMETRY_TYPES}\n"
                f"Given: {a.__class__} and {b.__class__}"
            )
        elif not len(a) == len(b) == 2:
            raise ValueError("geometry must be 2D")
        elif a is b:
            raise ValueError("geometry a/b cannot be the same geometry element")
    
    def _validate_constrained_geometry(self):
        """Raises an error if the constrained geometries are not one of the 
        allowed types"""
        a_constrain = self.get_a_constrained()
        b_constrain = self.get_b_constrained()
        if (not isinstance(a_constrain, self.REFERENCE_TYPES)
                or not isinstance(a_constrain, self.REFERENCE_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.REFERENCE_TYPES}\n"
                f"Given: {a_constrain.__class__} and {b_constrain.__class__}"
            )

class Distance(AbstractDistance):
    GEOMETRY_TYPES = (Point, Line, LineSegment, CoordinateSystem, Plane)
    REFERENCE_TYPES = (Point, Line, LineSegment, Plane)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    ReferenceType = reduce(lambda x, y: x | y, REFERENCE_TYPES)
    
    # Private Methods #
    def _validate_parent_geometry(self):
        """Raises an error if the geometries are not one of the allowed 
        types"""
        a = self.get_a()
        b = self.get_b()
        if (not isinstance(a, self.GEOMETRY_TYPES)
                or not isinstance(b, self.GEOMETRY_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.GEOMETRY_TYPES}\n"
                f"Given: {a.__class__} and {b.__class__}"
            )
        elif not len(a) == len(b):
            raise ValueError("Geometry a and b must have the same number"
                             " of dimensions")
        elif a is b:
            raise ValueError("geometry a/b cannot be the same geometry element")
    
    def _validate_constrained_geometry(self):
        """Raises an error if the constrained geometries are not one of the 
        allowed types"""
        a_constrain = self.get_a_constrained()
        b_constrain = self.get_b_constrained()
        if (not isinstance(a_constrain, self.REFERENCE_TYPES)
                or not isinstance(a_constrain, self.REFERENCE_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.REFERENCE_TYPES}\n"
                f"Given: {a_constrain.__class__} and {b_constrain.__class__}"
            )

class HorizontalDistance(AbstractDistance2D):
    def check(self) -> bool:
        """Returns whether the constraint is met by the geometry."""
        raise NotImplementedError("HorizontalDistance check not implemented"
                                  " yet")

class VerticalDistance(AbstractDistance2D):
    def check(self) -> bool:
        """Returns whether the constraint is met by the geometry."""
        raise NotImplementedError("VerticalDistance check not implemented"
                                  " yet")