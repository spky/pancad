"""A module providing a class defining the required properties and interfaces of 
PanCAD feature classes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from PanCAD.geometry.abstract_geometry import AbstractGeometry
from PanCAD.geometry.constants import ConstraintReference

class AbstractFeature(ABC):
    
    # Properties #
    @property
    @abstractmethod
    def uid(self) -> str:
        """The unique id of the feature, usually used as its name."""
    
    # Public Methods #
    @abstractmethod
    def get_dependencies(self) -> tuple[AbstractFeature | AbstractGeometry]:
        """Returns the feature's external dependencies. Example: A 
        :class:`~PanCAD.geometry.Sketch` returns the sketch's coordinate 
        system and its external geometry references.
        """