"""A Module providing constants for svg grammar regular expressions

Abbreviations
CONST = Constant, INT = Integer
WSP = Whitespace, ARG = Argument
FRAC = Fractional
"""
import re
from collections import namedtuple

def _capture_re(pattern: str, group_name: str) -> namedtuple:
    """Initializes a namedtuple with regular expressions that contain a pattern,
    a non-grouped pattern, a grouped pattern, and a named group pattern.
    
    :param pattern: A regular expression pattern
    :param group_name: The name of the named regular expression group
    :returns: A namedtuple with names ca (capture), dc (don't capture), na (named 
        group), and pa (plain pattern)
    """
    CaptureRegex = namedtuple("CaptureRegex", ["ca", "dc", "na", "pa"])
    return CaptureRegex(
        f"({pattern})",
        f"(?:{pattern})",
        f"(?P<{group_name}>{pattern})",
        pattern,
    )

# Manual Constants
SVG_CMD_TYPES = {
    "pairs": ["M", "L", "C", "S", "Q", "T"],
    "singles": ["H", "V"],
    "arcs": ["A"],
    "closepath": ["Z"],
}
WSP = _capture_re("\u0020|\u0009|\u000D|\u000A", "whitespace")
SIGN = _capture_re("\+|-", "sign")
_PIPE = "|"
DIGIT_SEQUENCE = _capture_re("[0-9]+", "digit_sequence")
INT_CONST = _capture_re("[0-9]+", "integer_constant")
FLAG = _capture_re("0|1", "flag")

# Derived Whitespace/Separators
comma_wsp = _capture_re(f"{WSP.dc}+,?{WSP.dc}*|,{WSP.dc}*", "comma_whitespace")

# Number Components
exponent = _capture_re(f"(?:e|E){SIGN.dc}?{DIGIT_SEQUENCE.dc}", "exponent")

fractional_const = _capture_re(
    f"{DIGIT_SEQUENCE.dc}?\.{DIGIT_SEQUENCE.dc}|{DIGIT_SEQUENCE.dc}\.",
    "fractional_constant"
)
float_const = _capture_re(
    f"{fractional_const.dc}{exponent.dc}?|{DIGIT_SEQUENCE.dc}{exponent.dc}",
    "floating_point_constant"
)
_number_pattern = f"{SIGN.dc}?{float_const.dc}|{SIGN.dc}?{INT_CONST.dc}"

# Numbers
number = _capture_re(_number_pattern, "number")
nonnegative_number = _capture_re(f"{float_const.dc}|{INT_CONST.dc}",
                                 "nonnegative_number")

# Named Number Groups
_exp_num = _capture_re(DIGIT_SEQUENCE.pa, "exponent_number")
_exp_sign = _capture_re(SIGN.pa, "exponent_sign")

_whole_num = _capture_re(DIGIT_SEQUENCE.pa, "whole_number")
_dec_num = _capture_re(DIGIT_SEQUENCE.pa, "decimal_number")

_exp_named = _capture_re(f"(?:E|e){_exp_sign.na}?{_exp_num.na}", "exponent_na")

_frac_const_dec_exp = f"{SIGN.na}?{_whole_num.na}?\.{_dec_num.na}{_exp_named.dc}?"
_frac_const_exp = f"{SIGN.na}?{_whole_num.na}\.{_exp_named.dc}?"
_int_const_exp = f"{SIGN.na}?{_whole_num.na}{_exp_named.dc}?"

# Coordinates
coordinate = _capture_re(_number_pattern, "coordinate")
coordinate_pair = _capture_re(f"{coordinate.dc}{comma_wsp.dc}{coordinate.dc}",
                              "coordinate_pair")
coordinate_pair_sequence = _capture_re(
    f"(?:{coordinate_pair.pa}{comma_wsp.dc}?|{coordinate_pair.pa})+",
    "coordinate_pair_sequence"
)
coordinate_sequence = _capture_re(
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
    elliptical_arc_arg = _capture_re(f"{comma_wsp.dc.join(_elliptical_args)}",
                                     "elliptical_arc_argument")
    elliptical_arc_arg_sequence = _capture_re(
        f"(?:{elliptical_arc_arg.pa}{comma_wsp.dc}?|{elliptical_arc_arg.pa})+",
        "elliptical_arc_argument_sequence"
    )
    return f"{character_re}{WSP.dc}*{elliptical_arc_arg_sequence.dc}"

def _pair_command(character_re: str) -> str:
    """Returns an svg command regex for a command that takes a sequence of 
    coordinate pairs as its arguments"""
    return f"{character_re}{WSP.dc}*{coordinate_pair_sequence.dc}"

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
        return _capture_re(pattern, group)
    else:
        raise ValueError(f"character must be 1 character, given: {character}")

def _cmd_re(character: str):
    """Returns an svg command regex for a command based on its character and 
    command type"""
    cmd_character_re = _upper_lower_case_command(character).dc
    for cmd_type, command_letters in SVG_CMD_TYPES.items():
        if character.upper() in command_letters:
            match cmd_type:
                case "pairs":
                    return _pair_command(cmd_character_re)
                case "singles":
                    return _singles_command(cmd_character_re)
                case "arcs":
                    return _arc_command(cmd_character_re)
                case "closepath":
                    return cmd_character_re
    raise ValueError(f"Character '{character}' is not an svg path command")

def parse_number(string: str) -> float | int:
    """Returns the value of a number in a string. Supports floats, integers 
    and scientific notation.
    
    :param string: A string that contains a number
    :returns: The value of the number in the string
    """
    if re.search(_frac_const_dec_exp, string):
        match = re.search(_frac_const_dec_exp, string)
    elif re.search(_frac_const_exp, string):
        match = re.search(_frac_const_exp, string)
    elif re.search(_int_const_exp, string):
        match = re.search(_int_const_exp, string)
    else:
        raise ValueError(f"Could not find a number in string: {string}")

# Generate Command Sensing Regular Expressions
_command_list = []
for _, cmd_letters in SVG_CMD_TYPES.items():
    _command_list.extend(
        [_cmd_re(letter) for letter in cmd_letters]
    )

command =  f"{WSP.dc}*({_PIPE.join(_command_list)})"

moveto = _cmd_re("M")
lineto = _cmd_re("L")
horizontal_lineto = _cmd_re("H")
vertical_lineto = _cmd_re("V")
curveto = _cmd_re("C")
smooth_curveto = _cmd_re("S")
quad_bezier_curveto = _cmd_re("Q")
smooth_quad_bezier_curveto = _cmd_re("T")
elliptical_arc = _cmd_re("A")