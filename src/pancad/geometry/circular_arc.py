"""A module providing a class to represent circular arcs in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from functools import partial
from sqlite3 import PrepareProtocol
from typing import TYPE_CHECKING

from numpy import array

from pancad.geometry import AbstractGeometry, Point
from pancad.geometry.constants import ConstraintReference
from pancad.utils import comparison
from pancad.utils.pancad_types import VectorLike
from pancad.utils.trigonometry import (
    get_unit_vector,
    to_1D_tuple,
    phi_of_cartesian,
    polar_to_cartesian,
)

if TYPE_CHECKING:
    from numbers import Real
    from typing import Self

isclose = partial(comparison.isclose, nan_equal=False)

class CircularArc(AbstractGeometry):
    """A class representing a circular arc in 2D or 3D space.
    
    :param center: The center point of the arc.
    :param radius: The radius dimension of the arc.
    :param start_vector: A vector pointing to the start of the arc.
    :param end_vector: A vector pointing to the end of the arc.
    :param is_clockwise: Sets whether the arc travels clockwise from the start 
        point to the end point.
    :param normal_vector: The vector normal to the start and end vectors that 
        defines which direction is clockwise. Required for 3D arcs.
    :param uid: The unique ID of the circle.
    """
    REFERENCES = (
        ConstraintReference.CORE,
        ConstraintReference.CENTER,
        ConstraintReference.START,
        ConstraintReference.END,
    )
    """All relevant ConstraintReferences for CircularArcs."""
    
    def __init__(self,
                 center: Point | VectorLike,
                 radius: Real,
                 start_vector: VectorLike,
                 end_vector: VectorLike,
                 is_clockwise: bool,
                 normal_vector: VectorLike | None=None,
                 uid: str=None) -> None:
        if isinstance(center, VectorLike):
            center = Point(center)
        # Initialize center first to establish 2D or 3D
        self._center = center.copy()
        if len(self) == 2:
            # 999 set so it's obvious if these are not changed
            self._start = Point(999, 0)
            self._start_vector = (999, 0)
            self._end = Point(999, 0)
            self._end_vector = (999, 0)
            self._normal_vector = None
        else:
            self._start = Point(999, 0, 0)
            self._start_vector = (999, 0, 0)
            self._end = Point(999, 0, 0)
            self._end_vector = (999, 0, 0)
            self._normal_vector = (0, 0, 1)
        
        self.radius = radius
        self.start_vector = start_vector
        self.end_vector = end_vector
        self.is_clockwise = is_clockwise
        self.normal_vector = normal_vector
        self.uid = uid
    
    @classmethod
    def from_angles(cls,
                    center: Point | VectorLike,
                    radius: Real,
                    start_angle: Real,
                    end_angle: Real,
                    is_clockwise: bool,
                    uid: str=None) -> None:
        """Initializes a 2D CircularArc using start and end angles instead of 
        vectors.
        
        :param center: The center point of the arc.
        :param radius: The radius dimension of the arc.
        :param start_angle: The angle from the horizontal axis to the line 
            between the center and the start of the arc in radians.
        :param end_angle: A vector pointing to the end of the arc.
        :param is_clockwise: Sets whether the arc travels clockwise from the 
            start point to the end point.
        :param uid: The unique ID of the circle.
        :raises ValueError: Raised if the center point is 3D since 3D arcs
            cannot be defined by angles.
        """
        if len(center) == 3:
            raise ValueError("3D CircularArcs cannot be initialized by angles")
        
        if isinstance(center, VectorLike):
            center = Point(center)
        start_vector = polar_to_cartesian((1, start_angle))
        end_vector = polar_to_cartesian((1, end_angle))
        return cls(center, radius, start_vector, end_vector, is_clockwise,
                   uid=uid)
    
    # Getters #
    @property
    def center(self) -> Point:
        """Center point of the arc.
        
        :getter: Returns the point.
        :setter: Updates the internal center point with values from a new point. 
            The arc's start and end points are updated to follow the center's
            new position. 
        """
        return self._center
    
    @property
    def is_clockwise(self) -> bool:
        """A boolean that sets whether the arc travels clockwise or 
        counterclockwise from its start point to its end point.
        """
        return self._is_clockwise
    
    @property
    def diameter(self) -> Real:
        """Diameter of the arc.
        
        :getter: Returns the twice the arc's radius value.
        :setter: Updates the arc's radius value with half the provided value.
        :raises ValueError: Raised if provided a value less than 0.
        """
        return 2 * self.radius
    
    @property
    def end(self) -> Point:
        """The end point of the arc.
        
        :getter: Returns the end point of the arc.
        :setter: Read-only. Would cause undefined center, radius and start 
            behavior if changed by itself.
        """
        return self._end
    
    @property
    def end_angle(self) -> Real:
        """The angle from the positive horizontal axis to the end_vector in 
        radians. Bounded -pi < angle <= pi.
        
        :getter: Returns the calculated angle of the end_vector relative to the 
            positive horizontal axis in radians.
        :setter: Sets the end_vector based on the value given in radians.
        :raises ValueError: Raised if accessed on a 3D arc.
        """
        if len(self) == 3:
            raise ValueError("3D arcs cannot be defined by axis angles")
        return phi_of_cartesian(self.end_vector)
    
    @property
    def end_vector(self) -> tuple[Real]:
        """The unit vector pointing to the end of the arc from its center.
        
        :getter: Returns the vector.
        :setter: Sets the unit vector of the provided vector to the end vector 
            and updates the end point's position.
        """
        return self._end_vector
    
    @property
    def normal_vector(self) -> tuple[Real] | None:
        """The unit vector defining the direction of clockwise.
        
        :getter: Returns the vector.
        :setter: Sets the unit vector of the provided vector to the normal
            vector and updates the start/end points/vectors to their new 
            positions rotated around the center.
        """
        if len(self) == 3:
            raise NotImplementedError("3D arcs not implemented yet, see #143")
        return self._normal_vector
    
    @property
    def radius(self) -> Real:
        """Radius of the arc.
        
        :getter: Returns the arc's radius value.
        :setter: Updates the arc's radius if the given value is greater than 
            or equal to 0.
        :raises ValueError: Raised if provided a value less than 0.
        """
        return self._radius
    
    @property
    def start(self) -> Point:
        """The start point of the arc.
        
        :getter: Returns the start point of the arc.
        :setter: Read-only. Would cause undefined center, radius and end 
            behavior if changed by itself.
        """
        return self._start
    
    @property
    def start_angle(self) -> Real:
        """The angle from the positive horizontal axis to the start_vector.
        Bounded -pi < angle <= pi.
        
        :getter: Returns the calculated angle of the start_vector relative to the 
            positive horizontal axis in radians.
        :setter: Sets the end_vector based on the value given in radians.
        :raises ValueError: Raised if accessed on a 3D arc.
        """
        if len(self) == 3:
            raise ValueError("3D arcs cannot be defined by axis angles")
        return phi_of_cartesian(self.start_vector)
    
    @property
    def start_vector(self) -> tuple[Real]:
        """The unit vector pointing to the start of the arc from its center.
        
        :getter: Returns the vector.
        :setter: Sets the unit vector of the provided vector to the end vector 
            and updates the start point's position.
        """
        return self._start_vector
    
    # Setters #
    @center.setter
    def center(self, point: Point | VectorLike) -> None:
        if isinstance(point, VectorLike):
            point = Point(point)
        
        if len(point) != len(self):
            raise ValueError(f"Can't update {len(self)}D arc to {len(point)}D")
        
        self._center.update(point)
        start_location = self._center + self.radius * array(self.start_vector)
        end_location = self._center + self.radius * array(self.end_vector)
        
        # Vectors stay the same, points are just translated
        self._start.update(Point(start_location))
        self._end.update(Point(end_location))
    
    @is_clockwise.setter
    def is_clockwise(self, value: bool) -> None:
        self._is_clockwise = value
    
    @diameter.setter
    def diameter(self, value: Real) -> None:
        self.radius = value / 2
    
    @end_angle.setter
    def end_angle(self, angle: Real) -> None:
        if len(self) == 3:
            raise ValueError("3D arcs cannot be defined by axis angles")
        self.end_vector = polar_to_cartesian((1, angle))
    
    @end_vector.setter
    def end_vector(self, vector: VectorLike) -> None:
        if len(vector) != len(self):
            raise ValueError(f"Can't update {len(self)}D arc to {len(point)}D")
        
        unit_vector = get_unit_vector(vector)
        self._end_vector = to_1D_tuple(unit_vector)
        
        # Everything but the end point stays the same
        end_location = self.center + self.radius * unit_vector
        self._end.update(Point(end_location))
    
    @normal_vector.setter
    def normal_vector(self, vector: VectorLike | None) -> None:
        if len(self) == 3:
            raise NotImplementedError("3D arcs not implemented yet, see #143")
        elif vector is None:
            self._normal_vector = vector
        else:
            raise ValueError(f"2D Arc normals must be None. Given: {vector}")
    
    @start_angle.setter
    def start_angle(self, angle: Real) -> None:
        if len(self) == 3:
            raise ValueError("3D arcs cannot be defined by axis angles")
        self.start_vector = polar_to_cartesian((1, angle))
    
    @start_vector.setter
    def start_vector(self, vector: VectorLike) -> None:
        if len(vector) != len(self):
            raise ValueError(f"Can't update {len(self)}D arc to {len(point)}D")
        
        unit_vector = get_unit_vector(vector)
        self._start_vector = to_1D_tuple(unit_vector)
        # Everything but the start point stays the same
        start_location = self.center + self.radius * unit_vector
        self._start.update(Point(start_location))
    
    @radius.setter
    def radius(self, value: Real) -> None:
        if value < 0:
            raise ValueError(f"Radius cannot be < 0. Given: {value}")
        
        self._radius = value
        start_location = self._center + value * array(self.start_vector)
        end_location = self._center + value * array(self.end_vector)
        
        # Vectors and center stay the same, start/end points are translated
        self._start.update(Point(start_location))
        self._end.update(Point(end_location))
    
    # Public Methods #
    def get_reference(self, reference: ConstraintReference) -> Point | Self:
        """Returns reference geometry for use in external modules like 
        constraints.
        
        :param reference: A ConstraintReference enumeration value applicable to 
            CircularArcs. See :attr:`CircularArc.REFERENCES`.
        :returns: The geometry corresponding to the reference.
        """
        match reference:
            case ConstraintReference.CORE:
                return self
            case ConstraintReference.CENTER:
                return self.center
            case ConstraintReference.START:
                return self.start
            case ConstraintReference.END:
                return self.end
            case _:
                raise ValueError(f"CircularArcs do not have {reference.name}"
                                 " reference geometry")
    
    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns all ConstraintReferences applicable to CircularArcs. See 
        :attr:`CircularArc.REFERENCES`.
        """
        return self.REFERENCES
    
    def update(self, other: CircularArc) -> Self:
        """Updates the center point, radius, start/end vectors and is_clockwise
        to match the other CircularArc.
        
        :param other: A CircularArc to update this CircularArc to.
        :returns: The updated CircularArc.
        """
        if len(self) == len(other):
            self._center.update(other.center)
            self._radius = other.radius
            self._start_vector = other.start_vector
            self._end_vector = other.end_vector
            self._is_clockwise = other.is_clockwise
            if len(self) == 3:
                self.normal_vector = other.normal_vector
            return self
        else:
            raise ValueError("Cannot update a 2D circular arc to 3D")
    
    # Python Dunders #
    def __conform__(self, protocol: PrepareProtocol) -> str:
        if protocol is PrepareProtocol:
            if len(self) == 3:
                raise NotImplementedError("3D CircularArcs not implemented yet")
            vectors = [self.center.cartesian, self.start_vector, self.end_vector]
            vector_strings = map(lambda v: ";".join(map(str, v)), vectors)
            return "|".join(
                [
                    *vector_strings,
                    str(int(self.is_clockwise)),
                    str(self.radius),
                ]
            )
    
    def __copy__(self) -> CircularArc:
        """Returns a copy of the arc with the same radius, center point, 
        start/end vectors, but with no assigned uid.
        """
        return CircularArc(self.center,
                           self.radius,
                           self.start_vector,
                           self.end_vector,
                           self.is_clockwise,
                           self.normal_vector)
    
    def __eq__(self, other: CircularArc) -> bool:
        if isinstance(other, CircularArc):
            if len(self) == 3:
                raise NotImplementedError("3D Arcs not supported yet")
            return (
                isclose(self.center.cartesian, other.center.cartesian)
                and isclose(self.start_vector, other.start_vector)
                and isclose(self.end_vector, other.end_vector)
                and self.is_clockwise == other.is_clockwise
                and isclose(self.radius, other.radius)
            )
        else:
            return NotImplemented
    
    def __len__(self) -> int:
        """Returns whether the arc is 2D or 3D."""
        return len(self.center)
    
    def __str__(self) -> str:
        center_str = str(self.center.cartesian).replace(" ","")
        start_str = str(self.start.cartesian).replace(" ","")
        end_str = str(self.end.cartesian).replace(" ","")
        prefix = super().__str__()
        string = (f"{prefix}"
                  f"{center_str}c{start_str}s{end_str}e{self.radius}r")
        return string + ">"