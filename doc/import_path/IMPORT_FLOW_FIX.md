# Import Flow Fix: Delayed File Saving

## Problem

The introduction of local pathway file storage (PathwayDocument + raw file saving) compromised the KEGG and SBML import flows by saving files **too early** in the pipeline:

**KEGG (Before Fix):**
```
1. Fetch from API → Save raw KGML file + Create PathwayDocument
2. User clicks Import → Parse → Convert → Load to canvas
```

**SBML (Before Fix):**
```
1. Browse for file → Save raw SBML file + Create PathwayDocument  
2. User clicks Parse → Parse → Validate → Post-process
3. User clicks Load → Convert → Load to canvas
```

### Issues This Caused

1. **Stale Metadata:** If user cancels import, PathwayDocument and raw file exist without corresponding model
2. **Inconsistent State:** Project references pathway that's not on canvas
3. **Confusion:** Files saved before user commits to importing
4. **Error Handling:** If import fails, cleanup becomes complex

## Solution

Move file saving and PathwayDocument creation to **AFTER** successful canvas load:

**KEGG (After Fix):**
```
1. Fetch from API → Store in memory only
2. User clicks Import → Parse → Convert → Load to canvas
3. SUCCESS → Save raw KGML file + Create PathwayDocument + Link to model
```

**SBML (After Fix):**
```
1. Browse for file → Store filepath only
2. User clicks Parse → Parse → Validate → Post-process
3. User clicks Load → Convert → Load to canvas
4. SUCCESS → Save raw SBML file + Create PathwayDocument + Link to model
```

### Benefits

1. **Atomic Import:** Files only saved if import succeeds completely
2. **Clean Cancellation:** User can cancel without leaving orphaned files
3. **Better Error Handling:** No cleanup needed if import fails
4. **Consistent State:** PathwayDocument always has corresponding model on canvas

## Changes Made

### KEGG Import Panel (`src/shypn/helpers/kegg_import_panel.py`)

**1. `__init__` method (line ~79):**
- Added `self.current_pathway_id = None` to store pathway ID for later saving

**2. `_on_fetch_complete` method (lines ~191-207):**
- **REMOVED:** File saving, PathwayDocument creation, project registration
- **KEPT:** Store parsed data in memory, enable Import button
- **ADDED:** Store `self.current_pathway_id` for later use

**3. `_on_import_complete` method (lines ~362-410):**
- **ADDED:** After successful canvas load:
  - Save raw KGML file to project/pathways/
  - Create PathwayDocument with metadata
  - Link PathwayDocument to model
  - Register with project and save
- **REMOVED:** Old linking code that assumed PathwayDocument already existed

### SBML Import Panel (`src/shypn/helpers/sbml_import_panel.py`)

**1. `_on_browse_clicked` method (lines ~330-369):**
- **REMOVED:** File copying, PathwayDocument creation, project registration
- **KEPT:** Store filepath, enable Parse button

**2. `_on_load_complete` method (lines ~650-700):**
- **ADDED:** After successful canvas load:
  - Copy SBML file to project/pathways/
  - Create PathwayDocument with metadata
  - Link PathwayDocument to model
  - Register with project and save
- **REMOVED:** Old linking code that assumed PathwayDocument already existed

## Testing Checklist

### Manual Testing

- [ ] **KEGG Import Success:**
  1. Open project
  2. Fetch KEGG pathway (e.g., hsa04110)
  3. Click Import with options
  4. Verify pathway loads to canvas
  5. Check File Panel shows `.kgml` file in project/pathways/
  6. Verify Report Panel can access pathway metadata

- [ ] **KEGG Import Cancellation:**
  1. Open project
  2. Fetch KEGG pathway
  3. Close panel without importing
  4. Verify NO `.kgml` file in project/pathways/
  5. Verify NO orphaned PathwayDocument in project

- [ ] **SBML Import Success:**
  1. Open project
  2. Browse for SBML file
  3. Click Parse
  4. Click Load to Canvas
  5. Verify pathway loads to canvas
  6. Check File Panel shows `.sbml`/`.xml` file in project/pathways/
  7. Verify Report Panel can access pathway metadata

- [ ] **SBML Import Cancellation:**
  1. Open project
  2. Browse for SBML file
  3. Close panel without parsing/loading
  4. Verify NO copied file in project/pathways/
  5. Verify NO orphaned PathwayDocument in project

### Error Cases

- [ ] **KEGG Import Failure:** If conversion fails, no files saved
- [ ] **SBML Parse Failure:** If parsing fails, no files saved
- [ ] **Project Save Failure:** Import succeeds even if metadata save fails (with warning)

### Integration Tests

- [ ] **File Panel Integration:**
  - Imported pathways show in File Panel
  - Can open pathway from File Panel
  - Raw files correctly stored in project/pathways/

- [ ] **Report Panel Integration:**
  - Report Panel can access PathwayDocument metadata
  - Statistics show correct source_type (kegg/sbml)
  - Provenance tracking works correctly

## Code Patterns

### Pattern: Delayed Save

**Before (WRONG):**
```python
def _on_fetch_complete(self, data):
    self.project.save_pathway_file(filename, data)  # ❌ Too early!
    self.current_pathway_doc = PathwayDocument(...)
    self.project.add_pathway(self.current_pathway_doc)
```

**After (CORRECT):**
```python
def _on_fetch_complete(self, data):
    self.current_data = data  # ✅ Store in memory
    
def _on_import_complete(self, model):
    # ... load to canvas ...
    if success:
        self.project.save_pathway_file(filename, self.current_data)  # ✅ Save after success
        self.current_pathway_doc = PathwayDocument(...)
        self.project.add_pathway(self.current_pathway_doc)
```

### Pattern: Atomic Import with Cleanup

```python
def _on_import_complete(self, document_model):
    try:
        # Load to canvas
        manager.load_objects(places=..., transitions=..., arcs=...)
        
        # SUCCESS - now save metadata
        if self.project:
            self.project.save_pathway_file(filename, data)
            pathway_doc = PathwayDocument(...)
            pathway_doc.link_to_model(model_id)
            self.project.add_pathway(pathway_doc)
            self.project.save()
            
    except Exception as e:
        # Import failed - no cleanup needed because nothing was saved!
        self._show_status(f"Import failed: {e}", error=True)
```

## Related Documentation

- **Project Management:** `src/shypn/data/project.py` - Project.save_pathway_file()
- **Pathway Metadata:** `src/shypn/data/pathway_document.py` - PathwayDocument class
- **KEGG Pipeline:** `src/shypn/importer/kegg/` - API client, parser, converter
- **SBML Pipeline:** `src/shypn/data/pathway/` - Parser, validator, postprocessor, converter

## Future Improvements

1. **Progress Feedback:** Show progress indicator during save (especially for large SBML files)
2. **Undo Support:** Allow user to undo import (remove from canvas + delete saved files)
3. **Duplicate Detection:** Check if pathway already imported before saving
4. **Batch Import:** Support importing multiple pathways at once
5. **Import History:** Track import timestamps and user actions in PathwayDocument

## Notes

- This fix maintains backward compatibility - existing PathwayDocuments in projects are unaffected
- The fix follows the principle of "late binding" - commit changes only when operation succeeds
- Error handling is simplified because early failures don't require cleanup
- The pattern can be applied to other import/export operations in the codebase
