"""A module providing helper functions for defining geometry and constraints."""
from __future__ import annotations

from functools import wraps
from itertools import islice
from collections.abc import Sequence
from typing import TYPE_CHECKING
from numbers import Real

import numpy as np

from pancad.utils import trigonometry as trig

if TYPE_CHECKING:
    from typing import Any

    from pancad.utils.pancad_types import SpaceVector

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
