# Context Menu Fix - GTK4 PopoverMenu Issue

## Problem Diagnosis

The debug output revealed:
```
🖱️  Right-click detected at (x, y)     ✓ Gesture working!
✓ Context menu exists                  ✓ Menu object created!
→ Calling popup()...                   ✓ Method called!
→ popup() called!                      ✓ No errors!
```

But the menu **doesn't appear visually**!

## Root Cause

**GTK4 PopoverMenu uses `present()` not `popup()`!**

In GTK3, menus used `popup()`, but GTK4's `Gtk.PopoverMenu` uses `present()` to display.

## Fix Applied

Changed from:
```python
self.context_menu.popup()
```

To:
```python
self.context_menu.present()
```

## How to Test

1. **Stop any running instances:**
   ```bash
   killall python3
   ```

2. **Run the app:**
   ```bash
   cd /home/simao/projetos/shypn
   python3 src/shypn.py
   ```

3. **Right-click in the file browser**
   - Click on a file/folder
   - OR click on empty space

4. **Context menu should now appear!**

## What Changed

**File:** `src/shypn/ui/panels/file_explorer_panel.py`
**Method:** `_on_tree_view_right_click()`
**Line:** ~577

```python
# OLD (GTK3 style):
self.context_menu.popup()

# NEW (GTK4 style):
self.context_menu.present()
```

## GTK3 vs GTK4 Differences

### GTK3 (Old)
```python
menu = Gtk.Menu()
menu.popup(...)  # Show menu
```

### GTK4 (New)
```python
menu = Gtk.PopoverMenu()
menu.present()  # Show menu
```

## Testing Commands

### Full debug output:
```bash
python3 src/shypn.py 2>&1 | grep -E "(🖱️|✓|→|present)"
```

### Watch for menu appearance:
```bash
python3 src/shypn.py 2>&1 | grep "present" --line-buffered
```

## Expected Behavior Now

1. Right-click anywhere in file browser
2. See debug output: `→ Context menu present() called`
3. **Menu appears at mouse position** ✨
4. Click menu item to perform action

## Menu Items Available

- **Open** - Open selected file
- **New Folder** - Create new folder
- **Cut** - Cut file/folder
- **Copy** - Copy file/folder
- **Paste** - Paste clipboard contents
- **Duplicate** - Duplicate item
- **Rename** - Rename item
- **Delete** - Delete item
- **Refresh** - Refresh file list
- **Properties** - View item properties

## If Menu Still Doesn't Appear

Try these alternatives:

### 1. Check GTK version
```bash
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print(Gtk.get_major_version(), Gtk.get_minor_version())"
```

### 2. Try popup_at_pointer()
```python
self.context_menu.popup_at_pointer(None)
```

### 3. Use set_visible()
```python
self.context_menu.set_visible(True)
self.context_menu.present()
```

### 4. Check if parent is correct
```python
print(f"Menu parent: {self.context_menu.get_parent()}")
```

## Status

✅ Gesture detection working
✅ Context menu object created
✅ Menu items configured
✅ Actions registered
🔄 Changed `popup()` to `present()`
⏳ Waiting for test results...

## Quick Test Script

```bash
#!/bin/bash
cd /home/simao/projetos/shypn
echo "Starting app..."
echo "Right-click in file browser to test!"
python3 src/shypn.py
```

Save as `test_menu.sh`, make executable with `chmod +x test_menu.sh`, and run!
