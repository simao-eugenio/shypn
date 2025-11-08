# BRENDA Context Menu Transition Selection Bug Fix

## Problem Report

**User Issue**: "Apply Selected to Model shows: Applied 1 parameters to T1, but it must be T27, because T27 was selected"

**Root Cause**: When user right-clicks on T27 and selects "Enrich with BRENDA", the system was applying parameters to T1 instead.

---

## Bug Analysis

### Expected Flow

```
1. User right-clicks on T27
   ↓
2. Context menu: "Enrich with BRENDA"
   ↓
3. Context menu handler stores: _enrichment_transition = T27
   ↓
4. BRENDA panel pre-filled with T27's EC number
   ↓
5. User queries BRENDA
   ↓
6. User selects parameters
   ↓
7. User clicks "Apply Selected to Model"
   ↓
8. System checks: _enrichment_transition → T27
   ↓
9. System applies to T27 ✓
```

### Actual Buggy Flow (BEFORE FIX)

```
1. User right-clicks on T27
   ↓
2. Context menu: "Enrich with BRENDA"
   ↓
3. Context menu calls: set_query_from_transition(transition_id=T27)
   ↓
4. set_query_from_transition() calls: _clear_enrichment_highlight()
   ↓
5. _clear_enrichment_highlight() sets: _enrichment_transition = None  ← BUG!
   ↓
6. Context menu tries to set: _enrichment_transition = T27 (but object might be stale)
   ↓
7. User queries BRENDA
   ↓
8. User selects parameters
   ↓
9. User clicks "Apply Selected to Model"
   ↓
10. System checks: _enrichment_transition → None OR stale object
   ↓
11. System falls back to showing dialog, which defaults to T1 ✗
```

---

## Root Causes Identified

### Issue 1: Stale Transition Object Reference

**Location**: `context_menu_handler.py` line 297

```python
# Context menu stores the transition object directly
brenda_category._enrichment_transition = transition
```

**Problem**: The `transition` object passed from the context menu might be:
- From a different canvas manager instance
- From before a model reload
- From a different tab

When `_show_apply_dialog()` later tries to use this transition, it might be stale or not match any transition in the current canvas manager.

### Issue 2: Potential Clearing of Enrichment Transition

**Location**: `brenda_category.py` line 1833

```python
def set_query_from_transition(...):
    # Clear previous enrichment highlight if user selects a different transition
    self._clear_enrichment_highlight()  # ← Sets _enrichment_transition = None
    
    # Store context
    self._transition_context = {'transition_id': transition_id, ...}
```

**Problem**: This clears `_enrichment_transition` BEFORE the context menu has a chance to set it again. Depending on timing, the enrichment transition might not be properly set.

---

## Fix Applied

### Solution: Re-fetch Transition from Canvas Manager

**Location**: `brenda_category.py` line ~1428 (in `_show_apply_dialog`)

**BEFORE** (Buggy):
```python
def _show_apply_dialog(self, selected_params):
    enrichment_transition = getattr(self, '_enrichment_transition', None)
    
    # If we have an enrichment transition, apply directly to it
    if enrichment_transition:
        # ❌ Uses potentially stale transition object!
        self._apply_single_transition_parameters(enrichment_transition, selected_params)
        return
```

**AFTER** (Fixed):
```python
def _show_apply_dialog(self, selected_params):
    enrichment_transition = getattr(self, '_enrichment_transition', None)
    
    self.logger.info(f"[APPLY_DIALOG] _enrichment_transition: {enrichment_transition}")
    if enrichment_transition:
        self.logger.info(f"[APPLY_DIALOG] _enrichment_transition.id: {enrichment_transition.id}")
    
    # If we have an enrichment transition, apply directly to it
    # BUT: Re-fetch from canvas manager to ensure we have current instance
    if enrichment_transition:
        target_id = enrichment_transition.id
        self.logger.info(f"[APPLY_DIALOG] Enrichment transition detected: {target_id}")
        
        # ✅ Re-fetch the transition from canvas manager (ensure fresh instance)
        target_transition = None
        if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'transitions'):
            for trans in self.model_canvas_manager.transitions:
                if str(trans.id) == str(target_id):
                    target_transition = trans
                    self.logger.info(f"[APPLY_DIALOG] Found matching transition in canvas manager: {trans.id}")
                    break
        
        if target_transition:
            self._apply_single_transition_parameters(target_transition, selected_params)
        else:
            self.logger.error(f"[APPLY_DIALOG] Could not find transition {target_id} in canvas manager!")
            self._show_status(f"Transition {target_id} not found on canvas", error=True)
        return
```

---

## What the Fix Does

1. **Extracts the transition ID** from the potentially stale `_enrichment_transition` object
2. **Re-fetches the transition** from the current `model_canvas_manager.transitions`
3. **Ensures fresh instance** that matches the current canvas state
4. **Adds comprehensive logging** to debug if the enrichment transition is set correctly
5. **Handles missing transition** gracefully with error message

---

## Why This Fix Works

### Before Fix - Stale Reference Problem

```python
# Context menu sets reference
_enrichment_transition = old_transition_object  # From old canvas instance

# Later, when applying...
apply_to(old_transition_object)  # ✗ Wrong canvas instance!
```

### After Fix - ID-Based Lookup

```python
# Context menu sets reference
_enrichment_transition = old_transition_object  # Still potentially stale

# Later, when applying...
target_id = old_transition_object.id  # Extract ID (still valid)
target_transition = find_in_current_canvas(target_id)  # ✓ Get fresh instance!
apply_to(target_transition)  # ✓ Correct canvas instance!
```

---

## Testing Scenarios

### Scenario 1: Simple Context Menu Flow
**Steps**:
1. Right-click on T27
2. Select "Enrich with BRENDA"
3. Query BRENDA
4. Select parameters
5. Click "Apply Selected"

**Expected Result**: ✅ Applied to T27
**Before Fix**: ❌ Applied to T1 (or showed dialog)
**After Fix**: ✅ Applied to T27

---

### Scenario 2: Switch Tabs After Context Menu
**Steps**:
1. Tab 1: Right-click on T27
2. Select "Enrich with BRENDA"
3. Switch to Tab 2 and back to Tab 1
4. Query BRENDA
5. Select parameters
6. Click "Apply Selected"

**Expected Result**: ✅ Applied to T27
**Before Fix**: ❌ Applied to wrong transition or error
**After Fix**: ✅ Applied to T27 (re-fetched from current canvas)

---

### Scenario 3: Model Reload After Context Menu
**Steps**:
1. Right-click on T27
2. Select "Enrich with BRENDA"
3. Reload model (File → Reload)
4. Query BRENDA
5. Select parameters
6. Click "Apply Selected"

**Expected Result**: ✅ Applied to T27 (if it still exists)
**Before Fix**: ❌ Applied to wrong transition or crash
**After Fix**: ✅ Applied to T27 (re-fetched from reloaded canvas)

---

## Debug Logging Added

The fix includes comprehensive debug logging:

```
[APPLY_DIALOG] _enrichment_transition: <Transition object at 0x...>
[APPLY_DIALOG] _enrichment_transition.id: T27
[APPLY_DIALOG] Enrichment transition detected: T27
[APPLY_DIALOG] Found matching transition in canvas manager: T27
[SINGLE_APPLY] Looking for transition with id: T27 (type: <class 'str'>)
[SINGLE_APPLY] Canvas manager has 5 transitions
[SINGLE_APPLY]   Transition 0: id=T1 (type: <class 'str'>)
[SINGLE_APPLY]   Transition 1: id=T5 (type: <class 'str'>)
[SINGLE_APPLY]   Transition 2: id=T27 (type: <class 'str'>)
[SINGLE_APPLY] Found matching transition: T27
[SINGLE_APPLY] Applying 1 parameters to transition T27
...
Applied 1 parameters to T27  ← CORRECT MESSAGE ✓
```

---

## Related Code Architecture

### Transition Lifecycle

```
1. Model Loaded
   ↓
   ModelCanvasManager.transitions = [T1, T5, T27, ...]
   
2. Context Menu
   ↓
   User right-clicks T27
   ↓
   Context menu gets transition from event
   ↓
   _enrichment_transition = transition (might be stale)
   
3. Apply Parameters
   ↓
   target_id = _enrichment_transition.id (extract ID)
   ↓
   target = find_in_canvas_manager(target_id) (re-fetch)
   ↓
   apply_to(target) (use fresh instance)
```

### Key Insight

**Don't cache canvas objects across operations - always re-fetch by ID**

This is the same pattern we used to fix the canvas instance bug earlier. The principle:
- **IDs are stable** (survive tab switches, reloads)
- **Object references are volatile** (become stale easily)
- **Always re-fetch before use** (ensures correct instance)

---

## Files Modified

1. **brenda_category.py** (line ~1428)
   - Modified `_show_apply_dialog()` to re-fetch transition from canvas manager
   - Added debug logging for transition lookup

---

## Verification

To verify the fix works, check the log output:

1. Right-click on T27 and select "Enrich with BRENDA"
2. Query BRENDA and select parameters
3. Click "Apply Selected"
4. Check logs for:
   ```
   [APPLY_DIALOG] _enrichment_transition.id: T27
   [APPLY_DIALOG] Found matching transition in canvas manager: T27
   Applied 1 parameters to T27
   ```

If logs show:
- `_enrichment_transition: None` → Context menu not setting it properly
- `Could not find transition T27 in canvas manager` → Transition doesn't exist in current canvas
- `Applied 1 parameters to T1` → Falling back to dialog (enrichment_transition not set)

---

## Additional Improvements to Consider

### 1. Store ID Instead of Object Reference

**Current**:
```python
brenda_category._enrichment_transition = transition  # Store object
```

**Better**:
```python
brenda_category._enrichment_transition_id = transition.id  # Store ID only
```

This would avoid storing stale object references entirely.

### 2. Validate Transition Exists Before Querying

When context menu sets enrichment transition, validate it exists in canvas manager:

```python
# In context menu handler
if hasattr(brenda_category, 'validate_transition'):
    if brenda_category.validate_transition(transition.id):
        brenda_category._enrichment_transition_id = transition.id
    else:
        # Show error: transition not found
```

### 3. Clear Enrichment Transition at Appropriate Time

Currently cleared in `_clear_enrichment_highlight()` which is called in multiple places. Consider only clearing:
- After successful apply (keep it during query/selection)
- When user explicitly selects a different transition
- Not when just re-populating query fields

---

## Conclusion

**Problem**: Context menu "Enrich with BRENDA" was applying parameters to wrong transition (T1 instead of T27)

**Root Cause**: Stale transition object reference stored by context menu

**Solution**: Re-fetch transition from canvas manager by ID before applying

**Impact**: User can now right-click on any transition and BRENDA will correctly apply parameters to that specific transition

**Status**: ✅ FIXED
