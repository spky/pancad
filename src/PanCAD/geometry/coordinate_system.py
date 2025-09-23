"""A module providing a class to represent coordinate systems in CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from functools import partial, singledispatchmethod
import math
from numbers import Real
from textwrap import indent
from typing import overload, Self, NoReturn

import numpy as np
import quaternion

from PanCAD.geometry import (AbstractFeature,
                             AbstractGeometry,
                             Point,
                             Line,
                             Plane)
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils import comparison
from PanCAD.utils.trigonometry import (yaw_pitch_roll,
                                       rotation_2,
                                       to_1D_tuple,
                                       cartesian_to_spherical)
from PanCAD.utils.pancad_types import VectorLike

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

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
    :param right_handed: Whether the coordinate system is right-handed. 
        Right-handed if True, left-handed if False. Defaults to False.
    :param uid: The unique ID of the coordinate system.
    :param context: The feature defining the context that the CoordinateSystem 
        exists inside of.
    :param name: The name of the feature displayed to the users in CAD.
    """
    REFERENCES = (ConstraintReference.ORIGIN,
                  ConstraintReference.X,
                  ConstraintReference.Y,
                  ConstraintReference.Z,
                  ConstraintReference.XY,
                  ConstraintReference.XZ,
                  ConstraintReference.YZ)
    """All relevant ConstraintReferences for CoordinateSystems. 2D 
    CoordinateSystems only have ORIGIN, X, and Y.
    """
    
    @overload
    def __init__(self,
                 origin: Point | VectorLike,
                 alpha: Real=0,
                 *,
                 uid: str=None,
                 context: AbstractFeature=None,
                 name: str=None) -> None: ...
    
    @overload
    def __init__(self,
                 origin: Point | VectorLike,
                 alpha: Real=0,
                 beta: Real=0,
                 gamma: Real=0,
                 *,
                 right_handed: bool=True,
                 uid: str=None,
                 context: AbstractFeature=None,
                 name: str=None) -> None: ...
    
    def __init__(self, origin=None, alpha=0, beta=0, gamma=0,
                 *, right_handed=True, uid=None, context=None, name=None):
        if origin is None:
            origin = (0, 0, 0)
        if isinstance(origin, VectorLike):
            origin = Point(origin)
        
        if not right_handed:
            raise NotImplementedError("Left-Handed CoordinateSystems not"
                                      " yet implemented.")
        
        # Initialize reference geometry and then translate/rotate into place
        if len(origin) == 2:
            if beta != 0 or gamma != 0:
                raise ValueError("beta and/or gamma angles cannot be set for a"
                                 " 2D coordinate system")
            self._init_2d(origin, alpha)
        else:
            self._init_3d(origin, alpha, beta, gamma)
        
        self.name = name
        self.context = context
        self.uid = uid
    
    # Class Methods #
    @classmethod
    def from_quaternion(cls,
                        origin: Point | VectorLike=None,
                        quat: np.quaternion=None,
                        *,
                        right_handed: bool=True,
                        uid: str=None,
                        name: str=None,
                        context: AbstractFeature=None) -> CoordinateSystem:
        """Returns a 3D coordinate system defined with a quaternion.
        
        :param origin: A 3D center Point of the coordinate system. Defaults to 
            (0, 0, 0).
        :param quat: A numpy quaternion used to rotate the coordinate system 
            from the canonical cartesian coordinate orientation to its desired 
            location.
        :param right-handed: Whether the coordinate system is right-handed. 
            Right-handed if true, left-handed if false.
        :param uid: The unique ID of the coordinate system.
        :returns: A 3D CoordinateSystem rotated according to the quaternion.
        """
        if quat is None:
            # Initialize a quaternion that won't rotate the coordinate system
            quat = np.quaternion(0, 0, 0, 1)
        
        if len(origin) != 3:
            raise ValueError("2D Coordinate Systems cannot be initialized"
                             " with quaternions")
        else:
            # Initialize an unrotated coordinate system
            coordinate_system = cls(origin,
                                    0, 0, 0,
                                    right_handed=right_handed,
                                    uid=uid,
                                    context=context,
                                    name=name)
        coordinate_system._rotate_axes(quat)
        return coordinate_system
    
    # Getters #
    @property
    def context(self) -> AbstractFeature | None:
        return self._context
    
    @property
    def origin(self) -> Point:
        """The origin point of the coordinate system.
        
        :getter: Returns the origin point of the coordinate system.
        :setter: Updates the origin point's location from another Point or 
            position vector.
        """
        return self._origin
    
    @property
    def x_vector(self) -> tuple[Real]:
        """The direction vector of the coordinate system's x-axis. Read-only."""
        return self._x_vector
    
    @property
    def y_vector(self) -> tuple[Real]:
        """The direction vector of the coordinate system's y-axis. Read-only."""
        return self._y_vector
    
    @property
    def z_vector(self) -> tuple[Real]:
        """The direction vector of the coordinate system's z-axis. Read-only."""
        return self._z_vector
    
    # Setters #
    @context.setter
    def context(self, context_feature: AbstractFeature | None) -> None:
        self._context = context_feature
    
    @origin.setter
    def origin(self, point: Point | VectorLike):
        if isinstance(point, Point):
            self._origin.update(point)
        else:
            self._origin.cartesian = point
    
    # Public Methods #
    def copy(self) -> CoordinateSystem:
        """Returns a copy of the CoordinateSystem.
        
        :returns: the same origin, axes, planes and context, but not the same 
            uid.
        """
        return self.__copy__()
    
    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns all ConstraintReferences applicable to CoordinateSystems. See 
        :attr:`CoordinateSystem.REFERENCES`.
        """
        if len(self) == 2:
            return self.REFERENCES[0:3]
        else:
            return self.REFERENCES
    
    def get_dependencies(self) -> tuple[AbstractFeature | AbstractGeometry]:
        if self.context is None:
            return tuple()
        else:
            return (self.context,)
    
    def get_axis_line_x(self) -> Line:
        """Returns the infinite line coincident with the x-axis."""
        return self._x_axis_line
    
    def get_axis_line_y(self) -> Line:
        """Returns the infinite line coincident with the y-axis."""
        return self._y_axis_line
    
    def get_axis_line_z(self) -> Line:
        """Returns the infinite line coincident with the z-axis."""
        return self._z_axis_line
    
    def get_axis_vectors(self) -> tuple[tuple[Real]]:
        """Returns a tuple of the coordinate system's axis direction tuples."""
        if len(self.origin) == 2:
            return (self.x_vector, self.y_vector)
        else:
            return (self.x_vector, self.y_vector, self.z_vector)
    
    def get_quaternion(self) -> np.quaternion:
        """Returns a quaternion that can be used to rotate other vectors from 
        the canonical cartesian coordinate system (1, 0, 0), (0, 1, 0),
        (0, 0, 1) to this coordinate system.
        """
        canon_axis = (0, 0, 1)
        if (np.allclose(canon_axis, self._z_vector)
                or np.allclose(canon_axis, -self._z_vector)):
            # Protect against the situation where the coordinate system is 
            # rotated around the z axis by switching to x axis
            canon_axis = (1, 0, 0)
            current_axis = self._x_vector
        else:
            current_axis = self._z_vector
        
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
    
    def get_reference(self,
                      reference: ConstraintReference) -> Point | Line | Plane:
        """Returns reference geometry for use in external modules like 
        constraints.
        
        :param reference: A ConstraintReference enumeration value applicable to 
            CoordinateSystems. See :attr:`CoordinateSystem.REFERENCES`.
        :returns: The geometry corresponding to the reference.
        """
        if len(self.origin) == 2:
            match reference:
                case ConstraintReference.ORIGIN:
                    return self.origin
                case ConstraintReference.X:
                    return self.get_axis_line_x()
                case ConstraintReference.Y:
                    return self.get_axis_line_y()
                case _:
                    raise ValueError(f"2D {self.__class__}s do not have any"
                                     f" {reference.name} reference geometry")
        else:
            match reference:
                case ConstraintReference.ORIGIN:
                    return self.origin
                case ConstraintReference.X:
                    return self.get_axis_line_x()
                case ConstraintReference.Y:
                    return self.get_axis_line_y()
                case ConstraintReference.Z:
                    return self.get_axis_line_z()
                case ConstraintReference.XY:
                    return self.get_xy_plane()
                case ConstraintReference.XZ:
                    return self.get_xz_plane()
                case ConstraintReference.YZ:
                    return self.get_yz_plane()
                case _:
                    raise ValueError(f"3D {self.__class__}s do not have any"
                                     f" {reference.name} reference geometry")
    
    def get_xy_plane(self) -> Plane:
        """Returns the XY plane of the CoordinateSystem."""
        return self._xy_plane
    
    def get_xz_plane(self) -> Plane:
        """Returns the XZ plane of the CoordinateSystem."""
        return self._xz_plane
    
    def get_yz_plane(self) -> Plane:
        """Returns the YZ plane of the CoordinateSystem."""
        return self._yz_plane
    
    def update(self, other: CoordinateSystem) -> Self:
        """Updates the origin, axes, and planes of the CoordinateSystem to match 
        another CoordinateSystem.
        
        :param other: The CoordinateSystem to update to.
        :returns: The updated CoordinateSystem.
        """
        self.origin = other.origin
        self._set_axes(other.get_axis_vectors())
        return Self
    
    # Private Methods #
    def _init_2d(self, origin: Point, alpha: Real) -> None:
        """Used to initialize a 2D coordinate system."""
        self._origin = Point(0, 0)
        self.origin = origin
        
        self._x_axis_line = Line(self.origin, (1, 0))
        self._y_axis_line = Line(self.origin, (0, 1))
        
        initial_axis_matrix = (self._x_axis_line.direction,
                               self._y_axis_line.direction)
        self._set_axes(initial_axis_matrix)
        rotation_matrix = rotation_2(alpha)
        self._rotate_axes(rotation_matrix)
    
    def _init_3d(self,
                 origin: Point,
                 alpha: Real, beta: Real, gamma: Real) -> None:
        """Used to initialize a 3D coordinate system."""
        self._origin = Point(0, 0, 0)
        self.origin = origin
        self._x_axis_line = Line(self.origin, (1, 0, 0))
        self._y_axis_line = Line(self.origin, (0, 1, 0))
        self._z_axis_line = Line(self.origin, (0, 0, 1))
        self._xy_plane = Plane(self.origin, self._z_axis_line.direction)
        self._xz_plane = Plane(self.origin, self._y_axis_line.direction)
        self._yz_plane = Plane(self.origin, self._x_axis_line.direction)
        
        initial_axis_matrix = (self._x_axis_line.direction,
                               self._y_axis_line.direction,
                               self._z_axis_line.direction)
        self._set_axes(initial_axis_matrix)
        rotation_matrix = yaw_pitch_roll(alpha, beta, gamma)
        self._rotate_axes(rotation_matrix)
    
    @singledispatchmethod
    def _rotate_axes(self, rotation) -> NoReturn:
        """Applies the rotation matrix to all the coordinate system's axes."""
        raise TypeError(f"Invalid rotation type {rotation.__class__}")
    
    @_rotate_axes.register
    def _with_quaternion(self, quat: quaternion.quaternion) -> Self:
        axis_array = np.array(self.get_axis_vectors())
        rotated = quaternion.rotate_vectors(quat, axis_array)
        self._set_axes(rotated)
        return self
    
    @_rotate_axes.register
    def _with_matrix(self, rotation_matrix: np.ndarray) -> Self:
        new_axis_matrix = [rotation_matrix @ axis
                           for axis in self.get_axis_vectors()]
        self._set_axes(new_axis_matrix)
        return self
    
    def _set_axes(self, axis_matrix: list | tuple | np.ndarray) -> None:
        """Used to set the axes all at once while ensuring they are tuples. 
        Assumes that the axes are still unit vectors, perpendicular, and 
        linearly independent (that's why this is private).
        """
        if len(self.origin) == len(axis_matrix) == 2:
            x, y = axis_matrix
            self._x_vector = to_1D_tuple(x)
            self._y_vector = to_1D_tuple(y)
        elif len(self.origin) == len(axis_matrix) == 3:
            x, y, z = axis_matrix
            self._x_vector = to_1D_tuple(x)
            self._y_vector = to_1D_tuple(y)
            self._z_vector = to_1D_tuple(z)
        else:
            raise ValueError("axis_matrix must be for the same number of"
                             " dimensions as the origin point")
        self._update_axis_lines_and_planes()
    
    def _update_axis_lines_and_planes(self):
        self._x_axis_line.update(Line(self.origin, self._x_vector))
        self._y_axis_line.update(Line(self.origin, self._y_vector))
        if len(self.origin) == 3:
            self._z_axis_line.update(Line(self.origin, self._z_vector))
            
            self._xy_plane.update(Plane(self.origin, self._z_vector))
            self._xz_plane.update(Plane(self.origin, self._y_vector))
            self._yz_plane.update(Plane(self.origin, self._x_vector))
    
    # Python Dunders #
    def __copy__(self) -> CoordinateSystem:
        """Returns a copy of the CoordinateSystem that has the same origin, 
        axes, planes and context, but not the same uid. Can be used with the 
        python copy module.
        """
        if len(self) == 3:
            return CoordinateSystem.from_quaternion(self.origin,
                                                    self.get_quaternion(),
                                                    context=self.context)
        else:
            new_system = CoordinateSystem(self.origin, context=self.context)
            new_initial_axis_matrix = (self._x_vector, self._y_vector)
            new_system._set_axes(new_initial_axis_matrix)
            return new_system
    
    def __repr__(self) -> str:
        pt_strs, axis_strs = [], []
        for i in range(0, len(self.origin)):
            if isclose0(self.origin[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self.origin[i]))
        axis_no = 0
        for axis in self.get_axis_vectors():
            
            component_strs = []
            for component in axis:
                if isclose0(component):
                    component_strs.append("0")
                else:
                    component_strs.append("{:g}".format(component))
            component_str = ",".join(component_strs)
            axis_name = chr(ord("x") + axis_no)
            axis_no += 1
            axis_strs.append(axis_name + "(" + component_str + ")")
        axis_str = "".join(axis_strs)
        point_str = ",".join(pt_strs)
        return f"<PanCADCoordSys'{self.name}'({point_str}){axis_str}>"
    
    def __len__(self) -> int:
        """Returns the number of dimensions of the coordinate system by 
        returning the number of dimensions of the origin point.
        """
        return len(self.origin)
    
    def __str__(self) -> str:
        INDENTATION = "    "
        pt_strs, axis_strs = [], []
        for i in range(0, len(self.origin)):
            if isclose0(self.origin[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self.origin[i]))
        axis_no = 0
        for axis in self.get_axis_vectors():
            
            component_strs = []
            for component in axis:
                if isclose0(component):
                    component_strs.append("0")
                else:
                    component_strs.append("{:g}".format(component))
            component_str = ", ".join(component_strs)
            axis_name = chr(ord("x") + axis_no)
            axis_no += 1
            axis_strs.append(f"{axis_name.upper()}-Axis ({component_str})")
        axis_str = " ".join(axis_strs)
        point_str = ", ".join(pt_strs)
        
        summary = [f"CoordinateSystem '{self.name}'",
                   "Origin and Axes:",
                   indent(f"Origin ({point_str})", INDENTATION),
                   indent("\n".join(axis_strs), INDENTATION),]
        return "\n".join(summary)