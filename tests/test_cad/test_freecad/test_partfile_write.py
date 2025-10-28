from functools import partial
from inspect import stack
import os
import unittest

from pancad import PartFile
from pancad.geometry import CoordinateSystem, Extrude
from pancad.geometry.constants import (ConstraintReference as CR,
                                       SketchConstraint as SC)
from pancad.geometry.constraints import make_constraint
from pancad.cad.freecad.freecad_python import validate_freecad

from tests.sample_pancad_objects import sample_sketches
from tests.utils import delete_all_suffix
from . import dump


class TestPartFileToFreeCADSingleBody(unittest.TestCase):
    def setUp(self):
        self.ext_name = "Test Extrude"
        self.height = 1
        self.dump = os.path.dirname(dump.__file__)
    
    def tearDown(self):
        os.remove(self.filepath)
        delete_all_suffix(self.dump, ".FCBak")
    
    def test_create_body(self):
        filename = stack()[0].function + ".FCStd"
        self.filepath = os.path.join(self.dump, filename)
        self.file = PartFile(filename)
        self.file.to_freecad(self.filepath)
        validate_freecad(self.filepath)
    
    def test_create_cube(self):
        filename = stack()[0].function + ".FCStd"
        self.filepath = os.path.join(self.dump, filename)
        self.file = PartFile(filename)
        cs = CoordinateSystem()
        sketch = sample_sketches.square(cs)
        extrude = Extrude.from_length(sketch, self.height, name=self.ext_name)
        self.file.features = [cs, sketch, extrude]
        self.file.to_freecad(self.filepath)
        validate_freecad(self.filepath)
    
    def test_create_cylinder(self):
        filename = stack()[0].function + ".FCStd"
        self.filepath = os.path.join(self.dump, filename)
        self.file = PartFile(filename)
        cs = CoordinateSystem()
        sketch = sample_sketches.circle(cs)
        extrude = Extrude.from_length(sketch, self.height, name=self.ext_name)
        self.file.features = [cs, sketch, extrude]
        self.file.to_freecad(self.filepath)
        validate_freecad(self.filepath)
    
    def test_create_ellipse_extrude(self):
        filename = stack()[0].function + ".FCStd"
        self.filepath = os.path.join(self.dump, filename)
        self.file = PartFile(filename)
        cs = CoordinateSystem()
        sketch = sample_sketches.ellipse(cs)
        extrude = Extrude.from_length(sketch, self.height, name=self.ext_name)
        self.file.features = [cs, sketch, extrude]
        self.file.to_freecad(self.filepath)
        validate_freecad(self.filepath)
    
    def test_create_rounded_square_extrude(self):
        filename = stack()[0].function + ".FCStd"
        self.filepath = os.path.join(self.dump, filename)
        self.file = PartFile(filename)
        sketch = sample_sketches.rounded_square()
        self.file.features = [sketch]
        self.file.to_freecad(self.filepath)
        validate_freecad(self.filepath)

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
            make_constraint(SC.COINCIDENT, self.b, CR.START, self.l, CR.END),
            make_constraint(SC.COINCIDENT, self.b, CR.END, self.r, CR.START),
            make_constraint(SC.COINCIDENT, self.r, CR.END, self.t, CR.START),
            make_constraint(SC.COINCIDENT, self.t, CR.END, self.l, CR.START),
            make_constraint(SC.COINCIDENT,
                            self.b, CR.START, self.sketch, CR.ORIGIN),
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
        validate_freecad(filepath)
    
    def test_two_equal_square_with_horizontal_vertical(self):
        self.file = PartFile(stack()[0].function + ".FCStd")
        self.constraints.extend(
            [
                make_constraint(SC.HORIZONTAL, self.b, CR.CORE),
                make_constraint(SC.VERTICAL, self.r, CR.CORE),
                make_constraint(SC.HORIZONTAL, self.t, CR.CORE),
                make_constraint(SC.VERTICAL, self.l, CR.CORE),
                make_constraint(SC.EQUAL, self.b, CR.CORE, self.r, CR.CORE),
                make_constraint(SC.DISTANCE, self.b, CR.START, self.b, CR.END,
                                value=self.side, unit=self.unit),
            ]
        )
        self.finish_to_freecad()
    
    def test_all_equal_square_with_horizontal_vertical(self):
        self.file = PartFile(stack()[0].function + ".FCStd")
        self.constraints.extend(
            [
                make_constraint(SC.HORIZONTAL, self.b, CR.CORE),
                make_constraint(SC.VERTICAL, self.l, CR.CORE),
                make_constraint(SC.EQUAL, self.b, CR.CORE, self.r, CR.CORE),
                make_constraint(SC.EQUAL, self.b, CR.CORE, self.t, CR.CORE),
                make_constraint(SC.EQUAL, self.b, CR.CORE, self.l, CR.CORE),
                make_constraint(SC.DISTANCE, self.b, CR.START, self.b, CR.END,
                                value=self.side, unit=self.unit),
            ]
        )
        self.finish_to_freecad()
    
    def test_all_equal_square_with_perpendicular(self):
        self.file = PartFile(stack()[0].function + ".FCStd")
        self.constraints.extend(
            [
                make_constraint(SC.HORIZONTAL, self.b, CR.CORE),
                make_constraint(SC.EQUAL, self.b, CR.CORE, self.r, CR.CORE),
                make_constraint(SC.EQUAL, self.b, CR.CORE, self.t, CR.CORE),
                make_constraint(SC.EQUAL, self.b, CR.CORE, self.l, CR.CORE),
                make_constraint(SC.PERPENDICULAR,
                                self.b, CR.CORE, self.l, CR.CORE),
                make_constraint(SC.DISTANCE, self.b, CR.START, self.b, CR.END,
                                value=self.side, unit=self.unit),
            ]
        )
        self.finish_to_freecad()
    
    def test_all_equal_square_with_perpendicular_and_parallel(self):
        self.file = PartFile(stack()[0].function + ".FCStd")
        self.constraints.extend(
            [
                make_constraint(SC.HORIZONTAL, self.b, CR.CORE),
                make_constraint(SC.EQUAL, self.b, CR.CORE, self.l, CR.CORE),
                make_constraint(SC.PERPENDICULAR,
                                self.b, CR.CORE, self.l, CR.CORE),
                make_constraint(SC.PARALLEL, self.r, CR.CORE, self.l, CR.CORE),
                make_constraint(SC.PARALLEL, self.b, CR.CORE, self.t, CR.CORE),
                make_constraint(SC.DISTANCE, self.b, CR.START, self.b, CR.END,
                                value=self.side, unit=self.unit),
            ]
        )
        self.finish_to_freecad()
