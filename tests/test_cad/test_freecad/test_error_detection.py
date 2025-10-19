from pathlib import Path
import unittest

from pancad.cad.freecad.freecad_python import call_freecad_python
from pancad.cad.freecad import error_detection
from tests import sample_freecad

class TestErrorDetection(unittest.TestCase):
    
    def setUp(self):
        self.sample_dir = Path(sample_freecad.__file__).parent
    
    def test_invalid_sketches(self):
        filename = "invalid_sketches.FCStd"
        test = call_freecad_python(error_detection.__file__,
                                   self.sample_dir / filename)
        
        DETACHED = "unattached"
        NO_UNCONSTRAINED = 5
        NO_ERRORS = 4
        
        with self.subTest(detached=DETACHED):
            detached_errs = test["detached"]
            self.assertEqual(detached_errs[0].split(":")[-1].strip(), DETACHED)
            self.assertEqual(len(detached_errs), 1)
        
        with self.subTest(expected_unconstrained=NO_UNCONSTRAINED):
            self.assertEqual(len(test["unconstrained"]), NO_UNCONSTRAINED)
        
        with self.subTest(expected_errors=NO_ERRORS):
            self.assertEqual(len(test["error"]), NO_ERRORS)
    
    def test_invalid_pads(self):
        filename = "invalid_pads.FCStd"
        test = call_freecad_python(error_detection.__file__,
                                   self.sample_dir / filename)
        with self.subTest(expected_unconstrained=1):
            self.assertEqual(len(test["unconstrained"]), 1)
        with self.subTest(expected_errors=1):
            self.assertEqual(len(test["error"]), 1)
