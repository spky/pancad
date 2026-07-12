import unittest
from math import radians

import pytest

from tests.testing_utils import sketch_gen

@pytest.fixture(
    params = [
        sketch_gen.square,
        sketch_gen.ellipse,
        sketch_gen.rounded_square
    ]
)
def default_sketch(request):
    """Executes sample sketches with no parameters. These sketches should not 
    have any external dependencies.
    """
    yield request.param()

@pytest.fixture
def constraint_in_sketch(default_sketch):
    yield default_sketch.geometry_system.constraints[0]

def test_get_constraint_dependencies(constraint_in_sketch, default_sketch):
    dependencies = constraint_in_sketch.get_dependencies()
    assert len(dependencies) == 1
    assert dependencies[0] is default_sketch

def test_get_system_dependencies(default_sketch):
    dependencies = default_sketch.geometry_system.get_dependencies()
    assert len(dependencies) == 1
    assert dependencies[0] is default_sketch

def test_get_sketch_dependencies(default_sketch):
    dependencies = default_sketch.get_dependencies()
    assert len(dependencies) == 0

if __name__ == "__main__":
    unittest.main()