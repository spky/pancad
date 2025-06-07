""" A module providing the SVG path element class that converts path elements 
into PanCAD geometry and vice-versa
"""
import re
from itertools import islice

import numpy as np

from PanCAD.graphics.svg import PathParameterType, PathCommandCharacter
from PanCAD.graphics.svg.grammar_regex import command, number, SVG_CMD_TYPES
from PanCAD.graphics.svg.parsers import to_number

from PanCAD.geometry import LineSegment, Point

class Path:
    
    def __init__(self, svg_id: str=None, d: str=None):
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
        return self._geometry
    
    # Setters #
    @d.setter
    def d(self, path_data: str):
        self._d = path_data
        self._geometry = self._parse_path_data(path_data)
    
    @staticmethod
    def _parse_path_data(path_data: str) -> tuple:
        d_commands = re.findall(command, path_data)
        
        cmd_params = []
        for cmd in d_commands:
            character = cmd[0]
            parameters = re.findall(number.ca, cmd)
            parameters = map(to_number, parameters)
            parameters = Path._batch_command(character, parameters)
            cmd_params.append((character, list(parameters)))
        explicit_cmds = Path._make_explicit(cmd_params)
        return Path._to_geometry(explicit_cmds)
    
    @staticmethod
    def _batch_command(character: str, parameters: list[float|int]) -> tuple:
        """Returns the command's parameters in batches according to its command 
        type"""
        for cmd_type, cmd_letters in SVG_CMD_TYPES.items():
            if character in cmd_letters:
                itercopy = parameters
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
    
    def _make_explicit(cmd_params: list[tuple[str, tuple]]) -> list[tuple]:
        """Returns a list of explicit commands from a list of raw command 
        tuples"""
        explicit = []
        for character, params in cmd_params:
            match character:
                case PathCommandCharacter.M:
                    explicit.append((character, params.pop(0)))
                    explicit.extend(
                        [(PathCommandCharacter.L.value, p) for p in params]
                    )
                case PathCommandCharacter.m:
                    if len(explicit) == 0:
                        # If m is the first command in the path, it is absolute
                        explicit.append((PathCommandCharacter.M, params.pop(0)))
                    else:
                        explicit.append((character, params.pop(0)))
                    explicit.extend(
                        [(PathCommandCharacter.l.value, p) for p in params]
                    )
                case PathCommandCharacter.z | PathCommandCharacter.Z:
                    explicit.append((character, None))
                case _:
                    if len(explicit) == 0:
                        raise ValueError("First command must be m or M,"
                                         f"given: {character}")
                    else:
                        explicit.extend([(character, p) for p in params])
        return explicit
    
    def _to_geometry(explicit_cmds: list[tuple]) -> list:
        """Returns a list of PanCAD geometry from a list of explicit svg path 
        data commands"""
        geometry = []
        _, coordinate = explicit_cmds.pop(0)
        current_pt = Point(coordinate)
        sub_path_pt = current_pt.copy()
        for character, parameter in explicit_cmds:
            match character:
                case PathCommandCharacter.M:
                    current_pt = Point(parameter)
                    sub_path_pt = current_pt.copy()
                case PathCommandCharacter.m:
                    current_pt = Point(
                        np.array(current_pt) + np.array(parameter)
                    )
                    sub_path_pt = current_pt.copy()
                case PathCommandCharacter.L:
                    geometry.append(LineSegment(current_pt, parameter))
                    current_pt = Point(parameter)
                case PathCommandCharacter.l:
                    new_pt = Point(np.array(current_pt) + np.array(parameter))
                    geometry.append(LineSegment(current_pt, new_pt))
                    current_pt = new_pt.copy()
                case PathCommandCharacter.H:
                    new_pt = Point(parameter, current_pt.y)
                    geometry.append(LineSegment(current_pt, new_pt))
                    current_pt = new_pt.copy()
                case PathCommandCharacter.h:
                    new_pt = Point(parameter + current_pt.x, current_pt.y)
                    geometry.append(LineSegment(current_pt, new_pt))
                    current_pt = new_pt.copy()
                case PathCommandCharacter.V:
                    new_pt = Point(current_pt.x, parameter)
                    geometry.append(LineSegment(current_pt, new_pt))
                    current_pt = new_pt.copy()
                case PathCommandCharacter.v:
                    new_pt = Point(current_pt.x, parameter + current_pt.y)
                    geometry.append(LineSegment(current_pt, new_pt))
                    current_pt = new_pt.copy()
                case PathCommandCharacter.z | PathCommandCharacter.Z:
                    geometry.append(LineSegment(current_pt, sub_path_pt))
                    current_pt = sub_path_pt.copy()
                case _:
                    raise NotImplementedError(f"{character} not implemented yet")
        return geometry