# Data Models

This directory contains data model files and business logic for the Shypn application, separated from UI components.

## Current Modules

### `model_canvas_manager.py`
**Canvas State Management and Document Controller**

Manages the canvas properties, transformations, and document lifecycle for Petri Net models:

- **Zoom Operations**: Pointer-centered zoom (in/out), zoom by factor, set absolute zoom
- **Pan Operations**: Viewport translation, drag-based panning
- **Grid System**: Adaptive spacing based on zoom, multiple styles (line/dot/cross)
- **Coordinate Transformations**: Screen ↔ World coordinate conversions
- **Document Metadata**: Filename, modified flag, creation/modification timestamps
- **View State Persistence**: Save/restore pan and zoom state across sessions
- **State Validation**: Initial document state validation
- **Rendering Pipeline**: Grid drawing with Cairo

**Key Features:**
- Independent of GTK widgets for better testability
- Maintains document state separately from UI
- Supports multi-document architecture
- Zoom range: 10% to 1000%
- Base grid spacing: ~5mm at 100% zoom
- View state file: `.shy.view` (stores pan_x, pan_y, zoom)

**View State Persistence:**
- Saves viewport state on all zoom operations (buttons, wheel, preset levels)
- Saves viewport state on pan operations
- Automatically restores view state when document is reopened
- Ensures user always returns to last working position and zoom level

### `user_model.py`
**User Data Models**

User-related data structures and models.

### `canvas/` Subdirectory
**Document and Canvas Data Structures**

Contains the core document model and canvas state management:

#### `document_model.py`
**Petri Net Document Model**

The main document class that represents a complete Petri Net model:
- Manages lists of places, transitions, and arcs
- Handles serialization/deserialization (to_dict/from_dict)
- Save/load operations with JSON format
- File format versioning and migration
- Document-level operations (add/remove objects)
- Connection validation and management

**File Format:**
```json
{
  "version": "2.0",
  "metadata": {...},
  "places": [...],
  "transitions": [...],
  "arcs": [...]
}
```

#### `canvas_state.py`
**Canvas State Management**

Manages transient canvas state that doesn't persist to file:
- Active tool selection
- Selection state
- Temporary rendering state
- UI interaction state

#### `document_canvas.py`
**Document Canvas Integration**

Bridges the document model with canvas rendering and state management.

## Architecture Notes

This `data/` directory is part of the internal package structure (`src/shypn/data/`), distinct from the external `data/` directory at repository root (used for packaging system data).

**Import Pattern:**
```python
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.data.canvas.document_model import DocumentModel
from shypn.data.user_model import ...
```

## Separation of Concerns

- **`model_canvas_manager.py`**: Canvas viewport and transformations (zoom, pan, grid)
- **`canvas/document_model.py`**: Petri Net structure and persistence
- **`canvas/canvas_state.py`**: Transient UI state
- **UI helpers** (in `helpers/`): GTK4 widgets and event handling