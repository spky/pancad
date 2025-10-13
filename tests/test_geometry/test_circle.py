import unittest

from pancad.geometry import Circle, Point
from pancad.utils.verification import assertPancadAlmostEqual

ROUNDING_PLACES = 10

class TestInit(unittest.TestCase):
    
    def setUp(self):
        self.radius = 1
        self.uid = "test_circle"
    
    def check_values(self,
                     test_circle: Circle,
                     center_point: Point,
                     radius: int | float,
                     vector_1: tuple=None,
                     vector_2: tuple=None,):
        test_vector_1, test_vector_2 = test_circle.get_orientation_vectors()
        
        with self.subTest(expected_center=center_point,
                          test_center=test_circle.center):
            assertPancadAlmostEqual(self, test_circle.center, center_point,
                                    ROUNDING_PLACES)
        with self.subTest(expected_radius=radius,
                          test_radius=test_circle.radius):
            self.assertAlmostEqual(test_circle.radius, radius, ROUNDING_PLACES)
        with self.subTest(expected_vector_1=vector_1,
                          test_vector=test_vector_1):
            if vector_1 is None:
                self.assertEqual(test_vector_1, vector_1)
            else:
                assertPancadAlmostEqual(self, test_vector_1, vector_1,
                                        ROUNDING_PLACES)

class Test2DCircle(TestInit):
    
    def setUp(self):
        super().setUp()
        self.center = Point(0, 0)
    
    def test_for_nominal_error(self):
        circle = Circle(self.center, self.radius, uid=self.uid)
        self.check_values(circle, self.center, self.radius)
    
    def test_for_nominal_error_no_uid(self):
        circle = Circle(self.center, self.radius)
        self.check_values(circle, self.center, self.radius)
    
    def test_orientation_vector_error(self):
        with self.assertRaises(ValueError):
            circle = Circle(self.center, self.radius,
                            (1, 0, 0), (0, 1, 0),uid=self.uid)
    
    def test_negative_radius_error(self):
        with self.assertRaises(ValueError):
            circle = Circle(self.center, -1, self.uid)
    
    def test_set_uid(self):
        circle = Circle(self.center, self.radius)
        circle.uid = self.uid
        self.check_values(circle, self.center, self.radius)
    
    def test_update(self):
        circle = Circle(self.center, self.radius)
        new_center = Point(1, 1)
        new_radius = 2
        new_circle = Circle(new_center, new_radius)
        circle.update(new_circle)
        self.check_values(circle, new_center, new_radius)
    
    def test_for_repr_error(self):
        circle = Circle(self.center, self.radius, uid=self.uid)
        repr_str = repr(circle)
    
    def test_for_str_error(self):
        circle = Circle(self.center, self.radius, uid=self.uid)
        str_str = str(circle)
    
    def test_equality_true(self):
        circle_1 = Circle(self.center, self.radius, uid=self.uid + "_1")
        circle_2 = Circle(self.center, self.radius, uid=self.uid + "_2")
        self.assertTrue(circle_1 == circle_2)
    
    def test_equality_false(self):
        circle_1 = Circle(self.center, self.radius, uid=self.uid + "_1")
        circle_2 = Circle(self.center, self.radius + 1, uid=self.uid + "_2")
        self.assertFalse(circle_1 == circle_2)


class Test3DCircle(TestInit):
    
    def setUp(self):
        super().setUp()
        self.center = Point(0, 0, 0)
        self.vector_1 = (1, 0, 0)
        self.vector_2 = (0, 1, 0)
    
    def test_whether_nominal_error(self):
        circle = Circle(self.center, self.radius, self.vector_1, self.vector_2,
                        uid=self.uid)
        self.check_values(circle, self.center, self.radius,
                          self.vector_1, self.vector_2)
    
    def test_for_repr_error(self):
        circle = Circle(self.center, self.radius, self.vector_1, self.vector_2,
                        uid=self.uid)
        repr_str = repr(circle)
    
    def test_for_repr_error(self):
        circle = Circle(self.center, self.radius, self.vector_1, self.vector_2,
                        uid=self.uid)
        str_str = str(circle)
    
    def test_equality_true(self):
        circle_1 = Circle(self.center, self.radius,
                          self.vector_1, self.vector_2, uid=self.uid + "_1")
        circle_2 = Circle(self.center, self.radius,
                          self.vector_1, self.vector_2, uid=self.uid + "_2")
        self.assertTrue(circle_1 == circle_2)
    
    def test_equality_false(self):
        circle_1 = Circle(self.center, self.radius,
                          self.vector_1, self.vector_2, uid=self.uid + "_1")
        circle_2 = Circle(self.center, self.radius + 1,
                          self.vector_1, self.vector_2, uid=self.uid + "_2")
        self.assertFalse(circle_1 == circle_2)