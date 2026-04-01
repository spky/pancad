"""A module providing secondary solving functions that perform operations on
pancad geometry. pancad geometry must not directly depend on these since doing
they would be cyclically dependent.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from functools import singledispatch

import numpy as np

from pancad.geometry.line_segment import LineSegment

if TYPE_CHECKING:
    from numbers import Real
    from typing import Literal

def get_length(segment: LineSegment,
               along: Literal["x", "y", "z"]=None) -> float:
    """Returns the length of the line segment, defined as the distance between
    the start and end points.

    :param segment: A LineSegment object.
    :param along: The cartesian direction to measure the length along. When
        None, the total length from start to end is returned.
    :raises TypeError: When provided an incorrect along value.
    """
    if along is None:
        start_to_end = np.array(segment.end) - np.array(segment.start)
        return np.linalg.norm(start_to_end)
    lengths = {"x": abs(segment.start.x - segment.end.x),
               "y": abs(segment.start.y - segment.end.y)}
    if len(segment) == 3:
        lengths["z"] = abs(segment.start.z - segment.end.z)
    try:
        return lengths[along]
    except KeyError as exc:
        expected = ["x", "y"]
        dim = len(segment)
        if dim == 3:
            expected.append("z")
        msg = (f"Incorrect along. Expected one of {expected}"
               f" for a {dim}D LineSegment. Got: {along}")
        raise TypeError(msg) from exc

def set_length(segment: LineSegment,
               value: Real,
               from_: Literal["start", "end"],
               along: Literal["x", "y", "z"]=None) -> LineSegment:
    """Sets the length of the line segment.

    .. note:: Cases similar to setting the y direction of a line segment
        initially parallel to the x axis assigns the correct length, but the
        direction the point moves in is dependent on both the from point and the
        segment's initial direction. This may be confusing and cause unexpected
        behavior, so it is recommended to confirm the positioning of such lines
        afterwards.

    :param segment: A LineSegment object.
    :param value: The new length of the line.
    :param from_: The LineSegment point to keep constant.
    :param along: The cartesian direction to measure the length along. When
        None, the total length is set in the segment's existing direction.
    :raises ValueError: When trying to set a LineSegment's length to 0.
    :raises TypeError: When provided an incorrect value for from_ or along.
    """
    if value == 0:
        raise ValueError("Length cannot be set to 0")

    pt_map = {"start": segment.start, "end":segment.end}
    try:
        from_pt = pt_map.pop(from_)
    except KeyError as exc:
        msg = f"Unexpected from_. Must be one of {list(pt_map)}. Got: {from_}"
        raise TypeError(msg) from exc
    _, move_pt = pt_map.popitem()

    if from_ == "start":
        vector_sign = 1
    else: # Always end as long as there are only 2 options
        vector_sign = -1

    if along is None:
        # Update in the same direction as the existing line segment.
        new_vector = np.array(segment.direction) * value
    else:
        along_map = {"x": 0, "y": 1}
        dim = len(segment)
        if dim == 3:
            along_map["z"] = 2
        try:
            axis = along_map[along]
        except KeyError as exc:
            msg = ("Unexpected along. Expected None or one"
                   f" of {list(along_map)} for a {dim}D LineSegment. Got: {along}")
            raise TypeError(msg) from exc
        new_vector = np.array(segment.end) - np.array(segment.start)
        new_vector[axis] = value * np.copysign(1, segment.direction[axis])
    move_pt.cartesian = from_pt.cartesian + vector_sign * new_vector
    return segment

def get_fit_box(geometry):
    pass
