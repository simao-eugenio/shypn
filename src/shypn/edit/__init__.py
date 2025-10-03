"""Edit utilities for visual feedback during Petri net editing.

This package provides non-model objects used for visual guidance during editing:
- TransientArc: Temporary preview arc shown during arc creation

These objects are NOT PetriNetObjects and are not added to the model.
They exist only for visual feedback during interactive editing.
"""
from shypn.edit.transient_arc import TransientArc

__all__ = ['TransientArc']
