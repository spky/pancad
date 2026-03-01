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
    """A partfile with just a square sketch and extrude inside it"""
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

@pytest.fixture
def cylinder_part_file() -> PartFile:
    part = PartFile("CylinderPartTest")
    sketch = sample_sketches.circle()
    extrude_settings = ExtrudeSettings(type_=FT.DIMENSION, length=1, unit="mm")
    extrude = Extrude(sketch, extrude_settings, name="CylinderExtrude")
    constraints = [
        AlignAxes(part.container.feature_system.coordinate_system,
                  sketch.pose.coordinate_system),
    ]
    part.container.feature_system.features.append(sketch)
    part.container.feature_system.constraints.extend(constraints)
    part.container.feature_system.features.append(extrude)
    return part
    
@pytest.fixture
def rounded_edge_cube_part_file() -> PartFile:
    part = PartFile("RoundedEdgeCubePartTest")
    sketch = sample_sketches.rounded_square()
    extrude_settings = ExtrudeSettings(type_=FT.DIMENSION, length=1, unit="mm")
    extrude = Extrude(sketch, extrude_settings, name="RoundedSquareExtrude")
    constraints = [
        AlignAxes(part.container.feature_system.coordinate_system,
                  sketch.pose.coordinate_system),
    ]
    part.container.feature_system.features.append(sketch)
    part.container.feature_system.constraints.extend(constraints)
    part.container.feature_system.features.append(extrude)
    return part

@pytest.fixture
def ellipse_part_file() -> PartFile:
    """A partfile with just a a single ellipse sketch and extrusion."""
    part = PartFile("EllipseExtrudePartTest")
    sketch = sample_sketches.ellipse()
    extrude_settings = ExtrudeSettings(type_=FT.DIMENSION, length=1, unit="mm")
    extrude = Extrude(sketch, extrude_settings, name="EllipseExtrude")
    constraints = [
        AlignAxes(part.container.feature_system.coordinate_system,
                  sketch.pose.coordinate_system),
    ]
    part.container.feature_system.features.append(sketch)
    part.container.feature_system.constraints.extend(constraints)
    part.container.feature_system.features.append(extrude)
    return part

@pytest.fixture
def square_variations_part_file(request, square_sketch_variations) -> PartFile:
    sketch = square_sketch_variations
    part = PartFile("square_sketch_variations")
    extrude_settings = ExtrudeSettings(type_=FT.DIMENSION, length=1, unit="mm")
    extrude = Extrude(sketch, extrude_settings, name="SquareVariationExtrude")
    constraints = [
        AlignAxes(part.container.feature_system.coordinate_system,
                  sketch.pose.coordinate_system),
    ]
    part.container.feature_system.features.append(sketch)
    part.container.feature_system.constraints.extend(constraints)
    part.container.feature_system.features.append(extrude)
    return part