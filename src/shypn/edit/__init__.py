"""Edit utilities for visual feedback during Petri net editing.

This package provides:
- Selection management: SelectionManager, SelectionMode
- Visual feedback: ObjectEditingTransforms, RectangleSelection
- TransientArc: Temporary preview arc shown during arc creation

These objects are NOT PetriNetObjects and are not added to the model.
They exist only for visual feedback during interactive editing.
"""
from shypn.edit.transient_arc import TransientArc
from shypn.edit.selection_manager import SelectionManager, SelectionMode
from shypn.edit.object_editing_transforms import ObjectEditingTransforms
from shypn.edit.rectangle_selection import RectangleSelection

__all__ = [
    'TransientArc',
    'SelectionManager',
    'SelectionMode',
    'ObjectEditingTransforms',
    'RectangleSelection'
]
