# BRENDA Enrichment Infrastructure - Quick Reference

**Status:** ✅ READY (awaiting BRENDA credentials)  
**Date:** October 25, 2025

---

## What Was Built

### New Controller: BRENDAEnrichmentController

Complete infrastructure for tracking BRENDA enrichments in project metadata.

**Location:** `src/shypn/helpers/brenda_enrichment_controller.py`

**Key Methods:**
```python
# High-level workflows (ready to use)
controller.enrich_canvas_from_api(ec_numbers=['2.7.1.1'], organism='Homo sapiens')
controller.enrich_canvas_from_file(file_path='/path/to/brenda.json')

# Lower-level control
controller.start_enrichment(source="brenda_api")
controller.apply_enrichment_to_transition('T1', {'km': 0.05, 'kcat': 450.0})
controller.add_citations(['PMID:12345678'])
controller.save_enrichment_to_project(brenda_data)
enrichment = controller.finish_enrichment()
```

---

## What Gets Tracked

### EnrichmentDocument

```python
{
    'id': 'enrichment-uuid',
    'type': 'kinetics',
    'source': 'brenda_api',
    'source_query': {'ec_numbers': ['2.7.1.1'], 'organism': 'Homo sapiens'},
    'data_file': 'brenda_enrichment_20251025_143022.json',
    'applied_date': '2025-10-25T14:30:22',
    'transitions_enriched': ['T1', 'T2', 'T3'],
    'parameters_added': {'km': 3, 'kcat': 3},
    'confidence': 'high',
    'citations': ['PMID:12345678', 'PMID:23456789'],
    'notes': ''
}
```

### Project Structure

```
project/
├── .project.shy              # Links pathway → enrichment
├── models/
│   └── glycolysis.shy        # Model with enriched kinetics
├── pathways/
│   └── hsa00010.kgml         # Source KEGG pathway
└── enrichments/              # NEW: Enrichment data files
    └── brenda_enrichment_TIMESTAMP.json
```

### .project.shy Content

```json
{
  "pathways": {
    "pathway-id": {
      "source_type": "kegg",
      "model_id": "model-id",
      "enrichments": ["enrichment-id"]  // ← Links to enrichment
    }
  }
}
```

---

## Integration Points

### 1. Pathway Panel Loader

**Already wired:**
```python
# In pathway_panel_loader.py
self.brenda_enrichment_controller = BRENDAEnrichmentController(
    model_canvas=self.model_canvas,
    project=self.project
)

# Button click handler
def _on_brenda_enrich_clicked(self, button):
    result = self.brenda_enrichment_controller.enrich_canvas_from_file(file_path)
    # Show results to user
```

**Updates with project changes:**
```python
def set_project(self, project):
    if self.brenda_enrichment_controller:
        self.brenda_enrichment_controller.set_project(project)
```

### 2. Project Model

**New method added:**
```python
def get_enrichments_dir(self) -> Optional[str]:
    """Get path to enrichments/ directory."""
    if self.base_path:
        return os.path.join(self.base_path, 'enrichments')
    return None
```

---

## What Still Needs Implementation

### When BRENDA Credentials Are Active

**1. BRENDA SOAP API Client** (~2-3 hours)
```python
def fetch_from_brenda_api(self, ec_number, organism):
    # Add zeep SOAP client
    # Query BRENDA with credentials
    # Parse and return data
```

**2. Canvas Scanning** (~1-2 hours)
```python
def scan_canvas_transitions(self):
    # Access canvas.document
    # Extract transitions with EC numbers
    # Return list for enrichment
```

**3. Parameter Application** (~1 hour)
```python
def apply_enrichment_to_transition(self, transition_id, parameters):
    # Find transition in canvas
    # Update metadata with kinetics
    # Mark as enriched
```

**Total: ~4-6 hours** when credentials ready

---

## Usage Examples

### Scenario 1: Enrich from BRENDA API (When Ready)

```python
from shypn.helpers.brenda_enrichment_controller import BRENDAEnrichmentController

# Initialize
controller = BRENDAEnrichmentController(
    model_canvas=canvas,
    project=current_project
)

# Enrich entire canvas
result = controller.enrich_canvas_from_api(
    ec_numbers=['2.7.1.1', '2.7.1.11', '1.1.1.1'],
    organism='Homo sapiens',
    override_existing=False
)

print(f"Enriched {result['transitions_enriched']} transitions")
print(f"Enrichment ID: {result['enrichment_id']}")
```

### Scenario 2: Enrich from Local File (Works Now)

```python
# Load BRENDA export file
result = controller.enrich_canvas_from_file(
    file_path='/path/to/brenda_export.json',
    override_existing=False
)

if result['success']:
    print(f"Scanned: {result['transitions_scanned']} transitions")
    print(f"Enriched: {result['transitions_enriched']} transitions")
```

### Scenario 3: Manual Control

```python
# Start enrichment session
controller.start_enrichment(
    source="brenda_api",
    query_params={'ec_numbers': ['2.7.1.1']}
)

# Scan canvas
transitions = controller.scan_canvas_transitions()

# Apply to specific transitions
controller.apply_enrichment_to_transition('T1', {
    'km': 0.05,
    'kcat': 450.0
})
controller.apply_enrichment_to_transition('T2', {
    'km': 0.03,
    'kcat': 230.0
})

# Add metadata
controller.add_citations(['PMID:12345678', 'PMID:23456789'])
controller.set_confidence('high')

# Save to project
controller.save_enrichment_to_project(brenda_data)

# Finish
enrichment = controller.finish_enrichment()
print(f"Created enrichment: {enrichment.id}")
print(f"Transitions: {enrichment.get_transition_count()}")
print(f"Parameters: {enrichment.get_total_parameters()}")
print(f"Citations: {enrichment.get_citation_count()}")
```

---

## Testing

### Manual Test (When Credentials Ready)

```bash
# Start SHYpn
cd /home/simao/projetos/shypn
python3 src/shypn.py

# 1. Create project "TestBRENDA"
# 2. Import KEGG pathway hsa00010
# 3. Open Pathway Panel → BRENDA tab
# 4. Click "Analyze and Enrich Canvas"

# Verify:
ls workspace/projects/TestBRENDA/enrichments/
# Should see: brenda_enrichment_TIMESTAMP.json

cat workspace/projects/TestBRENDA/.project.shy
# Should see enrichment linked to pathway
```

### Mock Test (Works Now)

```python
def test_enrichment_infrastructure():
    """Test enrichment tracking without actual BRENDA data."""
    project = Project(name="Test", base_path="/tmp/test")
    pathway = PathwayDocument(source_type="kegg", source_id="hsa00010")
    project.add_pathway(pathway)
    
    controller = BRENDAEnrichmentController(project=project)
    
    # Mock enrichment
    controller.start_enrichment(source="test")
    controller.apply_enrichment_to_transition('T1', {'km': 0.05})
    
    mock_data = {'2.7.1.1': {'km_values': [{'value': 0.05}]}}
    success = controller.save_enrichment_to_project(mock_data)
    
    enrichment = controller.finish_enrichment()
    
    # Verify
    assert success
    assert enrichment.get_transition_count() == 1
    assert len(pathway.enrichments) == 1
    assert pathway.enrichments[0] == enrichment.id
    
    # Verify file created
    enrichments_dir = project.get_enrichments_dir()
    files = os.listdir(enrichments_dir)
    assert len(files) == 1
    assert files[0].startswith('brenda_enrichment_')
```

---

## Key Differences from Phases 2-3

| Aspect | KEGG/SBML (Import) | BRENDA (Enrichment) |
|--------|-------------------|---------------------|
| Creates | New model | Updates existing |
| Document | PathwayDocument | EnrichmentDocument |
| Workflow | Fetch → Convert | Scan → Apply |
| Result | `.shy` file | Metadata update |
| Linking | Pathway → Model | Pathway → Enrichment |

---

## Next Steps

### Immediate (Phase 5)
- File Panel UI to display enrichments
- Visual indicators for enriched pathways
- Context menus for re-applying enrichments

### When Credentials Ready
1. Implement BRENDA SOAP client (2-3 hours)
2. Wire canvas scanning (1-2 hours)
3. Wire parameter application (1 hour)
4. Test with real BRENDA data (1 hour)

### Future Enhancements
- SABIO-RK integration (similar to BRENDA)
- Enrichment comparison UI
- Batch enrichment for multiple models
- Enrichment versioning/rollback

---

## References

- Full documentation: `doc/file_panel/PHASE4_BRENDA_INTEGRATION_COMPLETE.md`
- EnrichmentDocument schema: `src/shypn/data/enrichment_document.py`
- Controller implementation: `src/shypn/helpers/brenda_enrichment_controller.py`
- BRENDA API docs: `doc/brenda/BRENDA_INTEGRATION_SESSION.md`

---

**Status: Infrastructure Complete ✅**  
**Ready for Phase 5 (File Panel UI) while waiting for BRENDA activation**
