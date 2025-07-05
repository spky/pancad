"""A module providing a class to represent linear extrusions in 3D space 
starting from a sketch profile.
"""
from __future__ import annotations

from PanCAD.geometry import Sketch
from PanCAD.geometry.constants import FeatureType

class Extrude:
    """A class representing linear extrusions starting from a sketch profile in 
    3D space.
    """
    
    # Feature Type Checking Class Constants #
    LENGTH_TYPE_ENUMS = (
        FeatureType.DIMENSION | FeatureType.ANTI_DIMENSION
        | FeatureType.SYMMETRIC
        | FeatureType.TWO_DIMENSIONS | FeatureType.ANTI_TWO_DIMENSIONS
    )
    CONDITION_TYPE_ENUMS = FeatureType.UP_TO_LAST | FeatureType.UP_TO_FIRST
    END_FEATURE_TYPE_ENUMS = FeatureType.UP_TO_FACE | FeatureType.UP_TO_BODY
    
    def __init__(self, profile: Sketch, feature_type: FeatureType,
                 uid: str=None,
                 length: int | float=None,
                 opposite_length: int | float=None,
                 is_midplane: bool=False,
                 is_reverse_direction: bool=False,
                 end_feature: object=None):
        self.profile = profile
        self.feature_type = feature_type
        self.uid = uid
        self.length = length
        self.opposite_length  = opposite_length
        self.is_midplane = is_midplane
        self.is_reverse_direction = is_reverse_direction
        self.end_feature = end_feature
        if self.feature_type in self.LENGTH_TYPE_ENUMS:
            self._validate_length_extrude()
        elif self.feature_type in self.CONDITION_TYPE_ENUMS:
            raise NotImplementedError("Condition type extrudes have not"
                                      " yet been implemented")
        elif self.feature_type in self.END_FEATURE_TYPE_ENUMS:
            raise NotImplementedError("End feature type extrudes have not"
                                      " yet been implemented")
        else:
            raise ValueError(f"{feature_type} is not a valid extrude feature"
                             " type")
    
    # Public Methods #
    def get_dependencies(self) -> tuple:
        if self.end_feature is not None:
            return (self.profile, self.end_feature)
        else:
            return (self.profile,)
    
    # Class Methods #
    @classmethod
    def from_length(cls,
                    profile: Sketch,
                    length: int | float,
                    uid: str=None,
                    *,
                    opposite_length: int | float=None,
                    is_midplane: bool=False,
                    is_reverse_direction: bool=False) -> Extrude:
        if is_midplane:
            feature_type = FeatureType.SYMMETRIC
        elif opposite_length is None:
            if is_reverse_direction:
                feature_type = FeatureType.ANTI_DIMENSION
            else:
                feature_type = FeatureType.DIMENSION
        elif (isinstance(opposite_length, (int, float))
                and isinstance(length, (int, float))):
            if is_reverse_direction:
                feature_type = FeatureType.ANTI_TWO_DIMENSIONS
            else:
                feature_type = FeatureType.TWO_DIMENSIONS
        else:
            raise ValueError("length and opposite_length must be numbers,"
                             f" given {length} and {opposite_length}")
        return cls(profile, feature_type, uid,
                   length, opposite_length,
                   is_midplane, is_reverse_direction, end_feature=None)
    
    @classmethod
    def from_end_condition(cls,
                           profile: Sketch,
                           end_type: FeatureType,
                           *,
                           is_reverse_direction: bool=False,
                           uid: str=None) -> Extrude:
        raise NotImplementedError("End condition extrude not yet implemented")
    
    @classmethod
    def from_end_feature(cls,
                         profile: Sketch,
                         end_feature: object,
                         *,
                         is_reverse_direction: bool=False,
                         uid: str=None) -> Extrude:
        raise NotImplementedError("End feature extrude not yet implemented")
    
    # Private Methods #
    def _validate_length_extrude(self):
        if self.is_midplane and self.opposite_length is not None:
            raise ValueError("Opposite length cannot be defined for midplane"
                             " extrudes")
        elif self.length < 0:
            raise ValueError("Length cannot be negative")
        elif self.length == 0:
            raise ValueError("Length cannot be 0")
    
    # Python Dunders #
    def __repr__(self) -> str:
        """Returns the short string representation of the extrude"""
        return (f"<PanCAD_{repr(self.feature_type)}_Extrude'{self.uid}'"
                f"p'{self.profile.uid}'>")
    
    def __str__(self) -> str:
        """Returns the longer string representation of the extrude"""
        type_name = self.feature_type.name \
                                     .replace("_", " ") \
                                     .title()
        return (f"PanCAD {type_name} Extrude '{self.uid}'"
                f" with profile '{self.profile.uid}'")