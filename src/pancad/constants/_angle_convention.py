"""A private module with an enumeration defining the angle convention options.
"""
from enum import Flag, auto

class AngleConvention(Flag):
    """An enumeration defining which angle convention to use. 3D angles are 
    bounded between 0 and π, or 0 and 180° if using degrees, unless explicitly 
    stated otherwise.
    """
    PLUS_PI = auto()
    """Angle always between 0 and π, sign ignored."""
    PLUS_TAU = auto()
    """Angle always between 0 and 2π. Angle in 3D still less than π."""
    PLUS_180 = auto()
    """Angle always between 0 and 180°, sign ignored."""
    PLUS_360 = auto()
    """Angle always between 0 and 360°. Angle in 3D still less than 180°."""
    SIGN_PI = auto()
    """Angle always between -π and π. Sign ignored in 3D."""
    SIGN_180 = auto()
    """Angle always between -180° and 180°. Sign ignored in 3D."""
    def __repr__(self) -> str:
        return f"{self.name}"
