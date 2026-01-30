"""Tests for the FreeCAD api_utils module - utils that process common FreeCAD 
API data.
"""

from importlib.util import find_spec
from pathlib import Path

import pytest

try:
    import Part
    import FreeCAD as App
except ImportError:
    import sys
    from pancad.cad.freecad._bootstrap import get_app_dir
    sys.path.append(str(get_app_dir()))
    import FreeCAD as freecad

from pancad.cad.freecad import api_utils

SAMPLE_FREECAD = Path(find_spec("tests.sample_freecad").origin).parent

@pytest.fixture(params=["cube_1x1x1.FCStd", "one_of_each_sketch_geometry.FCStd"])
def freecad_doc(request):
    """Generic 1x1x1 cube file for easy testing."""
    return freecad.open(str(SAMPLE_FREECAD / request.param))

@pytest.fixture
def sketches(freecad_doc):
    """All sketches in the freecad document"""
    type_ = "Sketcher::SketchObject"
    return [obj for obj in freecad_doc.Objects if obj.TypeId == type_]

def test_read_element_xml(sketches):
    for element in sketches:
        content = api_utils.read_element_xml(element)

def test_get_geometry_sketch_id(sketches):
    ext_type = "Sketcher::SketchGeometryExtension"
    for sketch in sketches:
        label = sketch.Label
        for geometry in sketch.Geometry:
            found_id = api_utils.get_geometry_sketch_id(geometry, sketch)
            try:
                test_id = geometry.getExtensionOfType(ext_type).Id
            except:
                # Some elements like GeomPoint can't have their Id checked
                continue
            assert found_id == test_id

def test_get_geometry_sketch_index(sketches):
    for sketch in sketches:
        label = sketch.Label
        for index, geometry in enumerate(sketch.Geometry):
            found_index = api_utils.get_geometry_sketch_index(geometry, sketch)
            assert found_index == index
