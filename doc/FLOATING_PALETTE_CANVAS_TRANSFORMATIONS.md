# Floating Palette Canvas Transformation Awareness

## Overview

The floating Swiss Knife Palette needs to be aware of canvas transformations (pan, zoom, rotation) to maintain correct positioning and bounds when the user manipulates the canvas view.

## Current Implementation (Commit: a706cd5)

**Status**: ✅ Functional but transformation-unaware  
**Behavior**: Palette stays in screen space (doesn't move with canvas)

### Architecture

```
┌─────────────────────────────────────────────────┐
│ GtkOverlay (canvas container)                   │
│                                                  │
│  ┌─────────────────────────┐                   │
│  │ GtkDrawingArea          │                   │
│  │ (canvas with zoom/pan)  │                   │
│  │                         │                   │
│  │  [Canvas content]       │                   │
│  │  zoom: 1.5x             │                   │
│  │  pan: (100, 50)         │                   │
│  └─────────────────────────┘                   │
│                                                  │
│       ┌──────────────────┐ ← Floating palette   │
│       │ Swiss Palette    │   (overlay widget)   │
│       │ margin: (200,100)│   Screen-space       │
│       └──────────────────┘   position           │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Current Signal Flow

```
User drags palette grip (⋮⋮)
    ↓
swissknife_palette_new._on_drag_motion()
    → Calculates dx/dy in screen space
    → Updates drag_offset_x/y
    ↓
swissknife_palette_new._update_position()
    → Emits position-changed(dx, dy)
    ↓
model_canvas_loader._on_swissknife_position_changed()
    → Updates widget margins (screen space)
    → new_left = current_left + dx
    → new_top = current_top + dy
```

## The Transformation Awareness Issue

### Problem Statement

When the canvas has pan/zoom/rotation applied:
1. **Overlay coordinates** (widget margins) are in screen/viewport space
2. **Canvas coordinates** are transformed by zoom/pan/rotation matrix
3. **Palette positioning** uses raw screen deltas without transformation awareness

This causes potential issues:

#### Issue 1: Rotation
If canvas is rotated 45°, dragging the palette horizontally would ideally compensate for the rotation, but currently uses raw screen deltas.

```
Canvas rotated 45° CW:
User drags right (dx=+10, dy=0)
Expected: Palette moves along rotated axes
Actual: Palette moves right in screen space (correct for overlay)
```

#### Issue 2: Bounds Checking
Current bounds use hard-coded screen pixel limits:
```python
new_left = max(-100, min(1000, int(current_left + dx)))
new_top = max(-50, min(800, int(current_top + dy)))
```

These bounds don't account for:
- Viewport size (user may resize window)
- Canvas zoom (zooming in makes effective canvas area larger)
- Multiple monitors (DPI differences)

#### Issue 3: Attachment Points
When switching from floating → attached, the palette returns to bottom-center. If canvas is heavily zoomed/panned, the "center" might be off-screen.

## Design Decision: Screen Space vs World Space

### Option 1: Screen Space (CURRENT - RECOMMENDED)

Palette stays at fixed screen position regardless of canvas transformations.

**Pros**:
- ✅ Palette always visible and accessible
- ✅ Intuitive behavior (doesn't move when canvas pans)
- ✅ Simple implementation (no coordinate transforms)
- ✅ Matches typical IDE tool palette behavior

**Cons**:
- ⚠️ Disconnected from canvas content
- ⚠️ Can obscure canvas objects at any zoom level

**Use Cases**: Tools, controls, overlays that should always be accessible

### Option 2: World Space (Alternative)

Palette position follows canvas transformations.

**Pros**:
- ✅ Stays "attached" to canvas location
- ✅ Useful for annotation tools

**Cons**:
- ❌ Can be panned off-screen (poor UX)
- ❌ Scales with zoom (hard to interact when zoomed)
- ❌ Complex coordinate transforms required
- ❌ Not suitable for tool palettes

**Use Cases**: Canvas annotations, sticky notes, diagrams

### Decision: Use Screen Space ✅

The Swiss Knife Palette is a tool palette, not canvas content. It should stay in screen space for:
1. Always accessible
2. Fixed size (doesn't scale with zoom)
3. Intuitive drag behavior
4. Consistent with UI conventions

## Implementation Requirements

### 1. Viewport-Aware Bounds

Replace hard-coded bounds with viewport-relative calculations:

**Current**:
```python
new_left = max(-100, min(1000, int(current_left + dx)))
new_top = max(-50, min(800, int(current_top + dy)))
```

**Proposed**:
```python
# Get viewport dimensions
viewport_width = drawing_area.get_allocated_width()
viewport_height = drawing_area.get_allocated_height()

# Get palette dimensions
palette_width = widget.get_allocated_width()
palette_height = widget.get_allocated_height()

# Allow small off-screen margins but keep mostly visible
min_visible_margin = 50  # Pixels that must stay on screen

new_left = max(-palette_width + min_visible_margin, 
               min(viewport_width - min_visible_margin, 
                   int(current_left + dx)))
new_top = max(-palette_height + min_visible_margin,
              min(viewport_height - min_visible_margin,
                  int(current_top + dy)))
```

### 2. Canvas Manager Integration

Pass canvas_manager reference to position handler for transformation queries:

**Current Signal**:
```python
# swissknife_palette_new.py
self.emit('position-changed', dx, dy)
```

**Proposed Addition** (optional, for future rotation support):
```python
# If we ever need rotation-aware dragging:
# swissknife_palette_new.py - pass canvas manager
def set_canvas_manager(self, canvas_manager):
    """Set canvas manager for transformation awareness."""
    self.canvas_manager = canvas_manager

def _on_drag_motion(self, widget, event):
    if self.drag_active:
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        
        # Optional: Rotate delta if canvas is rotated
        if self.canvas_manager:
            rotation = self.canvas_manager.transformation_manager.get_rotation()
            if rotation and rotation.angle_degrees != 0:
                # Transform drag delta by inverse rotation
                import math
                angle = -rotation.angle_radians
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                dx_rot = dx * cos_a - dy * sin_a
                dy_rot = dx * sin_a + dy * cos_a
                dx, dy = dx_rot, dy_rot
        
        self.drag_offset_x += dx
        self.drag_offset_y += dy
        # ... rest of handler
```

### 3. Attachment Point Validation

When switching to attached mode, verify the attachment point is visible:

**Current**:
```python
# model_canvas_loader.py
def _on_swissknife_float_toggled(self, palette, is_floating, widget):
    if not is_floating:
        # Attached mode: move to bottom center
        widget.set_halign(Gtk.Align.CENTER)
        widget.set_valign(Gtk.Align.END)
        widget.set_margin_bottom(20)
```

**Proposed Enhancement**:
```python
def _on_swissknife_float_toggled(self, palette, is_floating, widget, drawing_area=None):
    if not is_floating:
        # Attached mode: move to bottom center
        widget.set_halign(Gtk.Align.CENTER)
        widget.set_valign(Gtk.Align.END)
        
        # Ensure bottom margin keeps palette visible
        if drawing_area:
            viewport_height = drawing_area.get_allocated_height()
            palette_height = widget.get_allocated_height()
            min_margin = 20
            max_margin = viewport_height - palette_height - 10
            margin = max(min_margin, min(50, max_margin))
            widget.set_margin_bottom(margin)
        else:
            widget.set_margin_bottom(20)
```

## Implementation Priority

### Phase 1: Viewport-Aware Bounds (HIGH PRIORITY) ⚡

**Why**: Hard-coded bounds break with window resizing
**Impact**: Medium - can cause palette to disappear off-screen
**Effort**: Low - single handler modification
**File**: `src/shypn/helpers/model_canvas_loader.py`

```python
def _on_swissknife_position_changed(self, palette, dx, dy, widget, drawing_area):
    """Handle position change with viewport-aware bounds."""
    # Get viewport dimensions
    viewport_width = drawing_area.get_allocated_width()
    viewport_height = drawing_area.get_allocated_height()
    
    # Get palette dimensions
    palette_width = widget.get_allocated_width()
    palette_height = widget.get_allocated_height()
    
    # Calculate new position with dynamic bounds
    current_left = widget.get_margin_start()
    current_top = widget.get_margin_top()
    
    # Keep at least 50px of palette visible
    min_visible = 50
    new_left = max(-palette_width + min_visible,
                   min(viewport_width - min_visible,
                       int(current_left + dx)))
    new_top = max(-palette_height + min_visible,
                  min(viewport_height - min_visible,
                      int(current_top + dy)))
    
    widget.set_margin_start(new_left)
    widget.set_margin_top(new_top)
```

### Phase 2: Attachment Point Validation (MEDIUM PRIORITY)

**Why**: Ensure palette is visible when attaching
**Impact**: Low - edge case (small viewports)
**Effort**: Low - modify toggle handler
**File**: `src/shypn/helpers/model_canvas_loader.py`

### Phase 3: Rotation-Aware Dragging (LOW PRIORITY)

**Why**: Nice-to-have for rotated canvas workflows
**Impact**: Low - most users don't rotate canvas
**Effort**: Medium - requires coordinate transforms
**Files**: 
- `src/shypn/helpers/swissknife_palette_new.py` (drag motion)
- `src/shypn/helpers/model_canvas_loader.py` (handler)

## Testing Strategy

### Test Cases

1. **Window Resize**
   - Start with palette floating at edge
   - Resize window smaller
   - Expected: Palette repositions to stay visible

2. **Canvas Zoom**
   - Float palette to corner
   - Zoom in/out on canvas
   - Expected: Palette stays at same screen position

3. **Canvas Pan**
   - Float palette to center
   - Pan canvas in all directions
   - Expected: Palette doesn't move (screen-space)

4. **Canvas Rotation**
   - Rotate canvas 45°
   - Drag palette horizontally
   - Current: Moves in screen space (correct)
   - Future: Could optionally rotate drag vector

5. **Attach/Float Toggle**
   - Float palette near top
   - Toggle to attached
   - Expected: Moves to bottom-center
   - Toggle to float
   - Expected: Returns to last floating position

6. **Edge Cases**
   - Very small window (palette larger than viewport)
   - Multi-monitor with different DPI
   - Rapid zoom/pan while dragging

### Manual Testing Procedure

```bash
# 1. Start application
python3 src/shypn.py

# 2. Test floating
- Click ↖ button to float palette
- Drag to each corner using ⋮⋮ grip
- Verify palette stays on screen

# 3. Test with canvas transformations
- Zoom in/out with mouse wheel
- Pan canvas with middle-click drag
- Verify palette doesn't move

# 4. Test attachment
- Click 📌 button to attach
- Verify palette returns to bottom-center
- Click ↖ to float again
- Verify palette is at last position

# 5. Test window resize
- Float palette to bottom-right corner
- Resize window to half size
- Verify palette repositions to stay visible
```

## Future Enhancements

### 1. Position Memory Across Sessions
Save/restore floating palette position in workspace settings:
```json
{
  "swissknife_palette": {
    "is_floating": true,
    "position": {"x": 200, "y": 100}
  }
}
```

### 2. Snap-to-Edge Behavior
Magnetic edges for easier alignment:
```python
SNAP_THRESHOLD = 20  # pixels
if abs(new_left) < SNAP_THRESHOLD:
    new_left = 0  # Snap to left edge
if abs(new_left + palette_width - viewport_width) < SNAP_THRESHOLD:
    new_left = viewport_width - palette_width  # Snap to right
```

### 3. Multiple Preset Positions
Quick positioning with keyboard shortcuts:
- Ctrl+1: Bottom center (default)
- Ctrl+2: Top-left corner
- Ctrl+3: Top-right corner
- Ctrl+4: Bottom-left corner

### 4. Canvas-Relative Annotations
For future annotation/note tools, implement world-space positioning as separate overlay layer.

## References

- **Implementation**: 
  - `src/shypn/helpers/swissknife_palette_new.py` (lines 270-320)
  - `src/shypn/helpers/model_canvas_loader.py` (lines 1017-1050)

- **Canvas Transformations**:
  - `src/shypn/data/model_canvas_manager.py` (zoom, pan, rotation)
  - `src/shypn/core/canvas_transformations.py` (TransformationManager)

- **Related Documentation**:
  - `doc/SWISSKNIFE_PALETTE_REFACTORING_PHASE3.md` - Palette architecture
  - `doc/CANVAS_ROTATION_IMPLEMENTATION.md` - Rotation transforms
  - `doc/ZOOM_AND_SCALING_IMPLEMENTATION.md` - Zoom/pan system

## Status

- ✅ **Screen-space positioning working** (commit 4c517be)
- ✅ **Drag and drop functional** (commit a706cd5)
- ✅ **Float/attach toggle working**
- ⏰ **TODO: Viewport-aware bounds** (Phase 1)
- ⏰ **TODO: Attachment validation** (Phase 2)
- ⏰ **TODO: Rotation-aware dragging** (Phase 3, optional)

Last updated: 2025-10-23
