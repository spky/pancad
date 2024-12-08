"""A module to provide functions for parsing svg tag information out into 
other formats
"""

import re

def parse_coordinate_string(coordinate: str) -> list:
    """Uses re to figure out what string of coordinates are in path 
    data's coordinate string and returns a list of coordinate pairs
    
    :param coordinate: coordinate string from an svg tag
    :return: list of coordinate pairs in the coordinate string
    """
    coordinate = coordinate.strip()
    
    xy_pattern = "([-+]?[0-9]*\.?[0-9]+)[ |,]*([-+]?[0-9]*\.?[0-9]+)"
    coordinate_re = re.compile(xy_pattern)
    coordinate_list = re.findall(coordinate_re, coordinate)
    
    out = []
    for c in coordinate_list:
        pair = [float(c[0]), float(c[1])]
        out.append(pair)
    return out

def match_front_cmd(path_data: str) -> dict:
    """Returns a dictionary with the "type" and "match of the first path data command.
    
    :param path_data: path data of an svg path object
    :return: dictionary of the first command with keys "type" and "match"
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

def split_path_data(path_data:str) -> list:
    """Returns a list of the commands in the svg path's data in the order 
    that they appear
    :param path_data: path data of an svg path object
    :return: list all commands in the path tag's data
    """
    
    command_pattern = "[A-Za-z].*(?=[ ]?[A-Za-z].*)"
    #command_pattern = "[A].*(?=[A-Za-z])"
    #command_pattern = "[A].*$?"
    #command_pattern = ".*(?=[A-Za-z]?)"
    command_re = re.compile(command_pattern)
    command_list = re.search(command_re, path_data)
    #command_list = re.split(command_re, path_data)
    return command_list