# Inline Project Creation Feature

## Overview

Implemented dialog-free project creation in the File Panel. Users can now create new projects by clicking "New Project" button, which creates an inline editable field in the `workspace/projects/` folder. User types the project name and presses Enter to create the full project structure.

## User Experience

### Workflow:

1. **User clicks "New Project" button** in Project Actions category
2. **File Panel navigates** to `workspace/projects/` folder automatically
3. **Inline editable field appears** with placeholder text "New Project"
4. **User types project name** and presses Enter
5. **Project structure is created** with .shy file and all templates
6. **Tree refreshes** to show the new project folder

### Cancellation:
- Press ESC to cancel without creating project
- Temporary entry is removed
- Returns to normal state

## Implementation Details

### Files Modified

#### 1. `src/shypn/ui/file_panel_controller.py`

**Added State:**
```python
self.on_project_created = None  # Callback when project is created
self.project_creation_mode = False  # Flag for inline project creation
```

**New Methods:**

**`on_new_project(button)`**
- Navigates to `workspace/projects/` folder (creates if doesn't exist)
- Enters project creation mode
- Starts inline editing for new project

**`_start_inline_edit_new_project()`**
- Creates temporary "New Project" entry in tree
- Makes name renderer editable
- Stores editing state
- Sets cursor to editing mode

#### 2. `src/shypn/helpers/project_actions_controller.py`

**Updated New Project Handler:**
```python
def _on_new_project_clicked(self, button):
    if self.file_panel_controller:
        # Use inline creation (no dialog)
        self.file_panel_controller.on_new_project(button)
    else:
        # Fallback to dialog for compatibility
        self.dialog_manager.show_new_project_dialog()
```

#### 3. `src/shypn/helpers/file_panel_v3_loader.py`

**Connected Cell Renderer Signals:**
```python
if self.name_renderer:
    self.name_renderer.connect('edited', self._on_cell_edited)
    self.name_renderer.connect('editing-canceled', self._on_cell_editing_canceled)
```

**New Methods:**

**`_on_cell_edited(renderer, path, new_text)`**
- Handles completion of inline editing
- Checks if in project creation mode
- Delegates to `_create_project_from_inline_edit()`

**`_on_cell_editing_canceled(renderer)`**
- Handles ESC key or cancellation
- Removes temporary entry
- Exits project creation mode
- Refreshes tree

**`_create_project_from_inline_edit(path, project_name)`**
- Validates project name (non-empty, trimmed)
- Removes temporary entry from tree
- Calls `ProjectManager.create_project()`
- Creates full project structure:
  - Project folder
  - .shy project file
  - models/ subdirectory
  - pathways/ subdirectory
  - analyses/ subdirectory
- Refreshes tree to show new project
- Triggers `on_project_created` callback

#### 4. `src/shypn/helpers/file_panel_loader.py`

**Wired Controller Callbacks:**
```python
if self.file_explorer and hasattr(self.file_explorer, 'controller'):
    self.file_explorer.controller.on_project_created = self._on_project_created_from_file_panel
```

**New Callback Handler:**
```python
def _on_project_created_from_file_panel(self, project):
    """Handle project creation from inline edit."""
    if self.project_controller:
        self.project_controller._on_project_created(project)
```

## Architecture Pattern

### MVC Flow for Project Creation:

```
User clicks "New Project" (View)
    ↓
ProjectActionsController._on_new_project_clicked
    ↓
FilePanelController.on_new_project
    ↓
Navigate to workspace/projects/
    ↓
_start_inline_edit_new_project (adds temp entry)
    ↓
User types name + Enter
    ↓
FilePanelV3Loader._on_cell_edited
    ↓
_create_project_from_inline_edit
    ↓
ProjectManager.create_project (Model)
    ↓
Callback → ProjectActionsController._on_project_created
    ↓
Update UI state & open project
```

### Component Responsibilities:

**FilePanelController (UI Logic):**
- Manages navigation to projects folder
- Manages project creation mode state
- Initiates inline editing
- Provides callbacks

**FilePanelV3Loader (Integration):**
- Connects cell renderer signals
- Handles editing completion/cancellation
- Creates project via ProjectManager
- Manages tree updates

**ProjectActionsController (Business Logic):**
- Routes button click to file panel or dialog
- Updates button states
- Notifies application of project creation

**ProjectManager (Data Model):**
- Creates project structure on disk
- Creates .shy file with metadata
- Initializes project folders
- Registers project in index

## Benefits

✅ **No Dialogs:** Inline editing in familiar file tree  
✅ **Fast:** Type name and press Enter - done!  
✅ **Visual:** See exactly where project will be created  
✅ **Clean:** Projects automatically organized in workspace/projects/  
✅ **Consistent:** Matches inline file/folder creation pattern  
✅ **Cancellable:** ESC key cancels without side effects  

## Project Structure Created

When user creates project "MyProject", the following structure is created:

```
workspace/
  projects/
    MyProject/
      MyProject.shy           # Project file with metadata
      models/                 # For model files
      pathways/              # For imported pathway raw files
      analyses/              # For analysis results
      README.md              # Project documentation
```

## Testing Checklist

### Manual Testing:

- [ ] **Click New Project:** Navigates to workspace/projects/, creates inline field
- [ ] **Type project name:** Can edit the "New Project" text
- [ ] **Press Enter:** Creates project structure, refreshes tree
- [ ] **Press ESC:** Cancels creation, removes temp entry
- [ ] **Empty name:** Validation prevents creation
- [ ] **Special characters:** Handled appropriately
- [ ] **Duplicate name:** Error handling (to be implemented)
- [ ] **Project opens:** After creation, project should be available to open

### Edge Cases:

- [ ] **workspace/projects/ doesn't exist:** Creates automatically
- [ ] **Permission denied:** Error message shown
- [ ] **Disk full:** Graceful error handling
- [ ] **Invalid characters in name:** Sanitization or error

### Integration:

- [ ] **Project appears in tree:** Immediately visible after creation
- [ ] **Can open created project:** Double-click works
- [ ] **Project Settings enabled:** Button becomes active
- [ ] **Recent projects updated:** New project in recent list

## Future Enhancements

1. **Project Templates:**
   - Select template during creation
   - Pre-populate with example models
   - Custom templates

2. **Duplicate Name Handling:**
   - Check for existing projects
   - Suggest alternative names
   - Append numbers (MyProject_2, MyProject_3)

3. **Project Properties Inline:**
   - Edit description inline
   - Set tags/categories
   - Configure settings

4. **Project Import:**
   - Drag & drop .shy file to import
   - Import from archive inline
   - Clone existing project

5. **Visual Feedback:**
   - Progress indicator during creation
   - Success animation
   - Error icons for invalid names

## Related Features

- **Open Project Inline:** `doc/FILE_PANEL_PROJECT_OPENING.md`
- **Project System:** `src/shypn/data/project_models.py`
- **Import Flow Fix:** `doc/IMPORT_FLOW_FIX.md`

## Migration Notes

- Dialog-based creation still works if file_panel_controller not set
- Backward compatible with existing code
- Can gradually migrate other creation flows to inline pattern

## Code Quality

- ✅ All files compile without syntax errors
- ✅ All imports work correctly
- ✅ Follows existing MVC pattern
- ✅ Error handling with try-except blocks
- ✅ Console logging for debugging
- ✅ Clean separation of concerns
- ✅ Callbacks for loose coupling
- ✅ Consistent with file/folder inline creation pattern
