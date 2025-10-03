# Selection and Arc Creation Analysis

## Overview

This document analyzes how object selection and arc creation work in the legacy shypnpy code, which is the foundation for interactive Petri net editing.

**Source**: `legacy/shypnpy/interface/interactions.py`

---

## Key Concepts

### 1. Tool System

Legacy uses a **single active tool** paradigm:
```python
TOOLS = ("place", "transition", "select", "arc", "lasso")
```

- Only ONE tool is active at a time
- Tools are mutually exclusive (radio button behavior)
- Default tool: `select`
- Tool buttons are toggle buttons with exclusive behavior

### 2. Selection Mechanism

#### Simple Selection (Select Tool Active)

When the **select tool** is active and user clicks:

1. **Hit Test**: Determine which object (if any) is under the cursor
   ```python
   obj = _resolve_hit(model, lx, ly)
   ```

2. **Toggle Selection**: Flip the object's `selected` flag
   ```python
   cur = bool(getattr(obj, 'selected', False))
   setattr(obj, 'selected', not cur)
   ```

3. **Visual Feedback**: Selected objects have a `selected` attribute = `True`
   - Renderer checks this flag and draws selection highlight
   - Blue outline or color change for selected objects

#### Selection Storage

- **Property**: Each object has a `selected` attribute (boolean)
- **Default**: `False` (not selected)
- **Multiple Selection**: Multiple objects can be selected simultaneously
- **Clear Selection**: Set all `selected` flags to `False`

### 3. Arc Creation Workflow

Arc creation is a **two-click process**:

#### State Machine

```
[No Source] --click on Place/Transition--> [Source Selected] --click on Place/Transition--> [Arc Created] --> [No Source]
                                                                    |
                                                                    v
                                                              (if invalid: stay in Source Selected)
```

#### Implementation Details

**State Storage**:
```python
app._core_arc_source = None  # Holds source element ID when first click made
```

**Click 1 - Select Source**:
```python
if tool == 'arc' and app._core_arc_source is None:
    hit = _resolve_hit(model, lx, ly)
    if hit is not None and hit.type in ('place', 'transition'):
        app._core_arc_source = hit.id
        # Status: "Arc: source {id} selected; click target"
```

**Click 2 - Create Arc**:
```python
if tool == 'arc' and app._core_arc_source is not None:
    target = _resolve_hit(model, lx, ly)
    if target is not None and target.id != app._core_arc_source:
        try:
            arc = model.add_arc(app._core_arc_source, target.id)
            # Record in undo, set dirty flag
        finally:
            app._core_arc_source = None  # Reset for next arc
```

**Visual Preview**:
- While `_core_arc_source` is set, draw orange preview line from source to cursor
- Preview uses `_last_cursor_pos` updated in motion event
- Preview line includes arrowhead at cursor position

#### Reset Arc Creation

- **Click on empty space**: Resets `_core_arc_source` to `None`
- **Tool change**: Should reset state (implementation detail)

---

## Hit Testing

### Purpose
Determine which object (if any) is under a click position.

### Implementation

1. **Primary**: Use dedicated `hittest.hit_test_element(model, x, y)` function
2. **Fallback**: Simple geometric checks
   - Places: Distance from center < radius
   - Transitions: Point inside bounding box

```python
def _resolve_hit(model, lx, ly):
    # Try sophisticated hit_test_element first
    if hit_test_element:
        res = hit_test_element(model, lx, ly)
        return res.get('object')
    
    # Fallback: simple checks
    for p in model.places.values():
        dx = lx - p.x; dy = ly - p.y
        if dx*dx + dy*dy <= p.radius**2:
            return p
    
    for t in model.transitions.values():
        if t.is_point_inside(lx, ly):
            return t
    
    return None
```

---

## Visual Feedback

### 1. Selection Highlight

Objects with `selected = True` get visual distinction:
- **Brighter color**: +0.3 brightness for selected
- **Thicker border**: +2px or similar
- **Blue tint**: Some implementations use blue overlay
- **Bounding box**: Dotted rectangle around selected elements

### 2. Arc Preview Line

When creating an arc (`_core_arc_source` is set):

**Properties**:
- Color: Orange (0.95, 0.5, 0.1)
- Alpha: 0.85 (semi-transparent)
- Line width: 2.0px
- Style: Dashed or solid depending on implementation

**Drawing**:
```python
# Get source position
src_x, src_y = source_element.x, source_element.y

# Get cursor position
cursor_x, cursor_y = app._last_cursor_pos

# Calculate start point (offset by source radius)
distance = sqrt((cursor_x - src_x)^2 + (cursor_y - src_y)^2)
unit_x, unit_y = (cursor_x - src_x) / distance, (cursor_y - src_y) / distance
start_x = src_x + unit_x * source_radius
start_y = src_y + unit_y * source_radius

# Draw line
cr.set_source_rgba(0.95, 0.5, 0.1, 0.85)
cr.set_line_width(2.0)
cr.move_to(start_x_screen, start_y_screen)
cr.line_to(cursor_x_screen, cursor_y_screen)
cr.stroke()

# Draw arrowhead at cursor
# (smaller preview arrowhead: 11px length, 6px width)
```

---

## Coordinate Transformations

### World Space vs Screen Space

**World Space** (Logical):
- Model coordinates (where objects actually live)
- Independent of zoom/pan
- Used for: Hit testing, object positions, arc connections

**Screen Space** (Device):
- Pixel coordinates on screen
- Affected by zoom and pan
- Used for: Rendering, mouse events

### Transformation Functions

**Device → Logical**:
```python
def device_to_logical(px, py):
    scale = app.zoom_scale
    pan_x = app._pan_x
    pan_y = app._pan_y
    return (px / scale - pan_x, py / scale - pan_y)
```

**Logical → Device**:
```python
def logical_to_device(lx, ly):
    scale = app.zoom_scale
    pan_x = app._pan_x
    pan_y = app._pan_y
    return ((lx + pan_x) * scale, (ly + pan_y) * scale)
```

**Usage**:
```python
# Mouse event gives device coordinates
def on_button_press(widget, event):
    device_x, device_y = event.x, event.y
    
    # Convert to logical for hit testing
    logical_x, logical_y = device_to_logical(device_x, device_y)
    
    # Hit test in logical space
    obj = resolve_hit(model, logical_x, logical_y)
```

---

## Event Handling

### GTK Event Masks

Required event masks for drawing area:
```python
da.add_events(
    Gdk.EventMask.BUTTON_PRESS_MASK |
    Gdk.EventMask.POINTER_MOTION_MASK |
    Gdk.EventMask.BUTTON_RELEASE_MASK |
    Gdk.EventMask.SCROLL_MASK
)
```

### Event Handlers

1. **button-press-event**: Tool-specific actions (select, create, start arc)
2. **motion-notify-event**: Preview updates (arc line, drag)
3. **button-release-event**: Finalize actions (end drag)
4. **scroll-event**: Zoom in/out
5. **draw**: Render overlays (selection box, arc preview)

---

## Implementation Strategy for Current Code

### Phase 1: Basic Selection (Simple, No Tools Yet)

Since you want **left-click to always select** (no tool system initially):

1. **Add `selected` property to PetriNetObject**:
   ```python
   class PetriNetObject:
       def __init__(self, ...):
           # ... existing code ...
           self.selected = False
   ```

2. **Implement hit testing in canvas**:
   ```python
   def on_button_press(self, widget, event):
       if event.button == 1:  # Left click
           lx, ly = self.device_to_logical(event.x, event.y)
           obj = self.find_object_at(lx, ly)
           if obj:
               obj.selected = not obj.selected  # Toggle
               self.queue_draw()
   ```

3. **Update rendering to show selection**:
   ```python
   def render(self, cr, transform=None):
       # ... normal rendering ...
       
       if self.selected:
           # Draw blue highlight
           cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)
           cr.set_line_width(self.border_width + 4)
           # Draw outline again with highlight color
   ```

### Phase 2: Arc Creation

1. **Add arc creation state to canvas/app**:
   ```python
   self._arc_source = None  # Element being used as arc source
   self._last_cursor_pos = (0, 0)  # For preview line
   ```

2. **Modify click handler**:
   ```python
   def on_button_press(self, widget, event):
       if event.button == 1:
           lx, ly = self.device_to_logical(event.x, event.y)
           obj = self.find_object_at(lx, ly)
           
           # If Control key held: start arc creation
           if event.state & Gdk.ModifierType.CONTROL_MASK:
               if self._arc_source is None:
                   # First click: set source
                   if obj and isinstance(obj, (Place, Transition)):
                       self._arc_source = obj
               else:
                   # Second click: create arc
                   if obj and obj != self._arc_source:
                       try:
                           arc = Arc(self._arc_source, obj, ...)
                           self.model.add_arc(arc)
                       except ValueError as e:
                           # Bipartite validation failed
                           print(f"Cannot create arc: {e}")
                       finally:
                           self._arc_source = None
           else:
               # Normal click: toggle selection
               if obj:
                   obj.selected = not obj.selected
   ```

3. **Add motion handler for preview**:
   ```python
   def on_motion_notify(self, widget, event):
       lx, ly = self.device_to_logical(event.x, event.y)
       self._last_cursor_pos = (lx, ly)
       
       if self._arc_source is not None:
           self.queue_draw()  # Redraw to show preview
   ```

4. **Draw preview line**:
   ```python
   def draw_overlays(self, cr):
       if self._arc_source is not None:
           # Draw orange preview line
           src_x, src_y = self._arc_source.x, self._arc_source.y
           cursor_x, cursor_y = self._last_cursor_pos
           
           # ... calculate offset by radius ...
           
           cr.set_source_rgba(0.95, 0.5, 0.1, 0.85)
           cr.set_line_width(2.0)
           cr.move_to(start_x, start_y)
           cr.line_to(cursor_x, cursor_y)
           cr.stroke()
   ```

### Phase 3: Tool System (Future)

Later, add proper tool buttons:
- Place tool (P key)
- Transition tool (T key)
- Arc tool (A key)
- Select tool (S key)

With exclusive toggle behavior and status bar feedback.

---

## Summary

### Key Patterns

1. **Selection**: Boolean flag on each object (`selected`)
2. **Arc Creation**: Two-click state machine with preview
3. **Hit Testing**: Geometric checks in logical (world) space
4. **Visual Feedback**: Highlights for selection, orange line for arc preview
5. **Coordinate Transform**: Device ↔ Logical using zoom/pan parameters

### Priority Implementation Order

1. ✅ Add `selected` property to PetriNetObject
2. ✅ Implement basic hit testing (circle/rectangle checks)
3. ✅ Left-click toggles selection
4. ✅ Render selection highlight (blue outline)
5. 🔄 Add arc creation state (`_arc_source`)
6. 🔄 Two-click arc creation (Control+click)
7. 🔄 Draw arc preview line (orange)
8. 🔄 Motion event updates preview
9. ⏳ Tool system (buttons, exclusive behavior)
10. ⏳ Keyboard shortcuts (P/T/A/S)

---

## Code Examples from Legacy

### Selection Toggle
```python
# From interactions.py line ~270
if tool == 'select':
    obj = _resolve_hit(model, lx, ly)
    if obj is not None:
        cur = bool(getattr(obj, 'selected', False))
        setattr(obj, 'selected', not cur)
        widget.queue_draw()
```

### Arc Preview Drawing
```python
# From interactions.py line ~400
if app._core_arc_source is not None:
    src = model.get_element_by_id(app._core_arc_source)
    cursor = app._last_cursor_pos
    
    sx, sy = src.x, src.y
    tx, ty = cursor
    
    # Offset start by source radius
    dx, dy = tx - sx, ty - sy
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist
    sr = src.radius  # or max(width, height)/2
    tsx, tsy = sx + ux * sr, sy + uy * sr
    
    # Draw preview line
    cr.set_source_rgba(0.95, 0.5, 0.1, 0.85)
    cr.set_line_width(2.0)
    cr.move_to(tsx_screen, tsy_screen)
    cr.line_to(tx_screen, ty_screen)
    cr.stroke()
```

### Hit Testing Fallback
```python
# From interactions.py line ~177
for p in model.places.values():
    dx = lx - p.x; dy = ly - p.y
    if dx*dx + dy*dy <= p.radius**2:
        return p

for t in model.transitions.values():
    if t.is_point_inside(lx, ly):
        return t
```

---

## References

- **Legacy File**: `legacy/shypnpy/interface/interactions.py`
- **Related**: `legacy/shypnpy/interface/arc_preview.py` (TransientArc implementation)
- **Related**: `doc/TRANSIENT_ARC.md` (Our current TransientArc docs)
