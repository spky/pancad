"""A module providing a class that will read FreeCAD files and 
convert information in them into equvalent SVGs
"""
import os
from pathlib import Path

import svg_file
import freecad_sketch_readers as fsr
import freecad_sketcher_to_svg_translators as fsst

class FreeCADSVGFile(svg_file.SVGFile):
    
    def __init__(self, freecad_file_path: str, svg_name: str = None,
                 unit = "mm", point_radius = "0.1") -> None:
        self.freecad_file_name = os.path.basename(freecad_file_path)
        if svg_name is None:
            # Default to naming the svg the same name as the FreeCAD file
            svg_name = Path(freecad_file_path).stem + ".svg"
        self.sketches = fsr.read_all_sketches_from_file(freecad_file_path)
        self.point_radius = point_radius
        super().__init__(svg_name, unit=unit)
        super().add_svg(Path(freecad_file_path).stem)
    
    def add_sketch_by_label(self, label: str) -> None:
        sketch = None
        for s in self.sketches:
            if s.Label == label:
                sketch = s
                break
        if sketch is None:
            raise ValueError("There is not sketch named '"
                             + label
                             + "' in FreeCAD file '"
                             + self.freecad_file_name)
        super().add_g(sketch.Name + ".." + sketch.Label)
        freecad_geometry = fsr.read_sketch_geometry(sketch)
        svg_geometry = fsst.translate_geometry(freecad_geometry)
        for g in svg_geometry:
            self.add_geometry(g)
    
    def add_geometry(self, fc_geometry: dict) -> None:
        match fc_geometry["geometry_type"]:
            case "line":
                super().add_path(fc_geometry["id"],
                                 fc_geometry["d"])
            case "point":
                super().add_circle(fc_geometry["id"],
                                   [fc_geometry["cx"], fc_geometry["cy"]],
                                   self.point_radius)
            case "circle":
                super().add_circle(fc_geometry["id"],
                                   [fc_geometry["cx"], fc_geometry["cy"]],
                                   fc_geometry["r"])
            case "circular_arc":
                super().add_path(fc_geometry["id"],
                                 fc_geometry["d"])
            case _:
                raise ValueError(str(fc_geometry["geometry_type"])
                                 + "is not a supported geometry type")