from pathlib import Path
from pprint import pp
from unittest import TestCase

from tests import sample_freecad

from pancad.cad.freecad.direct_reading import Document, read_properties
from pancad.cad.freecad.constants import XMLTag

class Cube1x1x1(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1.FCStd"
    
    def test_init(self):
        test = Document(self.path)
        # print()
        # pp(test.members)
    
    def test_read_sketch_properties(self):
        test = Document(self.path)
        sketch_element = test.objects[2674][XMLTag.OBJECT_DATA]
        properties = sketch_element.find(XMLTag.PROPERTIES)
        result = read_properties(sketch_element, XMLTag.PROPERTY)
        print()
        pp(result)