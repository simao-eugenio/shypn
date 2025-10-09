# Time Settings UI Design: User Intervention Analysis

## Problem Statement

The comprehensive time abstraction settings documented in `TIME_ABSTRACTIONS_IN_SIMULATION.md` include many parameters. **Which settings actually need user intervention?** How should we design a practical UI that balances:
- **Power**: Advanced users can tune for specific scenarios
- **Simplicity**: Beginners get sensible defaults
- **Automation**: System makes intelligent choices where possible

---

## Settings Classification

### Category 1: **AUTOMATIC** (No User Intervention Needed)

These should be handled automatically by the system:

| Setting | Why Automatic | Implementation |
|---------|---------------|----------------|
| `τ_viz` sampling rate | System calculates from plot resolution | `viz_width_pixels / duration → sample_rate` |
| Tick mark placement | Matplotlib smart defaults work well | Use matplotlib's AutoLocator |
| Scientific notation | Triggered by value magnitude | Auto-enable for |val| < 0.001 or > 10000 |
| Interpolation method | Default "linear" works for most cases | Only expose if user requests advanced |
| Display time units | Auto-scale based on duration | Auto-select ms/s/min/hr/day |

**Rationale**: These are presentation details that rarely need manual control. Auto-compute gives 95% good results.

---

### Category 2: **SEMI-AUTOMATIC** (Smart Defaults + Override)

Provide intelligent defaults but allow expert override:

| Setting | Smart Default | When User Overrides |
|---------|---------------|---------------------|
| Time step (`dt`) | Based on transition types | Fine-tuning for stiff systems |
| Time scale factor | 1.0 (real-time) | Matching specific experimental data |
| Simulation algorithm | Hybrid (discrete + continuous) | Pure discrete-event or pure time-stepped |
| Conflict resolution | Random | Deterministic testing, priority-based |

**Rationale**: 90% of users never change these, but 10% need precise control for specific models.

---

### Category 3: **USER-SPECIFIED** (Essential Configuration)

Must be user-specified for the model to be meaningful:

| Setting | Why User Must Specify | Example |
|---------|----------------------|---------|
| Real-world time units | Defines what model represents | "This model is in **milliseconds**" |
| Simulation duration (`t_max`) | How long to run | "Simulate for **60 seconds**" |
| Initial conditions | Starting state | "Start with 100 tokens in glucose" |
| Transition rates/delays | Model parameters | "Reaction rate = 2.5 /second" |

**Rationale**: These define the **semantics** of the model. No way to infer automatically.

---

## UI Design: Three-Tier Approach

### Tier 1: **Minimal UI** (80% of Users)

**Location**: Simulation control panel (always visible)

```
┌─ Simulation Controls ──────────────────────┐
│                                             │
│  ▶ Run    ⏸ Pause    ⏹ Stop    ⏮ Reset    │
│                                             │
│  Duration: [____60____] seconds [▼]        │
│            (auto-complete: 1m, 1h, 1d)     │
│                                             │
│  Time: 0.00 / 60.00 s  [━━━━━━━━░░] 45%    │
│                                             │
│  Speed: ⚡ x1  [ ± slider ]  🐢 x0.1        │
│         (animation speed, not sim accuracy)│
│                                             │
└────────────────────────────────────────────┘
```

**User Actions**:
1. Set how long to simulate (duration)
2. Choose time units from dropdown (s, ms, min, hr, days)
3. Run/pause/stop
4. Adjust animation speed (visual only, doesn't affect results)

**Everything else**: Automatic

---

### Tier 2: **Settings Dialog** (15% of Users)

**Location**: Menu → Simulation → Settings (or ⚙ button on panel)

```
┌─ Simulation Settings ─────────────────────────────┐
│                                                    │
│ ┌─ Time Configuration ──────────────────────────┐ │
│ │                                                │ │
│ │ Model Time Units: [seconds      ▼]            │ │
│ │   • milliseconds (ms)    • hours (h)          │ │
│ │   • seconds (s)          • days (d)           │ │
│ │   • minutes (min)                             │ │
│ │                                                │ │
│ │ ⚠ This defines what transition rates mean      │ │
│ │   Example: rate=2.5 with units="seconds"      │ │
│ │            means 2.5 firings per second       │ │
│ │                                                │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│ ┌─ Advanced (Optional) ─────────────────────────┐ │
│ │                                                │ │
│ │ [ ] Manual time step control                  │ │
│ │     Time step (dt): [___0.1___] (auto)       │ │
│ │                                                │ │
│ │ [ ] Time scale transformation                 │ │
│ │     Scale factor: [___1.0___]                │ │
│ │     (1.0=real-time, 1000=compressed)          │ │
│ │                                                │ │
│ │ Conflict Resolution: [Random ▼]              │ │
│ │   (When multiple transitions enabled)         │ │
│ │                                                │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│           [Cancel]  [Apply]  [OK]                 │
└───────────────────────────────────────────────────┘
```

**Collapsed by default**: Advanced section hidden unless user checks "Manual control"

**Smart behaviors**:
- Time step: Auto-calculated as `duration / 1000` (gives ~1000 steps)
- Scale factor: Defaults to 1.0 (most models don't need this)
- Conflict resolution: Random is fine for most stochastic models

---

### Tier 3: **Per-Transition Properties** (Expert Users)

**Location**: Right-click transition → Properties

```
┌─ Transition Properties: T1 ───────────────────────┐
│                                                    │
│ ┌─ General ──────────────────────────────────────┐ │
│ │ Name: [Glucose_Phosphorylation______________] │ │
│ │ Type: [Timed (TPN)            ▼]             │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│ ┌─ Timing ───────────────────────────────────────┐ │
│ │ Delay/Rate: [___2.5___] per second           │ │
│ │                                                │ │
│ │ For Timed transitions:                         │ │
│ │   Earliest: [___2.5___] Latest: [___2.5___]  │ │
│ │   (equal = deterministic, different = window) │ │
│ │                                                │ │
│ │ ℹ Time units from simulation settings: seconds │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│ ┌─ Priority (Optional) ──────────────────────────┐ │
│ │ Priority: [___0___] (higher fires first)      │ │
│ │   Used when conflict policy = "Priority"      │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│           [Cancel]  [Apply]  [OK]                 │
└───────────────────────────────────────────────────┘
```

**Per-transition settings**:
- Rate/delay (essential for timing)
- Priority (optional, only used if conflict policy set)

**Displays**: Current time units from global settings (for clarity)

---

## Visualization Settings

### Where: **Plot Settings Panel** (Right-click plot area → Settings)

```
┌─ Plot Settings ───────────────────────────────────┐
│                                                    │
│ ┌─ Time Axis ────────────────────────────────────┐ │
│ │                                                │ │
│ │ Display Units: [● Auto-scale ○ Same as model] │ │
│ │                                                │ │
│ │ If auto-scale OFF:                            │ │
│ │   Units: [seconds ▼]                          │ │
│ │                                                │ │
│ │ Scale: ○ Linear  ○ Logarithmic               │ │
│ │                                                │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│ ┌─ Data Display ─────────────────────────────────┐ │
│ │                                                │ │
│ │ [✓] Show simulation steps (as markers)        │ │
│ │ [✓] Connect with lines                        │ │
│ │ [ ] Show confidence intervals (stochastic)    │ │
│ │                                                │ │
│ │ Line interpolation: [Linear ▼]               │ │
│ │   • Step (hold value)                         │ │
│ │   • Linear (connect points)                   │ │
│ │   • Smooth (cubic spline) - can oscillate    │ │
│ │                                                │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│           [Cancel]  [Apply]  [OK]                 │
└───────────────────────────────────────────────────┘
```

**Default**: All auto (linear time, auto-units, linear interpolation)

---

## Implementation Strategy

### Phase 1: **Minimal Viable UI** (Week 1)

**Goal**: Get simulation running with minimal user friction

**Implement**:
1. ✅ Basic control panel: Run/Pause/Stop/Reset
2. ✅ Duration input with time unit dropdown
3. ✅ Progress bar
4. ✅ **Auto-compute everything else**:
   - `dt = duration / 1000`
   - `viz_sample_rate = 10 Hz` (fixed)
   - `time_scale = 1.0` (no transformation)
   - Linear interpolation
   - Auto-scale time units

**Code**:
```python
class SimulationControlPanel:
    def __init__(self):
        # User inputs (minimal)
        self.duration = 60.0  # seconds
        self.time_units = "seconds"
        
        # Auto-computed
        self.dt = self.duration / 1000  # ~1000 steps
        self.viz_sample_rate = 10.0  # 10 Hz
        self.time_scale = 1.0
        
    def on_duration_changed(self, new_duration):
        self.duration = new_duration
        self.dt = new_duration / 1000  # Re-compute
```

**UI**: Just the control panel (Tier 1)

---

### Phase 2: **Settings Dialog** (Week 2)

**Goal**: Allow power users to override defaults

**Implement**:
1. ✅ Settings dialog (⚙ button)
2. ✅ Time units dropdown (affects rate interpretation)
3. ✅ Advanced section (collapsed by default):
   - Manual `dt` checkbox + input
   - Time scale factor
   - Conflict resolution policy

**Code**:
```python
class SimulationSettingsDialog:
    def __init__(self):
        # User-visible settings
        self.time_units = "seconds"
        self.manual_dt_enabled = False
        self.dt_override = 0.1
        self.time_scale = 1.0
        self.conflict_policy = "random"
        
    def get_effective_dt(self, duration):
        if self.manual_dt_enabled:
            return self.dt_override
        else:
            return duration / 1000  # Auto
```

**UI**: Tier 1 (always visible) + Tier 2 (dialog)

---

### Phase 3: **Visualization Controls** (Week 3)

**Goal**: Flexible plotting for different analysis needs

**Implement**:
1. ✅ Plot settings panel
2. ✅ Time axis controls (auto-scale, log scale)
3. ✅ Interpolation options
4. ✅ Auto-format logic:

**Code**:
```python
class PlotSettingsPanel:
    def __init__(self):
        self.time_auto_scale = True
        self.time_display_units = "seconds"  # if not auto
        self.time_log_scale = False
        self.show_markers = True
        self.show_lines = True
        self.interpolation = "linear"  # step, linear, cubic
        
    def format_time_axis(self, ax, t_min, t_max, model_units):
        if self.time_auto_scale:
            # Auto-select best units
            duration = t_max - t_min
            if duration < 1e-3:
                display_units, scale = "ms", 1e3
            elif duration < 60:
                display_units, scale = "s", 1.0
            elif duration < 3600:
                display_units, scale = "min", 1/60
            else:
                display_units, scale = "hr", 1/3600
        else:
            display_units = self.time_display_units
            scale = convert_units(model_units, display_units)
        
        ax.set_xlabel(f"Time ({display_units})")
        if self.time_log_scale:
            ax.set_xscale('log')
```

**UI**: Tier 1 + Tier 2 + plot context menu

---

## Preset Configurations: The "Easy Button"

**Problem**: Users don't know what settings to use

**Solution**: Provide presets for common scenarios

### Location: Simulation → Load Preset

```
┌─ Load Simulation Preset ──────────────────────────┐
│                                                    │
│ Choose a configuration for your model:            │
│                                                    │
│ ○ Default (General Purpose)                       │
│   • Units: seconds                                │
│   • Duration: 60s                                 │
│   • Auto time step                                │
│                                                    │
│ ○ Fast Reactions (Enzyme Kinetics)               │
│   • Units: milliseconds                           │
│   • Duration: 100ms                               │
│   • Small time step (0.01ms)                      │
│                                                    │
│ ○ Slow Dynamics (Cell Cycle)                     │
│   • Units: hours                                  │
│   • Duration: 24h                                 │
│   • Adaptive time step                            │
│                                                    │
│ ○ Stochastic Simulation                           │
│   • Units: seconds                                │
│   • Event-driven algorithm                        │
│   • Random conflict resolution                    │
│                                                    │
│ ○ Custom (Manual Configuration)                   │
│   • Opens settings dialog                         │
│                                                    │
│                  [Cancel]  [Apply]                │
└───────────────────────────────────────────────────┘
```

**Implementation**:
```python
PRESETS = {
    "default": {
        "time_units": "seconds",
        "duration": 60.0,
        "dt": "auto",
        "description": "General purpose simulation"
    },
    "enzyme_kinetics": {
        "time_units": "milliseconds", 
        "duration": 100.0,
        "dt": 0.01,
        "viz_sample_rate": 1000.0,
        "description": "Fast reactions (ms scale)"
    },
    "cell_cycle": {
        "time_units": "hours",
        "duration": 24.0,
        "dt": "adaptive",
        "dt_min": 0.01,
        "dt_max": 1.0,
        "description": "Slow dynamics (hours scale)"
    },
    "stochastic": {
        "time_units": "seconds",
        "duration": 60.0,
        "algorithm": "event-driven",
        "conflict_policy": "random",
        "description": "Stochastic simulation"
    }
}

def load_preset(preset_name):
    """Apply preset configuration."""
    config = PRESETS[preset_name]
    controller.time_units = config["time_units"]
    controller.duration = config["duration"]
    # ... apply other settings
```

---

## Smart Defaults: What to Auto-Compute

### 1. Time Step (`dt`)

**Rule**: `dt = duration / 1000` unless user overrides

**Rationale**:
- 1000 steps gives good resolution without excessive computation
- Scales automatically with duration
- Users rarely need to change this

**Override cases**:
- Stiff systems (need smaller dt)
- Real-time constraints (need specific dt)
- Known dynamics (e.g., "I know period is 0.5s, use dt=0.01")

### 2. Visualization Sample Rate

**Rule**: `viz_rate = min(10 Hz, num_sim_steps)` 

**Rationale**:
- 10 Hz (100ms) is smooth for human perception
- Don't oversample (if simulation has 100 steps, show 100 points)
- Don't undersample (if simulation has 100k steps, decimate to 1k)

**Override cases**: Never (user doesn't care about this)

### 3. Time Units Display (Plots)

**Rule**: Auto-scale based on duration

| Duration Range | Display Units |
|----------------|---------------|
| < 1ms | microseconds (μs) |
| 1ms - 1s | milliseconds (ms) |
| 1s - 60s | seconds (s) |
| 60s - 3600s | minutes (min) |
| 3600s - 86400s | hours (h) |
| > 86400s | days (d) |

**Override cases**: Matching specific paper/experiment

### 4. Interpolation Method

**Rule**: Linear interpolation (default)

**Rationale**:
- Doesn't introduce oscillations
- Fast to compute
- Visually appropriate for most data

**Override cases**:
- Step function for discrete events (user preference)
- Cubic spline for publication-quality smooth curves

---

## UI Layout: Integrated Design

### Main Window Layout

```
┌─ shypn ───────────────────────────────────────────────────────┐
│ File  Edit  View  Simulation  Analysis  Help                  │
├───────────────────────────────────────────────────────────────┤
│ ┌─ Left Panel ───┐ ┌─ Canvas ───────────────────────────────┐ │
│ │                │ │                                         │ │
│ │  File Explorer │ │     [Petri Net Model Display]          │ │
│ │                │ │                                         │ │
│ │  Examples/     │ │        ●───→[T1]───→●                 │ │
│ │  Projects/     │ │                                         │ │
│ │                │ │                                         │ │
│ └────────────────┘ └─────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ Simulation Controls ─────────────────────────────────────┐  │
│ │  ▶ Run  ⏸ Pause  ⏹ Stop  ⏮ Reset     ⚙ Settings         │  │
│ │  Duration: [__60__] [seconds▼]   Time: 12.5/60.0 s ━━░   │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│ ┌─ Results Panel (Bottom) ──────────────────────────────────┐  │
│ │ Tabs: [ Plot ] [ Data Table ] [ Statistics ]             │  │
│ │                                                            │  │
│ │  [Line chart showing token counts over time]             │  │
│ │                                                            │  │
│ └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

**Key Points**:
1. **Simulation controls always visible** (no hunting for controls)
2. **Settings accessed via ⚙ button** (not cluttering main UI)
3. **Results integrated** (no separate window to manage)

---

## Validation & Error Handling

### Smart Validation

**When user enters duration**:
```python
def validate_duration(value, units):
    """Validate and provide helpful feedback."""
    if value <= 0:
        show_error("Duration must be positive")
        return False
    
    # Convert to seconds for sanity check
    value_seconds = convert_to_seconds(value, units)
    
    if value_seconds < 0.001:  # < 1ms
        show_warning(
            "Very short simulation (<1ms). "
            "Are you sure about the time units?"
        )
    
    if value_seconds > 31536000:  # > 1 year
        show_warning(
            "Very long simulation (>1 year). "
            "This may take a while..."
        )
    
    # Estimate computational cost
    estimated_steps = value_seconds / auto_dt(value_seconds)
    if estimated_steps > 1e6:
        show_warning(
            f"This will require ~{estimated_steps/1e6:.1f}M steps. "
            "Consider increasing time step in advanced settings."
        )
    
    return True
```

**When user enters time step manually**:
```python
def validate_dt(dt, duration):
    """Check if time step makes sense."""
    num_steps = duration / dt
    
    if num_steps < 10:
        show_warning(
            f"Only {num_steps} simulation steps. "
            "Results may be inaccurate. Use smaller time step."
        )
    
    if num_steps > 1e6:
        show_warning(
            f"This requires {num_steps/1e6:.1f}M steps. "
            "Increase time step for faster simulation."
        )
    
    return True
```

---

## Progressive Disclosure: Learning Path

### For New Users (Week 1)

**Show**: Only Tier 1 (control panel)
- Duration + units
- Run/Pause/Stop
- Progress indication

**Hide**: Everything else (auto-computed)

**User Experience**:
> "I just want to run my model. I set it to 60 seconds, click Run, and see results. Done."

### For Regular Users (Week 2-4)

**Show**: Tier 1 + occasional Tier 2
- Basic controls always visible
- Settings dialog for special cases
- Presets for common scenarios

**User Experience**:
> "Usually the defaults work, but for my stiff biochemical system, I need to set dt=0.01 manually."

### For Expert Users (Ongoing)

**Show**: All tiers
- Full control over all parameters
- Per-transition fine-tuning
- Advanced plot customization

**User Experience**:
> "I need Priority-based conflict resolution, log-scale time axis, and dt=0.001 for this specific model."

---

## Summary: Minimal User Intervention

### **What Users MUST Set** (Cannot Auto-Compute):

1. **Simulation duration** (`t_max`)
   - UI: Text input + dropdown
   - Why: System doesn't know "how long is interesting"

2. **Time units** (what rates mean)
   - UI: Dropdown (ms, s, min, hr, days)
   - Why: Defines semantics of transition rates

3. **Transition rates/delays** (per-transition)
   - UI: Transition properties dialog
   - Why: Model parameters (can't infer)

### **What System SHOULD Auto-Compute**:

1. ✅ Time step (`dt`) → `duration / 1000`
2. ✅ Visualization sampling → 10 Hz or match sim steps
3. ✅ Display time units → Auto-scale from duration
4. ✅ Tick marks → Matplotlib smart defaults
5. ✅ Interpolation → Linear (safe default)
6. ✅ Scientific notation → Based on magnitude
7. ✅ Conflict resolution → Random (stochastic default)

### **What Users CAN Override** (Advanced):

- Manual time step (for stiff systems)
- Time scale factor (for data matching)
- Conflict policy (for deterministic testing)
- Plot interpolation (step vs. smooth)
- Log scale time axis (for wide ranges)

---

## Implementation Priority

### Sprint 1 (Week 1): **Core Simulation**
- [ ] Control panel UI (Tier 1)
- [ ] Auto-compute dt
- [ ] Basic plotting with auto-scaling

### Sprint 2 (Week 2): **Settings Dialog**
- [ ] Settings dialog (Tier 2)
- [ ] Time units configuration
- [ ] Advanced settings (collapsed)

### Sprint 3 (Week 3): **Presets & Polish**
- [ ] Preset configurations
- [ ] Plot settings panel
- [ ] Validation & warnings

### Sprint 4 (Week 4): **Documentation**
- [ ] User guide: "Quick Start"
- [ ] User guide: "Understanding Time Settings"
- [ ] Example models with different time scales

---

## Conclusion

**Key Insight**: Most time-related settings should be **automatic with intelligent defaults**. User intervention is only needed for:

1. **Semantic choices** (time units, duration)
2. **Model parameters** (rates, delays)
3. **Advanced tuning** (optional, for experts)

By providing a **three-tier UI** (minimal → settings → expert), we serve:
- 80% of users with minimal friction (Tier 1 only)
- 15% of users who need customization (Tier 2)
- 5% of experts who want full control (Tier 3)

The system makes smart choices automatically, but allows override when needed. This is the **progressive disclosure** principle: show simple first, reveal complexity on demand.

**Next Steps**:
1. Implement Tier 1 UI (control panel)
2. Add auto-computation logic
3. Test with real users
4. Add Tier 2/3 based on feedback

**Status**: UI design complete, ready for implementation
**Date**: 2025-10-08
