"""A module to provide provide PanCAD functions to consistently compare values"""

from functools import singledispatch
import math
import numpy as np

# NumberType = int|float|np.int64|np.int32
# FloatType = 

@singledispatch
def isclose(value_a, value_b,
            abs_tol: float=1e-9, rel_tol: float=1e-9, nan_equal: bool = False):
    raise NotImplementedError(f"Unsupported 1st type {value_a.__class__}")

@isclose.register
def isclose_number(value_a: int|float|np.integer|np.floating,
                   value_b: int|float|np.integer|np.floating,
                   rel_tol: float=1e-9, abs_tol: float=1e-9,
                   nan_equal: bool=False):
    if (isinstance(value_a, (float,np.floating))
            or isinstance(value_b, (float,np.floating))):
        if nan_equal and math.isnan(value_a) and math.isnan(value_b):
            return True
        else:
            return math.isclose(value_a, value_b,
                                rel_tol=rel_tol, abs_tol=abs_tol)
    else:
        return value_a == value_b

@isclose.register
def isclose_tuple(tuple_a: tuple, tuple_b: tuple,
                  rel_tol: float=1e-9, abs_tol: float=1e-9,
                  nan_equal: bool=False):
    comparisons = []
    for val1, val2 in zip(tuple_a, tuple_b):
        if (isinstance(val1, (float,np.floating))
                or isinstance(val2, (float,np.floating))):
            if nan_equal and math.isnan(val1) and math.isnan(val2):
                comparisons.append(True)
            else:
                comparisons.append(
                    math.isclose(val1, val2, rel_tol=rel_tol, abs_tol=abs_tol)
                )
        else:
            comparisons.append(val1 == val2)
    return all(comparisons)