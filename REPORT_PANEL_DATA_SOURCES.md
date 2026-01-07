# Report Panel - Text Views/Labels and Data Sources

## Summary of All Categories and Their Data Sources

### 1. MODELS Category (`model_structure_category.py`)

**Labels:**
- `overview_label` - Model Overview
  - **Data Source:** `model._document_model.metadata['name']`, `model.name`, `model.file_path`
  - **Updated in:** `refresh()` method (lines 903-951)
  - **Gets:** Model name, project name, file path, creation date, modified date, description

- `structure_label` - Petri Net Structure  
  - **Data Source:** `len(model.places)`, `len(model.transitions)`, `len(model.arcs)`
  - **Updated in:** `refresh()` method (lines 953-1008)
  - **Gets:** Places count, transitions count, arcs count, model type (Stochastic/Continuous/Timed/Bio-PN)

- `provenance_label` - Import Provenance
  - **Data Source:** `pathway_doc` OR `model._document_model.metadata`
  - **Updated in:** `refresh()` method (lines 1010-1090)
  - **Gets from pathway_doc:** source_type, source_id, source_organism, imported_date, raw_file, species_count, reactions_count
  - **Gets from metadata (fallback):** source, source_type, source_id, pathway_id, organism, source_organism, imported_date, created, raw_file, original_file

**Issue:** Metadata is accessed via `model._document_model.metadata` (private attribute path)

---

### 2. TOPOLOGY ANALYSES Category (`topology_analyses_category.py`)

**Labels:**
- `status_label` - Analysis Status Summary
  - **Data Source:** `topology_panel.generate_summary_for_report_panel()`
  - **Updated in:** `_update_display()` method (line 355)
  - **Gets:** Emoji + status text based on analysis results

- `findings_label` - Key Findings
  - **Data Source:** `topology_panel.generate_summary_for_report_panel()['summary_lines']`
  - **Updated in:** `_update_display()` method (lines 358-361)
  - **Gets:** List of findings or "No significant findings"

**Tables (TreeView):**
- Structural Analysis Table - data from `statistics` dict
- Graph & Network Table - data from `statistics` dict  
- Behavioral Analysis Table - data from `statistics` dict
- Biological Analysis Table - data from `statistics` dict

**Issue:** Tables get data correctly from `statistics` dict keys

---

### 3. THERMODYNAMIC VALIDATION Category (`thermodynamic_validation_category.py`)

**Labels:**
- `status_label` - Validation Status
  - **Data Source:** `controller.thermodynamic_results`
  - **Updated in:** `refresh()` method (lines 238-243)
  - **Gets:** Emoji + validation counts (violations, warnings, valid)

- `summary_label` - Summary Statistics
  - **Data Source:** `controller.thermodynamic_results`
  - **Updated in:** `refresh()` method (lines 245-252)  
  - **Gets:** Total reactions, violations count, warnings count, valid count

- `settings_label` - Thermodynamic Settings
  - **Data Source:** `controller.thermodynamic_results['settings']`
  - **Updated in:** `refresh()` method (lines 254-267)
  - **Gets:** pH, temperature, ionic strength, tolerance, preset name

**Tables (TreeView):**
- Results Table - data from `controller.thermodynamic_results['violations']`, `['warnings']`, `['valid']`
- Compound Mappings Table - data from `controller.thermodynamic_results['compound_mappings']`

**Issue:** All working correctly

---

### 4. PROVENANCE & LINEAGE Category (`provenance_category.py`)

**Labels:**
- `summary_label` - Data Sources Summary
  - **Data Source:** `self.project.pathways.list_pathways()`
  - **Updated in:** `refresh()` method (lines 122-141)
  - **Gets:** Total pathways, KEGG count, SBML count, converted count, enriched count

**TextViews (with buffers):**
- `pipeline_buffer` - Transformation Pipeline
  - **Data Source:** `self.project.pathways.list_pathways()`
  - **Updated in:** `refresh()` method (line 148) via `_build_pipeline_text()`
  - **Gets:** List of imports with source, file, date, conversion status, enrichments

**Tables (TreeView):**
- Pathways Table - data from `self.project.pathways.list_pathways()`

**Issue:** All working correctly

---

### 5. PARAMETERS Category (`parameters_category.py`)

**Labels:**
- `summary_label` - Kinetic Parameters Summary
  - **Data Source:** `model.transitions` (counts parameters)
  - **Updated in:** `refresh()` method
  - **Gets:** Statistics about parameters across all transitions

- `simulation_status_label` - Simulation Status
  - **Data Source:** Not clearly connected to simulation controller
  - **Updated in:** `refresh()` method
  - **Gets:** Status text about simulation readiness

- `total_label`, `km_label`, `kcat_label`, `ki_label`, `vmax_label` - Parameter counts
  - **Data Source:** Transition parameters statistics
  - **Updated in:** `refresh()` method
  - **Gets:** Count of each parameter type

**Issue:** Needs review - may not be getting data from right place

---

### 6. SBML METADATA Category (`sbml_metadata_category.py`)

**Labels:**
- Header label - Model name
  - **Data Source:** SBML-specific metadata
  - **Updated in:** `refresh()` method
  - **Gets:** Model name from SBML metadata

- Description label - Model description  
  - **Data Source:** SBML-specific metadata
  - **Updated in:** `refresh()` method
  - **Gets:** Model description from SBML metadata

**Issue:** SBML-specific, may not apply to KEGG models

---

## Key Issues Found

### 1. **MODELS Category - Metadata Access**
```python
# CURRENT (accessing private attribute):
document_model = getattr(model, '_document_model', None)
metadata = getattr(document_model, 'metadata', {})

# NEEDED: Public property on ModelCanvasManager
@property
def metadata(self):
    return self._document_model.metadata if hasattr(self._document_model, 'metadata') else {}
```

### 2. **MODELS Category - Missing Data Population**
The `model._document_model.metadata` dictionary is populated during SBML/KEGG import but needs to ensure:
- `metadata['name']` is set from pathway name
- `metadata['source']` or `metadata['source_type']` is set (e.g., 'KEGG', 'SBML')
- `metadata['source_id']` is set from pathway ID
- `metadata['organism']` or `metadata['source_organism']` is set
- `metadata['imported_date']` or `metadata['created']` is set
- `metadata['raw_file']` is set to original file path

### 3. **Widget Visibility Issues**
All labels use:
```python
label.set_text(text)
label.show()
label.queue_draw()
```
This should force GTK to update, but labels may still not be visible if:
- Parent containers are not shown
- Label packing is incorrect
- Label size allocation is zero

### 4. **Data Flow Summary**

```
KEGG/SBML Import
    ↓
PathwayDocument (in project.pathways)
    ↓
Conversion to Model
    ↓
DocumentModel.metadata (persisted in .shypn file)
    ↓
ModelCanvasManager._document_model.metadata
    ↓
Report Panel Categories
```

## Recommendations

1. **Add public `metadata` property to ModelCanvasManager:**
   ```python
   @property
   def metadata(self):
       return self._document_model.metadata if hasattr(self._document_model, 'metadata') else {}
   ```

2. **Ensure metadata is populated during import** in pathway converter:
   - Set `metadata['name']` from pathway name
   - Set `metadata['source']` from pathway.source_type
   - Set `metadata['source_id']` from pathway.source_id
   - Set `metadata['organism']` from pathway.source_organism
   - Set `metadata['imported_date']` from pathway.imported_date

3. **Verify all refresh() methods are called** when:
   - Report panel is opened
   - Tab is switched
   - Model is loaded
   - Data changes

4. **Add debug logging** to track when labels are set vs when they should display
