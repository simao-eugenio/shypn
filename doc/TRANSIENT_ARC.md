"""
TransientArc Implementation - Visual Feedback During Editing
=============================================================

Date: October 3, 2025
Branch: restructure-project

## Learning from Legacy Code

### 1. Arc Preview Module (`legacy/shypnpy/interface/arc_preview.py`)

The legacy implementation provides a dedicated arc preview overlay:

```python
def _on_draw(_widget, cr):
    tool = getattr(app,'_core_active_tool', getattr(app,'_active_tool',''))
    if tool != 'arc':
        return False
    
    src_id = getattr(app,'_core_arc_source', None) or getattr(app,'_arc_pending', None)
    cursor = getattr(app,'_last_cursor_pos', None)
    
    if src_id is None or cursor is None:
        return False
    
    # Draw orange preview line with arrowhead
    cr.set_source_rgba(0.95,0.5,0.1,0.85)  # Orange
    cr.set_line_width(2.0)
    cr.move_to(dsx, dsy)
    cr.line_to(dtx, dty)
    cr.stroke()
    
    # Arrowhead (11px length, 6px width)
    # ... triangle fill ...
```

**Key Insights:**
- **Orange color** `(0.95, 0.5, 0.1)` distinguishes preview from real arcs (black)
- **Semi-transparent** `alpha=0.85` shows it's temporary
- **Thin line** `2.0px` vs real arcs `3.0px`
- **No validation** - just visual feedback
- **Follows cursor** - updated on motion events
- **Arrowhead** shows direction

### 2. Interaction Pattern (`legacy/shypnpy/interface/interactions.py`)

State management during arc creation:

```python
# Initialize
app._core_arc_source = None

# On first click (source element)
if app._core_arc_source is None:
    if hit:
        app._core_arc_source = getattr(hit,'id',None)
        app.set_status(f"Arc: source {app._core_arc_source} selected; click target")

# On second click (target element)
else:
    if target_id is None or target_id == app._core_arc_source:
        pass  # Invalid
    else:
        # Create real arc
        arc = model.add_arc(app._core_arc_source, target_id)
        app.set_status(f"Arc created {app._core_arc_source}->{target_id}")
        # Clear preview
        app._core_arc_source = None

# On motion (update preview)
if getattr(app, '_core_active_tool','') == 'arc' and getattr(app,'_core_arc_source',None) is not None:
    lx, ly = cursor_logical_position
    app.set_status(f"Arc: source {app._core_arc_source} -> ({lx:.0f},{ly:.0f})")
```

**Key Insights:**
- **Two-click pattern**: Click source → Click target
- **State stored**: `_core_arc_source` holds source element ID
- **Motion events**: Update status and trigger redraw
- **Validation**: Only when creating real arc, not during preview
- **Cancellation**: Clear state on ESC or right-click

### 3. Fallback Rendering (`legacy/shypnpy/validate_ui.py`)

Legacy also has fallback preview in main draw loop:

```python
if getattr(self, '_active_tool', '') == 'arc' and getattr(self, '_arc_pending', None) is not None:
    start = getattr(self, '_arc_pending') or {}
    sid = start.get('id')
    # ... get source element ...
    
    # Draw fallback preview
    cr.set_source_rgba(0.0,0.0,0.0,0.55)  # Shadow
    cr.set_line_width(8.0)
    cr.move_to(sx, sy); cr.line_to(hx, hy); cr.stroke()
    
    cr.set_source_rgba(0.05,0.95,0.40,0.98)  # Green
    cr.set_line_width(3.0)
    cr.move_to(sx, sy); cr.line_to(hx, hy); cr.stroke()
```

## Our Implementation

### Design Decisions

1. **Separate from PetriNetObject hierarchy**
   - TransientArc is NOT a PetriNetObject
   - Never gets an id/name
   - Never added to model collections
   - Exists only during editing

2. **Located in `src/shypn/edit/`**
   - Not in `src/shypn/api/` (not part of the model)
   - Dedicated package for editing utilities
   - Clear separation of concerns

3. **Orange styling** (from legacy arc_preview.py)
   - Color: `(0.95, 0.5, 0.1)` - Orange
   - Alpha: `0.85` - Semi-transparent
   - Width: `2.0px` - Thinner than real arcs
   - Clearly distinguishable from real arcs (black)

4. **Manager pattern**
   - `TransientArcManager` simplifies state management
   - Encapsulates start/update/finish/cancel logic
   - Easy to integrate into canvas interaction handlers

### File Structure

```
src/shypn/edit/
├── __init__.py              # Package exports
└── transient_arc.py         # TransientArc + TransientArcManager
```

### Class Hierarchy

```
PetriNetObject (base class for model objects)
├── Place
├── Transition
└── Arc
    └── InhibitorArc

TransientArc (NOT derived from anything)
    - Standalone class for visual feedback only
    - Not part of the model hierarchy
```

### Usage Pattern

```python
# In canvas manager or interaction handler
from shypn.edit import TransientArc
from shypn.edit.transient_arc import TransientArcManager

# Initialize manager
self.transient_manager = TransientArcManager()

# === Arc Tool Activation ===
def on_arc_tool_activated(self):
    self.active_tool = 'arc'
    self.status = "Arc tool: Click source element"

# === First Click (Source) ===
def on_mouse_click(self, event):
    if self.active_tool != 'arc':
        return
    
    world_x, world_y = self.screen_to_world(event.x, event.y)
    hit = self.find_element_at(world_x, world_y)
    
    if not self.transient_manager.has_active_arc():
        # First click - select source
        if hit and isinstance(hit, (Place, Transition)):
            self.transient_manager.start_arc(hit, world_x, world_y)
            self.status = f"Arc: source {hit.name} selected, click target"
            self.canvas.queue_draw()
    else:
        # Second click - select target
        source = self.transient_manager.get_source()
        if hit and isinstance(hit, (Place, Transition)) and hit != source:
            try:
                # Create real arc (validates bipartite property)
                arc = Arc(source=source, target=hit, id=..., name=...)
                self.model.add_arc(arc)
                self.transient_manager.finish_arc()
                self.status = f"Arc {arc.name} created"
                self.canvas.queue_draw()
            except ValueError as e:
                # Invalid connection (e.g., Place->Place)
                self.show_error(str(e))
                self.transient_manager.cancel_arc()

# === Mouse Motion (Update Preview) ===
def on_mouse_motion(self, event):
    if self.active_tool != 'arc':
        return
    
    if self.transient_manager.has_active_arc():
        world_x, world_y = self.screen_to_world(event.x, event.y)
        self.transient_manager.update_cursor(world_x, world_y)
        self.canvas.queue_draw()  # Trigger redraw

# === Canvas Draw (Render Preview) ===
def on_canvas_draw(self, widget, cr):
    # ... draw grid, model objects ...
    
    # Draw transient arc preview (if active)
    transient = self.transient_manager.get_active_arc()
    if transient:
        transient.render(cr, self.world_to_screen)
    
    return False

# === Cancellation (ESC, right-click) ===
def on_key_press(self, event):
    if event.keyval == Gdk.KEY_Escape:
        if self.transient_manager.has_active_arc():
            self.transient_manager.cancel_arc()
            self.status = "Arc creation canceled"
            self.canvas.queue_draw()

def on_right_click(self, event):
    if self.transient_manager.has_active_arc():
        self.transient_manager.cancel_arc()
        self.status = "Arc creation canceled"
        self.canvas.queue_draw()
```

## Comparison: Legacy vs Current

| Aspect | Legacy | Current |
|--------|--------|---------|
| **Storage** | `app._core_arc_source` (element ID) | `TransientArcManager` (object reference) |
| **Preview Object** | No explicit object, inline rendering | `TransientArc` class |
| **Color** | Orange `(0.95,0.5,0.1)` | Same |
| **Update Trigger** | Motion events + timer | Motion events only |
| **Validation** | None (deferred to add_arc) | None (deferred to Arc.__init__) |
| **Cancellation** | Clear `_core_arc_source` | `manager.cancel_arc()` |
| **Integration** | Scattered across multiple files | Centralized in `TransientArcManager` |

## Benefits of Our Approach

1. **Cleaner Separation**
   - Visual feedback code separate from model code
   - Clear boundary between editing and model

2. **Object-Oriented**
   - TransientArc is a proper class (not just state variables)
   - Encapsulates rendering logic

3. **Type Safety**
   - Object references instead of IDs
   - No lookup needed

4. **Easier Testing**
   - Can test TransientArc independently
   - No dependency on GTK/Cairo for logic tests

5. **Manager Pattern**
   - Simplified state management
   - Clear API for common operations

## Test Coverage

All tests pass (8/8):
- ✓ TransientArc creation
- ✓ Cursor updates
- ✓ Not a PetriNetObject
- ✓ TransientArcManager state management
- ✓ Arc cancellation
- ✓ Different source types (Place/Transition)
- ✓ Visual styling (orange, distinct from real arcs)
- ✓ No connection validation (deferred to real Arc)

## Next Steps

1. **Integrate into canvas interactions**
   - Add TransientArcManager to canvas manager
   - Hook up mouse events (click, motion)
   - Render in draw callback

2. **User feedback**
   - Status bar messages during arc creation
   - Cursor change when hovering valid targets
   - Error messages for invalid connections

3. **Additional features**
   - Snap to grid during arc creation
   - Show connection validity indicator (green/red)
   - Multi-arc mode (create multiple arcs without tool change)

## Summary

TransientArc provides visual feedback during arc creation:
- **Orange preview line** follows cursor
- **Two-click pattern**: source → target
- **No validation** until real arc created
- **Clean separation** from model objects
- **Manager pattern** simplifies integration

Learned from legacy:
- Orange color for distinction
- Semi-transparent for temporary feel
- No validation during preview
- Simple state management pattern
"""
