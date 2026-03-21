"""A module providing helper functions for defining geometry and constraints."""
from __future__ import annotations

from functools import wraps
from itertools import islice
from collections.abc import Sequence
from typing import TYPE_CHECKING
from numbers import Real
from warnings import catch_warnings

import numpy as np
import quaternion

from pancad.utils import trigonometry as trig

if TYPE_CHECKING:
    from typing import Any

    from pancad.utils.pancad_types import SpaceVector, Space3DVector

### Wrappers
def three_dimensional_only(func):
    """A wrapper to raise an error when a 3d method is called on 2d geometry."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if len(self) != 3:
            raise ValueError(f"{func.__name__} Method only available on 3D"
                             f" {self.__class__.__name__}s")
        result = func(self, *args, **kwargs)
        return result
    return wrapper


def two_dimensional_only(func):
    """A wrapper to raise an error when a 2d method is called on 3d geometry."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if len(self) != 2:
            raise ValueError(f"{func.__name__} Method only available on 2D"
                             f" {self.__class__.__name__}s")
        result = func(self, *args, **kwargs)
        return result
    return wrapper


def three_dimensions_required(func):
    """A wrapper to raise an error when a non-3D non-string/Real argument is
    supplied to a function that only works with 3D arguments.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        errors = []
        for arg in args:
            if not isinstance(arg, (str, Real, bool)) and len(arg) != 3:
                errors.append(arg)
        if errors:
            raise ValueError("Expected only 3D arguments,"
                             f" got non-3D args: {errors}")
        result = func(self, *args, **kwargs)
        return result
    return wrapper


def two_dimensions_required(func):
    """A wrapper to raise an error when a non-2D non-string/Real argument is
    supplied to a function that only works with 2D arguments.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        errors = []
        for arg in args:
            if not isinstance(arg, (str, Real, bool)) and len(arg) != 2:
                errors.append(arg)
        if errors:
            raise ValueError("Expected only 2D arguments,"
                             f" got non-2D args: {errors}")
        result = func(self, *args, **kwargs)
        return result
    return wrapper


def no_dimensional_mismatch(func):
    """A wrapper to raise an error when the first argument of a method does not
    match the dimension of the geometry.
    """
    @wraps(func)
    def wrapper(self, value, *args, **kwargs):
        if len(self) != len(value):
            raise ValueError(
                "Input Dimensional Mismatch:"
                f" {len(self)}D {self.__class__.__name__}"
                f" and {len(value)}D {value.__class__.__name__}"
            )
        result = func(self, value, *args, **kwargs)
        return result
    return wrapper

### Functions
def parse_vector(*components: Real | Sequence[Real] | np.ndarray
                 ) -> tuple[Real, Real] | tuple[Real, Real, Real]:
    """Batches structures of vector component inputs to a tuple of Reals.
    Usually used by pancad to parse position and direction information into the
    geometry classes.

    :raises TypeError: When provided a single component that is not Sequence or
        when 2 or more non-Real arguments.
    :raises ValueError: When provided 0 or more than 3 arguments.
    """
    if len(components) not in [1, 2, 3]:
        raise ValueError("components must be 1 to 3 arguments,"
                         f" got {len(components)}")
    if len(components) == 1:
        vector = components[0]
        if isinstance(vector, np.ndarray):
            if vector.shape not in [(2,), (3,), (2, 1), (3, 1)]:
                raise ValueError("NumPy vectors must be 2 or 3 elements,"
                                 f" got {vector}")
            return tuple(float(component.squeeze()) for component in vector)
        if isinstance(vector, Sequence):
            return tuple(vector)
        raise TypeError(f"Expected ndarray/Sequence, got {type(components)}")
    if all(isinstance(component, Real) for component in components):
        return tuple(components)
    types = [type(component) for component in components]
    raise TypeError(f"Expected Real components, got {types}")


def parse_pairs(*inputs: Sequence[Any, Any] | Any) -> list[tuple[Any, Any]]:
    """Flattens a sequence of inputs to pairs. Usually used by pancad to parse
    (geometry, reference) pair input.

    :raises ValueError: When an uneven number of inputs is provided.
    """
    items = []
    for item in inputs:
        if isinstance(item, Sequence):
            items.extend(item)
        else:
            items.append(item)
    tuples = []
    iterator = iter(items)
    while pair := tuple(islice(iterator, 2)):
        if len(pair) != 2:
            raise ValueError("Uneven number of reference_pairs")
        tuples.append(pair)
    return tuples

def closest_to_origin(point: SpaceVector, vector: SpaceVector) -> np.ndarray:
    """Returns the point closest to the origin on a line created by a point
    and a vector.

    :param point: A vector to a point on the line.
    :param vector: A vector in the same direction as the line.
    :returns: A numpy array vector pointing to the closest point on the line.
    :raises ValueError: When the direction vector is a zero vector or the
        point and vector dimensions do not match.
    """
    if np.allclose(vector, [0] * len(vector)):
        msg = f"Got zero vector for line direction: {tuple(vector)}"
        raise ValueError(msg)
    if len(point) != len(vector):
        msg = f"Point {point} and vector {vector} dimensions are not equal"
        raise ValueError(msg)
    point_vector = np.array(point)
    vector = np.array(vector)
    unit_vector = trig.get_unit_vector(vector)
    dot = np.dot(point_vector, unit_vector)
    if dot == 0:
        # Point vector and direction are perpendicular, or the point vector
        # is zero vector. Either way the provided point is the closest.
        return point_vector
    if np.isclose(abs(dot), np.linalg.norm(point_vector)):
        # Point vector and direction vector are parallel or anti-parallel,
        # so the closest point must be the origin.
        return np.array([0] * len(point))
    # No special case, so the off-closest point vector can be subtracted out
    # to get the closest point.
    return point_vector - dot * unit_vector

def get_perpendicular(vector: Space3DVector) -> Space3DVector:
    """Returns a non-unique 3D unit vector perpendicular to the vector by
    finding its cross product to the most orthogonal basis vector.

    :raises ValueError: When provided a zero vector.
    :raises TypeError: When provided a non-3D vector.
    """
    try:
        x, y, z = map(abs, vector)
    except ValueError as exc:
        if "values to unpack" in str(exc):
            msg = f"get_perpendicular only supports 3D vectors, got: {vector}"
            raise TypeError(msg) from exc
        raise
    if np.allclose(vector, (0, 0, 0)):
        raise ValueError(f"Expected non-zero vector, got {vector}")
    x_axis = (1, 0, 0)
    y_axis = (0, 1, 0)
    z_axis = (0, 0, 1)
    ortho_map = {
        # x < y | x < z | y < z
        (True, True, False): x_axis,
        (True, True, True): x_axis,
        (True, False, False): z_axis,
        (True, False, True): z_axis,
        (False, False, True): y_axis,
        (False, True, True): y_axis,
        (False, True, False): z_axis,
        (False, False, False): z_axis,
    }
    ortho = np.cross(vector, ortho_map[x < y, x < z, y < z])
    return trig.get_unit_vector(ortho)

def get_rotation_quat(start: Space3DVector, target: Space3DVector
                      ) -> np.quaternion:
    """Returns a (non-unique) shortest-arc quaternion to rotate the start vector
    to the target vector.

    :raises ValueError: When provided a zero vector.
    :raises TypeError: When provided a non-3D vector.
    """
    with catch_warnings(action="error"):
        # NumPy only produces a warning when a 2D cross product is attempted.
        try:
            scalar = (np.linalg.norm(start) * np.linalg.norm(target)
                          + np.dot(start, target))
            axis = np.cross(start, target)
        except (ValueError, DeprecationWarning) as exc:
            non_3d_msgs = ["2-dimensional vectors", "incompatible dimensions",
                           "not aligned"]
            if any(non_3d in str(exc) for non_3d in non_3d_msgs):
                msg = f"start/target must be 3D, got: {start}, {target}"
                raise TypeError(msg) from exc
            raise
    if any(np.allclose(vector, (0, 0, 0)) for vector in [start, target]):
        msg = f"start/target cannot be zero vector: {start}, {target}"
        raise ValueError(msg)
    quat = np.quaternion(scalar, *axis)
    norm = np.linalg.norm(quaternion.as_float_array(quat))
    if np.isclose(norm, 0):
        # If the norm of the quaternion is 0, the vectors are anti-parallel.
        # Anti-parallel vectors have an infinite number of shortest arc
        # quaternions, so an arbitrary perpendicular vector must be used as a
        # rotation axis.
        axis = get_perpendicular(start)
        quat = np.quaternion(scalar, *axis)
        norm = np.linalg.norm(quaternion.as_float_array(quat))
    return quat / norm
