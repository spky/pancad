"""A module providing a class to represent coordinate systems in CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass, fields
from functools import partial, singledispatchmethod, partialmethod
from textwrap import indent
from typing import TYPE_CHECKING, Self

import numpy as np
import quaternion

from pancad.abstract import AbstractFeature, AbstractGeometry
from pancad.constants import ConstraintReference
from pancad.geometry.point import Point
from pancad.geometry.line import Line
from pancad.geometry.plane import Plane
from pancad.utils import comparison
from pancad.utils.trigonometry import yaw_pitch_roll, rotation_2
from pancad.utils.pancad_types import VectorLike

if TYPE_CHECKING:
    from typing import NoReturn
    from numbers import Real

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

SystemAxes3D = namedtuple("SystemAxes3D", ["x", "y", "z"])

def updates_planes(func):
    """A wrapper to sync up SystemParts planes after the axes are updated."""
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if self.z is not None:
            for axis, plane in zip(reversed(self.get_axes()),
                                   self.get_planes()):
                plane.update(Plane(self.origin, axis.direction))
        return result
    return wrapper


@dataclass
class SystemParts:
    """A dataclass containing the geometric parts of a CoordinateSystem."""
    origin: Point
    x: Line
    y: Line
    z: Line = None
    xy: Plane = None
    xz: Plane = None
    yz: Plane = None

    def _get_typed(self, type_: str) -> list[Point | Line | Plane]:
        """Returns the non-None values of a specified type."""
        values = [getattr(self, field.name)
                  for field in fields(self) if field.type == type_]
        return [value for value in values if value is not None]

    get_axes = partialmethod(_get_typed, type_="Line")

    get_planes = partialmethod(_get_typed, type_="Plane")

    @updates_planes
    def move_to_point(self, location: Point) -> Self:
        """Moves the system to a new location with no rotation."""
        if not isinstance(location, Point):
            location = Point(location)
        self.origin.update(location)
        for axis in self.get_axes():
            axis.move_to_point(location)
        return self

    @singledispatchmethod
    @updates_planes
    def rotate(self, rotation) -> Self:
        """Applies rotation to the axes and planes about the origin."""
        raise TypeError(f"Expected numpy array or quaternion, got {rotation}")

    @rotate.register
    def _matrix(self, matrix: np.ndarray) -> Self:
        """Rotate with a rotation matrix."""
        if self.z is None and matrix.shape != (2, 2):
            raise ValueError(f"Expected 2x2 matrix, got {matrix}")
        if self.z is not None and matrix.shape != (3, 3):
            raise ValueError(f"Expected 3x3 matrix, got {matrix}")
        for axis in self.get_axes():
            axis.update(Line(self.origin, matrix @ axis.direction))
        return self

    @rotate.register
    def _quaternion(self, quat: quaternion.quaternion) -> Self:
        if self.z is None:
            raise ValueError("Cannot rotate 2D systems with quaternions!")
        for axis in self.get_axes():
            axis.update(
                Line(self.origin, quaternion.rotate_vectors(quat, axis.direction))
            )
        return self


class CoordinateSystem(AbstractGeometry, AbstractFeature):
    """A class representing coordinate systems in 2D and 3D space. Initial 
    rotation is defined by Tait-Bryan (zyx) yaw-pitch-roll angles.
    
    :param origin: A 2D or 3D center Point of the coordinate system. Defaults to 
        (0, 0, 0).
    :param alpha: Angle to rotate about the z-axis in radians, defaults to 0.
    :param beta: Angle to rotate about the y-axis in radians after alpha 
        rotation, defaults to 0. Cannot be set for a 2D coordinate system.
    :param gamma: Angle to rotate about the x-axis after beta rotation, defaults 
        to 0. Cannot be set for a 2D coordinate system.
    :param uid: The unique ID of the coordinate system.
    :param name: The name of the feature displayed to the users in CAD.
    :param context: The feature that acts as the context for this feature, 
        usually a :class:`~pancad.geometry.FeatureContainer`
    """
    def __init__(self,
                 origin: Point | VectorLike,
                 alpha: Real=0, beta: Real=0, gamma: Real=0,
                 *,
                 uid: str=None,
                 context: AbstractFeature=None,
                 name: str=None) -> None:
        if isinstance(origin, VectorLike):
            origin = Point(origin)
        if not isinstance(origin, Point):
            raise TypeError(f"Expected Point/Vector for origin, got {origin}")
        if len(origin) == 2 and any(angle != 0 for angle in [beta, gamma]):
            raise ValueError(f"beta {beta} and gamma {gamma} must be 0 when 2D")
        if len(origin) == 2:
            canon_vectors = [(1, 0), (0, 1)]
            planes = []
            rotation_matrix = rotation_2(alpha)
        else:
            canon_vectors = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
            planes = [Plane(origin, vector) for vector in reversed(canon_vectors)]
            rotation_matrix = yaw_pitch_roll(alpha, beta, gamma)
        axes = [Line(origin, vector) for vector in canon_vectors]
        self._parts = SystemParts(origin, *axes, *planes)
        self.rotate(rotation_matrix)
        self.name = name
        self.context = context
        self.uid = uid
        references = {
            ConstraintReference.CORE: self,
            ConstraintReference.ORIGIN: self._parts.origin,
            ConstraintReference.X: self._parts.x,
            ConstraintReference.Y: self._parts.y,
        }
        if len(self) == 3:
            references.update(
                {
                    ConstraintReference.Z: self._parts.z,
                    ConstraintReference.XY: self._parts.xy,
                    ConstraintReference.XZ: self._parts.xz,
                    ConstraintReference.YZ: self._parts.yz,
                }
            )
        super().__init__(references)

    # Class Methods #
    @classmethod
    def from_quaternion(cls,
                        origin: Point | VectorLike,
                        quat: np.quaternion,
                        *,
                        uid: str=None,
                        name: str=None,
                        context: AbstractFeature=None) -> CoordinateSystem:
        """Returns a 3D coordinate system defined with a quaternion.
        
        :param origin: A 3D center Point of the coordinate system. Defaults to 
            (0, 0, 0).
        :param quat: A numpy quaternion used to rotate the coordinate system 
            from the canonical cartesian coordinate orientation to its desired 
            location.
        :param uid: The unique ID of the coordinate system.
        :returns: A 3D CoordinateSystem rotated according to the quaternion.
        """
        if len(origin) != 3:
            raise ValueError("2D Coordinate Systems cannot be initialized"
                             " with quaternions")
        # Initialize an unrotated coordinate system
        coordinate_system = cls(origin,
                                0, 0, 0,
                                uid=uid,
                                context=context,
                                name=name)
        return coordinate_system.rotate(quat)

    # Properties
    @property
    def parts(self) -> SystemParts:
        """The geometric parts of the coordinate system. Read-only."""
        return self._parts

    @property
    def origin(self) -> Point:
        """The origin point of the coordinate system.
        
        :getter: Returns the origin point of the coordinate system.
        :setter: Updates the origin point's location from another Point or 
            position vector.
        """
        return self._parts.origin
    @origin.setter
    def origin(self, point: Point | VectorLike):
        if isinstance(point, VectorLike):
            point = Point(point)
        self._parts.origin.update(point)

    @property
    def x_vector(self) -> tuple[Real]:
        """The direction vector of the coordinate system's x-axis. Read-only."""
        return self._parts.x.direction

    @property
    def y_vector(self) -> tuple[Real]:
        """The direction vector of the coordinate system's y-axis. Read-only."""
        return self._parts.y.direction

    @property
    def z_vector(self) -> tuple[Real]:
        """The direction vector of the coordinate system's z-axis. Read-only."""
        return self._parts.z.direction

    # Public Methods
    def copy(self) -> CoordinateSystem:
        """Returns a copy of the CoordinateSystem.
        
        :returns: the same origin, axes, planes and context, but not the same 
            uid.
        """
        return CoordinateSystem(self.origin).update(self)

    def get_dependencies(self) -> tuple[AbstractFeature | AbstractGeometry]:
        if self.context is None:
            return tuple()
        return (self.context,)

    def get_axis_line_x(self) -> Line:
        """Returns the infinite line coincident with the x-axis."""
        return self._parts.x

    def get_axis_line_y(self) -> Line:
        """Returns the infinite line coincident with the y-axis."""
        return self._parts.y

    def get_axis_line_z(self) -> Line:
        """Returns the infinite line coincident with the z-axis."""
        return self._parts.z

    def get_axis_vectors(self) -> tuple[tuple[Real]]:
        """Returns a tuple of the coordinate system's axis direction tuples."""
        return tuple(axis.direction for axis in self._parts.get_axes())

    def get_quaternion(self) -> np.quaternion:
        """Returns a quaternion that can be used to rotate other vectors from 
        the canonical cartesian coordinate system (1, 0, 0), (0, 1, 0),
        (0, 0, 1) to this coordinate system.
        """
        canon_vectors = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        system_vectors = [self.x_vector, self.y_vector, self.z_vector]
        canon = SystemAxes3D(*[np.array(axis) for axis in canon_vectors])
        sys = SystemAxes3D(*[np.array(axis) for axis in system_vectors])
        if all(np.isclose(np.dot(c, s), 1) for c, s in zip(canon, sys)):
            # Check if the axes are all close to the canon axis directions and
            # return a quaternion with no rotation if so.
            return np.quaternion(1, 0, 0, 0)
        parallel_to_canons = [np.isclose(abs(np.dot(c, s)), 1)
                              for c, s in zip(canon, sys)]
        if all(parallel_to_canons):
            # Can only happen if all axes are counter-parallel, since they've all
            # been checked for whether they are the exact same. That would mean
            # that this is an opposite-handed coordinate system and wouldn't be
            # possible to rotate to.
            msg =("Cannot create a quaternion to rotate to this coordinate"
                  "system from a canon right-handed coordinate_system")
            raise ValueError(msg)
        canon_axis = canon[parallel_to_canons.index(False)]
        current_axis = sys[parallel_to_canons.index(False)]
        euler_axis = np.cross(canon_axis, current_axis)
        euler_axis = euler_axis / np.linalg.norm(euler_axis)
        normed_dot = (
            np.dot(canon_axis, current_axis)
            / (np.linalg.norm(canon_axis) * np.linalg.norm(current_axis))
        )
        cos_half_theta = np.sqrt((1 + normed_dot)/2)
        sin_half_theta = np.sqrt((1 - normed_dot)/2)
        quat_vector = euler_axis * sin_half_theta
        return np.quaternion(cos_half_theta, *quat_vector)

    def get_xy_plane(self) -> Plane:
        """Returns the XY plane of the CoordinateSystem."""
        return self._parts.xy

    def get_xz_plane(self) -> Plane:
        """Returns the XZ plane of the CoordinateSystem."""
        return self._parts.xz

    def get_yz_plane(self) -> Plane:
        """Returns the YZ plane of the CoordinateSystem."""
        return self._parts.yz

    def update(self, other: CoordinateSystem) -> Self:
        """Updates the origin, axes, and planes of the CoordinateSystem to match 
        another CoordinateSystem.
        
        :param other: The CoordinateSystem to update to.
        :returns: The updated CoordinateSystem.
        """
        for field in fields(self._parts):
            getattr(self.parts, field.name).update(
                getattr(other.parts, field.name)
            )
        return Self

    def rotate(self, rotation: np.ndarray | quaternion.quaternion) -> Self:
        """Rotates the system with a rotation matrix or quaternion."""
        self.parts.rotate(rotation)
        return self

    def move_to_point(self, location: Point) -> Self:
        """Moves the system to a new location with no rotation."""
        self.parts.move_to_point(location)
        return self

    # Python Dunders
    def __copy__(self) -> CoordinateSystem:
        """Returns a copy of the CoordinateSystem that has the same origin, 
        axes, planes and context, but not the same uid. Can be used with the 
        python copy module.
        """
        return self.copy()

    def __repr__(self) -> str:
        pt_strs, axis_strs = [], []
        for component in self.origin:
            if isclose0(component):
                pt_strs.append("0")
            else:
                pt_strs.append(f"{component:g}")
        axis_no = 0
        for axis in self.get_axis_vectors():
            component_strs = []
            for component in axis:
                if isclose0(component):
                    component_strs.append("0")
                else:
                    component_strs.append(f"{component:g}")
            component_str = ",".join(component_strs)
            axis_name = chr(ord("x") + axis_no)
            axis_no += 1
            axis_strs.append(axis_name + "(" + component_str + ")")
        axis_str = "".join(axis_strs)
        point_str = ",".join(pt_strs)
        return f"<pancadCoordSys'{self.name}'({point_str}){axis_str}>"

    def __len__(self) -> int:
        """Returns the number of dimensions of the coordinate system by 
        returning the number of dimensions of the origin point.
        """
        return len(self.origin)

    def __str__(self) -> str:
        indentation = "    "
        pt_strs, axis_strs = [], []
        for component in self.origin:
            if isclose0(component):
                pt_strs.append("0")
            else:
                pt_strs.append(f"{component:g}")
        axis_no = 0
        for axis in self.get_axis_vectors():
            component_strs = []
            for component in axis:
                if isclose0(component):
                    component_strs.append("0")
                else:
                    component_strs.append(f"{component:g}")
            component_str = ", ".join(component_strs)
            axis_name = chr(ord("x") + axis_no)
            axis_no += 1
            axis_strs.append(f"{axis_name.upper()}-Axis ({component_str})")
        point_str = ", ".join(pt_strs)
        summary = [f"CoordinateSystem '{self.name}'",
                   "Origin and Axes:",
                   indent(f"Origin ({point_str})", indentation),
                   indent("\n".join(axis_strs), indentation),]
        return "\n".join(summary)


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
                ConstraintReference.CORE: self,
                ConstraintReference.ORIGIN: self._coordinate_system.origin,
                ConstraintReference.X: self._coordinate_system.get_axis_line_x(),
                ConstraintReference.Y: self._coordinate_system.get_axis_line_y(),
                ConstraintReference.Z: self._coordinate_system.get_axis_line_z(),
                ConstraintReference.FRONT: self._coordinate_system.get_xy_plane(),
                ConstraintReference.RIGHT: self._coordinate_system.get_xz_plane(),
                ConstraintReference.TOP: self._coordinate_system.get_yz_plane(),
                ConstraintReference.CS: self._coordinate_system,
            }
        )

    @classmethod
    def from_yaw_pitch_roll(cls, position: Point | VectorLike,
                            yaw: Real=0, pitch: Real=0, roll: Real=0,
                            **kwargs) -> None:
        """Initializes a Pose from yaw, pitch, and roll angles in radians."""
        coordinate_system = CoordinateSystem(position, yaw, pitch, roll)
        return cls(coordinate_system, **kwargs)

    @property
    def coordinate_system(self) -> CoordinateSystem:
        """Internal coordinate_system representing the the Pose."""
        return self.get_reference(ConstraintReference.CS)

    @property
    def origin(self) -> Point:
        """The origin point of the Pose's internal coordinate_system."""
        return self.get_reference(ConstraintReference.ORIGIN)

    @property
    def front(self) -> Plane:
        """Front plane of the Pose."""
        return self.get_reference(ConstraintReference.FRONT)

    @property
    def right(self) -> Plane:
        """Right plane of the Pose."""
        return self.get_reference(ConstraintReference.RIGHT)

    @property
    def top(self) -> Plane:
        """Top plane of the Pose."""
        return self.get_reference(ConstraintReference.TOP)

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
