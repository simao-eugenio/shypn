# Simulation Integration Plan

## Overview
This document outlines the plan to integrate the simulation engine with the UI simulation tools palette (Run, Stop, Reset buttons).

## Current State Analysis

### Legacy Implementation
From `legacy/shypnpy/simulation/controller.py` and `legacy/shypnpy/deprecated/shypn.py`:

**SimulationController API:**
- `step(time_step=0.1)` - Single simulation step with locality-based firing
- `run(steps, time_step=0.1)` - Run multiple steps with stop capability
- `stop()` - Request simulation stop
- `reset()` - Reset model to initial state
- Callback system: `add_step_listener(callback)` for UI updates

**Legacy UI Button Connections:**
```python
# From deprecated shypn.py (~line 8090)
self.simulate_button.connect("clicked", self.on_simulate_clicked)
self.reset_button.connect("clicked", self.on_reset_clicked)
self.stop_button.connect("clicked", self.on_stop_clicked)

# Button handlers
def on_simulate_clicked(self, widget):
    self.start_simulation()

def on_reset_clicked(self, widget):
    self.reset_network()

def on_stop_clicked(self, button):
    self.stop_simulation()
```

### Current Implementation
From `src/shypn/helpers/simulate_tools_palette_loader.py`:

**SimulateToolsPaletteLoader:**
- **Signals emitted:**
  - `'run-clicked'` - When Run button pressed
  - `'stop-clicked'` - When Stop button pressed  
  - `'reset-clicked'` - When Reset button pressed
- **State management:**
  - `_simulation_running` - Tracks simulation state
  - `_initial_marking` - Stores initial state for reset
- **Button state control:**
  - Enables/disables buttons based on simulation state

## Architecture Design

### Component Structure
```
┌─────────────────────────────────────────────────┐
│           Main Application (shypn.py)           │
│  - Owns PetriNetModel                          │
│  - Creates SimulationController                │
│  - Wires palette signals to controller         │
└────────────┬────────────────────────────────────┘
             │
             ├───────────────────────────────────┐
             │                                   │
┌────────────▼──────────────┐    ┌──────────────▼────────────┐
│ SimulateToolsPaletteLoader│    │   SimulationController    │
│ - UI Button Panel          │    │   - step() execution      │
│ - Emits signals           │    │   - run() loop            │
│ - Updates button states   │    │   - stop() request        │
└────────────┬──────────────┘    │   - reset() model         │
             │                    │   - Callback system       │
             │ signals            └──────────┬────────────────┘
             │                               │
             │                               │ operates on
             │                               │
┌────────────▼───────────────────────────────▼────┐
│              PetriNetModel                       │
│  - places, transitions, arcs                    │
│  - logical_time                                 │
│  - execution_history                            │
│  - initial_marking (for reset)                  │
└──────────────────────────────────────────────────┘
```

### Signal Flow
```
User Click → Palette Button → Signal Emitted → Main App Handler → 
SimulationController Method → Model Update → Canvas Redraw
```

## Implementation Plan

### Phase 1: Create SimulationController Wrapper
**File:** `src/shypn/simulation/controller.py`

Copy and adapt from legacy with these changes:
1. Remove Phase 4 locality-based features (keep simple for now)
2. Focus on core API: `step()`, `run()`, `stop()`, `reset()`
3. Keep callback system for canvas updates
4. Simplify to work with current PetriNetModel

**Key Methods:**
```python
class SimulationController:
    def __init__(self, model):
        self.model = model
        self._stop_requested = False
        self._on_step = []  # Callbacks
    
    def step(self, time_step=0.1):
        """Single simulation step"""
        # Check enabled transitions
        # Fire transitions
        # Advance time
        # Call callbacks
        pass
    
    def run(self, steps, time_step=0.1):
        """Run multiple steps"""
        for i in range(steps):
            if self._stop_requested:
                break
            self.step(time_step)
        pass
    
    def stop(self):
        """Request stop"""
        self._stop_requested = True
    
    def reset(self):
        """Reset model to initial state"""
        self.model.reset()
        self._stop_requested = False
        # Call callbacks
    
    def add_step_listener(self, callback):
        """Register callback for step events"""
        if callback not in self._on_step:
            self._on_step.append(callback)
```

### Phase 2: Wire Signals in Main Application
**File:** `src/shypn.py`

Add in initialization:
```python
# Create simulation controller
self.simulation_controller = None

# Connect palette signals
self.simulate_tools_palette.connect('run-clicked', self._on_simulation_run)
self.simulate_tools_palette.connect('stop-clicked', self._on_simulation_stop)
self.simulate_tools_palette.connect('reset-clicked', self._on_simulation_reset)

# Register canvas redraw callback
if self.simulation_controller:
    self.simulation_controller.add_step_listener(self._on_simulation_step)
```

Add handlers:
```python
def _on_simulation_run(self, palette):
    """Handle Run button - start simulation"""
    if not self.simulation_controller:
        self.simulation_controller = SimulationController(self.model)
        self.simulation_controller.add_step_listener(self._on_simulation_step)
    
    # Store initial marking if first run
    if not self.simulation_controller.model.initial_marking:
        self.simulation_controller.model.store_initial_marking()
    
    # Start continuous simulation using GLib.timeout_add
    self._simulation_running = True
    GLib.timeout_add(100, self._simulation_loop)  # 100ms interval

def _on_simulation_stop(self, palette):
    """Handle Stop button - pause simulation"""
    self._simulation_running = False
    if self.simulation_controller:
        self.simulation_controller.stop()

def _on_simulation_reset(self, palette):
    """Handle Reset button - reset to initial marking"""
    self._simulation_running = False
    if self.simulation_controller:
        self.simulation_controller.reset()
        # Queue canvas redraw
        if self.canvas_loader and self.canvas_loader.drawing_area:
            self.canvas_loader.drawing_area.queue_draw()

def _simulation_loop(self):
    """Continuous simulation loop called by GLib timeout"""
    if not self._simulation_running:
        return False  # Stop loop
    
    if self.simulation_controller:
        self.simulation_controller.step(time_step=0.1)
    
    return True  # Continue loop

def _on_simulation_step(self, model, logical_time):
    """Callback when simulation advances one step"""
    # Queue canvas redraw
    if self.canvas_loader and self.canvas_loader.drawing_area:
        self.canvas_loader.drawing_area.queue_draw()
    
    # Update status bar with time
    print(f"[Simulation] Time: {logical_time:.2f}s")
```

### Phase 3: Implement Basic Firing Logic
**In SimulationController.step():**

1. **Check Enabled Transitions:**
   ```python
   enabled = []
   for tid, transition in self.model.transitions.items():
       if self._is_enabled(tid):
           enabled.append(tid)
   ```

2. **Fire Transitions:**
   ```python
   for tid in enabled:
       self._fire_transition(tid)
   ```

3. **Advance Time:**
   ```python
   self.model.logical_time += time_step
   ```

4. **Call Callbacks:**
   ```python
   for callback in self._on_step:
       callback(self.model, self.model.logical_time)
   ```

### Phase 4: Add Initial Marking Support
**In PetriNetModel:**

```python
def store_initial_marking(self):
    """Store current marking as initial state"""
    self.initial_marking = {}
    for pid, place in self.places.items():
        self.initial_marking[pid] = place.tokens

def reset(self):
    """Reset to initial marking"""
    if hasattr(self, 'initial_marking') and self.initial_marking:
        for pid, tokens in self.initial_marking.items():
            if pid in self.places:
                self.places[pid].tokens = tokens
    
    # Reset time
    self.logical_time = 0.0
```

### Phase 5: Test & Refine

**Test Cases:**
1. **Run Test:** Click Run → transitions should fire → tokens should move
2. **Stop Test:** Click Stop → simulation should pause
3. **Reset Test:** Click Reset → tokens return to initial marking
4. **Resume Test:** Run → Stop → Run → should continue from stopped state
5. **Multiple Resets:** Reset → Run → Reset → should work repeatedly

## Key Considerations

### 1. Thread Safety
- Use GLib.timeout_add for main thread execution
- Avoid threading complications initially
- All UI updates must be on main thread

### 2. Button State Management
- Run: Enable after Stop/Reset, disable while running
- Stop: Enable while running, disable otherwise
- Reset: Enable after Stop, disable while running

### 3. Canvas Redraw Optimization
- Only redraw when tokens change
- Use `queue_draw()` not `queue_draw_area()`
- Batch updates in callback

### 4. Error Handling
- Catch exceptions in simulation loop
- Don't crash on firing errors
- Log errors and continue

### 5. Performance
- Start with simple implementation
- Profile if slow (many transitions/places)
- Optimize firing algorithm later

## Future Enhancements (Post-MVP)

1. **Step-by-Step Mode:** Single step button
2. **Speed Control:** Slider for simulation speed
3. **Time Display:** Show current simulation time
4. **Transition Highlighting:** Show which transitions fired
5. **Animation:** Smooth token movement
6. **History:** Record and replay simulation
7. **Statistics:** Transition firing counts, throughput
8. **Locality-Based Firing:** Restore Phase 4 optimizations
9. **Formula Evaluation:** Guard and rate expressions
10. **Continuous Transitions:** Integrate continuous firing

## Dependencies

**Required Files:**
- `src/shypn/simulation/__init__.py` (new)
- `src/shypn/simulation/controller.py` (new, adapted from legacy)
- `src/shypn.py` (modify to wire signals)
- `src/shypn/netobjs/petri_net_model.py` (add reset methods if missing)

**Python Packages:**
- `gi.repository.GLib` (already used)
- No new external dependencies

## Risks & Mitigation

**Risk 1:** Performance with many transitions
- **Mitigation:** Start simple, profile, optimize later

**Risk 2:** UI freezing during simulation
- **Mitigation:** Use GLib.timeout_add with small steps

**Risk 3:** Complex firing logic errors
- **Mitigation:** Start with basic firing, add complexity gradually

**Risk 4:** State inconsistency between UI and model
- **Mitigation:** Use signals for all state changes

## Success Criteria

✅ **Minimal Viable Product (MVP):**
1. Run button starts simulation (transitions fire, tokens move)
2. Stop button pauses simulation
3. Reset button returns to initial marking
4. Canvas updates automatically during simulation
5. No crashes or UI freezing

✅ **Complete Implementation:**
- All button combinations work correctly
- Button states reflect simulation state
- Performance acceptable for typical nets (< 100 transitions)
- Error handling prevents crashes
- Clear feedback to user (status messages, visual updates)

## Timeline Estimate

- **Phase 1:** Controller creation - 2 hours
- **Phase 2:** Signal wiring - 1 hour
- **Phase 3:** Firing logic - 3 hours
- **Phase 4:** Initial marking - 1 hour
- **Phase 5:** Testing - 2 hours
- **Total:** ~9 hours

## Next Steps

1. ✅ Create `doc/SIMULATION_INTEGRATION_PLAN.md` (this document)
2. ⏳ Create `src/shypn/simulation/` directory
3. ⏳ Implement `controller.py` with basic API
4. ⏳ Wire signals in `shypn.py`
5. ⏳ Test Run button functionality
6. ⏳ Test Stop button functionality
7. ⏳ Test Reset button functionality
8. ⏳ Refine and optimize
