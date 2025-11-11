# Viability Panel Data Flow Analysis

## Problem Statement
The Viability Panel is not returning any data after creation despite observer and rule systems being in place.

## Architecture Overview

### Components
1. **ViabilityPanel** - Main panel container (in viability_panel.py)
2. **ViabilityObserver** - Event monitoring and rule evaluation system
3. **ViabilityCategories** - 4 categories (Structural, Biological, Kinetic, Diagnosis)
4. **ViabilityPanelLoader** - Per-document loader (creates one panel per model)

### Data Flow Path
```
1. Model Canvas Loader creates per-document ViabilityPanelLoader
   ↓
2. ViabilityPanelLoader.__init__() creates ViabilityPanel
   ↓
3. ViabilityPanel.__init__() creates observer and subscribes categories
   ↓
4. model_canvas_loader calls panel.set_model_canvas(self)
   ↓
5. set_model_canvas() calls _feed_observer_with_kb_data()
   ↓
6. _feed_observer_with_kb_data() calls observer.record_event('kb_updated', kb_data)
   ↓
7. observer.record_event() calls _evaluate_rules()
   ↓
8. _evaluate_rules() checks all rules and calls _notify_subscribers()
   ↓
9. _notify_subscribers() calls category._on_observer_update(issues)
   ↓
10. _on_observer_update() updates UI via GLib.idle_add(_display_issues)
```

## Critical Wiring Points

### 1. Panel Creation (model_canvas_loader.py:1410-1461)
```python
viability_panel_loader = ViabilityPanelLoader(model=None)
viability_panel_loader.set_model_canvas_loader(self)
viability_panel = viability_panel_loader.panel
viability_panel.set_drawing_area(drawing_area)  # ADDED
viability_panel.set_model_canvas(self)  # TRIGGERS KB FEED
```

### 2. Observer Subscription (viability_panel.py:154-157)
```python
self.observer.subscribe('structural', self.structural_category._on_observer_update)
self.observer.subscribe('biological', self.biological_category._on_observer_update)
self.observer.subscribe('kinetic', self.kinetic_category._on_observer_update)
self.observer.subscribe('diagnosis', self.diagnosis_category._on_observer_update)
```

### 3. Simulation Callback (model_canvas_loader.py:1442-1450)
```python
def combined_callback():
    if existing_callback and callable(existing_callback):
        existing_callback()
    viability_panel.on_simulation_complete()

simulation_controller.on_simulation_complete = combined_callback
```

### 4. Reset Wiring (model_canvas_loader.py:1077-1090)
Re-wires the callback after controller reset

## Debugging Added

### Print Statements Added To:
1. **viability_panel.py**:
   - `set_model_canvas()` - Entry point
   - `_feed_observer_with_kb_data()` - KB data extraction
   - `on_simulation_complete()` - Simulation data extraction

2. **viability_observer.py**:
   - `record_event()` - Event capture
   - `_evaluate_rules()` - Rule evaluation
   - `_notify_subscribers()` - Subscriber notification
   - `subscribe()` - Subscription registration

3. **base_category.py**:
   - `_on_observer_update()` - Category callback

## Test Procedure

### Phase 1: Startup Initialization
**Expected Output:**
```
[OBSERVER] ✅ Subscribed to category 'structural', total subscribers: 1
[OBSERVER] ✅ Subscribed to category 'biological', total subscribers: 1
[OBSERVER] ✅ Subscribed to category 'kinetic', total subscribers: 1
[OBSERVER] ✅ Subscribed to category 'diagnosis', total subscribers: 1
```

### Phase 2: Model Canvas Wiring
**Expected Output:**
```
[VIABILITY_PANEL] ========== set_model_canvas() CALLED ==========
[VIABILITY_PANEL] model_canvas: <ModelCanvasLoader>
[VIABILITY_OBSERVER] ========== _feed_observer_with_kb_data() CALLED ==========
[VIABILITY_OBSERVER] KB has:
  places: X
  transitions: Y
  arcs: Z
```

### Phase 3: Observer Event Processing
**Expected Output:**
```
[OBSERVER] ========== record_event() CALLED ==========
[OBSERVER] event_type: kb_updated
[OBSERVER] ========== _evaluate_rules() START ==========
[OBSERVER] Total rules: 9
[OBSERVER] Rule 'missing_firing_rates' (category=kinetic): condition=True
[OBSERVER]   → Generated N issues
[OBSERVER] Notifying subscribers for category 'kinetic'...
```

### Phase 4: Category Update
**Expected Output:**
```
[VIABILITY_CATEGORY] ========== _on_observer_update() CALLED ==========
[VIABILITY_CATEGORY] Category: KineticCategory
[VIABILITY_CATEGORY] Received N issues
[VIABILITY_CATEGORY] Scheduling UI update via GLib.idle_add...
```

### Phase 5: Simulation Complete
**Expected Output:**
```
[VIABILITY] ========== on_simulation_complete() CALLED ==========
[VIABILITY] controller: <SimulationController>
[VIABILITY] data_collector: <DataCollector>
[VIABILITY] has_data: True
[OBSERVER] ========== record_event() CALLED ==========
[OBSERVER] event_type: simulation_complete
```

## Potential Issues

### Issue 1: Observer Not Receiving Events
**Symptom:** No `[OBSERVER] record_event()` messages
**Possible Causes:**
- `_feed_observer_with_kb_data()` not being called
- Exception in KB retrieval
- model_canvas not set correctly

### Issue 2: Rules Not Triggering
**Symptom:** `condition=False` for all rules
**Possible Causes:**
- KB data structure mismatch
- Rule conditions too strict
- Knowledge dict not populated correctly

### Issue 3: Subscribers Not Registered
**Symptom:** No subscription messages at startup
**Possible Causes:**
- ViabilityPanel.__init__() not completing
- Observer not created
- Categories not created

### Issue 4: Categories Not Updating
**Symptom:** Observer notifies but categories don't update
**Possible Causes:**
- Category not expanded (UI update skipped)
- GLib.idle_add() not working
- _display_issues() failing

## Next Steps

1. **Run the app** and check for debug output
2. **Load a model** and watch for viability messages
3. **Run simulation** and check for simulation_complete handling
4. **Identify the break point** in the data flow
5. **Fix the specific issue** based on where data flow stops

## Files Modified (with debug output)
- `src/shypn/ui/panels/viability/viability_panel.py`
- `src/shypn/ui/panels/viability/viability_observer.py`
- `src/shypn/ui/panels/viability/base_category.py`

## To Test
```bash
cd /home/simao/projetos/shypn
python3 -u src/shypn.py 2>&1 | grep -E "(VIABILITY|OBSERVER)"
```

Then:
1. Load a model with transitions
2. Expand Diagnosis category
3. Run simulation
4. Watch for debug output at each phase
