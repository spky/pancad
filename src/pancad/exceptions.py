"""A module defining exceptions pancad can raise."""

class DupeUidError(ValueError):
    """Raised when an element with an already added uid is added to a pancad
    mutable sequence designed to contain only unique values.
    """

class HasDependentsError(ValueError):
    """Raised when attempting to remove an element while it still has detectable
    dependents. Should be used to disposition what actions should be taken, for
    example: delete the dependencies, mark the dependencies as invalid, or raise
    another error.
    """

class SketchDupeUidError(DupeUidError):
    """Raised when an element with an already added uid is added to a sketch
    element list.
    """

class MissingCADDependencyError(LookupError):
    """Raised when attempting to add a constraint to a sketch missing its
    dependencies.
    """

class SketchGeometryHasConstraintsError(HasDependentsError):
    """Raised when attempting to remove geometry from a sketch while it still has
    detectable constraints.
    """