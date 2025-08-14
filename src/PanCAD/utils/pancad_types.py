"""A module providing common types for use throughout PanCAD."""

from collections.abc import Sequence
from typing import Union

import numpy as np

VectorLike = Union[Sequence, np.ndarray]
