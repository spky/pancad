import re

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
        
        cmd = SVGPath.match_front_cmd(value)
        out = []
        match cmd["type"]:
            case "M" | "m":
                out.append({
                "type": cmd["type"],
                "coordinates": SVGPath._parse_coordinate_string(
                                           cmd["match"]["coord"]),
                "leftover": cmd["match"]["leftover"]
                })
            case _:
                out = None
        return out
    
    @staticmethod
    def match_front_cmd(path_data):
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
    
    @staticmethod
    def absolute_move_to(coordinate_list):
        first_point = coordinate_list.pop(0)
        command = "M " + str(first_point[0]) + " " + str(first_point[1])
        for c in coordinate_list:
            command += "\nM " + str(c[0]) + " " + str(c[1])
        return command
    
    @staticmethod
    def _parse_coordinate_string(coordinate_string):
        out = {}
        coordinate_string = coordinate_string.strip()
        
        xy_pattern = "([-+]?[0-9]*\.?[0-9]+)[ |,]*([-+]?[0-9]*\.?[0-9]+)"
        coordinate_re = re.compile(xy_pattern)
        coordinate_list = re.findall(coordinate_re, coordinate_string)
        
        out = []
        for c in coordinate_list:
            pair = [float(c[0]), float(c[1])]
            out.append(pair)
        return out