import sys
from pathlib import Path
import unittest

sys.path.append('src')

import free_cad_object_wrappers as fcow

class TestFreeCADObjectWrappers(unittest.TestCase):
    
    def setUp(self):
        