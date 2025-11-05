"""
Canvas Lifecycle Management

Provides unified lifecycle management for canvas-scoped components:
- Canvas creation and initialization
- Component synchronization
- State reset and cleanup
- IDManager scope management

This module ensures that global components (SwissKnifePalette, SimulationController)
are properly isolated per canvas and synchronized with canvas/document lifecycle.
"""

from .canvas_context import CanvasContext
from .lifecycle_manager import CanvasLifecycleManager
from .id_scope_manager import IDScopeManager

__all__ = [
    'CanvasContext',
    'CanvasLifecycleManager',
    'IDScopeManager',
]
