Usage
=====

Installation
------------

.. note::
    
    This project is under active development. and has not been placed into the 
    Python Package Index yet.

To use PanCAD, first install it using pip:

.. code-block:: console

   (.venv) $ pip install PanCAD

Getting Started Tutorials
-------------------------

How do I read from a FreeCAD file?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A FreeCAD file can be read into a :class:`~PanCAD.filetypes.PartFile` like this:

.. literalinclude:: tutorials/how_to_read_from_a_freecad_file.py
    :linenos:
    :lines: 1-3

The contents of the file can be summarized using print:

.. literalinclude:: tutorials/how_to_read_from_a_freecad_file.py
    :linenos:
    :lineno-match:
    :lines: 4

The PartFile will have a tabular summary output to the command line:

.. program-output:: cd tutorials && python how_to_read_from_a_freecad_file.py
    :shell:

How do I make a FreeCAD file?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

FreeCAD files can be created from :class:`~PanCAD.filetypes.PartFile`\ s, but