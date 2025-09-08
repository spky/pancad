import unittest

import PanCAD
from PanCAD.geometry import (Circle,
                             CoordinateSystem,
                             Ellipse,
                             Extrude,
                             FeatureContainer,
                             LineSegment,
                             Sketch,)
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

class TestFeatureContainerInit(unittest.TestCase):
    
    def test_add_coordinate_system(self):
        bucket = FeatureContainer(name="TestBucket")
        coordinate_system = CoordinateSystem(context=bucket, name="TestOrigin")
        bucket.add_feature(coordinate_system)
        # print()
        # print(bucket)
