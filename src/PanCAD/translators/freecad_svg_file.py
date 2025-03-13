"""A module providing a class that will read FreeCAD files and convert 
information in them into equvalent SVGs
"""

from __future__ import annotations

from PanCAD.svg import elements
from PanCAD.svg import element_utils as seu
from PanCAD.svg.file import SVGFile
from PanCAD.svg.generators import SVGStyle
from PanCAD.freecad import sketch_readers as fsr
from PanCAD.utils.config import Config, SettingsMissingError
# from PanCAD.freecad import object_wrappers as fcow
from PanCAD.translators import freecad_sketcher_to_svg as fc_to_svg
from PanCAD.translators import svg_to_freecad_sketcher as svg_to_fc

import Sketcher

SETTINGS = Config()

SVG_NON_CONSTRUCTION_SECTIONS = (
    "svg.geometry_style.font",
    "svg.geometry_style.text",
    "svg.geometry_style.color_and_paint",
)
SVG_CONSTRUCTION_SECTIONS = (
    "svg.construction_geometry_style"
)

if not SETTINGS.validate_options("svg"):
    raise SettingsMissingError("Settings file invalid for svg translation")

class SketchSVG(elements.svg):
    """A class representing svg elements containing FreeCAD sketch information.
    """
    
    point_radius = "0.1"
    
    def __init__(self) -> None:
        """Constructor method"""
        self.geometry_g = None
        super().__init__()
    
    @property
    def geometry(self) -> list[dict]:
        """Returns svg geometry from all the svg's subelements. Read-only.
        
        :returns: a list of svg geometry dictionaries
        """
        geo_list = []
        for shape in list(self.geometry_g):
            shape_list = []
            for geo_dict in shape.geometry:
                # points are represented as circles, so they need labeling
                if geo_dict["id"].startswith("point"):
                    geo_dict["geometry_type"] = "point"
                shape_list.append(geo_dict)
            geo_list.extend(shape_list)
        return geo_list
    
    def add_geometry(self, fc_geometry: dict) -> None:
        """Adds geometry from a FreeCAD geometry dictionary to the svg's 
        geometry group.
        
        :param fc_geometry: A dictionary containing FreeCAD geometry info
        """
        geometry_type = fc_geometry["geometry_type"]
        match geometry_type:
            case "line" | "circular_arc":
                self.geometry_g.append(elements.path(fc_geometry["id"],
                                                     fc_geometry["d"])
                )
            case "point":
                self.geometry_g.append(elements.circle(fc_geometry["id"],
                                                       fc_geometry["cx"],
                                                       fc_geometry["cy"],
                                                       self.point_radius)
                )
            case "circle":
                self.geometry_g.append(elements.circle(fc_geometry["id"],
                                                       fc_geometry["cx"],
                                                       fc_geometry["cy"],
                                                       fc_geometry["r"])
                )
            case _:
                raise ValueError(f"'{geometry_type}' is not supported")
        self._set_style(SETTINGS)
    
    def get_freecad_dict(self) -> list[dict]:
        """Returns FreeCAD geometry from all the svg's subelements.
        
        :returns: a list of FreeCAD geometry dictionaries
        """
        return svg_to_fc.translate_geometry(self.geometry)
    
    
    def _set_style(self, style_config: config.Config) -> None:
        """Sets the style of the non-construction geometry in the svg using a 
        config instance.
        
        :param style_config: The config.Config instance containing the desired 
                             settings
        """
        style = dict()
        for section in SVG_NON_CONSTRUCTION_SECTIONS:
            for option in SETTINGS.config[section]:
                option_value = SETTINGS.config[section][option]
                if option_value is not None:
                    style[option] = option_value
        new_style = SVGStyle()
        new_style.set_from_dict(style)
        self.geometry_g.set("style", new_style.string)
    
    @classmethod
    def from_sketch(cls, sketch: Sketcher.Sketch,
                    unit: str) -> FreeCADSketchSVG:
        """Returns a new SketchSVG made from a FreeCAD Sketch
        
        :param sketch: A FreeCAD Sketcher.Sketch object to convert to svg
        :param unit: The length unit used by the sketch
        :returns: A new FreeCAD SketchSVG object
        """
        new_sketch_svg = cls()
        new_sketch_svg.unit = unit
        new_sketch_svg.Label = sketch.Label
        # Non-construction group
        new_sketch_svg.geometry_g = elements.g(new_sketch_svg.Label
                                               + "_geometry")
        new_sketch_svg.append(new_sketch_svg.geometry_g)
        freecad_geometry = fsr.read_sketch_geometry(sketch)
        svg_geometry = fc_to_svg.translate_geometry(freecad_geometry)
        for geometry in svg_geometry:
            new_sketch_svg.add_geometry(geometry)
        new_sketch_svg.auto_size()
        return new_sketch_svg
    
    @classmethod
    def from_element(cls, svg_element: elements.svg) -> FreeCADSketchSVG:
        """Returns a FreeCADSketchSVG made from an svg element
        
        :param svg_element: A svg element to make a FreeCAD sketch from
        :returns: A new FreeCAD SketchSVG object
        """
        new_sketch_svg = super().from_element(svg_element)
        for sub in list(svg_element):
            new_sketch_svg.append(seu.upgrade_element(sub))
        new_sketch_svg.Label = new_sketch_svg.id_
        new_sketch_svg.geometry_g = new_sketch_svg.sub(
            new_sketch_svg.Label + "_geometry"
        )
        if new_sketch_svg.geometry_g is None:
            raise ValueError("No geometry group found in svg")
        return new_sketch_svg

def read_freecad_sketch(sketch_label: str, filepath: str,
                        mode: str = "r") -> SketchSVG:
    """Returns a svg file with sketch geometry from a FreeCAD .FCStd file.
    
    :param sketch_label: The label of the sketch in FreeCAD
    :param filepath: The filepath of the FreeCAD file
    :mode: The single character access mode for the FreeCAD file operation
    :returns: A SVGFile containing the geometry of the FreeCAD sketch
    """
    fc_sketch = fsr.read_sketch_by_label(filepath, sketch_label)
    fc_unit = "mm"
    
    sketch_svg = SketchSVG.from_sketch(fc_sketch, fc_unit)
    sketch_svg.unit = fc_unit
    fc_svg_file = SVGFile(mode="w")
    fc_svg_file.svg = sketch_svg
    return fc_svg_file