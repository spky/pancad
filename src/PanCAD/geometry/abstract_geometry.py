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
    @abstractmethod
    def get_reference(self, reference: ConstraintReference) -> AbstractGeometry:
        """Returns the subgeometry associated with the reference."""
    
    @abstractmethod
    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns the constraint references available for the geometry."""
    
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