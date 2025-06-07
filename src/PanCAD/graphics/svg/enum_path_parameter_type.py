"""A module providing the types of svg path parameter types"""

from enum import Enum, auto

class PathParameterType(Enum):
    PAIR = auto()
    SINGLE = auto()
    ARC = auto()
    CLOSEPATH = auto()