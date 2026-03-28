"""A module providing the types of svg path parameter types"""

from enum import Enum, auto

class PathParameterType(Enum):
    """An enumeration of svg path parameter input types used to dispatch reading
    and writing functionality.
    """
    PAIR = auto()
    SINGLE = auto()
    ARC = auto()
    CLOSEPATH = auto()
