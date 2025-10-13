import pancad
filename = "cube.FCStd"
part = pancad.PartFile.from_freecad(filename)
print(part)