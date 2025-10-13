"""A module to provide functions for creating svg path strings and a class 
for svg styles.
"""

from pancad.graphics.svg import validators as sv

def make_path_data(commands: list, delimiter: str = "\n") -> str:
    """Returns a string of svg commands joined together with a delimiter.
    
    :param commands: A list of strings where each string is an svg command
    :param delimiter: A string to put between each command, defaults to newline
    :returns: The path data string command
    """
    return delimiter.join(commands)

def make_moveto(coordinates: list, relative: bool = False) -> str:
    """Returns a string moveto command using a coordinate list and a 
    boolean stating whether the command is relative
    
    :param coordinates: A list of 2 element [x, y] coordinate lists
    :param relative: Whether the command will be relative, defaults to False
    :returns: The svg moveto command string
    """
    cmd = "m" if relative else "M"
    for c in coordinates:
        cmd += " " + str(c[0]) + " " + str(c[1])
    return cmd

def make_arc(rx: float, ry: float, x_axis_rotation: float,
             large_arc_flag: int, sweep_flag: int,
             x: float, y: float, relative: bool = False) -> str:
    """Returns a string arc command using the list of arc parameters and a 
    boolean stating whether the command is relative
    
    :param rx: arc x-axis radius
    :param ry: arc y-axis radius
    :param x_axis_rotation: angle that the ellipse's x-axis is rotated 
                            relative to the current coordinate system 
                            in degrees
    :param large_arc_flag: if 1, the >180 degree arc will be chosen, if 
                           0, the < 180 degree arc will be chosen
    :param sweep_flag: if 1, the arc is drawn in the positive angle 
                       direction, if 0 it will be drawn in the negative 
                       angle direction
    :param x: end x location
    :param y: end y location
    :param relative: determines whether the command will be relative
    :returns: The svg arc command string
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
    
    :param coordinates: A list of 2 element [x, y] coordinate lists
    :param relative: Whether the command will be relative, defaults to False
    :returns: The svg lineto command string
    """
    cmd = "l" if relative else "L"
    for c in coordinates:
        cmd += " " + str(c[0]) + " " + str(c[1])
    return cmd

def make_horizontal(lengths: list, relative: bool = False) -> str:
    """Returns a string horizontal command using a length list and a 
    boolean stating whether the command is relative
    
    :param coordinates: A list of x direction lengths
    :param relative: Whether the command will be relative, defaults to False
    :returns: The svg horizontal command string
    """
    cmd = "h" if relative else "H"
    for length in lengths:
        cmd += " " + str(length)
    return cmd

def make_vertical(lengths: list, relative: bool = False) -> str:
    """Returns a string vertical command using a length list and a 
    boolean stating whether the command is relative
    
    :param coordinates: A list of y direction lengths
    :param relative: Whether the command will be relative, defaults to False
    :returns: The svg vertical command string
    """
    cmd = "v" if relative else "V"
    for length in lengths:
        cmd += " " + str(length)
    return cmd

class SVGStyle:
    """A class to store, generate, and validate SVG styles"""
    
    def __init__(self) -> None:
        """Constructor method"""
        self._properties = {
            "color-interpolation": None,
            "color-interpolation-filters": None,
            "color-profile": None,
            "color-rendering": None,
            "fill": None,
            "fill-opacity": None,
            "fill-rule": None,
            "image-rendering": None,
            "marker": None,
            "marker-end": None,
            "marker-mid": None,
            "marker-start": None,
            "shape-rendering": None,
            "stroke": None,
            "stroke-dasharray": None,
            "stroke-dashoffset": None,
            "stroke-linecap": None,
            "stroke-linejoin": None,
            "stroke-miterlimit": None,
            "stroke-opacity": None,
            "stroke-width": None,
            "text-rendering": None,
        }
    
    @property
    def string(self) -> str:
        """The string representation of the style. Read-only.
        
        :getter: Concatenates the populated style attributes together and 
                 returns it as a string
        """
        settings = []
        for prop in self._properties:
            if self._properties[prop] is not None:
                settings.append(prop + ":" + self._properties[prop])
        return ";".join(settings)
    
    def set_from_dict(self, property_dictionary: dict) -> None:
        """Sets the style properties based on a dictionary instead of one at 
        a time.
        
        :property_dictionary: A dictionary with pairs like 'setting_name:value'
        """
        for setting in property_dictionary:
            self.set_property(setting, property_dictionary[setting])
    
    def set_property(self, name: str, value: str | int | float) -> None:
        """Sets a valid svg style attribute based on its name and value. Will 
        raise a ValueError if trying to set a property that is not 
        supported. Will check individual property types for validity 
        based on the value. See the SVG 1.1 styling properties at this link 
        here: 
        https://www.w3.org/TR/2011/REC-SVG11-20110816/styling.html#SVGStylingProperties
        
        :param name: The styling property's name
        :param value: The styling property's value
        """
        match name:
            case "color-interpolation":
                if value in ["auto", "sRGB", "linearRGB", "inherit"]:
                    set_value = value
            case "color-interpolation-filters":
                if value in ["auto", "sRGB", "linearRGB", "inherit"]:
                    set_value = value
            case "color-profile":
                if value in ["auto", "sRGB", "inherit"]:
                    # Custom color profile names not supported
                    set_value = value
            case "color-rendering":
                if value in ["auto", "optimizeSpeed",
                             "optimizeQuality", "inherit"]:
                    set_value = value
            case "fill":
                set_value = sv.paint(value)
            case "fill-opacity":
                if value in ["inherit"]:
                    set_value = value
                elif isinstance(value, float) or isinstance(value, int):
                    # Clamps value to be 0 or 1 if outside that range
                    set_value = str(sorted((0, value, 1))[1])
            case "fill-rule":
                if value in ["nonzero", "evenodd", "inherit"]:
                    set_value = value
            case "image-rendering":
                if value in ["auto", "optimizeSpeed",
                             "optimizeQuality", "inherit"]:
                    set_value = value
            case "marker":
                raise ValueError("marker is not yet supported")
            case "marker-end":
                raise ValueError("marker is not yet supported")
            case "marker-mid":
                raise ValueError("marker is not yet supported")
            case "marker-start":
                raise ValueError("marker is not yet supported")
            case "shape-rendering":
                if value in ["auto", "optimizeSpeed", "crispEdges",
                             "geometricPrecision", "inherit"]:
                    set_value = value
            case "stroke":
                set_value = sv.paint(value)
            case "stroke-dasharray":
                raise ValueError("stroke-dasharray is not yet supported")
            case "stroke-dashoffset":
                raise ValueError("stroke-dashoffset is not yet supported")
            case "stroke-linecap":
                set_value = sv.stroke_linecap(value)
            case "stroke-linejoin":
                set_value = sv.stroke_linejoin(value)
            case "stroke-miterlimit":
                if value in ["inherit"]:
                    set_value = value
                else:
                    value = sv.number(value)
                    if float(value) >= 1:
                        set_value = value
            case "stroke-opacity":
                set_value = sv.stroke_opacity(value)
            case "stroke-width":
                value = sv.length(value)
                if sv.length_value(value) >= 0:
                    set_value = value
            case "text-rendering":
                if value in ["auto", "optimizeSpeed", "optimizeLegibility",
                             "geometricPrecision", "inherit"]:
                    set_value = value
            case _:
                raise ValueError(f"'{name}' is not a supported style property")
        self._properties[name] = set_value