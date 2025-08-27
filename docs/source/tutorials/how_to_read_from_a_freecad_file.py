import PanCAD
filename = "cube.FCStd"
part = PanCAD.PartFile.from_freecad(filename)
print(part)