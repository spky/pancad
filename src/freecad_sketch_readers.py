import sys
import math

# Path to your FreeCAD.so or FreeCAD.pyd file
FREECADPATH = 'C:/Users/George/Documents/FreeCAD1/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/bin' 
sys.path.append(FREECADPATH) 
import FreeCAD as App
import Part
import Sketcher

def print_object_attributes(obj):
    print(str(obj.__doc__) + " Properties:")
    for prop in dir(obj):
        print(prop + " | " + str(getattr(obj,prop)))

def read_all_sketches_from_file(filepath: str) -> list[Sketcher.Sketch]:
    """Returns a list of all the sketches in a FCStd file
    """
    if filepath.endswith(".FCStd"):
        document = App.open(filepath)
        sketches = []
        for obj in document.Objects:
            if obj.TypeId == "Sketcher::SketchObject":
                sketches.append(obj)
        return sketches
    else:
        raise ValueError("Provided filepath'"
                         + str(filepath)
                         + "' is not a FreeCAD file!")

def read_sketch_by_label(filepath: str, label: str) -> Sketcher.Sketch:
    """Returns a sketch object from the given FreeCAD file based on 
    its label. If no sketch matches, it returns None
    :param filepath: The FreeCAD filepath
    :param label: the desired sketch's label
    """
    sketch = None
    all_sketches = read_all_sketches_from_file(filepath)
    for s in all_sketches:
        if s.Label == label:
            return s
    return None

def read_2d_vector(obj: App.Base.Vector, decimals: int = 6) -> list: 
    """Returns the [x, y] list of a FreeCAD vector after checking 
    that the z coordinate is 0
    
    :param obj: FreeCAD Vector object
    :returns: x, y, z list of vector's coordinates
    """
    if math.isclose(round(obj.z, decimals), 0):
        return [round(obj.x, decimals), round(obj.y, decimals)]
    else:
        raise ValueError("Vector's z is not 0, value given: " + str(obj.z))

def read_line_segment(obj: Part.LineSegment) -> dict:
    """Returns a dictionary with properties that define the given 
    FreeCAD Sketch LineSegment. Does not do any unit conversions, FreeCAD 
    usually defaults to mm. Will only work on Sketcher 
    'Part::GeomLineSegment' type line segments.
    
    :param obj: A line segment object from FreeCAD
    :returns: A dictionary of line segment id, start and end properties
    """
    if obj.hasExtensionOfType("Sketcher::SketchGeometryExtension"):
        GEO_EXT = "Sketcher::SketchGeometryExtension"
        properties = {
            "id": obj.getExtensionOfType(GEO_EXT).Id,
            "start": read_2d_vector(obj.StartPoint),
            "end": read_2d_vector(obj.EndPoint),
            "geometry_type": "line",
        }
        return properties
    else:
        raise ValueError("Line does not have SketchGeometryExtension, so "
                         "it may not be a Sketcher line!")

def read_point(obj: Part.Point) -> dict:
    """Returns a dictionary with the FreeCAD Sketch point's 
    properties. Will only work on Sketcher 'Part::GeomPoint' type 
    objects. Points do not have SketchGeometryExtensions in FreeCAD.
    
    :param obj: A point object from FreeCAD
    :returns: A dictionary of point properties, currently just the x, 
              y, z location as a list
    """
    if math.isclose(obj.Z, 0):
        properties = {
            "location": [obj.X, obj.Y],
            "geometry_type": "point",
        }
        return properties
    else:
        raise ValueError("The point's Z is not 0, value given: "
                         + str(obj.Z))

def read_circle(obj: Part.Circle) -> dict:
    """Returns a dictionary with the FreeCAD Sketch circle's 
    properties. Will only work on Sketcher 'Part::GeomCircle' type 
    objects
    
    :param obj: A circle object from FreeCAD
    :returns: A dictionary of circle id, location, and radius properties
    """
    if obj.hasExtensionOfType("Sketcher::SketchGeometryExtension"):
        GEO_EXT = "Sketcher::SketchGeometryExtension"
        properties = {
            "id": obj.getExtensionOfType(GEO_EXT).Id,
            "location": read_2d_vector(obj.Location),
            "radius": obj.Radius,
            "geometry_type": "circle",
        }
        return properties
    else:
        raise ValueError("Circle does not have SketchGeometryExtension, so "
                         "it may not be a Sketcher line!")

def read_circle_arc(obj: Part.ArcOfCircle) -> dict:
    """Returns a dictionary with the FreeCAD Sketch arc's 
    properties. Will only work on Sketcher 'Part::GeomArcOfCircle' type 
    objects
    
    :param obj: An Arc Of Circle object from FreeCAD
    :returns: A dictionary of circle id, location, radius, start 
              point, and end point properties
    """
    if obj.hasExtensionOfType("Sketcher::SketchGeometryExtension"):
        GEO_EXT = "Sketcher::SketchGeometryExtension"
        properties = {
            "id": obj.getExtensionOfType(GEO_EXT).Id,
            "location": read_2d_vector(obj.Location),
            "radius": obj.Radius,
            "start": read_2d_vector(obj.StartPoint),
            "end": read_2d_vector(obj.EndPoint),
            "geometry_type": "circular_arc",
        }
        return properties
    else:
        raise ValueError("Arc does not have SketchGeometryExtension, so "
                         "it may not be a Sketcher line!")

def read_sketch_geometry(obj: Sketcher.Sketch) -> list[dict]:
    """Returns a list of dictionaries describing each geometry object 
    in given FreeCAD sketch. The Sketcher.Sketch type may not be the 
    right type hint, it needs to be verified!
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
                raise ValueError(str(g.TypeId) + "is not a supported TypeId")
    return geometry
