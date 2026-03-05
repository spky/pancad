"""A module providing a class to represent circles in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from functools import partial
from sqlite3 import PrepareProtocol
from typing import TYPE_CHECKING

from pancad.abstract import AbstractGeometry
from pancad.constants import ConstraintReference
from pancad.geometry.point import Point
from pancad.utils import comparison
from pancad.utils.pancad_types import VectorLike

if TYPE_CHECKING:
    from numbers import Real
    from typing import Self

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
    def __init__(self,
                 center: Point | VectorLike,
                 radius: Real,
                 *,
                 uid: str=None) -> None:
        if isinstance(center, VectorLike):
            center = Point(center)
        if len(center) == 3:
            raise NotImplementedError("3D Circles not implemented yet.")
        self._center = center
        self._radius = radius
        self._validate_circle_parameters()
        self.uid = uid
        super().__init__(
            {
                ConstraintReference.CORE: self,
                ConstraintReference.CENTER: self.center,
            }
         )

    # Properties
    @property
    def center(self) -> Point:
        """Center point of the circle.
        
        :getter: Returns the point.
        :setter: Updates the internal center point with values from a new point.
        """
        return self._center
    @center.setter
    def center(self, point: Point) -> None:
        if len(point) == len(self):
            self._center.update(point)
        else:
            raise ValueError(f"Dimension mismatch: Provided center point is"
                             f" {len(point)}D, Circle is {len(self)}D")

    @property
    def radius(self) -> Real:
        """Radius of the circle.
        
        :getter: Returns the circle's radius value.
        :setter: Updates the circle's radius if the given value is greater than 
            or equal to 0. Raises a ValueError if the radius is less than 0.
        """
        return self._radius
    @radius.setter
    def radius(self, value: Real) -> None:
        if value >= 0:
            self._radius = value
        else:
            raise ValueError(f"Radius cannot be < 0. Given: {value}")

    # Public Methods
    def update(self, other: Circle) -> Self:
        """Updates the center point, radius, and orientation vectors to match 
        the other circle.
        
        :param other: A Circle to update this Circle to.
        :returns: The updated Circle.
        """
        if len(self) == len(other):
            self.center.update(other.center)
            self.radius = other.radius
            return self
        raise ValueError("Cannot update circle to a different dimension")

    # Private Methods
    def _validate_circle_parameters(self) -> None:
        """Validates all the circle's parameters to check they make geometric 
        sense.
        """
        if self.radius < 0:
            raise ValueError(f"Radius cannot be < 0. Given: {self.radius}")

    # Python Dunders #
    def __conform__(self, protocol: PrepareProtocol):
        """Conforms the circle's values for storage in sqlite. 2D circles are 
        stored as center_x;center_y;radius.
        
        :raises NotImplementedError: Raised when a 3D circle is provided.
        """
        if protocol is PrepareProtocol:
            if len(self) == 3:
                raise NotImplementedError("3D circles not implemented yet")
            dimensions = [*self.center, self.radius]
            return ";".join(map(str, dimensions))
        raise TypeError(f"Expected sqlite3.PrepareProtocol, got {protocol}")

    def __copy__(self) -> Circle:
        """Returns a copy of the circle with the same radius, center point, and 
        orientation vectors, but with no assigned uid.
        """
        return Circle(self.center, self.radius)

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
        return NotImplemented

    def __len__(self) -> int:
        """Returns whether the circle is 2D or 3D."""
        return len(self.center)

    def __repr__(self) -> str:
        center_str = str(self.center.cartesian).replace(" ", "")
        return super().__repr__().format(details=f"{center_str}r{self.radius}")
