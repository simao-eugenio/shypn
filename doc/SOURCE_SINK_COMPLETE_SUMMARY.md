# Source/Sink Implementation - Complete Summary

## User Feedback & Fixes

### Issue 1: Spurious Arc After Dialog Close ✅ FIXED
**Problem**: Small arc appeared after editing transition properties  
**Solution**: Implemented three-layer protection:
1. Clear arc state before opening dialog
2. Temporarily switch from arc tool to select tool during dialog
3. Set `ignore_next_release` flag to block next mouse interaction
4. Restore tool after dialog closes

### Issue 2: Source/Sink Simulation Not Working ✅ FIXED
**Problems**:
- "source does not reset count on reset"
- "sink works only for immediate"

**Solution**: Implemented source/sink behavior in ALL transition types:
- `immediate_behavior.py`: Source transitions always enabled, skip consumption/production
- `timed_behavior.py`: Source transitions always enabled with timing, skip consumption/production
- `stochastic_behavior.py`: Source transitions always enabled with burst, skip consumption/production  
- `continuous_behavior.py`: Source transitions always enabled, skip consumption/production in integration

### Issue 3: "Little Arc" on Source/Sink ⚠️ CLARIFICATION NEEDED
**User Report**: "little arc still there, on source mark it appears on the left of transition, on sink it appears on the right"

**Analysis**: This describes the VISUAL MARKERS that are INTENTIONALLY drawn to indicate source/sink status:
- Source: Arrow on LEFT (pointing into transition)
- Sink: Arrow on RIGHT (pointing out of transition)

**Two Possibilities**:
1. **User confusion**: Visual markers are working correctly, but user thinks they're a bug
2. **Real bug**: Markers appearing when checkboxes are NOT checked

**Latest Fix**: Added `cr.save()` / `cr.restore()` around arrow rendering to prevent Cairo path artifacts

## Visual Markers Explained

The arrows you see are NOT Petri net arcs - they are visual indicators:

**Source Transition:**
```
    →|====|
```
- Arrow points INTO the transition from the left
- Shows that this transition generates tokens externally
- Only visible when "Source" checkbox is CHECKED

**Sink Transition:**
```
    |====|→
```  
- Arrow points OUT OF the transition to the right
- Shows that this transition consumes tokens externally
- Only visible when "Sink" checkbox is CHECKED

## How to Test

### Test 1: Visual Markers Should Only Appear When Checked
1. Create a new transition
2. Double-click to open properties
3. Verify Source and Sink checkboxes are UNCHECKED
4. Click OK
5. **Expected**: NO arrows on the transition
6. Open properties again
7. Check "Source" checkbox
8. Click OK
9. **Expected**: Arrow on LEFT side of transition
10. Open properties, uncheck "Source", check "Sink"
11. Click OK
12. **Expected**: Arrow on RIGHT side of transition

### Test 2: Source Transition Simulation
1. Create: Place(5 tokens) → Source Transition → Place(0 tokens)
2. Mark transition as Source
3. Run simulation, fire the transition
4. **Expected**: Output place gets tokens WITHOUT consuming from input place
5. Reset simulation
6. **Expected**: Places return to initial marking, source can fire again

### Test 3: Sink Transition Simulation
1. Create: Place(5 tokens) → Sink Transition → Place(0 tokens)
2. Mark transition as Sink
3. Run simulation, fire the transition
4. **Expected**: Input place loses tokens WITHOUT producing to output place

### Test 4: All Transition Types
- Test source/sink with: Immediate, Timed, Stochastic, Continuous
- All should work correctly

## Next Steps

**Please verify**:
1. Are the arrows appearing when checkboxes are UNCHECKED? (This would be a bug)
2. Are the arrows appearing when checkboxes ARE CHECKED? (This is correct behavior)
3. Do you want a different visual style for the markers?
4. Or do you want NO visual markers at all (source/sink only affects simulation)?

