"""Canvas management package.

This package provides classes for managing canvas overlays and palettes:
- BaseOverlayManager: Abstract base class for overlay management
- CanvasOverlayManager: Concrete implementation for managing all canvas overlays

These classes separate overlay management concerns from the main canvas loader,
following the Single Responsibility Principle.
"""
from shypn.canvas.base_overlay_manager import BaseOverlayManager
from shypn.canvas.canvas_overlay_manager import CanvasOverlayManager

__all__ = [
    'BaseOverlayManager',
    'CanvasOverlayManager'
]
