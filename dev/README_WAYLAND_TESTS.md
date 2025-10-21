# Wayland Panel Test Scripts

## Overview

These test scripts isolate individual panels to reproduce and debug Wayland Error 71 issues.

**Error to watch for:**
```
Gdk-Message: Error 71 (Protocol error) dispatching to Wayland display.
```

## Test Scripts

### 1. File Panel Test (`test_file_panel_wayland.py`)

Tests the File Explorer panel in isolation.

**Run:**
```bash
./dev/test_file_panel_wayland.py
```

**What it tests:**
- Initial panel attachment
- Attach/Detach operations
- Float panel operation
- Hide/Show panel operations
- Rapid toggle stress test (10x attach/detach)
- Attach/Hide cycle stress test (20x)

**Expected behavior:**
- No Wayland Error 71 should appear during normal operations
- Panel should remain responsive during stress tests

### 2. Pathway Panel Test (`test_pathway_panel_wayland.py`)

Tests the Pathway Operations panel in isolation (includes SBML import UI).

**Run:**
```bash
./dev/test_pathway_panel_wayland.py
```

**What it tests:**
- Same operations as File panel test
- Includes SBML import panel with embedded widgets
- Tests complex nested UI reparenting

**Expected behavior:**
- No Wayland Error 71 during panel operations
- SBML UI should remain stable during attach/detach

### 3. MasterPalette + File Panel Test (`test_master_palette_file_panel.py`) ⭐ **NEW**

Tests the **interaction** between MasterPalette and File panel (the real use case).

**Run:**
```bash
./dev/test_master_palette_file_panel.py
```

**What it tests:**
- MasterPalette button click handling
- File panel attach/detach via palette buttons
- Paned widget position management
- **REAL file operations** (Open/Save/New buttons work!)
- FileChooser dialog operations
- Rapid toggle via MasterPalette (10x automated test)

**Expected behavior:**
- No Wayland Error 71 when clicking Files button
- Panel attaches/detaches cleanly via palette
- File operations (Open/Save) work without crashes
- FileChooser dialogs open without protocol errors

**Key difference from isolated test:**
- Uses MasterPalette callback mechanism
- Includes paned position management
- Tests the actual integration pattern used in main app

## Usage

### Interactive Testing

1. Run the test script:
   ```bash
   ./dev/test_file_panel_wayland.py
   ```

2. Use the buttons in the UI to test operations:
   - **Detach Panel**: Manually detach panel from container
   - **Float Panel**: Open panel in separate window
   - **Hide Panel**: Remove panel from view
   - **Show Panel**: Make panel visible again
   - **Rapid Toggle**: Automated stress test
   - **Attach/Hide Cycle**: Automated cycle test

3. Watch terminal output for errors

### Automated Testing

Run with timeout and grep for errors:

```bash
# File panel test
timeout 30 ./dev/test_file_panel_wayland.py 2>&1 | grep -E "Error 71|Protocol error"

# Pathway panel test  
timeout 30 ./dev/test_pathway_panel_wayland.py 2>&1 | grep -E "Error 71|Protocol error"
```

### Comparison Testing

Run both tests side-by-side to compare behavior:

```bash
# Terminal 1
./dev/test_file_panel_wayland.py 2>&1 | tee /tmp/file_panel_test.log

# Terminal 2
./dev/test_pathway_panel_wayland.py 2>&1 | tee /tmp/pathway_panel_test.log

# Compare logs
diff /tmp/file_panel_test.log /tmp/pathway_panel_test.log
```

## Debugging Tips

### Monitor Wayland Messages

```bash
# Run with detailed GTK debugging
GTK_DEBUG=interactive ./dev/test_file_panel_wayland.py 2>&1 | tee test.log

# Filter for specific messages
./dev/test_file_panel_wayland.py 2>&1 | grep -E "ATTACH|HIDE|FLOAT|Error"
```

### Check Panel State

Look for these debug messages in output:
- `[ATTACH] *Panel attach_to() called` - Entry to attach
- `[ATTACH] *Panel already attached, ensuring visibility` - Fast path
- `[ATTACH] *Panel scheduling deferred attach` - Slow path (idle callback)
- `[ATTACH] *Panel _do_attach() executing` - Actual attach operation
- `[HIDE] *Panel hide() called` - Entry to hide
- `[HIDE] *Panel _do_hide() executing` - Actual hide operation

### Identify Problem Operations

If Error 71 appears:
1. Note which button was clicked
2. Check which debug messages precede the error
3. Verify if error occurs on first operation or repeated operations
4. Test with rapid toggle to see if timing-related

## Known Issues

### Root Cause: MasterPalette Interaction

**Discovery:** Isolated panel tests work perfectly, but errors occur when panels are controlled via MasterPalette in the full application.

**Problem Sequence:**
1. MasterPalette button callback calls `panel.attach_to()`
2. `attach_to()` schedules idle callback and sets `is_attached=True`
3. MasterPalette callback completes
4. **Something triggers a second `attach_to()` call before idle callback executes**
5. Second call sees `is_attached=False` (timing issue)
6. Second idle callback scheduled
7. Both idle callbacks execute → double-attach → Error 71

**Evidence from logs:**
```
[MP] files calling callback(True)
[ATTACH] LeftPanel attach_to() called, is_attached=False
[ATTACH] LeftPanel scheduling deferred attach
[HANDLER] Set paned position to 250
[MP] files callback returned
[ATTACH] LeftPanel _do_attach() executing  <-- First idle
[ATTACH] LeftPanel attached successfully
[ATTACH] LeftPanel attach_to() called, is_attached=False  <-- Second call!
[ATTACH] LeftPanel _do_attach() executing  <-- Second idle
Gdk-Message: Error 71 (Protocol error)
```

**Theories:**
1. **Paned position change** triggers resize/allocation that somehow calls attach
2. **on_attach_callback** might indirectly trigger another attach
3. **GTK event processing** during idle callback causes re-entrance
4. **Button state updates** in panel trigger signal that calls attach

### File Panel

- **Issue**: Contains ProjectDialogManager with embedded GtkFileChooserButton widgets
- **Trigger**: FileChooserButton widgets may cause issues during reparenting
- **Workaround**: Lazy-load dialogs only when needed
- **Status**: ✅ FileChooser dialogs now use async pattern (no Error 71 from dialogs)

### Pathway Panel

- **Issue**: Contains SBML Import Panel with complex nested UI
- **Trigger**: SBML panel UI loaded eagerly, widgets reparented during attach/detach
- **Workaround**: Avoid calling `set_visible(False)` on content during hide()

## Fixes Applied

### 1. Avoid `set_visible(False)` in hide()

**Problem**: Calling `set_visible(False)` on panel content causes widgets to unrealize, which triggers Wayland surface destruction/recreation.

**Solution**: Just remove content from container without hiding:

```python
# BAD - causes unrealize
self.content.set_visible(False)

# GOOD - keeps widgets realized
self.parent_container.remove(self.content)
# Don't call set_visible - content stays ready
```

### 2. Prevent Duplicate Attach Operations

**Problem**: Fast path in `attach_to()` was calling `set_visible(True)` repeatedly, causing Wayland protocol errors.

**Solution**: Only set visibility if container is not visible:

```python
# Check before setting
if not container.get_visible():
    container.set_visible(True)
```

### 3. Guard Against Concurrent Operations

**Problem**: Multiple attach calls could occur before idle callback completes.

**Solution**: Add `_attach_in_progress` flag:

```python
if self._attach_in_progress:
    return
self._attach_in_progress = True
# ... schedule idle ...
# Clear flag in _do_attach()
self._attach_in_progress = False
```

## Success Criteria

Tests pass if:
1. ✅ No Wayland Error 71 during normal operations
2. ✅ Panel attaches/detaches cleanly
3. ✅ Float operation works without errors
4. ✅ Hide/show cycles work smoothly
5. ✅ Stress tests complete without crashes
6. ✅ Debug output shows single attach operation per call

## Future Improvements

- [ ] Add automated test runner script
- [ ] Create comparison test for Topology/Analyses panels (working)
- [ ] Add memory usage monitoring during stress tests
- [ ] Test with different GTK/Wayland versions
- [ ] Add test for FileChooser dialog operations within panels
