"""A module providing a constraint classes for snapto constraints in 2D 
geometry contexts. pancad defines a snapto constraint as one that can be applied 
to geometry with no additional arguments but still meaningfully constrain the 
geometry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pancad.geometry.constraints import AbstractConstraint

if TYPE_CHECKING:
    from typing import NoReturn
    from pancad.utils.constraints import GeometryReference
    from pancad.geometry import AbstractGeometry
    from pancad.geometry.constants import ConstraintReference

class AbstractSnapTo(AbstractConstraint):
    """An abstract class of constraints that can be applied to a set of **one 
    or two** geometries without any further definition.
    
    :param reference_pairs: The (AbstractGeometry, ConstraintReference) pairs of
        the geometry to be constrained.
    :param uid: The unique id of the constraint.
    """
    def __init__(self, *geometry: AbstractGeometry, uid: str=None) -> None:
        self.uid = uid
        if len(geometry) not in [1, 2]:
            raise ValueError(f"Expected 1 or 2 geometries, got: {geometry}")
        if any(len(g) != 2 for g in geometry):
            non_two_dimensional = [g for g in geometry if len(g) != 2]
            raise ValueError(f"Non-2D Geometry provided: {non_two_dimensional}")
        self._geometry = geometry

    # Python Dunders
    def __eq__(self, other: AbstractSnapTo) -> bool:
        """Checks whether two snapto relations are functionally the same by 
        comparing the memory ids of their constrained geometries.
        
        :param other: Another SnapTo relationship of the same type.
        :returns: Whether the relations are the same.
        """
        geometry_zip = zip(self.get_geometry(), other.get_geometry())
        if isinstance(other, self.__class__):
            return all(g is other_g for g, other_g in geometry_zip)
        return NotImplemented

class Horizontal(AbstractSnapTo):
    """A constraint that sets either a single geometry horizontal or a pair of 
    geometries horizontal relative to each other in a 2D coordinate system. Can 
    constrain:
    """

class Vertical(AbstractSnapTo):
    """A constraint that sets either a single geometry vertical or a pair of 
    geometries vertical relative to each other in a 2D coordinate system. Can 
    constrain:
    """
