# For Windows you must either use \\ or / in the path, using a single \ is problematic

from free_cad_object_wrappers import  FreeCADModel


def print_object_attributes(obj):
    print(str(obj.__doc__) + " Properties:")
    for prop in dir(obj):
        print(prop + " | " + str(getattr(obj,prop)))


def print_object_name_and_type(obj):
    print(obj.Name + " | " + obj.TypeId)


WORKING_FOLDER = 'C:/Users/George/Documents/text2freecad/'

FILENAME = WORKING_FOLDER + 'FreeCAD_Test_Model.FCStd'

fcmodel = FreeCADModel(FILENAME)


#part = fcmodel.add_part(fcmodel.document)
#body = fcmodel.add_body(part)
#body1 = fcmodel.add_body(part)
#body2 = fcmodel.add_body(part)
#body3 = fcmodel.add_body(part)

#fcmodel.print_objects()

#fcmodel.bodies['Body'].print_properties()
#fcmodel.sketches['Sketch'].print_properties()
#fcmodel.parts['Part'].print_properties()

#print_object_attributes(fcmodel.sketches['Sketch'].object_.addGeometry)

#print(fcmodel.bodies)
#print(fcmodel.parts)