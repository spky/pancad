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
    """Returns a dictionary with the "type" and "match of the first path 
    data command.
    
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
    # re is meant to look for the spot right before each alphabet character
    command_pattern = "(?=[A-Za-z])"
    command_re = re.compile(command_pattern)
    command_list = re.split(command_re, path_data)
    
    # Remove empty strings from the list ("")
    command_list = list(filter(None, command_list))
    
    # Ensure the commands do not have empty spaces at beginning/end
    out = []
    for cmd in command_list:
        out.append(cmd.strip())
    
    return out

def clean_command(command:str) -> str:
    """Returns a string with just the data part of a path data command 
    separated by commas
    
    :param command: an svg command
    :return: the data part of the command separated just by commas
    """
    command = command[1:]
    command = command.strip()
    command = command.replace(" ",",")
    return command

def csv_to_float(csv:str) -> list:
    """Returns a list of numbers from a string full of comma separated 
    numbers
    
    :param csv: a string of comma separated numbers
    :return: a list of the numbers in the string
    """
    return [float(num) for num in csv.split(",")]

def create_sublists(list_, no_parameters:int):
    """Returns a list of lists that have been split based upon the number 
    of parameters specified in the sublists
    
    :param list_: a list that will be split into sublists
    :param no_parameters: number of parameters per sublist
    :returns: a list of the sublists
    """
    
    list_length = len(list_)
    if list_length % no_parameters != 0:
        raise ValueError("Provided list is not divisible by the number of parameters")
    no_sublists = int(list_length/no_parameters)
    sublists = []
    for i in range(no_sublists):
        sublist = []
        for j in range(no_parameters):
            sublist.append(list_.pop(0))
        sublists.append(sublist)
    return sublists


def parse_moveto(command:str) -> list:
    """Returns a list of the coordinates given in an absolute or relative 
    moveto command.
    
    :param command: a moveto command with a series of [x,y] coordinates
    :return: a list of lists of the coordinates in the command
    """
    if not command.startswith(("m", "M")):
        raise ValueError("moveto commands must start with either m or M")
    
    command = clean_command(command)
    numbers = csv_to_float(command)
    coordinates = create_sublists(numbers, 2)
    return coordinates

def parse_arc(command:str) -> list:
    """Returns a list of lists of the parameters given in an absolute or 
    relative     elliptical arc command.
    
    :param command: an arc with [rx ry x-axis-rotation large-arc-flag sweep-flag x y] coordinates
    :return: a list of lists of the numbers in the command
    """
    if not command.startswith(("a", "A")):
        raise ValueError("arc commands must start with either a or A")
    command = clean_command(command)
    numbers = csv_to_float(command)
    coordinates = create_sublists(numbers, 7)
    return coordinates

def parse_lineto(command:str) -> list:
    """Returns a list of lists of the coordinates given in an absolute or 
    relative lineto command.
    
    :param command: a lineto command with a series of [x,y] coordinates
    :return: a list of lists of the coordinates in the command
    """
    if not command.startswith(("l", "L")):
        raise ValueError("lineto commands must start with either l or L")
    
    command = clean_command(command)
    numbers = csv_to_float(command)
    coordinates = create_sublists(numbers, 2)
    return coordinates

def parse_horizontal(command:str) -> list:
    """Returns a list of the lengths given in an absolute or relative 
    horizontal command.
    
    :param command: a horizontal command with a series of x coordinates
    :return: a list of the coordinates in the command
    """
    if not command.startswith(("h", "H")):
        raise ValueError("Horizontal commands must start with either h or H")
    
    command = clean_command(command)
    numbers = csv_to_float(command)
    return numbers

def parse_vertical(command:str) -> list:
    """Returns a list of the lengths given in an absolute or relative 
    vertical command.
    
    :param command: a vertical command with a series of y coordinates
    :return: a list of the coordinates in the command
    """
    if not command.startswith(("v", "V")):
        raise ValueError("Vertical commands must start with either v or V")
    
    command = clean_command(command)
    numbers = csv_to_float(command)
    return numbers