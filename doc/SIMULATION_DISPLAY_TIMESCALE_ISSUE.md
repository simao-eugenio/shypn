# Simulation Display Issue at Small Time Scales

**Date:** 2025-10-09  
**Status:** ⚠️ ISSUE IDENTIFIED - Display Update Rate Mismatch

## Problem Report

When duration is set to 2000 milliseconds, no tokens appear to be consumed during simulation, or token consumption appears very chunky/sudden.

## Root Cause Analysis

The issue is a **mismatch between simulation step rate and GUI update rate**.

### Current Behavior:

**Simulation Settings with 2000ms duration:**
- Duration: 2000 milliseconds = 2.0 seconds
- Time units: milliseconds  
- Target steps: 1000 (default)
- Calculated dt: 2.0s / 1000 = **0.002 seconds per step** (2 milliseconds)

**GUI Update Rate:**
```python
# In controller.py, line 613:
self._timeout_id = GLib.timeout_add(100, self._simulation_loop)
```
- GUI updates every **100 milliseconds**
- This is a **FIXED** interval regardless of simulation time step

**The Mismatch:**
- Simulation steps: Every 0.002 seconds (2ms)
- GUI updates: Every 0.1 seconds (100ms)
- **Result: 50 simulation steps happen between each visual update!**

### What the User Sees:

Instead of smooth token movement, you see:
1. Canvas shows initial state
2. Wait 100ms (GUI update interval)
3. Suddenly 50 steps worth of token changes appear at once
4. Wait 100ms
5. Another 50 steps worth of changes appear
6. Repeat...

This creates the illusion that:
- ❌ "No tokens are being consumed" (because changes are too small per GUI update)
- ❌ "Tokens disappear in chunks" (50 steps at once)
- ❌ "Simulation isn't working" (it IS working, just not visible)

## Technical Details

### Simulation Loop Code:

```python
# src/shypn/engine/simulation/controller.py:613
def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
    # ... setup ...
    
    # FIXED 100ms interval - doesn't adapt to time_step!
    self._timeout_id = GLib.timeout_add(100, self._simulation_loop)
    return True

def _simulation_loop(self) -> bool:
    """Called every 100ms by GLib timeout"""
    if self._stop_requested:
        return False
    if self._max_steps is not None and self._steps_executed >= self._max_steps:
        return False
    
    # Execute ONE step (but could be tiny 2ms step)
    success = self.step(self._time_step)
    if not success:
        return False
        
    self._steps_executed += 1
    return True  # Continue timeout
```

### Step Notification Chain:

```python
# 1. Controller.step() completes
controller.step(0.002)  # 2ms step

# 2. Notifies listeners
controller._notify_step_listeners()

# 3. SimulateToolsPaletteLoader receives notification
def _on_simulation_step(self, controller, time):
    self.emit('step-executed', time)  # Emit signal

# 4. ModelCanvasLoader receives signal
def _on_simulation_step(self, palette, time, drawing_area):
    drawing_area.queue_draw()  # Request redraw

# 5. GTK processes draw queue (async)
# This happens on next main loop iteration
```

### Why 100ms Interval?

The 100ms (10 Hz) update rate was chosen as a reasonable balance:
- Fast enough for visible animation (10 FPS)
- Slow enough to not overload GUI with redraws
- Works well for typical time steps (0.01s to 1.0s)

But it **breaks down** when:
- Time step is very small (< 0.01s)
- Time step is very large (> 1.0s)

## Examples

### Case 1: 2000ms duration (PROBLEMATIC)

```
Settings:
- Duration: 2000ms = 2.0s
- dt = 2.0s / 1000 steps = 0.002s per step

Timeline:
Time 0.000s:  [GUI Update] Show initial state
Time 0.002s:  Step 1 (token moves) - NO GUI UPDATE
Time 0.004s:  Step 2 (token moves) - NO GUI UPDATE
...
Time 0.098s:  Step 49 (token moves) - NO GUI UPDATE
Time 0.100s:  [GUI Update] Show result of 50 steps at once!
Time 0.102s:  Step 51 - NO GUI UPDATE
...
Time 0.200s:  [GUI Update] Show next 50 steps
```

**Result:** Choppy, sudden changes every 100ms

### Case 2: 10 seconds duration (WORKS WELL)

```
Settings:
- Duration: 10s
- dt = 10s / 1000 steps = 0.01s per step

Timeline:
Time 0.00s: [GUI Update] Show initial state
Time 0.01s: Step 1 - NO GUI UPDATE  
...
Time 0.09s: Step 9 - NO GUI UPDATE
Time 0.10s: [GUI Update] Show result of 10 steps
Time 0.11s: Step 11 - NO GUI UPDATE
Time 0.20s: [GUI Update] Show result of next 10 steps
```

**Result:** Smooth animation (10 steps per frame)

### Case 3: 100 seconds duration (ALSO WORKS WELL)

```
Settings:
- Duration: 100s
- dt = 100s / 1000 steps = 0.1s per step

Timeline:
Time 0.0s: [GUI Update] Show initial state
Time 0.1s: Step 1 [GUI Update] - Shows immediately!
Time 0.2s: Step 2 [GUI Update] - Shows immediately!
```

**Result:** Smooth, immediate updates (1 step per frame)

## Solutions

### Option 1: Adaptive GUI Update Rate (Recommended)

Adjust the GUI timeout interval based on the time step:

```python
def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
    if time_step is None:
        time_step = self.get_effective_dt()
    
    # ... setup ...
    
    # Calculate adaptive GUI update interval
    # Aim for 10-20 steps per GUI update for smooth animation
    target_steps_per_update = 15
    gui_interval_ms = int(time_step * target_steps_per_update * 1000)
    
    # Clamp to reasonable range
    gui_interval_ms = max(16, min(gui_interval_ms, 200))  # 16ms to 200ms
    
    self._timeout_id = GLib.timeout_add(gui_interval_ms, self._simulation_loop)
    return True
```

**Benefits:**
- Small time steps: Faster GUI updates (e.g., 2ms step → 30ms GUI interval)
- Large time steps: Slower GUI updates (e.g., 1s step → 200ms GUI interval)
- Always smooth animation regardless of time scale

**Drawbacks:**
- More complex
- More frequent redraws for small time steps (could impact performance)

### Option 2: Multiple Steps Per GUI Update

Execute multiple simulation steps per GUI callback:

```python
def _simulation_loop(self) -> bool:
    """Execute multiple steps per GUI update for efficiency."""
    # Calculate how many steps to do per GUI update
    # Aim for smooth animation
    target_fps = 10  # 10 frames per second
    gui_interval_s = 0.1  # 100ms
    steps_per_update = int(gui_interval_s / self._time_step)
    steps_per_update = max(1, min(steps_per_update, 100))  # Clamp 1-100
    
    for _ in range(steps_per_update):
        if self._stop_requested:
            self._running = False
            return False
        if self._max_steps is not None and self._steps_executed >= self._max_steps:
            self._running = False
            return False
            
        success = self.step(self._time_step)
        if not success:
            self._running = False
            return False
        self._steps_executed += 1
    
    return True
```

**Benefits:**
- Keeps fixed 100ms GUI interval (simpler)
- Batches simulation work
- Better performance for small time steps

**Drawbacks:**
- Could cause GUI to feel "laggy" if steps take too long
- Less smooth for very large time steps

### Option 3: User-Configurable Animation Speed

Add a "playback speed" slider separate from simulation time:

```python
class SimulationSettings:
    def __init__(self):
        # ... existing ...
        self.animation_speed = 1.0  # 1.0 = real-time, 0.5 = half speed, 2.0 = double speed
```

```python
def run(self, time_step: float = None, ...):
    # ... setup ...
    
    # Calculate GUI interval based on animation speed
    base_interval_ms = 100  # Default
    adjusted_interval_ms = int(base_interval_ms / self.settings.animation_speed)
    
    self._timeout_id = GLib.timeout_add(adjusted_interval_ms, self._simulation_loop)
```

**Benefits:**
- User control over animation smoothness
- Can slow down fast simulations
- Can speed up slow simulations

**Drawbacks:**
- Adds UI complexity
- Doesn't automatically solve the problem

## Recommended Implementation

**Combine Option 1 (Adaptive) + Option 2 (Batching):**

```python
def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
    if time_step is None:
        time_step = self.get_effective_dt()
    
    self._running = True
    self._stop_requested = False
    self._max_steps = max_steps
    self._steps_executed = 0
    self._time_step = time_step
    
    # Calculate optimal batching
    # Target: 10 FPS with 10-20 steps per frame
    target_fps = 10
    target_steps_per_frame = 15
    
    # Calculate steps per callback
    self._steps_per_callback = max(1, int(0.1 / time_step))  # How many steps fit in 100ms
    self._steps_per_callback = min(self._steps_per_callback, 100)  # Cap at 100
    
    # Fixed 100ms interval, but batch multiple steps
    self._timeout_id = GLib.timeout_add(100, self._simulation_loop)
    return True

def _simulation_loop(self) -> bool:
    """Execute multiple steps per GUI update for smooth animation."""
    # Execute batch of steps
    for _ in range(self._steps_per_callback):
        if self._stop_requested:
            self._running = False
            return False
        if self._max_steps is not None and self._steps_executed >= self._max_steps:
            self._running = False
            return False
            
        success = self.step(self._time_step)
        if not success:
            self._running = False
            return False
        self._steps_executed += 1
    
    # GUI updates once after all steps in batch
    return True
```

## Testing

After fix, verify with different durations:

| Duration | Time Step | Steps/Frame | Expected Behavior |
|----------|-----------|-------------|-------------------|
| 2000ms | 0.002s | 50 | Smooth animation |
| 10s | 0.01s | 10 | Smooth animation |
| 100s | 0.1s | 1 | Immediate updates |
| 0.1s | 0.0001s | 1000 | Cap at 100, smooth |

## Files to Modify

1. **src/shypn/engine/simulation/controller.py**
   - Line 613: Modify `GLib.timeout_add()` call
   - Line 615-650: Modify `_simulation_loop()` to batch steps
   - Add `self._steps_per_callback` attribute

## Impact

**Current Behavior:**
- Fast simulations (< 10s): Appear broken/choppy ❌
- Medium simulations (10-100s): Work okay ✓
- Slow simulations (> 100s): Work well ✓

**After Fix:**
- Fast simulations: Smooth animation ✅
- Medium simulations: Smooth animation ✅  
- Slow simulations: Smooth animation ✅

## Notes

This is a classic "time scale" problem in simulation visualization. The simulation engine is working correctly, but the visualization layer isn't adapting to the time scale.

Similar issues occur in:
- Game engines (fixed timestep vs variable framerate)
- Scientific visualization (fast molecular dynamics)
- Real-time systems (sampling rate mismatch)

The fix makes the GUI update rate "aware" of the simulation time scale.
