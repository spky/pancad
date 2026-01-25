import os
from math import sqrt, radians
from numbers import Real
from inspect import stack
from pathlib import Path
import unittest

import pancad
from pancad.filetypes.part_file import PartFile
from pancad.geometry.sketch import Sketch
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.point import Point
from pancad.constants import ConstraintReference
from pancad.constraints.distance import Angle, Distance
from pancad.constraints.state_constraint import Coincident, Equal
from pancad.cad.freecad.filetypes import FreeCADFile
from pancad.cad.freecad.freecad_python import validate_freecad

from . import dump

class TestSketches(unittest.TestCase):
    
    def setUp(self):
        self.dump = os.path.dirname(dump.__file__)
    
    def init_filename(self, function_name: str):
        self.filename = function_name + ".FCStd"
        self.filepath = os.path.join(self.dump, self.filename)
        self.file = PartFile(self.filename)
    
    def line_angled_to_x_axis(self,
                              quadrant: int,
                              angle_degrees: Real,
                              start_to_end: bool) -> Sketch:
        start = Point(0, 0)
        length = sqrt(2)
        match quadrant:
            case 1:
                end_polar_angle = radians(angle_degrees)
            case 2:
                end_polar_angle = radians(180 - angle_degrees)
            case 3:
                end_polar_angle = radians(180 + angle_degrees)
            case 4:
                end_polar_angle = radians(-angle_degrees)
            case _:
                raise ValueError(f"Invalid quadrant {quadrant}")
        end = Point.from_polar(length, end_polar_angle)
        name = f"test_sketch_quadrant{quadrant}_{angle_degrees}_degrees"
        if start_to_end:
            line_segment = LineSegment(end, start)
            name += "_StartEnd"
        else:
            line_segment = LineSegment(start, end)
            name += "_StartStart"
        sketch = Sketch(geometry=[line_segment], name=name)
        sketch.constraints = [
            Coincident(line_segment, sketch.two_origin),
            Distance(line_segment.start, line_segment.end,
                     value=length, unit="in"),
            Angle(sketch.two_x_axis, line_segment,
                  value=angle_degrees, quadrant=quadrant),
        ]
        return sketch
    
    def tearDown(self):
        path = Path(self.dump) / (self.file.name + ".FCStd")
        path.unlink(missing_ok=True)
    
    def test_line_angled_to_x_axis(self):
        self.file = PartFile(stack()[0].function + ".FCStd")
        
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
        filepath = os.path.join(self.dump, self.file.name + ".FCStd")
        self.file.to_freecad(filepath)
        validate_freecad(filepath)