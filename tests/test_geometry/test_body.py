import unittest

from PanCAD.geometry import Body

class TestBodyInit(unittest.TestCase):
    
    def test_init(self):
        body = Body(uid="test")

if __name__ == "__main__":
    unittest.main()