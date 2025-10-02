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
- **State Validation**: Initial document state validation
- **Rendering Pipeline**: Grid drawing with Cairo

**Key Features:**
- Independent of GTK widgets for better testability
- Maintains document state separately from UI
- Supports multi-document architecture
- Zoom range: 10% to 1000%
- Base grid spacing: ~5mm at 100% zoom

### `user_model.py`
**User Data Models**

User-related data structures and models.

## Architecture Notes

This `data/` directory is part of the internal package structure (`src/shypn/data/`), distinct from the external `data/` directory at repository root (used for packaging system data).

**Import Pattern:**
```python
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.data.user_model import ...
```