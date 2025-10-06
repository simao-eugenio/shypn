# Transformation Handlers - Developer Quick Reference

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   User Interaction                      │
│            (Double-click → Drag handle → Release)       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              model_canvas_loader.py                     │
│         (Event routing - minimal logic)                 │
├─────────────────────────────────────────────────────────┤
│  • _on_button_press()   → Detect handle click          │
│  • _on_motion_notify()  → Update transformation        │
│  • _on_button_release() → End transformation           │
│  • _on_key_press_event()→ Cancel transformation (ESC)  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           ObjectEditingTransforms                       │
│        (Transformation coordinator)                     │
├─────────────────────────────────────────────────────────┤
│  • check_handle_at_position()                          │
│  • start_transformation()                              │
│  • update_transformation()                             │
│  • end_transformation()                                │
│  • cancel_transformation()                             │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴──────────┬──────────────┐
         ▼                      ▼              ▼
┌─────────────────┐   ┌──────────────────┐   ┌────────────┐
│ HandleDetector  │   │ ResizeHandler    │   │   Future   │
│                 │   │                  │   │  Handlers  │
├─────────────────┤   ├──────────────────┤   ├────────────┤
│ • get_handle_   │   │ • can_transform()│   │ • Rotate   │
│   positions()   │   │ • start_         │   │ • Scale    │
│ • detect_handle │   │   transform()    │   │ • Skew     │
│   at_position() │   │ • update_        │   │ • ...      │
│ • get_cursor_   │   │   transform()    │   └────────────┘
│   for_handle()  │   │ • end_transform()│
└─────────────────┘   │ • cancel_        │
                      │   transform()    │
                      └──────────────────┘
```

## 📦 Module Structure

```
src/shypn/edit/transformation/
├── __init__.py              # Exports: TransformHandler, HandleDetector, ResizeHandler
├── transform_handler.py     # Abstract base class (ABC)
├── handle_detector.py       # Geometric calculations
└── resize_handler.py        # Resize implementation
```

## 🔑 Key Classes

### 1. TransformHandler (Abstract Base Class)

**Location**: `src/shypn/edit/transformation/transform_handler.py`

**Purpose**: Define interface for all transformation types

**Abstract Methods** (must implement):
```python
def can_transform(self, obj) -> bool:
    """Check if this handler supports this object type."""
    
def start_transform(self, obj, handle: str, start_x: float, start_y: float):
    """Begin transformation, store original state."""
    
def update_transform(self, current_x: float, current_y: float):
    """Update transformation during drag."""
    
def end_transform(self) -> bool:
    """Complete transformation, return True if successful."""
    
def cancel_transform(self):
    """Cancel and restore original state."""
    
def get_preview_geometry(self) -> Optional[Dict[str, Any]]:
    """Return current geometry for preview rendering."""
```

**Helper Methods** (provided):
```python
def is_transforming(self) -> bool:
    """Check if transformation is active."""
    
def get_original_state(self) -> Optional[Dict[str, Any]]:
    """Get stored original state."""
    
def reset(self):
    """Reset handler state."""
```

### 2. HandleDetector

**Location**: `src/shypn/edit/transformation/handle_detector.py`

**Purpose**: Calculate handle positions and detect clicks

**Key Methods**:
```python
def get_handle_positions(self, obj, zoom: float) -> Dict[str, Tuple[float, float]]:
    """Calculate handle positions for an object.
    Returns: {'n': (x, y), 'ne': (x, y), ...}
    """
    
def detect_handle_at_position(self, obj, screen_x: float, screen_y: float, 
                               zoom: float) -> Optional[str]:
    """Detect which handle (if any) is at given position.
    Returns: 'n', 'ne', 'e', etc. or None
    """
    
def get_cursor_for_handle(self, handle: str) -> str:
    """Get GTK cursor name for a handle.
    Returns: 'n-resize', 'ne-resize', etc.
    """
```

**Handle Names**:
```
    nw ─── n ─── ne
    │             │
    w     obj     e
    │             │
    sw ─── s ─── se
```

### 3. ResizeHandler

**Location**: `src/shypn/edit/transformation/resize_handler.py`

**Purpose**: Implement resize for Places and Transitions

**Key Methods**:
```python
def can_transform(self, obj) -> bool:
    """Supports Place and Transition only."""
    return isinstance(obj, (Place, Transition))

def start_transform(self, obj, handle: str, start_x: float, start_y: float):
    """Store original geometry (radius for Place, width/height for Transition)."""
    
def update_transform(self, current_x: float, current_y: float):
    """Calculate delta and apply resize with constraints."""
    
def end_transform(self) -> bool:
    """Check if anything changed, reset state, return success."""
    
def cancel_transform(self):
    """Restore original geometry from stored state."""
```

**Constraints**:
```python
MIN_PLACE_RADIUS = 10.0
MAX_PLACE_RADIUS = 100.0
MIN_TRANSITION_WIDTH = 20.0
MAX_TRANSITION_WIDTH = 200.0
MIN_TRANSITION_HEIGHT = 10.0
MAX_TRANSITION_HEIGHT = 100.0
```

## 🔄 Event Flow

### 1. User Clicks Handle

```python
# In model_canvas_loader.py: _on_button_press()
world_x, world_y = manager.screen_to_world(event.x, event.y)

if manager.selection_manager.is_edit_mode():
    edit_target = manager.selection_manager.get_edit_target()
    
    # Check if clicking on a handle
    handle = manager.editing_transforms.check_handle_at_position(
        edit_target, world_x, world_y, manager.zoom
    )
    
    if handle:
        # Start transformation
        if manager.editing_transforms.start_transformation(
            edit_target, handle, world_x, world_y
        ):
            state['is_transforming'] = True
            return True
```

### 2. User Drags Handle

```python
# In model_canvas_loader.py: _on_motion_notify()
if state.get('is_transforming', False):
    world_x, world_y = manager.screen_to_world(event.x, event.y)
    manager.editing_transforms.update_transformation(world_x, world_y)
    widget.queue_draw()
    return True
```

### 3. User Releases Mouse

```python
# In model_canvas_loader.py: _on_button_release()
if state.get('is_transforming', False):
    if manager.editing_transforms.end_transformation():
        widget.queue_draw()  # Transformation committed
    state['is_transforming'] = False
    return True
```

### 4. User Presses ESC

```python
# In model_canvas_loader.py: _on_key_press_event()
if event.keyval == Gdk.KEY_Escape:
    if manager.editing_transforms.is_transforming():
        manager.editing_transforms.cancel_transformation()
        widget.queue_draw()  # Restored to original
        return True
```

## 🎨 ObjectEditingTransforms API

**Location**: `src/shypn/edit/object_editing_transforms.py`

```python
class ObjectEditingTransforms:
    """Manages visual feedback and transformation for selected objects."""
    
    # Check if handle is at position
    handle = check_handle_at_position(obj, x, y, zoom) -> Optional[str]
    
    # Start transformation (creates appropriate handler)
    success = start_transformation(obj, handle, x, y) -> bool
    
    # Update during drag
    update_transformation(current_x, current_y)
    
    # End transformation
    success = end_transformation() -> bool
    
    # Cancel transformation
    cancel_transformation()
    
    # Check if transforming
    is_transforming() -> bool
```

## 🧪 Testing

**Test File**: `test_transformation_handlers.py`

**Run tests**:
```bash
cd /home/simao/projetos/shypn
python3 test_transformation_handlers.py
```

**Test Coverage**:
- ✅ HandleDetector position calculations
- ✅ HandleDetector hit detection
- ✅ ResizeHandler Place resize
- ✅ ResizeHandler Transition resize
- ✅ ResizeHandler cancel
- ✅ Size constraints enforcement

## 🔧 Common Code Patterns

### Pattern 1: Check if Object Supports Transformation

```python
from shypn.edit.transformation.resize_handler import ResizeHandler

handler = ResizeHandler(selection_manager)
if handler.can_transform(obj):
    # Object can be resized
    pass
```

### Pattern 2: Get Handle Under Cursor

```python
from shypn.edit.transformation.handle_detector import HandleDetector

detector = HandleDetector()
handle = detector.detect_handle_at_position(obj, x, y, zoom)
if handle:
    print(f"Handle {handle} clicked")
```

### Pattern 3: Start and Update Transformation

```python
# Start
handler.start_transform(obj, 'ne', start_x, start_y)

# Update (repeatedly during drag)
handler.update_transform(current_x, current_y)

# End
if handler.end_transform():
    print("Transformation committed")
```

### Pattern 4: Cancel Transformation

```python
if handler.is_transforming():
    handler.cancel_transform()
    print("Transformation cancelled, object restored")
```

## 🎯 Adding a New Transformation Type

### Step 1: Create Handler Class

```python
# src/shypn/edit/transformation/rotate_handler.py
from shypn.edit.transformation.transform_handler import TransformHandler

class RotateHandler(TransformHandler):
    def __init__(self, selection_manager):
        super().__init__(selection_manager)
        self.original_angle = None
        self.center_point = None
    
    def can_transform(self, obj) -> bool:
        from shypn.netobjs import Transition
        return isinstance(obj, Transition)
    
    def start_transform(self, obj, handle: str, start_x: float, start_y: float):
        self.is_active = True
        self.drag_start_pos = (start_x, start_y)
        self.center_point = (obj.x, obj.y)
        self.original_angle = getattr(obj, 'angle', 0)
        self.original_state = {'angle': self.original_angle}
    
    def update_transform(self, current_x: float, current_y: float):
        # Calculate angle from center to current position
        import math
        dx = current_x - self.center_point[0]
        dy = current_y - self.center_point[1]
        new_angle = math.atan2(dy, dx)
        # Apply to object
        obj = self.selection_manager.get_edit_target()
        obj.angle = new_angle
    
    def end_transform(self) -> bool:
        changed = abs(obj.angle - self.original_angle) > 0.01
        self.reset()
        return changed
    
    def cancel_transform(self):
        obj = self.selection_manager.get_edit_target()
        obj.angle = self.original_angle
        self.reset()
    
    def get_preview_geometry(self) -> Optional[Dict[str, Any]]:
        obj = self.selection_manager.get_edit_target()
        return {'angle': obj.angle} if obj else None
```

### Step 2: Register in ObjectEditingTransforms

```python
# In object_editing_transforms.py: start_transformation()
def start_transformation(self, obj, handle: str, world_x: float, world_y: float):
    # Decide which handler to use
    if handle == 'rotate':  # Or some other condition
        from shypn.edit.transformation.rotate_handler import RotateHandler
        self.active_handler = RotateHandler(self.selection_manager)
    else:
        from shypn.edit.transformation.resize_handler import ResizeHandler
        self.active_handler = ResizeHandler(self.selection_manager)
    
    if self.active_handler.can_transform(obj):
        self.active_handler.start_transform(obj, handle, world_x, world_y)
        return True
    return False
```

### Step 3: Export in __init__.py

```python
# In transformation/__init__.py
from shypn.edit.transformation.rotate_handler import RotateHandler

__all__ = [
    'TransformHandler',
    'HandleDetector',
    'ResizeHandler',
    'RotateHandler',
]
```

## 📚 Documentation

- **Architecture Plan**: `TRANSFORMATION_HANDLERS_PLAN.md`
- **Implementation Summary**: `TRANSFORMATION_HANDLERS_PHASE1_COMPLETE.md`
- **Usage Guide**: `TRANSFORMATION_HANDLERS_USAGE_GUIDE.md`
- **Checklist**: `TRANSFORMATION_HANDLERS_CHECKLIST.md`
- **This File**: `TRANSFORMATION_HANDLERS_DEV_REFERENCE.md`
- **Module README**: `src/shypn/edit/README.md`

## 🐛 Debugging Tips

### Enable Debug Output

```python
# In resize_handler.py
def update_transform(self, current_x: float, current_y: float):
    print(f"DEBUG: update_transform({current_x}, {current_y})")
    print(f"  Object: {self.object_being_resized}")
    print(f"  Handle: {self.active_handle}")
    # ... rest of method
```

### Check Handle Detection

```python
# In handle_detector.py
def detect_handle_at_position(self, obj, screen_x, screen_y, zoom):
    positions = self.get_handle_positions(obj, zoom)
    print(f"DEBUG: Checking position ({screen_x}, {screen_y})")
    print(f"  Handle positions: {positions}")
    # ... rest of method
```

### Verify State Management

```python
# Check if transformation is active
if manager.editing_transforms.is_transforming():
    handler = manager.editing_transforms.active_handler
    print(f"Active handler: {handler.__class__.__name__}")
    print(f"Original state: {handler.get_original_state()}")
```

## 🚀 Performance Considerations

- **Lazy Initialization**: HandleDetector is only created when needed
- **Efficient Hit Testing**: Simple distance calculations, no complex geometry
- **Minimal Redraws**: Only queue_draw() when transformation updates
- **State Caching**: Original geometry stored once at start

## ✅ Best Practices

1. **Always call `reset()`** after end or cancel
2. **Check `is_transforming()`** before operations
3. **Store original state** for undo/cancel
4. **Enforce constraints** in update_transform()
5. **Use type hints** for better IDE support
6. **Document handle behavior** for new handlers
7. **Test thoroughly** with unit tests

---

**Quick Start**: Read `TRANSFORMATION_HANDLERS_USAGE_GUIDE.md` for user instructions.  
**Full Details**: Read `TRANSFORMATION_HANDLERS_PLAN.md` for complete architecture.
