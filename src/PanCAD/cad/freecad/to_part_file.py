# TEMP #
from pprint import pprint
# TEMP #

from collections import OrderedDict

from PanCAD.cad.freecad import App, Sketcher, Part
from PanCAD.cad.freecad.constants import ObjectType, EdgeSubPart

from PanCAD.filetypes import PartFile
from PanCAD.geometry import (
    CoordinateSystem, Sketch, LineSegment
)
from PanCAD.geometry.constraints import (
    Coincident, Vertical, Horizontal,
    Distance, HorizontalDistance, VerticalDistance,
)
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils import file_handlers




def to_freecad(filepath: str, pancad_file) -> App.Document:
    
    if isinstance(pancad_file, PartFile):
        print("Start Run...\n\n")
        document = App.newDocument()
        document.FileName = file_handlers.filepath(filepath)
        
        """FreeCAD does not have a file that forces users to put only one part 
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
        # pprint(feature_map)
        
        document.recompute()
        document.save()
    else:
        raise ValueError(f"File type {pancad_file.__class__} not recognized")

def add_feature_to_freecad(feature, feature_map: dict) -> dict:
    """Adds the feature to the freecad file and updates the feature map to 
    maintain the connection between the new freecad feature and the pancad 
    feature.
    """
    
    if isinstance(feature, Sketch):
        # Assuming that the sketch is placed on a freecad coordinate system
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
    else:
        raise ValueError(f"Feature class {feature.__class__} not recognized")
    return feature_map

def map_sketch_geometry(sketch: Sketch, feature_map: dict) -> dict:
    freecad_sketch = feature_map[(sketch, ConstraintReference.CORE)]
    for i, (geo, cons) in enumerate(zip(sketch.geometry, sketch.construction)):
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
        print(f"__ Constraint {i} __")
        constraint_inputs = get_constraint_inputs(sketch, constraint)
        if isinstance(constraint, Coincident):
            new_constraint = Sketcher.Constraint("Coincident",
                                                 *constraint_inputs)
        elif isinstance(constraint, (Horizontal, Vertical)):
            if constraint.get_b() is None:
                # Horizontal/Vertical One Geometry Case
                if isinstance(constraint, Horizontal):
                    new_constraint = Sketcher.Constraint("Horizontal",
                                                         constraint_inputs[0])
                else:
                    new_constraint = Sketcher.Constraint("Vertical",
                                                         constraint_inputs[0])
            else:
                # Horizontal/Vertical Two Geometry Case
                if isinstance(constraint, Horizontal):
                    new_constraint = Sketcher.Constraint("Horizontal",
                                                         *constraint_inputs)
                else:
                    new_constraint = Sketcher.Constraint("Vertical",
                                                         *constraint_inputs)
        else:
            # IN WORK TEMP #
            continue
            # IN WORK TEMP #
        
        # Add constraint to freecad and map
        freecad_sketch.addConstraint(new_constraint)
        pprint(freecad_sketch.Constraints)
        # print(freecad_sketch.Constraints[-1])
        feature_map.update(
            {(sketch, "constraint", i): new_constraint}
        )
    
    return feature_map

def get_constraint_inputs(sketch: Sketch, constraint) -> tuple[int, int]:
    """Returns the indices required to reference constraint geometry in FreeCAD. 
    FreeCAD references the sketch origin, x-axis, and y-axis with hidden 
    external geometry elements. The origin is the start point of the x-axis 
    line, the x-axis line is at index -1, and the y-axis line is at index 
    -2. If those elements are referenced then they need to be mapped differently 
    than they are in PanCAD and likely other programs.
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
    a freecad origin object"""
    return { # Assumes FreeCAD maintains the same order in the future
        (coordinate_system, ConstraintReference.ORIGIN): origin,
        (coordinate_system, ConstraintReference.X): origin.OriginFeatures[0],
        (coordinate_system, ConstraintReference.Y): origin.OriginFeatures[1],
        (coordinate_system, ConstraintReference.Z): origin.OriginFeatures[2],
        (coordinate_system, ConstraintReference.XY): origin.OriginFeatures[3],
        (coordinate_system, ConstraintReference.XZ): origin.OriginFeatures[4],
        (coordinate_system, ConstraintReference.YZ): origin.OriginFeatures[5],
    }