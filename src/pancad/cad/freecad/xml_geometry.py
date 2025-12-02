"""A module providing functions for reading and writing FreeCAD geometry xml 
elements from/to its save files.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pancad.geometry.constants import ConstraintReference
from .constants.archive_constants import XMLGeometryAttr, XMLGeometryType, Tag

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

def _line_segment(element: Element) -> dict[ConstraintReference, tuple[float]]:
    line = element.find(Tag.LINE_SEGMENT)
    START_ATTR = [XMLGeometryAttr.START_X, XMLGeometryAttr.START_Y,
                  XMLGeometryAttr.START_Z]
    END_ATTR = [XMLGeometryAttr.END_X, XMLGeometryAttr.END_Y,
                XMLGeometryAttr.END_Z]
    start = [float(line.attrib[a]) for a in START_ATTR]
    end = [float(line.attrib[a]) for a in END_ATTR]
    if start[2] == end[2] == 0:
        del start[2]
        del end[2]
    return {ConstraintReference.START: tuple(start),
            ConstraintReference.END: tuple(end)}

GEOMETRY_DISPATCH = {
    XMLGeometryType.LINE_SEGMENT: _line_segment,
}