"""A module to provide functions for creating svg paths.
"""
import svg_validators as sv

def make_path_data(commands: list, delimiter: str = "\n"):
    """Returns a string of svg commands joined together with a delimiter. 
    The delimiter is defaulted to be a newline, but can be configured.
    
    :param commands: a list of strings where each string is an svg command
    :param delimiter: a string to put between each command
    """
    return delimiter.join(commands)

def make_moveto(coordinates: list, relative: bool = False) -> str:
    """Returns a string moveto command using a coordinate list and a 
    boolean stating whether the command is relative
    
    :param coordinates: a list of 2 element [x, y] coordinate lists
    :param relative: determines whether the command will be relative
    :returns: an svg moveto command string
    """
    cmd = "m" if relative else "M"
    for c in coordinates:
        cmd += " " + str(c[0]) + " " + str(c[1])
    return cmd

def make_arc(
    rx: float, ry: float, x_axis_rotation: float,
    large_arc_flag: int, sweep_flag: int,
    x: float, y: float, relative: bool = False):
    """Returns a string arc command using the list of arc parameters and a 
    boolean stating whether the command is relative
    
    :param rx: x-axis radius
    :param ry: y-axis radius
    :param x_axis_rotation: angle that the ellipse's x-axis is rotated relative to the current coordinate system in degrees
    :param large_arc_flag: if 1, the >180 degree arc will be chosen, if 0, the < 180 degree arc will be chosen
    :param sweep_flag: if 1, the arc is drawn in the positive angle direction, if 0 it will be drawn in the negative angle direction
    :param x: end x location
    :param y: end y location
    :param relative: determines whether the command will be relative
    :returns: an svg arc command string
    """
    cmd = "a" if relative else "A"
    arc_params = [rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, x, y]
    str_params = []
    for parameter in arc_params:
        str_params.append(str(parameter))
    cmd += " " + " ".join(str_params)
    return cmd

def make_lineto(coordinates: list, relative: bool = False) -> str:
    """Returns a string lineto command using a coordinate list and a 
    boolean stating whether the command is relative
    
    :param coordinates: a list of 2 element [x, y] coordinate lists
    :param relative: determines whether the command will be relative
    :returns: an svg lineto command string
    """
    cmd = "l" if relative else "L"
    for c in coordinates:
        cmd += " " + str(c[0]) + " " + str(c[1])
    return cmd

def make_horizontal(lengths: list, relative: bool = False) -> str:
    """Returns a string horizontal command using a length list and a 
    boolean stating whether the command is relative
    
    :param coordinates: a list of x direction lengths
    :param relative: determines whether the command will be relative
    :returns: an svg horizontal command string
    """
    cmd = "h" if relative else "H"
    for length in lengths:
        cmd += " " + str(length)
    return cmd

def make_vertical(lengths: list, relative: bool = False) -> str:
    """Returns a string vertical command using a length list and a 
    boolean stating whether the command is relative
    
    :param coordinates: a list of y direction lengths
    :param relative: determines whether the command will be relative
    :returns: an svg vertical command string
    """
    cmd = "v" if relative else "V"
    for length in lengths:
        cmd += " " + str(length)
    return cmd

def make_circle():
    pass

def make_style(style_dict: dict) -> str:
    """Returns a path style using each key of the given style 
    dictionary as a different property.
    
    :param style_dict: A dictionary full of key value pairs of the 
                       format 'property_name':'property_value'
    :returns: a style string ready to be assigned to a path's style property
    
    """
    properties = []
    for key in style_dict:
        properties.append(sv.path_style_property(key, style_dict[key]))
    return ";".join(properties)