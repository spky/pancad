"""A module providing the names of coordinate system planes"""

from enum import StrEnum

class PlaneName(StrEnum):
    XY = "XY"
    XZ = "XZ"
    YZ = "YZ"