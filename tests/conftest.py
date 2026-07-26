"""Module defining pytest fixture configuration"""
from __future__ import annotations

import math
import os
from functools import cache
from typing import TYPE_CHECKING
import tomllib
from pathlib import Path

import pytest

from pancad.constants import ConstraintReference as CR, SketchConstraint as SC
from pancad.constraints._generator import make_constraint
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.system import TwoDSketchSystem
from pancad.geometry.sketch import Pose, Sketch
from pancad.filetypes.part_file import PartFile
from pancad.constraints.state_constraint import AlignAxes
from pancad.constants import FeatureType as FT
from pancad.geometry.extrude import Extrude, ExtrudeSettings
from pancad.utils import trigonometry as trig

from tests.testing_utils import sketch_gen

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Optional, TypedDict

    from pancad.utils.pancad_types import SpaceVector
    from tests._typing import GeometrySampleData, SampleTestGroup, ChangeTestGroup

@cache
def read_test_data_file(path: Path) -> dict[str, Any]:
    """Returns the data from the test's toml file."""
    with open(path, "rb") as file:
        return tomllib.load(file)

@cache
def resolve_test_data_path(fixture_name: str) -> Path:
    """Returns the fixture's associated test data file path.

    :raises FileNotFoundError: When the file for the fixture name could not be found.
    """
    try:
        path = next(v for k, v in _map_data_paths().items() if fixture_name.startswith(k))
    except StopIteration as exc:
        raise FileNotFoundError(fixture_name) from exc
    return path

@cache
def _map_data_paths() -> dict[str, Path]:
    # Returns a mapping of the toml filename with no extension to the path of the datafile.
    paths: dict[str, Path] = {}
    for dirpath, _, filenames in os.walk(Path(__file__).parent):
        dirpath_path = Path(dirpath)
        for name in filenames:
            path = dirpath_path / name
            if path.suffix == ".toml":
                paths[path.stem] = path
    return paths

def read_vector(raw_vector: Any,
                normalize: bool=False,
                polar_spherical: bool=False) -> SpaceVector:
    """Returns a 2 or 3 float long vector from an unknown datatype, usually read from a toml file.

    :param raw_vector: An object that should be a vector.
    :param normalize: Whether to normalize the vector before returning it.
    :param polar_spherical: Whether the 2nd and 3rd (if present) components should be converted to
        radians.

    :raises ValueError: When the vector components could not be converted into floats.
    :raises AssertionError: When the vector's length is not 2 or 3.
    """
    vector = tuple(map(float, raw_vector))
    assert len(vector) == 2 or len(vector) == 3
    if polar_spherical:
        if len(vector) == 2: # Polar
            vector = (vector[0], math.radians(vector[1]))
        else: # Spherical
            vector = (vector[0], math.radians(vector[1]), math.radians(vector[2]))
    elif normalize:
        vector = trig.to_1d_tuple(trig.get_unit_vector(vector))
    return vector

def resolve_test_data_keys(fixture_name: str, data: dict[str, Any]) -> list[str]:
    """Returns a list of keys found in the fixture's name that match keys in the data.
    Progressively searches down the data's nested dictionary for keys that match the start of the
    fixture name with the previous names removed. Underscores preceding keys are ignored.

    :raises LookupError: When a key cannot be found.
    :raises RuntimeError: When the string loop fails to reduce the length of the key string.
    """
    key_str = fixture_name.removeprefix(resolve_test_data_path(fixture_name).stem).lstrip("_")
    keys: list[str] = []
    while key_str:
        check_str = key_str
        try:
            key, data = next((k, v) for k, v in data.items() if key_str.startswith(k))
        except StopIteration as exc:
            raise LookupError("Could not find a key with the same start as"
                              f"{key_str} in {data.keys()}") from exc
        keys.append(key)
        key_str = key_str.removeprefix(key).lstrip("_")
        if check_str == key_str:
            raise RuntimeError("Loop stuck, check/key strings match even after prefix removed."
                               f" key string: {key_str}")
    return keys

def _read_geometry_data_entry(entry: dict[str, Any]) -> GeometrySampleData:
    # Reads a geometry entry from a data file and converts its vectors/scalars from Any to floats
    # unit vectors, and radians as specified in the file.
    vectors = {k: read_vector(v) for k, v in entry.get("vectors", {}).items()}
    vectors.update(
        # Normalize to a unit vector and add any normed_vectors
        {k: read_vector(v, True) for k, v in entry.get("normed_vectors", {}).items()}
    )
    vectors.update( # Convert polar_spherical_vectors degrees inputs to radians
        {k: read_vector(v, polar_spherical=True)
         for k, v in entry.get("polar_spherical_vectors", {}).items()}
    )
    scalars = {k: float(v) for k, v in entry.get("scalars", {}).items()}
    scalars.update( # Covert degree scalars to radians
        {k: math.radians(v) for k, v in entry.get("degree_scalars", {}).items()}
    )
    if vectors or scalars:
        return {"vectors": vectors, "scalars": scalars}
    raise LookupError("No vectors or scalars found")

def read_geometry_data(data: dict[str, Any],
                        *keys: str) -> dict[tuple[str, ...], GeometrySampleData]:
    """Reads a nested dictionary of geometry into a dictionary of the nested keys mapped to the
    geometry data.

    :raises LookupError: When one of the provided keys could not be found in the data or if no
        vectors or scalars are found in one of the data entries.
    """
    for key in keys:
        try:
            data = data[key]
        except KeyError as exc:
            raise LookupError(f"Could not find '{key}' in chain '{'.'.join(keys)}'") from exc
    keyed_data = {keys + (k,): v for k, v in data.items()}
    while True:
        try:
            return {k: _read_geometry_data_entry(v) for k, v in keyed_data.items()}
        except LookupError:
            keyed_data ={k + (sk,): sv for k, v in keyed_data.items() for sk, sv in v.items()}

def _make_geometry_sample_input(fixture_name: str) -> SampleTestGroup:
    """Converts the raw data read from a fixture's sample data file into a list of test ids and a
    list of GeometrySampleData dictionaries.
    """
    raw_data = read_test_data_file(resolve_test_data_path(fixture_name))
    keys = resolve_test_data_keys(fixture_name, raw_data)
    data = read_geometry_data(raw_data, *keys)
    return [".".join(id_) for id_ in data], list(data.values())

def _make_geometry_change_input(fixture_name: str) -> ChangeTestGroup:
    """Converts the raw data read from a fixture's sample data file into a list of test ids and a
    list of GeometrySampleData dictionary pairs. The first of the pair is the starting geometry
    and the second specifies the change to perform on the starting geometry.
    """
    raw_data = read_test_data_file(resolve_test_data_path(fixture_name))
    keys = resolve_test_data_keys(fixture_name, raw_data)
    data = read_geometry_data(raw_data, *keys)
    ids: list[str] = []
    tests: list[tuple[GeometrySampleData, GeometrySampleData]] = []

    for initial_key, initial_geometry in [(k, v) for k, v in data.items() if k[-1] == "initial"]:
        # Match up initial geometry with any geometry that starts with the same set of keys.
        group_ids: list[str] = []
        group_tests: list[tuple[GeometrySampleData, GeometrySampleData]] = []
        for id_, change_geometry in data.items():
            if initial_key[:-1] == id_[:-1] and initial_key != id_:
                group_ids.append(".".join(id_))
                group_tests.append((initial_geometry, change_geometry))
        if not group_ids:
            raise ValueError(f"No changes found for initial geometry: {initial_key}")
        ids.extend(group_ids)
        tests.extend(group_tests)
    return ids, tests

def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generates tests from the names of the fixtures when the match patterns like data_ and
    changes_
    """
    for data_fixture in [f for f in metafunc.fixturenames if f.startswith("data_")]:
        ids, sample_data = _make_geometry_sample_input(data_fixture)
        metafunc.parametrize(data_fixture, sample_data, ids=ids)

    for change_fixture in [f for f in metafunc.fixturenames if f.startswith("changes_")]:
        ids, change_data = _make_geometry_change_input(change_fixture)
        metafunc.parametrize(change_fixture, change_data, ids=ids)

@pytest.fixture
def unconstrained_square_sketch() -> Sketch:
    """Square sketch with just the lines, no constraints."""
    side = 1
    bottom_left = (0, 0)
    bottom_right = (side, 0)
    top_left = (0, side)
    top_right = (side, side)

    bottom = LineSegment(bottom_left, bottom_right)
    right = LineSegment(bottom_right, top_right)
    top = LineSegment(top_right, top_left)
    left = LineSegment(top_left, bottom_left)
    system = TwoDSketchSystem([bottom, right, top, left])
    pose = Pose.from_yaw_pitch_roll((0, 0, 0), 0, 0, 0)
    return Sketch(system, pose)

@pytest.fixture
def joined_square_sketch(unconstrained_square_sketch) -> Sketch:
    """Square sketch with just the lines. Line end points are coincident."""
    sketch = unconstrained_square_sketch
    bottom, right, top, left = sketch.geometry_system.geometry
    sketch.geometry_system.constraints.extend(
        [
            make_constraint(SC.COINCIDENT, bottom.start, left.end),
            make_constraint(SC.COINCIDENT, bottom.end, right.start),
            make_constraint(SC.COINCIDENT, right.end, top.start),
            make_constraint(SC.COINCIDENT, top.end, left.start),
        ]
    )
    return sketch

@pytest.fixture
def square_sketch_bottom_length(joined_square_sketch) -> Sketch:
    """Square sketch with the bottom line length constrained."""
    sketch = joined_square_sketch
    unit = "mm"
    bottom, *_ = sketch.geometry_system.geometry
    side_length = bottom.end.x - bottom.start.x
    distance = make_constraint(SC.DISTANCE, bottom.start, bottom.end,
                               value=side_length, unit=unit)
    sketch.geometry_system.constraints.append(distance)
    return sketch

CSYS = -1
BOTTOM = 0
RIGHT = 1
TOP = 2
LEFT = 3

CONSTRAINT_PARAMS = [
    (
        # Bottom/Right Equal, Bottom/Top Horiz, Left/Right Vert, Bottom Start
        # *point* coincident to origin.
        (SC.HORIZONTAL, ((BOTTOM, CR.CORE),)),
        (SC.VERTICAL, ((RIGHT, CR.CORE),)),
        (SC.HORIZONTAL, ((TOP, CR.CORE),)),
        (SC.VERTICAL, ((LEFT, CR.CORE),)),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (RIGHT, CR.CORE))),
        (SC.COINCIDENT, ((BOTTOM, CR.START), (CSYS, CR.ORIGIN))),
    ),
    (
        # All Equal, Bottom Horizontal, Bottom/Left Perpendicular, Bottom Start
        # *point* coincident to origin.
        (SC.HORIZONTAL, ((BOTTOM, CR.CORE),)),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (RIGHT, CR.CORE))),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (TOP, CR.CORE))),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (LEFT, CR.CORE))),
        (SC.PERPENDICULAR, ((BOTTOM, CR.CORE), (LEFT, CR.CORE))),
        (SC.COINCIDENT, ((BOTTOM, CR.START), (CSYS, CR.ORIGIN))),
    ),
    (
        # Bottom Horizontal, Bottom/Left Perpendicular, R/L parallel, B/T
        # parallel, Bottom Start *point* coincident to origin.
        (SC.HORIZONTAL, ((BOTTOM, CR.CORE),)),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (RIGHT, CR.CORE))),
        (SC.PERPENDICULAR, ((BOTTOM, CR.CORE), (LEFT, CR.CORE))),
        (SC.PARALLEL, ((RIGHT, CR.CORE), (LEFT, CR.CORE))),
        (SC.PARALLEL, ((BOTTOM, CR.CORE), (TOP, CR.CORE))),
        (SC.COINCIDENT, ((BOTTOM, CR.START), (CSYS, CR.ORIGIN))),
    ),
    (
        # Bottom/Right Equal, Bottom/Top Horiz, Left/Right Vert, Bottom Left
        # *lines* coincident to origin.
        (SC.HORIZONTAL, ((BOTTOM, CR.CORE),)),
        (SC.VERTICAL, ((RIGHT, CR.CORE),)),
        (SC.HORIZONTAL, ((TOP, CR.CORE),)),
        (SC.VERTICAL, ((LEFT, CR.CORE),)),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (RIGHT, CR.CORE))),
        (SC.COINCIDENT, ((BOTTOM, CR.CORE), (CSYS, CR.ORIGIN))),
        (SC.COINCIDENT, ((LEFT, CR.CORE), (CSYS, CR.ORIGIN))),
    ),
    (
        # All Sides equal, bottom horizontal, left vertical, bottom left
        # coincident to origin
        (SC.HORIZONTAL, ((BOTTOM, CR.CORE),)),
        (SC.VERTICAL, ((LEFT, CR.CORE),)),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (RIGHT, CR.CORE))),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (TOP, CR.CORE))),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (LEFT, CR.CORE))),
        (SC.COINCIDENT, ((BOTTOM, CR.START), (CSYS, CR.ORIGIN))),
    ),

]
@pytest.fixture(params=CONSTRAINT_PARAMS)
def square_sketch_variations(request, square_sketch_bottom_length):
    """Variations on a fully constrained square sketch. Same geometry, varied
    constraints.
    """
    sketch = square_sketch_bottom_length
    constraints = []
    for type_, refs in request.param:
        input_geometry = []
        for index, constraint_ref in refs:
            geo = sketch.geometry_system.geometry[index]
            input_geometry.append(geo.get_reference(constraint_ref))
        constraints.append(make_constraint(type_, *input_geometry))
    sketch.geometry_system.constraints.extend(constraints)
    yield sketch

@pytest.fixture
def line_angled_to_x_axis_sketches(request) -> list[Sketch]:
    """A list of angle-sweeping sketches placing a single line segment in
    different quadrants relative to the sketch's x-axis. Useful for checking the
    implementation of angle constraints inside a single CAD file.
    """
    angle_sweep_params = [
        # Quadrant, Angle (Degrees), start_to_end
        (1, 45, False),
        (2, 45, False),
        (3, 45, False),
        (4, 45, False),
        (1, 45, True),
        (2, 45, True),
        (3, 45, True),
        (4, 45, True),
    ]
    sketches = []
    for quadrant, angle, start_radially_out in angle_sweep_params:
        sketch = sketch_gen.sketch_with_line_angled_to_x_axis(quadrant, angle, start_radially_out)
        sketch.name = f"Quadrant_{quadrant}_Angle_{angle}"
        if start_radially_out:
            sketch.name = sketch.name + "_EndOnOrigin"
        else:
            sketch.name = sketch.name + "_StartOnOrigin"
        sketches.append(sketch)
    return sketches


@pytest.fixture
def empty_part_file() -> PartFile:
    """A partfile with nothing in it."""
    return PartFile("EmptyTestPart")

@pytest.fixture
def square_sketch_part_file() -> PartFile:
    """A partfile with just a square sketch inside it"""
    part = PartFile("SquareSketchPartTest")
    sketch = sketch_gen.square()
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
    sketch = sketch_gen.square()
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
    sketch = sketch_gen.circle()
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
    sketch = sketch_gen.rounded_square()
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
    sketch = sketch_gen.ellipse()
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
def square_variations_part_file(square_sketch_variations) -> PartFile:
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

@pytest.fixture
def angle_dimension_sweep_part_file(line_angled_to_x_axis_sketches) -> PartFile:
    part = PartFile("angle_dimension_sweep")
    for sketch in line_angled_to_x_axis_sketches:
        part.container.feature_system.features.append(sketch)
        part.container.feature_system.constraints.append(
            AlignAxes(part.container.feature_system.coordinate_system,
                      sketch.pose.coordinate_system)
        )
    return part
