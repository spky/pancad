import unittest

from pancad.geometry.point import Point
from pancad.constraints.state_constraint import Coincident

class TestInit(unittest.TestCase):
    
    def setUp(self):
        self.a = Point(0, 0)
        self.b = Point(0, 0)
        self.uid = "test"
    
    def test_point_init(self):
        # Checking whether init errors out nominally
        c = Coincident(self.a, self.b, uid=self.uid)
    
    def test_point_change(self):
        # Check whether updating the point updates the value in coincident
        c = Coincident(self.a, self.b, uid=self.uid)
        original_a = self.a.copy()
        new_a = Point(1, 1)
        self.a.update(new_a)
        self.assertEqual(c.get_parents()[0], new_a)

if __name__ == "__main__":
    unittest.main()