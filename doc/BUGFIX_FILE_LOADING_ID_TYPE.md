# Bug Fix: File Loading Issues

**Date**: October 7, 2025  
**Status**: ✅ FIXED

## Problems

### Problem 1: File Loading Crash Due to ID Type Mismatch

When opening a saved `.shy` file, the application would crash with:
```
TypeError: can only concatenate str (not "int") to str
```

### Problem 2: Empty Canvas After File > Open

When using File > Open menu, the file would load without errors, but the canvas would remain empty with no objects visible.

## Root Causes

### Cause 1: ID Type Mismatch

In `document_model.py`, the `from_dict()` method was trying to do arithmetic operations on object IDs:

```python
# BUGGY CODE:
document._next_place_id = max(document._next_place_id, place.id + 1)
document._next_transition_id = max(document._next_transition_id, transition.id + 1)
document._next_arc_id = max(document._next_arc_id, arc.id + 1)
```

The problem: `place.id`, `transition.id`, and `arc.id` are **strings** like "P1", "T1", "A1", not integers.

### Cause 2: Missing Canvas Loading in Callback

In `file_explorer_panel.py`, the `_on_file_loaded_callback()` method (called by `NetObjPersistency` when File > Open is used) was only updating the UI display but NOT actually loading the document objects into the canvas manager:

```python
# BUGGY CODE:
def _on_file_loaded_callback(self, filepath: str, document):
    self.set_current_file(filepath)  # Only updates UI, doesn't load objects!
```

## Solutions

### Solution 1: Extract Numeric Part from String IDs

Extract the numeric part from the string IDs before doing arithmetic:

```python
# FIXED CODE:
if isinstance(place.id, str) and place.id.startswith('P'):
    try:
        place_num = int(place.id[1:])  # Extract "1" from "P1"
        document._next_place_id = max(document._next_place_id, place_num + 1)
    except (ValueError, IndexError):
        pass
```

Applied the same fix for transitions (starting with "T") and arcs (starting with "A").

### Solution 2: Load Document into Canvas in Callback

Modified `_on_file_loaded_callback()` to actually load the document into the canvas:

```python
# FIXED CODE:
def _on_file_loaded_callback(self, filepath: str, document):
    # Load the document into the canvas
    self._load_document_into_canvas(document, filepath)
    
    # Update the current file display
    self.set_current_file(filepath)
```

## Files Modified

- `src/shypn/data/canvas/document_model.py` (lines 436, 445, 453)
  - Fixed `from_dict()` method to properly parse string IDs

- `src/shypn/ui/panels/file_explorer_panel.py`
  - Fixed `_on_file_loaded_callback()` to load document into canvas
  - Added comprehensive debug logging
  - Added `ensure_arc_references()` and `mark_dirty()` calls in `_load_document_into_canvas()`

## Testing

Created test file `/tmp/test_visible.shy` with:
- 2 places (P1, P2)
- 1 transition (T1)

Verified:
- ✅ File loads without errors
- ✅ Objects are restored correctly
- ✅ ID counters are updated properly  
- ✅ Objects appear on canvas after File > Open
- ✅ Objects appear on canvas after double-click in file explorer

## Debug Output Added

Added debug logging to `file_explorer_panel.py` to help diagnose file loading issues:
- Logs when file loading starts
- Shows object counts from loaded document
- Shows object counts before/after restoration to canvas manager
- Confirms arc references are updated
- Confirms manager is marked dirty for redraw

## Impact

**Before**: 
- Opening saved files would crash OR show empty canvas
- File > Open menu didn't work
- Objects were not visible after loading

**After**: 
- Files load correctly with all objects restored
- Both File > Open and file explorer double-click work
- All objects visible on canvas immediately after loading
