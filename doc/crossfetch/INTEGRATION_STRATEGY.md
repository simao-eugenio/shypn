# CrossFetch Integration Strategy

**Date:** October 13, 2025  
**Status:** Planning Document

## Current State vs. Target State

### Current State ❌

**CrossFetch is isolated:**
```
┌─────────────────────────────────┐
│   Shypn Application             │
│   - Load .shy files             │
│   - Edit pathways               │
│   - Simulate                    │
│   - Save .shy files             │
└─────────────────────────────────┘
         (No connection)
              ↕️
┌─────────────────────────────────┐
│   CrossFetch System             │
│   - Fetch from databases        │
│   - Enrich mock objects         │
│   - Demo scripts only           │
└─────────────────────────────────┘
```

**Problems:**
- CrossFetch uses mock pathway objects
- No connection to real .shy file I/O
- No UI integration
- Manual workflow only

---

### Target State ✅

**CrossFetch integrated at multiple levels:**

```
┌─────────────────────────────────────────────────────────┐
│                  Shypn Application                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Shypn UI (PyQt6)                        │  │
│  │  - Menu: "Enrich from BioModels..."             │  │
│  │  - Dialog: Select data types to enrich          │  │
│  │  - Progress: Show fetch/enrich progress         │  │
│  │  - Results: Display enrichment summary          │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       ↓                                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │      Pathway Model (Python objects)              │  │
│  │  - Places, Transitions, Arcs                     │  │
│  │  - Properties, Metadata                          │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       ↓                                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │      File I/O (.shy format)                      │  │
│  │  - Load pathway from .shy                        │  │
│  │  - Save enriched pathway to .shy                 │  │
│  └────────────────────┬─────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│              CrossFetch System (API)                     │
├─────────────────────────────────────────────────────────┤
│  • EnrichmentPipeline                                   │
│  • Fetchers (KEGG, BioModels, Reactome)                │
│  • Enrichers (Concentration, Kinetics, etc.)           │
│  • Quality Scoring & Source Selection                   │
└─────────────────────────────────────────────────────────┘
```

---

## Integration Levels

### Level 1: API Integration (Easiest) ⭐ **Recommended First**

**Goal:** CrossFetch can enrich real Shypn pathway objects

**Requirements:**
1. Identify Shypn's pathway data model classes
2. Ensure enrichers work with real objects (not mocks)
3. Test with actual .shy files

**Code Changes:**
```python
# Instead of:
from demo import MockPathway, MockPlace, MockTransition

# Use:
from shypn.models import Pathway, Place, Transition

# Then enrichers work directly:
pathway = Pathway.load("glycolysis.shy")
pipeline.enrich(pathway_file, request, pathway)
pathway.save("glycolysis_enriched.shy")
```

**Effort:** 1-2 hours  
**Benefits:** CrossFetch immediately usable as library

---

### Level 2: CLI Integration (Medium)

**Goal:** Command-line tool for batch enrichment

**Implementation:**
```bash
# Command-line usage
shypn-enrich glycolysis.shy --sources biomodels,reactome \
                            --types concentrations,kinetics \
                            --output glycolysis_enriched.shy

# Batch enrichment
shypn-enrich models/*.shy --sources biomodels --output enriched/
```

**Code:**
```python
# New file: src/shypn/crossfetch/cli.py
import click
from pathlib import Path

@click.command()
@click.argument('pathway_file', type=click.Path(exists=True))
@click.option('--sources', '-s', multiple=True)
@click.option('--types', '-t', multiple=True)
@click.option('--output', '-o', type=click.Path())
def enrich(pathway_file, sources, types, output):
    """Enrich pathway from external sources."""
    pipeline = EnrichmentPipeline()
    request = EnrichmentRequest(...)
    
    pathway = load_pathway(pathway_file)
    results = pipeline.enrich(Path(pathway_file), request, pathway)
    
    if output:
        pathway.save(output)
    
    print_results(results)
```

**Effort:** 2-4 hours  
**Benefits:** Scriptable, batch processing, CI/CD integration

---

### Level 3: UI Integration (Advanced)

**Goal:** Menu items and dialogs in Shypn GUI

**Implementation:**

#### A. Menu Integration
```python
# In Shypn main window menu
menu_enrich = QMenu("&Enrich", self)
menu_enrich.addAction("Fetch from BioModels...", self.enrich_from_biomodels)
menu_enrich.addAction("Fetch from KEGG...", self.enrich_from_kegg)
menu_enrich.addAction("Fetch from Reactome...", self.enrich_from_reactome)
menu_enrich.addSeparator()
menu_enrich.addAction("Enrich Settings...", self.enrich_settings)
self.menuBar().addMenu(menu_enrich)
```

#### B. Enrichment Dialog
```python
class EnrichmentDialog(QDialog):
    """Dialog for configuring enrichment."""
    
    def __init__(self, pathway, parent=None):
        super().__init__(parent)
        self.pathway = pathway
        self.setup_ui()
    
    def setup_ui(self):
        # Data type selection
        self.checkboxes = {
            'concentrations': QCheckBox("Concentrations"),
            'kinetics': QCheckBox("Kinetic Parameters"),
            'interactions': QCheckBox("Protein Interactions"),
            'annotations': QCheckBox("Annotations")
        }
        
        # Source selection
        self.sources = {
            'biomodels': QCheckBox("BioModels"),
            'kegg': QCheckBox("KEGG"),
            'reactome': QCheckBox("Reactome")
        }
        
        # Buttons
        self.btn_enrich = QPushButton("Enrich")
        self.btn_enrich.clicked.connect(self.do_enrichment)
    
    def do_enrichment(self):
        # Create request from UI
        data_types = [k for k, cb in self.checkboxes.items() if cb.isChecked()]
        sources = [k for k, cb in self.sources.items() if cb.isChecked()]
        
        # Show progress dialog
        progress = QProgressDialog("Fetching data...", "Cancel", 0, 100, self)
        progress.show()
        
        # Run enrichment
        pipeline = EnrichmentPipeline()
        request = EnrichmentRequest(
            pathway_id=self.pathway.id,
            data_types=data_types,
            preferred_sources=sources
        )
        
        results = pipeline.enrich(self.pathway.file, request, self.pathway)
        
        # Show results
        self.show_results(results)
```

#### C. Results Display
```python
class EnrichmentResultsDialog(QDialog):
    """Show enrichment results."""
    
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.results = results
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Summary
        summary = QLabel(f"Enriched {results['statistics']['successful_enrichments']} data types")
        layout.addWidget(summary)
        
        # Details table
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Data Type", "Source", "Objects Modified", "Status"])
        
        for enrichment in results['applied_enrichments']:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(enrichment['data_type']))
            table.setItem(row, 1, QTableWidgetItem(enrichment['best_source']))
            table.setItem(row, 2, QTableWidgetItem(str(enrichment['objects_modified'])))
            table.setItem(row, 3, QTableWidgetItem("✓" if enrichment['success'] else "✗"))
        
        layout.addWidget(table)
        self.setLayout(layout)
```

**Effort:** 1-2 days  
**Benefits:** User-friendly, visual feedback, integrated workflow

---

## Integration Roadmap

### Phase 1: Foundation (1-2 hours) ⭐ **START HERE**

**Tasks:**
1. ✅ Identify Shypn's pathway model classes
   ```python
   # Find in codebase:
   grep -r "class.*Pathway" src/
   grep -r "class.*Place" src/
   grep -r "class.*Transition" src/
   ```

2. ✅ Test enrichers with real objects
   ```python
   # Create adapter test:
   from shypn.models import Pathway
   pathway = Pathway.load("test.shy")
   
   # Test each enricher:
   enricher = ConcentrationEnricher()
   result = enricher.apply(pathway, fetch_result)
   
   # Verify:
   assert result.success
   assert result.objects_modified > 0
   ```

3. ✅ Create integration demo
   ```python
   # demo_real_integration.py
   # Shows enrichment of actual .shy file
   ```

**Deliverable:** CrossFetch works with real Shypn pathways

---

### Phase 2: API Layer (2-4 hours)

**Tasks:**
1. Create pathway adapter if needed
   ```python
   # src/shypn/crossfetch/adapters/shypn_adapter.py
   class ShypnPathwayAdapter:
       """Adapts Shypn pathways for CrossFetch."""
       
       def __init__(self, shypn_pathway):
           self.pathway = shypn_pathway
       
       @property
       def places(self):
           return self.pathway.get_places()
       
       @property
       def transitions(self):
           return self.pathway.get_transitions()
   ```

2. Create convenience functions
   ```python
   # src/shypn/crossfetch/integration.py
   def enrich_pathway_file(
       filepath: Path,
       data_types: List[str],
       sources: Optional[List[str]] = None
   ) -> Dict[str, Any]:
       """
       One-function enrichment for .shy files.
       
       Example:
           results = enrich_pathway_file(
               Path("glycolysis.shy"),
               data_types=["concentrations", "kinetics"],
               sources=["biomodels"]
           )
       """
       # Load
       pathway = load_shy_file(filepath)
       
       # Enrich
       pipeline = EnrichmentPipeline()
       request = EnrichmentRequest(...)
       results = pipeline.enrich(filepath, request, pathway)
       
       # Save
       if results['statistics']['successful_enrichments'] > 0:
           save_shy_file(filepath, pathway)
       
       return results
   ```

**Deliverable:** Simple API for enrichment

---

### Phase 3: CLI Tool (2-4 hours)

**Tasks:**
1. Implement CLI using Click
2. Add progress indicators
3. Support batch processing
4. Add configuration file support

**Deliverable:** `shypn-enrich` command-line tool

---

### Phase 4: UI Integration (1-2 days)

**Tasks:**
1. Add menu items
2. Create enrichment dialog
3. Show progress during fetch/enrich
4. Display results
5. Add undo/rollback support

**Deliverable:** Full UI integration

---

## Current Answer to Your Question

**Q: Is CrossFetch a pre-process or standalone API?**

**A:** Currently **neither** - it's in a transitional state:

- ✅ Core functionality complete
- ✅ All enrichers working
- ✅ Pipeline integration done
- ❌ **NOT** integrated with real .shy files yet
- ❌ **NOT** integrated with Shypn UI yet

**What it SHOULD be:** **Both!**

1. **Standalone API** for programmatic use
2. **CLI tool** for batch processing  
3. **Integrated workflow** in Shypn UI

---

## Recommended Next Steps

### Option A: Quick API Integration (2 hours)
**Focus:** Make it work with real .shy files

**Tasks:**
1. Find Shypn pathway model classes
2. Test enrichers with real objects
3. Create load/enrich/save workflow
4. Document usage

**Outcome:** CrossFetch usable as library

---

### Option B: Full Integration (1 week)
**Focus:** Complete Shypn integration

**Tasks:**
1. API integration (Option A)
2. CLI tool implementation
3. UI menu and dialogs
4. User documentation

**Outcome:** Fully integrated feature

---

### Option C: Standalone Tool First (3 days)
**Focus:** Make it useful independently

**Tasks:**
1. Package as standalone tool
2. CLI implementation
3. Configuration files
4. Documentation

**Outcome:** Useful tool even without Shypn GUI

---

## My Recommendation

**Start with Option A** (Quick API Integration):

1. **Find the Shypn pathway classes** (30 min)
2. **Test with one enricher** (30 min)
3. **Create adapter if needed** (1 hour)
4. **Document integration** (30 min)

This gives you:
- ✅ Working integration
- ✅ Foundation for CLI/UI
- ✅ Immediate usability
- ✅ Low risk

Then decide: CLI next, or UI integration?

---

## Questions to Answer

Before proceeding, we need to know:

1. **Where are Shypn's pathway model classes?**
   - `src/shypn/models.py`?
   - `src/shypn/core/pathway.py`?
   - Something else?

2. **How are .shy files loaded/saved?**
   - Is there a `Pathway.load()` method?
   - Is there a separate parser?

3. **What's the data structure?**
   - Do places have `id`, `name`, `initial_marking`?
   - Do transitions have `id`, `name`, `transition_type`?
   - Do arcs have `source`, `target`, `weight`?

4. **What's the priority?**
   - Quick library integration?
   - Full UI integration?
   - Standalone tool?

Let me help you find the answers and integrate CrossFetch properly!
