"""A module to provide functions for creating svg path strings and a class
for svg styles.
"""

from numbers import Real

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
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    # Having this many arguments here makes sense due to how poorly svg arcs are
    # defined. They just really do take that many parameters all at once.
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
        for name, value in self._properties.items():
            if value is not None:
                settings.append(f"{name}:{value}")
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
        valid_map = {
            "color-interpolation": {"auto", "sRGB", "linearRGB", "inherit"},
            "color-interpolation-filters": {"auto", "sRGB", "linearRGB", "inherit"},
            "color-profile": {"auto", "sRGB", "inherit"},
            "color-rendering": {"auto", "optimizeSpeed", "optimizeQuality", "inherit"},
            "fill-rule": {"nonzero", "evenodd", "inherit"},
            "image-rendering": {"auto", "optimizeSpeed", "optimizeQuality", "inherit"},
            "shape-rendering": {"auto", "optimizeSpeed", "crispEdges",
                                "geometricPrecision", "inherit"},
            "text-rendering": {"auto", "optimizeSpeed", "optimizeLegibility",
                               "geometricPrecision", "inherit"},
        }
        if name in valid_map:
            self._properties[name] = value
            return
        func_map = {
            "fill": sv.paint,
            "stroke": sv.paint,
            "stroke-linecap": sv.stroke_linecap,
            "stroke-linejoin": sv.stroke_linejoin,
            "stroke-opacity": sv.stroke_opacity,
            "stroke-width": self._stroke_width,
            "fill-opacity": self._fill_opacity,
            "stroke-miterlimit": self._stroke_miterlimit,
        }
        if name in func_map:
            self._properties[name] = func_map[name](value)
            return
        not_supported = {"marker", "marker-end", "marker-mid", "marker-start",
                         "stroke-dasharray", "stroke-dashoffset"}
        if name in not_supported:
            msg = f"svg property '{name}' is not yet supported"
            raise NotImplementedError(msg)
        raise ValueError(f"'{name}' is not a supported style property")

    @staticmethod
    def _fill_opacity(value):
        if value == "inherit":
            return value
        if isinstance(value, Real):
            return str(sorted((0, value, 1))[1])
        raise ValueError(f"Unexpected value for fill-opacity: {value}")

    @staticmethod
    def _stroke_miterlimit(value):
        if value == "inherit":
            return value
        value = sv.number(value)
        if float(value) >= 1:
            return value
        raise ValueError(f"Unexpected value for stroke-miterlimit: {value}")

    @staticmethod
    def _stroke_width(value):
        value = sv.length(value)
        if sv.length_value(value) >= 0:
            return value
        raise ValueError(f"Unexpected value for stroke-width: {value}")
