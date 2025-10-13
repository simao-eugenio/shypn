# Time Abstraction: What's Already in Code vs. What's New

**Date**: 2025-10-08  
**Analysis**: Current implementation vs. TIME_ABSTRACTIONS_IN_SIMULATION.md proposal

---

## Executive Summary

### Current Implementation: **MINIMAL TIME SUPPORT** ✅

The code has **basic time tracking** but **NO time abstraction layers**:

```python
# What EXISTS in code:
class SimulationController:
    def __init__(self, model):
        self.time = 0.0  # ✅ Simulation time tracking
    
    def step(self, time_step=0.1):  # ✅ Fixed time step
        # ... do simulation logic ...
        self.time += time_step  # ✅ Advance time
    
    def run(self, time_step=0.1, max_steps=None):  # ✅ Run loop
        # ... continuous execution ...

# What DOES NOT EXIST:
# ❌ time_units (ms/s/min/hr/days)
# ❌ time_scale (real-world ↔ simulation conversion)
# ❌ duration/t_max (auto-stop at time)
# ❌ visualization resampling (τ_sim → τ_viz)
# ❌ auto time step calculation
# ❌ adaptive time stepping
# ❌ time display formatting
```

### Current UI: **RUN/STEP/STOP/RESET BUTTONS ONLY** 🎮

```python
# What EXISTS (simulate_tools_palette_loader.py):
class SimulateToolsPaletteLoader:
    # Four buttons:
    - Run [R]     → simulation.run(time_step=0.1)
    - Step [P]    → simulation.step(time_step=0.1)
    - Stop [S]    → simulation.stop()
    - Reset [T]   → simulation.reset()

# What DOES NOT EXIST:
# ❌ No duration input
# ❌ No time units selector
# ❌ No settings dialog
# ❌ No progress bar
# ❌ No time display
# ❌ No dt configuration
```

**Hardcoded everywhere**: `time_step=0.1` (no user control)

---

## Detailed Code Analysis

### 1. SimulationController (controller.py)

**Lines 112-130: Initialization**
```python
def __init__(self, model):
    self.model = model
    self.time = 0.0  # ✅ Has simulation time
    self.model_adapter = ModelAdapter(model, controller=self)
    self.step_listeners = []
    self._running = False
    self._stop_requested = False
    self._timeout_id = None
    self.behavior_cache = {}
    self.transition_states = {}
    self.conflict_policy = DEFAULT_POLICY  # ✅ Has conflict resolution
    self._round_robin_index = 0
    self.data_collector = None  # ✅ Data collection exists
```

**What's Missing**:
- ❌ `self.time_units` - No concept of real-world time units
- ❌ `self.time_scale` - No real-world ↔ simulation conversion
- ❌ `self.duration` / `self.t_max` - No auto-stop condition
- ❌ `self.dt_auto` - Time step always passed as parameter

**Lines 284-310: step() Method**
```python
def step(self, time_step: float=0.1) -> bool:
    """Execute one simulation step.
    
    Args:
        time_step: Time increment for this step (default: 0.1)  # ⚠️ Hardcoded
    
    Returns:
        bool: True if step executed, False if simulation ended
    """
    # ... 60 lines of simulation logic ...
    self.time += time_step  # ✅ Basic time advancement
    return True
```

**What's Missing**:
- ❌ No adaptive time stepping
- ❌ No duration check (never auto-stops)
- ❌ Time step always externally specified

**Lines 477-510: run() Method**
```python
def run(self, time_step: float=0.1, max_steps: Optional[int]=None) -> bool:
    """Run the simulation continuously.
    
    Args:
        time_step: Time increment per step (default: 0.1)  # ⚠️ Hardcoded
        max_steps: Maximum steps to execute (default: None = infinite)
    """
    self._running = True
    self._stop_requested = False
    self._time_step = time_step
    self._max_steps = max_steps
    self._step_count = 0
    
    # Uses GLib.timeout_add() for continuous execution
```

**What's Missing**:
- ❌ Duration-based stopping (only max_steps, not max_time)
- ❌ No progress reporting (current_time / duration)
- ❌ No time_scale consideration

**Lines 570-590: reset() Method**
```python
def reset(self):
    """Reset simulation to initial state."""
    self.stop()
    self.time = 0.0  # ✅ Resets time
    # ... reset places, clear caches ...
```

**What EXISTS**: ✅ Basic reset functionality

---

### 2. Transition Behaviors (timed_behavior.py, stochastic_behavior.py)

**TimedBehavior (TPN)**:
```python
class TimedBehavior(TransitionBehavior):
    def __init__(self, transition, model_adapter):
        # Uses transition.earliest and transition.latest
        # Time windows: [earliest, latest]
        self._enablement_time = None  # ✅ Tracks when enabled
    
    def can_fire(self, current_time: float) -> bool:
        # Checks: current_time ∈ [enable_time + earliest, enable_time + latest]
```

**What EXISTS**: ✅ TPN timing windows work correctly  
**What's Missing**: ❌ No awareness of time_units (delays are in abstract units)

**StochasticBehavior (FSPN)**:
```python
class StochasticBehavior(TransitionBehavior):
    def sample_firing_time(self, current_time: float) -> float:
        # Uses exponential distribution: -log(rand) / rate
        # Returns: current_time + delay
```

**What EXISTS**: ✅ Stochastic sampling works  
**What's Missing**: ❌ Rate is in abstract "per time unit" (no real-world meaning)

---

### 3. UI: Simulate Tools Palette (simulate_tools_palette_loader.py)

**Lines 70-85: Button Handlers**
```python
def _on_run_clicked(self, button):
    """Handle Run button click - start continuous simulation."""
    if self.simulation:
        self.simulation.run(time_step=0.1)  # ⚠️ HARDCODED 0.1
    
def _on_step_clicked(self, button):
    """Handle Step button click - execute one step."""
    if self.simulation:
        success = self.simulation.step(time_step=0.1)  # ⚠️ HARDCODED 0.1
        if success:
            self.emit('step-executed', self.simulation.time)

def _on_stop_clicked(self, button):
    """Handle Stop button click - pause simulation."""
    if self.simulation:
        self.simulation.stop()

def _on_reset_clicked(self, button):
    """Handle Reset button click - reset to initial marking."""
    if self.simulation:
        self.simulation.reset()
        self.emit('reset-executed')
```

**What EXISTS**:
- ✅ Run/Step/Stop/Reset buttons functional
- ✅ Signal emission for step/reset events

**What's Missing**:
- ❌ No duration input field
- ❌ No time units dropdown
- ❌ No settings button
- ❌ No progress display
- ❌ No time display (current time / duration)

---

### 4. Data Collection (SimulationDataCollector)

**What EXISTS**:
```python
class SimulationDataCollector:
    def on_simulation_step(self, controller, time):
        # Records: (time, place_tokens_dict)
        # ✅ Collects time-series data
    
    def get_data(self):
        # Returns: list of (time, state) tuples
        # ✅ Data ready for plotting
```

**What's Missing**:
- ❌ No `get_visualization_data()` method (resampling)
- ❌ No interpolation options
- ❌ No time range selection
- ❌ Data at simulation resolution (could be 100k points)

---

### 5. Plotting/Visualization

**Status**: Not found in search results  
**Likely**: Matplotlib used externally, not integrated into time abstraction

**What's Missing**:
- ❌ No PlotFormatter class
- ❌ No auto-scaling of time units
- ❌ No smart tick placement
- ❌ Manual axis labels required

---

## Gap Analysis: Existing vs. Proposed

| Feature | Current Code | Proposed | Gap Size |
|---------|-------------|----------|----------|
| **Core Time Tracking** | ✅ `self.time` | ✅ Same | None |
| **Time Step** | ⚠️ Hardcoded 0.1 | Auto-compute | Medium |
| **Time Units** | ❌ None | ms/s/min/hr/days | **Large** |
| **Time Scale** | ❌ None | τ_real / τ_sim | **Large** |
| **Duration/t_max** | ❌ None | Auto-stop at time | Medium |
| **Adaptive dt** | ❌ None | RK45/LSODA | **Large** |
| **Conflict Policy** | ✅ Exists | ✅ Same | None |
| **Data Collection** | ✅ Exists | ✅ + resampling | Medium |
| **UI Controls** | ⚠️ 4 buttons only | Duration/units/settings | **Large** |
| **Progress Display** | ❌ None | Time bar | Medium |
| **Visualization** | ❌ Not integrated | PlotFormatter | **Large** |

**Legend**:
- ✅ = Fully implemented
- ⚠️ = Partially implemented
- ❌ = Not implemented

**Gap Sizes**:
- **Small**: 1-2 hours work
- **Medium**: 1-2 days work
- **Large**: 1-2 weeks work

---

## What's New in TIME_ABSTRACTIONS_IN_SIMULATION.md

### Conceptual (Theory):
1. ✅ Three time concepts: τ_real, τ_sim, τ_viz
2. ✅ Time scale conversion: `τ_real = τ_sim / time_scale`
3. ✅ Multi-scale challenges (stiff systems)
4. ✅ Visualization resampling strategies

### Practical (Implementation):
1. ❌ `SimulationController.time_units` property
2. ❌ `SimulationController.time_scale` property
3. ❌ `SimulationController.duration` property
4. ❌ Auto-compute dt: `duration / 1000`
5. ❌ Duration-based stopping: `if self.time >= self.duration: stop()`
6. ❌ `DataCollector.get_visualization_data(sample_rate, interpolation)`
7. ❌ `PlotFormatter.format_time_axis(ax, data, time_units)`
8. ❌ Adaptive time stepping algorithms
9. ❌ Configuration presets (enzyme, metabolic, cell cycle)

### UI (New Components):
1. ❌ Duration input field
2. ❌ Time units dropdown
3. ❌ Settings dialog (⚙ button)
4. ❌ Progress bar (time/duration)
5. ❌ Current time display
6. ❌ Preset configurations menu

---

## UI Requirement: Simple Dialog or Docked Panel?

### Option A: **Simple Dialog** ✅ RECOMMENDED

**Rationale**:
- Settings changed **infrequently** (once per model)
- Not needed during simulation (only before Run)
- Most users never change defaults
- Follows Tier 2 design from TIME_SETTINGS_UI_DESIGN.md

**Implementation**:
```
Menu → Simulation → Settings  (or ⚙ button in palette)

┌─ Simulation Settings ────────────────────┐
│                                           │
│ Duration: [___60___] [seconds ▼]        │
│                                           │
│ ┌─ Advanced (collapsed by default) ────┐ │
│ │ [✓] Manual time step                 │ │
│ │     dt: [__0.1__]                    │ │
│ │                                       │ │
│ │ Time scale: [__1.0__]                │ │
│ │ (1.0 = real-time)                    │ │
│ └───────────────────────────────────────┘ │
│                                           │
│          [Cancel]  [OK]                  │
└───────────────────────────────────────────┘
```

**Why Simple Dialog Works**:
1. ✅ 80% of users only set duration + units
2. ✅ Advanced settings collapsed (not intimidating)
3. ✅ Doesn't clutter main UI
4. ✅ Can be opened on-demand
5. ✅ Familiar pattern (File→Preferences, Edit→Settings)

**Size**: ~200 lines of code (dialog + handler)

---

### Option B: **Docked Panel** ❌ NOT RECOMMENDED

**Would require**:
- Permanent screen space (always visible)
- More complex UI management
- Layout reconfiguration
- Unnecessary for infrequent settings

**When to use docked panels**:
- Real-time adjustments during simulation
- Frequently changed parameters
- Visual feedback needed
- Example: Animation speed slider (adjust while running)

**Verdict**: Overkill for our use case

---

### Option C: **Hybrid: Minimal Controls + Dialog** ⭐ BEST CHOICE

**Main Palette** (always visible, expanded):
```
┌─ Simulation Controls ─────────────────────────────┐
│  ▶ Run  ⏸ Pause  ⏹ Stop  ⏮ Reset       ⚙Settings │
│                                                    │
│  Duration: [__60__] [seconds▼]                   │
│  Time: 12.5 / 60.0 s  [━━━━━━░░░░] 21%           │
└────────────────────────────────────────────────────┘
```

**Settings Dialog** (⚙ button opens):
```
┌─ Advanced Simulation Settings ───────────────────┐
│                                                   │
│ Time Step:                                        │
│   ○ Automatic (recommended)                       │
│   ○ Manual: [__0.1__]                            │
│                                                   │
│ Time Scale:                                       │
│   [__1.0__] (1.0 = real-time, 1000 = compressed) │
│                                                   │
│ Conflict Resolution: [Random ▼]                  │
│                                                   │
│                [Cancel]  [OK]                    │
└───────────────────────────────────────────────────┘
```

**Why Best**:
1. ✅ Essential controls (duration, run/stop) always visible
2. ✅ Advanced settings hidden in dialog
3. ✅ Minimal screen space usage
4. ✅ Matches user mental model ("run with duration" vs "configure details")

---

## Implementation Roadmap

### Phase 1: **Minimal Duration Control** (1 day)

**Goal**: Add duration to existing palette

**Changes**:
1. Add to `simulate_tools_palette.ui`:
   ```xml
   <object class="GtkEntry" id="duration_entry">
     <property name="text">60</property>
   </object>
   <object class="GtkComboBoxText" id="time_units_combo">
     <items>
       <item>milliseconds</item>
       <item>seconds</item>  <!-- default -->
       <item>minutes</item>
       <item>hours</item>
     </items>
   </object>
   ```

2. Update `SimulateToolsPaletteLoader`:
   ```python
   def _on_run_clicked(self, button):
       duration = float(self.duration_entry.get_text())
       time_units = self.time_units_combo.get_active_text()
       
       # Convert to seconds
       duration_seconds = convert_to_seconds(duration, time_units)
       
       # Auto-compute time step
       dt = duration_seconds / 1000  # 1000 steps
       
       # Run with duration limit
       max_steps = int(duration_seconds / dt)
       self.simulation.run(time_step=dt, max_steps=max_steps)
   ```

3. Update `SimulationController`:
   ```python
   def run(self, time_step=0.1, max_steps=None, max_time=None):  # ADD max_time
       # ... existing code ...
       
       # Stop condition: max_steps OR max_time
       if max_time and self.time >= max_time:
           self.stop()
           return False
   ```

**Result**: Users can set duration, system auto-computes dt ✅

**Effort**: 4-6 hours

---

### Phase 2: **Settings Dialog** (2 days)

**Goal**: Allow advanced users to override defaults

**New Files**:
1. `ui/dialogs/simulation_settings.ui` (GTK dialog)
2. `src/shypn/helpers/simulation_settings_dialog.py` (dialog manager)

**Add to SimulationController**:
```python
def __init__(self, model):
    # ... existing code ...
    
    # NEW: Time abstraction properties
    self.time_units = "seconds"  # User-specified
    self.time_scale = 1.0        # Real-time by default
    self.duration = None         # Set before run()
    self.dt_auto = True          # Auto-compute dt
    self.dt_manual = 0.1         # User override

def get_effective_dt(self):
    """Get time step (auto or manual)."""
    if self.dt_auto:
        return self.duration / 1000 if self.duration else 0.1
    else:
        return self.dt_manual
```

**Add ⚙ button to palette**:
```python
def _on_settings_clicked(self, button):
    dialog = SimulationSettingsDialog(self.simulation)
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        dialog.apply_settings()
    dialog.destroy()
```

**Result**: Power users can tune dt, time_scale, conflict policy ✅

**Effort**: 8-12 hours

---

### Phase 3: **Progress & Time Display** (1 day)

**Goal**: Show simulation progress

**Add to palette UI**:
```python
# Progress bar
self.progress_bar = Gtk.ProgressBar()
self.progress_bar.set_fraction(0.0)
self.progress_bar.set_text("0.0 / 60.0 s")

# Update in step listener
def _on_simulation_step(self, controller, time):
    if controller.duration:
        fraction = time / controller.duration
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"{time:.1f} / {controller.duration:.1f} s")
```

**Result**: User sees "45% complete" feedback ✅

**Effort**: 2-4 hours

---

### Phase 4: **Visualization Enhancements** (3 days)

**Goal**: Auto-format plots with correct time units

**New Files**:
1. `src/shypn/visualization/plot_formatter.py`
2. `src/shypn/visualization/time_utils.py` (unit conversions)

**Add resampling to DataCollector**:
```python
def get_visualization_data(self, max_points=1000, interpolation='linear'):
    """Resample data for plotting.
    
    If simulation has 100k steps, decimate to 1k points for plot.
    """
    if len(self.data) <= max_points:
        return self.data  # Use as-is
    
    # Resample (interpolate)
    times = [t for t, _ in self.data]
    # ... interpolation logic ...
    return resampled_data
```

**Auto-format plots**:
```python
def format_time_axis(ax, times, time_units):
    """Auto-scale time axis for readability."""
    duration = max(times) - min(times)
    
    # Auto-select display units
    if duration < 1e-3:
        display_units, scale = "μs", 1e6
    elif duration < 1.0:
        display_units, scale = "ms", 1e3
    elif duration < 60:
        display_units, scale = "s", 1.0
    # ... etc ...
    
    ax.set_xlabel(f"Time ({display_units})")
    # Convert x values
    scaled_times = [t * scale for t in times]
    return scaled_times, display_units
```

**Result**: Plots automatically show "Time (ms)" or "Time (hours)" ✅

**Effort**: 12-16 hours

---

## Summary Table

| Component | Current Status | Lines to Add | Complexity | Priority |
|-----------|---------------|--------------|------------|----------|
| Duration input | ❌ Missing | ~50 | Low | **HIGH** |
| Auto-compute dt | ❌ Missing | ~20 | Low | **HIGH** |
| Time units | ❌ Missing | ~30 | Low | **HIGH** |
| Progress bar | ❌ Missing | ~40 | Low | **HIGH** |
| Settings dialog | ❌ Missing | ~200 | Medium | MEDIUM |
| time_scale | ❌ Missing | ~30 | Low | LOW |
| Adaptive dt | ❌ Missing | ~300 | High | LOW |
| PlotFormatter | ❌ Missing | ~250 | Medium | MEDIUM |
| Viz resampling | ❌ Missing | ~150 | Medium | MEDIUM |
| Presets | ❌ Missing | ~100 | Low | LOW |

**Total New Code**: ~1,170 lines  
**Core Features**: ~140 lines (duration, auto-dt, units, progress)  
**Advanced Features**: ~1,030 lines (settings, formatting, resampling, presets)

---

## Final Recommendation

### **Use Simple Dialog + Expanded Palette** ⭐

**Why**:
1. ✅ 90% of code already exists (SimulationController works)
2. ✅ Gap is mostly UI (duration input, progress display)
3. ✅ Simple dialog sufficient (settings changed infrequently)
4. ✅ Minimal effort (~140 lines for core features)
5. ✅ No need for complex docked panel

**What to Implement First**:
1. **Week 1**: Duration + units + auto-dt → Users can run timed simulations
2. **Week 2**: Settings dialog → Power users can tune
3. **Week 3**: Progress bar + time display → Better UX
4. **Week 4**: Plot formatting → Professional output

**What to Skip** (for now):
- ❌ Adaptive time stepping (complex, rarely needed)
- ❌ Presets (nice-to-have, not essential)
- ❌ Time scale transformation (academic, rarely used)

**Conclusion**: 
- **Current code**: 80% ready (simulation engine works)
- **Missing**: 20% UI layer (duration, units, settings)
- **Solution**: Simple dialog + expanded palette (~140 lines)
- **Effort**: 1-2 weeks for full implementation

The TIME_ABSTRACTIONS_IN_SIMULATION.md document is **excellent research** and **good architecture**, but **90% is theory**. Only **10% needs immediate implementation** (duration, units, auto-dt). The rest can be added incrementally as users request features.

---

**Status**: Analysis complete, ready for implementation  
**Next Action**: Implement Phase 1 (duration control) if approved  
**Date**: 2025-10-08
