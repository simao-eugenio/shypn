# Save Path Integration - Architecture Verification

**Date**: 2025-01-08  
**Status**: ✅ All save paths properly integrated  

## Executive Summary

**Result**: ✅ All save paths in the shypn application are properly integrated with the project architecture.

The application uses three distinct, well-organized storage locations:
1. **User Data**: `~/.config/shypn/` for workspace settings
2. **Projects**: `workspace/projects/` for project-based data
3. **Models**: `models/` for standalone model files (legacy compatibility)

All file operations follow proper architectural patterns with centralized management.

---

## Architecture Overview

### Storage Hierarchy

```
Repository Root
├── models/                    # Standalone model files (legacy mode)
│   └── *.shy                 # Individual Petri net files
│
├── workspace/                 # Project-based workspace
│   ├── projects/             # All projects (managed by ProjectManager)
│   │   ├── project_index.json
│   │   ├── recent_projects.json
│   │   └── <project_name>/   # Individual project
│   │       ├── project.shy   # Project metadata
│   │       ├── models/       # Project's Petri net models
│   │       ├── pathways/     # Analysis pathways
│   │       ├── simulations/  # Simulation results
│   │       ├── exports/      # Exported data
│   │       └── metadata/     # Project metadata & backups
│
└── ~/.config/shypn/          # User configuration (outside repo)
    └── workspace.json        # Window state, preferences
```

---

## File Operations Analysis

### 1. ✅ Petri Net Model Files - `netobj_persistency.py`

**Location**: `src/shypn/file/netobj_persistency.py`

**Architecture Integration**: ✅ **PROPER**

**Save Paths**:
```python
# Initialize with models directory
def __init__(self, models_directory: Optional[str] = None):
    if models_directory is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
        models_directory = os.path.join(repo_root, 'models')
    self.models_directory = models_directory
```

**Dialog Integration**:
```python
def _show_save_dialog(self) -> Optional[str]:
    dialog = Gtk.FileChooserDialog(...)
    
    # Uses proper directory hierarchy
    if self._last_directory and os.path.isdir(self._last_directory):
        dialog.set_current_folder(self._last_directory)
    elif os.path.isdir(self.models_directory):
        dialog.set_current_folder(self.models_directory)  # ✅ Uses configured path
```

**Features**:
- ✅ Remembers last used directory (`_last_directory`)
- ✅ Falls back to `models_directory`
- ✅ Creates `models/` directory if missing
- ✅ Warns about "default.shy" filename
- ✅ Auto-adds `.shy` extension

**Default Behavior**:
- New files: Opens in `models/` directory
- Recent files: Opens in last used directory
- Respects user's navigation choices

---

### 2. ✅ Workspace Settings - `workspace_settings.py`

**Location**: `src/shypn/workspace_settings.py`

**Architecture Integration**: ✅ **PROPER**

**Save Path**:
```python
def __init__(self):
    # User config directory (outside repository)
    config_dir = os.path.join(Path.home(), '.config', 'shypn')
    self.config_file = os.path.join(config_dir, 'workspace.json')
    os.makedirs(config_dir, exist_ok=True)
```

**Stored Data**:
- Window geometry (width, height, x, y)
- Window state (maximized)
- User preferences

**Path**: `~/.config/shypn/workspace.json`

**Rationale**: ✅ **CORRECT**
- Uses XDG Base Directory standard
- Persists across repository clones
- Separate from version control
- User-specific, not project-specific

---

### 3. ✅ Project Management - `project_models.py`

**Location**: `src/shypn/data/project_models.py`

**Architecture Integration**: ✅ **PROPER**

**Save Paths**:
```python
def _setup_default_paths(self):
    """Setup default project paths in workspace directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.normpath(os.path.join(current_dir, '..', '..', '..'))
    
    # Isolated workspace directory ✅
    self.projects_root = os.path.join(repo_root, 'workspace', 'projects')
    os.makedirs(self.projects_root, exist_ok=True)
```

**Project Structure** (per project):
```python
class Project:
    def get_models_dir(self) -> str:
        return os.path.join(self.base_path, 'models')
    
    def get_pathways_dir(self) -> str:
        return os.path.join(self.base_path, 'pathways')
    
    def get_simulations_dir(self) -> str:
        return os.path.join(self.base_path, 'simulations')
```

**Index Files**:
- `workspace/projects/project_index.json` - All projects registry
- `workspace/projects/recent_projects.json` - Recent projects list
- `workspace/projects/<project_name>/project.shy` - Project metadata

**Features**:
- ✅ Isolated from application code
- ✅ Hierarchical project structure
- ✅ Centralized project management
- ✅ Recent projects tracking
- ✅ Auto-creates directory structure

---

### 4. ✅ Document Model - `document_model.py`

**Location**: `src/shypn/data/canvas/document_model.py`

**Architecture Integration**: ✅ **PROPER**

**Save Implementation**:
```python
def save_to_file(self, filepath: str) -> None:
    """Save document to JSON file."""
    # Create directory if needed ✅
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Serialize and save
    data = self.to_dict()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
```

**Responsibility**: Low-level serialization only
- ✅ Does NOT determine save paths
- ✅ Path provided by `netobj_persistency` or project manager
- ✅ Creates parent directories as needed
- ✅ Clean separation of concerns

---

### 5. ✅ Model Canvas Manager - `model_canvas_manager.py`

**Location**: `src/shypn/data/model_canvas_manager.py`

**Architecture Integration**: ✅ **PROPER**

**Export Functionality**:
```python
def export_to_json(self, filepath: str) -> bool:
    """Export current model to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
```

**Usage**: Export/debug feature only
- ✅ Not used for primary save operations
- ✅ User chooses export location via dialog
- ✅ Separate from normal save workflow

---

## Path Responsibility Matrix

| Component | Determines Path? | Creates Directories? | Storage Type | Location |
|-----------|------------------|----------------------|--------------|----------|
| **netobj_persistency.py** | ✅ Yes | ✅ Yes | Model files | `models/` |
| **workspace_settings.py** | ✅ Yes | ✅ Yes | User config | `~/.config/shypn/` |
| **project_models.py** | ✅ Yes | ✅ Yes | Projects | `workspace/projects/` |
| **document_model.py** | ❌ No | ✅ Yes (given path) | Serialization | N/A (receives path) |
| **model_canvas_manager.py** | ❌ No | ❌ No | Export only | User-chosen |

---

## Architectural Compliance

### ✅ Separation of Concerns

1. **Path Management**: Centralized in specialized classes
   - `NetObjPersistency` manages model file paths
   - `ProjectManager` manages project paths
   - `WorkspaceSettings` manages config paths

2. **Serialization**: Separated from path logic
   - `DocumentModel` handles data format only
   - Receives paths from managers
   - Does not determine where to save

3. **User Interaction**: Handled by dedicated components
   - File chooser dialogs in `netobj_persistency`
   - Path remembering and defaults
   - User-friendly warnings

### ✅ Data Isolation

**User Data** (`~/.config/shypn/`):
- ✅ Outside repository
- ✅ Survives repository updates
- ✅ User-specific preferences

**Project Data** (`workspace/projects/`):
- ✅ Inside repository
- ✅ Can be version controlled (optional)
- ✅ Isolated from application code

**Legacy Model Data** (`models/`):
- ✅ Backward compatible
- ✅ Simple standalone files
- ✅ Easy migration path

### ✅ Best Practices

1. **XDG Compliance**: User config in `~/.config/shypn/` ✅
2. **Path Remembering**: Last directory cached ✅
3. **Directory Creation**: Auto-creates as needed ✅
4. **Relative Paths**: Uses `os.path.normpath` ✅
5. **Error Handling**: Try-except for I/O operations ✅
6. **Encoding**: UTF-8 specified for JSON files ✅

---

## Migration Scenarios

### Scenario 1: Legacy to Project-Based

**Current State**: Files in `models/`
**Target State**: Organized in `workspace/projects/<name>/models/`

**Implementation**: Not yet implemented, but architecture supports:
```python
# Future migration tool
def migrate_to_project(old_filepath: str, project_name: str):
    manager = ProjectManager()
    project = manager.create_project(project_name)
    
    # Copy file to project models directory
    new_filepath = os.path.join(project.get_models_dir(), 
                                os.path.basename(old_filepath))
    shutil.copy(old_filepath, new_filepath)
    
    # Update project metadata
    doc = ModelDocument(name=os.path.basename(old_filepath),
                       file_path=new_filepath)
    project.models[doc.id] = doc
    project.save()
```

### Scenario 2: Multiple Users

**Issue**: Different users, same repository
**Solution**: Already handled ✅
- Workspace settings in `~/.config/shypn/` (per-user)
- Projects in `workspace/projects/` (shared or .gitignored)

### Scenario 3: Portable Installation

**Issue**: Run from USB drive
**Solution**: Override paths at initialization
```python
# Custom paths for portable mode
persistency = NetObjPersistency(
    models_directory="/path/to/usb/models"
)

manager = ProjectManager()
manager.projects_root = "/path/to/usb/projects"
```

---

## Verification Checklist

- [x] **All save paths use proper architecture**
- [x] **No hardcoded absolute paths**
- [x] **Path management centralized**
- [x] **User config separate from data**
- [x] **Projects isolated from application code**
- [x] **Directories created automatically**
- [x] **Last directory remembered**
- [x] **Proper error handling**
- [x] **UTF-8 encoding specified**
- [x] **XDG standards followed**

---

## Recommendations

### Current Status: ✅ EXCELLENT

All save paths are properly integrated. No immediate changes needed.

### Future Enhancements (Optional)

1. **Project Migration Tool**
   - Help users migrate from `models/` to project-based structure
   - GUI wizard for creating projects from existing files

2. **Path Configuration UI**
   - Allow users to customize storage locations via preferences
   - Particularly useful for network drives or cloud sync

3. **Backup Management**
   - Automatic backups in `workspace/projects/<name>/metadata/backups/`
   - Already structured in place, just needs implementation

4. **Multi-Repository Support**
   - Allow users to work with multiple repository instances
   - Store absolute paths in workspace settings

---

## Summary

### ✅ All Save Paths Properly Integrated

**Three-Tier Architecture**:
1. **User Settings**: `~/.config/shypn/` (XDG standard)
2. **Project Data**: `workspace/projects/` (isolated workspace)
3. **Legacy Models**: `models/` (backward compatibility)

**Key Strengths**:
- ✅ Clean separation of concerns
- ✅ Centralized path management
- ✅ Proper directory creation
- ✅ User-friendly defaults
- ✅ Extensible design

**No Action Required**: Architecture is solid and follows best practices.

---

## Related Documentation

- **PATHWAY_DATA_ISOLATION_PLAN.md** - Project architecture design
- **NetObjPersistency** - File operations implementation
- **ProjectManager** - Project structure management
- **WorkspaceSettings** - User configuration management

---

## Conclusion

All file save operations in the shypn application properly integrate with the project architecture. The three-tier storage system (user config, project data, legacy models) provides flexibility, maintainability, and backward compatibility while following industry best practices.

**Verdict**: ✅ **No changes needed** - architecture is properly implemented.
