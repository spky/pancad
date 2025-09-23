from functools import partial
from inspect import stack
import os
import unittest

from PanCAD import PartFile
from PanCAD.geometry import CoordinateSystem, Extrude
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.geometry.constraints import (
    Coincident,
    Distance,
    Equal,
    Horizontal,
    Parallel,
    Perpendicular,
    Vertical,
)
from PanCAD.filetypes.constants import SoftwareName

from tests.sample_pancad_objects import sample_sketches
from . import dump


class TestPartFileToFreeCADSingleBody(unittest.TestCase):
    def setUp(self):
        self.ext_name = "Test Extrude"
        self.height = 1
        self.dump = os.path.dirname(dump.__file__)
    
    def tearDown(self):
        os.remove(self.filepath)
        for filename in os.listdir(self.dump):
            # Also delete any backup files in dump folder
            if filename.endswith(".FCBak"):
                os.remove(os.path.join(self.dump, filename))
    
    def test_create_body(self):
        filename = stack()[0].function + ".FCStd"
        self.filepath = os.path.join(self.dump, filename)
        self.file = PartFile(filename)
        self.file.to_freecad(self.filepath)
    
    def test_create_cube(self):
        filename = stack()[0].function + ".FCStd"
        self.filepath = os.path.join(self.dump, filename)
        self.file = PartFile(filename)
        cs = CoordinateSystem()
        sketch = sample_sketches.square(cs)
        extrude = Extrude.from_length(sketch, self.height, name=self.ext_name)
        self.file.features = [cs, sketch, extrude]
        self.file.to_freecad(self.filepath)
    
    def test_create_cylinder(self):
        filename = stack()[0].function + ".FCStd"
        self.filepath = os.path.join(self.dump, filename)
        self.file = PartFile(filename)
        cs = CoordinateSystem()
        sketch = sample_sketches.circle(cs)
        extrude = Extrude.from_length(sketch, self.height, name=self.ext_name)
        self.file.features = [cs, sketch, extrude]
        self.file.to_freecad(self.filepath)
    
    def test_create_ellipse_extrude(self):
        # TODO: Add constraints
        filename = stack()[0].function + ".FCStd"
        self.filepath = os.path.join(self.dump, filename)
        self.file = PartFile(filename)
        cs = CoordinateSystem()
        sketch = sample_sketches.ellipse(cs)
        extrude = Extrude.from_length(sketch, self.height, name=self.ext_name)
        self.file.features = [cs, sketch, extrude]
        self.file.to_freecad(self.filepath)

class TestPartFileSquareSketchVariationsToFreeCAD(unittest.TestCase):
    
    def setUp(self):
        self.side = 5
        self.unit = "mm"
        self.sketch = sample_sketches.square(side=self.side,
                                             unit=self.unit,
                                             include_constraints=False)
        self.b, self.r, self.t, self.l = self.sketch.geometry
        # bottom, right, top, left
        self.constraints = [ # Constraints in every sketch
            Coincident(self.b, ConstraintReference.START,
                       self.l, ConstraintReference.END),
            Coincident(self.b, ConstraintReference.END,
                       self.r, ConstraintReference.START),
            Coincident(self.r, ConstraintReference.END,
                       self.t, ConstraintReference.START),
            Coincident(self.t, ConstraintReference.END,
                       self.l, ConstraintReference.START),
        ]
        self.dump = os.path.dirname(dump.__file__)
    
    def tearDown(self):
        filepath = os.path.join(self.dump, self.file.filename + ".FCStd")
        os.remove(filepath)
    
    def finish_to_freecad(self):
        filepath = os.path.join(self.dump, self.file.filename + ".FCStd")
        self.sketch.constraints = self.constraints
        self.file.add_feature(self.sketch)
        self.file.to_freecad(filepath)
    
    def test_two_equal_square_with_horizontal_vertical(self):
        self.file = PartFile(stack()[0].function + ".FCStd")
        self.constraints.extend(
            [
                Horizontal(self.b, ConstraintReference.CORE),
                Vertical(self.r, ConstraintReference.CORE),
                Horizontal(self.t, ConstraintReference.CORE),
                Vertical(self.l, ConstraintReference.CORE),
                Equal(self.b, ConstraintReference.CORE,
                      self.r, ConstraintReference.CORE),
                Distance(self.b, ConstraintReference.START,
                         self.b, ConstraintReference.END,
                         value=self.side, unit=self.unit),
                Coincident(self.b, ConstraintReference.START,
                           self.sketch, ConstraintReference.ORIGIN)
            ]
        )
        self.finish_to_freecad()
    
    def test_all_equal_square_with_horizontal_vertical(self):
        self.file = PartFile(stack()[0].function + ".FCStd")
        self.constraints.extend(
            [
                Horizontal(self.b, ConstraintReference.CORE),
                Vertical(self.l, ConstraintReference.CORE),
                Equal(self.b, ConstraintReference.CORE,
                      self.r, ConstraintReference.CORE),
                Equal(self.b, ConstraintReference.CORE,
                      self.t, ConstraintReference.CORE),
                Equal(self.b, ConstraintReference.CORE,
                      self.l, ConstraintReference.CORE),
                Distance(self.b, ConstraintReference.START,
                         self.b, ConstraintReference.END,
                         value=self.side, unit=self.unit),
                Coincident(self.b, ConstraintReference.START,
                           self.sketch, ConstraintReference.ORIGIN)
            ]
        )
        self.finish_to_freecad()
    
    def test_all_equal_square_with_perpendicular(self):
        self.file = PartFile(stack()[0].function + ".FCStd")
        self.constraints.extend(
            [
                Horizontal(self.b, ConstraintReference.CORE),
                Equal(self.b, ConstraintReference.CORE,
                      self.r, ConstraintReference.CORE),
                Equal(self.b, ConstraintReference.CORE,
                      self.t, ConstraintReference.CORE),
                Equal(self.b, ConstraintReference.CORE,
                      self.l, ConstraintReference.CORE),
                Perpendicular(self.b, ConstraintReference.CORE,
                              self.l, ConstraintReference.CORE),
                Distance(self.b, ConstraintReference.START,
                         self.b, ConstraintReference.END,
                         value=self.side, unit=self.unit),
                Coincident(self.b, ConstraintReference.START,
                           self.sketch, ConstraintReference.ORIGIN)
            ]
        )
        self.finish_to_freecad()
    
    def test_all_equal_square_with_perpendicular_and_parallel(self):
        self.file = PartFile(stack()[0].function + ".FCStd")
        self.constraints.extend(
            [
                Horizontal(self.b, ConstraintReference.CORE),
                
                Equal(self.b, ConstraintReference.CORE,
                      self.l, ConstraintReference.CORE),
                Perpendicular(self.b, ConstraintReference.CORE,
                              self.l, ConstraintReference.CORE),
                Parallel(self.r, ConstraintReference.CORE,
                         self.l, ConstraintReference.CORE),
                Parallel(self.b, ConstraintReference.CORE,
                         self.t, ConstraintReference.CORE),
                Distance(self.b, ConstraintReference.START,
                         self.b, ConstraintReference.END,
                         value=self.side, unit=self.unit),
                Coincident(self.b, ConstraintReference.START,
                           self.sketch, ConstraintReference.ORIGIN)
            ]
        )
        self.finish_to_freecad()
