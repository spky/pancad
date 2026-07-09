"""Test input/output helpers"""
from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Iterable
from functools import wraps
import inspect
from inspect import Parameter

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable
    from typing import TypeVar, ParamSpec

    T = ParamSpec("T")
    R = TypeVar("R")
    ParamKey = str | tuple[str, int]
    ParamTuple = tuple[ParamKey, Hashable]

func_signatures: dict[str, inspect.Signature] = {}
inout_storage: dict[str, list[dict[str, object]]] = {}
"""A dictionary to save function input/output data to for nondeterminism testing."""

def save_inout(name: str) -> Callable[[Callable[T, R]], Callable[T, R]]:
    """A wrapper that saves each the inputs and output of a function call the name in the module's
    inout_storage dictionary. The output is saved as the provided name.
    """
    def decorator(func: Callable[T, R]) -> Callable[T, R]:
        @wraps(func)
        def wrapper(*args: T.args, **kwargs: T.kwargs) -> R:
            try: # Get or set and get the function's signature.
                sign = func_signatures[name]
            except KeyError:
                sign = func_signatures.setdefault(name, inspect.signature(func))
            inouts = {} # Save the function's inputs based on the signature.
            for i, param in enumerate(sign.parameters.values()):
                if param.kind in {Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD}:
                    try:
                        inouts[param.name] = args[i]
                    except IndexError:
                        inouts[param.name] = kwargs.get(param.name, param.default)
                elif param.kind == Parameter.KEYWORD_ONLY:
                    # An empty default would have already raised an error, so get() is ok here.
                    inouts[param.name] = kwargs.get(param.name, param.default)
                else:
                    raise NotImplementedError(f"Unsupported parameter kind {param.kind}")
            result = func(*args, **kwargs) # Execute the function to get the output.
            inouts[f"{name}"] = result
            inout_storage.setdefault(name, []).append(inouts)
            return result
        return wrapper
    return decorator

def get_chained_inout(name: str) -> list[dict[ParamKey, object]]:
    """Returns the saved inout values as a list of dictionaries with one noniterable value per
    key. Appends the index of the appearance to the end. This function assumes that the objects
    are only one nested level deep, i.e., like a vector and not an array. The output of the inout
    """
    data = []
    for func_call in inout_storage[name]:
        chained: dict[ParamKey, object] = {}
        for key, value in func_call.items():
            if isinstance(value, Iterable):
                for i, nested in enumerate(value):
                    chained[(key, i)] = nested
            else:
                chained[key] = value
        data.append(chained)
    return data

def get_inconsistent(name: str) -> dict[frozenset[ParamTuple], set[frozenset[ParamTuple]]]:
    """Returns a mapping of input to output values where the input has produced multiple unique
    outputs.
    """
    in_to_out: dict[frozenset[ParamTuple], set[frozenset[ParamTuple]]] = {}
    inouts = {tuple((k, v) for k, v in call.items()) for call in get_chained_inout(name)}
    for combo in inouts:
        inputs = frozenset((k, v) for k, v in combo if name not in k)
        outputs = frozenset(combo) - inputs
        in_to_out.setdefault(inputs, set()).add(outputs)
    return {k: v for k, v in in_to_out.items() if len(v) != 1}

def reconstruct_params(pairs: Iterable[ParamTuple]) -> dict[str, object | tuple[object, ...]]:
    """Returns a mapping of name to a reconstructed value or tuple of values from stored inout
    values.
    """
    reconstructed: dict[str, object | tuple[object, ...]] = {}
    trios = sorted((*key, value) for key, value in pairs if isinstance(key, tuple))
    for name in {name for name, *_ in trios}:
        reconstructed[name] = tuple(value for param_name, _, value in trios if param_name == name)
    reconstructed.update({key: value for key, value in pairs if isinstance(key, str)})
    return reconstructed
