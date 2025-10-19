# Pathway Transitions Not Firing - Root Cause and Fix

**Date**: October 19, 2025  
**Issue**: Imported pathway transitions were enabled but had zero rate, causing no token flow  
**Status**: ✅ FIXED

---

## Problem Summary

### User Report
After KEGG import → layout → add sources → simulate:
- ✓ Source transitions fire (generate tokens)
- ✗ Pathway transitions DON'T fire (tokens accumulate but don't flow)

### Initial Diagnosis
Test showed `Structurally enabled: 0/39` which seemed to indicate enablement issue, but this was actually a **test bug** (calling non-existent method `is_structurally_enabled()`).

### Actual Root Cause
Once test was fixed to call correct method (`can_fire()`), discovered:
- ✓ All 39 transitions were enabled
- ✓ Transitions had valid rate functions: `michaelis_menten(P105, 10.0, 0.5)`
- ✗ **Rate evaluated to 0.0** - no token flow!

---

## Root Cause Analysis

### The Bug

In `src/shypn/engine/continuous_behavior.py`, the rate function compiler builds an evaluation context with place tokens:

```python
# BEFORE (BROKEN):
for place_id, place in places.items():
    context[f'P{place_id}'] = place.tokens
```

### The Issue

For imported models:
- Place IDs are strings like `"P105"`, `"P88"`, etc. (not numeric)
- Rate expressions reference places as `P105`, `P88`, etc.
- Code created context variables: `PP105`, `PP88` (double P!)
- Expression `michaelis_menten(P105, ...)` looked for `P105` but found `PP105`
- Result: Variable not found → defaults to 0 → rate = 0 → no flow

### Example

```python
places = {'P105': <Place with 1 token>, 'P88': <Place with 1 token>}
rate_expr = "michaelis_menten(P105, 10.0, 0.5)"

# BROKEN context:
context = {
    'PP105': 1.0,  # Oops! Double P
    'PP88': 1.0
}

# Evaluation:
eval("michaelis_menten(P105, 10.0, 0.5)", context)
# P105 not found → treats as 0
# michaelis_menten(0, 10.0, 0.5) = 0 * 10.0 / (0.5 + 0) = 0
```

---

## The Fix

Updated `continuous_behavior.py` to handle both numeric IDs and string IDs:

```python
# AFTER (FIXED):
for place_id, place in places.items():
    # Handle both numeric IDs (1, 2, 3) and string IDs ("P88", "P105")
    if isinstance(place_id, str) and place_id.startswith('P'):
        # ID already has P prefix (e.g., "P105")
        context[place_id] = place.tokens
    else:
        # Numeric ID needs P prefix (e.g., 1 → P1)
        context[f'P{place_id}'] = place.tokens
```

Now:
- String ID `"P105"` → context variable `P105` ✓
- Numeric ID `105` → context variable `P105` ✓
- Rate expression matches context variable ✓

---

## Verification

### Before Fix
```
Running 50 simulation steps...
  Step 1: tokens=26.05 (only sources firing)
  Step 2: tokens=26.10 (only sources firing)
  ...
  Step 50: tokens=27.50 (only sources firing)

Places with changes: 5/26 (only source outputs)
```

### After Fix
```
Running 50 simulation steps...
  Step 1: tokens=26.16 (sources + pathway)
  Step 2: tokens=25.67 (pathway consuming!)
  Step 3: tokens=25.25 (active processing)
  ...
  Step 50: tokens=27.95 (balanced flow)

Places with changes: 26/26 (entire pathway active!)
```

### Rate Evaluation
```
Transition: T1 (R00710)
  Input: P105 (1 token)
  Rate expression: michaelis_menten(P105, 10.0, 0.5)

BEFORE FIX:
  rate: 0.0
  consumed: {}
  produced: {}

AFTER FIX:
  rate: 6.666666666666667
  consumed: {'P105': 0.6666666666666667}
  produced: {'P45': 0.6666666666666667}
```

---

## Impact

### Models Affected
- ✅ KEGG imports (use string IDs like "P105")
- ✅ SBML imports (likely use string IDs)
- ✅ Any model with string place IDs
- ⚠️ Models with numeric IDs were already working

### Files Modified
1. **`src/shypn/engine/continuous_behavior.py`** (lines 134-136)
   - Fixed place ID → context variable mapping
   - Now handles both string and numeric IDs

2. **`tests/validate/headless/test_any_model.py`** (line 320)
   - Fixed test to call `can_fire()` instead of non-existent `is_structurally_enabled()`

3. **`tests/validate/headless/test_headless_simulation.py`** (lines 215, 367)
   - Fixed test to call `can_fire()` instead of non-existent `is_structurally_enabled()`

### Test Results
```
================================================================================
✓ ALL TESTS PASSED!
================================================================================

Test Results:
  ✓ PASS: load
  ✓ PASS: transition_types
  ✓ PASS: canvas_manager
  ✓ PASS: controller
  ✓ PASS: behaviors
  ✓ PASS: simulation

Simulation Results:
  Structurally enabled: 39/39
  Steps executed: 50
  Token change: +1.95
  All 26 places active
```

---

## Lessons Learned

### 1. ID Type Assumptions
**Problem**: Code assumed numeric place IDs  
**Reality**: Import systems use string IDs  
**Fix**: Handle both formats gracefully

### 2. Silent Failures
**Problem**: Rate of 0 didn't raise an error  
**Why**: 0 is a valid rate (transition can be disabled)  
**Lesson**: Need better debugging tools to detect "unexpected zero rates"

### 3. Test Quality
**Problem**: Test called non-existent method `is_structurally_enabled()`  
**Why**: Method was silently failing in try/except block  
**Fix**: Use correct method `can_fire()` and check exceptions

### 4. Context Debugging
**Problem**: Hard to diagnose evaluation context issues  
**Solution**: Add verbose mode to show:
  - Place IDs being added to context
  - Context variable names
  - Expression evaluation steps

---

## Related Documentation

- **`doc/headless/README.md`**: Headless testing guide
- **`doc/headless/GLYCOLYSIS_SIMULATION_SOURCES.md`**: Source transitions setup
- **`src/shypn/engine/continuous_behavior.py`**: Continuous behavior implementation
- **`src/shypn/engine/function_catalog.py`**: Rate function catalog

---

## Testing Commands

```bash
# Test Glycolysis with sources (should show active pathway)
./headless glycolysis-sources -s 50

# Verbose mode (shows all steps)
./headless glycolysis-sources -s 50 -v

# Test any model
./headless workspace/projects/MyModel/model.shy -s 100
```

---

**Status**: ✅ **FIXED and VERIFIED**  
**Commit**: Ready for commit  
**Tests**: All passing
