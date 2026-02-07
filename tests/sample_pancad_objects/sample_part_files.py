"""A module providing sample part files to test pancad with."""

import pytest

from pancad.filetypes.part_file import PartFile
from pancad.constraints.state_constraint import AlignAxes

from tests.sample_pancad_objects import sample_sketches

@pytest.fixture
def empty_part_file() -> PartFile:
    """A partfile with nothing in it."""
    return PartFile("EmptyTestPart")

@pytest.fixture
def cube_part_file() -> PartFile:
    part = PartFile("CubePartTest")
    sketch = sample_sketches.square()
    constraints = [
        AlignAxes(part.container.feature_system.coordinate_system,
                  sketch.pose.coordinate_system),
    ]
    part.container.feature_system.features.append(sketch)
    part.container.feature_system.constraints.extend(constraints)
    return part