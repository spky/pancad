from pathlib import Path
from pprint import pp
from unittest import TestCase, skip

from tests import sample_freecad

from itertools import islice

from pancad.cad.freecad.direct_reading import Document, read_properties
from pancad.cad.freecad import xml_appearance
from pancad.cad.freecad.constants import XMLTag, SubFile, XMLAttr

def batched(iterable, n, *, strict=False):
    # batched('ABCDEFG', 2) → AB CD EF G
    if n < 1:
        raise ValueError('n must be at least one')
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        if strict and len(batch) != n:
            raise ValueError('batched(): incomplete batch')
        yield batch

def print_array_files(document: Document):
    INCLUDE = [
        # SubFile.POINT_COLOR_ARRAY,
        # SubFile.LINE_COLOR_ARRAY,
        SubFile.SHAPE_APPEARANCE,
    ]
    included = {name: info for name, info in document.members.items()
                if any(name.startswith(i) for i in INCLUDE)}
    
    for name, info in included.items():
        if name not in ["ShapeAppearance", "ShapeAppearance1"]: continue
        print(name)
        with document.archive.open(info, "r") as file:
            data = bytes(file.read())
        
        if tuple(data[0:4]) != (1, 0, 0, 0):
            raise ValueError("Unknown start to file!")
        
        # print("  Length:", len(data))
        # print("  1st 4 Bytes:", data[0:4])
        
        data = data[4:]
        color_data = data[:36]
        list_data = list(data[:36])
        ambient = tuple(list_data.pop(0) for i in range(0, 4))
        diffuse = tuple(list_data.pop(0) for i in range(0, 4))
        specular = tuple(list_data.pop(0) for i in range(0, 4))
        print("Ambient: ", ambient)
        print("Diffuse: ", diffuse)
        print("Specular: ", specular)
        print()
        for color in batched(color_data, n=4):
            print(color)
        
        print("  Color Data Len:", len(color_data))
        print("  Color Data", color_data)
        print("  Color Data", list(color_data))
        data = data[36:]
        if data:
            uid = data.decode()
            print("Uuid:", uid)
            # print("Uuid:", list(data))
        # print("Length of Data Left: ", len(data))
        # print("  ", color_data)
        # data = data[36:]
        # print("  Data Length:", len(data)) 
        # if len(data) > 36:
            # uid = data[-36:]
            # print("  uid: ", uid)
        # color_data = data[3:40]
        # print("  col: ", color_data)
        # print("  col: ", list(color_data))

def print_shape_appearances(document: Document):
    for attrs, _, props in document.view_provider_data:
        attr_dict = {name: value for name, *_, value in props}
        if "ShapeAppearance" not in attr_dict:
            continue
        
        filename = attr_dict["ShapeAppearance"]["file"]
        parsed = xml_appearance.read_shape_appearance(document.archive, filename)
        pp(parsed)

def print_point_color_arrays(document: Document):
    for attrs, _, props in document.view_provider_data:
        attr_dict = {name: value for name, *_, value in props}
        if "PointColorArray" not in attr_dict:
            continue
        filename = attr_dict["PointColorArray"]
        parsed = xml_appearance.read_color_array(document.archive, filename)
        pp(parsed)

class Cube1x1x1(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1.FCStd"
    
    def test_init(self):
        print()
        test = Document(self.path)
        # print()
        # pp(test.members)
        # print(test.expand)
        # for provider in test.view_provider_data:
            # print(provider[0])
            # for property_ in provider[2]:
                # if property_[3] is None:
                    # pp(property_)
        # pp(test.view_provider_data)
        # pp(test.members)
        # print_array_files(test)
        # pp(read_shape_appearance(test.archive, "ShapeAppearance"))
        # print_shape_appearances(test)
        print_point_color_arrays(test)
        
        # with test.archive.open(test.members[SubFile.LINE_COLOR_ARRAY], "r") as file:
            # data = file.read()
        # print(data)
        # print(list(data))
    
    @skip
    def test_read_sketch_properties(self):
        test = Document(self.path)
        sketch_element = test.objects[2674][XMLTag.OBJECT_DATA]
        properties = sketch_element.find(XMLTag.PROPERTIES)
        result = read_properties(sketch_element)
        pp(result)
        # empty = [r for r in result if r[3] is None]
        # print()
        # pp(empty)

class Cube1x1x1Colored(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1_colored.FCStd"
    
    def test_init(self):
        print()
        test = Document(self.path)
        # print_array_files(test)
        print_point_color_arrays(test)
        # print_shape_appearances(test)

@skip
class Empty(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "empty.FCStd"
    
    def test_init(self):
        test = Document(self.path)
        # print("\nProperties")
        # pp(test.properties)
        # print("\nPrivate Properties")
        # pp(test.private)
        # print(test.expand)

@skip
class OnlyOneSketch(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "only_one_sketch.FCStd"
    
    def test_init(self):
        test = Document(self.path)
        print_array_files(test)
        
