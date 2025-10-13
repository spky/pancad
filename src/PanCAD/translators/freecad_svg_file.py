"""A module providing a class that will read FreeCAD files and convert 
information in them into equvalent SVGs
"""

from __future__ import annotations

import pancad
from pancad.graphics.svg import elements
from pancad.graphics.svg import element_utils as seu
from pancad.graphics.svg.file import SVGFile
from pancad.graphics.svg.generators import SVGStyle
from pancad.cad.freecad import sketch_readers as fsr
from pancad.cad.freecad.object_wrappers import File as FreeCADFile
from pancad.cad.freecad.object_wrappers import Sketch as FreeCADSketch
from pancad.utils.config import Config, SettingsMissingError
from pancad.translators import freecad_sketcher_to_svg as fc_to_svg
from pancad.translators import svg_to_freecad_sketcher as svg_to_fc

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
    
    def to_sketch(self, label: str = None) -> FreeCADSketch:
        """Returns a FreeCAD sketch object that can be placed into FreeCAD.
        
        :param label: The label for the sketch, defaults to None which will 
                      cause the svg id to be assigned as the sketch label.
                      If the svg id is also None, a ValueError will be raised.
        :returns: A pancad.freecad.object_wrappers.Sketch object
        """
        if label is not None:
            sketch_label = label
        elif self.id_ is not None:
            sketch_label = self.id_
        else:
            raise ValueError("label and SketchSVG.id_ cannot both be None")
        
        new_freecad_sketch = FreeCADSketch()
        new_freecad_sketch.add_geometry_list(self.get_freecad_dict())
        new_freecad_sketch.label = sketch_label
        return new_freecad_sketch
    
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

def freecad_sketch_to_svg(sketch: str | Sketcher.Sketch, *,
                          model_filepath: str = None,
                          mode: str = "r") -> SVGFile:
    """Returns a svg file with sketch geometry from a FreeCAD .FCStd file.
    
    :param sketch: A FreeCAD sketch object or sketch label
    :param model_filepath: The filepath of the FreeCAD file. Only required if a 
                           sketch label used as the first argument
    :mode: The single character access mode for the FreeCAD file operation
    :returns: A SVGFile containing the geometry of the FreeCAD sketch
    """
    if isinstance(sketch, str):
        fc_sketch = fsr.read_sketch_by_label(model_filepath, sketch)
        fc_unit = "mm"
    elif hasattr(sketch, "TypeId") and sketch.TypeId == FreeCADFile.SKETCH_ID:
        fc_sketch = sketch
        fc_unit = "mm"
    else:
        raise ValueError(f"{sketch} not sketch label or Sketcher.Sketch object")
    
    sketch_svg = SketchSVG.from_sketch(fc_sketch, fc_unit)
    sketch_svg.unit = fc_unit
    fc_svg_file = SVGFile(mode="w")
    fc_svg_file.svg = sketch_svg
    return fc_svg_file

def svg_to_freecad_sketch(
        svg: elements.svg | SVGFile, sketch_label: str = None
    ) -> FreeCADSketch:
    """Returns a FreeCAD file with a sketch containing the svg file's geometry.
    
    :param svg: An SVGFile object representing sketch geometry. The root 
                     svg element must be a SketchSVG instance since the 
                     geometry has to be marked as construction or 
                     non-construction.
    :returns: A pancad.freecad.object_wrappers.File instance
    """
    if isinstance(svg, elements.svg):
        svg_element = svg
    elif isinstance(svg, SVGFile):
        svg_element = svg.svg
    else:
        raise ValueError(f"{svg} is not a svg element or svg file")
    
    freecad_svg = SketchSVG.from_element(svg_element)
    return freecad_svg.to_sketch(sketch_label)