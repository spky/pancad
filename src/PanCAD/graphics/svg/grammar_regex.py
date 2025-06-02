"""A Module providing constants for svg grammar regular expressions"""

# Abbreviations
## CONST = Constant
## INT = Integer
## WSP = Whitespace
## ARG = Argument

# Whitespace and Separators
WSP = "(\u0020|\u0009|\u000D|\u000A)"
COMMA = ","
COMMA_WSP = f"({WSP}+{COMMA}?{WSP}*|{COMMA}{WSP}*)"

# Numbers
DIGIT = "[0-9]"
SIGN = "(\+|-)"
DIGIT_SEQUENCE = f"({DIGIT}+)"
INT_CONST = DIGIT_SEQUENCE
EXPONENT = f"((e|E){SIGN}?{DIGIT_SEQUENCE})"
FRACTIONAL_CONST = f"({DIGIT_SEQUENCE}?\.{DIGIT_SEQUENCE}|{DIGIT_SEQUENCE}\.)"
FLOAT_CONST = f"({FRACTIONAL_CONST}{EXPONENT}?|{DIGIT_SEQUENCE}{EXPONENT})"
NUMBER = f"({SIGN}?{FLOAT_CONST}|{SIGN}?{INT_CONST})"
NONNEGATIVE_NUMBER = f"({FLOAT_CONST}|{INT_CONST})"

# Coordinates
COORDINATE = NUMBER
COORDINATE_PAIR = f"{COORDINATE}{COMMA_WSP}{COORDINATE}"
COORDINATE_PAIR_SEQUENCE = f"({COORDINATE_PAIR}{COMMA_WSP}?|{COORDINATE_PAIR})+"
COORDINATE_SEQUENCE = f"({COORDINATE}{COMMA_WSP}?|{COORDINATE})+"

# Command Characters
MOVETO_CHAR = "(M|m)"
FLAG = "(0|1)"
CLOSEPATH = "(Z|z)"
LINETO_CHAR = "(L|l)"
HORIZONTAL_LINETO_CHAR = "(H|h)"
VERTICAL_LINETO_CHAR = "(V|v)"
CURVETO_CHAR = "(C|c)"
SMOOTH_CURVETO_CHAR = "(S|s)"
QUAD_BEZIER_CURVETO_CHAR = "(Q|q)"
SMOOTH_QUAD_BEZIER_CURVETO_CHAR = "(T|t)"
ELLIPTICAL_ARC_CHAR = "(A|a)"

# Commands
## Expressions assume the correct number of arguments have been provided for 
## each command

def _pair_command(character: str) -> str:
    return f"{character}{WSP}*{COORDINATE_PAIR_SEQUENCE}"

def _singles_command(character: str) -> str:
    return f"{character}{WSP}*{COORDINATE_SEQUENCE}"

# MOVETO = f"{MOVETO_CHAR}{WSP}*{COORDINATE_PAIR_SEQUENCE}"
MOVETO = _pair_command(MOVETO_CHAR)

LINETO = _pair_command(LINETO_CHAR)
HORIZONTAL_LINETO = _singles_command(HORIZONTAL_LINETO_CHAR)
VERTICAL_LINETO = _singles_command(VERTICAL_LINETO_CHAR)
CURVETO = _pair_command(CURVETO_CHAR)
SMOOTH_CURVETO = _pair_command(SMOOTH_CURVETO_CHAR)
QUAD_BEZIER_CURVETO = _pair_command(QUAD_BEZIER_CURVETO_CHAR)
SMOOTH_QUAD_BEZIER_CURVETO = _pair_command(SMOOTH_QUAD_BEZIER_CURVETO_CHAR)

# rx, ry, x-axis-rotation, large-arc-flag, sweep-flag, x, y

_elliptical_args = [
    NONNEGATIVE_NUMBER, NONNEGATIVE_NUMBER, NUMBER,
    FLAG, FLAG, COORDINATE_PAIR
]
ELLIPTICAL_ARC_ARG = f"({COMMA_WSP.join(_elliptical_args)})"
ELLIPTICAL_ARC_ARG_SEQUENCE = (f"({ELLIPTICAL_ARC_ARG}{COMMA_WSP}?"
                               f"|{ELLIPTICAL_ARC_ARG})+")
ELLIPTICAL_ARC = f"{ELLIPTICAL_ARC_CHAR}{WSP}*{ELLIPTICAL_ARC_ARG_SEQUENCE}"

_drawto_command_list = [
    CLOSEPATH,
    LINETO, HORIZONTAL_LINETO, VERTICAL_LINETO,
    CURVETO, SMOOTH_CURVETO, QUAD_BEZIER_CURVETO,
    SMOOTH_QUAD_BEZIER_CURVETO,
    ELLIPTICAL_ARC,
]

_PIPE = "|"
DRAWTO_COMMAND = f"({_PIPE.join(_drawto_command_list)})"

_command_list = _drawto_command_list + [MOVETO]
COMMAND =  f"({_PIPE.join(_command_list)})"
