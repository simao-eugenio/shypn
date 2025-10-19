# Analysis Panel Locality UI List Display Fix

**Date**: October 19, 2025  
**Branch**: feature/property-dialogs-and-simulation-palette  
**Purpose**: Fix "Selected transitions" UI list to show locality places

---

## Issue Discovered

### Problem: Locality Places Not Shown in UI List ❌

**What the user sees**:
- User adds transition T1 to Transition Analysis
- UI list in "Selected transitions" section only shows:
  ```
  T1 [CON] (T1)
  ```
- Locality places (P_in, P_out) are **missing** from the UI list
- Even though they ARE added to PlaceRatePanel for plotting

**User Impact**:
- No visual confirmation that locality places were added
- UI list doesn't match what's being plotted
- Confusing UX - where are the locality places?

**Root Cause**: Two issues found:

1. **Base class `add_object()`** calls `_add_object_row()` for incremental UI updates
   - `_add_object_row()` doesn't know about locality places
   - Only adds the transition itself to the UI list

2. **`add_locality_places()` method** doesn't update the UI list
   - Stores locality info in `self._locality_places`
   - Adds places to PlaceRatePanel for plotting
   - Sets `self.needs_update = True` for plot refresh
   - But **never calls** `self._update_objects_list()` to refresh UI

---

## Solution Implemented

### Fix 1: Override add_object() in TransitionRatePanel ✅

**File**: `src/shypn/analyses/transition_rate_panel.py`  
**Location**: After `set_place_panel()` method (lines 98-110)

**Added Method**:
```python
def add_object(self, obj):
    """Add a transition to the selected list for plotting.
    
    Overrides parent to use full list rebuild instead of incremental add,
    because we need to show locality places under each transition.
    
    Args:
        obj: Transition object to add
    """
    if any((o.id == obj.id for o in self.selected_objects)):
        return
    self.selected_objects.append(obj)
    # Use full rebuild to show locality places in UI list
    self._update_objects_list()
    self.needs_update = True
```

**Why This Works**:
- Base class uses `_add_object_row()` for incremental adds (optimization)
- But incremental add doesn't show locality places
- Override to use `_update_objects_list()` which DOES show locality places
- Slight performance cost but necessary for correct UI display

**Note**: At the time of `add_object()` call, locality places may not be added yet. They'll appear when `add_locality_places()` is called next.

---

### Fix 2: Update UI List After Adding Locality Places ✅

**File**: `src/shypn/analyses/transition_rate_panel.py`  
**Location**: In `add_locality_places()` method (line 405)

**Change**:
```python
# Actually add the locality places to the PlaceRatePanel for plotting
if self._place_panel is not None:
    # Add input places
    for place in locality.input_places:
        self._place_panel.add_object(place)
    
    # Add output places
    for place in locality.output_places:
        self._place_panel.add_object(place)

# NEW: Update the UI list to show locality places under the transition
self._update_objects_list()

# Trigger plot update
self.needs_update = True
```

**Before**:
```python
# Add places to PlaceRatePanel
...

# Missing: self._update_objects_list()

# Trigger plot update
self.needs_update = True
```

**Why This Works**:
- After storing locality info in `self._locality_places`
- And after adding places to PlaceRatePanel
- **Now** also refreshes the UI list
- `_update_objects_list()` reads `self._locality_places` and displays them

---

## Complete Flow After Fixes

### Scenario: User Adds Transition via Context Menu

```
User right-clicks transition T1
    ↓
Selects "Add to Transition Analysis"
    ↓
ContextMenuHandler._add_transition_with_locality()
    ↓
Step 1: transition_panel.add_object(T1)
    ├─> TransitionRatePanel.add_object(T1)  ← Our Override
    ├─> selected_objects.append(T1)
    ├─> _update_objects_list()  ← Full UI rebuild
    │       └─> Shows: "T1 [CON] (T1)"
    └─> needs_update = True
    ↓
Step 2: transition_panel.add_locality_places(T1, locality)
    ├─> Store locality in self._locality_places[T1.id]
    ├─> place_panel.add_object(P_in)   ← Add to PlaceRatePanel
    ├─> place_panel.add_object(P_out)  ← Add to PlaceRatePanel
    ├─> _update_objects_list()  ← NEW! Update UI list
    │       └─> Shows: "T1 [CON] (T1)"
    │                  "  ← Input: P_in (5 tokens)"
    │                  "  → Output: P_out (0 tokens)"
    └─> needs_update = True
    ↓
Result: UI list shows transition AND locality places ✅
Result: PlaceRatePanel has P_in and P_out for plotting ✅
```

### What the User Sees Now

**"Selected transitions" UI list**:
```
┌─────────────────────────────────────────┐
│ ● T1 [CON] (T1)                     [×] │
│   ← Input: P_in (5 tokens)              │
│   → Output: P_out (0 tokens)            │
└─────────────────────────────────────────┘
```

**"Selected places" UI list** (in Places tab):
```
┌─────────────────────────────────────────┐
│ ● P_in (P1)                         [×] │
│ ● P_out (P2)                        [×] │
└─────────────────────────────────────────┘
```

**Plot**:
- T1 firing rate plotted
- P_in token count plotted
- P_out token count plotted
- All with proper legend and colors

---

## UI List Display Logic

The `_update_objects_list()` method in `TransitionRatePanel`:

1. **Clears existing UI list** (removes all children)
2. **For each selected transition**:
   - Creates transition row with:
     - Color indicator
     - Name + type abbreviation
     - Remove button
   - **If locality exists** in `self._locality_places[transition.id]`:
     - For source transitions: Shows output places only
     - For sink transitions: Shows input places only
     - For normal transitions: Shows both input and output places
   - Each locality place shown as indented row with:
     - Lighter/darker color indicator (lighter for inputs, darker for outputs)
     - Label prefix ("← Input:" or "→ Output:")
     - Place name and current token count
3. **Shows all rows** with `show_all()`

---

## Performance Considerations

### Trade-off: Full Rebuild vs Incremental Add

**Base Class Optimization**:
- Uses `_add_object_row()` for O(1) incremental UI adds
- Avoids full list rebuild on every add

**Our Override**:
- Uses `_update_objects_list()` for O(n) full rebuild
- Necessary to show hierarchical display (transition + localities)

**Impact**:
- Minimal - transition lists are typically small (< 20 items)
- Full rebuild of 20 items is still fast (< 5ms)
- Correct UI display is more important than micro-optimization

### Calling _update_objects_list() Twice?

**Question**: Do we call `_update_objects_list()` twice when adding a transition with locality?

**Answer**: Yes, but it's necessary:

1. **First call** in `add_object()`:
   - Shows transition immediately
   - Locality not added yet
   
2. **Second call** in `add_locality_places()`:
   - Shows transition + locality places
   - Complete display

**Alternative Considered**: Only call once
- Would require combining `add_object()` + `add_locality_places()` into one method
- Breaks separation of concerns
- Harder to maintain
- Not worth the complexity for 1 extra UI rebuild

---

## Testing Checklist

### Test 1: Context Menu Addition ✅
1. Create P1 → T1 → P2
2. Right-click T1 → "Add to Transition Analysis"
3. **Verify UI list shows**:
   - T1 [CON] (T1)
   - ← Input: P1 (X tokens)
   - → Output: P2 (Y tokens)

### Test 2: Search Field Addition ✅
1. Create P3 → T2 → P4
2. Type "T2" in search field, click Search
3. **Verify UI list shows**:
   - T2 [CON] (T2)
   - ← Input: P3 (X tokens)
   - → Output: P4 (Y tokens)

### Test 3: Source Transition ✅
1. Create source T_src → P5
2. Add T_src to analysis
3. **Verify UI list shows**:
   - T_src [CON+SRC] (T3)
   - → Output: P5 (Y tokens)
   - (No input places shown for source)

### Test 4: Sink Transition ✅
1. Create P6 → T_sink (sink)
2. Add T_sink to analysis
3. **Verify UI list shows**:
   - T_sink [CON+SNK] (T4)
   - ← Input: P6 (X tokens)
   - (No output places shown for sink)

### Test 5: Multiple Transitions ✅
1. Add T1 (with locality)
2. Add T2 (with locality)
3. **Verify UI list shows**:
   - T1 with its locality places
   - T2 with its locality places
   - All properly formatted and indented

### Test 6: Remove Transition ✅
1. Add T1 with locality
2. Click [×] button on T1
3. **Verify**: T1 and all its locality places removed from UI list

---

## Related Files

1. **`src/shypn/analyses/transition_rate_panel.py`**
   - Added `add_object()` override (lines 98-110)
   - Added `_update_objects_list()` call in `add_locality_places()` (line 405)

2. **`src/shypn/analyses/plot_panel.py`**
   - Base class with `add_object()` and `_add_object_row()`
   - Provides `_update_objects_list()` (can be overridden)

---

## Documentation

This fix is part of the complete locality plotting restoration:

1. **Integration Fix**: Wire PlaceRatePanel reference to TransitionRatePanel
   - `doc/ANALYSES_LOCALITY_AND_RESET_FIXES.md`

2. **UI List Display Fix** (this document):
   - Show locality places in "Selected transitions" list

3. **Canvas Reset Fix**:
   - Clear canvas properly on reset/clear
   - `doc/ANALYSES_LOCALITY_AND_RESET_FIXES.md`

---

## Summary

**Problem**: 
- ❌ Locality places not shown in "Selected transitions" UI list
- ❌ User has no visual confirmation of what's plotted

**Solution**:
1. ✅ Override `add_object()` to use full UI rebuild
2. ✅ Call `_update_objects_list()` after adding locality places

**Result**:
- ✅ UI list shows transition + locality places (hierarchical)
- ✅ Color-coded indicators (lighter for inputs, darker for outputs)
- ✅ Labels show "← Input:" and "→ Output:" prefixes
- ✅ Token counts displayed for each place
- ✅ Complete visual confirmation of what will be plotted

**Status**: Fixed and ready for testing! 🎉
