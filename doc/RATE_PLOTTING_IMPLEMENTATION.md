# Rate-Based Simulation Analysis - Implementation Plan

## Overview

Implement real-time rate-based plotting of Petri net simulation data in `src/shypn/analyses/` directory:
- **Places**: Token consumption/production rate over time (d(tokens)/dt)
- **Transitions**: Firing rate over time (firings per time unit)

---

## Rate Plotting Focus

### Place Analysis - Token Rate (PRIMARY)

**What to Plot**: Token consumption/production rate
- **Rate Calculation**: `rate = Δtokens / Δtime`
- **Positive rate**: Token production (tokens being added)
- **Negative rate**: Token consumption (tokens being removed)
- **Zero rate**: Stable state (no change)

**Visualization**:
```
Token Rate (tokens/s)
     ^
  10 |           ___
   5 |    __/‾‾‾    \___
   0 |___/                \___
  -5 |                        \___
 -10 |__________________________|___> Time (s)
     
     Production → Stable → Consumption
```

**Implementation**:
```python
def calculate_token_rate(self, place_id, time_window=0.1):
    """Calculate token consumption/production rate.
    
    Args:
        place_id: Place identifier
        time_window: Time window for rate calculation (seconds)
    
    Returns:
        float: Token rate (tokens/second)
    """
    data = self.place_data[place_id]
    
    if len(data) < 2:
        return 0.0
    
    # Get recent data points within time window
    recent_data = [(t, tokens) for t, tokens in data 
                   if data[-1][0] - t <= time_window]
    
    if len(recent_data) < 2:
        return 0.0
    
    # Calculate rate: Δtokens / Δtime
    dt = recent_data[-1][0] - recent_data[0][0]
    dtokens = recent_data[-1][1] - recent_data[0][1]
    
    return dtokens / dt if dt > 0 else 0.0
```

### Transition Analysis - Firing Rate (PRIMARY)

**What to Plot**: Transition firing rate
- **Rate Calculation**: `rate = firings / time_window`
- **Moving average**: Smooth out instantaneous spikes
- **Units**: Firings per second (Hz)

**Visualization**:
```
Firing Rate (firings/s)
     ^
   5 |        ___
   4 |       /   \___
   3 |  ____/        \___
   2 | /                 \___
   1 |/________________________\__> Time (s)
     
     Ramp-up → Peak → Decline
```

**Implementation**:
```python
def calculate_firing_rate(self, transition_id, time_window=1.0):
    """Calculate transition firing rate.
    
    Args:
        transition_id: Transition identifier
        time_window: Time window for rate calculation (seconds)
    
    Returns:
        float: Firing rate (firings/second)
    """
    events = self.transition_data[transition_id]
    
    if not events:
        return 0.0
    
    # Get recent firing events within time window
    current_time = events[-1][0] if events else 0
    recent_firings = [t for t, event_type, _ in events 
                     if event_type == 'fired' 
                     and current_time - t <= time_window]
    
    # Calculate rate: number of firings / time window
    return len(recent_firings) / time_window
```

---

## Directory Structure

```
src/shypn/analyses/
├── __init__.py
├── data_collector.py          # SimulationDataCollector class
├── plot_panel.py              # Base AnalysisPlotPanel class
├── place_rate_panel.py        # PlaceRatePanel (token rate plotting)
├── transition_rate_panel.py   # TransitionRatePanel (firing rate plotting)
└── rate_calculator.py         # Rate calculation utilities

src/shypn/ui/main/
└── main_window.py             # Integration point

src/shypn/helpers/
├── model_canvas_loader.py     # Add context menu
└── (search loaders)           # Add selection mechanism

doc/
└── RATE_PLOTTING_PLAN.md     # This document
```

---

## Class Architecture

### Core Classes

```python
# src/shypn/analyses/data_collector.py
class SimulationDataCollector:
    """Collects raw simulation data for rate calculations."""
    
    def __init__(self):
        # Place data: {place_id: [(time, tokens), ...]}
        self.place_data = defaultdict(list)
        
        # Transition data: {transition_id: [(time, event_type, details), ...]}
        self.transition_data = defaultdict(list)
        
        # Configuration
        self.max_data_points = 10000
        self.time_window = 1.0  # Default time window for rates
    
    def on_simulation_step(self, controller, time):
        """Collect data on each simulation step."""
        # Collect place token counts
        for place in controller.model.places:
            self.place_data[place.id].append((time, place.tokens))
        
        # Track transition firings (from previous step)
        # This requires integration with controller firing events
    
    def on_transition_fired(self, transition, time):
        """Record transition firing event."""
        self.transition_data[transition.id].append((time, 'fired', None))
```

```python
# src/shypn/analyses/rate_calculator.py
class RateCalculator:
    """Utility class for rate calculations."""
    
    @staticmethod
    def calculate_token_rate(data_points, time_window=0.1):
        """Calculate token consumption/production rate.
        
        Args:
            data_points: List of (time, tokens) tuples
            time_window: Time window for calculation (seconds)
        
        Returns:
            float: Token rate (tokens/second)
        """
        if len(data_points) < 2:
            return 0.0
        
        # Use recent data within time window
        current_time = data_points[-1][0]
        recent = [(t, tokens) for t, tokens in data_points 
                  if current_time - t <= time_window]
        
        if len(recent) < 2:
            return 0.0
        
        dt = recent[-1][0] - recent[0][0]
        dtokens = recent[-1][1] - recent[0][1]
        
        return dtokens / dt if dt > 0 else 0.0
    
    @staticmethod
    def calculate_firing_rate(event_times, current_time, time_window=1.0):
        """Calculate transition firing rate.
        
        Args:
            event_times: List of firing event times
            current_time: Current simulation time
            time_window: Time window for calculation (seconds)
        
        Returns:
            float: Firing rate (firings/second)
        """
        recent_firings = [t for t in event_times 
                         if current_time - t <= time_window]
        
        return len(recent_firings) / time_window
    
    @staticmethod
    def moving_average(rates, window_size=5):
        """Apply moving average smoothing to rate data.
        
        Args:
            rates: List of rate values
            window_size: Number of points for averaging
        
        Returns:
            List of smoothed rates
        """
        if len(rates) < window_size:
            return rates
        
        smoothed = []
        for i in range(len(rates)):
            start = max(0, i - window_size + 1)
            window = rates[start:i+1]
            smoothed.append(sum(window) / len(window))
        
        return smoothed
```

```python
# src/shypn/analyses/plot_panel.py
class AnalysisPlotPanel(Gtk.Box):
    """Base class for rate plotting panels."""
    
    def __init__(self, object_type, data_collector):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.object_type = object_type  # 'place' or 'transition'
        self.data_collector = data_collector
        self.rate_calculator = RateCalculator()
        
        self.selected_objects = []
        self.time_series_rates = {}  # {obj_id: [(time, rate), ...]}
        
        self._setup_ui()
        self._setup_matplotlib()
    
    def _get_rate_data(self, obj_id):
        """Get rate data for an object. Override in subclasses."""
        raise NotImplementedError
    
    def update_plot(self):
        """Update the rate plot with current data."""
        self.axes.clear()
        
        if not self.selected_objects:
            self._show_empty_state()
            return
        
        # Plot rate for each selected object
        for i, obj in enumerate(self.selected_objects):
            rate_data = self._get_rate_data(obj.id)
            
            if rate_data:
                times = [t for t, r in rate_data]
                rates = [r for t, r in rate_data]
                
                color = self._get_color(i)
                self.axes.plot(times, rates,
                              label=f'{obj.name} ({self.object_type[0].upper()}{obj.id})',
                              color=color,
                              linewidth=2)
        
        self._format_plot()
        self.canvas.draw()
    
    def _format_plot(self):
        """Format the plot with labels and styling."""
        self.axes.set_xlabel('Time (s)', fontsize=12)
        self.axes.set_ylabel(self._get_ylabel(), fontsize=12)
        self.axes.set_title(self._get_title(), fontsize=14, fontweight='bold')
        self.axes.legend(loc='best')
        self.axes.grid(True, alpha=0.3, linestyle='--')
        
        # Add zero line for reference
        if self.object_type == 'place':
            self.axes.axhline(y=0, color='gray', linestyle='-', 
                            linewidth=0.5, alpha=0.5)
```

```python
# src/shypn/analyses/place_rate_panel.py
class PlaceRatePanel(AnalysisPlotPanel):
    """Rate plotting panel for Place objects."""
    
    def __init__(self, data_collector):
        super().__init__('place', data_collector)
        self.time_window = 0.1  # 100ms window for token rate
    
    def _get_ylabel(self):
        return 'Token Rate (tokens/s)'
    
    def _get_title(self):
        return 'Place Token Consumption/Production Rate'
    
    def _get_rate_data(self, place_id):
        """Calculate and return token rate data for a place."""
        raw_data = self.data_collector.place_data.get(place_id, [])
        
        if len(raw_data) < 2:
            return []
        
        # Calculate rate at each time point
        rate_data = []
        for i in range(1, len(raw_data)):
            time = raw_data[i][0]
            
            # Get data within time window
            start_idx = max(0, i - 10)  # Look back ~10 points
            window_data = raw_data[start_idx:i+1]
            
            rate = self.rate_calculator.calculate_token_rate(
                window_data, self.time_window
            )
            
            rate_data.append((time, rate))
        
        return rate_data
    
    def on_simulation_step(self, controller, time):
        """Called on each simulation step."""
        # Mark that update is needed
        self.needs_update = True
```

```python
# src/shypn/analyses/transition_rate_panel.py
class TransitionRatePanel(AnalysisPlotPanel):
    """Rate plotting panel for Transition objects."""
    
    def __init__(self, data_collector):
        super().__init__('transition', data_collector)
        self.time_window = 1.0  # 1 second window for firing rate
    
    def _get_ylabel(self):
        return 'Firing Rate (firings/s)'
    
    def _get_title(self):
        return 'Transition Firing Rate'
    
    def _get_rate_data(self, transition_id):
        """Calculate and return firing rate data for a transition."""
        events = self.data_collector.transition_data.get(transition_id, [])
        
        if not events:
            return []
        
        # Extract firing times
        firing_times = [t for t, event_type, _ in events 
                       if event_type == 'fired']
        
        if len(firing_times) < 2:
            return []
        
        # Calculate rate at regular intervals
        rate_data = []
        start_time = firing_times[0]
        end_time = firing_times[-1]
        
        # Sample rate every 0.1 seconds
        current_time = start_time
        while current_time <= end_time:
            rate = self.rate_calculator.calculate_firing_rate(
                firing_times, current_time, self.time_window
            )
            rate_data.append((current_time, rate))
            current_time += 0.1
        
        return rate_data
    
    def on_simulation_step(self, controller, time):
        """Called on each simulation step."""
        self.needs_update = True
```

---

## Integration with Simulation

### Tracking Transition Firings

We need to capture when transitions fire. Modify the controller to notify the data collector:

```python
# In SimulationController._fire_transition()
def _fire_transition(self, transition):
    """Fire a transition and notify listeners."""
    behavior = self._get_behavior(transition)
    
    input_arcs = behavior.get_input_arcs()
    output_arcs = behavior.get_output_arcs()
    
    # Fire using behavior
    behavior.fire(input_arcs, output_arcs)
    
    # Notify data collector (if attached)
    if hasattr(self, 'data_collector') and self.data_collector:
        self.data_collector.on_transition_fired(transition, self.time)
```

### Attaching Data Collector

```python
# In main application initialization
from shypn.analyses.data_collector import SimulationDataCollector

# Create data collector
data_collector = SimulationDataCollector()

# Attach to controller
controller.data_collector = data_collector
controller.add_step_listener(data_collector.on_simulation_step)
```

---

## UI Layout

```
┌─ Place Tab ──────────────────────────────────┐
│                                              │
│  [Search Box]  [Search]                      │
│                                              │
│  Selected for Analysis:                      │
│  ┌────────────────────────────────────────┐ │
│  │ • P1: Buffer (rate: +2.5 tok/s)  [×] │ │
│  │ • P2: Queue (rate: -1.2 tok/s)   [×] │ │
│  └────────────────────────────────────────┘ │
│  [Clear Selection]                           │
│                                              │
│  ┌─ Token Consumption/Production Rate ────┐ │
│  │                                         │ │
│  │  Rate (tokens/s)                        │ │
│  │    ^                                    │ │
│  │  5 |    P1 (production)                 │ │
│  │    |   /‾‾\                             │ │
│  │  0 |__/____\_____ Zero line             │ │
│  │    |         \                          │ │
│  │ -5 |          \__ P2 (consumption)      │ │
│  │    |____________|_____> Time (s)        │ │
│  │                                         │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  [Grid] [Legend] [Export] [Auto Scale]      │
│  [Matplotlib Toolbar: Zoom, Pan, Save]      │
│                                              │
└──────────────────────────────────────────────┘

┌─ Transition Tab ─────────────────────────────┐
│                                              │
│  [Search Box]  [Search]                      │
│                                              │
│  Selected for Analysis:                      │
│  ┌────────────────────────────────────────┐ │
│  │ • T1: Process (rate: 3.2 firings/s) [×]│ │
│  │ • T2: Transfer (rate: 0.8 firings/s)[×]│ │
│  └────────────────────────────────────────┘ │
│  [Clear Selection]                           │
│                                              │
│  ┌─ Transition Firing Rate ───────────────┐ │
│  │                                         │ │
│  │  Rate (firings/s)                       │ │
│  │    ^                                    │ │
│  │  5 |      T1                            │ │
│  │    |     /‾‾\                           │ │
│  │  3 |  __/    \___                       │ │
│  │    | /           \                      │ │
│  │  1 |/     T2      \_                    │ │
│  │    |_______________\__> Time (s)        │ │
│  │                                         │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  [Grid] [Legend] [Export] [Auto Scale]      │
│  [Matplotlib Toolbar: Zoom, Pan, Save]      │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Data Collection Foundation (Days 1-2)

**Files to Create**:
1. `src/shypn/analyses/__init__.py`
2. `src/shypn/analyses/data_collector.py`
3. `src/shypn/analyses/rate_calculator.py`

**Tasks**:
- Create directory structure
- Implement SimulationDataCollector
- Implement RateCalculator utility
- Add transition firing tracking to controller
- Test data collection

### Phase 2: Base Plotting Panel (Days 3-4)

**Files to Create**:
1. `src/shypn/analyses/plot_panel.py`

**Tasks**:
- Create base AnalysisPlotPanel class
- Set up matplotlib canvas
- Implement selected objects list widget
- Add Clear button
- Test basic UI structure

### Phase 3: Place Rate Plotting (Days 5-6)

**Files to Create**:
1. `src/shypn/analyses/place_rate_panel.py`

**Tasks**:
- Implement PlaceRatePanel
- Token rate calculation logic
- Real-time plot updates
- Test with various place scenarios

### Phase 4: Transition Rate Plotting (Days 7-8)

**Files to Create**:
1. `src/shypn/analyses/transition_rate_panel.py`

**Tasks**:
- Implement TransitionRatePanel
- Firing rate calculation logic
- Real-time plot updates
- Test with various transition types

### Phase 5: Selection Mechanisms (Days 9-10)

**Files to Modify**:
1. `src/shypn/helpers/model_canvas_loader.py`
2. Search-related files in helpers/

**Tasks**:
- Add "Add to Analysis" to context menu
- Add selection from search results
- Wire up to analysis panels
- Test selection workflows

### Phase 6: Integration & Polish (Days 11-12)

**Files to Modify**:
1. `src/shypn/ui/main/main_window.py`

**Tasks**:
- Integrate panels into right tabs
- Connect to simulation controller
- Add plot controls (grid, legend, export)
- Performance optimization
- Comprehensive testing

---

## Rate Calculation Examples

### Example 1: Place Token Rate

```python
# Simulation data for Place P1
place_data = [
    (0.0, 10),   # Start: 10 tokens
    (0.1, 10),   # No change
    (0.2, 12),   # +2 tokens in 0.1s → rate = 20 tokens/s
    (0.3, 15),   # +3 tokens in 0.1s → rate = 30 tokens/s
    (0.4, 15),   # No change → rate = 0 tokens/s
    (0.5, 13),   # -2 tokens in 0.1s → rate = -20 tokens/s
]

# Rate at t=0.2 (looking back 0.1s):
# Δtokens = 12 - 10 = 2
# Δtime = 0.2 - 0.1 = 0.1
# Rate = 2 / 0.1 = 20 tokens/s (production)

# Rate at t=0.5 (looking back 0.1s):
# Δtokens = 13 - 15 = -2
# Δtime = 0.5 - 0.4 = 0.1
# Rate = -2 / 0.1 = -20 tokens/s (consumption)
```

### Example 2: Transition Firing Rate

```python
# Firing events for Transition T1
firing_times = [0.1, 0.3, 0.5, 0.6, 0.8, 1.0, 1.1]

# Rate at t=1.0 (with 1.0s window):
# Firings in window [0.0, 1.0]: 0.1, 0.3, 0.5, 0.6, 0.8, 1.0 = 6 firings
# Rate = 6 / 1.0 = 6.0 firings/s

# Rate at t=1.1 (with 1.0s window):
# Firings in window [0.1, 1.1]: 0.3, 0.5, 0.6, 0.8, 1.0, 1.1 = 6 firings
# Rate = 6 / 1.0 = 6.0 firings/s
```

---

## Performance Considerations

### Data Management

```python
class SimulationDataCollector:
    def __init__(self):
        self.max_data_points = 10000
        self.downsample_threshold = 8000
    
    def on_simulation_step(self, controller, time):
        """Collect data with automatic downsampling."""
        for place in controller.model.places:
            data = self.place_data[place.id]
            data.append((time, place.tokens))
            
            # Downsample if too many points
            if len(data) > self.downsample_threshold:
                # Keep every 2nd point
                self.place_data[place.id] = data[::2]
```

### Plot Update Throttling

```python
class AnalysisPlotPanel:
    def __init__(self, object_type, data_collector):
        # ...
        self.needs_update = False
        self.update_interval = 100  # ms
        
        # Schedule periodic updates
        GLib.timeout_add(self.update_interval, self._periodic_update)
    
    def _periodic_update(self):
        """Throttled plot update."""
        if self.needs_update and self.selected_objects:
            self.update_plot()
            self.needs_update = False
        return True
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_rate_calculator.py
def test_token_rate_calculation():
    """Test token rate calculation."""
    data = [(0.0, 10), (0.1, 12), (0.2, 15)]
    
    calc = RateCalculator()
    rate = calc.calculate_token_rate(data, time_window=0.1)
    
    # At t=0.2, looking back 0.1s: (15-12)/(0.2-0.1) = 30 tokens/s
    assert abs(rate - 30.0) < 0.01

def test_firing_rate_calculation():
    """Test firing rate calculation."""
    firing_times = [0.1, 0.3, 0.5, 0.6, 0.8]
    
    calc = RateCalculator()
    rate = calc.calculate_firing_rate(firing_times, 1.0, time_window=1.0)
    
    # 5 firings in 1.0s window = 5.0 firings/s
    assert abs(rate - 5.0) < 0.01
```

---

## Success Criteria

1. ✅ Place tab plots token consumption/production rate
2. ✅ Transition tab plots firing rate
3. ✅ Rates calculated correctly with configurable time windows
4. ✅ Real-time updates during simulation
5. ✅ Clear visualization with proper labels and legends
6. ✅ Selection via context menu works
7. ✅ Selection via search works
8. ✅ Clear button resets everything
9. ✅ Performance acceptable with 10+ objects
10. ✅ Code organized under `src/shypn/analyses/`

---

## Next Steps

1. Start with Phase 1: Create data collection infrastructure
2. Implement rate calculation utilities
3. Build base plotting panel
4. Add place-specific rate plotting
5. Add transition-specific rate plotting
6. Integrate selection mechanisms
7. Test and refine

Ready to begin implementation! 🚀
