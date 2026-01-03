"""A module providing a class defining the required properties and interfaces of 
pancad geometry classes.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from pancad.geometry import PancadThing

if TYPE_CHECKING:
    from typing import Self
    from pancad.geometry.constants import ConstraintReference

class AbstractGeometry(PancadThing):
    """A class defining the interfaces provided by pancad Geometry Elements."""
    # Public Methods #
    def __init__(self,
                 references: dict[ConstraintReference, AbstractGeometry]
                 ) -> None:
        self._references = references
        for reference, child in self.children.items():
            if child.uid != self.uid:
                child.parent = self

    @property
    def parent(self) -> AbstractGeometry | None:
        """The parent of the geometry. Example: A circle center point's parent 
        would be the circle, but if the point's parent is None then the point 
        is its own parent. Should never be set by the instance itself, only by 
        the parent to claim ownership.
        """
        if hasattr(self, "_parent"):
            return self._parent
        return None
    @parent.setter
    def parent(self, value: AbstractGeometry) -> None:
        self._parent = value

    @property
    def children(self) -> dict[ConstraintReference, AbstractGeometry]:
        """The mapping of the geometry's constraint references to its child 
        geometries. Read-only.
        """
        return {reference: self.get_reference(reference)
                for reference in self.get_all_references()}

    # Abstract Methods
    def get_reference(self, reference: ConstraintReference) -> AbstractGeometry:
        """Returns the subgeometry associated with the reference."""
        return self._references[reference]

    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns the constraint references available for the geometry."""
        return list(self._references.keys())

    @abstractmethod
    def update(self, other: AbstractGeometry) -> Self:
        """Takes geometry of the same type as the calling geometry and updates 
        the calling geometry to match the new geometry while maintaining its 
        uid. Should return itself afterwards.
        """

    # Python Dunders #
    def __len__(self) -> int:
        """Implements the Python len() function to return whether the geometry 
        is 2D or 3D.
        """

    def __repr__(self) -> str:
        return str(self)

    @abstractmethod
    def __str__(self) -> str:
        strings = ["<", self.__class__.__name__]
        if self.STR_VERBOSE:
            strings.append(f"'{self.uid}'")
        return "".join(strings)
