# Drag Behavior Architecture Options

**Date:** October 3, 2025  
**Context:** Adding drag functionality for selected objects  
**Current State:** Selection system exists, but no drag/move behavior

---

## Current System Overview

### Existing Components

1. **SelectionManager** (`src/shypn/edit/selection_manager.py`)
   - Manages which objects are selected
   - Tracks selection mode (NORMAL vs EDIT)
   - Currently ~224 lines

2. **DocumentCanvas** (`src/shypn/data/canvas/document_canvas.py`)
   - Main canvas controller
   - Manages viewport and document
   - Currently ~550 lines

3. **model_canvas_loader.py** (`src/shypn/helpers/`)
   - GTK event handler (button press, motion, scroll)
   - Currently handles panning and arc tool
   - Currently ~1372 lines (too large!)

4. **ObjectEditingTransforms** (`src/shypn/edit/object_editing_transforms.py`)
   - Renders selection highlights and handles
   - Currently ~264 lines

---

## Drag Behavior Requirements

### What Needs to Happen

1. **Click Detection** - User clicks on a selected object
2. **Drag Detection** - User moves mouse with button held (> 5px threshold)
3. **Drag Preview** - Objects move in real-time as mouse moves
4. **Multi-Object Support** - All selected objects move together
5. **Grid Snapping** (optional) - Snap to grid during or after drag
6. **Drag Complete** - On button release, finalize positions
7. **Undo Support** (future) - Record old positions for undo

### Coordinate Concerns

- Events arrive in **screen coordinates**
- Objects stored in **world coordinates**
- Need transformations: screen → world (for dragging)
- Delta calculation must respect zoom level

---

## Option 1: Add to SelectionManager (Expand Existing)

### Structure
```
src/shypn/edit/selection_manager.py
  + start_drag(obj, start_x, start_y)
  + update_drag(current_x, current_y, manager)
  + end_drag()
  + is_dragging()
  + get_drag_offset()
```

### Pros ✅
- All selection-related behavior in one place
- SelectionManager already knows what's selected
- Natural extension of existing selection system
- Easy to coordinate selection + dragging

### Cons ❌
- SelectionManager grows larger (may violate SRP)
- Mixes state management (what's selected) with behavior (how to drag)
- Harder to test drag behavior independently
- Selection class becomes less focused

### Code Example
```python
class SelectionManager:
    def __init__(self):
        self.selected_objects = set()
        self.drag_state = {
            'active': False,
            'start_x': 0,
            'start_y': 0,
            'initial_positions': {}  # obj_id -> (x, y)
        }
    
    def start_drag(self, screen_x, screen_y, manager):
        """Start dragging selected objects."""
        if not self.selected_objects:
            return False
        
        self.drag_state['active'] = True
        self.drag_state['start_x'] = screen_x
        self.drag_state['start_y'] = screen_y
        
        # Store initial positions
        self.drag_state['initial_positions'] = {}
        for obj in self.get_selected_objects(manager):
            self.drag_state['initial_positions'][id(obj)] = (obj.x, obj.y)
        
        return True
    
    def update_drag(self, screen_x, screen_y, manager):
        """Update drag positions."""
        if not self.drag_state['active']:
            return
        
        # Calculate delta in world coordinates
        start_wx, start_wy = manager.screen_to_world(
            self.drag_state['start_x'], 
            self.drag_state['start_y']
        )
        current_wx, current_wy = manager.screen_to_world(screen_x, screen_y)
        
        dx = current_wx - start_wx
        dy = current_wy - start_wy
        
        # Move all selected objects
        for obj in self.get_selected_objects(manager):
            initial_pos = self.drag_state['initial_positions'][id(obj)]
            obj.x = initial_pos[0] + dx
            obj.y = initial_pos[1] + dy
```

### Integration
- Loader calls `selection_manager.start_drag()` on button press
- Loader calls `selection_manager.update_drag()` on motion
- Loader calls `selection_manager.end_drag()` on button release

---

## Option 2: Create Separate DragController (New Class)

### Structure
```
src/shypn/edit/drag_controller.py  (NEW FILE)
  class DragController:
    + start_drag(objects, start_x, start_y)
    + update_drag(current_x, current_y, canvas)
    + end_drag()
    + is_dragging()
    + cancel_drag()
```

### Pros ✅
- **Single Responsibility** - DragController only handles dragging
- SelectionManager stays focused on selection
- Easy to test drag behavior in isolation
- Can be reused for different drag scenarios
- Clear separation of concerns
- Easy to add features (grid snap, constraints, etc.)

### Cons ❌
- Another class to coordinate
- Need to pass selected objects between classes
- Slightly more complex wiring in loader

### Code Example
```python
# src/shypn/edit/drag_controller.py
class DragController:
    """Handles dragging of objects on the canvas."""
    
    def __init__(self):
        self.dragging = False
        self.drag_objects = []  # Objects being dragged
        self.start_screen_x = 0
        self.start_screen_y = 0
        self.initial_positions = {}  # obj_id -> (x, y)
    
    def start_drag(self, objects, screen_x, screen_y):
        """Start dragging a set of objects.
        
        Args:
            objects: List of objects to drag
            screen_x: Starting X in screen coords
            screen_y: Starting Y in screen coords
        
        Returns:
            True if drag started
        """
        if not objects:
            return False
        
        self.dragging = True
        self.drag_objects = objects
        self.start_screen_x = screen_x
        self.start_screen_y = screen_y
        
        # Store initial positions
        self.initial_positions = {
            id(obj): (obj.x, obj.y) for obj in objects
        }
        
        return True
    
    def update_drag(self, screen_x, screen_y, canvas):
        """Update positions during drag.
        
        Args:
            screen_x: Current X in screen coords
            screen_y: Current Y in screen coords
            canvas: DocumentCanvas for coordinate transforms
        """
        if not self.dragging:
            return
        
        # Convert to world coordinates
        start_wx, start_wy = canvas.screen_to_world(
            self.start_screen_x, self.start_screen_y
        )
        current_wx, current_wy = canvas.screen_to_world(screen_x, screen_y)
        
        # Calculate delta
        dx = current_wx - start_wx
        dy = current_wy - start_wy
        
        # Apply to all objects
        for obj in self.drag_objects:
            initial = self.initial_positions[id(obj)]
            obj.x = initial[0] + dx
            obj.y = initial[1] + dy
    
    def end_drag(self):
        """Finalize drag operation."""
        if not self.dragging:
            return
        
        self.dragging = False
        self.drag_objects = []
        self.initial_positions = {}
    
    def cancel_drag(self):
        """Cancel drag and restore original positions."""
        if not self.dragging:
            return
        
        # Restore positions
        for obj in self.drag_objects:
            initial = self.initial_positions[id(obj)]
            obj.x = initial[0]
            obj.y = initial[1]
        
        self.end_drag()
    
    def is_dragging(self):
        """Check if currently dragging."""
        return self.dragging
```

### Integration
```python
# In loader
self.drag_controller = DragController()

def _on_button_press(self, widget, event, manager):
    # ... existing code ...
    if clicked_on_selected_object:
        selected_objs = selection_manager.get_selected_objects(manager)
        self.drag_controller.start_drag(selected_objs, event.x, event.y)

def _on_motion_notify(self, widget, event, manager):
    if self.drag_controller.is_dragging():
        self.drag_controller.update_drag(event.x, event.y, canvas)
        widget.queue_draw()
```

---

## Option 3: Add to DocumentCanvas (Centralized in Canvas)

### Structure
```
src/shypn/data/canvas/document_canvas.py
  + start_drag_selection(screen_x, screen_y)
  + update_drag(screen_x, screen_y)
  + end_drag()
  + cancel_drag()
```

### Pros ✅
- Canvas already coordinates everything
- Natural place for high-level operations
- Direct access to both document and viewport
- Simpler for loader (just call canvas methods)

### Cons ❌
- Canvas becomes more complex
- Violates separation of concerns (canvas shouldn't know about dragging)
- Harder to test drag behavior
- Canvas already has many responsibilities
- Not aligned with proposed architecture (editing should be separate)

### Code Example
```python
class DocumentCanvas:
    def __init__(self, width, height):
        # ... existing ...
        self._drag_state = {
            'active': False,
            'objects': [],
            'initial_positions': {}
        }
    
    def start_drag_selection(self, screen_x, screen_y):
        """Start dragging selected objects."""
        # Get selected objects from somewhere?
        # Problem: Canvas doesn't know about selection!
        pass
```

### Issues
- Canvas doesn't have access to SelectionManager
- Would need to add selection tracking to Canvas
- Couples canvas with selection and dragging
- **Not recommended** for this reason

---

## Option 4: Tool-Based Architecture (Future-Ready)

### Structure
```
src/shypn/controllers/          (NEW DIRECTORY)
  base_tool.py                  (Abstract base)
  select_tool.py                (Selection + Drag)
  arc_tool.py                   (Arc creation)
  place_tool.py                 (Place creation)
  transition_tool.py            (Transition creation)
```

### Pros ✅
- **Most scalable** - Easy to add new tools
- Clear tool state machines
- Follows industry patterns (Inkscape, GIMP, etc.)
- Each tool encapsulates its own behavior
- Easy to switch between tools
- Aligns with proposed architecture plan

### Cons ❌
- Most complex to implement initially
- Requires refactoring existing code
- Overkill if only adding one feature
- Need tool manager/coordinator

### Code Example
```python
# src/shypn/controllers/base_tool.py
class BaseTool:
    """Abstract base class for canvas tools."""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.active = False
    
    def on_button_press(self, event):
        """Handle button press. Return True if handled."""
        pass
    
    def on_button_release(self, event):
        """Handle button release. Return True if handled."""
        pass
    
    def on_motion(self, event):
        """Handle motion. Return True if handled."""
        pass
    
    def on_activate(self):
        """Called when tool becomes active."""
        self.active = True
    
    def on_deactivate(self):
        """Called when tool becomes inactive."""
        self.active = False


# src/shypn/controllers/select_tool.py
class SelectTool(BaseTool):
    """Selection and drag tool."""
    
    def __init__(self, canvas, selection_manager):
        super().__init__(canvas)
        self.selection_manager = selection_manager
        self.drag_controller = DragController()
    
    def on_button_press(self, event):
        # Check if clicking on selected object
        obj = self.canvas.get_object_at_screen_point(event.x, event.y)
        
        if obj and obj.selected:
            # Start drag
            selected = self.selection_manager.get_selected_objects()
            self.drag_controller.start_drag(selected, event.x, event.y)
            return True
        elif obj:
            # Select object
            multi = event.state & Gdk.ModifierType.CONTROL_MASK
            self.selection_manager.select(obj, multi=multi)
            return True
        else:
            # Clear selection or start rectangle select
            if not (event.state & Gdk.ModifierType.CONTROL_MASK):
                self.selection_manager.clear()
            return True
    
    def on_motion(self, event):
        if self.drag_controller.is_dragging():
            self.drag_controller.update_drag(event.x, event.y, self.canvas)
            return True
        return False
    
    def on_button_release(self, event):
        if self.drag_controller.is_dragging():
            self.drag_controller.end_drag()
            return True
        return False
```

### Integration
```python
# In loader
self.tool_manager = ToolManager()
self.tool_manager.register_tool('select', SelectTool(canvas, selection_manager))
self.tool_manager.register_tool('arc', ArcTool(canvas))
self.tool_manager.set_active_tool('select')

def _on_button_press(self, widget, event, manager):
    tool = self.tool_manager.get_active_tool()
    if tool.on_button_press(event):
        widget.queue_draw()
```

---

## Recommendation Matrix

| Criteria | Option 1: SelectionManager | Option 2: DragController | Option 3: Canvas | Option 4: Tools |
|----------|---------------------------|-------------------------|------------------|-----------------|
| **Simplicity** | ⭐⭐⭐⭐ Easy | ⭐⭐⭐ Moderate | ⭐⭐⭐⭐ Easy | ⭐⭐ Complex |
| **Clean Architecture** | ⭐⭐ Mixed concerns | ⭐⭐⭐⭐ SRP | ⭐ Violates SRP | ⭐⭐⭐⭐⭐ Best |
| **Testability** | ⭐⭐⭐ OK | ⭐⭐⭐⭐ Good | ⭐⭐ Hard | ⭐⭐⭐⭐⭐ Excellent |
| **Extensibility** | ⭐⭐ Limited | ⭐⭐⭐ Good | ⭐⭐ Limited | ⭐⭐⭐⭐⭐ Excellent |
| **Time to Implement** | ⭐⭐⭐⭐ 1-2 hours | ⭐⭐⭐ 2-3 hours | ⭐⭐⭐⭐ 1-2 hours | ⭐⭐ 4-6 hours |
| **Aligns with Plan** | ⭐⭐ Partial | ⭐⭐⭐⭐ Yes | ⭐ No | ⭐⭐⭐⭐⭐ Perfect |

---

## Final Recommendations

### For Quick Implementation (Now)
**Choose Option 2: DragController**

Reasons:
1. ✅ Clean separation of concerns
2. ✅ Follows Single Responsibility Principle
3. ✅ Reasonable complexity
4. ✅ Can be refactored into tools later
5. ✅ Testable in isolation
6. ✅ Doesn't pollute other classes

### For Long-Term (Future Refactoring)
**Migrate to Option 4: Tool-Based Architecture**

When to do it:
- After drag is working
- When adding 2-3+ more interactive features
- During the full loader refactoring (per architecture plan)

Migration path:
```
DragController → SelectTool (wraps DragController)
Arc creation → ArcTool
Object creation → PlaceTool, TransitionTool
```

---

## Implementation Plan (Option 2)

### Step 1: Create DragController
```bash
src/shypn/edit/drag_controller.py  (~150 lines)
```

### Step 2: Wire in Loader
```python
# In model_canvas_loader.py
self.drag_controller = DragController()

# Modify _on_button_press to detect drag start
# Modify _on_motion_notify to update drag
# Modify _on_button_release to end drag
```

### Step 3: Add to edit/__init__.py
```python
from .drag_controller import DragController
__all__ = [..., 'DragController']
```

### Step 4: Test
- Click on selected object → starts drag
- Move mouse → objects follow
- Release → drag ends
- Multi-select → all move together

---

## Summary

**Recommended: Option 2 (DragController)**
- Clean, focused, testable
- Quick to implement
- Easy to migrate to tools later

**Avoid: Option 3 (Canvas)**
- Violates architecture principles
- Makes canvas too complex

**Future: Option 4 (Tools)**
- Best long-term solution
- Implement after drag is working
- Part of larger refactoring effort

