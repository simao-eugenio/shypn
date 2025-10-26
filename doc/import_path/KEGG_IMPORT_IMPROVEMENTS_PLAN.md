# KEGG Import Flow Improvements Plan

**Date:** October 26, 2025  
**Status:** Planning Phase  
**Priority:** High  
**Related:** Apply successful SBML import patterns to KEGG workflow

## Executive Summary

Apply the successful automation, auto-save, and file organization patterns from the SBML import flow to the KEGG import workflow. The KEGG import currently lacks the one-click automation, auto-save functionality, and proper file organization that we implemented for SBML.

## Current KEGG Flow Analysis

### Current Implementation Location
- **File:** `src/shypn/helpers/kegg_import_panel.py`
- **Lines:** ~570 lines
- **Pattern:** Partial automation (fetch-and-import combined)

### Current Workflow
```
Enter pathway ID (e.g., "hsa00010") → Click Import
   ↓
Fetch from KEGG API (KGML format)
   ↓
Parse KGML
   ↓
Convert to Petri net
   ↓
Load to canvas
   ↓
DONE (but no auto-save, no PathwayDocument metadata)
```

### Current Issues

1. **No Auto-Save to project/pathways/**
   - Raw KGML files not saved to project structure
   - Missing for report generation and provenance

2. **No Auto-Save to project/models/**
   - Converted Petri net models not automatically saved
   - User must manually save after import

3. **No PathwayDocument Metadata**
   - No linking between raw KGML and Petri net model
   - Missing metadata tracking (source, timestamp, etc.)

4. **Browse Button Not Integrated**
   - Local file browsing exists but may not auto-save
   - Need to verify and enhance

5. **Inconsistent User Experience**
   - SBML: One-click with full automation
   - KEGG: Manual save required, no metadata

## Successful SBML Patterns to Apply

### 1. Auto-Save Raw Data Pattern
**SBML Implementation:** Lines 751-772 in `sbml_import_panel.py`

```python
# Save raw SBML to project/pathways/
if manager and manager.project_manager and manager.project_manager.current_project:
    project = manager.project_manager.current_project
    pathways_dir = os.path.join(project.root_path, 'pathways')
    os.makedirs(pathways_dir, exist_ok=True)
    
    # Generate filename from source
    base_name = os.path.splitext(filename)[0]
    pathway_filepath = os.path.join(pathways_dir, f"{base_name}.xml")
    
    # Copy/save raw file
    shutil.copy(source_path, pathway_filepath)
```

**KEGG Adaptation:**
- Save KGML data to `project/pathways/PATHWAY_ID.xml`
- Happens immediately after successful fetch
- Use pathway ID (e.g., "hsa00010") as filename

### 2. Auto-Save Petri Net Model Pattern
**SBML Implementation:** Lines 795-840 in `sbml_import_panel.py`

```python
# Auto-save Petri net model to project/models/
if manager and manager.project_manager and manager.project_manager.current_project:
    project = manager.project_manager.current_project
    models_dir = os.path.join(project.root_path, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Generate matching filename
    base_name = os.path.splitext(os.path.basename(raw_file))[0]
    model_filepath = os.path.join(models_dir, f"{base_name}.shy")
    
    # Create and save DocumentModel
    save_document = DocumentModel()
    save_document.places = list(manager.document_controller.places)
    save_document.transitions = list(manager.document_controller.transitions)
    save_document.arcs = list(manager.document_controller.arcs)
    save_document.save_to_file(model_filepath)
```

**KEGG Adaptation:**
- Save to `project/models/PATHWAY_ID.shy` after successful load
- Use same pathway ID as raw file for consistency
- Ensures both files have matching names

### 3. PathwayDocument Metadata Pattern
**SBML Implementation:** Lines 751-790 in `sbml_import_panel.py`

```python
from shypn.data.project_models import PathwayDocument

# Create metadata document
pathway_doc = PathwayDocument(
    source_type='kegg',
    source_id=pathway_id,
    raw_file=f'pathways/{pathway_id}.xml',
    model_file=f'models/{pathway_id}.shy',
    imported_date=datetime.now().isoformat()
)

# Link to project
if project.pathway_documents is None:
    project.pathway_documents = []
project.pathway_documents.append(pathway_doc)
project.save()
```

**KEGG Adaptation:**
- Set `source_type='kegg'`
- Use pathway ID as `source_id` (e.g., "hsa00010")
- Link raw KGML and converted model files
- Store fetch timestamp

### 4. Anti-Reentry Flag Pattern
**SBML Implementation:** Lines 97, 870-877, 885, 1188-1221

```python
# Initialize
self._auto_continuing = False

# Set when starting auto-workflow
self._auto_continuing = True
GLib.idle_add(lambda: next_step())

# Check at entry points
if self._auto_continuing:
    return  # Prevent re-entry

# Reset after completion
self._auto_continuing = False
```

**KEGG Note:**
- KEGG already has combined fetch-and-import in `_fetch_and_import()`
- May not need anti-reentry flag if no multi-step triggers
- Review for duplicate tab issues

## Implementation Plan

### Phase 1: Auto-Save Raw KGML (Priority: HIGH)
**Goal:** Save fetched KGML to `project/pathways/` automatically

**File:** `src/shypn/helpers/kegg_import_panel.py`

**Target Method:** `_on_fetch_complete_and_import()` (around line 318)

**Changes:**
1. After successful fetch and parse, check for project
2. Create `project/pathways/` directory if needed
3. Save `self.current_kgml` to `pathways/{pathway_id}.xml`
4. Log the save operation

**Estimated Lines:** +30 lines

**Dependencies:**
- `os`, `shutil` (already imported)
- Access to `self.project` (already available)

### Phase 2: Auto-Save Petri Net Model (Priority: HIGH)
**Goal:** Save converted model to `project/models/` automatically

**File:** `src/shypn/helpers/kegg_import_panel.py`

**Target Method:** `_on_import_complete()` (around line 370)

**Changes:**
1. After successful canvas load, check for project
2. Create `project/models/` directory if needed
3. Create DocumentModel from canvas netobjs
4. Save to `models/{pathway_id}.shy`
5. Log the save operation

**Estimated Lines:** +40 lines

**Dependencies:**
- `from shypn.data.canvas.document_model import DocumentModel`
- Access to `manager.document_controller` for netobjs

### Phase 3: PathwayDocument Metadata (Priority: MEDIUM)
**Goal:** Create metadata linking raw KGML and Petri net model

**File:** `src/shypn/helpers/kegg_import_panel.py`

**Target Method:** `_on_import_complete()` (after Phase 2 changes)

**Changes:**
1. Import `PathwayDocument` from `shypn.data.project_models`
2. Create PathwayDocument with:
   - `source_type='kegg'`
   - `source_id=pathway_id`
   - `raw_file='pathways/{pathway_id}.xml'`
   - `model_file='models/{pathway_id}.shy'`
   - `imported_date=datetime.now().isoformat()`
3. Add to `project.pathway_documents` list
4. Save project metadata

**Estimated Lines:** +25 lines

**Dependencies:**
- `from shypn.data.project_models import PathwayDocument`
- `from datetime import datetime`

### Phase 4: Browse Button Enhancement (Priority: LOW)
**Goal:** Ensure local KGML browsing also auto-saves

**File:** `src/shypn/helpers/kegg_import_panel.py`

**Target Method:** `_on_browse_clicked()` (needs review)

**Changes:**
1. Review current browse implementation
2. Ensure KGML file is copied to `project/pathways/`
3. Extract pathway ID from filename or KGML content
4. Apply same auto-save logic as fetch flow

**Estimated Lines:** +20 lines

**Note:** Need to determine pathway ID from local file

### Phase 5: Testing & Validation (Priority: HIGH)
**Goal:** Ensure KEGG import works like SBML import

**Test Cases:**
1. **Database Fetch Flow:**
   - Enter pathway ID "hsa00010"
   - Click Import (once)
   - Verify: KGML saved to `project/pathways/hsa00010.xml`
   - Verify: Model saved to `project/models/hsa00010.shy`
   - Verify: PathwayDocument created with links
   - Verify: Model loads on canvas
   - Verify: Only one tab created

2. **Local File Flow:**
   - Browse for local KGML file
   - Click Import
   - Verify: File copied to `project/pathways/`
   - Verify: Model auto-saved to `project/models/`
   - Verify: Metadata created

3. **Error Handling:**
   - Invalid pathway ID
   - Network failure
   - No project open
   - Parse errors

4. **File Operations:**
   - Verify files are readable
   - Verify proper permissions
   - Verify overwrite behavior

## Code Locations Reference

### Files to Modify
1. **`src/shypn/helpers/kegg_import_panel.py`**
   - Main implementation file
   - ~570 lines currently
   - Will grow to ~700 lines

### Methods to Modify
1. **`_on_fetch_complete_and_import()`** (Line ~318)
   - Add auto-save raw KGML logic
   
2. **`_on_import_complete()`** (Line ~370)
   - Add auto-save Petri net model logic
   - Add PathwayDocument metadata creation

3. **`_on_browse_clicked()`** (Location TBD)
   - Review and enhance for auto-save

4. **`__init__()`** (Line ~62)
   - Add `_auto_continuing` flag if needed
   - Initialize any new attributes

### New Imports Needed
```python
import shutil
from datetime import datetime
from shypn.data.project_models import PathwayDocument
from shypn.data.canvas.document_model import DocumentModel
```

## Success Criteria

### User Experience
- ✅ One-click import for KEGG pathways (same as SBML)
- ✅ No manual save required
- ✅ Consistent behavior between KEGG and SBML
- ✅ Clear status messages during import

### File Organization
- ✅ Raw KGML in `project/pathways/*.xml`
- ✅ Petri nets in `project/models/*.shy`
- ✅ Matching filenames based on pathway ID
- ✅ Proper directory creation

### Metadata
- ✅ PathwayDocument created for each import
- ✅ Links between raw and model files
- ✅ Source type, ID, and timestamp recorded
- ✅ Project metadata updated and saved

### Code Quality
- ✅ Debug logging throughout workflow
- ✅ Proper error handling
- ✅ No duplicate tabs created
- ✅ Consistent with SBML implementation

## Risk Assessment

### Low Risk
- ✅ Auto-save patterns proven in SBML
- ✅ File operations straightforward
- ✅ Clear separation of concerns

### Medium Risk
- ⚠️ Local file browse pathway ID extraction
- ⚠️ Overwrite behavior not defined
- ⚠️ Network failures during fetch

### Mitigation Strategies
1. **Pathway ID extraction:** Parse KGML header for pathway attribute
2. **Overwrite behavior:** Add timestamp suffix if file exists
3. **Network failures:** Robust error handling with retry option

## Timeline Estimate

### Phase 1: Auto-save KGML
- **Implementation:** 30 minutes
- **Testing:** 15 minutes
- **Total:** 45 minutes

### Phase 2: Auto-save Model
- **Implementation:** 45 minutes
- **Testing:** 20 minutes
- **Total:** 65 minutes

### Phase 3: Metadata
- **Implementation:** 30 minutes
- **Testing:** 15 minutes
- **Total:** 45 minutes

### Phase 4: Browse Enhancement
- **Implementation:** 30 minutes
- **Testing:** 20 minutes
- **Total:** 50 minutes

### Phase 5: Integration Testing
- **Testing:** 45 minutes
- **Documentation:** 15 minutes
- **Total:** 60 minutes

**Total Estimated Time:** ~4.5 hours

## Follow-Up Work

### After KEGG Implementation
1. **BRENDA Import Flow**
   - Apply same patterns to BRENDA import
   - Save enzyme data to `project/enzymes/`
   - Create EnzymeDocument metadata

2. **Unified Import Documentation**
   - Document consistent import patterns
   - Create developer guide for future imports
   - Example code snippets

3. **Import Report Generation**
   - Leverage PathwayDocument metadata
   - Generate import history reports
   - Track data provenance

4. **File Panel Integration**
   - Show imported pathways in file tree
   - Enable re-opening saved models
   - Link to original source data

## References

### Related Documentation
- `doc/import_path/SESSION_SUMMARY.md` - SBML implementation details
- `doc/import_path/SBML_IMPORT_FLOW_ANALYSIS.md` - Original flow analysis
- `doc/import_path/IMPORT_FLOW_FIX.md` - Import improvements

### Code References
- `src/shypn/helpers/sbml_import_panel.py` - Reference implementation
- `src/shypn/helpers/kegg_import_panel.py` - Target file
- `src/shypn/data/project_models.py` - PathwayDocument class

### Test References
- `tests/import_path/test_unified_import.py` - SBML import tests
- Future: `tests/import_path/test_kegg_import.py` - KEGG import tests

## Notes

- KEGG already has combined fetch-and-import, may be simpler than SBML
- Need to verify `model_canvas` manager access for document_controller
- Consider adding progress indicators for longer operations
- May need to handle KGML-specific edge cases

---

**Next Steps:**
1. Review current KEGG implementation in detail
2. Start with Phase 1 (auto-save KGML)
3. Test incrementally after each phase
4. Update this document with actual implementation details
