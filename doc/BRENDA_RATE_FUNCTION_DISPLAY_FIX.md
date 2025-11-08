# BRENDA Rate Function Display Fix

## Problem Summary
After applying BRENDA parameters to a transition, the rate function would not appear in the transition properties dialog, even though verification logs showed it was correctly stored in `transition.properties['rate_function']`.

## Root Cause Analysis

### Investigation Process
1. **User Report**: "I don't see when opening transition property the rate function altered, it is the same"
2. **Verification**: Logs confirmed rate function WAS being stored correctly
3. **Comparison**: Examined heuristic parameters flow which DOES work correctly
4. **Discovery**: Found the missing step

### The Missing Step: `mark_dirty()`

Compared the working heuristic flow with the BRENDA flow:

**Heuristic Flow** (from `heuristic_parameters_controller.py`, lines 295-310):
```python
# Set rate function in transition properties
transition.properties['rate_function'] = rate_function

# Mark document as dirty (manager has mark_dirty directly)
canvas_manager.mark_dirty()

# Refresh canvas
drawing_area.queue_draw()
```

**BRENDA Flow** (BEFORE fix):
```python
# Set rate function in transition properties
transition.properties['rate_function'] = rate_function

# Reset simulation state
self._reset_simulation_after_parameter_changes()

# Refresh canvas
self.model_canvas.queue_draw()

# ❌ MISSING: canvas_manager.mark_dirty()
```

### Why `mark_dirty()` is Critical

The `mark_dirty()` method:
1. **Marks the model as modified** - Signals that the document has unsaved changes
2. **Triggers property persistence** - Ensures properties are saved to the model
3. **Updates UI state** - Properties dialog reads from saved/persisted state
4. **Enables proper save** - Without it, changes may not be written to disk

Without `mark_dirty()`, the properties were stored in memory but not persisted to the model's saved state, causing the properties dialog to show old/cached values.

## Solution Implemented

Added `mark_dirty()` calls in **brenda_category.py** at two locations:

### Location 1: Single Apply (lines ~1663-1673)
```python
# Finish enrichment session
self.brenda_controller.finish_enrichment()

# Mark model as dirty (modified) so changes are saved
if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'mark_dirty'):
    self.model_canvas_manager.mark_dirty()
    self.logger.info(f"[SINGLE_APPLY] ✓ Marked model as dirty")

# CRITICAL: Reset simulation state after applying parameters
self._reset_simulation_after_parameter_changes()
```

### Location 2: Batch Apply (lines ~1391-1401)
```python
# Finish enrichment session
self.brenda_controller.finish_enrichment()

# Mark model as dirty (modified) so changes are saved
if applied_count > 0:
    if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'mark_dirty'):
        self.model_canvas_manager.mark_dirty()
        self.logger.info(f"[BATCH_APPLY] ✓ Marked model as dirty")

# CRITICAL: Reset simulation state after applying parameters
if applied_count > 0:
    self._reset_simulation_after_parameter_changes()
```

## Flow Comparison Summary

### Heuristic Parameters (WORKING)
1. Get transition from `canvas_manager.transitions`
2. Set `transition.properties['rate_function']`
3. **Call `canvas_manager.mark_dirty()`** ← KEY STEP
4. Call `drawing_area.queue_draw()`
5. Properties dialog shows new rate function ✓

### KEGG Import (WORKING)
- Similar pattern to heuristic flow
- Uses `mark_dirty()` to persist changes

### BRENDA Parameters (NOW FIXED)
1. Get transition from `canvas_manager.transitions`
2. Set `transition.properties['rate_function']`
3. Call `finish_enrichment()`
4. **Call `canvas_manager.mark_dirty()`** ← ADDED
5. Call `_reset_simulation_after_parameter_changes()`
6. Call `queue_draw()`
7. Properties dialog now shows new rate function ✓

## Testing Validation

To verify the fix works:

1. **Apply BRENDA parameters** to a transition
2. **Check verification logs**: Should show "✓ VERIFIED: rate_function correctly stored"
3. **Check mark_dirty log**: Should show "✓ Marked model as dirty"
4. **Open properties dialog**: Should now display the new rate function
5. **Save model**: Changes should be persisted to disk

## Technical Context

### Architecture Components
- **model_canvas_manager**: Contains live transition objects, has `mark_dirty()` method
- **model_canvas**: Canvas loader for drawing operations
- **transition.properties**: Dictionary storing rate functions and metadata
- **Properties Dialog**: Reads from persisted model state (requires `mark_dirty()`)

### Persistence Flow
```
1. Set property in memory:
   transition.properties['rate_function'] = "michaelis_menten(...)"

2. Mark model as dirty:
   canvas_manager.mark_dirty()
   ↓
   Triggers persistence to model state

3. Properties dialog:
   Reads from persisted model state
   ↓
   Shows updated rate function ✓
```

## Related Files Modified

1. **brenda_category.py**:
   - Added `mark_dirty()` call after single apply (line ~1668)
   - Added `mark_dirty()` call after batch apply (line ~1396)
   - Both locations: after `finish_enrichment()`, before `_reset_simulation_after_parameter_changes()`

## Session Context

This fix is part of a comprehensive BRENDA integration improvement session:

✅ **Previous Fixes**:
1. TransID column display (context.get('transition_id'))
2. Single apply method (correct signature + dict format)
3. Named parameters standardization (6 files, 13 locations)
4. "Apply twice" bug (re-fetch fresh transition)
5. T27 not found error (model_canvas_manager + string ID comparison)
6. canvas_loader AttributeError (added model_canvas_loader parameter)

✅ **Current Fix**:
7. Properties dialog not showing applied rate function (added `mark_dirty()`)

## Key Takeaway

**When modifying model properties programmatically, always call `mark_dirty()` to persist changes!**

This ensures:
- Properties are saved to model state
- Properties dialog displays current values
- Changes are preserved when saving the model
- UI state remains consistent with model state

## Pattern for Future Reference

When applying parameters programmatically:
```python
# 1. Get fresh transition from canvas_manager
transition = canvas_manager.transitions[...]

# 2. Set properties
transition.properties['rate_function'] = rate_function

# 3. Mark model as dirty (CRITICAL!)
canvas_manager.mark_dirty()

# 4. Reset simulation state
self._reset_simulation_after_parameter_changes()

# 5. Refresh canvas
drawing_area.queue_draw()
```

This pattern is now consistent across heuristic, KEGG, and BRENDA flows.
