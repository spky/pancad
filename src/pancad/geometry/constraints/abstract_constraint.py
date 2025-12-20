"""A module providing a class defining the required properties and interfaces of 
pancad constraint classes.
"""
from __future__ import annotations

from abc import abstractmethod
from itertools import islice
from collections.abc import Sequence

from pancad.geometry import PancadThing, AbstractGeometry
from pancad.geometry.constants import ConstraintReference

class AbstractConstraint(PancadThing):
    """A class defining the interfaces provided by all pancad Constraint 
    Elements.
    """
    # Abstract Public Methods #
    @abstractmethod
    def get_constrained(self) -> tuple[AbstractGeometry]:
        """Returns the geometry or geometries being constrained."""
    @abstractmethod
    def get_geometry(self) -> tuple[AbstractGeometry]:
        """Returns the portions of the constrained geometry being constrained. 
        
        Examples: The x axis of a :class:`~pancad.geometry.CoordinateSystem` or 
        the start point of a :class:`~pancad.geometry.LineSegment`.
        """
    @abstractmethod
    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometrys' ConstraintReferences in 
        the same order as the tuple returned by :meth:`get_constrained`.
        """
    def __repr__(self) -> str:
        return str(self)
    def __str__(self) -> str:
        strings = ["<", self.__class__.__name__]
        if self.STR_VERBOSE:
            strings.append(f"'{self.uid}'")
        strings.append("-")
        constrained = self.get_constrained()
        references = self.get_references()
        geometry_strings = []
        for geometry, reference in zip(constrained, references):
            geometry_strings.append(
                repr(geometry).replace("<", "").replace(">", "")
            )
            geometry_strings[-1] += reference.name
        strings.append(",".join(geometry_strings))
        strings.append(">")
        return "".join(strings)

GeometryReference = (tuple[AbstractGeometry, ConstraintReference]
                     | AbstractGeometry
                     | AbstractConstraint)

def constraint_args(*reference_pairs: GeometryReference
                    ) -> list[tuple[AbstractGeometry, ConstraintReference]]:
    """Flattens and parses combinations of constraint geometry reference pairs.
    
    :param reference_pairs: A series of (AbstractGeometry, ConstraintReference) 
        paired arguments. The arguments can be actually paired into tuples or 
        just given as a comma separated list of alternating AbstractGeometry and 
        ConstraintReference type objects.
    :returns: A list of (AbstractGeometry, ConstraintReference) tuples.
    :raises ValueError: When an uneven number of reference_pairs is provided.
    :raises TypeError: When the first of a pair is not AbstractGeometryGeometry 
        or the second of a pair is not a ConstraintReference.
    """
    items = []
    for item in reference_pairs:
        if isinstance(item, Sequence):
            items.extend(item)
        else:
            items.append(item)
    pairs = []
    iterator = iter(items)
    while pair := tuple(islice(iterator, 2)):
        if len(pair) != 2:
            raise ValueError("Uneven number of reference_pairs")
        pairs.append(pair)
    if any(not isinstance(geometry, AbstractGeometry) for geometry, _ in pairs):
        raise TypeError("Non-Geometry element in one of 1st pair elements.")
    if any(not isinstance(reference, ConstraintReference)
           for _, reference in pairs):
        raise TypeError("Non-ConstraintReference in one of 2nd pair elements.")
    return pairs
