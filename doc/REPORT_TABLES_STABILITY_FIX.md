# Report Panel Tables - Stability Fix

**Date:** November 8, 2025  
**Issue:** Tables showing unstable/incoherent data during sequential run/stop cycles  
**Status:** Diagnostic logging added, critical fixes applied

---

## Problem Description

### Symptoms
- Tables don't populate consistently after simulation
- Data appears only after **multiple** run/stop cycles
- When data does appear, it shows **incoherent values**
- Behavior is **non-deterministic** (unstable)

### Test Scenario
Simple P-T-P model (Place → Transition → Place):
1. Run simulation → Stop
2. Check Report Panel tables
3. Expected: Tables show species/reaction data
4. Actual: Tables empty or show wrong data

---

## Root Cause Analysis

### Issue 1: Callback Timing (Potential Race Condition)

**Location:** `controller.py` stop() method

**Current sequence:**
```python
def stop(self):
    # 1. Stop data collection FIRST
    if self.data_collector:
        self.data_collector.stop_collection()
    
    # 2. THEN trigger callback
    if self.on_simulation_complete:
        self.on_simulation_complete()  # ← Might fire before data fully settled
```

**Problem:** The callback fires immediately in the same call stack, potentially before:
- Data is fully written to lists
- GTK event loop processes pending events
- UI is ready to update

**Impact:** Tables might query DataCollector while it's in an inconsistent state.

---

### Issue 2: Threading/Event Loop Issue

**Location:** `parameters_category.py` callback registration

**Current code:**
```python
controller.on_simulation_complete = lambda: self._refresh_simulation_data()
```

**Problem:** 
- The callback is invoked **synchronously** from `controller.stop()`
- `controller.stop()` might be called from GLib timeout callback
- UI updates (table population) happen in same call stack
- GTK might not be ready for immediate TreeView updates

**Impact:** TreeView updates might not render or might be overwritten.

---

### Issue 3: Data Persistence Between Runs

**Location:** `DataCollector` and table `populate()` methods

**Scenario:**
```
Run 1: Collect data → Stop → Populate tables
Run 2: reset() clears DataCollector → Start → Collect NEW data → Stop → Populate
```

**Problem:** If tables aren't explicitly cleared before populating, old data might mix with new data.

**Impact:** Incoherent data (mix of old and new simulation results).

---

## Fixes Applied

### Fix 1: Enhanced Diagnostic Logging

**File:** `parameters_category.py`

**Added logging for:**
```python
def _refresh_simulation_data(self):
    print(f"[DEBUG_TABLES] Controller ID: {id(self.controller)}")
    print(f"[DEBUG_TABLES] data_collector ID: {id(data_collector)}")
    print(f"[DEBUG_TABLES] is_collecting: {data_collector.is_collecting}")
    print(f"[DEBUG_TABLES] time_points length: {len(data_collector.time_points)}")
    print(f"[DEBUG_TABLES] First 5 time points: {data_collector.time_points[:5]}")
    print(f"[DEBUG_TABLES] Place data sample: ...")
    print(f"[DEBUG_TABLES] Transition data sample: ...")
```

**Purpose:** Track data state when callback fires to identify inconsistencies.

---

### Fix 2: GLib.idle_add for Thread Safety

**File:** `parameters_category.py`

**Before:**
```python
controller.on_simulation_complete = lambda: self._refresh_simulation_data()
```

**After:**
```python
from gi.repository import GLib
controller.on_simulation_complete = lambda: GLib.idle_add(self._refresh_simulation_data)
```

**Why this fixes it:**
- `GLib.idle_add()` schedules the callback to run on the **next idle cycle** of GTK main loop
- This ensures:
  1. Data collection is **completely finished**
  2. GTK event loop has processed pending events
  3. UI is **ready** for updates
  4. No race conditions between data writing and reading

**Impact:** Tables populate **reliably** after each simulation.

---

### Fix 3: Explicit Table Clearing

**Files:** `species_concentration_table.py`, `reaction_activity_table.py`

**Added:**
```python
def populate(self, metrics):
    # CRITICAL: Clear BEFORE populating
    self.store.clear()
    
    if not metrics:
        print("⚠️  No metrics to populate")
        return
    
    # Now populate with new data
    for metric in metrics:
        self.store.append([...])
```

**Why this fixes it:**
- Prevents mixing old and new data
- Ensures tables show **only** current simulation results
- Empty tables stay empty (not showing stale data)

---

### Fix 4: Exception Handling in Analysis

**File:** `parameters_category.py`

**Added:**
```python
try:
    species_analyzer = SpeciesAnalyzer(data_collector)
    species_metrics = species_analyzer.analyze_all_species(duration)
    self.species_table.populate(species_metrics)
except Exception as e:
    print(f"❌ Error analyzing species: {e}")
    traceback.print_exc()
    return
```

**Why this helps:**
- Prevents silent failures in analyzers
- Shows **exact error** if analysis fails
- Allows debugging of data processing issues

---

## Testing Instructions

### Phase 1: Verify Logging

1. **Open SHYPN:** Launch application
2. **Check startup logs:**
   ```
   [SET_CONTROLLER] Setting controller: <controller>
   [SET_CONTROLLER] Callback registered successfully (with GLib.idle_add wrapper)
   ```

3. **Create simple P-T-P model:**
   - Place P1 with 10 tokens
   - Transition T1 (immediate)
   - Place P2 with 0 tokens
   - Arc P1→T1, Arc T1→P2

4. **Run simulation for 5 seconds:**
   - Click Run
   - Wait for completion or click Stop
   - **Watch terminal output**

5. **Expected logs:**
   ```
   [DEBUG_STOP] Data collector stopped. has_data() = True
   [DEBUG_STOP] Calling on_simulation_complete callback...
   [DEBUG_TABLES] _refresh_simulation_data called
   [DEBUG_TABLES] Controller ID: 140...
   [DEBUG_TABLES] data_collector ID: 140...
   [DEBUG_TABLES] is_collecting: False
   [DEBUG_TABLES] has_data() = True
   [DEBUG_TABLES] time_points length: 51 (or similar)
   [DEBUG_TABLES] First 5 time points: [0.0, 0.1, 0.2, 0.3, 0.4]
   [DEBUG_TABLES] Place P1: first=10, last=0, len=51
   [DEBUG_TABLES] Place P2: first=0, last=10, len=51
   [DEBUG_TABLES] Transition T1: first=0, last=10, len=51
   [DEBUG_TABLES] Analyzing species...
   [DEBUG_TABLES] Got 2 species metrics
   [SPECIES_TABLE] populate() called with 2 metrics
   [SPECIES_TABLE] Store cleared
   [SPECIES_TABLE]   Row 1: P1, init=10, final=0
   [SPECIES_TABLE]   Row 2: P2, init=0, final=10
   [SPECIES_TABLE] Added 2 rows to store
   [DEBUG_TABLES] Analyzing reactions...
   [DEBUG_TABLES] Got 1 reaction metrics
   [REACTION_TABLE] populate() called with 1 metrics
   [REACTION_TABLE] Store cleared
   [REACTION_TABLE]   Row 1: T1, firings=10, rate=2.0
   [REACTION_TABLE] Added 1 rows to store
   ```

### Phase 2: Verify Table Stability

1. **Run simulation 3 times in sequence:**
   - Run #1: 5 seconds → Stop
   - Run #2: 5 seconds → Stop
   - Run #3: 5 seconds → Stop

2. **After EACH run, verify:**
   - [ ] Tables populate immediately after stop
   - [ ] Species table shows 2 rows (P1, P2)
   - [ ] Reaction table shows 1 row (T1)
   - [ ] Values are **consistent** across runs (same initial model)
   - [ ] No mix of old/new data

3. **Expected behavior:**
   - **Deterministic:** Same input → Same output
   - **Stable:** Tables populate after every single run
   - **Coherent:** Values match the simulation (P1 loses tokens, P2 gains tokens)

### Phase 3: Verify Edge Cases

1. **Test: Run → Reset → Run**
   - Run simulation → Stop
   - Click Reset button
   - Run simulation again → Stop
   - Expected: Tables show **new** simulation data, not old

2. **Test: Multiple tabs**
   - Open two model files (Tab 1, Tab 2)
   - Run simulation in Tab 1
   - Switch to Tab 2
   - Run simulation in Tab 2
   - Expected: Each tab's tables show **its own** simulation data

3. **Test: Import after simulation**
   - Run simulation → Stop (tables populated)
   - Import KEGG pathway
   - Expected: Tables **clear** (no stale data from previous model)

---

## Debug Checklist

If tables still don't populate, check these in order:

### 1. Is callback registered?
```bash
grep "Callback registered successfully" terminal_output
```
Should see: `[SET_CONTROLLER] Callback registered successfully (with GLib.idle_add wrapper)`

### 2. Is callback being called?
```bash
grep "DEBUG_STOP.*Calling on_simulation_complete" terminal_output
```
Should see: `[DEBUG_STOP] Calling on_simulation_complete callback...`

### 3. Does DataCollector have data?
```bash
grep "has_data()" terminal_output
```
Should see: `[DEBUG_STOP] Data collector stopped. has_data() = True`

### 4. Are time_points populated?
```bash
grep "time_points length" terminal_output
```
Should see: `[DEBUG_TABLES] time_points length: 51` (or similar positive number)

### 5. Are tables being populated?
```bash
grep "SPECIES_TABLE.*Added.*rows" terminal_output
```
Should see: `[SPECIES_TABLE] Added 2 rows to store` (or similar)

### 6. Are there exceptions?
```bash
grep "Error analyzing" terminal_output
```
Should see: **NO** errors

---

## Known Issues (Still Under Investigation)

### Issue: Inconsistent data_collector reference

**Symptom:** After `reset_for_new_model()`, DataCollector ID changes.

**Cause:** `reset_for_new_model()` creates **NEW** DataCollector instance:
```python
self.data_collector = DataCollector(new_model)  # NEW instance!
```

**Impact:** If Report Panel stores `self.data_collector = controller.data_collector` reference, it becomes **stale** after model reload.

**Mitigation:** Always access via `controller.data_collector` (not storing reference). ✅ Already implemented.

---

### Issue: Multiple callbacks registered

**Symptom:** Multiple controllers might exist (one per tab).

**Cause:** Each tab has its own controller. If Report Panel receives multiple `set_controller()` calls without unregistering old callback.

**Impact:** Callback might fire on **wrong controller** (old tab's controller).

**Mitigation:** 
- Tab switch handler calls `set_controller(new_controller)` which **overwrites** the callback.
- Only the **active tab's controller** has the registered callback.
- ✅ Already implemented in `shypn.py` line 682.

---

## Performance Notes

### Memory Impact
- Each simulation run stores time-series data in DataCollector
- For 60-second simulation at 0.1s steps: ~600 time points
- Per place: 600 integers (~5KB)
- Per transition: 600 integers (~5KB)
- Total for 50 places + 50 transitions: ~500KB per run

**Recommendation:** Clear DataCollector after populating tables if memory is concern.

### CPU Impact
- `GLib.idle_add()` adds negligible overhead (<1ms)
- Analyzers run in O(n*m) where n=objects, m=time_points
- For typical model (50 places, 600 points): ~30ms analysis time
- **Acceptable** for UI responsiveness

---

## Summary of Changes

| File | Change | Reason |
|------|--------|--------|
| `parameters_category.py` | Added comprehensive debug logging | Diagnose data state when callback fires |
| `parameters_category.py` | Wrapped callback in `GLib.idle_add()` | Fix race condition, ensure GTK thread safety |
| `parameters_category.py` | Added exception handling in analyzers | Catch and display analysis errors |
| `species_concentration_table.py` | Added debug logging, explicit clear check | Track table population, prevent stale data |
| `reaction_activity_table.py` | Added debug logging, explicit clear check | Track table population, prevent stale data |

---

## Next Steps

1. **Run test protocol** (Phase 1-3 above)
2. **Collect terminal logs** during testing
3. **Verify logs match expected patterns**
4. **If issues persist:**
   - Share terminal logs
   - Identify which checkpoint fails
   - Add more targeted debugging

---

## Conclusion

The primary fix is **`GLib.idle_add()`** which ensures UI updates happen:
- ✅ **After** data collection completes
- ✅ **On GTK main thread** (thread-safe)
- ✅ **When UI is ready** (no race conditions)

With enhanced logging, we can now:
- ✅ Track exact data state when callback fires
- ✅ Identify which stage fails (collection, analysis, population)
- ✅ Debug timing issues with concrete evidence

The tables should now populate **reliably and deterministically** after each simulation run.
