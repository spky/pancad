import sys
import os
from pathlib import Path
import unittest

sys.path.append('src')

import free_cad_object_wrappers as fcow
import FreeCAD as App
import Part

class TestFreeCADObjectWrappers(unittest.TestCase):
    
    def setUp(self):
        self.FOLDER = 'tests/sample_freecad/'
        self.FILENAME = 'FreeCAD_Test_Model.FCStd'
        self.path = self.FOLDER + self.FILENAME
        self.fc = fcow.FreeCADModel(self.path)
    
    def test_init(self):
        pass

class TestSketch(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_add_line(self):
        
        tests = [
            [[0, 0], [1, 1]],
            [[0, 0, 0], [1, 1, 0]],
        ]
        for t in tests:
            with self.subTest(t=t):
                sketch = fcow.Sketch()
                sketch.add_line(t[0], t[1])
                line = sketch.geometry[0] 
                check = [list(line.StartPoint), list(line.EndPoint)]
                if t[0] == 2:
                    t[0].append(0)
                    t[1].append(0)
                self.assertCountEqual(check, [t[0], t[1]])
    
    def test_add_circle(self):
        
        tests = [
            [[0, 1], 2],
            [[1, 2, 0], 2],
        ]
        for t in tests:
            with self.subTest(t=t):
                sketch = fcow.Sketch()
                sketch.add_circle(t[0], t[1])
                circle = sketch.geometry[0] 
                check = [list(circle.Location), circle.Radius]
                if t[0] == 2:
                    t[0].append(0)
                self.assertCountEqual(check, [t[0], t[1]])
    
    def test_add_circular_arc(self):
        tests = [
            [[0, 0], 2, 0, 1],
        ]
        for t in tests:
            with self.subTest(t=t):
                sketch = fcow.Sketch()
                sketch.add_circular_arc(t[0], t[1], t[2], t[3])
                arc = sketch.geometry[0]
                print(arc)


class TestFile(unittest.TestCase):
    def setUp(self):
        self.TEST_FOLDER = "tests"
        self.OUTPUT_DUMP = os.path.join(self.TEST_FOLDER,
                                        "test_output_dump")
    
    def test_document_init(self):
        self.filepath = os.path.join(self.OUTPUT_DUMP,
                                     "test_freecad_file_init.FCStd")
        file = fcow.File(self.filepath)
        obj = file._document.addObject("Sketcher::SketchObjectPython", "Sketch1")
        file.save()
    
    def test_add_sketch(self):
        self.filepath = os.path.join(self.OUTPUT_DUMP,
                                      "test_freecad_add_sketch.FCStd")
        file = fcow.File(self.filepath)

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()