"""Module for testing specifically the way that SketchGeometrySystems are 
initialized and handle errors.
"""
from __future__ import annotations

import pytest
from typing import TYPE_CHECKING

from pancad.geometry import Point, AbstractGeometry, LineSegment
from pancad.geometry.sketch import SketchGeometrySystem
from pancad.exceptions import (DupeUidError,
                               HasDependentsError,
                               MissingCADDependencyError)
from pancad.geometry.unique_lists import GeometryList, ConstraintList
from pancad.geometry.constraints import Horizontal, Coincident

if TYPE_CHECKING:
    from pancad.geometry.constraints import AbstractConstraint

# Setting up Fixtures
@pytest.fixture
def empty_system() -> SketchGeometrySystem:
    yield SketchGeometrySystem()

@pytest.fixture
def single_point() -> Point:
    yield Point(0, 0)

@pytest.fixture
def empty_geometry_list(empty_system) -> GeometryList:
    yield empty_system.geometry

@pytest.fixture
def empty_constraint_list(empty_system) -> GeometryList:
    yield empty_system.constraints

@pytest.fixture
def list_of_points() -> list[Point]:
    yield [Point(0, 0), Point(1, 1), Point(2, 2)]

@pytest.fixture(params=["list_of_points"])
def multiple_geometry_list(empty_geometry_list, request) -> GeometryList:
    empty_geometry_list.extend(request.getfixturevalue(request.param))
    yield empty_geometry_list

@pytest.fixture
def horizontal_line_segment() -> tuple[list[LineSegment], list[Horizontal]]:
    line = LineSegment((0, 0), (1, 0))
    yield [line], [Horizontal(line)]

@pytest.fixture
def line_segment_coincident_with_origin(empty_system) -> tuple[list[LineSegment],
                                                               list[Coincident]]:
    line = LineSegment((0, 0), (1, 0))
    yield [line], [Coincident(line, empty_system.origin)]

@pytest.fixture(
    params = [
        "horizontal_line_segment", "line_segment_coincident_with_origin",
    ]
)
def geometry_and_constraint_sequences(request
                                      ) -> tuple[list[AbstractGeometry],
                                                 list[AbstractConstraint]]:
    value = request.getfixturevalue(request.param)
    yield value

@pytest.fixture
def system_just_geometry(empty_system,
                         geometry_and_constraint_sequences
                         ) -> SketchGeometrySystem:
    geometry, _ = geometry_and_constraint_sequences
    empty_system.geometry.extend(geometry)
    yield empty_system

@pytest.fixture
def system_with_constraints(system_just_geometry,
                            geometry_and_constraint_sequences
                            ) -> SketchGeometrySystem:
    """Systems where all geometry in the list has at least one constraint on it.
    """
    _, constraints = geometry_and_constraint_sequences
    system_just_geometry.constraints.extend(constraints)
    yield system_just_geometry

# Testing GeometryList
def test_system_coordinate_system_in_check(empty_system):
    assert empty_system in empty_system.geometry

def test_append_geometry(empty_geometry_list, single_point):
    empty_geometry_list.append(single_point)
    assert empty_geometry_list[0] is single_point

def test_duped_geometry_list(empty_geometry_list, single_point):
    empty_geometry_list.append(single_point)
    with pytest.raises(DupeUidError):
        empty_geometry_list.append(single_point)

def test_delete_geometry_in_empty(empty_geometry_list, single_point):
    empty_geometry_list.append(single_point)
    del empty_geometry_list[0]
    assert len(empty_geometry_list) == 0

def test_geometry_list_index(multiple_geometry_list):
    for i in range(len(multiple_geometry_list)):
        geometry = multiple_geometry_list[i]
        assert multiple_geometry_list.index(geometry) == i

def test_assign_system(system_just_geometry):
    for geometry in system_just_geometry.geometry:
        assert geometry.system is system_just_geometry

def test_delete_geometry_system(system_just_geometry):
    geometry = system_just_geometry.geometry[0]
    del system_just_geometry.geometry[0]
    assert geometry.system is None

def test_delete_geometry_with_constraints(system_with_constraints):
    with pytest.raises(HasDependentsError):
        del system_with_constraints.geometry[0]


# Testing ConstraintList
def test_add_constraint_without_dependencies(empty_constraint_list,
                                             geometry_and_constraint_sequences):
    _, constraints = geometry_and_constraint_sequences
    with pytest.raises(MissingCADDependencyError):
        empty_constraint_list.append(constraints[0])

def test_add_duped_constraint(geometry_and_constraint_sequences,
                              system_with_constraints):
    _, constraints = geometry_and_constraint_sequences
    with pytest.raises(DupeUidError):
        system_with_constraints.constraints.append(constraints[0])