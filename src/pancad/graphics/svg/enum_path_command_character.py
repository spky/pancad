"""A module providing the types of svg path command characters"""

from enum import StrEnum

class PathCommandCharacter(StrEnum):
    a = "a"
    A = "A"
    m = "m"
    M = "M"
    l = "l"
    L = "L"
    c = "c"
    C = "C"
    s = "s"
    S = "S"
    q = "q"
    Q = "Q"
    t = "t"
    T = "T"
    h = "h"
    H = "H"
    v = "v"
    V = "V"
    z = "z"
    Z = "Z"
    
    REL_MOVETO = m
    ABS_MOVETO = M
    
    REL_LINETO = l
    ABS_LINETO = L
    
    def __repr__(self):
        return self.value