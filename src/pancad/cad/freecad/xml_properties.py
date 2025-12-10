"""A module providing functions for reading FreeCAD xml properties from its save 
files without the FreeCAD Python API.
"""
from __future__ import annotations

import logging
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

from pancad import resources

from .constants.archive_constants import (
    App,
    Attr,
    Materials,
    Part,
    PropertyType,
    Sketcher,
    Tag,
)

if TYPE_CHECKING:
    from typing import Any
    from xml.etree.ElementTree import Element

logger = logging.getLogger(__name__)

FreecadPropertyValueType = (
    str
    | list[str]
    | dict[str, str | None | list[dict[str, str]] | list[str]]
)
"""The possible return types from the read_property_value function."""

### Configuration
def _xml_config() -> dict[str, str]:
    """Returns the xml configuration dict of the freecad.toml file."""
    FREECAD_TOML = Path(resources.__file__).parent / "freecad.toml"
    with open(FREECAD_TOML, "rb") as file:
        return tomllib.load(file)["xml"]

### Type Readers
def _read_bad_type(element: Element) -> list[dict[str, str]]:
    """Reads BadType typed elements, which appears to be some form of FreeCAD 
    file error. Only been seen on VisualLayerList elements.
    
    :raises FreecadUnknownBadTypeTag: Raised when the first subelement is not 
        VisualLayerList.
    """
    layer_list = element[0]
    if layer_list.tag != Tag.VISUAL_LAYER_LIST:
        raise FreecadUnknownBadTypeTag(f"Unexpected tag: {element.tag}")
    return [dict(list_.attrib) for list_ in layer_list.iter(Tag.VISUAL_LAYER)]

def _read_single(element: Element) -> str:
    """Reads the value from of the element nested in a property to a string."""
    for attr, value in dict(element[0].attrib).items():
        return value

def _read_enum(element: Element) -> str:
    """Returns the custom enumeration str or the selection integer as a str."""
    selection = element.find(Tag.INTEGER).attrib[Attr.VALUE]
    if (enum_list := element.find(Tag.CUSTOM_ENUM_LIST)) is not None:
        return enum_list[int(selection)].attrib[Attr.VALUE]
    else:
        return selection

def _read_constraint_list(element: Element) -> list[dict[str, str]]:
    """Reads all constraint properties into a dict list. Also adds the list name 
    and respective index based on the appearance order for each constraint.
    """
    fields = _xml_config()["pancad"]["fields"]
    
    list_name = element.get(Attr.NAME)
    data = []
    for i, constraint in enumerate(element.find(Tag.CONSTRAINT_LIST)):
        data.append(
            {
                fields["list_name"]: list_name,
                fields["list_index"]: str(i),
                **constraint.attrib,
            }
        )
    return data

def _read_geometry_list(element: Element) -> list[dict[str, str]]:
    """Reads geometry properties into a dict list. Also adds the list name and 
    respective index based on the appearance order for each geometry.
    """
    config = _xml_config()
    xpaths = config["xpaths"]
    fields = config["pancad"]["fields"]
    
    NON_GEOMETRY_TAGS = {Tag.GEOMETRY_EXTENSIONS, Tag.CONSTRUCTION}
    EXT_IGNORE_ATTR = [Attr.TYPE, Attr.ID]
    list_name = element.get(Attr.NAME)
    
    geometries = []
    geometry_list = element.find(Tag.GEOMETRY_LIST)
    sketch_ext_xpath = xpaths["GEOMETRY_EXT"].format(Sketcher.GEOMETRY_EXT)
    
    for list_index, geometry in enumerate(geometry_list):
        geometry_tag = ({sub.tag for sub in geometry} - NON_GEOMETRY_TAGS).pop()
        info = {fields["list_name"]: list_name,
                fields["list_index"]: str(list_index)}
        info.update(geometry.find(sketch_ext_xpath).attrib)
        info.update(geometry.attrib) # Overwrites SketchExt id and type
        info[Tag.CONSTRUCTION] = geometry.find(Tag.CONSTRUCTION).get(Attr.VALUE)
        info.update(geometry.find(geometry_tag).attrib)
        geometries.append(info)
    return geometries

def _read_link_sub(element: Element) -> dict[str, str]:
    """Reads LinkSub elements to a dict"""
    link_sub = element.find(Tag.LINK_SUB)
    return {
        Attr.NAME: link_sub.get(Attr.VALUE),
        Tag.SUB: [dict(sub.attrib) for sub in link_sub],
    }

def _read_multi_subelement_to_dicts(element: Element) -> list[dict[str, str]]:
    """Reads each subelement attrib dict into a dict list"""
    subelements = []
    for subelement in element[0]:
        subelements.append(dict(subelement.attrib))
    return subelements

def _read_part_shape(element: Element) -> dict[str, str | None]:
    """Reads the varying structure of a Part::PropertyPartShape element into a 
    consistently labeled dictionary.
    """
    PART_MAP = {
        Attr.HASHER_INDEX: Attr.HASHER_INDEX,
        Attr.ELEMENT_MAP: "_".join([Attr.ELEMENT_MAP, Tag.PART]),
        Attr.FILE: "_".join([Attr.FILE, Tag.PART])
    }
    MAP_2_MAP = {Attr.FILE: "_".join([Attr.FILE, Tag.ELEMENT_MAP_2]),}
    part_dict = {}
    map_2_dict = {}
    
    if (part := element.find(Tag.PART)) is not None:
        part_dict = dict(part.attrib)
    if (map_2 := element.find(Tag.ELEMENT_MAP_2)) is not None:
        map_2_dict = dict(map_2.attrib)
    
    elements = []
    if (element_map := element.find(Tag.ELEMENT_MAP)) is not None:
        for mapped in element_map:
            elements.append(dict(mapped.attrib))
    
    return {
        **{new: part_dict.setdefault(old) for old, new in PART_MAP.items()},
        **{new: map_2_dict.setdefault(old) for old, new in MAP_2_MAP.items()},
        Tag.ELEMENT_MAP: elements,
    }

def _read_subelement_list(element: Element) -> list[str]:
    """Returns each subelement value in a nested list"""
    values = []
    for list_element in element[0]:
        for _, value in dict(list_element.attrib).items():
            values.append(value)
            break
    return values

def _read_subelement_attrib_to_dict(element: Element) -> dict[str, str]:
    """Returns the single subelement's attributes as a dict."""
    return dict(element[0].attrib)

### Property Reading
PROPERTY_DISPATCH = { 
    App.ANGLE: _read_single,
    App.BOOL: _read_single,
    App.COLOR: _read_single,
    App.COLOR_LIST: _read_single,
    App.ENUM: _read_enum,
    App.EXPRESSION_ENGINE: _read_multi_subelement_to_dicts,
    App.FLOAT: _read_single,
    App.FLOAT_CONSTRAINT: _read_single,
    App.LENGTH: _read_single,
    App.LINK: _read_single,
    App.LINK_SUB: _read_link_sub,
    App.LINK_SUBLIST: _read_multi_subelement_to_dicts,
    App.LINK_LIST: _read_subelement_list,
    App.LINK_LIST_HIDDEN: _read_subelement_list,
    App.MATERIAL: _read_subelement_attrib_to_dict,
    App.MATERIAL_LIST: _read_subelement_attrib_to_dict,
    App.PLACEMENT: _read_subelement_attrib_to_dict,
    App.PYTHON_OBJECT: _read_subelement_attrib_to_dict,
    App.PERCENT: _read_single,
    App.PRECISION: _read_single,
    App.VECTOR: _read_subelement_attrib_to_dict,
    App.STRING: _read_single,
    App.UUID: _read_single,
    
    Materials.MATERIAL: _read_single,
    
    PropertyType.BAD_TYPE: _read_bad_type,
    
    Part.GEOMETRY_LIST: _read_geometry_list,
    Part.SHAPE: _read_part_shape,
    
    Sketcher.CONSTRAINT_LIST: _read_constraint_list,
}
"""A dict matching xml types to their respective parsing function calls."""

def read_property_value(element: Element) -> FreecadPropertyValueType:
    """Reads the values associated with a Property element.
    
    :param element: A Property element.
    :raises FreecadPropertyParseError: When a property type was recognized but 
        could not be parsed.
    :raises FreecadUnsupportedPropertyError: When an unknown property type is 
        encountered.
    """
    type_ = element.attrib[Attr.TYPE]
    try:
        value = PROPERTY_DISPATCH[type_](element)
        return value
    except FreecadUnknownBadTypeTag as err:
        name = element.get(Attr.NAME)
        logger.error(f"Could not read '{name}' BadType unknown tag: {err}")
        raise FreecadPropertyParseError(f"'{name}' typed '{type_}'", str(err))
    except KeyError as err:
        name = element.get(Attr.NAME)
        raise FreecadUnsupportedPropertyError(f"'{name}' typed {err}")
    except Exception as err:
        name = element.get(Attr.NAME)
        raise FreecadPropertyParseError(f"'{name}' typed '{type_}'", str(err))

### Exceptions
class FreecadUnknownBadTypeTag(ValueError):
    """Raised when a BadType typed element is encountered with an unknown tag."""

class FreecadUnsupportedPropertyError(KeyError):
    """Raised when a property can't be read from a FreeCAD file because it hasn't 
    been supported.
    """

class FreecadPropertyParseError(ValueError):
    """Raised when a property can't be read from a FreeCAD file because an error 
    was encountered while reading its value.
    """

# Possible Future implementation for color reading:
# ARGB = namedtuple("ARGB", ["a", "r", "g", "b"])
# """Typing for alpha red blue green color data"""
# def unpack_argb(packed: int) -> ARGB:
    # """Returns a tuple of ARGB values from an integer."""
    # return ARGB(*[(packed >> shift_by) & 0xFF for shift_by in [24, 16, 8, 0]])

# def _read_color(element: Element) -> tuple[int, int, int, int]:
    # """Returns the ARGB values from the integer in the element as a tuple."""
    # if len(element) != 1: raise ValueError(f"Found {len(element)}")
    # ARGB = namedtuple("ARGB", ["a", "r", "g", "b"])
    # integer = int(element.find(Tag.PROPERTY_COLOR).attrib[Attr.VALUE])
    # return unpack_argb(integer)