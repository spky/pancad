"""A module providing an enumeration class for the string constants that define 
FreeCAD pad types like Length, UpToShape, etc.
"""

from enum import StrEnum
from pancad.geometry.constants import FeatureType

MIDPLANE = "midplane"
REVERSED = "reversed"

class PadType(StrEnum):
    """An enumeration used to define the FreeCAD Pad options supported by 
    pancad.
    """
    LENGTH = "Length"
    UP_TO_LAST = "UpToLast"
    UP_TO_FIRST = "UpToFirst"
    UP_TO_FACE = "UpToFace"
    TWO_LENGTHS = "TwoLengths"
    UP_TO_SHAPE = "UpToShape"
    UP_TO_BODY = "UpToBody"
    def get_feature_type(self,
                         midplane: bool,
                         reversed_pad: bool) -> FeatureType:
        """Returns the equivalent FeatureType based upon the settings of a 
        FreeCAD Pad.
        
        :param midplane: Whether the Pad is a midplane extrusion.
        :param reversed_pad: Whether the Pad is a reversed extrusion.
        :returns: The equivalent :class:`~pancad.geometry.constants.FeatureType` 
            for the FreeCAD Pad settings.
        :raises ValueError: When an unsupported PadType executes this function.
        """
        if midplane and self in MODIFIABLE_TYPES:
            modifier = MIDPLANE
        elif reversed_pad and self in MODIFIABLE_TYPES:
            modifier = REVERSED
        else:
            modifier = None
        try:
            return _TO_FEATURE_TYPE[self, modifier]
        except KeyError as err:
            raise ValueError("Unexpected Type and Modifier") from err

MODIFIABLE_TYPES = [PadType.LENGTH, PadType.TWO_LENGTHS]
_TO_FEATURE_TYPE = {
    (PadType.LENGTH, MIDPLANE): FeatureType.SYMMETRIC,
    (PadType.LENGTH, REVERSED): FeatureType.ANTI_DIMENSION,
    (PadType.LENGTH, None): FeatureType.DIMENSION,
    (PadType.TWO_LENGTHS, REVERSED): FeatureType.ANTI_TWO_DIMENSIONS,
    (PadType.TWO_LENGTHS, None): FeatureType.TWO_DIMENSIONS,
    (PadType.UP_TO_LAST, None): FeatureType.UP_TO_LAST,
    (PadType.UP_TO_FIRST, None): FeatureType.UP_TO_FIRST,
    (PadType.UP_TO_FACE, None): FeatureType.UP_TO_FACE,
    (PadType.UP_TO_BODY, None): FeatureType.UP_TO_BODY,
}
