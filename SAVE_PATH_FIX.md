# Save Path Fix - Updated to workspace/projects

**Date**: 2025-01-08  
**Status**: ✅ Fixed  

## Issue

The save dialog was defaulting to `root/models/` instead of following the project architecture which uses `workspace/projects/`.

## Root Cause

In `netobj_persistency.py`, the `__init__` method was calculating:
```python
# OLD - Wrong path
models_directory = os.path.join(repo_root, 'models')
```

## Fix Applied

Changed default path to align with project architecture:
```python
# NEW - Correct path
models_directory = os.path.join(repo_root, 'workspace', 'projects')
```

## Project Directory Structure

According to `project_models.py`, each project has this structure:
```
workspace/projects/<project_name>/
├── project.shy           # Project metadata
├── models/              # ← Model files go here
├── pathways/            # Analysis pathways
├── simulations/         # Simulation results
├── exports/             # Exported data
└── metadata/            # Backups, etc.
```

## Current Behavior (After Fix)

### Save Dialog Default Location
1. **First save**: Opens in `workspace/projects/`
2. **Subsequent saves**: Opens in last used directory
3. User can navigate to create/use project subdirectories

### Example Flow
```
User: File → Save
Dialog opens in: /repo/workspace/projects/

User creates folder: MyProject/models/
Saves to: /repo/workspace/projects/MyProject/models/mymodel.shy

Next save opens in: /repo/workspace/projects/MyProject/models/
```

## Future Enhancement

For full project integration, we could:
1. Check if ProjectManager has a current project
2. Default to `current_project.get_models_dir()` if available
3. Fall back to `workspace/projects/` if no project active

```python
# Future enhancement pseudocode
from shypn.data.project_models import ProjectManager

def __init__(self, parent_window=None, models_directory=None):
    if models_directory is None:
        # Try to use current project's models directory
        manager = ProjectManager()
        if manager.current_project:
            models_directory = manager.current_project.get_models_dir()
        else:
            # Fall back to workspace/projects/
            repo_root = ...
            models_directory = os.path.join(repo_root, 'workspace', 'projects')
```

## Files Modified

1. **`src/shypn/file/netobj_persistency.py`**
   - Line ~76: Changed `'models'` to `'workspace', 'projects'`
   - Updated docstring to reflect new default
   - Updated example in `create_persistency_manager()` docstring

## Testing

Test the fix:
1. Launch app: `python3 src/shypn.py`
2. Create new model
3. File → Save
4. Verify dialog opens in `workspace/projects/`
5. Create a subdirectory if needed (e.g., `MyProject/models/`)
6. Save file
7. Next save should remember the subdirectory

## Related Files

- `src/shypn/data/project_models.py` - Defines project structure
- `src/shypn/file/netobj_persistency.py` - File operations (fixed)
- `src/shypn.py` - Creates persistency manager

## Summary

✅ **Fixed**: Save dialog now defaults to `workspace/projects/` instead of `models/`  
✅ **Architecture aligned**: Follows project-based organization  
✅ **User-friendly**: Remembers last directory, allows navigation  
🔮 **Future**: Could integrate with ProjectManager for automatic project detection
