# Simulation Time Scaling Analysis

**Date**: October 11, 2025  
**Subject**: Analysis of current simulation time control capabilities

## User Requirements Analysis

### Stated Requirements

1. **Real-time phenomena observation**: Should support milliseconds, seconds, minutes, hours, or days
2. **Time scale control**: Want to see the whole observed real-time phenomenon in different time scales
3. **Evolution visualization**: Should see the whole evolution of a phenomenon in any time scale
4. **Example scenario**: See hours of real-time phenomenon in one minute of simulation playback

### Core Need
**Ability to compress/expand real-world time when visualizing simulation results**

Example: A biological process that takes 24 hours in reality should be viewable in:
- 1 minute (1440x speedup)
- 5 minutes (288x speedup)  
- Real-time (1x)
- Slow motion (0.1x)

---

## Current Implementation Status

### ✅ What IS Implemented

#### 1. **Model Time Units** (`TimeUnits` enum)
- **Location**: `src/shypn/utils/time_utils.py`
- **Supported units**: milliseconds, seconds, minutes, hours, days
- **Purpose**: Define the time scale of the **model itself**
- **Status**: ✅ COMPLETE

```python
class TimeUnits(Enum):
    MILLISECONDS = ('milliseconds', 'ms', 0.001)
    SECONDS = ('seconds', 's', 1.0)
    MINUTES = ('minutes', 'min', 60.0)
    HOURS = ('hours', 'hr', 3600.0)
    DAYS = ('days', 'd', 86400.0)
```

#### 2. **Simulation Duration Control**
- **Location**: `src/shypn/engine/simulation/settings.py`
- **Feature**: Set total simulation duration
- **Units**: Can be specified in any TimeUnits
- **Status**: ✅ COMPLETE

```python
settings.set_duration(24.0, TimeUnits.HOURS)  # Simulate 24 hours
```

#### 3. **Time Step Control**
- **Location**: `SimulationSettings.get_effective_dt()`
- **Modes**:
  - **Auto**: `dt = duration / 1000` (default 1000 steps)
  - **Manual**: User-specified dt
- **Status**: ✅ COMPLETE

```python
# Auto: 24 hours / 1000 steps = 86.4 seconds per step
settings.dt_auto = True

# Manual: 10 seconds per step
settings.dt_auto = False
settings.dt_manual = 10.0
```

#### 4. **Batch Step Execution** (Animation Smoothness)
- **Location**: `SimulationController._simulation_loop()`
- **Feature**: Execute multiple simulation steps per GUI update
- **Purpose**: Smooth animation for very small time steps
- **Status**: ✅ COMPLETE

```python
gui_interval_s = 0.1  # 100ms GUI updates
self._steps_per_callback = max(1, int(gui_interval_s / time_step))
```

**Example**: If dt = 0.002s (2ms model time):
- Steps per GUI update: 0.1 / 0.002 = 50 steps
- Result: 50 simulation steps every 100ms = smooth animation

---

### ❌ What IS NOT Implemented

#### 1. **Playback Speed / Time Scale** ⚠️ **CRITICAL MISSING**

**Problem**: No independent control of visualization speed vs. model time

**Current behavior**:
- Model time step = GUI update rate
- If dt = 1 second, each GUI update advances 1 second of model time
- **NO WAY to say**: "Show me 1 hour of model time in 1 minute of real-world playback"

**What's needed**:
```python
# DESIRED (not implemented):
settings.time_scale = 60.0  # 60x speedup
# 1 second of real-world playback = 60 seconds of model time

settings.time_scale = 0.1  # 10x slowdown  
# 1 second of real-world playback = 0.1 seconds of model time
```

**Current workaround** (inadequate):
- Adjust `dt_manual` to smaller values → faster playback
- **Limitation**: This changes the **simulation accuracy**, not just visualization speed
- Small dt = more accurate but slower computation
- Large dt = less accurate but faster computation
- **No way to decouple simulation accuracy from playback speed**

#### 2. **Independent Visualization Tempo**

**Problem**: Playback rate is coupled to simulation computation

**Current flow**:
```
User clicks "Run" 
→ GLib timeout every 100ms
→ Execute N simulation steps (based on dt)
→ Update GUI
→ Repeat
```

**What's missing**:
- Ability to pre-compute simulation results
- Then play back at any desired speed
- Like video playback: pause, slow-mo, fast-forward

#### 3. **Real-Time Clock vs. Model Time Display**

**Partial implementation**:
- Time display shows **model time** (simulation time)
- **No display of**: Real-world elapsed time, playback speed multiplier

**Needed**:
```
Model Time:    2.5 hours
Real Time:     3 minutes elapsed  
Speed:         50x (50 model seconds per 1 real second)
```

---

## Technical Analysis

### Current Architecture

```
┌─────────────────────────────────────────────────────┐
│ SimulationSettings                                   │
│                                                      │
│ - time_units: TimeUnits (model time interpretation) │
│ - duration: float (how long to simulate)            │
│ - dt_auto/dt_manual: float (time step size)         │
│ - time_scale: float ⚠️ DEFINED BUT NOT USED         │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│ SimulationController                                 │
│                                                      │
│ - step(time_step): Execute one step                 │
│ - run(): Continuous execution                        │
│   → GLib.timeout_add(100ms, _simulation_loop)       │
│   → _simulation_loop():                              │
│       for _ in range(steps_per_callback):            │
│           self.step(self._time_step)                 │
│       return True  # Continue                        │
└─────────────────────────────────────────────────────┘
```

### Key Finding: `time_scale` Property Exists But Is Unused

**Location**: `SimulationSettings.time_scale`

```python
@property
def time_scale(self) -> float:
    """Get time scale factor (real-world to simulation)."""
    return self._time_scale

@time_scale.setter
def time_scale(self, value: float):
    """Set time scale with validation."""
    if value <= 0:
        raise ValueError("Time scale must be positive")
    self._time_scale = value
```

**Status**: Property exists, serializable, but **never read or used** in simulation execution

---

## Gap Analysis

### Requirement 1: Milliseconds to Days Time Range
- **Status**: ✅ **SATISFIED**
- **Implementation**: TimeUnits enum supports full range
- **Example**: Can simulate 48 hours with dt = 10 seconds

### Requirement 2: Different Time Scales for Same Phenomenon
- **Status**: ❌ **NOT SATISFIED**
- **Gap**: No way to set "playback speed" independent of simulation accuracy
- **Workaround**: Adjust dt_manual (but this affects accuracy)

### Requirement 3: See Whole Evolution in Any Time Scale
- **Status**: ⚠️ **PARTIALLY SATISFIED**
- **What works**: Can simulate any duration and visualize
- **What's missing**: Cannot control **speed of visualization** after simulation
- **Example issue**: 
  - Simulate 24 hours with dt = 60s (1440 steps)
  - Playback takes: 1440 steps × 0.1s GUI = 144 seconds (2.4 minutes)
  - **Cannot make this faster or slower without re-running simulation**

### Requirement 4: Hours of Real-Time in One Minute
- **Status**: ❌ **NOT SATISFIED**
- **Gap**: No explicit "real-world playback duration" setting
- **Current limitation**: Playback time = steps × GUI_interval
- **Need**: `playback_duration_seconds` setting that controls animation speed

---

## Recommended Implementation Plan

### Phase 1: Enable `time_scale` for Playback Control (HIGH PRIORITY)

**Goal**: Use existing `time_scale` property to control playback speed

**Changes needed**:

#### 1.1 Modify `SimulationController.run()` to use time_scale

```python
def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
    """Start continuous simulation execution.
    
    Uses settings.time_scale to control playback speed:
    - time_scale = 1.0: Real-time (1 second model = 1 second real)
    - time_scale = 60.0: 60x speedup (1 second real = 60 seconds model)
    - time_scale = 0.5: 2x slowdown (1 second real = 0.5 seconds model)
    """
    # ... existing code ...
    
    # Calculate GUI update interval based on time_scale
    # Default: 100ms real-time between GUI updates
    base_gui_interval_ms = 100  
    
    # How much model time should pass per GUI update?
    # time_scale = model_seconds / real_seconds
    model_time_per_gui_update = base_gui_interval_ms / 1000.0 * self.settings.time_scale
    
    # How many steps needed to cover that model time?
    self._steps_per_callback = max(1, int(model_time_per_gui_update / time_step))
    
    # Example: time_scale=60, dt=1.0, gui_interval=0.1s
    # model_time_per_update = 0.1 * 60 = 6 seconds model time
    # steps_per_callback = 6 / 1.0 = 6 steps
    # Result: 6 steps per 100ms = smooth 60x speedup
    
    self._timeout_id = GLib.timeout_add(base_gui_interval_ms, self._simulation_loop)
    return True
```

#### 1.2 Add Time Scale UI Control

**Location**: `simulate_tools_palette.ui` and `simulate_tools_palette_loader.py`

Add widgets:
- SpinButton: time_scale (range: 0.01 to 1000.0)
- Label: "Playback Speed: 60x" (calculated display)

Connect signal:
```python
def _on_time_scale_changed(self, spin_button):
    """Update time scale when user changes playback speed."""
    new_scale = spin_button.get_value()
    self.simulation.settings.time_scale = new_scale
    
    # If running, need to recalculate steps_per_callback
    if self.simulation.is_running():
        self.simulation.stop()
        self.simulation.run()  # Restart with new time scale
```

### Phase 2: Add Real-Time vs. Model Time Display (MEDIUM PRIORITY)

**Goal**: Show user both model time and real-world elapsed time

**Changes needed**:

#### 2.1 Track Real-World Start Time

```python
class SimulationController:
    def __init__(self, model):
        # ... existing code ...
        self._real_time_start = None  # time.time() when run() called
        self._real_time_paused = 0.0  # Total paused duration
    
    def run(self, ...):
        # ... existing code ...
        import time
        self._real_time_start = time.time()
        self._real_time_paused = 0.0
    
    def stop(self):
        # ... existing code ...
        if self._real_time_start is not None:
            elapsed = time.time() - self._real_time_start - self._real_time_paused
            self._real_time_paused += elapsed
    
    def get_real_time_elapsed(self) -> float:
        """Get real-world time elapsed since run started."""
        if self._real_time_start is None:
            return 0.0
        return time.time() - self._real_time_start - self._real_time_paused
```

#### 2.2 Update Time Display UI

```python
def _update_time_display(self):
    """Update time display with both model time and real time."""
    model_time = self.simulation.time
    real_time_elapsed = self.simulation.get_real_time_elapsed()
    
    # Calculate effective playback speed
    if real_time_elapsed > 0.001:
        effective_speed = model_time / real_time_elapsed
    else:
        effective_speed = self.simulation.settings.time_scale
    
    # Format: "Model: 2.5 hr | Real: 3m 12s | Speed: 50x"
    model_str = TimeFormatter.format_with_units(
        model_time, 
        self.simulation.settings.time_units
    )
    real_str = TimeFormatter.format_duration(real_time_elapsed)
    
    display_text = f"Model: {model_str} | Real: {real_str} | {effective_speed:.1f}x"
    self.time_display_label.set_text(display_text)
```

### Phase 3: Preset Time Scales (LOW PRIORITY, UX ENHANCEMENT)

**Goal**: Quick-select buttons for common time scales

**UI Addition**:
```
[0.1x] [0.5x] [1x] [5x] [10x] [60x] [Custom: ___]
```

Buttons set `settings.time_scale` and restart simulation if running.

### Phase 4: Post-Computation Playback (FUTURE ENHANCEMENT)

**Goal**: Separate simulation computation from visualization

**Architecture change**:
```
Step 1: Compute simulation
   → Store all states: [(time_0, state_0), (time_1, state_1), ...]

Step 2: Playback results
   → Interpolate between stored states
   → Play at any speed (independent of computation)
   → Scrub timeline, reverse, etc.
```

**Benefits**:
- Can replay same simulation at different speeds without recomputing
- Can scrub timeline (jump to specific time)
- Can reverse playback
- Can export animation

**Complexity**: HIGH (requires state recording infrastructure)

---

## Implementation Priority

### 🔴 **Phase 1** (Critical - Addresses core need)
**Estimated effort**: 4-6 hours  
**Impact**: HIGH - Enables the main user requirement

**Tasks**:
1. Use `settings.time_scale` in `SimulationController.run()` ✅ Property exists
2. Calculate `steps_per_callback` based on time_scale ✅ Pattern exists
3. Add time_scale spinbutton to simulation palette UI
4. Connect signal handler for time scale changes
5. Test with various scenarios (0.1x, 1x, 10x, 100x)

### 🟡 **Phase 2** (Recommended - Better UX)
**Estimated effort**: 2-3 hours  
**Impact**: MEDIUM - Improves user understanding

**Tasks**:
1. Add real-time tracking to SimulationController
2. Update time display to show both times + speed
3. Format time display for readability
4. Test time tracking accuracy

### 🟢 **Phase 3** (Optional - Convenience)
**Estimated effort**: 1-2 hours  
**Impact**: LOW - Nice to have

**Tasks**:
1. Add preset buttons to UI
2. Connect button signals
3. Style buttons for quick access

### ⚪ **Phase 4** (Future - Major feature)
**Estimated effort**: 20-30 hours  
**Impact**: VERY HIGH - Enables advanced features

**Tasks**:
- Design state recording system
- Implement state capture during simulation
- Build playback engine with interpolation
- Add timeline scrubber widget
- Add export functionality

**Recommendation**: Defer to future release

---

## Answer to User Question

### Current Status: ❌ **NOT FULLY SUPPORTED**

**What you CAN do now**:
1. ✅ Simulate phenomena at any time scale (milliseconds to days)
2. ✅ Set simulation duration in any units
3. ✅ Control time step (simulation accuracy)
4. ✅ Visualize simulation results

**What you CANNOT do now**:
1. ❌ **Control playback speed independent of simulation accuracy**
2. ❌ **See 24 hours of model time in 1 minute of real-world playback**
3. ❌ **Speed up/slow down visualization without changing dt (and thus accuracy)**

### Example Scenario Gap

**Your requirement**: 
> "See hours of real-time phenomenon in one minute"

**Current limitation**:
```python
# Want: 2 hours model time in 1 minute real playback
# That's 120 minutes / 1 minute = 120x speedup

# Current approach (WRONG):
settings.dt_manual = 2.0  # 2 second steps
# Problem: Changes simulation accuracy, not playback speed
# Also doesn't guarantee 1 minute real-time playback

# What's needed (NOT IMPLEMENTED):
settings.duration = 2.0  # 2 hours
settings.time_units = TimeUnits.HOURS
settings.playback_speed = 120.0  # 120x speedup ❌ MISSING
# Or equivalently:
settings.playback_duration_seconds = 60.0  # Play in 60 seconds ❌ MISSING
```

---

## Recommended Action

### Immediate (This week):
**Implement Phase 1** - Enable time_scale property for playback control

This will satisfy your core requirement with minimal code changes.

### Code changes required:
1. Modify `SimulationController.run()` to use `settings.time_scale`
2. Calculate `steps_per_callback = model_time_per_gui_update / dt`
3. Add time_scale spinbutton to simulation palette
4. Test various time scales

### Testing scenarios:
```python
# Scenario 1: 1 hour model time in 1 minute real time (60x)
settings.set_duration(1.0, TimeUnits.HOURS)  # 3600 seconds
settings.time_scale = 60.0  # 60x speedup
settings.dt_manual = 1.0  # 1 second steps
# Expected: 3600 steps in 60 seconds real time

# Scenario 2: 10 seconds model time in slow motion (0.5x)
settings.set_duration(10.0, TimeUnits.SECONDS)
settings.time_scale = 0.5  # Half speed
settings.dt_manual = 0.1  # 0.1 second steps
# Expected: 100 steps in 20 seconds real time

# Scenario 3: 24 hours in 5 minutes (288x)
settings.set_duration(24.0, TimeUnits.HOURS)
settings.time_scale = 288.0
settings.dt_manual = 10.0
# Expected: 8640 steps in 300 seconds
```

---

## Conclusion

**Current state**: Infrastructure is 80% complete but the critical `time_scale` property is not wired up to control playback speed.

**Path forward**: Implement Phase 1 (4-6 hours) to fully satisfy your requirements.

**Long-term vision**: Phase 4 (post-computation playback) would enable video-like control but is a major undertaking.

---

## Files Requiring Changes

### Phase 1 Implementation

1. **`src/shypn/engine/simulation/controller.py`**
   - Modify `run()` method (lines ~483-530)
   - Use `self.settings.time_scale` to calculate `steps_per_callback`

2. **`ui/simulate/simulate_tools_palette.ui`** (New widgets)
   - Add SpinButton for time_scale (0.01 to 1000.0)
   - Add Label showing "Playback Speed: Xx"

3. **`src/shypn/helpers/simulate_tools_palette_loader.py`**
   - Add `time_scale_spin` widget reference
   - Add `_on_time_scale_changed()` signal handler
   - Update time display to show effective speed

### Phase 2 Implementation (Optional)

4. **`src/shypn/engine/simulation/controller.py`**
   - Add `_real_time_start` and `_real_time_paused` tracking
   - Add `get_real_time_elapsed()` method

5. **`src/shypn/helpers/simulate_tools_palette_loader.py`**
   - Modify `_update_time_display()` to show both times

---

**END OF ANALYSIS**
