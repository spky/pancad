"""A module providing a class to represent lines in all CAD programs,
graphics, and other geometry use cases."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pancad.abstract import AbstractGeometry
from pancad.constants import ConstraintReference
from pancad.geometry.point import Point
from pancad.geometry.line import Axis
from pancad.utils import trigonometry as trig

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Self

    from pancad.utils.pancad_types import Space3DVector, Numpy1D, Numpy2D, SphericalVector
    from pancad.utils.quat import Quat

class Plane(AbstractGeometry):
    """A class representing planes in 3D space."""
    def __init__(self, point: Point | Sequence[float] | Numpy1D,
                 normal: Sequence[float] | Numpy1D | Numpy2D,
                 uid: str | None=None):
        self.uid = uid
        if not isinstance(point, Point):
            point = Point(point)
        self._axis = Axis(point, normal)
        if len(self._axis.direction) != 3:
            raise ValueError(f"Plane normal vector must be 3D, got: {normal}")
        self._point_closest_to_origin = Plane._closest_to_origin(point, self.normal)
        self._axis.move_to_point(self._point_closest_to_origin)
        super().__init__({ConstraintReference.CORE: self})

    @classmethod
    def from_point_and_angles(cls,
                              point: Point | Sequence[float] | Numpy1D,
                              phi: float,
                              theta: float,
                              uid: str | None=None) -> Plane:
        """Return a Plane from a given point, phi, and theta.

        :param point: A point on the plane
        :param phi: The phi angle of the plane's normal vector in radians
        :param theta: The theta angle of the plane's normal vector in radians
        :returns: A Plane object that runs through the point with a normal vector
            with the provided angles
        """
        return cls(point, trig.spherical_to_cartesian((1, phi, theta)), uid)

    @property
    def normal(self) -> Space3DVector:
        """The unit vector that describes the normal direction of the plane.

        :getter: Returns the normal vector of the plane.
        :setter: Sets the plane's normal to a new vector. Pivots about the Plane's current
            reference point.
        """
        assert len(self._axis.direction) == 3
        return self._axis.direction

    @normal.setter
    def normal(self, vector: Sequence[float] | Numpy1D | Numpy2D) -> None:
        self._axis.move_to_point(self._point_closest_to_origin, vector)

    @property
    def normal_spherical(self) -> SphericalVector:
        """The unit vector describing the normal direction of the plane in
        spherical coordinates. Read-only.
        """
        return trig.cartesian_to_spherical(self.normal)

    @property
    def phi(self) -> float:
        """The spherical azimuth of the plane's normal vector in radians.
        Read-only.
        """
        return trig.phi_of_cartesian(self.normal)

    @property
    def reference_point(self) -> Point:
        """The closest point to the origin on the plane. Read-only.

        :getter: Returns a copy of the Point instance representing the point
            closest to the origin on the plane.
        """
        # Copy to prevent remote changes of the plane reference point.
        return self._point_closest_to_origin.copy()

    @property
    def reference_axis(self) -> Axis:
        """the axis normal to the plane and going through the point closest to
        the origin. Read-only
        """
        return self._axis.copy()

    @property
    def theta(self) -> float:
        """The spherical inclination component of the plane's normal vector in
        radians. Read-only.

        :getter: Returns the inclination angle of the plane's normal vector.
        """
        return trig.theta_of_cartesian(self.normal)

    def copy(self) -> Plane:
        """Returns a copy of the plane that has the same closest to origin
        point and normal vector, but with a different uid.
        """
        return Plane(self.reference_point, self.normal)

    def is_equal(self, other: Plane) -> bool:
        """Returns whether the other geometry is geometrically equal. This is a
        separate check from whether a geometry element is equal to this
        geometry element since the uids would not be the same.
        """
        return (self.reference_axis.is_equal(other.reference_axis)
                and self.reference_point.is_equal(other.reference_point))

    def get_d(self) -> float:
        """Returns the Plane's Point-Normal form constant d (equation of form
        ax + by + cz + d = 0)
        """
        a, b, c = self.normal
        x0, y0, z0 = tuple(self.reference_point)
        return -(a*x0 + b*y0 + c*z0)

    def move_to_point(self, point: Point | Sequence[float] | Numpy1D,
                      normal: Sequence[float] | Numpy1D | Numpy2D | None=None) -> Self:
        """Moves the plane to the point. Sets the normal vector at that point if
        it is given.

        :param point: A point the plane will be coincident to.
        :param normal: A new normal vector for the plane. Defaults to the
            original normal vector when None.
        :returns: The updated Plane to enable chaining.
        """
        if not isinstance(point, Point):
            point = Point(point)
        if normal is None:
            normal = self.normal
        else:
            normal = trig.to_1d_tuple(normal)
            if len(normal) != 3:
                raise ValueError(f"Plane normal vector must be 3D, got: {normal}")
        new_closest = Plane._closest_to_origin(point, normal)
        self._point_closest_to_origin.update(new_closest)
        if normal is not None:
            self.normal = normal
        return self

    def rotate(self, rotation: Numpy2D | Quat) -> Self:
        """Rotates the plane about its point closest to the origin.

        :param rotation: The matrix or quaternion to rotate with.
        :returns: The updated Plane to enable chaining.
        """
        try:
            self._axis.rotate(rotation)
        except ValueError as exc:
            exc.add_note(f"Rotation of Plane Axis failed using: {rotation}")
            raise
        return self

    def update(self, other: Plane) -> Self:
        """Updates the plane to match the position and normal direction of
        another plane.

        :param other: The plane to update to
        """
        self._point_closest_to_origin.update(other.reference_point)
        self.normal = other.normal
        return self

    @staticmethod
    def _closest_to_origin(point: Point, normal: Space3DVector) -> Point:
        """Returns the point on the plane created by the point and normal vector
        closest to the origin.

        :param point: A Point on the plane
        :param normal: A vector normal to the plane
        :returns: The point on the plane closest to the origin
        """
        x0, y0, z0 = tuple(point)
        a, b, c = tuple(normal)
        # Equation derived from finding the itersection of a line through the
        # origin that is also perpendicular to the plane.
        t = (a*x0 + b*y0 + c*z0)/(a**2 + b**2 + c**2)
        return Point(a*t, b*t, c*t)

    def __copy__(self) -> Plane:
        return self.copy()

    def __len__(self) -> int:
        """Returns the number of elements in the plane's normal tuple,
        which is equivalent to the plane's number of dimnesions. Should always be
        3, but this is included for compatibility with other 2D objects."""
        return len(self.normal)

    def __repr__(self) -> str:
        """Returns the short string representation of the plane. Contains the
        point closest to the origin and the unit vector normal to the plane.
        """
        strings = []
        for vector in [self.reference_point.cartesian, self.normal]:
            vector_strings = []
            for component in vector:
                if np.isclose(component, 0):
                    vector_strings.append("0")
                else:
                    vector_strings.append(f"{component:g}")
            strings.append(",".join(vector_strings))
        point, normal = strings
        return super().__repr__().format(details=f"({point})({normal})")
