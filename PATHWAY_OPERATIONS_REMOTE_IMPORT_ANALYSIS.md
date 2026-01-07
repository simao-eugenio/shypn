# Pathway Operations Remote Import Flow Analysis

Analysis of how remote imports work for KEGG, SBML (BioModels), and BiGG categories, focusing on when/how metadata inspector gets populated.

---

## Common Pattern: Single "Import/Fetch" Button

All three categories follow a **single-button workflow**:
- User enters accession ID (e.g., "hsa00010", "BIOMD0000000061", "iML1515")
- User clicks ONE button ("Save to Project" for KEGG/SBML, "Import to Project" for BiGG)
- System does everything: fetch → parse → convert → populate metadata → save → load to canvas

---

## 1. KEGG Category Remote Flow

### Button Label
- **"Save to Project"** (line 319 in kegg_category.py)

### Flow Trigger
```python
def _on_import_button_clicked(self, button):
    # Line 730: Remote mode
    pathway_id = input_text
    self._show_progress(f"Fetching pathway {pathway_id} from KEGG...")
    self._fetch_and_import_remote(pathway_id)
```

### Background Thread Execution
**Method**: `_fetch_and_import_remote()` (line 964)

**Steps** (all in background thread):
1. **Fetch KGML from KEGG API**
   ```python
   kgml_data = self.api_client.fetch_kgml(pathway_id)
   ```

2. **Parse KGML**
   ```python
   parsed_pathway = self.parser.parse(kgml_data)
   ```

3. **User Choice Dialog** (if reversible reactions detected)
   - Shows dialog on main thread via `GLib.idle_add()`
   - Waits for user choice (convert to continuous/hybrid or proceed)
   - Stores choice in `parsed_pathway.metadata['user_choice_transition_type']`

4. **Validation** (check for reactions - signaling-only pathways rejected)

5. **Convert to Petri Net**
   ```python
   document_model = convert_pathway_enhanced(
       parsed_pathway,
       coordinate_scale=2.5,
       include_cofactors=True,
       filter_isolated_compounds=True,
       create_enzyme_places=True,
       enhancement_options=enhancement_options
   )
   ```

6. **Return result dict**
   ```python
   return {
       'pathway_id': pathway_id,
       'kgml_data': kgml_data,
       'parsed_pathway': parsed_pathway,
       'document_model': document_model,
       'coordinate_scale': 2.5,
       'source': 'remote'
   }
   ```

### Main Thread Post-Processing
**Method**: `_on_import_thread_complete(result)` (line 1093)

**When Metadata Inspector Gets Populated**:
1. **Update Preview** (line 1104)
   ```python
   self._update_preview(parsed_pathway)
   ```
   - This populates the preview text buffer with pathway summary

2. **Update Metadata Tree** (happens inside `_update_preview`)
   ```python
   # Called from _update_preview → _update_metadata_tree_from_parsed()
   # Populates 6-column TreeStore with KEGG pathway metadata
   ```

3. **Save to Project** (line 1116)
   ```python
   saved_filepath = self._save_to_project(pathway_id, kgml_data, 
                                          parsed_pathway, document_model, 
                                          coordinate_scale)
   ```
   - Saves .kgml, .json (parsed), .shypn (petri net) files

4. **Auto-Load to Canvas** (line 1124+)
   ```python
   canvas_loader = self._get_canvas_loader()
   # Creates new document tab with the model
   ```

5. **Store Metadata in Document** (line 1177+)
   ```python
   document_model.metadata['kegg_import'] = True
   document_model.metadata['pathway_id'] = pathway_id
   document_model.metadata['kgml_data'] = kegg_metadata_dict
   ```

### Key Insight
- **Metadata inspector populated DURING `_on_import_thread_complete()`**
- Happens via `_update_preview()` which calls `_update_metadata_tree_from_parsed()`
- This is POST-PROCESSING after background thread completes
- Tree is auto-expanded after population

---

## 2. SBML Category Remote Flow (BioModels)

### Button Label
- **"Save to Project"** (line 141 in sbml_category.py)

### Flow Trigger
```python
def _on_import_button_clicked(self, button):
    # Determines if fetching from BioModels or using local file
    # For remote: calls _run_sbml_import_in_background()
```

### Background Thread Execution
**Method**: `_run_sbml_import_in_background()` (around line 1400+)

**Steps** (all in background thread):
1. **Fetch SBML from BioModels API** (if remote mode)
   ```python
   filepath = biomodels_fetcher.fetch_model(biomodels_id)
   ```

2. **Parse SBML**
   ```python
   pathway_data = self.parser.parse_file(filepath)
   ```

3. **Validate**
   ```python
   validation_result = self.validator.validate(pathway_data)
   ```

4. **Get Layout Options** (from UI controls)
   - Algorithm: hierarchical or force_directed
   - Parameters: layer_spacing, node_spacing, iterations, etc.

5. **Convert to Petri Net** (via PathwayConverter)
   ```python
   document_model = self.converter.convert(
       processed_data,
       layout_options=layout_options
   )
   ```

6. **Return result**
   ```python
   return {
       'filepath': filepath,
       'parsed_pathway': pathway_data,
       'document_model': document_model
   }
   ```

### Main Thread Post-Processing
**Method**: `_on_sbml_import_complete(result)` (line ~1580+)

**When Metadata Inspector Gets Populated**:
1. **Update Metadata Tree** (explicit call)
   ```python
   # Populate metadata inspector with parsed SBML data
   self._update_metadata_tree_from_parsed(parsed_pathway)
   self.metadata_expander.set_expanded(True)
   ```

2. **Save to Project**
   ```python
   saved_filepath = self._save_to_project(...)
   ```

3. **Auto-Load to Canvas**
   ```python
   self._auto_load_to_canvas(document_model, saved_filepath)
   ```

4. **Compound Mapping** (thermodynamics preparation)
   ```python
   # Map species to thermodynamic database
   mappings, confidences = mapper_service.map_all_places(document_model)
   ```

5. **Store Metadata in Document** (happens in _save_to_project or before load)
   ```python
   document_model.metadata['sbml_import'] = True
   document_model.metadata['biomodels_id'] = biomodels_id
   document_model.metadata['sbml_data'] = sbml_metadata_dict
   ```

### Key Insight
- **Metadata inspector populated DURING `_on_sbml_import_complete()`**
- Explicit call to `_update_metadata_tree_from_parsed()` after background thread
- Tree is auto-expanded immediately after population
- Similar pattern to KEGG but with additional validation/layout steps

---

## 3. BiGG Category Remote Flow

### Button Label
- **"Import to Project"** (line 179 in bigg_category.py)

### Flow Trigger
```python
def _on_import_clicked(self, button):
    # Line 665: Starts import
    self.import_button.set_sensitive(False)
    # Launches import_thread()
```

### Background Thread Execution
**Method**: `import_thread()` (line 677, inside `_on_import_clicked`)

**Steps** (all in background thread):
1. **Download SBML from BiGG API** (or use local file)
   ```python
   sbml_path = self.downloader.download_sbml(
       model_id=model_id,
       use_cache=use_cache
   )
   ```

2. **Check for Cached Parse** (optimization)
   ```python
   if (hasattr(self, 'parsed_pathway') and self.parsed_pathway and 
       hasattr(self, 'current_filepath') and self.current_filepath == sbml_path):
       parsed_pathway = self.parsed_pathway  # Reuse from preview!
   else:
       parsed_pathway = self.sbml_parser.parse_file(sbml_path)
   ```

3. **Update SBML Metadata Inspector** (on main thread via GLib.idle_add)
   ```python
   GLib.idle_add(self._update_sbml_metadata_view, parsed_pathway)
   ```
   ⚠️ **KEY POINT**: Metadata populated HERE, during background thread execution!

4. **Post-Process**
   ```python
   processed_pathway = self.postprocessor.process(parsed_pathway)
   ```

5. **Convert to Petri Net**
   ```python
   document_model = self.converter.convert(processed_pathway)
   ```

6. **Add Metadata to Document**
   ```python
   document_model.metadata['source'] = 'bigg_import'
   document_model.metadata['model_id'] = model_id
   
   # Save minimal SBML data for metadata inspector
   bigg_sbml_data = {
       'model_id': model_id,
       'compartments_count': len(parsed_pathway.compartments),
       'species_count': len(parsed_pathway.species),
       'reactions_count': len(parsed_pathway.reactions),
       'parameters_count': len(parsed_pathway.parameters)
   }
   document_model.metadata['bigg_sbml_data'] = bigg_sbml_data
   ```

7. **Signal Classification** (if enabled)
   ```python
   if classify_energy:
       classified_places = self.classifier.classify_energy_signals(document_model.places)
   ```

8. **Module Creation** (BiGG-specific: compartment modules)
   ```python
   modules = self.compartment_processor.create_modules_from_compartments(...)
   ```

9. **Return result**
   ```python
   GLib.idle_add(self._on_import_complete, result)
   ```

### Main Thread Post-Processing
**Method**: `_on_import_complete(result)` (line 877)

**When Metadata Inspector Gets Populated**:
- **ALREADY POPULATED** during background thread via `GLib.idle_add(self._update_sbml_metadata_view, parsed_pathway)` at line 713!
- Main thread only does:
  1. Save to project
  2. Auto-load to canvas
  3. Notify callbacks

### Key Insight
- **BiGG is DIFFERENT**: Metadata inspector populated **DURING background thread**
- Uses `GLib.idle_add()` to schedule UI update from background thread
- This is **earlier** than KEGG/SBML which do it in post-processing callback
- More efficient but requires thread-safe UI updates

---

## Summary Table

| Category | Button Label | Fetch Method | Parse Method | Metadata Population Point | Thread Safety |
|----------|-------------|--------------|--------------|---------------------------|---------------|
| **KEGG** | "Save to Project" | `api_client.fetch_kgml()` | `parser.parse()` | Main thread, inside `_on_import_thread_complete()` via `_update_preview()` | Safe (main thread) |
| **SBML** | "Save to Project" | `biomodels_fetcher.fetch_model()` | `parser.parse_file()` | Main thread, inside `_on_sbml_import_complete()` via explicit call | Safe (main thread) |
| **BiGG** | "Import to Project" | `downloader.download_sbml()` | `sbml_parser.parse_file()` | Background thread, via `GLib.idle_add(self._update_sbml_metadata_view, ...)` | Safe (GLib.idle_add) |

---

## Common Post-Processing Pattern

All three categories follow this **post-processing sequence**:

1. **Parse complete** (background thread)
2. **Populate Metadata Inspector** (main thread or via GLib.idle_add)
3. **Save to project** (`_save_to_project()`)
   - Saves raw file (.kgml/.sbml)
   - Saves parsed JSON
   - Saves Petri net (.shypn)
4. **Auto-load to canvas** (creates new document tab)
5. **Store metadata in document.metadata** (for tab-switch sensitivity)
6. **Re-enable import button**

---

## Metadata Storage for Tab-Switch Sensitivity

All categories store metadata in `document_model.metadata` dict:

### KEGG
```python
document_model.metadata['kegg_import'] = True
document_model.metadata['pathway_id'] = "hsa00010"
document_model.metadata['kgml_data'] = {
    'pathway_id': '...',
    'pathway_title': '...',
    'organism': '...',
    # ... full parsed pathway structure
}
```

### SBML (BioModels)
```python
document_model.metadata['sbml_import'] = True  
document_model.metadata['biomodels_id'] = "BIOMD0000000061"
document_model.metadata['sbml_data'] = {
    'model_id': '...',
    'compartments': [...],
    'species': [...],
    # ... full parsed SBML structure
}
```

### BiGG
```python
document_model.metadata['source'] = 'bigg_import'
document_model.metadata['model_id'] = "iML1515"
document_model.metadata['bigg_sbml_data'] = {
    'model_id': '...',
    'compartments_count': 8,
    'species_count': 1877,
    'reactions_count': 2712,
    'parameters_count': 0
}
```

---

## Tab-Switch Detection Pattern

When user switches tabs, `on_tab_switched()` checks document metadata:

### KEGG
```python
def refresh_metadata_inspector(self):
    document = self.get_current_model()
    if document and hasattr(document, 'metadata'):
        metadata = document.metadata
        if metadata.get('kegg_import'):
            # This is a KEGG model - load metadata
            kgml_data = metadata.get('kgml_data')
            if kgml_data:
                self._load_kegg_metadata_from_dict(kgml_data)
                self.metadata_expander.set_expanded(True)
        else:
            # Not a KEGG model - clear
            self.metadata_store.clear()
```

### SBML
```python
def refresh_metadata_inspector(self):
    document = self.get_current_model()
    if document and hasattr(document, 'metadata'):
        metadata = document.metadata
        if metadata.get('sbml_import'):
            # This is an SBML model - load metadata
            sbml_data = metadata.get('sbml_data')
            if sbml_data:
                self._load_sbml_metadata_from_dict(sbml_data)
                self.metadata_expander.set_expanded(True)
        else:
            # Not an SBML model - clear
            self.metadata_store.clear()
```

### BiGG
```python
def refresh_metadata_inspector(self):
    document = self.get_current_model()
    if document and hasattr(document, 'metadata'):
        source = document.metadata.get('source')
        if source == 'bigg_import':
            # This is a BiGG model - load metadata
            bigg_data = document.metadata.get('bigg_sbml_data')
            if bigg_data:
                self._load_sbml_metadata_from_dict(bigg_data)
                self.sbml_metadata_expander.set_expanded(True)
        else:
            # Not a BiGG model - clear
            self.sbml_metadata_store.clear()
```

---

## Recommendations for Consistency

### 1. Standardize Metadata Key Names
- Use `source: 'kegg_import' | 'sbml_import' | 'bigg_import'` consistently
- Use `source_id` for accession (pathway_id, biomodels_id, model_id)
- Use `source_data` for the full parsed structure

### 2. Standardize Population Timing
- Consider moving BiGG to post-processing callback (like KEGG/SBML)
- OR move KEGG/SBML to during-thread with GLib.idle_add (like BiGG)
- Current mix works but is inconsistent

### 3. Cache Optimization
- BiGG already checks for `self.parsed_pathway` cache (line 699)
- KEGG could add similar check in `_fetch_and_import_remote()`
- SBML could add similar check in `_run_sbml_import_in_background()`

### 4. Error Handling
- All three need consistent error reporting for:
  - Network failures (fetch)
  - Parse failures
  - Conversion failures
  - Save failures

---

## Current Status ✅

**Working Features**:
- ✅ Single-button remote import for all categories
- ✅ Background threading prevents UI freeze
- ✅ Metadata inspector populated during/after import
- ✅ Tree auto-expansion after population
- ✅ Metadata stored in document for tab-switch sensitivity
- ✅ Tab-switch correctly loads/clears metadata per category

**Next Steps**:
- Consider standardizing metadata key naming
- Consider standardizing population timing (all during-thread or all post-thread)
- Add progress indicators for long downloads (large BiGG models)
- Test with slow networks to ensure timeout handling
