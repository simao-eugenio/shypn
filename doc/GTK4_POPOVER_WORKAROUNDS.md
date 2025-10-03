# GTK4 Popover Issues and Workarounds (WSL/Linux)

## Common Issues

### 1. Frozen/Leftover Popovers
**Symptoms:**
- Popover stays visible even after clicking outside
- `set_autohide(True)` doesn't work
- Popover appears but never dismisses

**Root Causes:**
- WSL1/WSL2 limited windowing support
- XWayland compositor limitations
- Event handling conflicts with gesture controllers
- GTK4 version-specific bugs

### 2. PopoverMenu Not Appearing
**Symptoms:**
- `popup()` or `present()` called successfully but nothing shows
- No errors in console
- Works in native Linux but not WSL

**Root Causes:**
- `Gtk.PopoverMenu` with `Gio.Menu` is unstable in many GTK4 versions
- Action system conflicts
- Parent widget constraints

## Proven Workarounds

### Workaround 1: Use Simple Popover Instead of PopoverMenu ✅ (IMPLEMENTED)
```python
# DON'T USE (buggy):
popover = Gtk.PopoverMenu()
popover.set_menu_model(menu_model)

# USE THIS INSTEAD:
popover = Gtk.Popover()
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
button = Gtk.Button(label="Item")
button.set_has_frame(False)
button.connect("clicked", callback)
box.append(button)
popover.set_child(box)
```

### Workaround 2: Manual Popover Dismissal
```python
def on_button_clicked(self, button):
    # Always explicitly close popover
    self.popover.popdown()
    # Then do action
    self.perform_action()
```

### Workaround 3: Add Manual Dismiss on Outside Click
```python
# Add click controller to main window
click_controller = Gtk.GestureClick.new()
click_controller.connect('pressed', self._on_window_clicked)
window.add_controller(click_controller)

def _on_window_clicked(self, gesture, n_press, x, y):
    # Close any open popovers
    if self.popover and self.popover.get_visible():
        self.popover.popdown()
```

### Workaround 4: Use Gtk.Rectangle Correctly (GTK4)
```python
# GTK3 (OLD):
rect = Gtk.Rectangle()  # ❌ Doesn't exist in GTK4

# GTK4 (NEW):
rect = Gdk.Rectangle()  # ✅ Use Gdk not Gtk
rect.x = int(x)
rect.y = int(y)
rect.width = 1
rect.height = 1
popover.set_pointing_to(rect)
```

### Workaround 5: Force Popover to Front
```python
# After popup(), force it to be topmost
popover.popup()
popover.present()  # Call both
popover.grab_focus()  # Try to grab focus
```

### Workaround 6: Use Timeout for Stubborn Popovers
```python
def show_popover(self, x, y):
    rect = Gdk.Rectangle()
    rect.x = int(x)
    rect.y = int(y)
    rect.width = 1
    rect.height = 1
    self.popover.set_pointing_to(rect)
    
    # Try multiple times with delay
    self.popover.popup()
    GLib.timeout_add(10, lambda: self.popover.present())
    GLib.timeout_add(20, lambda: self.popover.set_visible(True))
```

### Workaround 7: Context Menu on Drag Release (Canvas)
```python
# For canvas that uses right-click for panning:
# Show menu only if no drag occurred

def _on_right_drag_end(self, gesture, offset_x, offset_y, manager, drawing_area):
    # Check if it was actually a drag or just a click
    drag_distance = (offset_x**2 + offset_y**2)**0.5
    if drag_distance < 5:  # Less than 5px = click
        start_x, start_y = gesture.get_start_point()
        self._show_context_menu(start_x, start_y)
    else:
        # It was a drag, handle panning
        self._handle_pan(offset_x, offset_y)
```

### Workaround 8: Alternative - Use Floating Window
```python
# If popovers are too problematic, use an undecorated window:
menu_window = Gtk.Window()
menu_window.set_decorated(False)
menu_window.set_transient_for(main_window)
menu_window.set_modal(True)
menu_window.set_default_size(200, -1)

# Position at cursor
display = Gdk.Display.get_default()
seat = display.get_default_seat()
pointer = seat.get_pointer()
_, x, y = pointer.get_surface().get_device_position(pointer)
menu_window.move(x, y)
menu_window.present()
```

### Workaround 9: Check WSL Display Backend
```bash
# Check if running under X11 or Wayland
echo $XDG_SESSION_TYPE

# For WSL, X11 is more reliable:
export GDK_BACKEND=x11

# Or in Python:
import os
os.environ['GDK_BACKEND'] = 'x11'
```

### Workaround 10: Upgrade GTK4 Version
```bash
# Check current version
pkg-config --modversion gtk4

# Upgrade to latest (many popover bugs fixed in 4.10+)
sudo apt update
sudo apt install libgtk-4-dev

# Or use flatpak runtime for newer GTK4
```

## Testing Checklist

- [ ] Popover appears when triggered
- [ ] Popover dismisses when clicking outside
- [ ] Popover dismisses when pressing Escape
- [ ] Popover doesn't interfere with other interactions
- [ ] Popover positioning is correct
- [ ] Menu items are clickable
- [ ] Menu items trigger correct actions
- [ ] No frozen popovers after multiple uses

## Environment-Specific Notes

### WSL1
- Limited compositor support
- Use X11 backend (`GDK_BACKEND=x11`)
- Simple Popover works better than PopoverMenu

### WSL2
- Better graphics support with WSLg
- Still has some compositor limitations
- Test with both X11 and Wayland

### Native Linux
- Generally works well with GTK 4.10+
- Wayland is preferred backend
- PopoverMenu should work on recent versions

## References

- GTK4 PopoverMenu known issues: https://gitlab.gnome.org/GNOME/gtk/-/issues
- GTK4 Migration Guide: https://docs.gtk.org/gtk4/migrating-3to4.html
- WSL Graphics: https://github.com/microsoft/wslg

## Current Implementation Status

✅ Using simple `Gtk.Popover` instead of `Gtk.PopoverMenu`
✅ Using `Gdk.Rectangle` instead of `Gtk.Rectangle`
✅ Manual `popdown()` in all button handlers
✅ Canvas: Context menu only on click (no drag)
✅ File Browser: Context menu on right-click

## Remaining Issues

⚠️ Need to test autohide behavior
⚠️ May need manual window click handler to force close
⚠️ Consider adding Escape key handler to close popover
