import unittest
from uuid import UUID

from numpy import array

from pancad.geometry import CircularArc, Point

class InitTest(unittest.TestCase):
    
    def check_values(self,
                     test: CircularArc,
                     center,
                     radius,
                     start_vector,
                     end_vector,
                     is_clockwise):
        
        start = array(center) + (radius * array(start_vector))
        end = array(center) + (radius * array(end_vector))
        
        tests = [
            ("center", Point(center), test.center),
            ("radius", radius, test.radius),
            ("start vector", start_vector, test.start_vector),
            ("start", Point(start), test.start),
            ("end vector", end_vector, test.end_vector),
            ("end", Point(end), test.end),
            ("is clockwise", is_clockwise, test.is_clockwise),
        ]
        for name, expected, result in tests:
            with self.subTest(name=name, expected=expected, result=result):
                self.assertEqual(result, expected)
        with self.subTest(expected="uid is a UUID"):
            self.assertTrue(isinstance(test.uid, UUID))
        
    def test_2d_unit_arc(self):
        center = (0, 0)
        radius = 2
        start_vector = (1, 0)
        end_vector = (0, 1)
        is_clockwise = False
        test = CircularArc(
            center, radius, start_vector, end_vector, is_clockwise
        )
        self.check_values(
            test, center, radius, start_vector, end_vector, is_clockwise
        )