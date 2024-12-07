import re

import svg_parsers as sp

class SVGPath:
    
    def __init__(self, element):
        self.element = element
        self.svg_id = element.getAttribute("id")
        self.style = element.getAttribute("style")
        self.d = element.getAttribute("d")
    
    
    @property
    def d(self):
        return self._d
    
    @d.setter
    def d(self, value):
        self.element.setAttribute("d", value)
        self._d = value
    
    @staticmethod
    def _parse_path_data(value):
        """returns the first command set of a path data string"""
        
        cmd = sp.match_front_cmd(value)
        out = []
        match cmd["type"]:
            case "M" | "m":
                out.append({
                "type": cmd["type"],
                "coordinates": sp.parse_coordinate_string(
                                           cmd["match"]["coord"]),
                "leftover": cmd["match"]["leftover"]
                })
            case _:
                out = None
        return out
    
    @staticmethod
    def absolute_move_to(coordinate_list):
        first_point = coordinate_list.pop(0)
        command = "M " + str(first_point[0]) + " " + str(first_point[1])
        for c in coordinate_list:
            command += "\nM " + str(c[0]) + " " + str(c[1])
        return command