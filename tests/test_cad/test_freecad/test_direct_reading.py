from pathlib import Path
from pprint import pp
from unittest import TestCase

from tests import sample_freecad

from pancad.cad.freecad.direct_reading import Document

class Cube1x1x1(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1.FCStd"
    
    def test_init(self):
        test = Document(self.path)
        # print()
        # pp(test.members)