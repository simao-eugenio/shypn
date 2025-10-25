# Report Panel Design Specification

**Date:** October 25, 2025  
**Purpose:** Scientific report panel organized by SHYpn's core modeling concepts  
**Architecture:** CategoryFrame expanders with rich content views

---

## Overview

The Report Panel provides a comprehensive, publication-ready view of the project organized by scientific modeling concepts that researchers need to document their work.

---

## Panel Structure

```
REPORT Panel (Main Tab)
├── MODEL STRUCTURE (Petri net + biological entities)
├── TOPOLOGY (Network connectivity analysis)
├── KINETIC PARAMETERS (Rate constants + provenance)
├── SIMULATION CONFIGURATION (Setup + initial conditions)
├── SIMULATION RESULTS (Time series + analysis)
├── VALIDATION & QUALITY (Verification + experimental)
├── PROVENANCE & LINEAGE (Sources + transformations)
├── METADATA & ANNOTATIONS (Context + references)
└── [Export Buttons: PDF, HTML, Copy, Print]
```

---

## Category Details

### 1. MODEL STRUCTURE
**What is being modeled?**

**Content:**
- Petri Net Components
  - Places count (species, metabolites)
  - Transitions count (reactions, processes)
  - Arcs count (connections)
- Biological Entities
  - Metabolites list with identifiers
  - Enzymes list with EC numbers
  - Protein complexes
- Model Diagram (embedded visualization)

**Data Sources:**
- `model_canvas.get_places()`
- `model_canvas.get_transitions()`
- `model_canvas.get_arcs()`

### 2. TOPOLOGY
**How is it connected?**

**Content:**
- Topology Metrics
  - Node degree distribution
  - Connected components
  - Cycles detected
  - Hub nodes
- Pathway Modules
  - Identified subpathways
  - Modular structure
- Connectivity Analysis
  - Source/sink nodes
  - Branching points

**Data Sources:**
- Analysis results from topology analyzer
- Graph metrics computed from model

### 3. KINETIC PARAMETERS
**What are the rates?**

**Content:**
- Parameter Summary (counts by type)
  - Km (substrate affinity)
  - Kcat (turnover number)
  - Ki (inhibition constant)
  - Vmax (maximum velocity)
- Parameter Sources (Provenance)
  - BRENDA contributions
  - SABIO-RK contributions
  - Literature citations
- Quality Assessment
  - Confidence levels (High/Medium/Low)
  - Coverage percentage
- Organism Context
  - Parameters by organism

**Data Sources:**
- `project.pathways` (enrichments)
- `EnrichmentDocument` metadata
- Transition parameters in model

### 4. SIMULATION CONFIGURATION
**How to run it?**

**Content:**
- Simulation Method
  - Type (stochastic/deterministic)
  - Algorithm (Gillespie/ODE solver)
  - Time span
  - Step size
- Initial Conditions
  - Species → initial marking/concentration table
- Boundary Conditions
  - Fixed species
  - Variable species

**Data Sources:**
- Simulation settings (future)
- Model initial markings

### 5. SIMULATION RESULTS
**What happened?**

**Content:**
- Simulation Runs Summary
  - Total runs
  - Success/failure counts
- Time Series Data
  - Plots (concentration vs time)
- Steady State Analysis
  - Equilibrium values
- Statistical Summary
  - Mean, std dev, confidence intervals

**Data Sources:**
- Simulation results (future integration)

### 6. VALIDATION & QUALITY
**Is it correct?**

**Content:**
- Model Checks
  - Mass conservation verification
  - Stoichiometry validation
  - Thermodynamic consistency
- Experimental Validation
  - Comparison to experimental data
  - R² value, RMSE
- Quality Metrics
  - Parameter coverage
  - Citation count
  - Confidence score

**Data Sources:**
- Validation results (future)
- Quality metrics computed

### 7. PROVENANCE & LINEAGE
**Where did it come from?**

**Content:**
- Source Pathways
  - KEGG pathways (ID, name, date)
  - SBML models (name, file, date)
- Transformation Pipeline
  - Conversion steps
  - Enrichment applications
  - Merge operations
- Change History
  - Timeline of all operations

**Data Sources:**
- `project.pathways.list_pathways()`
- `PathwayDocument` metadata
- `EnrichmentDocument` metadata

### 8. METADATA & ANNOTATIONS
**What else should I know?**

**Content:**
- Model Metadata
  - Title, description
  - Keywords
  - Author, date
- Biological Context
  - Organism, tissue
  - Cellular compartment
- External References
  - PubMed IDs
  - DOIs
  - Database links
- SBML/MIRIAM Annotations
  - CV terms
  - Biological qualifiers

**Data Sources:**
- Project metadata
- SBML annotations
- Pathway metadata

---

## Implementation Files

```
src/shypn/ui/
└── report_panel.py                    # Main panel container

src/shypn/helpers/report/
├── __init__.py
├── model_structure_controller.py      # Category 1
├── topology_controller.py             # Category 2
├── parameters_controller.py           # Category 3
├── simulation_config_controller.py    # Category 4
├── simulation_results_controller.py   # Category 5
├── validation_controller.py           # Category 6
├── provenance_controller.py           # Category 7
├── metadata_controller.py             # Category 8
└── export_controller.py               # PDF/HTML/Print
```

---

## Export Formats

### PDF Export
- Professional layout
- Embedded images/plots
- Proper pagination
- Table of contents

### HTML Export
- Responsive design
- Interactive plots (if applicable)
- Printable CSS

### Markdown Export
- Plain text format
- Compatible with GitHub/GitLab
- Easy to version control

### Copy to Clipboard
- Formatted text
- Ready to paste into documents

---

## User Workflows

### Workflow 1: Generate Publication Report
```
1. User opens Report panel
2. Expands all categories to review
3. Clicks [Export PDF]
4. Selects destination
5. Gets publication-ready PDF with:
   - Model structure
   - Parameters with citations
   - Validation metrics
   - Full provenance
```

### Workflow 2: Quick Parameter Check
```
1. User opens Report panel
2. Expands KINETIC PARAMETERS
3. Reviews parameter counts and sources
4. Checks confidence levels
5. Copies citation list for reference
```

### Workflow 3: Share Model Documentation
```
1. User opens Report panel
2. Reviews all sections
3. Clicks [Export HTML]
4. Shares HTML file with collaborators
5. Collaborators view in browser
```

---

## Integration Points

### With File Panel
- Minimal overlap (File Panel = quick overview)
- Report Panel = comprehensive details

### With Pathway Panel
- Uses same data sources (project.pathways)
- Read-only view (no editing)

### With Model Canvas
- Extracts structure information
- Displays topology metrics
- No modification of model

### With Project
- Reads all metadata
- Updates when project changes
- No writes (read-only report)

---

## Implementation Timeline

### Phase 6a: Core Panel Structure (1 day)
- Create `report_panel.py`
- Set up category framework
- Add export button placeholders

### Phase 6b: Priority Categories (3 days)
**Day 1:** MODEL STRUCTURE + TOPOLOGY
- Extract model components
- Compute basic metrics

**Day 2:** KINETIC PARAMETERS + PROVENANCE
- Aggregate enrichment data
- Build lineage view

**Day 3:** METADATA
- Extract annotations
- Format references

### Phase 6c: Future Categories (placeholders)
- SIMULATION CONFIG (0.5 days)
- SIMULATION RESULTS (0.5 days)
- VALIDATION (0.5 days)

### Phase 6d: Export Functions (2 days)
- PDF generation
- HTML export
- Copy/print functions

**Total: 7-8 days**

---

## Success Criteria

✅ All 8 categories display correctly  
✅ Data auto-updates when project changes  
✅ Export to PDF works  
✅ Export to HTML works  
✅ Reports are publication-ready  
✅ Performance is acceptable (< 2s to generate)  
✅ UI follows SHYpn patterns (CategoryFrame)

---

## Next Steps

1. Finish File Panel (PROJECT INFORMATION spreadsheet view)
2. Begin Report Panel implementation
3. Start with MODEL STRUCTURE + PROVENANCE (most valuable)
4. Add export functions
5. Iterate based on user feedback
