# Model Canvas Controls

## Refinements Implemented

### 1. Startup Grid at 100% Zoom
- **Issue**: Grid appeared expanded on startup
- **Solution**: Added automatic viewport centering on first draw
  - Canvas now centers at world coordinate (0, 0) on startup
  - Grid displays at true 100% zoom (20px = ~5mm at 96 DPI)

### 2. Relative Pan Behavior
- **Issue**: Pan was recalculating from pointer center on each update, causing "waving" effect
- **Solution**: Changed to incremental delta tracking
  - Pan now moves relative to drag start position
  - Smooth, predictable panning behavior
  - Works correctly with all three pan methods (right-click, middle-click, ctrl+left)

### 3. Alternative Grid Patterns
Three grid styles available:
- **Line Grid** (default): Standard grid lines
- **Dot Grid**: Small circles at intersections (cleaner look)
- **Cross Grid**: Small crosses at intersections (combines both axes)

## Current Controls

### Zoom
- **Mouse Wheel**: Zoom in/out (pointer-centered)
- **Zoom Level**: Always starts at 100% (1.0)
- **Range**: 10% to 1000%

### Pan
- **Right-Click + Drag**: Pan viewport
- **Middle-Click + Drag**: Pan viewport  
- **Ctrl + Left-Click + Drag**: Pan viewport

### Grid
- **Grid Spacing**: 20 pixels at 100% zoom (~5mm on 96 DPI displays)
- **Adaptive**: Grid subdivides/multiplies based on zoom level
- **Styles**: Line (default), Dot, Cross

## Testing Grid Styles

To cycle through grid styles programmatically, you can use the Python console:

```python
# In the application, access the model canvas loader
# and cycle through grid styles:
canvas_loader.cycle_grid_style()  # line -> dot -> cross -> line
```

Or set a specific style:

```python
canvas_loader.set_grid_style('dot')   # Dot grid
canvas_loader.set_grid_style('cross') # Cross grid
canvas_loader.set_grid_style('line')  # Line grid (default)
```

## Technical Details

### Coordinate Systems
- **Screen Space**: Pixel coordinates in viewport
- **World Space**: Model coordinates (independent of zoom/pan)
- **Transformations**: Bidirectional screen ↔ world conversion

### Pan Implementation
- Tracks last offset for each drawing area
- Calculates incremental delta: `delta = current_offset - last_offset`
- Applies delta to pan: `manager.pan(-delta_x, -delta_y)`
- No more "waving" or recalculation artifacts

### Viewport Centering
- On first draw, calculates pan to center (0, 0) world coordinate
- Formula: `pan_x = -(viewport_width / 2) / zoom`
- Only applies once per canvas instance
- Subsequent pans are relative to user interaction

## Next Steps

Future enhancements could include:
- Keyboard shortcut to cycle grid styles (e.g., 'G' key)
- Grid visibility toggle
- Grid color/opacity customization
- Snap-to-grid for drawing operations
