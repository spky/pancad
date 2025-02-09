import sys
import os
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


sys.path.append('src')

import freecad_svg_file as fcsf
import svg_file as sf
import svg_generators as sg
import freecad_sketch_readers as fsr

class TestFreeCADSVGFile(unittest.TestCase):
    
    def setUp(self):
        self.TESTS_FOLDER = 'tests'
        self.SAMPLE_FC_FOLDER = os.path.join(self.TESTS_FOLDER,
                                             'sample_freecad')
        self.SAMPLE_SVG_FOLDER = os.path.join(self.TESTS_FOLDER,
                                              'sample_svgs')
        self.FC_FILENAME = 'test_sketch_readers.FCStd'
        self.FC_MODEL_PATH = os.path.join(self.SAMPLE_FC_FOLDER,
                                          self.FC_FILENAME)
        self.OUT_FOLDER = os.path.join(self.TESTS_FOLDER,
                                       'test_output_dump')
        self.default_style = sg.SVGStyle()
        self.default_style.set_property("fill", "none")
        self.default_style.set_property("stroke", "black")
        self.default_style.set_property("stroke-width", "0.05px")
        self.default_style.set_property("stroke-linecap", "butt")
        self.default_style.set_property("stroke-linejoin", "miter")
    
    def test_init(self):
        sketch_obj = fsr.read_sketch_by_label(
            self.FC_MODEL_PATH,
            "xz_rounded_rectangle_with_circle"
        )
        obj = fcsf.FreeCADSketchSVG()
        obj.unit = "mm"
    
    def test_write_freecad_sketch(self):
        sketch_obj = fsr.read_sketch_by_label(
            self.FC_MODEL_PATH,
            "xz_rounded_rectangle_with_circle"
        )
        sketch_svg = fcsf.FreeCADSketchSVG.from_sketch(sketch_obj, "mm")
        sketch_svg.unit = "mm"
        sketch_svg.geometry_g.set("style", self.default_style.string)
        
        svg_filepath = os.path.join(self.OUT_FOLDER,
                                    "test_write_freecad_sketch.svg")
        file = sf.SVGFile(svg_filepath, "w")
        file.svg = sketch_svg
        file.write(indent="  ")
    
    def test_from_element(self):
        filepath = os.path.join(
            self.SAMPLE_SVG_FOLDER,
            'test_write_freecad_sketch_loop_back_input.svg'
        )
        file = sf.SVGFile(filepath, "r")
        #sketch_svg = fcsf.FreeCADSketchSVG(svg_filepath=filepath)
        sketch_svg = fcsf.FreeCADSketchSVG.from_element(file.svg)
        
    
    """
    def test_loop_back_freecad_svg(self):
        filepath = os.path.join(
            self.SAMPLE_SVG_FOLDER,
            'test_write_freecad_sketch_loop_back_input.svg'
        )
        sketch_svg = fcsf.FreeCADSketchSVG(svg_filepath=filepath)
        print(sketch_svg.to_string())
    """

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()