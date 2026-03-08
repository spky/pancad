"""Tests converting pancad objects to freecad objects."""

from importlib.util import find_spec
from pathlib import Path

import pytest

from pancad.cad.freecad._feature_translation import (
    new_document_from_part, new_part_from_document
)
from pancad.cad.freecad.read_xml import FCStd

SAMPLE_FREECAD = Path(find_spec("tests.sample_freecad").origin).parent

@pytest.fixture(params=[
    "cube_1x1x1.FCStd",
    "one_of_each_sketch_geometry.FCStd",
    "cube_1x1x1_PointOnObject.FCStd",
    ]
)
def freecad_doc(request):
    """Generic 1x1x1 cube file for easy testing."""
    yield str(SAMPLE_FREECAD / request.param)

@pytest.mark.parametrize(
    "part_file_fixture, expected",
    [
        ("empty_part_file", 8),
        ("square_sketch_part_file", 9),
        ("cube_part_file", 10),
        ("cylinder_part_file", 10),
        ("rounded_edge_cube_part_file", 10),
        pytest.param("ellipse_part_file", 10,
                     marks=pytest.mark.xfail(reason="Ellipse write api side not implemented")),
    ]
)
def test_new_document_from_part(part_file_fixture, expected, tmp_path, request):
    part_file = request.getfixturevalue(part_file_fixture)
    document = new_document_from_part(part_file)
    document.recompute()
    document.saveAs(str(tmp_path / "test_new_document_from_part.FCStd"))
    assert len(document.Objects) == expected

@pytest.fixture
def fcstd(freecad_doc):
    yield FCStd.from_path(freecad_doc)

@pytest.fixture
def xml_doc(fcstd):
    yield fcstd.document

def test_read_label(xml_doc):
    # Check that at least the label property reading is working.
    label = xml_doc.get_property("Label").value
    assert label == xml_doc.file.path.stem

def test_fcstd_metadata(fcstd):
    metadata = fcstd.metadata
    assert metadata.label == fcstd.path.stem

def test_new_part_from_document(fcstd):
    part_file = new_part_from_document(fcstd)

def test_square_sketch_variations(square_variations_part_file, tmp_path):
    document = new_document_from_part(square_variations_part_file)
    document.recompute()
    document.saveAs(str(tmp_path / "sketch_variation.FCStd"))

def test_angle_sweep_sketches(angle_dimension_sweep_part_file, tmp_path):
    document = new_document_from_part(angle_dimension_sweep_part_file)
    document.recompute()
    document.saveAs(str(tmp_path / "angle_sweep.FCStd"))
