"""A module to provide functions used to verify that PanCAD is operating 
correctly."""
import math

from PanCAD.geometry.point import Point

def assertTupleAlmostEqual(self_input, 
                           tuple_a: tuple, tuple_b: tuple, places: int = 7):
    for val1, val2 in zip(tuple_a, tuple_b):
        if type(val1) is float or type(val2) is float:
            if math.isnan(val1) and math.isnan(val2):
                self_input.assertTrue(math.isnan(val1) and math.isnan(val2))
            else:
                self_input.assertAlmostEqual(val1, val2, places)
        else:
            self_input.assertEqual(val1, val2)

def assertPointsAlmostEqual(self_input,
                            point_a: Point, point_b: Point, places: int = 7):
    assertTupleAlmostEqual(self_input, tuple(point_a), tuple(point_b), places)