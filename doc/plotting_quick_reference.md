# Real-Time Plotting - Quick Reference

## Overview

Add matplotlib-based real-time plotting to analyze Place and Transition behavior during simulation.

---

## Key Features

### 1. Dual Selection Mechanisms
- **Context Menu**: Right-click object → "Add to Analysis"
- **Search Selection**: Select from search results → Add to analysis

### 2. Visual Feedback
- Selected objects listed under search area
- Shows: name, ID, current state
- Remove button (×) for each

### 3. Real-Time Plotting
- **Place Tab**: Token counts over time
- **Transition Tab**: Firing events over time
- Updates automatically during simulation

### 4. Clear Functionality
- Clear button removes all selections
- Resets plot to empty state

---

## Architecture

```
AnalysisPlotPanel (base class)
├── PlaceAnalysisPanel
│   └── Plots: token count vs time
└── TransitionAnalysisPanel
    └── Plots: firing count vs time
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Create `AnalysisPlotPanel` base class
- [ ] Add selected objects list widget
- [ ] Add Clear button
- [ ] Integrate into right panel tabs

### Phase 2: Selection
- [ ] Add "Add to Analysis" to context menu
- [ ] Add selection from search results
- [ ] Update selected list display
- [ ] Prevent duplicates

### Phase 3: Data Collection
- [ ] Create `SimulationDataCollector` class
- [ ] Hook into simulation step listener
- [ ] Store time-series data efficiently
- [ ] Implement data retrieval methods

### Phase 4: Plotting
- [ ] Embed matplotlib canvas
- [ ] Implement PlaceAnalysisPanel plotting
- [ ] Implement TransitionAnalysisPanel plotting
- [ ] Add color scheme for multiple objects

### Phase 5: Real-Time Updates
- [ ] Connect to simulation events
- [ ] Implement throttled plot refresh
- [ ] Optimize for performance

### Phase 6: Controls
- [ ] Add matplotlib toolbar (zoom, pan)
- [ ] Add grid/legend toggles
- [ ] Add export functionality
- [ ] Add autoscale button

### Phase 7: Polish
- [ ] Implement clear functionality
- [ ] Handle simulation reset
- [ ] Add empty state messaging
- [ ] Test with multiple scenarios

---

## Code Structure

```
src/shypn/ui/analysis/
├── plot_panel.py              # AnalysisPlotPanel base
├── place_analysis_panel.py    # Place-specific
├── transition_analysis_panel.py # Transition-specific
└── data_collector.py          # Data collection

Files to Modify:
├── ui/main/main_window.py     # Integrate panels
├── helpers/model_canvas_loader.py # Add context menu
└── (search tab files)         # Add selection button
```

---

## Key Classes

### SimulationDataCollector
```python
class SimulationDataCollector:
    place_data: Dict[int, List[Tuple[float, float]]]
    transition_data: Dict[int, List[Tuple[float, str, Any]]]
    
    def on_simulation_step(controller, time)
    def get_data_for_object(obj_id, obj_type)
    def clear_data()
```

### AnalysisPlotPanel
```python
class AnalysisPlotPanel(Gtk.Box):
    selected_objects: List
    matplotlib_canvas: FigureCanvas
    axes: matplotlib.axes.Axes
    
    def add_object_to_analysis(obj)
    def remove_object_from_analysis(obj)
    def clear_selection()
    def update_plot()
```

---

## UI Layout

```
┌─ Right Panel Tab ────────────────────┐
│                                      │
│  [Search Box] [Search]               │
│                                      │
│  Selected for Analysis:              │
│  ┌────────────────────────────────┐ │
│  │ • P1: Buffer (5)          [×] │ │
│  │ • P3: Queue (12)          [×] │ │
│  └────────────────────────────────┘ │
│  [Clear Selection]                   │
│                                      │
│  ┌─ Plot ──────────────────────┐    │
│  │                              │    │
│  │   [Matplotlib Canvas]        │    │
│  │                              │    │
│  └──────────────────────────────┘    │
│                                      │
│  [Grid] [Legend] [Export] [Zoom]     │
│                                      │
└──────────────────────────────────────┘
```

---

## Plot Types

### Places
- **Line plot**: Token count vs time
- **Step plot**: Discrete changes
- Multiple places: different colors

### Transitions
- **Step plot**: Cumulative firings
- **Scatter plot**: Firing events
- **Rate plot**: Firings per second

---

## Testing Priorities

1. Data collection accuracy
2. Real-time plot updates
3. Performance with 10+ objects
4. Memory usage over long runs
5. UI responsiveness
6. Clear/reset behavior

---

## Timeline

| Week | Focus |
|------|-------|
| 1 | UI foundation + selection |
| 2 | Data collection + basic plotting |
| 3 | Real-time updates + controls |
| 4 | Polish + testing |

---

## Success Metrics

- ✅ Select objects via context menu
- ✅ Select objects from search
- ✅ Real-time plot updates (< 100ms delay)
- ✅ Handle 10+ objects smoothly
- ✅ Export plots to PNG/PDF
- ✅ Clear functionality works
- ✅ Twin code reuse for both tabs

---

## Quick Start Commands

```bash
# Run simulation with plotting
python3 src/shypn.py

# Run tests
python3 tests/test_data_collector.py
python3 tests/test_place_analysis_panel.py
python3 tests/test_transition_analysis_panel.py
```

---

## Dependencies

- matplotlib (plotting)
- numpy (data handling)
- GTK3 (UI)
- GLib (events)

All already available in project!

---

## Notes

- Keep plots responsive (throttle updates)
- Limit data points (downsample old data)
- Use consistent color scheme
- Provide clear empty states
- Make twin code truly reusable
