# Mode Palette - Quick Reference

## What is the Mode Palette?

The mode palette is a floating UI element at the bottom center of the canvas with two buttons:
- **Edit**: Switches to editing mode (create/modify places, transitions, arcs)
- **Sim**: Switches to simulation mode (run, step, stop, reset simulation)

## Location

- **Position**: Bottom center of the canvas
- **Always visible**: Yes (floats above canvas)
- **Independent per tab**: Each tab has its own mode state

## Behavior

### Edit Mode (Default)
- Edit palette ([E] button) is visible on the left
- Edit tools palette (Place/Transition/Arc) accessible via [E] button
- Simulation palettes are hidden
- Edit button is inactive (grayed out)
- Sim button is active (clickable)

### Simulation Mode
- Simulation palette ([S] button) is visible on the right
- Simulation tools (Run/Step/Stop/Reset) accessible via [S] button
- Edit palettes are hidden
- Sim button is inactive (grayed out)
- Edit button is active (clickable)

## Usage

### Switching Modes

1. **To Edit Mode**: Click the "Edit" button
   - Edit palettes appear
   - Simulation palettes disappear
   - You can create and modify network objects

2. **To Simulation Mode**: Click the "Sim" button
   - Simulation palettes appear
   - Edit palettes disappear
   - You can run and analyze the simulation

### Workflow Example

```
1. Start application (Edit mode by default)
2. Click [E] → Select Place tool → Draw places
3. Click [E] → Select Transition tool → Draw transitions
4. Click [E] → Select Arc tool → Connect places and transitions
5. Click "Sim" button → Switch to simulation mode
6. Click [S] → Click Run → Watch tokens move
7. Click [S] → Click Stop → Pause simulation
8. Click "Edit" button → Return to editing
9. Modify network as needed
10. Repeat steps 5-9 as needed
```

## Key Features

### No Palette Overlap
- Only one set of palettes visible at a time
- Clean, uncluttered interface
- Clear separation between editing and simulation

### Intuitive Navigation
- Single click to switch modes
- Visual feedback (button states change)
- Tooltips guide users

### Per-Tab Independence
- Each tab maintains its own mode state
- Switch tabs without affecting mode
- Work in edit mode on one tab, simulation on another

## Technical Details

### Signal Flow
```
User clicks button
  ↓
Mode palette emits 'mode-changed' signal
  ↓
Canvas loader receives signal
  ↓
Palette visibility updated
  ↓
UI reflects new mode
```

### Files Involved
- **UI Definition**: `ui/palettes/mode/mode_palette.ui`
- **Loader**: `src/ui/palettes/mode/mode_palette_loader.py`
- **Integration**: `src/shypn/helpers/model_canvas_loader.py`

## Future Enhancements

- Keyboard shortcut (e.g., Tab key to switch modes)
- Mode indicator in status bar
- Smooth transitions/animations
- Mode state persistence across sessions

## Troubleshooting

### Mode palette not visible
- Check that overlay is properly initialized
- Verify UI file path is correct
- Check for import errors in console

### Palettes not switching
- Verify signal connection in model_canvas_loader.py
- Check that palette widgets have show()/hide() methods
- Look for errors in _on_mode_changed handler

### Button states not updating
- Check update_button_states() is called after mode change
- Verify current_mode is tracking correctly
- Ensure buttons have proper sensitivity settings

## Developer Notes

### Extending the Mode System

To add a new mode:

1. Add button to `mode_palette.ui`
2. Add handler method in `ModePaletteLoader`
3. Update `_update_palette_visibility()` logic
4. Create palettes for new mode
5. Connect signals in `_setup_canvas_manager()`

### Signal API

```python
# Connect to mode-changed signal
mode_palette.connect('mode-changed', callback, *args)

# Callback signature
def callback(palette, mode, *args):
    # mode: str ('edit' or 'sim')
    # Handle mode change
    pass
```

### Widget API

```python
# Get mode palette widget
widget = mode_palette.get_widget()

# Get current mode
current_mode = mode_palette.current_mode  # 'edit' or 'sim'

# Programmatically change mode (emit signal)
mode_palette.emit('mode-changed', 'sim')
```

## Contact

For questions or issues with the mode palette, check:
- Documentation: `doc/mode_palette_implementation.md`
- Implementation plan: `doc/mode_palette_plan.md`
- Code: `src/ui/palettes/mode/`
