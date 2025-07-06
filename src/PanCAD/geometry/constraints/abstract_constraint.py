"""A module providing a class defining the required properties and interfaces of 
PanCAD constraint classes.
"""
# from __future__ import annotations

from abc import ABC, abstractmethod

from PanCAD.geometry.abstract_geometry import AbstractGeometry
from PanCAD.geometry.constants import ConstraintReference

class AbstractConstraint(ABC):
    
    # Public Methods #
    @abstractmethod
    def get_constrained(self) -> tuple[AbstractGeometry]:
        """Returns a tuple of the constrained geometries."""
    
    @abstractmethod
    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometrys'
        ConstraintReferences.
        """