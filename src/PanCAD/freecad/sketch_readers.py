"""A module providing functions to read FreeCAD sketches and geometry 
information from files into Python"""

import sys
import math

# Path to your FreeCAD.so or FreeCAD.pyd file
FREECADPATH = 'C:/Users/George/Documents/FreeCAD1/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/bin' 
sys.path.append(FREECADPATH) 
import FreeCAD as App
import Part
import Sketcher

def read_all_sketches_from_file(filepath: str) -> list[Sketcher.Sketch]:
    """Returns a list of all the sketches in a FCStd file
    
    :param filepath: The filepath of a FreeCAD file
    :returns: a list of all the sketches in the file
    """
    if filepath.endswith(".FCStd"):
        document = App.open(filepath)
        sketches = []
        for obj in document.Objects:
            if obj.TypeId == "Sketcher::SketchObject":
                sketches.append(obj)
        return sketches
    else:
        raise ValueError(f"Filepath '{filepath}' is not a FreeCAD file!")

def read_sketch_by_label(filepath: str, label: str) -> Sketcher.Sketch:
    """Returns a sketch object from the given FreeCAD file based on 
    its label. If no sketch matches, it returns None
    
    :param filepath: The FreeCAD filepath
    :param label: the desired sketch's label
    :returns: The desired sketch if found, otherwise None
    """
    all_sketches = read_all_sketches_from_file(filepath)
    for s in all_sketches:
        if s.Label == label:
            return s
    return None

def read_2d_vector(obj: App.Base.Vector, decimals: int = 6) -> list: 
    """Returns the [x, y] list of a FreeCAD vector after checking 
    that the z coordinate is 0
    
    :param obj: FreeCAD Vector object
    :param decimals: The number of decimals to round the coordinates to
    :returns: x, y, z list of vector's coordinates
    """
    if math.isclose(round(obj.z, decimals), 0):
        return [round(obj.x, decimals), round(obj.y, decimals)]
    else:
        raise ValueError(f"Vector's z is not 0, value given: '{obj.z}'")

def read_line_segment(line: Part.LineSegment) -> dict:
    """Returns a dictionary with properties that define the given FreeCAD 
    Sketch LineSegment. Does not do any unit conversions, FreeCAD usually 
    defaults to mm. Will only work on Sketcher 'Part::GeomLineSegment' 
    type line segments.
    
    :param line: A FreeCAD line segment object
    :returns: A dictionary of line segment id, start and end properties
    """
    if line.hasExtensionOfType("Sketcher::SketchGeometryExtension"):
        GEO_EXT = "Sketcher::SketchGeometryExtension"
        properties = {
            "id": line.getExtensionOfType(GEO_EXT).Id,
            "start": read_2d_vector(line.StartPoint),
            "end": read_2d_vector(line.EndPoint),
            "geometry_type": "line",
        }
        return properties
    else:
        raise ValueError("Line does not have SketchGeometryExtension, so "
                         + "it may not be a Sketcher line!")

def read_point(point: Part.Point) -> dict:
    """Returns a dictionary with the FreeCAD Sketch point's 
    properties. Will only work on Sketcher 'Part::GeomPoint' type 
    objects. Points do not have SketchGeometryExtensions in FreeCAD.
    
    :param point: A point object from FreeCAD
    :returns: A dictionary of point properties, currently just the [x, y] 
              location as a list
    """
    if math.isclose(point.Z, 0):
        properties = {
            "location": [point.X, point.Y],
            "geometry_type": "point",
        }
        return properties
    else:
        raise ValueError(f"The point's Z is not 0, value given: {point.Z}")

def read_circle(circle: Part.Circle) -> dict:
    """Returns a dictionary with the FreeCAD Sketch circle's 
    properties. Will only work on Sketcher 'Part::GeomCircle' type 
    objects
    
    :param circle: A FreeCAD circle object
    :returns: A dictionary of circle id, location, and radius properties
    """
    if circle.hasExtensionOfType("Sketcher::SketchGeometryExtension"):
        GEO_EXT = "Sketcher::SketchGeometryExtension"
        properties = {
            "id": circle.getExtensionOfType(GEO_EXT).Id,
            "location": read_2d_vector(circle.Location),
            "radius": circle.Radius,
            "geometry_type": "circle",
        }
        return properties
    else:
        raise ValueError("Circle does not have SketchGeometryExtension, so "
                         + "it may not be a Sketcher line!")

def read_circle_arc(arc: Part.ArcOfCircle) -> dict:
    """Returns a dictionary with the FreeCAD Sketch arc's 
    properties. Will only work on Sketcher 'Part::GeomArcOfCircle' type 
    objects
    
    :param arc: An Arc Of Circle object
    :returns: A dictionary of circle id, location, radius, start 
              point, and end point properties
    """
    if arc.hasExtensionOfType("Sketcher::SketchGeometryExtension"):
        GEO_EXT = "Sketcher::SketchGeometryExtension"
        properties = {
            "id": arc.getExtensionOfType(GEO_EXT).Id,
            "location": read_2d_vector(arc.Location),
            "radius": arc.Radius,
            "start": read_2d_vector(arc.StartPoint),
            "end": read_2d_vector(arc.EndPoint),
            "geometry_type": "circular_arc",
        }
        return properties
    else:
        raise ValueError("Arc does not have SketchGeometryExtension, so "
                         + "it may not be a Sketcher line!")

def read_sketch_geometry(obj: Sketcher.Sketch) -> list[dict]:
    """Returns a list of dictionaries describing each geometry object 
    in given FreeCAD sketch.
    
    :param sketch: A FreeCAD Sketch object
    :returns: A list of geometry dictionaries for each sketch object
    """
    geometry = []
    for g in obj.Geometry:
        match g.TypeId:
            case "Part::GeomLineSegment":
                geometry.append(read_line_segment(g))
            case "Part::GeomPoint":
                geometry.append(read_point(g))
            case "Part::GeomArcOfCircle":
                geometry.append(read_circle_arc(g))
            case "Part::GeomCircle":
                geometry.append(read_circle(g))
            case _:
                raise ValueError(f"'{g.TypeId}' is not a supported TypeId")
    return geometry
