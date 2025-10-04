# Real-Time Simulation Data Plotting - Implementation Plan

## Overview

Implement dynamic real-time plotting of Petri net simulation data using matplotlib, integrated into the right panel's Transition and Place tabs. Users can select objects for analysis through context menus or search, with visual feedback and synchronized plotting capabilities.

---

## Requirements Summary

### Functional Requirements

1. **Dual Selection Mechanisms**
   - Context menu on canvas objects: "Add to Analysis" option
   - Selection from search results in Transition/Place tabs
   
2. **Visual Feedback**
   - Selected objects displayed under search area in both tabs
   - Clear indication of what will be plotted
   
3. **Matplotlib Integration**
   - Canvas embedded in both Transition and Place tabs
   - Real-time data plotting during simulation
   
4. **Clear Functionality**
   - Button to deselect all objects
   - Refresh/clear the matplotlib canvas
   
5. **Twin Panel Design**
   - Same code architecture for both tabs
   - Place tab: plots place data (token counts over time)
   - Transition tab: plots transition data (firing events, rates)

---

## Architecture Design

### Component Structure

```
┌─────────────────────────────────────────────────────┐
│           Right Panel (Notebook/Tabs)               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─ Place Tab ────────────────────────────────┐   │
│  │                                             │   │
│  │  [ Search Box ]  [Search Button]            │   │
│  │                                             │   │
│  │  Selected for Analysis:                     │   │
│  │  ┌───────────────────────────────────────┐ │   │
│  │  │ • P1: Buffer (tokens: 5)       [x]    │ │   │
│  │  │ • P3: Queue (tokens: 12)       [x]    │ │   │
│  │  └───────────────────────────────────────┘ │   │
│  │  [Clear Selection]                         │   │
│  │                                             │   │
│  │  ┌─ Matplotlib Canvas ─────────────────┐  │   │
│  │  │                                      │  │   │
│  │  │   Token Count vs Time                │  │   │
│  │  │                                      │  │   │
│  │  │   [Plot Area]                        │  │   │
│  │  │                                      │  │   │
│  │  └──────────────────────────────────────┘  │   │
│  │                                             │   │
│  │  [Grid] [Legend] [Export] [Zoom] [Pan]     │   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─ Transition Tab ─────────────────────────┐     │
│  │  (Same structure, plots transition data)  │     │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Class Architecture

```python
# Base class for plotting panels
class AnalysisPlotPanel:
    """Base class for Place and Transition analysis plotting."""
    
    def __init__(self, parent, object_type: str):
        self.object_type = object_type  # 'place' or 'transition'
        self.selected_objects = []
        self.time_series_data = {}  # {object_id: [(time, value), ...]}
        
        # UI components
        self.search_box = None
        self.selected_list_widget = None
        self.clear_button = None
        self.matplotlib_canvas = None
        self.figure = None
        self.axes = None
    
    def add_object_to_analysis(self, obj):
        """Add object to selection list."""
        
    def remove_object_from_analysis(self, obj):
        """Remove object from selection list."""
        
    def clear_selection(self):
        """Clear all selected objects and plot."""
        
    def update_plot(self):
        """Refresh the matplotlib plot with current data."""
        
    def on_simulation_step(self, controller, time):
        """Called on each simulation step to collect data."""

# Specific implementations
class PlaceAnalysisPanel(AnalysisPlotPanel):
    """Analysis panel for Place objects."""
    
    def collect_data(self, time):
        """Collect token counts for selected places."""
        for place in self.selected_objects:
            self.time_series_data[place.id].append((time, place.tokens))
    
    def plot_data(self):
        """Plot token count vs time for each selected place."""

class TransitionAnalysisPanel(AnalysisPlotPanel):
    """Analysis panel for Transition objects."""
    
    def collect_data(self, time):
        """Collect firing events/rates for selected transitions."""
        for transition in self.selected_objects:
            # Collect firing count, last firing time, rate, etc.
    
    def plot_data(self):
        """Plot transition activity vs time."""
```

---

## Implementation Phases

### Phase 1: UI Foundation (Week 1)

**Goal**: Set up basic UI structure and selection mechanisms

#### Tasks:

1. **Analyze Current UI**
   - Examine existing right panel tabs
   - Locate search functionality
   - Identify insertion points for new components

2. **Create Base AnalysisPlotPanel Class**
   ```python
   # src/shypn/ui/analysis/plot_panel.py
   class AnalysisPlotPanel(Gtk.Box):
       def __init__(self, object_type):
           super().__init__(orientation=Gtk.Orientation.VERTICAL)
           self.object_type = object_type
           self.selected_objects = []
           self._setup_ui()
   ```

3. **Add Selected Objects Display Widget**
   - Create a scrollable list under search box
   - Show object name, ID, current value
   - Add remove buttons (×) for each item

4. **Add Clear Button**
   - Place below selected objects list
   - Connect to clear_selection() method

**Deliverables**:
- `src/shypn/ui/analysis/plot_panel.py` - Base panel class
- UI mockup with widgets in place
- Basic selection list display

---

### Phase 2: Selection Mechanisms (Week 1-2)

**Goal**: Implement two ways to select objects for analysis

#### Selection Method 1: Context Menu

**Implementation**:

```python
# In model canvas right-click handler
def on_canvas_right_click(self, widget, event):
    if event.button == 3:  # Right click
        clicked_obj = self.get_object_at_position(event.x, event.y)
        
        if isinstance(clicked_obj, (Place, Transition)):
            menu = Gtk.Menu()
            
            # Existing menu items...
            
            # Add separator
            menu.append(Gtk.SeparatorMenuItem())
            
            # Add to analysis option
            analysis_item = Gtk.MenuItem(label="Add to Analysis")
            analysis_item.connect("activate", self.on_add_to_analysis, clicked_obj)
            menu.append(analysis_item)
            
            menu.show_all()
            menu.popup_at_pointer(event)
```

**Handler**:

```python
def on_add_to_analysis(self, menu_item, obj):
    """Handle 'Add to Analysis' context menu selection."""
    if isinstance(obj, Place):
        self.place_analysis_panel.add_object_to_analysis(obj)
    elif isinstance(obj, Transition):
        self.transition_analysis_panel.add_object_to_analysis(obj)
```

#### Selection Method 2: Search Results

**Implementation**:

```python
# In search results display
def on_search_result_selected(self, list_box, row):
    """Handle search result selection."""
    obj = row.get_data("object")
    
    # Add button or checkbox in search results
    if self.add_to_analysis_button.get_active():
        self.analysis_panel.add_object_to_analysis(obj)
```

**Deliverables**:
- Context menu integration
- Search result selection mechanism
- Object tracking in selected list

---

### Phase 3: Data Collection Infrastructure (Week 2)

**Goal**: Implement simulation data collection and storage

#### Data Structure Design

```python
class SimulationDataCollector:
    """Collects and stores time-series simulation data."""
    
    def __init__(self):
        # Place data: {place_id: [(time, tokens), ...]}
        self.place_data = defaultdict(list)
        
        # Transition data: {transition_id: [(time, event_type, details), ...]}
        self.transition_data = defaultdict(list)
        
        # Metadata
        self.start_time = 0
        self.current_time = 0
    
    def on_simulation_step(self, controller, time):
        """Collect data on each simulation step."""
        self.current_time = time
        
        # Collect place data
        for place in controller.model.places:
            self.place_data[place.id].append((time, place.tokens))
        
        # Collect transition data
        for transition in controller.model.transitions:
            behavior = controller._get_behavior(transition)
            enabled = behavior.can_fire()[0]
            # Store enablement state, firing events, etc.
    
    def get_data_for_object(self, obj_id, object_type):
        """Retrieve time-series data for a specific object."""
        if object_type == 'place':
            return self.place_data.get(obj_id, [])
        else:
            return self.transition_data.get(obj_id, [])
    
    def clear_data(self):
        """Clear all collected data."""
        self.place_data.clear()
        self.transition_data.clear()
```

#### Integration with Simulation

```python
# In SimulationController initialization
self.data_collector = SimulationDataCollector()
self.add_step_listener(self.data_collector.on_simulation_step)
```

**Deliverables**:
- `src/shypn/engine/simulation/data_collector.py` - Data collection class
- Integration with SimulationController
- Efficient data storage for real-time access

---

### Phase 4: Matplotlib Integration (Week 2-3)

**Goal**: Embed matplotlib canvas and implement plotting

#### Canvas Setup

```python
# In AnalysisPlotPanel.__init__()
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

def _setup_matplotlib(self):
    """Set up matplotlib figure and canvas."""
    self.figure = Figure(figsize=(8, 6), dpi=100)
    self.axes = self.figure.add_subplot(111)
    
    self.canvas = FigureCanvas(self.figure)
    self.canvas.set_size_request(800, 600)
    
    # Add to container
    self.canvas_container.pack_start(self.canvas, True, True, 0)
    
    # Initial plot setup
    self.axes.set_xlabel('Time (s)')
    self.axes.set_ylabel(self._get_ylabel())
    self.axes.set_title(self._get_title())
    self.axes.grid(True, alpha=0.3)
```

#### Place Plotting

```python
class PlaceAnalysisPanel(AnalysisPlotPanel):
    
    def update_plot(self):
        """Update plot with current place data."""
        self.axes.clear()
        
        # Plot each selected place
        for place in self.selected_objects:
            data = self.data_collector.get_data_for_object(place.id, 'place')
            
            if data:
                times = [t for t, v in data]
                tokens = [v for t, v in data]
                
                self.axes.plot(times, tokens, 
                              label=f'{place.name} (P{place.id})',
                              marker='o', 
                              markersize=3,
                              linewidth=2)
        
        # Formatting
        self.axes.set_xlabel('Time (s)')
        self.axes.set_ylabel('Token Count')
        self.axes.set_title('Place Token Evolution')
        self.axes.legend(loc='best')
        self.axes.grid(True, alpha=0.3)
        
        self.canvas.draw()
```

#### Transition Plotting

```python
class TransitionAnalysisPanel(AnalysisPlotPanel):
    
    def update_plot(self):
        """Update plot with current transition data."""
        self.axes.clear()
        
        for transition in self.selected_objects:
            data = self.data_collector.get_data_for_object(
                transition.id, 'transition'
            )
            
            if data:
                # Option 1: Firing count over time
                times = [t for t, event, _ in data if event == 'fired']
                counts = list(range(1, len(times) + 1))
                
                self.axes.step(times, counts,
                              label=f'{transition.name} (T{transition.id})',
                              where='post',
                              linewidth=2)
        
        # Formatting
        self.axes.set_xlabel('Time (s)')
        self.axes.set_ylabel('Cumulative Firings')
        self.axes.set_title('Transition Firing Events')
        self.axes.legend(loc='best')
        self.axes.grid(True, alpha=0.3)
        
        self.canvas.draw()
```

**Deliverables**:
- Matplotlib canvas embedded in both tabs
- Basic plotting for places (token count vs time)
- Basic plotting for transitions (firing events)
- Plot refresh mechanism

---

### Phase 5: Real-Time Updates (Week 3)

**Goal**: Connect simulation to live plot updates

#### Update Strategy

```python
class AnalysisPlotPanel:
    
    def __init__(self, parent, object_type):
        # ...
        self.update_interval = 100  # ms
        self.needs_update = False
        
        # Schedule periodic updates
        GLib.timeout_add(self.update_interval, self._periodic_update)
    
    def on_simulation_step(self, controller, time):
        """Mark that plot needs update."""
        self.needs_update = True
    
    def _periodic_update(self):
        """Periodic callback to update plot if needed."""
        if self.needs_update and self.selected_objects:
            self.update_plot()
            self.needs_update = False
        
        return True  # Continue timeout
```

#### Performance Optimization

```python
# Data buffering
class SimulationDataCollector:
    
    def __init__(self):
        self.place_data = defaultdict(list)
        self.max_data_points = 10000  # Limit data points
    
    def on_simulation_step(self, controller, time):
        """Collect data with buffering."""
        for place in controller.model.places:
            data_list = self.place_data[place.id]
            data_list.append((time, place.tokens))
            
            # Keep only recent data
            if len(data_list) > self.max_data_points:
                # Keep every Nth point for older data (downsampling)
                data_list[:] = data_list[::2]
```

**Deliverables**:
- Real-time plot updates during simulation
- Efficient update strategy (throttling)
- Data buffering to prevent memory issues

---

### Phase 6: Plot Controls & Customization (Week 3-4)

**Goal**: Add user controls for plot customization

#### Control Panel

```python
def _setup_controls(self):
    """Set up plot control buttons."""
    controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    
    # Grid toggle
    self.grid_button = Gtk.ToggleButton(label="Grid")
    self.grid_button.set_active(True)
    self.grid_button.connect("toggled", self.on_grid_toggled)
    controls_box.pack_start(self.grid_button, False, False, 0)
    
    # Legend toggle
    self.legend_button = Gtk.ToggleButton(label="Legend")
    self.legend_button.set_active(True)
    self.legend_button.connect("toggled", self.on_legend_toggled)
    controls_box.pack_start(self.legend_button, False, False, 0)
    
    # Export button
    export_button = Gtk.Button(label="Export")
    export_button.connect("clicked", self.on_export_plot)
    controls_box.pack_start(export_button, False, False, 0)
    
    # Auto-scale button
    autoscale_button = Gtk.Button(label="Auto Scale")
    autoscale_button.connect("clicked", self.on_autoscale)
    controls_box.pack_start(autoscale_button, False, False, 0)
    
    self.pack_start(controls_box, False, False, 6)
```

#### Matplotlib Toolbar

```python
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar

def _setup_matplotlib(self):
    # ... create canvas ...
    
    # Add matplotlib toolbar (zoom, pan, save)
    toolbar = NavigationToolbar(self.canvas, self)
    self.pack_start(toolbar, False, False, 0)
```

#### Export Functionality

```python
def on_export_plot(self, button):
    """Export plot to file."""
    dialog = Gtk.FileChooserDialog(
        title="Export Plot",
        parent=self.get_toplevel(),
        action=Gtk.FileChooserAction.SAVE
    )
    
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_SAVE, Gtk.ResponseType.OK
    )
    
    # Add file filters
    filter_png = Gtk.FileFilter()
    filter_png.set_name("PNG Image")
    filter_png.add_mime_type("image/png")
    dialog.add_filter(filter_png)
    
    filter_pdf = Gtk.FileFilter()
    filter_pdf.set_name("PDF Document")
    filter_pdf.add_mime_type("application/pdf")
    dialog.add_filter(filter_pdf)
    
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        filename = dialog.get_filename()
        self.figure.savefig(filename, dpi=300, bbox_inches='tight')
    
    dialog.destroy()
```

**Deliverables**:
- Control buttons (grid, legend, autoscale)
- Matplotlib toolbar integration
- Export to PNG/PDF functionality

---

### Phase 7: Clear & Reset Functionality (Week 4)

**Goal**: Implement clearing and resetting of selections and plots

#### Clear Selection

```python
def clear_selection(self):
    """Clear all selected objects and reset plot."""
    # Clear selection list
    self.selected_objects.clear()
    
    # Clear UI list widget
    for child in self.selected_list_box.get_children():
        self.selected_list_box.remove(child)
    
    # Clear data
    self.data_collector.clear_data()
    
    # Clear plot
    self.axes.clear()
    self.axes.set_xlabel('Time (s)')
    self.axes.set_ylabel(self._get_ylabel())
    self.axes.set_title(self._get_title())
    self.axes.grid(True, alpha=0.3)
    self.axes.text(0.5, 0.5, 'No objects selected for analysis',
                  ha='center', va='center',
                  transform=self.axes.transAxes,
                  fontsize=14, color='gray')
    self.canvas.draw()
```

#### Reset on Simulation Reset

```python
def on_simulation_reset(self, controller):
    """Handle simulation reset."""
    # Keep selected objects but clear data
    self.data_collector.clear_data()
    
    # Clear and reinitialize plot
    self.axes.clear()
    self._setup_plot_formatting()
    self.canvas.draw()
```

**Deliverables**:
- Clear button functionality
- Reset behavior on simulation reset
- Clean state management

---

## Data Types & Plotting Strategies

### Place Data

**What to Plot**:
- Token count over time (primary)
- Token rate of change (derivative)
- Min/max/average tokens in time windows

**Plot Types**:
- Line plot (default): continuous token evolution
- Step plot: discrete token changes
- Area plot: filled area showing token count

### Transition Data

**What to Plot**:
- Cumulative firing count over time
- Firing rate (firings per second)
- Inter-firing time intervals
- Enablement state over time (binary: enabled/disabled)

**Plot Types**:
- Step plot: cumulative firings (staircase)
- Scatter plot: individual firing events
- Rate plot: moving average of firing rate
- Timeline: enabled periods as horizontal bars

---

## UI/UX Considerations

### Selected Objects Display

**Design Options**:

**Option 1: List with Remove Buttons**
```
Selected for Analysis:
┌─────────────────────────────────┐
│ ● P1: Buffer (5 tokens)    [×] │
│ ● P2: Queue (12 tokens)    [×] │
│ ● T1: Process (enabled)    [×] │
└─────────────────────────────────┘
```

**Option 2: Chip/Tag Style**
```
Selected: [P1: Buffer ×] [P2: Queue ×] [T1: Process ×]
```

**Recommendation**: Option 1 - clearer, more space for info

### Color Scheme

**Automatic Color Assignment**:
```python
from matplotlib import cm
import numpy as np

def get_color_for_object(self, index):
    """Get distinct color for object by index."""
    colormap = cm.get_cmap('tab10')  # Or 'tab20' for more colors
    return colormap(index % 10)
```

### Plot Layout

**Responsive Design**:
- Canvas expands to fill available space
- Minimum canvas size: 600×400
- Controls fixed height at bottom
- Selected list fixed height (scrollable)

---

## File Structure

```
src/shypn/
├── ui/
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── plot_panel.py              # Base AnalysisPlotPanel
│   │   ├── place_analysis_panel.py    # PlaceAnalysisPanel
│   │   ├── transition_analysis_panel.py # TransitionAnalysisPanel
│   │   └── data_collector.py          # SimulationDataCollector
│   │
│   └── main/
│       └── main_window.py             # Integration point
│
├── engine/
│   └── simulation/
│       ├── controller.py              # Add data collector integration
│       └── data_collector.py          # Moved from ui/analysis
│
└── helpers/
    └── plot_helpers.py                # Plotting utility functions

doc/
└── PLOTTING_ANALYSIS_PLAN.md         # This document

tests/
├── test_data_collector.py
├── test_place_analysis_panel.py
└── test_transition_analysis_panel.py
```

---

## Testing Strategy

### Unit Tests

1. **Data Collector Tests**
   - Data collection during simulation
   - Data retrieval for specific objects
   - Memory management with large datasets
   - Clear functionality

2. **Selection Tests**
   - Adding/removing objects
   - Duplicate prevention
   - Cross-tab consistency

3. **Plotting Tests**
   - Plot generation with various data
   - Empty data handling
   - Multiple object plotting
   - Color assignment

### Integration Tests

1. **Simulation Integration**
   - Real-time data collection
   - Plot updates during simulation
   - Reset behavior

2. **UI Integration**
   - Context menu activation
   - Search result selection
   - Clear button behavior

### Performance Tests

1. **Large Dataset Handling**
   - 10,000+ data points per object
   - 10+ objects plotted simultaneously
   - Long-running simulations

2. **UI Responsiveness**
   - Plot refresh rate
   - Simulation step performance impact
   - Canvas redraw optimization

---

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Phase 1 | UI foundation, base classes |
| 1-2 | Phase 2 | Selection mechanisms |
| 2 | Phase 3 | Data collection infrastructure |
| 2-3 | Phase 4 | Matplotlib integration, basic plotting |
| 3 | Phase 5 | Real-time updates, optimization |
| 3-4 | Phase 6 | Plot controls, customization |
| 4 | Phase 7 | Clear/reset functionality |
| 4 | Testing | Comprehensive testing & refinement |

**Total Estimated Time**: 4 weeks

---

## Success Criteria

1. ✅ Users can select places/transitions via context menu
2. ✅ Users can select places/transitions from search results
3. ✅ Selected objects displayed clearly under search area
4. ✅ Real-time plots update during simulation
5. ✅ Place tab plots token counts over time
6. ✅ Transition tab plots firing events/rates
7. ✅ Clear button removes all selections and clears plot
8. ✅ Plots are customizable (grid, legend, zoom, pan)
9. ✅ Plots can be exported to image files
10. ✅ Performance remains acceptable with 10+ objects
11. ✅ Same codebase used for both tabs (twin design)

---

## Future Enhancements (Post-MVP)

1. **Advanced Plotting**
   - Histogram of token distributions
   - Heatmaps for multi-place analysis
   - Phase space plots (place1 vs place2)
   
2. **Statistical Analysis**
   - Mean, median, std deviation display
   - Min/max values highlighted
   - Trend lines and regression
   
3. **Comparison Mode**
   - Compare multiple simulation runs
   - Before/after parameter changes
   
4. **Export Data**
   - Export time-series data to CSV
   - Export plot data to JSON
   
5. **Plot Presets**
   - Save/load plot configurations
   - Templates for common analyses

---

## Dependencies

**Required Packages** (already available):
- `matplotlib` - Plotting library
- `numpy` - Numerical operations
- `GTK3` - UI framework
- `gi.repository.GLib` - Event loop integration

**New Dependencies**:
- None (all requirements already met)

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance degradation with many objects | Medium | High | Implement data downsampling, plot throttling |
| Memory issues with long simulations | Medium | Medium | Circular buffer, data point limits |
| UI complexity overwhelming users | Low | Medium | Clear documentation, tooltips, defaults |
| Matplotlib GTK3 integration issues | Low | High | Test early, have fallback options |
| Real-time updates causing lag | Medium | Medium | Async updates, configurable refresh rate |

---

## Conclusion

This plan provides a comprehensive approach to implementing real-time simulation data plotting with dual selection mechanisms and twin panel design. The phased approach ensures incremental progress with testable milestones, while the shared codebase architecture (AnalysisPlotPanel base class) ensures maintainability and consistency between Place and Transition tabs.

The implementation leverages existing simulation infrastructure (step listeners) and builds upon the current UI structure, minimizing disruption while adding powerful analysis capabilities.
