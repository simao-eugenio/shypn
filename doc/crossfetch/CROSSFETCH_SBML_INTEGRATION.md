# CrossFetch SBML Integration Architecture

**Date:** October 13, 2025  
**Status:** In Development  
**Purpose:** Document how CrossFetch integrates as PRE-processor for SBML import

---

## 🎯 Core Concept

CrossFetch is a **PRE-processor** that enriches SBML files BEFORE they go through Shypn's existing import pipeline.

**NOT** a replacement for SBML import - it's an enhancement layer!

---

## 📊 Complete Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INPUT                                    │
│                    Pathway ID                                    │
│              (e.g., "BIOMD0000000002")                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Fetch Primary Data (BioModels)                         │
│  ────────────────────────────────────────────                   │
│  • Download SBML file from BioModels                            │
│  • This SBML contains:                                          │
│    ✓ Pathway structure (species, reactions)                     │
│    ✓ Stoichiometry                                              │
│    ✓ Compartments                                               │
│    ? Some concentrations (often incomplete)                     │
│    ? Some kinetics (often incomplete)                           │
│    ? Some annotations (often incomplete)                        │
│                                                                  │
│  Output: Base SBML (has structure, lacks details)               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: PRE-PROCESSING - CrossFetch Enrichment ⭐ NEW!         │
│  ──────────────────────────────────────────────────             │
│  Module: src/shypn/crossfetch/sbml_enricher.py                 │
│                                                                  │
│  Process:                                                        │
│  1. Analyze base SBML for missing data                          │
│     - Which species lack initial concentrations?                │
│     - Which reactions lack kinetic laws?                        │
│     - Which elements lack annotations?                          │
│                                                                  │
│  2. Fetch missing data from external sources                    │
│     - KEGG: kinetic parameters, pathway topology                │
│     - Reactome: interaction details, annotations                │
│     - ChEBI: compound properties (future)                       │
│                                                                  │
│  3. Merge fetched data into SBML structure                      │
│     - Add <initialConcentration> to species                     │
│     - Add <kineticLaw> to reactions                             │
│     - Add <annotation> RDF blocks                               │
│                                                                  │
│  Output: Enriched SBML (structure + complete details)           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: POST-PROCESSING - Existing Shypn Converters            │
│  ───────────────────────────────────────────────────            │
│  Modules: src/shypn/data/pathway/                               │
│                                                                  │
│  3A. SBMLParser (sbml_parser.py)                                │
│      • Parse enriched SBML into PathwayData                     │
│      • Extract species → Species objects                        │
│      • Extract reactions → Reaction objects                     │
│      • Extract kinetics → KineticLaw objects                    │
│                                                                  │
│  3B. PathwayConverter (pathway_converter.py)                    │
│      • Convert PathwayData to Shypn Petri net                   │
│      • Species → Place (tokens from concentrations!)            │
│      • Reactions → Transition (rates from kinetics!)            │
│      • Stoichiometry → Arc (weights)                            │
│                                                                  │
│  3C. PathwayPostProcessor (pathway_postprocessor.py)            │
│      • Auto-layout algorithm                                    │
│      • Arc routing and aesthetics                               │
│      • Visual refinements                                       │
│                                                                  │
│  Output: Shypn Petri Net Model (.shy file)                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│              Render & Simulate in Shypn UI                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Design Decisions

### 1. **CrossFetch is a PRE-processor**
   - Operates BEFORE existing parsers
   - Enriches SBML at the XML level
   - Transparent to existing conversion code

### 2. **SBML is the primary format**
   - BioModels provides structure (species, reactions)
   - CrossFetch provides details (concentrations, kinetics)
   - Merged SBML goes through standard pipeline

### 3. **Existing code is unchanged**
   - SBMLParser doesn't need modifications
   - PathwayConverter sees richer data automatically
   - PostProcessor works as before

### 4. **Enrichment is optional**
   - User can choose to enrich or not
   - Checkbox in import dialog: "Enrich with external data"
   - Falls back gracefully if enrichment fails

---

## 📁 File Organization

```
src/shypn/
├── crossfetch/                    # CrossFetch module (PRE-processing)
│   ├── sbml_enricher.py          # ⭐ Main enricher class
│   ├── core/
│   │   └── enrichment_pipeline.py # Orchestrates fetching
│   ├── fetchers/                 # Data source fetchers
│   │   ├── kegg_fetcher.py
│   │   ├── biomodels_fetcher.py
│   │   └── reactome_fetcher.py
│   └── enrichers/                # Data type enrichers
│       ├── concentration_enricher.py
│       ├── kinetics_enricher.py
│       └── annotation_enricher.py
│
├── data/pathway/                 # Existing SBML converters (POST-processing)
│   ├── sbml_parser.py           # Parse SBML → PathwayData
│   ├── pathway_converter.py     # PathwayData → Shypn objects
│   └── pathway_postprocessor.py # Layout & refinements
│
└── helpers/
    └── sbml_import_panel.py     # UI for SBML import (will add enrichment checkbox)
```

---

## 🔄 Data Flow Example

### Input: `BIOMD0000000002` (MAPK cascade)

#### Step 1: Base SBML from BioModels
```xml
<model id="BIOMD0000000002" name="Kholodenko2000_MAPK_feedback">
  <listOfSpecies>
    <species id="MKKK" name="MKKK" compartment="cell">
      <!-- NO initialConcentration! -->
    </species>
    <species id="MKKK_P" name="MKKK_P" compartment="cell">
      <!-- NO initialConcentration! -->
    </species>
    ...
  </listOfSpecies>
  
  <listOfReactions>
    <reaction id="R1" name="MKKK phosphorylation">
      <listOfReactants>
        <speciesReference species="MKKK" stoichiometry="1"/>
      </listOfReactants>
      <listOfProducts>
        <speciesReference species="MKKK_P" stoichiometry="1"/>
      </listOfProducts>
      <!-- NO kineticLaw! -->
    </reaction>
    ...
  </listOfReactions>
</model>
```

#### Step 2: CrossFetch Enrichment

**Analysis:**
- Missing: 5 species without initial concentrations
- Missing: 8 reactions without kinetic laws

**Fetching:**
- KEGG: Find hsa04010 (MAPK signaling pathway)
  - Get typical MKKK concentration: 0.1 µM
  - Get phosphorylation rate constant: k = 0.02 s⁻¹
- Reactome: Get detailed interaction data

**Merging:**
```xml
<model id="BIOMD0000000002" name="Kholodenko2000_MAPK_feedback">
  <listOfSpecies>
    <species id="MKKK" name="MKKK" compartment="cell" 
             initialConcentration="0.0001">  <!-- ⭐ ADDED! -->
      <annotation>
        <rdf:RDF>
          <bqbiol:is rdf:resource="http://identifiers.org/kegg.compound/C00035"/>
          <!-- ⭐ ADDED KEGG cross-reference -->
        </rdf:RDF>
      </annotation>
    </species>
    ...
  </listOfSpecies>
  
  <listOfReactions>
    <reaction id="R1" name="MKKK phosphorylation">
      <listOfReactants>
        <speciesReference species="MKKK" stoichiometry="1"/>
      </listOfReactants>
      <listOfProducts>
        <speciesReference species="MKKK_P" stoichiometry="1"/>
      </listOfProducts>
      <kineticLaw>  <!-- ⭐ ADDED! -->
        <math xmlns="http://www.w3.org/1998/Math/MathML">
          <apply>
            <times/>
            <ci>k</ci>
            <ci>MKKK</ci>
          </apply>
        </math>
        <listOfParameters>
          <parameter id="k" value="0.02" units="per_second"/>
          <!-- ⭐ ADDED rate constant from KEGG -->
        </listOfParameters>
      </kineticLaw>
    </reaction>
    ...
  </listOfReactions>
</model>
```

#### Step 3: Existing Converters

**SBMLParser** extracts:
```python
species_data = {
    'id': 'MKKK',
    'name': 'MKKK',
    'initial_concentration': 0.0001,  # ← From enriched SBML!
    'compartment': 'cell'
}

reaction_data = {
    'id': 'R1',
    'name': 'MKKK phosphorylation',
    'kinetic_law': {
        'formula': 'k * MKKK',
        'parameters': {'k': 0.02}  # ← From enriched SBML!
    }
}
```

**PathwayConverter** creates:
```python
place_mkkk = Place(
    x=100, y=100,
    id=1, name='P1',
    label='MKKK',
    tokens=100,  # ← Converted from 0.0001 M
    initial_marking=100
)

transition_r1 = Transition(
    x=150, y=150,
    id=1, name='T1',
    label='MKKK phosphorylation',
    rate=0.02  # ← From enriched kinetics!
)
```

**Final result:** Rich Shypn model with realistic initial conditions and rates!

---

## 🚀 Implementation Status

### ✅ Completed
- [x] CrossFetch fetchers (KEGG, BioModels, Reactome)
- [x] CrossFetch enrichers (Concentration, Kinetics, Annotation)
- [x] EnrichmentPipeline orchestration
- [x] Quality scoring and source selection
- [x] SBMLEnricher class (PRE-processor)

### 🚧 In Progress
- [ ] SBML XML manipulation (concentration merging)
- [ ] SBML XML manipulation (kinetics merging)
- [ ] SBML annotation merging (RDF/XML)

### 📋 Planned
- [ ] Add enrichment checkbox to sbml_import_panel.py
- [ ] Wire SBMLEnricher into import workflow
- [ ] Progress reporting during enrichment
- [ ] Error handling and fallback
- [ ] Integration tests with real BioModels

---

## 🧪 Testing Strategy

### Test Cases

1. **Full enrichment workflow**
   ```bash
   python3 demo_sbml_enrichment.py BIOMD0000000206
   ```
   - Fetch glycolysis model from BioModels
   - Enrich with KEGG data
   - Verify concentrations added
   - Verify kinetics added

2. **Partial enrichment (missing data)**
   - SBML with some concentrations already set
   - Should only enrich missing values
   - Should not overwrite existing data

3. **Enrichment failure handling**
   - Network error during fetch
   - Should fall back to base SBML
   - Should log warning but not crash

4. **End-to-end integration**
   - Enrich SBML → Parse → Convert → Render
   - Verify tokens reflect concentrations
   - Verify transition rates reflect kinetics

---

## 💡 Future Enhancements

1. **Multiple enrichment strategies**
   - Conservative: Only fill missing data
   - Aggressive: Override with higher-quality data
   - User-configurable preference

2. **Enrichment preview**
   - Show what will be enriched before applying
   - Let user choose which data to accept

3. **Enrichment metadata**
   - Track provenance (where each value came from)
   - Store in SBML annotations
   - Allow rollback/inspection

4. **Additional sources**
   - ChEBI for compound properties
   - UniProt for protein data
   - MetaCyc for metabolic pathways

---

## 📚 Related Documentation

- [CROSSFETCH_STATUS.md](CROSSFETCH_STATUS.md) - Overall project status
- [CROSSFETCH_PHASE4_ENRICHERS.md](CROSSFETCH_PHASE4_ENRICHERS.md) - Enricher details
- [CROSSFETCH_PIPELINE_INTEGRATION_COMPLETE.md](CROSSFETCH_PIPELINE_INTEGRATION_COMPLETE.md) - Pipeline architecture

---

**Last Updated:** October 13, 2025  
**Next Milestone:** Wire SBMLEnricher into sbml_import_panel.py
