import unittest

import pancad
from pancad.geometry.coordinate_system import CoordinateSystem

class TestFeatureContainerInit(unittest.TestCase):
    
    def test_add_coordinate_system(self):
        bucket = FeatureContainer(name="TestBucket")
        coordinate_system = CoordinateSystem((0, 0, 0),
                                             context=bucket, name="TestOrigin")
        bucket.add_feature(coordinate_system)
        # print()
        # print(bucket)
