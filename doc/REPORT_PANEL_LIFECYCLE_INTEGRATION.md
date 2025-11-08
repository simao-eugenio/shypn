# Report Panel - Global Lifecycle Integration

**Date:** November 8, 2025  
**Author:** Analysis by GitHub Copilot  
**Feature:** Report Panel Dynamic Analyses - Simulation Results Tables  
**Context:** Multi-document application with canvas lifecycle management

---

## Executive Summary

The Report Panel must integrate with SHYPN's **Global Lifecycle System** which manages:
1. **Multiple canvas tabs** (multi-document interface)
2. **Per-canvas simulation controllers** (isolated state)
3. **Model loading/switching** (File→Open, File→New, Import, Tab switching)
4. **Controller lifecycle** (creation, reset, recreation, cleanup)

**Critical Insight:** The SimulationController is **PER-CANVAS**, not global. Each canvas tab has its own controller instance, and the Report Panel must track the **currently active controller** as tabs switch.

---

## Global Lifecycle Architecture

### Core Components

```
Application
│
├─> ModelCanvasLoader (multi-document manager)
│   ├─> GtkNotebook (tab container)
│   ├─> canvas_managers{} (ModelCanvasManager per tab)
│   ├─> simulation_controllers{} (SimulationController per tab)
│   └─> overlay_managers{} (CanvasOverlayManager per tab)
│
├─> CanvasLifecycleManager (coordinates lifecycle)
│   ├─> canvas_registry{} (CanvasContext per canvas)
│   ├─> id_manager (per-canvas ID scoping)
│   └─> lifecycle hooks (create, reset, switch, destroy)
│
└─> ReportPanelLoader (SINGLE INSTANCE - shared across all tabs)
    └─> ReportPanel
        ├─> ModelsCategory
        ├─> DynamicAnalysesCategory ← needs controller reference
        ├─> TopologyAnalysesCategory
        └─> ProvenanceCategory
```

### Key Data Structures

```python
# In ModelCanvasLoader
self.canvas_managers = {}           # drawing_area → ModelCanvasManager
self.simulation_controllers = {}     # drawing_area → SimulationController
self.overlay_managers = {}           # drawing_area → CanvasOverlayManager

# In CanvasLifecycleManager
self.canvas_registry = {}            # canvas_id → CanvasContext
```

---

## Lifecycle Events & Report Panel Integration

### Event 1: Application Startup

**Sequence:**
```
shypn.py: on_activate()
  ├─> model_canvas_loader.load()
  │   └─> create_default_canvas()
  │       ├─> Creates GtkDrawingArea (tab)
  │       ├─> Creates ModelCanvasManager(drawing_area)
  │       ├─> Creates SimulationController(manager)
  │       └─> Stores in dictionaries
  │
  ├─> report_panel_loader.load()
  │   └─> Creates ReportPanel (SINGLE INSTANCE)
  │
  └─> WIRE STARTUP CONTROLLER TO REPORT
      ├─> drawing_area = model_canvas_loader.get_current_document()
      ├─> controller = model_canvas_loader.get_canvas_controller(drawing_area)
      └─> report_panel_loader.panel.set_controller(controller)
```

**Report Panel Action:**
- Receives **initial controller** reference
- Registers `on_simulation_complete` callback
- Ready to receive simulation results from this controller

**Code Location:** `shypn.py` lines 620-658

---

### Event 2: Tab Switching (User clicks different tab)

**Sequence:**
```
User clicks Tab 2
  ↓
GtkNotebook 'switch-page' signal
  ↓
on_canvas_tab_switched_report()
  ├─> drawing_area = get_current_document()  ← NEW active tab
  ├─> report_panel.on_tab_switched(drawing_area)
  │   └─> Updates model_canvas reference
  │
  └─> controller = get_canvas_controller(drawing_area)  ← Tab 2's controller
      └─> report_panel.set_controller(controller)       ← REWIRE!
          └─> parameters_category.set_controller(controller)
              └─> controller.on_simulation_complete = _refresh_simulation_data
```

**Report Panel Action:**
- **Receives NEW controller** for the switched-to tab
- Unregisters old callback (implicitly by overwriting)
- Registers new callback on new controller
- Refreshes categories to show new tab's data

**Critical:** Each tab has its own simulation state and results. Report must track the active tab's controller.

**Code Location:** `shypn.py` lines 671-682

---

### Event 3: File → Open (Load .shy file)

**Sequence:**
```
User: File → Open → selects model.shy
  ↓
file_explorer.on_file_open_requested(filepath)
  ├─> model_canvas_loader.load_file(filepath)
  │   ├─> Creates NEW tab (drawing_area)
  │   ├─> Creates ModelCanvasManager with loaded data
  │   ├─> Creates SimulationController(manager)
  │   └─> controller.reset_for_new_model(manager)
  │       └─> Recreates DataCollector with new model
  │
  ├─> lifecycle_manager.sync_after_file_load()
  │   └─> Registers existing IDs, creates TransitionStates
  │
  └─> on_file_open_with_report_notify(filepath)
      └─> report_panel.on_file_opened(filepath)
          ├─> Gets current controller (delayed 100ms)
          ├─> Updates categories with new model
          └─> Auto-refreshes to show loaded data
```

**Report Panel Action:**
- Waits for model to fully load (100ms delay)
- Gets the newly created controller
- Refreshes all categories with loaded model data
- Ready for simulation on this model

**Code Location:** `shypn.py` lines 687-696, `model_canvas_loader.py` lines 935-1015

---

### Event 4: File → New (Create blank canvas)

**Sequence:**
```
User: File → New
  ↓
menu_actions.on_file_new()
  ├─> model_canvas_loader.create_new_canvas()
  │   ├─> Creates NEW tab (drawing_area)
  │   ├─> Creates empty ModelCanvasManager
  │   ├─> Creates SimulationController(manager)
  │   └─> Sets as current tab
  │
  └─> on_file_new_with_report_notify()
      ├─> report_panel.on_file_new()
      │   └─> Refreshes categories
      │
      └─> WIRE NEW CONTROLLER
          ├─> drawing_area = get_current_document()
          ├─> controller = get_canvas_controller(drawing_area)
          └─> report_panel.set_controller(controller)
```

**Report Panel Action:**
- Receives controller for new blank canvas
- Shows empty state in categories
- Ready for user to build model and simulate

**Code Location:** `shypn.py` lines 699-718

---

### Event 5: Import Pathway (KEGG/SBML/BioPAX)

**Sequence:**
```
User: Pathway Ops → Import KEGG
  ↓
pathway_importer.import_kegg()
  ├─> Parses KEGG XML
  ├─> Creates places/transitions in current manager
  │
  ├─> controller.reset_for_new_model(manager)  ← CRITICAL!
  │   ├─> Recreates model_adapter
  │   ├─> Recreates DataCollector(new_model)  ← NEW collector!
  │   ├─> Clears transition_states
  │   └─> Creates TransitionState for each imported transition
  │
  └─> _ensure_simulation_reset(drawing_area)
      ├─> Updates palette controller reference
      ├─> Re-registers step listeners
      └─> WIRES CONTROLLER TO REPORT PANEL
          └─> report_panel.set_controller(controller)
```

**Report Panel Action:**
- **Receives RESET controller** with new DataCollector
- Old simulation data is gone (DataCollector recreated)
- Categories refresh to show imported pathway
- Ready for new simulation on imported model

**Critical:** `reset_for_new_model()` **RECREATES** the DataCollector. Any simulation data from before the import is **LOST**.

**Code Location:** `model_canvas_loader.py` lines 942-1014

---

### Event 6: Canvas Reset (File → Reset Canvas)

**Sequence:**
```
User: File → Reset Canvas
  ↓
lifecycle_manager.reset_canvas(drawing_area)
  ├─> Stops running simulation
  ├─> Clears model (places, transitions, arcs)
  ├─> controller.reset()
  │   ├─> Stops simulation
  │   ├─> data_collector.clear()  ← Clears time-series data
  │   ├─> Resets transition.firing_count = 0
  │   └─> Resets places to initial_marking
  │
  ├─> Resets palette state
  └─> Resets ID scope
```

**Report Panel Action:**
- Controller reference **stays the same**
- DataCollector is **cleared** (not recreated)
- Tables become empty (no simulation data)
- Ready for new simulation on reset canvas

**Difference from Event 5:** 
- Reset: Clears DataCollector (same instance)
- Import: Recreates DataCollector (new instance)

**Code Location:** `lifecycle_manager.py` lines 182-231

---

### Event 7: Simulation Run → Stop

**Sequence:**
```
User: Clicks "Run" button
  ↓
simulate_tools_palette.on_run_button_clicked()
  ↓
controller.run(time_step, max_steps)
  ├─> data_collector.start_collection()
  │   └─> Initializes place_data{}, transition_data{}
  │
  ├─> Loop: controller._run_step_and_continue()
  │   └─> For each step:
  │       ├─> Fire enabled transitions
  │       ├─> Advance time
  │       └─> data_collector.record_state(time)  ← Collects data
  │
  └─> User clicks "Stop" OR duration reached
      └─> controller.stop()
          ├─> data_collector.stop_collection()
          │
          └─> if self.on_simulation_complete:     ← CALLBACK!
              └─> self.on_simulation_complete()
                  └─> parameters_category._refresh_simulation_data()
                      ├─> analyzer = SpeciesAnalyzer(data_collector)
                      ├─> species_metrics = analyzer.analyze_all_species(duration)
                      ├─> species_table.populate(species_metrics)
                      ├─> analyzer = ReactionAnalyzer(data_collector)
                      ├─> reaction_metrics = analyzer.analyze_all_reactions(duration)
                      └─> reaction_table.populate(reaction_metrics)
```

**Report Panel Action:**
1. Callback is triggered when simulation stops
2. Gets data_collector from controller
3. Creates analyzers to compute metrics
4. Populates tables with results
5. User sees simulation results in Report Panel

**Code Location:** 
- Controller: `controller.py` lines 1547-1654
- Report: `parameters_category.py` lines 284-347

---

## Critical Integration Points

### Point 1: Controller Wiring (set_controller)

**Where it happens:**
1. **Startup:** `shypn.py` line 631
2. **Tab switch:** `shypn.py` line 682
3. **File new:** `shypn.py` line 716
4. **Import/Reset:** `model_canvas_loader.py` line 1009

**What it does:**
```python
report_panel.set_controller(controller)
  └─> parameters_category.set_controller(controller)
      └─> self.controller = controller
      └─> controller.on_simulation_complete = self._refresh_simulation_data
```

**Effect:**
- Report Panel registers its callback on the controller
- When simulation stops, callback fires → tables populate

---

### Point 2: DataCollector Lifecycle

**Three states:**

1. **Created:** During `SimulationController.__init__(model)`
   ```python
   self.data_collector = DataCollector(model)
   ```

2. **Cleared:** During `controller.reset()`
   ```python
   self.data_collector.clear()  # Empties lists
   ```

3. **Recreated:** During `controller.reset_for_new_model(new_model)`
   ```python
   self.data_collector = DataCollector(new_model)  # NEW instance!
   ```

**Impact on Report Panel:**
- State 1: Empty (no data yet)
- State 2: Empty (data cleared)
- State 3: Empty + old reference invalid (NEW instance)

**Problem:** If Report Panel holds old DataCollector reference, State 3 breaks it.

**Solution:** Report Panel **always** accesses via `controller.data_collector` (not storing reference).

---

### Point 3: Multi-Controller Coexistence

**Two DataCollectors per canvas:**

1. **Controller's DataCollector** (for Report Panel tables)
   - Created in: `SimulationController.__init__`
   - Purpose: Post-simulation analysis (tables)
   - Accessed by: `controller.data_collector`

2. **Palette's DataCollector** (for real-time plots)
   - Created in: `SimulateToolsPalette.__init__`
   - Purpose: Live plot updates during simulation
   - Accessed by: `simulate_tools_palette.data_collector`

**Both receive step notifications:**
```python
controller.add_step_listener(simulate_tools_palette.data_collector.on_simulation_step)
```

**Critical:** Do NOT overwrite `controller.data_collector` with palette's collector!

**Code Location:** `model_canvas_loader.py` line 999-1000

---

## Report Panel Responsibilities

### During Application Lifecycle

| Lifecycle Event | Report Panel Must |
|-----------------|-------------------|
| **Startup** | Receive initial controller, register callback |
| **Tab Switch** | Receive new tab's controller, update categories |
| **File Open** | Wait for load completion, refresh with loaded data |
| **File New** | Receive blank canvas controller, show empty state |
| **Import** | Receive reset controller with new DataCollector |
| **Canvas Reset** | Handle cleared DataCollector, show empty tables |
| **Simulation Stop** | Callback fires, populate tables from data_collector |
| **Tab Close** | No action needed (controller destroyed automatically) |

### Data Access Pattern

**✅ CORRECT:**
```python
def _refresh_simulation_data(self):
    if not self.controller:
        return
    if not self.controller.data_collector:
        return
    
    # Access through controller reference
    data_collector = self.controller.data_collector
    analyzer = SpeciesAnalyzer(data_collector)
    metrics = analyzer.analyze_all_species(duration)
```

**❌ WRONG:**
```python
def set_controller(self, controller):
    self.controller = controller
    self.data_collector = controller.data_collector  # ← DANGEROUS!
    # This reference becomes stale when controller.reset_for_new_model() is called
```

---

## Debugging Checklist

When simulation tables don't populate, check:

### 1. Controller Wiring
```python
print(f"[DEBUG] controller = {report_panel.controller}")
print(f"[DEBUG] callback registered = {report_panel.controller.on_simulation_complete is not None}")
```

### 2. DataCollector State
```python
print(f"[DEBUG] data_collector = {controller.data_collector}")
print(f"[DEBUG] has_data() = {controller.data_collector.has_data()}")
print(f"[DEBUG] time_points = {len(controller.data_collector.time_points)}")
```

### 3. Callback Invocation
```python
# In controller.stop():
if self.on_simulation_complete:
    print("[DEBUG] Calling on_simulation_complete callback")
    self.on_simulation_complete()
else:
    print("[DEBUG] ⚠️ No callback registered!")
```

### 4. Active Tab Tracking
```python
drawing_area = model_canvas_loader.get_current_document()
controller = model_canvas_loader.get_canvas_controller(drawing_area)
print(f"[DEBUG] Active tab controller = {id(controller)}")
print(f"[DEBUG] Report panel controller = {id(report_panel.controller)}")
# Should be the same!
```

### 5. Import/Reset Events
```python
# After import or reset:
print(f"[DEBUG] Controller data_collector ID = {id(controller.data_collector)}")
# Should be NEW ID after reset_for_new_model()
```

---

## Common Issues & Solutions

### Issue 1: Tables Don't Populate After Simulation

**Symptoms:** Simulation runs, stops, but Report tables stay empty.

**Possible Causes:**
1. Callback not registered (check `controller.on_simulation_complete`)
2. Wrong controller wired (check tab switching)
3. DataCollector empty (check `has_data()`)

**Solution:**
```python
# In parameters_category.py
def set_controller(self, controller):
    print(f"[SET_CONTROLLER] Setting controller: {controller}")
    print(f"[SET_CONTROLLER] Has data_collector: {hasattr(controller, 'data_collector')}")
    self.controller = controller
    if controller:
        controller.on_simulation_complete = lambda: self._refresh_simulation_data()
        print(f"[SET_CONTROLLER] Callback registered successfully")
```

---

### Issue 2: Tables Show Old Data After Import

**Symptoms:** Import pathway, tables still show previous simulation results.

**Cause:** DataCollector was recreated (new instance), but tables not refreshed.

**Solution:**
```python
# In _ensure_simulation_reset() after reset_for_new_model():
if self.report_panel_loader:
    report_panel = self.report_panel_loader.panel
    report_panel.set_controller(controller)  # Rewire to new controller
    # Clear tables explicitly
    for category in report_panel.categories:
        if isinstance(category, DynamicAnalysesCategory):
            category._refresh_simulation_data()  # Will show empty (no data)
```

---

### Issue 3: Wrong Tab's Data Displayed

**Symptoms:** Switch to Tab 2, but Report shows Tab 1's results.

**Cause:** Tab switch handler not wiring new controller.

**Solution:**
```python
# In shypn.py
def on_canvas_tab_switched_report(notebook, page, page_num):
    drawing_area = model_canvas_loader.get_current_document()
    if drawing_area and report_panel_loader.panel:
        # CRITICAL: Rewire controller for new tab
        controller = model_canvas_loader.get_canvas_controller(drawing_area)
        if controller:
            print(f"[TAB_SWITCH] Wiring controller {id(controller)} to Report Panel")
            report_panel_loader.panel.set_controller(controller)
            # Refresh to show new tab's data
            report_panel_loader.panel.refresh_all()
```

---

## Summary

### Key Takeaways

1. **SimulationController is PER-CANVAS**
   - Each tab has its own controller
   - Report Panel must track the active tab's controller

2. **DataCollector has THREE lifecycle states**
   - Created, Cleared, Recreated
   - Always access via `controller.data_collector`, never store reference

3. **Report Panel wiring happens at FIVE points**
   - Startup, Tab Switch, File New, Import/Reset
   - Each point must call `report_panel.set_controller(controller)`

4. **Callback pattern is the integration mechanism**
   - `controller.on_simulation_complete = callback`
   - Triggered in `controller.stop()`
   - Drives table population

5. **Multi-controller coexistence is intentional**
   - Controller's DataCollector: Report Panel tables
   - Palette's DataCollector: Real-time plots
   - Both exist, both receive step notifications

### Implementation Checklist

- [x] ✅ Report Panel receives controller at startup
- [x] ✅ Report Panel rewired on tab switch
- [x] ✅ Report Panel rewired on file new
- [x] ✅ Report Panel rewired after import/reset
- [x] ✅ Callback registered in set_controller()
- [x] ✅ DataCollector accessed via controller reference
- [x] ✅ Tables populate in _refresh_simulation_data()
- [x] ✅ Debug logging added for troubleshooting

---

**Conclusion:** The Report Panel is **fully integrated** with the Global Lifecycle system. All wiring points are in place. If tables aren't populating, use the debugging checklist to identify which lifecycle event is not properly wiring the controller.

