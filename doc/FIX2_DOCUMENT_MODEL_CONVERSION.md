# Fix #2: AttributeError - ModelCanvasManager has no 'document' attribute

## Issue

After fixing the `get_current_document()` method, a new error appeared:

```python
AttributeError: 'ModelCanvasManager' object has no attribute 'document'
```

**Error Location:** `file_explorer_panel.py` line 1177:
```python
if manager is None or manager.document is None:  # ❌ manager doesn't have 'document'
```

## Root Cause

**Architectural Mismatch:**

The code was trying to access `manager.document`, but:

1. **`ModelCanvasManager`** stores Petri net objects directly:
   - `self.places: List[Place]`
   - `self.transitions: List[Transition]`
   - `self.arcs: List[Arc]`

2. **`NetObjPersistency.save_document()`** expects a `DocumentModel` instance:
   ```python
   def save_document(self, document, save_as, is_default_filename):
       document.save_to_file(self.current_filepath)  # Needs DocumentModel
   ```

3. **The gap:** No conversion between `ModelCanvasManager` and `DocumentModel`

## The Fix

### 1. Added `to_document_model()` method to `ModelCanvasManager`

**File:** `src/shypn/data/model_canvas_manager.py`

```python
def to_document_model(self):
    """Convert canvas manager's Petri net objects to a DocumentModel.
    
    This creates a DocumentModel instance that can be saved/loaded by
    the persistency manager.
    
    Returns:
        DocumentModel: Document model containing all Petri net objects
    """
    from shypn.data.canvas import DocumentModel
    
    document = DocumentModel()
    document.places = list(self.places)
    document.transitions = list(self.transitions)
    document.arcs = list(self.arcs)
    
    # Sync ID counters
    document._next_place_id = self._next_place_id
    document._next_transition_id = self._next_transition_id
    document._next_arc_id = self._next_arc_id
    
    return document
```

### 2. Updated `save_current_document()` to use the new method

**File:** `src/shypn/ui/panels/file_explorer_panel.py`

**Before:**
```python
manager = self.canvas_loader.get_canvas_manager(drawing_area)
if manager is None or manager.document is None:  # ❌ Doesn't exist
    return

self.persistency.save_document(
    manager.document,  # ❌ Doesn't exist
    save_as=False,
    is_default_filename=manager.is_default_filename()
)
```

**After:**
```python
manager = self.canvas_loader.get_canvas_manager(drawing_area)
if manager is None:  # ✅ Check only manager
    return

# ✅ Convert to DocumentModel
document = manager.to_document_model()

self.persistency.save_document(
    document,  # ✅ Pass DocumentModel
    save_as=False,
    is_default_filename=manager.is_default_filename()
)
```

### 3. Updated `save_current_document_as()` similarly

Same pattern applied to the Save As operation.

## Why This Design?

**Separation of Concerns:**

1. **`ModelCanvasManager`**: 
   - Manages canvas rendering, viewport, transformations
   - Stores Petri net objects for drawing
   - Manages UI state (selection, tools, etc.)

2. **`DocumentModel`**:
   - Pure data storage for serialization
   - No UI dependencies
   - Simple serialization interface (`save_to_file`, `load_from_file`)

3. **Conversion Layer**:
   - `to_document_model()` bridges the gap
   - Allows each class to focus on its responsibility
   - Clean separation between UI/rendering and persistence

## Files Modified

```
src/shypn/data/model_canvas_manager.py       (Added to_document_model() method)
src/shypn/ui/panels/file_explorer_panel.py   (Updated save methods to use conversion)
```

## Testing

After this fix, the save operation should:

1. Get the current drawing area ✅ (Fixed in Fix #1)
2. Get the canvas manager ✅
3. Convert to DocumentModel ✅ (Fixed in Fix #2)
4. Check `is_default_filename()` flag ✅
5. Show file chooser if needed ✅
6. Save to file ✅

**Expected Console Output:**
```
[FileExplorer] save_current_document() called
[FileExplorer] Manager filename: 'default'
[FileExplorer] is_default_filename(): True
[FileExplorer] Calling save_document with is_default_filename=True
[Persistency] save_document() called with save_as=False, is_default_filename=True
[Persistency] needs_prompt = True
[Persistency] Showing file chooser dialog
```

Then the file chooser should appear!

## Summary

**Fix #1:** Updated `get_current_document()` to handle Overlay structure  
**Fix #2:** Added `to_document_model()` to bridge ModelCanvasManager → DocumentModel

Both fixes address structural/architectural mismatches introduced by feature additions:
- Fix #1: Zoom overlay feature changed widget hierarchy
- Fix #2: Persistence layer needs DocumentModel, not direct manager access

---

🎯 **Ready for testing:** Run the app and click Save button to verify file chooser appears!
