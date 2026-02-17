"""A module providing methods for FreeCADMap to translate features to and from
FreeCAD.
"""
from __future__ import annotations

from functools import singledispatchmethod, singledispatch
from typing import TYPE_CHECKING
from math import pi
import numpy as np
import warnings
import logging
import itertools

try:
    import FreeCAD as App
    import Part
    import Sketcher
except ImportError:
    import sys
    from pancad.cad.freecad._bootstrap import get_app_dir
    app_path = get_app_dir()
    sys.path.append(str(app_path))
    import FreeCAD as App
    import Part
    import Sketcher

from pancad.abstract import AbstractFeature, AbstractGeometry
from pancad.constants import (
    ConstraintReference as CR,
    SketchConstraint as SC,
    FeatureType as FT,
)
from pancad.geometry.circle import Circle
from pancad.geometry.circular_arc import CircularArc
from pancad.geometry.coordinate_system import CoordinateSystem
from pancad.geometry.ellipse import Ellipse
from pancad.geometry.extrude import Extrude, ExtrudeSettings
from pancad.geometry.feature_container import FeatureContainer
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.point import Point
from pancad.geometry.sketch import Sketch
from pancad.geometry.system import SketchGeometrySystem
from pancad.filetypes.part_file import PartFile

from pancad.cad.freecad import api_utils
from pancad.cad.freecad.api_utils import FreeCADUID, FreeCADConstraintGeoRef
from pancad.cad.freecad.constants import (
    ListName, ObjectType, PadType, ConstraintType as CT, EdgeSubPart as ESP
)
from pancad.cad.freecad._application_types import (
    FreeCADBody,
    FreeCADCircle,
    FreeCADCircularArc,
    FreeCADEllipse,
    FreeCADFeature,
    FreeCADGeometry,
    FreeCADLineSegment,
    FreeCADOrigin,
    FreeCADPad,
    FreeCADPoint,
    FreeCADSketch,
)
from ._map_typing import SketchElementID

if TYPE_CHECKING:
    from pancad.abstract import AbstractConstraint
    from pancad.geometry.coordinate_system import Pose

    from pancad.cad.freecad._application_types import (
        FreeCADDocument, FreeCADPlacement, FreeCADConstraint,
    )

logger = logging.getLogger(__name__)

################################################################################
# pancad ---> FreeCAD Geometry
################################################################################
def new_placement_from_pose(pose: Pose) -> FreeCADPlacement:
    """Creates a FreeCADPlacement from a pancad Pose."""
    placement = App.Placement()
    placement.Base = tuple(pose.origin)
    quat = pose.coordinate_system.get_quaternion()
    # FreeCAD Quaternions have their real component at the end.
    placement.Rotation.Q = (quat.x, quat.y, quat.z, quat.w)
    return placement

################################################################################
# FreeCAD ---> pancad Features
################################################################################
def new_part_from_document(path: str) -> PartFile:
    
    document = App.open(path)
    part = PartFile(document.Label)
    uid_map = {}
    ordered_ids = api_utils.get_topo_reading_order(document)
    return part

################################################################################
# pancad ---> FreeCAD Features
################################################################################
def new_document_from_part(part: PartFile) -> FreeCADDocument:
    """Creates a new FreeCADDocument from a PartFile"""
    document = App.newDocument()
    api_utils.relabel_object(document, part.name)

    uid_map = {part.uid: FreeCADUID.from_document(document)}
    # TODO: Move the body to the correct location in the tree
    new_feature_from_pancad(part.container, document, uid_map)
    return document

def new_feature_from_pancad(feature: AbstractFeature,
                            document: FreeCADDocument,
                            uid_map: dict[str, FreeCADUID]) -> FreeCADFeature:
    """Creates a new FreeCAD Feature from a pancad feature and adds it to the
    provided uid_map.
    """
    # TODO: Think of a less jank way to dispatch features to the right
    # functions, maybe someday. Maybe by having each feature type have a
    # dispatch string. singledispatch requires importing FreeCAD types.
    # It might also be possible to truly have each feature have common
    # interfaces, but that would need to be mapped out thoroughly for stuff like
    # sketches.
    funcs = [
        (FeatureContainer, _new_body_from_container),
        (Sketch, _new_sketch_from_pancad_sketch),
        (Extrude, _new_pad_from_pancad_extrude),
    ]
    try:
        feature_func = next(f for f in funcs if isinstance(feature, f[0]))[1]
    except StopIteration as exc:
        msg = f"Unsupported feature type '{feature.__class__}'"
        raise TypeError(msg, feature)
    return feature_func(feature, document, uid_map)

def _new_body_from_container(feature: FeatureContainer,
                             document: FreeCADDocument,
                             uid_map: dict[str, FreeCADUID]) -> FreeCADBody:
    """Adds a new body to the FreeCADDocument from a FeatureContainer"""
    if feature.uid in uid_map:
        msg = "pancad uid of container already in uid map"
        raise ValueError(msg, feature)
    body = document.addObject(ObjectType.BODY)
    api_utils.relabel_object(body, feature.name)

    body.Placement = new_placement_from_pose(feature.pose)

    # Map Origin and OriginFeatures to names that can map to container children
    origin = body.Origin
    origin_map = {"Coordinate_System": origin}
    origin_map.update(
        {api_utils.get_map_name(f.Name): f for f in origin.OriginFeatures}
    )
    reference_to_name = {
        (CR.CS, "Coordinate_System"),
        (CR.ORIGIN, "Coordinate_System"),
        # There is no center point on the Origin object, so the origin point is
        # mapped to the Origin where other systems can derive the location.
        (CR.X, "X_Axis"),
        (CR.Y, "Y_Axis"),
        (CR.Z, "Z_Axis"),
        (CR.XY, "XY_Plane"),
        (CR.XZ, "XZ_Plane"),
        (CR.YZ, "YZ_Plane"),
    }

    new_uid_map_items = {}
    system = feature.feature_system
    for reference, map_name in reference_to_name:
        pancad_uid = system.children[reference].uid
        if pancad_uid in uid_map:
            element = system.children[reference]
            msg = "pancad uid of element already in uid map"
            raise ValueError(msg, element)
        freecad_uid = FreeCADUID.from_feature(origin_map[map_name],
                                                        document)
        new_uid_map_items[pancad_uid] = freecad_uid

    body_uid = FreeCADUID.from_feature(body, document)
    new_uid_map_items[feature.uid] = body_uid
    uid_map.update(new_uid_map_items)
    for feature in system.features:
        new_feature_from_pancad(feature, document, uid_map)
    return body

def _new_sketch_from_pancad_sketch(feature: Sketch,
                                   document: FreeCADDocument,
                                   uid_map: dict[str, FreeCADUID]
                                   ) -> FreeCADSketch:
    # Get relevant pancad mapping info
    fc_parent_uid = uid_map[feature.system.feature.uid]
    fc_plane_uid = uid_map[feature.get_support().uid]

    # Add equivalent objects to freecad
    fc_sketch = document.addObject(ObjectType.SKETCH)
    api_utils.relabel_object(fc_sketch, feature.name)
    api_utils.get_by_uid(fc_parent_uid, document).addObject(fc_sketch)
    fc_sketch.AttachmentSupport = api_utils.get_by_uid(fc_plane_uid, document)
    # TODO: Add logic for assigning MapMode and raising errors around it
    fc_sketch.MapMode = "FlatFace"

    new_uid_map_items = {}
    geo_sys = feature.geometry_system
    sys_pairs = [
        (0, geo_sys.coordinate_system),
        (0, geo_sys.origin),
        (0, geo_sys.x_axis),
        (1, geo_sys.y_axis),
    ]
    for index, pc_geo in sys_pairs:
        fc_geo = fc_sketch.ExternalGeo[index]
        new_uid_map_items[pc_geo.uid] = FreeCADUID.from_sketch_geometry(
            fc_geo, "ExternalGeo", fc_sketch, document
        )
    new_uid_map_items[feature.uid] = FreeCADUID.from_feature(fc_sketch, document)
    uid_map.update(new_uid_map_items)
    _add_sketch_geometry_from_pancad(feature, document, uid_map)
    _add_sketch_constraints_from_pancad(feature, document, uid_map)
    return fc_sketch

def _new_pad_from_pancad_extrude(feature: Extrude,
                                 document: FreeCADDocument,
                                 uid_map: dict[str, FreeCADUID]) -> FreeCADPad:
    fc_parent_uid = uid_map[feature.system.feature.uid]
    fc_profile_uid = uid_map[feature.profile.uid]
    fc_profile = api_utils.get_by_uid(fc_profile_uid, document)

    pad = document.addObject(ObjectType.PAD)
    api_utils.relabel_object(pad, feature.name)
    api_utils.get_by_uid(fc_parent_uid, document).addObject(pad)
    pad.Profile = fc_profile

    if feature.unit is None:
        msg = "The unit of Extrude '{feature.name}' is not set, assuming mm"
        warnings.warn(msg)
        unit = "mm"
    else:
        unit = feature.unit
    angle_unit = "deg"

    pad.Length = f"{feature.length} {unit}"
    pad.Length2 = f"{feature.opposite_length} {unit}"
    pad.TaperAngle = f"{feature.taper_angle} {angle_unit}"
    pad.TaperAngle2 = f"{feature.opposite_taper_angle} {angle_unit}"
    pad.UseCustomVector = False
    pad.ReferenceAxis = (fc_profile, ["N_Axis"])
    pad_type_map = { # Type name, Reversed bool, Midplane bool
        FT.DIMENSION: ("Length", False, False),
        FT.ANTI_DIMENSION: ("Length", True, False),
        FT.SYMMETRIC: ("Length", False, True),
        FT.TWO_DIMENSIONS: ("TwoLengths", False, False),
        FT.ANTI_TWO_DIMENSIONS: ("TwoLengths", True, False),
    }
    pad.Type, pad.Reversed, pad.Midplane = pad_type_map[feature.type_]

    # TODO: Once Extrude supports UpToFace, add offset and UpToFace logic.
    pad.UpToFace = None
    pad.Offset = 0

    fc_profile.Visibility = False
    uid_map[feature.uid] = FreeCADUID.from_feature(pad, document)
    return pad


def _add_sketch_geometry_from_pancad(sketch: Sketch,
                                     document: FreeCADDocument,
                                     uid_map: dict[str, FreeCADUID]
                                     ) -> FreeCADSketch:
    """Adds all the sketch geometry in a pancad sketch to the mapped FreeCAD
    sketch.
    """
    fc_sketch = api_utils.get_by_uid(uid_map[sketch.uid], document)

    system = sketch.geometry_system
    new_uid_map_items = {}
    for pc_geo, is_construction in zip(system.geometry, system.construction):
        fc_geo = pancad_to_freecad_geometry(pc_geo)
        fc_sketch.addGeometry(fc_geo, is_construction)
        new_uid_map_items[pc_geo.uid] = FreeCADUID.from_sketch_geometry(
            fc_geo, "Geometry", fc_sketch, document
        )
        if fc_geo.TypeId == "Part::GeomEllipse":
            # TODO: Implement Ellipse mapping
            msg = "Ellipse mapping hasn't been implemented yet!"
            raise NotImplementedError(msg, fc_geo)
    uid_map.update(new_uid_map_items)
    return fc_sketch

def _add_sketch_constraints_from_pancad(sketch: Sketch,
                                        document: FreeCADDocument,
                                        uid_map: dict[str, FreeCADUID]
                                        ) -> FreeCADSketch:
    """Adds all the sketch constraints in a pancad sketch to the mapped FreeCAD
    sketch.
    """
    fc_sketch = api_utils.get_by_uid(uid_map[sketch.uid], document)
    new_uid_map_items = {}
    for pc_cons in sketch.geometry_system.constraints:
        fc_cons = new_constraint_from_pancad(pc_cons, document, uid_map)
        fc_sketch.addConstraint(fc_cons)
        fc_cons_uid = FreeCADUID.from_sketch_constraint(fc_cons, fc_sketch,
                                                        document)
        new_uid_map_items[pc_cons.uid] = fc_cons_uid
    uid_map.update(new_uid_map_items)
    return fc_sketch

@singledispatchmethod
def _pancad_to_freecad_feature(self,
                               feature: AbstractFeature) -> FreeCADFeature:
    """Creates a FreeCAD equivalent to the pancad feature and adds its id to the
    id map. Will also create geometry inside of features if any exist and add
    them to the map.
    """
    raise TypeError(f"Unrecognized pancad feature type {key.__class__}")

@_pancad_to_freecad_feature.register
def _coordinate_system(self, system: CoordinateSystem) -> FreeCADOrigin:
    parent = self[system.feature]
    origin = parent.Origin
    self._id_map[origin.ID] = origin
    for subfeature in origin.OriginFeatures:
        self._id_map[subfeature.ID] = subfeature
    return origin

@_pancad_to_freecad_feature.register
def _extrude(self, pancad_extrude: Extrude) -> FreeCADFeature:
    pad = self._document.addObject(ObjectType.PAD, pancad_extrude.name)
    parent = self[pancad_extrude.context]
    parent.addObject(pad)
    pad.Profile = (self[pancad_extrude.profile], [""])
    pad.Length = pancad_extrude.length
    pad.ReferenceAxis = (self[pancad_extrude.profile], ["N_Axis"])
    self[pancad_extrude.profile].Visibility = False
    self._id_map[pad.ID] = pad
    return pad

@_pancad_to_freecad_feature.register
def _feature_container(self, container: FeatureContainer) -> FreeCADBody:
    # A container creates a FreeCAD Body. FreeCAD Bodies have an origin, axes,
    # and planes created inside of them when initialized.
    body = self._document.addObject(ObjectType.BODY, container.name)
    origin = body.Origin
    sys = container.feature_system
    to_origin_feats = {
        "X_Axis": sys.x_axis,
        "Y_Axis": sys.y_axis,
        "Z_Axis": sys.z_axis,
        "XY_Plane": sys.xy_plane,
        "XZ_Plane": sys.xz_plane,
        "YZ_Plane": sys.yz_plane,
    }
    self._id_map[body.ID] = body
    self._id_map[origin.ID] = origin
    for feature in origin.OriginFeatures:
        self._id_map[feature.ID] = feature
        pc_geo = to_origin_feats[feature.Name]
        self._pancad_to_freecad[pc_geo.uid] = (pc_geo, feature.ID)
    return body

@_pancad_to_freecad_feature.register
def _sketch(self, pancad_sketch: Sketch) -> FreeCADSketch:
    # Creates both the feature and the equivalent geometry inside the sketch.
    sketch = self._document.addObject(ObjectType.SKETCH, pancad_sketch.name)
    feat_sys = pancad_sketch.system
    support = pancad_sketch.get_support()
    sketch_plane = self[support]
    breakpoint()
    parent = self[feat_sys.feature]
    parent.addObject(sketch)
    sketch.AttachmentSupport = (sketch_plane, [""])
    sketch.MapMode = "FlatFace"
    sketch.Label = pancad_sketch.name
    self._id_map[sketch.ID] = sketch
    geo_sys = sketch.geometry_system

    # Add geometry in the sketch
    pancad_pairs = zip(pancad_sketch.geometry, pancad_sketch.construction)
    for pancad_geometry, construction in pancad_pairs:
        geometry = self.pancad_to_freecad_geometry(pancad_geometry)
        geometry_id = self._freecad_add_to_sketch(geometry,
                                                  sketch,
                                                  construction)
        # The initial map between the pancad sketch geometry and the core
        # element of the freecad sketch geometry has to be set here because
        # there's no way to know which element corresponds to which unless
        # the single core relationship is mapped during generation.
        self._pancad_to_freecad[pancad_geometry.uid] = (pancad_geometry,
                                                        geometry_id)
    return sketch

################################################################################
# pancad ---> FreeCAD Geometry
################################################################################
@singledispatch
def pancad_to_freecad_geometry(geometry: AbstractGeometry) -> FreeCADGeometry:
    """Returns an equivalent FreeCAD geometry element from pancad Geometry."""
    raise TypeError(f"Unsupported pancad element type: {geometry}")

@pancad_to_freecad_geometry.register
def _line_segment(line_segment: LineSegment) -> FreeCADLineSegment:
    start = App.Vector(tuple(line_segment.start) + (0,))
    end = App.Vector(tuple(line_segment.end) + (0,))
    return Part.LineSegment(start, end)

@pancad_to_freecad_geometry.register
def _ellipse(ellipse: Ellipse) -> FreeCADEllipse:
    major_axis_point = App.Vector(tuple(ellipse.major_axis_max) + (0,))
    minor_axis_point = App.Vector(tuple(ellipse.minor_axis_max) + (0,))
    center = App.Vector(tuple(ellipse.center) + (0,))
    return Part.Ellipse(major_axis_point, minor_axis_point, center)

@pancad_to_freecad_geometry.register
def _circle(circle: Circle) -> FreeCADCircle:
    center = App.Vector(tuple(circle.center) + (0,))
    normal = App.Vector((0, 0, 1))
    return Part.Circle(center, normal, circle.radius)

@pancad_to_freecad_geometry.register
def _circular_arc(arc: CircularArc) -> FreeCADCircularArc:
    center = App.Vector(tuple(arc.center) + (0,))
    normal = App.Vector((0, 0, 1))
    circle =  Part.Circle(center, normal, arc.radius)

    if arc.is_clockwise:
        # All FreeCAD circular arcs are drawn counterclockwise
        end = arc.start_angle
        start = arc.end_angle
    else:
        start = arc.start_angle
        end = arc.end_angle

    # FreeCAD's circular arc angles are all positive
    if start < 0:
        start += 2 * pi
    if end < 0:
        end += 2 * pi
    if end < start:
        # FreeCAD forces the end angle to be larger than the start angle
        end += 2 * pi
    return Part.ArcOfCircle(circle, start, end)

# Adding FreeCAD Geometry to Sketch and setting internal id
@singledispatchmethod
def _freecad_add_to_sketch(self,
                           geometry: FreeCADGeometry,
                           sketch: FreeCADSketch,
                           construction: bool) -> SketchElementID:
    """Adds the geometry to the FreeCAD sketch and returns its unique pancad
    derived id. Updates the internal FreeCADMap's id map to include the new
    geometry and any sub geometry.
    """
    raise TypeError(f"Unsupported pancad element type: {geometry}")

@_freecad_add_to_sketch.register
def _ellipse(self,
             ellipse: FreeCADEllipse,
             sketch: FreeCADSketch,
             construction:bool) -> SketchElementID:
    initial_index = len(sketch.Geometry)
    sketch.addGeometry(ellipse, construction)
    sketch.exposeInternalGeometry(initial_index)
    for index in range(initial_index, initial_index + 4):
        geometry_id = (sketch.ID, ListName.GEOMETRY, index)
        self._id_map[geometry_id] = sketch.Geometry[index]
    # Returns the id of the ellipse element, not the sub elements
    return (sketch.ID, ListName.GEOMETRY, initial_index)

@_freecad_add_to_sketch.register
def _one_to_one_cases(self,
                      geometry: (FreeCADLineSegment
                                 | FreeCADCircle
                                 | FreeCADCircularArc),
                      sketch: FreeCADSketch,
                      construction: bool) -> SketchElementID:
    index = len(sketch.Geometry)
    sketch.addGeometry(geometry, construction)
    geometry_id = (sketch.ID, ListName.GEOMETRY, index)
    self._id_map[geometry_id] = geometry
    return geometry_id

################################################################################
# pancad ---> FreeCAD Constraints
################################################################################

def get_constraint_type_from_pancad(constraint: AbstractConstraint) -> CT:
    type_map = {
        SC.ANGLE: CT.ANGLE,
        SC.DISTANCE: CT.DISTANCE,
        SC.DISTANCE_HORIZONTAL: CT.DISTANCE_X,
        SC.DISTANCE_VERTICAL: CT.DISTANCE_Y,
        SC.DISTANCE_DIAMETER: CT.DIAMETER,
        SC.DISTANCE_RADIUS: CT.RADIUS,
        SC.EQUAL: CT.EQUAL,
        SC.HORIZONTAL: CT.HORIZONTAL,
        SC.PARALLEL: CT.PARALLEL,
        SC.PERPENDICULAR: CT.PERPENDICULAR,
        SC.VERTICAL: CT.VERTICAL,
    }
    if constraint.type_name in type_map: # One-to-one checks
        return type_map[constraint.type_name]
    if constraint.type_name == SC.TANGENT:
        raise NotImplementedError("Tangent constraints aren't available yet.",
                                  constraint)

    geometries = constraint.get_geometry()
    if constraint.type_name == SC.COINCIDENT:
        if all(isinstance(g, Point) for g in geometries):
            return CT.COINCIDENT
        if any(isinstance(g, Point) for g in geometries):
            return CT.POINT_ON_OBJECT
        return CT.TANGENT
    msg = f"Unrecognized constraint type '{constraint.__class__}'"
    raise TypeError(msg, constraint)

def new_constraint_from_pancad(constraint: AbstractConstraint,
                               document: FreeCADDocument,
                               uid_map: dict[str, FreeCADUID]) -> FreeCADConstraint:
    """Creates a new FreeCAD Constraint from a pancad constraint and adds it to
    the provided uid_map.
    """
    constraints_input_map = { 
        # If present, the integer is the number of points in the references.
        CT.EQUAL: "indexes_only",
        CT.PARALLEL: "indexes_only",
        CT.PERPENDICULAR: "indexes_only",
        CT.COINCIDENT: "original_order",
        CT.ANGLE: "quadrant_order",
        CT.POINT_ON_OBJECT: "points_first",
        (CT.TANGENT, 0): "indexes_only",
        (CT.TANGENT, 1): "points_first",
        (CT.TANGENT, 2): "original_order",
        (CT.DISTANCE, 0): "bugged_distance",
        (CT.DISTANCE_X, 0): "bugged_distance",
        (CT.DISTANCE_Y, 0): "bugged_distance",
        (CT.DISTANCE, 1): "points_first",
        (CT.DISTANCE_X, 1): "points_first",
        (CT.DISTANCE_Y, 1): "points_first",
        (CT.DISTANCE, 2): "original_order",
        (CT.DISTANCE_X, 2): "original_order",
        (CT.DISTANCE_Y, 2): "original_order",
    }
    fc_sketch_uid = uid_map[constraint.system.feature.uid]

    # TODO: Add a check for whether there are point-to-point tangents
    refs = []
    for geo in constraint.get_geometry():
        geo_ref = get_constraint_pair_from_pancad(geo, document, uid_map)
        refs.append(geo_ref)

    if len(refs) == 3:
        msg = f"Unsupported type with 3 geometries '{constraint.__class__}'"
        raise TypeError(msg, constraint)

    type_ = get_constraint_type_from_pancad(constraint)
    no_points = [r.is_point for r in refs].count(True)
    if len(refs) == 1:
        input_type = "indexes_only"
    elif type_ in constraints_input_map:
        input_type = constraints_input_map[type_]
    elif (type_, no_points) in constraints_input_map:
        input_type = constraints_input_map[type_, no_points]
    else:
        msg = ("Unexpected constraint type and points combination:"
              f" '{constraint.__class__}', num points: {no_points}")
        raise TypeError(msg, constraint)

    constraint_inputs = [type_]
    match input_type:
        case "indexes_only":
            constraint_inputs.extend(r.index for r in refs)
        case "original_order":
            constraint_inputs.extend(i for r in refs for i in r.pair)
        case "points_first":
            sorted_refs = sorted(refs, key=lambda r: int(r.is_point),
                                 reverse=True)
            first, second = sorted_refs
            constraint_inputs.extend([first.index, first.part, second.index])
        case "bugged_distance":
            first, second = refs
            constraint_inputs.extend([first.index, ESP.START, second.index])
        case "quadrant_order":
            first, second = refs
            quadrant_map = {
                1: (first.index, ESP.START, second.index, ESP.START),
                2: (second.index, ESP.START, first.index, ESP.END),
                3: (first.index, ESP.END, second.index, ESP.START),
                4: (second.index, ESP.START, first.index, ESP.START),
            }
            constraint_inputs.extend(quadrant_map[constraint.quadrant])
        case _:
            raise ValueError(f"Unexpected input type '{input_type}'", constraint)

    # Add value if available from pancad constraint for distance, etc.
    pc_value = getattr(constraint, "value", None)
    if pc_value is not None:
        unit_map = {"degrees": "deg"}
        unit = unit_map.setdefault(constraint.unit, constraint.unit)
        constraint_inputs.append(App.Units.Quantity(f"{pc_value} {unit}"))
    return Sketcher.Constraint(*constraint_inputs)

def get_constraint_pair_from_pancad(geometry: AbstractGeometry,
                                    document: FreeCADDocument,
                                    uid_map: dict[str, FreeCADUID]
                                    ) -> FreeCADConstraintGeoRef:
    """Finds the equivalent constraint index and edge sub part to constrain the
    pancad equivalent geometry in FreeCAD.
    """
    # The FreeCAD UID is mapped directly to the geometry or the parent geometry.
    # Get the geometry uid and the api geometry element.
    if geometry.uid in uid_map:
        fc_geo_uid = uid_map[geometry.uid]
    else:
        try:
            fc_geo_uid = uid_map[geometry.parent.uid]
        except KeyError as exc:
            msg = "Neither the geometry or parent geometry is in the uid_map"
            raise LookupError(msg, geometry) from exc
    fc_geo = api_utils.get_by_uid(fc_geo_uid, document)
    geo_type = api_utils.get_geometry_type(fc_geo)

    # Get the sub part corresponding to the geometry and its parent.
    if geo_type == "GeomPoint":
        sub_part_key = (geometry.self_reference, geo_type)
    elif getattr(geometry, "is_clockwise", False):
        sub_part_key = (geometry.self_reference, "clockwise")
    else:
        sub_part_key = geometry.self_reference
    sub_part_map = {
        CR.CORE: ESP.EDGE,
        CR.ORIGIN: ESP.START, # Sketch Origin is at start of x-axis.
        CR.X_MIN: ESP.START,
        CR.Y_MIN: ESP.START,
        CR.X_MAX: ESP.END,
        CR.Y_MAX: ESP.END,
        CR.X: ESP.EDGE, # Either sketch or ellipse x-axis.
        CR.Y: ESP.EDGE, # Either sketch or ellipse y-axis.
        CR.CENTER: ESP.CENTER,
        CR.START: ESP.START,
        CR.END: ESP.END,
        # Standalone Points are always START.
        (CR.CORE, "GeomPoint"): ESP.START,
        # All FreeCAD arcs are counterclockwise. Clockwise arcs must be reversed
        (CR.START, "clockwise"): ESP.END,
        (CR.END, "clockwise"): ESP.START,
    }
    ref_index = api_utils.get_reference_index_by_uid(fc_geo_uid, document)
    sub_part = sub_part_map[sub_part_key]
    return FreeCADConstraintGeoRef(ref_index, sub_part, geo_type)

################################################################################
# FreeCAD ---> pancad Features
################################################################################

def _freecad_to_pancad_feature(self,
                               feature: FreeCADFeature) -> AbstractFeature:
    """Generates a contextless pancad feature equivalent to the FreeCAD feature.
    """
    match feature.TypeId:
        # Poor man's singledispatchmethod using the FreeCAD TypeId
        case ObjectType.BODY:
            pancad_feature = _ftpf_container(self, feature)
        case ObjectType.SKETCH:
            pancad_feature = _ftpf_sketch(self, feature)
        case ObjectType.PAD:
            pancad_feature = _ftpf_extrude(self, feature)
        case ObjectType.ORIGIN:
            pancad_feature = _ftpf_coordinate_system(self, feature)
        case _:
            raise TypeError(f"Unrecognized TypeId '{feature.TypeId}'")

    # Eliminate duplicate parents
    parent_list = list(set(feature.Parents))
    if len(parent_list) == 1:
        # Add pancad geometry to its context
        parent, _ = parent_list[0]
        pancad_context, _ = self._freecad_to_pancad[parent.ID]
        pancad_context.add_feature(pancad_feature)
    elif not parent_list and isinstance(pancad_feature, FeatureContainer):
        # Found the top level element, can only have one right now
        self._part_file.container = pancad_feature
    elif not parent_list:
        raise ValueError("Elements with no parents are expected to be"
                         " PartFile container and expected to be"
                         " FeatureContainers, got: "
                         f" {pancad_feature.__class__}")
    else:
        raise ValueError("Unknown situation where FreeCAD object has two"
                         " or more unique parents! Please make a github"
                         " issue so it can be supported.")
    return pancad_feature

# ABBREVIATION
# ftpf = freecad_to_pancad_feature
def _ftpf_container(self, body: FreeCADBody) -> FeatureContainer:
    self._id_map[body.ID] = body
    return FeatureContainer(name=body.Label)

def _ftpf_coordinate_system(self, origin: FreeCADOrigin) -> FeatureContainer:
    if len(origin.Parents) > 1:
        raise ValueError("Unknown situation where FreeCAD object has"
                         " two or more unique parents! Please make a"
                         " github issue so it can be supported.")
    self._id_map[origin.ID] = origin
    for subfeature in origin.OriginFeatures:
        self._id_map[subfeature.ID] = subfeature
    body, _ = origin.Parents[0]
    location = tuple(body.Placement.Base)
    components = body.Placement.Rotation.Q
    components =(components[-1],) + components[0:3]
    quat = np.quaternion(*components)
    return CoordinateSystem.from_quaternion(location, quat, name=origin.Label)

def _ftpf_extrude(self, pad: FreeCADPad) -> Extrude:
    self._id_map[pad.ID] = pad
    freecad_profile, _ = pad.Profile
    profile, _ = self._freecad_to_pancad[freecad_profile.ID]
    feature_type = PadType(pad.Type).get_feature_type(pad.Midplane,
                                                      pad.Reversed)
    unit = pad.Length.toStr().split(" ")[-1]
    settings = ExtrudeSettings(feature_type,
                               pad.Length.Value, pad.Length2.Value,
                               unit, pad.Label)
    # Up to face/feature not handled in the return, future work
    return Extrude(profile, settings)

def _ftpf_sketch(self, freecad_sketch: FreeCADSketch) -> Sketch:
    self._id_map[freecad_sketch.ID] = freecad_sketch
    support, _ = freecad_sketch.AttachmentSupport[0]
    coordinate_system, reference = self.get_pancad(support.ID)
    sketch = Sketch(coordinate_system=coordinate_system,
                    plane_reference=reference,
                    name=freecad_sketch.Label)
    # Ensure that all internal geometry has been added to Geometry
    for i, freecad_geometry in enumerate(freecad_sketch.Geometry):
        try:
            freecad_sketch.exposeInternalGeometry(i)
        except ValueError:
            # FreeCAD doesn't provide a way to check whether something has
            # internal geometry, so this function can be run on each item and
            # then pancad can just ignore the errors
            pass

    # Actually translate geometry
    for i, freecad_geometry in enumerate(freecad_sketch.Geometry):
        geometry = self._freecad_to_pancad_geometry(freecad_geometry)
        sketch.add_geometry(geometry, freecad_sketch.getConstruction(i))
        geometry_id = (freecad_sketch.ID, ListName.GEOMETRY, i)
        self._id_map[geometry_id] = freecad_geometry
        self._pancad_to_freecad[geometry.uid] = (geometry, geometry_id)
        self._freecad_to_pancad[geometry_id] = (geometry, CR.CORE)
    return sketch

################################################################################
# FreeCAD ---> pancad Geometry
################################################################################

@singledispatchmethod
@staticmethod
def _freecad_to_pancad_geometry(geometry: FreeCADGeometry) -> AbstractGeometry:
    """Returns pancad geometry from FreeCAD geometry elements."""
    raise TypeError(f"Unsupported FreeCAD element type: {geometry}")

@_freecad_to_pancad_geometry.register
@staticmethod
def _line_segment(line_segment: FreeCADLineSegment) -> LineSegment:
    return LineSegment(line_segment.StartPoint[0:2],
                       line_segment.EndPoint[0:2])

@_freecad_to_pancad_geometry.register
@staticmethod
def _circle(circle: FreeCADCircle) -> Circle:
    return Circle(circle.Center[0:2], circle.Radius)

@_freecad_to_pancad_geometry.register
@staticmethod
def _circular_arc(arc: FreeCADCircularArc) -> CircularArc:
    center = np.array(arc.Center[0:2])
    start_vector = np.array(arc.StartPoint[0:2]) - center
    end_vector = np.array(arc.EndPoint[0:2]) - center
    return CircularArc(center, arc.Radius, start_vector, end_vector, False)

@_freecad_to_pancad_geometry.register
@staticmethod
def _point(point: FreeCADPoint) -> Point:
    return Point(point.X, point.Y)

@_freecad_to_pancad_geometry.register
@staticmethod
def _ellipse(ellipse: FreeCADEllipse) -> Ellipse:
    return Ellipse.from_angle(ellipse.Center[0:2],
                              ellipse.MajorRadius,
                              ellipse.MinorRadius,
                              ellipse.AngleXU)