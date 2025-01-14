"""A module to provide functions for parsing svg tag information out into 
other formats
"""

import re
import trigonometry as trig

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

def split_path_data(path_data: str) -> list:
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

def path_data_to_dicts(path_data: str, path_id: str = "") -> list[dict]:
    """Returns a list of dictionaries for each command in the svg path's 
    data in the order that they appear. Each dictionary has the geometry 
    the command describes in strictly absolute coordinates
    :param path_data: path data of an svg path object
    :returns: a list of geometry dictionaries
    """
    cmd_list = split_path_data(path_data)
    current_point = [0, 0]
    shape_count = 0
    out = []
    for i, cmd in enumerate(cmd_list):
        match path_cmd_type(cmd):
            case "absolute_moveto":
                (
                    current_point, lines,
                    subpath_initial_point, shape_count
                ) = absolute_moveto_to_dict(cmd,path_id,shape_count)
                out.extend(lines)
            case "relative_moveto":
                (
                    current_point, lines,
                    subpath_initial_point, shape_count
                ) = relative_moveto_to_dict(cmd, current_point, i,
                                            path_id, shape_count)
                out.extend(lines)
            case "absolute_arc":
                (
                    current_point, arcs, subpath_initial_point, shape_count
                ) = arc_to_dict(cmd, current_point, path_id,
                                shape_count, False)
                out.extend(arcs)
            case "relative_arc":
                (
                    current_point, arcs, subpath_initial_point, shape_count
                ) = arc_to_dict(cmd, current_point, path_id,
                                shape_count, True)
                out.extend(arcs)
            case "closepath":
                if subpath_initial_point is not None:
                    out.append({
                        "id": path_id + "_" + str(shape_count),
                        "start": current_point,
                        "end": subpath_initial_point,
                        "geometry_type": "line",
                    })
                    current_point = subpath_initial_point
            case "absolute_lineto":
                pass
            case "relative_lineto":
                pass
            case "absolute_horizontal":
                pass
            case "relative_horizontal":
                pass
            case "absolute_vertical":
                pass
    return out

def path_cmd_type(path_data_cmd: str) -> str:
    """Returns the type of a path command. Will only parse one command at 
    a time!
    :param path_data_cmd: one command of an svg path object's path data
    :returns: the type of the command
    """
    match path_data_cmd[0]:
        case "M":
            return "absolute_moveto"
        case "m":
            return "relative_moveto"
        case "A":
            return "absolute_arc"
        case "a":
            return "relative_arc"
        case "z" | "Z":
            return "closepath"
        case "L":
            return "absolute_lineto"
        case "l":
            return "relative_lineto"
        case "H":
            return "absolute_horizontal"
        case "h":
            return "relative_horizontal"
        case "V":
            return "absolute_vertical"
        case "v":
            return "relative_vertical"
        case _:
            raise ValueError(str(path_data_cmd[0])
                             + " is not a supported command type")

def clean_command(command:str) -> str:
    """Returns a string with just the data part of a path data command 
    separated by commas. Assumes the first character is the command's 
    letter
    
    :param command: an svg command
    :return: the data part of the command separated just by commas
    """
    command = command[1:]
    command = command.strip()
    command = command.replace(", ",",")
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

def absolute_moveto_to_dict(command: str, path_id: str,
                            shape_count: int) -> tuple:
    """Returns a tuple of geometry info represented by an svg absolute 
    moveto command. Intended for use in the path_data_to_dicts function
    
    :param command: An absolute moveto command
    :param path_id: The id of the moveto command's path element
    :param shape_count: How many shapes have already been read in the path
    """
    coordinates = parse_moveto(command)
    point_count = len(coordinates)
    lines = []
    if point_count == 1:
        current_point = coordinates[0]
        subpath_initial_point = None
    elif point_count > 1:
        subpath_initial_point = coordinates[0]
        for i in range(1, point_count):
            current_point = coordinates[i]
            lines.append({
                "id": path_id + "_" + str(shape_count),
                "start": coordinates[i-1], "end": current_point,
                "geometry_type": "line",
            })
            shape_count += 1
    else:
        raise ValueError("A moveto cannot have 0 points")
    return current_point, lines, subpath_initial_point, shape_count

def relative_moveto_to_dict(command: str, current_point: list,
                            command_no: int, path_id: str,
                            shape_count: int) -> tuple:
    """Returns a tuple of the geometry info represented by an svg relative 
    moveto command. Intended for use in the path_data_to_dicts function
    
    :param command: An relative moveto command
    :param current_point: The current svg point
    :param command_no: How many commands have been read in the path
    :param path_id: The id of the moveto command's path element
    :param shape_count: How many shapes have already been read in the path
    """
    coordinates = parse_moveto(command)
    point_count = len(coordinates)
    lines = []
    if command_no == 0:
        # If path's first cmd, SVG treats 1st cmd as absolute
        current_point = coordinates[0]
    else:
        current_point = [current_point[0] + coordinates[0][0],
                         current_point[1] + coordinates[0][1]]
    if point_count == 1:
        # If there is only one point, no lines are created
        subpath_initial_point = None
    elif point_count > 1:
        subpath_initial_point = current_point
        for i in range(1, point_count):
            next_point = [current_point[0] + coordinates[i][0],
                          current_point[1] + coordinates[i][1]]
            lines.append({
                "id": path_id + "_" + str(shape_count),
                "start": current_point,
                "end": next_point,
                "geometry_type": "line",
            })
            current_point = next_point
            shape_count += 1
    else:
        raise ValueError("A moveto cannot have 0 points")
    return current_point, lines, subpath_initial_point, shape_count

def parse_arc(command:str) -> list:
    """Returns a list of lists of the parameters given in an absolute or 
    relative elliptical arc command.
    
    :param command: an arc with [rx ry x-axis-rotation large-arc-flag sweep-flag x y] coordinates
    :return: a list of lists of the numbers in the command
    """
    if not command.startswith(("a", "A")):
        raise ValueError("arc commands must start with either a or A")
    command = clean_command(command)
    numbers = csv_to_float(command)
    coordinates = create_sublists(numbers, 7)
    return coordinates

def arc_to_dict(command: str, current_point: list, path_id: str,
                shape_count: int, relative: bool) -> tuple:
    """Returns a tuple of geometry info represented by an svg elliptical 
    arc command. Intended for use in the path_data_to_dicts function. Will 
    identify the arc as circular if rx = ry
    
    :param command: An absolute elliptical arc command
    :param current_point: The current svg point, where the arc will start
    :param path_id: the id of the arc command's path element
    :param shape_count: How many shapes have already been read in the path
    """
    arc_cmds = parse_arc(command)
    arcs = []
    for arc in arc_cmds:
        subpath_initial_point = current_point
        if relative:
            next_point = [current_point[0] + arc[5],
                          current_point[1] + arc[6]]
        else:
            next_point = [arc[5], arc[6]]
        rx, ry = arc[0], arc[1]
        if rx == ry:
            geometry_type = "circular_arc"
        else:
            geometry_type = "elliptical_arc"
        arcs.append({
            "id": path_id + "_" + str(shape_count),
            "point_1": current_point,
            "point_2": next_point,
            "x_radius": rx,
            "y_radius": ry,
            "x_axis_rotation": arc[2],
            "large_arc_flag": arc[3],
            "sweep_flag": arc[4],
            "geometry_type": geometry_type,
        })
        current_point = next_point
        shape_count += 1
    return current_point, arcs, subpath_initial_point, shape_count

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