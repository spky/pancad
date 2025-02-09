"""A module providing a class that will read FreeCAD files and 
convert information in them into equvalent SVGs
"""
from __future__ import annotations
import os
from pathlib import Path

import svg_file as sf
import svg_elements as se
import freecad_sketch_readers as fsr
import freecad_sketcher_to_svg_translators as fsst
import Sketcher
import svg_element_utils as seu


class FreeCADSketchSVG(se.svg):
    point_radius = "0.1"
    def __init__(self) -> None:
        super().__init__()
    
    def add_geometry(self, fc_geometry: dict) -> None:
        match fc_geometry["geometry_type"]:
            case "line" | "circular_arc":
                self.geometry_g.append(se.path(fc_geometry["id"],
                                               fc_geometry["d"]))
            case "point":
                self.geometry_g.append(se.circle(fc_geometry["id"],
                                                 fc_geometry["cx"],
                                                 fc_geometry["cy"],
                                                 self.point_radius))
            case "circle":
                self.geometry_g.append(se.circle(fc_geometry["id"],
                                                 fc_geometry["cx"],
                                                 fc_geometry["cy"],
                                                 fc_geometry["r"]))
            case _:
                raise ValueError(str(fc_geometry["geometry_type"])
                                 + "is not a supported geometry type")
    
    @classmethod
    def from_sketch(cls, sketch: Sketcher.Sketch,
                    unit: str) -> FreeCADSketchSVG:
        """Returns a FreeCADSketchSVG made from a FreeCAD Sketch"""
        new_sketch_svg = cls()
        new_sketch_svg.unit = unit
        new_sketch_svg.Label = sketch.Label
        # Non-construction group
        new_sketch_svg.geometry_g = se.g(new_sketch_svg.Label
                                         + "_geometry")
        new_sketch_svg.append(new_sketch_svg.geometry_g)
        freecad_geometry = fsr.read_sketch_geometry(sketch)
        svg_geometry = fsst.translate_geometry(freecad_geometry)
        for geometry in svg_geometry:
            new_sketch_svg.add_geometry(geometry)
        new_sketch_svg.auto_size()
        return new_sketch_svg
    
    @classmethod
    def from_element(cls, svg_element: se.svg) -> FreeCADSketchSVG:
        """Returns a FreeCADSketchSVG made from an svg file"""
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