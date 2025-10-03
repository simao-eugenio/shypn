# Context Menu Troubleshooting Guide

## Issue
Context menu is not appearing when right-clicking in the file browser.

## Changes Made to Fix

### 1. Added Debug Output
Added extensive debug logging to track:
- When right-click is detected
- Whether context menu object exists
- What coordinates were clicked
- Whether clicking on item or empty space

### 2. Dual Gesture Handlers
Added gesture handlers to BOTH:
- TreeView widget (catches clicks on items)
- ScrolledWindow widget (catches clicks that might be intercepted)

### 3. Enhanced Right-Click Handler
The handler now:
- Logs all click events
- Checks if context menu exists
- Handles both item clicks and empty space clicks
- Shows detailed debug information

## Files Modified

**src/shypn/ui/panels/file_explorer_panel.py:**
- Added `_on_scroll_window_right_click()` method
- Enhanced `_on_tree_view_right_click()` with debug output
- Added gesture handler to scrolled window
- Added comprehensive logging

## How to Test

### Quick Test (Interactive)
```bash
cd /home/simao/projetos/shypn
./scripts/run_with_debug.sh
```

Then:
1. Wait for app to load (you'll see ✓ messages)
2. Right-click anywhere in file browser
3. Watch terminal for debug output

### Expected Output When Right-Clicking

**If gesture is detected:**
```
🖱️  Right-click detected at (123.0, 456.0)
✓ Context menu exists: <Gtk.PopoverMenu object>
  → Clicked on item: test_model.json
  → Showing context menu...
  → Context menu popup() called
```

**If context menu doesn't exist:**
```
🖱️  Right-click detected at (123.0, 456.0)
✗ Context menu is None!
```

**If gesture NOT detected:**
```
(no output at all)
```

## Possible Issues and Solutions

### Issue 1: No Output (Gesture Not Triggered)
**Symptom:** No debug output when right-clicking
**Possible Causes:**
- Gesture controller not properly attached
- Another widget consuming the event
- ScrolledWindow blocking events

**Solution:** We added gesture to both TreeView AND ScrolledWindow

### Issue 2: "Context menu is None"
**Symptom:** Right-click detected but menu object doesn't exist
**Possible Causes:**
- Menu model not found in UI file
- PopoverMenu not properly created
- Menu setup failed

**Solution:** Check if menu model "file_browser_context_menu" exists in left_panel.ui

### Issue 3: popup() Called But Menu Doesn't Show
**Symptom:** Debug says "popup() called" but menu doesn't appear
**Possible Causes:**
- Parent widget issue
- Pointing rectangle invalid
- Menu model empty
- GTK4 version incompatibility

**Solution:** May need to use different approach (Gtk.Menu, different popup method)

## Debug Commands

### Check if context menu model exists in UI
```bash
grep -n "file_browser_context_menu" ui/panels/left_panel.ui
```

### Check gesture setup in code
```bash
grep -n "GestureClick" src/shypn/ui/panels/file_explorer_panel.py
```

### Watch all app output including debug
```bash
python3 src/shypn.py 2>&1 | tee app_output.log
```

## Alternative Approaches to Try

If current approach doesn't work, we can try:

### Approach 1: Use Gtk 4 Popover.present()
Instead of `popup()`, try `present()`

### Approach 2: Use legacy GtkMenu (if available in GTK4)
Create menu programmatically instead of from model

### Approach 3: Handle button-press-event
Use lower-level event handling

### Approach 4: Secondary-click gesture
GTK4 has GestureClick with secondary button signal

## Current Code Structure

```python
# Setup (in __init__)
self._setup_context_menu()  # Creates menu
self._connect_signals()     # Adds gesture handlers

# Context Menu Setup
def _setup_context_menu(self):
    # Create actions
    self.action_group = Gio.SimpleActionGroup()
    # ... add actions ...
    
    # Create menu from UI file
    menu_model = self.builder.get_object("file_browser_context_menu")
    self.context_menu = Gtk.PopoverMenu()
    self.context_menu.set_menu_model(menu_model)
    self.context_menu.set_parent(self.tree_view)

# Gesture Handler
def _on_tree_view_right_click(self, gesture, n_press, x, y):
    # Debug output
    # Get clicked item or use current directory
    # Show menu at click position
    self.context_menu.popup()
```

## Next Steps

1. **Run the debug script:**
   ```bash
   ./scripts/run_with_debug.sh
   ```

2. **Right-click in the file browser**

3. **Check terminal output:**
   - If you see 🖱️  : Gesture IS working
   - If you see ✗ : Menu object doesn't exist
   - If you see nothing: Gesture NOT working

4. **Report back with:**
   - What debug output you see (if any)
   - Whether menu appears
   - Any error messages

## GTK4 PopoverMenu Notes

GTK4 uses `Gtk.PopoverMenu` which is different from GTK3's `Gtk.Menu`:
- Must have a parent widget
- Uses `set_menu_model()` with Gio.Menu
- Uses `popup()` or `present()` to show
- Position set with `set_pointing_to()`

Our implementation follows GTK4 best practices but there might be environment-specific issues.
