# Fix: Empty Resizable Panel on Startup

## Problem Description
After previous refactoring, an empty resizable panel was appearing on startup. This was a leftover widget showing a visible paned separator even though no panel content was attached.

## Root Cause
The issue was in `/home/simao/projetos/shypn/ui/main/main_window.ui`:

1. **Dock areas were always visible**: Both `left_dock_area` and `right_dock_area` had no `visible` property set, defaulting to `visible="true"`.

2. **GtkPaned always shows separators**: Even when a child has `width-request="0"` and the paned position is set to collapse it, GTK4's GtkPaned widget shows a thin separator/handle for resizing. When the dock area container is visible but empty, this creates a visible empty panel with a resize handle.

3. **No visibility management**: The panel loaders were not managing container visibility - they would attach content but leave empty containers visible.

## Solution

### 1. Hide Dock Areas by Default in UI
Modified `ui/main/main_window.ui` to set both dock areas initially invisible:

```xml
<!-- Left dock area -->
<object class="GtkBox" id="left_dock_area">
  <property name="orientation">vertical</property>
  <property name="spacing">0</property>
  <property name="width-request">0</property>
  <property name="visible">false</property>  <!-- Added -->
  <!-- Panel content will be attached here dynamically -->
</object>

<!-- Right dock area -->
<object class="GtkBox" id="right_dock_area">
  <property name="orientation">vertical</property>
  <property name="spacing">0</property>
  <property name="width-request">0</property>
  <property name="visible">false</property>  <!-- Added -->
  <!-- Panel content will be attached here dynamically -->
</object>
```

### 2. Show Container When Panel Attaches
Modified both `left_panel_loader.py` and `right_panel_loader.py` in the `attach_to()` method:

```python
# Only append if not already in container
if self.content.get_parent() != container:
    container.append(self.content)

# Make container visible when panel is attached
container.set_visible(True)  # Added

# Make sure content is visible
self.content.set_visible(True)
```

### 3. Hide Container When Panel Hides
Modified both loaders' `hide()` method:

```python
def hide(self):
    """Hide panel (works for both attached and detached states)."""
    if self.is_attached:
        # When attached, hide both content and container
        self.content.set_visible(False)
        if self.parent_container:
            self.parent_container.set_visible(False)  # Added
    elif self.window:
        self.window.set_visible(False)
    print("✓ [Panel]: hidden")
```

## Files Modified

1. `/home/simao/projetos/shypn/ui/main/main_window.ui`
   - Added `<property name="visible">false</property>` to `left_dock_area`
   - Added `<property name="visible">false</property>` to `right_dock_area`

2. `/home/simao/projetos/shypn/src/shypn/left_panel_loader.py`
   - `attach_to()`: Added `container.set_visible(True)` after appending content
   - `hide()`: Added `self.parent_container.set_visible(False)` when hiding attached panel

3. `/home/simao/projetos/shypn/src/shypn/right_panel_loader.py`
   - `attach_to()`: Added `container.set_visible(True)` after appending content
   - `hide()`: Added `self.parent_container.set_visible(False)` when hiding attached panel

## Behavior

### Before Fix
- Application startup showed empty resizable panel on left or right side
- GtkPaned separator was visible even with no content
- User could drag the empty separator, creating confusion

### After Fix
- Application startup shows clean workspace with no empty panels
- Dock areas are completely hidden (invisible) until panel is activated
- When panel toggle button is pressed:
  - Container becomes visible
  - Content is attached
  - Paned position is adjusted
- When panel toggle is released:
  - Content is hidden
  - Container is hidden
  - Paned position collapses
- No leftover widgets or visible separators

## Testing
✅ Application starts with clean workspace, no empty panels
✅ Left panel toggle shows/hides panel correctly with container visibility
✅ Right panel toggle shows/hides panel correctly with container visibility
✅ Floating/docking behavior preserved
✅ Grid and zoom working correctly at 100% startup

## Technical Notes

**Why not just use `shrink-*-child="true"`?**

Setting `shrink-start-child="true"` or `shrink-end-child="true"` on GtkPaned allows the child to shrink below its minimum size, but:
1. It doesn't make the paned separator invisible
2. It doesn't hide the container widget itself
3. The separator handle remains interactive and visible

**Why set visibility on both content and container?**

- **Content visibility**: Controls whether the panel content itself is shown
- **Container visibility**: Controls whether the dock area (including any borders, spacing, or paned effects) is rendered at all

Setting both ensures the entire panel system is truly hidden, not just the content inside it.

## Related Issues
This fix completes the work from previous refinement sessions:
- Session 1: Fixed right paned position to hide empty panel
- Session 2: Fixed grid spacing algorithm  
- Session 3 (this): Fixed leftover visible dock area containers
