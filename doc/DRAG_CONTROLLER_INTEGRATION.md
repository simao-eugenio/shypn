# DragController Integration Guide

## Overview

The `DragController` is now available as a clean, OOP-oriented component for handling drag-and-drop operations on canvas objects.

## Features

✅ **Multi-object dragging** - Drag all selected objects together  
✅ **Grid snapping** - Snap to grid during or after drag  
✅ **Axis constraints** - Lock to horizontal or vertical movement  
✅ **Cancel support** - ESC key restores original positions  
✅ **Callbacks** - Hook into drag lifecycle events  
✅ **Undo support** - Initial positions preserved for undo  
✅ **Clean API** - Simple, intuitive methods  

---

## Basic Usage

```python
from shypn.edit import DragController

# Create controller (typically once in loader __init__)
self.drag_controller = DragController()

# On mouse button press
def _on_button_press(self, widget, event, manager):
    # Check if clicking on a selected object
    world_x, world_y = manager.screen_to_world(event.x, event.y)
    clicked_obj = manager.get_object_at(world_x, world_y)
    
    if clicked_obj and clicked_obj.selected:
        # Get all selected objects
        selected_objs = self.selection_manager.get_selected_objects(manager)
        
        # Start drag
        self.drag_controller.start_drag(selected_objs, event.x, event.y)

# On mouse motion
def _on_motion_notify(self, widget, event, manager):
    if self.drag_controller.is_dragging():
        # Update drag positions
        self.drag_controller.update_drag(event.x, event.y, manager)
        widget.queue_draw()

# On mouse button release
def _on_button_release(self, widget, event, manager):
    if self.drag_controller.is_dragging():
        # Finalize drag
        self.drag_controller.end_drag()
        widget.queue_draw()

# On ESC key press
def _on_key_press(self, widget, event, manager):
    if event.keyval == Gdk.KEY_Escape:
        if self.drag_controller.is_dragging():
            # Cancel drag and restore positions
            self.drag_controller.cancel_drag()
            widget.queue_draw()
```

---

## Advanced Features

### Grid Snapping

```python
# Enable grid snapping
drag_controller.set_snap_to_grid(True, grid_spacing=50.0)

# Or snap on individual update
drag_controller.update_drag(event.x, event.y, canvas, snap_to_grid=True)
```

### Axis Constraints

```python
# Lock to horizontal movement (Shift key)
if event.state & Gdk.ModifierType.SHIFT_MASK:
    drag_controller.set_axis_constraint('horizontal')
else:
    drag_controller.set_axis_constraint(None)

# Lock to vertical movement (Ctrl key)
if event.state & Gdk.ModifierType.CONTROL_MASK:
    drag_controller.set_axis_constraint('vertical')
```

### Callbacks

```python
# Hook into drag lifecycle
drag_controller.set_on_drag_start(lambda: print("Drag started"))
drag_controller.set_on_drag_update(lambda: print("Dragging..."))
drag_controller.set_on_drag_end(lambda: self._mark_document_modified())
drag_controller.set_on_drag_cancel(lambda: print("Drag canceled"))
```

### Undo Support

```python
# Get initial positions before drag started
initial_positions = drag_controller.get_initial_positions()

# Store for undo system
self.undo_stack.push(MoveCommand(initial_positions, current_positions))
```

---

## Complete Integration Example

```python
class ModelCanvasLoader:
    def __init__(self, ...):
        # ... existing code ...
        
        # Create drag controller
        self.drag_controller = DragController()
        
        # Configure grid snapping
        self.drag_controller.set_snap_to_grid(False, grid_spacing=10.0)
        
        # Set callbacks
        self.drag_controller.set_on_drag_end(self._on_drag_completed)
    
    def _on_button_press(self, widget, event, manager):
        """Handle button press events."""
        # ... existing arc tool and other logic ...
        
        # Check for drag start on left button
        if event.button == 1:
            world_x, world_y = manager.screen_to_world(event.x, event.y)
            clicked_obj = manager.get_object_at(world_x, world_y)
            
            if clicked_obj and clicked_obj.selected:
                # Clicking on selected object - start drag
                selected_objs = self.selection_manager.get_selected_objects(manager)
                
                if self.drag_controller.start_drag(selected_objs, event.x, event.y):
                    print(f"Started dragging {len(selected_objs)} objects")
                    return True
            elif clicked_obj:
                # Clicking on unselected object - select it first
                multi = event.state & Gdk.ModifierType.CONTROL_MASK
                self.selection_manager.select(clicked_obj, multi=multi, manager=manager)
                widget.queue_draw()
                return True
        
        return False
    
    def _on_motion_notify(self, widget, event, manager):
        """Handle motion events."""
        # Check for drag update
        if self.drag_controller.is_dragging():
            # Check for modifier keys
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                self.drag_controller.set_axis_constraint('horizontal')
            elif event.state & Gdk.ModifierType.CONTROL_MASK:
                self.drag_controller.set_axis_constraint('vertical')
            else:
                self.drag_controller.set_axis_constraint(None)
            
            # Update drag
            self.drag_controller.update_drag(event.x, event.y, manager)
            widget.queue_draw()
            return True
        
        # ... existing panning and other logic ...
        return False
    
    def _on_button_release(self, widget, event, manager):
        """Handle button release events."""
        # Check for drag end
        if self.drag_controller.is_dragging():
            # Get drag info for undo
            initial_pos = self.drag_controller.get_initial_positions()
            
            # End drag
            self.drag_controller.end_drag()
            
            # Mark document as modified
            manager.mark_modified()
            
            # TODO: Add to undo stack
            # self.undo_stack.push(MoveCommand(initial_pos, ...))
            
            widget.queue_draw()
            return True
        
        # ... existing code ...
        return False
    
    def _on_key_press(self, widget, event, manager):
        """Handle key press events."""
        # ESC cancels drag
        if event.keyval == Gdk.KEY_Escape:
            if self.drag_controller.is_dragging():
                self.drag_controller.cancel_drag()
                widget.queue_draw()
                return True
        
        # ... existing code ...
        return False
    
    def _on_drag_completed(self):
        """Called when drag completes successfully."""
        print("Drag completed - positions finalized")
        # Could trigger autosave, update UI, etc.
```

---

## API Reference

### Core Methods

| Method | Description |
|--------|-------------|
| `start_drag(objects, screen_x, screen_y)` | Start dragging objects |
| `update_drag(screen_x, screen_y, canvas, snap_to_grid=False)` | Update during drag |
| `end_drag()` | Finalize drag |
| `cancel_drag()` | Cancel and restore positions |
| `is_dragging()` | Check if currently dragging |

### Configuration

| Method | Description |
|--------|-------------|
| `set_snap_to_grid(enabled, grid_spacing)` | Enable grid snapping |
| `set_axis_constraint(axis)` | Constrain to 'horizontal', 'vertical', or None |

### Queries

| Method | Description |
|--------|-------------|
| `get_dragged_objects()` | Get list of dragged objects |
| `get_initial_positions()` | Get positions before drag (for undo) |
| `get_drag_delta(canvas)` | Get current drag offset |
| `get_drag_info()` | Get complete state info |

### Callbacks

| Method | Description |
|--------|-------------|
| `set_on_drag_start(callback)` | Called when drag starts |
| `set_on_drag_update(callback)` | Called on each mouse move |
| `set_on_drag_end(callback)` | Called when drag completes |
| `set_on_drag_cancel(callback)` | Called when drag is canceled |

---

## Testing

All features have been tested:
- ✅ Multi-object dragging
- ✅ Position updates
- ✅ Cancel/restore
- ✅ Grid snapping
- ✅ Axis constraints
- ✅ Callbacks
- ✅ State queries

---

## Next Steps

1. **Integrate into loader** - Wire up button press/motion/release events
2. **Add undo support** - Use `get_initial_positions()` for undo commands
3. **Add visual feedback** - Show drag outline or highlight during drag
4. **Add constraints** - Prevent dragging outside canvas bounds
5. **Add collision detection** - Prevent overlapping objects (optional)

---

## Migration Path to Tool-Based Architecture

When ready to move to tool-based architecture:

```python
class SelectTool(BaseTool):
    def __init__(self, canvas, selection_manager):
        super().__init__(canvas)
        self.selection_manager = selection_manager
        self.drag_controller = DragController()  # Reuse!
    
    def on_button_press(self, event):
        # Use drag_controller as-is
        pass
```

The DragController is **tool-agnostic** and can be easily wrapped into a SelectTool later.
