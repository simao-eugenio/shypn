# Phase 5 Side Effects - Fix Plan

**Date**: October 18, 2025

## Issues Identified

1. ✅ **SBML Import** - Working correctly
2. ❌ **KEGG Import** - `invalid literal for int() with base 10` error
3. ❌ **Open File** - Loads but doesn't render (objects off-screen)
4. ❌ **Double-Click File** - Same as #3
5. ❌ **Coordinates** - Need to center on canvas middle, accounting for pan/zoom

## Root Cause Analysis

### Issue #2: KEGG Import Error
The error "invalid literal for int()" suggests somewhere we're trying to convert a non-numeric string to int. This is likely in the entry ID parsing where KEGG uses strings like "cpd:C00031" but code expects integers.

### Issues #3-4: File Loading Not Rendering
Files load successfully (objects are in memory) but don't appear on canvas. This means:
- Objects exist (`load_objects()` works)
- Draw callback is connected
- **BUT**: Objects are positioned far from viewport origin
- `fit_to_page()` with `deferred=True` might not be executing

### Issue #5: Canvas Centering
When loading objects, they should be centered on the canvas middle point, accounting for:
- Current pan position
- Current zoom level
- Canvas dimensions (viewport width/height)

The `fit_to_page()` method exists but isn't working for file loads.

## Solution Strategy

### Fix 1: KEGG Entry ID Handling
Ensure all entry IDs are kept as strings (never convert to int):
- ✅ `KEGGEntry.id` is already `str` in models.py
- ❌ Check if somewhere we're doing `int(entry.id)`
- ❌ Check arc builder or converter code

### Fix 2: File Load Rendering
The issue is that `fit_to_page()` is only called in SBML/KEGG import, not in file loading!

**Current code** (`file_explorer_panel.py`):
```python
manager.load_objects(places=..., transitions=..., arcs=...)
# ❌ Missing: fit_to_page() call!
drawing_area.queue_draw()
```

**Should be**:
```python
manager.load_objects(places=..., transitions=..., arcs=...)
manager.fit_to_page(padding_percent=15, deferred=True)  # ✅ Add this!
drawing_area.queue_draw()
```

### Fix 3: Deferred fit_to_page Execution
The `deferred=True` flag means fit_to_page waits for first draw to get viewport dimensions. We need to ensure:
1. Flag is set correctly
2. Draw callback checks for pending flag
3. Execution happens on first draw

**Current flow**:
```
1. load_objects() called
2. fit_to_page(deferred=True) sets manager._fit_to_page_pending = True
3. drawing_area.queue_draw() triggers draw
4. _on_draw() checks _fit_to_page_pending
5. If True: executes fit_to_page(deferred=False)
```

This should work, so issue might be:
- Flag not being set
- Flag being cleared prematurely
- Viewport dimensions not available

### Fix 4: Canvas Centering Formula
The `fit_to_page()` method should:
1. Calculate bounding box of all objects
2. Calculate scale to fit with padding
3. Calculate pan to center the bounding box
4. Apply zoom and pan

Formula:
```python
# Get bounding box
min_x, min_y, max_x, max_y = get_bounding_box(objects)
bbox_width = max_x - min_x
bbox_height = max_y - min_y
bbox_center_x = (min_x + max_x) / 2
bbox_center_y = (min_y + max_y) / 2

# Calculate zoom to fit
padding = 0.15  # 15%
zoom_x = viewport_width / (bbox_width * (1 + padding))
zoom_y = viewport_height / (bbox_height * (1 + padding))
zoom = min(zoom_x, zoom_y)  # Use smaller to fit both dimensions

# Calculate pan to center bbox at viewport center
viewport_center_x = viewport_width / 2
viewport_center_y = viewport_height / 2

# Pan in world coordinates
pan_x = viewport_center_x / zoom - bbox_center_x
pan_y = viewport_center_y / zoom - bbox_center_y
```

## Implementation Plan

### Step 1: Find and Fix KEGG int() Error
Search for where entry IDs might be converted to int.

### Step 2: Add fit_to_page() to File Loading
Modify `file_explorer_panel.py` to call fit_to_page after loading.

### Step 3: Verify Deferred Execution
Check that `_on_draw()` properly executes pending fit_to_page.

### Step 4: Test Canvas Centering
Verify that objects are centered correctly with proper zoom.

## Testing Plan

1. **KEGG Import**: Import hsa00010, verify no int() error
2. **File Open**: Open existing .shy file, verify objects visible and centered
3. **File Double-Click**: Same as #2
4. **Centering**: Objects should be centered in viewport
5. **Zoom/Pan**: After fit, objects should fill viewport with padding

## Files to Modify

1. `src/shypn/helpers/file_explorer_panel.py` - Add fit_to_page() call
2. `src/shypn/helpers/kegg_import_panel.py` - Fix int() conversion (if found)
3. `src/shypn/data/model_canvas_manager.py` - Verify fit_to_page() logic
4. `src/shypn/helpers/model_canvas_loader.py` - Verify deferred execution

---

**Next**: Implement fixes starting with file loading (easiest to verify).
