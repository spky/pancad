import pytest

from pancad.geometry import LineSegment
from pancad.geometry.constants import ConstraintReference
from pancad.geometry.constraints import constraint_args

LINE_1 = LineSegment((0, 0), (1, 1))
REF_1 = ConstraintReference.START
LINE_2 = LineSegment((0, 1), (1, 0))
REF_2 = ConstraintReference.END
LINE_3 = LineSegment((2, 1), (1, 2))
REF_3 = ConstraintReference.CORE

@pytest.mark.parametrize(
    "pairs,expected",
    [
        # 1 Geometry
        ([(LINE_1, REF_1)], [(LINE_1, REF_1)]),
        ([LINE_1, REF_1], [(LINE_1, REF_1)]),
        # 2 Geometries
        (
            [(LINE_1, REF_1), (LINE_2, REF_2)],
            [(LINE_1, REF_1), (LINE_2, REF_2)]
        ),
        (
            [LINE_1, REF_1, LINE_2, REF_2],
            [(LINE_1, REF_1), (LINE_2, REF_2)]
        ),
        (
            [(LINE_1, REF_1), LINE_2, REF_2],
            [(LINE_1, REF_1), (LINE_2, REF_2)]
        ),
        # 3 Geometries
        (
            [(LINE_1, REF_1), (LINE_2, REF_2), (LINE_3, REF_3)],
            [(LINE_1, REF_1), (LINE_2, REF_2), (LINE_3, REF_3)]
        ),
        (
            [LINE_1, REF_1, LINE_2, REF_2, LINE_3, REF_3],
            [(LINE_1, REF_1), (LINE_2, REF_2), (LINE_3, REF_3)]
        ),
        (
            [(LINE_1, REF_1), LINE_2, REF_2, LINE_3, REF_3],
            [(LINE_1, REF_1), (LINE_2, REF_2), (LINE_3, REF_3)]
        ),
    ]
)
def test_nominal_geometries(pairs, expected):
    assert constraint_args(*pairs) == expected

def test_uneven_number_of_pairs():
    with pytest.raises(ValueError):
        constraint_args(LINE_1, REF_1, LINE_2)

def test_geometry_type_error():
    with pytest.raises(TypeError) as excinfo:
        constraint_args(REF_1, REF_2)
    assert "Geometry" in str(excinfo.value)

def test_reference_type_error():
    with pytest.raises(TypeError) as excinfo:
        constraint_args(LINE_1, LINE_2)
    assert "ConstraintReference" in str(excinfo.value)