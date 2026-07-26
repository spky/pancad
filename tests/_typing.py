"""A module providing types specific to pancad tests. These are never to be used in the main
program.
"""

from typing import TypedDict
from pancad.utils.pancad_types import SpaceVector

class GeometrySampleData(TypedDict):
    """A dictionary containing inputs for an element of sample geometry.

    :params vectors: A mapping of 2 or 3 element long float vectors to names. Ex: Locations and
        directions.
    :params scalars: A dict of names to floats to specify geometry. Ex: Lengths and angles
    """
    vectors: dict[str, SpaceVector]
    scalars: dict[str, float]

SampleTestGroup = tuple[list[str], list[GeometrySampleData]] # List of ids and list of geometry
ChangeTest = tuple[GeometrySampleData, GeometrySampleData] # Pair of initial and change data
ChangeTestGroup = tuple[list[str], list[ChangeTest]] # Paired up lists of ids and ChangeTests
