"""A module providing an enumeration class for the string constants that define 
FreeCAD pad types like Length, UpToShape, etc.
"""

from enum import StrEnum
from PanCAD.geometry.constants import FeatureType

class PadType(StrEnum):
    LENGTH = "Length"
    UP_TO_LAST = "UpToLast"
    UP_TO_FIRST = "UpToFirst"
    UP_TO_FACE = "UpToFace"
    TWO_LENGTHS = "TwoLengths"
    UP_TO_SHAPE = "UpToShape"
    
    def get_feature_type(self,
                         midplane: bool,
                         reversed_pad: bool) -> FeatureType:
        """Returns the equivalent FeatureType based upon the settings of a 
        FreeCAD Pad
        """
        match self.name:
            case "LENGTH":
                if midplane:
                    return FeatureType.SYMMETRIC
                elif reversed_pad:
                    return FeatureType.ANTI_DIMENSION
                else:
                    return FeatureType.DIMENSION
            case "TWO_LENGTHS":
                if reversed_pad:
                    return FeatureType.ANTI_TWO_DIMENSIONS
                else:
                    return FeatureType.TWO_DIMENSIONS
            case "UP_TO_LAST":
                return FeatureType.UP_TO_LAST
            case "UP_TO_FIRST":
                return FeatureType.UP_TO_FIRST
            case "UP_TO_FACE":
                return FeatureType.UP_TO_FACE
            case "UP_TO_SHAPE":
                return FeatureType.UP_TO_BODY
            case _:
                raise ValueError(f"Unexpected Type {self.name}")