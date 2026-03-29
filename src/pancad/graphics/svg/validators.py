"""A module providing functions and regular expressions to verify svg syntax
since errors won't appear until the user tries to open it with inkscape or a
browser.
"""

import re
from numbers import Real

from pancad.graphics.svg.constants import Color

FLOAT_RE = r"[+-]?[0-9]*\.[0-9]+"
INTEGER_RE = "[+-]?[0-9]+"
NUMBER_RE = "(" + FLOAT_RE + "|" + INTEGER_RE + ")"
HEX_6_COLOR_RE = "#[0-9A-Fa-f]{6}"
HEX_3_COLOR_RE = "#[0-9A-Fa-f]{3}"
RGB_NUMBER_RE = r"[rR][gG][bB]\([0-9]{1,3},[0-9]{1,3},[0-9]{1,3}\)"
RGB_PERCENT_RE = r"[rR][gG][bB]\([0-9]{1,3}%,[0-9]{1,3}%,[0-9]{1,3}%\)"
STYLE_LENGTH_UNITS_RE = "(em|ex|px|in|cm|mm|pt|pc)"
PRESENTATION_LENGTH_UNITS_RE = "(em|ex|px|in|cm|mm|pt|pc|%)"
LENGTH_RE = "^" + NUMBER_RE + PRESENTATION_LENGTH_UNITS_RE + "?$"

def number(setting: str | Real) -> str:
    """Returns the setting after checking whether it is a number"""
    setting = str(setting)
    if re.match("^" + NUMBER_RE + "$", setting):
        return setting
    raise ValueError(setting + " does not match svg number format")

def stroke_linecap(setting: str) -> str:
    """Returns the setting after checking that it meets the rules for
    a stroke-linecap svg setting. If the setting is not butt, round,
    square, or inherit, it will raise a ValueError

    :param setting: the setting to set an svg stroke-linecap setting.
    :returns: echos back the setting
    """
    allowable_values = [ "butt", "round", "square", "inherit"]
    if setting not in allowable_values:
        raise ValueError(f"stroke-linecap '{setting}' is not in allowable"
                         + f" values: {allowable_values}")
    return setting

def stroke_linejoin(setting: str) -> str:
    """Returns the setting after checking that it meets the rules for
    a stroke-linejoin svg setting. If the setting is not miter,
    round, bevel, or inherit, it will raise a ValueError

    :param setting: the setting to set an svg stroke-linejoin setting.
    :returns: echos back the setting
    """
    allowable_values = [ "miter", "round", "bevel", "inherit"]
    if setting not in allowable_values:
        raise ValueError(f"stroke-linejoin '{setting}' is not in allowable"
                         + f" values: {allowable_values}")
    return setting

def stroke_opacity(setting: Real) -> str:
    """Returns the setting after checking that it meets the rules for
    a stroke-opacity svg setting. If the setting is not between 0 and
    1 or is not a float/int, it will raise a ValueError.

    :param setting: the setting to set an svg stroke-linejoin setting.
    :returns: echos back the setting after converting to str
    """
    if setting in ["inherit"]:
        return setting
    if isinstance(setting, Real):
        # Clamps value to be 0 or 1 if outside that range
        return str(sorted((0, setting, 1))[1])
    raise ValueError(f"'{setting}' is not a recognized opacity format")

def color(setting: str) -> str:
    """Returns the setting as is after checking that it meets the rules
    for svg colors. This function is intended to be used to feed into
    another setting function, ex: fill, stroke, etc. If it does not meet
    the rules for svg color input, it will raise a ValueError.

    :param setting: the color setting in hex, rgb, or svg color keyword format
    :returns: the color setting
    """
    if re.match(r"^" + HEX_6_COLOR_RE + "$", setting):
        return setting
    if re.match(r"^" + HEX_3_COLOR_RE + "$", setting):
        return setting
    if re.match(r"^" + RGB_NUMBER_RE + "$", setting):
        rgb_vals = setting[4:-1]
        rgb_vals = rgb_vals.split(",")
        for val in rgb_vals:
            if int(val) > 255:
                raise ValueError(f"Provided value of '{setting}' has rgb >255")
        return setting
    if re.match(r"^" + RGB_PERCENT_RE + "$", setting):
        rgb_vals = setting[4:-1]
        rgb_vals = rgb_vals.replace("%","")
        rgb_vals = rgb_vals.split(",")
        for val in rgb_vals:
            if int(val) > 100:
                raise ValueError(f"Provided value of '{setting}' has rgb >100%")
        return setting
    if setting.upper() in Color.__members__:
        return setting
    raise ValueError(f"Color '{setting}' is not in a recognized format")

def paint(setting: str) -> str:
    """Returns a paint setting as is after checking that it meets svg
    paint rules. If it does not meet the rules for svg paint input, it will
    raise a ValueError.

    :param setting: the paint setting
    :returns: echos back the setting
    """
    if setting in {"none", "currentColor"}:
        return setting
    return color(setting)

def percentage(setting: str) -> str:
    """Returns a percentage setting as is after checking that it meets svg
    percentage rules. If it does not meet the rules for svg percentage
    input, it will raise a ValueError.

    :param setting: the percentage setting
    :returns: echos back the setting
    """
    setting = str(setting)
    if re.match("^" + NUMBER_RE + "%$", setting):
        return setting
    raise ValueError(f"'{setting}' is not svg 1.1 <percentage> formatted")

def stroke_width(setting: str | Real) -> str:
    """Returns the setting after checking that the value is greater
    than 0 and that the unit is em, ex, px, in, cm, mm, pt, or pc

    :param setting: the setting to set an svg stroke-width setting.
    :returns: echos back the setting
    """
    if length_value(setting) < 0:
        raise ValueError("Provided length value '"
                         + setting
                         + "' must be greater than 0")
    return length(setting)

def length(setting: str) -> str:
    """Returns the setting as is or after turning it to a string after
    checking that it fulfills the svg length requirements

    | Valid Units:
    | em = relative top the font-size of the element
    | ex = relative to the x-height of the current font
    | px = pixels, where 1px = 1/96th of 1 inch
    | in = inches
    | cm = centimeters
    | mm = millimeters
    | pt = points, where 1pt = 1/72 of 1 inch
    | pc = picas where 1pc = 12pt
    | None = not recommended, svg 1.1 spec says that it represents a
      distance in the current user coordinate system. This is the only
      unit available if setting is a int or float

    :param setting: the setting to set an svg length setting.
    :returns: echos back the setting as a string
    """
    setting = str(setting)
    if re.match(LENGTH_RE, setting):
        return setting
    raise ValueError(f"'{setting}' is not svg 1.1 <length> format")

def length_value(setting: str) -> Real:
    """Returns just the number of the given length without the unit.

    :param setting: the setting to set an svg length setting.
    :returns: the number value of the setting as a float or int
    """
    setting = length(setting)
    length_match = re.match(LENGTH_RE, setting)
    if not length_match:
        raise ValueError(f"Format of '{setting}' is not recognized")
    setting = length_match[1] # Isolate numerical value
    if re.match(r"^" + FLOAT_RE + "$", setting):
        return float(setting)
    return int(setting)

def length_unit(setting: str | Real) -> str:
    """Returns just the unit of the given length without the value.
    If an int, float, or number represented as a string is given
    this returns "". If the given value is just a unit string like
    "in", then it checks that the unit is a valid unit and echos
    it back

    :param setting: an svg 1.1 length setting or svg 1.1 unit string
    :returns: the unit of the setting
    """
    setting = str(setting)
    if setting == "":
        return ""
    if re.match("^" + PRESENTATION_LENGTH_UNITS_RE + "$", setting):
        return setting
    setting = length(setting)

    if re.match("^" + NUMBER_RE + "$", setting):
        return ""
    if re.match("^" + NUMBER_RE + PRESENTATION_LENGTH_UNITS_RE + "$",
                  setting):
        return re.search(PRESENTATION_LENGTH_UNITS_RE, setting)[0]
    msg = f"'{setting}' is an unrecognized format that passed length's check"
    raise ValueError(msg)
