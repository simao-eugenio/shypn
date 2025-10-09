"""Edit utilities for visual feedback during Petri net editing.

This package provides:
- Selection management: SelectionManager, SelectionMode
- Drag operations: DragController
- Visual feedback: ObjectEditingTransforms, RectangleSelection
- TransientArc: Temporary preview arc shown during arc creation
- Editing Operations Palette: UI and operations for editing (undo/redo/clipboard/lasso)
- Graph Layout: Automatic layout algorithms for imported pathways

These objects are NOT PetriNetObjects and are not added to the model.
They exist only for visual feedback during interactive editing.
"""
from shypn.edit.transient_arc import TransientArc
from shypn.edit.selection_manager import SelectionManager, SelectionMode
from shypn.edit.object_editing_transforms import ObjectEditingTransforms
from shypn.edit.rectangle_selection import RectangleSelection
from shypn.edit.drag_controller import DragController
from shypn.edit.base_palette_loader import BasePaletteLoader
from shypn.edit.editing_operations_palette import EditingOperationsPalette
from shypn.edit.editing_operations_palette_loader import EditingOperationsPaletteLoader
from shypn.edit.edit_operations import EditOperations
from shypn.edit.lasso_selector import LassoSelector
from shypn.edit.graph_layout import LayoutEngine, LayoutAlgorithm

__all__ = [
    'TransientArc',
    'SelectionManager',
    'SelectionMode',
    'ObjectEditingTransforms',
    'RectangleSelection',
    'DragController',
    'BasePaletteLoader',
    'EditingOperationsPalette',
    'EditingOperationsPaletteLoader',
    'EditOperations',
    'LassoSelector',
    'LayoutEngine',
    'LayoutAlgorithm'
]
