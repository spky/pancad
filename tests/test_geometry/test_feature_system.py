"""Module for testing the ways that FeatureSystems and their lists are 
initialized and handle errors.
"""
from __future__ import annotations

import pytest

from pancad.geometry.feature_container import FeatureContainer
from pancad.geometry.extrude import Extrude
from pancad.geometry.system import FeatureSystem
from tests.sample_pancad_objects import sample_sketches

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
    init_system.features.extend([iso_sketch, iso_extrude])
    print(init_system)
    print([(feature, feature.get_dependencies()) for feature in init_system.features])
