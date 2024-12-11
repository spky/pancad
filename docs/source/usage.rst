Usage
=====

Installation
------------

To use text2freecad, first install it using pip:

.. code-block:: console

   (.venv) $ pip install text2freecad

Function Explanations
---------------------

Reading design information from SVG files
#########################################

.. autofunction:: svg_parsers.match_front_cmd
.. autofunction:: svg_parsers.parse_coordinate_string
.. autofunction:: svg_parsers.split_path_data
.. autofunction:: svg_parsers.clean_command
.. autofunction:: svg_parsers.csv_to_float
.. autofunction:: svg_parsers.create_sublists
.. autofunction:: svg_parsers.parse_moveto
.. autofunction:: svg_parsers.parse_arc
.. autofunction:: svg_parsers.parse_lineto
.. autofunction:: svg_parsers.parse_horizontal
.. autofunction:: svg_parsers.parse_vertical