import unittest

import pytest

from pancad.geometry.extrude import Extrude, ExtrudeSettings, DEFAULT_NAME
from pancad.geometry.constraints import (
    Coincident, Vertical, Horizontal,
    Distance, HorizontalDistance, VerticalDistance,
)
from pancad.geometry.constants import FeatureType as FT, ConstraintReference as CR

from tests.sample_pancad_objects import sample_sketches


# Testing Properties During Nominal Initialization
@pytest.fixture(
    scope="module",
    params=[
        (FT.DIMENSION, 1, 0, "mm", "test_extrude"),
        (FT.DIMENSION, 1, 0, "mm", None),
        (FT.ANTI_DIMENSION, 1, 0, "mm", "test_extrude"),
    ]
)
def square_extrude(request):
    type_, length, opposite, unit, name = request.param
    params = {
        "type_": type_,
        "length": length,
        "opposite_length": opposite,
        "unit": unit,
        "name": name
    }
    sketch = sample_sketches.square()
    settings = ExtrudeSettings(type_, length, opposite, unit, name)
    yield Extrude(sketch, settings), params

def test_length(square_extrude):
    assert square_extrude[0].length == square_extrude[1]["length"]

def test_type_(square_extrude):
    assert square_extrude[0].type_ == square_extrude[1]["type_"]

def test_opposite_length(square_extrude):
    assert square_extrude[0].opposite_length == square_extrude[1]["opposite_length"]

def test_unit(square_extrude):
    assert square_extrude[0].unit == square_extrude[1]["unit"]

def test_name(square_extrude):
    extrude, params = square_extrude
    if params["name"] is None:
        assert extrude.name == DEFAULT_NAME
    else:
        assert extrude.name == params["name"]

def test_length_change(square_extrude):
    new_length = 300
    extrude, params = square_extrude
    extrude.length = new_length
    assert extrude.length == new_length and extrude.type_ == params["type_"]

# Testing from_length
@pytest.mark.parametrize(
    "type_",
    [
        FT.UP_TO_FACE, FT.UP_TO_LAST, FT.UP_TO_FIRST, FT.UP_TO_BODY,
        FT.TWO_DIMENSIONS, FT.ANTI_TWO_DIMENSIONS,
    ]
)
def test_from_length_type_exception(type_):
    with pytest.raises(TypeError):
        test = Extrude.from_length(sample_sketches.square(), 1, type_=type_)

def test_from_length_nominal():
    extrude = Extrude.from_length(sample_sketches.square(), 1)
