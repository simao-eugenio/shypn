# Zoom Control Palette Implementation

## Overview
A floating zoom control palette has been added to the canvas in the bottom-right corner. The palette provides quick access to zoom operations without using mouse wheel or keyboard shortcuts.

## Features

### Visual Layout
```
[ − ] [ 100% ▼ ] [ + ]
```

- **Zoom Out Button (−)**: Decrease zoom by one step (÷1.1)
- **Zoom Level Display**: Shows current zoom percentage with dropdown menu
- **Zoom In Button (+)**: Increase zoom by one step (×1.1)

### Predefined Zoom Levels
Click the zoom percentage to open a menu with predefined levels:
- 25% (0.25x)
- 50% (0.5x)
- 75% (0.75x)
- 100% (1.0x) - Default
- 150% (1.5x)
- 200% (2.0x)
- 400% (4.0x)
- **Fit to Window** - Auto-adjust to fit canvas

### Zoom Behavior
- **Button Zoom**: Centers zoom at viewport center
- **Menu Selection**: Jumps to exact zoom level, centered at viewport
- **Wheel Zoom**: Centers at mouse pointer (existing behavior)
- **Display Updates**: Automatically reflects current zoom level

## Architecture

### File Structure

**UI Definition**: `ui/palettes/zoom.ui`
- GtkBox container with horizontal layout
- GtkButton widgets for zoom in/out
- GtkMenuButton with Gio.Menu for predefined levels
- Compact styling with flat buttons
- Positioned with `halign="end"`, `valign="end"` for bottom-right placement

**Controller**: `src/shypn/predefined_zoom.py`
- `PredefinedZoom` class manages the palette lifecycle
- Action handlers for menu items (Gio.SimpleActionGroup)
- Integration with ModelCanvasManager for zoom operations
- Updates display when zoom changes externally

**Integration**: `src/shypn/model_canvas_loader.py`
- Modified to support GtkOverlay structure in canvas
- Each canvas page has overlay with zoom palette
- Zoom palette dictionary maps drawing areas to palettes
- Mouse wheel zoom updates palette display

### Canvas Structure

```
GtkNotebook (canvas_notebook)
└─ GtkNotebookPage
   └─ GtkOverlay (canvas_overlay_1)
      ├─ GtkScrolledWindow (main content)
      │  └─ GtkDrawingArea (canvas)
      └─ GtkBox (overlay, type="overlay")
         └─ Zoom Control Widget (added programmatically)
```

## Implementation Details

### Action System
Uses GTK4 action system for menu integration:

```python
# Action for predefined zoom levels
action_set_level = Gio.SimpleAction.new_stateful(
    'set-level',
    GLib.VariantType.new('d'),  # double parameter
    GLib.Variant.new_double(1.0)  # initial state (100%)
)
```

Menu items target the action with zoom level as parameter:
```xml
<item>
  <attribute name="label">200%</attribute>
  <attribute name="action">zoom.set-level</attribute>
  <attribute name="target">2.0</attribute>
</item>
```

### Zoom Operations

**Zoom In/Out Buttons**:
```python
def _on_zoom_in_clicked(self, button):
    center_x = self.canvas_manager.viewport_width / 2
    center_y = self.canvas_manager.viewport_height / 2
    self.canvas_manager.zoom_in(center_x, center_y)
    self._update_zoom_display()
    self.drawing_area.queue_draw()
```

**Predefined Zoom Levels**:
```python
def _on_set_zoom_level(self, action, parameter):
    zoom_level = parameter.get_double()
    center_x = self.canvas_manager.viewport_width / 2
    center_y = self.canvas_manager.viewport_height / 2
    self.canvas_manager.set_zoom(zoom_level, center_x, center_y)
    self._update_zoom_display()
    self.drawing_area.queue_draw()
```

### Display Sync
When zoom changes via mouse wheel, the loader updates the palette:

```python
def _on_scroll(self, controller, dx, dy, manager, drawing_area):
    # ... zoom in/out via manager ...
    
    # Update zoom palette display if available
    if drawing_area in self.zoom_palettes:
        self.zoom_palettes[drawing_area].update_zoom_display()
```

## Usage

### For Users
1. **Zoom In**: Click the `+` button
2. **Zoom Out**: Click the `−` button
3. **Quick Zoom**: Click percentage, select from menu
4. **Mouse Zoom**: Still works with mouse wheel (pointer-centered)

### For Developers

**Create zoom palette**:
```python
from shypn.predefined_zoom import create_zoom_palette

palette = create_zoom_palette()
widget = palette.get_widget()
palette.set_canvas_manager(manager, drawing_area)
```

**Add to overlay**:
```python
overlay_box.append(widget)
```

**Update display after external zoom**:
```python
palette.update_zoom_display()
```

## Styling

The palette uses standard GTK4 CSS classes:
- `.toolbar` - Toolbar appearance
- `.zoom-palette` - Custom class for additional styling
- `.flat` - Flat buttons without borders

Custom CSS can be added in the future to style the palette:
```css
.zoom-palette {
    background-color: rgba(255, 255, 255, 0.9);
    border-radius: 6px;
    padding: 4px;
}
```

## Future Enhancements

Potential improvements:
1. **Keyboard Shortcuts**: 
   - `+` / `=` for zoom in
   - `-` for zoom out
   - `0` for reset to 100%
   
2. **Zoom to Selection**: Add menu item to zoom into selected objects

3. **Custom Zoom**: Allow user to type exact percentage

4. **Zoom History**: Remember last 5 zoom levels, quick navigation

5. **Grid Visibility Toggle**: Add button to show/hide grid

6. **Mini-map**: Small overview of entire canvas with viewport indicator

## Testing

✅ Palette appears in bottom-right corner
✅ Zoom in/out buttons work correctly
✅ Menu shows predefined levels
✅ Selecting menu item sets zoom level
✅ Display updates with mouse wheel zoom
✅ Multiple canvases each have own palette
✅ Palette positioned correctly in overlay
✅ No interference with canvas drawing or pan/zoom

## Files Modified/Created

### Created
- `/home/simao/projetos/shypn/ui/palettes/zoom.ui` - UI definition
- `/home/simao/projetos/shypn/src/shypn/predefined_zoom.py` - Controller class

### Modified
- `/home/simao/projetos/shypn/ui/canvas/model_canvas.ui` - Added GtkOverlay structure
- `/home/simao/projetos/shypn/src/shypn/model_canvas_loader.py` - Integrated zoom palette
  - Added zoom_palettes dictionary
  - Modified _setup_canvas_manager() to accept overlay_box
  - Updated load() to extract overlay structure
  - Updated _on_scroll() to sync palette display
  - Added import for create_zoom_palette

## Summary

The zoom control palette provides an intuitive, always-visible interface for zoom operations. It complements existing mouse wheel zoom by offering discrete, predictable zoom levels and visual feedback of the current zoom state. The implementation uses GTK4's overlay system for non-intrusive placement and the action system for menu integration.
