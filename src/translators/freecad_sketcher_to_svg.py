"""A module that acts as a interface control between freecad sketcher and an 
svg file. This module is not intended to generate the actual elements or 
objects in either format, it only takes textual information from FreeCAD 
are converts it into the equivalent information in SVG. This module is 
intended to be the actual 'baton pass' point, where all the work before 
this was dealing with FreeCAD and everything after this is dealing with 
SVG.
"""

import trigonometry as trig
import svg.generators as sg

def line(freecad_properties: dict) -> dict:
    """Returns a dictionary of equivalent svg properties to recreate a 
    FreeCAD line in an svg file as a path.
    
    :param freecad_properties: line segment properties from FreeCAD
    :returns: svg line properties to be used to create an equivalent 
              path element
    """
    id_ = freecad_properties["id"]
    d = sg.make_moveto([
        freecad_properties["start"],
        freecad_properties["end"]
    ])
    properties = {
        "id": "line" + str(id_),
        "d": d,
        "geometry_type": "line"
    }
    return properties

def point(freecad_properties: dict) -> dict:
    """Returns a dictionary of equivalent svg properties to recreate a 
    FreeCAD point in an svg file as a circle. SVGs do not have an actual 
    point element type, so they have to be represented as something 
    similar.
    
    WARNING: A consistent id for points in FreeCAD has not been easy 
    to find, so for the moment points will not have transferable IDs
    
    :param freecad_properties: point properties from FreeCAD
    :returns: svg point properties to be used to create an equivalent 
              circle element to represent the point
    """
    cx = freecad_properties["location"][0]
    cy = freecad_properties["location"][1]
    properties = {
        "id": "_".join(["point", str(cx), str(cy)]),
        "cx": cx,
        "cy": cy,
        "r": 0,
        "geometry_type": "point"
    }
    return properties

def circle(freecad_properties: dict) -> dict:
    """Returns a dictionary of equivalent svg properties to recreate 
    a FreeCAD circle in an svg file as a circle.
    
    :param freecad_properties: circle properties from FreeCAD
    :returns: svg circle properties to be used to create an 
              equivalent circle element
    """
    properties = {
        "cx": freecad_properties["location"][0],
        "cy": freecad_properties["location"][1],
        "r": freecad_properties["radius"],
        "id": "circle" + str(freecad_properties["id"]),
        "geometry_type": "circle"
    }
    return properties

def ellipse(freecad_properties: dict) -> dict:
    """TODO: Placeholder for ellipse translator implementation"""
    pass

def circular_arc(freecad_properties: dict) -> dict:
    """Returns a dictionary of equivalent svg properties to recreate a 
    FreeCAD circular arc in an svg file as an equivalent path element. 
    Some trigonometry is required to translate the information from one 
    format to another
    
    :param freecad_properties: circular arc properties from FreeCAD
    :returns: svg arc properties to be used to create an equivalent arc element
    """
    start = freecad_properties["start"]
    end = freecad_properties["end"]
    center_pt = trig.point_2d(freecad_properties["location"])
    start_pt = trig.point_2d(start)
    end_pt = trig.point_2d(end)
    radius = freecad_properties["radius"]
    
    start_angle = trig.angle_between_vectors_2d(trig.point_2d([1, 0]),
                                                start_pt - center_pt)
    sweep_angle = trig.three_point_angle(start_pt, end_pt, center_pt)
    
    arc_list = trig.circle_arc_center_to_endpoint(center_pt, radius,
                                                  start_angle, sweep_angle)
    large_arc_flag = 1 if arc_list[2] else 0
    sweep_flag = 1 if arc_list[3] else 0
    
    moveto_cmd = sg.make_moveto([start])
    arc_cmd = sg.make_arc(radius, radius, 0, large_arc_flag, sweep_flag,
                          end[0], end[1], False)
    d = sg.make_path_data([moveto_cmd, arc_cmd], " ")
    
    properties = {
        "id": "circular_arc" + str(freecad_properties["id"]),
        "d": d,
        "geometry_type": "circular_arc"
    }
    return properties

def elliptical_arc(freecad_properties: dict) -> dict:
    """TODO: Placeholder for elliptical arc translator implementation"""
    pass

def translate_geometry(freecad_sketch_geometry: list[dict]) -> list[dict]:
    """Returns a list of dictionaries that have been translated from 
    freecad to svg properties
    
    :param freecad_properties: geometry properties for a shape from FreeCAD
    :returns: svg properties to be used to create an equivalent svg element
    """
    geometry = []
    for g in freecad_sketch_geometry:
        geometry_type = g["geometry_type"]
        match geometry_type:
            case "line":
                geometry.append(line(g))
            case "point":
                geometry.append(point(g))
            case "circle":
                geometry.append(circle(g))
            case "circular_arc":
                geometry.append(circular_arc(g))
            case _:
                raise ValueError(f"'{geometry_type}' not supported")
    return geometry