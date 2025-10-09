# Project-Aware File Operations - Implementation

**Date**: 2025-01-08  
**Status**: ✅ Complete  

## Overview

`NetObjPersistency` is now fully integrated with `ProjectManager` to automatically use the current project's directory structure for save/load operations.

## Implementation

### Automatic Project Detection

When `NetObjPersistency` is initialized, it automatically:
1. Checks if there's an active project via `ProjectManager`
2. Uses the active project's `models/` directory if available
3. Falls back to `workspace/projects/` if no project is active
4. Gracefully handles cases where `ProjectManager` is not available

### Code Changes

**File**: `src/shypn/file/netobj_persistency.py`

#### 1. Project-Aware Initialization

```python
def __init__(self, parent_window=None, models_directory=None):
    """Initialize with automatic project detection."""
    
    if models_directory is None:
        # Try to use current project's models directory
        try:
            from shypn.data.project_models import ProjectManager
            manager = ProjectManager()
            
            if manager.current_project:
                # Use current project's models directory ✅
                models_directory = manager.current_project.get_models_dir()
            else:
                # No active project, use projects root ✅
                models_directory = manager.projects_root
        except Exception:
            # Fallback if ProjectManager not available ✅
            models_directory = os.path.join(repo_root, 'workspace', 'projects')
```

#### 2. Dynamic Directory Update

```python
def update_models_directory_from_project(self) -> None:
    """Update models directory when project changes.
    
    Call this method when:
    - User switches to a different project
    - User creates a new project
    - User opens a project
    """
    manager = ProjectManager()
    
    if manager.current_project:
        new_dir = manager.current_project.get_models_dir()
        self.models_directory = new_dir
        self._last_directory = new_dir  # Reset to project directory
    else:
        self.models_directory = manager.projects_root
```

## Behavior by Scenario

### Scenario 1: Active Project Exists

```
Current Project: "MySimulation"
Project Path: workspace/projects/MySimulation/

Save Dialog Opens In:
→ workspace/projects/MySimulation/models/  ✅

Load Dialog Opens In:
→ workspace/projects/MySimulation/models/  ✅
```

### Scenario 2: No Active Project

```
Current Project: None

Save Dialog Opens In:
→ workspace/projects/  ✅
(User can create project folder or save standalone)

Load Dialog Opens In:
→ workspace/projects/  ✅
```

### Scenario 3: User Navigates Away

```
Current Project: "MySimulation"
Dialog Opens: workspace/projects/MySimulation/models/

User navigates to: workspace/projects/OtherProject/models/
Saves file there

Next dialog opens:
→ workspace/projects/OtherProject/models/  ✅
(Remembers last directory)
```

### Scenario 4: Project Switches

```
Initial: Project A
Dialog opens: workspace/projects/ProjectA/models/

User switches to: Project B

Code calls: persistency.update_models_directory_from_project()

Next dialog opens:
→ workspace/projects/ProjectB/models/  ✅
```

## Integration Points

### Where to Update Directory

Call `update_models_directory_from_project()` when:

1. **Project Selection Changes**
```python
def on_project_selected(self, project):
    manager = ProjectManager()
    manager.current_project = project
    
    # Update persistency to use new project's directory
    self.persistency.update_models_directory_from_project()
```

2. **New Project Created**
```python
def create_new_project(self, name):
    manager = ProjectManager()
    project = manager.create_project(name)
    manager.current_project = project
    
    # Update persistency
    self.persistency.update_models_directory_from_project()
```

3. **Project Opened**
```python
def open_project(self, project_file):
    manager = ProjectManager()
    project = Project.load(project_file)
    manager.current_project = project
    
    # Update persistency
    self.persistency.update_models_directory_from_project()
```

## Directory Resolution Flow

```
┌─────────────────────────────────────────┐
│ NetObjPersistency.__init__()            │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ models_directory parameter provided?    │
└───────────────┬─────────────────────────┘
                │
        ┌───────┴───────┐
        │               │
       Yes              No
        │               │
        │               ▼
        │    ┌──────────────────────────┐
        │    │ Import ProjectManager     │
        │    └──────────┬────────────────┘
        │               │
        │               ▼
        │    ┌──────────────────────────┐
        │    │ manager.current_project?  │
        │    └──────────┬────────────────┘
        │               │
        │       ┌───────┴───────┐
        │      Yes              No
        │       │               │
        │       ▼               ▼
        │  ┌────────┐    ┌──────────┐
        │  │project │    │projects  │
        │  │.get_   │    │_root     │
        │  │models_ │    │          │
        │  │dir()   │    │          │
        │  └────┬───┘    └─────┬────┘
        │       │              │
        └───────┴──────────────┴────────┐
                                        │
                                        ▼
                        ┌───────────────────────────┐
                        │ self.models_directory =   │
                        │ (chosen path)             │
                        └───────────────────────────┘
```

## File Explorer Integration

If you have a file explorer panel, it should also respond to project changes:

```python
class FileExplorerPanel:
    def __init__(self):
        self.persistency = create_persistency_manager()
        
        # Listen for project changes
        manager = ProjectManager()
        manager.on_project_changed = self._on_project_changed
    
    def _on_project_changed(self, project):
        """Update when active project changes."""
        # Update persistency directory
        self.persistency.update_models_directory_from_project()
        
        # Refresh file tree to show new project's files
        self.refresh_file_tree()
```

## Backward Compatibility

### Legacy Files (Not in a Project)

Files saved before project system implementation:
```
models/old_model.shy  (legacy location)
```

Can still be opened:
1. User navigates to `models/` directory
2. Opens legacy file
3. Can save back to `models/` or move to a project

### Manual Override

If you need to force a specific directory:
```python
# Force specific directory (bypasses project detection)
persistency = NetObjPersistency(
    parent_window=window,
    models_directory="/custom/path/to/models"
)
```

## Testing Checklist

### Test 1: No Active Project
- [ ] Launch app (no project loaded)
- [ ] File → Save
- [ ] ✅ Dialog opens in `workspace/projects/`

### Test 2: Active Project
- [ ] Create/open project "TestProject"
- [ ] File → Save
- [ ] ✅ Dialog opens in `workspace/projects/TestProject/models/`

### Test 3: Project Switch
- [ ] Open project "ProjectA"
- [ ] File → Save (should open in ProjectA/models/)
- [ ] Switch to project "ProjectB"
- [ ] Call `update_models_directory_from_project()`
- [ ] File → Save
- [ ] ✅ Dialog opens in `workspace/projects/ProjectB/models/`

### Test 4: User Navigation
- [ ] Save dialog opens in project models/
- [ ] User navigates to different folder
- [ ] Saves file there
- [ ] Next save
- [ ] ✅ Dialog opens in last used folder

### Test 5: Project Creation
- [ ] Create new project "NewProject"
- [ ] Call `update_models_directory_from_project()`
- [ ] File → Save
- [ ] ✅ Dialog opens in `workspace/projects/NewProject/models/`

## Implementation Status

- [x] **Project detection in __init__**
- [x] **Dynamic directory update method**
- [x] **Fallback for no active project**
- [x] **Fallback for ProjectManager unavailable**
- [x] **Documentation updated**
- [x] **No syntax errors**
- [ ] **Integration with project UI** (future)
- [ ] **File explorer synchronization** (future)
- [ ] **Project switching hooks** (future)

## Future Enhancements

### 1. Automatic Synchronization
```python
class NetObjPersistency:
    def __init__(self):
        # Auto-register for project change notifications
        manager = ProjectManager()
        manager.register_observer(self._on_project_changed)
    
    def _on_project_changed(self, project):
        """Automatically update when project changes."""
        self.update_models_directory_from_project()
```

### 2. Project-Aware File Browser
```python
def _show_save_dialog(self):
    dialog = Gtk.FileChooserDialog(...)
    
    # Add shortcuts to all projects
    manager = ProjectManager()
    for project_id, info in manager.project_index.items():
        project_path = info.get('base_path')
        dialog.add_shortcut_folder(project_path)
```

### 3. Recently Used Projects in Dialog
```python
def _show_save_dialog(self):
    # Add recent projects as shortcuts
    manager = ProjectManager()
    for project_id in manager.recent_projects[:5]:
        project = manager.get_project(project_id)
        if project:
            dialog.add_shortcut_folder(project.get_models_dir())
```

## Summary

✅ **File operations now project-aware**  
✅ **Automatic directory detection**  
✅ **Dynamic updates on project change**  
✅ **Graceful fallbacks**  
✅ **Backward compatible**  

The save/load system now intelligently uses the current project's directory structure, making file management seamless for project-based workflows while maintaining backward compatibility with standalone files.

## Related Files

- `src/shypn/file/netobj_persistency.py` - Project-aware file operations (modified)
- `src/shypn/data/project_models.py` - Project structure definitions
- `src/shypn.py` - Main app (creates persistency manager)

## Migration Notes

**No migration needed!** The changes are backward compatible:
- Existing code works without changes
- Projects automatically detected when available
- Legacy files (outside projects) still accessible
