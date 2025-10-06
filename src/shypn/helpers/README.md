# UI Helpers

This directory contains UI component loaders and controllers that bridge the GTK4 interface layer with the data/business logic layer.

## Panel Loaders

### `left_panel_loader.py`
**Left Panel (File Operations) Loader**

Manages the attachable/detachable File Operations panel:
- Load UI from `ui/panels/left_panel.ui`
- Handle attach/detach behavior (window ↔ inline)
- Position panel at extreme left when attached
- Maintain panel state across attach/detach cycles
- Float button for panel detachment
- Callbacks for attach/float events
- Integration with file explorer

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
- Integration with analysis modules

**Key Class:** `RightPanelLoader`

## Canvas and Document Loaders

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
- View state persistence on tab switches

**Key Class:** `ModelCanvasLoader`

**Tab Label Features:**
- Right-aligned entry fields
- Dynamic white/transparent backgrounds (default vs. custom names)
- Static `.shy` extension label
- Active tab indication with shadow
- Auto-focus text selection

## Tool Palettes

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
- **View state persistence**: Saves pan/zoom on all operations

**Key Class:** `PredefinedZoom`
**Factory Function:** `create_zoom_palette()`

### `edit_palette_loader.py`
**Edit Tools Palette Loader**

Loads and manages the edit tools palette:
- Tool selection for creating/editing Petri Net objects
- Place creation tool
- Transition creation tools (immediate, timed, stochastic, continuous)
- Arc creation tools (normal, inhibitor, curved)
- Selection and pan tools
- Tool state management

### `edit_tools_loader.py`
**Edit Toolbar Loader**

Loads the main edit toolbar with common editing operations:
- Cut, copy, paste operations
- Undo/redo operations
- Alignment tools
- Distribution tools
- Object deletion

### `simulate_palette_loader.py`
**Simulation Palette Loader**

Loads and manages the simulation control palette:
- Start/stop simulation
- Step through simulation
- Reset to initial marking
- Simulation speed control
- Simulation state display

### `simulate_tools_palette_loader.py`
**Simulation Tools Palette Loader**

Additional simulation tools and controls:
- Token game visualization
- Transition firing controls
- Marking exploration
- Simulation statistics

## Properties Dialog Loaders

### `place_prop_dialog_loader.py`
**Place Properties Dialog**

Dialog for editing place properties:
- Load UI from properties dialog template
- Edit place name and label
- Set tokens (current marking)
- Set initial marking (simulation baseline)
- Set capacity (optional)
- Color selection
- Apply/Cancel buttons
- **Token persistence**: Updates both `tokens` and `initial_marking` when user edits

**Key Feature:** When user manually sets tokens, both current marking and initial marking are updated, making the new value the baseline for simulation resets.

### `transition_prop_dialog_loader.py`
**Transition Properties Dialog**

Dialog for editing transition properties:
- Edit transition name and label
- Set transition type (immediate, timed, stochastic, continuous)
- Set priority (for immediate transitions)
- Set delay (for timed transitions)
- Set rate function (for stochastic/continuous transitions)
- Color selection
- Apply/Cancel buttons

### `arc_prop_dialog_loader.py`
**Arc Properties Dialog**

Dialog for editing arc properties:
- Edit arc weight/multiplicity
- Set arc type (normal, inhibitor, test)
- Configure curved arcs (control points)
- Color and style selection
- Apply/Cancel buttons

## UI Widgets

### `color_picker.py`
**Color Picker Widget**

Reusable color picker component:
- GTK4 ColorButton integration
- RGBA color selection
- Color preview
- Recent colors palette
- Used by properties dialogs for object coloring

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
