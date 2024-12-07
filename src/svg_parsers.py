import re

def parse_coordinate_string(coordinate_string):
    """
    Uses re to figure out what string of coordinates are in path 
    data's coordinate string and returns a list of coordinate pairs
    """
    coordinate_string = coordinate_string.strip()
    
    xy_pattern = "([-+]?[0-9]*\.?[0-9]+)[ |,]*([-+]?[0-9]*\.?[0-9]+)"
    coordinate_re = re.compile(xy_pattern)
    coordinate_list = re.findall(coordinate_re, coordinate_string)
    
    out = []
    for c in coordinate_list:
        pair = [float(c[0]), float(c[1])]
        out.append(pair)
    return out

def match_front_cmd(path_data):
    """
    Uses re to figure out what type of command is the first in the 
    path data and then returns a dictionary with the "type" of 
    command and the "match" of the regex. If no command is found, 
    returns None
    """
    command_type_regexs = {
        "M": "(?P<type>^M)[ ]?(?P<coord>.*)(?P<leftover>[ ]?[a-zA-Z].*)",
        "m": "(?P<type>^m)[ ]?(?P<coord>.*)(?P<leftover>[ ]?[a-zA-Z].*)",
        "L": "(?P<type>^L)[ ]?(?P<coord>.*)(?P<leftover>[ ]?[a-zA-Z].*)",
        "l": "(?P<type>^l)[ ]?(?P<coord>.*)(?P<leftover>[ ]?[a-zA-Z].*)",
        "H": "(?P<type>^H)[ ]?(?P<coord>.*)(?P<leftover>[ ]?[a-zA-Z].*)",
        "h": "(?P<type>^h)[ ]?(?P<coord>.*)(?P<leftover>[ ]?[a-zA-Z].*)",
        "V": "(?P<type>^V)[ ]?(?P<coord>.*)(?P<leftover>[ ]?[a-zA-Z].*)",
        "v": "(?P<type>^v)[ ]?(?P<coord>.*)(?P<leftover>[ ]?[a-zA-Z].*)",
        "A": "(?P<type>^v)[ ]?(?P<coord>.*)(?P<leftover>[ ]?[a-zA-Z].*)",
        "a": "(?P<type>^v)[ ]?(?P<coord>.*)(?P<leftover>[ ]?[a-zA-Z].*)",
    }
    
    for regex in command_type_regexs:
        match = re.compile(command_type_regexs[regex])
        search = re.search(match, path_data)
        if search:
            out = {
            "type": regex,
            "match": search,
            }
            return out
    return None