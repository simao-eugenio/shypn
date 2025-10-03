# Canvas Context Menu - Test Implementation

## Purpose

Test if GTK4 PopoverMenu works at all by implementing a simple context menu on the model canvas.

## Implementation

### Location
`src/shypn/helpers/model_canvas_loader.py`

### Features Added

#### Context Menu Items:
1. **Clear Canvas** - Clears all objects from canvas (placeholder for now)
2. **Reset Zoom** - Resets zoom to 100%
3. **Center View** - Centers the viewport

#### Key Technical Details:

1. **Right-click Detection in CAPTURE Phase**
   ```python
   context_menu_gesture = Gtk.GestureClick.new()
   context_menu_gesture.set_button(3)
   context_menu_gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
   ```
   
2. **Event Claiming to Prevent Panning**
   ```python
   gesture.set_state(Gtk.EventSequenceState.CLAIMED)
   ```

3. **PopoverMenu Setup**
   ```python
   popover = Gtk.PopoverMenu()
   popover.set_menu_model(menu)
   popover.set_parent(drawing_area)
   popover.set_has_arrow(False)
   popover.set_autohide(True)
   ```

4. **Showing the Menu**
   ```python
   popover.set_pointing_to(rect)
   popover.popup()
   ```

## How to Test

1. **Run the application:**
   ```bash
   cd /home/simao/projetos/shypn
   python3 src/shypn.py
   ```

2. **Right-click on the canvas** (the white drawing area in the center)

3. **Expected behavior:**
   - Context menu should appear instantly
   - Menu shows: Clear Canvas, Reset Zoom, Center View
   - Clicking an item triggers the action (you'll see print output)

4. **Check terminal output:**
   ```
   🖱️  Canvas right-click at (x, y)
     → Showing canvas context menu...
     → popup() called!
   ```

## Why This Test?

### Isolating the Problem

The file browser context menu has these complications:
- TreeView widget intercepting events
- ScrolledWindow wrapper
- Complex hierarchy
- Multiple gesture handlers

The canvas is simpler:
- Direct DrawingArea widget
- Minimal event complexity
- Clear parent/child relationship

### What We'll Learn

#### If Canvas Menu Works:
✅ PopoverMenu works in GTK4
✅ Our setup code is correct
→ Problem is specific to file browser (TreeView/ScrolledWindow interaction)

#### If Canvas Menu Doesn't Work:
✗ PopoverMenu might not work in this GTK4 version
✗ System/environment issue
→ Need alternative approach (Gtk.Menu, custom widget, etc.)

## Comparison: File Browser vs Canvas

### File Browser Setup:
```python
# File browser (NOT working)
popover.set_parent(self.tree_view)  # TreeView parent
popover.set_pointing_to(rect)
popover.popup()  # or present()
# Menu doesn't appear
```

### Canvas Setup:
```python
# Canvas (testing now)
popover.set_parent(drawing_area)  # DrawingArea parent
popover.set_pointing_to(rect)
popover.popup()
# Will this work?
```

## Debug Output to Watch For

### Success Case:
```
✓ Canvas context menu configured
🖱️  Canvas right-click at (123, 456)
  → Showing canvas context menu...
  → popup() called!
✓ Reset Zoom action triggered!  (if you click the menu item)
```

### Failure Case:
```
✓ Canvas context menu configured
🖱️  Canvas right-click at (123, 456)
  → Showing canvas context menu...
  → popup() called!
(but nothing appears visually)
```

## Next Steps Based on Results

### If It Works:
1. Apply same approach to file browser
2. Check parent widget differences
3. Test with different parent (ScrolledWindow vs TreeView)
4. May need to restructure file browser menu setup

### If It Doesn't Work:
1. Try alternative menu methods:
   - `present()` instead of `popup()`
   - `set_visible(True)`
   - `popup_at_pointer()`
2. Check GTK4 version compatibility
3. Consider fallback to custom popover widget
4. Research GTK4 PopoverMenu known issues

## Alternative Approaches if PopoverMenu Fails

### Option 1: Gtk.Popover with Custom Content
```python
popover = Gtk.Popover()
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
# Add buttons manually
popover.set_child(box)
```

### Option 2: Floating Window
```python
window = Gtk.Window()
window.set_decorated(False)
# Position at cursor
```

### Option 3: Custom Widget Overlay
```python
# Add to overlay layer
menu_widget = CustomMenuWidget()
overlay.add_overlay(menu_widget)
```

## Files Modified

- `src/shypn/helpers/model_canvas_loader.py`
  - Added `_setup_canvas_context_menu()`
  - Added `_on_context_menu_request()`
  - Added `_on_clear_canvas()`, `_on_reset_zoom()`, `_on_center_view()`
  - Modified `_setup_event_controllers()` to add context menu gesture

## Status

✅ Canvas context menu implemented
✅ Event claiming configured
✅ Menu actions wired up
⏳ Awaiting test results

---

**Please right-click on the canvas and report if the menu appears!** 🎯
