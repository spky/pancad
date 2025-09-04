"""A collection of modules representing 2D and 3D geometry."""

# Warning: Import order matters, the modules at the top of the file are 
# sometimes dependencies of the modules towards the bottom of the file

# Import Geometry Types
from PanCAD.geometry.abstract_pancad_thing import PanCADThing
from PanCAD.geometry.abstract_geometry import AbstractGeometry

from PanCAD.geometry.point import Point
from PanCAD.geometry.line import Line
from PanCAD.geometry.line_segment import LineSegment
from PanCAD.geometry.plane import Plane
from PanCAD.geometry.circle import Circle
from PanCAD.geometry.ellipse import Ellipse
from PanCAD.geometry.coordinate_system import CoordinateSystem

# Import Features
from PanCAD.geometry.abstract_feature import AbstractFeature

# Import 2D Geometry Aggregations - dependent on Geometry Types
from PanCAD.geometry.sketch import Sketch

# Import 3D Geometry Aggregations - dependent on 2D Geometry Aggregations
from PanCAD.geometry.extrude import Extrude

from PanCAD.geometry.body import Body