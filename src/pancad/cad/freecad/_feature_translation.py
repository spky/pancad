"""A module providing methods for FreeCADMap to translate features to and from
FreeCAD.
"""
from __future__ import annotations

from collections import deque
from functools import singledispatch
from typing import TYPE_CHECKING
from math import pi, cos, sin
import warnings
import logging

import numpy as np

from pancad.abstract import AbstractFeature, AbstractGeometry
from pancad.constants import (
    ConstraintReference as CR,
    SketchConstraint as SC,
    FeatureType as FT,
)
from pancad.constraints._generator import make_constraint
from pancad.geometry.circle import Circle
from pancad.geometry.circular_arc import CircularArc
from pancad.geometry.ellipse import Ellipse
from pancad.geometry.extrude import Extrude, ExtrudeSettings
from pancad.geometry.feature_container import FeatureContainer
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.point import Point
from pancad.geometry.sketch import Sketch
from pancad.filetypes.part_file import PartFile

from pancad.cad.freecad import api_utils
from pancad.cad.freecad.api_utils import FreeCADConstraintGeoRef
from pancad.cad.freecad import xml_utils
from pancad.cad.freecad.xml_utils import FreeCADUID
from pancad.cad.freecad.constants import (
    ConstraintType as CT,
    ConstraintSubPart as CSP,
    InternalGeometryType as IGT,
    PadType as PT,
)
from pancad.cad.freecad._application_types import (
    FreeCADBody,
    FreeCADCircle,
    FreeCADCircularArc,
    FreeCADEllipse,
    FreeCADFeature,
    FreeCADGeometry,
    FreeCADLineSegment,
    FreeCADPad,
    FreeCADPoint,
    FreeCADSketch,
)

from pancad.cad.freecad.api import freecad, freecad_sketcher, freecad_part

if TYPE_CHECKING:
    from typing import Literal
    from collections.abc import Container, Collection

    from pancad.abstract import AbstractConstraint, PancadThing
    from pancad.geometry.coordinate_system import Pose
    from pancad.cad.freecad._application_types import (
        FreeCADDocument, FreeCADPlacement, FreeCADConstraint,
    )
    from pancad.cad.freecad.read_xml import (
        FCStd,
        FreeCADConstraintXML,
        FreeCADDocumentXML,
        FreeCADGeometryXML,
        FreeCADLink,
        FreeCADObjectXML,
        ConstraintGeoRef,
    )

logger = logging.getLogger(__name__)

################################################################################
# pancad ---> FreeCAD Geometry
################################################################################
def new_placement_from_pose(pose: Pose) -> FreeCADPlacement:
    """Creates a FreeCADPlacement from a pancad Pose."""
    placement = freecad.Placement()
    placement.Base = tuple(pose.origin)
    quat = pose.coordinate_system.get_quaternion()
    # FreeCAD Quaternions have their real component at the end.
    placement.Rotation.Q = (quat.x, quat.y, quat.z, quat.w)
    return placement

################################################################################
# FreeCAD ---> pancad Features
################################################################################
def new_part_from_document(file: FCStd) -> PartFile:
    """Returns a new PartFile from a FreeCAD FCStd file"""
    part = PartFile(file.metadata.label)
    object_uids = deque(file.get_topo_uids())
    top = file.get_by_uid(object_uids.popleft())
    if top.type_ != "PartDesign::Body":
        msg = (f"Incompatible with PartFile: FCStd starts with {top.type_},"
               " expected a PartDesign::Body.")
        raise ValueError(msg)
    uid_map = {file.uid: part}
    map_container_from_freecad(top, part, uid_map)
    while object_uids:
        uid = object_uids.popleft()
        if uid in uid_map:
            continue
        obj = file.get_by_uid(uid)
        try:
            new_feature_from_freecad(obj, uid_map)
        except (ValueError, NotImplementedError) as exc:
            msg = (f"On FreeCAD Object type {obj.type_} named '{obj.name}',"
                   f" labeled '{obj.label}'")
            exc.add_note(msg)
            raise
    return part

def new_feature_from_freecad(feature: FreeCADObjectXML,
                             uid_map: dict[FreeCADUID, PancadThing]
                             ) -> AbstractFeature:
    """Creates a new pancad feature from a FreeCAD one and adds it to the
    PartFile.
    """
    type_to_func = {
        "Sketcher::SketchObject": _sketch_from_freecad,
        "PartDesign::Pad": _extrude_from_freecad,
    }
    try:
        func = type_to_func[feature.type_]
    except KeyError as exc:
        msg = f"Object translation for {feature.type_} has not been implemented."
        raise NotImplementedError(msg) from exc
    return func(feature, uid_map)

def _sketch_from_freecad(feature: FreeCADObjectXML,
                         uid_map: dict[FreeCADUID, PancadThing]
                         ) -> Sketch:
    new_uids = uid_map.copy() # Copy so it's still possible to error out.
    sketch = Sketch(name=feature.get_property("Label").value)
    new_uids[feature.uid] = sketch

    # Find the pancad equivalent support from FreeCAD objects
    fc_plane = _get_sketch_support(feature)
    body = _get_origin_feature_body(fc_plane, new_uids)
    container = uid_map[body.uid]
    plane = uid_map[fc_plane.uid]

    # Add sketch to FeatureContainer
    container.feature_system.features.append(sketch)
    if plane.self_reference != CR.XY:
        msg = ("Sketches not set on the Coordinate system's XY plane are"
               f" not yet supported for translation. On {plane.self_reference}")
        raise NotImplementedError(msg)
    feature_constraints = [
        make_constraint(SC.ALIGN_AXES,
                        container.feature_system.coordinate_system,
                        sketch.pose.coordinate_system),
    ]
    container.feature_system.constraints.extend(feature_constraints)
    _add_sketch_geometry_from_freecad(feature, sketch, new_uids)
    _add_sketch_constraints_from_freecad(feature, sketch, new_uids)
    uid_map.update(new_uids)
    return sketch

def _add_sketch_geometry_from_freecad(fc_sketch: FreeCADObjectXML,
                                      pc_sketch: Sketch,
                                      uid_map: dict[FreeCADUID, PancadThing]
                                      ) -> None:
    """Creates pancad sketch geometry from FreeCAD geometry and adds it to the
    uid_map.
    """
    fc_ext_geo = fc_sketch.get_property("ExternalGeo").value
    if len(fc_ext_geo) > 2:
        msg = "Sketches with external references are not yet supported"
        raise NotImplementedError(msg)
    for i in range(0, 2): # Map 2D Coordinate System
        uid_map[fc_ext_geo[i].uid] = pc_sketch.geometry_system.coordinate_system
    for fc_geo in fc_sketch.get_property("Geometry").value:
        pc_geo = geometry_from_freecad(fc_geo)
        uid_map[fc_geo.uid] = pc_geo
        pc_sketch.geometry_system.geometry.append(pc_geo)

def _add_sketch_constraints_from_freecad(fc_sketch: FreeCADObjectXML,
                                         pc_sketch: Sketch,
                                         uid_map: dict[FreeCADUID, PancadThing]
                                         ) -> None:
    """Creates pancad sketch constraints from FreeCAD constraints and adds it to
    the uid_map.
    """
    for fc_con in fc_sketch.get_property("Constraints").value:
        if fc_con.internal_type != IGT.NOT_INTERNAL:
            # Internal Alignment constraints are not required by pancad.
            continue
        pc_con = constraint_from_freecad(fc_con, uid_map)
        uid_map[fc_con.uid] = pc_con
        pc_sketch.geometry_system.constraints.append(pc_con)

def _get_sketch_support(sketch: FreeCADObjectXML) -> FreeCADObjectXML:
    """Returns the plane supporting the sketch in FreeCAD."""
    support = sketch.get_property("AttachmentSupport").value
    if len(support) != 1:
        msg = "Sketches with more than one support link are not implemented"
        raise NotImplementedError(msg)
    support = support.pop()
    return sketch.document.get_object(support.name)

def _get_origin_feature_body(feature: FreeCADObjectXML,
                             uid_map: dict[FreeCADUID, PancadThing]
                             ) -> FreeCADObjectXML:
    """Returns the body containing the origin subfeature."""
    origin = None
    for obj in get_typed_objects("App::Origin", feature.document, uid_map):
        if in_links(feature, obj.get_property("OriginFeatures").value):
            origin = obj
            break
    if origin is None:
        msg = f"No Origin for feature {feature.type_} '{feature.name}' found"
        raise ValueError(msg)
    for obj in get_typed_objects("PartDesign::Body", feature.document, uid_map):
        if obj.get_property("Origin").value.name == origin.name:
            return obj
    raise ValueError(f"No Body found with origin '{origin.name}'")

def _extrude_from_freecad(feature: FreeCADObjectXML,
                          uid_map: dict[FreeCADUID, PancadThing]
                          ) -> Extrude:
    # Determine the equivalent FeatureType.
    pc_type = _get_extrude_type_from_freecad(feature)
    settings_params = {"type_": pc_type, "unit": "mm"} # FreeCAD always uses mm
    prop_map = {
        "length": "Length", "opposite_length": "Length2",
        "taper_angle": "TaperAngle", "opposite_taper_angle": "TaperAngle2"
    }
    for pc_prop, fc_prop in prop_map.items():
        settings_params[pc_prop] = feature.get_property(fc_prop).value
    settings = ExtrudeSettings(**settings_params)
    profile_link = feature.get_property("Profile").value
    if len(profile_link) != 1:
        msg = ("Pads without exactly 1 profile link are not yet supported."
               f" Found {len(profile_link)} links in Pad '{feature.label}'")
        raise NotImplementedError(msg)
    profile_link = profile_link.pop()
    if profile_link.sub is not None:
        msg = f"Unsupported non-None sub link in Pad profile: {profile_link}"
        raise NotImplementedError(msg)
    fc_profile = feature.document.get_object(profile_link.name)
    pc_profile = uid_map[fc_profile.uid]
    extrude = Extrude(pc_profile, settings, name=feature.label)
    pc_profile.system.features.append(extrude)
    return extrude

def _get_extrude_type_from_freecad(extrude: FreeCADObjectXML) -> FT:
    """Returns the equivalent pancad extrude type from a freecad pad type."""
    reversible = {PT.LENGTH, PT.TWO_LENGTHS}
    midplanable = {PT.LENGTH}
    fc_type = PT(extrude.get_property("Type").value)
    key = [fc_type]
    if fc_type in reversible:
        key.append(extrude.get_property("Reversed").value)
    if fc_type in midplanable:
        key.append(extrude.get_property("Midplane").value)
    type_map = {
        # PadType, is_reversed, is_midplane
        (PT.LENGTH, False, False): FT.DIMENSION,
        (PT.LENGTH, True, False): FT.ANTI_DIMENSION,
        (PT.LENGTH, True, True): FT.SYMMETRIC,
        (PT.LENGTH, False, True): FT.SYMMETRIC,
        # PadType, is_reversed
        (PT.TWO_LENGTHS, False): FT.TWO_DIMENSIONS,
        (PT.TWO_LENGTHS, True): FT.ANTI_TWO_DIMENSIONS,
    }
    try:
        return type_map[tuple(key)]
    except KeyError as exc:
        msg = f"No equivalent type found for freecad pad type {fc_type.name}"
        if fc_type in reversible:
            msg = msg + f", Reversed: {extrude.get_property('Reversed').value}"
        if fc_type in midplanable:
            msg = msg + f", Midplane: {extrude.get_property('Midplane').value}"
        raise ValueError(msg) from exc


def in_links(feature: FreeCADObjectXML, links: Collection[FreeCADLink]) -> bool:
    """Returns whether a FreeCAD Object is in a Collection fo FreeCADLinks"""
    return any(feature.name == link.name for link in links)

def get_typed_objects(types: str | Container[str],
                      doc: FreeCADDocumentXML,
                      uids: Container[FreeCADUID],
                      empty_allowed: bool=False
                      ) -> list[FreeCADObjectXML]:
    """Returns a list of objects with a type from the document and that are also
    in a Container of uids.

    :param type_: A string or a Container of FreeCAD object TypeIds.
    :param doc: A FreeCAD document.
    :param uids: A Container of FreeCADUIDs.
    :param empty_allowed: Whether the list can be empty and valid.
    :raises ValueError: When not_empty is False and there are no objects of the
        type in the document while also having a uid in the uids Container.
    """
    if isinstance(types, str):
        types = {types}
    objects = [o for o in doc.objects if o.type_ in types and o.uid in uids]
    if objects or empty_allowed:
        return objects
    msg = (f"No objects of the types in '{types}' found with a uid in"
           " available uids")
    raise ValueError(msg)

def map_container_from_freecad(feature: FreeCADObjectXML, part: PartFile,
                               uid_map: dict[FreeCADUID, PancadThing]
                               ) -> None:
    """Maps the PartFile's top level container to a FreeCAD Body."""
    container = part.container
    new_uids = {feature.uid: container}

    origin = feature.document.get_object(
        feature.get_property("Origin").value.name
    )
    _map_origin_features_from_freecad(origin, container, new_uids)
    placement = feature.get_property("Placement").value
    container.pose.rotate(placement.quat)
    container.pose.move_to_point(placement.location)
    uid_map.update(new_uids)

def _map_origin_features_from_freecad(origin: FreeCADObjectXML,
                                      container: FeatureContainer,
                                      uid_map: dict[FreeCADUID, PancadThing]
                                      ) -> None:
    """Maps the origin and its origin features to a feature container and adds
    them to the uid map.
    """
    map_name_to_feat = {xml_utils.get_map_name(origin.name): origin}
    for sub_name in origin.get_property("OriginFeatures").value:
        sub_feat = origin.document.get_object(sub_name.name)
        map_name_to_feat[xml_utils.get_map_name(sub_name.name)] = sub_feat

    name_map = {"Origin": CR.CS,
                "X_Axis": CR.X, "Y_Axis": CR.Y, "Z_Axis": CR.Z,
                "XY_Plane": CR.XY, "XZ_Plane": CR.XZ, "YZ_Plane": CR.YZ}
    for map_name, reference in name_map.items():
        try:
            sub_feat = map_name_to_feat[map_name]
        except KeyError as exc:
            msg = f"No '{map_name}' found in Origin '{origin.name}'"
            raise ValueError(msg) from exc
        uid_map[sub_feat.uid] = container.feature_system.get_reference(reference)


################################################################################
# pancad ---> FreeCAD Features
################################################################################
def new_document_from_part(part: PartFile) -> FreeCADDocument:
    """Creates a new FreeCADDocument from a PartFile"""
    document = freecad.newDocument()
    api_utils.relabel_object(document, part.name)

    uid_map = {part.uid: api_utils.read_document_uid(document)}
    new_feature_from_pancad(part.container, document, uid_map)
    return document

def new_feature_from_pancad(feature: AbstractFeature,
                            document: FreeCADDocument,
                            uid_map: dict[str, FreeCADUID]) -> FreeCADFeature:
    """Creates a new FreeCAD Feature from a pancad feature and adds it to the
    provided uid_map.
    """
    funcs = [
        (FeatureContainer, _new_body_from_container),
        (Sketch, _new_sketch_from_pancad_sketch),
        (Extrude, _new_pad_from_pancad_extrude),
    ]
    try:
        feature_func = next(f for f in funcs if isinstance(feature, f[0]))[1]
    except StopIteration as exc:
        msg = f"Unsupported feature type '{feature.__class__}'"
        raise TypeError(msg, feature) from exc
    return feature_func(feature, document, uid_map)

def _new_body_from_container(feature: FeatureContainer,
                             document: FreeCADDocument,
                             uid_map: dict[str, FreeCADUID]) -> FreeCADBody:
    """Adds a new body to the FreeCADDocument from a FeatureContainer"""
    if feature.uid in uid_map:
        msg = "pancad uid of container already in uid map"
        raise ValueError(msg, feature)
    body = document.addObject("PartDesign::Body")
    api_utils.relabel_object(body, feature.name)

    body.Placement = new_placement_from_pose(feature.pose)

    # Map Origin and OriginFeatures to names that can map to container children
    origin_map = {"Coordinate_System": body.Origin}
    origin_map.update(
        {xml_utils.get_map_name(f.Name): f for f in body.Origin.OriginFeatures}
    )
    ref_name_map = {
        CR.CS: "Coordinate_System", CR.ORIGIN: "Coordinate_System",
        # There is no center point on the Origin object, so the origin point is
        # mapped to the Origin where other systems can derive the location.
        CR.X: "X_Axis", CR.Y: "Y_Axis", CR.Z: "Z_Axis",
        CR.XY: "XY_Plane", CR.XZ: "XZ_Plane", CR.YZ: "YZ_Plane",
    }

    new_uids = {}
    system = feature.feature_system
    for reference, map_name in ref_name_map.items():
        pancad_uid = system.children[reference].uid
        if pancad_uid in uid_map:
            msg = "pancad uid of element already in uid map"
            raise ValueError(msg, system.children[reference])
        new_uids[pancad_uid] = api_utils.read_feature_uid(origin_map[map_name],
                                                          document)
    new_uids[feature.uid] = api_utils.read_feature_uid(body, document)
    uid_map.update(new_uids)

    # Moving deeper down into to the subfeatures
    for sub_feature in system.features:
        new_feature_from_pancad(sub_feature, document, uid_map)
    return body

def _new_sketch_from_pancad_sketch(feature: Sketch,
                                   document: FreeCADDocument,
                                   uid_map: dict[str, FreeCADUID]
                                   ) -> FreeCADSketch:
    # Get relevant pancad mapping info
    fc_parent_uid = uid_map[feature.system.feature.uid]
    fc_plane_uid = uid_map[feature.get_support().uid]

    # Add equivalent objects to freecad
    fc_sketch = document.addObject("Sketcher::SketchObject")
    api_utils.relabel_object(fc_sketch, feature.name)
    api_utils.get_by_uid(fc_parent_uid, document).addObject(fc_sketch)
    fc_sketch.AttachmentSupport = api_utils.get_by_uid(fc_plane_uid, document)
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
        new_uid_map_items[pc_geo.uid] = api_utils.read_geometry_uid(
            fc_geo, "ExternalGeo", fc_sketch, document
        )
    new_uid_map_items[feature.uid] = api_utils.read_feature_uid(fc_sketch,
                                                                document)
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

    pad = document.addObject("PartDesign::Pad")
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

    pad.UpToFace = None
    pad.Offset = 0

    fc_profile.Visibility = False
    uid_map[feature.uid] = api_utils.read_feature_uid(pad, document)
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
        new_uid_map_items[pc_geo.uid] = api_utils.read_geometry_uid(
            fc_geo, "Geometry", fc_sketch, document
        )
        if fc_geo.TypeId == "Part::GeomEllipse":
            msg = "Ellipse mapping hasn't been implemented yet. See #235"
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
        fc_cons_uid = api_utils.read_constraint_uid(fc_cons, fc_sketch, document)
        new_uid_map_items[pc_cons.uid] = fc_cons_uid
    uid_map.update(new_uid_map_items)
    return fc_sketch

################################################################################
# pancad ---> FreeCAD Geometry
################################################################################
@singledispatch
def pancad_to_freecad_geometry(geometry: AbstractGeometry) -> FreeCADGeometry:
    """Returns an equivalent FreeCAD geometry element from pancad Geometry."""
    raise TypeError(f"Unsupported pancad element type: {geometry}")

@pancad_to_freecad_geometry.register
def _line_segment(line_segment: LineSegment) -> FreeCADLineSegment:
    start = freecad.Vector(tuple(line_segment.start) + (0,))
    end = freecad.Vector(tuple(line_segment.end) + (0,))
    return freecad_part.LineSegment(start, end)

@pancad_to_freecad_geometry.register
def _ellipse(ellipse: Ellipse) -> FreeCADEllipse:
    major_axis_point = freecad.Vector(tuple(ellipse.major_axis_max) + (0,))
    minor_axis_point = freecad.Vector(tuple(ellipse.minor_axis_max) + (0,))
    center = freecad.Vector(tuple(ellipse.center) + (0,))
    return freecad_part.Ellipse(major_axis_point, minor_axis_point, center)

@pancad_to_freecad_geometry.register
def _circle(circle: Circle) -> FreeCADCircle:
    center = freecad.Vector(tuple(circle.center) + (0,))
    normal = freecad.Vector((0, 0, 1))
    return freecad_part.Circle(center, normal, circle.radius)

@pancad_to_freecad_geometry.register
def _circular_arc(arc: CircularArc) -> FreeCADCircularArc:
    center = freecad.Vector(tuple(arc.center) + (0,))
    normal = freecad.Vector((0, 0, 1))
    circle =  freecad_part.Circle(center, normal, arc.radius)

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
    return freecad_part.ArcOfCircle(circle, start, end)

################################################################################
# pancad ---> FreeCAD Constraints
################################################################################

def get_constraint_type_from_pancad(constraint: AbstractConstraint) -> CT:
    """Returns the equivalent FreeCAD constraint type from pancad constraints"""
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
        msg = "Tangent constraints aren't available for translation yet."
        raise NotImplementedError(msg, constraint)

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
    input_map = {
        # If present, the integer is the number of points in the references.
        CT.ANGLE: "quadrant_order",
        CT.COINCIDENT: "original_order",
        CT.DIAMETER: "indexes_only",
        CT.RADIUS: "indexes_only",
        CT.EQUAL: "indexes_only",
        CT.HORIZONTAL: "indexes_only",
        CT.VERTICAL: "indexes_only",
        CT.PARALLEL: "indexes_only",
        CT.PERPENDICULAR: "indexes_only",
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
    type_ = get_constraint_type_from_pancad(constraint)
    key = _get_constraint_write_key(constraint, document, uid_map)
    try:
        input_type = input_map[key]
    except KeyError as exc:
        msg = f"Unsupported constraint type and/or point count: {key}"
        raise NotImplementedError(msg) from exc

    refs = [get_constraint_pair_from_pancad(g, document, uid_map)
            for g in constraint.get_geometry()]

    indicies = _get_freecad_constraint_indices(
        input_type, refs, getattr(constraint, "quadrant", None)
    )
    pc_value = getattr(constraint, "value", None)
    if pc_value is None:
        return freecad_sketcher.Constraint(type_.human_name, *indicies)
    # Add value if available from pancad constraint for distance, etc.
    unit_map = {"degrees": "deg"}
    unit = unit_map.setdefault(constraint.unit, constraint.unit)
    return freecad_sketcher.Constraint(type_.human_name, *indicies,
                                       freecad.Units.Quantity(f"{pc_value} {unit}"))

def _get_freecad_constraint_indices(
            input_type: Literal["quadrant_order", "original_order",
                                "indexes_only", "points_first",
                                "bugged_distance"],
            refs: list[FreeCADConstraintGeoRef],
            quadrant: Literal[1, 2, 3, 4]=None
        ) -> list[int]:
    """Returns the list of indicies FreeCAD requires for constraint definition.

    :param input_type: A string for the reading type required for the references
    :param refs: The geometry reference pairs read from pancad objects.
    :param quadrant: The quadrant of an angle constraint. Should be None if not
        an angle.
    :raises ValueError: When input_type or quadrant is an unexpected value.
    """
    match input_type:
        case "indexes_only":
            return [r.index for r in refs]
        case "original_order":
            return [i for r in refs for i in r.pair]
        case "points_first":
            sorted_refs = sorted(refs, key=lambda r: int(r.is_point),
                                 reverse=True)
            first, second = sorted_refs
            return [first.index, first.part, second.index]
        case "bugged_distance":
            first, second = refs
            return [first.index, CSP.START, second.index]
        case "quadrant_order":
            first, second = refs
            quadrant_map = {
                1: (first.index, CSP.START, second.index, CSP.START),
                2: (second.index, CSP.START, first.index, CSP.END),
                3: (first.index, CSP.END, second.index, CSP.START),
                4: (second.index, CSP.START, first.index, CSP.START),
            }
            try:
                return quadrant_map[quadrant]
            except KeyError as exc:
                msg = f"Unexpected value for angle quadrant: {quadrant}"
                raise ValueError(msg) from exc
    raise ValueError(f"Unexpected input type '{input_type}'")

def _get_constraint_write_key(constraint: AbstractConstraint,
                              document: FreeCADDocument,
                              uid_map: dict[str, FreeCADUID]
                              ) -> CT | tuple[CT, int]:
    """Returns a key to dispatch how to write the constraint to FreeCAD."""
    # Some constraint types in FreeCAD depend on the # of points in the refs
    point_dependent = {CT.TANGENT, CT.DISTANCE, CT.DISTANCE_X, CT.DISTANCE_Y}
    type_ = get_constraint_type_from_pancad(constraint)
    if type_ in point_dependent:
        refs = []
        for geo in constraint.get_geometry():
            refs.append(get_constraint_pair_from_pancad(geo, document, uid_map))
        return (type_, [r.is_point for r in refs].count(True))
    return type_

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
        CR.CORE: CSP.EDGE,
        CR.ORIGIN: CSP.START, # Sketch Origin is at start of x-axis.
        CR.X_MIN: CSP.START,
        CR.Y_MIN: CSP.START,
        CR.X_MAX: CSP.END,
        CR.Y_MAX: CSP.END,
        CR.X: CSP.EDGE, # Either sketch or ellipse x-axis.
        CR.Y: CSP.EDGE, # Either sketch or ellipse y-axis.
        CR.CENTER: CSP.CENTER,
        CR.START: CSP.START,
        CR.END: CSP.END,
        # Standalone Points are always START.
        (CR.CORE, "GeomPoint"): CSP.START,
        # All FreeCAD arcs are counterclockwise. Clockwise arcs must be reversed
        (CR.START, "clockwise"): CSP.END,
        (CR.END, "clockwise"): CSP.START,
    }
    ref_index = api_utils.get_reference_index_by_uid(fc_geo_uid, document)
    sub_part = sub_part_map[sub_part_key]
    return FreeCADConstraintGeoRef(ref_index, sub_part, geo_type)

################################################################################
# FreeCAD ---> pancad Geometry
################################################################################

def geometry_from_freecad(data: FreeCADGeometryXML) -> AbstractGeometry:
    """Creates a pancad geometry object from a FreeCAD object."""
    tag_funcs = {
        "Part::GeomPoint": _from_freecad_point,
        "Part::GeomLineSegment": _from_freecad_line_segment,
        "Part::GeomArcOfCircle": _from_freecad_circular_arc,
        "Part::GeomCircle": _from_freecad_circle,
        "Part::GeomEllipse": _from_freecad_ellipse,
    }
    try:
        func = tag_funcs[data.type_]
    except KeyError as exc:
        msg = f"Sketch geometry type {data.type_} is not supported yet"
        raise NotImplementedError(msg) from exc
    return func(data)

def _from_freecad_point(data: FreeCADGeometryXML) -> Point:
    return Point(data.geometry.location)

def _from_freecad_line_segment(data: FreeCADGeometryXML) -> LineSegment:
    return LineSegment(data.geometry.start, data.geometry.end)

def _from_freecad_circle(data: FreeCADGeometryXML) -> Circle:
    return Circle(data.geometry.center, data.geometry.radius)

def _from_freecad_circular_arc(data: FreeCADGeometryXML) -> CircularArc:
    geo = data.geometry
    start_vector = (cos(geo.start_angle), sin(geo.start_angle))
    end_vector = (cos(geo.end_angle), sin(geo.end_angle))
    return CircularArc(geo.center, geo.radius, start_vector, end_vector, False)

def _from_freecad_ellipse(data: FreeCADGeometryXML) -> Ellipse:
    geo = data.geometry
    return Ellipse.from_angle(geo.center, geo.major_radius, geo.minor_radius,
                              geo.major_axis_angle)

################################################################################
# FreeCAD ---> pancad Constraints
################################################################################

def constraint_from_freecad(constraint: FreeCADConstraintXML,
                            uid_map: dict[xml_utils.FreeCADUID, PancadThing]
                            ) -> AbstractConstraint:
    """Returns a pancad constraint from a FreeCAD constraint."""
    pc_type = sketch_constraint_from_freecad(constraint)
    pc_geometry = []
    for geo_ref in constraint.get_references():
        pc_ref = reference_from_freecad(geo_ref)
        fc_geo, _ = geo_ref.get_geometry()
        if fc_geo.internal_type != IGT.NOT_INTERNAL:
            fc_geo = fc_geo.get_defining_geometry()
        pc_parent_geo = uid_map[fc_geo.uid]
        pc_geometry.append(pc_parent_geo.get_reference(pc_ref))
    kwargs = {}
    if constraint.type_.requires_value:
        # Only some constraints like distance require a value.
        kwargs["value"] = constraint.value
        if constraint.type_ == CT.ANGLE:
            points_pos = []
            for geo_ref in constraint.get_references():
                fc_geo, part = geo_ref.get_geometry()
                if fc_geo.type_ != "Part::GeomLineSegment":
                    msg = f"FreeCAD angles on {fc_geo.type_} not yet supported"
                    raise NotImplementedError(msg)
                points_pos.append(
                    ((fc_geo.geometry.start, fc_geo.geometry.end), part)
                )
            if len(points_pos) != 2:
                msg = (f"FreeCAD angles constraining {len(points_pos)}"
                       " elements not yet supported")
                raise NotImplementedError(msg)
            kwargs["quadrant"] = xml_utils.read_angle_quadrant(tuple(points_pos))
        else:
            # All FreeCAD value constraints are in mm except Angles. pancad
            # doesn't take a unit parameter for angles, so it shouldn't be
            # included here.
            kwargs["unit"] = "mm"
    return make_constraint(pc_type, *pc_geometry, **kwargs)

def reference_from_freecad(geo_ref: ConstraintGeoRef) -> CR:
    """Returns a pancad ConstraintReference from a FreeCAD constraint geometry
    reference.
    """
    geo, part = geo_ref.get_geometry()
    ref_key = [part, geo.internal_type]
    if geo.internal_type == IGT.NOT_INTERNAL and geo.type_ == "Part::GeomPoint":
        # FreeCAD points are always referred to as Start.
        ref_key.append(geo.type_)
    # Account for FreeCAD x and y axes being in the ExternalGeo list.
    index_map = {-1: "x_axis", -2: "y_axis"}
    if geo_ref.index in index_map:
        ref_key.append(index_map[geo_ref.index])
    ref_map = {
        (CSP.EDGE, IGT.NOT_INTERNAL): CR.CORE,
        (CSP.START, IGT.NOT_INTERNAL, "Part::GeomPoint"): CR.CORE,
        (CSP.START, IGT.NOT_INTERNAL): CR.START,
        (CSP.END, IGT.NOT_INTERNAL): CR.END,
        (CSP.CENTER, IGT.NOT_INTERNAL): CR.CENTER,
        (CSP.EDGE, IGT.NOT_INTERNAL, "x_axis"): CR.X,
        (CSP.START, IGT.NOT_INTERNAL, "x_axis"): CR.ORIGIN,
        (CSP.EDGE, IGT.NOT_INTERNAL, "y_axis"): CR.Y,
        (CSP.EDGE, IGT.ELLIPSE_MAJOR_DIAMETER): CR.MAJOR_AXIS,
        (CSP.START, IGT.ELLIPSE_MAJOR_DIAMETER): CR.X_MIN,
        (CSP.END, IGT.ELLIPSE_MAJOR_DIAMETER): CR.X_MAX,
        (CSP.START, IGT.ELLIPSE_MINOR_DIAMETER): CR.Y_MIN,
        (CSP.END, IGT.ELLIPSE_MINOR_DIAMETER): CR.Y_MAX,
        (CSP.START, IGT.ELLIPSE_FOCUS_1): CR.FOCAL_PLUS,
        (CSP.START, IGT.ELLIPSE_FOCUS_2): CR.FOCAL_MINUS,
    }
    try:
        return ref_map[tuple(ref_key)]
    except KeyError as exc:
        msg = (f"Unrecognized reference combo: Geo Type: '{geo.type_}',"
               f" SubPart: '{part.name}',"
               f" Internal Type: '{geo.internal_type.name}',"
               f" List/Index: {geo_ref.list_name}[{geo_ref.index}]"
               f" Failed Ref Key: {ref_key}")
        raise ValueError(msg) from exc

def sketch_constraint_from_freecad(constraint: FreeCADConstraintXML) -> SC:
    """Returns the equivalent pancad SketchConstraint from a freecad
    constraint.
    """
    type_map = {
        CT.ANGLE: SC.ANGLE,
        CT.DISTANCE: SC.DISTANCE,
        CT.DISTANCE_X: SC.DISTANCE_HORIZONTAL,
        CT.DISTANCE_Y: SC.DISTANCE_VERTICAL,
        CT.DIAMETER: SC.DISTANCE_DIAMETER,
        CT.RADIUS: SC.DISTANCE_RADIUS,
        CT.EQUAL: SC.EQUAL,
        CT.HORIZONTAL: SC.HORIZONTAL,
        CT.PERPENDICULAR: SC.PERPENDICULAR,
        CT.PARALLEL: SC.PARALLEL,
        CT.VERTICAL: SC.VERTICAL,
        CT.COINCIDENT: SC.COINCIDENT,
        CT.POINT_ON_OBJECT: SC.COINCIDENT,
    }
    if constraint.type_ in type_map:
        return type_map[constraint.type_]
    if constraint.type_ == CT.TANGENT:
        geo_pairs = [r.get_geometry() for r in constraint.get_references()]
        if all(g.type_ == "Part::GeomLineSegment" and not p.is_point
               for g, p in geo_pairs):
            return SC.COINCIDENT
        combo = "; ".join([f"{g.type_} {p.name}" for g, p in geo_pairs])
        msg = f"Tangent with geometry combo '{combo}' is not supported yet"
        raise NotImplementedError(msg)
    msg = f"Constraint type '{constraint.type_.name}' is not supported yet"
    raise NotImplementedError(msg)

@singledispatch
def _freecad_to_pancad_geometry(geometry: FreeCADGeometry) -> AbstractGeometry:
    """Returns pancad geometry from FreeCAD geometry elements."""
    raise TypeError(f"Unsupported FreeCAD element type: {geometry}")

@_freecad_to_pancad_geometry.register
def _line_segment(line_segment: FreeCADLineSegment) -> LineSegment:
    return LineSegment(line_segment.StartPoint[0:2],
                       line_segment.EndPoint[0:2])

@_freecad_to_pancad_geometry.register
def _circle(circle: FreeCADCircle) -> Circle:
    return Circle(circle.Center[0:2], circle.Radius)

@_freecad_to_pancad_geometry.register
def _circular_arc(arc: FreeCADCircularArc) -> CircularArc:
    center = np.array(arc.Center[0:2])
    start_vector = np.array(arc.StartPoint[0:2]) - center
    end_vector = np.array(arc.EndPoint[0:2]) - center
    return CircularArc(center, arc.Radius, start_vector, end_vector, False)

@_freecad_to_pancad_geometry.register
def _point(point: FreeCADPoint) -> Point:
    return Point(point.X, point.Y)

@_freecad_to_pancad_geometry.register
def _ellipse(ellipse: FreeCADEllipse) -> Ellipse:
    return Ellipse.from_angle(ellipse.Center[0:2],
                              ellipse.MajorRadius,
                              ellipse.MinorRadius,
                              ellipse.AngleXU)
