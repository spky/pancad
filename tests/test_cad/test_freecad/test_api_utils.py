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

# Testing Reading Content

@pytest.fixture(params=["cube_1x1x1.FCStd", "one_of_each_sketch_geometry.FCStd"])
def freecad_doc(request):
    """Generic 1x1x1 cube file for easy testing."""
    return freecad.open(str(SAMPLE_FREECAD / request.param))

@pytest.fixture
def sketches(freecad_doc):
    """All sketches in the freecad document"""
    type_ = "Sketcher::SketchObject"
    return [obj for obj in freecad_doc.Objects if obj.TypeId == type_]

@pytest.fixture
def uid_pairs(freecad_doc) -> list[tuple[api_utils.FreeCADUID, object]]:
    """pairing of uid to the corresponding FreeCAD API object."""
    pairs = []
    for obj in freecad_doc.Objects:
        pairs.append((api_utils.FreeCADUID.from_feature(obj, freecad_doc), obj))
        if obj.TypeId == "Sketcher::SketchObject":
            for geo in obj.Geometry:
                pairs.append(
                    (api_utils.FreeCADUID.from_sketch_geometry(geo, obj, freecad_doc),
                     geo)
                )
    return pairs

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

def test_get_geometry_by_sketch_id(sketches):
    for sketch in sketches:
        label = sketch.Label
        for geometry in sketch.Geometry:
            id_ = api_utils.get_geometry_sketch_id(geometry, sketch)
            found_geometry = api_utils.get_geometry_by_sketch_id(id_, sketch)
            assert geometry.Content == found_geometry.Content

def test_get_geometry_sketch_index(sketches):
    for sketch in sketches:
        label = sketch.Label
        for index, geometry in enumerate(sketch.Geometry):
            found_index = api_utils.get_geometry_sketch_index(geometry, sketch)
            assert found_index == index

def test_get_constraint_sketch_index(sketches):
    for sketch in sketches:
        label = sketch.Label
        for index, constraint in enumerate(sketch.Constraints):
            found_index = api_utils.get_constraint_sketch_index(constraint, sketch)
            assert found_index == index

def test_get_by_uid(freecad_doc, uid_pairs):
    for uid, obj in uid_pairs:
        found_obj = api_utils.get_by_uid(uid, freecad_doc)
        assert found_obj.Content == obj.Content

# Testing FreeCADUID

@pytest.fixture(
    params=[
        ["7c2a603d-b250-44ce-8938-f714395e519f", "feature", 2674],
        ["7c2a603d-b250-44ce-8938-f714395e519f", "sketchgeo", 2674, 10],
    ]
)
def uid_str(request):
    yield api_utils.FreeCADUID.delim.join(map(str, request.param))

@pytest.fixture
def freecad_uid(uid_str):
    yield api_utils.FreeCADUID(uid_str)

def test_file_uid(freecad_uid):
    assert freecad_uid.file_uid == freecad_uid.split(api_utils.FreeCADUID.delim)[0]

def test_type_(freecad_uid):
    assert freecad_uid.type_ == freecad_uid.split(api_utils.FreeCADUID.delim)[1]

def test_data(freecad_uid):
    all_data = freecad_uid.split(freecad_uid.delim)
    int_data = tuple(map(int, all_data[2:]))
    data = tuple(all_data[:2]) + int_data
    assert freecad_uid.data == data


# Testing FreeCADUID from FreeCAD API objects

def test_from_feature(freecad_doc):
    for obj in freecad_doc.Objects:
        uid = api_utils.FreeCADUID.from_feature(obj, freecad_doc)
        assert uid.data.feature_id == obj.ID

def test_from_sketch_geometry(freecad_doc, sketches):
    uids = []
    for sketch in sketches:
        for geometry in sketch.Geometry:
            uid = api_utils.FreeCADUID.from_sketch_geometry(
                geometry, sketch, freecad_doc
            )
            found_id = api_utils.get_geometry_sketch_id(geometry, sketch)
            assert uid.data.geometry_id == found_id
    if len(uids) != len(set(uids)):
        raise ValueError("Duplicate uids were created!", uids)

def test_from_sketch_constraint(freecad_doc, sketches):
    uids = []
    for sketch in sketches:
        for constraint in sketch.Constraints:
            uid = api_utils.FreeCADUID.from_sketch_constraint(
                constraint, sketch, freecad_doc
            )
            uids.append(uid)
    if len(uids) != len(set(uids)):
        raise ValueError("Duplicate uids were created!", uids)
