# Panel Dock/Undock Fix Documentation

## Issue Description
When using the float button inside the right panel to dock/undock, an empty container was being left visible in the main window, and the header toggle button was not synchronized with the panel's state.

## Root Causes Identified

### 1. Container Visibility Not Managed
When the panel floated (detached), the container in the main window that previously held the panel content was not being hidden, leaving an empty visible box.

### 2. Toggle Button Synchronization Missing
The float button inside the panel and the toggle button in the main window header were not synchronized:
- Clicking the float button inside the panel didn't update the header toggle
- This caused confusion about the actual state of the panel

### 3. GTK3 Widget Visibility
Using `window.present()` instead of `window.show_all()` didn't properly show all child widgets when floating.

## Solutions Implemented

### Fix 1: Hide Container When Floating

**File: `src/shypn/helpers/right_panel_loader.py`**
**File: `src/shypn/helpers/left_panel_loader.py`**

Modified the `float()` method to hide the container after unattaching:

```python
def float(self, parent_window=None):
    # ... existing code ...
    
    # If currently attached, unattach first (moves content back to window)
    if self.is_attached:
        self.unattach()
        # Hide the container after unattaching
        if self.parent_container:
            self.parent_container.set_visible(False)
    
    # ... rest of method ...
```

This ensures that when the panel floats, the empty container in the main window is hidden.

### Fix 2: Show Container When Attaching

**Already implemented in `attach_to()` method:**

```python
def attach_to(self, container, parent_window=None):
    # ... existing code ...
    
    # Make container visible when panel is attached
    container.set_visible(True)
    
    # Make sure content is visible
    self.content.set_visible(True)
    self.content.show_all()  # Ensure all child widgets are visible
    
    # ... rest of method ...
```

### Fix 3: Bidirectional Toggle Synchronization

**File: `src/shypn.py`**

Restructured the initialization order:
1. Get toggle buttons first
2. Define toggle handlers
3. Define float/attach callbacks that reference the handlers
4. Connect the handlers

Added synchronization in callbacks:

```python
def on_right_float():
    """Collapse right paned when panel floats."""
    # ... paned management ...
    
    # Sync header toggle button to off when panel floats
    if right_toggle and right_toggle.get_active():
        right_toggle.handler_block_by_func(on_right_toggle)
        right_toggle.set_active(False)
        right_toggle.handler_unblock_by_func(on_right_toggle)

def on_right_attach():
    """Expand right paned when panel attaches."""
    # ... paned management ...
    
    # Sync header toggle button to on when panel attaches
    if right_toggle and not right_toggle.get_active():
        right_toggle.handler_block_by_func(on_right_toggle)
        right_toggle.set_active(True)
        right_toggle.handler_unblock_by_func(on_right_toggle)
```

The `handler_block_by_func()` and `handler_unblock_by_func()` prevent recursive toggle events.

### Fix 4: Use show_all() Instead of present()

**Files: `src/shypn/helpers/right_panel_loader.py`, `left_panel_loader.py`**

Changed from:
```python
self.window.present()
```

To:
```python
self.window.show_all()
```

This ensures all child widgets (search entries, buttons, labels, canvas containers) are visible when the panel floats.

## Behavior Flow After Fix

### Floating Sequence:
1. User clicks float button inside panel (or toggles header button OFF)
2. `float()` method is called
3. Content is moved from container to window via `unattach()`
4. **Container is hidden** (`container.set_visible(False)`)
5. Float callback runs, collapses paned
6. Float callback synchronizes header toggle to OFF
7. Window is shown with `show_all()`

### Attaching Sequence:
1. User clicks float button again (or toggles header button ON)
2. `attach_to()` method is called
3. Content is moved from window to container
4. Window is hidden
5. **Container is shown** (`container.set_visible(True)`)
6. Content is shown with `show_all()`
7. Attach callback runs, expands paned
8. Attach callback synchronizes header toggle to ON

## Verification

### What to Test:
1. ✅ Click float button inside right panel → panel floats, no empty container left behind
2. ✅ Click float button again → panel docks back, container visible with content
3. ✅ Click header toggle button → same behavior, buttons stay synchronized
4. ✅ All widgets (search, buttons, labels, canvas) visible in both states
5. ✅ No ghost windows or duplicate panels
6. ✅ Paned divider adjusts correctly

### Expected Results:
- **When Docked**: Content visible in container, window hidden, header toggle ON
- **When Floating**: Window visible with all content, container hidden, header toggle OFF
- **Always**: Both buttons (float and header toggle) reflect the same state

## Debug Logging

Enhanced logging tracks:
- Content parent changes
- Container visibility changes
- Window hide/show operations
- Button state synchronization

Example log output:
```
→ Right panel float button toggled: active=True, is_attached=True
  → unattach called
  → Removing content from container
  → Adding content back to window
✓ Right panel: unattached
✓ Right panel: floating
```

## Files Modified

1. `src/shypn/helpers/right_panel_loader.py`
   - Added container hiding in `float()`
   - Enhanced debug logging throughout
   - Changed `present()` to `show_all()`

2. `src/shypn/helpers/left_panel_loader.py`
   - Added container hiding in `float()`
   - Changed to `show_all()` for consistency

3. `src/shypn.py`
   - Restructured initialization order
   - Added bidirectional toggle synchronization
   - Moved toggle definitions before callbacks

## Notes

- The `handler_block_by_func()` / `handler_unblock_by_func()` pattern is crucial to prevent infinite recursion when programmatically toggling buttons
- Container visibility management is separate from content visibility - both must be managed
- GTK3 requires explicit `show_all()` calls to ensure child widgets are visible
- The paned warnings about `get_width()` are separate issues and don't affect panel functionality
