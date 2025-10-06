# Editing Operations

This directory contains modules for object editing, selection management, and interactive canvas operations.

## Core Modules

### `transformation/` (NEW)
**OOP Transformation Handler System**

The transformation package provides interactive transformation operations (resize, rotate, scale) through a clean OOP architecture:

**Structure:**
```
transformation/
├── __init__.py              # Package exports
├── transform_handler.py     # Abstract base class
├── handle_detector.py       # Handle positioning & hit detection
└── resize_handler.py        # Resize operations
```

**Features:**
- Double-click object to enter edit mode
- Drag handles to resize Places and Transitions
- Press ESC to cancel transformation
- Size constraints enforced (min/max)
- Easy to extend with new transformation types

**Usage:**
```python
# Check if handle clicked
handle = editing_transforms.check_handle_at_position(obj, x, y, zoom)

# Start transformation
if handle:
    editing_transforms.start_transformation(obj, handle, x, y)

# Update during drag
editing_transforms.update_transformation(current_x, current_y)

# End transformation
editing_transforms.end_transformation()

# Cancel transformation
editing_transforms.cancel_transformation()
```

**Resize Behavior:**
- **Places**: All handles resize uniformly (change radius)
- **Transitions**: 
  - Edge handles (n, e, s, w): Resize one dimension
  - Corner handles (ne, se, sw, nw): Resize both dimensions

**Constraints:**
```python
MIN_PLACE_RADIUS = 10.0
MAX_PLACE_RADIUS = 100.0
MIN_TRANSITION_WIDTH = 20.0
MAX_TRANSITION_WIDTH = 200.0
MIN_TRANSITION_HEIGHT = 10.0
MAX_TRANSITION_HEIGHT = 100.0
```

### `selection_manager.py`
**Selection and Multi-select Management**

Manages object selection state and multi-select operations:
- **Single Selection**: Click to select one object
- **Multi-select**: Ctrl+Click to add/remove from selection
- **Rectangle Selection**: Drag rectangle to select multiple objects
- **Selection State**: Track selected objects across operations
- **Selection Events**: Notify listeners of selection changes
- **Selection Rendering**: Highlight selected objects
- **Edit Mode**: Double-click to enter transformation mode

**Features:**
```python
# Select object
selection_manager.select(object)

# Multi-select
selection_manager.add_to_selection(object)

# Clear selection
selection_manager.clear()

# Get selected objects
objects = selection_manager.get_selected()

# Check if object is selected
if selection_manager.is_selected(object):
    ...

# Edit mode (for transformations)
selection_manager.enter_edit_mode(object)
selection_manager.exit_edit_mode()
if selection_manager.is_edit_mode():
    target = selection_manager.get_edit_target()
```

**Selection Modes:**
- **NORMAL**: Basic selection (for operations like arc creation, dragging)
- **EDIT**: Transformation mode (shows bounding box + handles)

**Mode-specific behavior:**
- **Replace**: Click replaces current selection
- **Add**: Ctrl+Click adds to selection
- **Toggle**: Ctrl+Click toggles selection
- **Rectangle**: Drag selects all enclosed objects

### `drag_controller.py`
**Drag and Drop Operations**

Manages dragging of objects and control points:
- **Object Dragging**: Move places and transitions
- **Multi-object Drag**: Move all selected objects together
- **Control Point Dragging**: Adjust curved arc control points
- **Drag Preview**: Show ghost/outline during drag
- **Grid Snapping**: Snap to grid during drag (optional)
- **Boundary Constraints**: Keep objects within canvas bounds

**Drag States:**
1. **Idle**: No drag in progress
2. **Press**: Mouse button pressed, potential drag start
3. **Dragging**: Active drag operation
4. **Release**: Drag complete, apply changes

**Drag Operations:**
```python
# Start drag
drag_controller.start_drag(object, start_x, start_y)

# Update drag position
drag_controller.update_drag(current_x, current_y)

# Complete drag
drag_controller.end_drag()

# Cancel drag
drag_controller.cancel_drag()
```

**Features:**
- **Multi-object Drag**: Maintain relative positions
- **Snap to Grid**: Align to grid lines
- **Undo/Redo**: Record drag operations
- **Constraints**: Minimum spacing, canvas bounds

### `object_editing_transforms.py`
**Object Transformations**

Geometric transformations for Petri Net objects:
- **Move**: Translate object position
- **Rotate**: Rotate object (transitions only)
- **Resize**: Resize object (not typically used for Petri Nets)
- **Align**: Align objects (left, right, center, top, bottom)
- **Distribute**: Distribute objects evenly
- **Grid Snap**: Snap objects to grid

**Transformation Operations:**
```python
# Move object
transform.move(object, delta_x, delta_y)

# Align objects
transform.align_left(objects)
transform.align_center_vertical(objects)

# Distribute objects
transform.distribute_horizontal(objects)
transform.distribute_vertical(objects)

# Snap to grid
transform.snap_to_grid(object, grid_spacing)
```

**Alignment Options:**
- **Horizontal**: Left, Center, Right
- **Vertical**: Top, Middle, Bottom

**Distribution Options:**
- **Horizontal**: Even spacing between objects
- **Vertical**: Even spacing between objects
- **Grid**: Arrange in grid pattern

### `rectangle_selection.py`
**Rectangle Selection Tool**

Interactive rectangle selection for multi-select:
- **Visual Feedback**: Show selection rectangle during drag
- **Intersection Test**: Select objects within rectangle
- **Selection Modes**: Fully enclosed vs. partial overlap
- **Keyboard Modifiers**: Ctrl (add), Shift (toggle)

**Usage Flow:**
```python
1. User presses mouse button on canvas
2. User drags to create selection rectangle
3. Rectangle drawn with dashed border
4. Objects within rectangle highlighted
5. User releases mouse button
6. Objects within rectangle selected
```

**Selection Criteria:**
- **Fully Enclosed**: Object completely inside rectangle (default)
- **Partial Overlap**: Any part of object touches rectangle (Shift)

### `transient_arc.py`
**Temporary Arc During Creation**

Manages the temporary arc shown while creating new arcs:
- **Visual Preview**: Show arc from source to mouse cursor
- **Source Highlighting**: Highlight valid source objects
- **Target Highlighting**: Highlight valid target objects
- **Connection Rules**: Enforce place ↔ transition connections
- **Snap to Target**: Snap to target object when close

**Arc Creation Flow:**
```python
1. User selects arc tool from palette
2. User clicks source object (place or transition)
3. Transient arc appears from source to cursor
4. User moves cursor (arc follows)
5. Valid targets highlighted when cursor hovers
6. User clicks target object
7. Permanent arc created
8. Transient arc removed
```

**Connection Rules:**
- Place → Transition: Valid
- Transition → Place: Valid
- Place → Place: Invalid
- Transition → Transition: Invalid

**Visual Feedback:**
- **Valid Source**: Green highlight
- **Valid Target**: Blue highlight
- **Invalid Target**: Red highlight
- **Transient Arc**: Dashed line

## Editing Tool Integration

### Edit Palette Tools
- **Select**: Selection and multi-select
- **Pan**: Canvas panning (no object selection)
- **Place**: Create places
- **Transition**: Create transitions (various types)
- **Arc**: Create arcs (normal, inhibitor, curved)

### Tool State Machine
```python
State: IDLE
    on tool_select: State = TOOL_SELECTED

State: TOOL_SELECTED
    on canvas_click: 
        if object_at_click:
            State = OBJECT_SELECTED
        else:
            State = CREATING_OBJECT

State: CREATING_OBJECT
    on drag: Update preview
    on release: Create object, State = IDLE

State: OBJECT_SELECTED
    on drag: State = DRAGGING
    on delete: Delete object, State = IDLE

State: DRAGGING
    on drag: Update position
    on release: Apply changes, State = OBJECT_SELECTED
```

## Keyboard Shortcuts

### Selection
- **Ctrl+A**: Select all
- **Escape**: Clear selection
- **Delete**: Delete selected objects

### Editing
- **Ctrl+X**: Cut
- **Ctrl+C**: Copy
- **Ctrl+V**: Paste
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo

### Movement
- **Arrow Keys**: Move selected objects by 1 pixel
- **Shift+Arrow**: Move selected objects by 10 pixels
- **Ctrl+Arrow**: Move selected objects to grid

### Alignment
- **Ctrl+L**: Align left
- **Ctrl+R**: Align right
- **Ctrl+T**: Align top
- **Ctrl+B**: Align bottom

## Mouse Interactions

### Selection
- **Click**: Select object (replace selection)
- **Ctrl+Click**: Add/remove from selection
- **Drag**: Rectangle selection
- **Double-Click**: Edit object properties

### Dragging
- **Drag Object**: Move object
- **Drag Multi-select**: Move all selected objects
- **Drag Control Point**: Adjust curved arc

### Context Menu
- **Right-Click Object**: Show object context menu
- **Right-Click Canvas**: Show canvas context menu

## Undo/Redo Support

All editing operations support undo/redo:
- **Move**: Record original and new positions
- **Create**: Record created object
- **Delete**: Record deleted object
- **Property Edit**: Record old and new values

**Undo Stack:**
```python
operations = [
    MoveOperation(objects, old_pos, new_pos),
    CreateOperation(new_object),
    DeleteOperation(deleted_object),
    PropertyOperation(object, "name", old_name, new_name)
]
```

## Coordinate Systems

### Screen Coordinates
- Canvas pixel coordinates (0,0 = top-left)
- Mouse events in screen coordinates
- UI rendering in screen coordinates

### World Coordinates
- Model coordinates (pan/zoom independent)
- Object positions in world coordinates
- Serialization in world coordinates

### Conversion
```python
# Screen to world
world_x, world_y = manager.screen_to_world(screen_x, screen_y)

# World to screen
screen_x, screen_y = manager.world_to_screen(world_x, world_y)
```

## Validation Rules

### Object Creation
- Places and transitions must have unique names
- Objects must be within canvas bounds
- Minimum spacing between objects

### Arc Creation
- Source and target must be different objects
- Source and target must be valid types (place ↔ transition)
- No duplicate arcs between same source/target

### Object Movement
- Objects must remain within canvas bounds
- Maintain minimum spacing (optional)
- Preserve connectivity (arcs follow objects)

## Import Patterns

```python
from shypn.edit.selection_manager import SelectionManager
from shypn.edit.drag_controller import DragController
from shypn.edit.object_editing_transforms import (
    align_objects,
    distribute_objects,
    snap_to_grid
)
from shypn.edit.rectangle_selection import RectangleSelection
from shypn.edit.transient_arc import TransientArc
```

## Performance Optimizations

- **Spatial Indexing**: Fast object lookup at coordinates
- **Dirty Rectangles**: Redraw only changed regions
- **Selection Caching**: Cache selected object list
- **Intersection Tests**: Optimize rectangle selection
- **Event Throttling**: Limit drag update frequency

## Accessibility

- **Keyboard Navigation**: Full keyboard support for all operations
- **Focus Indicators**: Clear visual focus for selected objects
- **Screen Reader**: Announce selection and editing operations
- **High Contrast**: Support high contrast themes
