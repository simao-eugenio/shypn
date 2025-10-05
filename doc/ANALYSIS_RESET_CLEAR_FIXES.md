# Analysis Panel Reset and Clear Fixes

**Date**: October 5, 2025  
**Purpose**: Ensure plots blank correctly when simulation resets or Clear button is clicked

---

## Issues Fixed

### Issue 1: Simulation Reset Doesn't Blank Plots ❌
**Problem**: When user clicks "Reset" button in simulation palette:
- Simulation time resets to 0
- Places restore initial marking
- **But**: Analysis plots still show old data from previous simulation run
- Data collector keeps old data (never cleared)

### Issue 2: Clear Button Doesn't Blank Canvas Immediately ❌
**Problem**: When user clicks "Clear" button in analysis panel:
- Selected objects list clears
- **But**: Canvas still shows old plot until next update cycle
- Looks unresponsive to user

---

## Solutions Implemented

### Fix 1: Clear Data Collector on Simulation Reset ✅

**File**: `src/shypn/engine/simulation/controller.py`

**Change**: Added data collector clear in `reset()` method

```python
def reset(self):
    """Reset the simulation to initial marking."""
    # ... stop simulation if running ...
    
    # Reset time
    self.time = 0.0
    
    # NEW: Clear data collector if attached
    if self.data_collector is not None:
        self.data_collector.clear()
        print("[SimulationController] Data collector cleared on reset")
    
    # Clear transition states
    self.transition_states.clear()
    
    # ... rest of reset logic ...
```

**Effect**:
- All place token history cleared
- All transition firing events cleared
- Next simulation starts with fresh data
- Plots show only new simulation data

### Fix 2: Immediate Canvas Blank on Clear Button ✅

**File**: `src/shypn/analyses/plot_panel.py`

**Change**: Modified `_on_clear_clicked()` to immediately blank canvas

```python
def _on_clear_clicked(self, button):
    """Handle clear button click - clear selection and blank canvas."""
    self.selected_objects.clear()
    self.last_data_length.clear()  # Reset data length tracking
    
    # NEW: Immediately blank the canvas - don't wait for periodic update
    self._show_empty_state()
    
    # NEW: Also update the objects list UI
    self._update_objects_list()
    
    print(f"[{self.__class__.__name__}] Cleared all selections and blanked canvas")
```

**Before**:
- Set `needs_update = True`
- Wait for next periodic update (up to 100ms delay)
- User sees old plot briefly

**After**:
- Immediately call `_show_empty_state()` 
- Canvas blanks instantly
- Shows "No objects selected" message
- Responsive UX

### Fix 3: Enhanced Reset Handler ✅

**File**: `src/shypn/helpers/model_canvas_loader.py`

**Change**: Modified `_on_simulation_reset()` to reset tracking state

```python
def _on_simulation_reset(self, palette):
    """Handle simulation reset - blank analysis plots and prepare for new data."""
    print("[ModelCanvasLoader] Simulation reset - blanking analysis panels")
    
    if self.right_panel_loader:
        if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
            panel = self.right_panel_loader.place_panel
            
            # NEW: Reset data length tracking
            panel.last_data_length.clear()
            
            # If objects are selected, mark for update
            if panel.selected_objects:
                panel.needs_update = True
            else:
                # Show empty state if nothing selected
                panel._show_empty_state()
        
        # Same for transition panel...
```

**Effect**:
- Clears `last_data_length` tracking dictionary
- Prevents false "no data change" detection after reset
- Ensures plots update properly with new simulation data

---

## Flow Diagrams

### Reset Flow (After Fix)

```
User clicks "Reset" button
    ↓
SimulateToolsPaletteLoader._on_reset_clicked()
    ↓
SimulationController.reset()
    ├─> time = 0.0
    ├─> data_collector.clear() ← NEW!
    ├─> transition_states.clear()
    └─> places restore initial marking
    ↓
emit('reset-executed')
    ↓
ModelCanvasLoader._on_simulation_reset()
    ├─> place_panel.last_data_length.clear() ← NEW!
    ├─> transition_panel.last_data_length.clear() ← NEW!
    └─> panels.needs_update = True
    ↓
Next periodic update (100ms)
    ↓
Panels check data → No data (cleared!)
    ↓
Show empty plots or initial state (t=0 with 0 data points)
```

### Clear Button Flow (After Fix)

```
User clicks "Clear" button in analysis panel
    ↓
AnalysisPlotPanel._on_clear_clicked()
    ├─> selected_objects.clear()
    ├─> last_data_length.clear()
    ├─> _show_empty_state() ← NEW! Immediate blank
    └─> _update_objects_list() ← NEW! Update UI list
    ↓
Canvas blanked IMMEDIATELY (no delay)
    ↓
Shows: "No objects selected
         Add objects to analyze"
```

---

## Testing Scenarios

### Test 1: Reset During Simulation ✅

**Steps**:
1. Start simulation with places/transitions in analysis panels
2. Let simulation run for 10 seconds (plots show data)
3. Click "Reset" button
4. **Expected**: Plots immediately blank/reset, ready for new simulation

**Before Fix**: Old data still visible ❌  
**After Fix**: Plots blank cleanly ✅

### Test 2: Reset After Simulation Complete ✅

**Steps**:
1. Run simulation to completion (deadlock or max time)
2. Plots show full history
3. Click "Reset" button
4. Click "Run" to start new simulation
5. **Expected**: New plot starts from scratch, no old data

**Before Fix**: Old data mixed with new ❌  
**After Fix**: Clean new plot ✅

### Test 3: Clear Button Responsiveness ✅

**Steps**:
1. Add 5 places to analysis panel
2. Run simulation (plots show data)
3. Click "Clear" button
4. **Expected**: Canvas blanks immediately, list clears

**Before Fix**: Up to 100ms delay, old plot visible ❌  
**After Fix**: Instant blank, responsive ✅

### Test 4: Clear Then Add Same Objects ✅

**Steps**:
1. Add place P1 to analysis
2. Run simulation (plot shows P1 data)
3. Click "Clear"
4. Add P1 again
5. Run simulation again
6. **Expected**: Only new simulation data plotted

**Before Fix**: Might show stale data ❌  
**After Fix**: Clean new plot ✅

### Test 5: Reset With No Objects Selected ✅

**Steps**:
1. Run simulation (no objects in analysis panels)
2. Click "Reset"
3. **Expected**: No errors, panels show empty state

**Before Fix**: Works but tracking state not cleared ⚠️  
**After Fix**: Fully cleaned up ✅

---

## Technical Details

### Data Structures Cleared

**SimulationDataCollector.clear()**:
```python
def clear(self):
    """Clear all collected data."""
    self.place_data.clear()        # Dict[place_id, List[(time, tokens)]]
    self.transition_data.clear()   # Dict[trans_id, List[(time, event, details)]]
    self.step_count = 0
    self.total_firings = 0
```

**AnalysisPlotPanel tracking reset**:
```python
self.last_data_length.clear()  # Dict[obj_id, int] - tracks data length per object
```

### Why `last_data_length` Matters

The hang fix introduced data change detection:
```python
# Periodic update only redraws if data changed
for obj in selected_objects:
    current_length = len(data_collector.get_data(obj.id))
    if current_length != self.last_data_length.get(obj.id, 0):
        data_changed = True  # Trigger redraw
```

**Problem**: After reset, data collector is cleared but `last_data_length` still has old values
- Old: `last_data_length[P1] = 252`
- After reset: `len(data_collector.get_place_data(P1)) = 0`
- Comparison: `0 != 252` → data_changed = True → Plot updates ✅

**But then**:
- `last_data_length[P1]` updated to `0`
- Next check: `0 == 0` → No change detected
- Even though new simulation is generating data!

**Solution**: Clear `last_data_length` on reset so it starts fresh

---

## Benefits

### ✅ Clean UX
- No confusion about whether reset worked
- Plots visually confirm data cleared
- Immediate feedback on Clear button

### ✅ Correct Data Separation
- Each simulation run isolated
- No data pollution between runs
- Reproducible results

### ✅ Performance
- Old data released from memory
- Doesn't accumulate across resets
- Prevents memory leak on repeated resets

### ✅ Consistency
- Reset behavior matches user expectation
- Clear button behaves like clear should
- No surprising state retention

---

## Related Files Modified

1. **`src/shypn/engine/simulation/controller.py`**
   - Added `data_collector.clear()` in `reset()` method

2. **`src/shypn/analyses/plot_panel.py`**
   - Modified `_on_clear_clicked()` to immediately blank canvas
   - Added `_update_objects_list()` call for instant UI update

3. **`src/shypn/helpers/model_canvas_loader.py`**
   - Enhanced `_on_simulation_reset()` to clear tracking state
   - Added blank empty state when no objects selected

---

## Backward Compatibility

### No Breaking Changes ✅
- All changes are internal improvements
- No API changes
- No UI changes (only behavior fixes)
- Existing code continues to work

### Signal Flow Unchanged
- `'reset-executed'` signal still emitted
- Listeners still notified
- Just added clearing logic

---

## Future Enhancements

### Visual Reset Confirmation
Could add brief visual feedback:
```python
# Flash canvas or show "Data Cleared" message
self._show_reset_confirmation()
GLib.timeout_add(1000, self._hide_reset_confirmation)
```

### Partial Clear
Could add button to clear individual objects:
```python
# Context menu on legend: "Remove from plot"
# Or X button next to each object in list (already have this!)
```

### Save Plot Before Clear
Could prompt user:
```python
"Clear plot data? This will discard current analysis."
[ Save Plot ] [ Clear Anyway ] [ Cancel ]
```

---

## Summary

**Problem**: Plots retained stale data after reset and Clear button had delayed response

**Solution**: 
1. Clear data collector on simulation reset
2. Immediately blank canvas on Clear button
3. Reset data change tracking state

**Result**: Clean, responsive UX with proper data isolation ✅

---

## Quick Test

```bash
# 1. Start app
./shypn.sh

# 2. Create simple net
P1[10] → T1 → P2[0]

# 3. Add both places to analysis panel

# 4. Run simulation for a few seconds
Click "Run" → Wait → Click "Stop"

# 5. Test Reset
Click "Reset" → Plots should blank immediately ✅

# 6. Test Clear
Click "Clear" in analysis panel → Canvas blanks instantly ✅

# 7. Run again
Click "Run" → New clean plot appears ✅
```

Perfect behavior! 🎉
