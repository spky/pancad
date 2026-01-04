"""Module for testing specifically the way that SketchGeometrySystems are 
initialized and handle errors.
"""
from __future__ import annotations

import pytest
from typing import TYPE_CHECKING

from pancad.geometry import Point, AbstractGeometry, LineSegment
from pancad.geometry.sketch import (
    SketchGeometrySystem,
    GeometryList,
    ConstraintList,
    SketchDupeUidError,
    SketchMissingDependencyError,
    SketchGeometryHasConstraintsError,
)
from pancad.geometry.constants import ConstraintReference as CR
from pancad.geometry.constraints import Horizontal, Coincident

if TYPE_CHECKING:
    from pancad.geometry.constraints import AbstractConstraint

@pytest.fixture
def empty_system() -> SketchGeometrySystem:
    yield SketchGeometrySystem()

@pytest.fixture(params=[Point(0, 0)])
def single_geometry(request) -> AbstractGeometry:
    yield request.param

@pytest.fixture
def empty_geometry_list(empty_system) -> GeometryList:
    yield empty_system.geometry

@pytest.fixture
def empty_constraint_list(empty_system) -> GeometryList:
    yield empty_system.constraints

@pytest.fixture(
    params=[
        (Point(0, 0), Point(1, 1), Point(2, 2)),
    ]
)
def multiple_geometry_list(empty_geometry_list, request) -> GeometryList:
    empty_geometry_list.extend(request.param)
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
def system_with_constraints(empty_system,
                            geometry_and_constraint_sequences
                            ) -> SketchGeometrySystem:
    """Systems where all geometry in the list has at least one constraint on it.
    """
    geometry, constraints = geometry_and_constraint_sequences
    empty_system.geometry.extend(geometry)
    empty_system.constraints.extend(constraints)
    yield empty_system

# Testing GeometryList
def test_system_coordinate_system_in_check(empty_system):
    assert empty_system in empty_system.geometry

def test_append_geometry(empty_geometry_list, single_geometry):
    empty_geometry_list.append(single_geometry)
    assert empty_geometry_list[0] is single_geometry

def test_duped_geometry_list(empty_geometry_list, single_geometry):
    empty_geometry_list.append(single_geometry)
    with pytest.raises(SketchDupeUidError):
        empty_geometry_list.append(single_geometry)

def test_delete_geometry_in_empty(empty_geometry_list, single_geometry):
    empty_geometry_list.append(single_geometry)
    del empty_geometry_list[0]
    assert len(empty_geometry_list) == 0

def test_geometry_list_index(multiple_geometry_list):
    for i in range(len(multiple_geometry_list)):
        geometry = multiple_geometry_list[i]
        assert multiple_geometry_list.index(geometry) == i

def test_delete_geometry_with_constraints(system_with_constraints):
    with pytest.raises(SketchGeometryHasConstraintsError):
        del system_with_constraints.geometry[0]

# Testing ConstraintList
def test_add_constraint_without_dependencies(empty_constraint_list,
                                             geometry_and_constraint_sequences):
    _, constraints = geometry_and_constraint_sequences
    with pytest.raises(SketchMissingDependencyError):
        empty_constraint_list.append(constraints[0])

def test_add_duped_constraint(geometry_and_constraint_sequences,
                              system_with_constraints):
    _, constraints = geometry_and_constraint_sequences
    with pytest.raises(SketchDupeUidError):
        system_with_constraints.constraints.append(constraints[0])