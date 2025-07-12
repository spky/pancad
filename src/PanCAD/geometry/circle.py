"""A module providing a class to represent circles in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from functools import partial

import numpy as np

from PanCAD.geometry.abstract_geometry import AbstractGeometry
from PanCAD.geometry import Point
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils.trigonometry import get_unit_vector
from PanCAD.utils import comparison

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class Circle(AbstractGeometry):
    """A class representing a circle in 2D or 3D space.
    
    :param center: The center point of the circle.
    :param radius: The radius dimension of the circle.
    :param x_vector: The direction vector of the x-axis of the circle.
    :param y_vector: The direction vector of the y-axis of the circle.
    :param uid: The unique ID of the circle for interoperable CAD
        identification.
    """
    CENTER_UID_FORMAT = "{uid}_center"
    
    def __init__(self,
                 center: tuple | np.ndarray | Point,
                 radius: int | float,
                 x_vector: tuple[int | float]=None,
                 y_vector: tuple[int | float]=None,
                 uid: str=None):
        if isinstance(center, (tuple, np.ndarray)):
            center = Point(center)
        
        self._references = (ConstraintReference.CORE,
                            ConstraintReference.CENTER)
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
        :setter: Updates the internal point with the values of a new point.
        """
        return self._center
    
    @property
    def radius(self) -> int | float:
        """Radius dimension of the circle.
        
        :getter: Returns the radius value.
        :setter: Updates the radius if the given value is >0.
        """
        return self._radius
    
    @property
    def uid(self) -> str:
        """Unique id of the circle.
        
        :getter: returns the unique id.
        :setter: Updates the circle's and its center point's uids.
        """
        return self._uid
    
    # Setters #
    @center.setter
    def center(self, point: Point):
        if len(point) == len(self):
            self._center.update(point)
        else:
            raise ValueError(f"Dimension mismatch: Provided center point is"
                             f" {len(point)}D, Circle is {len(self)}D")
    
    @radius.setter
    def radius(self, value: int | float):
        if value >= 0:
            self._radius = value
        else:
            raise ValueError(f"Radius cannot be < 0. Given: {value}")
    
    @uid.setter
    def uid(self, value: str):
        self._uid = value
        if self._uid is None:
            self.center.uid = None
        else:
            self.center.uid = self.CENTER_UID_FORMAT.format(uid=self._uid)
    
    # Public Methods #
    def get_reference(self, reference: ConstraintReference) -> Point | Circle:
        """Returns the subgeometry associated with the reference.
        
        :param reference: A ConstraintReference. Circles can only return CORE 
            (its edge) and CENTER (its center point).
        :returns: The associated subgeometry.
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
        """Returns a tuple of the constraint references available for the 
        geometry.
        
        :returns: A tuple of ConstraintReferences that can be called for
            Circles.
        """
        return self._references
    
    def get_orientation_vectors(self) -> tuple[tuple[int], tuple[int]]:
        return self._x_vector, self._y_vector
    
    def set_orientation_vectors(self,
                                x_vector: tuple[int | float],
                                y_vector: tuple[int | float]) -> None:
        if len(x_vector) == len(y_vector) == len(self) == 3:
            self._x_vector = get_unit_vector(x_vector)
            self._y_vector = get_unit_vector(y_vector)
        elif len(self) != 3:
            raise ValueError("Orientation vectors cannot be set on 2D circles")
        else:
            raise ValueError("Orientation vectors must be 3D, given:"
                             f" {x_vector} and {y_vector}")
    
    def update(self, other: Circle) -> None:
        """Updates the center point, radius, and orientation vectors to match 
        the other circle.
        
        :param other: A circle to update this circle to.
        """
        if len(self) == len(other):
            self.center.update(other.center)
            self.radius = other.radius
            if len(self) == 3:
                self.set_orientation_vectors(other._x_vector, other._y_vector)
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
            orientations directions are equal
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
        """Returns the short string representation of the circle."""
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