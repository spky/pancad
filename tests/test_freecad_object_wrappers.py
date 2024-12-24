import sys
from pathlib import Path
import unittest

sys.path.append('src')

import free_cad_object_wrappers as fcow

class TestFreeCADObjectWrappers(unittest.TestCase):
    
    def setUp(self):
        self.FOLDER = 'tests/sample_freecad/'
        self.FILENAME = 'FreeCAD_Test_Model.FCStd'
        self.path = self.FOLDER + self.FILENAME
        self.fc = fcow.FreeCADModel(self.path)
    
    def test_init(self):
        pass

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()