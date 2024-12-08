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

To get the first command in a path, you can use the ``svg_parsers.match_front_cmd()`` function:

.. autofunction:: svg_parsers.match_front_cmd
.. autofunction:: svg_parsers.parse_coordinate_string