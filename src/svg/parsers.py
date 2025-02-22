"""A module to provide functions for parsing svg tag information out into 
other formats
"""

import re

import trigonometry as trig
import svg.validators as sv

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
                    out.append(
                        line(path_id, shape_count,
                             current_point, subpath_initial_point)
                    )
                    current_point = subpath_initial_point
                    subpath_initial_point = None
            case (
                     "absolute_lineto" | "relative_lineto"
                     | "absolute_horizontal" | "relative_horizontal"
                     | "absolute_vertical" | "relative_vertical"
                 ):
                (
                    current_point, lines,
                    subpath_initial_point, shape_count
                ) = lineto_to_dict(cmd, current_point, path_id, shape_count)
                out.extend(lines)
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

def length_unit(setting: str | float) -> None | str:
    """Returns the unit of the given length setting as a string. Will 
    return an empty string if no unit is in the string or if the setting 
    is a number
    
    :param setting: length setting for an svg tag
    :returns: the unit of the length
    """
    if isinstance(setting, int) or isinstance(setting, float):
        return ""
    else:
        number = sv.length_value(setting) # Also checks the validity of the setting
        return setting.replace(str(number), "")

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
    :returns: tuple of (current point, a list of line dictionaries, sub-path initial 
              point, and incremented shape count).
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
            lines.append(line(path_id, shape_count,
                              coordinates[i-1], current_point))
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
    :returns: tuple of (current point, lines dictionary, sub-path initial 
              point, and incremented shape count)
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
            lines.append(line(path_id, shape_count,
                              current_point, next_point))
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
    
    :param command: An elliptical arc command
    :param current_point: The current svg point, where the arc will start
    :param path_id: the id of the arc command's path element
    :param shape_count: How many shapes have already been read in the path
    :param relative: Absolute coordinates if false, relative if true
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
        large_arc = True if arc[3] else False
        sweep = True if arc[4] else False
        if rx == ry:
            arcs.append(
                circular_arc(path_id, shape_count,
                             current_point, next_point,
                             rx, large_arc, sweep)
            )
        else:
            arcs.append(
                elliptical_arc(path_id, shape_count,
                               current_point, next_point,
                               rx, ry, arc[2], large_arc, sweep)
            )
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

def lineto_to_dict(command: str, current_point: list, path_id: str,
                   shape_count: int) -> tuple:
    """Returns a tuple of geometry info represented by svg lineto, 
    horizontal and vertical commands. Intended for use in the 
    path_data_to_dicts function.
    
    :param command: A lineto, horizontal, or vertical command
    :param current_point: The current svg point
    :param path_id: the id of the command's path element
    :param shape_count: How many shapes have already been read in the path
    :param relative: Absolute coordinates if false, relative if true
    """
    cmd_type = path_cmd_type(command)
    relative = True if cmd_type.startswith("relative") else False
    line_pts = [current_point]
    lines = []
    if cmd_type.endswith("lineto"):
        coordinates = parse_lineto(command)
        subpath_initial_point = current_point
        if relative:
            for c in coordinates:
                line_pts.append([current_point[0] + c[0],
                                current_point[1] + c[1]])
        else:
            line_pts.extend(coordinates)
        current_point = line_pts[-1]
    elif cmd_type.endswith("horizontal"):
        subpath_initial_point = None
        x_values = parse_horizontal(command)
        for x in x_values:
            if relative:
                next_point = [current_point[0] + x, current_point[1]]
            else:
                next_point = [x, current_point[1]]
            line_pts.append(next_point)
            current_point = next_point
    elif cmd_type.endswith("vertical"):
        subpath_initial_point = None
        y_values = parse_vertical(command)
        for y in y_values:
            if relative:
                next_point = [current_point[0], current_point[1] + y]
            else:
                next_point = [current_point[0], y]
            line_pts.append(next_point)
            current_point = next_point
    else:
        raise ValueError(str(command) + " is not v/V/h/H/l/L!")
    point_count = len(line_pts)
    for i in range(1, point_count):
        current_point = line_pts[i]
        lines.append(line(path_id, shape_count, line_pts[i-1], line_pts[i]))
        shape_count += 1
    return current_point, lines, subpath_initial_point, shape_count

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

def line(
        path_id: str, shape_count: int,
        start: list[float, float], end: list[float, float]) -> dict:
    """Returns a dictionary defining a svg line
    
    :param path_id: id of the svg path the line is in
    :param shape_count: the shape number of the line in the svg path
    :param start: the start point of the line, [x, y]
    :param end: the end point of the line, [x, y]
    :returns: A dictionary with keys for id, start, end, and 
              geometry_type. geometry_type is set to line.
    """
    return {
        "id": path_id + "_" + str(shape_count),
        "start": start, "end": end, "geometry_type": "line"
    }

def circular_arc(
        path_id: str, shape_count: int,
        start: list[float, float], end: list[float, float],
        radius: float, large_arc_flag: bool, sweep_flag: bool
    ) -> dict:
    """Returns a dictionary of defining a svg circular arc
    
    :param path_id: id of the svg path the arc is in
    :param shape_count: the shape number of the line in the svg path
    :param start: the start point of the arc, [x, y]
    :param end: the end point of the arc, [x, y]
    :param radius: the radius of the associated circle
    :param large_arc_flag: svg large arc flag
    :param sweep_flag: svg sweep flag
    :returns: A dictionary with keys for id, start, end, radius,
              large_arc_flag, sweep_flag and geometry_type. geometry_type
              is set to circular arc.
    """
    return {
        "id": path_id + "_" + str(shape_count),
        "start": start, "end": end, "radius": radius,
        "large_arc_flag": large_arc_flag, "sweep_flag": sweep_flag,
        "geometry_type": "circular_arc"
    }

def elliptical_arc(
        path_id: str, shape_count: int,
        start: list[float, float], end: list[float, float],
        x_radius: float, y_radius: float,
        x_axis_rotation: float, large_arc_flag: bool, sweep_flag: bool
    ) -> dict:
    """Returns a dictionary of defining an svg elliptical arc
    
    :param path_id: id of the svg path the arc is in
    :param shape_count: the shape number of the line in the svg path
    :param start: the start point of the arc, [x, y]
    :param end: the end point of the arc, [x, y]
    :param x_radius: the major axis radius of the associated ellipse
    :param y_radius: the minor axis radius of the associated ellipse
    :param x_axis_rotation: the major axis angle of the associated ellipse
    :param large_arc_flag: svg large arc flag
    :param sweep_flag: svg sweep flag
    :returns: A dictionary with keys for id, start, end, x_radius, 
              y_radius, x_axis_rotation, large_arc_flag, sweep_flag, and 
              geometry_type. geometry_type is set to elliptical_arc.
    """
    return {
        "id": path_id + "_" + str(shape_count),
        "start": start, "end": end,
        "x_radius": x_radius, "y_radius": y_radius,
        "x_axis_rotation": x_axis_rotation,
        "large_arc_flag": large_arc_flag, "sweep_flag": sweep_flag,
        "geometry_type": "elliptical_arc"
    }

def circle(id_: str, radius: float, center: list[float, float]):
    """Returns a dictionary defining an circle
    
    :param id_: id of the svg circle
    :param radius: radius of the circle
    :param center: center point of the circle, [x, y]
    :returns: A dictionary with keys for id, radius, center, and 
              geometry_type. geometry_type is set to circle.
    """
    return {
        "id": id_, "radius": radius,
        "center": center, "geometry_type": "circle"
    }