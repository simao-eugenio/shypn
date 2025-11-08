# Plotting Debug Instructions

## Problem

Transitions and places selected for plotting, but no plotting occurs after recent modifications.

## Root Cause Hypothesis

The right panel's data collector reference may not be updating correctly when:
1. Opening a new model
2. Switching between canvas tabs
3. Running simulations

This causes plot panels to fetch data from the wrong (or missing) data collector.

## Debug Output Added

I've added comprehensive debug statements to trace the entire data flow:

### 1. Tab Switch Events
**File:** `model_canvas_loader.py` → `_on_notebook_page_changed()`

**Output:**
```
[TAB_SWITCH] ==========================================
[TAB_SWITCH] Page changed to index 0
[TAB_SWITCH] ==========================================
[TAB_SWITCH] Extracted drawing_area: <GtkDrawingArea object> (id=139876543210)
[TAB_SWITCH] Calling _wire_data_collector_for_page()...
[TAB_SWITCH] Wiring result: True
```

### 2. Data Collector Wiring
**File:** `model_canvas_loader.py` → `_wire_data_collector_for_page()`

**Output:**
```
[WIRE] _wire_data_collector_for_page() called
[WIRE]   drawing_area=<GtkDrawingArea object> (id=139876543210)
[WIRE]   Found overlay_manager
[WIRE]   Found swissknife_palette
[WIRE]   simulate_tools_palette=<SimulateToolsPaletteLoader object>
[WIRE]   ✅ SUCCESS: Wiring data_collector to right panel
[WIRE]      data_collector=<SimulationDataCollector object> (id=139876789012)
```

### 3. Category Data Collector Updates
**File:** `base_dynamic_category.py` → `set_data_collector()`

**Output:**
```
[CATEGORY] TransitionsCategory.set_data_collector() called
[CATEGORY]   data_collector=<SimulationDataCollector object> (id=139876789012)
[CATEGORY]   Setting panel.data_collector (panel=TransitionRatePanel)
```

### 4. Simulation Data Collection
**File:** `analyses/data_collector.py` → `on_simulation_step()`

**Output (first 3 steps):**
```
[OLD_DC] Step 1 at time 0.0000 (collector id=139876789012)
[OLD_DC]   Collecting data for 5 places
[OLD_DC]     Place 1 (P1): 10 tokens
[OLD_DC]     Place 2 (P2): 0 tokens
...
```

**File:** `analyses/data_collector.py` → `on_transition_fired()`

**Output (first 5 firings):**
```
[OLD_DC] Transition fired: 1 (T1) at time 0.1234
[OLD_DC]   Total firings so far: 1
[OLD_DC]   Details: {'rate': 0.5}
```

### 5. Plot Data Retrieval
**File:** `transition_rate_panel.py` → `_get_rate_data()`

**Output:**
```
[PLOT] _get_rate_data() called for transition 1
[PLOT]   self.data_collector=<SimulationDataCollector object> (id=139876789012)
[PLOT]   raw_events count: 15
```

## Testing Procedure

### Test 1: Single Model - Basic Plotting

1. **Start application**: `python src/shypn.py`
2. **Open a model**: File → Open → Select test model
3. **Watch terminal** for wiring output:
   - Should see `[WIRE] ✅ SUCCESS`
   - Note the data_collector ID
4. **Open Dynamic Analyses Panel** (right panel)
5. **Click on TRANSITIONS category**
6. **Select a transition** for plotting
7. **Run simulation** (Swiss Palette → Simulate → Run)
8. **Watch terminal** for:
   - `[OLD_DC] Step 1...` (data collection happening)
   - `[OLD_DC] Transition fired...` (transitions firing)
   - `[PLOT] _get_rate_data()...` (plot requesting data)
   - **Note the data_collector ID in [PLOT] output**
9. **Compare IDs**: 
   - [WIRE] data_collector ID
   - [PLOT] data_collector ID
   - **They should MATCH!**

**Expected Result:** Plot appears with transition data

**If plot doesn't appear:**
- Check if [PLOT] data_collector ID matches [WIRE] ID
- Check if [PLOT] shows `raw_events count: 0` (no data collected)
- Check if [OLD_DC] steps are happening (data being collected)

### Test 2: Multiple Models - Tab Switching

1. **Open Model 1**: File → Open → Select first model
   - Watch for `[WIRE] ✅ SUCCESS` with collector ID #1
2. **Run simulation** on Model 1
   - Watch for `[OLD_DC]` output with collector ID #1
3. **Open Model 2**: File → Open → Select second model
   - New tab created
   - Watch for `[WIRE] ✅ SUCCESS` with collector ID #2 (different!)
4. **Switch back to Model 1 tab**
   - Should see `[TAB_SWITCH]` output
   - Should see `[WIRE]` re-wiring to collector ID #1
   - Should see `[CATEGORY]` updates with collector ID #1
5. **Switch to Model 2 tab**
   - Should see `[TAB_SWITCH]` output
   - Should see `[WIRE]` re-wiring to collector ID #2
   - Should see `[CATEGORY]` updates with collector ID #2
6. **Select transition in Model 2**
7. **Run simulation on Model 2**
8. **Check plot data retrieval**:
   - `[PLOT]` should show collector ID #2
   - Should match the `[WIRE]` collector ID #2

**Expected Result:** Each tab has its own data collector, plots show correct data

**If wrong data appears:**
- Check if [TAB_SWITCH] is triggering on tab clicks
- Check if [WIRE] is re-wiring on each switch
- Check if [PLOT] collector ID matches current tab's [WIRE] collector ID

### Test 3: Reset and Re-run

1. **Open model and run simulation**
2. **Select transition for plotting**
3. **Verify plot appears**
4. **Click Reset button**
   - Should see plot clear (tested separately)
5. **Run simulation again**
6. **Verify plot updates** with new data

## Diagnosis Guide

### Issue: No data in plots

**Symptoms:**
- Transitions selected
- Simulation runs
- No lines appear on plot

**Check:**
1. `[WIRE]` output shows ✅ SUCCESS
2. `[OLD_DC]` output shows steps and firings
3. `[PLOT]` output shows `raw_events count: > 0`
4. All IDs match

**Possible causes if IDs don't match:**
- Tab switch not triggering re-wiring
- Category not receiving updated data collector
- Plot panel keeping stale reference

### Issue: Wrong data in plots

**Symptoms:**
- Plot shows data from different model
- Plot doesn't update when switching tabs

**Check:**
1. `[TAB_SWITCH]` triggers on tab click
2. `[WIRE]` shows different collector IDs for different tabs
3. `[CATEGORY]` receives new collector on tab switch
4. `[PLOT]` uses updated collector ID

**Possible causes:**
- Tab switch handler not calling wire method
- Right panel not propagating collector to categories
- Plot panels caching old collector reference

### Issue: Collector ID mismatch

**Symptoms:**
- `[WIRE]` shows collector ID=123456
- `[PLOT]` shows collector ID=789012 (different!)

**This means:** Plot panel has stale data collector reference

**Solution needed:**
- Add cache clearing when data collector changes
- Force plot panels to update their reference
- See fix in `plot_panel.py` (clear `_plot_lines` cache)

## Next Steps After Testing

Once you run the tests and collect the terminal output:

1. **If wiring works correctly:**
   - Remove debug statements
   - System is working as designed

2. **If IDs don't match:**
   - Need to add cache clearing to plot panels
   - Need to force full redraw when collector changes

3. **If no data collected:**
   - Check if OLD collector registered as step listener
   - Check lifecycle_manager._link_palette_to_controller()

4. **If wiring fails:**
   - Check overlay_manager structure
   - Check swissknife_palette.widget_palette_instances
   - Check simulate_tools creation timing

## Files Modified

All changes are non-invasive debug output:

1. `model_canvas_loader.py` - Tab switch and wiring debug
2. `base_dynamic_category.py` - Category update debug
3. `analyses/data_collector.py` - Data collection debug
4. `transition_rate_panel.py` - Data retrieval debug

No functional changes - only print statements to trace execution.
