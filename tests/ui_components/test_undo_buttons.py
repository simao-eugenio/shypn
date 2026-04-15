#!/usr/bin/env python3
"""Quick test to verify undo/redo button wiring."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.model_canvas_manager import ModelCanvasManager

# Create manager
manager = ModelCanvasManager()

# Check initial state
print(f"Initial state: can_undo={manager.undo_manager.can_undo()}, can_redo={manager.undo_manager.can_redo()}")

# Add a place
place = manager.add_place(100, 100)
print(f"After add_place: can_undo={manager.undo_manager.can_undo()}, can_redo={manager.undo_manager.can_redo()}")

# Undo
if manager.undo_manager.undo(manager):
    print(f"After undo: can_undo={manager.undo_manager.can_undo()}, can_redo={manager.undo_manager.can_redo()}")

# Redo
if manager.undo_manager.redo(manager):
    print(f"After redo: can_undo={manager.undo_manager.can_undo()}, can_redo={manager.undo_manager.can_redo()}")

print("\nTest complete!")
