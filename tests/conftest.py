"""Module defining pytest fixture configuration"""

import pytest

from tests.sample_pancad_objects.sample_sketches import (
    unconstrained_square_sketch,
    joined_square_sketch,
    square_sketch_bottom_length,
    square_sketch_variations,
)

from tests.sample_pancad_objects.sample_part_files import (
    empty_part_file,
    square_sketch_part_file,
    cube_part_file,
    cylinder_part_file,
    rounded_edge_cube_part_file,
    ellipse_part_file,
    square_variations_part_file,
)