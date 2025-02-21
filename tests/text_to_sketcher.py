# For Windows you must either use \\ or / in the path, using a single \ is problematic
import sys

sys.path.append('../src')


from text2freecad.free_cad_object_wrappers import FreeCADModel


def print_object_attributes(obj):
    print(str(obj.__doc__) + " Properties:")
    for prop in dir(obj):
        print(prop + " | " + str(getattr(obj,prop)))


def print_object_name_and_type(obj):
    print(obj.Name + " | " + obj.TypeId)


WORKING_FOLDER = 'C:/Users/George/Documents/text2freecad/'

FILENAME = WORKING_FOLDER + 'FreeCAD_Test_Model.FCStd'

fcmodel = FreeCADModel(FILENAME)

#sketch = fcmodel.sketches["Sketch"]

#print_object_attributes(fcmodel.xy_plane)

sketch = fcmodel.add_sketch(fcmodel.xy_plane)

print(sketch.label)
sketch.label = "poop"
print(sketch.label)
#fcmodel.add_sketch(fcmodel.xz_plane)
#fcmodel.add_sketch(fcmodel.yz_plane)
#print(sketch.get_position())
