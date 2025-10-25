# Import Flow Integration Analysis
## KEGG & SBML → Report Panel Data Flow

**Date**: October 25, 2025  
**Purpose**: Document import flows and integration points for Report Panel testing

---

## 🔄 KEGG Import Flow

### Step-by-Step Process

```
1. USER ACTION: Click Pathways button → Enter pathway ID (e.g., "hsa00010")
   ↓
2. FETCH: KEGGImportPanel._on_fetch_clicked()
   - KEGGAPIClient.fetch_kgml(pathway_id)
   - Downloads KGML XML from https://rest.kegg.jp/get/hsa00010/kgml
   - Background thread (non-blocking)
   ↓
3. PARSE: KGMLParser.parse(kgml_xml)
   - Returns KEGGPathway object
   - Contains: compounds, reactions, coordinates, metadata
   ↓
4. PREVIEW: Update UI with pathway info
   - Shows: name, organism, # compounds, # reactions
   - Enables "Import" button
   ↓
5. USER ACTION: Click "Import to Canvas"
   ↓
6. CONVERT: PathwayConverter.convert_pathway_enhanced()
   - KEGGPathway → DocumentModel
   - Compounds → Places
   - Reactions → Transitions
   - Substrate/Product → Arcs
   - Background thread (non-blocking)
   ↓
7. LOAD TO CANVAS: model_canvas.add_document(filename=pathway_name)
   - Creates new tab: "Glycolysis / Gluconeogenesis"
   - ModelCanvasManager.load_objects(places, transitions, arcs)
   - Fit to page with padding
   - Mark as imported (triggers "Save As" on Ctrl+S)
   ↓
8. PROJECT TRACKING (if project exists):
   - Create PathwayDocument metadata
   - Link to model ID
   - Save project file
   ↓
9. CANVAS READY:
   - Objects visible and selectable
   - Swiss Palette available for layout
   - Ready for analysis
```

### Key Files

- **UI Controller**: `src/shypn/helpers/kegg_import_panel.py`
- **API Client**: `src/shypn/importer/kegg/api_client.py`
- **Parser**: `src/shypn/importer/kegg/kgml_parser.py`
- **Converter**: `src/shypn/importer/kegg/pathway_converter.py`
- **Models**: `src/shypn/importer/kegg/models.py`

### Data Structures

**KEGGPathway** (parsed from KGML):
```python
KEGGPathway:
    - pathway_id: str (e.g., "hsa00010")
    - title: str (e.g., "Glycolysis / Gluconeogenesis")
    - organism: str (e.g., "hsa")
    - compounds: List[KEGGEntry]  # Species
    - reactions: List[KEGGReaction]
    - coordinates: Dict[str, Tuple[x, y]]
```

**DocumentModel** (loaded to canvas):
```python
DocumentModel:
    - places: List[Place]  # From compounds
    - transitions: List[Transition]  # From reactions
    - arcs: List[Arc]  # From substrates/products
    - metadata: Dict (title, organism, source)
```

---

## 🧬 SBML Import Flow

### Step-by-Step Process

```
1. USER ACTION: Click Pathways button → Select SBML tab → Browse file
   ↓
2. FILE SELECTION: SBMLImportPanel._on_browse_clicked()
   - FileChooser with .sbml/.xml filters
   - Sets file path in entry widget
   - Enables "Parse File" button
   ↓
3. USER ACTION: Click "Parse File"
   ↓
4. PARSE: SBMLImportPanel._on_parse_clicked()
   - SBMLParser.parse_file(filepath)
   - Returns PathwayData object
   - Background thread (non-blocking)
   ↓
5. VALIDATE: PathwayValidator.validate(pathway)
   - Checks references, units, stoichiometry
   - Returns ValidationResult with errors/warnings
   ↓
6. PREVIEW: Update UI with pathway info
   - Shows: name, # species, # reactions
   - Shows validation errors/warnings
   ↓
7. AUTO-LOAD: _on_load_clicked() (automatic after parse)
   ↓
8. CONVERT: PathwayConverter.convert(pathway_data)
   - PathwayData → DocumentModel
   - Species → Places
   - Reactions → Transitions
   - Stoichiometry → Arcs with weights
   - Background thread (non-blocking)
   ↓
9. LOAD TO CANVAS: model_canvas.add_document(filename=pathway_name)
   - Creates new tab with pathway name
   - ModelCanvasManager.load_objects(places, transitions, arcs)
   - Fit to page with offsets
   - Mark as imported
   ↓
10. PROJECT TRACKING (if project exists):
    - Create PathwayDocument metadata
    - Link to model ID
    - Save project file
    ↓
11. CANVAS READY:
    - Objects at arbitrary positions (no layout yet)
    - Swiss Palette force-directed layout available
    - Ready for analysis
```

### Key Files

- **UI Controller**: `src/shypn/helpers/sbml_import_panel.py`
- **Parser**: `src/shypn/data/pathway/sbml_parser.py`
- **Validator**: `src/shypn/data/pathway/pathway_validator.py`
- **Converter**: `src/shypn/data/pathway/pathway_converter.py`
- **Models**: `src/shypn/data/pathway/models.py`

### Data Structures

**PathwayData** (parsed from SBML):
```python
PathwayData:
    - species: List[Species]  # Chemical compounds
    - reactions: List[Reaction]
    - compartments: List[Compartment]
    - parameters: List[Parameter]
    - units: List[UnitDefinition]
    - metadata: Dict (name, notes, annotations)
```

**DocumentModel** (loaded to canvas):
```python
DocumentModel:
    - places: List[Place]  # From species
    - transitions: List[Transition]  # From reactions
    - arcs: List[Arc]  # From reactants/products
    - metadata: Dict (name, source, parameters)
```

---

## 📊 Integration with Report Panel

### Data Available After Import

Both KEGG and SBML imports create the same final structure in the canvas:

1. **Model Structure** (ModelCanvasManager):
   ```python
   manager.places: List[Place]
   manager.transitions: List[Transition]
   manager.arcs: List[Arc]
   manager.document_controller.document: DocumentModel
   ```

2. **Project Metadata** (if project exists):
   ```python
   project.pathways: List[PathwayDocument]
   PathwayDocument:
       - source_type: "KEGG" or "SBML"
       - source_id: pathway_id or file_path
       - import_date: datetime
       - metadata: Dict (title, organism, etc.)
       - linked_model_id: UUID (links to DocumentModel)
   ```

3. **Enrichment Data** (future):
   ```python
   manager.enrichments: List[EnrichmentData]
   EnrichmentData:
       - transition_id: UUID
       - parameters: Dict (Km, kcat, Ki, etc.)
       - source: "BRENDA" or "Kinetics"
       - citations: List[str]
   ```

### Report Panel Data Access

The Report Panel can access this data through:

```python
class ReportPanel:
    def __init__(self, project=None, model_canvas=None):
        self.project = project  # Access pathways metadata
        self.model_canvas = model_canvas  # Access current canvas
    
    def refresh(self):
        # Get current canvas manager
        manager = self.model_canvas.get_current_canvas_manager()
        
        if manager:
            # MODELS category
            places_count = len(manager.places)
            transitions_count = len(manager.transitions)
            arcs_count = len(manager.arcs)
            
            # DYNAMIC ANALYSES category
            enrichments = manager.enrichments if hasattr(manager, 'enrichments') else []
            
            # TOPOLOGY ANALYSES category
            # (Will integrate with Analyses Panel results)
            
            # PROVENANCE & LINEAGE category
            if self.project:
                pathways = self.project.pathways
                for pw in pathways:
                    source_type = pw.source_type  # "KEGG" or "SBML"
                    source_id = pw.source_id
                    import_date = pw.import_date
```

---

## 🧪 Testing Integration

### Test Case 1: KEGG Import → Report Panel

```
1. Launch SHYpn: python3 src/shypn.py
2. Click Pathways button in Master Palette
3. Enter pathway ID: "hsa00010" (Glycolysis)
4. Click "Fetch Pathway"
5. Wait for fetch to complete
6. Click "Import to Canvas"
7. Wait for canvas to load
8. Click Report button in Master Palette
9. Verify MODELS category shows:
   - ~45 places
   - ~38 transitions
   - ~120 arcs
10. Expand PROVENANCE & LINEAGE category
11. Verify shows:
    - Source: KEGG
    - Pathway: hsa00010 - Glycolysis
    - Import date: [today's date]
```

### Test Case 2: SBML Import → Report Panel

```
1. Launch SHYpn: python3 src/shypn.py
2. Click Pathways button in Master Palette
3. Select SBML tab
4. Click "Browse" and select SBML file (or use BioModels)
5. Click "Parse File"
6. Wait for auto-load to complete
7. Click Report button in Master Palette
8. Verify MODELS category shows correct counts
9. Expand PROVENANCE & LINEAGE category
10. Verify shows:
    - Source: SBML
    - File: [filename or model ID]
    - Import date: [today's date]
```

### Test Case 3: File Explorer Integration

```
1. Launch SHYpn
2. Click Files button in Master Palette
3. Create new model or load existing .shy file
4. Click Report button
5. Verify MODELS category shows model structure
6. Verify PROVENANCE & LINEAGE shows file operations history
```

---

## 🎯 Integration Points for Report Panel

### Immediate Integration (Phase 1)

1. **MODELS Category**:
   - Wire to `model_canvas.get_current_canvas_manager()`
   - Count: `len(manager.places)`, `len(manager.transitions)`, `len(manager.arcs)`
   - No additional data needed ✅

2. **PROVENANCE & LINEAGE Category**:
   - Wire to `project.pathways`
   - Display pathway source, ID, import date
   - Shows transformation pipeline (KEGG/SBML → Parse → Convert → Load)

### Future Integration (Phase 2)

3. **DYNAMIC ANALYSES Category**:
   - Wire to enrichment data (when BRENDA integration complete)
   - Count enriched transitions
   - List parameter sources

4. **TOPOLOGY ANALYSES Category**:
   - Wire to Analyses Panel results
   - Check if analyses have been run
   - Display cached results

---

## 📝 Conclusion

**Import flows are well-established** ✅
- Both KEGG and SBML follow clean MVC pattern
- Background threading prevents UI blocking
- Data ends up in same DocumentModel structure
- Project tracking already in place

**Report Panel integration is straightforward** ✅
- MODELS category: Direct access to manager.places/transitions/arcs
- PROVENANCE category: Direct access to project.pathways
- Ready for testing with real imported data

**Next Steps**:
1. Test KEGG import → Report Panel display
2. Test SBML import → Report Panel display  
3. Test File operations → Report Panel display
4. Wire DYNAMIC ANALYSES when enrichment data available
5. Wire TOPOLOGY ANALYSES to Analyses Panel results

---

**Status**: Ready for integration testing! 🚀
