"""A module providing functions and regular expressions to verify svg syntax 
since errors won't appear until the user tries to open it with inkscape or a 
browser.
"""

import re

from PanCAD.graphics.svg import enum_color_keywords

float_re = "[+-]?[0-9]*\.[0-9]+"
integer_re = "[+-]?[0-9]+"
number_re = "(" + float_re + "|" + integer_re + ")"
hex_6_color_re = "#[0-9A-Fa-f]{6}"
hex_3_color_re = "#[0-9A-Fa-f]{3}"
rgb_number_re = "[rR][gG][bB]\([0-9]{1,3},[0-9]{1,3},[0-9]{1,3}\)"
rgb_percent_re = "[rR][gG][bB]\([0-9]{1,3}%,[0-9]{1,3}%,[0-9]{1,3}%\)"
style_length_units_re = "(em|ex|px|in|cm|mm|pt|pc)"
presentation_length_units_re = "(em|ex|px|in|cm|mm|pt|pc|%)"
length_re = "^" + number_re + presentation_length_units_re + "?$"

def number(setting: str | int | float) -> str:
    """Returns the setting after checking whether it is a number"""
    setting = str(setting)
    if re.match("^" + number_re + "$", setting):
        return setting
    else:
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
    else:
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
    else:
        return setting

def stroke_opacity(setting: float | str) -> str:
    """Returns the setting after checking that it meets the rules for 
    a stroke-opacity svg setting. If the setting is not between 0 and 
    1 or is not a float/int, it will raise a ValueError.
    
    :param setting: the setting to set an svg stroke-linejoin setting.
    :returns: echos back the setting after converting to str
    """
    if setting in ["inherit"]:
        return setting
    elif isinstance(setting, float) or isinstance(setting, int):
        # Clamps value to be 0 or 1 if outside that range
        return str(sorted((0, setting, 1))[1])
    else:
        raise ValueError(f"'{setting}' is not a recognized opacity format")

def color(setting: str) -> str:
    """Returns the setting as is after checking that it meets the rules 
    for svg colors. This function is intended to be used to feed into 
    another setting function, ex: fill, stroke, etc. If it does not meet 
    the rules for svg color input, it will raise a ValueError.
    
    :param setting: the color setting in hex, rgb, or svg color keyword format
    :returns: the color setting
    """
    if re.match(r"^" + hex_6_color_re + "$", setting):
        return setting
    elif re.match(r"^" + hex_3_color_re + "$", setting):
        return setting
    elif re.match(r"^" + rgb_number_re + "$", setting):
        rgb_vals = setting[4:-1]
        rgb_vals = rgb_vals.split(",")
        for val in rgb_vals:
            if int(val) > 255:
                raise ValueError(f"Provided value of '{setting}' has rgb >255")
        return setting
    elif re.match(r"^" + rgb_percent_re + "$", setting):
        rgb_vals = setting[4:-1]
        rgb_vals = rgb_vals.replace("%","")
        rgb_vals = rgb_vals.split(",")
        for val in rgb_vals:
            if int(val) > 100:
                raise ValueError(f"Provided value of '{setting}' has rgb >100%")
        return setting
    elif setting in enum_color_keywords.Color.__members__:
        return setting
    else:
        raise ValueError(f"Color '{setting}' is not in a recognized format")

def paint(setting: str) -> str:
    """Returns a paint setting as is after checking that it meets svg 
    paint rules. If it does not meet the rules for svg paint input, it will 
    raise a ValueError.
    
    :param setting: the paint setting
    :returns: echos back the setting
    """
    if setting == "none" or setting == "currentColor":
        return setting
    else:
        return color(setting)

def percentage(setting: str) -> str:
    """Returns a percentage setting as is after checking that it meets svg 
    percentage rules. If it does not meet the rules for svg percentage 
    input, it will raise a ValueError.
    
    :param setting: the percentage setting
    :returns: echos back the setting
    """
    setting = str(setting)
    if re.match("^" + number_re + "%$", setting):
        return setting
    else:
        raise ValueError(f"'{setting}' is not svg 1.1 <percentage> formatted")

def stroke_width(setting: str | int | float) -> str:
    """Returns the setting after checking that the value is greater 
    than 0 and that the unit is em, ex, px, in, cm, mm, pt, or pc
    
    :param setting: the setting to set an svg stroke-width setting.
    :returns: echos back the setting
    """
    if length_value(setting) < 0:
        raise ValueError("Provided length value '" 
                         + setting
                         + "' must be greater than 0")
    else:
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
    if re.match(length_re, setting):
        return setting
    else:
        raise ValueError(f"'{setting}' is not svg 1.1 <length> format")

def length_value(setting: str) -> float | int:
    """Returns just the number of the given length without the unit.
    
    :param setting: the setting to set an svg length setting.
    :returns: the number value of the setting as a float or int
    """
    setting = length(setting)
    length_match = re.match(length_re, setting)
    if length_match:
        setting = length_match[1] # Isolate numerical value
    else:
        raise ValueError(f"Format of '{setting}' is not recognized")
    if re.match(r"^" + float_re + "$", setting):
        return float(setting)
    else:
        return int(setting)

def length_unit(setting: str | int | float) -> str:
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
    elif re.match("^" + presentation_length_units_re + "$", setting):
        return setting
    else:
        setting = length(setting)
    
    if re.match("^" + number_re + "$", setting):
        return ""
    elif re.match("^" + number_re + presentation_length_units_re + "$",
                  setting):
        return re.search(presentation_length_units_re, setting)[0]
    else:
        raise ValueError(f"'{setting}' is an unrecognized format that passed"
                         + f" length's check")