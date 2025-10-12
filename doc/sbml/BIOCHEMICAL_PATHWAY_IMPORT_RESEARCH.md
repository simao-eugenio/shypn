# Biochemical Pathway Import - Research & Implementation Plan

**Date**: October 12, 2025  
**Purpose**: Enable import of biochemical pathways from standard databases into Petri net models  
**Status**: Research & Planning Phase

---

## 1. BIOCHEMICAL PATHWAY DATABASES

### 1.1 Major Databases Available

| Database | Type | Access | Data Focus |
|----------|------|--------|------------|
| **KEGG** | Commercial/Academic | REST API | Pathways, compounds, reactions, enzymes |
| **Reactome** | Open Source | REST API, GraphQL | Pathways, reactions, species interactions |
| **BioCyc** | Free/Subscription | Web Services | Metabolic pathways, enzymes |
| **SBML BioModels** | Open Source | File Downloads | Curated models with kinetics |
| **MetaCyc** | Free/Subscription | Flat Files | Metabolic pathways |
| **Rhea** | Open Source | REST API | Biochemical reactions |
| **ChEBI** | Open Source | REST API | Chemical entities |

### 1.2 Data Format Standards

**SBML (Systems Biology Markup Language)** ⭐ RECOMMENDED
- XML-based standard format
- Widely adopted (1000+ tools support it)
- Contains: species, reactions, compartments, kinetics
- Level 3 Version 2 is current standard
- Python library: `python-libsbml`

**BioPAX (Biological Pathway Exchange)**
- OWL-based format
- Good for pathway topology
- Limited kinetic information

**GPML (GenMAPP Pathway Markup Language)**
- XML format used by WikiPathways
- Visual layout information included

---

## 2. AVAILABLE DATA TYPES

### 2.1 Structural Data (Always Available)

| Data Type | Description | Petri Net Mapping |
|-----------|-------------|-------------------|
| **Metabolites/Compounds** | Chemical species (glucose, ATP, etc.) | **Places (Tokens)** |
| **Reactions** | Biochemical transformations | **Transitions** |
| **Stoichiometry** | Consumption/production ratios | **Arc Weights** |
| **Compartments** | Cellular locations (cytosol, etc.) | **Place grouping/color** |
| **Pathways** | Named groups of reactions | **Model metadata** |

### 2.2 Kinetic Data (Sometimes Available)

| Data Type | Description | Petri Net Mapping |
|-----------|-------------|-------------------|
| **Rate Laws** | Mathematical formulas (Michaelis-Menten, etc.) | **Transition rate functions** |
| **Rate Constants** | kcat, Km, Ki values | **Transition rate parameters** |
| **Initial Concentrations** | Starting amounts | **Initial token counts** |
| **Enzyme Names** | Catalysts | **Transition metadata** |

### 2.3 Annotation Data

| Data Type | Description | Use Case |
|-----------|-------------|----------|
| **Identifiers** | KEGG IDs, ChEBI IDs, etc. | Cross-referencing, tooltips |
| **Names** | Common and systematic names | Display labels |
| **Formulas** | Chemical formulas (C6H12O6) | Metadata |
| **Pathway Maps** | Layout coordinates | Visual positioning |

---

## 3. DATA MAPPING TO PETRI NETS

### 3.1 Core Mapping Strategy

```
BIOCHEMICAL MODEL          →    PETRI NET MODEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Metabolite/Compound        →    Place
  - Name                   →      Place.name
  - Initial concentration  →      Place.initial_tokens
  - ChEBI/KEGG ID         →      Place.metadata

Reaction                   →    Transition
  - Name                   →      Transition.name
  - Enzyme                 →      Transition.metadata
  - Type (reversible)      →      Two transitions (forward/reverse)

Stoichiometry             →    Arc Weight
  - Reactant coefficient   →      Input arc weight
  - Product coefficient    →      Output arc weight

Kinetic Parameters        →    Transition Rate
  - Rate constant (k)      →      Transition.rate
  - Rate law               →      Transition.rate_function
  - Michaelis constant     →      Transition behavior params

Compartment               →    Visual Grouping
  - Cytosol, Nucleus, etc. →      Place color/region
```

### 3.2 Example: Glycolysis Step

**Biochemical Reaction**:
```
Glucose + ATP  →[Hexokinase]→  Glucose-6-phosphate + ADP
Stoichiometry: 1 glucose + 1 ATP → 1 G6P + 1 ADP
Rate: v = Vmax * [Glucose] / (Km + [Glucose])
```

**Petri Net Representation**:
```
Places:
  - P1: "Glucose" (initial_tokens = 100)
  - P2: "ATP" (initial_tokens = 500)
  - P3: "Glucose-6-phosphate" (initial_tokens = 0)
  - P4: "ADP" (initial_tokens = 50)

Transition:
  - T1: "Hexokinase"
    - type: "continuous"
    - rate: "Vmax * Glucose / (Km + Glucose)"
    - Vmax: 10.0
    - Km: 0.1

Arcs:
  - P1 → T1 (weight = 1)  # Consumes 1 glucose
  - P2 → T1 (weight = 1)  # Consumes 1 ATP
  - T1 → P3 (weight = 1)  # Produces 1 G6P
  - T1 → P4 (weight = 1)  # Produces 1 ADP
```

---

## 4. SBML STRUCTURE & PARSING

### 4.1 SBML File Structure

```xml
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core">
  <model id="glycolysis" name="Glycolysis Pathway">
    
    <!-- Compartments -->
    <listOfCompartments>
      <compartment id="cytosol" name="Cytosol" size="1.0"/>
    </listOfCompartments>
    
    <!-- Species (Metabolites) -->
    <listOfSpecies>
      <species id="glucose" name="Glucose" 
               compartment="cytosol" 
               initialConcentration="5.0"
               hasOnlySubstanceUnits="false"/>
      <species id="atp" name="ATP" 
               compartment="cytosol" 
               initialConcentration="2.5"/>
    </listOfSpecies>
    
    <!-- Reactions -->
    <listOfReactions>
      <reaction id="hexokinase" name="Hexokinase" reversible="false">
        
        <!-- Reactants -->
        <listOfReactants>
          <speciesReference species="glucose" stoichiometry="1"/>
          <speciesReference species="atp" stoichiometry="1"/>
        </listOfReactants>
        
        <!-- Products -->
        <listOfProducts>
          <speciesReference species="g6p" stoichiometry="1"/>
          <speciesReference species="adp" stoichiometry="1"/>
        </listOfProducts>
        
        <!-- Kinetic Law -->
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <apply>
              <divide/>
              <apply>
                <times/>
                <ci> Vmax </ci>
                <ci> glucose </ci>
              </apply>
              <apply>
                <plus/>
                <ci> Km </ci>
                <ci> glucose </ci>
              </apply>
            </apply>
          </math>
          <listOfParameters>
            <parameter id="Vmax" value="10.0"/>
            <parameter id="Km" value="0.1"/>
          </listOfParameters>
        </kineticLaw>
      </reaction>
    </listOfReactions>
  </model>
</sbml>
```

### 4.2 Key SBML Elements to Parse

| Element | Contains | Maps To |
|---------|----------|---------|
| `<species>` | Metabolites | Places |
| `<reaction>` | Transformations | Transitions |
| `<speciesReference>` | Stoichiometry | Arc weights |
| `<kineticLaw>` | Rate equations | Transition rates |
| `<compartment>` | Locations | Visual grouping |
| `<parameter>` | Constants | Transition parameters |

---

## 5. IMPORT PIPELINE ARCHITECTURE

### 5.1 Current Architecture

```
Current File Import Flow:
┌─────────────────┐
│ File Explorer   │
│ (Open .shy)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DocumentModel   │
│ .load_from_file()│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Canvas Loader   │
│ _load_document  │
│ _into_canvas()  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Model Canvas    │
│ (Display)       │
└─────────────────┘
```

### 5.2 Proposed Enhanced Architecture

```
Enhanced Import Pipeline:
┌──────────────────────────────────────────┐
│         File Open Dialog                  │
│  Filter: *.shy, *.sbml, *.xml            │
└────────────────┬─────────────────────────┘
                 │
       ┌─────────┴─────────┐
       │                   │
       ▼                   ▼
┌─────────────┐    ┌─────────────────┐
│ .shy File   │    │ .sbml File      │
│ (Native)    │    │ (Pathway)       │
└──────┬──────┘    └────────┬────────┘
       │                    │
       │                    ▼
       │           ┌─────────────────┐
       │           │ SBML Parser     │
       │           │ (New Module)    │
       │           └────────┬────────┘
       │                    │
       │                    ▼
       │           ┌─────────────────┐
       │           │ Pathway →       │
       │           │ DocumentModel   │
       │           │ Converter       │
       │           └────────┬────────┘
       │                    │
       └────────────────────┘
                 │
                 ▼
       ┌─────────────────┐
       │ DocumentModel   │
       │ (Unified)       │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ Canvas Display  │
       └─────────────────┘
```

### 5.3 New Components Needed

**1. SBML Parser Module** (`src/shypn/data/pathway/sbml_parser.py`)
```python
class SBMLParser:
    def parse_file(self, filepath: str) -> PathwayData
    def extract_species(self, model) -> List[Species]
    def extract_reactions(self, model) -> List[Reaction]
    def extract_kinetics(self, reaction) -> KineticData
```

**2. Pathway Converter** (`src/shypn/data/pathway/pathway_converter.py`)
```python
class PathwayConverter:
    def to_document_model(self, pathway: PathwayData) -> DocumentModel
    def species_to_place(self, species: Species) -> Place
    def reaction_to_transition(self, reaction: Reaction) -> Transition
    def stoichiometry_to_arcs(self, reaction: Reaction) -> List[Arc]
```

**3. Auto-Layout Engine** (`src/shypn/helpers/pathway_layout.py`)
```python
class PathwayLayoutEngine:
    def auto_layout(self, model: DocumentModel) -> None
    def apply_force_directed_layout(self) -> None
    def group_by_compartment(self) -> None
```

---

## 6. IMPLEMENTATION PLAN

### Phase 1: Foundation (Week 1-2)
**Goal**: Set up SBML parsing infrastructure

**Tasks**:
1. ✅ Install dependencies: `pip install python-libsbml`
2. ✅ Create module structure:
   ```
   src/shypn/data/pathway/
   ├── __init__.py
   ├── sbml_parser.py
   ├── pathway_converter.py
   ├── pathway_data.py (data classes)
   └── kinetics_mapper.py
   ```
3. ✅ Implement basic SBML file reading
4. ✅ Extract species and reactions (no kinetics yet)
5. ✅ Write unit tests with sample SBML files

**Deliverable**: Can parse SBML and extract basic structure

---

### Phase 2: Data Conversion (Week 3-4)
**Goal**: Convert pathway data to Petri net format

**Tasks**:
1. ✅ Implement `PathwayConverter.to_document_model()`
2. ✅ Map species → places with initial concentrations
3. ✅ Map reactions → transitions
4. ✅ Map stoichiometry → arc weights
5. ✅ Handle reversible reactions (create two transitions)
6. ✅ Add metadata (IDs, formulas, enzyme names)
7. ✅ Test with complete glycolysis pathway

**Deliverable**: Can convert SBML to DocumentModel

---

### Phase 3: Kinetics Integration (Week 5-6)
**Goal**: Import and apply kinetic parameters

**Tasks**:
1. ✅ Parse rate laws from SBML `<kineticLaw>`
2. ✅ Map rate constants to transition rates
3. ✅ Implement Michaelis-Menten mapping
4. ✅ Handle mass action kinetics
5. ✅ Set transition types (continuous for kinetic models)
6. ✅ Add rate function validation
7. ✅ Test with kinetic SBML models from BioModels

**Deliverable**: Kinetic parameters correctly mapped

---

### Phase 4: UI Integration (Week 7-8)
**Goal**: Integrate into existing import pipeline

**Tasks**:
1. ✅ Update file open dialog filter: `*.shy|*.sbml|*.xml`
2. ✅ Add file type detection in `file_explorer_panel.py`
3. ✅ Route SBML files to new parser
4. ✅ Show progress dialog for large pathways
5. ✅ Add "Import from SBML" menu option
6. ✅ Handle import errors gracefully
7. ✅ Update user documentation

**Deliverable**: Users can open SBML files like native files

---

### Phase 5: Layout & Visualization (Week 9-10)
**Goal**: Automatic layout for imported pathways

**Tasks**:
1. ✅ Implement force-directed graph layout
2. ✅ Use SBML layout extension if available
3. ✅ Group places by compartment (color coding)
4. ✅ Optimize node spacing for readability
5. ✅ Allow manual refinement after import
6. ✅ Save layout with model

**Deliverable**: Imported pathways are visually organized

---

### Phase 6: Database Integration (Week 11-12)
**Goal**: Fetch pathways directly from databases

**Tasks**:
1. ✅ Add "Fetch from Database" dialog
2. ✅ Implement KEGG REST API client (if licensed)
3. ✅ Implement Reactome API client
4. ✅ Search pathways by name/ID
5. ✅ Download and cache SBML files
6. ✅ Handle API rate limits and errors

**Deliverable**: Can fetch pathways without manual download

---

## 7. TECHNICAL SPECIFICATIONS

### 7.1 Dependencies

```python
# requirements.txt additions
python-libsbml>=5.19.0    # SBML parsing
requests>=2.28.0          # API calls for database fetching
beautifulsoup4>=4.11.0    # HTML parsing for web scraping
networkx>=2.8.0           # Graph algorithms for layout
```

### 7.2 Data Classes

```python
# src/shypn/data/pathway/pathway_data.py

@dataclass
class Species:
    id: str
    name: str
    compartment: str
    initial_concentration: float
    formula: Optional[str] = None
    charge: Optional[int] = None
    chebi_id: Optional[str] = None

@dataclass
class Reaction:
    id: str
    name: str
    reversible: bool
    reactants: List[Tuple[str, float]]  # (species_id, stoichiometry)
    products: List[Tuple[str, float]]
    enzyme: Optional[str] = None
    kinetic_law: Optional[KineticLaw] = None

@dataclass
class KineticLaw:
    formula: str
    parameters: Dict[str, float]
    rate_type: str  # 'mass_action', 'michaelis_menten', 'custom'

@dataclass
class PathwayData:
    name: str
    species: List[Species]
    reactions: List[Reaction]
    compartments: Dict[str, str]
    metadata: Dict[str, Any]
```

### 7.3 Converter Example

```python
def reaction_to_transition(self, reaction: Reaction) -> Transition:
    """Convert biochemical reaction to Petri net transition."""
    
    # Create transition
    transition = Transition(
        x=0, y=0,  # Will be set by layout engine
        id=self.get_next_id(),
        name=reaction.name
    )
    
    # Set transition type based on kinetics
    if reaction.kinetic_law:
        transition.transition_type = 'continuous'
        transition.rate = self._parse_rate_law(reaction.kinetic_law)
    else:
        transition.transition_type = 'immediate'
        transition.rate = 1.0
    
    # Store metadata
    transition.metadata = {
        'reaction_id': reaction.id,
        'enzyme': reaction.enzyme,
        'reversible': reaction.reversible
    }
    
    return transition
```

---

## 8. EXAMPLE USE CASES

### Use Case 1: Simple Pathway Import
```python
# User workflow:
1. File → Open → Select "glycolysis.sbml"
2. System parses SBML automatically
3. Converts to Petri net (10 places, 10 transitions)
4. Auto-layouts on canvas
5. User can simulate immediately
```

### Use Case 2: Kinetic Simulation
```python
# Imported pathway with kinetics:
- Transition rates = Michaelis-Menten equations
- Initial tokens = Starting concentrations
- Simulation shows metabolite dynamics over time
- Results plotted in right panel
```

### Use Case 3: Database Fetch
```python
# User workflow:
1. Tools → Fetch Pathway → "Reactome"
2. Search: "Glycolysis"
3. Select pathway from results
4. Download SBML → Convert → Display
5. Pathway ready for analysis
```

---

## 9. CHALLENGES & SOLUTIONS

### Challenge 1: Complex Rate Laws
**Problem**: SBML uses MathML for rate equations  
**Solution**: Parse MathML to Python expressions using `sympy` or custom parser

### Challenge 2: Large Pathways
**Problem**: 100+ species can clutter canvas  
**Solution**: 
- Hierarchical views (expandable subpathways)
- Filter by compartment
- Zoom and pan optimization

### Challenge 3: Reversible Reactions
**Problem**: One SBML reaction = Two Petri net transitions  
**Solution**: 
- Create forward and reverse transitions
- Link them visually (grouped)
- Share kinetic parameters

### Challenge 4: Missing Kinetics
**Problem**: Many SBML files lack rate laws  
**Solution**:
- Use default mass action kinetics
- Allow user to add kinetics later
- Warn when kinetics missing

### Challenge 5: Unit Conversion
**Problem**: SBML uses various units (mM, molecules, etc.)  
**Solution**:
- Parse SBML unit definitions
- Convert to consistent units (e.g., molecules)
- Store unit info in metadata

---

## 10. TESTING STRATEGY

### 10.1 Sample SBML Files

**Source**: https://www.ebi.ac.uk/biomodels/

Test with models of increasing complexity:
1. **Simple**: 5 species, 3 reactions (e.g., BIOMD0000000001)
2. **Medium**: 20 species, 15 reactions (glycolysis)
3. **Complex**: 100+ species, 80+ reactions (complete metabolism)
4. **With Kinetics**: Models with detailed rate laws
5. **Without Kinetics**: Structural models only

### 10.2 Unit Tests

```python
def test_parse_simple_sbml():
    parser = SBMLParser()
    pathway = parser.parse_file('tests/data/simple.sbml')
    assert len(pathway.species) == 5
    assert len(pathway.reactions) == 3

def test_species_to_place():
    species = Species(id='glc', name='Glucose', initial_concentration=5.0)
    converter = PathwayConverter()
    place = converter.species_to_place(species)
    assert place.name == 'Glucose'
    assert place.initial_tokens == 5

def test_stoichiometry_mapping():
    reaction = Reaction(
        id='r1',
        reactants=[('glc', 1), ('atp', 1)],
        products=[('g6p', 1), ('adp', 1)]
    )
    arcs = converter.stoichiometry_to_arcs(reaction)
    assert len(arcs) == 4  # 2 input, 2 output
    assert arcs[0].weight == 1
```

---

## 11. RESOURCES & REFERENCES

### Documentation
- **SBML Specification**: http://sbml.org/Documents/Specifications
- **python-libsbml Tutorial**: http://sbml.org/Software/libSBML/docs/python-api/
- **BioModels Database**: https://www.ebi.ac.uk/biomodels/
- **Reactome API**: https://reactome.org/dev/content-service

### Example Pathways
- **KEGG Glycolysis**: https://www.genome.jp/pathway/map00010
- **Reactome Pathways**: https://reactome.org/
- **BioCyc MetaCyc**: https://metacyc.org/

### Papers
- Hucka et al. (2003) "The systems biology markup language (SBML)"
- Le Novère et al. (2009) "BioModels Database"

---

## 12. ESTIMATED EFFORT

| Phase | Duration | Complexity | Risk |
|-------|----------|------------|------|
| Phase 1: Foundation | 2 weeks | Medium | Low |
| Phase 2: Conversion | 2 weeks | Medium | Medium |
| Phase 3: Kinetics | 2 weeks | High | Medium |
| Phase 4: UI Integration | 2 weeks | Low | Low |
| Phase 5: Layout | 2 weeks | High | Medium |
| Phase 6: Database API | 2 weeks | Medium | High |
| **Total** | **12 weeks** | | |

**Developer Effort**: 1 full-time developer  
**Dependencies**: python-libsbml, requests, networkx

---

## 13. SUMMARY & RECOMMENDATION

### ✅ FEASIBILITY: **HIGH**

**Yes, it is definitely possible to fetch and import biochemical pathway data!**

### Key Findings:

1. ✅ **Standard formats exist** (SBML is the gold standard)
2. ✅ **Open databases available** (Reactome, BioModels)
3. ✅ **Python libraries ready** (python-libsbml)
4. ✅ **Clear mapping to Petri nets**:
   - Metabolites → Places (tokens)
   - Reactions → Transitions
   - Stoichiometry → Arc weights
   - Kinetics → Transition rates
5. ✅ **Integration path is straightforward**

### Recommended Approach:

**Start with Phase 1-3** (6 weeks):
- Implement SBML parser
- Convert to Petri nets
- Map kinetics to rates

This provides immediate value and can be extended later with:
- Advanced layouts (Phase 5)
- Direct database fetching (Phase 6)

### Quick Win Strategy:

**Minimal Viable Import** (2 weeks):
1. Parse SBML species and reactions only
2. Convert to places and transitions
3. Use fixed stoichiometry (weight=1)
4. Manual layout initially
5. Add to existing import pipeline

This gets basic pathway import working quickly, proving the concept!

---

**Next Steps**: Approve plan → Begin Phase 1 → Iterative development

