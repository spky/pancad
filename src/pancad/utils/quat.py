"""A module containing the definition of pancad's quaternion implementation."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, SupportsFloat, overload

import numpy as np
if TYPE_CHECKING:
    from typing import Literal

    import numpy.typing as npt

    from pancad.utils.pancad_types import Numpy1D, Space3DVector

    ListSlice = slice[int | None, int | None, int | None]

class Quat(Sequence[float]):
    """A class representing a quaternion.

    :param coefficients: The scalar quaternion value followed by the i, j, and k vector parts.
    """

    def __init__(self, *coefficients: float | Iterable[float]) -> None:
        reals: tuple[float, ...]
        if len(coefficients) == 1 and isinstance(coefficients[0], Iterable):
            reals = tuple(coefficients[0])
        elif len(coefficients) == 4:
            reals = tuple(float(c) for c in coefficients if isinstance(c, SupportsFloat))
        else:
            raise ValueError(f"Expected 4 floats or 1 iterable, got: {coefficients}")
        if len(reals) != 4:
            raise ValueError(f"Expected exactly 4 floats, got: {reals}")
        self._coefficients: tuple[float, float, float, float] = reals

    @property
    def scalar(self) -> float:
        """The scalar part of the quaternion."""
        return self._coefficients[0]

    @property
    def vector(self) -> Space3DVector:
        """The vector part of the quaternion"""
        return self._coefficients[1:]

    @property
    def conjugate(self) -> Quat:
        """The quaternion conjugate of this Quat."""
        return Quat(self.scalar, *[-c for c in self.vector])

    w = scalar # w is a common alias for scalar

    @property
    def x(self) -> float:
        """The coefficient of the i vector component."""
        return self._coefficients[1]

    @property
    def y(self) -> float:
        """The coefficient of the j vector component."""
        return self._coefficients[2]

    @property
    def z(self) -> float:
        """The coefficient of the k vector component."""
        return self._coefficients[3]

    @overload
    def __getitem__(self, index: int) -> float: ...
    @overload
    def __getitem__(self, index: ListSlice) -> tuple[float, ...]: ...
    def __getitem__(self, index: int | ListSlice) -> float | tuple[float, ...]:
        return self._coefficients[index]

    def __len__(self) -> int:
        return 4 # Quat is always 4 long.

    def __array__(self, dtype: npt.DTypeLike | None=None, copy: bool=True) -> Numpy1D:
        if not copy:
            raise ValueError("Quat cannot return the original array.")
        return np.array(self._coefficients, dtype=dtype)

    def __hash__(self) -> int:
        return hash(self._coefficients)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Quat):
            return hash(self) == hash(other)
        return NotImplemented

    def __repr__(self) -> str:
        return f"[{self.scalar}, {self.x}i, {self.y}j, {self.z}k]"
