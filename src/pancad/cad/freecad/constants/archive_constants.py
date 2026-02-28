"""A module for constant values used inside of FreeCAD Document archives."""

from enum import StrEnum, IntEnum

class UnitSystem(IntEnum):
    """An enumeration matching the UnitSystem options inside FreeCAD files."""
    STANDARD = 0
    MKS = 1
    US_CUSTOMARY = 2
    IMPERIAL_DECIMAL = 3
    BUILDING_EURO = 4
    BUILDING_US = 5
    METRIC_SMALL_PARTS = 6
    IMPERIAL_CIVIL = 7
    FEM = 8
    METER_DECIMAL = 9

    _ignore_ = ["_length_unit_map"]
    _length_unit_map = {
        STANDARD: "mm",
        MKS: "mm",
        US_CUSTOMARY: "in",
        IMPERIAL_DECIMAL: "in",
        BUILDING_EURO: "cm",
        BUILDING_US: "in", # Fractional Inches
        METRIC_SMALL_PARTS: "mm",
        IMPERIAL_CIVIL: "ft",
        FEM: "mm",
        METER_DECIMAL: "m",
    }

    @property
    def length(self) -> str:
        """The unit abbreviation for the default length unit in the system."""
        return self._length_unit_map[self.value]

class ConstraintSubPart(IntEnum):
    """An enumeration of integers corresponding to FreeCAD constraint sub part 
    references.
    """
    EDGE = 0
    """Constraint affects the entire edge."""
    START = 1
    """Constraint affects the start point of an edge."""
    END = 2
    """Constraint affects the end point of an edge."""
    CENTER = 3
    """Constraint affects the center point of an edge."""

    @property
    def name(self) -> str:
        """The name of the constraint subpart reference represented by the 
        integer.
        """
        names = {
            self.EDGE: "Edge",
            self.START: "Start",
            self.END: "End",
            self.CENTER: "Center",
        }
        return names[self.value]

    @property
    def is_point(self) -> bool:
        """Whether the subpart is referencing a point."""
        return self.value > 0

class InternalGeometryType(IntEnum):
    """An enumeration of integers corresponding to FreeCAD 
    InternalAlignmentTypes inside geometry SketchGeometryExtensions. See FreeCAD 
    source code here (as of 2026-02-25): https://github.com/FreeCAD/FreeCAD/blob/34ae16cd01b179eb9e1801591276dbc5a38669b5/src/Mod/Sketcher/App/SketchGeometryExtension.h#L139
    """
    NOT_INTERNAL = 0
    ELLIPSE_MAJOR_DIAMETER = 1
    ELLIPSE_MINOR_DIAMETER = 2
    ELLIPSE_FOCUS_1 = 3
    ELLIPSE_FOCUS_2 = 4
    HYPERBOLA_MAJOR = 5
    HYPERBOLA_MINOR = 6
    HYPERBOLA_FOCUS = 7
    PARABOLA_FOCUS = 8
    B_SPLINE_CONTROL_POINT = 9
    B_SPLINE_KNOT_POINT = 10
    PARABOLA_FOCAL_AXIS = 11

    @property
    def name(self) -> str:
        """The name of the internal geometry type represented by the integer."""
        names = {
            self.NOT_INTERNAL: "Not Internal Geometry",
            self.ELLIPSE_MAJOR_DIAMETER: "Ellipse Major Axis",
            self.ELLIPSE_MINOR_DIAMETER: "Ellipse Minor Axis",
            self.ELLIPSE_FOCUS_1: "Ellipse Positive Focal Point",
            self.ELLIPSE_FOCUS_2: "Ellipse Negative Focal Point",
            self.HYPERBOLA_MAJOR: "Hyperbola Major Axis",
            self.HYPERBOLA_MINOR: "Hyperbola Minor Axis",
            self.HYPERBOLA_FOCUS: "Hyperbola Focus",
            self.PARABOLA_FOCUS: "Parabola Focus",
            self.B_SPLINE_CONTROL_POINT: "B-Spline Control Point",
            self.B_SPLINE_KNOT_POINT: "B-Spline Knot Point",
            self.PARABOLA_FOCAL_AXIS: "Parabola Focal Axis",
        }
        return names[self.value]

class ConstraintTypeNum(IntEnum):
    """An enumeration of integers corresponding to FreeCAD constraint types."""
    COINCIDENT = 1 #
    HORIZONTAL = 2 #
    VERTICAL = 3 #
    PARALLEL = 4 #
    TANGENT = 5
    DISTANCE = 6 #
    DISTANCE_X = 7 #
    DISTANCE_Y = 8 #
    ANGLE = 9 #
    PERPENDICULAR = 10 #
    RADIUS = 11 #
    EQUAL = 12 #
    POINT_ON_OBJECT = 13 #
    SYMMETRIC = 14
    INTERNAL_ALIGNMENT = 15
    SNELLS_LAW = 16
    BLOCK = 17
    DIAMETER = 18 #
    WEIGHT = 19

    @property
    def name(self) -> str:
        """The name of the constraint type represented by the integer."""
        names = {
            self.COINCIDENT: "Coincident",
            self.HORIZONTAL: "Horizontal",
            self.VERTICAL: "Vertical",
            self.PARALLEL: "Parallel",
            self.TANGENT: "Tangent",
            self.DISTANCE: "Distance",
            self.DISTANCE_X: "DistanceX",
            self.DISTANCE_Y: "DistanceY",
            self.ANGLE: "Angle",
            self.PERPENDICULAR: "Perpendicular",
            self.RADIUS: "Radius",
            self.EQUAL: "Equal",
            self.POINT_ON_OBJECT: "PointOnObject",
            self.SYMMETRIC: "Symmetric",
            self.INTERNAL_ALIGNMENT: "InternalAlignment",
            self.SNELLS_LAW: "SnellsLaw",
            self.BLOCK: "Block",
            self.DIAMETER: "Diameter",
            self.WEIGHT: "Weight",
        }
        return names[self.value]

    @property
    def requires_value(self) -> bool:
        """Returns whether the constraint requires a value."""
        valued = {self.DISTANCE, self.DISTANCE_X, self.DISTANCE_Y,
                  self.ANGLE, self.RADIUS, self.DIAMETER}
        return self in valued


class SubFile(StrEnum):
    """An enumeration of file names inside of FreeCAD document."""
    DOCUMENT_XML = "Document.xml"
    """XML file containing geometric information."""
    GUI_DOCUMENT_XML = "GuiDocument.xml"
    """XML file containing GUI specific information"""
    LINE_COLOR_ARRAY = "LineColorArray"
    POINT_COLOR_ARRAY = "PointColorArray"
    """File with unknown purpose. Can have multiple with an incrementing suffix 
    integer
    """
    SHAPE_APPEARANCE = "ShapeAppearance"
    """File with unknown purpose. Can have multiple with an incrementing suffix 
    integer
    """
    SHAPE_BRP = ".Shape.brp"
    """Suffix of file with unknown purpose."""
    SHAPE_MAP_TXT = ".Shape.Map.txt"
    """Suffix of file with unknown purpose. There is one of these per document 
    object.
    """
    STRING_HASHER_TABLE_TXT = "StringHasher.Table.txt"
    """File with unknown purpose."""
    INTERNAL_SHAPE_BRP = ".InternalShape.brp"
    """Suffix of file with unknown purpose. Some document objects have one."""
    ADD_SUB_SHAPE_BRP = ".AddSubShape.brp"
    """Suffix of file with unknwon purpose."""
    ADD_SUB_SHAPE_MAP_TXT = ".AddSubShape.Map.txt"
    """Suffix of file with unknwon purpose."""
    SUPPRESSED_SHAPE_BRP = ".SuppressedShape.brp"
    """Suffix of file with unknwon purpose."""

class Tag(StrEnum):
    """Enumeration of the tags used in FCStd xml files."""
    ARC_OF_CIRCLE = "ArcOfCircle"
    """Element defining the center, orientation, radius, and sweep angles of a 
    sketch circular arc.
    """
    BOOL = "Bool"
    CAMERA = "Camera"
    CIRCLE = "Circle"
    """Element defining the center, orientation, and radius of a sketch circle."""
    COLOR_LIST = "ColorList"
    CONSTRAINT = "Constrain"
    CONSTRAINT_LIST = "ConstraintList"
    CONSTRUCTION = "Construction"
    CUSTOM_ENUM_LIST = "CustomEnumList"
    DOCUMENT = "Document"
    """Top level xml element."""
    DEP = "Dep"
    """Object dependency element."""
    ELLIPSE = "Ellipse"
    """Element defining the center, orientation, and radii of a sketch ellipse."""
    ELEMENT_MAP = "ElementMap"
    ELEMENT_MAP_2 = "ElementMap2"
    EXPAND = "Expand"
    EXPRESSION_ENGINE = "ExpressionEngine"
    EXTENSIONS = "Extensions"
    """Grouping of Extension elements."""
    EXTENSION = "Extension"
    """Element containing information about an extension of an Object."""
    FLOAT = "Float"
    GEOM_POINT = "GeomPoint"
    """Element defining the location of a sketch point."""
    GEOMETRY = "Geometry"
    GEOMETRY_EXTENSION = "GeoExtension"
    GEOMETRY_EXTENSIONS = "GeoExtensions"
    GEOMETRY_LIST = "GeometryList"
    INTEGER = "Integer"
    """Element containing an integer"""
    LINE_SEGMENT = "LineSegment"
    """Element defining the end points of a sketch line segment."""
    LINK = "Link"
    LINK_LIST = "LinkList"
    LINK_SUB = "LinkSub"
    LINK_SUB_LIST = "LinkSubList"
    MAP = "Map"
    MATERIAL_LIST = "MaterialList"
    OBJECT = "Object"
    """An element with information about an object."""
    OBJECT_DATA = "ObjectData"
    """Grouping of Object elements with CAD information."""
    OBJECT_DEPENDENCIES = "ObjectDeps"
    """Grouping of Dep object dependency elements."""
    OBJECTS = "Objects"
    """Grouping of ObjectDeps and Object elements with ids."""
    PART = "Part"
    PROPERTIES = "Properties"
    """Grouping of Property elements."""
    PROPERTY = "Property"
    """Property of an Object. Usually has subelements with further definition."""
    PROPERTY_COLOR = "PropertyColor"
    """Stores a color as an ARGB integer"""
    PROPERTY_MATERIAL = "PropertyMaterial"
    PROPERTY_PLACEMENT = "PropertyPlacement"
    PROPERTY_VECTOR = "PropertyVector"
    PYTHON = "Python"
    STRING_HASHER = "StringHasher"
    """Under top level xml element. Can have incrementing suffix integer."""
    STRING = "String"
    SUB = "Sub"
    """Element containing the selection in an enumeration list"""
    TRANSIENT_PROPERTY = "_Property"
    VIEW_PROVIDER = "ViewProvider"
    VIEW_PROVIDER_DATA = "ViewProviderData"
    VISUAL_LAYER = "VisualLayer"
    VISUAL_LAYER_LIST = "VisualLayerList"
    UUID = "Uuid"
    def __repr__(self):
        return f"'{self.value}'"

class Sketcher(StrEnum):
    """Enumeration of 'Sketcher::' options in FCStd xml files."""
    SKETCH = "Sketcher::SketchObject"
    """type attribute of Sketch Object elements."""
    CONSTRAINT_LIST = "Sketcher::PropertyConstraintList"
    """type attribute of constraint list Property elements."""
    GEOMETRY_EXT = "Sketcher::SketchGeometryExtension"
    """type attribute of sketch GeoExtension elements with sketch specific info 
    stored on them.
    """
    EXTERNAL_EXT = "Sketcher::ExternalGeometryExtension"
    """type attribute of sketch GeoExtension elements. Unknown use."""

class App(StrEnum):
    """Enumeration of 'App::' options in FCStd xml files."""
    ANGLE = "App::PropertyAngle"
    BOOL = "App::PropertyBool"
    COLOR = "App::PropertyColor"
    COLOR_LIST = "App::PropertyColorList"
    ENUM = "App::PropertyEnumeration"
    EXPRESSION_ENGINE = "App::PropertyExpressionEngine"
    FLOAT = "App::PropertyFloat"
    FLOAT_CONSTRAINT = "App::PropertyFloatConstraint"
    LENGTH = "App::PropertyLength"
    LINE = "App::Line"
    LINK = "App::PropertyLink"
    LINK_LIST = "App::PropertyLinkList"
    LINK_SUB = "App::PropertyLinkSub"
    LINK_SUBLIST = "App::PropertyLinkSubList"
    LINK_LIST_HIDDEN = "App::PropertyLinkListHidden"
    MAP = "App::PropertyMap"
    MATERIAL = "App::PropertyMaterial"
    MATERIAL_LIST = "App::PropertyMaterialList"
    ORIGIN = "App::Origin"
    PERCENT = "App::PropertyPercent"
    PLACEMENT = "App::PropertyPlacement"
    PLANE = "App::Plane"
    PRECISION = "App::PropertyPrecision"
    PYTHON_OBJECT = "App::PropertyPythonObject"
    STRING = "App::PropertyString"
    UUID = "App::PropertyUUID"
    VECTOR = "App::PropertyVector"

class Attacher(StrEnum):
    """Enumeration of 'Attacher::' options in FCStd xml files."""
    ATTACH_ENGINE_PLANE = "Attacher::AttachEnginePlane"

class Part(StrEnum):
    """Enumeration of 'Part::' options in FCStd xml files."""
    ARC_OF_CIRCLE = "Part::GeomArcOfCircle"
    CIRCLE = "Part::GeomCircle"
    ELLIPSE = "Part::GeomEllipse"
    LINE_SEGMENT = "Part::GeomLineSegment"
    POINT = "Part::GeomPoint"
    SHAPE = "Part::PropertyPartShape"
    GEOMETRY_LIST = "Part::PropertyGeometryList"

class PartDesign(StrEnum):
    """Enumeration of 'PartDesign::' options in FCStd xml files."""
    BODY = "PartDesign::Body"
    PAD = "PartDesign::Pad"
    REVOLUTION = "PartDesign::Revolution"
    POCKET = "PartDesign::Pocket"
    GROOVE = "PartDesign::Groove"

class Materials(StrEnum):
    """Enumeration of 'Materials::' options in FCStd xml files."""
    MATERIAL = "Materials::PropertyMaterial"

class PropertyType(StrEnum):
    """Enumeration of types that do not have a '::' namespace."""
    BAD_TYPE = "BadType"
    def __repr__(self):
        return self.name

class XMLGeometryType(StrEnum):
    """Enumeration of the supported FCStd Geometry element type attributes"""
    ARC_OF_CIRCLE = "Part::GeomArcOfCircle"
    CIRCLE = "Part::GeomCircle"
    ELLIPSE = "Part::GeomEllipse"
    LINE_SEGMENT = "Part::GeomLineSegment"
    POINT = "Part::GeomPoint"

class Attr(StrEnum):
    """Enumeration of element attribute names in FCStd xml files."""
    COUNT = "count"
    COUNT_CAPITALIZED = "Count"
    ELEMENT_MAP = "ElementMap"
    EXPANDED = "expanded"
    EXTENSIONS = "Extensions"
    FILE = "file"
    HASHER_INDEX = "HasherIndex"
    ID = "id"
    INTERNAL_GEOMETRY_TYPE = "internalGeometryType"
    KEY = "key"
    LINE_PATTERN = "linePattern"
    LINE_WIDTH = "lineWidth"
    LINK_SUB = "sub"
    MIGRATED = "migrated"
    NAME = "name"
    NAME_CAPITALIZED = "Name"
    NEW = "new"
    OBJECT = "obj"
    POSITION_X = "Px"
    POSITION_Y = "Py"
    POSITION_Z = "Pz"
    QUAT_0 = "Q0"
    QUAT_1 = "Q1"
    QUAT_2 = "Q2"
    QUAT_3 = "Q3"
    SCHEMA_VERSION = "SchemaVersion"
    PROGRAM_VERSION = "ProgramVersion"
    FILE_VERSION = "FileVersion"
    SETTINGS = "settings"
    STRING_HASHER = "StringHasher"
    STATUS = "status"
    TRANSIENT_COUNT = "TransientCount"
    TREE_RANK = "treeRank"
    TYPE = "type"
    TYPE_CAPITALIZED = "Type"
    VALUE = "value"
    VALUE_CAPITALIZED = "Value"
    VISIBLE = "visible"
    def __repr__(self):
        return f"'{self.value}'"
