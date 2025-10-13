"""A module providing an enumeration for the feature types available to 3D 
features to define their directions and end conditions. 
"""

from enum import Flag, auto

class FeatureType(Flag):
    """An enumeration used by features to define their directions and end 
    conditions.
    """
    
    # Dimension Types #
    DIMENSION = auto()
    """Features that take one parameter in the normal direction of their 
    initial plane. Example: An extrusion specified by one length dimension and 
    extending normal to its sketch plane.
    """
    ANTI_DIMENSION = auto()
    """Features that take one parameter in the anti-normal direction of their 
    initial plane. Example: An extrusion specified by one length dimension and 
    extending anti-normal to its sketch plane after checking "Reverse" in the 
    CAD application.
    """
    SYMMETRIC = auto()
    """Features that take one parameter symmetric about their initial plane. 
    Example: An extrusion specified by a length dimension and extending to 
    that length equally in both directions about its midplane.
    """
    TWO_DIMENSIONS = auto()
    """Features that take one parameter in the normal direction of their initial 
    plane and one parameter in the anti-normal direction, in that order.
    """
    ANTI_TWO_DIMENSIONS = auto()
    """Features that take one parameter in the anti-normal direction of their 
    initial plane and one parameter in the normal direction, in that order.
    """
    # Condition Types #
    UP_TO_LAST = auto()
    """Features that extend up to the last available face in its local context, 
    usually the part model as defined up to the new feature.
    """
    UP_TO_FIRST = auto()
    """Features that extend up to the first available face in its local context, 
    usually the part model as defined up to the new feature.
    """
    # Feature Types #
    UP_TO_FACE = auto()
    """Features that extend up to a user specified face."""
    UP_TO_BODY = auto()
    """Features that extend up to a user specified body."""
    
    # Aliases #
    DIMENSION_TYPE = (
        DIMENSION
        | ANTI_DIMENSION
        | SYMMETRIC
        | TWO_DIMENSIONS
        | ANTI_TWO_DIMENSIONS
    )
    """The FeatureTypes using dimension values to define direction and end 
    condition.
    """
    CONDITION_TYPE = UP_TO_FIRST | UP_TO_LAST
    """The FeatureTypes using conditions to define direction and end condition.
    """
    END_FEATURE_TYPE = UP_TO_FACE | UP_TO_BODY
    """The FeatureTypes using conditions to define direction and end condition.
    """
    
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