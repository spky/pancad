"""A module providing classes for horizontal, vertical, and direct distance 
constraints. Distance can be used to force geometry elements to be at set 
distances from specified portions of each other. The horizontal and vertical 
variants can only be applied to 2D geometry and allow the distance 
to be limited to the x or y direction respectively.
"""
from __future__ import annotations

from abc import abstractmethod
from functools import reduce
import math

from PanCAD.geometry.constraints.abstract_constraint import AbstractConstraint
from PanCAD.geometry import (
    Circle, CoordinateSystem, Line, LineSegment, Plane, Point
)
from PanCAD.geometry.constants import ConstraintReference

class AbstractValue(AbstractConstraint):
    
    VALUE_STR_FORMAT = "{value}{unit}"
    
    # Shared Public Methods #
    def get_value_string(self, include_unit: bool=True) -> str:
        """Returns a string of the value of the value constraint with its 
        associated unit.
        """
        if include_unit:
            return VALUE_STR_FORMAT.format(value=self.value, unit=self.unit)
        else:
            return str(self.value)
    
    # Abstract Public Methods #
    @abstractmethod
    def get_constrained(self) -> tuple[GeometryType]:
        """Returns a tuple of the constrained geometry parents"""
    
    @abstractmethod
    def get_geometry(self) -> tuple[GeometryType]:
        """Returns a tuple of the specific geometry elements inside of the 
        constrained elements"""
    
    @abstractmethod
    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometry's references"""
    
    # Shared Private Methods #
    def _validate_constrained_geometry(self):
        """Raises an error if the constrained geometries are not one of the 
        allowed types"""
        if not any([isinstance(g, self.REFERENCE_TYPES)
                    for g in self.get_geometry()]):
            classes = [g.__class__ for g in self.get_geometry()]
            raise ValueError(
                f"geometries must be one of:\n{self.REFERENCE_TYPES}\n"
                f"Given: {classes}"
            )
    
    # Abstract Private Methods #
    @abstractmethod
    def _validate_parent_geometry(self):
        """Raises an error if the parent geometry cannot be used"""
    
    @abstractmethod
    def _validate_value(self):
        """Raises an error if the value of the constraint cannot be used."""
    
    # Shared Dunder Methods
    def __eq__(self, other: AbstractValue) -> bool:
        """Checks whether two value relations are functionally the same by 
        comparing the memory ids of their geometries and the values of the 
        constraints.
        
        :param other: Another value constraint of the same type.
        :returns: Whether the relations are functionally the same.
        """
        geometry_zip = zip(self.get_geometry(), other.get_geometry())
        if isinstance(other, self.__class__):
            return all([g is other_g for g, other_g in geometry_zip])
        else:
            return NotImplemented
    
    def __repr__(self) -> str:
        """Short string representation of the value constraint"""
        geometry_reprs = "".join([repr(g) for g in self.get_constrained()])
        return (f"<{self.__class__.__name__}'{self.uid}'"
                f"{geometry_reprs}v{self.value}>")
    
    # Abstract Dunder Methods #
    @abstractmethod
    def __str__(self) -> str:
        """String representation of the value constraint"""
    
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

class Angle(AbstractValue):
    """A class representing angle value constraints between lines.
    
    :param geometry_a: First line-like, defines the x-axis equivalent for
        quadrant selection.
    :param geometry_b: Second line-like, defines the y-axis equivalent for 
        quadrant selection.
    :param value: Angle value in degrees or radians.
    :param quadrant: Quadrant selection between 1 (+, +), 2 (-, +), 3 (-, -)
        and 4 (+, -). Initial selection is only dependent on geometry_a, e.g., 
        the first quadrant is the one immediately clockwise of the direction 
        vector of geometry_a. The clockwise selection method is to simulate how 
        users pick quadrants visually.
    :param uid: Unique identifier of the constraint.
    :param is_radians: Whether value is in radians. Defaults to False.
    """
    GEOMETRY_TYPES = (Line, LineSegment)
    REFERENCE_TYPES = (Line, LineSegment)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    ReferenceType = reduce(lambda x, y: x | y, REFERENCE_TYPES)
    
    QUADRANTS = [1, 2, 3, 4]
    
    def __init__(self,
                 geometry_a: GeometryType, reference_a: ConstraintReference,
                 geometry_b: GeometryType, reference_b: ConstraintReference,
                 value: int | float,
                 quadrant: int,
                 uid: str = None,
                 is_radians: bool=False):
        self.uid = uid
        self._a = geometry_a
        self._a_reference = reference_a
        self._b = geometry_b
        self._b_reference = reference_b
        self.quadrant = quadrant
        if is_radians:
            self.value = math.degrees(value)
        else:
            self.value = value
    
    # Getters #
    @property
    def quadrant(self) -> int:
        return self._quadrant
    
    @property
    def value(self) -> int | float:
        """Value of the angle constraint in degrees"""
        return self._value
    
    # Setters #
    @quadrant.setter
    def quadrant(self, value: int):
        if value in self.QUADRANTS:
            self._quadrant = value
        else:
            raise ValueError(f"Provided quadrant {value} not recognized."
                             f" Must be one of {self.QUADRANTS}")
    
    @value.setter
    def value(self, value: int | float):
        self._value = value
        self._validate_value()
    
    # Public Methods #
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
    
    def get_value(self, in_radians: bool=False) -> int | float:
        if in_radians:
            return math.radians(self.value)
        else:
            return self.value
    
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
    
    def _validate_value(self):
        """Raises an error if the value of the constraint cannot be used."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("Value must be an int or float,"
                             f" given: {value.__class__}")
    
    # Dunder Methods #
    def __str__(self) -> str:
        """String representation of a 2 geometry distance constraint"""
        return (f"PanCAD {self.__class__.__name__} Constraint '{self.uid}'"
                f" with {repr(self._a)} as geometry a and {repr(self._b)} as"
                f" geometry b and value {self.value}")

class AbstractDistance(AbstractValue):
    
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

class Abstract2GeometryDistance(AbstractDistance):
    
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
    
    def __str__(self) -> str:
        """String representation of a 2 geometry distance constraint"""
        return (f"PanCAD {self.__class__.__name__} Constraint '{self.uid}'"
                f" with {repr(self._a)} as geometry a and {repr(self._b)} as"
                f" geometry b and value {self.value}")

class Abstract1GeometryDistance(AbstractDistance):
    GEOMETRY_TYPES = (Circle,)
    REFERENCE_TYPES = (Circle,)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    ReferenceType = reduce(lambda x, y: x | y, REFERENCE_TYPES)
    
    def __init__(self,
                 geometry_a: GeometryType, reference_a: ConstraintReference,
                 value: int | float,
                 uid: str=None,
                 unit: str=None):
        self.uid = uid
        self._a = geometry_a
        self._a_reference = reference_a
        self.value = value
        self.unit = unit
        
        self._validate_parent_geometry()
        self._validate_constrained_geometry()
        self._validate_value()
    
    # Public Methods #
    def get_constrained(self) -> tuple[GeometryType]:
        """Returns a tuple of the constrained geometry parents"""
        return (self._a,)
    
    def get_geometry(self) -> tuple[GeometryType]:
        """Returns a tuple of the specific geometry elements inside of the 
        constrained elements"""
        return (self._a.get_reference(self._a_reference),)
    
    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometry's references"""
        return (self._a_reference,)
    
    def __str__(self) -> str:
        """String representation of a 1 geometry distance constraint"""
        return (f"PanCAD {self.__class__.__name__} Constraint '{self.uid}'"
                f" with {repr(self._a)} as geometry a and value {self.value}")
    
    # Private Methods #
    def _validate_parent_geometry(self):
        """Raises an error if the geometries are not one of the allowed 
        types"""
        if not isinstance(self._a, self.GEOMETRY_TYPES):
            raise ValueError(
                f"geometry a must be one of:\n{self.GEOMETRY_TYPES}\n"
                f"Given: {self._a.__class__}"
            )

# 2D and 3D Distance Classes #
################################################################################

class Distance(Abstract2GeometryDistance):
    """A constraint that defines the direct distance between two elements in 2D 
    or 3D.
    """
    GEOMETRY_TYPES = (Point, Line, LineSegment, CoordinateSystem, Plane)
    REFERENCE_TYPES = (Point, Line, LineSegment, Plane)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    ReferenceType = reduce(lambda x, y: x | y, REFERENCE_TYPES)
    
    # Public Methods #
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

# 2D Only Classes #
################################################################################
class AbstractDistance2D(Abstract2GeometryDistance):
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

class HorizontalDistance(AbstractDistance2D):
    """A constraint that sets the horizontal distance between two elements"""

class VerticalDistance(AbstractDistance2D):
    """A constraint that sets the vertical distance between two elements"""

class Radius(Abstract1GeometryDistance):
    """A constraint that sets the radius of a curve"""

class Diameter(Abstract1GeometryDistance):
    """A constraint that sets the diameter of a curve"""