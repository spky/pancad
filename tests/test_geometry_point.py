import sys
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
import os

import numpy as np

sys.path.append('src')

from PanCAD.geometry.point import Point

class TestPointInit(unittest.TestCase):
    
    def setUp(self):
        self.coordinate1 = (1, 1, 1)
        self.coordinates = coordinates = [
            (0, 0, 0),
            (1, 1, 1),
            (1, 1),
        ]
    
    def test_point_init_no_arg(self):
        pt = Point()
    
    def test_point_init_tuple(self):
        for coordinate in self.coordinates:
            with self.subTest(coordinate=coordinate):
                pt = Point(coordinate)
                self.assertCountEqual(coordinate, pt.position)
    
    def test_point_tuple_iter(self):
        for coordinate in self.coordinates:
            with self.subTest(coordinate=coordinate):
                pt = Point(coordinate)
                self.assertCountEqual(tuple(pt), pt.position)
    
    def test_point_numpy_array(self):
        pt = Point(self.coordinate1)
        self.assertCountEqual(np.array(pt), np.array(self.coordinate1))
    
    def test_str_dunder(self):
        pt = Point(self.coordinate1)
        self.assertEqual(str(pt), "PanCAD Point at position (1, 1, 1)")
    
    def test_vector(self):
        pass

class TestPointFunctions(unittest.TestCase):
    
    def setUp(self):
        self.pt = Point()
        self.coordinates = coordinates = [
            (0, 0, 0),
            (1, 1, 1),
            (1, 1),
        ]
    
    def test_set_position(self):
        for coordinate in self.coordinates:
            with self.subTest(coordinate = coordinate):
                self.pt.position = coordinate
                self.assertEqual(self.pt.position, coordinate)
    
    def test_get_xyz(self):
        pass

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()