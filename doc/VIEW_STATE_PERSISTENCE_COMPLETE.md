# View State Persistence - Complete Implementation

## Overview

Implemented comprehensive view state persistence that saves and restores the user's complete working environment, including:
- **Zoom level**: Current zoom factor (0.3x to 3.0x)
- **Pan position**: Viewport translation (pan_x, pan_y)
- **Rotation**: Canvas rotation angle (0°, 90°, 180°, 270°)

When users save a document and reopen it later, they will see the model exactly as they left it - with the same zoom, viewport position, and rotation angle.

## Problem Statement

Previously, the view state persistence system only saved zoom and pan, but not rotation. Users would:
1. Rotate canvas to preferred orientation (e.g., 90° clockwise)
2. Zoom and pan to working area
3. Save document
4. Close and reopen document
5. **Find rotation was reset to 0°** - frustrating workflow disruption

This caused constant interruption as users had to manually rotate the canvas back to their preferred orientation every time they reopened a file.

## Solution Architecture

### Data Flow

```
User saves file:
  ModelCanvasManager.to_document_model()
    → DocumentModel.view_state = {zoom, pan_x, pan_y, transformations}
      → transformations = transformation_manager.to_dict()
        → rotation = {angle_degrees: 90, enabled: true}
  → DocumentModel.save_to_file()
    → JSON file with embedded view_state

User opens file:
  DocumentModel.load_from_file()
    → document.view_state = {zoom, pan_x, pan_y, transformations}
  → FileExplorerPanel._load_document_into_canvas()
    → manager.zoom = view_state['zoom']
    → manager.pan_x = view_state['pan_x']
    → manager.pan_y = view_state['pan_y']
    → manager.transformation_manager.from_dict(view_state['transformations'])
  → Canvas redraws with restored rotation
```

### Key Components

1. **TransformationManager** (`canvas_transformations.py`)
   - Already had `to_dict()` and `from_dict()` methods
   - Serializes all transformations (currently only rotation)
   - Format: `{"rotation": {"angle_degrees": 90, "enabled": true}}`

2. **ModelCanvasManager** (`model_canvas_manager.py`)
   - `get_view_state()`: Captures current view state including transformations
   - `set_view_state()`: Restores view state including transformations
   - `to_document_model()`: Converts manager state to DocumentModel with complete view state

3. **DocumentModel** (`document_model.py`)
   - Already had `view_state` attribute
   - Already serialized to JSON in `save_to_file()`
   - Now stores transformations in addition to zoom/pan

4. **FileExplorerPanel** (`file_explorer_panel.py`)
   - `_load_document_into_canvas()`: Restores transformations when loading document
   - Calls `manager.transformation_manager.from_dict()` if transformations present

## Implementation Details

### Changes to ModelCanvasManager

**Before:**
```python
def get_view_state(self):
    return {
        'pan_x': self.pan_x,
        'pan_y': self.pan_y,
        'zoom': self.zoom
    }
```

**After:**
```python
def get_view_state(self):
    return {
        'pan_x': self.pan_x,
        'pan_y': self.pan_y,
        'zoom': self.zoom,
        'transformations': self.transformation_manager.to_dict()
    }
```

**Before:**
```python
def set_view_state(self, view_state):
    if view_state:
        self.pan_x = view_state.get('pan_x', 0.0)
        self.pan_y = view_state.get('pan_y', 0.0)
        self.zoom = view_state.get('zoom', 1.0)
        # ... validation ...
```

**After:**
```python
def set_view_state(self, view_state):
    if view_state:
        self.pan_x = view_state.get('pan_x', 0.0)
        self.pan_y = view_state.get('pan_y', 0.0)
        self.zoom = view_state.get('zoom', 1.0)
        
        # ... validation ...
        
        # Restore transformations (rotation)
        if 'transformations' in view_state:
            self.transformation_manager.from_dict(view_state['transformations'])
```

**Before:**
```python
def to_document_model(self):
    # ...
    document.view_state = {
        "zoom": self.zoom,
        "pan_x": self.pan_x,
        "pan_y": self.pan_y
    }
```

**After:**
```python
def to_document_model(self):
    # ...
    document.view_state = {
        "zoom": self.zoom,
        "pan_x": self.pan_x,
        "pan_y": self.pan_y,
        "transformations": self.transformation_manager.to_dict()
    }
```

### Changes to FileExplorerPanel

**Before:**
```python
def _load_document_into_canvas(self, document, filepath):
    # ...
    if hasattr(document, 'view_state') and document.view_state:
        manager.zoom = document.view_state.get('zoom', 1.0)
        manager.pan_x = document.view_state.get('pan_x', 0.0)
        manager.pan_y = document.view_state.get('pan_y', 0.0)
        manager._initial_pan_set = True
```

**After:**
```python
def _load_document_into_canvas(self, document, filepath):
    # ...
    if hasattr(document, 'view_state') and document.view_state:
        manager.zoom = document.view_state.get('zoom', 1.0)
        manager.pan_x = document.view_state.get('pan_x', 0.0)
        manager.pan_y = document.view_state.get('pan_y', 0.0)
        manager._initial_pan_set = True
        
        # Restore transformations (rotation) if available
        if 'transformations' in document.view_state:
            manager.transformation_manager.from_dict(document.view_state['transformations'])
```

## File Format

The saved JSON file now includes transformations in the view_state:

```json
{
  "version": "1.0",
  "places": [...],
  "transitions": [...],
  "arcs": [...],
  "view_state": {
    "zoom": 1.5,
    "pan_x": 100.0,
    "pan_y": -50.0,
    "transformations": {
      "rotation": {
        "angle_degrees": 90,
        "enabled": true
      }
    }
  }
}
```

## Backward Compatibility

✅ **Fully backward compatible** with existing .shy files:

- Old files without `transformations` key: Will load normally, rotation defaults to 0°
- Old files with only `zoom`, `pan_x`, `pan_y`: Will load normally
- New files with `transformations`: Will load with rotation restored

The code uses defensive checks:
```python
if 'transformations' in view_state:
    manager.transformation_manager.from_dict(view_state['transformations'])
```

## User Experience

### Before Fix
1. User rotates canvas 90° to preferred orientation
2. User zooms and pans to working area
3. User saves document (Ctrl+S)
4. User closes document
5. User reopens document
6. ❌ **Canvas is at 0° rotation** - must manually rotate again
7. User frustrated by workflow interruption

### After Fix
1. User rotates canvas 90° to preferred orientation
2. User zooms and pans to working area
3. User saves document (Ctrl+S)
4. User closes document
5. User reopens document
6. ✅ **Canvas is at 90° rotation** - exactly as user left it
7. User can immediately continue work

## Testing Scenarios

### Scenario 1: Basic Rotation Persistence
1. Open a document (or create new)
2. Add some objects (places, transitions, arcs)
3. Rotate canvas 90° clockwise (context menu → Rotate 90° CW)
4. Zoom to 150%
5. Pan to specific area
6. Save document (Ctrl+S)
7. Close document
8. Reopen same document
9. ✅ **Verify**: Canvas shows at 90° rotation, 150% zoom, same pan position

### Scenario 2: Multiple Rotations
1. Open document
2. Rotate 90° CW → Save → Close → Reopen
3. ✅ **Verify**: Canvas at 90°
4. Rotate 90° CW again (now 180°) → Save → Close → Reopen
5. ✅ **Verify**: Canvas at 180°
6. Rotate 90° CCW (now 90°) → Save → Close → Reopen
7. ✅ **Verify**: Canvas at 90°

### Scenario 3: Reset Rotation
1. Open document (rotated at 90°)
2. Context menu → Reset Rotation (back to 0°)
3. Save document
4. Close and reopen
5. ✅ **Verify**: Canvas at 0° rotation

### Scenario 4: Backward Compatibility
1. Open old .shy file (saved before this feature)
2. ✅ **Verify**: File loads normally, rotation defaults to 0°
3. Rotate to 90° and save
4. Close and reopen
5. ✅ **Verify**: Now rotation persists at 90°

### Scenario 5: Multi-Document with Different Rotations
1. Open document A, rotate to 90°, switch tabs
2. Open document B, rotate to 180°, switch tabs
3. Open document C, keep at 0°
4. Save all three documents
5. Close all
6. Reopen all three
7. ✅ **Verify**: A at 90°, B at 180°, C at 0°

## Files Modified

1. **src/shypn/data/model_canvas_manager.py**
   - Updated `get_view_state()` to include transformations
   - Updated `set_view_state()` to restore transformations
   - Updated `to_document_model()` to save transformations

2. **src/shypn/helpers/file_explorer_panel.py**
   - Updated `_load_document_into_canvas()` to restore transformations

## Dependencies

This feature builds on existing infrastructure:
- ✅ TransformationManager with to_dict()/from_dict() (already implemented)
- ✅ DocumentModel with view_state attribute (already implemented)
- ✅ JSON serialization in save_to_file() (already implemented)
- ✅ View state loading in _load_document_into_canvas() (already implemented)

The implementation simply **connects existing pieces** - no new infrastructure needed.

## Benefits

1. **Workflow Continuity**: Users maintain their preferred view orientation across sessions
2. **Reduced Friction**: No manual re-rotation needed when reopening files
3. **Multi-Document Support**: Each document remembers its own rotation independently
4. **Backward Compatible**: Works seamlessly with existing files
5. **Extensible**: Framework ready for future transformations (reflection, etc.)

## Future Enhancements

The TransformationManager architecture supports adding more transformations:
- Horizontal/vertical reflection
- Custom transformation matrices
- Animation/interpolation between states

All would automatically persist using the same `to_dict()`/`from_dict()` pattern.

## Commit Message

```
Add rotation persistence to view state

Extend view state persistence to include canvas rotation angle.
Users can now save documents with rotated canvas and the rotation
will be restored when reopening the file.

Changes:
- Updated get_view_state() to include transformation_manager.to_dict()
- Updated set_view_state() to restore transformation_manager.from_dict()
- Updated to_document_model() to save transformations in view_state
- Updated _load_document_into_canvas() to restore transformations

Benefits:
- Preserves user's preferred canvas orientation across sessions
- Each document independently tracks its rotation state
- Fully backward compatible with existing .shy files
- No manual re-rotation needed when reopening files

Files modified:
- src/shypn/data/model_canvas_manager.py
- src/shypn/helpers/file_explorer_panel.py
```
