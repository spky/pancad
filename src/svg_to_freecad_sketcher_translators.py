"""A module that acts as a interface control between freecad sketcher 
and an svg file. This module is not intended to generate the actual 
elements or objects in either format, it only takes textual 
information from FreeCAD are converts it into the equivalent 
information in SVG. This module is intended to be the actual 'baton 
pass' point, where all the work before this was dealing with FreeCAD 
and everything after this is dealing with SVG.
"""

import sys
import math

import trigonometry as trig
import svg_parsers as sp
import svg_generators as sg

def line(svg_properties: dict) -> dict:
    """Returns a dictionary of equivalent FreeCAD properties to recreate 
    an svg path line in an FreeCAD sketch as a line.
    
    :param svg_properties: line segment properties from an svg file
    :returns: FreeCAD line properties to be used to create an equivalent 
              line
    """
    svg_dict = check_path_data(svg_properties["d"],
                               svg_properties["id"],
                               "line")
    return {
        "id": svg_dict["id"],
        "start": svg_dict["start"],
        "end": svg_dict["end"],
        "geometry_type": "line",
    }

def circular_arc(svg_properties: dict) -> dict:
    """Returns a dictionary of equivalent FreeCAD properties to recreate 
    an svg path circular arc in an FreeCAD sketch as a circular arc.
    
    :param svg_properties: circular arc properties from an svg file
    :returns: FreeCAD arc properties to be used to create an equivalent 
              arc
    """
    svg_dict = check_path_data(svg_properties["d"],
                               svg_properties["id"],
                               "circular_arc")
    point_1 = trig.point_2d(svg_dict["start"])
    point_2 = trig.point_2d(svg_dict["end"])
    
    arc_properties = trig.circle_arc_endpoint_to_center(
        trig.point_2d(svg_dict["start"]),
        trig.point_2d(svg_dict["end"]),
        svg_dict["large_arc_flag"],
        svg_dict["sweep_flag"],
        svg_dict["radius"],
    )
    return {
        "id": svg_dict["id"],
        "location": trig.pt2list(arc_properties[0]),
        "radius": svg_dict["radius"],
        "start": svg_dict["start"],
        "end": svg_dict["end"],
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
        #"id": svg_properties["id"],
        "location": [svg_properties["cx"], svg_properties["cy"]],
        "geometry_type": "point",
    }

def ellipse(svg_properties: dict) -> dict:
    pass

def circle(svg_properties: dict) -> dict:
    """Returns a dictionary of equivalent FreeCAD properties to 
    recreate a point from a SVG in a FreeCAD sketch
    
    :param svg_properties: circle properties from an svg file
    :returns: FreeCAD point properties to be used to create an equivae
    """
    return {
        "id": freecad_id_from_svg_id(svg_properties["id"], "circle"),
        "location": [svg_properties["cx"], svg_properties["cy"]],
        "radius": svg_properties["r"],
        "geometry_type": "circle",
    }

def freecad_id_from_svg_id(svg_id: str, geometry_type: str) -> int:
    """Returns the freecad geometry id from the svg id
    :param svg_id: id from an svg geometry element
    :geometry_type: the type of geometry that the id is associated with
    :returns: FreeCAD geometry id
    """
    return int(svg_id.replace(geometry_type, ""))

def check_path_data(path_data: str, id_: str, geometry_type:str) -> dict:
    """Raises a value error if the number of commands does not equal 
    1 or if the geometry type does not match the given type"""
    path_dict_list = sp.path_data_to_dicts(path_data)
    if len(path_dict_list) != 1:
        raise ValueError(str(path_data)
                         + " has too many commands to map "
                         + "into FreeCAD using this translator")
    elif path_dict_list[0]["geometry_type"] != geometry_type:
        raise ValueError(path_dict_list[0]["geometry_type"]
                         + " is the wrong geometry type, expected: "
                         + geometry_type)
    else:
        path_dict = path_dict_list[0]
        path_dict["id"] = freecad_id_from_svg_id(id_, geometry_type)
        return path_dict

def translate_geometry(svg_geometry: list[dict]) -> list[dict]:
    """Returns a list of dictionaries that have been translated from 
    svg to freecad properties
    """
    geometry = []
    for g in svg_geometry:
        match g["geometry_type"]:
            case "line":
                geometry.append(line(g))
            case "point":
                geometry.append(point(g))
            case "circle":
                geometry.append(circle(g))
            case "circular_arc":
                geometry.append(circular_arc(g))
            case _:
                raise ValueError(str(g["geometry_type"])
                                 + "is not a supported geometry type")
    return geometry