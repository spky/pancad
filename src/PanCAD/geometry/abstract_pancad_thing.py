"""A module defining the properties and methods that all PanCAD elements 
share.
"""

from abc import ABC, abstractmethod
from uuid import UUID, uuid4

class PanCADThing(ABC):
    """An abstract class defining the properties and methods that all PanCAD 
    elements, constraints, or whatever must have with no exceptions.
    """
    
    STR_VERBOSE = False
    """A Flag allowing PanCAD objects to print more verbose strings and reprs.
    """
    
    # Getters #
    @property
    def uid(self) -> str | UUID:
        """The unique id of the element, used for CAD interoperability. Can be 
        manually set, but is usually randomly generated or read from an existing 
        file.
        """
        return self._uid
    
    # Setters #
    @uid.setter
    def uid(self, value: str | None) -> None:
        if value is None:
            self._uid = uuid4()
        else:
            self._uid = value