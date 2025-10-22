"""A collection of modules representing 2D and 3D geometry."""

# Warning: Import order matters, the modules at the top of the file are 
# sometimes dependencies of the modules towards the bottom of the file

# Import Geometry Types
from pancad.geometry.abstract_pancad_thing import PancadThing
from pancad.geometry.abstract_geometry import AbstractGeometry
from pancad.geometry.abstract_feature import AbstractFeature

from pancad.geometry.point import Point
from pancad.geometry.line import Line
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.plane import Plane
from pancad.geometry.circle import Circle
from pancad.geometry.circular_arc import CircularArc
from pancad.geometry.ellipse import Ellipse
from pancad.geometry.coordinate_system import CoordinateSystem

# Import Features

# Import 2D Geometry Aggregations - dependent on Geometry Types
from pancad.geometry.sketch import Sketch

# Import 3D Geometry Aggregations - dependent on 2D Geometry Aggregations
from pancad.geometry.feature_container import FeatureContainer
from pancad.geometry.extrude import Extrude