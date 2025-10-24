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
from numbers import Real
from typing import TYPE_CHECKING

from pancad.geometry.constraints import AbstractConstraint
from pancad.geometry import (
    Circle,
    CircularArc,
    CoordinateSystem,
    Ellipse,
    Line,
    LineSegment,
    Plane,
    Point,
)

if TYPE_CHECKING:
    from typing import NoReturn
    
    from pancad.geometry.constants import ConstraintReference

class AbstractValue(AbstractConstraint):
    """An abstract class of constraints that can be applied to one or more 
    geometries that has a value associated with it.
    """
    
    VALUE_STR_FORMAT = "{value}{unit}"
    
    @property
    @abstractmethod
    def value(self) -> Real:
        """The value that the constraint enforces."""
    
    # Shared Public Methods #
    def get_value_string(self, include_unit: bool=True) -> str:
        """Returns a string of the value of the constraint.
        
        :param include_unit: Whether to include the unit in the output. Defaults 
            to 'True'.
        :returns: A string with the value of the constraint. Includes the unit 
            in the string if include_unit is 'True'. 
        """
        if include_unit:
            return self.VALUE_STR_FORMAT.format(value=self.value,
                                                unit=self.unit)
        else:
            return str(self.value)
    
    # Shared Private Methods #
    def _validate_constrained_geometry(self) -> NoReturn:
        """Raises an error if the constrained geometries are not one of the 
        allowed types.
        """
        if not any([isinstance(g, self.GEOMETRY_TYPES)
                    for g in self.get_geometry()]):
            classes = [g.__class__ for g in self.get_geometry()]
            raise ValueError(
                f"geometries must be one of:\n{self.GEOMETRY_TYPES}\n"
                f"Given: {classes}"
            )
    
    # Abstract Private Methods #
    @abstractmethod
    def _validate_parent_geometry(self) -> NoReturn:
        """Raises an error if the parent geometry cannot be used."""
    
    @abstractmethod
    def _validate_value(self) -> NoReturn:
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
    
    def __str__(self) -> str:
        super_str = super().__str__().removesuffix(">")
        return f"{super_str}[{self.value}{self.unit}]>"

class Angle(AbstractValue):
    """A class representing angle value constraints between lines. Stores and 
    returns angles in degrees by default since nearly all CAD programs take user 
    angle inputs in degrees. Can constrain:
    
    - :class:`~pancad.geometry.CoordinateSystem`
    - :class:`~pancad.geometry.Line`
    - :class:`~pancad.geometry.LineSegment`
    - :class:`~pancad.geometry.Ellipse`
    
    :param geometry_a: First line-like, defines the x-axis equivalent for
        quadrant selection.
    :param reference_a: The ConstraintReference of the portion of geometry_a to 
        be constrained.
    :param geometry_b: Second line-like, defines the y-axis equivalent for 
        quadrant selection.
    :param reference_b: The ConstraintReference of the portion of geometry_b to 
        be constrained.
    :param value: Angle value in degrees or radians.
    :param quadrant: Quadrant selection between 1 (+, +), 2 (-, +), 3 (-, -)
        and 4 (+, -). Initial selection is only dependent on geometry_a.
        Example: the first quadrant is the one immediately clockwise of the 
        direction vector of geometry_a. The clockwise selection method is to 
        simulate how users pick quadrants visually.
    :param uid: Unique identifier of the constraint.
    :param is_radians: Whether provided value is in radians. Defaults to False.
    """
    CONSTRAINED_TYPES = (
        CoordinateSystem,
        Line,
        LineSegment,
        Ellipse,
    )
    GEOMETRY_TYPES = (Line, LineSegment)
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    QUADRANTS = [1, 2, 3, 4]
    """The allowed quadrant choices for where to place the angle."""
    
    def __init__(self,
                 geometry_a: ConstrainedType,
                 reference_a: ConstraintReference,
                 geometry_b: ConstrainedType,
                 reference_b: ConstraintReference,
                 value: Real,
                 quadrant: int,
                 uid: str=None,
                 is_radians: bool=False) -> None:
        self.uid = uid
        self._a = geometry_a
        self._a_reference = reference_a
        self._b = geometry_b
        self._b_reference = reference_b
        self.quadrant = quadrant
        self.unit = "degrees"
        if is_radians:
            self.value = math.degrees(value)
        else:
            self.value = value
    
    # Getters #
    @property
    def quadrant(self) -> int:
        return self._quadrant
    
    @property
    def value(self) -> Real:
        """Value of the angle constraint in degrees"""
        return self._value
    
    # Setters #
    @quadrant.setter
    def quadrant(self, value: int) -> None:
        if value in self.QUADRANTS:
            self._quadrant = value
        else:
            raise ValueError(f"Provided quadrant {value} not recognized."
                             f" Must be one of {self.QUADRANTS}")
    
    @value.setter
    def value(self, value: Real) -> None:
        self._value = value
        self._validate_value()
    
    # Public Methods #
    def get_constrained(self) -> tuple[ConstrainedType]:
        return (self._a, self._b)
    
    def get_geometry(self) -> tuple[ConstrainedType]:
        return (self._a.get_reference(self._a_reference),
                self._b.get_reference(self._b_reference))
    
    def get_references(self) -> tuple[ConstraintReference]:
        return (self._a_reference, self._b_reference)
    
    def get_value(self, in_radians: bool=False) -> Real:
        """Returns the value of the angle constraint.
        
        :param in_radians: Whether to return the value in radians or degrees. 
            Defaults to 'False'.
        :returns: The angle value in degrees if in_radians is 'False', in 
            radians if 'True'.
        """
        if in_radians:
            return math.radians(self.value)
        else:
            return self.value
    
    # Private Methods #
    def _validate_parent_geometry(self) -> NoReturn:
        """Raises an error if the geometries are not one of the allowed 
        types.
        """
        if (not isinstance(self._a, self.CONSTRAINED_TYPES)
                or not isinstance(self._b, self.CONSTRAINED_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.CONSTRAINED_TYPES}\n"
                f"Given: {self._a.__class__} and {self._b.__class__}"
            )
        elif not len(self._a) == len(self._b) == 2:
            raise ValueError("geometry must be 2D")
        elif self._a is self._b:
            raise ValueError("geometry a/b cannot be the same geometry element")
    
    def _validate_value(self) -> NoReturn:
        """Raises an error if the value of the constraint cannot be used."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("Value must be an int or float,"
                             f" given: {value.__class__}")

class AbstractDistance(AbstractValue):
    """An abstract class of constraints that can be applied to one or more 
    geometries that has a distance associated with it.
    """
    
    @property
    def value(self) -> Real:
        """The distance the constrain enforces. Cannot be negative."""
        return self._value
    
    @value.setter
    def value(self, value: Real) -> None:
        self._value = value
    
    # Shared Private Methods #
    def _validate_value(self) -> NoReturn:
        """Raises an error if the value of the constraint cannot be used."""
        if not isinstance(self.value, Real):
            raise ValueError("Value must be an int or float,"
                             f" given: {value.__class__}")
        elif self.value < 0:
            name = self.__class__.__name__
            raise ValueError(f"Values for {name} constraints cannot be < 0,"
                " negative value behavior should be handled outside of"
                f" distance constraint contexts.\nGiven: {self.value}")

class Abstract2GeometryDistance(AbstractDistance):
    """An abstract class of constraints that can be applied **exactly two** 
    geometries that has a distance associated with it. Distances cannot be 
    negative.
    
    :param geometry_a: First geometry to constrain.
    :param reference_a: The ConstraintReference of the portion of geometry_a to 
        be constrained.
    :param geometry_b: Second geometry to constrain relative to geometry_a.
    :param reference_b: The ConstraintReference of the portion of geometry_b to 
        be constrained.
    :param value: Distance value, must be positive.
    :param uid: Unique identifier of the constraint. Defaults to None.
    :param unit: The unit of the distance value. Defaults to None.
    """
    def __init__(self,
                 geometry_a: ConstrainedType,
                 reference_a: ConstraintReference,
                 geometry_b: ConstrainedType,
                 reference_b: ConstraintReference,
                 value: Real,
                 uid: str=None,
                 unit: str=None) -> None:
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
    
    def get_constrained(self) -> tuple[ConstrainedType]:
        return (self._a, self._b)
    
    def get_geometry(self) -> tuple[ConstrainedType]:
        return (self._a.get_reference(self._a_reference),
                self._b.get_reference(self._b_reference))
    
    def get_references(self) -> tuple[ConstraintReference]:
        return (self._a_reference, self._b_reference)

class Abstract1GeometryDistance(AbstractDistance):
    """An abstract class of constraints that can be applied **exactly one** 
    geometry that has a distance associated with it. Distances cannot be 
    negative.
    
    :param geometry_a: First geometry to constrain.
    :param reference_a: The ConstraintReference of the portion of geometry_a to 
        be constrained.
    :param geometry_b: Second geometry to constrain relative to geometry_a.
    :param reference_b: The ConstraintReference of the portion of geometry_b to 
        be constrained.
    :param value: Distance value, must be positive.
    :param uid: Unique identifier of the constraint. Defaults to None.
    :param unit: The unit of the distance value. Defaults to None.
    """
    CONSTRAINED_TYPES = (
        Circle,
        CircularArc,
    )
    GEOMETRY_TYPES = (
        Circle,
        CircularArc,
    )
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    def __init__(self,
                 geometry_a: ConstrainedType,
                 reference_a: ConstraintReference,
                 value: Real,
                 uid: str=None,
                 unit: str=None) -> None:
        self.uid = uid
        self._a = geometry_a
        self._a_reference = reference_a
        self.value = value
        self.unit = unit
        
        self._validate_parent_geometry()
        self._validate_constrained_geometry()
        self._validate_value()
    
    # Public Methods #
    def get_constrained(self) -> tuple[ConstrainedType]:
        return (self._a,)
    
    def get_geometry(self) -> tuple[ConstrainedType]:
        return (self._a.get_reference(self._a_reference),)
    
    def get_references(self) -> tuple[ConstraintReference]:
        return (self._a_reference,)
    
    # Private Methods #
    def _validate_parent_geometry(self) -> NoReturn:
        """Raises an error if the geometries are not one of the allowed 
        types.
        """
        if not isinstance(self._a, self.CONSTRAINED_TYPES):
            raise ValueError(
                f"geometry a must be one of:\n{self.CONSTRAINED_TYPES}\n"
                f"Given: {self._a.__class__}"
            )

# 2D and 3D Distance Classes #
################################################################################

class Distance(Abstract2GeometryDistance):
    """A constraint that defines the direct distance between two elements in 2D 
    or 3D.
    
    - :class:`~pancad.geometry.CoordinateSystem`
    - :class:`~pancad.geometry.Circle`
    - :class:`~pancad.geometry.CircularArc`
    - :class:`~pancad.geometry.Ellipse`
    - :class:`~pancad.geometry.Line`
    - :class:`~pancad.geometry.LineSegment`
    - :class:`~pancad.geometry.Point`
    - :class:`~pancad.geometry.Plane`
    """
    CONSTRAINED_TYPES = (
        Circle,
        CircularArc,
        CoordinateSystem,
        Ellipse,
        Line,
        LineSegment,
        Plane,
        Point,
    )
    GEOMETRY_TYPES = (Point, Line, LineSegment, Plane)
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    # Private Methods #
    def _validate_parent_geometry(self) -> NoReturn:
        """Raises an error if the geometries are not one of the allowed 
        types.
        """
        if (not isinstance(self._a, self.CONSTRAINED_TYPES)
                or not isinstance(self._b, self.CONSTRAINED_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.CONSTRAINED_TYPES}\n"
                f"Given: {self._a.__class__} and {self._b.__class__}"
            )
        elif not len(self._a) == len(self._b):
            # Distance can apply to 3D contexts, but a and b must match
            raise ValueError("Geometry a and b must have the same number"
                             " of dimensions")
        elif (self._a.get_reference(self._a_reference)
              is self._b.get_reference(self._b_reference)):
            raise ValueError("subgeometry of a/b cannot be the same geometry"
                             " element")

# 2D Only Classes #
################################################################################
class AbstractDistance2D(Abstract2GeometryDistance):
    """An abstract class for 2D distance constraints."""
    CONSTRAINED_TYPES = (
        Circle,
        CircularArc,
        CoordinateSystem,
        Ellipse,
        Line,
        LineSegment,
        Point,
    )
    GEOMETRY_TYPES = (
        Line,
        LineSegment,
        Point,
    )
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    # Private Methods #
    def _validate_parent_geometry(self) -> NoReturn:
        """Raises an error if the geometries are not one of the allowed types.
        """
        if (not isinstance(self._a, self.CONSTRAINED_TYPES)
                or not isinstance(self._b, self.CONSTRAINED_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.CONSTRAINED_TYPES}\n"
                f"Given: {self._a.__class__} and {self._b.__class__}"
            )
        elif not len(self._a) == len(self._b) == 2:
            raise ValueError("geometry must be 2D")

class HorizontalDistance(AbstractDistance2D):
    """A constraint that sets the horizontal distance between two elements. Can 
    constrain:
    
    - :class:`~pancad.geometry.CoordinateSystem`
    - :class:`~pancad.geometry.Circle`
    - :class:`~pancad.geometry.CircularArc`
    - :class:`~pancad.geometry.Ellipse`
    - :class:`~pancad.geometry.Line`
    - :class:`~pancad.geometry.LineSegment`
    - :class:`~pancad.geometry.Point`
    """

class VerticalDistance(AbstractDistance2D):
    """A constraint that sets the vertical distance between two elements. Can 
    constrain:
    
    - :class:`~pancad.geometry.CoordinateSystem`
    - :class:`~pancad.geometry.Circle`
    - :class:`~pancad.geometry.CircularArc`
    - :class:`~pancad.geometry.Ellipse`
    - :class:`~pancad.geometry.Line`
    - :class:`~pancad.geometry.LineSegment`
    - :class:`~pancad.geometry.Point`
    """

class Radius(Abstract1GeometryDistance):
    """A constraint that sets the radius of a curve. Can constrain:
    
    - :class:`~pancad.geometry.Circle`
    - :class:`~pancad.geometry.CircularArc`
    """

class Diameter(Abstract1GeometryDistance):
    """A constraint that sets the diameter of a curve. Can constrain:
    
    - :class:`~pancad.geometry.Circle`
    - :class:`~pancad.geometry.CircularArc`
    """