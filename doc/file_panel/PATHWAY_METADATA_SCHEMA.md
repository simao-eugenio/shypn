# Pathway Metadata Schema Design

## Problem Statement

**Current Limitation:**
```python
class Project:
    self.pathways = []  # Just file paths - no metadata or relationships
```

**Required Feature:**
```
1. Import KEGG pathway (hsa00010) → Model A
2. Import SBML pathway (glycolysis) → Model B
3. Enrich Model A with BRENDA (EC 2.7.1.1) → Associate BRENDA data with hsa00010
4. Enrich Model B with BRENDA (EC 1.2.1.12) → Associate BRENDA data with glycolysis

Question: How to track which enrichment belongs to which pathway?
```

## Proposed Solution: PathwayDocument Class

### Architecture

```python
class PathwayDocument:
    """Represents an external pathway with metadata and enrichments.
    
    A PathwayDocument is the source data (KEGG/SBML file) that was imported,
    along with all associated enrichments (BRENDA, etc.) and the link to the
    converted model on the canvas.
    """
    def __init__(self):
        # Identity
        self.id: str = str(uuid.uuid4())
        self.name: str = "Glycolysis"
        
        # Source provenance
        self.source_type: str = "kegg"  # or "sbml"
        self.source_id: str = "hsa00010"  # KEGG pathway ID or SBML filename
        self.source_organism: str = "Homo sapiens"  # hsa = human
        
        # File locations (relative to project pathways/ directory)
        self.raw_file: str = "hsa00010.kgml"  # Original imported file
        self.metadata_file: str = "hsa00010.meta.json"  # Extracted metadata
        
        # Timestamps
        self.imported_date: str = "2025-10-25T14:30:00"
        self.last_modified: str = "2025-10-25T14:30:00"
        
        # Associated enrichments
        self.enrichments: List[EnrichmentDocument] = []
        
        # Link to converted model (if user converted to canvas)
        self.model_id: Optional[str] = None  # Links to Project.models[model_id]
        
        # Tags and notes
        self.tags: List[str] = []
        self.notes: str = ""


class EnrichmentDocument:
    """Represents enrichment data from an external source (BRENDA, etc.)."""
    def __init__(self):
        # Identity
        self.id: str = str(uuid.uuid4())
        self.type: str = "kinetics"  # "kinetics", "structural", "functional"
        
        # Source
        self.source: str = "brenda"  # "brenda", "reactome", etc.
        self.source_query: Dict = {
            "ec_number": "2.7.1.1",
            "organism": "Homo sapiens"
        }
        
        # File location
        self.data_file: str = "brenda_ec_2_7_1_1.json"
        
        # Enrichment results
        self.applied_date: str = "2025-10-25T15:00:00"
        self.transitions_enriched: List[str] = ["transition_1", "transition_3"]
        self.parameters_added: Dict = {
            "km_values": 3,
            "kcat_values": 2,
            "ki_values": 1,
            "citations": 5
        }
        
        # Quality metrics
        self.confidence: str = "high"  # "high", "medium", "low"
        self.citations: List[str] = ["PMID:12345678", "PMID:23456789"]


class Project:
    """Enhanced Project with structured pathway tracking."""
    def __init__(self):
        # ... existing fields ...
        
        # CHANGE: From flat list to structured dict
        self.pathways: Dict[str, PathwayDocument] = {}  # pathway_id -> PathwayDocument
        # Was: self.pathways = []
```

## Data Flow Examples

### Example 1: Import KEGG Pathway

```python
# User: File → Import → KEGG Pathway → hsa00010

# 1. Fetch and save raw data
kgml_data = fetch_pathway("hsa00010")
pathway_doc = PathwayDocument()
pathway_doc.name = "Glycolysis / Gluconeogenesis"
pathway_doc.source_type = "kegg"
pathway_doc.source_id = "hsa00010"
pathway_doc.source_organism = "Homo sapiens"
pathway_doc.raw_file = "hsa00010.kgml"
pathway_doc.imported_date = datetime.now().isoformat()

# 2. Save files to project structure
project.save_pathway_file("hsa00010.kgml", kgml_data)
project.save_pathway_metadata("hsa00010.meta.json", {
    "title": pathway.title,
    "organism": pathway.organism,
    "genes": [list of genes],
    "compounds": [list of compounds]
})

# 3. Register in project
project.pathways[pathway_doc.id] = pathway_doc
project.save()

# Result:
# workspace/projects/MyProject/
#   pathways/
#     hsa00010.kgml              ← Raw KEGG data
#     hsa00010.meta.json         ← Extracted metadata
#   project.shy                  ← Contains PathwayDocument reference
```

### Example 2: Convert Pathway to Canvas

```python
# User: Clicks "Convert to Canvas" button

# 1. Load pathway from saved file
pathway_doc = project.pathways[pathway_id]
kgml_path = project.get_pathways_dir() / pathway_doc.raw_file
pathway = parse_kgml(kgml_path.read_text())

# 2. Convert to Petri net model
converter = PathwayConverter()
document = converter.convert(pathway)

# 3. Create ModelDocument and link
model = ModelDocument()
model.name = pathway_doc.name
model.file_path = project.get_models_dir() / f"{pathway_doc.source_id}.shy"
document.save(model.file_path)

# 4. Link pathway to model (bi-directional)
pathway_doc.model_id = model.id
project.models[model.id] = model
project.save()

# Result:
# - Model appears on canvas
# - PathwayDocument.model_id points to ModelDocument
# - Can trace back: Model → PathwayDocument → Raw KEGG file
```

### Example 3: Enrich with BRENDA

```python
# User: Opens model, clicks Pathways → BRENDA → Analyze and Enrich

# 1. Load model and find source pathway
model = project.models[model_id]
pathway_doc = project.find_pathway_by_model_id(model_id)

# 2. Query BRENDA for transitions
brenda_results = query_brenda_for_transitions(model.document.transitions)

# 3. Create enrichment record
enrichment = EnrichmentDocument()
enrichment.type = "kinetics"
enrichment.source = "brenda"
enrichment.source_query = {"ec_numbers": ["2.7.1.1", "2.7.1.11"]}
enrichment.data_file = f"brenda_{pathway_doc.source_id}.json"
enrichment.applied_date = datetime.now().isoformat()
enrichment.transitions_enriched = ["R01", "R02", "R05"]
enrichment.parameters_added = {
    "km_values": 8,
    "kcat_values": 5,
    "citations": 12
}

# 4. Save BRENDA data and link to pathway
project.save_enrichment_file(enrichment.data_file, brenda_results)
pathway_doc.enrichments.append(enrichment)
project.save()

# Result:
# workspace/projects/MyProject/
#   pathways/
#     hsa00010.kgml                      ← Source pathway
#     hsa00010.meta.json                 ← KEGG metadata
#     brenda_hsa00010.json               ← BRENDA enrichment
#   models/
#     hsa00010.shy                       ← Canvas model (enriched)
#   project.shy
#     → PathwayDocument:
#         source: hsa00010.kgml
#         model_id: abc-123
#         enrichments: [brenda_hsa00010.json]
```

### Example 4: Report Generation

```python
# User: Generate report for enriched model

# 1. Load model
model = project.models[model_id]

# 2. Find source pathway
pathway_doc = project.find_pathway_by_model_id(model_id)

# 3. Generate report with full lineage
report = ReportGenerator()
report.add_section("Data Provenance")
report.add_metadata({
    "Source": f"{pathway_doc.source_type.upper()}: {pathway_doc.source_id}",
    "Organism": pathway_doc.source_organism,
    "Imported": pathway_doc.imported_date,
    "Enrichments": len(pathway_doc.enrichments)
})

# 4. Add enrichment details
for enrichment in pathway_doc.enrichments:
    report.add_subsection(f"{enrichment.source.upper()} Enrichment")
    report.add_metadata({
        "Type": enrichment.type,
        "Applied": enrichment.applied_date,
        "Transitions Enriched": len(enrichment.transitions_enriched),
        "Parameters Added": sum(enrichment.parameters_added.values()),
        "Confidence": enrichment.confidence.upper(),
        "Citations": len(enrichment.citations)
    })
    
    # Include raw enrichment data
    enrichment_path = project.get_pathways_dir() / enrichment.data_file
    enrichment_data = json.loads(enrichment_path.read_text())
    report.add_enrichment_table(enrichment_data)

# Result: Report with complete data lineage
```

## Database Schema (project.shy JSON)

### Current (inadequate):

```json
{
  "content": {
    "models": [
      {"id": "abc-123", "name": "Glycolysis", "file_path": "models/model1.shy"}
    ],
    "pathways": [
      "hsa00010.kgml",
      "glycolysis.sbml"
    ],
    "simulations": []
  }
}
```

**Problem:** Cannot tell which model came from which pathway, or which enrichments belong to which pathway.

### Proposed (with PathwayDocument):

```json
{
  "content": {
    "models": [
      {"id": "abc-123", "name": "Glycolysis", "file_path": "models/hsa00010.shy"}
    ],
    "pathways": {
      "pathway-1": {
        "id": "pathway-1",
        "name": "Glycolysis / Gluconeogenesis",
        "source_type": "kegg",
        "source_id": "hsa00010",
        "source_organism": "Homo sapiens",
        "raw_file": "hsa00010.kgml",
        "metadata_file": "hsa00010.meta.json",
        "imported_date": "2025-10-25T14:30:00",
        "model_id": "abc-123",
        "enrichments": [
          {
            "id": "enrich-1",
            "type": "kinetics",
            "source": "brenda",
            "data_file": "brenda_hsa00010.json",
            "applied_date": "2025-10-25T15:00:00",
            "transitions_enriched": ["R01", "R02", "R05"],
            "parameters_added": {"km_values": 8, "kcat_values": 5},
            "confidence": "high",
            "citations": ["PMID:12345678", "PMID:23456789"]
          }
        ],
        "tags": ["human", "metabolism"],
        "notes": "Primary glycolysis pathway"
      },
      "pathway-2": {
        "id": "pathway-2",
        "name": "Alternative Glycolysis",
        "source_type": "sbml",
        "source_id": "glycolysis_v2.xml",
        "source_organism": "Saccharomyces cerevisiae",
        "raw_file": "glycolysis_v2.sbml",
        "metadata_file": "glycolysis_v2.meta.json",
        "imported_date": "2025-10-25T16:00:00",
        "model_id": null,
        "enrichments": [],
        "tags": ["yeast"],
        "notes": "Not yet converted to canvas"
      }
    },
    "simulations": []
  }
}
```

**Benefits:**
- ✅ Full traceability: Model → Pathway → Enrichments → Raw files
- ✅ Multiple pathways from same/different sources
- ✅ Track which enrichments belong to which pathway
- ✅ Support report generation with provenance
- ✅ Enable "View Source" functionality in UI

## Project Methods to Add

```python
class Project:
    # ... existing methods ...
    
    # Pathway management
    def add_pathway(self, pathway_doc: PathwayDocument) -> None:
        """Register pathway in project."""
        self.pathways[pathway_doc.id] = pathway_doc
    
    def remove_pathway(self, pathway_id: str) -> None:
        """Remove pathway and its files."""
        pathway_doc = self.pathways.pop(pathway_id)
        # Delete files
        (self.get_pathways_dir() / pathway_doc.raw_file).unlink()
        (self.get_pathways_dir() / pathway_doc.metadata_file).unlink()
        for enrichment in pathway_doc.enrichments:
            (self.get_pathways_dir() / enrichment.data_file).unlink()
    
    def find_pathway_by_model_id(self, model_id: str) -> Optional[PathwayDocument]:
        """Find pathway that was converted to this model."""
        for pathway_doc in self.pathways.values():
            if pathway_doc.model_id == model_id:
                return pathway_doc
        return None
    
    def find_pathways_by_source(self, source_type: str) -> List[PathwayDocument]:
        """Find all pathways from a specific source (kegg/sbml)."""
        return [p for p in self.pathways.values() if p.source_type == source_type]
    
    # File operations
    def save_pathway_file(self, filename: str, content: str) -> None:
        """Save pathway file to pathways/ directory."""
        path = self.get_pathways_dir() / filename
        path.write_text(content, encoding='utf-8')
    
    def save_pathway_metadata(self, filename: str, metadata: Dict) -> None:
        """Save pathway metadata as JSON."""
        path = self.get_pathways_dir() / filename
        path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    
    def save_enrichment_file(self, filename: str, data: Dict) -> None:
        """Save enrichment data to pathways/ directory."""
        path = self.get_pathways_dir() / filename
        path.write_text(json.dumps(data, indent=2), encoding='utf-8')
```

## Migration Strategy

For existing projects (if any use the flat list):

```python
@classmethod
def migrate_v1_to_v2(cls, data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate old flat pathway list to new PathwayDocument structure."""
    content = data.get('content', {})
    old_pathways = content.get('pathways', [])
    
    if isinstance(old_pathways, list):
        # Old format: list of file paths
        new_pathways = {}
        for i, filepath in enumerate(old_pathways):
            # Create PathwayDocument from file path
            pathway_doc = {
                'id': f'migrated-{i}',
                'name': Path(filepath).stem,
                'source_type': 'unknown',
                'source_id': Path(filepath).stem,
                'raw_file': filepath,
                'metadata_file': '',
                'imported_date': datetime.now().isoformat(),
                'model_id': None,
                'enrichments': [],
                'tags': ['migrated'],
                'notes': 'Migrated from v1 project'
            }
            new_pathways[pathway_doc['id']] = pathway_doc
        
        content['pathways'] = new_pathways
        data['content'] = content
    
    return data
```

## Implementation Priority

1. **Phase 1: Data Model** (HIGH - blocks everything)
   - [ ] Add `PathwayDocument` class to `project_models.py`
   - [ ] Add `EnrichmentDocument` class to `project_models.py`
   - [ ] Update `Project.pathways` from `list` to `dict`
   - [ ] Add pathway management methods
   - [ ] Update serialization (`to_dict`, `from_dict`)
   - [ ] Add migration function

2. **Phase 2: Import Integration** (HIGH - needed for Phase 3 of File Panel)
   - [ ] Update KEGG importer to create `PathwayDocument`
   - [ ] Update SBML importer to create `PathwayDocument`
   - [ ] Save raw files to `pathways/` directory
   - [ ] Extract and save metadata

3. **Phase 3: Enrichment Integration** (MEDIUM)
   - [ ] Update BRENDA enrichment to create `EnrichmentDocument`
   - [ ] Save enrichment data files
   - [ ] Link enrichments to pathways

4. **Phase 4: UI Updates** (MEDIUM)
   - [ ] File Panel: Display pathways with metadata
   - [ ] Show source type icons (KEGG/SBML)
   - [ ] Show enrichment status
   - [ ] Add "View Source" button

5. **Phase 5: Report Generation** (LOW - nice to have)
   - [ ] Generate reports with full provenance
   - [ ] Include enrichment details and citations
   - [ ] Export pathway lineage

## Success Criteria

✅ Can import multiple pathways from different sources
✅ Can track which model came from which pathway
✅ Can enrich pathways and track enrichment history
✅ Can generate reports with full data lineage
✅ Project file contains complete provenance information
✅ No data loss when saving/loading projects

## Testing Plan

```python
def test_pathway_coupling():
    """Test pathway-enrichment coupling."""
    project = Project(name="Test", base_path="/tmp/test")
    
    # Import KEGG pathway
    kegg_pathway = PathwayDocument()
    kegg_pathway.name = "Glycolysis"
    kegg_pathway.source_type = "kegg"
    kegg_pathway.source_id = "hsa00010"
    project.add_pathway(kegg_pathway)
    
    # Convert to model
    model = ModelDocument()
    model.name = "Glycolysis Model"
    kegg_pathway.model_id = model.id
    project.models[model.id] = model
    
    # Enrich with BRENDA
    enrichment = EnrichmentDocument()
    enrichment.source = "brenda"
    enrichment.transitions_enriched = ["R01", "R02"]
    kegg_pathway.enrichments.append(enrichment)
    
    # Verify coupling
    assert project.find_pathway_by_model_id(model.id) == kegg_pathway
    assert len(kegg_pathway.enrichments) == 1
    assert kegg_pathway.enrichments[0].source == "brenda"
    
    # Save and reload
    project.save()
    loaded = Project.load(project.get_project_file_path())
    
    # Verify persistence
    loaded_pathway = loaded.find_pathway_by_model_id(model.id)
    assert loaded_pathway is not None
    assert loaded_pathway.name == "Glycolysis"
    assert len(loaded_pathway.enrichments) == 1
```

## Conclusion

**Answer:** ❌ Current structure **cannot** handle pathway-enrichment coupling.

**Solution:** Implement `PathwayDocument` and `EnrichmentDocument` classes to provide:
- Structured metadata tracking
- Source provenance (KEGG/SBML)
- Enrichment history (BRENDA)
- Model linkage
- Full data lineage for reports

This is a **prerequisite** for Phase 3 (Data Persistence) of the File Panel completion plan.
