"""A module providing a class defining the required properties and interfaces of 
PanCAD feature classes.
"""
from __future__ import annotations

from abc import abstractmethod

from PanCAD.geometry import PanCADThing, AbstractGeometry
from PanCAD.geometry.constants import ConstraintReference

class AbstractFeature(PanCADThing):
    
    # Public Methods #
    @abstractmethod
    def get_dependencies(self) -> tuple[AbstractFeature | AbstractGeometry]:
        """Returns the feature's external dependencies. Example: A 
        :class:`~PanCAD.geometry.Sketch` returns the sketch's coordinate 
        system and its external geometry references.
        """