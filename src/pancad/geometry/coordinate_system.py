"""A module providing a class to represent coordinate systems in CAD programs,
graphics, and other geometry use cases.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Self

import numpy as np
import quaternion

from pancad.abstract import AbstractGeometry
from pancad.constants import ConstraintReference as CR
from pancad.geometry.point import Point
from pancad.geometry.line import Axis
from pancad.geometry.plane import Plane
from pancad.utils.trigonometry import yaw_pitch_roll
from pancad.utils.pancad_types import VectorLike
from pancad.utils.text_formatting import format_vector

if TYPE_CHECKING:
    from typing import NoReturn
    from numbers import Real

    from pancad.utils.pancad_types import (
        SpaceVector, Space3DVector, Space2DVector
    )

class CoordinateSystem(AbstractGeometry):
    """A class representing coordinate systems in 2D and 3D space. Initial
    rotation is defined by Tait-Bryan (zyx) yaw-pitch-roll angles.

    :param origin: A 2D or 3D center Point of the coordinate system.
    :param rotation: A rotation matrix or quaternion to rotate the canonical
        2D/3D CoordinateSystem to a desired orientation.
    :param uid: The unique ID of the coordinate system.
    """
    def __init__(self,
                 origin: Point | SpaceVector,
                 rotation: np.ndarray | np.quaternion=None,
                 *, uid: str=None) -> None:
        self.uid = uid
        if not isinstance(origin, Point):
            origin = Point(origin)
        references = {CR.CORE: self, CR.ORIGIN: origin}
        if len(origin) == 2:
            axes = {CR.X: (1, 0), CR.Y: (0, 1)}
        else:
            axes = {CR.X: (1, 0, 0), CR.Y: (0, 1, 0), CR.Z: (0, 0, 1)}
            planes = {CR.XY: (0, 0, 1), CR.XZ: (0, 1, 0), CR.YZ: (1, 0, 0)}
            references.update({r: Plane(origin, n) for r, n in planes.items()})
        references.update({r: Axis(origin, v) for r, v in axes.items()})
        super().__init__(references)
        if rotation is not None:
            self.rotate(rotation)

    @classmethod
    def from_yaw_pitch_roll(cls, position: Point | Space3DVector,
                            yaw: Real=0, pitch: Real=0, roll: Real=0,
                            **kwargs) -> None:
        """Initializes a Pose from yaw, pitch, and roll angles in radians."""
        rotation = yaw_pitch_roll(yaw, pitch, roll)
        return cls(position, rotation, **kwargs)

    # Properties
    @property
    def origin(self) -> Point:
        """The CoordinateSystem's Origin Point."""
        return self.get_reference(CR.ORIGIN)

    @origin.setter
    def origin(self, point: Point | SpaceVector):
        self.move_to_point(point)

    @property
    def x_axis(self) -> Axis:
        """The CoordinateSystem's X-Axis."""
        return self.get_reference(CR.X)

    @property
    def y_axis(self) -> Axis:
        """The CoordinateSystem's Y-Axis."""
        return self.get_reference(CR.Y)

    @property
    def z_axis(self) -> Axis:
        """The CoordinateSystem's Z-Axis."""
        return self.get_reference(CR.Z)

    @property
    def xy_plane(self) -> Plane:
        """The CoordinateSystem's XY-Plane."""
        return self.get_reference(CR.XY)

    @property
    def xz_plane(self) -> Plane:
        """The CoordinateSystem's XZ-Plane."""
        return self.get_reference(CR.XZ)

    @property
    def yz_plane(self) -> Plane:
        """The CoordinateSystem's YZ-Plane."""
        return self.get_reference(CR.YZ)

    # Public Methods
    def copy(self) -> CoordinateSystem:
        """Returns a copy of the CoordinateSystem.

        :returns: the same origin, axes, and planes, but not the same uid.
        """
        return CoordinateSystem(self.origin).update(self)

    # def get_quaternion(self) -> np.quaternion:
        # """Returns a quaternion that can be used to rotate other vectors from
        # the canonical cartesian coordinate system (1, 0, 0), (0, 1, 0),
        # (0, 0, 1) to this coordinate system.
        # """
        # # TODO: Update get_quaternion to work with new Axis and Plane
        # canon_vectors = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        # system_vectors = [self.x_vector, self.y_vector, self.z_vector]
        # canon = SystemAxes3D(*[np.array(axis) for axis in canon_vectors])
        # sys = SystemAxes3D(*[np.array(axis) for axis in system_vectors])
        # if all(np.isclose(np.dot(c, s), 1) for c, s in zip(canon, sys)):
            # # Check if the axes are all close to the canon axis directions and
            # # return a quaternion with no rotation if so.
            # return np.quaternion(1, 0, 0, 0)
        # parallel_to_canons = [np.isclose(abs(np.dot(c, s)), 1)
                              # for c, s in zip(canon, sys)]
        # if all(parallel_to_canons):
            # # Can only happen if all axes are counter-parallel, since they've all
            # # been checked for whether they are the exact same. That would mean
            # # that this is an opposite-handed coordinate system and wouldn't be
            # # possible to rotate to.
            # msg =("Cannot create a quaternion to rotate to this coordinate"
                  # "system from a canon right-handed coordinate_system")
            # raise ValueError(msg)
        # canon_axis = canon[parallel_to_canons.index(False)]
        # current_axis = sys[parallel_to_canons.index(False)]
        # euler_axis = np.cross(canon_axis, current_axis)
        # euler_axis = euler_axis / np.linalg.norm(euler_axis)
        # normed_dot = (
            # np.dot(canon_axis, current_axis)
            # / (np.linalg.norm(canon_axis) * np.linalg.norm(current_axis))
        # )
        # cos_half_theta = np.sqrt((1 + normed_dot)/2)
        # sin_half_theta = np.sqrt((1 - normed_dot)/2)
        # quat_vector = euler_axis * sin_half_theta
        # return np.quaternion(cos_half_theta, *quat_vector)

    def update(self, other: CoordinateSystem) -> Self:
        """Updates the origin, axes, and planes of the CoordinateSystem to match
        another CoordinateSystem.

        :param other: The CoordinateSystem to update to.
        :returns: The updated CoordinateSystem.
        """
        for ref, geometry in self.children.items():
            if ref == CR.CORE:
                continue
            geometry.update(other.get_reference(ref))
        return self

    def rotate(self, rotation: np.ndarray | np.quaternion) -> Self:
        """Rotates the system with a rotation matrix or quaternion."""
        for ref, geometry in self.children.items():
            if ref in (CR.ORIGIN, CR.CORE):
                continue
            geometry.rotate(rotation) # Rotate around closest points
            geometry.move_to_point(self.origin) # Realign axes and planes
        return self

    def move_to_point(self, location: Point | SpaceVector) -> Self:
        """Moves the system to a new location with no rotation."""
        if not isinstance(location, Point):
            location = Point(location)
        self.origin.update(location)
        for ref, geometry in self.children.items():
            if ref in (CR.ORIGIN, CR.CORE):
                continue
            geometry.move_to_point(location)
        return self

    # Python Dunders
    def __copy__(self) -> CoordinateSystem:
        """Returns a copy of the CoordinateSystem that has the same origin,
        axes, planes and context, but not the same uid. Can be used with the
        python copy module.
        """
        return self.copy()

    def __repr__(self) -> str:
        label_map = {"": self.origin.cartesian,
                     "X": self.x_axis.direction, "Y": self.y_axis.direction}
        strings = [f"{l}({format_vector(v)})" for l, v in label_map.items()]
        return super().__repr__().format(details="".join(strings))

    def __len__(self) -> int:
        """Returns the number of dimensions of the coordinate system by
        returning the number of dimensions of the origin point.
        """
        return len(self.origin)


class Pose(AbstractGeometry):
    """The position and orientation of a 3D object."""
    def __init__(self, coordinate_system: CoordinateSystem,
                 *, uid: str=None) -> None:
        self.uid = uid
        if (dimensions := len(coordinate_system)) != 3:
            raise ValueError("Expected 3D coordinate system,"
                             f" got {dimensions}D: {coordinate_system}")
        self._coordinate_system = coordinate_system
        super().__init__(
            {
                CR.CORE: self,
                CR.ORIGIN: self._coordinate_system.origin,
                CR.X: self._coordinate_system.x_axis,
                CR.Y: self._coordinate_system.y_axis,
                CR.Z: self._coordinate_system.z_axis,
                CR.FRONT: self._coordinate_system.xy_plane,
                CR.RIGHT: self._coordinate_system.xz_plane,
                CR.TOP: self._coordinate_system.yz_plane,
                CR.CS: self._coordinate_system,
            }
        )

    @classmethod
    def from_yaw_pitch_roll(cls, position: Point | VectorLike,
                            yaw: Real=0, pitch: Real=0, roll: Real=0,
                            **kwargs) -> None:
        """Initializes a Pose from yaw, pitch, and roll angles in radians."""
        coordinate_system = CoordinateSystem.from_yaw_pitch_roll(
            position, yaw, pitch, roll
        )
        return cls(coordinate_system, **kwargs)

    @property
    def coordinate_system(self) -> CoordinateSystem:
        """Internal coordinate_system representing the the Pose."""
        return self.get_reference(CR.CS)

    @property
    def origin(self) -> Point:
        """The origin point of the Pose's internal coordinate_system."""
        return self.get_reference(CR.ORIGIN)

    @property
    def front(self) -> Plane:
        """Front plane of the Pose."""
        return self.get_reference(CR.FRONT)

    @property
    def right(self) -> Plane:
        """Right plane of the Pose."""
        return self.get_reference(CR.RIGHT)

    @property
    def top(self) -> Plane:
        """Top plane of the Pose."""
        return self.get_reference(CR.TOP)

    def move_to_point(self, location: Point) -> Self:
        """Moves the pose to a new location with no rotation."""
        self.coordinate_system.move_to_point(location)

    def rotate(self, rotation: np.ndarray | quaternion.quaternion) -> Self:
        """Rotates the pose with a rotation matrix or quaternion."""
        self.coordinate_system.rotate(rotation)
        return self

    def update(self, other: Pose) -> Self:
        """Updates the position and orientation of the Pose to the other Pose."""
        self.coordinate_system.update(other.coordinate_system)
        return self

    def __len__(self) -> int:
        """Returns the number of dimensions of the Pose. Poses are always 3D."""
        return 3

    def __repr__(self) -> str:
        origin = str(tuple(self.origin)).replace(" ", "")
        return super().__repr__().format(details=f"{origin}")
