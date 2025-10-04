# Simulation Palette Integration

## Overview
The simulation palette provides Run, Stop, and Reset controls for Petri net simulation, positioned beside the edit palette at the bottom center of the canvas.

## Architecture

### Components

1. **Main Palette Button (`simulate_palette.ui`)**
   - Red [S] toggle button (36x36px)
   - Positioned at bottom center with 44px horizontal offset (36px edit button + 8px gap)
   - Styled with red gradient (#e74c3c → #c0392b) to match edit palette's green styling
   - Toggles visibility of simulation tools

2. **Tools Palette (`simulate_tools_palette.ui`)**
   - Revealer container with slide-up animation (200ms)
   - Three tool buttons (40x40px each):
     - **[R] Run**: Start simulation execution
     - **[S] Stop**: Pause simulation (disabled until running)
     - **[T] Reset**: Reset to initial marking
   - Positioned above main button with same horizontal offset

3. **Loader (`simulate_palette_loader.py`)**
   - `SimulatePaletteLoader`: Manages main [S] button
   - `SimulateToolsPaletteLoader`: Manages tools revealer
   - Factory functions: `create_simulate_palette()`, `create_simulate_tools_palette()`
   - Embedded CSS styling for red button appearance

### Integration Points

**File: `src/shypn/helpers/model_canvas_loader.py`**

```python
# Import simulation palettes (line ~60)
from shypn.helpers.simulate_palette_loader import create_simulate_palette, create_simulate_tools_palette

# Palette dictionaries (line ~95)
self.simulate_palettes = {}  # {drawing_area: SimulatePaletteLoader}
self.simulate_tools_palettes = {}  # {drawing_area: SimulateToolsPaletteLoader}

# Create and add to overlay (line ~320)
simulate_tools_palette = create_simulate_tools_palette()
simulate_palette = create_simulate_palette()
simulate_palette.set_tools_palette_loader(simulate_tools_palette)
overlay_widget.add_overlay(simulate_tools_widget)
overlay_widget.add_overlay(simulate_widget)
```

## Positioning Strategy

### Horizontal Layout
```
┌────────────────────────────────────────┐
│                                        │
│              Canvas                    │
│                                        │
│                                        │
│      [E]              [S]              │ ← Bottom center
│      ↑                ↑                │
│      │                └─ 140px offset  │
│      └────────────────── center (0px)  │
│                                        │
│      |<─── 3 buttons ───>|            │
│         gap spacing                    │
└────────────────────────────────────────┘
```

- **Edit palette [E]**: `halign=center`, `margin_start=0`
- **Simulate palette [S]**: `halign=center`, `margin_start=140` (space for ~3 buttons between)
- Both: `valign=end`, `margin_bottom=24`

### Vertical Stack (when revealed)
```
┌──────────────┐
│ [S] [P] [T]  │ ← Edit tools (margin_bottom=78)
└──────────────┘
      [E]        ← Edit button (margin_bottom=24)

┌──────────────┐
│ [R] [S] [T]  │ ← Simulate tools (margin_bottom=78)
└──────────────┘
      [S]        ← Simulate button (margin_bottom=24)
```

## Styling

### Color Scheme
- **Edit Palette [E]**: Green gradient (#2ecc71 → #27ae60)
  - Professional, productivity-focused
  - Associated with creation and construction

- **Simulate Palette [S]**: Red gradient (#e74c3c → #c0392b)
  - Attention-grabbing for execution mode
  - Associated with action and dynamics
  - Distinct from edit mode

### CSS Classes
```css
/* Edit button */
.edit-button {
    background: linear-gradient(to bottom, #2ecc71, #27ae60);
    border: 2px solid #229954;
    /* ... */
}

/* Simulate button */
.simulate-button {
    background: linear-gradient(to bottom, #e74c3c, #c0392b);
    border: 2px solid #a93226;
    /* ... */
}
```

Both follow the same design pattern:
- Gradient background
- 2px solid border
- 6px border radius
- 3-layer shadow (depth + glow)
- Hover state brightens
- Active/checked state darkens with inset shadow

## Connection to Simulation Engine

### TODO Markers (to be implemented)

**File: `ui/simulate/simulate_palette_controller.py`**

```python
def _on_run_clicked(self, button):
    # TODO: self.manager.simulation_engine.start()
    pass

def _on_stop_clicked(self, button):
    # TODO: self.manager.simulation_engine.stop()
    pass

def _on_reset_clicked(self, button):
    # TODO: self.manager.simulation_engine.reset()
    pass
```

### Next Steps

1. **Create Simulation Engine Manager**
   - Instantiate transition engine for current net
   - Manage simulation state (running/stopped)
   - Handle transition firing events

2. **Connect Button Handlers**
   - Replace TODO markers with actual engine calls
   - Update button sensitivity based on state
   - Trigger canvas redraws on marking changes

3. **Add Visual Feedback**
   - Highlight enabled transitions
   - Animate token movement
   - Update place token counts in real-time

4. **Implement Simulation Loop**
   - Use GLib.timeout_add() for step timing
   - Apply transition behaviors (Immediate, Timed, Stochastic, Probabilistic)
   - Handle conflicts (multiple enabled transitions)

## File Structure

```
ui/simulate/
├── __init__.py                       # Module exports
├── simulate_palette.ui               # Main [S] button UI
├── simulate_tools_palette.ui         # [R][S][T] buttons UI
└── simulate_palette_controller.py    # Controller (with TODOs)

src/shypn/helpers/
└── simulate_palette_loader.py        # GTK loaders + CSS styling

src/shypn/engine/                     # Transition engine (ready)
├── __init__.py
├── transition.py                     # Base Transition class
├── immediate_transition.py           # Fires instantly
├── timed_transition.py               # Fires after delay
├── stochastic_transition.py          # Fires with exponential distribution
└── probabilistic_transition.py       # Fires with probability
```

## Usage Flow

1. User clicks [S] button → Tools revealer slides up
2. User clicks [R] Run → Simulation starts
   - [S] Stop button becomes enabled
   - [R] Run button becomes disabled
3. Simulation executes transitions according to their behaviors
4. User clicks [S] Stop → Simulation pauses
   - [S] Stop button becomes disabled
   - [R] Run button becomes enabled
5. User clicks [T] Reset → Marking restored to initial state
   - All token counts reset
   - Canvas redraws

## Testing

### Manual Testing Steps
1. Launch application: `python3 src/shypn.py`
2. Open a Petri net model
3. Verify [E] and [S] buttons appear side-by-side at bottom center
4. Click [E] → Edit tools should appear
5. Click [S] → Simulation tools should appear
6. Verify [S] button is red (vs [E] green)
7. Click [R] → Should log "Run clicked" (currently no-op)
8. Verify [S] Stop button becomes enabled
9. Click [T] → Should restore marking (if places exist)

### Automated Tests
- Palette loading: `python3 test_simulate_palette.py` (requires GTK)
- Syntax check: `python3 -m py_compile src/shypn/helpers/simulate_palette_loader.py`

## Implementation Status

✅ **Completed**:
- UI definitions (simulate_palette.ui, simulate_tools_palette.ui)
- Loader classes (SimulatePaletteLoader, SimulateToolsPaletteLoader)
- CSS styling (red button matching edit palette style)
- Integration into model_canvas_loader.py
- Positioning calculation (44px offset to prevent overlap)
- Controller skeleton with state management

⏳ **Pending**:
- Simulation engine manager instantiation
- Button handler implementation (replace TODOs)
- Visual feedback during simulation
- Transition firing logic
- Token animation

## Related Documentation
- `doc/EDIT_PALETTE_ARCHITECTURE.md` - Edit palette design patterns
- `doc/TRANSITION_ENGINE_COMPLETE_INDEX.md` - Simulation engine details
- `doc/CANVAS_ARCHITECTURE.md` - Overall canvas architecture
