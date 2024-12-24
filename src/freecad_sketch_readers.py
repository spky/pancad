import sys
import math

# Path to your FreeCAD.so or FreeCAD.pyd file
FREECADPATH = 'C:/Users/George/Documents/FreeCAD1/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/bin' 
sys.path.append(FREECADPATH) 
import FreeCAD as App
import Part

def print_object_attributes(obj):
    print(str(obj.__doc__) + " Properties:")
    for prop in dir(obj):
        print(prop + " | " + str(getattr(obj,prop)))

def read_2d_vector(obj: App.Base.Vector) -> list: 
    """Returns the [x, y] list of a FreeCAD vector after checking 
    that the z coordinate is 0
    
    :param obj: FreeCAD Vector object
    :returns: x, y, z list of vector's coordinates
    """
    if math.isclose(obj.z, 0):
        return [obj.x, obj.y]
    else:
        raise ValueError("Vector's z is not 0, value given: " + str(obj.z))

def read_line_segment(obj: Part.LineSegment) -> dict:
    """Returns a dictionary with properties that define the given 
    FreeCAD Sketch LineSegment. Does not do any unit conversions, FreeCAD 
    usually defaults to mm. Will only work on Sketcher line segments.
    
    :param obj: A line segment object from FreeCAD
    :returns: A dictionary of line segment properties
    """
    if obj.hasExtensionOfType("Sketcher::SketchGeometryExtension"):
        GEO_EXT = "Sketcher::SketchGeometryExtension"
        properties = {
            "id": obj.getExtensionOfType(GEO_EXT).Id,
            "start": read_2d_vector(obj.StartPoint),
            "end": read_2d_vector(obj.EndPoint),
        }
        return properties
    else:
        raise ValueError("Line does not have SketchGeometryExtension, so "
                         "it may not be a Sketcher line!")