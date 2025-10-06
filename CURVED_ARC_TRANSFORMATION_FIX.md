# CurvedArc Transformation Fix - Dragging and Ghost Line

## Issue

When double-clicking `CurvedArc` instances and attempting to drag the transformation handle:
1. **Handle did not drag the curve** - The curve remained in its original position
2. **Ghost straight line appeared** - A straight line was drawn from source to target during editing, even though the arc was rendered as curved

## Root Causes

### 1. ArcTransformHandler Only Supported `is_curved` Flag System

`ArcTransformHandler` was designed for the **new curve system** using:
- `arc.is_curved` boolean flag
- `arc.control_offset_x` and `arc.control_offset_y` manual offsets

However, `CurvedArc` is a **separate legacy class** that:
- Automatically calculates control points (20% of line length)
- Does NOT have `is_curved`, `control_offset_x`, or `control_offset_y` properties
- Uses `_calculate_curve_control_point()` method for rendering

**Result**: When dragging a CurvedArc handle, the handler tried to set properties that don't exist, so nothing happened.

### 2. ObjectEditingTransforms Drew Ghost Straight Lines

In `object_editing_transforms.py`, the selection and edit mode rendering only checked `obj.is_curved` flag:
- `CurvedArc` instances don't have `is_curved` property
- System defaulted to drawing straight line from source to target
- This straight line appeared as a "ghost" during editing

## Solution

### 1. Added Manual Control Point Override to CurvedArc

**File**: `src/shypn/netobjs/curved_arc.py`

Added support for `manual_control_point` property:
- When `manual_control_point` is set, use it directly (override automatic calculation)
- When `manual_control_point` is `None`, use automatic calculation (default behavior)

```python
# In render() method:
if hasattr(self, 'manual_control_point') and self.manual_control_point is not None:
    # Use manual control point directly
    control_point = self.manual_control_point
else:
    # Check for parallel arcs and calculate offset for control point
    # ... automatic calculation ...
    control_point = self._calculate_curve_control_point(offset=offset_distance)
```

### 2. Updated ArcTransformHandler to Support Both Systems

**File**: `src/shypn/edit/transformation/arc_transform_handler.py`

Added logic to detect and handle `CurvedArc` instances separately:

**In `start_transform()`**:
```python
from shypn.netobjs.curved_arc import CurvedArc

# Check if this is a CurvedArc (legacy class) or Arc with is_curved flag
self.is_curved_arc_class = isinstance(obj, CurvedArc)

if self.is_curved_arc_class:
    # CurvedArc: add manual override properties if not present
    if not hasattr(obj, 'manual_control_point'):
        obj.manual_control_point = None  # None = use automatic calculation
    
    # Store original state
    self.original_geometry = {
        'type': 'curved_arc',
        'manual_control_point': obj.manual_control_point,
    }
else:
    # Arc with is_curved flag (original behavior)
    # ...
```

**In `update_transform()`**:
```python
if self.is_curved_arc_class:
    # CurvedArc: set manual control point
    arc.manual_control_point = (current_x, current_y)
else:
    # Arc with is_curved: make sure it's curved and update offsets
    # ... original behavior ...
```

**In `end_transform()` and `cancel_transform()`**:
- Handle CurvedArc state restoration separately
- For CurvedArc, only dragging is allowed (no toggle straight/curved)

### 3. Fixed Ghost Line Rendering

**File**: `src/shypn/edit/object_editing_transforms.py`

Updated both selection and edit mode rendering to detect `CurvedArc`:

```python
from shypn.netobjs.curved_arc import CurvedArc

# Check if this is a curved arc
is_curved = isinstance(obj, CurvedArc) or getattr(obj, 'is_curved', False)

if is_curved:
    # Get control point
    if isinstance(obj, CurvedArc):
        # CurvedArc: check for manual control point first
        if hasattr(obj, 'manual_control_point') and obj.manual_control_point is not None:
            control_x, control_y = obj.manual_control_point
        else:
            # Use automatic calculation
            control_point = obj._calculate_curve_control_point()
            if control_point:
                control_x, control_y = control_point
            else:
                control_x, control_y = mid_x, mid_y
    else:
        # Arc with is_curved flag: use control offsets
        control_x = mid_x + getattr(obj, 'control_offset_x', 0.0)
        control_y = mid_y + getattr(obj, 'control_offset_y', 0.0)
    
    # Draw curved selection/outline
    cr.move_to(src_x, src_y)
    cr.curve_to(control_x, control_y, control_x, control_y, tgt_x, tgt_y)
else:
    # Draw straight selection/outline
    # ...
```

This ensures:
1. **Selection highlight** follows the curve (no ghost straight line)
2. **Edit mode dashed outline** follows the curve
3. Both automatic and manual control points are respected

## Test Results

All tests in `test_curved_arc_dragging.py` pass:

```
✓ CurvedArc can store manual control point!
✓ CurvedArc transformation handler works correctly!
✓ Manual control point differs from automatic!
✓ Cancel transformation works correctly!
```

## Affected Arc Types

✅ **CurvedArc** - Now fully supports dragging transformation

✅ **CurvedInhibitorArc** - Inherits fix from CurvedArc

✅ **Arc** with `is_curved=True` - Still works (original system)

✅ **InhibitorArc** with `is_curved=True` - Still works

## Behavior

### CurvedArc Transformation

1. **Double-click** CurvedArc → Handle appears at automatic control point
2. **Drag handle** → Sets `manual_control_point` to dragged position
3. **Release** → Curve updates to new control point
4. **ESC** → Cancels, restores to automatic calculation (manual_control_point = None)

### Visual Feedback

- **Before**: Ghost straight line + curve rendered
- **After**: Only curve rendered (selection, edit outline, and arc itself)

### Toggle Behavior

- **Arc with is_curved**: Click handle → toggles straight/curved
- **CurvedArc**: Click handle → no toggle (dragging only)
  - Rationale: CurvedArc is a specific class for curves; to make it straight, user should delete and create a regular Arc

## Integration

The fix is **backward compatible**:
- Existing CurvedArc instances work without changes
- `manual_control_point` defaults to `None` (automatic calculation)
- Only set when user drags the handle
- Both curve systems coexist harmoniously

## Files Modified

1. **src/shypn/netobjs/curved_arc.py**
   - Added manual control point override in `render()` method

2. **src/shypn/edit/transformation/arc_transform_handler.py**
   - Added CurvedArc detection and handling
   - Updated `start_transform()`, `update_transform()`, `end_transform()`, `cancel_transform()`

3. **src/shypn/edit/object_editing_transforms.py**
   - Fixed `_render_object_selection()` to follow curve path
   - Fixed `_render_edit_mode_visual()` to follow curve path
   - Both methods now detect `CurvedArc` and use appropriate control points

## Summary

✅ **Fixed**: CurvedArc handles now respond to dragging

✅ **Fixed**: Ghost straight line eliminated during editing

✅ **Tested**: All transformation scenarios verified

✅ **Backward Compatible**: Existing code and arcs unaffected

✅ **Two Systems Supported**: Both `is_curved` flag and `CurvedArc` class work correctly
