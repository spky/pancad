"""A module containing the definition of pancad's quaternion implementation."""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, SupportsFloat, overload

import numpy as np

from pancad.utils import trigonometry as trig

if TYPE_CHECKING:
    from collections.abc import Iterable, Collection
    from typing import Literal, Self

    import numpy.typing as npt

    from pancad.utils.pancad_types import Numpy1D, Space3DVector

    ListSlice = slice[int | None, int | None, int | None]

class Quat(Sequence[float]):
    """A class representing a quaternion using the scalar-first convention.

    :param coefficients: The scalar quaternion value followed by the i, j, and k vector parts.
    :raises ValueError: When not provided exactly 4 floats in a iterable or as separate args.
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
        self._coefficients = reals

    @classmethod
    def from_angle(cls, angle: float, axis: Iterable[float]) -> Self:
        """Creates a Quat from an angle and a rotation axis.

        :param angle: The angle to rotate about the axis. Must be in radians.
        :param axis: A 3D vector for the axis to rotate about.
        """
        axis_vector = [c * math.sin(angle / 2) for c in axis]
        return cls(trig.get_unit_vector([math.cos(angle / 2), *axis_vector]))

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

    @property
    def inverse(self) -> Quat:
        """The quaternion inverse of this Quat."""
        return self.conjugate / np.linalg.norm(self)

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

    def rotate(self, vector: Collection[float]) -> Space3DVector:
        """Returns a 3D vector rotated per the quaternion from a vector. The quaternion is
        normalized internally to perform the rotation.
        """
        vector_quat = Quat(0, *vector)
        product = self * vector_quat * self.conjugate / np.linalg.norm(self) ** 2
        return product.vector

    def __add__(self, other: object) -> Quat:
        if isinstance(other, Quat):
            return Quat(np.array(self) + np.array(other))
        return NotImplemented

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

    def __invert__(self) -> Quat:
        return self.inverse

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Quat):
            return hash(self) == hash(other)
        return NotImplemented

    def __mul__(self, other: object) -> Quat:
        if isinstance(other, Quat):
            a, b, c, d = self
            w, x, y, z = other
            return Quat(a*w - b*x - c*y - d*z,
                        a*x + b*w + c*z - d*y,
                        a*y - b*z + c*w + d*x,
                        a*z + b*y - c*x + d*w)
        if isinstance(other, (int, float)):
            return Quat([other * coefficient for coefficient in self])
        return NotImplemented

    def __neg__(self) -> Quat:
        return Quat(-np.array(self))

    def __sub__(self, other: object) -> Quat:
        if isinstance(other, Quat):
            return Quat(np.array(self) - np.array(other))
        return NotImplemented

    def __truediv__(self, other: object) -> Quat:
        if isinstance(other, (int, float)):
            return Quat([coefficient / other for coefficient in self])
        return NotImplemented

    def __repr__(self) -> str:
        return f"[{self.scalar}, {self.x}i, {self.y}j, {self.z}k]"
