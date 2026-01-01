"""A module providing a class to represent linear extrusions in 3D space 
starting from a sketch profile.
"""
from __future__ import annotations

import dataclasses
from numbers import Real
from textwrap import indent
from typing import TYPE_CHECKING

from pancad.geometry import AbstractFeature
from pancad.geometry.constants import FeatureType
from pancad.utils.text_formatting import get_table_string

if TYPE_CHECKING:
    from typing import NoReturn, Self
    from pancad.geometry import AbstractGeometry, Sketch

@dataclasses.dataclass
class ExtrudeSettings:
    """A dataclass containing the constant settings for an Extrude feature.
    
    :param type_: The active type of the Extrude that sets whether the extrude 
        is linear, midplane, etc.
    :param length: The length of the Extrude when a static length is active.
    :param opposite_length: The opposite length of the Extrude when a static 
        opposite length is active. Ignored if the Extrude is midplane.
    :param unit: The unit of the Extrude's length values.
    :param name: The name of the feature displayed to the users in CAD.
    :raises ValueError: When a negative number is provided for length or 
        opposite_length.
    """
    type_: FeatureType
    length: Real = 0
    opposite_length: Real = 0
    unit: str = None
    name: str = "Extrude" # TODO: Add a way to set default names in config
    def __post_init__(self):
        if self.name is None:
            self.name = "Extrude" # Has to be synced with name field
        if self.length < 0:
            raise ValueError(f"length cannot be <0, got {self.length}")
        if self.opposite_length < 0:
            raise ValueError("opposite_length cannot be <0,"
                             f" got {self.opposite_length}")
        if self.type_ in [FeatureType.UP_TO_LAST, FeatureType.UP_TO_FIRST]:
            raise NotImplementedError("Condition Extrudes not supported yet")
        if self.type_ in [FeatureType.UP_TO_FACE, FeatureType.UP_TO_BODY]:
            raise NotImplementedError("End Feature Extrudes not supported yet")

class Extrude(AbstractFeature):
    """A class representing linear extrusions starting from a sketch profile in 
    3D space. Extrusions in CAD programs often store suppressed information that 
    can be recalled later, such as when a two dimension extrusion is changed 
    to a one dimension extrusion and back again. Extrude also saves this 
    suppressed information and uses a FeatureType enumeration value to 
    determine which information is relevant currently.
    
    :param profile: The sketch defining the extrusion 2D shape.
    :param settings: The constant settings of the Extrude, stored inside a 
        ExtrudeSettings dataclass.
    :param uid: The unique id of the Extrude. When set to None the uid is 
        automatically generated.
    :param context: The feature that acts as the context for this feature, 
        usually a :class:`~pancad.geometry.FeatureContainer`
    """
    VALUE_STR_FORMAT = "{value}{unit}"
    # Feature Type Checking Class Constants #
    def __init__(self, profile: Sketch, settings: ExtrudeSettings,
                 *, uid: str=None, context: AbstractFeature=None) -> None:
        self.profile = profile
        self.settings = settings
        self.uid = uid
        self.context = context

    # Class Methods #
    @classmethod
    def from_length(cls, profile: Sketch, length: Real, *,
                    context: AbstractFeature=None, uid: str=None,
                    **settings) -> Self:
        """Initializes a linear extrude from length dimensions.
        
        :param profile: The sketch defining the extrusion 2D shape.
        :param length: The length of the extrusion the direction specified by 
            the extrusion type relative to the profile sketch.
        :param uid: The unique id of the Extrude. Defaults to None.
        :param context: The feature that acts as the context for this feature, 
            usually a :class:`~pancad.geometry.FeatureContainer`
        :param settings: See :class:`~pancad.geometry.extrude.ExtrudeSettings` 
            for additional keyword arguments. If the 'type_' setting is not 
            provided, it's assumed to be FeatureType.DIMENSION.
        """
        type_ = settings.setdefault("type_", FeatureType.DIMENSION)
        if type_ not in FeatureType.SINGLE_DIMENSION:
            raise TypeError(f"type_ '{type_}' needs more than one length.")
        settings.pop("type_", None)
        return cls(profile, ExtrudeSettings(type_, length, **settings),
                   uid=uid, context=context)

    # Properties #
    @property
    def context(self) -> AbstractFeature | None:
        return self._context
    @context.setter
    def context(self, feature: AbstractFeature | None) -> None:
        self._context = feature

    @property
    def length(self) -> Real:
        """The linear length of the extrude in its normal direction."""
        return self.settings.length
    @length.setter
    def length(self, value: Real) -> None:
        self.settings = dataclasses.replace(self.settings, length=value)

    @property
    def name(self) -> str:
        return self.settings.name
    @name.setter
    def name(self, value: str) -> None:
        self.settings = dataclasses.replace(self.settings, name=value)

    @property
    def opposite_length(self) -> Real:
        """The linear length of the extrude opposite its normal direction."""
        return self.settings.opposite_length
    @opposite_length.setter
    def opposite_length(self, value: Real) -> None:
        self.settings = dataclasses.replace(self.settings, opposite_length=value)

    @property
    def type_(self) -> FeatureType:
        """The active type of extrusion method."""
        return self.settings.type_
    @type_.setter
    def type_(self, value: FeatureType) -> None:
        self.settings = dataclasses.replace(self.settings, type_=value)

    @property
    def unit(self) -> str | None:
        """The unit of the Extrude's length values."""
        return self.settings.unit
    @unit.setter
    def unit(self, value: str) -> None:
        self.settings = dataclasses.replace(self.unit, unit=value)

    # Public Methods #
    def get_dependencies(self) -> tuple[AbstractFeature | AbstractGeometry]:
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
        if self.unit is None:
            return str(value)
        return self.VALUE_STR_FORMAT.format(value=value, unit=self.unit)

    # Python Dunders #
    def __repr__(self) -> str:
        return f"<pancad{repr(self.type_)}Extrude'{self.name}'>"

    def __str__(self) -> str:
        type_name = self.type_.name \
                              .replace("_", " ") \
                              .title()
        summary = []
        summary.append(f"Extrude '{self.name}' of profile '{self.profile.uid}'")
        summary_info = {
            "Active Type": type_name,
            "Length": self.get_length_string(),
            "Opposite Length": self.get_opposite_length_string(),
        }
        summary.append(indent(get_table_string(summary_info), "  "))
        return "\n".join(summary)
