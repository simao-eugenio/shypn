# Save/Load Path Verification

**Date:** 2025-10-09  
**Status:** ⚠️ ISSUE IDENTIFIED

## Problem Report

User reports: "when I save a model, on open it reveals an empty model"

## Root Cause Analysis

The issue is in the **Project Opening Flow**. When a project is opened:

### What Happens Now (BROKEN):

1. ✅ User clicks "Open Project" button
2. ✅ Dialog shows project browser
3. ✅ User selects `project.shy` file
4. ✅ `ProjectManager.open_project_by_path()` loads the project
5. ✅ `Project.from_dict()` restores project metadata
6. ✅ ModelDocument entries are restored (with `file_path` to model files)
7. ❌ **Individual model `.shy` files are NOT loaded into canvas**
8. ❌ **Canvas remains empty or shows default blank document**

### Project Structure:

```
workspace/projects/MyProject/
├── project.shy                    # Project metadata
├── models/
│   ├── model1.shy                 # Actual model content (NOT loaded)
│   ├── model2.shy                 # Actual model content (NOT loaded)
│   └── ...
├── pathways/
└── simulations/
```

### Data Flow Problem:

**project.shy** contains:
```json
{
  "identity": {...},
  "content": {
    "models": [
      {
        "id": "uuid-1234",
        "name": "My Model",
        "file_path": "workspace/projects/MyProject/models/model1.shy"
      }
    ]
  }
}
```

**models/model1.shy** contains (THIS IS NOT BEING LOADED):
```json
{
  "version": "2.0",
  "places": [
    {"id": "P1", "name": "P1", "label": "Place1", "x": 100, "y": 100, "tokens": 5},
    ...
  ],
  "transitions": [...],
  "arcs": [...]
}
```

## The Missing Link

The `ModelDocument` class only stores **metadata**:

```python
class ModelDocument:
    """Model document metadata entry in project."""
    
    def __init__(self, id: str = None, name: str = "Untitled Model",
                 description: str = "", file_path: str = None):
        self.id = id
        self.name = name
        self.description = description
        self.file_path = file_path  # Path to actual .shy file
        self.created_date = datetime.now().isoformat()
        self.modified_date = self.created_date
        # NO PLACES, TRANSITIONS, ARCS!
```

When a project is opened, the code **does not**:
1. Iterate through `project.models`
2. Load each model's `file_path` using `DocumentModel.load_from_file()`
3. Create canvas tabs for each loaded model
4. Populate canvases with places/transitions/arcs

## Where the Fix Should Go

### Option 1: In `ProjectManager.open_project_by_path()` (Recommended)

After loading the project, automatically load all model files:

```python
def open_project_by_path(self, project_file: str) -> Optional[Project]:
    """Open a project by file path."""
    try:
        project = Project.load(project_file)
        self.current_project = project
        
        # ✅ ADD THIS: Load all models into canvas
        for model_id, model_doc in project.models.items():
            if model_doc.file_path and os.path.exists(model_doc.file_path):
                # Load the actual model content
                document = DocumentModel.load_from_file(model_doc.file_path)
                # Need canvas_loader reference to create tabs
                # This requires wiring canvas_loader to ProjectManager
                self.canvas_loader.load_model_document(document, model_doc.name)
        
        self.add_to_recent(project.id)
        return project
    except Exception as e:
        print(f"Error loading project: {e}")
        return None
```

**Problem with this approach:** `ProjectManager` doesn't have access to `canvas_loader`!

### Option 2: In `ProjectActionsController._on_project_opened()` (Better)

When the `on_project_opened` callback is fired:

```python
def _on_project_opened(self, project):
    """Called when a project is opened."""
    # Enable project settings button
    if self.project_settings_button:
        self.project_settings_button.set_sensitive(True)
    
    # ✅ ADD THIS: Load all models into canvas
    if hasattr(self, 'canvas_loader') and self.canvas_loader:
        for model_id, model_doc in project.models.items():
            if model_doc.file_path and os.path.exists(model_doc.file_path):
                try:
                    from shypn.data.canvas.document_model import DocumentModel
                    document = DocumentModel.load_from_file(model_doc.file_path)
                    self.canvas_loader.load_model_into_tab(document, model_doc.name)
                except Exception as e:
                    print(f"Error loading model {model_doc.name}: {e}")
    
    # Notify external callback
    if self.on_project_opened:
        self.on_project_opened(project)
```

**Problem with this approach:** `ProjectActionsController` also doesn't have `canvas_loader` reference!

### Option 3: In main application (`shypn.py`) (BEST)

Wire the project opened callback to load models:

```python
# In shypn.py, after creating project_actions_controller:

def on_project_opened_handler(project):
    """Handle project opened - load all models into canvas."""
    if project and project.models:
        for model_id, model_doc in project.models.items():
            if model_doc.file_path and os.path.exists(model_doc.file_path):
                try:
                    from shypn.data.canvas.document_model import DocumentModel
                    document = DocumentModel.load_from_file(model_doc.file_path)
                    
                    # Load into canvas with tab name from model metadata
                    filename = model_doc.name or os.path.splitext(
                        os.path.basename(model_doc.file_path)
                    )[0]
                    
                    page_index, drawing_area = model_canvas_loader.add_document(filename=filename)
                    manager = model_canvas_loader.get_canvas_manager(drawing_area)
                    if manager:
                        # Restore objects
                        manager.places = list(document.places)
                        manager.transitions = list(document.transitions)
                        manager.arcs = list(document.arcs)
                        manager._next_place_id = document._next_place_id
                        manager._next_transition_id = document._next_transition_id
                        manager._next_arc_id = document._next_arc_id
                        
                        # Restore view state
                        if hasattr(document, 'view_state') and document.view_state:
                            manager.zoom = document.view_state.get('zoom', 1.0)
                            manager.pan_x = document.view_state.get('pan_x', 0.0)
                            manager.pan_y = document.view_state.get('pan_y', 0.0)
                            manager._initial_pan_set = True
                        
                        # Mark as clean (just loaded)
                        if persistency:
                            persistency.set_filepath(model_doc.file_path)
                            persistency.mark_clean()
                        
                        drawing_area.queue_draw()
                        
                except Exception as e:
                    print(f"Error loading model {model_doc.name}: {e}")
                    import traceback
                    traceback.print_exc()

# Wire it up
if hasattr(project_actions_controller, 'set_on_project_opened'):
    project_actions_controller.on_project_opened = on_project_opened_handler
```

## Current Code Locations

**Project Loading:**
- `src/shypn/data/project_models.py:469` - `ProjectManager.open_project_by_path()`
- `src/shypn/data/project_models.py:257` - `Project.load()`
- `src/shypn/data/project_models.py:214` - `Project.from_dict()`

**Model Document:**
- `src/shypn/data/project_models.py:40` - `ModelDocument` class (only metadata!)
- `src/shypn/data/project_models.py:68` - `ModelDocument.from_dict()`

**Document Model (Actual Content):**
- `src/shypn/data/canvas/document_model.py:502` - `DocumentModel.load_from_file()`
- `src/shypn/data/canvas/document_model.py:409` - `DocumentModel.from_dict()`

**Project Actions:**
- `src/shypn/helpers/project_actions_controller.py:111` - `_on_open_project_clicked()`
- `src/shypn/helpers/project_actions_controller.py:150` - `_on_project_opened()`

**Main Application:**
- `src/shypn.py` - Main application entry point with wiring

## Verification Test

To verify this is the issue:

1. Create a new model with some places/transitions
2. Save it to `test_model.shy`
3. Check file contents:
   ```bash
   cat test_model.shy  # Should show places, transitions, arcs
   ```
4. Close and reopen the file
5. ✅ Model should load correctly (this works for individual files)

6. Now create a project
7. Add the model to the project
8. Save project as `test_project.shy`
9. Check project file:
   ```bash
   cat test_project.shy  # Should show models array with file_path
   ```
10. Close and open the project
11. ❌ Canvas is empty (because model files aren't loaded)

## Save Flow (This Works Correctly)

When saving:
1. ✅ Canvas content → `DocumentModel.to_dict()` → `model.shy`
2. ✅ Project metadata → `Project.to_dict()` → `project.shy`
3. ✅ Both files are written correctly

## Load Flow (This is BROKEN)

When loading:
1. ✅ `project.shy` → `Project.from_dict()` → Project with ModelDocument list
2. ❌ **Individual `model.shy` files are NOT loaded**
3. ❌ Canvas remains empty

## Recommended Fix

Implement Option 3 in `shypn.py` to wire up model loading when a project is opened.

This maintains separation of concerns:
- `ProjectManager` handles project metadata
- Canvas loader handles document rendering  
- Main application wires them together

## Testing After Fix

After implementing the fix, verify:

1. ✅ Create project with 2 models
2. ✅ Save project
3. ✅ Close application
4. ✅ Reopen application
5. ✅ Open project
6. ✅ **All models load into separate tabs**
7. ✅ **All places/transitions/arcs are visible**
8. ✅ **Zoom and pan state restored for each model**

## Impact

**Current Behavior (BROKEN):**
- Save project → OK
- Open project → Empty canvas ❌

**After Fix:**
- Save project → OK
- Open project → All models loaded ✅

## Related Files to Modify

1. **src/shypn.py** - Add `on_project_opened_handler` to load models
2. **src/shypn/helpers/project_actions_controller.py** - Possibly add `canvas_loader` reference
3. **doc/PROJECT_WORKFLOW.md** - Update documentation about project opening

## Notes

The save path is **correct** - files are being saved properly with all content. The load path is **incomplete** - project metadata loads but individual model files don't.

This is a classic case of "metadata vs. content" separation where the wiring between them was never completed.
