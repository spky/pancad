from math import radians
import unittest

from PanCAD import PartFile
from PanCAD.cad.freecad import App, Part, Sketcher
from PanCAD.cad.freecad.constants import ObjectType
from PanCAD.cad.freecad.feature_mappers import FreeCADMap
from PanCAD.cad.freecad.sketch_geometry import get_freecad_sketch_geometry
from PanCAD.geometry import (LineSegment,
                             CoordinateSystem,
                             Ellipse,
                             Sketch,
                             FeatureContainer,
                             Extrude,)
from PanCAD.geometry.constraints import (Coincident,
                                         Equal,
                                         Diameter,
                                         Distance,
                                         Horizontal,
                                         HorizontalDistance,
                                         Parallel,
                                         Perpendicular,
                                         Radius,
                                         Vertical,
                                         VerticalDistance,)
from PanCAD.geometry.constants import ConstraintReference

class TestPanCADtoFreeCAD(unittest.TestCase):
    
    def setUp(self):
        self.file = PartFile("Testing Mapping")
        self.document = App.newDocument()
        self.test_map = FreeCADMap(self.document)
    
    def test_nominal_init(self):
        mapping = FreeCADMap(self.document)
    
    # def test_map_line_segment(self):
        # pancad_line_1 = LineSegment((0, 0), (1, 1))
        # pancad_line_2 = LineSegment((-1, 0), (1, 0))
        # freecad_line = get_freecad_sketch_geometry(pancad_line_1)
        # self.mapping[pancad_line_1] = freecad_line
    
    # def test_map_coordinate_system(self):
        # root = self.document.addObject(ObjectType.BODY, "Body")
        # cs = CoordinateSystem()
        # self.mapping[cs] = root.Origin
    
    def test_map_add_feature_container(self):
        container = FeatureContainer(name="TestBucket")
        coordinate_system = CoordinateSystem()
        line = LineSegment((0, 0), (1, 1))
        sketch = Sketch(name="Test Mapping Sketch",
                        geometry=[line],
                        coordinate_system=coordinate_system)
        container.features = [coordinate_system, sketch]
        self.test_map.add_pancad_feature(container)
        print(self.test_map)
        # for key, value in self.mapping.items():
            # print(key, ": ", value)
        # self.assertEqual(len(self.mapping), 2)

class TestPanCADtoFreeCADCubeExtrudeMap(TestPanCADtoFreeCAD):
    def square_sketch(self,
                      name: str,
                      plane_ref: ConstraintReference,
                      coordinate_system: CoordinateSystem):
        length = 1
        width = 1
        unit = "mm"
        geometry = [ # A 1x1 square
            LineSegment((0, 0), (width, 0)),
            LineSegment((width, 0), (width, length)),
            LineSegment((width, length), (0, length)),
            LineSegment((0, length), (0, 0)),
        ]
        # Constrain geometry to each other
        constraints = [
            Horizontal(geometry[0], ConstraintReference.CORE),
            Vertical(geometry[1], ConstraintReference.CORE),
            Horizontal(geometry[2], ConstraintReference.CORE),
            Vertical(geometry[3], ConstraintReference.CORE),
            Coincident(geometry[0], ConstraintReference.START,
                       geometry[3], ConstraintReference.END),
            Coincident(geometry[0], ConstraintReference.END,
                       geometry[1], ConstraintReference.START),
            Coincident(geometry[1], ConstraintReference.END,
                       geometry[2], ConstraintReference.START),
            Coincident(geometry[2], ConstraintReference.END,
                       geometry[3], ConstraintReference.START),
            Distance(geometry[0], ConstraintReference.CORE,
                     geometry[2], ConstraintReference.CORE,
                     length, unit="mm"),
            Distance(geometry[1], ConstraintReference.CORE,
                     geometry[3], ConstraintReference.CORE,
                     width, unit="mm"),
        ]
        sketch = Sketch(coordinate_system=coordinate_system,
                        plane_reference=plane_ref,
                        geometry=geometry,
                        constraints=constraints,
                        name=name)
        # Constrain bottom left corner to origin
        sketch.add_constraint(
            Coincident(geometry[0], ConstraintReference.START,
                       sketch.get_sketch_coordinate_system(),
                       ConstraintReference.ORIGIN)
        )
        return sketch
    
    def test_map_cube_extrude(self):
        container = FeatureContainer(name="TestBucket")
        cs = CoordinateSystem()
        sketch = self.square_sketch("Test Sketch", ConstraintReference.XY, cs)
        extrude = Extrude.from_length(sketch, 1, name="Test Extrude")
        container.features = [cs, sketch, extrude]
        self.test_map.add_pancad_feature(container)
        # print(self.mapping._freecad_sketch_geometry_map)
        
        print(self.test_map)

class TestPanCADtoFreeCADEllipseExtrude(TestPanCADtoFreeCAD):
    def ellipse_sketch(self,
                       name: str,
                       plane_ref: ConstraintReference,
                       coordinate_system: CoordinateSystem):
        geometry = [
            LineSegment((0, 0), (1, 1)),
            Ellipse.from_angle((0, 0), 2, 1, radians(45))
        ]
        sketch = Sketch(coordinate_system=coordinate_system,
                        plane_reference=plane_ref,
                        geometry=geometry,
                        name=name)
        return sketch
    
    def test_map_ellipse_extrude(self):
        container = FeatureContainer(name="TestBucket")
        cs = CoordinateSystem()
        sketch = self.ellipse_sketch("Test Sketch", ConstraintReference.XY, cs)
        extrude = Extrude.from_length(sketch, 1, name="Test Extrude")
        container.features = [cs, sketch, extrude]
        self.test_map.add_pancad_feature(container)