# UI Helpers

This directory contains UI component loaders and controllers that bridge the GTK4 interface layer with the data/business logic layer.

## Current Modules

### `left_panel_loader.py`
**Left Panel (File Operations) Loader**

Manages the attachable/detachable File Operations panel:
- Load UI from `ui/panels/left_panel.ui`
- Handle attach/detach behavior (window ↔ inline)
- Position panel at extreme left when attached
- Maintain panel state across attach/detach cycles
- Float button for panel detachment
- Callbacks for attach/float events

**Key Class:** `LeftPanelLoader`

### `right_panel_loader.py`
**Right Panel (Dynamic Analyses) Loader**

Manages the attachable/detachable Dynamic Analyses panel:
- Load UI from `ui/panels/right_panel.ui`
- Handle attach/detach behavior (window ↔ inline)
- Position panel at extreme right when attached
- Maintain panel state across attach/detach cycles
- Float button for panel detachment
- Callbacks for attach/float events

**Key Class:** `RightPanelLoader`

### `model_canvas_loader.py`
**Multi-Document Canvas Loader**

Manages the main canvas area with multi-document support:
- Load UI from `ui/canvas/model_canvas.ui`
- GtkNotebook-based tab management
- Per-document canvas state (via ModelCanvasManager)
- Editable tab labels with `.shy` extension
- New document creation with validation
- Document filename tracking
- Active tab visual feedback (relief effect)
- Canvas click handlers for revealer auto-hide
- Integration with zoom palettes per document

**Key Class:** `ModelCanvasLoader`

**Tab Label Features:**
- Right-aligned entry fields
- Dynamic white/transparent backgrounds (default vs. custom names)
- Static `.shy` extension label
- Active tab indication with shadow
- Auto-focus text selection

### `predefined_zoom.py`
**Zoom Control Palette with Revealer**

Floating zoom control overlay for canvas:
- Load UI from `ui/palettes/zoom.ui`
- GtkRevealer-based inline expansion (stable under WSL)
- Zoom in/out buttons with pointer-centered zoom
- Display button toggles predefined zoom levels
- Predefined zooms: 25%, 50%, 75%, 100%, 150%, 200%, 400%
- Fit-to-window option
- Font metric-based sizing (1.3× 'W' character height)
- CSS styling with gradients and shadows
- Auto-hide on zoom selection or canvas click

**Key Class:** `PredefinedZoom`

**Factory Function:** `create_zoom_palette()`

### `example_helper.py`
Example helper utilities and patterns for development reference.

## Architecture Pattern

All loaders follow a consistent pattern:

```python
class ComponentLoader:
    def __init__(self, ui_path=None):
        """Initialize with optional UI path (auto-detected if None)"""
        
    def load(self):
        """Load UI and return the main widget"""
        
    # Component-specific methods
```

**Factory Functions:**
```python
def create_component(ui_path=None):
    """Convenience function to create and load component"""
    loader = ComponentLoader(ui_path)
    widget = loader.load()
    return widget, loader
```

## UI Path Resolution

All loaders automatically resolve UI file paths relative to repository root:

```python
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
ui_path = os.path.join(repo_root, 'ui', 'subdirectory', 'file.ui')
```

This works because loaders are in `src/shypn/helpers/` and UI files are in `ui/`.

## Integration with Data Layer

Helpers create and manage data layer objects:

```python
# In model_canvas_loader.py
from shypn.data.model_canvas_manager import ModelCanvasManager

canvas_manager = ModelCanvasManager(
    canvas_width=2000,
    canvas_height=2000,
    filename="default"
)
```

Loaders handle:
- **UI events** → **Data layer method calls**
- **Data layer state changes** → **UI updates**

## Import Patterns

```python
# From main application
from shypn.helpers.left_panel_loader import create_left_panel
from shypn.helpers.right_panel_loader import create_right_panel
from shypn.helpers.model_canvas_loader import create_model_canvas

# From other helpers
from shypn.helpers.predefined_zoom import create_zoom_palette
```

## Recent Changes (October 2025)

All UI loaders were moved from `src/shypn/` root to `src/shypn/helpers/` to:
1. Separate UI layer from data layer
2. Improve code organization and discoverability
3. Clarify architectural boundaries
4. Group related UI components together

UI path calculations were updated to account for the new directory depth.
