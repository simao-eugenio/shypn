# Mode Palette Implementation

## Overview
Implemented a floating mode palette with Edit/Sim buttons that acts as a mode switcher for the application. This palette is positioned at the bottom center of the canvas and controls which set of palettes (Edit or Simulation) are visible.

## Files Created

### 1. UI File: `ui/palettes/mode/mode_palette.ui`
- Defines a GtkBox container with two buttons: Edit and Sim
- Positioned at bottom center using halign=center, valign=end
- Margin bottom=24 for spacing from canvas edge
- Buttons styled with custom CSS classes: mode-button, edit-button, sim-button

### 2. Loader: `src/ui/palettes/mode/mode_palette_loader.py`
- `ModePaletteLoader` class (extends GObject.GObject)
- Emits `mode-changed` signal when user switches modes
- Manages button states (active button is insensitive)
- Tracks current mode ('edit' or 'sim')
- Default mode: 'edit'

### 3. Package Init: `src/ui/palettes/mode/__init__.py`
- Exports ModePaletteLoader for clean imports

## Integration with ModelCanvasLoader

### Changes to `src/shypn/helpers/model_canvas_loader.py`

#### 1. Import Section
Added import for ModePaletteLoader:
```python
from ui.palettes.mode.mode_palette_loader import ModePaletteLoader
```

#### 2. Class State
Added mode palette tracking dictionary:
```python
self.mode_palettes = {}  # {drawing_area: ModePaletteLoader}
```

#### 3. Palette Setup (_setup_canvas_manager)
After creating edit and simulation palettes, added mode palette:
```python
# Create and add mode palette (Edit/Sim buttons)
mode_palette = ModePaletteLoader()
mode_widget = mode_palette.get_widget()

if mode_widget:
    overlay_widget.add_overlay(mode_widget)
    self.mode_palettes[drawing_area] = mode_palette
    
    # Connect mode-changed signal
    mode_palette.connect('mode-changed', self._on_mode_changed, 
                        drawing_area, edit_palette, edit_tools_palette,
                        simulate_palette, simulate_tools_palette)
    
    # Initialize: show edit palettes, hide simulation palettes
    self._update_palette_visibility(drawing_area, 'edit', ...)
```

#### 4. Event Handlers
Added two new methods:

**`_on_mode_changed()`**
- Handles mode-changed signal from mode palette
- Delegates to _update_palette_visibility()

**`_update_palette_visibility()`**
- Shows/hides palettes based on current mode
- In 'edit' mode: shows edit palettes, hides simulation palettes
- In 'sim' mode: shows simulation palettes, hides edit palettes
- Respects palette controllers (doesn't force-show tools palettes)

## Architecture

### Mode Switching Flow
1. User clicks Edit or Sim button in mode palette
2. ModePaletteLoader emits 'mode-changed' signal with new mode
3. ModelCanvasLoader receives signal in _on_mode_changed()
4. _update_palette_visibility() called to adjust palette visibility
5. Appropriate palettes shown/hidden based on mode
6. Mode palette buttons update states (active button becomes insensitive)

### Palette Visibility Rules
- **Edit Mode**: 
  - Edit palette ([E] button): visible
  - Edit tools palette: controlled by [E] button
  - Simulation palette ([S] button): hidden
  - Simulation tools palette: hidden
  
- **Simulation Mode**:
  - Edit palette ([E] button): hidden
  - Edit tools palette: hidden
  - Simulation palette ([S] button): visible
  - Simulation tools palette: controlled by [S] button

### Layout
- **Mode Palette**: Bottom center, always visible
- **Edit Palettes**: Left side when in edit mode
- **Simulation Palettes**: Right side when in simulation mode
- **No Overlap**: Only one set of palettes visible at a time

## Benefits
1. **Clean UI**: No palette overlap, clear mode separation
2. **Consistent Behavior**: Each mode has its own dedicated palette set
3. **Intuitive Navigation**: Simple two-button switcher
4. **Extensible**: Easy to add more modes or palette sets in future

## Next Steps
1. Test the implementation in a running application
2. Add CSS styling for mode buttons (active/inactive states)
3. Add keyboard shortcuts for mode switching (e.g., Tab key)
4. Persist mode state across application sessions
5. Add visual feedback for mode transitions (animations/highlights)
