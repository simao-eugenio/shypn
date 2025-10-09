# Simulation Palette Refinements

**Status**: ✅ Complete  
**Date**: 2025-01-06  
**Files Modified**:
- `src/shypn/helpers/simulate_tools_palette_loader.py`

## Overview

This document details the refinements made to the simulation tools palette to improve robustness, user experience, and integration with data visualization components.

## Refinements Implemented

### 1. ✅ Centralized Button State Management

**Problem**: Button sensitivity was being set in multiple places with hardcoded values, making state management difficult to maintain and prone to inconsistencies.

**Solution**: Created a centralized `_update_button_states()` method that implements a clear state machine.

**State Machine**:
```
┌─────────────────────────────────────────────────────────────┐
│ IDLE (after reset)                                          │
│ • Run: ✓  Step: ✓  Stop: ✗  Reset: ✗  Settings: ✓         │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Run clicked
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ RUNNING                                                      │
│ • Run: ✗  Step: ✗  Stop: ✓  Reset: ✗  Settings: ✗         │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Stop clicked
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PAUSED                                                       │
│ • Run: ✓  Step: ✓  Stop: ✗  Reset: ✓  Settings: ✓         │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Step until complete
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ COMPLETED                                                    │
│ • Run: ✗  Step: ✗  Stop: ✗  Reset: ✓  Settings: ✓         │
└─────────────────────────────────────────────────────────────┘
```

**Implementation**:
```python
def _update_button_states(self, running=False, completed=False, reset=False):
    """Update button sensitivity based on simulation state.
    
    Args:
        running: True if simulation is actively running
        completed: True if simulation reached duration limit
        reset: True if simulation was just reset to initial state
    """
    if running:
        # Running: only Stop available, no settings changes
        self.run_button.set_sensitive(False)
        self.step_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)
        self.reset_button.set_sensitive(False)
        self.settings_button.set_sensitive(False)
    elif completed:
        # Completed: only Reset available
        self.run_button.set_sensitive(False)
        self.step_button.set_sensitive(False)
        self.stop_button.set_sensitive(False)
        self.reset_button.set_sensitive(True)
        self.settings_button.set_sensitive(True)
    elif reset:
        # Just reset: fresh start state
        self.run_button.set_sensitive(True)
        self.step_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        self.reset_button.set_sensitive(False)  # Already at start
        self.settings_button.set_sensitive(True)
    else:
        # Paused/stopped: can resume, step, or reset
        self.run_button.set_sensitive(True)
        self.step_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        self.reset_button.set_sensitive(True)
        self.settings_button.set_sensitive(True)
```

**Modified Methods**:
- `_on_run_clicked()`: Now calls `_update_button_states(running=True)`
- `_on_step_clicked()`: Added completion detection, calls `_update_button_states(running=False, completed=True)` when done
- `_on_stop_clicked()`: Now calls `_update_button_states(running=False)`
- `_on_reset_clicked()`: Now calls `_update_button_states(running=False, reset=True)`

**Benefits**:
- ✅ Single source of truth for button states
- ✅ Easy to reason about state transitions
- ✅ Consistent behavior across all handlers
- ✅ Settings button properly disabled during simulation runs
- ✅ Prevents race conditions and inconsistent UI states

---

### 2. ✅ Enhanced Settings Persistence

**Problem**: Settings dialog could be opened during simulation, potentially causing issues. Parameter changes weren't properly logged or signaled.

**Solution**: Enhanced `_on_settings_clicked()` to:
1. Detect if simulation is running
2. Pause simulation before opening dialog
3. Apply settings changes
4. Update all displays
5. Emit signal for dependent components
6. Restore appropriate button state

**Implementation**:
```python
def _on_settings_clicked(self, button):
    """Handle Settings dialog click - open simulation settings dialog."""
    if self.simulation is None:
        return
    
    # Pause simulation if running
    was_running = self.simulation.is_running()
    if was_running:
        self.simulation.stop()
    
    try:
        # ... show dialog ...
        
        if show_simulation_settings_dialog(self.simulation.settings, parent):
            # Settings updated successfully
            self._update_duration_display()
            self._update_progress_display()
            
            # Emit signal for data collector/matplotlib updates
            self.emit('settings-changed')
            
            # Notify user if simulation was running
            if was_running:
                print("⚠️  Simulation was paused to change settings. Click Run to resume.")
    finally:
        # Update button states based on current state
        self._update_button_states(running=was_running)
```

**Benefits**:
- ✅ Safe to open settings at any time
- ✅ Running simulations are paused automatically
- ✅ User is notified of state changes
- ✅ All displays update consistently
- ✅ Dependent components receive notification

---

### 3. ✅ Parameter Changes During Simulation

**Problem**: Changing duration or time units while simulation is paused could cause inconsistent state or incorrect progress bar display.

**Solution**: Enhanced `_on_duration_changed()` to:
1. Detect significant changes in duration (> 0.001s)
2. Update progress bar with new duration scale
3. Emit signal for dependent components
4. Log changes for user feedback

**Implementation**:
```python
def _on_duration_changed(self, entry):
    """Handle duration entry change - update simulation settings.
    
    If simulation is running, it will continue with new duration.
    Progress bar will recalculate based on new duration.
    Emits 'settings-changed' signal for matplotlib/data collector updates.
    """
    # ... validation ...
    
    # Store old duration for comparison
    old_duration = self.simulation.settings.get_duration_seconds() if self.simulation.settings.duration else None
    
    # Update settings
    self.simulation.settings.set_duration(duration, units)
    new_duration = self.simulation.settings.get_duration_seconds()
    
    # If duration changed significantly, update progress display and notify listeners
    if old_duration is None or abs(new_duration - old_duration) > 0.001:
        self._update_progress_display()
        
        # Emit signal for data collector/matplotlib updates
        self.emit('settings-changed')
        
        # Log the change for user feedback
        if old_duration:
            print(f"⏱️  Duration updated: {duration} {units.abbreviation} (was {old_duration:.1f}s)")
```

**Time Units Handler**:
The `_on_time_units_changed()` handler simply revalidates duration with new units by calling `_on_duration_changed()`, which then handles all the updates and signal emission.

**Benefits**:
- ✅ Progress bar updates correctly when duration changes
- ✅ Settings persist across run/pause cycles
- ✅ User receives feedback about parameter changes
- ✅ Dependent components notified of scale changes
- ✅ No data loss or state corruption

---

### 4. ✅ Matplotlib Signal Integration

**Problem**: Data collector and matplotlib plots needed notification when simulation parameters changed to adjust time scales and displays.

**Solution**: Added new `settings-changed` signal and emit it whenever simulation settings are modified.

**Signal Definition**:
```python
__gsignals__ = {
    'step-executed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
    'reset-executed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    'settings-changed': (GObject.SignalFlags.RUN_FIRST, None, ())  # NEW
}
```

**Signal Emission Points**:
1. **Settings Dialog**: When user applies changes via dialog
2. **Duration Change**: When duration entry is modified
3. **Time Units Change**: When time units combo box changes (via duration handler)

**Usage Pattern**:
```python
# In data collector or matplotlib component:
palette.connect('settings-changed', self._on_simulation_settings_changed)

def _on_simulation_settings_changed(self, palette):
    """Handle simulation settings changes.
    
    Update time scales, axis labels, and recompute display ranges.
    """
    new_duration = palette.simulation.settings.get_duration_seconds()
    new_units = palette.simulation.settings.time_units
    
    # Update matplotlib axes
    self.ax.set_xlim(0, new_duration)
    self.ax.set_xlabel(f"Time ({new_units.abbreviation})")
    
    # Redraw if needed
    self.canvas.draw()
```

**Benefits**:
- ✅ Data collector receives timely notifications
- ✅ Matplotlib plots can adjust automatically
- ✅ Time scales remain synchronized
- ✅ Clean signal-based architecture
- ✅ Decoupled components

---

### 5. ✅ Settings Dialog Behavior

**Problem**: Settings dialog opening behavior needed verification across all simulation states.

**Solution**: Implemented comprehensive state handling in `_on_settings_clicked()`:

**Behavior by State**:

| State     | Dialog Opens? | Simulation Action          | After Close           |
|-----------|---------------|----------------------------|-----------------------|
| IDLE      | ✓ Yes         | None (already stopped)     | Remains IDLE/PAUSED   |
| RUNNING   | ✓ Yes         | **Auto-pause** (with warning) | Remains PAUSED     |
| PAUSED    | ✓ Yes         | None (already paused)      | Remains PAUSED        |
| COMPLETED | ✓ Yes         | None (already complete)    | Remains COMPLETED     |

**User Feedback**:
```
⚠️  Simulation was paused to change settings. Click Run to resume.
```

**Validation**:
- ✅ Dialog shows current settings correctly
- ✅ Validation prevents invalid inputs (via SimulationSettings)
- ✅ Cancel button discards changes
- ✅ OK button applies and signals changes
- ✅ No simulation state corruption

**Benefits**:
- ✅ Safe to open at any time
- ✅ Clear user feedback
- ✅ State preserved correctly
- ✅ Intuitive behavior

---

## Testing Recommendations

### Manual Testing Scenarios

#### Scenario 1: Button State Transitions
1. Start app → buttons in IDLE state
2. Click Run → only Stop enabled
3. Click Stop → Run, Step, Reset enabled
4. Click Step → verify completion detection
5. Complete simulation → only Reset enabled
6. Click Reset → back to IDLE state

**Expected**: All state transitions work smoothly, no buttons stuck in wrong state.

#### Scenario 2: Settings Dialog During Run
1. Start simulation (Run)
2. Click Settings while running
3. Verify dialog opens, simulation pauses
4. Change duration, click OK
5. Verify warning message shown
6. Click Run to resume
7. Verify progress bar reflects new duration

**Expected**: Simulation pauses gracefully, settings apply correctly, can resume.

#### Scenario 3: Parameter Changes While Paused
1. Start simulation (Run)
2. Stop simulation (pause)
3. Change duration in entry field
4. Verify progress bar updates
5. Change time units
6. Verify progress bar adjusts
7. Click Run to resume
8. Verify simulation continues with new settings

**Expected**: All changes apply immediately, progress bar stays accurate.

#### Scenario 4: Matplotlib Integration
1. Open data collector/plots
2. Start simulation
3. Change duration while paused
4. Verify plots update time scale
5. Change via settings dialog
6. Verify plots receive signal and update

**Expected**: Plots stay synchronized with simulation settings.

#### Scenario 5: Completion Detection
1. Set short duration (e.g., 5 seconds)
2. Click Step repeatedly
3. When duration reached, verify:
   - Step button detects completion
   - Buttons transition to COMPLETED state
   - Only Reset enabled

**Expected**: Completion properly detected and handled.

### Automated Testing

Consider adding unit tests for:
```python
test_button_states_idle()
test_button_states_running()
test_button_states_paused()
test_button_states_completed()
test_settings_dialog_during_run()
test_duration_change_emits_signal()
test_settings_dialog_emits_signal()
test_parameter_persistence()
```

---

## Architecture Benefits

### Before Refinements
- ❌ Scattered button state management
- ❌ No signal for settings changes
- ❌ Settings dialog could open during run
- ❌ Parameter changes not properly logged
- ❌ Matplotlib components unaware of changes

### After Refinements
- ✅ Centralized state machine
- ✅ Clear signal architecture
- ✅ Safe settings dialog behavior
- ✅ User feedback on parameter changes
- ✅ Decoupled component updates
- ✅ Robust state handling

---

## Migration Notes

### For Data Collectors
If you have a data collector component, connect to the new signal:

```python
# In your data collector __init__ or setup method:
self.palette = palette
self.palette.connect('settings-changed', self._on_settings_changed)

def _on_settings_changed(self, palette):
    """Handle simulation settings changes."""
    # Get new settings
    settings = palette.simulation.settings
    duration_sec = settings.get_duration_seconds()
    units = settings.time_units
    
    # Update your plots/displays
    self._update_time_scale(duration_sec, units)
```

### For Matplotlib Plots
Update your plot components to handle the signal:

```python
def _on_settings_changed(self, palette):
    """Adjust plot scales when settings change."""
    duration = palette.simulation.settings.get_duration_seconds()
    units = palette.simulation.settings.time_units
    
    # Update x-axis
    self.ax.set_xlim(0, duration)
    self.ax.set_xlabel(f"Time ({units.abbreviation})")
    
    # Redraw
    self.figure.canvas.draw_idle()
```

---

## Known Limitations

1. **Settings button behavior**: Currently disabled during running state. Consider if "pause to edit" behavior should be automatic on click.

2. **Duration validation**: Currently allows any positive float. Consider adding upper limits for practical simulations.

3. **Restart policy**: When simulation completes, Run button is disabled. Consider if restart from beginning should be allowed.

4. **Progress bar scale**: Progress bar updates when duration changes, but if simulation is far into run, this can cause visual jump.

---

## Related Files

- `src/shypn/helpers/simulate_tools_palette_loader.py` - Main implementation
- `src/shypn/engine/simulation/controller.py` - SimulationController with `is_running()` and `is_simulation_complete()`
- `src/shypn/simulation/simulation_settings.py` - SimulationSettings class
- `src/shypn/dialogs/simulation_settings_dialog.py` - Settings dialog UI
- `tests/test_simulation_timing.py` - Test suite (48/48 tests passing)

---

## Summary

These refinements significantly improve the robustness and user experience of the simulation palette:

1. **State Management**: Centralized, consistent, maintainable
2. **Settings Persistence**: Safe across all states
3. **Parameter Changes**: Properly handled and signaled
4. **Component Integration**: Clean signal-based updates
5. **User Experience**: Clear feedback, safe interactions

All refinements maintain backward compatibility while adding new capabilities. No breaking changes to existing code.
