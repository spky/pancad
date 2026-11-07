"""
residual_calculations.py contains the base ResidualCalculation class and specializations for
the class. ResidualCalculation objects represent a type of equation solver residual/error
calculation that take a series of vector and scalar inputs to return one or more residual
 values.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import math
from typing import TYPE_CHECKING, TypedDict, NamedTuple

if TYPE_CHECKING:
    from typing import Final, Self
    from collections.abc import Sequence

Vector2D = NamedTuple("Vector2D", [("x", float), ("y", float)])

class ResidualCalculation(ABC):
    """A calculation of one or more residual errors and the respective gradient vectors evaluated
    at a sequence of inputs.

    :param inputs: The ordered input values.
    :param names: The ordered input value names.
    :param no_vectors: The number of input vectors at the front of the input vector.
    :param dimension: The dimension the residual is calculated for, e.g., 1, 2, or 3.
    :param scale: The scale factor for the residual.
    """
    dimensions: tuple[int, ...] = ()
    """The dimensions this calculation can support."""

    def __init__(self,
                 inputs: Sequence[float],
                 names: Sequence[str],
                 no_vectors: int,
                 dimension: int,
                 scale: float=1):
        self._inputs: Final[tuple[float, ...]] = tuple(inputs)
        self._names: Final[tuple[str, ...]] = tuple(names)
        self._no_vectors: Final[int] = no_vectors
        self._dimension: Final[int] = dimension
        self._scale: Final[float] = scale

    @classmethod
    @abstractmethod
    def from_floats(cls, inputs: Sequence[float], scale: float=1) -> Self:
        """Creates a new calculation from the raw float values.

        :param inputs: The ordered input values.
        :param scale: The scale factor for the residual.
        :raises ValueError: When the length of inputs is not valid for the residual.
        """

    class ReadableData(TypedDict):
        """A dictionary format allowing residual inputs and outputs to be printed easily."""
        type_: type
        no_vectors: int
        dimension: int
        scale: float
        inputs: dict[str, float | tuple[float, ...]]
        residual: tuple[float, ...]
        gradient: tuple[dict[str, float | tuple[float, ...]], ...]

    @property
    @abstractmethod
    def residual(self) -> tuple[float, ...]:
        """The error of the residual functions current state(s)."""

    @property
    @abstractmethod
    def gradient(self) -> tuple[tuple[float, ...], ...]:
        """The gradient(s) of the residual function(s) in the current state."""

    def _map_names_to_vector(self, v: Sequence[float], /) -> dict[str, float | tuple[float, ...]]:
        # Maps the names of the input vector to the input/gradient vector.
        values = iter(v)
        names = iter(self._names)
        name_to_value: dict[str, float | tuple[float, ...]] = {}
        for _ in range(self._no_vectors):
            # Assumes all vectors are the same dimension.
            name_to_value[next(names)] = tuple(next(values) for __ in range(self._dimension))
        name_to_value.update(dict(zip(names, values, strict=True)))
        return name_to_value

    def to_dict(self) -> ReadableData:
        """Returns the inputs value mapped to their names for debugging."""
        return {
            "type_": type(self),
            "no_vectors": self._no_vectors,
            "dimension": self._dimension,
            "scale": self._scale,
            "inputs": self._map_names_to_vector(self._inputs),
            "residual": self.residual,
            "gradient": tuple(self._map_names_to_vector(g) for g in self.gradient),
        }

class EqualScalars(ResidualCalculation):
    """The residuals and gradient of a constraint holding 2 scalars equal.

    :param a: A scalar value.
    :param b: Another scalar value.
    :param scale: Solver scale factor.
    """
    dimensions = (2, 3)

    def __init__(self, a: float, b: float, /, scale: float=1):
        super().__init__((a, b), ("a", "b"), 0, 1, scale)
        self.__inputs: tuple[float, float] = (a, b)

    @classmethod
    def from_floats(cls, inputs: Sequence[float], scale: float=1) -> Self:
        try:
            a, b = inputs
        except ValueError as exc:
            raise ValueError(f"Got {len(inputs)} inputs for {cls}, expected 2.") from exc
        return cls(a, b, scale)

    @property
    def residual(self) -> tuple[float]:
        return (self._residual(*self.__inputs, self._scale),)

    @property
    def gradient(self) -> tuple[tuple[float, float]]:
        return self._gradient(self._scale)

    @staticmethod
    def _residual(a: float, b: float, /, scale: float=1) -> float:
        return scale * (b - a)

    @staticmethod
    def _gradient(scale: float=1) -> tuple[tuple[float, float]]:
        return ((-scale, scale),) # Gradient is (-1, 1)

class EqualVectorComponents2D(ResidualCalculation):
    """The residuals/gradients of a constraint holding 2 2D vectors equal, solved component-wise.

    :param v0: A 2D Vector.
    :param v1: Another 2D Vector.
    :param scale: Solver scale factor.
    """
    dimensions = (2,)

    def __init__(self, v0: tuple[float, float], v1: tuple[float, float], /, scale: float=1):
        inputs = tuple(f for v in (v0, v1) for f in v)
        super().__init__(inputs, ("v0", "v1"), 2, 2, scale)
        self.__inputs = (Vector2D(*v0), Vector2D(*v1))

    @classmethod
    def from_floats(cls, inputs: Sequence[float], scale: float=1) -> Self:
        try:
            x0, y0, x1, y1 = inputs
        except ValueError as exc:
            raise ValueError(f"Got {len(inputs)} inputs for {cls}, expected 4.") from exc
        return cls((x0, y0), (x1, y1), scale)

    @property
    def residual(self) -> tuple[float, float]:
        return self._residual(*self.__inputs, self._scale)

    @property
    def gradient(self) -> tuple[tuple[float, float, float, float],
                                tuple[float, float, float, float]]:
        return self._gradient(*self.__inputs, self._scale)

    @staticmethod
    def _residual(v0: Vector2D, v1: Vector2D, scale: float=1) -> tuple[float, float]:
        return (*EqualScalars(v0.x, v1.x, scale).residual,
                *EqualScalars(v0.y, v1.y, scale).residual)

    @staticmethod
    def _gradient(v0: Vector2D, v1: Vector2D, /,
                  scale: float=1) -> tuple[tuple[float, float, float, float],
                                           tuple[float, float, float, float]]:
        # The respective component residual inputs are independent of each other, e.g., the
        # gradients of the x residual are independent of y so they're always 0.
        dr0dx0, dr0dx1 = EqualScalars(v0.x, v1.x, scale).gradient[0]
        dr1dy0, dr1dy1 = EqualScalars(v0.x, v1.x, scale).gradient[0]
        return ((dr0dx0, 0, dr0dx1, 0), (0, dr1dy0, 0, dr1dy1))

class EqualVectors2D(ResidualCalculation):
    """The residuals and gradient of a constraint holding 2 2D vectors equal.

    :param v0: A 2D Vector.
    :param v1: Another 2D Vector.
    :param scale: Solver scale factor.
    """
    dimensions = (2,)

    def __init__(self, v0: tuple[float, float], v1: tuple[float, float], /, scale: float=1):
        inputs = tuple(f for v in (v0, v1) for f in v)
        super().__init__(inputs, ("v0", "v1"), 2, 2, scale)
        self.__inputs = (Vector2D(*v0), Vector2D(*v1))

    @classmethod
    def from_floats(cls, inputs: Sequence[float], scale: float=1) -> Self:
        try:
            x0, y0, x1, y1 = inputs
        except ValueError as exc:
            raise ValueError(f"Got {len(inputs)} inputs for {cls}, expected 4.") from exc
        return cls((x0, y0), (x1, y1), scale)

    @property
    def residual(self) -> tuple[float]:
        return (self._residual(*self.__inputs, self._scale),)

    @property
    def gradient(self) -> tuple[tuple[float, float, float, float]]:
        return self._gradient(*self.__inputs, self._scale)

    @staticmethod
    def _residual(v0: Vector2D, v1: Vector2D, /, scale: float=1) -> float:
        return scale * math.sqrt((v1.x - v0.x)**2 + (v1.y - v0.x)**2)

    @staticmethod
    def _gradient(v0: Vector2D, v1: Vector2D, /,
                  scale: float=1) -> tuple[tuple[float, float, float, float]]:
        distance = EqualVectors2D._residual(v0, v1)
        return (
            (
                scale * (v0.x - v1.x) / distance,
                scale * (v0.y - v1.y) / distance,
                scale * (v1.x - v0.x) / distance,
                scale * (v1.y - v0.y) / distance
            ),
        )

class CoincidentLinePoint2D(ResidualCalculation):
    """The residuals and gradient of a 2D Line to Point coincident constraint.

    :param p0: The point vector.
    :param p1: The first line point.
    :param p2: The second line point.
    :param scale: Solver scale factor.
    """
    dimensions = (2,)

    def __init__(self,
                 p0: tuple[float, float],
                 p1: tuple[float, float],
                 p2: tuple[float, float], /,
                 scale: float=1):
        inputs = tuple(f for v in (p0, p1, p2) for f in v)
        super().__init__(inputs, ("p0", "p1", "p2"), 3, 2, scale)
        self.__inputs = (Vector2D(*p0), Vector2D(*p1), Vector2D(*p2))

    @classmethod
    def from_floats(cls, inputs: Sequence[float], scale: float=1) -> Self:
        try:
            x0, y0, x1, y1, x2, y2 = inputs
        except ValueError as exc:
            raise ValueError(f"Got {len(inputs)} inputs for {cls}, expected 6.") from exc
        return cls((x0, y0), (x1, y1), (x2, y2), scale)

    @property
    def residual(self) -> tuple[float]:
        return (self._residual(*self.__inputs, self._scale),)

    @property
    def gradient(self) -> tuple[tuple[float, float, float, float, float, float]]:
        return self._gradient(*self.__inputs, self._scale)

    @staticmethod
    def _residual(p0: Vector2D, p1: Vector2D, p2: Vector2D, /, scale: float=1) -> float:
        delta_y = p2.y - p1.y
        delta_x = p2.x - p1.x
        dot = -p0.x * delta_y + p0.y * delta_x + p1.x * p2.y - p2.x * p1.y
        return scale * dot / math.sqrt(delta_x**2 + delta_y**2)

    @classmethod
    def _gradient(cls, p0: Vector2D, p1: Vector2D, p2: Vector2D, /,
                  scale: float=1) -> tuple[tuple[float, float, float, float, float, float]]:
        n_s = -p0.x * (p1.y - p2.y) - p1.x * (p0.y + p2.y) + p2.x * (p0.y - p1.y)
        d_s = p2.x**2 + p2.y**2 + p1.x**2 + p1.y**2 - 2 * (p1.x * p2.x + p1.y * p2.y)
        return (
            (
                scale * (p1.y + p2.y) / math.sqrt(d_s),
                scale * (p2.x - p1.x) / math.sqrt(d_s),
                2*scale * (d_s * (p2.y - p0.y) - n_s * (p1.x - p2.x)) / d_s**(3/2),
                -scale * (d_s * (p0.x - p2.x) - n_s * (p1.x - p2.x)) / d_s**(3/2),
                scale * (d_s * (p0.y - p1.y) - n_s * (p2.x - p1.x)) / d_s**(3/2),
                scale * (d_s * (p1.x - p0.x) - n_s * (p2.y - p1.y)) / d_s**(3/2),
            ),
        )
