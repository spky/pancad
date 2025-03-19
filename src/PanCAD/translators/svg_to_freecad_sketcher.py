"""A module that acts as a interface control between freecad sketcher 
and an svg file. This module is not intended to generate the actual 
elements or objects in either format, it only takes textual 
information from svg files and converts it into the equivalent 
information in FreeCAD. This module is intended to be the actual 'baton 
pass' point, where all the work before this was dealing with SVG 
and everything after this is dealing with FreeCAD.
"""

from PanCAD import trigonometry as trig
from PanCAD.svg import parsers as sp

def line(svg_properties: dict) -> dict:
    """Returns a dictionary of equivalent FreeCAD properties to recreate 
    an svg path line in an FreeCAD sketch as a line.
    
    :param svg_properties: line segment properties from an svg file
    :returns: FreeCAD line properties to be used to create an equivalent 
              line
    """
    return {
        "id": freecad_id_from_svg_id(svg_properties["id"], "line"),
        "start": svg_properties["start"],
        "end": svg_properties["end"],
        "geometry_type": "line",
    }

def circular_arc(svg_properties: dict) -> dict:
    """Returns a dictionary of equivalent FreeCAD properties to recreate 
    an svg path circular arc in an FreeCAD sketch as a circular arc.
    
    :param svg_properties: circular arc properties from an svg file
    :returns: FreeCAD arc properties to be used to create an equivalent 
              arc
    """
    point_1 = trig.point_2d(svg_properties["start"])
    point_2 = trig.point_2d(svg_properties["end"])
    
    arc_properties = trig.circle_arc_endpoint_to_center(
        trig.point_2d(svg_properties["start"]),
        trig.point_2d(svg_properties["end"]),
        svg_properties["large_arc_flag"],
        svg_properties["sweep_flag"],
        svg_properties["radius"],
    )
    center_point = trig.pt2list(arc_properties[0])
    start_angle = arc_properties[1]
    sweep_angle = arc_properties[2]
    
    if sweep_angle < 0:
        # FreeCAD arcs are always drawn CCW, so the start and end switch
        end_angle = start_angle
        start_angle = trig.positive_angle(start_angle + sweep_angle)
    elif sweep_angle == 0:
        raise ValueError("Arc sweep angles cannot be zero")
    else:
        end_angle = start_angle + sweep_angle
    
    return {
        "id": freecad_id_from_svg_id(svg_properties["id"], "circular_arc"),
        "location": center_point,
        "radius": svg_properties["radius"],
        "start": start_angle,
        "end": end_angle,
        "geometry_type": "circular_arc",
    }

def point(svg_properties: dict) -> dict:
    """Returns a dictionary of equivalent FreeCAD properties to 
    recreate a point from an svg in a FreeCAD sketch. WARNING: 
    FreeCAD points do not have easily accessible ids, so these do 
    not have ids currently and are not possible to sync
    
    :param svg_properties: point properties from an svg file, 
                           represented as a circle
    :returns: FreeCAD point properties to be used to create an equivae
    """
    return {
        "location": svg_properties["center"],
        "geometry_type": "point",
    }

def ellipse(svg_properties: dict) -> dict:
    """TODO: Placeholder for ellipse translator implementation"""
    pass

def elliptical_arc(freecad_properties: dict) -> dict:
    """TODO: Placeholder for elliptical arc translator implementation"""
    pass

def circle(svg_properties: dict) -> dict:
    """Returns a dictionary of equivalent FreeCAD properties to 
    recreate a point from a SVG in a FreeCAD sketch
    
    :param svg_properties: circle properties from an svg file
    :returns: FreeCAD circle properties to be used to create an equivalent
    """
    return {
        "id": freecad_id_from_svg_id(svg_properties["id"], "circle"),
        "location": svg_properties["center"],
        "radius": svg_properties["radius"],
        "geometry_type": "circle",
    }

def freecad_id_from_svg_id(svg_id: str, geometry_type: str) -> int:
    """Returns the freecad geometry id from the svg id
    
    :param svg_id: id from an svg geometry element
    :geometry_type: the type of geometry that the id is associated with
    :returns: FreeCAD geometry id
    """
    svg_id = svg_id.replace(geometry_type, "")
    svg_id = svg_id.replace("_0", "")
    return int(svg_id)

def translate_geometry(svg_geometry: list[dict]) -> list[dict]:
    """Returns a list of dictionaries that have been translated from 
    svg to freecad properties
    
    :param svg_properties: geometry properties from an svg file
    :returns: a list of FreeCAD geometry dictionaries to create equivalent 
              FreeCAD shapes
    """
    fc_geometry = []
    for g in svg_geometry:
        geometry_type = g["geometry_type"]
        match geometry_type:
            case "line":
                fc_geometry.append(line(g))
            case "point":
                fc_geometry.append(point(g))
            case "circle":
                fc_geometry.append(circle(g))
            case "circular_arc":
                fc_geometry.append(circular_arc(g))
            case _:
                raise ValueError(f"'{geometry_type}' is not a"
                                 + f" supported geometry type")
    return fc_geometry