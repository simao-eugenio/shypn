# API Folder Flattening Plan

**Date**: 2025-01-XX  
**Branch**: canvas-architecture-refactoring  
**Purpose**: Simplify directory structure by removing redundant `api/` intermediate folder

---

## Rationale

### Why Flatten?

1. **Simplifies Import Paths**
   - Current: `from shypn.api.netobjs.place import Place`
   - After: `from shypn.netobjs.place import Place`

2. **Removes Redundancy**
   - Everything under `src/shypn/` is already part of the API
   - The `api/` folder name doesn't add semantic value

3. **Cleaner Structure**
   - Prepares for new architecture additions (canvas/, controllers/, renderers/)
   - Avoids confusion about what "api" means vs actual package organization

4. **Better Organization**
   - `netobjs/` clearly indicates "network objects" (Petri net primitives)
   - `file/` clearly indicates "file operations"
   - No need for "api" grouping

---

## Current Structure

```
src/shypn/
├── api/
│   ├── __init__.py              # Re-exports from netobjs
│   ├── file/
│   │   ├── __init__.py          # Exports FileExplorer
│   │   └── explorer.py          # FileExplorer class (690 lines)
│   └── netobjs/
│       ├── __init__.py          # Exports all Petri net classes
│       ├── petri_net_object.py  # Base class
│       ├── place.py             # Place class
│       ├── transition.py        # Transition class
│       ├── arc.py               # Arc class
│       └── inhibitor_arc.py     # InhibitorArc class
├── data/
├── edit/
├── helpers/
├── ui/
└── utils/
```

---

## Target Structure

```
src/shypn/
├── file/                        # ← Moved from api/file/
│   ├── __init__.py
│   └── explorer.py
├── netobjs/                     # ← Moved from api/netobjs/
│   ├── __init__.py
│   ├── petri_net_object.py
│   ├── place.py
│   ├── transition.py
│   ├── arc.py
│   └── inhibitor_arc.py
├── data/
├── edit/
├── helpers/
├── ui/
└── utils/
```

**Note**: The `api/` folder will be completely removed.

---

## Import Changes Required

### 1. **Within netobjs/ Package (Internal Imports)**

**Files to Update**: 7 files

**File**: `src/shypn/netobjs/__init__.py`
```python
# OLD (imports from api.netobjs)
from shypn.api.netobjs.petri_net_object import PetriNetObject
from shypn.api.netobjs.place import Place
from shypn.api.netobjs.transition import Transition
from shypn.api.netobjs.arc import Arc
from shypn.api.netobjs.inhibitor_arc import InhibitorArc

# NEW (imports from netobjs directly)
from shypn.netobjs.petri_net_object import PetriNetObject
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
```

**File**: `src/shypn/netobjs/place.py`
```python
# OLD
from shypn.api.netobjs.petri_net_object import PetriNetObject

# NEW
from shypn.netobjs.petri_net_object import PetriNetObject
```

**File**: `src/shypn/netobjs/transition.py`
```python
# OLD
from shypn.api.netobjs.petri_net_object import PetriNetObject

# NEW
from shypn.netobjs.petri_net_object import PetriNetObject
```

**File**: `src/shypn/netobjs/arc.py` (3 import locations)
```python
# OLD
from shypn.api.netobjs.petri_net_object import PetriNetObject
# ... and in methods:
from shypn.api.netobjs.place import Place
from shypn.api.netobjs.transition import Transition

# NEW
from shypn.netobjs.petri_net_object import PetriNetObject
# ... and in methods:
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
```

**File**: `src/shypn/netobjs/inhibitor_arc.py`
```python
# Inherits from Arc, so similar changes as arc.py
```

---

### 2. **Code Files Using netobjs (External Imports)**

**Files to Update**: 4 files

**File**: `src/shypn/helpers/model_canvas_loader.py` (4 locations)
```python
# OLD
from shypn.netobjs import Place, Transition, Arc

# NEW (Option A: Import from netobjs package)
from shypn.netobjs import Place, Transition, Arc

# NEW (Option B: Direct imports)
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
```

**File**: `src/shypn/data/model_canvas_manager.py`
```python
# OLD
from shypn.api import Place, Arc, Transition

# NEW
from shypn.netobjs import Place, Arc, Transition
```

**File**: `src/shypn/edit/selection_manager.py`
```python
# OLD
from shypn.netobjs import Place, Transition, Arc

# NEW
from shypn.netobjs import Place, Transition, Arc
```

**File**: `src/shypn/edit/object_editing_transforms.py`
```python
# OLD
from shypn.netobjs import Place, Transition, Arc

# NEW
from shypn.netobjs import Place, Transition, Arc
```

**File**: `src/shypn/edit/rectangle_selection.py`
```python
# OLD
from shypn.netobjs import Place, Transition

# NEW
from shypn.netobjs import Place, Transition
```

---

### 3. **Code Files Using file/ Package**

**Files to Update**: 2 files

**File**: `src/shypn/ui/panels/file_explorer_panel.py`
```python
# OLD
from shypn.api.file import FileExplorer

# NEW
from shypn.file import FileExplorer
```

**File**: `tests/test_file_operations.py`
```python
# OLD
from shypn.api.file import FileExplorer

# NEW
from shypn.file import FileExplorer
```

---

### 4. **Documentation Files**

**Files to Update**: ~5 documentation files

These files contain example imports that should be updated for consistency:

- `doc/SELECTION_AND_TRANSFORMATION_PLAN.md`
- `doc/LOADER_RESPONSIBILITIES_ANALYSIS.md`
- `doc/IMPLEMENTATION_SUMMARY.md`
- `doc/TESTING_CHECKLIST.md`
- `doc/BUGFIX_MISSING_IMPORTS.md`
- `tests/README.md`

**Change Pattern**:
```python
# OLD
from shypn.netobjs import Place, Transition, Arc

# NEW
from shypn.netobjs import Place, Transition, Arc
```

---

## File Operations Summary

### Files to Move:
1. `src/shypn/api/netobjs/` → `src/shypn/netobjs/`
2. `src/shypn/api/file/` → `src/shypn/file/`

### Files to Delete:
1. `src/shypn/api/__init__.py` (no longer needed)
2. `src/shypn/api/` directory (after moving contents)

### Files to Update (Code):
1. `src/shypn/netobjs/__init__.py` - Internal imports
2. `src/shypn/netobjs/place.py` - Import PetriNetObject
3. `src/shypn/netobjs/transition.py` - Import PetriNetObject
4. `src/shypn/netobjs/arc.py` - Import PetriNetObject, Place, Transition
5. `src/shypn/netobjs/inhibitor_arc.py` - Similar to arc.py
6. `src/shypn/helpers/model_canvas_loader.py` - Change 4 import statements
7. `src/shypn/data/model_canvas_manager.py` - Change import
8. `src/shypn/edit/selection_manager.py` - Change import
9. `src/shypn/edit/object_editing_transforms.py` - Change import
10. `src/shypn/edit/rectangle_selection.py` - Change import
11. `src/shypn/ui/panels/file_explorer_panel.py` - Change import
12. `tests/test_file_operations.py` - Change import

**Total Code Files**: 12 files

### Files to Update (Documentation):
- `doc/SELECTION_AND_TRANSFORMATION_PLAN.md`
- `doc/LOADER_RESPONSIBILITIES_ANALYSIS.md`
- `doc/IMPLEMENTATION_SUMMARY.md`
- `doc/TESTING_CHECKLIST.md`
- `doc/BUGFIX_MISSING_IMPORTS.md`
- `tests/README.md`
- `src/shypn/README.md` (if exists)

**Total Doc Files**: ~7 files

---

## Step-by-Step Migration Procedure

### Phase 1: Move Directories
```bash
# Move netobjs
mv src/shypn/api/netobjs src/shypn/netobjs

# Move file
mv src/shypn/api/file src/shypn/file
```

### Phase 2: Update Internal Imports (within netobjs/)

**Order matters**: Update base class first, then derived classes

1. Update `src/shypn/netobjs/__init__.py`
2. Update `src/shypn/netobjs/petri_net_object.py` (no imports to change)
3. Update `src/shypn/netobjs/place.py`
4. Update `src/shypn/netobjs/transition.py`
5. Update `src/shypn/netobjs/arc.py`
6. Update `src/shypn/netobjs/inhibitor_arc.py`

### Phase 3: Update External Imports (code using netobjs)

7. Update `src/shypn/data/model_canvas_manager.py`
8. Update `src/shypn/helpers/model_canvas_loader.py`
9. Update `src/shypn/edit/selection_manager.py`
10. Update `src/shypn/edit/object_editing_transforms.py`
11. Update `src/shypn/edit/rectangle_selection.py`

### Phase 4: Update File Explorer Imports

12. Update `src/shypn/ui/panels/file_explorer_panel.py`
13. Update `tests/test_file_operations.py`

### Phase 5: Update Documentation

14. Update all documentation files with new import examples

### Phase 6: Remove api/ Directory
```bash
# Delete old api/__init__.py
rm src/shypn/api/__init__.py

# Remove api directory (should be empty now)
rmdir src/shypn/api
```

### Phase 7: Verify & Test

```bash
# Run tests
pytest tests/

# Check for any remaining old imports
grep -r "from shypn.api" src/
grep -r "from shypn.api" tests/

# Start application and test basic functionality
python -m shypn
```

---

## Impact Analysis

### Low Risk Areas ✅
- **Internal netobjs imports**: Isolated within netobjs/ package
- **File explorer**: Only 2 files importing it
- **Documentation**: No runtime impact

### Medium Risk Areas ⚠️
- **model_canvas_loader.py**: Large file (1,372 lines), 4 import locations
- **Selection system**: 3 files in edit/ package
- **Canvas manager**: Core data management file

### Testing Required
1. **Basic Import Tests**: Verify all modules can be imported
2. **Canvas Loading**: Test opening existing Petri net files
3. **Object Creation**: Test creating Places, Transitions, Arcs
4. **Selection System**: Test selecting/transforming objects
5. **File Explorer**: Test browsing files in UI

---

## Backward Compatibility

### Breaking Changes
- **External Code**: Any code outside this repository importing `from shypn.api.*` will break
- **Saved Scripts**: User scripts with old imports will need updating

### Migration Path for External Code
```python
# If external code exists, provide migration guide:

# OLD import style (will break)
from shypn.netobjs import Place, Transition, Arc
from shypn.api.file import FileExplorer

# NEW import style (use this)
from shypn.netobjs import Place, Transition, Arc
from shypn.file import FileExplorer
```

### Notes
- Since this is application code (not a published library), external compatibility is likely not a concern
- If there ARE external users, could keep `api/__init__.py` temporarily with deprecation warnings

---

## Rollback Plan

If issues arise after flattening:

1. **Git Revert**: 
   ```bash
   git revert HEAD
   ```

2. **Manual Rollback**:
   ```bash
   # Move directories back
   mkdir src/shypn/api
   mv src/shypn/netobjs src/shypn/api/netobjs
   mv src/shypn/file src/shypn/api/file
   
   # Restore api/__init__.py from git
   git checkout HEAD -- src/shypn/api/__init__.py
   
   # Revert all import changes
   git checkout HEAD -- src/shypn/helpers/
   git checkout HEAD -- src/shypn/data/
   git checkout HEAD -- src/shypn/edit/
   git checkout HEAD -- src/shypn/ui/
   ```

---

## Post-Flattening Benefits

After this flattening is complete:

1. **Cleaner Imports**
   ```python
   from shypn.netobjs import Place, Transition, Arc
   from shypn.file import FileExplorer
   from shypn.edit import SelectionManager
   from shypn.data.canvas import DocumentCanvas  # Future
   ```

2. **Logical Structure**
   ```
   src/shypn/
   ├── netobjs/      # Petri net domain objects
   ├── file/         # File operations
   ├── edit/         # Editing support
   ├── data/         # Data management
   │   └── canvas/   # (Future) Canvas architecture
   ├── controllers/  # (Future) Interaction controllers
   ├── renderers/    # (Future) Rendering system
   └── ui/           # UI components
   ```

3. **Ready for New Architecture**
   - Clear separation between domain (netobjs), data (canvas), editing, rendering
   - No ambiguity about where new code should go
   - Import paths clearly indicate module purpose

---

## Timeline Estimate

- **Phase 1-2** (Move + Internal): ~15 minutes
- **Phase 3-4** (External + File): ~20 minutes
- **Phase 5** (Documentation): ~10 minutes
- **Phase 6-7** (Cleanup + Verify): ~15 minutes

**Total**: ~60 minutes

---

## Approval Checklist

Before executing this plan:

- [ ] Review all files listed for updates
- [ ] Confirm no external dependencies on `shypn.api.*` imports
- [ ] Backup current branch state
- [ ] Ensure all current tests pass
- [ ] Confirm this is desired structure
- [ ] Ready to execute migration

---

## Next Steps After Flattening

Once API flattening is complete:

1. **Commit Changes**
   ```bash
   git add -A
   git commit -m "Flatten API structure: move netobjs/ and file/ up one level"
   git push origin canvas-architecture-refactoring
   ```

2. **Proceed with Canvas Architecture**
   - Create `src/shypn/data/canvas/` structure
   - Implement DocumentCanvas, DocumentModel, CanvasState
   - Create controllers and tools under `src/shypn/controllers/`
   - Create renderers under `src/shypn/renderers/`
   - Refactor model_canvas_loader.py

3. **Update Documentation**
   - Update CANVAS_ARCHITECTURE_REVISION_PLAN.md with new import paths
   - Update CANVAS_STRUCTURE_NAMING_PLAN.md with actual implementation
   - Create migration guide if needed

---

## Questions to Resolve

1. **Prefer**: `from shypn.netobjs import Place` or `from shypn.netobjs.place import Place`?
   - Recommendation: Use package-level imports (`from shypn.netobjs import Place`)
   - Reason: Shorter, cleaner, matches how we currently use `from shypn.api import Place`

2. **Keep** `netobjs/__init__.py` exporting all classes?
   - Recommendation: Yes
   - Reason: Allows convenient `from shypn.netobjs import Place, Transition, Arc`

3. **Documentation** update priority?
   - Recommendation: Update inline with code changes
   - Reason: Keeps docs accurate, minimal extra effort

---

## Conclusion

This flattening operation is a **logical simplification** that:
- Removes unnecessary directory nesting
- Clarifies package structure
- Simplifies imports throughout the codebase
- Prepares for upcoming canvas architecture implementation

**Risk Level**: Low-Medium (systematic import changes across 12 code files)  
**Benefit**: High (cleaner structure, simpler imports, better organization)  
**Recommendation**: Proceed with migration
