# Wayland Error 71 Investigation

**Date**: 2025-10-21  
**Status**: 🔍 INVESTIGATING  
**Error**: `Gdk-Message: Error 71 (Protocol error) dispatching to Wayland display`

## Error Context

The error appears in the console output:
```
[ATTACH] LeftPanel _do_attach() executing
[ATTACH] LeftPanel attached successfully, content visible
Gdk-Message: 10:33:12.357: Error 71 (Protocol error) dispatching to Wayland display.
```

## Timing Analysis

The error occurs:
- ✅ After successful panel attachment
- ✅ After all widgets are visible
- ❌ Not during dialog creation (dialogs not yet opened)
- ❌ Not during panel loading

## What We've Fixed

### 1. FileExplorerPanel Dialog Parent Windows ✅
- **Fixed**: All 4 dialog types now use `self.parent_window`
  - New Folder dialog
  - Rename dialog
  - Delete confirmation
  - Properties dialog
- **Method**: Added `set_parent_window()` and updated all dialog methods
- **Commit**: bae4d81

### 2. Early Parent Window Initialization ✅
- **Fixed**: Set `parent_window` immediately at startup
- **Before**: Only set during `attach_to()`
- **After**: Set right after `create_left_panel()`
- **Benefit**: Prevents crashes if buttons clicked before panel attached
- **Commit**: d6ced05

### 3. NetObjPersistency Parent Windows ✅
- **Status**: Already working (parent_window set at creation)
- **Dialogs**: Open, Save, Save As
- **No changes needed**

## Current Status

### What Works ✅
- Application starts successfully
- Panel attaches without crashing
- All widgets visible and functional
- Parent windows properly set for all dialogs

### What Remains ❓
- Wayland Error 71 still appears in console
- **Question**: Does it actually crash the app?
- **Question**: Or is it just a warning that can be ignored?
- **Question**: Which specific actions trigger crashes?

## Wayland Error 71 Meaning

**Error 71 = EPROTO (Protocol error)**

Common causes on Wayland:
1. **Invalid surface state** - surface destroyed while compositor still references it
2. **Double-free** - surface freed twice
3. **Reparenting issues** - widget moved between containers incorrectly
4. **Dialog parent mismatch** - dialog parent changes during realization
5. **Event delivery failure** - event sent to destroyed window

## Hypothesis

The error might be related to the **panel reparenting operation** itself, not the dialogs:

```python
# In LeftPanelLoader.attach_to()
def _do_attach():
    # Remove from old parent (window)
    self.window.remove(self.content)  # ← Potential issue?
    
    # Hide window before reparenting (WAYLAND FIX)
    self.window.hide()  # ← Another potential issue?
    
    # Add to new parent (container)
    container.add(self.content)  # ← Or here?
```

### Possible Issues:
1. **Window hide timing**: Hiding window after removing content might leave surface in invalid state
2. **Content reparenting**: Moving content between window and container might cause protocol error
3. **Event queue**: Events pending for old parent arrive after reparenting

## Next Steps

### 1. Verify Actual Impact
- [ ] Does app actually crash or just show error?
- [ ] Can user continue working after error?
- [ ] Do File Explorer buttons work correctly?
- [ ] Do dialogs open without issues?

### 2. If It's Just a Warning (Non-Fatal)
- Document as known cosmetic issue
- Focus on ensuring functionality works
- Consider suppressing or filtering the message

### 3. If It Causes Crashes
Need to investigate:
- [ ] Test each File Explorer button individually
- [ ] Add more detailed logging around reparenting
- [ ] Try alternative reparenting strategies
- [ ] Consider using `GLib.idle_add()` with different timing

## Testing Protocol

### Test Each Button:
1. **New Folder** button
   - Click → Dialog opens?
   - Enter name → Folder created?
   - Any crash?

2. **Open** button
   - Click → File chooser opens?
   - Select file → File loads?
   - Any crash?

3. **Save** button
   - Modify document → Click Save
   - Dialog opens (if needed)?
   - File saves?
   - Any crash?

4. **Save As** button
   - Click → File chooser opens?
   - Choose location → File saved?
   - Any crash?

5. **Context Menu** operations
   - Right-click file → Menu shows?
   - Rename → Dialog opens?
   - Delete → Confirmation opens?
   - Properties → Dialog opens?
   - Any crash?

## Alternative Approaches (If Crashes Continue)

### Option A: Different Reparenting Strategy
```python
# Instead of remove + add, try:
# 1. Create content in container directly
# 2. Never reparent between window and container
# 3. Show/hide containers instead
```

### Option B: Delay Reparenting
```python
# Use multiple idle callbacks to spread operations:
GLib.idle_add(lambda: self.window.remove(self.content))
GLib.idle_add(lambda: self.window.hide(), priority=GLib.PRIORITY_LOW)
GLib.idle_add(lambda: container.add(self.content), priority=GLib.PRIORITY_LOW)
```

### Option C: Avoid Reparenting Entirely
```python
# Keep two copies of content:
# - One for window (floating mode)
# - One for container (attached mode)
# Switch visibility instead of reparenting
```

## Related Files

- `src/shypn/helpers/left_panel_loader.py` - Panel lifecycle management
- `src/shypn/helpers/file_explorer_panel.py` - File Explorer dialogs
- `src/shypn/file/netobj_persistency.py` - File operations (Open/Save)

## User Feedback Needed

Please provide:
1. **Does the application crash?** Or just show the error?
2. **Which button causes crash?** New Folder? Open? Save? Other?
3. **When does crash occur?** Immediately? After clicking? After dialog?
4. **Can you continue working?** Or is app unusable?

## Summary

We've successfully fixed:
- ✅ All FileExplorerPanel dialog parent windows
- ✅ Early parent_window initialization
- ✅ NetObjPersistency already working

Remaining:
- ❓ Wayland Error 71 during panel attach
- ❓ Impact unclear (crash vs warning)
- ❓ Need user feedback on specific failing operations

