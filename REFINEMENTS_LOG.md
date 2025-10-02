# Refinements Log - October 1, 2025

## Issue 1: Empty Right Panel Visible on Startup

### Problem
On application startup, an empty right panel (thin vertical area) was visible on the right side of the window, even though the toggle button was inactive.

### Root Cause
In `ui/main/main_window.ui`, the `right_paned` widget had:
```xml
<property name="position">800</property>
```

The window's default width is 800px. Setting the paned position to exactly 800 meant the divider was at the right edge, but because the `right_dock_area` has `width-request="0"` and the paned is trying to honor both sides, a thin sliver was visible.

### Solution
Changed the `right_paned` position to a large value (10000) to ensure it's always collapsed on startup:
```xml
<property name="position">10000</property>
```

When the right panel is activated via the toggle button, the code dynamically calculates the correct position:
```python
paned_width = right_paned.get_width()
if paned_width > 280:
    right_paned.set_position(paned_width - 280)
```

### Files Modified
- `/home/simao/projetos/shypn/ui/main/main_window.ui`

---

## Issue 2: Grid Cells Too Large on Startup (~30mm instead of ~5mm)

### Problem
At 100% zoom (zoom=1.0), grid cells appeared to be approximately 30mm wide instead of the expected 5mm (~20 pixels at 96 DPI).

### Root Cause
The `get_grid_spacing()` method in `ModelCanvasManager` was iterating through subdivision levels in **reverse order**:

```python
for level in reversed(self.GRID_SUBDIVISION_LEVELS):  # [10, 5, 2, 1]
    spacing = base_spacing * level
    screen_spacing = spacing * self.zoom
    if screen_spacing >= 10:
        return spacing  # Would return 200 at zoom=1.0!
```

With `GRID_SUBDIVISION_LEVELS = [1, 2, 5, 10]` and `BASE_GRID_SPACING = 20`:
- At zoom=1.0, the reversed iteration checked level=10 first
- spacing = 20 × 10 = 200
- screen_spacing = 200 × 1.0 = 200 pixels ✓ (>= 10)
- **Returned 200**, which is 10× too large!

The algorithm was selecting the **largest** spacing that met the threshold instead of the **smallest**.

### Solution
Removed the `reversed()` call to iterate in ascending order:

```python
for level in self.GRID_SUBDIVISION_LEVELS:  # [1, 2, 5, 10]
    spacing = base_spacing * level
    screen_spacing = spacing * self.zoom
    if screen_spacing >= 10:
        return spacing  # Now returns 20 at zoom=1.0 ✓
```

Now at zoom=1.0:
- level=1: spacing=20, screen_spacing=20 ✓ (>= 10)
- **Returns 20** immediately ✓

### Behavior at Different Zoom Levels
With the corrected algorithm:

| Zoom | Level Selected | World Spacing | Screen Spacing | Approx. Size |
|------|---------------|---------------|----------------|--------------|
| 0.3  | 2             | 40            | 12 px          | ~10mm        |
| 0.5  | 1             | 20            | 10 px          | ~5mm         |
| 1.0  | 1             | 20            | 20 px          | ~5mm         |
| 2.0  | 1             | 20            | 40 px          | ~10mm        |
| 5.0  | 1             | 20            | 100 px         | ~26mm        |

The grid adapts by selecting progressively larger spacing as you zoom out, preventing cluttered overlapping lines while maintaining at least 10 pixels between lines on screen.

### Files Modified
- `/home/simao/projetos/shypn/src/data/model_canvas_manager.py`

---

## Testing

Both issues have been fixed and tested. The application now:
1. ✅ Starts with no empty panels visible (both left and right panels hidden)
2. ✅ Displays grid at correct 100% zoom with ~5mm cells (20px at 96 DPI)
3. ✅ Pan behavior remains smooth and relative
4. ✅ Three grid styles available (line, dot, cross)

## Related Changes from Previous Session

These refinements build on the previous session where we implemented:
- Viewport centering on startup
- Incremental delta tracking for smooth pan
- Alternative grid patterns (line/dot/cross)
- Grid style API methods (`set_grid_style`, `cycle_grid_style`)
