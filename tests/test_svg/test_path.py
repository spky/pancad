import unittest

from pancad.graphics.svg import Path
from pancad.geometry import LineSegment

class TestPathDataParsing(unittest.TestCase):
    
    def setUp(self):
        self.path_id = "test_path"
    
    def test_init_path_parse(self):
        d = "M 1.0 1 3 3 4 4 L 2.2e-4 2 4 4 l 10 10 H 1 2 V 3 v 4Z"
        path = Path(self.path_id, d)
        # print(path.geometry)
        # todo: add assertion
    # todo: check that the string is fully parsed with no left over params
    
    def test_get_normalized_d(self):
        tests = [
            ("  M 1 1 3 3 4 4 L 2 2 5 5  ", "M1,1 3,3 4,4 L2,2 5,5"),
        ]
        for original_d, normalized_d in tests:
            with self.subTest(original=original_d, normalized=normalized_d):
                path = Path(self.path_id, original_d)
                Path.COORDINATE_DELIMITER = ","
                Path.PARAMETER_DELIMITER = " "
                Path.POST_COMMAND_CHAR = ""
                Path.PRE_COMMAND_CHAR = " "
                result = path._normalize_d(original_d)
                self.assertEqual(result, normalized_d)

class TestGeometrySetting(unittest.TestCase):
    
    def setUp(self):
        self.path_id = "test_path"
    
    def test_set_geometry_line_segments_equal_points(self):
        geo_list = [
            LineSegment((1, 1), (2, 2)),
            LineSegment((2, 2), (5, 5)),
            LineSegment((5, 5), (10, 10)),
        ]
        path = Path.from_geometry(self.path_id, geo_list)
        self.assertEqual(path.d, "M1,1 2,2 5,5 10,10")
    
    def test_set_geometry_line_segments_unequal_points(self):
        geo_list = [
            LineSegment((1, 1), (2, 2)),
            LineSegment((3, 3), (5, 5)),
        ]
        path = Path.from_geometry(self.path_id, geo_list)
        self.assertEqual(path.d, "M1,1 2,2 M3,3 5,5")
    
    def test_geometry_uids(self):
        geo_list = []
        for i in range(1, 12):
            geo_list.append(LineSegment((0, 0), (i, i/2)))
        path = Path.from_geometry(self.path_id, geo_list)
        self.assertEqual(path.geometry[0].uid, self.path_id + "_00")
    
    def test_svg_id_update(self):
        geo_list = [
            LineSegment((1, 1), (2, 2)),
            LineSegment((3, 3), (5, 5)),
        ]
        path = Path.from_geometry(self.path_id, geo_list)
        new_id = "new_test_path"
        path.svg_id = new_id
        self.assertEqual(path.geometry[0].uid, new_id + "_0")
        

if __name__ == "__main__":
    unittest.main()