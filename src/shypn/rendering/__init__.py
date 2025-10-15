"""Rendering services for Shypn.

This module contains pure rendering functions for canvas elements:
- GridRenderer: Adaptive grid drawing (line/dot/cross styles)
"""

from .grid_renderer import (
    GRID_STYLE_LINE,
    GRID_STYLE_DOT,
    GRID_STYLE_CROSS,
    BASE_GRID_SPACING,
    GRID_MAJOR_EVERY,
    get_adaptive_grid_spacing,
    draw_grid,
)

__all__ = [
    'GRID_STYLE_LINE',
    'GRID_STYLE_DOT',
    'GRID_STYLE_CROSS',
    'BASE_GRID_SPACING',
    'GRID_MAJOR_EVERY',
    'get_adaptive_grid_spacing',
    'draw_grid',
]
