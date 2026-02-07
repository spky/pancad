"""Tests converting pancad objects to freecad objects."""

from importlib.util import find_spec
from pathlib import Path

import pytest

from tests.sample_pancad_objects.sample_part_files import (
    empty_part_file,
    cube_part_file,
)

from pancad.cad.freecad._feature_translation import new_document_from_part

SAMPLE_FREECAD = Path(find_spec("tests.sample_freecad").origin).parent

# @pytest.fixture(params=["cube_1x1x1.FCStd"])
# def freecad_doc(request):
    # """Generic 1x1x1 cube file for easy testing."""
    # return freecad.open(str(SAMPLE_FREECAD / request.param))

@pytest.mark.parametrize(
    "part_file_fixture, expected",
    [
        ("empty_part_file", 8),
        ("cube_part_file", 9),
    ]
)
def test_new_document_from_part(part_file_fixture, expected, request):
    part_file = request.getfixturevalue(part_file_fixture)
    document = new_document_from_part(part_file)
    assert len(document.Objects) == expected
