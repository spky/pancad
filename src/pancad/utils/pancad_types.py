"""A module providing common types for use throughout pancad."""

import dataclasses
from collections import namedtuple
from collections.abc import Sequence
from typing import Union

import numpy as np

VectorLike = Union[Sequence, np.ndarray]
Space2DVector = tuple[float, float]
Space3DVector = tuple[float, float, float]
SpaceVector = Space2DVector | Space3DVector

@dataclasses.dataclass(frozen=True, eq=True)
class PolarVector:
    """Class for tracking polar vector components."""
    r: float
    phi: float

    def __getitem__(self, item: int) -> float:
        match item:
            case 0:
                return self.r
            case 1:
                return self.phi
        raise IndexError("vector index out of range")

    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        array = np.array([self.r, self.phi])
        if copy is not None and not copy:
            raise ValueError("PolarVector cannot return the original")
        if dtype:
            return array.astype(dtype)
        return array

@dataclasses.dataclass(frozen=True, eq=True)
class SphericalVector:
    """Class for tracking spherical vector components."""
    r: float
    phi: float
    theta: float

    def __getitem__(self, item: int) -> float:
        match item:
            case 0:
                return self.r
            case 1:
                return self.phi
            case 2:
                return self.theta
        raise IndexError("vector index out of range")

    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        array = np.array([self.r, self.phi, self.theta])
        if copy is not None and not copy:
            raise ValueError("SphericalVector cannot return the original")
        if dtype:
            return array.astype(dtype)
        return array

FitBox2D = namedtuple("FitBox2D", ["min_", "max_"])
