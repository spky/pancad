"""A module providing a class to represent the file and collect xml 
elements to be written to files.
"""

import svg_writers as sw
import svg_generators as sg

class SVGFile:
    
    def __init__(self, name: str, line_style: dict = None) -> None:
        if name.endswith(".svg"):
            self.name = name
        else:
            self.name = name + ".svg"
        self.active_svg = None
        self.active_g = None
        # Multiple svg tags is supported, but browsers do not like it
        self.svgs = {}
        self.declaration = sw.xml_declaration()
        if line_style is None:
            line_style = {
                "fill": "none",
                "stroke": "#000000",
                "stroke-width": "0.010467px",
                "stroke-linecap": "butt",
                "stroke-linejoin": "miter",
                "stroke-opacity": 1,
            }
        self.default_line_style = sg.make_style(line_style)
    
    def activate_svg(self, id_: str) -> None:
        """Activates the svg with the given id, if it exists"""
        if id_ in self.svgs:
            self.active_svg = id_
            self.active_g = None
            return None
        else:
            raise ValueError("Provided id '"
                             + id_
                             + "' does not appear as an svg in the file")
    
    def activate_g(self, id_: str) -> None:
        """Activates the g with the given id in the active svg, if it 
        exists"""
        find_term = "./g[@id='" + id_ + "']"
        g = self.svgs[self.active_svg].find(find_term)
        if g is not None:
            self.active_g = id_
        else:
            raise ValueError("Provided id '"
                             + id_ 
                             + "' does not appear as a g element in the active svg")
    
    def add_svg(
            self, id_: str = None, width: str = "0in", height: str = "0in",
            property_dicts: list = None) -> None:
        """Adds a new svg element and sets it as the active svg"""
        if id_ is None:
            id_ = "svg" + str(len(self.svgs) + 1)
        svg = sw.make_svg_element(id_, width, height, property_dicts)
        self.svgs[id_] = svg
        self.activate_svg(id_)
    
    def add_g(self, id_: str, property_dicts: list = None) -> None:
        """Adds a new g element to the active svg and sets it as the 
        active layer"""
        g = sw.make_g_element(id_, property_dicts)
        self.svgs[self.active_svg].append(g)
        self.activate_g(id_)
    
    def add_path(
            self, id_: str, d: str, style: str = None,
            property_dicts: list = None) -> None:
        """Adds a new path element to the active layer"""
        if style is None:
            style = self.default_line_style
        path = sw.make_path_element(id_, style, d, property_dicts)
        find_term = "./g[@id='" + self.active_g + "']"
        self.svgs[self.active_svg].find(find_term).append(path)
    
    def add_circle(
            self, id_: str, center_xy: list[str, str], radius: str, 
            style: str = None, property_dicts: list = None) -> None:
        """Adds a new circle element to the active layer"""
        if style is None:
            style = self.default_line_style
        circle = sw.make_circle_element(id_, style, center_xy, radius,
                                        property_dicts)
        find_term = "./g[@id='" + self.active_g + "']"
        self.svgs[self.active_svg].find(find_term).append(circle)
    
    def write_single_svg(
            self, svg_id: str, folder: str, indent: str = "  ") -> None:
        """Writes the specified svg's information to a file in the 
        given folder"""
        svg_element = [self.svgs[svg_id]]
        top = sw.svg_top(svg_element, declaration = self.declaration)
        if folder.endswith("/"):
            filename = folder + self.name
        else:
            filename = folder + "/" + self.name
        sw.write_xml(filename, top)
    
    def write(self, folder: str, indent: str = "  ") -> None:
        """Writes all internal svgs to a file in the given folder"""
        svg_elements = []
        for s in self.svgs:
            svg_elements.append(self.svgs[s])
        top = sw.svg_top(svg_elements, declaration = self.declaration)
        if folder.endswith("/"):
            filename = folder + self.name
        else:
            filename = folder + "/" + self.name
        sw.write_xml(filename, top)
        