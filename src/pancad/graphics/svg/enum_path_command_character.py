"""A module providing the types of svg path command characters"""

from enum import StrEnum

class PathCommandCharacter(StrEnum):
    """An enumeration of the characters used to define svg path element strings.
    """
    REL_ARC = "a"
    ABS_ARC = "A"
    REL_MOVE = "m"
    ABS_MOVE = "M"
    REL_LINE = "l"
    ABS_LINE = "L"
    REL_CURVE = "c"
    ABS_CURVE = "C"
    REL_SMOOTH_CURVE = "s"
    ABS_SMOOTH_CURVE = "S"
    REL_QUADRATIC = "q"
    ABS_QUADRATIC = "Q"
    REL_BEZIER = "t"
    ABS_BEZIER = "T"
    REL_HORIZONTAL = "h"
    ABS_HORIZONTAL = "H"
    REL_VERTICAL = "v"
    ABS_VERTICAL = "V"
    REL_CLOSEPATH = "z"
    ABS_CLOSEPATH = "Z"

    def __repr__(self):
        return self.value
