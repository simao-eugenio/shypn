"""Services package - stateless utility services.

Services are stateless classes or modules that provide utility functions.
They don't maintain state and can be called from anywhere.
"""

from .coordinate_transform import (
    screen_to_world,
    world_to_screen,
    mm_to_pixels,
    pixels_to_mm,
    validate_zoom,
)

from .arc_geometry_service import (
    detect_parallel_arcs,
    calculate_arc_offset,
    count_parallel_arcs,
    has_parallel_arcs,
    get_arc_offset_for_rendering,
    separate_parallel_arcs_by_direction,
)

__all__ = [
    'screen_to_world',
    'world_to_screen',
    'mm_to_pixels',
    'pixels_to_mm',
    'validate_zoom',
    'detect_parallel_arcs',
    'calculate_arc_offset',
    'count_parallel_arcs',
    'has_parallel_arcs',
    'get_arc_offset_for_rendering',
    'separate_parallel_arcs_by_direction',
]
