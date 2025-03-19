import sys
import os
from pathlib import Path
import unittest
sys.path.append('src')

from PanCAD.freecad import object_wrappers as fcow
from PanCAD import file_handlers

import FreeCAD as App
import Part

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
                check = [list(arc.Center), arc.Radius,
                         arc.FirstParameter, arc.LastParameter]
                self.assertCountEqual(check, t)
    
    def test_add_point(self):
        tests = [
            [0, 0],
            [1, 1],
        ]
        for t in tests:
            with self.subTest(t=t):
                sketch = fcow.Sketch()
                sketch.add_point(t)
                point = sketch.geometry[0]
                check = [point.X, point.Y, point.Z]
                if len(t) == 2:
                    t.append(0)
                self.assertCountEqual(check, t)

class TestFile(unittest.TestCase):
    def setUp(self):
        self.TEST_FOLDER = "tests"
        self.OUTPUT_DUMP = os.path.join(self.TEST_FOLDER,
                                        "test_output_dump")
    
    def test_document_init(self):
        filepath = os.path.join(self.OUTPUT_DUMP,
                                "test_freecad_file_init.FCStd")
        if file_handlers.exists(filepath):
            os.remove(filepath)
        file = fcow.File(filepath, "w")
        obj = file._document.addObject("Sketcher::SketchObjectPython", "Sketch1")
        file.save()
    
    def test_add_sketch(self):
        filepath = os.path.join(self.OUTPUT_DUMP,
                                "test_freecad_add_sketch.FCStd")
        if file_handlers.exists(filepath):
            os.remove(filepath)
        file = fcow.File(filepath, "w")
        sketch = fcow.Sketch()
        sketch.add_line([0, 0], [1, 1])
        sketch.add_circle([0, 0], 1)
        sketch.add_circular_arc([0, 0], 2, 0, 1)
        sketch.add_point([3, 3])
        sketch.label = "test_sketch"
        file.new_sketch(sketch)
        file.save()

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()