"""Tests for pancad's system constraint solving residual systems."""
from __future__ import annotations

from pprint import pp
from typing import TYPE_CHECKING, Type

import pytest

from pancad.abstract import AbstractGeometry, PancadThing
from pancad.constraints.state_constraint import Coincident, Parallel, Antiparallel, Codirectional
from pancad.constraints.snapto import Fixed
from pancad.api import Axis, Line, Point, Plane, Sketch

from pancad.utils.solver_schemas import SCHEMAS
from pancad.utils.solver_residuals import (
    geo_product,
    CalculationSchema,
    GuessVector,
    CalcInput,
    ResidualFactory,
    SystemSolution,
    GeometryComboMap,
)
from pancad.utils.residual_calculations import (
    CoincidentLinePoint2D,
    EqualScalars,
    EqualVectors2D,
)

from tests.testing_utils.data_collectors import make_feature_sample_input
from tests.testing_utils.thing_factory import make_feature

if TYPE_CHECKING:
    from collections.abc import Mapping, Iterable

    # pytest-regressions doesn't have an type implementation for data_regression
    from pytest_regressions.data_regression import DataRegressionFixture # type: ignore

    from pancad.utils.residual_calculations import ResidualCalculation
    from pancad.utils.solver_schemas import GeoComboSpec, ValueMapSpec, MixedThing
    from pancad.utils.solver_residuals import GeometryTerm, ComboDimSpec
    from tests._typing import TestGroup


def _make_residuals(fixture_name: str) -> TestGroup[ResidualCalculation]:
    residuals = [
        ("equal_scalars_unequal", EqualScalars(1, 2)),
        ("2d_equal_vectors_unequal", EqualVectors2D((1, 1), (2, 2))),
        ("line_point_coincident_off", CoincidentLinePoint2D((1, 1), (0, 0), (1, 0))),
    ]
    tests: TestGroup[ResidualCalculation] = ([], [])
    for name, calc in residuals:
        tests[0].append(f"{fixture_name}.{name}")
        tests[1].append(calc)
    return tests

def _solve_sketches(fixture_name: str) -> TestGroup[Sketch]:
    sketches: TestGroup[Sketch] = ([], [])
    for spec_id, spec in zip(*make_feature_sample_input(fixture_name)):
        sketch = make_feature(spec)
        assert isinstance(sketch, Sketch)
        assert sketch.name is not None
        sketches[0].append(".".join((spec_id, sketch.name)))
        sketches[1].append(sketch)
    return sketches

def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generates sample sketch and residual calculation result fixtures for tests in this file."""
    if "sample_sketch" in metafunc.fixturenames:
        ids, sketches = _solve_sketches("feat_geo_sys_sample_solvesketches")
        metafunc.parametrize("sample_sketch", sketches, ids=ids)
    if "res_calc" in metafunc.fixturenames:
        ids, calcs = _make_residuals("res_calc")
        metafunc.parametrize("res_calc", calcs, ids=ids)


def test_res_calc_to_dict(res_calc: ResidualCalculation) -> None:
    """ResidualCalculation must be able to transfer its data to a readable dict."""
    res_calc.to_dict()


@pytest.mark.parametrize(
    "terms, expected",
    [
        ((Point, (Line, Axis)), [(Point, Line), (Point, Axis)]),
        ((Line, Axis), [(Line, Axis),]),
        (((Line, Axis), (Line, Axis)), [(Line, Line), (Line, Axis), (Axis, Line), (Axis, Axis)]),
        (Point, [(Point,)]),
        ((Point,), [(Point,)]),
    ]
)
def test_geo_product(terms: GeometryTerm,
                     expected: list[tuple[Type[AbstractGeometry], ...]]) -> None:
    """geo_product must produce the cartesian product of geometry types and nested tuples of
    geometry types.
    """
    assert set(geo_product(terms)) == set(expected)

class TestGeometryComboMap:
    """Tests for GeometryComboMap creation and usage."""

    @classmethod
    @pytest.fixture(scope="class")
    def spec(cls) -> Mapping[Iterable[Type[PancadThing]],
                             Iterable[Mapping[GeoComboSpec, str | tuple[str, ...]]]]:
        """A geometry combination mapping specification dictionary."""
        return {
            (Coincident,): (
                {Point: ("cartesian",)},
                {Plane: ("normal", "ref")},
                {Point: "cartesian", Plane: ("normal", "ref")},
                {((Line, Axis), (Line, Axis)): ("direction", "ref")},
                {Point: ("cartesian",), (Line, Axis): ("direction", "ref")},
            ),
            (Parallel, Antiparallel, Codirectional): (
                {((Line, Axis), (Line, Axis)): "direction"},
                {Plane: "normal"},
                {(Line, Axis): "direction", Plane: "normal"},
            )
        }

    @classmethod
    @pytest.fixture(scope="class")
    def mapping(cls, spec: Mapping[Iterable[Type[PancadThing]],
                                   Iterable[Mapping[GeoComboSpec, str | tuple[str, ...]]]]
                ) -> GeometryComboMap[str | tuple[str, ...]]:
        """A sample GeometryComboMap to test the functionality of GeometryComboMap with."""
        return GeometryComboMap(spec)

    def test_getitem(self, mapping: GeometryComboMap[str | tuple[str, ...]]) -> None:
        """GeometryComboMap must account for product produced keys and singular keys."""
        # Test that products between keys are accounted for
        assert mapping[Coincident, frozenset({Point, Axis}), Axis] == ("direction", "ref")
        # Test that products in one key are accounted for
        assert mapping[Coincident, frozenset({Line}), Line] == ("direction", "ref")

    def test_iter(self, mapping: GeometryComboMap[tuple[str, str]]) -> None:
        """GeometryComboMap must produce every possible constraint, combo, and value tuple from a
        specification.
        """
        print()
        pp(tuple(
            tuple(
                k.__name__ if isinstance(k, type) else {t.__name__ for t in k} for k in m)
                for m in mapping
            )
        )
        assert len(mapping) == 39

class TestCalculationSchema:
    """Tests for the ability to use CalculationSchemas to solve geometry systems."""

    @classmethod
    @pytest.fixture(scope="class")
    def spec(cls) -> Mapping[Type[ResidualCalculation],
                                     Mapping[MixedThing, Mapping[GeoComboSpec, ValueMapSpec]]]:
        """A CalculationSchema dictionary specification."""
        return SCHEMAS["pancad_default"]

    @classmethod
    @pytest.fixture(scope="class")
    def schema(cls, spec: Mapping[Type[ResidualCalculation],
                                     Mapping[MixedThing, Mapping[GeoComboSpec, ValueMapSpec]]]
                ) -> CalculationSchema:
        """A CalculationSchema schema produced from a specification to test with."""
        return CalculationSchema(spec)

    def test_iter(self, schema: CalculationSchema) -> None:
        """All CalculationSchema mappings must be possible to turn into dictionaries."""
        print("\nValues:")
        pp(dict(schema.values))
        print("Contexts:")
        pp(dict(schema.contexts))
        print("Order:")
        pp(dict(schema.order))
        print("Calcs:")
        pp(dict(schema.calcs))

    def test_values(self, schema: CalculationSchema) -> None:
        """CalculationSchema must be able to return the value names required for a geometry in a
        calculation scenario defined by a cosntraint, geometry combo, and dimension.
        """
        assert schema.values[(Coincident, frozenset([Point, Line]), 2), Point] == ("cartesian",)

    def test_guess_sorting(self,
                           sample_sketch: Sketch,
                           schema: CalculationSchema,
                           data_regression: DataRegressionFixture) -> None:
        """GuessVector must deterministically sort its elements, sources, and initial vector."""
        guess = GuessVector(sample_sketch.geometry_system.constraints, schema)
        keys = [(str(geo), name, dim) for geo, name, dim  in guess]
        sources = {(str(geo), name, dim): i for (geo, name, dim), i in guess.sources.items()}
        data = {"guess": keys, "sources": sources, "initial": guess.initial}
        data_regression.check(data)

    def test_calc_input_sorting(self,
                            sample_sketch: Sketch,
                            schema: CalculationSchema,
                            data_regression: DataRegressionFixture) -> None:
        """CalcInputs must deterministically sort its source inputs."""
        sources = {}
        for constraint in sample_sketch.geometry_system.constraints:
            if isinstance(constraint, Fixed):
                continue
            calc_input = CalcInput(constraint, schema)
            calc_sources = [(str(geo), name, i) for geo, name, i in calc_input]
            sources[constraint.name] = (calc_input.calc.__name__, calc_sources)
        data_regression.check(sources)

    def test_residual_factory(self,
                              sample_sketch: Sketch,
                              schema: CalculationSchema,
                              data_regression: DataRegressionFixture) -> None:
        """ResidualFactory must confirm that its constrained based on its inputs versus results
        and be able to evaluate its initial guess value.
        """
        guess = GuessVector(sample_sketch.geometry_system.constraints, schema)
        factory = ResidualFactory(guess)
        keys = [(str(geo), name, dim) for geo, name, dim  in guess]
        fixed_keys = [(str(geo), name, dim) for geo, name, dim  in guess.fixed_values]
        data = {
            "guess": keys,
            "fixed_sources": fixed_keys,
            "fixed_values": guess.fixed,
            "initial_guess": guess.initial,
            "initial_result": factory(guess.initial),
            "constrained": factory.constrained,
        }
        data_regression.check(data)
        assert factory.constrained # Catch unconstrained in case a new calculation doesn't work.

    def test_solution(self, sample_sketch: Sketch, data_regression:DataRegressionFixture) -> None:
        """SolutionVector solutions must be deterministic."""
        old_geometry = [str(geo) for geo in sample_sketch.geometry_system.geometry]
        sol = SystemSolution(sample_sketch.geometry_system)
        initial_jac = sol.factory.make_jac(sol.factory.guess.initial)
        sol.update()
        new_geometry = [str(geo) for geo in sample_sketch.geometry_system.geometry]
        data = {
            "old_geometry": old_geometry,
            "new_geometry": new_geometry,
            "initial": sol.factory.guess.initial,
            "solution": tuple(sol),
            "initial_jacobian": initial_jac,
        }
        data_regression.check(data)
