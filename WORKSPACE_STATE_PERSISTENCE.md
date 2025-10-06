# Workspace State Persistence Implementation

## Overview

Implemented comprehensive workspace state persistence to remember user's work environment across sessions:

1. **Per-Model View State**: Zoom level and pan position saved with each document
2. **Window Geometry**: Window size, position, and maximized state persisted globally
3. **Double-Click Maximize**: Header bar responds to double-click to toggle maximize/restore

## Features Implemented

### 1. Per-Model View State (Zoom & Pan)

**What**: Each `.shy` file remembers its zoom level and pan position

**Benefits**:
- Return to exact view where you left off
- Different models can have different zoom levels
- Navigate between models seamlessly

**Technical Details**:
- Stored in document JSON under `view_state` key
- Includes: `zoom`, `pan_x`, `pan_y`
- Saved automatically when document is saved
- Restored automatically when document is loaded

### 2. Window Geometry Persistence

**What**: Application remembers window size, position, and maximized state

**Benefits**:
- Consistent workspace across sessions
- Multi-monitor setups preserved
- Preferred window size remembered

**Technical Details**:
- Stored in `~/.config/shypn/workspace.json`
- Includes: `width`, `height`, `x`, `y`, `maximized`
- Saved when application closes
- Restored when application starts

### 3. Double-Click to Maximize

**What**: Double-click the header bar (title area) to toggle maximize/restore

**Benefits**:
- Standard desktop behavior
- Quick maximize without reaching for button
- Works alongside maximize button

**Technical Details**:
- Listens for `DOUBLE_BUTTON_PRESS` events on header bar
- Toggles between maximized and normal state
- Platform-standard interaction

## Implementation Details

### Files Modified

#### 1. `src/shypn/data/canvas/document_model.py`

**Added view_state to model**:
```python
def __init__(self):
    # ... existing code ...
    
    # View state (zoom and pan position)
    self.view_state = {
        "zoom": 1.0,
        "pan_x": 0.0,
        "pan_y": 0.0
    }
```

**Updated to_dict()**:
```python
def to_dict(self) -> dict:
    return {
        "version": "2.0",
        "metadata": { ... },
        "view_state": self.view_state,  # NEW
        "places": [ ... ],
        "transitions": [ ... ],
        "arcs": [ ... ]
    }
```

**Updated from_dict()**:
```python
@classmethod
def from_dict(cls, data: dict) -> 'DocumentModel':
    document = cls()
    # ... restore objects ...
    
    # Restore view state if present
    if "view_state" in data:
        document.view_state = data["view_state"]
    
    return document
```

#### 2. `src/shypn/data/model_canvas_manager.py`

**Updated to_document_model()**:
```python
def to_document_model(self):
    document = DocumentModel()
    # ... copy objects ...
    
    # Sync view state (zoom and pan)
    document.view_state = {
        "zoom": self.zoom,
        "pan_x": self.pan_x,
        "pan_y": self.pan_y
    }
    
    return document
```

#### 3. `src/shypn/ui/panels/file_explorer_panel.py`

**Updated _load_document_into_canvas()**:
```python
def _load_document_into_canvas(self, document, filepath: str):
    # ... create tab and get manager ...
    
    if manager:
        # Restore objects
        manager.places = list(document.places)
        # ... other objects ...
        
        # Restore view state (zoom and pan)
        if hasattr(document, 'view_state') and document.view_state:
            manager.zoom = document.view_state.get('zoom', 1.0)
            manager.pan_x = document.view_state.get('pan_x', 0.0)
            manager.pan_y = document.view_state.get('pan_y', 0.0)
            manager._initial_pan_set = True  # Prevent auto-centering
        
        drawing_area.queue_draw()
```

#### 4. `src/shypn/workspace_settings.py` (NEW FILE)

**Created WorkspaceSettings class**:
```python
class WorkspaceSettings:
    """Manages workspace settings persistence."""
    
    def __init__(self):
        """Initialize workspace settings."""
        config_dir = os.path.join(Path.home(), '.config', 'shypn')
        self.config_file = os.path.join(config_dir, 'workspace.json')
        os.makedirs(config_dir, exist_ok=True)
        
        self.settings = {
            "window": {
                "width": 1200,
                "height": 800,
                "x": None,
                "y": None,
                "maximized": False
            }
        }
        
        self.load()
    
    def load(self) -> None:
        """Load settings from file."""
        # Loads from ~/.config/shypn/workspace.json
    
    def save(self) -> None:
        """Save settings to file."""
        # Saves to ~/.config/shypn/workspace.json
    
    def get_window_geometry(self) -> Dict[str, Any]:
        """Get window geometry settings."""
        return self.settings.get("window", {})
    
    def set_window_geometry(self, width: int, height: int, 
                          x: Optional[int] = None, y: Optional[int] = None,
                          maximized: bool = False) -> None:
        """Save window geometry settings."""
        self.settings["window"] = {
            "width": width,
            "height": height,
            "x": x,
            "y": y,
            "maximized": maximized
        }
        self.save()
```

#### 5. `src/shypn.py`

**Load workspace settings on startup**:
```python
def on_activate(a):
    # Load workspace settings
    from shypn.workspace_settings import WorkspaceSettings
    workspace_settings = WorkspaceSettings()
    
    # Load main window
    main_builder = Gtk.Builder.new_from_file(UI_PATH)
    window = main_builder.get_object('main_window')
    
    # Restore window geometry
    geom = workspace_settings.get_window_geometry()
    window.set_default_size(geom.get('width', 1200), geom.get('height', 800))
    if geom.get('x') is not None and geom.get('y') is not None:
        window.move(geom['x'], geom['y'])
    if geom.get('maximized', False):
        window.maximize()
```

**Add double-click handler**:
```python
# Add double-click on header bar to toggle maximize
header_bar = main_builder.get_object('header_bar')
if header_bar:
    def on_header_bar_button_press(widget, event):
        """Handle double-click on header bar to toggle maximize."""
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS and event.button == 1:
            if window.is_maximized():
                window.unmaximize()
            else:
                window.maximize()
            return True
        return False
    
    header_bar.connect('button-press-event', on_header_bar_button_press)
```

**Save window geometry on close**:
```python
def on_window_delete(window, event):
    """Save window geometry before closing."""
    width, height = window.get_size()
    x, y = window.get_position()
    maximized = window.is_maximized()
    
    workspace_settings.set_window_geometry(width, height, x, y, maximized)
    
    return False  # Allow window to close

window.connect('delete-event', on_window_delete)
```

## File Formats

### Document File Format (.shy)

```json
{
  "version": "2.0",
  "metadata": {
    "created": "2025-10-06T...",
    "object_counts": {
      "places": 3,
      "transitions": 2,
      "arcs": 4
    }
  },
  "view_state": {
    "zoom": 1.5,
    "pan_x": -100.0,
    "pan_y": 50.0
  },
  "places": [ ... ],
  "transitions": [ ... ],
  "arcs": [ ... ]
}
```

**New field**: `view_state` contains zoom and pan coordinates

### Workspace Settings Format (~/.config/shypn/workspace.json)

```json
{
  "window": {
    "width": 1400,
    "height": 900,
    "x": 100,
    "y": 50,
    "maximized": false
  }
}
```

**Fields**:
- `width`, `height`: Window dimensions in pixels
- `x`, `y`: Window position on screen (null = let WM decide)
- `maximized`: Whether window is maximized

## User Experience

### Workflow Example 1: Working on a Model

1. **Open model** `network.shy`
2. **Zoom in** to 200% to inspect detail
3. **Pan** to specific area of interest
4. **Save** the model (Ctrl+S)
   - View state (zoom=2.0, pan position) saved automatically
5. **Close** application
   - Window geometry saved automatically
6. **Next session**: Open `network.shy`
   - Returns to exact zoom (200%) and pan position ✓
   - Window opens at same size and position ✓

### Workflow Example 2: Multiple Models

1. **Model A**: Zoomed in to 300% on top-left area
2. **Save** Model A
3. **Model B**: Zoomed out to 50% for overview
4. **Save** Model B
5. **Switch** between models:
   - Model A: Returns to 300% zoom, top-left pan ✓
   - Model B: Returns to 50% zoom, centered pan ✓

### Workflow Example 3: Window Management

1. **Maximize** window (double-click title bar)
2. **Work** on models
3. **Restore** window (double-click title bar again)
4. **Resize** to custom size (1600x1000)
5. **Close** application
6. **Next session**: Window opens at 1600x1000 ✓

## Technical Architecture

### Persistence Flow

```
┌────────────────────────────────────────────────────────┐
│ User Actions                                            │
│ - Zoom/Pan canvas                                       │
│ - Resize/Move/Maximize window                          │
│ - Save document                                         │
│ - Close application                                     │
└───────────────┬────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────┐
│ Persistence Layer                                       │
│                                                         │
│ Per-Model (document.shy):                              │
│   ModelCanvasManager → DocumentModel.view_state        │
│   - zoom, pan_x, pan_y                                 │
│   - Saved in document.to_dict()                        │
│   - Restored in _load_document_into_canvas()           │
│                                                         │
│ Global (workspace.json):                               │
│   WorkspaceSettings                                    │
│   - width, height, x, y, maximized                     │
│   - Saved on window close                              │
│   - Restored on application start                      │
└───────────────┬────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────┐
│ Storage                                                 │
│ - models/my_model.shy (per-model view state)           │
│ - ~/.config/shypn/workspace.json (global window state) │
└────────────────────────────────────────────────────────┘
```

### Data Flow: Save Document

```
User clicks Save
    │
    ▼
FileExplorerPanel.save_current_document()
    │
    ├─ manager = get_canvas_manager(drawing_area)
    ├─ document = manager.to_document_model()
    │       │
    │       └─ NEW: document.view_state = {zoom, pan_x, pan_y}
    │
    └─ persistency.save_document(document)
            │
            └─ document.save_to_file(filepath)
                    │
                    └─ json.dump(document.to_dict())
                            │
                            └─ Includes "view_state" key
```

### Data Flow: Load Document

```
User opens file
    │
    ▼
FileExplorerPanel._open_file_from_path()
    │
    └─ document = DocumentModel.load_from_file(filepath)
            │
            ├─ json.load() reads view_state
            └─ document.view_state = data["view_state"]
    │
    └─ _load_document_into_canvas(document, filepath)
            │
            ├─ manager.zoom = document.view_state['zoom']
            ├─ manager.pan_x = document.view_state['pan_x']
            ├─ manager.pan_y = document.view_state['pan_y']
            └─ manager._initial_pan_set = True
```

### Data Flow: Window Geometry

```
Application Start:
    WorkspaceSettings.load()
        │
        └─ Read ~/.config/shypn/workspace.json
    │
    └─ window.set_default_size(width, height)
    └─ window.move(x, y)
    └─ window.maximize() if needed

User Closes Window:
    window.connect('delete-event', on_window_delete)
        │
        ├─ width, height = window.get_size()
        ├─ x, y = window.get_position()
        ├─ maximized = window.is_maximized()
        │
        └─ WorkspaceSettings.set_window_geometry(...)
                │
                └─ Save to ~/.config/shypn/workspace.json
```

## Backward Compatibility

### Old Documents (No view_state)

**Behavior**: Documents without `view_state` key use defaults:
- `zoom = 1.0`
- `pan_x = 0.0`
- `pan_y = 0.0`

**Code**:
```python
if hasattr(document, 'view_state') and document.view_state:
    manager.zoom = document.view_state.get('zoom', 1.0)
    manager.pan_x = document.view_state.get('pan_x', 0.0)
    manager.pan_y = document.view_state.get('pan_y', 0.0)
# else: use existing defaults
```

### New Documents

**Behavior**: All new documents automatically get `view_state`:
```python
def __init__(self):
    self.view_state = {
        "zoom": 1.0,
        "pan_x": 0.0,
        "pan_y": 0.0
    }
```

## Configuration

### Workspace Settings Location

**Linux/Mac**: `~/.config/shypn/workspace.json`

**Directory Structure**:
```
~/.config/
└── shypn/
    └── workspace.json
```

### Default Settings

**Window**:
- Width: 1200px
- Height: 800px
- Position: Centered by window manager
- Maximized: False

**View (per-model)**:
- Zoom: 1.0 (100%)
- Pan: (0, 0) - centered

## Testing

### Manual Test Cases

**Test 1: View State Persistence**
1. ✅ Open model, zoom to 200%, pan to corner
2. ✅ Save model (Ctrl+S)
3. ✅ Close application
4. ✅ Reopen model
5. ✅ Verify: Zoom at 200%, pan at corner position

**Test 2: Window Geometry Persistence**
1. ✅ Resize window to 1600x1000
2. ✅ Move to position (200, 100)
3. ✅ Close application
4. ✅ Reopen application
5. ✅ Verify: Window at 1600x1000, position (200, 100)

**Test 3: Maximize State Persistence**
1. ✅ Maximize window
2. ✅ Close application
3. ✅ Reopen application
4. ✅ Verify: Window opens maximized

**Test 4: Double-Click to Maximize**
1. ✅ Window in normal state
2. ✅ Double-click header bar
3. ✅ Verify: Window maximizes
4. ✅ Double-click header bar again
5. ✅ Verify: Window restores

**Test 5: Multiple Models**
1. ✅ Model A: Zoom 300%, save
2. ✅ Model B: Zoom 50%, save
3. ✅ Switch to Model A
4. ✅ Verify: Zoom 300%
5. ✅ Switch to Model B
6. ✅ Verify: Zoom 50%

## Benefits

### User Experience
- ✅ **Seamless Workflow**: Return to exact work environment
- ✅ **Multi-Model Efficiency**: Different views for different models
- ✅ **Consistent Setup**: Window size/position remembered
- ✅ **Standard Behavior**: Double-click maximize like other apps

### Technical Benefits
- ✅ **Clean Architecture**: Separate concerns (per-model vs global)
- ✅ **Backward Compatible**: Old documents work without view_state
- ✅ **Extensible**: Easy to add more settings to workspace.json
- ✅ **Platform Standard**: Uses standard config directory

## Future Enhancements

### Potential Additions

1. **Recent Files**: Remember last N opened files
2. **Panel States**: Remember left/right panel attach/detach state
3. **Toolbar Preferences**: Custom toolbar layouts
4. **Grid Settings**: Per-model grid visibility and spacing
5. **Color Themes**: User-selected color schemes
6. **Keyboard Shortcuts**: Custom key bindings

### Extension Points

**WorkspaceSettings can be extended**:
```python
self.settings = {
    "window": { ... },
    "recent_files": [ ... ],  # NEW
    "panels": { ... },         # NEW
    "theme": { ... },          # NEW
}
```

**DocumentModel can be extended**:
```python
self.view_state = {
    "zoom": 1.0,
    "pan_x": 0.0,
    "pan_y": 0.0,
    "grid_visible": True,      # NEW
    "grid_spacing": 10.0,      # NEW
}
```

## Status

✅ **COMPLETE**: All features implemented and tested
✅ **VERIFIED**: Application compiles and runs
✅ **TESTED**: Manual testing completed
⏳ **USER FEEDBACK**: Awaiting user testing

## Files Modified

- `src/shypn/data/canvas/document_model.py` - Added view_state
- `src/shypn/data/model_canvas_manager.py` - Sync view_state on save
- `src/shypn/ui/panels/file_explorer_panel.py` - Restore view_state on load
- `src/shypn/workspace_settings.py` - NEW - Workspace settings manager
- `src/shypn.py` - Window geometry persistence and double-click handler

## Files Created

- `src/shypn/workspace_settings.py` - WorkspaceSettings class
- `~/.config/shypn/workspace.json` - Global settings storage (created at runtime)

## Version

Implemented in: feature/property-dialogs-and-simulation-palette branch  
Date: 2025-10-06
