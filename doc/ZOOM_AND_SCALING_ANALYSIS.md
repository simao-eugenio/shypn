# Zoom and Object Scaling Analysis

## Overview

This document analyzes the legacy ShyPN zoom and object scaling implementation to port it to the current codebase.

**Date**: October 3, 2025  
**Legacy Code**: `legacy/shypnpy/interface/interactions.py`, `coords.py`, `validate_ui.py`, `color_utils.py`  
**Current Code**: `src/shypn/data/model_canvas_manager.py`, `src/shypn/helpers/model_canvas_loader.py`, `src/shypn/api/*.py`

---

## Legacy Zoom Implementation

### 1. Zoom State Variables

The legacy code uses three key state variables:

```python
app.zoom_scale = 1.0      # Zoom factor (0.05 to 20.0, default 1.0 = 100%)
app._pan_x = 0.0          # Pan offset X in world coordinates
app._pan_y = 0.0          # Pan offset Y in world coordinates
```

**Zoom Range**: 5% (0.05) to 2000% (20.0)  
**Default**: 100% (1.0)

### 2. Coordinate Transformation

#### Device-to-Logical (Screen→World)

From `legacy/shypnpy/interface/coords.py`:

```python
def device_to_logical(app, px: float, py: float) -> Tuple[float,float]:
    scale = getattr(app, 'zoom_scale', 1.0) or 1.0
    pan_x = getattr(app, '_pan_x', 0.0)
    pan_y = getattr(app, '_pan_y', 0.0)
    return (px / scale - pan_x, py / scale - pan_y)
```

**Formula**: `logical = screen / zoom - pan`

#### Logical-to-Device (World→Screen)

```python
def logical_to_device(app, lx: float, ly: float) -> Tuple[float,float]:
    scale = getattr(app, 'zoom_scale', 1.0) or 1.0
    pan_x = getattr(app, '_pan_x', 0.0)
    pan_y = getattr(app, '_pan_y', 0.0)
    return ((lx + pan_x) * scale, (ly + pan_y) * scale)
```

**Formula**: `screen = (world + pan) * zoom`

### 3. Pointer-Centered Zoom

From `legacy/shypnpy/interface/interactions.py` (lines 98-119):

```python
def _apply_zoom_factor(factor: float, center_px: float, center_py: float, widget=None):
    """Apply zoom factor while keeping logical coordinate under pointer fixed."""
    old = getattr(app,'zoom_scale',1.0) or 1.0
    new_scale = max(0.05, min(20.0, old * factor))
    
    if abs(new_scale - old) < 1e-9:
        return  # No change
    
    pan_x = getattr(app,'_pan_x',0.0)
    pan_y = getattr(app,'_pan_y',0.0)
    
    # Preserve logical coordinate under pointer: L = px/old - pan
    Lx = center_px / old - pan_x
    Ly = center_py / old - pan_y
    
    # Recalculate pan to keep L fixed at the same screen position
    pan_x = center_px / new_scale - Lx
    pan_y = center_py / new_scale - Ly
    
    setattr(app,'zoom_scale', new_scale)
    setattr(app,'_pan_x', pan_x)
    setattr(app,'_pan_y', pan_y)
    
    if hasattr(app,'set_status'):
        app.set_status(f"Zoom {int(new_scale*100)}%")
    
    widget.queue_draw()
```

**Key Insight**: The zoom operation keeps the logical coordinate under the mouse pointer fixed in screen space, creating a "zoom to cursor" effect.

### 4. Mouse Wheel Zoom

From `legacy/shypnpy/interface/interactions.py` (lines 438-457):

```python
def _on_scroll(widget, event):
    """Handle scroll events for zoom."""
    direction = getattr(event,'direction',None)
    factor = None
    
    # Smooth scrolling (trackpad) uses delta_y sign
    if direction == Gdk.ScrollDirection.SMOOTH:
        dy = getattr(event,'delta_y',0.0)
        if abs(dy) < 1e-6:
            return False
        factor = (1/1.1) if dy > 0 else 1.1
    else:
        # Discrete scroll wheel
        if direction in (Gdk.ScrollDirection.UP, Gdk.ScrollDirection.LEFT):
            factor = 1.1      # Zoom in 10%
        elif direction in (Gdk.ScrollDirection.DOWN, Gdk.ScrollDirection.RIGHT):
            factor = 1/1.1    # Zoom out 10%
    
    if factor is None:
        return False
    
    _apply_zoom_factor(factor, event.x, event.y, widget)
    return True
```

**Zoom Factor**:
- Scroll up/trackpad up: 1.1 (zoom in 10%)
- Scroll down/trackpad down: 1/1.1 ≈ 0.909 (zoom out 10%)

### 5. Zoom Buttons

From `legacy/shypnpy/interface/interactions.py` (lines 121-136):

```python
def _wire_zoom(btn_id, factor):
    """Connect zoom button to zoom operation."""
    b = getattr(app,'bobj',lambda n: None)(btn_id)
    if b is None:
        return
    
    def _clicked(_w):
        da_local = getattr(app,'bobj',lambda n: None)('drawing_area')
        if da_local is not None:
            # Zoom centered at viewport center
            cx = da_local.get_allocated_width()/2.0
            cy = da_local.get_allocated_height()/2.0
            _apply_zoom_factor(factor, cx, cy, da_local)
    
    b.connect('clicked', _clicked)

_wire_zoom('zoom_btn_in', 1.1)      # Zoom in button
_wire_zoom('zoom_btn_out', 1/1.1)   # Zoom out button
```

**Difference from Mouse Wheel**: Buttons zoom to viewport center, not cursor position.

---

## Object Scaling with Zoom

### 1. Cairo Transform Approach

From `legacy/shypnpy/interface/validate_ui.py` (lines 5933-5934):

```python
# Apply pan and zoom transformation to Cairo context
cr.save()
cr.translate(self._pan_x * scale, self._pan_y * scale)
cr.scale(scale, scale)

# Draw objects in world coordinates (they get transformed automatically)
self._draw_objects(cr, scale)

cr.restore()
```

**Key Insight**: The legacy code applies `cr.scale(scale, scale)` to the Cairo context, which automatically scales all subsequent drawing operations. This means:
- Object positions scale automatically
- Object sizes (radius, width, height) scale automatically
- **Line widths must be adjusted** to maintain visual consistency

### 2. Line Width Compensation

From `legacy/shypnpy/interface/color_utils.py`:

#### Places (line 55)
```python
def draw_place(cr, place, scale=1.0):
    # ...
    cr.set_line_width(3.0 / max(scale, 1e-6))  # Compensate for zoom
    cr.arc(place.x, place.y, radius, 0, 6.28318)
    cr.stroke()
```

#### Arcs (line 96)
```python
def draw_arc(cr, arc, model, scale=1.0):
    # ...
    cr.set_line_width(2.0 / max(scale, 1e-6))  # Compensate for zoom
    cr.move_to(src.x, src.y)
    cr.line_to(tgt.x, tgt.y)
    cr.stroke()
```

**Line Width Formula**: `visual_width = desired_width / zoom_scale`

This ensures that:
- At zoom 100% (1.0): Line width = 3.0px
- At zoom 200% (2.0): Line width = 1.5px (appears as 3.0px after scaling)
- At zoom 50% (0.5): Line width = 6.0px (appears as 3.0px after scaling)

**Result**: Lines maintain constant pixel width regardless of zoom level.

### 3. What Scales and What Doesn't

#### Objects that Scale with Zoom:
- ✅ **Place positions** (x, y coordinates)
- ✅ **Place radius** (circle gets bigger/smaller)
- ✅ **Transition positions** (x, y coordinates)
- ✅ **Transition dimensions** (width, height scale)
- ✅ **Arc endpoints** (follow connected objects)
- ✅ **Token positions** (inside places)
- ✅ **Text positions** (labels, weights)

#### Objects that DON'T Scale (maintain pixel size):
- ❌ **Border line widths** (3.0px always)
- ❌ **Arc line widths** (2.0px always)
- ❌ **Selection highlight widths** (3.0px always)
- ❌ **Arc preview line width** (2.0px always)
- ❌ **Arrowhead sizes** (11px length, 6px width always)
- ⚠️ **Text font sizes** (usually constant, but can scale)

---

## Current Code Analysis

### 1. Existing Zoom Infrastructure

From `src/shypn/data/model_canvas_manager.py` (lines 46-72):

```python
class ModelCanvasManager:
    def __init__(self, model):
        self.model = model
        
        # Zoom level (1.0 = 100%, range typically 0.1 to 10.0)
        self.zoom = 1.0
        
        # Pan offset (in world coordinates)
        self.pan_x = 0.0  # Pan offset X (in world coordinates)
        self.pan_y = 0.0  # Pan offset Y (in world coordinates)
        
        # Viewport size (screen coordinates) - updated when widget is allocated
        self.viewport_width = 800
        self.viewport_height = 600
```

**✅ Good News**: The infrastructure already exists! We just need to connect it.

### 2. Coordinate Transformations

From `src/shypn/data/model_canvas_manager.py` (lines 91-113):

```python
def screen_to_world(self, screen_x, screen_y):
    """Convert screen coordinates to world (model) coordinates."""
    world_x = (screen_x / self.zoom) + self.pan_x
    world_y = (screen_y / self.zoom) + self.pan_y
    return world_x, world_y

def world_to_screen(self, world_x, world_y):
    """Convert world (model) coordinates to screen coordinates."""
    screen_x = (world_x - self.pan_x) * self.zoom
    screen_y = (world_y - self.pan_y) * self.zoom
    return screen_x, screen_y
```

**⚠️ Issue**: Current transformation differs from legacy!

#### Current (WRONG for pan):
```
screen = (world - pan) * zoom
world = screen / zoom + pan
```

#### Legacy (CORRECT):
```
screen = (world + pan) * zoom
world = screen / zoom - pan
```

**Explanation**: The current code treats `pan_x`/`pan_y` as offsets to subtract from world coordinates, but the legacy code treats them as offsets to add. This is a semantic difference in how pan is interpreted.

### 3. Existing Zoom Methods

From `src/shypn/data/model_canvas_manager.py` (lines 115-147):

```python
def zoom_at_point(self, factor, screen_x, screen_y):
    """Zoom in/out while keeping the point under cursor fixed.
    
    Args:
        factor: Zoom multiplier (> 1.0 zooms in, < 1.0 zooms out)
        screen_x, screen_y: Screen coordinates of zoom center
    """
    # Get world coordinate under cursor BEFORE zoom
    old_world_x, old_world_y = self.screen_to_world(screen_x, screen_y)
    
    # Apply zoom with limits
    old_zoom = self.zoom
    self.zoom = max(0.1, min(10.0, self.zoom * factor))
    
    # Get world coordinate under cursor AFTER zoom (with old pan)
    new_world_x, new_world_y = self.screen_to_world(screen_x, screen_y)
    
    # Adjust pan to keep world coordinate fixed
    self.pan_x += (new_world_x - old_world_x)
    self.pan_y += (new_world_y - old_world_y)
    
    self._needs_redraw = True
```

**✅ Good News**: Pointer-centered zoom already implemented!

**⚠️ Limitation**: Zoom range is 10% to 1000% (0.1 to 10.0), but legacy supports 5% to 2000% (0.05 to 20.0).

### 4. Scroll Event Handler (Already Exists!)

From `src/shypn/helpers/model_canvas_loader.py` (lines 520-529):

```python
def _on_scroll_event(self, widget, event, manager):
    """Handle scroll events for zoom (GTK3)."""
    if event.direction == Gdk.ScrollDirection.UP:
        manager.zoom_at_point(1.1, event.x, event.y)
        widget.queue_draw()
    elif event.direction == Gdk.ScrollDirection.DOWN:
        manager.zoom_at_point(0.9, event.x, event.y)
        widget.queue_draw()
    return True
```

**✅ Scroll zoom already connected and functional!**

**⚠️ Issues**:
1. Doesn't handle `SMOOTH` scroll (trackpad)
2. Factor is 0.9 instead of 1/1.1 ≈ 0.909 (minor)

### 5. Rendering Without Cairo Transform

From `src/shypn/helpers/model_canvas_loader.py` (lines 565-575):

```python
def _on_draw(self, drawing_area, cr, width, height, manager):
    """Draw callback for the canvas."""
    # Clear background
    cr.set_source_rgb(1.0, 1.0, 1.0)  # White background
    cr.paint()
    
    # Draw grid
    manager.draw_grid(cr)
    
    # Draw Petri Net objects
    for obj in manager.get_all_objects():
        obj.render(cr, manager.world_to_screen)
    # ...
```

**Current Approach**: No `cr.scale()` transformation. Each object's `render()` method receives a `transform` function and must call it explicitly for each coordinate.

**Legacy Approach**: Apply `cr.scale()` once, then draw everything in world coordinates.

### 6. Object Rendering (Line Widths Are Fixed!)

From `src/shypn/api/place.py` (lines 71-75):

```python
def render(self, cr, transform=None):
    # Apply transform if provided
    if transform:
        screen_x, screen_y = transform(self.x, self.y)
        screen_radius = self.radius  # TODO: Scale radius with zoom
    else:
        screen_x, screen_y = self.x, self.y
        screen_radius = self.radius
    
    # Draw hollow circle (legacy style: stroke only, no fill)
    cr.arc(screen_x, screen_y, screen_radius, 0, 2 * math.pi)
    cr.set_source_rgb(*self.border_color)
    cr.set_line_width(self.border_width)  # Always 3.0px - WRONG!
    cr.stroke()
```

**⚠️ Critical Issue**: 
- `screen_radius = self.radius` - radius doesn't scale with zoom!
- `cr.set_line_width(self.border_width)` - line width doesn't compensate for zoom!

**Result**: Objects don't scale properly with zoom.

---

## Implementation Strategy

### Approach 1: Cairo Transform (RECOMMENDED - Legacy-Compatible)

Apply `cr.scale(zoom, zoom)` and `cr.translate()` to the Cairo context, matching legacy behavior exactly.

**Pros**:
- ✅ Matches legacy behavior exactly
- ✅ Simpler object rendering (no per-coordinate transforms)
- ✅ Automatic scaling of positions and sizes
- ✅ Easy to add line width compensation

**Cons**:
- ⚠️ Requires refactoring render methods to use world coordinates
- ⚠️ Text rendering needs special handling

**Implementation**:
```python
def _on_draw(self, drawing_area, cr, width, height, manager):
    # Clear background
    cr.set_source_rgb(1.0, 1.0, 1.0)
    cr.paint()
    
    # Draw grid in device space
    manager.draw_grid(cr)
    
    # Apply zoom transformation
    cr.save()
    cr.translate(manager.pan_x * manager.zoom, manager.pan_y * manager.zoom)
    cr.scale(manager.zoom, manager.zoom)
    
    # Draw objects in world coordinates
    for obj in manager.get_all_objects():
        obj.render(cr, zoom=manager.zoom)  # Pass zoom for line width compensation
    
    cr.restore()
```

### Approach 2: Per-Object Transform (CURRENT - Needs Fixes)

Continue using per-coordinate transforms, but fix radius scaling and line width compensation.

**Pros**:
- ✅ Maintains current architecture
- ✅ Explicit coordinate transforms (easier to debug)

**Cons**:
- ❌ More complex render methods
- ❌ Must transform every coordinate pair
- ❌ Harder to ensure consistency
- ❌ Performance overhead (more function calls)

**Implementation**:
```python
def render(self, cr, transform=None, zoom=1.0):
    if transform:
        screen_x, screen_y = transform(self.x, self.y)
        screen_radius = self.radius * zoom  # FIX: Scale radius
    else:
        screen_x, screen_y = self.x, self.y
        screen_radius = self.radius
    
    cr.arc(screen_x, screen_y, screen_radius, 0, 2 * math.pi)
    cr.set_source_rgb(*self.border_color)
    cr.set_line_width(self.border_width / zoom)  # FIX: Compensate line width
    cr.stroke()
```

---

## Recommended Implementation Plan

### Phase 1: Fix Coordinate Transformations ✅

**Goal**: Match legacy transformation formulas.

**Changes to `model_canvas_manager.py`**:

```python
def screen_to_world(self, screen_x, screen_y):
    """Convert screen coordinates to world (model) coordinates.
    
    Legacy formula: world = screen / zoom - pan
    """
    world_x = (screen_x / self.zoom) - self.pan_x
    world_y = (screen_y / self.zoom) - self.pan_y
    return world_x, world_y

def world_to_screen(self, world_x, world_y):
    """Convert world (model) coordinates to screen coordinates.
    
    Legacy formula: screen = (world + pan) * zoom
    """
    screen_x = (world_x + self.pan_x) * self.zoom
    screen_y = (world_y + self.pan_y) * self.zoom
    return screen_x, screen_y
```

### Phase 2: Adopt Cairo Transform Approach ✅

**Goal**: Apply `cr.scale()` transformation like legacy code.

**Changes to `model_canvas_loader.py`**:

```python
def _on_draw(self, drawing_area, cr, width, height, manager):
    # Update viewport size
    if manager.viewport_width != width or manager.viewport_height != height:
        manager.set_viewport_size(width, height)
    
    # Clear background
    cr.set_source_rgb(1.0, 1.0, 1.0)
    cr.paint()
    
    # Draw grid (in device space, before transform)
    manager.draw_grid(cr)
    
    # Apply pan and zoom transformation
    cr.save()
    cr.translate(manager.pan_x * manager.zoom, manager.pan_y * manager.zoom)
    cr.scale(manager.zoom, manager.zoom)
    
    # Draw objects in world coordinates (they scale automatically)
    for obj in manager.get_all_objects():
        obj.render(cr, zoom=manager.zoom)  # Pass zoom for line width compensation
    
    cr.restore()
    
    # Draw arc preview in device space (after restore)
    if drawing_area in self._arc_state:
        arc_state = self._arc_state[drawing_area]
        if (manager.is_tool_active() and manager.get_tool() == 'arc' and 
            arc_state['source'] is not None):
            self._draw_arc_preview(cr, arc_state, manager)
    
    manager.mark_clean()
```

### Phase 3: Update Object Render Methods ✅

**Goal**: Remove explicit coordinate transforms, add line width compensation.

**Changes to `place.py`, `transition.py`, `arc.py`, etc.**:

```python
# OLD (with transform function):
def render(self, cr, transform=None):
    if transform:
        screen_x, screen_y = transform(self.x, self.y)
        screen_radius = self.radius
    else:
        screen_x, screen_y = self.x, self.y
        screen_radius = self.radius
    
    cr.arc(screen_x, screen_y, screen_radius, 0, 2 * math.pi)
    cr.set_line_width(self.border_width)
    cr.stroke()

# NEW (with zoom parameter):
def render(self, cr, zoom=1.0):
    # Draw in world coordinates (Cairo transform handles scaling)
    cr.arc(self.x, self.y, self.radius, 0, 2 * math.pi)
    cr.set_line_width(self.border_width / max(zoom, 1e-6))  # Compensate for zoom
    cr.stroke()
```

**Note**: Selection highlights, arrowheads, and other pixel-based elements must also compensate:

```python
# Selection highlight (always 3px visual width)
if self.selected:
    cr.arc(self.x, self.y, self.radius + 3 / zoom, 0, 2 * math.pi)
    cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)
    cr.set_line_width(3.0 / zoom)  # Compensate
    cr.stroke()
```

### Phase 4: Fix Arc Preview Rendering ✅

**Goal**: Arc preview line should also maintain constant pixel width.

**Changes to `_draw_arc_preview()` in `model_canvas_loader.py`**:

Currently, arc preview is drawn in screen space (after `cr.restore()`), so it doesn't need zoom compensation. However, if we want consistency, we could draw it in world space:

```python
def _draw_arc_preview(self, cr, arc_state, manager):
    """Draw orange preview line for arc creation (in world space)."""
    source = arc_state['source']
    cursor_x, cursor_y = arc_state['cursor_pos']
    
    # Source position (already in world coordinates)
    src_x, src_y = source.x, source.y
    
    # Calculate direction
    dx = cursor_x - src_x
    dy = cursor_y - src_y
    dist = math.sqrt(dx * dx + dy * dy)
    
    if dist < 1:
        return
    
    ux, uy = dx / dist, dy / dist
    
    # Determine source radius
    if isinstance(source, Place):
        src_radius = source.radius
    elif isinstance(source, Transition):
        w = source.width if source.horizontal else source.height
        h = source.height if source.horizontal else source.width
        src_radius = max(w, h) / 2.0
    else:
        src_radius = 20.0
    
    # Start point (offset by radius)
    start_x = src_x + ux * src_radius
    start_y = src_y + uy * src_radius
    
    # Draw in world space (Cairo transform active)
    cr.set_source_rgba(0.95, 0.5, 0.1, 0.85)
    cr.set_line_width(2.0 / manager.zoom)  # Compensate for zoom
    cr.move_to(start_x, start_y)
    cr.line_to(cursor_x, cursor_y)
    cr.stroke()
    
    # Arrowhead (scaled sizes)
    arrow_len = 11.0 / manager.zoom
    arrow_width = 6.0 / manager.zoom
    
    left_x = cursor_x - arrow_len * ux + arrow_width * (-uy)
    left_y = cursor_y - arrow_len * uy + arrow_width * ux
    right_x = cursor_x - arrow_len * ux - arrow_width * (-uy)
    right_y = cursor_y - arrow_len * uy - arrow_width * ux
    
    cr.move_to(cursor_x, cursor_y)
    cr.line_to(left_x, left_y)
    cr.line_to(right_x, right_y)
    cr.close_path()
    cr.fill()
```

### Phase 5: Improve Scroll Handler ✅

**Goal**: Add smooth scroll support (trackpad).

**Changes to `_on_scroll_event()` in `model_canvas_loader.py`**:

```python
def _on_scroll_event(self, widget, event, manager):
    """Handle scroll events for zoom (GTK3)."""
    direction = event.direction
    factor = None
    
    # Smooth scrolling (trackpad) uses delta_y sign
    if direction == Gdk.ScrollDirection.SMOOTH:
        dy = event.delta_y
        if abs(dy) < 1e-6:
            return False
        factor = (1 / 1.1) if dy > 0 else 1.1
    else:
        # Discrete scroll wheel
        if direction == Gdk.ScrollDirection.UP:
            factor = 1.1  # Zoom in 10%
        elif direction == Gdk.ScrollDirection.DOWN:
            factor = 1 / 1.1  # Zoom out 10%
    
    if factor is None:
        return False
    
    manager.zoom_at_point(factor, event.x, event.y)
    widget.queue_draw()
    return True
```

### Phase 6: Extend Zoom Range (Optional) ⚠️

**Goal**: Match legacy zoom range (5% to 2000%).

**Changes to `model_canvas_manager.py`**:

```python
def zoom_at_point(self, factor, screen_x, screen_y):
    # ...
    old_zoom = self.zoom
    self.zoom = max(0.05, min(20.0, self.zoom * factor))  # Extended range
    # ...
```

**Warning**: Very high zoom (> 10x) may cause rendering artifacts. Test carefully!

---

## Testing Checklist

### Basic Zoom
- [ ] Scroll wheel zooms in/out (10% increments)
- [ ] Trackpad smooth scroll zooms in/out
- [ ] Zoom range limited to 0.05-20.0 (5%-2000%)
- [ ] Zoom indicator shows correct percentage

### Pointer-Centered Zoom
- [ ] Zoom keeps cursor position fixed in world space
- [ ] Works at canvas center
- [ ] Works at canvas edges
- [ ] Works with objects under cursor

### Object Scaling
- [ ] Places scale with zoom (radius increases/decreases)
- [ ] Transitions scale with zoom (width/height increase/decrease)
- [ ] Arcs follow connected objects correctly
- [ ] Tokens stay centered in places
- [ ] Labels stay positioned correctly

### Line Width Consistency
- [ ] Place borders maintain 3px visual width at all zoom levels
- [ ] Transition borders maintain 3px visual width at all zoom levels
- [ ] Arc lines maintain 2px visual width at all zoom levels
- [ ] Selection highlights maintain 3px visual width at all zoom levels
- [ ] Arc preview line maintains 2px visual width at all zoom levels

### Interaction with Zoom
- [ ] Selection works at different zoom levels
- [ ] Arc creation works at different zoom levels
- [ ] Panning works at different zoom levels
- [ ] Hit testing accuracy at different zoom levels

### Edge Cases
- [ ] Zoom at minimum (5%): Objects very small but visible
- [ ] Zoom at maximum (2000%): Objects very large, lines stay thin
- [ ] Rapid zoom in/out doesn't cause drift
- [ ] Zoom with no objects (empty canvas)

---

## Summary

### Key Changes Needed

1. **✅ Fix coordinate transformations** - Match legacy formulas
2. **✅ Adopt Cairo transform** - Apply `cr.scale()` and `cr.translate()`
3. **✅ Update render methods** - Remove explicit transforms, add zoom parameter
4. **✅ Add line width compensation** - Divide by zoom for constant pixel widths
5. **✅ Fix radius scaling** - Use world coordinates, let Cairo scale automatically
6. **✅ Improve scroll handler** - Add smooth scroll support
7. **⚠️ Optional: Extend zoom range** - 0.05 to 20.0 (test carefully!)

### Estimated Impact

- **Lines Changed**: ~200-300 across multiple files
- **Files Modified**: 6-8 (manager, loader, place, transition, arc, inhibitor_arc)
- **Risk Level**: Medium (coordinate system changes affect everything)
- **Testing Required**: Extensive (all interactions at multiple zoom levels)

### Priority

**HIGH** - Zoom is a fundamental navigation feature. Users expect it to work correctly.

---

## References

- Legacy interactions: `legacy/shypnpy/interface/interactions.py`
- Legacy coords: `legacy/shypnpy/interface/coords.py`
- Legacy rendering: `legacy/shypnpy/interface/validate_ui.py`
- Legacy drawing: `legacy/shypnpy/interface/color_utils.py`
- Current manager: `src/shypn/data/model_canvas_manager.py`
- Current loader: `src/shypn/helpers/model_canvas_loader.py`
- Current objects: `src/shypn/api/*.py`
