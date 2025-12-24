"""A module providing helper functions for defining geometry and constraints."""
from __future__ import annotations

from itertools import islice
from collections.abc import Sequence
from typing import TYPE_CHECKING
from numbers import Real

from numpy import ndarray

if TYPE_CHECKING:
    from typing import Any

def parse_vector(*components: Real | Sequence[Real] | ndarray
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
        if isinstance(vector, ndarray):
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
