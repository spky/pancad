Constraints
===========

.. autofunction:: pancad.api.make_constraint

Abstract Constraint Interfaces
------------------------------

.. autoclass:: pancad.constraints.distance.AbstractDistance
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.snapto.AbstractSnapTo
    :show-inheritance:
    :members:
    :exclude-members: get_constrained, get_geometry, get_references

.. autoclass:: pancad.constraints.state_constraint.AbstractStateConstraint
    :show-inheritance:
    :members:
    :exclude-members: get_constrained, get_geometry, get_references

.. autoclass:: pancad.constraints.distance.AbstractValue
    :show-inheritance:
    :members:
    :exclude-members: get_constrained, get_geometry, get_references

.. autoclass:: pancad.constraints.distance.Abstract1GeometryDistance
    :show-inheritance:
    :members:
    :exclude-members: get_constrained, get_geometry, get_references

.. autoclass:: pancad.constraints.distance.Abstract2GeometryDistance
    :show-inheritance:
    :members:
    :exclude-members: get_constrained, get_geometry, get_references

.. autoclass:: pancad.constraints.distance.AbstractDistance2D
    :show-inheritance:
    :members:
    :exclude-members: get_constrained, get_geometry, get_references

Specific Constraints
--------------------

.. autoclass:: pancad.abstract.AbstractConstraint
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.distance.Angle
    :show-inheritance:
    :members:
    :exclude-members: get_constrained, get_geometry, get_references,

.. autoclass:: pancad.constraints.state_constraint.Coincident
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.distance.Diameter
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.distance.Distance
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.state_constraint.Equal
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.snapto.Horizontal
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.distance.HorizontalDistance
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.state_constraint.Parallel
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.state_constraint.Perpendicular
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.distance.Radius
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.snapto.Vertical
    :show-inheritance:
    :members:

.. autoclass:: pancad.constraints.distance.VerticalDistance
    :show-inheritance:
    :members:



