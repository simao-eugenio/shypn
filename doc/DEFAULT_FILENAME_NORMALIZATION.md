# Default Filename Normalization

**Date**: October 4, 2025  
**Status**: ✅ Implemented  
**Default Filename**: `"default"`

## Summary

Normalized the default filename handling across all canvas initialization and clear operations. The canvas now consistently uses `"default"` as the filename property for new/unsaved documents.

## Implementation

### 1. **Canvas Manager Initialization**

The `ModelCanvasManager` always initializes with `"default"` filename:

```python
def __init__(self, canvas_width=2000, canvas_height=2000, filename="default"):
    """Initialize the canvas manager.
    
    Args:
        filename: Base filename without extension (default: "default").
    """
    self.filename = filename  # Always starts as "default" for new documents
```

### 2. **Clear Canvas Behavior**

Updated `clear_all_objects()` to reset to "default" state:

```python
def clear_all_objects(self):
    """Remove all Petri net objects and reset to new document state."""
    self.places.clear()
    self.transitions.clear()
    self.arcs.clear()
    
    # Reset ID counters
    self._next_place_id = 1
    self._next_transition_id = 1
    self._next_arc_id = 1
    
    # Reset to default filename (unsaved document state)
    self.filename = "default"
    self.modified = False
    self.created_at = datetime.now()
    self.modified_at = None
    
    self.mark_dirty()
```

**Changes from previous implementation:**
- Now resets `filename` to `"default"`
- Sets `modified = False` (was calling `mark_modified()`)
- Resets timestamps to indicate new document
- Removes `mark_modified()` call (since it's a fresh state)

### 3. **Context Menu Integration**

Updated canvas context menu "Clear Canvas" action:

```python
def _on_clear_canvas_clicked(self, menu, drawing_area, manager):
    """Clear the canvas and reset to default state.
    
    This removes all objects and resets the document to "default" filename
    state (unsaved), as if creating a new document.
    """
    manager.clear_all_objects()
    drawing_area.queue_draw()
```

**Previous implementation:**
```python
# TODO: Implement canvas clearing when we have objects
drawing_area.queue_draw()
```

### 4. **Save Dialog Pre-fill**

When saving a document with `filename="default"`, the save dialog pre-fills with `"default.shy"`:

```python
# In NetObjPersistency._show_save_dialog()
if self.current_filepath:
    dialog.set_filename(self.current_filepath)
else:
    # Pre-fill with "default.shy" to prompt user to change it
    default_name = "default.shy"
    dialog.set_current_name(default_name)
```

### 5. **Default Filename Warning**

When user tries to save as `"default.shy"`, they see a warning:

```python
if filename.lower() == "default.shy":
    # Show warning dialog
    warning_dialog = Gtk.MessageDialog(
        parent=self.parent_window,
        flags=Gtk.DialogFlags.MODAL,
        type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.YES_NO,
        text="Save as 'default.shy'?"
    )
    warning_dialog.format_secondary_text(
        "You are about to save with the default filename 'default.shy'.\n\n"
        "This may overwrite existing default files or make it hard to "
        "identify this model later.\n\n"
        "Do you want to continue with this filename?"
    )
    
    warning_response = warning_dialog.run()
    warning_dialog.destroy()
    
    if warning_response != Gtk.ResponseType.YES:
        # User wants to change the filename, show dialog again
        return self._show_save_dialog()
```

## Use Cases

### **New Canvas**
```python
# Canvas is created
manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
manager.create_new_document()

assert manager.filename == "default"
assert manager.modified == False

# User clicks Save
# Dialog shows "default.shy" pre-filled
# Warning appears if user keeps "default.shy"
```

### **Clear Canvas (Context Menu)**
```python
# User has a canvas with objects
assert len(manager.places) > 0
assert manager.filename == "mymodel"

# User right-clicks → "Clear Canvas"
manager.clear_all_objects()

assert len(manager.places) == 0
assert manager.filename == "default"  # Reset to default!
assert manager.modified == False
```

### **Clear Canvas (Programmatic)**
```python
# Clear from code
manager.clear_all_objects()

# State is now fresh
assert manager.filename == "default"
assert manager.modified == False
assert manager.created_at is recent
assert manager.modified_at is None
```

## Benefits

### ✅ **Consistency**
- All new/cleared canvases start with `"default"` filename
- No ambiguity about unsaved document state

### ✅ **User Awareness**
- Pre-filled "default.shy" in save dialog is obvious
- Warning dialog prevents accidental default saves
- Clear indication that filename should be changed

### ✅ **Clean State**
- Clearing canvas fully resets to new document state
- No leftover metadata or modified flags
- Timestamps properly reset

### ✅ **File System Organization**
- Prevents proliferation of "untitled" files
- Encourages meaningful filenames
- Default files are clearly identified

## File Changes

### Modified Files

1. **`src/shypn/data/model_canvas_manager.py`**
   - `clear_all_objects()`: Now resets to "default" filename and fresh state
   - Documentation updated to clarify behavior

2. **`src/shypn/helpers/model_canvas_loader.py`**
   - `_on_clear_canvas_clicked()`: Updated to use `clear_all_objects()`
   - Removed TODO comment, fully implemented

3. **`src/shypn/file/netobj_persistency.py`** (already implemented)
   - Pre-fills save dialog with "default.shy"
   - Shows warning when saving as "default.shy"

## Testing

### Manual Test Procedure

1. **Test New Canvas**:
   ```bash
   ./run.sh
   # Create new canvas
   # Draw something
   # Click Save
   # Verify "default.shy" is pre-filled
   # Try to save as "default.shy"
   # Verify warning appears
   ```

2. **Test Clear Canvas**:
   ```bash
   ./run.sh
   # Draw some objects
   # Right-click → Clear Canvas
   # All objects removed
   # Click Save
   # Verify "default.shy" appears again (reset to default)
   ```

3. **Test Save After Clear**:
   ```bash
   # Open existing file "mymodel.shy"
   # Right-click → Clear Canvas
   # Canvas cleared
   # Click Save
   # Should prompt with "default.shy" (not "mymodel.shy")
   ```

## Future Enhancements

### Possible Improvements

1. **Numbered Defaults**: `"default_1.shy"`, `"default_2.shy"`, etc.
2. **Timestamp Defaults**: `"untitled_20251004_103045.shy"`
3. **Template Names**: `"new_petri_net_001.shy"`
4. **Smart Naming**: Suggest names based on model content
5. **Recent Names**: Remember and suggest recently used names

---

**Status**: ✅ Fully implemented and ready for testing!
