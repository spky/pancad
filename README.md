# Text-to-FreeCAD

Text-to-FreeCAD is intended to translate FreeCAD (and any other 
geometry program!) to plain text and back

# Development Notes
--------------------------------------------------------------------------------

## Future Work

- [ ] Comb through significant figure implementation and unit test the 
trigonometry module for arbitrary decimal places
- [ ] Add a ton of error checking for the elliptical and circular arc 
translation tools
- [ ] Add FreeCAD constraints to the svg file as metadata
- [ ] Verify that constraints in the svg file are met and notify the 
user if not
- [ ] Verify whether or not a sketch in svg is fully constrained
- [ ] Add ways to compare the actual output of svgs instead of just the 
text, to make it possible to compare the results independent of the 
inputs
- [ ] Default the svg files to mirror about the x axis since svg files 
have their origin in the top left with the positive y direction pointing
 downwards
- [ ] Develop a reliable way to ID points for FreeCAD-SVG synchronization
- [ ] Add ellipse translation from freecad to svg
- [ ] Add elliptical arc translation from freecad to svg
- [ ] Add an auto sizing feature to svg_file.py

## Reference Info

- [Packaging Python Projects Reference][DN1]
- [sampleproject github][DN2]

[DN1]: https://packaging.python.org/en/latest/tutorials/packaging-projects/
[DN2]: https://github.com/pypa/sampleproject/tree/main