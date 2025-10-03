# Model Canvas Architecture - Deep Analysis

## Overview
The model canvas is a multi-document Petri Net drawing area with zoom, pan, and grid features. It follows a clean separation between UI (GTK3), Controller (loader), and Data (manager).

---

## File Structure

### 1. UI Layer: `ui/canvas/model_canvas.ui`
**GTK3 XML Interface Definition**

```xml
GtkBox (model_canvas_container)
└── GtkNotebook (canvas_notebook) [scrollable tabs]
    └── Page 1 (default)
        ├── GtkOverlay (canvas_overlay_1)
        │   ├── GtkScrolledWindow (canvas_scroll_1)
        │   │   └── GtkDrawingArea (canvas_drawing_1) [800x600]
        │   └── GtkBox (canvas_overlay_box_1) [overlay - bottom-right]
        │       └── [Zoom control added programmatically]
        └── Tab Label: "Model 1"
```

**Key Properties:**
- **Notebook**: Scrollable tabs, popup menu enabled, borders shown
- **Overlay**: Allows floating widgets (zoom palette) over canvas
- **ScrolledWindow**: Automatic scrollbars for large canvas (2000x2000)
- **DrawingArea**: Actual drawing surface, default 800x600 viewport

---

## 2. Controller Layer: `src/shypn/helpers/model_canvas_loader.py`

### Purpose
Manages UI loading, document lifecycle, event handling, and bridges UI ↔ Data layer.

### Key Responsibilities

#### A. Document Management
```python
self.document_count = 0  # Track number of open documents
self.canvas_managers = {}  # {drawing_area: ModelCanvasManager}
self.zoom_palettes = {}  # {drawing_area: PredefinedZoom}
self.document_filenames = {}  # {drawing_area: filename_without_extension}
```

- **Multi-document support**: Each tab has its own DrawingArea + ModelCanvasManager
- **Editable tab labels**: Shows `[filename.shy]` format with in-place editing
- **Tab styling**: Active tab highlighted with CSS classes

#### B. Event Handling (GTK3)
**Mouse Events:**
```python
# GTK3 signal connections (not EventControllers)
drawing_area.connect('button-press-event', self._on_button_press, manager)
drawing_area.connect('button-release-event', self._on_button_release, manager)
drawing_area.connect('motion-notify-event', self._on_motion_notify, manager)
drawing_area.connect('scroll-event', self._on_scroll_event, manager)
drawing_area.connect('key-press-event', self._on_key_press_event, manager)
```

**Event Types:**
- **Left drag**: (Future) Selection/drawing
- **Right drag**: Pan canvas (or Ctrl+Left drag)
- **Middle drag**: Pan canvas
- **Scroll**: Zoom at pointer position
- **Right-click (no drag)**: Show context menu
- **Escape**: Dismiss context menu

**Drag State Tracking:**
```python
self._drag_state[drawing_area] = {
    'active': False,    # Is button pressed
    'button': 0,        # Which button (1=left, 2=middle, 3=right)
    'start_x': 0,       # Drag start X
    'start_y': 0,       # Drag start Y
    'is_panning': False # Did drag exceed threshold (5px)
}
```

#### C. Context Menu
**Implementation**: Simple GTK Window with ListBox (not Popover - WSL compatibility)
```python
menu_window = Gtk.Window()
menu_window.set_decorated(False)  # No title bar
listbox = Gtk.ListBox()           # Menu items

Items:
- Clear Canvas (TODO: clear all objects)
- Reset Zoom (set zoom to 100%)
- Center View (reset pan to 0,0)
```

**Dismiss Behavior:**
- Escape key → hide menu
- Left-click on canvas → hide menu
- Menu item selection → hide menu

#### D. Canvas Rendering
```python
def _on_draw(drawing_area, cr, width, height, manager):
    # 1. Update viewport size
    manager.set_viewport_size(width, height)
    
    # 2. Clear background (white)
    cr.set_source_rgb(1.0, 1.0, 1.0)
    cr.paint()
    
    # 3. Draw grid
    manager.draw_grid(cr)
    
    # 4. TODO: Draw Petri Net objects (Places, Transitions, Arcs)
    
    # 5. Mark clean
    manager.mark_clean()
```

#### E. Zoom Palette Integration
```python
zoom_palette = create_zoom_palette()
overlay_box.pack_start(zoom_widget, False, False, 0)
zoom_palette.set_canvas_manager(manager, drawing_area, parent_window)
```

- **Position**: Bottom-right corner via overlay
- **Features**: Zoom in/out buttons, percentage display, fit/100%/200% presets
- **Integration**: Directly controls ModelCanvasManager zoom

---

## 3. Data Layer: `src/shypn/data/model_canvas_manager.py`

### Purpose
Pure business logic for canvas transformations, no GTK dependencies.

### Core Properties
```python
# Canvas logical size (world coordinates)
canvas_width = 2000
canvas_height = 2000

# Viewport (screen coordinates)
viewport_width = 800
viewport_height = 600

# Transformations
zoom = 1.0        # 1.0 = 100%, range: 0.1 to 10.0
pan_x = 0.0       # World coordinate offset X
pan_y = 0.0       # World coordinate offset Y

# Pointer tracking (for pointer-centered zoom)
pointer_x = 0
pointer_y = 0

# Grid
grid_style = 'line'  # 'line', 'dot', or 'cross'
BASE_GRID_SPACING = 20  # pixels at 100% zoom (~5mm at 96 DPI)
```

### Coordinate Systems

#### Screen Space → World Space
```python
world_x = (screen_x / zoom) + pan_x
world_y = (screen_y / zoom) + pan_y
```

#### World Space → Screen Space
```python
screen_x = (world_x - pan_x) * zoom
screen_y = (world_y - pan_y) * zoom
```

### Zoom Operations
```python
zoom_in(center_x, center_y)   # Zoom in by 1.1×
zoom_out(center_x, center_y)  # Zoom out by 1/1.1×
set_zoom(level, center_x, center_y)  # Set absolute zoom

# Pointer-centered zoom maintains point under cursor
zoom_by_factor(factor, center_x, center_y):
    world_x, world_y = screen_to_world(center_x, center_y)
    new_zoom = zoom * factor
    pan_x = world_x - (center_x / new_zoom)  # Keep world point at same screen pos
    pan_y = world_y - (center_y / new_zoom)
```

### Pan Operations
```python
pan(dx, dy)          # Pan by screen pixels
pan_to(world_x, world_y)  # Center on world coordinate
pan_relative(dx, dy)  # Pan incrementally (for drag updates)
```

### Grid System

#### Adaptive Grid Spacing
```python
GRID_SUBDIVISION_LEVELS = [1, 2, 5, 10]

get_grid_spacing():
    for level in [1, 2, 5, 10]:
        spacing = BASE_GRID_SPACING * level
        screen_spacing = spacing * zoom
        if screen_spacing >= 10:  # Min 10px on screen
            return spacing
```

**Logic**: As you zoom out, grid spacing increases (10, 20, 50, 100, 200...) to prevent clutter.

#### Grid Styles
1. **Line** (default): Continuous horizontal/vertical lines
2. **Dot**: Small circles at intersections
3. **Cross**: Small + marks at intersections

```python
draw_grid(cr):
    grid_spacing = get_grid_spacing()
    min_x, min_y, max_x, max_y = get_visible_bounds()
    
    if grid_style == 'line':
        # Draw vertical and horizontal lines
    elif grid_style == 'dot':
        # Draw circles at intersections
    elif grid_style == 'cross':
        # Draw + marks at intersections
```

### Document Metadata
```python
filename = "default"       # Base name without .shy
modified = False           # Dirty flag
created_at = datetime.now()
modified_at = None         # Updated on mark_modified()
```

---

## Architecture Patterns

### 1. MVC Separation
- **Model** (Data): `ModelCanvasManager` - pure Python, testable
- **View** (UI): `model_canvas.ui` - declarative GTK3 XML
- **Controller** (Loader): `ModelCanvasLoader` - glue layer

### 2. Multi-Document Design
- **Notebook widget**: Tabbed interface
- **One manager per tab**: Each DrawingArea has its own ModelCanvasManager
- **Independent state**: Zoom, pan, grid style per document

### 3. Event Flow
```
User Action (mouse/keyboard)
    ↓
GTK3 Signal (button-press-event, scroll-event, etc.)
    ↓
ModelCanvasLoader Handler (_on_button_press, _on_scroll_event)
    ↓
ModelCanvasManager Method (pan, zoom_in, set_pointer_position)
    ↓
drawing_area.queue_draw()
    ↓
_on_draw callback
    ↓
ModelCanvasManager.draw_grid(cr)
    ↓
Cairo rendering to screen
```

### 4. GTK3 Compatibility
**Conversion from GTK4:**
- `EventController` → direct signal connections (`connect()`)
- `load_from_string()` → `load_from_data(bytes)`
- `append()` → `pack_start()` / `add()`
- `set_child()` → `add()`
- `get_style_context()` for CSS classes

---

## Key Features

### ✅ Implemented
1. **Multi-document tabs** with editable filenames
2. **Zoom**: Scroll wheel, pointer-centered, 0.1× to 10×
3. **Pan**: Right-drag, middle-drag, Ctrl+left-drag
4. **Adaptive grid**: 3 styles (line/dot/cross), auto-spacing
5. **Context menu**: Clear/Reset Zoom/Center View
6. **Zoom palette**: Floating overlay with controls
7. **Coordinate transforms**: Screen ↔ World

### 🚧 TODO (Future Extensions)
1. **Petri Net objects**: Place (circle), Transition (rectangle), Arc (arrow)
2. **Drawing tools**: Select, draw, move, delete
3. **Object selection**: Highlight, properties panel
4. **Undo/Redo**: Command pattern
5. **File I/O**: Save/load .shy files
6. **Snapping**: Grid snapping for precision
7. **Layers**: Foreground/background elements

---

## Testing Considerations

### Unit Tests (ModelCanvasManager)
```python
# Pure Python, no GTK
test_coordinate_transforms()
test_zoom_operations()
test_pan_operations()
test_grid_spacing()
```

### Integration Tests (ModelCanvasLoader)
```python
# Requires GTK3
test_document_creation()
test_event_handling()
test_zoom_palette_integration()
```

---

## Performance Notes

1. **Grid rendering**: Only draws visible region (get_visible_bounds)
2. **Adaptive spacing**: Prevents excessive grid lines
3. **Dirty flag**: `_needs_redraw` optimization (not fully utilized yet)
4. **Cairo drawing**: Efficient vector graphics

---

## Related Files
- `ui/palettes/zoom.ui` - Zoom control palette UI
- `src/shypn/helpers/predefined_zoom.py` - Zoom palette controller
- `src/shypn.py` - Main app integrates canvas into workspace

---

## Summary
The model canvas is a well-architected, multi-document drawing surface with clean layer separation. The GTK3 conversion is complete with working zoom, pan, grid, and context menu. Ready for Petri Net object implementation.
