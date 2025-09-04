"""A module providing a class to represent circles in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from functools import partial
from numbers import Real
from typing import Self

import numpy as np

from PanCAD.geometry import AbstractGeometry, Point
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils import comparison
from PanCAD.utils.trigonometry import get_unit_vector
from PanCAD.utils.pancad_types import VectorLike

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class Circle(AbstractGeometry):
    """A class representing a circle in 2D or 3D space.
    
    :param center: The center point of the circle.
    :param radius: The radius dimension of the circle.
    :param x_vector: The direction vector of the x-axis of the circle. Defaults 
        to None, but is required for a 3D circle.
    :param y_vector: The direction vector of the y-axis of the circle. Defaults 
        to None, but is required for a 3D circle.
    :param uid: The unique ID of the circle.
    """
    REFERENCES = (ConstraintReference.CORE, ConstraintReference.CENTER)
    """All relevant ConstraintReferences for Circles."""
    
    def __init__(self,
                 center: Point | VectorLike,
                 radius: Real,
                 x_vector: tuple[Real]=None,
                 y_vector: tuple[Real]=None,
                 uid: str=None) -> None:
        if isinstance(center, VectorLike):
            center = Point(center)
        
        self._center = center
        self._radius = radius
        self._x_vector = x_vector
        self._y_vector = y_vector
        self._validate_circle_parameters()
        self.uid = uid
    
    # Getters #
    @property
    def center(self) -> Point:
        """Center point of the circle.
        
        :getter: Returns the point.
        :setter: Updates the internal center point with values from a new point.
        """
        return self._center
    
    @property
    def radius(self) -> Real:
        """Radius of the circle.
        
        :getter: Returns the circle's radius value.
        :setter: Updates the circle's radius if the given value is greater than 
            or equal to 0. Raises a ValueError if the radius is less than 0.
        """
        return self._radius
    
    # Setters #
    @center.setter
    def center(self, point: Point) -> None:
        if len(point) == len(self):
            self._center.update(point)
        else:
            raise ValueError(f"Dimension mismatch: Provided center point is"
                             f" {len(point)}D, Circle is {len(self)}D")
    
    @radius.setter
    def radius(self, value: Real) -> None:
        if value >= 0:
            self._radius = value
        else:
            raise ValueError(f"Radius cannot be < 0. Given: {value}")
    
    # Public Methods #
    def get_reference(self, reference: ConstraintReference) -> Point | Self:
        """Returns reference geometry for use in external modules like 
        constraints.
        
        :param reference: A ConstraintReference enumeration value applicable to 
            Circles. See :attr:`Circle.REFERENCES`.
        :returns: The geometry corresponding to the reference.
        """
        match reference:
            case ConstraintReference.CORE:
                return self
            case ConstraintReference.CENTER:
                return self.center
            case _:
                raise ValueError(f"Circles do not have {reference.name}"
                                 " reference geometry")
    
    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns all ConstraintReferences applicable to Circles. See 
        :attr:`Circle.REFERENCES`.
        """
        return self.REFERENCES
    
    def get_orientation_vectors(self) -> tuple[tuple[Real], tuple[Real]]:
        """Returns the orientation vectors for a 3D circle.
        
        :returns: A tuple of the x and y orientation vectors of the circle.
        """
        return self._x_vector, self._y_vector
    
    def set_orientation_vectors(self,
                                x_vector: tuple[Real],
                                y_vector: tuple[Real]) -> Self:
        """Sets the orientation vectors for a 3D circle.
        
        :param x_vector: The direction vector of the x-axis of the circle.
        :param y_vector: The direction vector of the y-axis of the circle.
        :returns: The updated Circle.
        """
        if len(x_vector) == len(y_vector) == len(self) == 3:
            self._x_vector = get_unit_vector(x_vector)
            self._y_vector = get_unit_vector(y_vector)
            return self
        elif len(self) != 3:
            raise ValueError("Orientation vectors cannot be set on 2D circles")
        else:
            raise ValueError("Orientation vectors must be 3D, given:"
                             f" {x_vector} and {y_vector}")
    
    def update(self, other: Circle) -> Self:
        """Updates the center point, radius, and orientation vectors to match 
        the other circle.
        
        :param other: A Circle to update this Circle to.
        :returns: The updated Circle.
        """
        if len(self) == len(other):
            self.center.update(other.center)
            self.radius = other.radius
            if len(self) == 3:
                self.set_orientation_vectors(other._x_vector, other._y_vector)
            return self
        else:
            raise ValueError("Cannot update a 2D circle to 3D")
    
    # Private Methods #
    def _validate_circle_parameters(self) -> None:
        """Validates all the circle's parameters to check they make geometric 
        sense.
        """
        if self.radius < 0:
            raise ValueError(f"Radius cannot be < 0. Given: {self.radius}")
        
        vectors = self.get_orientation_vectors()
        if len(self) == 2 and any([d is not None for d in vectors]):
            raise ValueError("2D circles cannot have 3D vectors defined."
                             f" Given vectors {vectors}")
        elif len(self) == 3 and any([d is None for d in vectors]):
            raise ValueError("3D circles must have 2 orthogonal 3D vectors"
                             f" defined. Given vectors {vectors}")
    
    # Python Dunders #
    def __copy__(self) -> Circle:
        """Returns a copy of the circle with the same radius, center point, and 
        orientation vectors, but with no assigned uid.
        """
        return Circle(self.center, self.radius, *self.get_orientation_vectors())
    
    def __eq__(self, other: Circle) -> bool:
        """Rich comparison for circle equality that allows for circles to be 
        directly compared with ==.
        
        :param other: The circle to compare this circle to.
        :returns: Whether the tuples of the circle's center points, radii and 
            orientations directions are equal.
        """
        if isinstance(other, Circle) and len(self) == len(other) == 2:
            return (
                isclose(self.center.cartesian, other.center.cartesian)
                and isclose(self.radius, other.radius)
            )
        elif isinstance(other, Circle) and len(self) == len(other) == 3:
            x_vector, y_vector = self.get_orientation_vectors()
            other_x, other_y = self.get_orientation_vectors()
            return (
                isclose(self.center.cartesian, other.center.cartesian)
                and isclose(self.radius, other.radius)
                and isclose(x_vector, other_x)
                and isclose(y_vector, other_y)
            )
        elif isinstance(other, Circle) and len(self) != len(other):
            return False
        else:
            return NotImplemented
    
    def __len__(self) -> int:
        """Returns whether the circle is 2D or 3D."""
        return len(self.center)
    
    def __repr__(self) -> str:
        center_str = str(self.center.cartesian).replace(" ","")
        string = f"<PanCADCircle'{self.uid}'{center_str}r{self.radius}"
        if len(self) == 3:
            x_vector, y_vector = self.get_orientation_vectors()
            x_vector_str = str(x_vector).replace(" ","")
            y_vector_str = str(y_vector).replace(" ","")
            string += f"x{x_vector_str}y{y_vector_str}"
        return string + ">"
    
    def __str__(self) -> str:
        string = (f"PanCAD Circle '{self.uid}' with center"
                  f" {self.center.cartesian} and radius {self.radius}")
        if len(self) == 3:
            x_vector, y_vector = self.get_orientation_vectors()
            string += (f", oriented with the x direction {x_vector} and"
                       f" y direction {y_vector}")
        return string