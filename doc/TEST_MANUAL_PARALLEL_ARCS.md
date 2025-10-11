# Manual Parallel Arc Test

**Date**: 2025-10-10  
**Purpose**: Test manual control of parallel arcs without automatic conversion  
**Change**: Disabled `_auto_convert_parallel_arcs_to_curved()` in `model_canvas_manager.py`

## Test Workflow

### Setup
1. Create two nodes:
   - Place (circle) at position A
   - Transition (rectangle) at position B

### Test Case 1: Manual Curve in One Direction

**Step 1**: Draw straight arc A → B
- **Action**: Click Place, drag to Transition
- **Expected**: Straight arc appears from A to B
- **Verify**: ✓ Arc touches boundaries (radius + border_width/2)

**Step 2**: Transform arc to curved
- **Action**: Double-click arc to enter edit mode
- **Expected**: Blue handle appears at arc midpoint
- **Action**: Drag handle perpendicular to arc
- **Expected**: Arc becomes curved, follows mouse
- **Verify**: 
  - ✓ Arc remains anchored at boundaries
  - ✓ Blue preview matches real arc
  - ✓ Curve is smooth (quadratic Bezier)

**Step 3**: Click away to exit edit mode
- **Expected**: Curved arc remains, handle disappears
- **Verify**: ✓ Arc shape preserved

### Test Case 2: Manual Curve in Opposite Direction

**Step 4**: Draw straight arc B → A (opposite direction)
- **Action**: Click Transition, drag to Place
- **Expected**: Straight arc appears from B to A
- **Verify**: 
  - ✓ Arc touches boundaries
  - ✓ Arc is straight (NOT automatically curved)
  - ✓ Two arcs may overlap visually (both straight)

**Step 5**: Transform second arc to curved
- **Action**: Double-click second arc to enter edit mode
- **Expected**: Blue handle appears
- **Action**: Drag handle perpendicular (opposite side from first arc)
- **Expected**: Second arc becomes curved in opposite direction
- **Verify**:
  - ✓ Both arcs anchor at boundaries
  - ✓ Arcs curve in opposite directions (visual separation)
  - ✓ Parallel arc offset applied to control point only

**Step 6**: Click away to exit edit mode
- **Expected**: Both curved arcs remain
- **Verify**: 
  - ✓ Arc A→B curves one way
  - ✓ Arc B→A curves opposite way
  - ✓ Both properly anchored at boundaries

### Test Case 3: Context Menu on Both Arcs

**Step 7**: Right-click first arc (A→B)
- **Expected**: Context menu appears
- **Verify**:
  - ✓ Menu shows arc properties
  - ✓ Options: Properties, Transform to Straight, Delete

**Step 8**: Right-click second arc (B→A)
- **Expected**: Context menu appears
- **Verify**: ✓ Can select either arc independently

### Test Case 4: Hit Detection on Curved Parallel Arcs

**Step 9**: Click along middle of first arc
- **Expected**: First arc is selected (blue highlight)
- **Verify**: ✓ Hit detection works on full curve path

**Step 10**: Click along middle of second arc
- **Expected**: Second arc is selected
- **Verify**: ✓ Hit detection distinguishes between parallel arcs

### Test Case 5: Same-Direction Parallel Arcs

**Step 11**: Draw third arc A → B (same direction as first)
- **Action**: Click Place, drag to Transition again
- **Expected**: Straight arc appears (overlapping first arc)
- **Verify**: ✓ No automatic conversion to curved

**Step 12**: Transform third arc to curved (different side)
- **Action**: Double-click third arc, drag handle to opposite side
- **Expected**: Three arcs now visible:
  - Arc 1 (A→B): Curved one way
  - Arc 2 (B→A): Curved opposite way
  - Arc 3 (A→B): Curved different from Arc 1
- **Verify**: ✓ All three anchor at boundaries with different curves

## Expected Behavior Summary

### ✅ Automatic Conversion Disabled
- Creating parallel arcs does NOT automatically convert them to curved
- User must manually double-click and drag to curve arcs
- Gives full control over which arcs are curved

### ✅ Parallel Arc Offset Still Works
- Even though arcs start straight, parallel offset is applied when curved
- Offset affects **control point** position, not anchor points
- Arcs remain anchored at actual object boundaries

### ✅ Manual Control Benefits
1. **User decides**: Which arcs should be curved
2. **User decides**: Which direction to curve (positive or negative offset)
3. **Cleaner start**: New arcs don't automatically change shape
4. **Predictable**: No automatic transformations happening behind the scenes

## Visual Comparison

### Before (Automatic):
```
1. Draw A→B: [Straight arc]
2. Draw B→A: [BOTH automatically become curved]
   - User didn't ask for curved
   - Unexpected transformation
```

### After (Manual):
```
1. Draw A→B: [Straight arc]
2. Draw B→A: [Straight arc, may overlap]
3. User transforms A→B: [Curved one way]
4. User transforms B→A: [Curved opposite way]
   - User has full control
   - Explicit transformations only
```

## Implementation Details

### Change Made
**File**: `src/shypn/data/model_canvas_manager.py`  
**Line**: 280  
**Action**: Commented out auto-conversion call

```python
# DISABLED: Auto-conversion to curved arcs for parallels
# Users now manually control curve conversion via transformation handles
# self._auto_convert_parallel_arcs_to_curved(arc)
```

### Parallel Arc Offset Behavior
- **Detection**: `detect_parallel_arcs()` still works (finds parallel arcs)
- **Offset Calculation**: `calculate_arc_offset()` still works (returns offset value)
- **Application**: Offset applied ONLY to control point (not endpoints)
- **Timing**: Offset takes effect when arc is curved (manual or from file)

### Backward Compatibility
✅ Loading old files with curved parallel arcs: **Works correctly**  
✅ Existing curved arcs: **No change**  
✅ New straight arcs: **Remain straight until manually curved**  
✅ Parallel arc rendering: **Correct boundary anchoring**  

## Success Criteria

- [ ] Draw two opposite arcs, both stay straight initially
- [ ] Manually transform first arc to curved
- [ ] Manually transform second arc to curved (opposite direction)
- [ ] Both arcs anchor at boundaries (not floating)
- [ ] Context menu works on both arcs
- [ ] Hit detection distinguishes between parallel arcs
- [ ] Can add third parallel arc and curve it independently
- [ ] Undo/redo works for arc creation and transformation

## Notes

- This change improves user experience by removing "magic" automatic transformations
- Users now have explicit control over arc shapes
- Parallel arc offset still provides visual separation when arcs ARE curved
- Straight parallel arcs will overlap (expected behavior - user should curve them)

## Related Files

- `src/shypn/data/model_canvas_manager.py` - Disabled auto-conversion
- `src/shypn/netobjs/arc.py` - Parallel offset applied to control point
- `src/shypn/edit/transformation/arc_transform_handler.py` - Manual curve transformation
- `PARALLEL_ARC_FIX.md` - Parallel arc boundary anchoring fix

