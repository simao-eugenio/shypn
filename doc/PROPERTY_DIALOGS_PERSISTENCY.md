# Property Dialogs Persistency Integration

## Overview

This document describes the implementation of persistency integration with object property dialogs. When users modify object properties through the UI dialogs, the document is now automatically marked as "dirty" (having unsaved changes), triggering the file system to track these modifications.

## Architecture

### Component Responsibilities

1. **Property Dialog Loaders** (`PlacePropDialogLoader`, `ArcPropDialogLoader`, `TransitionPropDialogLoader`)
   - Load and display property dialog UI
   - Populate fields with current object properties
   - Apply changes to objects when OK is clicked
   - **NEW**: Mark document as dirty via persistency manager
   - **NEW**: Emit `properties-changed` signal for observers

2. **NetObjPersistency**
   - Tracks dirty state (unsaved changes)
   - Provides `mark_dirty()` and `mark_clean()` methods
   - Notifies observers via `on_dirty_changed` callback
   - Handles save/load dialogs and file operations

3. **ModelCanvasLoader**
   - Creates and manages property dialogs
   - Passes persistency manager to dialog loaders
   - Connects to `properties-changed` signal for canvas redraw

4. **FileExplorerPanel**
   - Listens to `on_dirty_changed` callback
   - Updates file tree view with visual indicators (e.g., asterisk)
   - Provides visual feedback for unsaved changes

## Implementation Details

### 1. Property Dialog Loaders

All three dialog loaders (`PlacePropDialogLoader`, `ArcPropDialogLoader`, `TransitionPropDialogLoader`) were updated with the following changes:

#### Changes Made:

**A. Added GObject Signal Support**
```python
class PlacePropDialogLoader(GObject.GObject):
    """..."""
    
    __gsignals__ = {
        'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
```

**B. Added Persistency Manager Parameter**
```python
def __init__(self, place_obj, parent_window=None, ui_dir: str = None, persistency_manager=None):
    """...
    Args:
        ...
        persistency_manager: NetObjPersistency instance for marking document dirty
    """
    super().__init__()
    ...
    self.persistency_manager = persistency_manager
```

**C. Updated Response Handler to Mark Dirty**
```python
def _on_response(self, dialog, response_id):
    """Handle dialog response (OK/Cancel)."""
    if response_id == Gtk.ResponseType.OK:
        self._apply_changes()
        
        # Mark document as dirty if persistency manager is available
        if self.persistency_manager:
            self.persistency_manager.mark_dirty()
            print(f"[PlacePropDialogLoader] Document marked as dirty")
        
        # Emit signal to notify observers (for canvas redraw)
        self.emit('properties-changed')
    
    dialog.destroy()
```

**D. Updated Factory Functions**
```python
def create_place_prop_dialog(place_obj, parent_window=None, ui_dir: str = None, persistency_manager=None):
    """Factory function to create a Place properties dialog loader.
    
    Args:
        ...
        persistency_manager: NetObjPersistency instance for marking document dirty
    """
    return PlacePropDialogLoader(
        place_obj, 
        parent_window=parent_window, 
        ui_dir=ui_dir, 
        persistency_manager=persistency_manager
    )
```

### 2. ModelCanvasLoader Integration

Updated `_on_object_properties()` method to:

1. **Pass persistency manager** to dialog loaders
2. **Connect to signal** for canvas redraw
3. **Ensure canvas updates** after property changes

```python
def _on_object_properties(self, obj, manager, drawing_area):
    """Open properties dialog for an object."""
    from shypn.helpers.place_prop_dialog_loader import create_place_prop_dialog
    # ... other imports
    
    if isinstance(obj, Place):
        dialog_loader = create_place_prop_dialog(
            obj, 
            parent_window=self.parent_window,
            persistency_manager=self.persistency  # ← Pass persistency manager
        )
    # ... similar for Transition and Arc
    
    # Connect to properties-changed signal for canvas redraw
    dialog_loader.connect('properties-changed', lambda _: drawing_area.queue_draw())
    
    # Run dialog
    response = dialog_loader.run()
    
    # Redraw canvas (backup in case signal didn't fire)
    if response == Gtk.ResponseType.OK:
        drawing_area.queue_draw()
```

## Data Flow

### Property Change Flow

```
User opens property dialog
    ↓
Dialog displays current object properties
    ↓
User modifies properties
    ↓
User clicks OK
    ↓
Dialog._on_response() called
    ↓
Dialog._apply_changes() → modifies object
    ↓
persistency_manager.mark_dirty() → sets dirty flag
    ↓
persistency_manager.on_dirty_changed(True) → notifies observers
    ↓
FileExplorerPanel._on_dirty_changed_callback() → updates tree view
    ↓
Dialog.emit('properties-changed') → triggers canvas redraw
    ↓
drawing_area.queue_draw() → canvas redraws with new properties
```

### Visual Feedback Chain

```
Property changed → mark_dirty() → on_dirty_changed callback → File tree shows asterisk (*)
                                                             ↓
Property changed → properties-changed signal → queue_draw() → Canvas redraws
```

## Benefits

### 1. **Automatic Dirty State Tracking**
- No manual tracking needed
- Consistent across all property dialogs
- Works for all object types (Place, Transition, Arc)

### 2. **Visual Feedback**
- File explorer shows asterisk (*) for unsaved files
- Users know when changes need to be saved
- Prevents accidental data loss

### 3. **Integration with File Operations**
- Save dialog prompts when closing unsaved documents
- "Save As" operation works correctly with dirty state
- File reloading checks for unsaved changes

### 4. **Clean Architecture**
- Single Responsibility Principle maintained
- Dialog loaders focus on UI
- Persistency manager handles dirty state
- Canvas loader coordinates interactions

### 5. **Extensibility**
- Easy to add new property dialogs
- Signal-based communication allows multiple observers
- Persistency manager can be shared across components

## Testing

### Manual Test Procedure

1. **Test Place Properties**
   ```
   1. Open application
   2. Create a Place object
   3. Right-click → Properties
   4. Change name or marking
   5. Click OK
   6. Verify:
      - Console shows "[PlacePropDialogLoader] Document marked as dirty"
      - File tree shows asterisk (*) next to filename
      - Canvas redraws with new properties
   ```

2. **Test Transition Properties**
   ```
   1. Create a Transition object
   2. Right-click → Properties
   3. Change name or label
   4. Click OK
   5. Verify dirty flag and canvas redraw
   ```

3. **Test Arc Properties**
   ```
   1. Create Place and Transition
   2. Draw Arc between them
   3. Right-click Arc → Properties
   4. Change weight or label
   5. Click OK
   6. Verify dirty flag and canvas redraw
   ```

4. **Test Save Workflow**
   ```
   1. Modify object properties
   2. File → Save (Ctrl+S)
   3. Verify:
      - File is saved
      - Asterisk (*) disappears
      - Dirty state cleared
   ```

5. **Test Close with Unsaved Changes**
   ```
   1. Modify object properties
   2. Try to close tab or application
   3. Verify:
      - Dialog appears: "Document has unsaved changes"
      - Options: Save / Discard / Cancel
      - Correct behavior for each option
   ```

## Files Modified

### Core Implementation
1. **`src/shypn/helpers/place_prop_dialog_loader.py`**
   - Added `persistency_manager` parameter
   - Added `__gsignals__` for `properties-changed`
   - Updated `_on_response()` to mark dirty and emit signal
   - Updated factory function

2. **`src/shypn/helpers/arc_prop_dialog_loader.py`**
   - Same changes as place dialog loader

3. **`src/shypn/helpers/transition_prop_dialog_loader.py`**
   - Same changes as place dialog loader

4. **`src/shypn/helpers/model_canvas_loader.py`**
   - Updated `_on_object_properties()` to pass persistency manager
   - Connected to `properties-changed` signal
   - Ensured canvas redraw after property changes

## Technical Notes

### GObject Signals
- Used `__gsignals__` to define custom signal
- Signal: `properties-changed` with no parameters
- Emitted after properties are applied successfully

### Persistency Manager Reference
- Passed as optional parameter (backward compatible)
- Checked before use: `if self.persistency_manager:`
- Allows testing without full persistency setup

### Canvas Redraw Strategy
- Primary: Signal-based (`properties-changed` → `queue_draw()`)
- Backup: Direct call after dialog closes (OK response)
- Ensures canvas always reflects current state

## Future Enhancements

### Possible Improvements

1. **Granular Dirty Tracking**
   - Track which objects were modified
   - Allow selective save/discard per object
   - Show object-specific change indicators

2. **Undo/Redo Integration**
   - Property changes become undoable operations
   - Integrate with command pattern
   - Stack-based undo history

3. **Property Validation**
   - Validate property values before applying
   - Show error messages in dialog
   - Prevent invalid states

4. **Property Change Events**
   - Emit events with old and new values
   - Allow observers to react to specific changes
   - Support property-specific logic

5. **Batch Property Changes**
   - Select multiple objects
   - Edit properties together
   - Single dirty mark for batch operation

## Conclusion

The persistency integration with property dialogs provides a robust foundation for tracking document changes. The implementation follows clean architecture principles, maintains backward compatibility, and provides clear visual feedback to users. The signal-based approach allows for easy extension and integration with future features like undo/redo and collaborative editing.
