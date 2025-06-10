""" A module providing the SVG path element class that converts path elements 
into PanCAD geometry and vice-versa.

The Path class is primarily intended to generate PanCAD geometry using its 
initialization 'd' (the string representing the path's path data) argument.

"""
import re
from itertools import islice

import numpy as np

from PanCAD.graphics.svg import (
    PathParameterType, PathCommandCharacter as CmdChar
)
from PanCAD.graphics.svg.grammar_regex import command, number, SVG_CMD_TYPES
from PanCAD.graphics.svg.parsers import to_number

from PanCAD.geometry import LineSegment, Point, Line, Plane, CoordinateSystem

class Path:
    """A class that represents svg path elements and syncs them with PanCAD 
    geometry.
    
    :param svg_id: The id of the svg path element. Will be prepended to each 
        geometry element's id
    :param d: The path element's path data string. Will be translated into PanCAD 
        geometry
    """
    
    COORDINATE_DELIMITER = ","
    PARAMETER_DELIMITER = " "
    POST_COMMAND_CHAR = " "
    PRE_COMMAND_CHAR = " "
    
    def __init__(self, svg_id: str, d: str=None):
        self._geometry = []
        self.svg_id = svg_id
        self.d = d
    
    # Getters #
    @property
    def d(self) -> str:
        """The svg path data for the path element.
        
        :getter: Returns the path data string
        :setter: Sets path data string and updates the path's geometry
        """
        return self._d
    
    @property
    def geometry(self) -> list:
        """The PanCAD geometry elements that represent the path data
        
        :getter: Returns a list of PanCAD geometry
        :setter: Sets the PanCAD geometry and syncs the path data
        """
        return self._geometry
    
    @property
    def svg_id(self) -> str:
        return self._svg_id
    
    # Setters #
    @d.setter
    def d(self, path_data: str):
        self._d = path_data
        separated_cmds = self._separate_path_data(path_data)
        explicit_cmds = self._to_explicit(separated_cmds)
        self._geometry = self._to_geometry(explicit_cmds)
        self._update_geometry_uids()
    
    @geometry.setter
    def geometry(self, geometry_list: list):
        explicit_cmds = cls._geometry_to_explicit(geometry_list)
        implicit_cmds = cls._to_implicit(explicit_cmds)
        self.d = self._implicit_to_string(implicit_cmds)
    
    @svg_id.setter
    def svg_id(self, new_id: str):
        self._svg_id = new_id
        if len(self.geometry) > 0:
            self._update_geometry_uids()
    
    # Class Methods #
    @classmethod
    def from_geometry(cls, svg_id: str, geometry_list: list):
        """Initializes a Path element purely from PanCAD elements"""
        explicit_cmds = cls._geometry_to_explicit(geometry_list)
        implicit_cmds = cls._to_implicit(explicit_cmds)
        path_data = cls._implicit_to_string(implicit_cmds)
        return cls(svg_id, path_data)
    
    # Static Methods #
    @staticmethod
    def _geometry_to_explicit(geometry_list: list) -> list[tuple[str, str]]:
        """Creates a list of explicit (i.e. one parameter per command) path data 
        commands from a list of PanCAD geometry.
        """
        cmds = []
        previous_pt = None
        for geometry in geometry_list:
            if isinstance(geometry, LineSegment):
                if previous_pt is None or previous_pt != geometry.point_a:
                    cmds.append(
                        (CmdChar.M, tuple(geometry.point_a))
                    )
                cmds.append(
                    (CmdChar.L, tuple(geometry.point_b))
                )
                previous_pt = geometry.point_b
            elif isinstance(geometry, (Point, Line, Plane, CoordinateSystem)):
                raise ValueError(f"{geometry.__class__} cannot be represented"
                                 " by svg path data")
            else:
                raise ValueError(f"{geometry.__class__} not recognized")
        return cmds
    
    @staticmethod
    def _normalize_d(path_data: str, explicit=False):
        """Returns a path data string with consistent formatting since the input 
        path data can be any format as long as it meets the svg standard.
        """
        cmds = Path._separate_path_data(path_data)
        if explicit:
            cmds = Path._to_explicit(cmds)
            cmds = [(character, [params]) for character, params in cmds]
        return Path._implicit_to_string(cmds)
    
    @staticmethod
    def _implicit_to_string(cmds: list) -> str:
        """Returns an equivalent string from a series of implicit commands.
        """
        normalized_cmds = []
        for character, params in cmds:
            normalized_params = []
            for p in params:
                str_p = map(str, p)
                normalized_params.append(Path.COORDINATE_DELIMITER.join(str_p))
            normalized_cmds.append(
                character + Path.POST_COMMAND_CHAR
                + Path.PARAMETER_DELIMITER.join(normalized_params)
            )
        return Path.PRE_COMMAND_CHAR.join(normalized_cmds)
    
    @staticmethod
    def _separate_path_data(path_data: str) -> list[tuple[str, str]]:
        """Separates a path data string into two length tuples consisting of its 
        character and its associated parameters. The parameters will maintain the
        implied commands.
        
        :param path_data: A string of svg path data commands
        :returns: A tuple where the first element is the command's character and 
            the second element is the command's parameter string
        """
        d_commands = re.findall(command, path_data)
        
        cmd_params = []
        for cmd in d_commands:
            character = cmd[0]
            parameters = re.findall(number.ca, cmd)
            parameters = map(to_number, parameters)
            parameters = Path._batch_command(character, parameters)
            cmd_params.append(
                (character, list(parameters))
            )
        return cmd_params
    
    @staticmethod
    def _batch_command(character: str, parameters: list[float|int]) -> tuple:
        """Returns the command's parameters in batches according to its command 
        type
        """
        for cmd_type, cmd_letters in SVG_CMD_TYPES.items():
            if character in cmd_letters:
                match cmd_type:
                    case PathParameterType.PAIR:
                        batch_size = 2
                        break
                    case PathParameterType.SINGLE:
                        batch_size = 1
                        break
                    case PathParameterType.ARC:
                        batch_size = 7
                        break
                    case PathParameterType.CLOSEPATH:
                        return parameters
        
        # itertools.batched is not in Python 3.11, so its equivalent is below
        while batch := tuple(islice(parameters, batch_size)):
            if len(batch) != batch_size:
                raise ValueError(f"Incomplete {cmd_type.name} parameters,"
                                 f" must have {batch_size} elements")
            elif batch_size == 1:
                yield batch[0]
            else:
                yield batch
    
    @staticmethod
    def _to_explicit(cmd_params: list[tuple[str, str]]
                     ) -> list[tuple[str, str]]:
        """Returns a list of explicit commands from a list of separated command 
        tuples
        """
        explicit = []
        for character, params in cmd_params:
            match character:
                case CmdChar.M:
                    explicit.append((character, params.pop(0)))
                    explicit.extend(
                        [(CmdChar.L, p) for p in params]
                    )
                case CmdChar.m:
                    if len(explicit) == 0:
                        # If m is the first command in the path, it is absolute
                        explicit.append((CmdChar.M, params.pop(0)))
                    else:
                        explicit.append((character, params.pop(0)))
                    explicit.extend(
                        [(CmdChar.l, p) for p in params]
                    )
                case CmdChar.z | CmdChar.Z:
                    explicit.append((character, None))
                case _:
                    if len(explicit) == 0:
                        raise ValueError("First command must be m or M,"
                                         f"given: {character}")
                    else:
                        explicit.extend([(character, p) for p in params])
        return explicit
    
    @staticmethod
    def _to_implicit(explicit_cmds: list[tuple[str, tuple]]
                     ) -> list[tuple[str, list]]:
        """Returns a smaller set of commands that take advantage of implicit 
        commands in svg.
        
        """
        character, coordinate = explicit_cmds.pop(0)
        previous_character = character
        combine_with_previous = False
        cmds = [(character, [coordinate])]
        for character, param in explicit_cmds:
            
            if character == CmdChar.L and previous_character == CmdChar.M:
                character, coordinates = cmds.pop(-1)
                param = coordinates + [param]
                combine_with_previous = False
            elif character == CmdChar.l and previous_character == CmdChar.m:
                character, coordinates = cmds.pop(-1)
                param = coordinates + [param]
                combine_with_previous = False
            elif (character not in (CmdChar.m, CmdChar.M)
                    and character == previous_character):
                character, coordinates = cmds.pop(-1)
                param = coordinates + [param]
                combine_with_previous = False
            else:
                param = [param]
            cmds.append((character, param))
            previous_character = character
        return cmds
    
    @staticmethod
    def _to_geometry(explicit_cmds: list[tuple]) -> list:
        """Returns a list of PanCAD geometry from a list of explicit svg path 
        data commands. Here, explicit commands are defined as svg path data 
        commands that only contain a single set of their parameters with no 
        implied continuation parameters. Ex: M 1 1 L 2 2 and not M 1 1 2 2
        
        :param explicit_cmds: A list of 2 length tuples containing the command 
            character as the first element and its parameters as the second 
            element
        :returns: A list of equivalent PanCAD Geometry
        """
        geometry = []
        _, coordinate = explicit_cmds.pop(0)
        current_pt = Point(coordinate)
        sub_path_pt = current_pt.copy()
        for character, param in explicit_cmds:
            match character:
                case CmdChar.M:
                    # Absolute Moveto
                    current_pt = Point(param)
                    sub_path_pt = current_pt.copy()
                case CmdChar.m:
                    # Relative Moveto
                    current_pt = Point(np.array(current_pt) + np.array(param))
                    sub_path_pt = current_pt.copy()
                case CmdChar.L:
                    # Absolute Lineto
                    geometry.append(LineSegment(current_pt, param))
                    current_pt = Point(param)
                case CmdChar.l:
                    # Relative Lineto
                    new_pt = Point(np.array(current_pt) + np.array(param))
                    geometry.append(LineSegment(current_pt, new_pt))
                    current_pt = new_pt.copy()
                case CmdChar.H:
                    # Absolute Horizontal Lineto
                    new_pt = Point(param, current_pt.y)
                    geometry.append(LineSegment(current_pt, new_pt))
                    current_pt = new_pt.copy()
                case CmdChar.h:
                    # Relative Horizontal Lineto
                    new_pt = Point(param + current_pt.x, current_pt.y)
                    geometry.append(LineSegment(current_pt, new_pt))
                    current_pt = new_pt.copy()
                case CmdChar.V:
                    # Absolute Vertical Lineto
                    new_pt = Point(current_pt.x, param)
                    geometry.append(LineSegment(current_pt, new_pt))
                    current_pt = new_pt.copy()
                case CmdChar.v:
                    # Relative Vertical Lineto
                    new_pt = Point(current_pt.x, param + current_pt.y)
                    geometry.append(LineSegment(current_pt, new_pt))
                    current_pt = new_pt.copy()
                case CmdChar.z | CmdChar.Z:
                    # Closepath
                    geometry.append(LineSegment(current_pt, sub_path_pt))
                    current_pt = sub_path_pt.copy()
                case CmdChar.a:
                    raise NotImplementedError(f"{character} not implemented yet")
                case CmdChar.A:
                    raise NotImplementedError(f"{character} not implemented yet")
                case CmdChar.c:
                    raise NotImplementedError(f"{character} not implemented yet")
                case CmdChar.C:
                    raise NotImplementedError(f"{character} not implemented yet")
                case CmdChar.s:
                    raise NotImplementedError(f"{character} not implemented yet")
                case CmdChar.S:
                    raise NotImplementedError(f"{character} not implemented yet")
                case CmdChar.q:
                    raise NotImplementedError(f"{character} not implemented yet")
                case CmdChar.Q:
                    raise NotImplementedError(f"{character} not implemented yet")
                case CmdChar.t:
                    raise NotImplementedError(f"{character} not implemented yet")
                case CmdChar.T:
                    raise NotImplementedError(f"{character} not implemented yet")
                case _:
                    raise ValueError(f"{character} not recognized")
        return geometry
    
    # Private Methods #
    def _update_geometry_uids(self):
        """Syncs the uids on the geometry with the svg_id"""
        num_id_digits = len(
            str(len(self._geometry))
        )
        for i, geometry in enumerate(self._geometry):
            geometry_id = str(i).zfill(num_id_digits)
            geometry.uid = f"{self.svg_id}_{geometry_id}"