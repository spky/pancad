from collections import OrderedDict

from PanCAD.cad.freecad import App, Sketcher, Part
from PanCAD.cad.freecad.sketch_constraints import translate_constraint
from PanCAD.cad.freecad.constants import ObjectType, EdgeSubPart

from PanCAD.filetypes import PartFile
from PanCAD.geometry import (
    Circle, CoordinateSystem, Extrude, LineSegment, Sketch
)
from PanCAD.geometry.constraints import (
    Coincident, Vertical, Horizontal,
    Distance, HorizontalDistance, VerticalDistance,
    Radius, Diameter,
)
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils import file_handlers

def to_freecad(filepath: str, pancad_file: PartFile) -> None:
    """Saves a PanCAD file object to a FreeCAD file.
    
    :param filepath: Location to save the new FreeCAD file.
    :param pancad_file: A pancad file object
    """
    if isinstance(pancad_file, PartFile):
        document = App.newDocument()
        document.FileName = file_handlers.filepath(filepath)
        
        """
        FreeCAD does not have a file that forces users to put only one part 
        into a file, but most other cad programs do. The file created by 
        PanCAD sets up a file structured to only have one body in it at the 
        end of processing.
        """
        
        # Add body and coordinate system
        root = document.addObject(ObjectType.BODY, "Body")
        file_cs = pancad_file.get_coordinate_system()
        
        # Initialize feature map with part file coordinate system
        feature_map = OrderedDict()
        feature_map.update(
            map_coordinate_system(file_cs, root.Origin)
        )
        for f in pancad_file.get_features():
            feature_map = add_feature_to_freecad(f, feature_map)
        
        document.recompute()
        document.save()
    else:
        raise ValueError(f"File type {pancad_file.__class__} not recognized")

def add_feature_to_freecad(feature: Sketch | Extrude,
                           feature_map: dict) -> dict:
    """Adds the feature to the freecad file and updates the feature map to 
    maintain the connection between the new freecad feature and the pancad 
    feature.
    
    :param feature: A PanCAD feature.
    :param feature_map: A dict connecting pancad objects to equivalent freecad 
        objects.
    :return: The feature_map with new entries for the feature.
    """
    
    if isinstance(feature, Sketch):
        # Assumes that the sketch is placed on a freecad coordinate system
        freecad_origin = feature_map[
            (feature.coordinate_system, ConstraintReference.ORIGIN)
        ]
        origin_parent = freecad_origin.getParent()
        # Add sketch to file and to map
        freecad_sketch = origin_parent.newObject(ObjectType.SKETCH, feature.uid)
        support = feature_map[
            (feature.coordinate_system, feature.plane_reference)
        ]
        freecad_sketch.AttachmentSupport = (support, [""])
        freecad_sketch.MapMode = "FlatFace"
        feature_map.update(
            {(feature, ConstraintReference.CORE): freecad_sketch}
        )
        # Add geometry to sketch and to map
        feature_map = map_sketch_geometry(feature, feature_map)
    elif isinstance(feature, Extrude):
        freecad_profile = feature_map[
            (feature.profile, ConstraintReference.CORE)
        ]
        profile_parent = freecad_profile.getParent()
        freecad_pad = profile_parent.newObject(ObjectType.PAD, feature.uid)
        
        freecad_pad.Profile = (freecad_profile, [""])
        freecad_pad.Length = feature.length
        freecad_pad.ReferenceAxis = (freecad_profile, ["N_Axis"])
        freecad_profile.Visibility = False
    else:
        raise ValueError(f"Feature class {feature.__class__} not recognized")
    return feature_map

def map_sketch_geometry(sketch: Sketch, feature_map: dict) -> dict:
    """Updates and returns a feature_map with the geometry in the sketch.
    
    :param sketch: A PanCAD sketch.
    :param feature_map: A dict connecting pancad objects to equivalent freecad 
        objects.
    """
    freecad_sketch = feature_map[(sketch, ConstraintReference.CORE)]
    
    for i, (geo, cons) in enumerate(zip(sketch.geometry, sketch.construction)):
        # Add all sketch geometry
        if isinstance(geo, LineSegment):
            start = App.Vector(tuple(geo.point_a) + (0,))
            end = App.Vector(tuple(geo.point_b) + (0,))
            new_geometry = Part.LineSegment(start, end)
        elif isinstance(geo, Circle):
            center = App.Vector(tuple(geo.center) + (0,))
            normal = App.Vector((0, 0, 1))
            new_geometry = Part.Circle(center, normal, geo.radius)
        else:
            raise ValueError(f"Geometry class {geo.__class__} not recognized")
        
        freecad_sketch.addGeometry(new_geometry, cons)
        feature_map.update({(sketch, "geometry", i): new_geometry})
    
    for i, constraint in enumerate(sketch.constraints):
        # Add all sketch constraints
        new_constraint = translate_constraint(sketch, constraint)
        freecad_sketch.addConstraint(new_constraint)
        feature_map.update(
            {(sketch, "constraint", i): new_constraint}
        )
    
    return feature_map

def map_coordinate_system(coordinate_system: CoordinateSystem,
                          origin: App.DocumentObject) -> dict:
    """Returns a dict that maps pancad (coordinate system, reference) tuples to 
    a freecad origin object.
    
    :param coordinate_system: A PanCAD coordinate system.
    :param origin: A FreeCAD origin object.
    :returns: A dict mapping the coordinate_system's subgeometry to the FreeCAD 
        origin's OriginFeatures with ConstraintReferences.
    """
    return { # Assumes FreeCAD maintains the same order in the future
        (coordinate_system, ConstraintReference.ORIGIN): origin,
        (coordinate_system, ConstraintReference.X): origin.OriginFeatures[0],
        (coordinate_system, ConstraintReference.Y): origin.OriginFeatures[1],
        (coordinate_system, ConstraintReference.Z): origin.OriginFeatures[2],
        (coordinate_system, ConstraintReference.XY): origin.OriginFeatures[3],
        (coordinate_system, ConstraintReference.XZ): origin.OriginFeatures[4],
        (coordinate_system, ConstraintReference.YZ): origin.OriginFeatures[5],
    }