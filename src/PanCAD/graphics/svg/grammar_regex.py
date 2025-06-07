"""A Module that creates and exposes constants for svg grammar regular expressions

Abbreviations
CONST = Constant, INT = Integer
WSP = Whitespace, ARG = Argument
FRAC = Fractional

# Regular Expression Constants:

## High Level Path Data Parsing
command: Splits path data into a list of its sub-commands. If path data 
    does not match this regular expression, it likely does not meet the svg 1.1 
    specification. Ex: "M1,2 L3 4" will be split into ["M1,2 ", "L3 4"].

## Individual Path Data Commands
closepath: Finds closepath (Z or z) commands in path data. Closepath takes no 
    parameters.
curveto: Finds curveto (C or c) commands in path data. Curveto parameters are a 
    series of (x1 y1 x2 y2 x y) coordinate sets
elliptical_arc: Finds elliptical arc (A or a) commands in path data. Elliptical 
    arc parameters are a series of (rx ry x-axis-rotation large-arc-flag 
    sweep-flag x y) number sets.
horizontal_lineto: Finds horizontal lineto (H or h) commands in path data. 
    Horizontal lineto parameters are a series of x coordinates.
lineto: Finds lineto (L or l) commands in path data. Lineto parameters are a 
    series of (x, y) coordinate pairs.
moveto: Finds moveto (M or m) commands in path data. Moveto parameters are a 
    series of (x, y) coordinate pairs.
quad_bezier_curveto: Finds quadratic bezier curveto (Q or q) commands in path 
    data. Quadratic bezier curveto parameters are a series of (x1 y1 x y) 
    coordinate sets.
smooth_curveto: Finds shorthand/smooth curveto (S or s) commands in path data. 
    Smooth curveto parameters are a series of (x2 y2 x y) coordinate sets
smooth_quad_bezier_curveto: Finds shorthand/smooth quadratic bezier curveto
    (T or t) commands in path data. Smooth quadratic bezier curveto parameters 
    are a series of (x, y) coordinate pairs.
vertical_lineto: Finds vertical lineto (V or v) commands in path data. Vertical 
    lineto parameters are a series of y coordinates.

# Type dictionaries
SVG_CMD_TYPES: A dictionary containing the lists of what commands fall into the
    4 types of parameter formats: pairs, singles, arcs, closepath

## Grammar Component NamedTuples
**NOTE**: Reference PanCAD.utils.regex for tuple names
WSP: Finds path data whitespace, defined as a space, tab, newline, or carriage 
    return.
SIGN: Finds signs: + or -.
DIGIT_SEQUENCE: Finds series of integers.
FLAG: Finds a 0 or 1 flag.
comma_wsp: Finds a comma or whitespace.
exponent: Finds exponents such as "E+100"
number: Finds numbers in strings. Works for float, int, or scientific formats.
coordinate_pair: Finds pairs of numbers in a string.
"""
import re
from collections import namedtuple

from PanCAD.graphics.svg import PathParameterType, PathCommandCharacter
from PanCAD.utils.regex import capture_re

# Manual Constants

SVG_CMD_TYPES = {
    PathParameterType.PAIR: [
        PathCommandCharacter.M, PathCommandCharacter.m,
        PathCommandCharacter.L, PathCommandCharacter.l,
        PathCommandCharacter.C, PathCommandCharacter.c,
        PathCommandCharacter.S, PathCommandCharacter.s,
        PathCommandCharacter.Q, PathCommandCharacter.q,
        PathCommandCharacter.T, PathCommandCharacter.t,
    ],
    PathParameterType.SINGLE: [
        PathCommandCharacter.H, PathCommandCharacter.h,
        PathCommandCharacter.V, PathCommandCharacter.v,
    ],
    PathParameterType.ARC: [
        PathCommandCharacter.A, PathCommandCharacter.a,
    ],
    PathParameterType.CLOSEPATH: [
        PathCommandCharacter.Z, PathCommandCharacter.z,
    ],
}
WSP = capture_re("\u0020|\u0009|\u000D|\u000A", "whitespace")
SIGN = capture_re("\+|-", "sign")
_PIPE = "|"
DIGIT_SEQUENCE = capture_re("[0-9]+", "digit_sequence")
INT_CONST = capture_re("[0-9]+", "integer_constant")
FLAG = capture_re("0|1", "flag")

# Derived Whitespace/Separators
comma_wsp = capture_re(f"{WSP.dc}+,?{WSP.dc}*|,{WSP.dc}*", "comma_whitespace")

# Number Components
exponent = capture_re(f"(?:e|E){SIGN.dc}?{DIGIT_SEQUENCE.dc}", "exponent")

fractional_const = capture_re(
    f"{DIGIT_SEQUENCE.dc}?\.{DIGIT_SEQUENCE.dc}|{DIGIT_SEQUENCE.dc}\.",
    "fractional_constant"
)
float_const = capture_re(
    f"{fractional_const.dc}{exponent.dc}?|{DIGIT_SEQUENCE.dc}{exponent.dc}",
    "floating_point_constant"
)
_number_pattern = f"{SIGN.dc}?{float_const.dc}|{SIGN.dc}?{INT_CONST.dc}"

# Numbers
number = capture_re(_number_pattern, "number")
nonnegative_number = capture_re(f"{float_const.dc}|{INT_CONST.dc}",
                                 "nonnegative_number")



# Coordinates
coordinate = capture_re(_number_pattern, "coordinate")
coordinate_pair = capture_re(f"{coordinate.dc}{comma_wsp.dc}{coordinate.dc}",
                              "coordinate_pair")
coordinate_pair_sequence = capture_re(
    f"(?:{coordinate_pair.pa}{comma_wsp.dc}?|{coordinate_pair.pa})+",
    "coordinate_pair_sequence"
)
coordinate_sequence = capture_re(
    f"(?:{coordinate.dc}{comma_wsp.dc}?|{coordinate.dc})+",
    "coordinate_sequence"
)

# Commands
## Expressions assume the correct number of arguments have been provided for 
## each command
def _arc_command(character_re: str) -> str:
    """Produces an SVG elliptical arc command regular expression. SVG arcs 
    are a special case of commands that have their arguments in the 
    following order: rx, ry, x-axis-rotation, large-arc-flag, sweep-flag, x, y
    """
    _elliptical_args = [
        nonnegative_number.dc, nonnegative_number.dc, number.dc,
        FLAG.dc, FLAG.dc, coordinate_pair.dc
    ]
    elliptical_arc_arg = capture_re(f"{comma_wsp.dc.join(_elliptical_args)}",
                                     "elliptical_arc_argument")
    elliptical_arc_arg_sequence = capture_re(
        f"(?:{elliptical_arc_arg.pa}{comma_wsp.dc}?|{elliptical_arc_arg.pa})+",
        "elliptical_arc_argument_sequence"
    )
    return f"{character_re}{WSP.dc}*{elliptical_arc_arg_sequence.dc}"

def _pair_command(character_re: str) -> str:
    """Returns an svg command regex for a command that takes a sequence of 
    coordinate pairs as its arguments"""
    return f"{character_re}{WSP.dc}*{coordinate_sequence.dc}"

def _singles_command(character_re: str) -> str:
    """Returns an svg command regex for a command that takes a sequence of 
    standalone coordinates as its arguments"""
    return f"{character_re}{WSP.dc}*{coordinate_sequence.dc}"

def _upper_lower_case_command(character: str, group: str="command") -> str:
    """Initializes a command character that consists of the upper and lower case 
    characters to initialize svg command regular expressions.
    """
    if len(character) == 1:
        pattern = f"{character.upper()}|{character.lower()}"
        return capture_re(pattern, group)
    else:
        raise ValueError(f"character must be 1 character, given: {character}")

def _cmd_re(character: str):
    """Returns an svg command regex for a command based on its character and 
    command type"""
    cmd_character_re = _upper_lower_case_command(character).dc
    for cmd_type, command_letters in SVG_CMD_TYPES.items():
        if character in command_letters:
            match cmd_type:
                case PathParameterType.PAIR:
                    return _pair_command(cmd_character_re)
                case PathParameterType.SINGLE:
                    return _singles_command(cmd_character_re)
                case PathParameterType.ARC:
                    return _arc_command(cmd_character_re)
                case PathParameterType.CLOSEPATH:
                    return cmd_character_re
    raise ValueError(f"Character '{character}' is not an svg path command")

# Generate Command Sensing Regular Expressions
_command_list = []
for _, cmd_letters in SVG_CMD_TYPES.items():
    _command_list.extend(
        [_cmd_re(letter) for letter in cmd_letters]
    )

command =  f"{WSP.dc}*({_PIPE.join(_command_list)})"

moveto = _cmd_re(PathCommandCharacter.M)
lineto = _cmd_re(PathCommandCharacter.L)
horizontal_lineto = _cmd_re(PathCommandCharacter.H)
vertical_lineto = _cmd_re(PathCommandCharacter.V)
curveto = _cmd_re(PathCommandCharacter.C)
smooth_curveto = _cmd_re(PathCommandCharacter.S)
quad_bezier_curveto = _cmd_re(PathCommandCharacter.Q)
smooth_quad_bezier_curveto = _cmd_re(PathCommandCharacter.T)
elliptical_arc = _cmd_re(PathCommandCharacter.A)
closepath = _cmd_re(PathCommandCharacter.Z)