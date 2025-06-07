import unittest

from PanCAD.graphics.svg import Path

class TestPathDataParsing(unittest.TestCase):
    
    def test_init_path_parse(self):
        d = "M 1.0 1 3 3 4 4 L 2.2e-4 2 4 4 l 10 10 H 1 2 V 3 v 4Z"
        path_id = "path1"
        path = Path(path_id, d)
        print(path.geometry)
    # todo: check that the string is fully parsed with no left over params


if __name__ == "__main__":
    unittest.main()