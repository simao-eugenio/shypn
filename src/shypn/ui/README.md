# UI State Management

This directory manages UI-specific state that doesn't belong in the data layer, such as view preferences, window positions, and user interface settings.

## Purpose

The `ui/` directory is separate from `helpers/` to maintain a clear distinction:
- **`helpers/`**: UI component loaders and GTK4 controllers (bridges UI ↔ data)
- **`ui/`**: UI state management and preferences (UI-specific state)

## Current Structure

### `panels/` Subdirectory
Contains UI panel-specific state and configuration:
- Panel visibility states
- Panel positions and sizes
- Panel attachment/detachment state
- Panel preferences

## UI State Categories

### View State
Managed primarily by `data/model_canvas_manager.py`:
- Canvas pan position (x, y offsets)
- Zoom level (10% to 1000%)
- Grid visibility and style
- Stored in `.shy.view` file alongside document

### Window State
Application window configuration:
- Main window size and position
- Window maximization state
- Multi-monitor configuration
- Restored on application restart

### Panel State
Panel configuration and layout:
- Left panel (File Operations): attached/detached
- Right panel (Dynamic Analyses): attached/detached
- Panel sizes when detached
- Panel visibility toggles

### Tool State
Active tool and palette state:
- Currently selected tool (select, place, transition, arc)
- Tool palette visibility (edit, simulate, zoom)
- Tool-specific settings
- Recent tool selections

### Preferences
User preferences and settings:
- Theme selection (light/dark)
- Grid style (line/dot/cross)
- Default zoom level
- Auto-save interval
- Recent files limit
- Color schemes

## State Persistence

### Session State
Temporary state during application runtime:
- Active document tabs
- Undo/redo stacks per document
- Clipboard contents
- Current tool selection

### Persistent State
State saved between sessions:
- Window size and position
- Panel layout preferences
- Recent files list
- User preferences
- Stored in: `~/.config/shypn/ui_state.json`

### Document-Specific State
State tied to specific documents:
- View state (pan, zoom)
- Selection state (not persisted)
- Stored in: `.shy.view` alongside `.shy` file

## State Storage Format

### UI State File
`~/.config/shypn/ui_state.json`:
```json
{
  "window": {
    "width": 1200,
    "height": 800,
    "x": 100,
    "y": 100,
    "maximized": false
  },
  "panels": {
    "left_panel": {
      "attached": true,
      "width": 250,
      "visible": true
    },
    "right_panel": {
      "attached": true,
      "width": 300,
      "visible": true
    }
  },
  "preferences": {
    "theme": "light",
    "grid_style": "dot",
    "auto_save_interval": 300,
    "recent_files_limit": 10
  },
  "tools": {
    "last_selected": "select",
    "edit_palette_visible": true,
    "zoom_palette_visible": true
  }
}
```

### View State File
`.shy.view` (per document):
```json
{
  "pan_x": 100.0,
  "pan_y": 50.0,
  "zoom": 1.5,
  "grid_visible": true,
  "grid_style": "dot"
}
```

## State Management Classes

### WindowStateManager
Manages main window state:
```python
class WindowStateManager:
    def save_window_state(window)
    def restore_window_state(window)
    def on_window_configure(event)  # Auto-save on resize/move
```

### PanelStateManager
Manages panel layout state:
```python
class PanelStateManager:
    def save_panel_state(panel_id, state)
    def restore_panel_state(panel_id) -> state
    def on_panel_attach(panel_id)
    def on_panel_detach(panel_id)
```

### PreferencesManager
Manages user preferences:
```python
class PreferencesManager:
    def get_preference(key, default=None)
    def set_preference(key, value)
    def save_preferences()
    def load_preferences()
```

## State Synchronization

### Application Startup
```python
1. Load UI state from config file
2. Restore window size and position
3. Restore panel layout
4. Load user preferences
5. Apply theme
6. Open recent files (if configured)
```

### Application Shutdown
```python
1. Save current window state
2. Save panel layout
3. Save user preferences
4. Save view state for all open documents
5. Write UI state to config file
```

### Document Switch
```python
1. Save view state of current document
2. Load view state of new document
3. Apply view state (pan, zoom)
4. Update UI to reflect document state
```

## Integration Points

### With Data Layer
- View state persisted via `ModelCanvasManager.save_view_state_to_file()`
- View state loaded via `ModelCanvasManager.load_view_state_from_file()`

### With Helpers Layer
- Panel loaders query `PanelStateManager` for initial state
- Window manager uses `WindowStateManager` on startup
- Preference dialogs interact with `PreferencesManager`

### With File Layer
- View state saved alongside document files
- Recent files list stored in UI state
- Last used directory tracked in UI state

## Configuration Directory

**Location:** `~/.config/shypn/`

**Files:**
- `ui_state.json` - UI state and preferences
- `recent_files.json` - Recent files list
- `themes/` - Custom themes
- `templates/` - Document templates
- `backups/` - Auto-save backups

## Platform-Specific Considerations

### Linux
- Config directory: `~/.config/shypn/`
- Follows XDG Base Directory specification
- Integration with GNOME/KDE settings

### Windows
- Config directory: `%APPDATA%\shypn\`
- Registry integration (optional)
- Windows theme integration

### macOS
- Config directory: `~/Library/Application Support/shypn/`
- macOS native theming
- Retina display support

## Theme Support

### Theme Configuration
```json
{
  "theme": {
    "name": "dark",
    "colors": {
      "background": "#2e3440",
      "foreground": "#d8dee9",
      "place": "#88c0d0",
      "transition": "#81a1c1",
      "arc": "#5e81ac",
      "selected": "#ebcb8b"
    }
  }
}
```

### Theme Application
- Applied via GTK CSS
- Custom colors for Petri Net objects
- Syntax highlighting in editors
- Icon theming

## Import Patterns

```python
from shypn.ui.window_state import WindowStateManager
from shypn.ui.panel_state import PanelStateManager
from shypn.ui.preferences import PreferencesManager
```

## Future Enhancements

- **Workspace Layouts**: Multiple saved layouts
- **Custom Toolbars**: User-configurable toolbars
- **Keyboard Shortcuts**: Custom shortcut configuration
- **Accessibility**: High contrast, screen reader support
- **Multi-monitor**: Monitor-specific settings
- **Session Management**: Save/restore entire sessions
