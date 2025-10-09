# Bug Fix: Continuous Transition Overflow

**Date:** October 8, 2025  
**Status:** ✅ Fixed  
**Test Impact:** 36/38 time tests passing (up from 35/38)  
**Overall:** 61/63 tests passing (97%, up from 60/63)

---

## Problem Description

### Symptom

Continuous transitions could transfer **more tokens than available** in source places, resulting in negative token counts.

### Example

```python
# Setup
P1 = Place(tokens=5.0)
T1 = Transition(type='continuous', rate=1000.0)
P2 = Place(tokens=0.0)

# Execute
controller.step(dt=1.0)

# Expected behavior:
# transfer = min(rate * dt, available) = min(1000, 5) = 5 tokens
# P1 = 0, P2 = 5

# BUGGY behavior (before fix):
# transfer = rate * dt = 1000 tokens
# P1 = -995 ❌ (NEGATIVE!)
# P2 = 1000 ✅
```

### Root Cause

In `continuous_behavior.py`, the `integrate_step()` method calculated transfer amount as:

```python
# OLD CODE (buggy)
consumption = arc.weight * rate * dt
actual_consumption = min(consumption, source_place.tokens)  # Per-arc clamping
source_place.set_tokens(source_place.tokens - actual_consumption)
```

**Problem:** Each arc was clamped independently, but if multiple arcs consumed from the same place, or if the calculation was wrong, negative tokens could occur.

**Better:** The **flow rate** should be clamped **before** calculating per-arc consumption.

---

## Solution

### Design

Calculate the maximum possible flow based on **available tokens across all input arcs**, then use that clamped flow for all operations:

```python
# 1. Calculate intended flow
intended_flow = rate * dt

# 2. Clamp to available tokens (check all input arcs)
actual_flow = intended_flow
for arc in input_arcs:
    max_flow_from_arc = source_place.tokens / arc.weight
    actual_flow = min(actual_flow, max_flow_from_arc)

# 3. Use clamped flow for all arcs
consumption = arc.weight * actual_flow  # Always <= available
```

### Implementation

**File:** `src/shypn/engine/continuous_behavior.py`

**Location:** `integrate_step()` method, lines ~276-320

**Changes:**

1. **Calculate intended flow first:**
   ```python
   intended_flow = rate * dt
   ```

2. **Clamp flow to available tokens (Phase 1):**
   ```python
   actual_flow = intended_flow
   if not is_source:
       for arc in input_arcs:
           source_place = self._get_place(arc.source_id)
           max_flow_from_arc = source_place.tokens / arc.weight
           actual_flow = min(actual_flow, max_flow_from_arc)
   ```

3. **Use clamped flow for consumption (Phase 2):**
   ```python
   consumption = arc.weight * actual_flow  # Guaranteed <= available
   source_place.set_tokens(source_place.tokens - consumption)
   ```

4. **Use clamped flow for production (Phase 3):**
   ```python
   production = arc.weight * actual_flow
   target_place.set_tokens(target_place.tokens + production)
   ```

5. **Record clamping in event details:**
   ```python
   return {
       'rate': rate,  # Desired rate
       'actual_rate': actual_flow / dt,  # Actual rate achieved
       'clamped': (actual_flow < intended_flow)  # Was it limited?
   }
   ```

---

## Verification

### Test Case

**File:** `tests/test_time_continuous.py`  
**Test:** `test_very_large_rate()`

```python
def test_very_large_rate(self):
    """Very large rate should not exceed source tokens."""
    # Setup
    p1.tokens = 5.0
    rate = 1000.0  # Huge rate
    dt = 1.0
    
    # Execute
    controller.step(1.0)
    
    # Verify: Should not transfer more than available
    assert p1.tokens >= 0, "Source should not go negative"
    assert p2.tokens <= 5.0 + 1e-6, "Should not transfer more than available"
```

**Before Fix:** ❌ xfail (marked as known bug)  
**After Fix:** ✅ PASSED

### Test Results

```bash
$ pytest tests/test_time_continuous.py::test_very_large_rate -v
test_very_large_rate PASSED ✅
```

**All time tests:**
```bash
$ pytest tests/test_time_*.py -v --tb=no
36 passed, 1 skipped, 1 xfailed ✅
```

**Combined tests:**
```bash
$ pytest tests/test_phase*.py tests/test_time_*.py -q
61 passed, 1 skipped, 1 xfailed ✅
```

---

## Impact

### Test Suite Status

| Suite | Before | After | Change |
|-------|--------|-------|--------|
| Time tests | 35/38 (92%) | 36/38 (95%) | +1 ✅ |
| Phase tests | 25/25 (100%) | 25/25 (100%) | - |
| **Combined** | **60/63 (95%)** | **61/63 (97%)** | **+1** |

### Remaining Issues

1. **Bug #2: Window crossing** (1 skip, 1 xfail)
   - Behavior-level detection complete
   - Controller integration pending
   - Target: 63/63 (100%)

---

## Key Insights

### Why This Bug Matters

1. **Physical impossibility:** Can't transfer what doesn't exist
2. **Conservation violation:** Total tokens in system should be conserved
3. **Negative tokens:** Breaks mathematical model assumptions
4. **Cascading errors:** Negative tokens can cause further issues downstream

### Correct Semantics

For continuous Petri nets:
- **Rate** defines desired flow speed (tokens/second)
- **Actual flow** is limited by: `min(rate * dt, available_tokens)`
- **Conservation** must hold: tokens_consumed = tokens_produced
- **Clamping** should be transparent to user (logged in event details)

### Design Pattern

This fix follows the **clamp-before-apply** pattern:

```python
# 1. Calculate desired value
desired = calculate_desired_value()

# 2. Clamp to constraints
actual = min(desired, constraint1, constraint2, ...)

# 3. Apply clamped value (guaranteed safe)
apply(actual)

# 4. Report both desired and actual
return {'desired': desired, 'actual': actual, 'clamped': (actual < desired)}
```

---

## Related Bugs

### Bug #1: Negative Time Steps ✅ FIXED
- **Issue:** Time could go backwards
- **Fix:** Added validation in `controller.step()`
- **Impact:** All tests passing

### Bug #2: Window Crossing ⚠️ PARTIAL
- **Issue:** Zero-width windows can be skipped
- **Status:** Behavior detection done, controller integration pending
- **Impact:** 2 tests (1 skip, 1 xfail)

### Bug #3: Continuous Overflow ✅ FIXED (this document)
- **Issue:** Transfer more than available
- **Fix:** Clamp flow before applying
- **Impact:** +1 test passing (36/38)

---

## Documentation Updates

### Updated Files

1. **`src/shypn/engine/continuous_behavior.py`** (~45 lines modified)
   - Added flow clamping logic
   - Added actual_rate tracking
   - Added clamped flag in results

2. **`tests/test_time_continuous.py`** (~5 lines modified)
   - Removed xfail marker
   - Updated docstring

3. **`doc/TEST_STATUS_SUMMARY.md`** (to be updated)
   - Update test counts
   - Update known issues

---

## Code Diff Summary

### Key Changes

```diff
# continuous_behavior.py: integrate_step()

+ # Calculate intended flow
+ intended_flow = rate * dt
+ 
+ # Clamp to available tokens
+ actual_flow = intended_flow
+ if not is_source:
+     for arc in input_arcs:
+         source_place = self._get_place(arc.source_id)
+         max_flow_from_arc = source_place.tokens / arc.weight
+         actual_flow = min(actual_flow, max_flow_from_arc)
  
- # OLD: Per-arc clamping (buggy)
- consumption = arc.weight * rate * dt
- actual_consumption = min(consumption, source_place.tokens)

+ # NEW: Use pre-clamped flow (correct)
+ consumption = arc.weight * actual_flow
```

**Lines Changed:** ~45  
**Files Changed:** 2  
**Time to Fix:** ~30 minutes  
**Complexity:** Low (straightforward clamping logic)

---

## Lessons Learned

1. **Clamp early:** Clamp values at calculation time, not at application time
2. **Global vs local constraints:** Flow must respect constraints across all arcs
3. **Test edge cases:** Large rates, zero tokens, multiple arcs all need testing
4. **Report clamping:** Users should know when constraints are active
5. **Conservation laws:** Physics-inspired constraints are non-negotiable

---

## Next Steps

1. ✅ **Bug #3 fixed** - This document
2. ⏳ **Update TEST_STATUS_SUMMARY.md** - Reflect new test counts
3. ⏳ **Bug #2: Complete window crossing** - Controller integration
4. ⏳ **Achieve 100%** - Fix remaining 2 tests (1 skip, 1 xfail)

---

**Status:** Bug fixed successfully. Continuous transitions now correctly respect available token constraints. System integrity maintained.
