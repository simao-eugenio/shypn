# Time Abstractions in Simulation: Research & Implementation Guide

## Executive Summary

This document analyzes the three distinct time concepts in simulation systems and their implications for simulation control, visualization, and user understanding. It provides implementation recommendations for the shypn simulator.

---

## The Three Times: Conceptual Framework

### 1. **Real-World Time (Physical Time, τ_real)**
The actual time scale of the phenomenon being modeled.

**Examples**:
- **Biochemical reactions**: milliseconds to seconds (enzyme kinetics)
- **Cell cycles**: hours to days (cell division, protein synthesis)
- **Metabolic pathways**: seconds to minutes (glucose metabolism)
- **Population dynamics**: days to years (bacterial growth)
- **Ecological systems**: years to centuries (species interactions)

**Characteristics**:
- Fixed by nature/physics
- Independent of computation
- May span vastly different scales (nanoseconds to millennia)
- Often non-uniform (fast/slow phases)

---

### 2. **Simulation Time (Logical Time, τ_sim)**
The time variable advanced by the simulation algorithm.

**Examples**:
- **Discrete-event**: Advances by event occurrence (t = 0, 0.5, 1.7, 3.2, ...)
- **Time-stepped**: Advances by fixed increments (t = 0, 0.1, 0.2, 0.3, ...)
- **Continuous**: Advances with ODE integration (variable step size)
- **Hybrid**: Mixes discrete events and continuous integration

**Characteristics**:
- Controlled by simulation algorithm
- May be non-uniform (adaptive step sizing)
- Can run faster or slower than real-world time
- Decoupled from wall-clock time
- **Key Property**: τ_sim represents the "when" in the modeled system

---

### 3. **Visualization Time (Display Time, τ_viz)**
The time axis used for plotting and data presentation.

**Examples**:
- **Same as simulation**: Plot every simulation step
- **Resampled**: Interpolate to uniform intervals for display
- **Aggregated**: Show moving averages, windows
- **Multi-scale**: Logarithmic axes, zoom levels

**Characteristics**:
- Controlled by user/visualization system
- May be resampled for display purposes
- Can be transformed (log scale, normalized)
- Affects user perception and interpretation

---

## Mathematical Relationships

### Time Scale Mappings

```
Real-World Time → Simulation Time → Visualization Time
     τ_real     →      τ_sim      →      τ_viz

Transformations:
1. τ_sim = f(τ_real) = τ_real / time_scale
   - time_scale = 1.0: real-time simulation
   - time_scale = 1000.0: 1 sim second = 1000 real seconds
   
2. τ_viz = g(τ_sim) = resample/interpolate(τ_sim)
   - May involve: smoothing, decimation, interpolation
```

### Example: Enzyme Kinetics

```python
# Real-world: Reaction completes in 10 milliseconds
τ_real = 0.010 seconds

# Simulation: Model at 1000x slower for numerical stability
time_scale = 1000.0
τ_sim = τ_real * time_scale = 10.0 seconds

# Visualization: Show at 100ms intervals regardless of sim steps
τ_viz = linspace(0, 10, 100)  # 100 uniform points
```

---

## Research: Simulation Time Concepts in Literature

### 1. **Discrete-Event Simulation (DES)**

**Reference**: Banks et al., "Discrete-Event System Simulation" (2010)

**Key Concepts**:
- **Event Calendar**: Ordered list of future events
- **Next-Event Time Advance**: Jump directly to next event
- **Simulation Clock**: τ_sim = t_next_event

**Petri Net Application**:
```python
# Timed Petri Net (TPN) - Merlin & Farber (1976)
# Transitions have [earliest, latest] firing windows
# Time advances to next scheduled firing

while event_calendar.not_empty():
    event = event_calendar.pop()
    τ_sim = event.time  # Jump to event time
    fire_transition(event.transition)
    schedule_new_events()
```

**Time Scale Issues**:
- Events may cluster (multiple firings at same time)
- Large gaps between events (idle periods)
- Visualization needs interpolation for smooth plots

---

### 2. **Time-Stepped Simulation**

**Reference**: Gillespie, "Exact Stochastic Simulation of Coupled Chemical Reactions" (1977)

**Key Concepts**:
- **Fixed Time Step (Δt)**: Advance by constant increment
- **State Update**: Evaluate all changes per step
- **Synchronous**: All components update together

**Petri Net Application**:
```python
# Fixed time step hybrid simulation
dt = 0.1  # Time step in simulation units

while τ_sim < τ_max:
    # 1. Fire immediate transitions (τ = 0)
    exhaust_immediate_transitions()
    
    # 2. Check timed transitions
    for t in timed_transitions:
        if t.enabled_time + t.delay <= τ_sim:
            fire(t)
    
    # 3. Integrate continuous transitions
    for t in continuous_transitions:
        integrate_flow(t, dt)
    
    τ_sim += dt
```

**Time Scale Issues**:
- Δt must match real-world dynamics
- Too large: Miss events, numerical instability
- Too small: Excessive computation
- **Stiff systems**: Multiple time scales require adaptive Δt

---

### 3. **Hybrid Simulation (Discrete + Continuous)**

**Reference**: Henzinger, "The Theory of Hybrid Automata" (1996)

**Key Concepts**:
- **Mode Switches**: Discrete state changes
- **Flow Equations**: Continuous ODEs within modes
- **Guard Conditions**: Triggers for mode switches

**Petri Net Application**:
```python
# Hybrid Petri Nets (Continuous + Discrete)
# David & Alla, "Discrete, Continuous, and Hybrid Petri Nets" (2005)

while τ_sim < τ_max:
    # Discrete phase (zero time)
    changed = True
    while changed:
        changed = fire_any_enabled_discrete()
    
    # Continuous phase (time advances)
    integrate_continuous_flows(dt)
    τ_sim += dt
```

**Time Scale Issues**:
- **Fast/slow dynamics**: Enzyme binding (ms) vs. gene expression (hours)
- **Time scale separation**: Multiple Δt values needed
- **Stiffness**: Jacobian eigenvalues span orders of magnitude

---

### 4. **Stochastic Simulation (Gillespie Algorithm)**

**Reference**: Gillespie (1977), Gibson & Bruck (2000)

**Key Concepts**:
- **Reaction Propensities**: α_i = rate × reactant combinations
- **Time-to-Next-Reaction**: τ = -ln(rand)/Σα_i
- **Variable Time Step**: Adaptive based on kinetics

**Petri Net Application**:
```python
# Stochastic Petri Net (FSPN - Fluid Stochastic)
# Time advances by exponentially distributed intervals

while τ_sim < τ_max:
    # Calculate propensities (rates)
    propensities = [calc_propensity(t) for t in transitions]
    total = sum(propensities)
    
    # Sample time to next event
    τ_next = τ_sim + exponential(1.0 / total)
    
    # Sample which transition fires
    transition = weighted_choice(transitions, propensities)
    
    τ_sim = τ_next
    fire(transition)
```

**Time Scale Issues**:
- **Rare events**: Long wait times between firings
- **Fast reactions**: Many events in short time
- **Averaging**: Need τ_viz ≫ τ_sim for smooth plots

---

## Real-World Examples: Time Scale Problems

### Example 1: Glycolysis Pathway

**Real-World Times**:
- Glucose phosphorylation: ~10 ms (fast enzyme)
- Pyruvate production: ~1-2 seconds (pathway completion)
- ATP concentration change: continuous over seconds

**Simulation Challenges**:
```
τ_real (ms):  [0.01, 10, 100, 1000, 2000]
τ_sim:        Need uniform step dt = 0.01s to capture fast reactions
              → 200,000 steps for 2 seconds!
              
Solution 1: Time scaling
  τ_sim = τ_real * 100  (1 real-ms = 100 sim-units)
  dt = 1 sim-unit = 10 μs real-time
  
Solution 2: Multi-rate
  Fast reactions: dt = 0.001s
  Slow reactions: dt = 0.1s
  Use event scheduling for transitions
```

**Visualization**:
```python
# τ_viz: Show at 10 Hz for animation (100 ms intervals)
# But simulation has 200,000 steps
# → Decimate: Show every 20,000th step
# → Or: Interpolate to exact 10 Hz grid

τ_viz = np.linspace(0, 2.0, 20)  # 20 frames = 10 Hz
concentration_viz = interpolate(τ_sim, concentration_sim, τ_viz)
```

---

### Example 2: Cell Cycle Simulation

**Real-World Times**:
- Checkpoint decision: ~minutes (protein signaling)
- DNA replication: ~6-8 hours
- Cell division: ~24 hours (total cycle)

**Simulation Challenges**:
```
τ_real: [0, 360, 720, ... 86400] seconds (24 hours)
dt_needed: 1-60 seconds (depending on phase)

Problem: Adaptive time step
- Checkpoints: dt = 1s (need resolution)
- S-phase: dt = 60s (slow, uniform)

Solution: Event-driven + time-stepped hybrid
```

**Visualization**:
```python
# τ_viz: Show in hours, not seconds
τ_viz_hours = τ_sim / 3600.0

# Use log scale for early events
if show_details:
    ax.set_xscale('log')  # First minutes in detail
```

---

## Implementation Recommendations for shypn

### 1. **Simulation Controller Settings**

```python
class SimulationController:
    """Enhanced with time scale management."""
    
    def __init__(self, model):
        # Time management
        self.time = 0.0              # Current simulation time
        self.time_scale = 1.0        # τ_real / τ_sim conversion
        self.time_units = "seconds"  # Real-world units
        
        # Step control
        self.dt = 0.1                # Base time step
        self.adaptive_dt = False     # Enable adaptive stepping
        self.dt_min = 0.001          # Minimum step size
        self.dt_max = 1.0            # Maximum step size
        
        # Scheduling
        self.use_event_calendar = False  # For discrete-event mode
        self.event_calendar = []         # Sorted event list
```

#### Settings UI:

```
┌─ Simulation Settings ────────────────────┐
│                                          │
│ Time Configuration:                      │
│   Real-World Time Units: [seconds ▼]    │
│     (ms, seconds, minutes, hours, days)  │
│                                          │
│   Time Scale Factor: [____1.0____]      │
│     (1.0 = real-time, >1 = compressed)   │
│                                          │
│ Step Control:                            │
│   Base Time Step (dt): [____0.1____]    │
│   Adaptive Stepping: [ ] Enable         │
│     Min dt: [_0.001_]  Max dt: [_1.0_]  │
│                                          │
│ Algorithm:                               │
│   ○ Time-Stepped (Fixed dt)             │
│   ○ Event-Driven (Variable dt)          │
│   ● Hybrid (Fixed dt + Events)          │
│                                          │
└─────────────────────────────────────────┘
```

---

### 2. **Visualization Time Management**

```python
class DataCollector:
    """Enhanced with visualization time control."""
    
    def __init__(self):
        # Data storage
        self.time_points = []        # τ_sim values
        self.data_points = {}        # {place_id: [token_values]}
        
        # Visualization settings
        self.viz_sample_rate = 10.0  # Hz (samples per sim-second)
        self.viz_interpolation = "linear"  # linear, cubic, step
        self.viz_time_transform = None     # None, log, sqrt
        
    def get_visualization_data(self, t_start=None, t_end=None):
        """Resample data for visualization."""
        # Get raw simulation data
        t_sim = np.array(self.time_points)
        
        # Create uniform visualization time grid
        if t_start is None:
            t_start = t_sim[0]
        if t_end is None:
            t_end = t_sim[-1]
            
        # Determine sample points
        n_samples = int((t_end - t_start) * self.viz_sample_rate)
        t_viz = np.linspace(t_start, t_end, n_samples)
        
        # Interpolate data
        data_viz = {}
        for place_id, values in self.data_points.items():
            if self.viz_interpolation == "step":
                # Step function (hold previous value)
                data_viz[place_id] = interp_step(t_sim, values, t_viz)
            elif self.viz_interpolation == "linear":
                # Linear interpolation
                data_viz[place_id] = np.interp(t_viz, t_sim, values)
            elif self.viz_interpolation == "cubic":
                # Cubic spline
                from scipy.interpolate import CubicSpline
                cs = CubicSpline(t_sim, values)
                data_viz[place_id] = cs(t_viz)
        
        return t_viz, data_viz
```

#### Visualization Settings UI:

```
┌─ Plot Settings ──────────────────────────┐
│                                          │
│ Time Axis:                               │
│   Display Units: [seconds ▼]            │
│   Transform: ○ Linear  ○ Logarithmic    │
│                                          │
│ Sampling:                                │
│   Visualization Rate: [___10___] Hz     │
│   Interpolation: [Linear ▼]             │
│     (Step, Linear, Cubic Spline)         │
│                                          │
│ Range:                                   │
│   Start Time: [___0.0___]               │
│   End Time:   [___10.0__] (auto)        │
│                                          │
│ Display:                                 │
│   [✓] Show simulation steps (markers)    │
│   [✓] Show interpolated curve            │
│   [ ] Show confidence intervals          │
│                                          │
└─────────────────────────────────────────┘
```

---

### 3. **Matplotlib Formatting Based on Time Scale**

```python
class PlotFormatter:
    """Format plots based on time scale characteristics."""
    
    @staticmethod
    def format_time_axis(ax, t_min, t_max, time_units="seconds", 
                         time_scale=1.0, auto_scale=True):
        """
        Format time axis with appropriate units and ticks.
        
        Args:
            ax: Matplotlib axis
            t_min, t_max: Time range in simulation units
            time_units: Real-world time units
            time_scale: Conversion factor
            auto_scale: Automatically choose best units
        """
        # Convert to real-world time
        t_real_min = t_min / time_scale
        t_real_max = t_max / time_scale
        duration = t_real_max - t_real_min
        
        # Auto-select best units
        if auto_scale:
            if duration < 1e-6:  # < 1 microsecond
                display_units = "nanoseconds"
                scale_factor = 1e9
            elif duration < 1e-3:  # < 1 millisecond
                display_units = "microseconds"
                scale_factor = 1e6
            elif duration < 1:  # < 1 second
                display_units = "milliseconds"
                scale_factor = 1e3
            elif duration < 60:  # < 1 minute
                display_units = "seconds"
                scale_factor = 1.0
            elif duration < 3600:  # < 1 hour
                display_units = "minutes"
                scale_factor = 1.0 / 60
            elif duration < 86400:  # < 1 day
                display_units = "hours"
                scale_factor = 1.0 / 3600
            else:  # >= 1 day
                display_units = "days"
                scale_factor = 1.0 / 86400
        else:
            display_units = time_units
            scale_factor = 1.0
        
        # Scale axis
        t_display_min = t_real_min * scale_factor
        t_display_max = t_real_max * scale_factor
        
        ax.set_xlim(t_display_min, t_display_max)
        ax.set_xlabel(f"Time ({display_units})")
        
        # Smart tick placement
        PlotFormatter._set_smart_ticks(ax, t_display_min, t_display_max)
    
    @staticmethod
    def _set_smart_ticks(ax, t_min, t_max):
        """Set tick marks at nice intervals."""
        duration = t_max - t_min
        
        # Determine nice interval
        if duration < 1:
            # Sub-second: 0.1, 0.2, 0.5
            interval = PlotFormatter._nice_interval(duration, n_ticks=5)
        elif duration < 60:
            # Seconds: 1, 2, 5, 10
            interval = PlotFormatter._nice_interval(duration, n_ticks=6)
        elif duration < 3600:
            # Minutes: 1, 5, 10, 15, 30
            interval = PlotFormatter._choose_from([1, 5, 10, 15, 30], 
                                                   duration / 6)
        else:
            # Hours/days: powers of 10
            interval = PlotFormatter._nice_interval(duration, n_ticks=10)
        
        ticks = np.arange(
            np.ceil(t_min / interval) * interval,
            t_max,
            interval
        )
        ax.set_xticks(ticks)
    
    @staticmethod
    def format_concentration_axis(ax, c_min, c_max, units="M"):
        """Format concentration/token axis with scientific notation if needed."""
        # Use scientific notation for very small/large values
        if c_max < 1e-3 or c_max > 1e4:
            ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
        
        ax.set_ylabel(f"Concentration ({units})")
        ax.set_ylim(c_min - 0.1 * (c_max - c_min), 
                    c_max + 0.1 * (c_max - c_min))
```

---

### 4. **Multi-Scale Visualization**

For phenomena with multiple time scales (e.g., glycolysis):

```python
class MultiScalePlot:
    """Create multi-panel plots for different time scales."""
    
    @staticmethod
    def create_multi_scale_view(data, breakpoints):
        """
        Create subplot panels for different time scales.
        
        Args:
            data: Time series data
            breakpoints: List of time points defining scale changes
                        e.g., [0.01, 1.0, 60.0] for fast/medium/slow
        
        Example:
            ┌─────────────────┬─────────────────┐
            │ Fast (0-10ms)   │ Medium (0-1s)   │
            │ Linear scale    │ Linear scale    │
            ├─────────────────┴─────────────────┤
            │ Slow (0-60s)                      │
            │ Log scale for detail              │
            └───────────────────────────────────┘
        """
        n_panels = len(breakpoints) - 1
        fig, axes = plt.subplots(1, n_panels, figsize=(12, 4))
        
        for i, (t_start, t_end) in enumerate(zip(breakpoints[:-1], 
                                                   breakpoints[1:])):
            ax = axes[i] if n_panels > 1 else axes
            
            # Filter data for this time range
            mask = (data['time'] >= t_start) & (data['time'] <= t_end)
            t_panel = data['time'][mask]
            v_panel = data['values'][mask]
            
            ax.plot(t_panel, v_panel)
            
            # Format based on scale
            PlotFormatter.format_time_axis(ax, t_start, t_end)
            
            # Use log scale for wide ranges
            if (t_end / t_start) > 100:
                ax.set_xscale('log')
                ax.set_title(f"Time Scale: {t_start} - {t_end} (log)")
            else:
                ax.set_title(f"Time Scale: {t_start} - {t_end}")
        
        plt.tight_layout()
        return fig, axes
```

---

## Configuration Recommendations

### Preset Configurations for Common Scenarios

```python
SIMULATION_PRESETS = {
    "enzyme_kinetics": {
        "time_units": "milliseconds",
        "dt": 0.01,  # 10 μs
        "time_scale": 1000.0,  # 1 real-ms = 1000 sim-units
        "viz_sample_rate": 1000.0,  # 1 kHz
        "viz_interpolation": "cubic",
        "description": "Fast enzyme reactions (ms scale)"
    },
    
    "metabolic_pathway": {
        "time_units": "seconds",
        "dt": 0.01,  # 10 ms
        "time_scale": 1.0,
        "viz_sample_rate": 100.0,  # 100 Hz
        "viz_interpolation": "linear",
        "description": "Metabolic pathways (seconds scale)"
    },
    
    "cell_cycle": {
        "time_units": "hours",
        "dt": 0.1,  # 6 minutes
        "time_scale": 1.0,
        "viz_sample_rate": 0.1,  # Every 10 hours
        "viz_interpolation": "step",
        "adaptive_dt": True,
        "dt_min": 0.01,  # 36 seconds
        "dt_max": 1.0,   # 1 hour
        "description": "Cell cycle (hours to days)"
    },
    
    "stochastic_reactions": {
        "time_units": "seconds",
        "dt": "event-driven",  # Variable
        "time_scale": 1.0,
        "viz_sample_rate": 10.0,  # 10 Hz
        "viz_interpolation": "step",
        "use_event_calendar": True,
        "description": "Stochastic simulation (Gillespie)"
    }
}
```

---

## Summary: Implementation Checklist

### Core Features to Implement

1. **Simulation Controller**:
   - [ ] Add `time_scale` parameter
   - [ ] Add `time_units` string
   - [ ] Implement adaptive time stepping
   - [ ] Add event calendar for discrete events
   - [ ] Support hybrid (discrete + continuous) stepping

2. **Data Collection**:
   - [ ] Store raw (τ_sim, data) pairs
   - [ ] Implement `get_visualization_data()` with resampling
   - [ ] Add interpolation options (step, linear, cubic)
   - [ ] Support time range selection

3. **Visualization**:
   - [ ] Auto-scale time units for display
   - [ ] Smart tick placement
   - [ ] Multi-scale plots (panels for different ranges)
   - [ ] Scientific notation for concentrations
   - [ ] Log scale option for wide time ranges

4. **UI/Settings**:
   - [ ] Time configuration panel
   - [ ] Preset configurations dropdown
   - [ ] Visualization settings panel
   - [ ] Real-time vs simulation time display

5. **Documentation**:
   - [ ] User guide: Understanding time scales
   - [ ] Examples: Enzyme kinetics, cell cycle, stochastic
   - [ ] Best practices: Choosing dt, time_scale

---

## References

### Foundational Papers

1. **Merlin & Farber (1976)**: "Recoverability of Communication Protocols"
   - Original Time Petri Net (TPN) definition
   
2. **Gillespie (1977)**: "Exact Stochastic Simulation of Coupled Chemical Reactions"
   - Stochastic simulation algorithm (SSA)
   
3. **David & Alla (2005)**: "Discrete, Continuous, and Hybrid Petri Nets"
   - Hybrid Petri Net formalism
   
4. **Banks et al. (2010)**: "Discrete-Event System Simulation"
   - Comprehensive DES methods

### Numerical Methods

5. **Hairer & Wanner (1996)**: "Solving Ordinary Differential Equations II: Stiff and Differential-Algebraic Problems"
   - Stiff ODE solvers for continuous systems
   
6. **Ascher & Petzold (1998)**: "Computer Methods for Ordinary Differential Equations"
   - Numerical integration techniques

### Systems Biology Applications

7. **Wilkinson (2006)**: "Stochastic Modelling for Systems Biology"
   - Multi-scale biological simulation
   
8. **Klipp et al. (2009)**: "Systems Biology: A Textbook"
   - Time scales in biological systems

---

## Conclusion

The distinction between real-world time (τ_real), simulation time (τ_sim), and visualization time (τ_viz) is fundamental to effective simulation design. By providing explicit control over these three time concepts, shypn can:

1. **Accurately model** phenomena across vastly different time scales
2. **Efficiently simulate** using appropriate step sizes and algorithms
3. **Clearly visualize** results in user-friendly time units and scales

The recommended implementation provides:
- Flexible time scale management
- Adaptive algorithms for multi-scale systems
- Intelligent visualization resampling
- User-friendly preset configurations

This approach enables shypn to handle everything from fast enzyme reactions (microseconds) to slow ecological dynamics (years) within a unified framework.

---

**Next Steps**:
1. Implement time_scale and time_units in SimulationController
2. Add visualization resampling to DataCollector
3. Create PlotFormatter with auto-scaling
4. Design simulation settings UI
5. Create example models demonstrating time scale handling
6. Write user documentation with tutorials

**Status**: Research complete, ready for implementation
**Date**: 2025-10-08
