# Dynamic Analysis Implementation Summary

**Feature**: Real-time Place Token Rate and Transition Firing Rate Analysis
**Date**: October 4, 2025
**Status**: ✅ Complete (10/10 implementation tasks)

## Overview

This document describes the implementation of the dynamic analysis plotting system in Shypn, which provides real-time visualization of place token consumption/production rates and transition firing rates during Petri net simulation.

## Architecture

### Design Principles

1. **Separation of Concerns**: Business logic in separate modules, loaders only wire components
2. **Tab-Aware**: Right panel automatically switches data sources when users change tabs
3. **Clean Dependencies**: Lazy imports to avoid circular dependencies
4. **Real-time Updates**: Throttled updates (100ms interval) for smooth performance
5. **User-Friendly**: Multiple ways to add objects to analysis (search, context menu)

### Component Structure

```
src/shypn/analyses/
├── __init__.py                    # Lazy imports, package exports
├── data_collector.py              # SimulationDataCollector - collects raw data
├── rate_calculator.py             # RateCalculator - rate computation utilities
├── plot_panel.py                  # AnalysisPlotPanel - base plotting class
├── place_rate_panel.py            # PlaceRatePanel - place token rate plotting
├── transition_rate_panel.py       # TransitionRatePanel - firing rate plotting
├── search_handler.py              # SearchHandler - search places/transitions
└── context_menu_handler.py        # ContextMenuHandler - context menu integration
```

## Implementation Details

### 1. Data Collection Infrastructure

**Files**: `data_collector.py`, `rate_calculator.py`, `__init__.py`

#### SimulationDataCollector
- **Purpose**: Collects raw simulation data for analysis
- **Data Stored**:
  - Place token counts: `{place_id: [(time, token_count), ...]}`
  - Transition firing events: `{transition_id: [(time, event_type, data), ...]}`
- **Features**:
  - Automatic downsampling at 8000 data points per object
  - Statistics tracking (min, max, average, total firings)
  - Step listener interface for controller integration
  - Clear method for simulation reset

#### RateCalculator
- **Purpose**: Utility class for rate calculations
- **Methods**:
  - `calculate_token_rate(data, time_window)`: Token rate at specific time
  - `calculate_token_rate_series(data, time_window, sample_interval)`: Rate time series
  - `calculate_firing_rate(events, start_time, end_time, time_window)`: Firing rate
  - `calculate_firing_rate_series(events, time_window, sample_interval)`: Firing rate series
  - `moving_average(values, window_size)`: Smooth rate values

**Integration Points**:
- Controller: Added `data_collector` attribute, notifies on transition firings
- SimulateToolsPaletteLoader: Creates data_collector, attaches to controller, registers as step listener

### 2. Plotting Panel Modules

**Files**: `plot_panel.py`, `place_rate_panel.py`, `transition_rate_panel.py`

#### AnalysisPlotPanel (Base Class)
- **Purpose**: Common infrastructure for all analysis plots
- **Features**:
  - Matplotlib canvas with GTK3 integration
  - NavigationToolbar2GTK3 (zoom, pan, save)
  - Selected objects list with color indicators and remove buttons
  - Plot controls (grid, legend, auto scale toggles)
  - Throttled updates (100ms) via GLib.timeout
  - 10-color palette for multiple objects
  - Abstract methods for subclass customization

**UI Components**:
1. Selected Objects Frame: List of objects with colors and remove buttons
2. Plot Controls Frame: Checkboxes for grid, legend, auto scale
3. Canvas Frame: Matplotlib toolbar + plot canvas

**Methods**:
- `add_object(obj)`: Add place/transition to plot
- `remove_object(obj)`: Remove from plot
- `update_plot()`: Redraw with current data
- `_format_plot()`: Apply styling (grid, legend, labels, auto scale)
- Abstract: `_get_rate_data(obj_id)`, `_get_ylabel()`, `_get_title()`

#### PlaceRatePanel
- **Purpose**: Plot place token consumption/production rates
- **Rate Calculation**: d(tokens)/dt using configurable time window (default: 0.1s)
- **Features**:
  - Positive rate = token production
  - Negative rate = token consumption
  - Zero reference line for clear visualization
  - Configurable time window via `set_time_window(window)`

#### TransitionRatePanel
- **Purpose**: Plot transition firing rates (firings per second)
- **Rate Calculation**: Firing frequency using time window (default: 1.0s for Hz)
- **Features**:
  - Rate in Hz (firings/second)
  - Configurable time window via `set_time_window(window)`

### 3. UI Integration

**Files**: `right_panel_loader.py`, `right_panel.ui`

#### Right Panel Structure
- Dynamic Analyses expander with internal notebook
- Two tabs: Transitions and Places
- Each tab contains:
  - Search controls (entry, search/clear buttons)
  - Result label
  - Canvas container (replaced with plot panel)

#### RightPanelLoader Updates
- Added `data_collector` parameter to `__init__()`
- Added `model` attribute for search functionality
- `_setup_plotting_panels()`: Instantiates panels, removes placeholders
- `_wire_search_ui()`: Connects search widgets to panel methods
- `set_data_collector(data_collector)`: Late binding for data collector
- `set_model(model)`: Late binding for model reference
- Creates `ContextMenuHandler` after panels exist

### 4. Tab-Aware Data Switching

**Files**: `model_canvas_loader.py`, `shypn.py`

#### ModelCanvasLoader Updates
- Added `right_panel_loader` attribute
- Added `context_menu_handler` attribute
- Enhanced `_on_notebook_page_changed()`:
  - Extracts drawing_area from page widget
  - Looks up `simulate_tools_palette` for that tab
  - Gets `data_collector` from palette
  - Calls `right_panel_loader.set_data_collector(data_collector)`
  - Looks up `canvas_manager` for that tab
  - Calls `right_panel_loader.set_model(manager)`
- Added `set_right_panel_loader(loader)` method
- Added `set_context_menu_handler(handler)` method
- Modified `_show_object_context_menu()` to call handler

#### Shypn.py Wiring
```python
# Wire right panel to canvas loader (after line 143)
model_canvas_loader.set_right_panel_loader(right_panel_loader)

# Wire context menu handler (after line 150)
if right_panel_loader.context_menu_handler:
    model_canvas_loader.set_context_menu_handler(right_panel_loader.context_menu_handler)
```

### 5. Search Functionality

**Files**: `search_handler.py`, `place_rate_panel.py`, `transition_rate_panel.py`

#### SearchHandler
- **Methods**:
  - `search_places(model, query)`: Case-insensitive search by name/label
  - `search_transitions(model, query)`: Case-insensitive search by name/label
  - `format_result_summary(results, object_type)`: Format display string

#### Panel Integration
- `wire_search_ui(entry, search_btn, clear_btn, result_label, model)`: Wires UI
- Auto-adds single search results to plot
- Enter key support in search entry
- Displays formatted result summaries

**User Flow**:
1. User types "P1" in search entry
2. Clicks search or presses Enter
3. SearchHandler finds matching places
4. If 1 result: automatically added to plot
5. If multiple: shows "Found 3 places: P1, P10, P12"

### 6. Context Menu Integration

**Files**: `context_menu_handler.py`

#### ContextMenuHandler
- **Purpose**: Add "Add to Analysis" items to canvas context menus
- **Methods**:
  - `add_analysis_menu_items(menu, obj)`: Adds menu items
  - `_on_add_to_analysis_clicked(obj, panel)`: Handles click
- **Integration**: Called from `_show_object_context_menu()` in model_canvas_loader

**User Flow**:
1. User right-clicks on place/transition in canvas
2. Context menu appears with properties, edit, delete
3. New separator + "Add to Place/Transition Analysis" item
4. Click adds object to appropriate plot panel

### 7. Plot Controls

**Features**:
- **Matplotlib Toolbar**: Zoom, pan, home, back, forward, save to file
- **Show Grid**: Toggle grid lines (default: on)
- **Show Legend**: Toggle legend display (default: on)
- **Auto Scale Y-axis**: Toggle automatic Y-axis scaling (default: on)

**Implementation**: All in `AnalysisPlotPanel._setup_ui()` and `_format_plot()`

## Data Flow

### Simulation → Data Collection → Plotting

```
1. User runs simulation (clicks "Step" or "Run")
   ↓
2. Controller.step() executes
   ↓
3. Controller notifies step listeners (including data_collector)
   ↓
4. SimulationDataCollector.on_simulation_step() captures:
   - Current time
   - All place token counts
   ↓
5. On transition firing:
   Controller.notify_transition_fired()
   ↓
   SimulationDataCollector.on_transition_fired()
   Records firing event
   ↓
6. Panel periodic update (every 100ms):
   AnalysisPlotPanel._periodic_update()
   ↓
   If needs_update: update_plot()
   ↓
7. Panel calls RateCalculator to compute rates:
   - PlaceRatePanel: calculate_token_rate_series()
   - TransitionRatePanel: calculate_firing_rate_series()
   ↓
8. Plot updated with new rate curves
```

### Tab Switching → Data Source Update

```
1. User clicks different tab
   ↓
2. GTK fires "switch-page" signal
   ↓
3. model_canvas_loader._on_notebook_page_changed()
   ↓
4. Extracts drawing_area from page
   ↓
5. Looks up simulate_tools_palette for that drawing_area
   ↓
6. Gets data_collector from palette
   ↓
7. Calls right_panel_loader.set_data_collector(data_collector)
   ↓
8. place_panel.data_collector = data_collector
   transition_panel.data_collector = data_collector
   ↓
9. Looks up canvas_manager for that drawing_area
   ↓
10. Calls right_panel_loader.set_model(manager)
    ↓
11. Search now works with new tab's model
    ↓
12. Plots now show data from new tab's simulation
```

## Performance Optimizations

### Data Collection
- **Downsampling**: Automatically limits to 8000 points per object
- **Strategy**: Keep first/last, uniform sampling of middle points
- **Benefit**: Prevents memory bloat during long simulations

### Plot Updates
- **Throttling**: 100ms update interval via GLib.timeout
- **Benefit**: Prevents overwhelming UI during rapid simulation steps
- **Flag-based**: `needs_update` flag prevents redundant redraws

### Rate Calculation
- **Vectorized**: Uses list comprehensions for efficiency
- **Cached**: Rates calculated on-demand, not stored
- **Benefit**: Memory-efficient, always uses latest data

## User Workflows

### Workflow 1: Add Places to Analysis via Search

1. Open right panel (toggle button in toolbar)
2. Click "Places" tab in Dynamic Analyses
3. Type "P" in search entry
4. Press Enter or click Search
5. See "Found 5 places: P1, P2, P3, P4, P5"
6. Type "P1" for specific place
7. Press Enter
8. P1 automatically added to plot
9. Run simulation to see token rate

### Workflow 2: Add Transitions via Context Menu

1. Right-click on transition in canvas
2. See context menu with "Edit Properties", "Delete", etc.
3. Click "Add to Transition Analysis"
4. Transition appears in plot's selected list
5. Run simulation to see firing rate

### Workflow 3: Control Plot Appearance

1. Add multiple places to plot
2. Run simulation
3. Uncheck "Show Grid" to hide grid lines
4. Uncheck "Show Legend" to hide legend
5. Uncheck "Auto Scale Y-axis" for fixed scale
6. Use toolbar zoom to focus on time region
7. Click save icon to export plot image

### Workflow 4: Multi-Tab Analysis

1. Open Tab 1 with model A
2. Add P1, P2 to place analysis
3. Run simulation, observe rates
4. Create new tab (File > New)
5. Build model B in Tab 2
6. Switch to Tab 2
7. Right panel automatically shows model B's data
8. Add places from model B
9. Switch back to Tab 1
10. Right panel shows model A's data again

## Files Modified

### New Files Created (8)
1. `src/shypn/analyses/__init__.py`
2. `src/shypn/analyses/data_collector.py`
3. `src/shypn/analyses/rate_calculator.py`
4. `src/shypn/analyses/plot_panel.py`
5. `src/shypn/analyses/place_rate_panel.py`
6. `src/shypn/analyses/transition_rate_panel.py`
7. `src/shypn/analyses/search_handler.py`
8. `src/shypn/analyses/context_menu_handler.py`

### Modified Files (5)
1. `src/shypn/engine/controller.py` - Added data_collector support
2. `src/shypn/helpers/simulate_tools_palette_loader.py` - Creates and wires data_collector
3. `src/shypn/helpers/right_panel_loader.py` - Panel instantiation, search wiring, context menu handler
4. `src/shypn/helpers/model_canvas_loader.py` - Tab switching, context menu integration
5. `src/shypn.py` - Main wiring of components

### Existing Files (no changes)
- `ui/panels/right_panel.ui` - Already had placeholder structure

## Code Statistics

- **Total Lines Added**: ~1800 lines
- **New Python Modules**: 8 files
- **Modified Python Files**: 5 files
- **New Classes**: 7 classes (SimulationDataCollector, RateCalculator, AnalysisPlotPanel, PlaceRatePanel, TransitionRatePanel, SearchHandler, ContextMenuHandler)
- **Design Pattern**: Strategy pattern (abstract base class with concrete implementations)

## Key Features Summary

### ✅ Core Functionality
- [x] Real-time data collection during simulation
- [x] Place token rate plotting (consumption/production)
- [x] Transition firing rate plotting (Hz)
- [x] Automatic data downsampling (8000 point limit)
- [x] Multiple object selection per plot
- [x] 10-color palette for object differentiation

### ✅ UI Integration
- [x] Right panel with tabbed interface
- [x] Search functionality (name/label matching)
- [x] Context menu "Add to Analysis" option
- [x] Matplotlib navigation toolbar
- [x] Plot control toggles (grid, legend, auto scale)

### ✅ Multi-Tab Support
- [x] Tab-aware data collector switching
- [x] Tab-aware model reference switching
- [x] Independent analysis per tab
- [x] Seamless switching between tabs

### ✅ User Experience
- [x] Auto-add for single search results
- [x] Color-coded object list
- [x] Remove buttons for individual objects
- [x] Clear selection button
- [x] Throttled updates (smooth performance)

## Testing Recommendations

### Test Cases (for Task 11)

1. **Basic Functionality**
   - Add places to plot via search
   - Add transitions via context menu
   - Verify colors are distinct
   - Remove individual objects
   - Clear all selections

2. **Rate Calculations**
   - Discrete net: verify token rates match manual calculation
   - Continuous net: verify rates are smooth
   - Stochastic net: verify firing rates are reasonable
   - Test different time steps (0.01s, 0.1s, 1.0s)

3. **Performance**
   - 10+ objects on single plot
   - Long simulation (>10,000 steps)
   - Verify downsampling at 8000 points
   - Check memory usage stays reasonable
   - Verify UI remains responsive

4. **Multi-Tab**
   - Create 3 tabs with different models
   - Add objects to analysis in each tab
   - Switch between tabs
   - Verify correct data shows in right panel
   - Run simulation in different tabs

5. **Plot Controls**
   - Toggle grid on/off
   - Toggle legend on/off
   - Toggle auto scale
   - Use toolbar zoom/pan
   - Save plot to file

6. **Float/Dock Behavior**
   - Float right panel
   - Add objects to plot
   - Dock panel back
   - Verify plot state preserved

## Example Models to Create

1. **Simple Producer-Consumer**
   - P1 (buffer) → T1 (consume) → P2 (output)
   - Shows token consumption/production clearly

2. **Parallel Transitions**
   - P1 → (T1, T2, T3) → P2
   - Good for comparing firing rates

3. **Continuous Flow**
   - Continuous transitions with rate functions
   - Demonstrates smooth rate curves

4. **Stochastic System**
   - Multiple stochastic transitions
   - Shows variable firing patterns

## Future Enhancements (Out of Scope)

- Export data to CSV
- Time window adjustment spinner in UI
- Histogram view for firing times
- Statistical summary panel
- Comparison mode (overlay multiple tabs)
- Custom color selection
- Plot annotations
- Derivative/integral views

## Conclusion

The dynamic analysis system is fully implemented and ready for testing. All 10 implementation tasks are complete, providing a robust, user-friendly real-time analysis capability for Petri net simulations. The architecture is clean, maintainable, and extensible for future enhancements.

**Status**: ✅ Ready for testing (Task 11)
