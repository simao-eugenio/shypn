# Plotting Infrastructure Implementation - Progress Summary

**Date**: October 4, 2025  
**Branch**: feature/property-dialogs-and-simulation-palette  
**Status**: Phase 1 Complete - Foundation Ready

---

## Completed Work

### 1. Data Collection Infrastructure ✅

**Files Created**:
- `src/shypn/analyses/__init__.py` - Package initialization with lazy imports
- `src/shypn/analyses/data_collector.py` - SimulationDataCollector class
- `src/shypn/analyses/rate_calculator.py` - RateCalculator utility

**SimulationDataCollector Features**:
- Collects place token counts at each simulation step
- Tracks transition firing events with timestamps
- Automatic downsampling at 8000 points threshold (keeps every 2nd point)
- Memory-efficient `defaultdict` storage
- Statistics tracking (steps, firings, data points)
- Methods: `on_simulation_step()`, `on_transition_fired()`, `get_place_data()`, `get_transition_data()`

**RateCalculator Features**:
- `calculate_token_rate()` - Computes d(tokens)/dt with configurable time window
- `calculate_firing_rate()` - Computes firings/time with sliding window
- `moving_average()` - Smooths noisy rate data
- `calculate_token_rate_series()` - Generates full time series for plotting
- `calculate_firing_rate_series()` - Generates firing rate time series
- All methods are static (no instance needed)

### 2. Controller Integration ✅

**Files Modified**:
- `src/shypn/engine/simulation/controller.py`
- `src/shypn/helpers/simulate_tools_palette_loader.py`

**Controller Changes**:
- Added optional `data_collector` attribute
- Modified `_fire_transition()` to call `data_collector.on_transition_fired()`
- No changes to simulation logic - purely additive

**Palette Loader Changes**:
- Creates `SimulationDataCollector` instance on init
- Attaches to controller: `simulation.data_collector = data_collector`
- Registers as step listener: `add_step_listener(data_collector.on_simulation_step)`

**Verification**:
- All 25 existing tests still passing (Phases 1-4)
- Data collection is non-intrusive and optional

### 3. Plotting Panel Modules ✅

**Files Created** (SEPARATE MODULES - not in loaders!):
- `src/shypn/analyses/plot_panel.py` - AnalysisPlotPanel base class
- `src/shypn/analyses/place_rate_panel.py` - PlaceRatePanel
- `src/shypn/analyses/transition_rate_panel.py` - TransitionRatePanel

**AnalysisPlotPanel Base Class**:
- Extends `Gtk.Box` for GTK3 integration
- Matplotlib `FigureCanvas` setup with GTK3Agg backend
- Selected objects `ListBox` with color indicators
- Remove buttons (✕) per object
- Clear selection button
- Throttled plot updates (100ms) using `GLib.timeout`
- 10-color palette for multiple objects
- Abstract methods: `_get_rate_data()`, `_get_ylabel()`, `_get_title()`
- Empty state display when no objects selected
- Methods: `add_object()`, `remove_object()`, `update_plot()`, `on_simulation_step()`

**PlaceRatePanel**:
- Token consumption/production rate plotting (d(tokens)/dt)
- Uses `RateCalculator.calculate_token_rate_series()`
- Zero reference line (y=0) distinguishes consumption from production
- Configurable time window (default: 0.1s)
- Y-axis: "Token Rate (tokens/s)"
- Title: "Place Token Consumption/Production Rate"

**TransitionRatePanel**:
- Transition firing rate plotting (firings/s - Hz)
- Uses `RateCalculator.calculate_firing_rate_series()`
- Filters 'fired' events from raw data
- Configurable time window (default: 1.0s)
- Y-axis: "Firing Rate (firings/s)"
- Title: "Transition Firing Rate"

### 4. Right Panel Integration ✅

**File Modified**:
- `src/shypn/helpers/right_panel_loader.py`

**Changes Made** (LOADER ONLY WIRES - NO BUSINESS LOGIC!):
- Added `data_collector` parameter to `__init__()`
- Created `_setup_plotting_panels()` method:
  - Imports `PlaceRatePanel` and `TransitionRatePanel`
  - Gets canvas containers from builder: `places_canvas_container`, `transitions_canvas_container`
  - Removes placeholder labels
  - Instantiates panels: `PlaceRatePanel(data_collector)`, `TransitionRatePanel(data_collector)`
  - Adds panels to containers
- Added `set_data_collector()` method for late binding
- Updated `create_right_panel()` to accept `data_collector` parameter

**Integration Points**:
- `places_canvas_container` → PlaceRatePanel
- `transitions_canvas_container` → TransitionRatePanel

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Simulation Controller                        │
│  - step() advances simulation                                   │
│  - _fire_transition() executes discrete transitions             │
│  - Notifies step_listeners on each step                         │
└─────────────┬───────────────────────────────┬──────────────────┘
              │                               │
              │ on_simulation_step()          │ on_transition_fired()
              ↓                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              SimulationDataCollector (Module)                    │
│  - place_data: {place_id: [(time, tokens), ...]}               │
│  - transition_data: {trans_id: [(time, 'fired', None), ...]}   │
│  - Auto downsampling at 8000 points                             │
└─────────────────────────────────────────────────────────────────┘
              │
              │ get_place_data() / get_transition_data()
              ↓
┌─────────────────────────────────────────────────────────────────┐
│                RateCalculator (Utility Module)                   │
│  - calculate_token_rate_series() → [(time, rate), ...]         │
│  - calculate_firing_rate_series() → [(time, rate), ...]        │
└─────────────────────────────────────────────────────────────────┘
              │
              │ Used by
              ↓
┌─────────────────────────────────────────────────────────────────┐
│              PlaceRatePanel (Module extends Gtk.Box)            │
│  - Matplotlib canvas with token rate plot                       │
│  - Selected places list with color indicators                   │
│  - Real-time updates (100ms throttle)                           │
│                                                                  │
│            TransitionRatePanel (Module extends Gtk.Box)         │
│  - Matplotlib canvas with firing rate plot                      │
│  - Selected transitions list with color indicators              │
│  - Real-time updates (100ms throttle)                           │
└─────────────────────────────────────────────────────────────────┘
              ↑
              │ Instantiated and attached by
              │
┌─────────────────────────────────────────────────────────────────┐
│              RightPanelLoader (Wiring Only!)                     │
│  - _setup_plotting_panels() creates panels                      │
│  - Attaches to places_canvas_container                          │
│  - Attaches to transitions_canvas_container                     │
│  - NO business logic - pure wiring!                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Principles Applied

### 1. Separation of Concerns ✅
- **Data Collection**: `data_collector.py` module
- **Rate Calculation**: `rate_calculator.py` utility module
- **Plotting Logic**: `plot_panel.py`, `place_rate_panel.py`, `transition_rate_panel.py` modules
- **UI Wiring**: `right_panel_loader.py` (NO business logic!)

### 2. Modular Architecture ✅
- All plotting functionality in **separate modules** under `src/shypn/analyses/`
- Loaders are **pure wiring** - they only instantiate and connect
- Business logic stays in modules, not in loaders

### 3. Clean Interfaces ✅
- `SimulationDataCollector`: Simple data storage with `get_*_data()` methods
- `RateCalculator`: Static utility methods for rate computation
- `AnalysisPlotPanel`: Abstract base class with template pattern
- `PlaceRatePanel`/`TransitionRatePanel`: Concrete implementations

### 4. Non-Intrusive Integration ✅
- Controller changes are minimal and optional
- All 25 existing tests pass unchanged
- Data collection is transparent to simulation logic

---

## Commits

1. **63b7559**: feat: Add simulation data collector and rate calculator
2. **93519b9**: feat: Add plotting panel modules (separate from loaders)
3. **7d8d498**: feat: Wire plotting panels to right panel UI (loader only)
4. **[pending]**: docs: Add data collector integration summary

---

## Next Steps

### Task 6: Connect Active Tab Data Collector ⏳
**Goal**: Ensure right panel always shows data for the ACTIVE tab

**Approach**:
1. In `model_canvas_loader.py`, find tab switch handler
2. Get active tab's `simulate_tools_palette.data_collector`
3. Call `right_panel_loader.set_data_collector(data_collector)`
4. Test with multiple tabs

### Task 7: Create Search Handler Module
**Goal**: Search for places/transitions to add to analysis

**Files to Create**:
- `src/shypn/analyses/search_handler.py`

**Features**:
- `search_places(model, query)` - Name/ID matching
- `search_transitions(model, query)` - Name/ID matching
- Returns list of matching objects

### Task 8: Wire Search UI in Panels
**Goal**: Connect search buttons to panels

**Approach**:
- Add `wire_search_ui()` method to panels
- Panels handle all search logic internally
- Loader just passes widget references

### Task 9: Context Menu Integration
**Goal**: Add "Add to Analysis" to canvas context menus

**Files to Create**:
- `src/shypn/analyses/context_menu_handler.py`

**Approach**:
- Module handles menu item addition
- `model_canvas_loader.py` just calls the module

### Task 10: Plot Controls
**Goal**: Add matplotlib toolbar and custom controls

**Features**:
- NavigationToolbar2GTK3 for zoom/pan/save
- Grid toggle, legend toggle, auto scale
- Time window adjustment spinner
- All in panel modules!

### Task 11: Testing & Documentation
**Goal**: Comprehensive testing and docs

---

## Success Metrics

✅ Data collector collects place token counts  
✅ Data collector tracks transition firings  
✅ Rate calculator computes token rates  
✅ Rate calculator computes firing rates  
✅ Plotting panels display in right panel tabs  
✅ Panels update in real-time during simulation  
✅ All 25 existing tests still pass  
✅ Modular architecture with separate modules  
✅ Loaders contain NO business logic  

⏳ Panels show data for active tab  
⏳ Search functionality works  
⏳ Context menu "Add to Analysis" works  
⏳ Matplotlib controls functional  
⏳ Performance tested with 10+ objects  

---

## Technical Notes

### Matplotlib GTK3 Integration
```python
import matplotlib
matplotlib.use('GTK3Agg')  # Must be before pyplot import
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
```

### Throttled Updates
```python
GLib.timeout_add(self.update_interval, self._periodic_update)  # 100ms

def _periodic_update(self):
    if self.needs_update:
        self.update_plot()
        self.needs_update = False
    return True  # Continue calling
```

### Rate Calculation Example
```python
# Token rate
rate_series = RateCalculator.calculate_token_rate_series(
    [(0.0, 10), (0.1, 12), (0.2, 15)],
    time_window=0.1
)
# Returns: [(0.1, 20.0), (0.2, 30.0)]  # 20 tokens/s, 30 tokens/s

# Firing rate
rate_series = RateCalculator.calculate_firing_rate_series(
    [0.1, 0.3, 0.5, 0.6, 0.8],
    time_window=1.0
)
# Returns rates sampled every 0.1s
```

---

## Documentation Files

- `doc/RATE_PLOTTING_IMPLEMENTATION.md` - Complete implementation plan
- `doc/DATA_COLLECTOR_INTEGRATION_COMPLETE.md` - Integration summary
- `doc/PLOTTING_PROGRESS_SUMMARY.md` - This document

---

**Foundation Complete! Ready for next phase: Tab connectivity and user interaction.**
