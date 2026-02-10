"""A module providing sample part files to test pancad with."""

import pytest

from pancad.filetypes.part_file import PartFile
from pancad.constraints.state_constraint import AlignAxes
from pancad.constants import FeatureType as FT
from pancad.geometry.extrude import Extrude, ExtrudeSettings

from tests.sample_pancad_objects import sample_sketches

@pytest.fixture
def empty_part_file() -> PartFile:
    """A partfile with nothing in it."""
    return PartFile("EmptyTestPart")

@pytest.fixture
def square_sketch_part_file() -> PartFile:
    """A partfile with just a square sketch inside it"""
    part = PartFile("SquareSketchPartTest")
    sketch = sample_sketches.square()
    constraints = [
        AlignAxes(part.container.feature_system.coordinate_system,
                  sketch.pose.coordinate_system),
    ]
    part.container.feature_system.features.append(sketch)
    part.container.feature_system.constraints.extend(constraints)
    return part

@pytest.fixture
def cube_part_file() -> PartFile:
    """A partfile with just a square sketch inside it"""
    part = PartFile("CubePartTest")
    sketch = sample_sketches.square()
    extrude_settings = ExtrudeSettings(type_=FT.DIMENSION, length=1, unit="mm")
    extrude = Extrude(sketch, extrude_settings, name="CubeExtrude")
    constraints = [
        AlignAxes(part.container.feature_system.coordinate_system,
                  sketch.pose.coordinate_system),
    ]
    part.container.feature_system.features.append(sketch)
    part.container.feature_system.constraints.extend(constraints)
    part.container.feature_system.features.append(extrude)
    return part
