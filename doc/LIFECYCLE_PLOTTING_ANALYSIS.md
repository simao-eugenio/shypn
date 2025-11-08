# Lifecycle, Simulation Controllers, and Plotting Analysis

## Problem Statement

**Issue**: Transitions and places selected for plotting, but no plotting occurs after recent modifications.

**Context**: 
- Two data collector systems now coexist (OLD for plots, NEW for Report Panel tables)
- Multiple lifecycle modifications related to canvas context management
- Cached data needs to be cleared when switching between canvas models

## Architecture Overview

### 1. Dual Data Collector System

```
┌─────────────────────────────────────────────────────────────┐
│                    SimulationController                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ controller.data_collector = DataCollector (NEW)        │ │
│  │   Purpose: Post-simulation tables in Report Panel      │ │
│  │   Location: shypn.engine.simulation.data_collector     │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ controller.step_listeners = [...]                      │ │
│  │   - simulate_tools.data_collector (OLD)                │ │
│  │   - simulate_tools._on_simulation_step                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           SimulateToolsPaletteLoader                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ simulate_tools.data_collector = SimulationDataCollector│ │
│  │   Purpose: Real-time plots in Dynamic Analyses Panel   │ │
│  │   Location: shypn.analyses.data_collector              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2. Plotting Data Flow

```
Simulation Step (controller.step())
         ↓
controller.step_listeners (includes OLD data_collector)
         ↓
OLD.on_simulation_step(controller, time)
         ↓
Collects: place_data[place_id] = [(time, tokens), ...]
         ↓
Periodic Update (GLib.timeout_add)
         ↓
plot_panel.update_plot()
         ↓
plot_panel._get_rate_data(obj_id)
         ↓
self.data_collector.get_transition_data(transition_id)
         ↓
Returns: raw_events from OLD.transition_data[transition_id]
```

## Lifecycle Analysis

### Scenario 1: Open First Model

**Flow:**
1. User: File → Open → Select model
2. `model_canvas_loader.load_document_async()`
3. Creates canvas context via `lifecycle_manager.initialize_canvas()`
4. Creates `SimulationController` with NEW `DataCollector`
5. Creates SwissKnifePalette with `SimulateToolsPaletteLoader`
6. `SimulateToolsPaletteLoader.__init__()` creates OLD `SimulationDataCollector`
7. `lifecycle_manager._link_palette_to_controller()`:
   - Links `simulate_tools.simulation = controller`
   - Registers OLD data_collector as step listener
   - **CRITICAL**: Does NOT overwrite `controller.data_collector`
8. `model_canvas_loader.wire_existing_canvases_to_right_panel()`:
   - Gets OLD data_collector from simulate_tools
   - Calls `right_panel_loader.set_data_collector(OLD)`
   - Right panel updates `dynamic_analyses_panel.set_data_collector(OLD)`
   - Dynamic analyses panel propagates to all categories
   - **Categories wire OLD collector to their plot panels**

**Expected State:**
- ✅ Controller has NEW data collector (for Report Panel)
- ✅ OLD data collector registered as step listener (receives simulation steps)
- ✅ Right panel has OLD data collector reference
- ✅ Plot panels can fetch data from OLD collector

### Scenario 2: Open Second Model (Switch Canvas)

**Flow:**
1. User: File → Open → Select second model (while first is open)
2. Creates NEW canvas context (separate drawing_area)
3. Creates NEW `SimulationController` with NEW `DataCollector`
4. Creates NEW SwissKnifePalette with NEW `SimulateToolsPaletteLoader`
5. NEW `SimulateToolsPaletteLoader` creates NEW OLD `SimulationDataCollector`
6. Wiring happens for new canvas
7. **PROBLEM**: Right panel is SHARED across canvases!

**Issue:**
```python
# model_canvas_loader.py has ONE right_panel_loader instance
self.right_panel_loader = RightPanelLoader(...)

# When tab switches, wire_existing_canvases_to_right_panel() is called
# But does it properly update the right panel's data collector?
```

### Scenario 3: Switch Between Canvas Tabs

**Flow:**
1. User clicks on Tab 2 (different model)
2. `_on_notebook_page_changed()` triggered
3. Calls `wire_existing_canvases_to_right_panel()`
4. **CRITICAL**: Must get data collector from Tab 2's simulate_tools
5. Must update right_panel with Tab 2's data collector

**Potential Issue:**
- Right panel may still be referencing Tab 1's data collector
- Plot panels may be plotting Tab 1's data when Tab 2 is active

## Data Collector Lifecycle

### OLD SimulationDataCollector (for plots)

**Creation:**
```python
# In SimulateToolsPaletteLoader.__init__()
from shypn.analyses import SimulationDataCollector
self.data_collector = SimulationDataCollector()
```

**Registration:**
```python
# In lifecycle_manager._link_palette_to_controller()
controller.add_step_listener(simulate_tools.data_collector.on_simulation_step)
```

**Data Collection:**
```python
# During simulation, OLD collector receives:
def on_simulation_step(self, controller, time):
    # Collects place tokens
    for place in controller.model.places:
        self.place_data[place.id].append((time, place.tokens))

def on_transition_fired(self, transition, time, details):
    # Collects transition firing events
    self.transition_data[transition.id].append((time, 'fired', details))
```

**Clearing:**
```python
# In simulate_tools_palette_loader._on_reset_clicked()
if self.data_collector:
    self.data_collector.clear()

# In dynamic_analyses_panel.reset()
for category in self.categories:
    if hasattr(category, 'clear_plot'):
        category.clear_plot()
```

## Critical Wiring Points

### 1. Right Panel Data Collector Wiring

**Location:** `model_canvas_loader.wire_existing_canvases_to_right_panel()`

**Current Implementation:**
```python
def wire_existing_canvases_to_right_panel(self, page):
    drawing_area = None
    if isinstance(page, Gtk.Overlay):
        scrolled = page.get_child()
        if isinstance(scrolled, Gtk.ScrolledWindow):
            drawing_area = scrolled.get_child()
    
    if self.right_panel_loader and drawing_area:
        if drawing_area in self.overlay_managers:
            overlay_manager = self.overlay_managers[drawing_area]
            if hasattr(overlay_manager, 'swissknife_palette'):
                swissknife = overlay_manager.swissknife_palette
                if hasattr(swissknife, 'widget_palette_instances'):
                    simulate_tools_palette = swissknife.widget_palette_instances.get('simulate')
                    if simulate_tools_palette and hasattr(simulate_tools_palette, 'data_collector'):
                        data_collector = simulate_tools_palette.data_collector
                        print(f"[WIRE] Wiring data_collector to right panel: {data_collector}")
                        self.right_panel_loader.set_data_collector(data_collector)
                        return True
```

**Analysis:**
- ✅ Uses correct accessor: `widget_palette_instances.get('simulate')`
- ✅ Gets OLD data_collector from simulate_tools
- ✅ Calls `right_panel_loader.set_data_collector()`
- ❓ Is this called on EVERY tab switch?

### 2. Right Panel Propagation

**Location:** `right_panel_loader.set_data_collector()`

```python
def set_data_collector(self, data_collector):
    self.data_collector = data_collector
    
    # Update dynamic analyses panel
    if self.dynamic_analyses_panel:
        self.dynamic_analyses_panel.set_data_collector(data_collector)
```

**Location:** `dynamic_analyses_panel.set_data_collector()`

```python
def set_data_collector(self, data_collector):
    self.data_collector = data_collector
    
    # Update all categories
    for category in self.categories:
        category.set_data_collector(data_collector)
```

**Location:** `transitions_category.set_data_collector()` (via BaseDynamicCategory)

```python
# In BaseDynamicCategory
def set_data_collector(self, data_collector):
    self.data_collector = data_collector
    if self.panel:
        self.panel.data_collector = data_collector
```

**Analysis:**
- ✅ Propagation chain is complete
- ✅ Each plot panel gets updated data_collector reference
- ❓ Are plot panels actually using this reference?

### 3. Plot Panel Data Access

**Location:** `transition_rate_panel._get_rate_data()`

```python
def _get_rate_data(self, transition_id):
    # Safety check: return empty if no data collector
    if not self.data_collector:
        return []
    
    # Get raw firing event data from collector
    raw_events = self.data_collector.get_transition_data(transition_id)
    
    if not raw_events:
        return []
    # ... process data ...
```

**Analysis:**
- ✅ Uses `self.data_collector` to fetch data
- ✅ Returns empty list if no collector
- ❓ Is `self.data_collector` actually set correctly?

## Diagnostic Strategy

### Test 1: Verify Data Collector Wiring

**Add debug to `transitions_category.set_data_collector()`:**

```python
def set_data_collector(self, data_collector):
    print(f"[CATEGORY] TransitionsCategory.set_data_collector() called")
    print(f"[CATEGORY]   data_collector={data_collector}")
    self.data_collector = data_collector
    if self.panel:
        print(f"[CATEGORY]   Setting panel.data_collector={data_collector}")
        self.panel.data_collector = data_collector
    else:
        print(f"[CATEGORY]   WARNING: No panel to update!")
```

### Test 2: Verify Data Collection

**Add debug to OLD SimulationDataCollector:**

```python
def on_simulation_step(self, controller, time):
    self.step_count += 1
    print(f"[OLD_DC] Step {self.step_count} at time {time}")
    for place in controller.model.places:
        data = self.place_data[place.id]
        data.append((time, place.tokens))
        print(f"[OLD_DC]   Place {place.id}: {place.tokens} tokens")
```

### Test 3: Verify Data Retrieval

**Add debug to `transition_rate_panel._get_rate_data()`:**

```python
def _get_rate_data(self, transition_id):
    print(f"[PLOT] _get_rate_data() called for transition {transition_id}")
    print(f"[PLOT]   self.data_collector={self.data_collector}")
    
    if not self.data_collector:
        print(f"[PLOT]   ERROR: No data collector!")
        return []
    
    raw_events = self.data_collector.get_transition_data(transition_id)
    print(f"[PLOT]   raw_events count: {len(raw_events) if raw_events else 0}")
    
    if not raw_events:
        print(f"[PLOT]   WARNING: No raw events for transition {transition_id}")
        return []
    # ...
```

### Test 4: Verify Tab Switch Wiring

**Add debug to `_on_notebook_page_changed()`:**

```python
def _on_notebook_page_changed(self, notebook, page, page_num):
    print(f"[TAB_SWITCH] Page changed to {page_num}")
    
    # Get drawing_area for this page
    drawing_area = self._extract_drawing_area(page)
    print(f"[TAB_SWITCH]   drawing_area={drawing_area}")
    
    # Wire right panel to this canvas's data collector
    wired = self.wire_existing_canvases_to_right_panel(page)
    print(f"[TAB_SWITCH]   Wiring result: {wired}")
```

## Root Cause Hypotheses

### Hypothesis 1: Right Panel Not Re-wiring on Tab Switch
**Likelihood: HIGH**

**Evidence:**
- `wire_existing_canvases_to_right_panel()` exists
- Method has correct accessor path (fixed recently)
- But is it being called on EVERY tab switch?

**Test:**
- Add debug to `_on_notebook_page_changed()`
- Verify wire method is called
- Verify it returns True (successful wiring)

### Hypothesis 2: Plot Panels Cached Old Data Collector
**Likelihood: MEDIUM**

**Evidence:**
- Plot panels created once
- Data collector set once at creation
- Tab switch updates reference, but does plot panel get it?

**Test:**
- Add debug to `transitions_category.set_data_collector()`
- Verify it's called on tab switch
- Verify panel reference is updated

### Hypothesis 3: OLD Data Collector Not Receiving Steps
**Likelihood: LOW**

**Evidence:**
- Lifecycle manager correctly registers as step listener
- No overwrites happening (fixed in Phase 1-2)

**Test:**
- Add debug to `OLD.on_simulation_step()`
- Verify it's called during simulation
- Verify data is collected

### Hypothesis 4: Cached Data Not Cleared Between Models
**Likelihood: HIGH**

**Evidence:**
- When opening new model, OLD data collector is NEW instance
- But right panel might still reference OLD instance from previous canvas
- Plot panels might be plotting data from WRONG canvas

**Test:**
- Open Model 1 → Run simulation → Select transition → Verify data
- Open Model 2 (new tab) → Run simulation → Select transition
- Check if right panel data_collector ID changed
- Check if plot panel is using Model 2's data or Model 1's data

## Recommended Fix Strategy

### Step 1: Add Comprehensive Debug Output

Add debug statements to trace the entire flow:
1. OLD data collector creation and ID
2. Wiring to right panel (with collector ID)
3. Tab switch events (with collector ID update)
4. Data collection (with collector ID)
5. Data retrieval (with collector ID)

### Step 2: Verify Tab Switch Triggers Re-wiring

Ensure `wire_existing_canvases_to_right_panel()` is called on EVERY tab switch.

Check: `_on_notebook_page_changed()` implementation.

### Step 3: Clear Plot Panel Cache on Context Switch

When data collector changes, plot panels need to:
1. Clear their `_plot_lines` cache
2. Clear their `last_data_length` tracking
3. Force full redraw with new data

Add to `plot_panel.py`:
```python
def set_data_collector(self, data_collector):
    """Update data collector and clear cached state."""
    self.data_collector = data_collector
    self._plot_lines.clear()
    self.last_data_length.clear()
    if self.selected_objects:
        self.needs_update = True
```

### Step 4: Verify Context Isolation

Each canvas context should have:
- Its own SimulationController
- Its own SimulateToolsPaletteLoader
- Its own OLD SimulationDataCollector
- No shared state between contexts

The ONLY shared component is the right panel, which MUST update its data_collector reference when tabs switch.

## Summary

**Root Cause:** Right panel's data collector reference is not being updated when switching between canvas tabs, causing plot panels to fetch data from the wrong context.

**Solution:** Ensure `wire_existing_canvases_to_right_panel()` is called reliably on every tab switch and that plot panels clear their cached state when data collector changes.

**Next Steps:**
1. Add debug output to confirm hypothesis
2. Verify tab switch wiring is working
3. Add cache clearing when data collector changes
4. Test with multiple open models
