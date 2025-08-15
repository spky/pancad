"""A module providing a class defining the required properties and interfaces of 
PanCAD geometry classes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

from PanCAD.geometry.constants import ConstraintReference

class AbstractGeometry(ABC):
    """A class defining the interfaces provided by PanCAD Geometry Elements."""
    
    # Properties #
    @property
    @abstractmethod
    def uid(self) -> str:
        """The unique id of the geometry, usually used as its name."""
    
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
        memory location (Python id). Should return itself afterwards.
        """
    
    # Python Dunders #
    def __len__(self) -> int:
        """Implements the Python len() function to return whether the geometry 
        is 2D or 3D.
        """
