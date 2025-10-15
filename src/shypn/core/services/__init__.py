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

__all__ = [
    'screen_to_world',
    'world_to_screen',
    'mm_to_pixels',
    'pixels_to_mm',
    'validate_zoom',
]
