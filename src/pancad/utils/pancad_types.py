"""A module providing common types for use throughout pancad."""

from collections import namedtuple
from collections.abc import Sequence
from typing import Union
from numbers import Real

import numpy as np

VectorLike = Union[Sequence, np.ndarray]
Space2DVector = tuple[Real, Real]
Space3DVector = tuple[Real, Real, Real]
SpaceVector = Space2DVector | Space3DVector

PolarVector = namedtuple("PolarVector", ["r", "phi"])
SphericalVector = namedtuple("SphericalVector", ["r", "phi", "theta"])

FitBox2D = namedtuple("FitBox2D", ["min_", "max_"])
