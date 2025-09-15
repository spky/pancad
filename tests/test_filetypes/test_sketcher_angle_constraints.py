import os
import math
from inspect import stack
import unittest

import PanCAD
from PanCAD.filetypes import PartFile
from PanCAD.geometry import Sketch, LineSegment, Point
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.geometry.constraints import Angle, Coincident, Distance, Equal
from PanCAD.cad.freecad import FreeCADFile

class TestSketches(unittest.TestCase):
    
    def setUp(self):
        self.dump_dir = os.path.join(os.path.dirname(__file__), "dump")
    
    def init_filename(self, function_name: str):
        self.filename = function_name + ".FCStd"
        self.filepath = os.path.join(self.dump_dir, self.filename)
        self.file = PartFile(self.filename)
    
    def line_angled_to_x_axis(self,
                              quadrant: int,
                              angle_degrees: int | float,
                              start_to_end: bool) -> Sketch:
        start = Point(0, 0)
        length = math.sqrt(2)
        unit = "in"
        match quadrant:
            case 1:
                end_polar_angle = math.radians(angle_degrees)
            case 2:
                end_polar_angle = math.radians(180 - angle_degrees)
            case 3:
                end_polar_angle = math.radians(180 + angle_degrees)
            case 4:
                end_polar_angle = math.radians(-angle_degrees)
            case _:
                raise ValueError(f"Invalid quadrant {quadrant}")
        end = Point.from_polar(length, end_polar_angle)
        uid = f"test_sketch_quadrant{quadrant}_{angle_degrees}_degrees"
        if start_to_end:
            geometry = [LineSegment(end, start),]
            uid += "_StartEnd"
        else:
            geometry = [LineSegment(start, end),]
            uid += "_StartStart"
        
        
        sketch = Sketch(geometry=geometry,
                        uid=uid)
        sketch.constraints = [
            Coincident(geometry[0], ConstraintReference.START,
                       sketch, ConstraintReference.ORIGIN),
            Distance(geometry[0], ConstraintReference.START,
                     geometry[0], ConstraintReference.END,
                     value=length, unit=unit),
            Angle(sketch, ConstraintReference.X,
                  geometry[0], ConstraintReference.CORE,
                  value=angle_degrees, quadrant=quadrant),
        ]
        return sketch
    
    def tearDown(self):
        os.remove(self.filepath)
    
    def test_line_angled_to_x_axis(self):
        self.init_filename(stack()[0].function + ".FCStd")
        quadrant_angle = [
            (1, 45, False),
            (2, 45, False),
            (3, 45, False),
            (4, 45, False),
            (1, 45, True),
            (2, 45, True),
            (3, 45, True),
            (4, 45, True),
        ]
        for quadrant, angle, start_to_end in quadrant_angle:
            sketch = self.line_angled_to_x_axis(quadrant, angle, start_to_end)
            self.file.add_feature(sketch)
        self.file.to_freecad(self.filepath)