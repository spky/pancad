"""A module providing classes for horizontal, vertical, and direct distance 
constraints. Distance can be used to force geometry elements to be at set 
distances from specified portions of each other. The horizontal and vertical 
variants can only be applied to 2D geometry and allow the distance 
to be limited to the x or y direction respectively.
"""
from __future__ import annotations

import math
from abc import abstractmethod
from typing import TYPE_CHECKING

from pancad.abstract import AbstractConstraint

if TYPE_CHECKING:
    from numbers import Real

    from pancad.abstract import AbstractGeometry
    from pancad.constants import ConstraintReference

class AbstractValue(AbstractConstraint):
    """An abstract class of constraints that can be applied to one or more 
    geometries that has a value associated with it.
    """
    VALUE_STR_FORMAT = "{value}{unit}"
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
    # Shared Dunder Methods
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
    QUADRANTS = [1, 2, 3, 4]
    """The allowed quadrant choices for where to place the angle."""
    def __init__(self,
                 *geometry: AbstractGeometry,
                 value: Real,
                 quadrant: int,
                 uid: str=None,
                 is_radians: bool=False) -> None:
        if len(geometry) != 2:
            raise ValueError(f"Expected 2 geometries, provided {geometry}")
        if any(len(g) != 2 for g in geometry):
            non_two_dimensional = [g for g in geometry if len(g) != 2]
            raise ValueError(f"Non-2D Geometry provided: {non_two_dimensional}")
        self._geometry = geometry
        self.uid = uid
        self.quadrant = quadrant
        self.unit = "degrees"
        if is_radians:
            self.value = math.degrees(value)
        else:
            self.value = value

    # Properties
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
        if value < 0:
            raise ValueError(f"Negative length not allowed: {value}")
        self._value = value

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
    def __init__(self, *geometry: AbstractGeometry,
                 value: Real, uid: str=None, unit: str=None) -> None:
        self.uid = uid
        if len(geometry) != 2:
            raise ValueError(f"Expected 2 geometries, provided {geometry}")
        if len(set(len(g) for g in geometry)) != 1:
            raise ValueError(f"Geometry not all the same dimension: {geometry}")
        self._geometry = geometry
        self.unit = unit
        self.value = value

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
    def __init__(self, geometry: AbstractGeometry,
                 value: Real, uid: str=None, unit: str=None) -> None:
        self.uid = uid
        self._geometry = [geometry]
        self.unit = unit
        self.value = value

# 2D and 3D Distance Classes #
################################################################################

class Distance(Abstract2GeometryDistance):
    """A constraint that defines the direct distance between two elements in 2D 
    or 3D.
    """

# 2D Only Classes #
################################################################################
class AbstractDistance2D(Abstract2GeometryDistance):
    """An abstract class for 2D distance constraints."""
    def __init__(self, *geometry: AbstractGeometry, **kwargs) -> None:
        if any(len(g) != 2 for g in geometry):
            non_two_dimensional = [g for g in geometry if len(g) != 2]
            raise ValueError(f"Non-2D geometry provided: {non_two_dimensional}")
        super().__init__(*geometry, **kwargs)

class HorizontalDistance(AbstractDistance2D):
    """A constraint that sets the horizontal distance between two elements."""

class VerticalDistance(AbstractDistance2D):
    """A constraint that sets the vertical distance between two elements."""

class Radius(Abstract1GeometryDistance):
    """A constraint that sets the radius of a curve."""

class Diameter(Abstract1GeometryDistance):
    """A constraint that sets the diameter of a curve."""
