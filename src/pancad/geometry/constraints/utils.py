"""A module providing types and functions to assist in defining and creating 
constraints.
"""
from __future__ import annotations

from itertools import islice
from collections.abc import Sequence
from typing import TYPE_CHECKING

from pancad.geometry import AbstractGeometry
from pancad.geometry.constants import ConstraintReference
from pancad.geometry.constraints import AbstractConstraint

if TYPE_CHECKING:
    from typing import Any

GeometryReference = (Sequence[AbstractGeometry, ConstraintReference]
                     | AbstractGeometry
                     | AbstractConstraint)

def flatten_to_pairs(*inputs: Sequence[Any, Any] | Any) -> list[tuple[Any, Any]]:
    """Flattens the inputs and then pairs them into tuples.
    
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

def constraint_args(*reference_pairs: GeometryReference
                    ) -> list[tuple[AbstractGeometry, ConstraintReference]]:
    """Flattens and parses combinations of constraint geometry reference pairs.
    
    :param reference_pairs: A series of (AbstractGeometry, ConstraintReference) 
        paired arguments. The arguments can be actually paired into tuples or 
        just given as a comma separated list of alternating AbstractGeometry and 
        ConstraintReference type objects.
    :returns: A list of (AbstractGeometry, ConstraintReference) tuples.
    :raises ValueError: When an uneven number of reference_pairs is provided.
    :raises TypeError: When the first of a pair is not AbstractGeometry Geometry 
        or the second of a pair is not a ConstraintReference.
    """
    pairs = flatten_to_pairs(*reference_pairs)
    if any(not isinstance(geometry, AbstractGeometry) for geometry, _ in pairs):
        raise TypeError("Non-Geometry element in one of 1st pair elements.")
    if any(not isinstance(reference, ConstraintReference)
           for _, reference in pairs):
        raise TypeError("Non-ConstraintReference in one of 2nd pair elements.")
    return pairs
