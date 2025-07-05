"""A module providing an enumeration for the constraint types available to 2D 
sketches"""

from enum import Flag, auto

class FeatureType(Flag):
    # Dimension/Length Types
    DIMENSION = auto() # i.e. Length for extrusions
    ANTI_DIMENSION = auto()
    SYMMETRIC = auto() # i.e. midplane for extrusions
    
    TWO_DIMENSIONS = auto() # i.e. Two Lengths for extrusions
    ANTI_TWO_DIMENSIONS = auto()
    
    # Condition Type
    UP_TO_LAST = auto()
    UP_TO_FIRST = auto()
    
    # Feature Type
    UP_TO_FACE = auto()
    UP_TO_BODY = auto()
    
    def __repr__(self):
        match self:
            case self.DIMENSION:
                return "Dim"
            case self.ANTI_DIMENSION:
                return "ADim"
            case self.SYMMETRIC:
                return "Sym"
            case self.TWO_DIMENSIONS:
                return "2Dim"
            case self.ANTI_TWO_DIMENSIONS:
                return "A2Dim"
            case self.UP_TO_LAST:
                return "toLast"
            case self.UP_TO_FIRST:
                return "toFirst"
            case self.UP_TO_FACE:
                return "toFace"
            case self.UP_TO_BODY:
                return "toBody"
            case _:
                return repr(self)