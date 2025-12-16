"""A module to provide trigonometric functions that translate geometry 
between formats.
"""

from functools import partial
import math
from math import degrees
from numbers import Real
from typing import Any

import numpy as np
from numpy.linalg import norm

from pancad.constants import AngleConvention
from pancad.utils.comparison import isclose
from pancad.utils.pancad_types import VectorLike

def angle_mod(angle: Real) -> float:
    """Returns the angle bounded from -2π to +2π since python's modulo 
    operator by default always returns the divisor's sign, which is 
    different than other programming languages like C and C++.
    
    :param angle: The angle in radians.
    :returns: The equivalent angle bounded between -2pi and +2pi.
    """
    if angle >= 0:
        return angle % (2*np.pi)
    return angle % (-2*np.pi)

def get_unit_vector(vector: VectorLike) -> np.ndarray:
    """Returns the unit vector of the given vector. If the vector is a zero 
    vector, returns the zero vector.
    """
    if isinstance(vector, np.ndarray):
        shape = vector.shape
    else:
        shape = (len(vector),)
    vector = to_1d_np(vector)
    length = np.linalg.norm(vector)
    if is_geometry_vector(vector):
        if length == 0:
            unit_vector = vector
        else:
            unit_vector = vector / length
    else:
        raise ValueError("Unit vectors will only be found for 2 and 3 element"
                         f" vectors. Vector '{vector}' has shape {shape}")
    return unit_vector.reshape(shape)

def get_vector_angle(vector1: VectorLike,
                     vector2: VectorLike,
                     *,
                     opposite: bool=False,
                     convention: AngleConvention=AngleConvention.PLUS_PI
                     ) -> float:
    """Returns the angle between vector1 and vector2 based on the given angle 
    convention.
    
    :param vector1: A vector with cartesian components.
    :param vector2: Another vector with cartesian components.
    :param opposite: Sets whether to return the supplement/explement of the angle 
        between vector1 and vector2.
    :param convention: The angle convention the output will follow. See 
        :class:`~pancad.constants.AngleConvention` for 
        available options.
    :returns: The angle between vector1 and vector2.
    """
    if (dimension := len(vector1)) != len(vector2):
        raise ValueError("Vectors must be the same length")
    if dimension not in [2, 3]:
        raise ValueError("Vectors must be 2D or 3D")
    if dimension == 2:
        match convention:
            case AngleConvention.PLUS_PI | AngleConvention.PLUS_180:
                angle = _get_angle_between_2d_vectors_pi(vector1, vector2,
                                                         opposite, False)
            case AngleConvention.SIGN_PI | AngleConvention.SIGN_180:
                angle = _get_angle_between_2d_vectors_pi(vector1, vector2,
                                                         opposite, True)
            case AngleConvention.PLUS_TAU | AngleConvention.PLUS_360:
                angle = _get_angle_between_2d_vectors_2pi(vector1, vector2,
                                                          opposite)
            case _:
                raise ValueError(f"Convention {convention} not recognized")
    else:
        angle = _get_angle_between_3d_vectors_pi(vector1, vector2, opposite)
    if convention in (AngleConvention.PLUS_180,
                      AngleConvention.PLUS_360,
                      AngleConvention.SIGN_180):
        return degrees(angle)
    return angle

def is_clockwise(vector1: VectorLike, vector2: VectorLike) -> bool:
    """Returns whether 2D vector2 is clockwise of 2D vector1.
    
    :param vector1: A 2D vector with cartesian components.
    :param vector2: Another 2D vector with cartesian components.
    :returns: 'True' if vector2 is clockwise of vector1, otherwise 'False'.
    """
    if len(vector1) == len(vector2) == 2:
        x1, y1 = vector1
        vector1_90_ccw = (-y1, x1)
        return np.dot(vector1_90_ccw, vector2) < 0
    raise ValueError("Both vectors must be 2 long")

def is_geometry_vector(vector: np.ndarray) -> bool:
    """Returns whether the NumPy vector is a valid 2D or 3D vector
    
    :param vector: A NumPy vector to be checked
    :returns: True if the vector is a valid 2D or 3D vector
    """
    return vector.shape in [(2,), (3,), (2,1), (3,1)]

def is_iterable(value: Any) -> bool:
    """Returns whether a value is iterable."""
    return hasattr(value, "__iter__")

def multi_rotation(permutation: str, *angles: Real) -> np.ndarray:
    """Returns a rotation matrix of multiple rotations around the x, y, and z 
    axes.
    
    :param permutation: An arbitrary length string of letters x, y, and z in the 
        order the rotations should be performed. Example: 'xyzzyx'.
    :param angles: The rotation angle corresponding to the rotation at the same 
        index in permutation. The number of angles must be the same as the 
        number of permutations.
    :returns: A rotation matrix to perform the series of rotations.
    """
    if len(angles) != len(permutation):
        raise ValueError("Length of permutation must be the same as the number"
                         f" of angles ({len(permutation)}!={len(angles)})")
    rotation_funcs = {
        "x": rotation_x,
        "y": rotation_y,
        "z": rotation_z,
    }
    permutation = permutation.casefold()
    matrix = np.identity(3)
    for angle, axis in zip(angles, list(permutation)):
        matrix = matrix @ rotation_funcs[axis](angle)
    return matrix

def rotation(angle: Real, around: str | tuple[Real, Real, Real]) -> np.ndarray:
    """Returns a rotation matrix that rotates around the given axis/vector by the 
    angle. Assumes a right-handed coordinate system.
    
    :param angle: The counter-clockwise rotation angle in radians.
    :param around: The axis to rotate around. Options x, y, z, 2, and a 
        tuple. 2 produces a 2D rotation matrix. If given tuple of 3 Reals, the 
        rotation matrix will be for rotating around that vector.
    :returns: A numpy rotation matrix.
    """
    cost = math.cos(angle)
    sint = math.sin(angle)
    match around:
        case "x" | (1, 0, 0):
            matrix = [
                [1, 0, 0],
                [0, cost, -sint],
                [0, sint, cost],
            ]
        case "y" | (0, 1, 0):
            matrix = [
                [cost, 0, sint],
                [0, 1, 0],
                [-sint, 0, cost],
            ]
        case "z" | (0, 0, 1):
            matrix = [
                [cost, -sint, 0],
                [sint, cost, 0],
                [0, 0, 1],
            ]
        case "2":
            matrix = [
                [cost, -sint],
                [sint, cost],
            ]
        case _:
            if len(around) != 3:
                raise ValueError("Vector around must be 3 elements long,"
                                 f" given {around}")
            around = get_unit_vector(around)
            x, y, z = around
            mcost = 1 - cost
            matrix = [
                [x**2 * mcost + cost, x*y*mcost - z*sint, x*z*mcost + y*sint],
                [x*y*mcost + z*sint, y**2 * mcost + cost, y*z*mcost - x*sint],
                [x*z*mcost - y*sint, y*z*mcost + x*sint, z**2 * mcost + cost],
            ]
    return np.array(matrix)

# Special Case Rotation Matrices
rotation_x = partial(rotation, around="x")
"""Returns a rotation matrix for rotation about the x axis. Requires only 1 
angle argument.
"""
rotation_y = partial(rotation, around="y")
"""Returns a rotation matrix for rotation about the y axis. Requires only 1 
angle.
"""
rotation_z = partial(rotation, around="z")
"""Returns a rotation matrix for rotation about the z axis. Requires only 1 
angle argument.
"""
rotation_2 = partial(rotation, around="2")
"""Returns a rotation matrix for rotation in 2D. Requires only 1 angle 
argument.
"""
# Special Case Multi-Rotations
yaw_pitch_roll = partial(multi_rotation, "zyx")
"""Returns a rotation matrix for rotation about the z axis, then the y axis, and 
finally the x axis. Requires 3 input angles.
"""

def positive_angle(angle: Real) -> float:
    """Returns the positive representation of an angle in radians, bounded from 
    0 to 2π.
    """
    if angle >= 0:
        return angle_mod(angle)
    return angle_mod(angle) + 2*np.pi

def to_1d_tuple(value: VectorLike) -> tuple:
    """Returns a 1D tuple from a given value."""
    if isinstance(value, tuple) and not all(map(is_iterable, value)):
        return value
    if isinstance(value, list) and not all(map(is_iterable, value)):
        return tuple(value)
    if isinstance(value, np.ndarray) and is_geometry_vector(value):
        return tuple(float(coordinate.squeeze()) for coordinate in value)
    raise ValueError(f"Cannot convert {value} of class {value.__class__}")

def to_1d_np(value: VectorLike) -> np.ndarray:
    """Returns a 1D numpy array from a given value."""
    if isinstance(value, tuple) and not all(map(is_iterable, value)):
        return np.array(value)
    if isinstance(value, list) and not all(map(is_iterable, value)):
        return np.array(value)
    if isinstance(value, np.ndarray) and is_geometry_vector(value):
        return value.squeeze()
    raise ValueError(f"Cannot convert {value} of class {value.__class__} to"
                     "a 1D numpy.ndarray")

def r_of_cartesian(cartesian: VectorLike) -> float:
    """Returns the r component of a polar or spherical vector from a 
    given cartesian vector.
    
    :param cartesian: A vector with cartesian components (x, y) or (x, y, z).
    :returns: The radius component of the equivalent polar/spherical vector.
    """
    if len(cartesian) in (2, 3):
        return math.hypot(*cartesian)
    raise ValueError("Can only return r if the cartesian vector is 2 or 3")

def phi_of_cartesian(cartesian: VectorLike) -> float:
    """Returns the polar/spherical azimuth component of the equivalent 
    polar/spherical vector in radians. Bounded from -π to π.
    
    :param cartesian: A vector with cartesian components (x, y) or (x, y, z).
    :returns: The azimuth component of the equivalent polar/spherical vector.
    """
    if cartesian[0] == 0 and cartesian[1] == 0:
        return math.nan
    return math.atan2(cartesian[1], cartesian[0])

def theta_of_cartesian(cartesian: VectorLike) -> float:
    """Returns the spherical inclination component of the equivalent spherical 
    vector in radians.
    
    :param cartesian: A 3D vector with cartesian components (x, y, z).
    :returns: The inclination coordinate of the equivalent polar/spherical 
        coordinate.
    """
    x, y, z = cartesian
    if z == 0 and math.hypot(x, y) != 0:
        return math.pi/2
    if x == y == z == 0:
        return math.nan
    if z > 0:
        return math.atan(math.hypot(x, y) / z)
    if z < 0:
        return math.pi + math.atan(math.hypot(x, y) / z)
    raise ValueError(f"Unhandled exception, cartesian: {cartesian}")

def cartesian_to_polar(cartesian: VectorLike) -> tuple[float, float]:
    """Returns the polar version of the given cartesian vector.
    
    :param cartesian: A 2D vector with cartesian components x and y.
    :returns: An equivalent 2D vector with polar components r (radial distance) 
              and phi (azimuth) in radians.
    """
    if len(cartesian) == 2:
        return (r_of_cartesian(cartesian), phi_of_cartesian(cartesian))
    if len(cartesian) == 3:
        raise ValueError("2D, use cartesian_to_spherical for 3D points")
    raise ValueError("Invalid cartesian vector, must be 2 long to return")

def polar_to_cartesian(polar: VectorLike) -> tuple[float, float]:
    """Returns the cartesian version of the given polar vector.
    
    :param polar: A 2D vector with polar components r (radial distance) and phi 
        (azimuth angle) in radians.
    :returns: An equivalent 2D vector with cartesian components x and y.
    """
    if len(polar) != 2:
        raise ValueError("Vector must be 2D to return a polar coordinate")
    r, phi = polar
    if r == 0 and math.isnan(phi):
        return (0, 0)
    if r < 0:
        raise ValueError(f"r cannot be less than zero: {r}")
    if math.isnan(phi):
        raise ValueError("phi cannot be NaN if r is non-zero")
    return (r * math.cos(phi), r * math.sin(phi))

def spherical_to_cartesian(spherical: VectorLike) -> tuple[float, float, float]:
    """Returns the cartesian version of the given spherical vector.
    
    :param spherical: A 3D vector with spherical components r (radial distance), 
        phi (azimuth in radians), and theta (inclination in radians).
    :returns: An equivalent 3D vector with cartesian components x, y, and z.
    """
    if len(spherical) == 3:
        r, phi, theta = spherical
        if r == 0 and math.isnan(phi) and math.isnan(theta):
            return (0, 0, 0)
        if r > 0 and not math.isnan(phi) and (0 <= theta <= math.pi):
            return (
                r * math.sin(theta) * math.cos(phi),
                r * math.sin(theta) * math.sin(phi),
                r * math.cos(theta)
            )
        if r > 0 and math.isnan(phi) and theta == 0:
            return (0, 0, r)
        if r > 0 and math.isnan(phi) and theta == math.pi:
            return (0, 0, -r)
        if r < 0:
            raise ValueError(f"r cannot be less than zero: {r}")
        if not math.isnan(theta) and (not 0 <= theta <= math.pi):
            raise ValueError(f"theta must be between 0 and pi, value: {theta}")
        if math.isnan(phi) and math.isnan(theta):
            raise ValueError(f"r value {r} cannot be non-zero if phi and "
                             + "theta are NaN.")
        if math.isnan(theta):
            raise ValueError("Theta cannot be NaN if r is non-zero")
        if math.isnan(phi) and (theta != 0 or theta != math.pi):
            raise ValueError("If phi is NaN, theta must be pi/2")
        raise ValueError("Unhandled spherical case!")
    if len(spherical) == 2:
        raise ValueError("3D, use polar_to_cartesian for 2D points")
    raise ValueError("Vector must be 3 long to return a spherical vector")

def cartesian_to_spherical(cartesian: VectorLike) -> tuple[float, float, float]:
    """Returns the spherical version of the given cartesian vector.
    
    :param cartesian: A 3D vector with cartesian components x, y, z.
    :returns: A 3D vector with spherical components r (radial distance), phi 
        (azimuth in radians), and theta (inclination in radians).
    """
    if len(cartesian) == 3:
        return (r_of_cartesian(cartesian),
                phi_of_cartesian(cartesian),
                theta_of_cartesian(cartesian))
    if len(cartesian) == 2:
        raise ValueError("2D, use cartesian_to_polar for 2D points")
    raise ValueError("Invalid cartesian vector, must be 3 long")

def _get_angle_between_2d_vectors_2pi(vector1: VectorLike,
                                      vector2: VectorLike,
                                      explementary: bool=False) -> float:
    """Returns the counter-clockwise angle between vector1 and vector2 in radians 
    bounded between 0 and 2π. Returns the clockwise angle if explementary is 
    set to True.
    
    :param vector1: A 2D vector with cartesian components.
    :param vector2: Another 2D vector with cartesian components.
    :param explementary: Sets whether to return the explement of the angle 
        between vector1 and vector2.
    :returns: The angle between vector1 and vector2.
    """
    unit_dot = np.dot(vector1, vector2) / (norm(vector1) * norm(vector2))
    if isclose(abs(unit_dot), 1):
        angle = math.acos(round(unit_dot))
    else:
        angle = math.acos(unit_dot)
    if is_clockwise(vector1, vector2):
        angle = math.tau - angle
    if explementary:
        return math.tau - angle
    return angle

def _get_angle_between_2d_vectors_pi(vector1: VectorLike,
                                     vector2: VectorLike,
                                     supplementary: bool=False,
                                     signed: bool=False) -> float:
    """Returns the angle between vector1 and vector2 in radians between 0 and π.
    
    :param vector1: A 2D vector with cartesian components.
    :param vector2: Another 2D vector with cartesian components.
    :param supplementary: Sets whether to return the supplement of the angle 
        between vector1 and vector2.
    :param signed: Sets whether to return a negative angle if the angle is 
        oriented clockwise.
    :returns: The angle between vector1 and vector2.
    """
    unit_dot = np.dot(vector1, vector2) / (norm(vector1) * norm(vector2))
    if isclose(abs(unit_dot), 1):
        angle = math.acos(round(unit_dot))
    else:
        angle = math.acos(unit_dot)
    if supplementary:
        angle = math.pi - angle
    if signed and (is_clockwise(vector1, vector2) ^ supplementary):
        return -angle
    return angle

def _get_angle_between_3d_vectors_pi(vector1: VectorLike,
                                     vector2: VectorLike,
                                     supplementary: bool=False) -> float:
    """Returns the angle between vector1 and vector2 in radians between 0 and π.
    
    :param vector1: A 3D vector with cartesian components.
    :param vector2: Another 3D vector with cartesian components.
    :param supplementary: Sets whether to return the supplement of the angle 
        between vector1 and vector2.
    :returns: The angle between vector1 and vector2.
    """
    unit_dot = np.dot(vector1, vector2) / (norm(vector1) * norm(vector2))
    if isclose(abs(unit_dot), 1):
        angle = math.acos(round(unit_dot))
    else:
        angle = math.acos(unit_dot)
    if supplementary:
        return math.pi - angle
    return angle
