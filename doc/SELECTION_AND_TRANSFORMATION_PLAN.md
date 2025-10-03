# Selection and Transformation System - Implementation Plan

**Date:** October 3, 2025  
**Branch:** petri-net-objects-editing  
**Priority:** High (Core editing functionality)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Proposed Architecture](#proposed-architecture)
4. [Implementation Plan](#implementation-plan)
5. [Visual Feedback Specification](#visual-feedback-specification)
6. [Testing Strategy](#testing-strategy)

---

## Executive Summary

### Problem Statement

**Current Issues:**
1. ✗ Selection feedback exists but may be inconsistent (blue highlight implemented but not always visible)
2. ✗ No object transformation handles (move, resize, rotate)
3. ✗ No unified selection layer for managing multiple selections
4. ✗ No visual feedback for multi-select operations
5. ✗ Object transformation logic scattered across codebase

### Proposed Solution

Create a **unified selection and transformation system** with:
- **Selection Layer:** Dedicated rendering layer for selection feedback
- **Transform Handles:** Visual controls for move, resize, rotate operations
- **ObjectEditingTransforms Class:** Centralized transformation logic
- **Multi-selection Support:** Select and transform multiple objects simultaneously
- **Consistent Visual Feedback:** Blue highlights, bounding boxes, transform handles

---

## Current State Analysis

### Existing Selection Code

#### 1. Object Selection State

**File:** `src/shypn/api/petri_net_object.py`
```python
class PetriNetObject:
    def __init__(self, id, name, label=""):
        self.selected = False  # Selection state exists
```

**Status:** ✓ Base infrastructure present

#### 2. Selection Rendering

**File:** `src/shypn/api/place.py` (lines 73-79)
```python
# Draw selection highlight if selected
if self.selected:
    # Offset by 3px in screen space = 3/zoom in world space
    cr.arc(self.x, self.y, self.radius + 3 / zoom, 0, 2 * math.pi)
    cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)  # Blue highlight
    cr.set_line_width(3.0 / zoom)  # Compensate for zoom
    cr.stroke()
```

**Status:** ✓ Visual feedback implemented for Place

**File:** `src/shypn/api/transition.py` (lines 94-102)
```python
# Draw selection highlight if selected
if self.selected:
    # Offset by 3px in screen space = 3/zoom in world space
    offset = 3 / zoom
    cr.rectangle(self.x - half_w - offset, self.y - half_h - offset, 
                width + 2 * offset, height + 2 * offset)
    cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)  # Blue highlight
    cr.set_line_width(3.0 / zoom)  # Compensate for zoom
    cr.stroke()
```

**Status:** ✓ Visual feedback implemented for Transition

**File:** `src/shypn/api/arc.py` (lines 139-147)
```python
# Draw selection highlight if selected
if self.selected:
    # Redraw arc with thicker line
    # (similar pattern)
```

**Status:** ✓ Visual feedback implemented for Arc

#### 3. Selection Interaction

**File:** `src/shypn/helpers/model_canvas_loader.py` (lines 448-458)
```python
# Left-click: toggle selection
world_x, world_y = manager.screen_to_world(event.x, event.y)
clicked_obj = manager.find_object_at_position(world_x, world_y)

if clicked_obj is not None:
    # Toggle selection
    clicked_obj.selected = not clicked_obj.selected
    status = "selected" if clicked_obj.selected else "deselected"
    print(f"{clicked_obj.name} {status}")
    widget.queue_draw()
    return True
```

**Status:** ✓ Basic selection interaction present

### Issues Identified

1. **✗ No Multi-selection Support**
   - Ctrl+Click to add to selection not implemented
   - Shift+Click for range selection not implemented
   - No "Select All" functionality

2. **✗ No Selection Manager**
   - Selection state scattered across individual objects
   - No unified way to query all selected objects
   - No selection history/undo

3. **✗ No Transform Handles**
   - Can't move selected objects by dragging
   - No resize handles on bounding box
   - No rotation control

4. **✗ No Bounding Box**
   - No visual indicator of multi-selection bounds
   - No group transformation preview

5. **✗ Inconsistent Visual Feedback**
   - Each object renders its own selection
   - No unified selection layer
   - Selection may be hidden behind other objects

---

## Proposed Architecture

### Layer Model

```
┌─────────────────────────────────────┐
│     Canvas Rendering Layers         │
├─────────────────────────────────────┤
│  1. Background (white fill)         │
│  2. Grid Layer (device space)       │
│  3. Object Layer (world space)      │ ← Objects render WITHOUT selection
│  4. Selection Layer (world space)   │ ← NEW: Selection feedback here
│  5. Transform Layer (world space)   │ ← NEW: Handles and bounding box
│  6. Overlay Layer (device space)    │ ← Arc preview, UI overlays
└─────────────────────────────────────┘
```

### Class Architecture

```
ObjectEditingTransforms
├── SelectionManager
│   ├── get_selected_objects() → List[PetriNetObject]
│   ├── select(obj, multi=False)
│   ├── deselect(obj)
│   ├── clear_selection()
│   ├── select_all()
│   └── get_selection_bounds() → (min_x, min_y, max_x, max_y)
│
├── TransformState
│   ├── active: bool
│   ├── operation: 'move' | 'resize' | 'rotate' | None
│   ├── start_pos: (x, y)
│   ├── current_pos: (x, y)
│   ├── objects: List[PetriNetObject]
│   └── preview_offsets: Dict[obj, (dx, dy)]
│
├── TransformHandles
│   ├── render(cr, zoom)
│   ├── hit_test(x, y) → 'move' | 'n' | 'ne' | 'e' | 'se' | etc.
│   └── update_from_selection()
│
└── Rendering
    ├── render_selection_feedback(cr, zoom)
    ├── render_bounding_box(cr, zoom)
    └── render_transform_handles(cr, zoom)
```

---

## Implementation Plan

### Phase 1: Selection Layer (Priority 1)

**Goal:** Separate selection rendering from object rendering for clean layering.

#### Task 1.1: Remove Selection Rendering from Objects

**Files to modify:**
- `src/shypn/api/place.py`
- `src/shypn/api/transition.py`
- `src/shypn/api/arc.py`

**Changes:**
```python
# Remove this from render() methods:
# if self.selected:
#     # Draw selection highlight
#     ...

# Keep only core object rendering
def render(self, cr, zoom=1.0):
    # Draw hollow circle (Place)
    cr.arc(self.x, self.y, self.radius, 0, 2 * math.pi)
    cr.set_source_rgb(*self.border_color)
    cr.set_line_width(self.border_width / max(zoom, 1e-6))
    cr.stroke()
    # NO selection rendering here
```

#### Task 1.2: Create SelectionManager Class

**New file:** `src/shypn/data/selection_manager.py`

```python
"""Selection Manager for Petri Net Objects.

Manages selection state and provides queries for selected objects.
"""
from typing import List, Optional, Tuple
from shypn.netobjs import PetriNetObject, Place, Transition, Arc


class SelectionManager:
    """Manages selection state for canvas objects."""
    
    def __init__(self):
        """Initialize selection manager."""
        self.selected_objects = set()  # Set of selected object IDs
        self._selection_history = []  # For undo
    
    def select(self, obj: PetriNetObject, multi: bool = False):
        """Select an object.
        
        Args:
            obj: Object to select
            multi: If True, add to selection (Ctrl+Click). If False, replace selection.
        """
        if not multi:
            self.clear_selection()
        
        obj.selected = True
        self.selected_objects.add(id(obj))
    
    def deselect(self, obj: PetriNetObject):
        """Deselect an object."""
        obj.selected = False
        self.selected_objects.discard(id(obj))
    
    def toggle_selection(self, obj: PetriNetObject, multi: bool = False):
        """Toggle object selection state."""
        if obj.selected:
            self.deselect(obj)
        else:
            self.select(obj, multi)
    
    def clear_selection(self):
        """Clear all selections."""
        # Must deselect all objects (they hold state)
        for obj_id in list(self.selected_objects):
            # Find object and deselect (need reference)
            pass  # Will implement with manager integration
        self.selected_objects.clear()
    
    def get_selected_objects(self, manager) -> List[PetriNetObject]:
        """Get list of currently selected objects.
        
        Args:
            manager: Canvas manager to query objects from
            
        Returns:
            List of selected objects
        """
        selected = []
        for obj in manager.get_all_objects():
            if obj.selected:
                selected.append(obj)
        return selected
    
    def get_selection_bounds(self, manager) -> Optional[Tuple[float, float, float, float]]:
        """Calculate bounding box of selected objects.
        
        Returns:
            (min_x, min_y, max_x, max_y) or None if no selection
        """
        selected = self.get_selected_objects(manager)
        if not selected:
            return None
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for obj in selected:
            if isinstance(obj, Place):
                min_x = min(min_x, obj.x - obj.radius)
                min_y = min(min_y, obj.y - obj.radius)
                max_x = max(max_x, obj.x + obj.radius)
                max_y = max(max_y, obj.y + obj.radius)
            elif isinstance(obj, Transition):
                w = obj.width if obj.horizontal else obj.height
                h = obj.height if obj.horizontal else obj.width
                half_w = w / 2
                half_h = h / 2
                min_x = min(min_x, obj.x - half_w)
                min_y = min(min_y, obj.y - half_h)
                max_x = max(max_x, obj.x + half_w)
                max_y = max(max_y, obj.y + half_h)
            # Add Arc bounds calculation if needed
        
        return (min_x, min_y, max_x, max_y)
    
    def has_selection(self) -> bool:
        """Check if any objects are selected."""
        return len(self.selected_objects) > 0
    
    def selection_count(self) -> int:
        """Get number of selected objects."""
        return len(self.selected_objects)
```

#### Task 1.3: Create ObjectEditingTransforms Class

**New file:** `src/shypn/data/object_editing_transforms.py`

```python
"""Object Editing and Transform System.

Unified class for rendering selection feedback, bounding boxes,
and transform handles for selected objects.
"""
import math
from shypn.data.selection_manager import SelectionManager
from shypn.netobjs import Place, Transition


class ObjectEditingTransforms:
    """Manages visual feedback and transformation for selected objects."""
    
    # Visual constants
    SELECTION_COLOR = (0.2, 0.6, 1.0, 0.5)  # Blue highlight with alpha
    SELECTION_LINE_WIDTH = 3.0  # Pixels (compensated for zoom)
    SELECTION_OFFSET = 3.0  # Pixels offset from object edge
    
    BBOX_COLOR = (0.2, 0.6, 1.0, 0.8)  # Darker blue for bounding box
    BBOX_LINE_WIDTH = 1.5  # Pixels
    BBOX_DASH = [5, 3]  # Dash pattern (5px line, 3px gap)
    
    HANDLE_SIZE = 8.0  # Pixels (square handles)
    HANDLE_FILL = (1.0, 1.0, 1.0, 1.0)  # White fill
    HANDLE_STROKE = (0.2, 0.6, 1.0, 1.0)  # Blue stroke
    HANDLE_LINE_WIDTH = 1.5  # Pixels
    
    def __init__(self, selection_manager: SelectionManager):
        """Initialize transform system.
        
        Args:
            selection_manager: SelectionManager instance to track selection
        """
        self.selection_manager = selection_manager
        self.active_handle = None  # 'move', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw'
    
    def render_selection_layer(self, cr, manager, zoom: float):
        """Render all selection feedback.
        
        Should be called in world space (inside Cairo transform).
        
        Args:
            cr: Cairo context
            manager: Canvas manager
            zoom: Current zoom level (for compensation)
        """
        selected = self.selection_manager.get_selected_objects(manager)
        
        if not selected:
            return
        
        # Render individual object selection highlights
        for obj in selected:
            self._render_object_selection(cr, obj, zoom)
        
        # Render bounding box for multi-selection
        if len(selected) > 1:
            self._render_bounding_box(cr, manager, zoom)
        
        # Render transform handles
        if len(selected) >= 1:
            self._render_transform_handles(cr, manager, zoom)
    
    def _render_object_selection(self, cr, obj, zoom: float):
        """Render selection highlight for individual object.
        
        Args:
            cr: Cairo context (world space)
            obj: Object to render selection for
            zoom: Current zoom level
        """
        offset = self.SELECTION_OFFSET / zoom
        
        if isinstance(obj, Place):
            # Circle outline
            cr.arc(obj.x, obj.y, obj.radius + offset, 0, 2 * math.pi)
            cr.set_source_rgba(*self.SELECTION_COLOR)
            cr.set_line_width(self.SELECTION_LINE_WIDTH / zoom)
            cr.stroke()
        
        elif isinstance(obj, Transition):
            # Rectangle outline
            w = obj.width if obj.horizontal else obj.height
            h = obj.height if obj.horizontal else obj.width
            half_w = w / 2
            half_h = h / 2
            
            cr.rectangle(
                obj.x - half_w - offset,
                obj.y - half_h - offset,
                w + 2 * offset,
                h + 2 * offset
            )
            cr.set_source_rgba(*self.SELECTION_COLOR)
            cr.set_line_width(self.SELECTION_LINE_WIDTH / zoom)
            cr.stroke()
        
        # Add Arc selection rendering if needed
    
    def _render_bounding_box(self, cr, manager, zoom: float):
        """Render dashed bounding box around all selected objects.
        
        Args:
            cr: Cairo context (world space)
            manager: Canvas manager
            zoom: Current zoom level
        """
        bounds = self.selection_manager.get_selection_bounds(manager)
        if not bounds:
            return
        
        min_x, min_y, max_x, max_y = bounds
        
        # Add padding
        padding = 10.0 / zoom
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        
        # Draw dashed rectangle
        cr.rectangle(min_x, min_y, max_x - min_x, max_y - min_y)
        cr.set_source_rgba(*self.BBOX_COLOR)
        cr.set_line_width(self.BBOX_LINE_WIDTH / zoom)
        
        # Set dash pattern (compensated for zoom)
        dash_pattern = [d / zoom for d in self.BBOX_DASH]
        cr.set_dash(dash_pattern)
        cr.stroke()
        cr.set_dash([])  # Reset dash pattern
    
    def _render_transform_handles(self, cr, manager, zoom: float):
        """Render resize/rotate handles on bounding box corners and edges.
        
        Args:
            cr: Cairo context (world space)
            manager: Canvas manager
            zoom: Current zoom level
        """
        bounds = self.selection_manager.get_selection_bounds(manager)
        if not bounds:
            return
        
        min_x, min_y, max_x, max_y = bounds
        
        # Add padding (same as bounding box)
        padding = 10.0 / zoom
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        
        # Calculate handle positions
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        handle_size = self.HANDLE_SIZE / zoom
        half_size = handle_size / 2
        
        # 8 handles: corners and midpoints
        handles = {
            'nw': (min_x, min_y),     # Top-left
            'n':  (center_x, min_y),  # Top-center
            'ne': (max_x, min_y),     # Top-right
            'e':  (max_x, center_y),  # Right-center
            'se': (max_x, max_y),     # Bottom-right
            's':  (center_x, max_y),  # Bottom-center
            'sw': (min_x, max_y),     # Bottom-left
            'w':  (min_x, center_y),  # Left-center
        }
        
        # Render each handle
        for position, (hx, hy) in handles.items():
            # Draw filled rectangle for handle
            cr.rectangle(hx - half_size, hy - half_size, handle_size, handle_size)
            cr.set_source_rgba(*self.HANDLE_FILL)
            cr.fill_preserve()
            
            # Draw handle border
            cr.set_source_rgba(*self.HANDLE_STROKE)
            cr.set_line_width(self.HANDLE_LINE_WIDTH / zoom)
            cr.stroke()
    
    def hit_test_handle(self, x: float, y: float, manager, zoom: float) -> Optional[str]:
        """Test if a point hits a transform handle.
        
        Args:
            x, y: Point in world coordinates
            manager: Canvas manager
            zoom: Current zoom level
            
        Returns:
            Handle name ('nw', 'n', 'ne', etc.) or None
        """
        bounds = self.selection_manager.get_selection_bounds(manager)
        if not bounds:
            return None
        
        min_x, min_y, max_x, max_y = bounds
        padding = 10.0 / zoom
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        handle_size = self.HANDLE_SIZE / zoom
        half_size = handle_size / 2
        
        handles = {
            'nw': (min_x, min_y),
            'n':  (center_x, min_y),
            'ne': (max_x, min_y),
            'e':  (max_x, center_y),
            'se': (max_x, max_y),
            's':  (center_x, max_y),
            'sw': (min_x, max_y),
            'w':  (min_x, center_y),
        }
        
        # Check each handle
        for name, (hx, hy) in handles.items():
            if (hx - half_size <= x <= hx + half_size and
                hy - half_size <= y <= hy + half_size):
                return name
        
        return None
```

#### Task 1.4: Integrate into Canvas Rendering

**File:** `src/shypn/helpers/model_canvas_loader.py`

**Changes to `_on_draw` method:**

```python
def _on_draw(self, drawing_area, cr, width, height, manager):
    """Draw callback for the canvas."""
    # ... existing code ...
    
    # Apply pan and zoom transformation
    cr.save()
    cr.translate(manager.pan_x * manager.zoom, manager.pan_y * manager.zoom)
    cr.scale(manager.zoom, manager.zoom)
    
    # Draw objects WITHOUT selection (objects render themselves only)
    for obj in manager.get_all_objects():
        obj.render(cr, zoom=manager.zoom)
    
    # NEW: Draw selection layer (after objects, before handles)
    if hasattr(manager, 'editing_transforms'):
        manager.editing_transforms.render_selection_layer(cr, manager, manager.zoom)
    
    cr.restore()
    
    # ... rest of overlay rendering ...
```

#### Task 1.5: Add to ModelCanvasManager

**File:** `src/shypn/data/model_canvas_manager.py`

```python
from shypn.data.selection_manager import SelectionManager
from shypn.data.object_editing_transforms import ObjectEditingTransforms

class ModelCanvasManager:
    def __init__(self, ...):
        # ... existing code ...
        
        # Selection and transformation system
        self.selection_manager = SelectionManager()
        self.editing_transforms = ObjectEditingTransforms(self.selection_manager)
```

---

### Phase 2: Multi-selection Support (Priority 2)

#### Task 2.1: Update Click Handler for Multi-select

**File:** `src/shypn/helpers/model_canvas_loader.py`

**Update `_on_button_press` method:**

```python
def _on_button_press(self, widget, event, manager):
    # ... existing tool handling ...
    
    # No tool active: selection mode
    if event.button == 1:
        # Left-click: toggle selection
        world_x, world_y = manager.screen_to_world(event.x, event.y)
        clicked_obj = manager.find_object_at_position(world_x, world_y)
        
        # Check for Ctrl key (multi-select)
        is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        
        if clicked_obj is not None:
            # Toggle selection with multi-select support
            manager.selection_manager.toggle_selection(clicked_obj, multi=is_ctrl)
            status = "selected" if clicked_obj.selected else "deselected"
            multi_str = " (multi)" if is_ctrl else ""
            print(f"{clicked_obj.name} {status}{multi_str}")
            widget.queue_draw()
            return True
        else:
            # Clicked empty space: clear selection (unless Ctrl held)
            if not is_ctrl:
                manager.selection_manager.clear_selection()
                widget.queue_draw()
```

#### Task 2.2: Add Keyboard Shortcuts

**File:** `src/shypn/helpers/model_canvas_loader.py`

**Update `_on_key_press_event` method:**

```python
def _on_key_press_event(self, widget, event, manager):
    """Handle key press events."""
    keyval = event.keyval
    keyname = Gdk.keyval_name(keyval)
    
    # Ctrl+A: Select All
    if keyname == 'a' and (event.state & Gdk.ModifierType.CONTROL_MASK):
        for obj in manager.get_all_objects():
            manager.selection_manager.select(obj, multi=True)
        print(f"Selected all ({manager.selection_manager.selection_count()} objects)")
        widget.queue_draw()
        return True
    
    # Escape: Clear selection
    elif keyname == 'Escape':
        if manager.selection_manager.has_selection():
            manager.selection_manager.clear_selection()
            print("Selection cleared")
            widget.queue_draw()
            return True
    
    # Delete: Delete selected objects
    elif keyname in ['Delete', 'BackSpace']:
        selected = manager.selection_manager.get_selected_objects(manager)
        if selected:
            for obj in selected:
                if isinstance(obj, Place):
                    manager.remove_place(obj)
                elif isinstance(obj, Transition):
                    manager.remove_transition(obj)
                elif isinstance(obj, Arc):
                    manager.remove_arc(obj)
            manager.selection_manager.clear_selection()
            print(f"Deleted {len(selected)} objects")
            widget.queue_draw()
            return True
    
    return False
```

---

### Phase 3: Object Transformation (Priority 3)

#### Task 3.1: Implement Drag-to-Move

**File:** `src/shypn/helpers/model_canvas_loader.py`

**Update drag state initialization:**

```python
self._drag_state[drawing_area] = {
    'active': False,
    'button': 0,
    'start_x': 0,
    'start_y': 0,
    'start_pan_x': 0,
    'start_pan_y': 0,
    'is_panning': False,
    # NEW: Object dragging state
    'is_dragging_objects': False,
    'drag_start_world': (0, 0),
    'dragged_objects': [],
    'object_start_positions': {},  # {obj: (start_x, start_y)}
}
```

**Update `_on_button_press`:**

```python
# Check if clicking on selected object (start drag)
if clicked_obj is not None and clicked_obj.selected:
    # Start dragging selected objects
    state['is_dragging_objects'] = True
    state['drag_start_world'] = (world_x, world_y)
    
    # Store start positions of all selected objects
    selected = manager.selection_manager.get_selected_objects(manager)
    state['dragged_objects'] = selected
    state['object_start_positions'] = {
        obj: (obj.x, obj.y) for obj in selected
    }
    return True
```

**Update `_on_motion_notify`:**

```python
# Check for object dragging (before panning)
if state['is_dragging_objects']:
    world_x, world_y = manager.screen_to_world(event.x, event.y)
    start_wx, start_wy = state['drag_start_world']
    
    # Calculate world-space delta
    dx = world_x - start_wx
    dy = world_y - start_wy
    
    # Move all selected objects
    for obj in state['dragged_objects']:
        start_x, start_y = state['object_start_positions'][obj]
        obj.x = start_x + dx
        obj.y = start_y + dy
    
    widget.queue_draw()
    return True

# ... existing pan logic ...
```

**Update `_on_button_release`:**

```python
if state['is_dragging_objects']:
    print(f"Moved {len(state['dragged_objects'])} objects")
    state['is_dragging_objects'] = False
    state['dragged_objects'] = []
    state['object_start_positions'] = {}
    return True
```

#### Task 3.2: Implement Handle-based Resize

**File:** `src/shypn/data/object_editing_transforms.py`

**Add resize logic:**

```python
def apply_resize(self, handle: str, dx: float, dy: float, objects: List):
    """Apply resize transformation based on handle drag.
    
    Args:
        handle: Handle being dragged ('n', 'ne', 'e', etc.)
        dx, dy: Delta in world coordinates
        objects: Objects to resize
    """
    # For single object: resize directly
    if len(objects) == 1:
        obj = objects[0]
        if isinstance(obj, Place):
            # Resize radius
            if handle in ['n', 'ne', 'nw']:
                obj.radius -= dy
            if handle in ['s', 'se', 'sw']:
                obj.radius += dy
            if handle in ['e', 'ne', 'se']:
                obj.radius += dx
            if handle in ['w', 'nw', 'sw']:
                obj.radius -= dx
            
            # Clamp to minimum size
            obj.radius = max(10.0, obj.radius)
        
        elif isinstance(obj, Transition):
            # Resize width/height
            if handle in ['n', 'ne', 'nw']:
                obj.height -= 2 * dy
                obj.y += dy
            if handle in ['s', 'se', 'sw']:
                obj.height += 2 * dy
                obj.y += dy
            if handle in ['e', 'ne', 'se']:
                obj.width += 2 * dx
                obj.x += dx
            if handle in ['w', 'nw', 'sw']:
                obj.width -= 2 * dx
                obj.x -= dx
            
            # Clamp to minimum size
            obj.width = max(20.0, obj.width)
            obj.height = max(10.0, obj.height)
    
    # For multi-object: scale group (advanced feature)
    else:
        # TODO: Implement group scaling
        pass
```

---

### Phase 4: Visual Polish (Priority 4)

#### Task 4.1: Add Hover Feedback

**Show lighter highlight when hovering over selectable objects:**

```python
# In _on_motion_notify:
hovered_obj = manager.find_object_at_position(world_x, world_y)
if hovered_obj != manager.hovered_object:
    manager.hovered_object = hovered_obj
    widget.queue_draw()

# In ObjectEditingTransforms.render_selection_layer:
if hasattr(manager, 'hovered_object') and manager.hovered_object:
    obj = manager.hovered_object
    if not obj.selected:
        # Draw lighter hover highlight
        self._render_hover_feedback(cr, obj, zoom)
```

#### Task 4.2: Add Cursor Feedback

**Change cursor based on context:**

```python
def update_cursor(self, widget, context):
    """Update cursor based on interaction context.
    
    Args:
        widget: GTK widget
        context: 'default', 'move', 'resize-nw', 'resize-n', etc.
    """
    cursors = {
        'default': Gdk.CursorType.ARROW,
        'move': Gdk.CursorType.FLEUR,
        'resize-n': Gdk.CursorType.TOP_SIDE,
        'resize-s': Gdk.CursorType.BOTTOM_SIDE,
        'resize-e': Gdk.CursorType.RIGHT_SIDE,
        'resize-w': Gdk.CursorType.LEFT_SIDE,
        'resize-ne': Gdk.CursorType.TOP_RIGHT_CORNER,
        'resize-nw': Gdk.CursorType.TOP_LEFT_CORNER,
        'resize-se': Gdk.CursorType.BOTTOM_RIGHT_CORNER,
        'resize-sw': Gdk.CursorType.BOTTOM_LEFT_CORNER,
    }
    
    cursor_type = cursors.get(context, Gdk.CursorType.ARROW)
    cursor = Gdk.Cursor.new(cursor_type)
    window = widget.get_window()
    if window:
        window.set_cursor(cursor)
```

#### Task 4.3: Add Transform Preview

**Show ghost preview during transformation:**

```python
def render_transform_preview(self, cr, manager, zoom):
    """Render preview of objects during transformation.
    
    Shows semi-transparent ghost at new position/size.
    """
    if not self.is_transforming:
        return
    
    # Draw ghost objects at preview positions
    for obj, preview_state in self.preview_objects.items():
        cr.save()
        cr.set_source_rgba(0.2, 0.6, 1.0, 0.3)  # Semi-transparent blue
        # Draw object at preview position/size
        # ...
        cr.restore()
```

---

## Visual Feedback Specification

### Selection Highlight

**Single Object:**
- **Color:** RGB(0.2, 0.6, 1.0) alpha 0.5 (blue with transparency)
- **Line Width:** 3.0 pixels (compensated for zoom)
- **Offset:** 3.0 pixels from object edge
- **Pattern:** Solid stroke

**Multi-selection Bounding Box:**
- **Color:** RGB(0.2, 0.6, 1.0) alpha 0.8 (darker blue)
- **Line Width:** 1.5 pixels (compensated for zoom)
- **Offset:** 10.0 pixels padding from objects
- **Pattern:** Dashed [5px line, 3px gap]

### Transform Handles

**Appearance:**
- **Size:** 8×8 pixels (compensated for zoom)
- **Fill:** White RGB(1.0, 1.0, 1.0)
- **Stroke:** Blue RGB(0.2, 0.6, 1.0)
- **Line Width:** 1.5 pixels

**Positions:**
- 8 handles: NW, N, NE, E, SE, S, SW, W
- Corners and edge midpoints

**Hover State:**
- Fill: Light blue RGB(0.8, 0.9, 1.0)
- Stroke: Darker blue RGB(0.1, 0.4, 0.8)

### Hover Feedback (Not Selected)

**Color:** RGB(0.2, 0.6, 1.0) alpha 0.2 (very light blue)
**Line Width:** 2.0 pixels
**Offset:** 2.0 pixels from edge

### Cursor States

| Context | Cursor | Use Case |
|---------|--------|----------|
| Default | Arrow | Normal canvas interaction |
| Selectable | Hand | Hovering over object |
| Move | Move (cross arrows) | Dragging selected objects |
| Resize N/S | Vertical resize | N or S handle |
| Resize E/W | Horizontal resize | E or W handle |
| Resize NE/SW | Diagonal resize ↗↙ | NE or SW handle |
| Resize NW/SE | Diagonal resize ↖↘ | NW or SE handle |

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_selection_manager.py`

```python
def test_select_single():
    """Test selecting single object."""
    manager = SelectionManager()
    obj = Place(100, 100, 1, "P1")
    
    manager.select(obj)
    assert obj.selected == True
    assert manager.selection_count() == 1

def test_select_multi():
    """Test multi-selection with Ctrl."""
    manager = SelectionManager()
    obj1 = Place(100, 100, 1, "P1")
    obj2 = Place(200, 200, 2, "P2")
    
    manager.select(obj1, multi=False)
    manager.select(obj2, multi=True)
    
    assert obj1.selected == True
    assert obj2.selected == True
    assert manager.selection_count() == 2

def test_selection_bounds():
    """Test bounding box calculation."""
    # Test implementation
    pass
```

### Integration Tests

**Manual Testing Checklist:**

- [ ] **Selection**
  - [ ] Click object to select
  - [ ] Click again to deselect
  - [ ] Ctrl+Click to add to selection
  - [ ] Click empty space to clear selection
  - [ ] Ctrl+A to select all
  - [ ] Escape to clear selection

- [ ] **Visual Feedback**
  - [ ] Blue highlight on selected object
  - [ ] Bounding box for multi-selection
  - [ ] Transform handles on selection
  - [ ] Hover feedback on unselected objects

- [ ] **Transformation**
  - [ ] Drag selected object to move
  - [ ] Drag multiple selected objects
  - [ ] Drag handles to resize
  - [ ] Cursor changes appropriately

- [ ] **Zoom Independence**
  - [ ] Selection visible at all zoom levels
  - [ ] Handles maintain size at all zooms
  - [ ] Line widths compensated correctly

---

## Implementation Timeline

### Phase 1: Selection Layer (Week 1)
- Days 1-2: Create SelectionManager class
- Days 3-4: Create ObjectEditingTransforms class
- Day 5: Integrate into rendering pipeline
- Testing and bug fixes

### Phase 2: Multi-selection (Week 2)
- Days 1-2: Implement Ctrl+Click multi-select
- Day 3: Add keyboard shortcuts
- Days 4-5: Testing and polish

### Phase 3: Transformation (Week 3)
- Days 1-3: Implement drag-to-move
- Days 4-5: Implement handle-based resize
- Testing and bug fixes

### Phase 4: Visual Polish (Week 4)
- Days 1-2: Add hover feedback
- Day 3: Add cursor feedback
- Days 4-5: Transform preview and final polish

**Total Estimated Time:** 4 weeks

---

## Success Criteria

### Functional Requirements

✓ **Selection**
- Can select objects by clicking
- Can multi-select with Ctrl+Click
- Can clear selection with Escape or empty click
- Can select all with Ctrl+A

✓ **Visual Feedback**
- Blue highlight visible on selected objects
- Bounding box shown for multi-selection
- Transform handles visible and interactive
- Feedback scales correctly with zoom

✓ **Transformation**
- Can move selected objects by dragging
- Can resize objects using handles
- Multiple objects move together
- Transformations smooth and responsive

### Non-functional Requirements

✓ **Performance**
- Selection rendering adds < 5ms overhead
- Smooth dragging at 60 FPS
- No lag with 100+ objects

✓ **Usability**
- Intuitive visual feedback
- Familiar keyboard shortcuts
- Responsive cursor changes
- Clear visual hierarchy

---

**Document Version:** 1.0  
**Last Updated:** October 3, 2025  
**Status:** Planning Complete - Ready for Implementation ✅
