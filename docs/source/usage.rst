Usage
=====

Installation
------------

To use pancad, first install it using pip:

.. code-block:: console

   (.venv) $ pip install pancad

If you intend to use pancad to write FreeCAD files: you will also need to install
FreeCAD to its default directory or add its executable to your PATH so pancad can
find it. You can download FreeCAD `here`_. Just reading FreeCAD files
does not require FreeCAD.

.. _here: https://www.freecad.org/downloads

Getting Started Tutorials
-------------------------

How do I read from a FreeCAD file?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A FreeCAD file can be read into a :class:`~pancad.api.PartFile` like this:

.. literalinclude:: tutorials/how_to_read_from_a_freecad_file.py
    :linenos:
    :lines: 1,2,3

The number of features in the file can be summarized by using print on the
PartFile:

.. literalinclude:: tutorials/how_to_read_from_a_freecad_file.py
    :linenos:
    :lines: 4
    :lineno-match:

How do I make a FreeCAD file?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A :class:`~pancad.api.PartFile` can generate a FreeCAD file, allowing CAD
to be finely version controlled.

Let's make a 1 mm cube as a first step. We'll start by defining the corners of
the a square as tuples:

.. literalinclude:: tutorials/how_do_i_make_a_freecad_file.py
    :start-after: [corner-definition-start]
    :end-before: [corner-definition-end]

With the corner points defined, we can create
4 :class:`~pancad.api.LineSegment` elements to act as the bottom, right,
top and left sides of a square CAD sketch. We'll constrain them into place later.
The line segments can be created like this:

.. note::
    Pay attention to the order of the first and second corner arguments! The
    'start' and 'end' points of a line segment will matter when we return to
    fully define the sketch.

.. literalinclude:: tutorials/how_do_i_make_a_freecad_file.py
    :start-after: [line-definition-start]
    :end-before: [line-definition-end]

pancad :class:`~pancad.api.Sketch` geometry systems contain special lists that 
manage CAD dependencies, so now our square's line segments need to be placed into 
a sketch geometry list. We'll also name the sketch using the 'name' keyword 
argument:

.. literalinclude:: tutorials/how_do_i_make_a_freecad_file.py
    :start-after: [sketch-definition-start]
    :end-before: [sketch-definition-end]

If we were to send save this sketch to FreeCAD now, the lines in the sketch
would be 'unconstrained'. The line end points would not be rigidly connected and
they would be able to rotate freely.

Below is the sketch as generated on the left and after clicking and dragging the
top left corner on the right, note that the unconstrained lines are shown in
blue:

.. image:: tutorials/images/how_do_i_make_a_freecad_file_unconstrained_square.png
    :width: 49 %
.. image:: tutorials/images/how_do_i_make_a_freecad_file_unconstrained_square_moved_corner_w_arrow.svg
    :width: 49 %

FreeCAD and most CAD software won't be able to tell that this is an
extrusion-ready square that without additional constraints placed on the
lines. There are dozens of ways that even just these 4 lines can be constrained
to make a square, but we have to pick one so we'll just choose to constrain:

1. The end points to each other.
2. The orientations of the lines to vertical or horizontal
3. The distances between the top/bottom and left/right pairs of lines.
4. The bottom left corner to the sketch's origin point.

We'll need the :func:`~pancad.api.make_constraint` method and a pancad enumeration
called a :class:`~pancad.api.SketchConstraint` to fully  constrain the lines
using the strategy above. We'll also need to add in the side length we defined
earlier and define its unit as millimeters.

.. literalinclude:: tutorials/how_do_i_make_a_freecad_file.py
    :start-after: [constraint-definition-start]
    :end-before: [constraint-definition-end]

The sketch constraints were the hard part, so now all that's left is to 
add the sketch, constrain it to the file's coordinate system, and extrude
it to finish off the cube. We'll do this by making a pancad
:class:`~pancad.api.Extrude` using its
:meth:`~pancad.api.Extrude.from_length` method. Using from_length's default
arguments will extrude the sketch directly from the plane it's defined on.

.. literalinclude:: tutorials/how_do_i_make_a_freecad_file.py
    :start-after: [extrude-definition-start]
    :end-before: [extrude-definition-end]

The cube CAD's done! Now to add the sketch and extrude to a
:class:`~pancad.api.PartFile` by setting its
:attr:`~pancad.api.PartFile.features` property to the list of features.
We can save it to FreeCAD using :meth:`~pancad.api.PartFile.to_freecad`\ .
Make sure to add the sketch before the extrude, since the extrude depends on the
sketch. You should find the FreeCAD '.FCStd' file in the same directory that you
ran the script in.

.. literalinclude:: tutorials/how_do_i_make_a_freecad_file.py
    :start-after: [file-definition-start]
    :end-before: [file-definition-end]

.. note::
    When you open the FreeCAD file after initially generating it, you'll find
    that the geometry doesn't appear in the window. Don't worry, it's there
    but invisible! (no, really)

    The pancad-to-FreeCAD interface does not yet support initializing the
    visualization of the model, so you need to go into Model tab and click
    the eye symbols next to the pad and body features to see the geometry.

Here's what you should get when you open the file in FreeCAD:

.. image:: tutorials/images/how_do_i_make_a_freecad_file_cube.png
    :width: 49 %