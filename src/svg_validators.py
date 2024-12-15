"""A module providing functions to verify svg syntax since errors won't 
appear until the user tries to open it with inkscape or a browser
"""

import re

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
    the setting is not mitre, round, bevel, or inherit, it will raise a 
    ValueError
    
    :param setting: the setting to set an svg stroke-linejoin setting.
    :returns: the setting with stroke-linejoin: prepended to it
    """
    allowable_values = [ "mitre", "round", "bevel", "inherit"]
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
    
    :param setting: the color setting to be fed into a more specific setting
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
    return "fill:" + color(setting)

def stroke(setting:str) -> str:
    """Returns the setting with 'stroke:' prepended to it after 
    checking that it meets the rules for a color svg setting
    
    :param setting: the setting to set an svg stroke setting.
    :returns: the setting with 'stroke:' prepended to it
    """
    return "stroke:" + color(setting)