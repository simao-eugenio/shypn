# KEGG Biological Petri Net Import

## Overview

KEGG pathways can optionally import as **Biological Petri Nets** when enzyme-reaction associations are detected. By setting `create_enzyme_places=True`, enzyme entries (gene/enzyme/ortholog types) with reaction attributes are converted to **test arcs** (non-consuming catalysts).

**⚠️ IMPORTANT**: By default (`create_enzyme_places=False`), KEGG imports produce **clean, human-readable layouts** matching the original KEGG pathway visualization. Enzyme places are NOT created to avoid layout disruption.

## Layout Consideration

### Default Behavior (Recommended for Visualization)

```python
# Default: Clean KEGG layout without enzyme places
document = convert_pathway(pathway)
```

- ✅ **Clean layout**: Matches original KEGG visualization
- ✅ **Human-readable**: No enzyme clutter
- ✅ **Classical Petri Net**: Standard PN semantics
- ⚠️ **Enzymes implicit**: Not represented as places

### Biological Analysis Mode (Opt-in)

```python
# Opt-in: Biological PN with explicit enzyme places
document = convert_pathway(pathway, create_enzyme_places=True)
```

- ✅ **Biological accuracy**: Enzymes as explicit places
- ✅ **Test arcs**: Non-consuming catalysts
- ✅ **Topology analysis**: Dependency & Coupling, Regulatory Structure
- ⚠️ **Layout disruption**: May affect visual organization

## Implementation

### Theory: Biological Petri Net

A Biological Petri Net extends classical Petri nets with the Σ component:

**BioPN = (P, T, F, W, M₀, K, Φ, Σ, Θ, Δ)**

Where:
- **Σ: T → 2^P** - Maps transitions to their regulatory/catalyst places
- **Σ(t) = {p | arc(p,t) is test arc}**

Test arcs represent **catalysts** (enzymes) that enable reactions without being consumed.

### KEGG Data Model

KEGG represents enzymes differently from SBML:

**SBML**: Explicit modifiers per reaction
```xml
<reaction id="R00710">
  <listOfModifiers>
    <modifierSpeciesReference species="enzyme1"/>
  </listOfModifiers>
</reaction>
```

**KEGG**: Implicit enzyme-reaction associations via entry attributes
```xml
<!-- Enzyme entry with reaction attribute -->
<entry id="3" name="gene:12345" type="gene" reaction="rn:R00710">
  <graphics name="Hexokinase" x="150" y="50"/>
</entry>

<!-- Reaction -->
<reaction id="4" name="rn:R00710" type="irreversible">
  <substrate id="1" name="cpd:C00031"/>
  <product id="2" name="cpd:C00068"/>
</reaction>
```

The enzyme entry's `reaction` attribute (`rn:R00710`) links it to the reaction it catalyzes.

## Implementation Details

### Enhanced KEGG Importer

**File**: `src/shypn/importer/kegg/pathway_converter.py`

#### 1. Enzyme Place Creation

Enzyme entries (type="gene"/"enzyme"/"ortholog") with reaction attributes now become places:

```python
# Phase 1: Create places from compounds AND enzyme entries
for entry_id, entry in pathway.entries.items():
    if entry.is_gene() and entry.reaction:
        # Create enzyme place
        place = Place(x, y, place_id, place_name, label=label)
        place.tokens = 1  # Enzymes typically present/active
        place.metadata['is_enzyme'] = True
        place.metadata['catalyzes_reaction'] = entry.reaction
        document.places.append(place)
        place_map[entry.id] = place
```

#### 2. KEGGEnzymeConverter Class

New converter class implements Σ component:

```python
class KEGGEnzymeConverter:
    """Converts KEGG enzyme entries to test arcs (Biological Petri Net).
    
    For each enzyme entry with a reaction attribute:
    - enzyme_entry.type in ("gene", "enzyme", "ortholog")
    - enzyme_entry.reaction = "rn:R00710" (KEGG reaction ID)
    - Create test arc: enzyme_place → reaction_transition
    """
    
    def convert(self) -> List[TestArc]:
        test_arcs = []
        for entry_id, entry in self.pathway.entries.items():
            if entry.is_gene() and entry.reaction:
                enzyme_place = self.entry_to_place[entry_id]
                reaction_transition = self.reaction_name_to_transition[entry.reaction]
                
                test_arc = TestArc(
                    source=enzyme_place,
                    target=reaction_transition,
                    weight=1
                )
                test_arcs.append(test_arc)
        return test_arcs
```

#### 3. Automatic Biological PN Marking

Documents are automatically marked when test arcs are created:

```python
if test_arcs:
    document.metadata['source'] = 'kegg'
    document.metadata['has_test_arcs'] = True
    document.metadata['model_type'] = 'Biological Petri Net'
    document.metadata['test_arc_count'] = len(test_arcs)
```

## Examples

### Example 1: Single Enzyme

**KGML Input**:
```xml
<pathway name="path:test00010">
  <!-- Compounds -->
  <entry id="1" name="cpd:C00031" type="compound">
    <graphics name="Glucose" x="100" y="100"/>
  </entry>
  <entry id="2" name="cpd:C00668" type="compound">
    <graphics name="G6P" x="200" y="100"/>
  </entry>
  
  <!-- Enzyme -->
  <entry id="3" name="gene:12345" type="gene" reaction="rn:R00710">
    <graphics name="Hexokinase" x="150" y="50"/>
  </entry>
  
  <!-- Reaction -->
  <reaction id="4" name="rn:R00710" type="irreversible">
    <substrate id="1" name="cpd:C00031"/>
    <product id="2" name="cpd:C00668"/>
  </reaction>
</pathway>
```

**Petri Net Output**:
- **Places**: Glucose (P1), G6P (P2), Hexokinase (P3 - enzyme)
- **Transitions**: R00710 (T1 - phosphorylation)
- **Normal Arcs**: 
  - P1 → T1 (Glucose consumed)
  - T1 → P2 (G6P produced)
- **Test Arc**: P3 → T1 (Hexokinase catalyzes, not consumed)
- **Metadata**: `model_type = "Biological Petri Net"`

### Example 2: Multiple Enzymes

When a pathway has multiple enzyme-catalyzed reactions:

```python
pathway = parse_kgml(kgml)
document = convert_pathway(pathway)

# Check for enzymes
enzyme_places = [p for p in document.places if p.metadata.get('is_enzyme')]
test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]

print(f"Enzymes: {len(enzyme_places)}")
print(f"Test arcs: {len(test_arcs)}")
print(f"Model type: {document.metadata['model_type']}")
# Output:
# Enzymes: 3
# Test arcs: 3
# Model type: Biological Petri Net
```

## Test Suite

**File**: `test_kegg_catalyst_import.py`

### Test Coverage

✅ **test_kegg_enzyme_creates_test_arcs**
- Verifies enzyme entries with reaction attributes create test arcs
- Checks test arcs are non-consuming
- Validates document marked as Biological PN

✅ **test_kegg_multiple_enzymes**
- Tests multiple enzyme entries create multiple test arcs
- Verifies test_arc_count metadata

✅ **test_kegg_enzyme_without_reaction_attribute**
- Ensures enzymes without reaction attributes don't create test arcs
- Verifies document NOT marked as Biological PN

✅ **test_kegg_compound_entries_not_converted_to_test_arcs**
- Confirms compound entries excluded from test arc conversion

✅ **test_kegg_ortholog_entry_creates_test_arc**
- Tests ortholog entries (another enzyme type) create test arcs

### Running Tests

```bash
cd /home/simao/projetos/shypn
PYTHONPATH=src:$PYTHONPATH python3 test_kegg_catalyst_import.py
```

**Expected Output**:
```
Testing KEGG enzyme-to-test-arc conversion...

✓ KEGG enzyme creates test arc
✓ Test arc: Enzyme XYZ → R00710
✓ Document marked as: Biological Petri Net

✓ Multiple enzymes create multiple test arcs
✓ Created 2 test arcs from 2 enzyme entries

✓ Enzyme without reaction attribute doesn't create test arc

✓ Compound entries correctly excluded from test arc conversion

✓ Ortholog entry creates test arc

============================================================
All KEGG catalyst import tests passed! ✓
============================================================
```

## Usage

### Basic Import (Default - Clean Layout)

```python
from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway

# Fetch KEGG pathway (e.g., human glycolysis)
kgml = fetch_pathway("hsa00010")

# Parse KGML XML
pathway = parse_kgml(kgml)

# Convert to Petri net (default: clean layout, no enzyme places)
document = convert_pathway(pathway)

# Result: Classical PN with clean KEGG layout
print(f"Places: {len(document.places)} (compounds only)")
print(f"Transitions: {len(document.transitions)}")
print(f"Layout: Clean (matches KEGG visualization)")
```

### Biological Analysis (Opt-in)

```python
# Enable enzyme places for biological analysis
document = convert_pathway(pathway, create_enzyme_places=True)

# Check if Biological PN
if document.metadata.get('has_test_arcs'):
    print(f"Biological Petri Net with {document.metadata['test_arc_count']} enzymes")
    print(f"Places: {len(document.places)} (compounds + enzymes)")
else:
    print("No enzymes detected in pathway")
```

### Accessing Enzyme Information (when create_enzyme_places=True)

```python
# Convert with enzyme places enabled
document = convert_pathway(pathway, create_enzyme_places=True)

# Find enzyme places
enzyme_places = [
    place for place in document.places 
    if place.metadata.get('is_enzyme')
]

for place in enzyme_places:
    enzyme_name = place.label
    catalyzes = place.metadata['catalyzes_reaction']
    print(f"{enzyme_name} catalyzes {catalyzes}")

# Find test arcs (catalysts)
from shypn.netobjs.test_arc import TestArc
test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]

for arc in test_arcs:
    print(f"Catalyst: {arc.source.label} → {arc.target.label}")
```

## When to Use Each Mode

### Use Default Mode (create_enzyme_places=False) When:

- 📊 **Visualizing pathways**: Want clean, KEGG-like layout
- 🎨 **Presentation/documentation**: Need human-readable diagrams
- 🚀 **Quick exploration**: Browsing pathways without analysis
- 💻 **UI/Web display**: Showing pathways to users

### Use Biological Mode (create_enzyme_places=True) When:

- 🔬 **Biological analysis**: Using topology analyzers
- 📈 **Dependency analysis**: Studying enzyme sharing, regulatory patterns
- 🧬 **Metabolic modeling**: Need explicit enzyme representation
- 📚 **Research/publication**: Analyzing biological semantics

## Comparison: SBML vs KEGG

| Aspect | SBML | KEGG |
|--------|------|------|
| **Catalyst Representation** | Explicit `<modifier>` | Implicit `reaction` attribute |
| **Data Location** | Per-reaction modifiers list | Separate enzyme entries |
| **Entry Types** | Species (all compounds) | Compound + Gene/Enzyme/Ortholog |
| **Association** | Direct reference | Name matching (e.g., "rn:R00710") |
| **Parser Complexity** | Simple extraction | Entry-to-reaction mapping |

## Benefits

### 1. Automatic Detection
No user intervention needed - pathways with enzymes automatically become Biological PNs.

### 2. Unified Theory
Both SBML and KEGG imports now implement same Biological PN theory (Σ component).

### 3. Topology Analysis
Enzyme-catalyzed reactions correctly classified by:
- **Dependency & Coupling Analyzer**: Detects shared catalysts
- **Regulatory Structure Analyzer**: Identifies catalyst patterns

### 4. Visual Distinction
Test arcs visually distinct (dashed lines, hollow diamonds) from normal arcs.

### 5. Simulation Accuracy
Test arcs correctly simulate enzyme catalysis (enable without consumption).

## Integration with Existing Infrastructure

### Topology Panel

The Topology Panel's **Biological category** now works with KEGG imports:

```python
# Dependency & Coupling Analysis
analyzer = DependencyAndCouplingAnalyzer(document)
results = analyzer.analyze()

# Example output for KEGG pathway:
# Transition T1 and T2: Convergent (shared catalyst P3)
# Dependency: Σ-Dependent (regulatory coupling via enzyme)
```

### Report Panel

Biological metrics automatically available for KEGG imports:
- Test arc count
- Enzyme-transition associations
- Catalyst sharing patterns

## Future Enhancements

### Planned

1. **Inhibitors**: Detect inhibitory relations from KEGG KEGGRelation objects
2. **Enzyme Complexes**: Handle multi-enzyme complexes from KEGG groups
3. **Reversible Enzyme Handling**: Split reversible reactions preserve enzyme associations
4. **KEGG API Metadata**: Fetch enzyme details (EC numbers, names) from KEGG API

### Under Consideration

- **Allosteric Regulation**: Model activators/inhibitors as weighted test arcs
- **Enzyme Concentration**: Use KEGG expression data for initial enzyme tokens
- **Pathway Crosstalk**: Link shared enzymes across multiple pathways

## References

### Biological Petri Nets Theory
- Reddy et al., "Petri Net Representations in Metabolic Pathways"
- Zevedei-Oancea & Schuster, "Topological Analysis of Metabolic Networks"

### KEGG Data Format
- KGML Specification: https://www.kegg.jp/kegg/xml/docs/
- KEGG Entry Types: https://www.kegg.jp/kegg/xml/docs/#entry

### Implementation Files
- `src/shypn/importer/kegg/pathway_converter.py` - Main converter with KEGGEnzymeConverter
- `src/shypn/importer/kegg/models.py` - KEGG data structures
- `src/shypn/netobjs/test_arc.py` - Test arc implementation
- `test_kegg_catalyst_import.py` - Test suite

## See Also

- **SBML_BIOLOGICAL_PN_IMPORT.md** - SBML modifier conversion (similar approach)
- **BIOLOGICAL_PETRI_NET_THEORY.md** - Complete Bio-PN formalization
- **TOPOLOGY_ANALYSIS_GUIDE.md** - Using analyzers with biological models
