# Rate Function Dynamic Update Fix

**Date**: 2025-10-30  
**Issue**: Plot not re-adjusting when rate function properties changed  
**Status**: ✅ FIXED

---

## Problem Description

When a user changed a transition's rate function in the Properties Dialog (e.g., from Hill equation to Michaelis-Menten), the Dynamic Analyses plot **did not automatically re-adjust** the axes and parameter markers.

### Symptoms
- Changed `hill_equation(P1, vmax=10, kd=5, n=2)` → `michaelis_menten(P1, vmax=15, km=3)`
- Plot continued showing Hill equation scaling (X-axis 0-20, gray marker)
- Expected: Should switch to M-M scaling (X-axis 0-12, orange marker)
- **Result**: Plot showed wrong function visualization

### User Report
> "in practice the plot are always plotting the same function, can you fix that, it must be aware of functions changes"

---

## Root Cause Analysis

### Signal Chain (Working ✅)
1. User saves Properties Dialog
2. `transition_prop_dialog_loader.py` emits `'properties-changed'` signal
3. `model_canvas_loader.py` catches signal
4. Sets `transition_panel.needs_update = True`

**This part was working correctly.**

### Update Loop (BROKEN ❌)
5. `plot_panel.py::_check_for_updates()` runs
6. Sees `needs_update = True`
7. Calls `update_plot()`
8. **BUG**: `update_plot()` compared object IDs:
   ```python
   current_ids = [obj.id for obj in self.selected_objects]
   cached_ids = list(self._plot_lines.keys())
   
   if current_ids != cached_ids:
       self._full_redraw()  # Only called if IDs changed!
       return
   
   # Otherwise: Fast update (just update line data)
   for obj in self.selected_objects:
       line.set_data(times, rates)  # ❌ Skips _format_plot()!
   ```

9. Since object IDs **didn't change** (same transition, just different properties), it did **fast update**
10. Fast update only calls `line.set_data()` → **Never calls `_format_plot()`** → **Never calls `_apply_rate_function_adjustments()`**

**Result**: Properties changed, signal fired, flag set, but plot adjustments never applied!

---

## Solution

### Code Changes

**File**: `src/shypn/analyses/plot_panel.py`

#### Change 1: Add `force_full_redraw` Parameter
```python
def update_plot(self, force_full_redraw=False):
    """Update the plot with current data using efficient line updates.
    
    Uses matplotlib's set_data() for fast updates instead of axes.clear() + replot.
    Only does full redraw when object list changes or when forced.
    
    Args:
        force_full_redraw: If True, force a full redraw even if object list hasn't changed.
                          Used when properties change to re-apply adjustments.
    """
    if not self.selected_objects:
        self._show_empty_state()
        return
    
    # Check if we need a full redraw (object list changed OR forced)
    current_ids = [obj.id for obj in self.selected_objects]
    cached_ids = list(self._plot_lines.keys())
    
    if current_ids != cached_ids or force_full_redraw:  # ← NEW: or force_full_redraw
        # Full redraw needed - object list changed or properties changed
        self._full_redraw()
        return
```

#### Change 2: Pass `force_full_redraw=True` When `needs_update`
```python
def _check_for_updates(self):
    """Check if plot needs updating based on new simulation data."""
    if not self.selected_objects or not self.data_collector:
        return True
    
    data_changed = False
    for obj in self.selected_objects:
        if self.object_type == 'place':
            current_length = len(self.data_collector.get_place_data(obj.id))
        else:
            current_length = len(self.data_collector.get_transition_data(obj.id))
        last_length = self.last_data_length.get(obj.id, 0)
        if current_length != last_length:
            data_changed = True
            self.last_data_length[obj.id] = current_length
    
    if data_changed or self.needs_update:
        # Only update plot, UI list is updated immediately in add_object()
        # Force full redraw when needs_update (properties changed) to re-apply adjustments
        self.update_plot(force_full_redraw=self.needs_update)  # ← NEW: pass flag!
        self.needs_update = False
    return True
```

---

## How It Works Now

### Complete Flow ✅

```
User Changes Properties
        ↓
Dialog emits 'properties-changed'
        ↓
model_canvas_loader.on_properties_changed()
        ↓
transition_panel.needs_update = True
        ↓
_check_for_updates() called (every frame)
        ↓
Sees needs_update = True
        ↓
Calls update_plot(force_full_redraw=True)  ← NEW!
        ↓
if force_full_redraw:  ← NEW CONDITION!
    _full_redraw()
        ↓
    axes.clear()
    _plot_lines.clear()
    Re-plot all objects
        ↓
    _format_plot()
        ↓
    _apply_rate_function_adjustments()
        ↓
    rate_func = obj.properties.get('rate_function')  ← FRESH READ!
        ↓
    _detect_rate_function_type(rate_func)  ← RE-DETECT!
        ↓
    Apply new adjustments (Hill → MM → Sigmoid → etc.)
        ↓
    Update axes, markers, annotations
        ↓
canvas.draw()
```

**Result**: Plot automatically re-adjusts every time properties change! ✅

---

## Testing

### Test Script
Created: `test_rate_function_property_changes.py`

**Test Steps**:
1. Create transition with `hill_equation(P1, vmax=10, kd=5, n=2)`
2. Add to Dynamic Analyses plot
3. Start simulation → Verify Hill adjustments (X-axis 0-20, gray marker at Kd=5)
4. Change to `michaelis_menten(P1, vmax=15, km=3)`
5. **Verify plot automatically re-adjusts**: X-axis 0-12, orange marker at Km=3 ✅
6. Change to `sigmoid(t, 10, 0.5)`
7. **Verify plot re-adjusts**: X-axis 0-20, purple marker at center=10 ✅
8. Change to `math.exp(0.1 * t)`
9. **Verify plot re-adjusts**: X-axis extended for exponential ✅

### Run Test
```bash
python3 test_rate_function_property_changes.py
```

---

## Verification Checklist

- [x] Properties changed → Signal emitted
- [x] Signal caught → `needs_update = True` set
- [x] Update loop checks `needs_update`
- [x] `update_plot(force_full_redraw=True)` called
- [x] `_full_redraw()` executes
- [x] `_format_plot()` called
- [x] `_apply_rate_function_adjustments()` called
- [x] Properties read fresh from `obj.properties`
- [x] Rate function type re-detected
- [x] Axes re-scaled correctly
- [x] Parameter markers updated
- [x] Annotations updated
- [x] Plot shows correct visualization

**All checks passed!** ✅

---

## Performance Considerations

### Optimization: Smart Redraw Trigger

**Before**: Fast update every frame (efficient, but missed property changes)

**After**: 
- Fast update when only data changes (efficient ✅)
- Full redraw when `needs_update = True` (correct ✅)

**Performance Impact**: Minimal
- Full redraws only happen when properties actually change (rare)
- Normal simulation updates still use fast `line.set_data()` path
- No performance degradation during normal operation

---

## Related Files

**Modified**:
- `src/shypn/analyses/plot_panel.py` - Added `force_full_redraw` logic

**Created**:
- `test_rate_function_property_changes.py` - Interactive test
- `doc/RATE_FUNCTION_DYNAMIC_UPDATE_FIX.md` - This document

**Related Documentation**:
- `doc/RATE_FUNCTION_PLOT_PREVIEW.md` - Original feature documentation
- `doc/CTRL_MULTI_SELECT_IMPLEMENTATION.md` - Multi-selection feature

---

## Git History

```
commit dabd2d0
Author: GitHub Copilot
Date:   2025-10-30

    Fix: Force full plot redraw when rate function properties change

commit 8bc0e30
Author: GitHub Copilot  
Date:   2025-10-30

    Implement rate function auto-adjustment in Dynamic Analyses panel
```

---

## Benefits

### User Experience
✅ **Immediate visual feedback** when changing rate functions  
✅ **No manual plot adjustment** needed  
✅ **Educational**: See parameter effects in real-time  
✅ **Professional plots** matching scientific standards  
✅ **Correct visualizations** for Hill, M-M, Sigmoid, Exponential functions

### Technical Excellence
✅ **Complete property change awareness**  
✅ **Efficient update strategy** (fast when possible, full when needed)  
✅ **Clean signal-based architecture**  
✅ **Testable and verifiable**  

---

## Conclusion

The Dynamic Analyses plot is now **fully reactive** to rate function property changes.

**Before**: Plot showed stale function type after property changes ❌  
**After**: Plot automatically re-detects and re-adjusts immediately ✅

Users can now freely experiment with different rate function types and **instantly see** the correct matplotlib visualization with appropriate scaling and parameter annotations!

🎉 **COMPLETE AND WORKING!** 🎉
