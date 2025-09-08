"""A module providing a class to represent linear extrusions in 3D space 
starting from a sketch profile.
"""
from __future__ import annotations

import textwrap
from numbers import Real
from typing import NoReturn, overload, Self

from PanCAD.geometry import AbstractFeature, AbstractGeometry, Sketch
from PanCAD.geometry.constants import FeatureType
from PanCAD.utils.text_formatting import get_table_string

class Extrude(AbstractFeature):
    """A class representing linear extrusions starting from a sketch profile in 
    3D space. Extrusions in CAD programs often store suppressed information that 
    can be recalled later, such as when a two dimension extrusion is changed 
    to a one dimension extrusion and back again. Extrude also saves this 
    suppressed information and uses a FeatureType enumeration value to 
    determine which information is relevant currently.
    
    :param profile: The sketch defining the extrusion 2D shape.
    :param feature_type: The FeatureType defining the active direction(s) and 
        end conditions of the extrusion.
    :param uid: The unique id of the Extrude. Defaults to None.
    :param length: The length of the extrusion in the normal direction of the 
        plane of the profile sketch. Defaults to None.
    :param opposite_length: The length of the extrusion in the anti-normal 
        direction of the plane of the profile sketch. Defaults to None.
    :param is_midplane: Whether the length of the extrusion is actually 
        symmetric about its sketch profile midplane. Defaults to 'False'.
    :param is_reverse_direction: Whether the directions of length and 
        opposite_length are switched. Defaults to 'False'.
    :param end_feature: The face, feature, or body used by any end conditions 
        defined by features.
    :param unit: The unit of the length and opposite_length values. Defaults 
        to None.
    :param name: The name of the feature displayed to the users in CAD.
    :raises ValueError: Raised for 
        :attr:`~PanCAD.geometry.constants.FeatureType.DIMENSION_TYPE` extrudes 
        if it is midplane and also has an opposite length defined or if length 
        value is less than or equal to zero.
    """
    
    VALUE_STR_FORMAT = "{value}{unit}"
    
    # Feature Type Checking Class Constants #
    LENGTH_TYPE_ENUMS = (
        FeatureType.DIMENSION
        | FeatureType.ANTI_DIMENSION
        | FeatureType.SYMMETRIC
        | FeatureType.TWO_DIMENSIONS
        | FeatureType.ANTI_TWO_DIMENSIONS
    )
    CONDITION_TYPE_ENUMS = FeatureType.UP_TO_LAST | FeatureType.UP_TO_FIRST
    END_FEATURE_TYPE_ENUMS = FeatureType.UP_TO_FACE | FeatureType.UP_TO_BODY
    
    def __init__(self,
                 profile: Sketch,
                 feature_type: FeatureType,
                 uid: str=None,
                 length: Real=None,
                 opposite_length: Real=None,
                 is_midplane: bool=False,
                 is_reverse_direction: bool=False,
                 end_feature: object=None,
                 unit: str=None,
                 name: str=None,
                 context: AbstractFeature=None,) -> None:
        self.profile = profile
        self.feature_type = feature_type
        self.uid = uid
        self.length = length
        self.opposite_length  = opposite_length
        self.is_midplane = is_midplane
        self.is_reverse_direction = is_reverse_direction
        self.end_feature = end_feature
        self.unit = unit
        self.name = name
        self.context = context
        # if self.feature_type in self.LENGTH_TYPE_ENUMS:
        if self.feature_type in FeatureType.DIMENSION_TYPE:
            self._validate_length_extrude()
        elif self.feature_type in FeatureType.CONDITION_TYPE:
            raise NotImplementedError("Condition type extrudes have not"
                                      " yet been implemented")
        elif self.feature_type in FeatureType.END_FEATURE_TYPE:
            raise NotImplementedError("End feature type extrudes have not"
                                      " yet been implemented")
        else:
            raise ValueError(f"{feature_type} is not a valid extrude feature"
                             " type")
    
    # Class Methods #
    @overload
    @classmethod
    def from_length(cls,
                    profile: Sketch,
                    length: Real,
                    uid: str=None,
                    *,
                    is_reverse_direction: bool=False,
                    unit: str=None,
                    name: str=None,
                    context: AbstractFeature=None,) -> Self: ...
    
    @overload
    @classmethod
    def from_length(cls,
                    profile: Sketch,
                    length: Real,
                    uid: str=None,
                    *,
                    is_midplane: bool=False,
                    unit: str=None,
                    name: str=None,
                    context: AbstractFeature=None,) -> Self: ...
    
    @overload
    @classmethod
    def from_length(cls,
                    profile: Sketch,
                    length: Real,
                    uid: str=None,
                    *,
                    opposite_length: Real,
                    is_reverse_direction: bool=False,
                    unit: str=None,
                    name: str=None,
                    context: AbstractFeature=None,) -> Self: ...
    
    @classmethod
    def from_length(cls,
                    profile: Sketch,
                    length: Real,
                    uid: str=None,
                    *,
                    opposite_length: Real=None,
                    is_midplane: bool=False,
                    is_reverse_direction: bool=False,
                    unit: str=None,
                    name: str=None,
                    context: AbstractFeature=None,) -> Self:
        """Initializes an extrude from length dimensions. Determines the correct 
        FeatureType based on the input combination.
        
        :param profile: The sketch defining the extrusion 2D shape.
        :param uid: The unique id of the Extrude. Defaults to None.
        :param length: The length of the extrusion in the normal direction of 
            the plane of the profile sketch. Defaults to None.
        :param opposite_length: The length of the extrusion in the anti-normal 
            direction of the plane of the profile sketch. Defaults to None.
        :param is_midplane: Whether the length of the extrusion is actually 
            symmetric about its sketch profile midplane. Defaults to 'False'.
        :param is_reverse_direction: Whether the directions of length and 
            opposite_length are switched. Defaults to 'False'.
        :param unit: The unit of the length and opposite_length values. Defaults 
            to None.
        :raises ValueError: Raised if length or opposite_length are given as 
            non-Reals.
        """
        if is_midplane:
            feature_type = FeatureType.SYMMETRIC
        elif opposite_length is None:
            if is_reverse_direction:
                feature_type = FeatureType.ANTI_DIMENSION
            else:
                feature_type = FeatureType.DIMENSION
        elif (isinstance(opposite_length, Real)
                and isinstance(length, Real)):
            if is_reverse_direction:
                feature_type = FeatureType.ANTI_TWO_DIMENSIONS
            else:
                feature_type = FeatureType.TWO_DIMENSIONS
        else:
            raise ValueError("length and opposite_length must be numbers,"
                             f" given {length} and {opposite_length}")
        return cls(profile,
                   feature_type,
                   uid,
                   length,
                   opposite_length,
                   is_midplane,
                   is_reverse_direction,
                   end_feature=None,
                   unit=unit,
                   name=name,
                   context=context,)
    
    @classmethod
    def from_end_condition(cls,
                           profile: Sketch,
                           end_type: FeatureType,
                           *,
                           is_reverse_direction: bool=False,
                           uid: str=None) -> Self:
        raise NotImplementedError("End condition extrude not yet implemented,"
                                  " see issue #61")
    
    @classmethod
    def from_end_feature(cls,
                         profile: Sketch,
                         end_feature: object,
                         *,
                         is_reverse_direction: bool=False,
                         uid: str=None) -> Self:
        raise NotImplementedError("End condition extrude not yet implemented,"
                                  " see issues #63 and #64")
    
    # Getters #
    @property
    def context(self) -> AbstractFeature | None:
        return self._context
    
    # Setters #
    @context.setter
    def context(self, context_feature: AbstractFeature | None) -> None:
        self._context = context_feature
    
    # Public Methods #
    def get_dependencies(self) -> tuple[AbstractFeature | AbstractGeometry]:
        if self.end_feature is not None:
            return (self.profile, self.end_feature)
        else:
            return (self.profile,)
    
    def get_length_string(self) -> str:
        """Return length value with the associated unit."""
        return self._get_value_string(self.length)
    
    def get_opposite_length_string(self) -> str:
        """Return opposite length value with the associated unit."""
        return self._get_value_string(self.opposite_length)
    
    # Private Methods #
    def _get_value_string(self, value: Real | None) -> str:
        """Returns a string of the constraint's value with the constraint's 
        unit. If the unit is None, then this just returns the value as a string.
        """
        if value is None:
            return ""
        elif self.unit is None:
            return str(value)
        else:
            return self.VALUE_STR_FORMAT.format(value=value, unit=self.unit)
    
    def _validate_length_extrude(self) -> NoReturn:
        """Checks whether a length extrude's parameters conflict or if they are 
        invalid values.
        """
        if self.is_midplane and self.opposite_length is not None:
            raise ValueError("Opposite length cannot be defined for midplane"
                             " extrudes")
        elif self.length < 0:
            raise ValueError("Length cannot be negative")
        elif self.length == 0:
            raise ValueError("Length cannot be 0")
    
    # Python Dunders #
    def __repr__(self) -> str:
        return (f"<PanCAD_{repr(self.feature_type)}_Extrude'{self.uid}'"
                f"p'{self.profile.uid}'>")
    
    def __str__(self) -> str:
        type_name = self.feature_type.name \
                                     .replace("_", " ") \
                                     .title()
        if self.end_feature is None:
            end_feature_uid = None
        else:
            end_feature_uid = self.end_feature.uid
        summary = []
        summary.append(f"Extrude '{self.uid}' of profile '{self.profile.uid}'")
        summary_info = {
            "Active Type": type_name,
            "Length": self.get_length_string(),
            "Opposite Length": self.get_opposite_length_string(),
            "Midplane": self.is_midplane,
            "Reversed": self.is_reverse_direction,
        }
        summary.append(
            textwrap.indent(get_table_string(summary_info), "  ")
        )
        return "\n".join(summary)