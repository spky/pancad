import unittest

from PanCAD.geometry import CoordinateSystem, LineSegment, Sketch, Extrude
from PanCAD.geometry.constraints import (
    Coincident, Vertical, Horizontal,
    Distance, HorizontalDistance, VerticalDistance,
)
from PanCAD.geometry.constants import FeatureType, ConstraintReference as CR

class TestExtrudeInit(unittest.TestCase):
    
    def setUp(self):
        cs = CoordinateSystem((0, 0, 0))
        geometry = [ # A 1x1 square
            LineSegment((0, 0), (1, 0)),
            LineSegment((1, 0), (1, 1)),
            LineSegment((1, 1), (0, 1)),
            LineSegment((0, 1), (0, 0)),
        ]
        constraints = [
            Horizontal(geometry[0], CR.CORE),
            Vertical(geometry[1], CR.CORE),
            Horizontal(geometry[2], CR.CORE),
            Vertical(geometry[3], CR.CORE),
            Coincident(geometry[0], CR.START, geometry[3], CR.END),
            Coincident(geometry[0], CR.END, geometry[1], CR.START),
            Coincident(geometry[1], CR.END, geometry[2], CR.START),
            Coincident(geometry[2], CR.END, geometry[3], CR.START),
            VerticalDistance(geometry[0], CR.CORE, geometry[2], CR.CORE, 1),
            HorizontalDistance(geometry[1], CR.CORE, geometry[3], CR.CORE, 1),
        ]
        self.sketch = Sketch(cs, geometry=geometry, constraints=constraints,
                             uid="TestSketch")
        self.uid = "test_extrude"
        self.length = 1
    
    def results_vs_expected(self, extrude: Extrude):
        self.assertCountEqual(self.get_results(extrude),
                              self.exp_list(self.expected))
    
    @staticmethod
    def get_results(e):
        return [
            e.feature_type,
            e.uid,
            e.length,
            e.opposite_length,
            e.is_midplane,
            e.is_reverse_direction,
            e.end_feature,
        ]
    
    @staticmethod
    def make_expected(feature_type, uid=None,
                      length=None, opposite_length=None,
                      is_midplane=False, is_reverse_direction=False,
                      end_feature=None):
        return {
            "feature_type": feature_type,
            "uid": uid,
            "length": length,
            "opposite_length": opposite_length,
            "is_midplane": is_midplane,
            "is_reverse_direction": is_reverse_direction,
            "end_feature": end_feature,
        }
    
    @staticmethod
    def exp_list(exp: dict) -> list:
        return [e for _, e in exp.items()]

class TestFromLength(TestExtrudeInit):
    
    def setUp(self):
        super().setUp()
        self.expected = self.make_expected(
            None, uid=self.uid, length=self.length
        )
    
    def test_from_length_dimension(self):
        e = Extrude.from_length(self.sketch, self.length, self.uid)
        self.expected["feature_type"] = FeatureType.DIMENSION
        self.results_vs_expected(e)
    
    def test_from_length_anti_dimension(self):
        e = Extrude.from_length(self.sketch, self.length, self.uid,
                                is_reverse_direction=True)
        self.expected["feature_type"] = FeatureType.ANTI_DIMENSION
        self.expected["is_reverse_direction"] = True
        self.results_vs_expected(e)
    
    def test_from_length_midplane(self):
        e = Extrude.from_length(self.sketch, self.length, self.uid,
                                is_midplane=True)
        self.expected["feature_type"] = FeatureType.SYMMETRIC
        self.expected["is_midplane"] = True
        self.results_vs_expected(e)

class TestFrom2Lengths(TestExtrudeInit):
    
    def setUp(self):
        super().setUp()
        self.opposite_length = 2
        self.expected = self.make_expected(
            None, uid=self.uid, length=self.length,
            opposite_length=self.opposite_length
        )
    
    def test_from_lengths_two_dimensions(self):
        e = Extrude.from_length(self.sketch, self.length, self.uid,
                                opposite_length=self.opposite_length)
        self.expected["feature_type"] = FeatureType.TWO_DIMENSIONS
        self.results_vs_expected(e)
    
    def test_from_lengths_anti_two_dimensions(self):
        e = Extrude.from_length(self.sketch, self.length, self.uid,
                                opposite_length=self.opposite_length,
                                is_reverse_direction=True)
        self.expected["feature_type"] = FeatureType.ANTI_TWO_DIMENSIONS
        self.expected["is_reverse_direction"] = True
        self.results_vs_expected(e)