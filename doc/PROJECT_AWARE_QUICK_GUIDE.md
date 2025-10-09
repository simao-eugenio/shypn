# Project-Aware Save/Load - Quick Guide

## What Changed

`NetObjPersistency` now automatically detects and uses the current project's directory.

## Behavior

### With Active Project
```
Current Project: "MySimulation"

File → Save opens in:
📁 workspace/projects/MySimulation/models/  ✅
```

### Without Active Project
```
No current project

File → Save opens in:
📁 workspace/projects/  ✅
```

## Usage

### Basic Usage (Automatic)
```python
# Automatically uses current project
persistency = create_persistency_manager(window)

# Save dialog opens in current project's models/ directory
persistency.save_document(document)
```

### Update on Project Change
```python
# When user switches projects
def on_project_changed(new_project):
    manager = ProjectManager()
    manager.current_project = new_project
    
    # Update persistency to use new project directory
    persistency.update_models_directory_from_project()
```

## Directory Selection Logic

```
models_directory parameter provided?
├─ Yes → Use provided directory
└─ No  → Auto-detect:
    ├─ ProjectManager available?
    │  ├─ Yes → current_project exists?
    │  │  ├─ Yes → Use project.get_models_dir()  ✅ ProjectA/models/
    │  │  └─ No  → Use manager.projects_root    ✅ workspace/projects/
    │  └─ No  → Use fallback                     ✅ workspace/projects/
    └─ Fallback: workspace/projects/
```

## Integration Points

### When Creating Persistency Manager
```python
# In main app initialization
self.persistency = create_persistency_manager(window)
# Already project-aware! ✅
```

### When Project Changes
```python
# Project opened
self.persistency.update_models_directory_from_project()

# Project switched
self.persistency.update_models_directory_from_project()

# Project created
self.persistency.update_models_directory_from_project()
```

## Examples

### Example 1: App Startup (No Project)
```python
# Launch app
persistency = create_persistency_manager(window)
# Uses: workspace/projects/ ✅

# User creates model and saves
# Dialog opens: workspace/projects/
# User can create: workspace/projects/MyProject/models/model1.shy
```

### Example 2: Open Existing Project
```python
# User opens project
manager = ProjectManager()
project = Project.load('workspace/projects/SimProject/project.shy')
manager.current_project = project

# Update persistency
persistency.update_models_directory_from_project()

# Next save dialog opens in:
# workspace/projects/SimProject/models/ ✅
```

### Example 3: Switch Between Projects
```python
# Currently in ProjectA
# Save opens: workspace/projects/ProjectA/models/ ✅

# Switch to ProjectB
manager.current_project = projectB
persistency.update_models_directory_from_project()

# Save opens: workspace/projects/ProjectB/models/ ✅
```

## Directory Structure

```
workspace/projects/
├── ProjectA/
│   ├── project.shy
│   ├── models/              ← Opens here when ProjectA active
│   │   ├── model1.shy
│   │   └── model2.shy
│   ├── pathways/
│   └── simulations/
│
├── ProjectB/
│   ├── project.shy
│   ├── models/              ← Opens here when ProjectB active
│   │   └── model3.shy
│   └── ...
│
└── standalone_model.shy     ← Can save here when no project active
```

## API Reference

### NetObjPersistency

```python
class NetObjPersistency:
    def __init__(self, parent_window=None, models_directory=None):
        """Initialize with automatic project detection."""
        
    def update_models_directory_from_project(self):
        """Update directory when project changes.
        
        Call this when:
        - Project opened
        - Project switched
        - Project created
        """
        
    def save_document(self, document, save_as=False):
        """Save to current project's models directory."""
        
    def load_document(self):
        """Load from current project's models directory."""
```

### Helper Function

```python
def create_persistency_manager(parent_window=None, models_directory=None):
    """Create project-aware persistency manager."""
    # Returns NetObjPersistency instance
```

## Status

✅ **Auto-detects current project**  
✅ **Uses project's models/ directory**  
✅ **Falls back to workspace/projects/**  
✅ **Updates when project changes**  
✅ **Backward compatible**  
✅ **No breaking changes**  

## Testing

Quick test:
```bash
# 1. Launch app
python3 src/shypn.py

# 2. File → Save
# Should open in: workspace/projects/

# 3. Create project folder structure
# e.g., TestProject/models/

# 4. Save file there
# Next save should remember TestProject/models/
```

## Summary

File operations are now **project-aware**:
- Automatically use current project's structure
- Fallback to workspace when no project active
- Update dynamically when projects change
- Maintain backward compatibility

**No changes needed to existing code!**
