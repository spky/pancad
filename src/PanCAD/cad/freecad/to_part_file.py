from collections import OrderedDict

from PanCAD.cad.freecad import App, Sketcher, Part
from PanCAD.cad.freecad.constants import ObjectType, EdgeSubPart

from PanCAD.filetypes import PartFile
from PanCAD.geometry import (
    CoordinateSystem, Sketch, LineSegment, Extrude
)
from PanCAD.geometry.constraints import (
    Coincident, Vertical, Horizontal,
    Distance, HorizontalDistance, VerticalDistance,
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
            new_line = Part.LineSegment(start, end)
            freecad_sketch.addGeometry(new_line, cons)
            feature_map.update(
                {(sketch, "geometry", i): new_line}
            )
        else:
            raise ValueError(f"Geometry class {g.__class__} not recognized")
    
    for i, constraint in enumerate(sketch.constraints):
        # Add all sketch constraints
        geometry_inputs = get_constraint_inputs(sketch, constraint)
        if isinstance(constraint, Coincident):
            new_constraint = Sketcher.Constraint("Coincident", *geometry_inputs)
        elif isinstance(constraint, (Horizontal, Vertical)):
            if len(constraint.get_constrained()) == 1:
                # Horizontal/Vertical One Geometry Case
                if isinstance(constraint, Horizontal):
                    new_constraint = Sketcher.Constraint("Horizontal",
                                                         geometry_inputs[0])
                else:
                    new_constraint = Sketcher.Constraint("Vertical",
                                                         geometry_inputs[0])
            else:
                # Horizontal/Vertical Two Geometry Case
                if isinstance(constraint, Horizontal):
                    new_constraint = Sketcher.Constraint("Horizontal",
                                                         *geometry_inputs)
                else:
                    new_constraint = Sketcher.Constraint("Vertical",
                                                         *geometry_inputs)
        elif isinstance(constraint, Distance):
            geometry_inputs = bug_fix_001_distance(sketch, constraint)
            freecad_value_str = f"{constraint.value} {constraint.unit}"
            new_constraint = Sketcher.Constraint(
                "Distance", *geometry_inputs,
                App.Units.Quantity(freecad_value_str)
            )
        else:
            raise ValueError(f"Constraint {constraint} not a recognized type")
        
        # Add constraint to freecad and map
        freecad_sketch.addConstraint(new_constraint)
        feature_map.update(
            {(sketch, "constraint", i): new_constraint}
        )
    
    return feature_map

def bug_fix_001_distance(sketch: Sketch, constraint: Distance) -> tuple[int]:
    """Returns a modified constraint input tuple that takes into account FreeCAD 
    distance bugs.
    
    Known bugs
    - Distance between two parallel lines is actually stored as a distance 
    between the start point of the first line and the edge of the second 
    line. This causes undefined behavior when the orientation constraint that 
    made it possible to place the distance constraint is removed without 
    removing the distance constraint. Additionally, this scenario takes fewer 
    geometry inputs than normal (3 instead of 4).
    
    :param sketch: A PanCAD sketch.
    :param constraint: A PanCAD Distance constraint.
    :returns: A tuple of integer inputs to define a FreeCAD constraint.
    """
    original_inputs = zip(constraint.get_constrained(),
                          constraint.get_references())
    if all([isinstance(g, LineSegment) and r == ConstraintReference.CORE
            for g, r in original_inputs]):
        a_i, a_ref, b_i, b_ref = get_constraint_inputs(sketch, constraint)
        return (a_i, EdgeSubPart.START, b_i)
    else:
        return get_constraint_inputs(sketch, constraint)

def get_constraint_inputs(sketch: Sketch, constraint) -> tuple[int]:
    """Returns the indices required to reference constraint geometry in FreeCAD. 
    FreeCAD references the sketch origin, x-axis, and y-axis with hidden 
    external geometry elements. The origin is the start point of the x-axis 
    line, the x-axis line is at index -1, and the y-axis line is at index 
    -2. If those elements are referenced then they need to be mapped differently 
    than they are in PanCAD and likely other programs.
    
    :param sketch: A PanCAD sketch.
    :param constraint: A PanCAD Distance constraint.
    :returns: A tuple of integer inputs to define a FreeCAD constraint.
    """
    original_inputs = zip(constraint.get_constrained(),
                          constraint.get_references())
    freecad_inputs = tuple()
    for constrained, reference in original_inputs:
        if constrained is sketch.get_sketch_coordinate_system():
            # FreeCAD keeps its sketch coordinate system in negative index 
            # locations, so this is a special case for constraints.
            match reference:
                case ConstraintReference.ORIGIN:
                    index = -1
                    subpart = EdgeSubPart.START
                case ConstraintReference.X:
                    index = -1
                    subpart = EdgeSubPart.EDGE
                case ConstraintReference.Y:
                    index = -2
                    subpart = EdgeSubPart.EDGE
                case _:
                    raise ValueError(f"Invalid ConstraintReference {reference}")
        else:
            index = sketch.get_index_of(constrained)
            subpart = map_to_subpart(reference)
        freecad_inputs = freecad_inputs + (index, subpart)
    return freecad_inputs


def map_to_subpart(pancad_reference: ConstraintReference) -> EdgeSubPart:
    """Returns the EdgeSubPart that matches the PanCAD constraint reference.
    
    :param pancad_reference: A reference to a subpart of geometry.
    :returns: The FreeCAD equivalent to the pancad_reference.
    """
    match pancad_reference:
        case ConstraintReference.CORE:
            return EdgeSubPart.EDGE
        case ConstraintReference.START:
            return EdgeSubPart.START
        case ConstraintReference.END:
            return EdgeSubPart.END
        case ConstraintReference.CENTER:
            return EdgeSubPart.CENTER

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