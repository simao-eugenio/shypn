"""
Arc Rendering Status and Troubleshooting Guide
===============================================

## Current Status

### ✓ Arc Implementation (COMPLETE)

1. **Arc Class** (`src/shypn/api/arc.py`)
   - Properly defined with render() method
   - Calculates boundary intersections correctly
   - Draws line from source to target with arrowhead
   - Color: Black `(0.0, 0.0, 0.0)`
   - Width: 3.0px
   - Validates bipartite connections (Place ↔ Transition only)

2. **TransientArc Class** (`src/shypn/edit/transient_arc.py`)
   - Preview arc for visual feedback during editing
   - Color: Orange `(0.95, 0.5, 0.1)`
   - Width: 2.0px
   - NOT added to model (temporary only)
   - Includes TransientArcManager helper

3. **Model Integration** (`src/shypn/data/model_canvas_manager.py`)
   - Arcs stored in `manager.arcs` list
   - `add_arc()` method works correctly
   - `get_all_objects()` returns arcs FIRST (correct rendering order)
   - Test objects create 2 arcs: P1→T1 and T1→P2

### ✓ Rendering Order (CORRECT)

```python
def get_all_objects(self):
    # Arcs render first → appear behind nodes
    return list(self.arcs) + list(self.places) + list(self.transitions)
```

Order: Arcs (behind) → Places → Transitions (on top)

### ✓ Draw Callback (`src/shypn/helpers/model_canvas_loader.py`)

```python
def _on_draw(self, drawing_area, cr, width, height, manager):
    # Clear background
    cr.set_source_rgb(1.0, 1.0, 1.0)  # White
    cr.paint()
    
    # Draw grid
    manager.draw_grid(cr)
    
    # Draw objects (arcs first, then nodes)
    for obj in manager.get_all_objects():
        obj.render(cr, manager.world_to_screen)
```

## Diagnostic Results

**Test 1: Arc Logic** (`tests/test_arc_rendering.py`)
```
✓ Arc created successfully
✓ Direction vector calculated
✓ Boundary points calculated
✓ Cairo operations called
```

**Test 2: Model Integration** (`tests/diagnose_arc_rendering.py`)
```
✓ 2 arcs created in test network
✓ Arcs in manager.arcs collection
✓ get_all_objects() returns 5 objects (2 arcs, 2 places, 1 transition)
✓ Arcs render first (correct order)
✓ Arc.render() method exists
✓ Arc length sufficient (100 units)
✓ Arc color black (visible on white)
✓ Arc width 3.0px (visible)
```

## Possible Issues (If Arcs Not Visible)

### 1. Transform Function Issues

The `world_to_screen` transform might not be working:

```python
# In manager.world_to_screen:
screen_x = (world_x - self.pan_x) * self.zoom
screen_y = (world_y - self.pan_y) * self.zoom

# Check:
# - Is zoom != 0?
# - Are coordinates in viewport?
# - Is pan correct?
```

**Test:** Try rendering without transform:
```python
obj.render(cr, transform=None)  # Use world coords directly
```

### 2. Cairo Context Issues

Cairo context might be invalid or state corrupted:

```python
# Add debugging in render:
def render(self, cr, transform=None):
    cr.save()  # Save state
    try:
        # ... rendering code ...
        print(f"Rendering {self.name}: {self.source.name} → {self.target.name}")
    except Exception as e:
        print(f"Error rendering {self.name}: {e}")
    finally:
        cr.restore()  # Restore state
```

### 3. Draw Callback Not Triggered

The GTK draw signal might not be connected:

**Check in model_canvas_loader.py:**
```python
def create_canvas(self):
    drawing_area = Gtk.DrawingArea()
    # Is this being called?
    drawing_area.set_draw_func(
        lambda da, cr, w, h: self._on_draw(da, cr, w, h, manager)
    )
```

### 4. Objects Outside Viewport

Arcs might be positioned outside the visible area:

```python
# Check coordinates:
print(f"Viewport: {manager.viewport_width}x{manager.viewport_height}")
print(f"Pan: ({manager.pan_x}, {manager.pan_y})")
print(f"Zoom: {manager.zoom}")
print(f"Arc endpoints: ({arc.source.x}, {arc.source.y}) → ({arc.target.x}, {arc.target.y})")
```

**Solution:** Use "Fit to View" or zoom out to see entire network.

### 5. Exceptions During Render

Silent exceptions might prevent rendering:

```python
# Add try-catch in draw loop:
for obj in manager.get_all_objects():
    try:
        obj.render(cr, manager.world_to_screen)
    except Exception as e:
        print(f"Error rendering {obj.__class__.__name__} {obj.name}: {e}")
        import traceback
        traceback.print_exc()
```

### 6. GTK4 vs GTK3 Differences

If using GTK4, the draw callback signature is different:

**GTK3:**
```python
drawing_area.connect('draw', callback)  # cr passed automatically
```

**GTK4:**
```python
drawing_area.set_draw_func(callback)  # Must create cr manually
```

## Debugging Steps

### Step 1: Add Debug Output to Arc.render()

```python
# In src/shypn/api/arc.py, add to render():
def render(self, cr, transform=None):
    print(f"[ARC RENDER] {self.name}: {self.source.name}→{self.target.name}")
    print(f"  World: ({self.source.x}, {self.source.y}) → ({self.target.x}, {self.target.y})")
    
    # ... existing code ...
    
    if transform:
        print(f"  Screen: ({start_x:.1f}, {start_y:.1f}) → ({end_x:.1f}, {end_y:.1f})")
```

### Step 2: Add Debug Output to Draw Callback

```python
# In src/shypn/helpers/model_canvas_loader.py:
def _on_draw(self, drawing_area, cr, width, height, manager):
    print(f"[DRAW] Viewport: {width}x{height}")
    print(f"[DRAW] Objects: {len(manager.get_all_objects())}")
    
    for obj in manager.get_all_objects():
        print(f"[DRAW] Rendering {obj.__class__.__name__}: {obj.name}")
        obj.render(cr, manager.world_to_screen)
```

### Step 3: Test Transform Function

```python
# Test world_to_screen transform:
manager = ModelCanvasManager()
manager.set_viewport_size(800, 600)
manager.pan_x = 0
manager.pan_y = 0
manager.zoom = 1.0

# Test point at origin
screen_x, screen_y = manager.world_to_screen(0, 0)
print(f"World (0,0) → Screen ({screen_x}, {screen_y})")

# Should be near center of viewport
expected_x = 400  # width/2
expected_y = 300  # height/2
```

### Step 4: Visual Debug - Draw Test Rectangle

```python
# Add to _on_draw before rendering objects:
# Draw a test rectangle to verify Cairo is working
cr.save()
cr.set_source_rgb(1.0, 0.0, 0.0)  # Red
cr.rectangle(10, 10, 100, 50)
cr.fill()
cr.restore()
# If you see red rectangle, Cairo is working!
```

## TransientArc Integration

TransientArc is NOT yet integrated into the canvas. To use it:

```python
# In canvas manager or interaction handler:
from shypn.edit.transient_arc import TransientArcManager

# Initialize
self.transient_manager = TransientArcManager()

# On mouse click (arc tool active, first click):
if hit_element:
    self.transient_manager.start_arc(hit_element)

# On mouse motion:
if self.transient_manager.has_active_arc():
    world_x, world_y = self.screen_to_world(event.x, event.y)
    self.transient_manager.update_cursor(world_x, world_y)
    self.queue_draw()

# In draw callback:
transient = self.transient_manager.get_active_arc()
if transient:
    transient.render(cr, manager.world_to_screen)

# On second click (create real arc):
source = self.transient_manager.get_source()
arc = Arc(source=source, target=target, ...)
manager.add_arc(arc)
self.transient_manager.finish_arc()
```

## Summary

### What Works
- ✓ Arc class implemented correctly
- ✓ TransientArc class ready for integration
- ✓ Model stores arcs properly
- ✓ Rendering order correct (arcs behind nodes)
- ✓ Draw callback exists and iterates objects
- ✓ Bipartite validation works

### What to Check
- ? Transform function (world_to_screen)
- ? Cairo context validity
- ? Draw callback actually being triggered
- ? Objects within viewport
- ? No silent exceptions during render
- ? GTK version compatibility

### Next Steps
1. Add debug output to confirm rendering is called
2. Test transform function with known coordinates
3. Verify Cairo context is valid
4. Check viewport/zoom/pan settings
5. Integrate TransientArc into canvas interactions
"""
