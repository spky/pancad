"""A module providing a class to represent lines in all CAD programs,  
graphics, and other geometry use cases. Not to be confused with line 
segments, which is part of a line that is the shortest distance between two 
points.
"""
from __future__ import annotations

from functools import partial
import math
from numbers import Real
from typing import Self
from uuid import uuid4

import numpy as np

from PanCAD.geometry import AbstractGeometry, Point
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils import comparison, trigonometry as trig
from PanCAD.utils.pancad_types import VectorLike

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class Line(AbstractGeometry):
    """A class representing infinite lines in 2D and 3D space. A Line 
    instance can be uniquely identified and compared for equality/inequality 
    with other lines by using its direction and reference_point. The 
    reference_point is the point on the line closest to the origin and should 
    not be changed directly. The 'direction' of the line is defined to be 
    unique, see the definition in the :meth:`direction` property.
    
    :param point: A point on the line.
    :param direction: A vector in the direction of the line.
    :param uid: The unique ID of the line.
    """
    
    REFERENCES = (ConstraintReference.CORE,)
    """All relevant ConstraintReferences for Line."""
    
    def __init__(self,
                 point: Point=None,
                 direction: VectorLike=None,
                 uid: str=None) -> None:
        self.uid = uid
        self.direction = direction
        
        if isinstance(point, Point):
            self._point_closest_to_origin = Line.closest_to_origin(
                point, self.direction
            )
        elif isinstance(point, tuple):
            raise ValueError("point cannot be a tuple for Line's init function."
                             "Use Line.from_two_points instead")
        else:
            self._point_closest_to_origin = None
    
    # Class Methods #
    @classmethod
    def from_two_points(cls,
                        a: Point | VectorLike,
                        b: Point | VectorLike,
                        uid: str=None) -> Self:
        """Returns a Line instance defined by points a and b. 2D points will 
        produce 2D lines, 3D produce 3D lines, and 2D and 3D points cannot 
        be mixed.
        
        :param a: A PanCAD Point on the line.
        :param b: A PanCAD Point on the line that is not the same as point a.
        :param uid: The unique ID of the line.
        :returns: A Line that is coincident with points a and b.
        """
        if isinstance(a, VectorLike) and len(a) in (2, 3):
            a = Point(a)
        if isinstance(b, VectorLike) and len(b) in (2, 3):
            b = Point(b)
        
        if not isinstance(a, Point) or not isinstance(b, Point):
            raise ValueError("a and b must be VectorLikes or PanCAD Points."
                             f" Classes - a: {a.__class__}, b:{b.__class__}")
        
        if a != b:
            a_vector, b_vector = np.array(a), np.array(b)
            ab_vector = b_vector - a_vector
            return cls(Point(a_vector), ab_vector, uid)
        else:
            raise ValueError(f"A line cannot be defined by 2 points at the same"
                             f" location. Point a: {tuple(a)}, Point b:"
                             f" {tuple(b)}")
    
    @classmethod
    def from_slope_and_y_intercept(cls,
                                   slope: Real,
                                   intercept: Real,
                                   uid: str=None) -> Self:
        """Returns a 2D line described by y = mx + b, where m is the slope 
        and b is the y intercept.
        
        :param slope: The slope of the line.
        :param intercept: The y-intercept of the line.
        :param uid: The unique id of the line.
        :returns: A Line with the provided slope and intercept.
        """
        if slope == 0: # Horizontal
            point_a = Point((0, intercept))
            point_b = Point((1, intercept))
        else:
            point_a = Point((0, intercept))
            point_b = Point((1, slope + intercept))
        
        return Line.from_two_points(point_a, point_b, uid)
    
    @classmethod
    def from_point_and_angle(cls,
                             point: Point | VectorLike,
                             phi: Real,
                             theta: Real=None,
                             uid: str=None) -> Self:
        """Return a line from a given point and phi or phi and theta. The Line 
        will be 2D if point is 2D. The Line will be 3D if point is 3D, phi 
        is provided, and theta is provided.
        
        :param point: A point on the line.
        :param phi: The azimuth angle of the line around the point in radians.
        :param theta: The inclination angle of a 3D line around the point in 
            radians.
        :returns: A Line that runs through the point in a direction defined by 
            the provided angles.
        """
        if isinstance(point, VectorLike): point = Point(point)
        if len(point) == 2 and theta is None:
            direction_end_pt = Point(1, 0)
            direction_end_pt.phi = phi
        elif len(point) == 3 and theta is not None:
            direction_end_pt = Point(1, 0, 0)
            direction_end_pt.spherical = (1, phi, theta)
        elif len(point) == 3 and theta is None:
            raise ValueError("If a 3D point is given, theta must also be given")
        elif len(point) == 2 and theta is not None:
            raise ValueError("Theta can only be specified for 3D points")
        
        direction = tuple(direction_end_pt)
        return cls(point, direction, uid)
    
    @classmethod
    def from_x_intercept(cls, x_intercept: Real, uid: str=None) -> Self:
        """Returns a 2D vertical line that passes through the x intercept.
        
        :param x_intercept: The value of x where the line crosses the x-axis.
        :param uid: The unique ID of the line.
        :returns: A vertical line coincident with (x_intercept, 0).
        """
        return cls(Point(x_intercept, 0), (0, 1), uid)
    
    @classmethod
    def from_y_intercept(cls, y_intercept: Real, uid: str=None) -> Self:
        """Returns a 2D horizontal line that passes through the y intercept.
        
        :param y_intercept: The value of y where the line crosses the y-axis.
        :param uid: The unique ID of the line.
        :returns: A horizontal line coincident with (0, y_intercept).
        """
        return cls(Point(0, y_intercept), (1, 0), uid)
    
    # Getters #
    @property
    def direction(self) -> tuple[Real]:
        """The unique direction of the line with cartesian components.
        
        PanCAD Line Directions in 2D are defined to be unique since infinite 
        lines do not have a true direction. For a given vector, the unique 
        direction is defined by these rules:
        
        1. The direction vector must have a magnitude of 1.
        2. The z component must be positive or 0.
        3. If the z component is 0 or the line is 2D, the y component must be 
           positive or 0.
        4. If both the y and z components are 0, the x component must be 
           positive.
        
        :getter: Returns the direction of the line.
        :setter: Finds and sets the vector's unique direction vector as the 
            direction of the Line.
        """
        return self._direction
    
    @property
    def direction_polar(self) -> tuple[Real]:
        """The unique direction of the line with polar components.
        
        :getter: Returns the direction of the line as a (r, phi) tuple. Phi is 
            the azimuth angle in radians.
        :setter: Finds and sets the polar vector's unique direction vector as 
            the direction of the Line.
        """
        return trig.cartesian_to_polar(self.direction)
    
    @property
    def direction_spherical(self) -> tuple[Real]:
        """The unique direction of the line with spherical components.
        
        :getter: Returns the direction of the line as a (r, phi, theta) tuple. 
            phi and theta are the azimuth and inclination angles respectively, 
            in radians.
        :setter: Finds and sets the spherical vector's unique direction vector 
            as the direction of the Line.
        """
        return trig.cartesian_to_spherical(self.direction)
    
    @property
    def phi(self) -> Real:
        """The polar/spherical azimuth component of the line's direction in 
        radians.
        
        :getter: Returns the azimuth component of the line's direction.
        :setter: Read-only.
        """
        return trig.phi_of_cartesian(self.direction)
    
    @property
    def reference_point(self) -> Point:
        """The closest point to the origin on the line.
        
        :getter: Returns a copy of the Point closest to the origin on the line.
        :setter: Read-only.
        """
        return self._point_closest_to_origin.copy()
    
    @property
    def slope(self) -> Real:
        """The slope of the line (m in y = mx + b), only available if the line 
        is 2D.
        
        :getter: Returns the slope of the line.
        :setter: Sets the slope of the line while keeping the y intercept (b 
            in y = mx + b) the same.
        """
        if len(self) == 2:
            if self.direction[0] == 0:
                return math.nan
            else:
                return self.direction[1]/self.direction[0]
        else:
            raise ValueError("slope is not defined for a 3D line")
    
    @property
    def theta(self) -> Real:
        """The spherical inclination component of the line's direction in 
        radians.
        
        :getter: Returns the inclination angle of the line's direction
        :setter: Read-only.
        """
        return trig.theta_of_cartesian(self.direction)
    
    @property
    def x_intercept(self) -> Real:
        """The x-intercept of the 2D line (x when y = 0 in y = mx + b), raises
        a ValueError if the line is 3D.
        
        :getter: Returns the x-intercept of the line.
        :setter: Sets the x-intercept of the line while keeping the slope (m 
            in y = mx + b) constant.
        """
        if len(self) == 2:
            if self.direction[0] == 1:
                return math.nan
            elif self.direction[0] == 0:
                return self.reference_point.x
            else:
                return (self.slope*self.reference_point.x
                        - self.reference_point.y)/self.slope
        else:
            raise ValueError("x-intercept is not defined for a 3D line")
    
    @property
    def y_intercept(self) -> Real:
        """The y-intercept of the line (b in y = mx + b), only available if 
        the line is 2D.
        
        :getter: Returns the y-intercept of the line
        :setter: Sets the y-intercept of the line while keeping the slope (m 
            in y = mx + b) constant.
        """
        if len(self) == 2:
            if self.direction[0] == 0:
                return math.nan
            else:
                return (self.reference_point.y
                        - self.slope*self.reference_point.x)
        else:
            raise ValueError("y-intercept is not defined for a 3D line")
    
    # Setters #
    @direction.setter
    def direction(self, vector: VectorLike) -> None:
        if vector is not None:
            vector = trig.to_1D_np(vector)
            self._direction = Line._unique_direction(vector)
        else:
            self._direction = None
    
    @direction_polar.setter
    def direction_polar(self, vector: VectorLike) -> None:
        self.direction = trig.polar_to_cartesian(vector)
    
    @direction_spherical.setter
    def direction_spherical(self, vector: VectorLike) -> None:
        self.direction = trig.spherical_to_cartesian(vector)
    
    # Public Methods #
    def copy(self) -> Line:
        """Returns a copy of the Line.
        
        :returns: A new Line with the same position and direction as this Line.
        """
        return self.__copy__()
    
    def get_parametric_point(self, t: Real) -> Point:
        """Returns the point at parameter t where a, b, and c are defined by 
        the unique unit vector direction of the line and initialized at the 
        point closest to the origin.
        
        :param t: The value of the line parameter.
        :returns: The Point on the line corresponding to the parameter's value.
        """
        return Point(np.array(self.reference_point)
                     + trig.to_1D_np(self.direction)*t)
    
    def get_parametric_constants(self) -> tuple[Real]:
        """Returns a tuple containing parameters for the line. The reference 
        point is used for the initial position and the line's direction vector 
        is used for a, b, and c.
        
        :returns: Line parameters (x0, y0, z0, a, b, c)
        """
        return (*self.reference_point.cartesian, *self.direction)
    
    def get_reference(self, reference: ConstraintReference) -> Self:
        """Returns reference geometry for use in external modules like 
        constraints. Raises a ValueError if the ConstraintReference is not 
        relevant for Lines.
        
        :param reference: A ConstraintReference enumeration value applicable to 
            Lines. See :attr:`Line.REFERENCES`.
        :returns: The geometry corresponding to the reference.
        """
        match reference:
            case ConstraintReference.CORE:
                return self
            case _:
                raise ValueError(f"{self.__class__}s do not have any"
                                 f" {reference.name} reference geometry")
    
    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns all ConstraintReferences applicable to Lines. See 
        :attr:`Line.REFERENCES`.
        """
        return self.REFERENCES
    
    def move_to_point(self,
                      point: Point,
                      phi: Real=None,
                      theta: Real=None) -> Self:
        """Moves the line to go through a point and changes the line's 
        direction's around that point.
        
        :param point: A point the user wants to be on the line
        :param phi: The line's new azimuth angle around the point in radians. If
            None, the Line's azimuth angle remains constant.
        :param theta: The line's new inclination angle around the point in 
            radians. If None, the Line's inclination angle remains constant.
        :returns: The line with an updated reference_point that goes through the
            point.
        """
        if phi is not None or theta is not None:
            direction_end_pt = Point(self.direction)
            if phi is not None and theta is not None and len(self) == 3:
                direction_end_pt.spherical = (1, phi, theta)
            elif theta is not None and len(self) == 2:
                raise ValueError("Theta can only be set on 3D Lines")
            elif phi is not None and theta is None:
                direction_end_pt.phi = phi
            elif phi is None and theta is not None:
                direction_end_pt.theta = theta
            self.direction = tuple(direction_end_pt)
        
        self._point_closest_to_origin = self.closest_to_origin(
            point, self.direction
        )
        return self
    
    def update(self, other: Line) -> Self:
        """Updates the line to match the position and direction of another line.
        
        :param other: The line to update to.
        :returns: The updated Line.
        """
        self._point_closest_to_origin.update(other.reference_point)
        self.direction = other.direction
        return self
    
    # Static Methods #
    @staticmethod
    def closest_to_origin(point: Point, vector: VectorLike) -> Point:
        """Returns the point on a line created by the point and vector closest 
        to the origin.
        
        :param point: A Point on the line.
        :param vector: A vector in the direction of the line.
        :returns: The point on the line created by the given point and vector 
            closest to the origin.
        """
        point_vector = np.array(point)
        vector = trig.to_1D_np(vector)
        unit_vector = trig.get_unit_vector(vector)
        dot_product = np.dot(point_vector, unit_vector)
        
        if dot_product == 0:
            point_closest_to_origin = Point(point_vector)
        elif abs(dot_product) == np.linalg.norm(point_vector):
            if len(point) == 2:
                point_closest_to_origin = Point((0,0))
            else:
                point_closest_to_origin = Point((0,0,0))
        elif (np.linalg.norm(point_vector + unit_vector)
              < np.linalg.norm(point_vector + unit_vector)):
            point_closest_to_origin = Point(
                point_vector + dot_product * unit_vector
            )
        else:
            point_closest_to_origin = Point(
                point_vector - dot_product * unit_vector
            )
        
        return point_closest_to_origin
    
    @staticmethod
    def _unique_direction(vector: np.ndarray) -> np.ndarray:
        """Returns a unit vector that can uniquely identify the direction of 
        the given vector. Does so flipping the unit vector if necessary to 
        ensure there can only ever be one vector for every direction.
        
        :param vector: A 1D vector of cartesian coordinates.
        :returns: The unique unit vector to represent the vector's direction.
        """
        unit_vector = trig.get_unit_vector(vector)
        if len(unit_vector) == 3:
            x, y, z = unit_vector
            if x < 0 and isclose0(y) and isclose0(z):
                unit_vector = -unit_vector
            elif y < 0 and isclose0(z):
                unit_vector = -unit_vector
            elif z < 0:
                unit_vector = -unit_vector
        elif len(unit_vector) == 2:
            x, y = unit_vector
            if x < 0 and isclose0(y):
                unit_vector = -unit_vector
            elif not isclose0(y) and y < 0:
                unit_vector = -unit_vector
        
        # Add 0 to ensure negative zero representations are eliminated
        return trig.to_1D_tuple(unit_vector + 0)
    
    # Python Dunders #
    def __copy__(self) -> Line:
        """Returns a copy of the line that has the same closest to origin 
        point and direction, but a different uid. Can be used with the python 
        copy module.
        """
        return Line(self.reference_point, self.direction)
    
    def __eq__(self, other: Line) -> bool:
        """Rich comparison for line equality that allows for lines to be 
        directly compared with ==.
        
        :param other: The line to compare self to.
        :returns: Whether the tuples of the lines' reference_points and 
            directions are equal.
        """
        if isinstance(other, Line):
            return (
                isclose(tuple(self._point_closest_to_origin),
                        tuple(other._point_closest_to_origin))
                and isclose(self.direction, other.direction)
            )
        else:
            return NotImplemented
    
    def __len__(self) -> int:
        """Returns the number of elements in the line's direction tuple, 
        which is equivalent to the line's number of dimnesions.
        """
        return len(self.direction)
    
    def __repr__(self) -> str:
        """Returns the short string representation of the line."""
        pt_strs, direction_strs = [], []
        for i in range(0, len(self.direction)):
            if isclose0(self._point_closest_to_origin[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self._point_closest_to_origin[i]))
            if isclose0(self.direction[i]):
                direction_strs.append("0")
            else:
                direction_strs.append("{:g}".format(self.direction[i]))
        point_str = ",".join(pt_strs)
        direction_str = ",".join(direction_strs)
        return f"<PanCADLine'{self.uid}'({point_str})({direction_str})>"
    
    def __str__(self) -> str:
        """String function to output the line's description, closest 
        cartesian point to the origin, and unique cartesian direction 
        unit vector.
        """
        pt_strs, direction_strs = [], []
        for i in range(0, len(self.direction)):
            if isclose0(self._point_closest_to_origin[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self._point_closest_to_origin[i]))
            if isclose0(self.direction[i]):
                direction_strs.append("0")
            else:
                direction_strs.append("{:g}".format(self.direction[i]))
        point_str = ", ".join(pt_strs)
        direction_str = ", ".join(direction_strs)
        return (f"PanCAD Line with a point closest to the origin at"
                + f" ({point_str}) and in the direction ({direction_str})")