import math
import unittest

import numpy as np

from PanCAD.utils import trigonometry as trig
from PanCAD.utils import verification
from PanCAD.geometry import Point, Line, LineSegment, Plane

ROUNDING_PLACES = 10

class TestPlaneInit(unittest.TestCase):
    
    def test_plane_init_no_arg(self):
        pln = Plane()
    
    def test_plane_init_origin(self):
        pt = Point(0, 0, 0)
        normal = (1, 0, 0)
        pln = Plane(pt, normal)
        results = [
            pln.reference_point == pt,
            verification.isTupleAlmostEqual(pln.normal, normal, ROUNDING_PLACES)
        ]
        self.assertTrue(all(results))
    
    def test_plane_init_111(self):
        pt = Point(1, 1, 1)
        normal = trig.get_unit_vector((1, 1, 1))
        pln = Plane(pt, normal)
        results = [
            pln.reference_point == pt,
            verification.isTupleAlmostEqual(pln.normal, normal, ROUNDING_PLACES)
        ]
        self.assertTrue(all(results))
    
    def test_plane_init_003(self):
        pt = Point(0, 0, 3)
        normal = trig.get_unit_vector((1, 1, 1))
        pln = Plane(pt, normal)
        closest_pt = Point(1, 1, 1)
        results = [
            pln.reference_point == closest_pt,
            verification.isTupleAlmostEqual(pln.normal, normal, ROUNDING_PLACES)
        ]
        self.assertTrue(all(results))

if __name__ == "__main__":
    unittest.main()