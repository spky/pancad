import sys
import unittest
import logging

from PanCAD.cad.freecad._bootstrap import find_app_dir

logger = logging.getLogger()
logger.level = logging.INFO
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

class TestFreeCADSetUp(unittest.TestCase):
    
    def test_find_app_dir(self):
        path = find_app_dir()