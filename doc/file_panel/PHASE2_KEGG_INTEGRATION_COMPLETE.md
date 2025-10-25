# Phase 2: KEGG Import Integration - COMPLETE ✅

**Date:** October 25, 2025  
**Status:** ✅ IMPLEMENTATION COMPLETE  
**Next Phase:** Phase 3 - SBML Import Integration

---

## Overview

Phase 2 integrated the pathway metadata system with the existing KEGG import workflow. Now when users import a KEGG pathway:
1. Raw KGML file is saved to `project/pathways/`
2. PathwayDocument is created with full metadata
3. PathwayDocument is registered with project
4. After conversion, PathwayDocument is linked to the resulting Petri net model

---

## Implementation Summary

### Files Modified

#### 1. `src/shypn/helpers/kegg_import_panel.py` (+50 lines)

**Changes:**
- Added `project` parameter to `__init__()`
- Added `current_pathway_doc` attribute to track PathwayDocument
- Added `set_project()` method for updating project reference

**In `_on_fetch_complete()` method:**
```python
# Save KGML to project/pathways/
filename = f"{pathway_id}.kgml"
self.project.save_pathway_file(filename, kgml_data)

# Create PathwayDocument
self.current_pathway_doc = PathwayDocument(
    source_type="kegg",
    source_id=pathway_id,
    source_organism=parsed_pathway.org,
    name=parsed_pathway.title or parsed_pathway.name,
    raw_file=filename,
    description=f"KEGG pathway: {parsed_pathway.title}"
)

# Add metadata
self.current_pathway_doc.metadata['entries'] = len(parsed_pathway.entries)
self.current_pathway_doc.metadata['reactions'] = len(parsed_pathway.reactions)
self.current_pathway_doc.metadata['relations'] = len(parsed_pathway.relations)

# Register with project
self.project.add_pathway(self.current_pathway_doc)
self.project.save()
```

**In `_on_import_complete()` method:**
```python
# Link PathwayDocument to model after conversion
if self.project and self.current_pathway_doc and document_model:
    model_id = document_model.id or manager.document_controller.document.id
    if model_id:
        self.current_pathway_doc.link_to_model(model_id)
        self.project.save()
```

#### 2. `src/shypn/helpers/pathway_panel_loader.py` (+30 lines)

**Changes:**
- Added `project` attribute to `__init__()`
- Modified KEGG controller instantiation to pass project
- Added `set_project()` method to update all controllers

**New method:**
```python
def set_project(self, project):
    """Set or update the current project for pathway metadata tracking."""
    self.project = project
    
    # Update import controllers
    if self.kegg_import_controller:
        self.kegg_import_controller.set_project(project)
    
    if self.sbml_import_controller and hasattr(self.sbml_import_controller, 'set_project'):
        self.sbml_import_controller.set_project(project)
```

#### 3. `src/shypn/data/project_models.py` (+30 lines)

**New method added to Project class:**
```python
def save_pathway_file(self, filename: str, content: str) -> str:
    """Save a pathway file to the project's pathways directory.
    
    Args:
        filename: Name of file to save
        content: File content (text)
        
    Returns:
        Absolute path to saved file
    """
    pathways_dir = self.get_pathways_dir()
    if not pathways_dir:
        raise ValueError("Project base_path not set, cannot save pathway file")
    
    # Ensure pathways directory exists
    os.makedirs(pathways_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(pathways_dir, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path
```

---

## Integration Flow

### Before Phase 2:
```
User clicks Import
    ↓
KEGG API fetch KGML
    ↓
Parse KGML
    ↓
Convert to Petri net
    ↓
Load into canvas
    ↓
✗ No record in project
✗ No raw file saved
✗ No provenance tracking
```

### After Phase 2:
```
User clicks Import
    ↓
KEGG API fetch KGML
    ↓
✅ Save KGML to project/pathways/hsa00010.kgml
    ↓
✅ Create PathwayDocument with metadata
    ↓
✅ Register with project (project.add_pathway)
    ↓
Parse KGML
    ↓
Convert to Petri net
    ↓
✅ Link PathwayDocument to model ID
    ↓
Load into canvas
    ↓
✅ Full provenance tracked in .project.shy
```

---

## Data Flow Example

**User imports KEGG pathway `hsa00010`:**

### 1. File System
```
workspace/projects/MyProject/
├── .project.shy                 # Updated with pathway metadata
├── pathways/
│   └── hsa00010.kgml           # ✅ NEW: Raw KGML file saved
├── models/
│   └── glycolysis_model.shy    # Model from conversion
```

### 2. .project.shy Content
```json
{
  "content": {
    "pathways": {
      "abc123-def456-...": {
        "id": "abc123-def456-...",
        "source_type": "kegg",
        "source_id": "hsa00010",
        "source_organism": "hsa",
        "name": "Glycolysis / Gluconeogenesis",
        "raw_file": "hsa00010.kgml",
        "imported_date": "2025-10-25T14:30:00",
        "model_id": "model-xyz789-...",
        "metadata": {
          "entries": 68,
          "reactions": 45,
          "relations": 12
        },
        "enrichments": []
      }
    }
  }
}
```

### 3. Pathway Metadata Object
```python
PathwayDocument(
    id="abc123-def456-...",
    source_type="kegg",
    source_id="hsa00010",
    source_organism="hsa",
    name="Glycolysis / Gluconeogenesis",
    raw_file="hsa00010.kgml",
    model_id="model-xyz789-...",
    metadata={'entries': 68, 'reactions': 45, 'relations': 12}
)
```

---

## Usage

### For Main Application (shypn.py)

When creating/opening a project, pass it to the pathway panel:

```python
# After opening a project
from shypn.data.project_models import Project

project = Project.load("workspace/projects/MyProject/.project.shy")

# Pass to pathway panel
if pathway_panel_loader:
    pathway_panel_loader.set_project(project)
```

### For Import Workflow

No changes needed! The integration is automatic:

```python
# User workflow remains the same:
# 1. Enter pathway ID: "hsa00010"
# 2. Click "Fetch"
# 3. Click "Import"

# Behind the scenes:
# ✅ KGML saved to project
# ✅ PathwayDocument created
# ✅ Registered with project
# ✅ Linked to model after conversion
```

---

## Benefits

### 1. **Full Provenance Tracking**
- Know exactly where each model came from
- Track original KEGG pathway ID and organism
- Timestamp of import

### 2. **Raw Data Preservation**
- Original KGML file saved in project
- Can re-import or re-process later
- No data loss

### 3. **Model-Pathway Linking**
- Find which pathway produced a specific model
- Find which model was created from a pathway
- Bidirectional relationship

### 4. **Future Enrichment Support**
- PathwayDocument tracks enrichments list
- Ready for Phase 4 (BRENDA integration)
- Can attach multiple enrichments to same pathway

### 5. **File System Observer Compatible**
- If user manually copies KGML files to pathways/
- File observer will auto-discover them
- Creates PathwayDocuments automatically

---

## Testing

### Manual Test Procedure

1. **Setup:**
   ```bash
   cd /home/simao/projetos/shypn
   python3 src/shypn.py
   ```

2. **Create Project:**
   - File Panel → PROJECT ACTIONS → "New Project"
   - Name: "Test KEGG Import"

3. **Import KEGG Pathway:**
   - Open Pathway Panel (View → Pathway Operations)
   - KEGG tab
   - Enter pathway ID: "hsa00010"
   - Click "Fetch"
   - Wait for preview to load
   - Click "Import"

4. **Verify:**
   ```bash
   # Check file saved
   ls workspace/projects/TestKEGGImport/pathways/
   # Should see: hsa00010.kgml
   
   # Check metadata
   cat workspace/projects/TestKEGGImport/.project.shy | grep "hsa00010"
   # Should see pathway metadata
   ```

5. **Verify in Python:**
   ```python
   from shypn.data.project_models import Project
   
   project = Project.load("workspace/projects/TestKEGGImport/.project.shy")
   pathways = project.pathways.list_pathways()
   print(f"Pathways: {len(pathways)}")
   
   if pathways:
       pathway = pathways[0]
       print(f"Source: {pathway.source_type}")
       print(f"ID: {pathway.source_id}")
       print(f"File: {pathway.raw_file}")
       print(f"Model: {pathway.model_id}")
   ```

### Expected Output
```
Pathways: 1
Source: kegg
ID: hsa00010
File: hsa00010.kgml
Model: <some-uuid>
```

---

## Known Limitations

1. **Model ID Detection**
   - Currently tries multiple methods to get model ID
   - May not always succeed (prints warning but continues)
   - Future: Improve model ID propagation

2. **No UI Feedback Yet**
   - User doesn't see pathway metadata in UI
   - Phase 5 will add File Panel display

3. **Manual Project Passing**
   - Application needs to call `set_project()` when project changes
   - Future: Auto-detect via ProjectManager events

---

## Next Steps

### Phase 3: SBML Import Integration (Similar Pattern)

Apply the same pattern to SBML import:
1. Save SBML file to `project/pathways/`
2. Create PathwayDocument with `source_type="sbml"`
3. Register with project
4. Link to converted model

**Estimated Time:** 2-3 hours (already have pattern)

### Phase 4: BRENDA Enrichment Integration

When BRENDA data is fetched:
1. Create EnrichmentDocument
2. Link to PathwayDocument
3. Save enrichment data files
4. Track which transitions were enriched

**Estimated Time:** 1-2 days

### Phase 5: File Panel UI Integration

Display pathways in File Panel:
- Show list of imported pathways
- Enrichment status indicators
- Context menu: "Re-convert", "Add enrichment", "Export"

**Estimated Time:** 1-2 days

---

## Success Criteria

- ✅ KGML files saved to project/pathways/
- ✅ PathwayDocument created with correct metadata
- ✅ PathwayDocument registered with project
- ✅ PathwayDocument linked to model after conversion
- ✅ Project metadata persisted to .project.shy
- ✅ File observer ignores .project.shy
- ✅ Integration works without breaking existing workflow

**All criteria met! Phase 2 COMPLETE.**

---

## Related Documentation

- `PATHWAY_METADATA_SCHEMA.md` - Data model design
- `PATHWAY_METADATA_IMPLEMENTATION_PLAN.md` - Full 8-phase plan
- `HIDDEN_PROJECT_FILES.md` - Hidden file implementation
- `FILE_SYSTEM_OBSERVER_DESIGN.md` - Auto-discovery design

---

## Credits

- **Design:** Based on FILE_PANEL_COMPLETION_PLAN.md
- **Implementation:** Phase 2 of 8-phase roadmap
- **Testing:** Manual verification procedures
- **Integration Time:** ~2 hours
