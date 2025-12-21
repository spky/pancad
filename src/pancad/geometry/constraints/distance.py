"""A module providing classes for horizontal, vertical, and direct distance 
constraints. Distance can be used to force geometry elements to be at set 
distances from specified portions of each other. The horizontal and vertical 
variants can only be applied to 2D geometry and allow the distance 
to be limited to the x or y direction respectively.
"""
from __future__ import annotations

from abc import abstractmethod
import math
from numbers import Real
from typing import TYPE_CHECKING

from pancad.geometry.constraints import AbstractConstraint
from pancad.geometry.constraints.utils import GeometryReference, constraint_args
from pancad.geometry import (
    AbstractGeometry,
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
    GEOMETRY_TYPES = AbstractGeometry
    @property
    @abstractmethod
    def value(self) -> Real:
        """The value that the constraint enforces."""
    @property
    def unit(self) -> str:
        """The unit of the constraint's value.
        
        :getter: Returns the constraint's unit.
        :setter: Sets the constraints unit.
        """
        return self._unit
    @unit.setter
    def unit(self, value: str) -> None:
        self._unit = value
    @property
    def _pairs(self) -> list[tuple[AbstractGeometry, ConstraintReference]]:
        return self.__pairs
    @_pairs.setter
    def _pairs(self, value: list[tuple[AbstractGeometry,
                                       ConstraintReference]]) -> None:
        self.__pairs = value
    # Shared Public Methods #
    def get_value_string(self, include_unit: bool=True) -> str:
        """Returns a string of the value of the constraint.
        
        :param include_unit: Whether to include the unit in the output. Defaults 
            to 'True'.
        :returns: A string with the value of the constraint. Includes the unit 
            in the string if include_unit is 'True'. 
        """
        if include_unit:
            return self.VALUE_STR_FORMAT.format(value=self.value, unit=self.unit)
        return str(self.value)
    # Public Methods #
    def get_constrained(self) -> tuple[AbstractGeometry]:
        return tuple(geometry for geometry, _ in self._pairs)
    def get_geometry(self) -> tuple[AbstractGeometry]:
        return tuple(geometry.get_reference(reference)
                     for geometry, reference in self._pairs)
    def get_references(self) -> tuple[ConstraintReference]:
        return tuple(reference for _, reference in self._pairs)
    # Abstract Private Methods #
    @abstractmethod
    def _validate(self) -> None:
        """Raises an error if the constraint is badly defined."""
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
            return all(g is other_g for g, other_g in geometry_zip)
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
    
    :param reference_pairs: The (AbstractGeometry, ConstraintReference) pairs of
        the geometry to be constrained.
    :param value: Angle value in degrees or radians.
    :param quadrant: Quadrant selection between 1 (+, +), 2 (-, +), 3 (-, -)
        and 4 (+, -). Initial selection is only dependent on the first element.
        Example: the first quadrant is the one immediately clockwise of the 
        direction vector of the firest element. The clockwise selection method is 
        to simulate how users pick quadrants visually.
    :param uid: Unique identifier of the constraint.
    :param is_radians: Whether provided value is in radians. Defaults to False.
    :raises ValueError: When the subgeometries are not 2D or if not exactly 2
        pairs are provided.
    """
    CONSTRAINED_TYPES = (CoordinateSystem, Line, LineSegment, Ellipse)
    GEOMETRY_TYPES = (Line, LineSegment)
    QUADRANTS = [1, 2, 3, 4]
    """The allowed quadrant choices for where to place the angle."""
    def __init__(self,
                 *reference_pairs: GeometryReference,
                 value: Real,
                 quadrant: int,
                 uid: str=None,
                 is_radians: bool=False) -> None:
        self._pairs = constraint_args(*reference_pairs)
        self.uid = uid
        self.quadrant = quadrant
        self.unit = "degrees"
        if is_radians:
            self.value = math.degrees(value)
        else:
            self.value = value
    # Getters #
    @property
    def quadrant(self) -> int:
        """The quadrant that the angle constraint is applied to.
        
        :raises ValueError: If the quadrant is not 1, 2, 3, or 4.
        """
        return self._quadrant
    @quadrant.setter
    def quadrant(self, value: int) -> None:
        if value not in self.QUADRANTS:
            raise ValueError(f"Quadrant must be one of {self.QUADRANTS}")
        self._quadrant = value
    @property
    def value(self) -> Real:
        """Value of the angle constraint in degrees.
        
        :raises TypeError: When the value is not a Real number.
        """
        return self._value
    @value.setter
    def value(self, value: Real) -> None:
        self._value = value
        self._validate()
    # Public Methods #
    def get_value(self, in_radians: bool=False) -> Real:
        """Returns the value of the angle constraint.
        
        :param in_radians: Whether to return the value in radians or degrees. 
            Defaults to 'False'.
        :returns: The angle value in degrees if in_radians is 'False', in 
            radians if 'True'.
        """
        if in_radians:
            return math.radians(self.value)
        return self.value
    # Private Methods #
    def _validate(self) -> None:
        if any(len(geometry.get_reference(reference)) != 2
                for geometry, reference in self._pairs):
            raise ValueError("Geometry not 2D")
        if not isinstance(self.value, Real):
            raise TypeError("Value must be Real")
        if len(self._pairs) != 2:
            raise ValueError(f"Expected 2 pairs, given {self._pairs}")

class AbstractDistance(AbstractValue):
    """An abstract class of constraints that can be applied to one or more 
    geometries that has a distance associated with it.
    """
    @property
    def value(self) -> Real:
        """The distance the constraint enforces.
        
        :raises ValueError: When the distance is a negative number.
        """
        return self._value
    @value.setter
    def value(self, value: Real) -> None:
        self._value = value
        self._validate()
    # Shared Private Methods #
    def _validate(self) -> None:
        """Raises errors if the value of the constraint is badly defined."""
        if not isinstance(self.value, Real):
            raise TypeError("Value must be Real")
        if self.value < 0:
            raise ValueError("Distance cannot be stored negative")

class Abstract2GeometryDistance(AbstractDistance):
    """An abstract class of constraints that can be applied **exactly two** 
    geometries that has a distance associated with it. Distances cannot be 
    negative.
    
    :param reference_pairs: The (AbstractGeometry, ConstraintReference) pairs of
        the geometry to be constrained.
    :param value: Distance value, must be positive.
    :param uid: Unique identifier of the constraint. Defaults to None.
    :param unit: The unit of the distance value. Defaults to None.
    :raises ValueError: When not provided 2 pairs or when the subgeometries are 
        not the same dimension.
    """
    def __init__(self,
                 *reference_pairs: GeometryReference,
                 value: Real,
                 uid: str=None,
                 unit: str=None) -> None:
        self.uid = uid
        self._pairs = constraint_args(*reference_pairs)
        self.value = value
        self.unit = unit
    def _validate(self) -> None:
        super()._validate()
        if len(self._pairs) != 2:
            raise ValueError(f"Expected 2 pairs, given {self._pairs}")
        iterator = iter(len(geometry.get_reference(reference))
                        for geometry, reference in self._pairs)
        first_length = next(iterator)
        if not all(first_length == length for length in iterator):
            raise ValueError("Not all subgeometry is the same dimension")

class Abstract1GeometryDistance(AbstractDistance):
    """An abstract class of constraints that can be applied **exactly one** 
    geometry that has a distance associated with it. Distances cannot be 
    negative.
    
    :param reference_pairs: The (AbstractGeometry, ConstraintReference) pairs of
        the geometry to be constrained.
    :param value: Distance value, must be positive.
    :param uid: Unique identifier of the constraint. Defaults to None.
    :param unit: The unit of the distance value. Defaults to None.
    """
    CONSTRAINED_TYPES = (Circle, CircularArc)
    GEOMETRY_TYPES = (Circle, CircularArc)
    def __init__(self,
                 *reference_pairs: GeometryReference,
                 value: Real,
                 uid: str=None,
                 unit: str=None) -> None:
        self.uid = uid
        self._pairs = constraint_args(*reference_pairs)
        self.unit = unit
        self.value = value
    def _validate(self) -> None:
        super()._validate()
        if len(self._pairs) != 1:
            raise ValueError(f"Expected 1 pair, given {self._pairs}")

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
    GEOMETRY_TYPES = (Line, LineSegment, Point)
    # Private Methods #
    def _validate(self) -> None:
        super()._validate()
        if any(len(geometry.get_reference(reference)) != 2
                for geometry, reference in self._pairs):
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
