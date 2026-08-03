"""A module containing the definition of pancad's quaternion implementation."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, SupportsFloat, overload

if TYPE_CHECKING:
    ListSlice = slice[int | None, int | None, int | None]

class Quat(Sequence[float]):
    """A class representing a quaternion.

    :param coefficients: The scalar quaternion value followed by the i, j, and k vector parts.
    """

    def __init__(self, *coefficients: float | Iterable[float]) -> None:
        self._coefficients: tuple[float, float, float, float]
        reals: tuple[float, ...]
        if len(coefficients) == 1 and isinstance(coefficients[0], Iterable):
            reals = tuple(coefficients[0])
        elif len(coefficients) == 4:
            reals = tuple(float(c) for c in coefficients if isinstance(c, SupportsFloat))
        else:
            raise ValueError(f"Expected 4 floats or 1 iterable, got: {coefficients}")
        if len(reals) != 4:
            raise ValueError(f"Expected exactly 4 floats, got: {reals}")
        self._coefficients = reals

    @property
    def w(self) -> float:
        """The scalar part of the quaternion."""
        return self._coefficients[0]

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
    def __getitem__(self, index: ListSlice) -> list[float]: ...
    def __getitem__(self, index: int | ListSlice) -> float | list[float]:
        return self._coefficients[index]

    def __len__(self) -> int:
        return 4 # Quat is always 4 long.
