"""Module for testing the ways that FeatureSystems and their lists are 
initialized and handle errors.
"""
from __future__ import annotations

import pytest
from pprint import pp

from pancad.constraints.state_constraint import AlignAxes
from pancad.geometry.feature_container import FeatureContainer
from pancad.geometry.extrude import Extrude
from pancad.geometry.system import FeatureSystem
from tests.sample_pancad_objects import sample_sketches
from pancad.exceptions import MissingCADDependencyError


@pytest.fixture(
    params = [
        sample_sketches.square,
        sample_sketches.ellipse,
        sample_sketches.rounded_square
    ]
)
def iso_sketch(request):
    """Executes sample sketches with no parameters. These sketches should not 
    have any external dependencies.
    """
    yield request.param()

@pytest.fixture
def iso_extrude(iso_sketch):
    yield Extrude.from_length(iso_sketch, 1)

@pytest.fixture
def init_container() -> FeatureContainer:
    yield FeatureContainer()

@pytest.fixture
def init_system(init_container) -> FeatureSystem:
    yield init_container.feature_system

def test_add_extrude(init_system, iso_sketch, iso_extrude):
    constraints = [
        AlignAxes(init_system.coordinate_system,
                  iso_sketch.pose.coordinate_system),
    ]
    init_system.features.append(iso_sketch)
    init_system.constraints.extend(constraints)
    init_system.features.append(iso_extrude)
    print("\nDirect Dependents")
    pp({feature: init_system.get_direct_dependents(feature)
        for feature in init_system.features.get_contents()})
    print("\nTopo Dependents")
    pp({feature: init_system.get_dependents(feature)
         for feature in init_system.features.get_contents()})
    print("\nDependencies")
    pp({feature: feature.get_dependencies()
        for feature in init_system.features.get_contents()})

def test_add_constraint_without_sketch(init_system, iso_sketch):
    constraint = AlignAxes(init_system.coordinate_system,
                           iso_sketch.pose.coordinate_system)
    with pytest.raises(MissingCADDependencyError):
        init_system.constraints.append(constraint)

def test_add_extrude_without_sketch(init_system, iso_extrude):
    with pytest.raises(MissingCADDependencyError):
        init_system.features.append(iso_extrude)

def test_add_out_of_order(init_system, iso_sketch, iso_extrude):
    # Tests if adding features out of order (as in, dependencies are later in 
    # the list order than their dependents.) raises an error
    with pytest.raises(MissingCADDependencyError):
        init_system.features.extend([iso_extrude, iso_sketch])
