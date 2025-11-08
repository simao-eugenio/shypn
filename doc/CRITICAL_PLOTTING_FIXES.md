# Critical Plotting Fixes - Debug Output Analysis

## Issues Found from Debug Output

### Issue 1: SwissKnifePalette Architecture Mismatch ❌

**Error:**
```
[WIRE]   ❌ FAIL: No widget_palette_instances attribute
```

**Root Cause:**
The application uses `swissknife_palette_new.py` (refactored modular architecture), where `widget_palette_instances` is stored in the `registry` attribute, not directly on the SwissKnifePalette instance.

**Old Structure (swissknife_palette.py):**
```python
swissknife.widget_palette_instances = {}
```

**New Structure (swissknife_palette_new.py):**
```python
swissknife.registry.widget_palette_instances = {}
```

**Fix Applied:**
Modified `model_canvas_loader.py` → `_wire_data_collector_for_page()` to support both architectures:

```python
# NEW architecture: widget_palette_instances is in swissknife.registry
# OLD architecture: widget_palette_instances is directly on swissknife
simulate_tools_palette = None

if hasattr(swissknife, 'registry') and hasattr(swissknife.registry, 'widget_palette_instances'):
    print(f"[WIRE]   Using NEW architecture (registry.widget_palette_instances)")
    simulate_tools_palette = swissknife.registry.widget_palette_instances.get('simulate')
elif hasattr(swissknife, 'widget_palette_instances'):
    print(f"[WIRE]   Using OLD architecture (widget_palette_instances)")
    simulate_tools_palette = swissknife.widget_palette_instances.get('simulate')
else:
    print(f"[WIRE]   ❌ FAIL: No widget_palette_instances found in registry or swissknife")
```

**Impact:** 
- **CRITICAL** - Without this fix, right panel data collector is never wired
- Plot panels have no data collector reference
- No plotting possible

**Status:** ✅ FIXED

---

### Issue 2: Transition Missing `outgoing_arcs` Attribute ❌

**Error:**
```python
AttributeError: 'Transition' object has no attribute 'outgoing_arcs'
File: reaction_analyzer.py, line 99
```

**Root Cause:**
The `Transition` class in `netobjs/transition.py` does not have an `outgoing_arcs` attribute. Arcs are stored separately in the model's arc collection.

**Incorrect Code:**
```python
# reaction_analyzer.py line 99
output_arcs = [a for a in transition.outgoing_arcs]  # ❌ Transition has no outgoing_arcs
```

**Fix Applied:**
Get arcs from the model's arc collection:

```python
# Get output arcs from model (transition → place)
output_arcs = [arc for arc in self.model.arcs 
              if hasattr(arc, 'source') and arc.source == transition]
tokens_per_firing = sum(arc.weight for arc in output_arcs) if output_arcs else 1
metrics.total_flux = metrics.firing_count * tokens_per_firing
```

**Impact:**
- **CRITICAL** - Without this fix, simulation stops with exception
- Report Panel tables cannot populate
- Application crashes on simulation stop

**Status:** ✅ FIXED

---

## Debug Output Analysis - What's Working

### ✅ Data Collection Working
```
[OLD_DC] Step 1 at time 0.0060 (collector id=132864536870592)
[OLD_DC]   Collecting data for 65 places
[OLD_DC]     Place P1 (P1): 0 tokens
[OLD_DC]     Place P27 (P27): 1 tokens
...
[OLD_DC] Step 2 at time 0.0120 (collector id=132864536870592)
[OLD_DC] Step 3 at time 0.0180 (collector id=132864536870592)
```

**Analysis:** OLD data collector is properly receiving simulation steps and collecting place data.

### ✅ Simulation Controller Wiring
```
[RESET] ✅ Updating SimulateToolsPaletteLoader.simulation reference
[RESET] New controller ID: 132864536671392
[RESET] Re-registered palette step listener
[RESET] Re-registered data collector step listener
[RESET] ✅ Preserved both data collectors (controller + palette)
```

**Analysis:** Lifecycle manager correctly wires both data collectors to the controller.

### ✅ Report Panel Data Collector
```
[STOP] Data collector stopped. Has data: True
[STOP] Time points collected: 1793
[STOP] Places tracked: 65
[STOP] Transitions tracked: 39
[REPORT] has_data() = True
[REPORT] Data available! Time points: 1793
```

**Analysis:** NEW data collector (for Report Panel) is working correctly and has collected simulation data.

---

## What Still Needs Testing

### 1. Plot Panel Data Wiring

**Now that SwissKnifePalette wiring is fixed**, we need to verify:

1. Open model → Run simulation
2. Open Dynamic Analyses Panel
3. Select transition for plotting
4. **Watch for:**
   ```
   [WIRE] ✅ SUCCESS: Wiring data_collector to right panel
   [WIRE]    data_collector=<...> (id=XXXXX)
   [CATEGORY] TransitionsCategory.set_data_collector() called
   [CATEGORY]   data_collector=<...> (id=XXXXX)  ← Should match [WIRE] ID
   [PLOT] _get_rate_data() called for transition X
   [PLOT]   self.data_collector=<...> (id=XXXXX)  ← Should match [WIRE] ID
   [PLOT]   raw_events count: > 0
   ```

5. **Expected Result:** Plot appears with transition firing data

### 2. Tab Switching

**Test with multiple models:**

1. Open Model 1 → Note collector ID from [WIRE]
2. Open Model 2 → Should see different collector ID
3. Switch to Model 1 tab
   - Should see `[TAB_SWITCH]` output
   - Should see `[WIRE]` re-wiring with Model 1's collector ID
   - Should see `[CATEGORY]` updates with Model 1's collector ID
4. Switch to Model 2 tab
   - Should see `[WIRE]` re-wiring with Model 2's collector ID

**Expected Result:** Each tab maintains its own data collector, plots show correct data per tab.

### 3. Reset Functionality

**Test plot clearing on reset:**

1. Run simulation with plots visible
2. Click Reset button
3. **Watch for:** Plots clearing (separate fix already applied)
4. Run simulation again
5. **Expected Result:** Plots update with new data

---

## Files Modified

### 1. model_canvas_loader.py
**Location:** `_wire_data_collector_for_page()` method (lines ~230-250)

**Change:** Support both OLD and NEW SwissKnifePalette architectures
- Check `swissknife.registry.widget_palette_instances` first (NEW)
- Fallback to `swissknife.widget_palette_instances` (OLD)

**Impact:** Critical for plot panel data wiring

### 2. reaction_analyzer.py
**Location:** `_analyze_transition()` method (lines ~99-101)

**Change:** Get output arcs from model's arc collection, not from transition
```python
# OLD: output_arcs = [a for a in transition.outgoing_arcs]
# NEW: output_arcs = [arc for arc in self.model.arcs if arc.source == transition]
```

**Impact:** Critical for Report Panel table population

---

## Next Steps

1. **Test the application** with the fixes applied
2. **Verify plotting works** - transitions selected → plots appear
3. **Verify Report Panel tables populate** - simulation stops → tables show data
4. **Test tab switching** - multiple models → correct data per tab
5. **Remove debug output** once verified working (all print statements)

---

## Debug Output to Remove Later

Once everything is verified working, remove debug statements from:

1. `model_canvas_loader.py` - All `[WIRE]` and `[TAB_SWITCH]` prints
2. `base_dynamic_category.py` - All `[CATEGORY]` prints
3. `analyses/data_collector.py` - All `[OLD_DC]` prints  
4. `transition_rate_panel.py` - All `[PLOT]` prints

**Keep only essential logging** for production debugging.
