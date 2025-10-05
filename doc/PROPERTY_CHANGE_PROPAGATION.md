# Property Change Propagation During Simulation

## Problem Statement

During simulation time, between sessions (after Stop/Reset but before next Run), users can interactively modify:
- **Places**: Number of tokens via properties dialog
- **Transitions**: Type, rate, priority, guard functions via properties dialog

These changes need to be properly propagated to:
1. **Simulation Controller** - To use updated transition behaviors
2. **Analysis Panels** - To reflect updated property values in plots

## Previous Behavior

When a user edited object properties via the properties dialog:
- ✅ Properties were updated in the model objects (Place/Transition)
- ✅ Canvas was redrawn to show visual changes
- ❌ SimulationController behavior cache was NOT cleared
- ❌ Analysis panels were NOT notified about changes

**Consequences:**
- Simulation would use **stale behavior** for transitions (old rate/priority/type)
- Analysis plots would not immediately reflect property changes
- Users had to restart the application to see behavior changes

## Solution Implemented

### Overview

Extended the `properties-changed` signal handler in `ModelCanvasLoader._on_object_properties()` to:
1. Clear simulation behavior cache for changed transitions
2. Mark analysis panels for update when selected objects change

**Additionally**, added reset notification mechanism:
3. Emit `reset-executed` signal when Reset button is clicked
4. Mark analysis panels for update to show initial markings after reset

### Technical Details

**Files Modified:** 
- `src/shypn/helpers/model_canvas_loader.py`
- `src/shypn/helpers/simulate_tools_palette_loader.py`

**1. Enhanced `on_properties_changed()` callback:**

```python
def on_properties_changed(_):
    # Existing: Canvas redraw
    drawing_area.queue_draw()
    
    # NEW: Notify simulation controller about transition changes
    if isinstance(obj, Transition) and drawing_area in self.simulate_tools_palettes:
        simulate_tools = self.simulate_tools_palettes[drawing_area]
        if simulate_tools.simulation:
            # Clear behavior cache for this transition
            if obj.id in simulate_tools.simulation.behavior_cache:
                del simulate_tools.simulation.behavior_cache[obj.id]
                print(f"[ModelCanvasLoader] Cleared behavior cache for transition {obj.id}")
    
    # NEW: Notify analysis panels about property changes
    if isinstance(obj, (Place, Transition)) and self.right_panel_loader:
        if isinstance(obj, Place):
            # Mark place panel for update if this place is selected
            if obj in self.right_panel_loader.place_panel.selected_objects:
                self.right_panel_loader.place_panel.needs_update = True
        
        if isinstance(obj, Transition):
            # Mark transition panel for update if this transition is selected
            if obj in self.right_panel_loader.transition_panel.selected_objects:
                self.right_panel_loader.transition_panel.needs_update = True
```

**2. Added Reset Notification (`simulate_tools_palette_loader.py`):**

```python
# Added new signal
__gsignals__ = {
    'step-executed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
    'reset-executed': (GObject.SignalFlags.RUN_FIRST, None, ()),  # NEW
}

# Emit signal in _on_reset_clicked()
def _on_reset_clicked(self, button):
    self.simulation.reset()
    self.emit('reset-executed')  # NEW: Notify listeners
    # ... button state updates ...
```

**3. Added Reset Handler (`model_canvas_loader.py`):**

```python
# Connect reset signal
simulate_tools_palette.connect('reset-executed', self._on_simulation_reset)

# Handler marks analysis panels for update
def _on_simulation_reset(self, palette):
    if self.right_panel_loader:
        if self.right_panel_loader.place_panel:
            self.right_panel_loader.place_panel.needs_update = True
        if self.right_panel_loader.transition_panel:
            self.right_panel_loader.transition_panel.needs_update = True
```

### Architecture Flow

```
User edits properties
    ↓
PlacePropDialogLoader / TransitionPropDialogLoader
    ↓
_apply_changes() → Update object properties
    ↓
emit('properties-changed')
    ↓
on_properties_changed() callback
    ↓
    ├─> Canvas redraw (existing)
    ├─> Clear SimulationController.behavior_cache[transition_id] (NEW)
    └─> Set analysis_panel.needs_update = True (NEW)
        ↓
    Next simulation step uses fresh behavior
    Next plot update shows new data

User clicks Reset button
    ↓
SimulateToolsPaletteLoader._on_reset_clicked()
    ↓
simulation.reset() → Restore initial markings
    ↓
emit('reset-executed')
    ↓
_on_simulation_reset() callback
    ↓
    ├─> Set place_panel.needs_update = True (NEW)
    └─> Set transition_panel.needs_update = True (NEW)
        ↓
    Next plot update shows reset state
```

## Benefits

### 1. Simulation Correctness
- ✅ Transition behavior (rate, type, priority) is immediately updated
- ✅ No need to restart simulation to pick up changes
- ✅ Behavior cache is surgically cleared only for changed transitions

### 2. Analysis Panel Accuracy
- ✅ Plots reflect current property values
- ✅ Selected objects show updated data on next refresh
- ✅ Minimal performance impact (only marks needs_update flag)

### 3. User Experience
- ✅ Interactive property editing during simulation pauses
- ✅ Immediate feedback for property changes
- ✅ Consistent behavior across canvas, simulation, and analysis views
- ✅ Reset button updates analysis plots to show initial markings

## Testing Scenarios

### Scenario 1: Transition Rate Change
1. Run simulation with transition T1 (rate=1.0)
2. Stop simulation
3. Edit T1 properties → change rate to 5.0
4. Resume simulation
5. **Expected:** T1 fires 5x faster (behavior cache cleared)
6. **Expected:** If T1 is in analysis panel, plot updates with new firing pattern

### Scenario 2: Place Token Change
1. Run simulation with place P1 (tokens=10)
2. Stop simulation
3. Edit P1 properties → change tokens to 50
4. Resume simulation or step
5. **Expected:** Simulation continues with 50 tokens in P1
6. **Expected:** If P1 is in analysis panel, plot shows token change

### Scenario 3: Transition Type Change
1. Run simulation with transition T1 (type=immediate)
2. Stop simulation
3. Edit T1 properties → change type to timed
4. Resume simulation
5. **Expected:** T1 behaves as timed transition (behavior cache cleared)

### Scenario 4: Reset Button Updates Plots
1. Run simulation, modify place tokens during execution
2. Stop simulation
3. Click Reset button
4. **Expected:** All places return to initial_marking values
5. **Expected:** Analysis plots immediately refresh to show reset token values
6. **Expected:** Transition analysis plots also refresh to show reset state

## Implementation Notes

### Why Behavior Cache Clearing?

The `SimulationController` caches `TransitionBehavior` instances for performance:
```python
self.behavior_cache = {}  # {transition_id: TransitionBehavior}
```

When a transition's properties change (rate, type, priority), the cached behavior becomes **stale**. 
Clearing the cache forces the controller to create a fresh behavior instance with updated properties.

### Why `needs_update` Flag?

Analysis panels use periodic updates (100ms interval) to refresh plots:
```python
def _periodic_update(self):
    if self.needs_update or self.selected_objects:
        self._update_plot()
        self.needs_update = False
```

Setting `needs_update = True` ensures the next periodic update will refresh the plot, showing the updated property values.

### Why Reset Signal?

When users click the Reset button, all places are restored to their `initial_marking` values. The analysis plots need to immediately reflect this state change:
- Place token plots show the reset token counts
- Transition firing plots show the reset enablement state

Emitting a `reset-executed` signal allows the analysis panels to be notified without tight coupling between the simulation palette and the analysis panels.

### Thread Safety

All operations occur on the GTK main thread (via GLib.timeout_add), so no locking is required.

## Future Enhancements

1. **Batch Property Changes**: If user edits multiple objects, batch cache clearing
2. **Property Change Events**: Add more granular events (e.g., 'token-changed', 'rate-changed')
3. **Undo/Redo Support**: Track property changes for undo/redo functionality
4. **Data Collector Notification**: Optionally reset collector data when properties change significantly

## Related Files

- `src/shypn/helpers/model_canvas_loader.py` - Property change and reset notification logic
- `src/shypn/helpers/simulate_tools_palette_loader.py` - Reset signal emission
- `src/shypn/helpers/place_prop_dialog_loader.py` - Place properties dialog
- `src/shypn/helpers/transition_prop_dialog_loader.py` - Transition properties dialog
- `src/shypn/engine/simulation/controller.py` - Behavior cache management
- `src/shypn/analyses/plot_panel.py` - Analysis panel update mechanism

## Commit

**Title:** Add property change and reset notifications to analysis panels

**Description:**
- Clear simulation behavior cache when transition properties change
- Mark analysis panels for update when selected object properties change
- Add 'reset-executed' signal to SimulateToolsPaletteLoader
- Notify analysis panels when Reset button is clicked
- Ensures simulation uses fresh behavior after property edits
- Ensures analysis plots reflect updated property values and reset state
- Improves interactive editing during simulation pauses

**Files Changed:**
- `src/shypn/helpers/model_canvas_loader.py`
- `src/shypn/helpers/simulate_tools_palette_loader.py`
- `doc/PROPERTY_CHANGE_PROPAGATION.md`

**Date:** 2025-10-04
