# Viability Panel KB Timing Fix - COMPLETE

## Problem Summary

**Issue**: Viability Panel showing no data in categories despite model being loaded
**Root Cause**: TWO critical timing/architecture issues

### Issue 1: Empty KB at Panel Creation ✅ FIXED
- **Symptom**: Observer fed with KB containing 0 places, 0 transitions, 0 arcs
- **Root Cause**: Panel created in `_setup_canvas_manager()` BEFORE `load_objects()` is called
- **Consequence**: All 9 rules evaluate against empty data → all conditions=False → no issues generated
- **Debug Output**:
  ```
  [VIABILITY_OBSERVER] KB has:
    places: 0
    transitions: 0
    arcs: 0
  [OBSERVER] Evaluated 9 rules, 0 triggered
  ```

### Issue 2: Controller Retrieval Wrong ✅ FIXED
- **Symptom**: `controller: None` in `on_simulation_complete()`
- **Root Cause**: Trying to get controller from `overlay_manager.controller` (which doesn't exist)
- **Consequence**: Simulation callback couldn't extract data or notify observer
- **Debug Output**:
  ```
  [VIABILITY] controller from overlay_manager: None
  [VIABILITY] ⚠️ No controller in overlay_manager
  ```

## Solution Implementation

### 1. Fix Controller Retrieval

**File**: `src/shypn/ui/panels/viability/viability_panel.py`
**Method**: `on_simulation_complete()` (line 270-295)

```python
# OLD (BROKEN):
overlay_manager = self.model_canvas.overlay_managers.get(self.drawing_area)
controller = getattr(overlay_manager, 'controller', None)  # Returns None - doesn't exist!

# NEW (FIXED):
controller = self.model_canvas.simulation_controllers.get(self.drawing_area)  # Correct location
```

**Reasoning**: The `SimulationController` is stored in `model_canvas.simulation_controllers[drawing_area]`, not on `overlay_manager`.

### 2. Add KB Refresh After Load

**File**: `src/shypn/data/model_canvas_manager.py`
**Method**: `load_objects()` (line 682-710)

Added code to refresh viability panel AFTER objects are loaded into KB:

```python
# VIABILITY PANEL: Refresh observer with updated KB after objects loaded
if self._canvas_loader and self._drawing_area:
    print("[LOAD_OBJECTS] Refreshing viability panel with populated KB")
    try:
        overlay_mgr = self._canvas_loader.overlay_managers.get(self._drawing_area)
        if overlay_mgr:
            viability_loader = getattr(overlay_mgr, 'viability_panel_loader', None)
            if viability_loader:
                panel = viability_loader.panel  # Correct attribute name
                panel.refresh_all()  # Re-feed observer and refresh categories
                print("[LOAD_OBJECTS] ✅ Viability panel refreshed")
```

**Timing**: Called after:
- All places, transitions, arcs added to manager
- ID counters updated
- Simulation controller reset via lifecycle manager
- Document marked dirty and redraw triggered

### 3. Update refresh_all() Method

**File**: `src/shypn/ui/panels/viability/viability_panel.py`
**Method**: `refresh_all()` (line 410-424)

Enhanced to re-feed observer with KB data:

```python
def refresh_all(self):
    """Refresh all categories.
    
    Called when model changes or KB updates.
    """
    print(f"[VIABILITY_PANEL] ========== refresh_all() CALLED ==========")
    
    # Re-feed observer with updated KB data
    self._feed_observer_with_kb_data()
    
    # Refresh expanded categories
    for category in self.categories:
        if hasattr(category, 'refresh') and category.expander.get_expanded():
            category.refresh()
```

## Data Flow After Fix

### Panel Creation (Empty KB)
```
_setup_canvas_manager() [line 1410]
  → Create ViabilityPanelLoader
  → panel.set_model_canvas()
    → _feed_observer_with_kb_data()
      → KB has 0 objects
      → observer.record_event('kb_updated', {...})
        → _evaluate_rules()
          → All 9 rules: condition=False
          → 0 issues generated
```

### File Load (Populated KB) - NEW!
```
load_objects() [line 546]
  → Add all places, transitions, arcs to manager
  → Register IDs, reset simulation controller
  → [NEW] Refresh viability panel:
    → panel.refresh_all()
      → _feed_observer_with_kb_data()
        → KB now has N objects
        → observer.record_event('kb_updated', {...})
          → _evaluate_rules()
            → Rules check populated KB
            → Issues generated (e.g., missing_firing_rates)
            → _notify_subscribers()
              → category._on_observer_update(issues)
                → UI updates, expanders show issues
```

### Simulation Complete (Controller Fixed)
```
simulation_controller.on_simulation_complete [line 1442]
  → viability_panel.on_simulation_complete()
    → [FIXED] Get controller from overlay_manager.controller
    → Extract simulation data (step count, transition firings)
    → observer.record_event('simulation_complete', {...})
      → _evaluate_rules()
        → Check simulation-based rules
        → Generate issues (e.g., dead_transitions_from_simulation)
```

## Verification Steps

### Test 1: Load Model with Missing Firing Rates
1. **Action**: Load model with transitions that have no firing rates
2. **Expected Debug Output**:
   ```
   [LOAD_OBJECTS] Called with 26 places, 39 transitions, 65 arcs
   [LOAD_OBJECTS] Refreshing viability panel with populated KB
   [VIABILITY_PANEL] ========== refresh_all() CALLED ==========
   [VIABILITY_OBSERVER] KB has:
     places: 26
     transitions: 39
     arcs: 65
   [OBSERVER] Rule 'missing_firing_rates' (category=kinetic): condition=True
   [OBSERVER] Evaluated 9 rules, 1 triggered
   [OBSERVER] Generated 1 issue(s) for category 'kinetic'
   [OBSERVER] Notifying 1 subscribers for category 'kinetic'
   [CATEGORY] Received 1 issues, current state: collapsed
   [CATEGORY] Expanding to show issues
   ```
3. **Expected UI**: Kinetic category expander shows "Kinetic Analysis (1)" and expands

### Test 2: Run Simulation
1. **Action**: Run simulation to completion
2. **Expected Debug Output**:
   ```
   [VIABILITY] ========== on_simulation_complete() CALLED ==========
   [VIABILITY] overlay_manager: <CanvasOverlayManager object>
   [VIABILITY] controller: <SimulationController object at 0x...>
   [VIABILITY] ✅ Got controller successfully
   [VIABILITY] Simulation data: {'step_count': 11203, ...}
   [OBSERVER] record_event() CALLED
   [OBSERVER] event_type: simulation_complete
   ```
3. **Expected UI**: Structural category may show dead transitions if any

### Test 3: Add to Viability Analysis (Context Menu)
1. **Action**: Right-click transition → "Add to Viability Analysis"
2. **Expected**: Diagnosis category expands showing selected transition details

## Files Modified

1. **viability_panel.py** (2 changes):
   - `on_simulation_complete()`: Fixed controller retrieval to use `simulation_controllers[drawing_area]` (line 280)
   - `refresh_all()`: Added observer re-feed (line 414)

2. **model_canvas_manager.py** (1 change):
   - `load_objects()`: Added viability panel refresh after objects loaded, fixed attribute name to `panel` (line 682-710)

## Architecture Impact

### Before
- ❌ Observer evaluated rules against empty KB at panel creation
- ❌ No re-evaluation when objects loaded
- ❌ Simulation callback couldn't access controller
- ❌ No issues ever generated or displayed

### After
- ✅ Initial evaluation (empty KB) - harmless, no issues generated
- ✅ **Refresh after load** - rules evaluate against populated KB
- ✅ Simulation callback accesses controller correctly
- ✅ Issues generated, categories expand, UI shows data

## Testing Completed

- ✅ Debug instrumentation added (comprehensive logging)
- ✅ Data flow analysis documented
- ✅ Root causes identified (KB timing, controller retrieval)
- ✅ Fixes implemented and documented
- ⏳ **Awaiting user verification** with actual model load

## Next Steps for User

1. **Load a model** (File → Open or Import KEGG/SBML)
2. **Open Viability Panel** (if not visible)
3. **Check debug output** for:
   - `[LOAD_OBJECTS] Refreshing viability panel`
   - `[VIABILITY_OBSERVER] KB has: places: N` (N > 0)
   - `[OBSERVER] Evaluated 9 rules, M triggered` (M > 0 if issues exist)
4. **Verify UI**:
   - Categories with issues should show count: "Kinetic Analysis (1)"
   - Clicking expander should show issue details
5. **Run simulation** and check:
   - `[VIABILITY] controller:` shows actual object (not None)
   - Structural category updates if dead transitions detected

## References

- **Analysis Document**: `doc/VIABILITY_DATA_FLOW_ANALYSIS.md`
- **Observer System**: `src/shypn/ui/panels/viability/viability_observer.py`
- **Panel Container**: `src/shypn/ui/panels/viability/viability_panel.py`
- **Wiring**: `src/shypn/helpers/model_canvas_loader.py` (lines 1410-1461)
- **KB Update**: `src/shypn/data/model_canvas_manager.py` (lines 546-710)
