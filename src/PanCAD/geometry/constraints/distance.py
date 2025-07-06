"""A module providing classes for horizontal, vertical, and direct distance 
constraints. Distance can be used to force geometry elements to be at set 
distances from specified portions of each other. The horizontal and vertical 
variants can only be applied to 2D geometry and allow the distance 
to be limited to the x or y direction respectively.
"""
from __future__ import annotations

from functools import reduce
from abc import abstractmethod

from PanCAD.geometry.constraints.abstract_constraint import AbstractConstraint
from PanCAD.geometry import Point, Line, LineSegment, CoordinateSystem, Plane
from PanCAD.geometry.constants import ConstraintReference

class AbstractDistance(AbstractConstraint):
    
    VALUE_STR_FORMAT = "{value}{unit}"
    
    def __init__(self,
                 geometry_a: GeometryType, reference_a: ConstraintReference,
                 geometry_b: GeometryType, reference_b: ConstraintReference,
                 value: int | float,
                 uid: str=None,
                 unit: str=None):
        self.uid = uid
        self._a = geometry_a
        self._a_reference = reference_a
        self._b = geometry_b
        self._b_reference = reference_b
        self.value = value
        self.unit = unit
        
        self._validate_parent_geometry()
        self._validate_constrained_geometry()
        self._validate_value()
    
    # Shared Public Methods #
    def get_constrained(self) -> tuple[GeometryType]:
        """Returns a tuple of the constrained geometry parents"""
        return (self._a, self._b)
    
    def get_geometry(self) -> tuple[GeometryType]:
        """Returns a tuple of the specific geometry elements inside of the 
        constrained elements"""
        return (self._a.get_reference(self._a_reference),
                self._b.get_reference(self._b_reference))
    
    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometry's references"""
        return (self._a_reference, self._b_reference)
    
    def get_value_string(self, include_unit: bool=True) -> str:
        """Returns a string of the value of the distance constraint with its 
        associated unit.
        """
        return VALUE_STR_FORMAT.format(value=self.value, unit=self.unit)
    
    # Shared Private Methods #
    def _validate_value(self):
        """Raises an error if the value of the constraint cannot be used."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("Value must be an int or float,"
                             f" given: {value.__class__}")
        elif self.value < 0:
            name = self.__class__.__name__
            raise ValueError(f"Values for {name} constraints cannot be < 0,"
                " negative value behavior should be handled outside of"
                f" distance constraint contexts.\nGiven: {self.value}")
    
    # Shared Dunder Methods
    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__}'{self.uid}'"
                f"{repr(self._a)}{repr(self._b)}d{self.value}>")
    
    def __str__(self) -> str:
        return (f"PanCAD {self.__class__.__name__} Constraint '{self.uid}'"
                f" with {repr(self._a)} as geometry a and {repr(self._b)} as"
                f" geometry b and value {self.value}")
    
    def __eq__(self, other: AbstractDistance) -> bool:
        """Checks whether two distance relations are functionally the same by 
        comparing the memory ids of their geometries and the values of the 
        constraints.
        
        :param other: Another distance relationship of the same type.
        :returns: Whether the relations are functionally the same.
        """
        geometry_zip = zip(self.get_geometry(), other.get_geometry())
        if isinstance(other, self.__class__):
            return all([g is other_g for g, other_g in geometry_zip])
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

# 2D and 3D Distance Classes #
################################################################################
class Distance(AbstractDistance):
    GEOMETRY_TYPES = (Point, Line, LineSegment, CoordinateSystem, Plane)
    REFERENCE_TYPES = (Point, Line, LineSegment, Plane)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    ReferenceType = reduce(lambda x, y: x | y, REFERENCE_TYPES)
    
    def check(self) -> bool:
        """Returns whether the constraint is met by the geometry."""
        raise NotImplementedError("HorizontalDistance check not implemented"
                                  " yet")
    
    # Private Methods #
    def _validate_parent_geometry(self):
        """Raises an error if the geometries are not one of the allowed 
        types"""
        if (not isinstance(self._a, self.GEOMETRY_TYPES)
                or not isinstance(self._b, self.GEOMETRY_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.GEOMETRY_TYPES}\n"
                f"Given: {self._a.__class__} and {self._b.__class__}"
            )
        elif not len(self._a) == len(self._b):
            # Distance can apply to 3D contexts, but a and b must match
            raise ValueError("Geometry a and b must have the same number"
                             " of dimensions")
        elif self._a is self._b:
            raise ValueError("geometry a/b cannot be the same geometry element")
    
    def _validate_constrained_geometry(self):
        """Raises an error if the constrained geometries are not one of the 
        allowed types"""
        if not any([isinstance(g, self.REFERENCE_TYPES)
                    for g in self.get_geometry()]):
            classes = [g.__class__ for g in self.get_geometry()]
            raise ValueError(
                f"geometry a and b must be one of:\n{self.REFERENCE_TYPES}\n"
                f"Given: {classes}"
            )

# 2D Only Classes #
################################################################################
class AbstractDistance2D(AbstractDistance):
    """An abstract class for 2D distance constraints"""
    GEOMETRY_TYPES = (Point, Line, LineSegment, CoordinateSystem)
    REFERENCE_TYPES = (Point, Line, LineSegment)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    ReferenceType = reduce(lambda x, y: x | y, REFERENCE_TYPES)
    
    # Private Methods #
    def _validate_parent_geometry(self) -> None:
        """Raises an error if the geometries are not one of the allowed 
        types"""
        if (not isinstance(self._a, self.GEOMETRY_TYPES)
                or not isinstance(self._b, self.GEOMETRY_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.GEOMETRY_TYPES}\n"
                f"Given: {self._a.__class__} and {self._b.__class__}"
            )
        elif not len(self._a) == len(self._b) == 2:
            raise ValueError("geometry must be 2D")
        elif self._a is self._b:
            raise ValueError("geometry a/b cannot be the same geometry element")
    
    def _validate_constrained_geometry(self) -> None:
        """Raises an error if the constrained geometries are not one of the 
        allowed types"""
        if not any([isinstance(g, self.REFERENCE_TYPES)
                    for g in self.get_geometry()]):
            classes = [g.__class__ for g in self.get_geometry()]
            raise ValueError(
                f"geometry a and b must be one of:\n{self.REFERENCE_TYPES}\n"
                f"Given: {classes}"
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