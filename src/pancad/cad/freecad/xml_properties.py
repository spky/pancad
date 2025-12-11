"""A module providing functions for reading FreeCAD xml properties from its save 
files without the FreeCAD Python API.
"""
from __future__ import annotations

from functools import cache
import logging
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

from pancad import resources

from .constants.archive_constants import Attr, Sketcher, Tag

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any
    from xml.etree.ElementTree import Element

logger = logging.getLogger(__name__)

FreecadPropertyValueType = (
    str
    | list[str]
    | dict[str, str | None | list[dict[str, str]] | list[str]]
)
"""The possible return types from the read_property_value function."""

### Property Reading
def read_property_value(element: Element) -> FreecadPropertyValueType:
    """Reads the values associated with a Property element.
    
    :param element: A Property element.
    :raises FreecadPropertyParseError: When a property type was recognized but 
        could not be parsed.
    :raises FreecadUnsupportedPropertyError: When an unknown property type is 
        encountered.
    """
    type_ = element.attrib[Attr.TYPE]
    dispatch = _property_dispatch()
    try:
        value = dispatch[type_](element)
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

### Configuration
@cache
def _xml_config() -> dict[str, str]:
    """Returns the xml configuration dict of the freecad.toml file."""
    FREECAD_TOML = Path(resources.__file__).parent / "freecad.toml"
    with open(FREECAD_TOML, "rb") as file:
        return tomllib.load(file)["xml"]

@cache
def _property_dispatch() -> dict[str, Callable[Element]]:
    """Returns a dict mapping xml types to their respective parsing function."""
    PARSERS = {
        "bad_type": _read_bad_type,
        "enum": _read_enum,
        "constraint_list": _read_constraint_list,
        "geometry_list": _read_geometry_list,
        "link_sub": _read_link_sub,
        "multi_subelement_to_dicts": _read_multi_subelement_to_dicts,
        "part_shape": _read_part_shape,
        "single": _read_single,
        "subelement_attrib_to_dict": _read_subelement_attrib_to_dict,
        "subelement_list": _read_subelement_list,
    }
    dispatch = {}
    for format_category, types in _xml_config()["pancad"]["dispatch"].items():
        for type_ in types:
            dispatch[type_] = PARSERS[format_category]
    return dispatch

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