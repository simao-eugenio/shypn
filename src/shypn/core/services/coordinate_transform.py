"""Coordinate transformation utilities.

This module provides stateless functions for converting between screen
and world coordinate systems. These are pure mathematical transformations
with no side effects.

Coordinate Systems:
- Screen coordinates: Pixels on the display (top-left origin)
- World coordinates: Logical model space (can be negative, unbounded)

Transformations:
- screen_to_world: Convert mouse/display coords to model coords
- world_to_screen: Convert model coords to display coords
- mm_to_pixels: Convert physical units to screen pixels (DPI-aware)
"""

from typing import Tuple


def screen_to_world(screen_x: float, screen_y: float,
                    zoom: float, pan_x: float, pan_y: float) -> Tuple[float, float]:
    """Convert screen coordinates to world (model) coordinates.
    
    Formula: world = screen / zoom - pan
    
    This transformation accounts for both zoom level and pan offset,
    converting from pixel coordinates to logical model coordinates.
    
    Args:
        screen_x: X coordinate in screen space (pixels)
        screen_y: Y coordinate in screen space (pixels)
        zoom: Current zoom level (1.0 = 100%, 2.0 = 200%)
        pan_x: Pan offset in X (world coordinates)
        pan_y: Pan offset in Y (world coordinates)
    
    Returns:
        Tuple of (world_x, world_y) in model coordinate space
    
    Example:
        # Convert mouse click at (400, 300) to world coordinates
        world_x, world_y = screen_to_world(
            screen_x=400,
            screen_y=300,
            zoom=1.5,  # 150% zoom
            pan_x=100,
            pan_y=50
        )
    """
    world_x = (screen_x / zoom) - pan_x
    world_y = (screen_y / zoom) - pan_y
    return world_x, world_y


def world_to_screen(world_x: float, world_y: float,
                    zoom: float, pan_x: float, pan_y: float) -> Tuple[float, float]:
    """Convert world (model) coordinates to screen coordinates.
    
    Formula: screen = (world + pan) * zoom
    
    This transformation converts from logical model coordinates to
    pixel coordinates for rendering on screen.
    
    Args:
        world_x: X coordinate in world space (model units)
        world_y: Y coordinate in world space (model units)
        zoom: Current zoom level (1.0 = 100%, 2.0 = 200%)
        pan_x: Pan offset in X (world coordinates)
        pan_y: Pan offset in Y (world coordinates)
    
    Returns:
        Tuple of (screen_x, screen_y) in screen coordinate space (pixels)
    
    Example:
        # Convert object at world (100, 50) to screen for rendering
        screen_x, screen_y = world_to_screen(
            world_x=100,
            world_y=50,
            zoom=1.5,  # 150% zoom
            pan_x=10,
            pan_y=5
        )
    """
    screen_x = (world_x + pan_x) * zoom
    screen_y = (world_y + pan_y) * zoom
    return screen_x, screen_y


def mm_to_pixels(millimeters: float, screen_dpi: float = 96.0) -> float:
    """Convert millimeters to pixels based on screen DPI.
    
    This is used for DPI-aware rendering where physical sizes (e.g., 1mm grid)
    need to be converted to screen pixels that look the same size regardless
    of screen resolution.
    
    Args:
        millimeters: Size in millimeters
        screen_dpi: Screen resolution in dots per inch (default: 96.0)
    
    Returns:
        Size in pixels
    
    Example:
        # Convert 1mm physical spacing to pixels
        pixels = mm_to_pixels(1.0, screen_dpi=120.0)
    
    Note:
        Standard DPI values:
        - 96 DPI: Standard displays
        - 120 DPI: High-resolution displays
        - 144 DPI: Very high-resolution displays
    """
    # 1 inch = 25.4 mm
    # pixels = mm * (pixels/inch) / (mm/inch)
    pixels_per_mm = screen_dpi / 25.4
    return millimeters * pixels_per_mm


def pixels_to_mm(pixels: float, screen_dpi: float = 96.0) -> float:
    """Convert pixels to millimeters based on screen DPI.
    
    Inverse of mm_to_pixels. Useful for determining physical sizes
    from pixel measurements.
    
    Args:
        pixels: Size in pixels
        screen_dpi: Screen resolution in dots per inch (default: 96.0)
    
    Returns:
        Size in millimeters
    
    Example:
        # Convert 96 pixels to millimeters at 96 DPI
        mm = pixels_to_mm(96.0, screen_dpi=96.0)
        # Result: 25.4 mm (1 inch)
    """
    pixels_per_mm = screen_dpi / 25.4
    return pixels / pixels_per_mm


def validate_zoom(zoom: float, min_zoom: float = 0.3, max_zoom: float = 3.0) -> float:
    """Clamp zoom level to valid range.
    
    Args:
        zoom: Desired zoom level
        min_zoom: Minimum allowed zoom (default: 0.3 = 30%)
        max_zoom: Maximum allowed zoom (default: 3.0 = 300%)
    
    Returns:
        Clamped zoom level within [min_zoom, max_zoom]
    
    Example:
        zoom = validate_zoom(5.0)  # Returns 3.0 (clamped to max)
        zoom = validate_zoom(0.1)  # Returns 0.3 (clamped to min)
    """
    return max(min_zoom, min(zoom, max_zoom))
