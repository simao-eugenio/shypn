# Palette Reveal Fix - Debug Session

## Problem
The [E] and [S] buttons were not revealing their respective tools palettes when clicked.

## Root Cause Analysis

### Issue 1: Missing `show()` and `hide()` Methods
The `SimulateToolsPaletteLoader` was using `set_revealed()` method directly, but the main palette was calling methods that didn't exist. The `EditToolsLoader` has `show()` and `hide()` methods that wrap `set_reveal_child()`.

**Fix**: Added `show()` and `hide()` methods to `SimulateToolsPaletteLoader`:
```python
def show(self) -> None:
    """Show the tools palette with animation."""
    if self.simulate_tools_revealer:
        self.simulate_tools_revealer.set_reveal_child(True)

def hide(self) -> None:
    """Hide the tools palette with animation."""
    if self.simulate_tools_revealer:
        self.simulate_tools_revealer.set_reveal_child(False)
```

### Issue 2: Inconsistent Toggle Handler
The `SimulatePaletteLoader._on_simulate_toggle()` was calling `set_revealed()` instead of `show()`/`hide()` like the edit palette does.

**Fix**: Updated to match edit palette pattern:
```python
def _on_simulate_toggle(self, toggle_button: Gtk.ToggleButton) -> None:
    is_active = toggle_button.get_active()
    
    if self.tools_palette_loader:
        if is_active:
            self.tools_palette_loader.show()
        else:
            self.tools_palette_loader.hide()
```

## Debug Logging Added

Added comprehensive debug output to trace the reveal flow:

### SimulatePaletteLoader
```python
def _on_simulate_toggle(self, toggle_button: Gtk.ToggleButton) -> None:
    is_active = toggle_button.get_active()
    print(f"[SimulatePalette] Toggle clicked: is_active={is_active}, has_tools_loader={self.tools_palette_loader is not None}")
    
    if self.tools_palette_loader:
        if is_active:
            print("[SimulatePalette] Calling tools_palette_loader.show()")
            self.tools_palette_loader.show()
        else:
            print("[SimulatePalette] Calling tools_palette_loader.hide()")
            self.tools_palette_loader.hide()
    else:
        print("[SimulatePalette] WARNING: tools_palette_loader is None!")
```

### SimulateToolsPaletteLoader
```python
def show(self) -> None:
    print(f"[SimulateToolsPalette] show() called, revealer={self.simulate_tools_revealer is not None}")
    if self.simulate_tools_revealer:
        print("[SimulateToolsPalette] Setting reveal_child to True")
        self.simulate_tools_revealer.set_reveal_child(True)

def hide(self) -> None:
    print(f"[SimulateToolsPalette] hide() called, revealer={self.simulate_tools_revealer is not None}")
    if self.simulate_tools_revealer:
        print("[SimulateToolsPalette] Setting reveal_child to False")
        self.simulate_tools_revealer.set_reveal_child(False)
```

### EditPaletteLoader (for comparison)
```python
def _on_edit_toggled(self, toggle_button):
    is_active = toggle_button.get_active()
    print(f"[EditPalette] Toggle clicked: is_active={is_active}, has_tools_loader={self.tools_palette_loader is not None}")
    
    if self.tools_palette_loader:
        if is_active:
            print("[EditPalette] Calling tools_palette_loader.show()")
            self.tools_palette_loader.show()
        else:
            print("[EditPalette] Calling tools_palette_loader.hide()")
            self.tools_palette_loader.hide()
    else:
        print("[EditPalette] WARNING: tools_palette_loader is None!")
```

## Expected Console Output

When clicking [E] button:
```
[EditPalette] Toggle clicked: is_active=True, has_tools_loader=True
[EditPalette] Calling tools_palette_loader.show()
[EditToolsPalette] show() called, revealer=True
[EditToolsPalette] Setting reveal_child to True
```

When clicking [S] button:
```
[SimulatePalette] Toggle clicked: is_active=True, has_tools_loader=True
[SimulatePalette] Calling tools_palette_loader.show()
[SimulateToolsPalette] show() called, revealer=True
[SimulateToolsPalette] Setting reveal_child to True
```

## Testing Steps

1. Launch application: `python3 src/shypn.py`
2. Open a Petri net model
3. Click [E] button:
   - Watch console for debug output
   - Verify edit tools slide up
4. Click [E] again:
   - Watch console for hide output
   - Verify edit tools slide down
5. Click [S] button:
   - Watch console for debug output
   - Verify simulate tools slide up
6. Click [S] again:
   - Watch console for hide output
   - Verify simulate tools slide down

## Diagnostic Questions

If palettes still don't reveal:

1. **Is the toggle handler being called?**
   - Look for `[EditPalette] Toggle clicked` or `[SimulatePalette] Toggle clicked`
   - If missing: Signal connection failed

2. **Is tools_palette_loader set?**
   - Check for `has_tools_loader=True`
   - If False: `set_tools_palette_loader()` not called in model_canvas_loader.py

3. **Is show() being called?**
   - Look for `Calling tools_palette_loader.show()`
   - If missing: Logic issue in toggle handler

4. **Does revealer exist?**
   - Check for `revealer=True` in show/hide output
   - If False: UI file not loaded correctly

5. **Is set_reveal_child() being called?**
   - Look for `Setting reveal_child to True`
   - If missing: Revealer not found in loaded UI

## Files Modified

1. **src/shypn/helpers/simulate_palette_loader.py**
   - Added `show()` and `hide()` methods to `SimulateToolsPaletteLoader`
   - Updated `_on_simulate_toggle()` to use show/hide
   - Added debug logging throughout

2. **src/shypn/helpers/edit_palette_loader.py**
   - Added debug logging to `_on_edit_toggled()`

## Integration Points

Both palettes follow the same pattern now:

```python
# In model_canvas_loader.py
edit_tools_palette = create_edit_tools_palette()
edit_palette = create_edit_palette()
edit_palette.set_tools_palette_loader(edit_tools_palette)

simulate_tools_palette = create_simulate_tools_palette()
simulate_palette = create_simulate_palette()
simulate_palette.set_tools_palette_loader(simulate_tools_palette)
```

## Next Steps

1. Run the application and test both palettes
2. Review console output to identify any remaining issues
3. Once working, remove debug print statements
4. Add unit tests for palette reveal/hide functionality

## Success Criteria

✅ [E] button toggles edit tools palette visibility  
✅ [S] button toggles simulate tools palette visibility  
✅ Tools slide up smoothly (200ms animation)  
✅ Tools slide down when button clicked again  
✅ Both palettes work independently  
✅ No console errors during toggle operations
