# Drag Controller Integration - Editing Layer Approach

**Date**: October 3, 2025  
**Status**: Ready for editing layer integration  
**Recommendation**: Integrate via SelectionManager, not ModelCanvasLoader

## Architecture Decision

The drag controller should be integrated at the **editing layer**, not the loader layer.

### Why Not in Loader?

The `ModelCanvasLoader` handles **raw GTK events** and routing:
- Mouse button press/release
- Motion events  
- Key press events
- Scroll events

It should **not** handle:
- Object manipulation logic
- Selection state management
- Transform operations
- Editing behavior

### Correct Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  ModelCanvasLoader                      │
│  (Raw GTK event handling and routing)                   │
│  • Captures mouse/keyboard events                       │
│  • Routes to appropriate handlers                       │
│  • Manages canvas state (pan, zoom)                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ Delegates editing events to
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Editing Layer (shypn.edit)                 │
│  • SelectionManager - Selection state                   │
│  • DragController - Object dragging (READY)            │
│  • ObjectEditingTransforms - Transform handles         │
│  • RectangleSelection - Rubber-band selection          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ Operates on
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Data Objects (netobjs)                     │
│  • Place, Transition, Arc                               │
│  • Direct property manipulation (x, y, etc.)           │
└─────────────────────────────────────────────────────────┘
```

## Current Status

### ✅ DragController Ready
- **Location**: `src/shypn/edit/drag_controller.py`
- **Status**: Fully implemented and tested
- **Tests**: `tests/test_drag_integration.py` (all passing)
- **Size**: ~12KB, 370 lines

### ✅ SelectionManager Exists
- **Location**: `src/shypn/edit/selection_manager.py`
- **Current**: Handles selection state and edit mode
- **Needs**: Integration point for DragController

### ❌ Integration Not Yet Done
- DragController exists but is not connected
- SelectionManager doesn't use it yet
- Objects can be selected but not dragged with DragController

## Recommended Integration Strategy

### Option 1: Extend SelectionManager (Recommended)

Add drag handling to SelectionManager since it already manages selected objects:

```python
# In src/shypn/edit/selection_manager.py

from shypn.edit.drag_controller import DragController

class SelectionManager:
    def __init__(self):
        # ... existing code ...
        self.drag_controller = DragController()
    
    def start_drag_if_selected(self, screen_x, screen_y, clicked_obj, manager):
        """Start dragging if clicking on selected object."""
        if clicked_obj and clicked_obj.selected:
            selected_objs = self.get_selected_objects(manager)
            self.drag_controller.start_drag(selected_objs, screen_x, screen_y)
            return True
        return False
    
    def update_drag(self, screen_x, screen_y, canvas):
        """Update drag positions."""
        if self.drag_controller.is_dragging():
            self.drag_controller.update_drag(screen_x, screen_y, canvas)
            return True
        return False
    
    def end_drag(self):
        """End drag operation."""
        if self.drag_controller.is_dragging():
            self.drag_controller.end_drag()
            return True
        return False
    
    def cancel_drag(self):
        """Cancel drag and restore positions."""
        if self.drag_controller.is_dragging():
            self.drag_controller.cancel_drag()
            return True
        return False
```

Then the loader just calls SelectionManager methods:

```python
# In model_canvas_loader.py button press handler
if clicked_obj and clicked_obj.selected:
    manager.selection_manager.start_drag_if_selected(
        event.x, event.y, clicked_obj, manager
    )

# In motion handler
manager.selection_manager.update_drag(event.x, event.y, manager)

# In button release handler
manager.selection_manager.end_drag()

# In key press handler (ESC key)
manager.selection_manager.cancel_drag()
```

### Option 2: Separate Editing Controller

Create a higher-level editing controller that orchestrates SelectionManager and DragController:

```python
# New file: src/shypn/edit/editing_controller.py

class EditingController:
    def __init__(self, selection_manager):
        self.selection_manager = selection_manager
        self.drag_controller = DragController()
    
    def handle_button_press(self, event, clicked_obj, manager):
        """Handle button press for editing operations."""
        # Check if should start drag
        if clicked_obj and clicked_obj.selected:
            selected = self.selection_manager.get_selected_objects(manager)
            self.drag_controller.start_drag(selected, event.x, event.y)
    
    def handle_motion(self, event, manager):
        """Handle motion for editing operations."""
        if self.drag_controller.is_dragging():
            self.drag_controller.update_drag(event.x, event.y, manager)
            return True
        return False
    
    # ... etc
```

## Benefits of Editing Layer Integration

### 1. Separation of Concerns ✅
- Loader: Event routing
- Editing: Object manipulation
- Data: Object storage

### 2. Testability ✅
- Can test editing logic without GTK
- Mock events at editing layer
- Unit test drag behavior

### 3. Maintainability ✅
- Editing logic in one place
- Easy to find and modify
- Clear responsibilities

### 4. Extensibility ✅
- Easy to add new editing modes
- Can add undo/redo at editing layer
- Transform handles work together with drag

### 5. Reusability ✅
- Editing layer can be used by other UI frameworks
- Not tied to GTK specifics
- Clean API for programmatic manipulation

## Current Drag Behavior (Legacy)

The loader currently has inline drag code:

**In motion handler** (~line 680):
```python
# Handle dragging only if button is pressed
if state['active'] and state['button'] > 0:
    # ... drag logic mixed with pan logic ...
```

**Problems**:
- Drag logic mixed with pan logic
- Hard to test
- No grid snapping
- No axis constraints
- No cancel support
- Responsibilities unclear

## Migration Path

### Phase 1: Extend SelectionManager
1. Add DragController to SelectionManager
2. Add drag methods to SelectionManager API
3. Update loader to call SelectionManager methods
4. Test with existing objects

### Phase 2: Clean Up Loader
1. Remove inline drag code from loader
2. Simplify motion handler
3. Verify all functionality works
4. Update documentation

### Phase 3: Add Advanced Features
1. Grid snapping (already in DragController)
2. Axis constraints (Shift/Ctrl keys)
3. Cancel with ESC key
4. Callbacks for undo support

## Summary

### ✅ What's Ready
- DragController fully implemented
- Tests passing
- Documentation complete
- Architecture designed

### ❌ What's Needed
- Integration into SelectionManager or EditingController
- Update loader to call editing layer
- Remove inline drag code from loader
- Test end-to-end with GTK UI

### 🎯 Recommendation

**Option 1** (Extend SelectionManager) is recommended because:
- SelectionManager already owns selected objects
- Minimal new code needed
- Clear responsibility (selection + manipulation)
- Easy to integrate into existing code

### Next Steps

1. **Review** current SelectionManager API
2. **Add** drag methods to SelectionManager
3. **Update** loader to delegate to SelectionManager
4. **Test** with GTK UI
5. **Clean up** inline drag code
6. **Document** new editing layer architecture

---

**The drag controller is production-ready, just needs proper integration at the editing layer level.** ✅
