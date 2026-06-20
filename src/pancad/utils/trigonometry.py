"""A module to provide trigonometric functions that translate geometry
between formats.
"""
from __future__ import annotations

from functools import partial
import math
from math import degrees
from typing import TYPE_CHECKING, overload
from collections.abc import Sequence

import numpy as np
from numpy.linalg import norm

from pancad.constants import AngleConvention
from pancad.utils.pancad_types import PolarVector, SphericalVector

if TYPE_CHECKING:
    from typing import Literal

    import numpy.typing as npt

    from pancad.utils.pancad_types import (
        Space3DVector, Space2DVector, SpaceVector, Numpy1D, Numpy2D
    )

def angle_mod(angle: float) -> float:
    """Returns the angle bounded from -2pi to +2pi since python's modulo
    operator by default always returns the divisor's sign, which is
    different than other programming languages like C and C++.

    :param angle: The angle in radians.
    :returns: The equivalent angle bounded between -2pi and +2pi.
    """
    if angle >= 0:
        return angle % (2*np.pi)
    return angle % (-2*np.pi)

@overload
def get_unit_vector(vector: SpaceVector) -> Numpy1D: ...
@overload
def get_unit_vector(vector: Numpy1D) -> Numpy1D: ...
@overload
def get_unit_vector(vector: Numpy2D) -> Numpy2D: ...
def get_unit_vector(vector: SpaceVector | Numpy1D | Numpy2D) -> Numpy1D | Numpy2D:
    """Returns the unit vector of the given vector. If the vector is a zero
    vector, returns the zero vector.

    :raises TypeError: When provided a 0D or >2D numpy array.
    :raises ValueError: When provided a non 2D or 3D vector.
    """
    shape: tuple[int] | tuple[int, int]
    flat_vector = to_1d_np(vector)
    if isinstance(vector, np.ndarray):
        if len(vector.shape) == 1:
            shape = (vector.shape[0],)
        elif len(vector.shape) == 2 and vector.shape[1] == 1:
            shape = (vector.shape[0], 1)
        else:
            msg = f"Expected a 1D or 2D (with 1 column) numpy array. Got: {vector.shape}"
            raise TypeError(msg)
    else:
        shape = (len(vector),)
    if shape[0] not in {2, 3}:
        raise ValueError(f"Expected a 2 or 3 long vector. Got shape {shape}")
    length = np.linalg.norm(flat_vector)
    if length == 0:
        return flat_vector.reshape(*shape)
    unit_vector = flat_vector / length
    return unit_vector.reshape(*shape)

def get_vector_angle(vector1: SpaceVector,
                     vector2: SpaceVector,
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
    :raises TypeError: When non 2D/3D vectors or vectors of different lengths are provided.
    :returns: The angle between vector1 and vector2.
    """
    if len(vector1) == len(vector2) == 2:
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
    elif len(vector1) == len(vector2) == 3:
        angle = _get_angle_between_3d_vectors_pi(vector1, vector2, opposite)
    else:
        raise TypeError(f"Expected 2 2D/3D vectors of the same length, got {vector1}, {vector2}")
    if convention in (AngleConvention.PLUS_180,
                      AngleConvention.PLUS_360,
                      AngleConvention.SIGN_180):
        return degrees(angle)
    return angle

def is_clockwise(vector1: Space2DVector, vector2: Space2DVector) -> bool:
    """Returns whether 2D vector2 is clockwise of 2D vector1.

    :param vector1: A 2D vector with cartesian components.
    :param vector2: Another 2D vector with cartesian components.
    :returns: 'True' if vector2 is clockwise of vector1, otherwise 'False'.
    """
    if len(vector1) == len(vector2) == 2:
        x1, y1 = vector1
        vector1_90_ccw = (-y1, x1)
        # numpy can output an array from dot, so float is called on it here to guarantee the type
        return float(np.dot(vector1_90_ccw, vector2)) < 0
    raise ValueError("Both vectors must be 2 long")

def is_geometry_vector(vector: npt.NDArray[np.float64]) -> bool:
    """Returns whether the NumPy vector is a valid 2D or 3D vector

    :param vector: A NumPy vector to be checked
    :returns: True if the vector is a valid 2D or 3D vector
    """
    return vector.shape in [(2,), (3,), (2,1), (3,1)]

def multi_rotation(permutation: str, *angles: float) -> npt.NDArray[np.float64]:
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
    matrix: npt.NDArray[np.floating] = np.identity(3)
    for angle, axis in zip(angles, list(permutation)):
        matrix = matrix @ rotation_funcs[axis](angle)
    return matrix.astype(np.float64)

def rotation(angle: float,
             around: Literal["x", "y", "z", "2"] | Space3DVector) -> npt.NDArray[np.float64]:
    """Returns a rotation matrix that rotates around the given axis/vector by the
    angle. Assumes a right-handed coordinate system.

    :param angle: The counter-clockwise rotation angle in radians.
    :param around: The axis to rotate around. Options x, y, z, 2, and a
        tuple. 2 produces a 2D rotation matrix. If given tuple of 3 floats, the
        rotation matrix will be for rotating around that vector.
    :returns: A numpy rotation matrix.
    """
    cost = math.cos(angle)
    sint = math.sin(angle)
    around_axis: npt.NDArray[np.float64]

    if around == "2":
        return np.array([[cost, -sint], [sint, cost]])
    canon_axis_map = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
    if isinstance(around, str):
        around_axis = np.array(canon_axis_map[around])
    else:
        if len(around) != 3:
            raise TypeError(f"Expected 3D vector axis or axis letter for around, got: {around}")
        around_axis = get_unit_vector(around)

    x, y, z = around_axis
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

def positive_angle(angle: float) -> float:
    """Returns the positive representation of an angle in radians, bounded from
    0 to 2pi.
    """
    if angle >= 0:
        return angle_mod(angle)
    return angle_mod(angle) + 2*np.pi

def to_1d_tuple(value: Sequence[float] | Numpy1D | Numpy2D) -> SpaceVector:
    """Returns a 2D or 3D vector as a tuple from a given value."""
    tuple_value: tuple[float, ...]
    # Convert internal values based on the container type
    if isinstance(value, Sequence):
        tuple_value = tuple(map(float, value))
    elif isinstance(value, np.ndarray):
        tuple_value = tuple(to_1d_np(value))
    # Unpack and return tuple to guarantee length
    if len(tuple_value) == 2:
        x, y = tuple_value
        return (x, y)
    if len(tuple_value) == 3:
        x, y, z = tuple_value
        return (x, y, z)
    raise ValueError(f"Cannot convert {value} of class {value.__class__} to a 2 or 3 long tuple")

def to_1d_np(value: Sequence[float] | Numpy1D | Numpy2D) -> Numpy1D:
    """Returns a flat/horizontal 1D numpy array from a given sequence of floats or a 1 dimensional 
    numpy array.
    """
    if isinstance(value, Sequence):
        try:
            return np.array(value, dtype=np.float64, # pylint: disable=unexpected-keyword-arg
                            ndmax=1)
        except ValueError as exc:
            msg = f"Could not create a 1D numpy array from sequence value: {value}"
            raise TypeError(msg) from exc
    if isinstance(value, np.ndarray):
        return np.array(value.flatten(), dtype=np.float64)
    raise ValueError(f"Cannot convert {value} of class {value.__class__} to a 1D numpy array")

def r_of_cartesian(cartesian: SpaceVector) -> float:
    """Returns the r component of a polar or spherical vector from a
    given cartesian vector.

    :param cartesian: A vector with cartesian components (x, y) or (x, y, z).
    :returns: The radius component of the equivalent polar/spherical vector.
    """
    if len(cartesian) in (2, 3):
        return math.hypot(*cartesian)
    raise ValueError("Can only return r if the cartesian vector is 2 or 3")

def phi_of_cartesian(cartesian: SpaceVector) -> float:
    """Returns the polar/spherical azimuth component of the equivalent
    polar/spherical vector in radians. Bounded from -pi to pi.

    :param cartesian: A vector with cartesian components (x, y) or (x, y, z).
    :returns: The azimuth component of the equivalent polar/spherical vector.
    """
    if cartesian[0] == 0 and cartesian[1] == 0:
        return math.nan
    return math.atan2(cartesian[1], cartesian[0])

def theta_of_cartesian(cartesian: Space3DVector) -> float:
    """Returns the spherical inclination component of the equivalent spherical
    vector in radians.

    :param cartesian: A 3D vector with cartesian components (x, y, z).
    :returns: The inclination coordinate of the equivalent polar/spherical
        coordinate.
    """
    try:
        x, y, z = cartesian
    except ValueError as err:
        raise IndexError("Index out of range, likely 2D instead of 3D") from err
    if z == 0 and math.hypot(x, y) != 0:
        return math.pi/2
    if x == y == z == 0:
        return math.nan
    if z > 0:
        return math.atan(math.hypot(x, y) / z)
    if z < 0:
        return math.pi + math.atan(math.hypot(x, y) / z)
    raise ValueError(f"Unhandled exception, cartesian: {cartesian}")

def cartesian_to_polar(cartesian: Space2DVector) -> PolarVector:
    """Returns the polar version of the given cartesian vector.

    :param cartesian: A 2D vector with cartesian components x and y.
    :returns: An equivalent 2D vector with polar components r (radial distance)
              and phi (azimuth) in radians.
    """
    if len(cartesian) == 2:
        return PolarVector(r_of_cartesian(cartesian), phi_of_cartesian(cartesian))
    if len(cartesian) == 3:
        raise ValueError("2D, use cartesian_to_spherical for 3D points")
    raise ValueError("Invalid cartesian vector, must be 2 long to return")

def polar_to_cartesian(polar: Space2DVector) -> Space2DVector:
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

def spherical_to_cartesian(spherical: Space3DVector) -> Space3DVector:
    """Returns the cartesian version of the given spherical vector.

    :param spherical: A 3D vector with spherical components r (radial distance),
        phi (azimuth in radians), and theta (inclination in radians).
    :returns: An equivalent 3D vector with cartesian components x, y, and z.
    """
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
    raise ValueError(f"Unhandled spherical case! Got: {spherical}")

def cartesian_to_spherical(cartesian: Space3DVector) -> SphericalVector:
    """Returns the spherical version of the given cartesian vector.

    :param cartesian: A 3D vector with cartesian components x, y, z.
    :returns: A 3D vector with spherical components r (radial distance), phi
        (azimuth in radians), and theta (inclination in radians).
    """
    if len(cartesian) == 3:
        return SphericalVector(r_of_cartesian(cartesian),
                               phi_of_cartesian(cartesian),
                               theta_of_cartesian(cartesian))
    if len(cartesian) == 2:
        raise ValueError("2D, use cartesian_to_polar for 2D points")
    raise ValueError("Invalid cartesian vector, must be 3 long")

def _get_angle_between_2d_vectors_2pi(vector1: Space2DVector,
                                      vector2: Space2DVector,
                                      explementary: bool=False) -> float:
    """Returns the counter-clockwise angle between vector1 and vector2 in radians
    bounded between 0 and 2pi. Returns the clockwise angle if explementary is
    set to True.

    :param vector1: A 2D vector with cartesian components.
    :param vector2: Another 2D vector with cartesian components.
    :param explementary: Sets whether to return the explement of the angle
        between vector1 and vector2.
    :returns: The angle between vector1 and vector2.
    """
    unit_dot = np.dot(vector1, vector2) / (norm(vector1) * norm(vector2))
    if np.isclose(abs(unit_dot), 1):
        angle = math.acos(round(unit_dot))
    else:
        angle = math.acos(unit_dot)
    if is_clockwise(vector1, vector2):
        angle = math.tau - angle
    if explementary:
        return math.tau - angle
    return angle

def _get_angle_between_2d_vectors_pi(vector1: Space2DVector,
                                     vector2: Space2DVector,
                                     supplementary: bool=False,
                                     signed: bool=False) -> float:
    """Returns the angle between vector1 and vector2 in radians between 0 and pi.

    :param vector1: A 2D vector with cartesian components.
    :param vector2: Another 2D vector with cartesian components.
    :param supplementary: Sets whether to return the supplement of the angle
        between vector1 and vector2.
    :param signed: Sets whether to return a negative angle if the angle is
        oriented clockwise.
    :returns: The angle between vector1 and vector2.
    """
    unit_dot = np.dot(vector1, vector2) / (norm(vector1) * norm(vector2))
    if np.isclose(abs(unit_dot), 1):
        angle = math.acos(round(unit_dot))
    else:
        angle = math.acos(unit_dot)
    if supplementary:
        angle = math.pi - angle
    if signed and (is_clockwise(vector1, vector2) ^ supplementary):
        return -angle
    return angle

def _get_angle_between_3d_vectors_pi(vector1: Space3DVector,
                                     vector2: Space3DVector,
                                     supplementary: bool=False) -> float:
    """Returns the angle between vector1 and vector2 in radians between 0 and pi.

    :param vector1: A 3D vector with cartesian components.
    :param vector2: Another 3D vector with cartesian components.
    :param supplementary: Sets whether to return the supplement of the angle
        between vector1 and vector2.
    :returns: The angle between vector1 and vector2.
    """
    unit_dot = np.dot(vector1, vector2) / (norm(vector1) * norm(vector2))
    if np.isclose(abs(unit_dot), 1):
        angle = math.acos(round(unit_dot))
    else:
        angle = math.acos(unit_dot)
    if supplementary:
        return math.pi - angle
    return angle
