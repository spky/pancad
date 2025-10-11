"""A module providing an enumeration class for the string constants that define 
FreeCAD pad types like Length, UpToShape, etc.
"""

from enum import StrEnum
from PanCAD.geometry.constants import FeatureType

class PadType(StrEnum):
    """An enumeration used to define the FreeCAD Pad options supported by 
    PanCAD.
    """
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
        FreeCAD Pad.
        
        :param midplane: Whether the Pad is a midplane extrusion.
        :param reversed_pad: Whether the Pad is a reversed extrusion.
        :returns: The equivalent :class:`~PanCAD.geometry.constants.FeatureType` 
            for the FreeCAD Pad settings.
        :raises ValueError: When an unsupported PadType executes this function.
        """
        match self:
            case PadType.LENGTH:
                if midplane:
                    return FeatureType.SYMMETRIC
                elif reversed_pad:
                    return FeatureType.ANTI_DIMENSION
                else:
                    return FeatureType.DIMENSION
            case PadType.TWO_LENGTHS:
                if reversed_pad:
                    return FeatureType.ANTI_TWO_DIMENSIONS
                else:
                    return FeatureType.TWO_DIMENSIONS
            case PadType.UP_TO_LAST:
                return FeatureType.UP_TO_LAST
            case PadType.UP_TO_FIRST:
                return FeatureType.UP_TO_FIRST
            case PadType.UP_TO_FACE:
                return FeatureType.UP_TO_FACE
            case PadType.UP_TO_BODY:
                return FeatureType.UP_TO_BODY
            case _:
                raise ValueError(f"Unexpected Type {self.name}")