"""
Transformation handlers for object editing.

This package provides OOP-based transformation handlers for editing
Petri Net objects through interactive handles.

Key components:
- TransformHandler: Abstract base class for all transformations
- HandleDetector: Handle hit detection and positioning
- ResizeHandler: Resize operations for Places and Transitions
- ArcTransformHandler: Curve/straight toggle and control point adjustment for Arcs
"""

from shypn.edit.transformation.transform_handler import TransformHandler
from shypn.edit.transformation.handle_detector import HandleDetector
from shypn.edit.transformation.resize_handler import ResizeHandler
from shypn.edit.transformation.arc_transform_handler import ArcTransformHandler

__all__ = [
    'TransformHandler',
    'HandleDetector',
    'ResizeHandler',
    'ArcTransformHandler',
]
