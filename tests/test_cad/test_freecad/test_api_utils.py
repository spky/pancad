"""Tests for the FreeCAD api_utils module - utils that process common FreeCAD
API data.
"""

from importlib.util import find_spec
from pathlib import Path
from dataclasses import astuple

import pytest

from pancad.cad.freecad import api_utils, xml_utils
from pancad.cad.freecad.api import freecad, freecad_part

SAMPLE_FREECAD = Path(find_spec("tests.sample_freecad").origin).parent

# Testing Reading Content

@pytest.fixture(name="freecad_doc",
                params=["cube_1x1x1.FCStd", "one_of_each_sketch_geometry.FCStd"])
def fixture_freecad_doc(request):
    """Generic 1x1x1 cube file for easy testing."""
    return freecad.open(str(SAMPLE_FREECAD / request.param))

@pytest.fixture(name="sketches")
def fixture_sketches(freecad_doc):
    """All sketches in the freecad document"""
    type_ = "Sketcher::SketchObject"
    return [obj for obj in freecad_doc.Objects if obj.TypeId == type_]

@pytest.fixture(name="uid_pairs")
def fixture_uid_pairs(freecad_doc) -> list[tuple[api_utils.FreeCADUID, object]]:
    """pairing of uid to the corresponding FreeCAD API object."""
    pairs = []
    pairs.append((api_utils.read_document_uid(freecad_doc), freecad_doc))
    for obj in freecad_doc.Objects:
        pairs.append((api_utils.read_feature_uid(obj, freecad_doc), obj))
        if obj.TypeId == "Sketcher::SketchObject":
            for geo in obj.Geometry:
                pairs.append(
                    (api_utils.read_geometry_uid(geo, "Geometry", obj, freecad_doc),
                     geo)
                )
            for geo in obj.ExternalGeo:
                pairs.append(
                    (api_utils.read_geometry_uid(geo, "ExternalGeo", obj, freecad_doc),
                     geo)
                )
            for con in obj.Constraints:
                pairs.append(
                    (api_utils.read_constraint_uid(con, obj, freecad_doc),
                     con)
                )
    return pairs

def test_read_element_xml(sketches):
    """Test that read_element_xml can read all test file sketch element xmls."""
    for element in sketches:
        api_utils.read_element_xml(element)

def test_get_geometry_sketch_id(sketches):
    """Test that get_geometry_sketch_id can get all test file sketch geometry
    ids.
    """
    ext_type = "Sketcher::SketchGeometryExtension"
    for sketch in sketches:
        for geometry in sketch.Geometry:
            found_id = api_utils.get_geometry_sketch_id(geometry, "Geometry",
                                                        sketch)
            try:
                test_id = geometry.getExtensionOfType(ext_type).Id
            except freecad_part.OCCError:
                if geometry.TypeId == "Part::GeomPoint":
                    # Some elements like GeomPoint can't have their Id checked
                    # because FreeCAD doesn't store its id correctly in the
                    # api xml.
                    continue
                raise
            assert found_id == test_id

def test_get_geometry_by_sketch_id(sketches):
    """Test that get_geometry_by_sketch_id can get all the geometry in all test
    files by their geometry uid.
    """
    for sketch in sketches:
        for geometry in sketch.Geometry:
            id_ = api_utils.get_geometry_sketch_id(geometry, "Geometry", sketch)
            found_geometry = api_utils.get_geometry_by_sketch_id(id_, "Geometry",
                                                                 sketch)
            assert geometry.Content == found_geometry.Content

def test_get_geometry_sketch_index(sketches):
    """Test that get_geometry_sketch_index can get the indices of all the
    geometry in all test files in their respective sketches.
    """
    for sketch in sketches:
        for index, geometry in enumerate(sketch.Geometry):
            found_index = api_utils.get_geometry_sketch_index(geometry, "Geometry",
                                                              sketch)
            assert found_index == index

def test_get_constraint_sketch_index(sketches):
    """Test that get_constraint_sketch_index can get the constraint indices of
    all constraints in all test files.
    """
    for sketch in sketches:
        for index, constraint in enumerate(sketch.Constraints):
            found_index = api_utils.get_constraint_sketch_index(constraint, sketch)
            assert found_index == index

def test_get_by_uid(freecad_doc, uid_pairs):
    """Test that all api objects can be retrieved using the pancad generated uid
    using get_by_uid.
    """
    for uid, obj in uid_pairs:
        found_obj = api_utils.get_by_uid(uid, freecad_doc)
        assert found_obj.Content == obj.Content

# Testing FreeCADUID

@pytest.fixture(
    name="uid_str",
    params=[
        ["7c2a603d-b250-44ce-8938-f714395e519f", "feature", 2674],
        ["7c2a603d-b250-44ce-8938-f714395e519f", "sketchgeo", 2674, 0, 10],
    ]
)
def fixture_uid_str(request):
    """Representative uid strings of FreeCAD elements to test that FreeCAD UID
    recognizes them and can get data from them.
    """
    yield xml_utils.FreeCADUID.delim.join(map(str, request.param))

@pytest.fixture(name="freecad_uid")
def fixture_freecad_uid(uid_str):
    """The processed FreeCADUID from the uid_str fixture."""
    yield xml_utils.FreeCADUID(uid_str)

def test_file_uid(freecad_uid):
    """Test that the file_uid can be read from FreeCADUID."""
    assert freecad_uid.file_uid == freecad_uid.split(xml_utils.FreeCADUID.delim)[0]

def test_type_(freecad_uid):
    """Test that FreeCADUID type can be read from FreeCADUID."""
    assert freecad_uid.type_ == freecad_uid.split(xml_utils.FreeCADUID.delim)[1]

def test_data(freecad_uid):
    """Test that the data in the uid string was read correctly by FreeCADUID."""
    all_data = freecad_uid.split(freecad_uid.delim)
    int_data = tuple(map(int, all_data[2:]))
    data = tuple(all_data[:2]) + int_data
    assert astuple(freecad_uid.data) == data


# Testing FreeCADUID from FreeCAD API objects

def test_from_feature(freecad_doc):
    """Test that a FreeCADUID can be read from an api feature object."""
    for obj in freecad_doc.Objects:
        uid = api_utils.read_feature_uid(obj, freecad_doc)
        assert uid.data.feature_id == obj.ID

def test_from_sketch_geometry(freecad_doc, sketches):
    """Test that a FreeCADUID can be read from an api sketch geometry object."""
    uids = []
    for sketch in sketches:
        for geometry in sketch.Geometry:
            uid = api_utils.read_geometry_uid(
                geometry, "Geometry", sketch, freecad_doc
            )
            found_id = api_utils.get_geometry_sketch_id(geometry, "Geometry",
                                                        sketch)
            assert uid.data.geometry_id == found_id
    if len(uids) != len(set(uids)):
        raise ValueError("Duplicate uids were created!", uids)

def test_from_sketch_constraint(freecad_doc, sketches):
    """Test that a FreeCADUID can be read from an api sketch constraint object."""
    uids = []
    for sketch in sketches:
        for constraint in sketch.Constraints:
            uid = api_utils.read_constraint_uid(constraint, sketch, freecad_doc)
            uids.append(uid)
    if len(uids) != len(set(uids)):
        raise ValueError("Duplicate uids were created!", uids)
