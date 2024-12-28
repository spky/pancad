"""A module providing functions to verify svg syntax since errors won't 
appear until the user tries to open it with inkscape or a browser
"""

import re
import trigonometry as trig

def stroke_linecap(setting: str) -> str:
    """Returns the setting with 'stroke-linecap:' prepended to it after 
    checking that it meets the rules for a stroke-linecap svg setting. If 
    the setting is not butt, round, square, or inherit, it will raise a 
    ValueError
    
    :param setting: the setting to set an svg stroke-linecap setting.
    :returns: the setting with stroke-linecap: prepended to it
    """
    allowable_values = [ "butt", "round", "square", "inherit"]
    if setting not in allowable_values:
        raise ValueError("Provided setting value '" 
                         + str(setting)
                         + "' is not in the list of allowed values: "
                         + str(allowable_values))
    else:
        return "stroke-linecap:" + setting

def stroke_linejoin(setting: str) -> str:
    """Returns the setting with 'stroke-linejoin:' prepended to it after 
    checking that it meets the rules for a stroke-linejoin svg setting. If 
    the setting is not miter, round, bevel, or inherit, it will raise a 
    ValueError
    
    :param setting: the setting to set an svg stroke-linejoin setting.
    :returns: the setting with stroke-linejoin: prepended to it
    """
    allowable_values = [ "miter", "round", "bevel", "inherit"]
    if setting not in allowable_values:
        raise ValueError("Provided setting value '" 
                         + str(setting)
                         + "' is not in the list of allowed values: "
                         + str(allowable_values))
    else:
        return "stroke-linejoin:" + setting

def stroke_opacity(setting: float) -> str:
    """Returns the setting with 'stroke-opacity:' prepended to it after 
    checking that it meets the rules for a stroke-opacity svg setting. If 
    the setting is not between 0 and 1 or is not a float/int, it will 
    raise a ValueError
    
    :param setting: the setting to set an svg stroke-linejoin setting.
    :returns: the setting with stroke-opacity: prepended to it
    """
    if not isinstance(setting, float) and not isinstance(setting, int):
        raise ValueError("Provided value of '" 
                         + str(setting) 
                         + "' must be of type float or int")
    elif float(setting) < 0.0 or float(setting) > 1.0:
        raise ValueError("Provided value of '" 
                         + str(setting)
                         + "' is not between 0 and 1")
    else:
        return "stroke-opacity:" + str(setting)

def color(setting: str) -> str:
    """Returns the setting as is after checking that it meets the rules 
    for svg colors. This function is intended to be used to feed into 
    another setting function, ex: fill, stroke, etc. If it does not meet 
    the rules for color input, it will raise a ValueError
    
    :param setting: the color setting to be fed into a more specific 
                    setting
    :returns: the color setting
    """
    if re.match(r"^#[0-9A-Fa-f]{6}$", setting):
        return setting
    elif re.match(r"^#[0-9A-Fa-f]{3}$", setting):
        return setting
    elif re.match(r"^[rR][gG][bB]\([0-9]{1,3},[0-9]{1,3},[0-9]{1,3}\)$", setting):
        # Have to also check that the values are less than 255
        rgb_vals = setting[4:-1]
        rgb_vals = rgb_vals.split(",")
        for val in rgb_vals:
            if int(val) > 255:
                raise ValueError("Provided value of '"
                                 + str(setting)
                                 + "' has rgb values >255")
        return setting
    elif re.match(r"^[rR][gG][bB]\([0-9]{1,3}%,[0-9]{1,3}%,[0-9]{1,3}%\)$", setting):
        # Have to also check that the percentages are less than 100%
        rgb_vals = setting[4:-1]
        rgb_vals = rgb_vals.replace("%","")
        rgb_vals = rgb_vals.split(",")
        for val in rgb_vals:
            if int(val) > 100:
                raise ValueError("Provided value of '"
                                 + str(setting)
                                 + "' has rgb percentages >100%")
        return setting
    else:
        raise ValueError("Provided value of '"
                         + str(setting)
                         + "' does not match any supported color input format")

def fill(setting:str) -> str:
    """Returns the setting with 'fill:' prepended to it after 
    checking that it meets the rules for a color svg setting
    
    :param setting: the setting to set an svg fill setting.
    :returns: the setting with 'fill:' prepended to it
    """
    if setting == "none":
        return "fill:" + setting
    else:
        return  "fill:" + color(setting)

def stroke(setting:str) -> str:
    """Returns the setting with 'stroke:' prepended to it after 
    checking that it meets the rules for a color svg setting
    
    :param setting: the setting to set an svg stroke setting.
    :returns: the setting with 'stroke:' prepended to it
    """
    return "stroke:" + color(setting)

def stroke_width(setting: str | int | float) -> str:
    """Returns the setting with 'stroke-width:' prepended to it after 
    checking that the value is greater than 0 and that the unit is em, ex, 
    px, in, cm, mm, pt, or pc
    
    :param setting: the setting to set an svg stroke-width setting.
    :returns: the setting with 'stroke-width:' prepended to it
    """
    return "stroke-width:" + length(setting)

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
    :returns: the setting after being validated
    """
    allowable_units = ["em", "ex", "px", "in", "cm", "mm", "pt", "pc"]
    setting = str(setting)
    if re.match(r"^[0-9]+(\.[0-9]+)?$", setting):
        if float(setting) < 0:
            raise ValueError("Provided length value '" 
                             + setting
                             + "' must be greater than 0")
        else:
            return setting
    elif re.match(r"[0-9]+(\.[0-9]+)?[A-Za-z]+", setting):
        setting_value = float(setting[:-2])
        setting_unit = setting[-2:]
        if float(setting_value) < 0:
            raise ValueError("Provided length value '" 
                             + setting
                             + "' must be greater than 0")
        elif setting_unit not in allowable_units:
            raise ValueError("Provided unit '" 
                             + str(unit)
                             + " is not supported by svg 1.1")
        else:
            return setting
    else:
        raise ValueError("Provided value '"
                         + setting
                         + "' does not match the format of an svg 1.1 <length>")

def length_value(setting:str) -> float | int:
    """Returns just the number of the given length without the unit.
    
    :param setting: the setting to set an svg length setting.
    :returns: the number value of the setting
    """
    setting = length(setting)
    if re.match(r"^[0-9]+(\.[0-9]+)?[a-zA-Z]{2}$", setting):
        setting = setting[:-2]
    
    if re.match(r"^[0-9]+\.[0-9]+$", setting):
        return float(setting)
    elif re.match(r"^[0-9]+$", setting):
        return int(setting)
    else:
        raise ValueError("Provided value of '"
                         + setting
                         + "'pass length(), but is not recognized")

def path_style_property(property_name: str, value: str | int | float) -> str:
    """Returns the path style setting with the appropriate prepended 
    property name after checking that it meets the svg format
    
    :param property_name: the name of the svg path property. Can be 
                          stroke-linecap, stroke-linejoin, fill, stroke, 
                          stroke-opacity, or stroke-width.
    :param value: the value that the path property is going to be set to
    :returns: the setting with its prepended property name
    """
    match property_name:
        case "stroke-linecap":
            return stroke_linecap(value)
        case "stroke-linejoin":
            return stroke_linejoin(value)
        case "fill":
            return fill(value)
        case "stroke":
            return stroke(value)
        case "stroke-opacity":
            return stroke_opacity(value)
        case "stroke-width":
            return stroke_width(value)