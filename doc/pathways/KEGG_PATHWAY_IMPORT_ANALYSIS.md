# KEGG Pathway Import to Petri Net - Analysis

**Date**: October 7, 2025  
**Status**: 🔬 RESEARCH PHASE

## Overview

This document analyzes the feasibility and strategy for importing KEGG biochemical pathways and converting them to Petri net models in shypn.

## KEGG Data Structure

### KGML (KEGG Markup Language)

KGML is an XML format that represents pathway topology. Key elements:

```xml
<pathway name="path:hsa00010" org="hsa" number="00010" 
         title="Glycolysis / Gluconeogenesis">
  
  <!-- Entries: nodes in the pathway graph -->
  <entry id="18" name="hsa:226 hsa:229 hsa:230" type="gene" 
         reaction="rn:R01068">
    <graphics name="ALDOA..." x="483" y="407" width="46" height="17"/>
  </entry>
  
  <entry id="45" name="cpd:C00022" type="compound">
    <graphics name="Pyruvate" x="483" y="566" width="8" height="8"/>
  </entry>
  
  <!-- Relations: edges between entries (interactions, regulatory) -->
  <relation entry1="18" entry2="45" type="ECrel">
    <subtype name="compound" value="46"/>
  </relation>
  
  <!-- Reactions: metabolic transformations -->
  <reaction id="23" name="rn:R01068" type="irreversible">
    <substrate id="17" name="cpd:C00118"/>  <!-- D-Glyceraldehyde 3-phosphate -->
    <product id="19" name="cpd:C00236"/>    <!-- 3-Phospho-D-glyceroyl phosphate -->
  </reaction>
  
</pathway>
```

### Key KGML Elements

| Element | Description | Petri Net Mapping |
|---------|-------------|-------------------|
| **entry (gene/enzyme)** | Protein that catalyzes reaction | **Transition** (active element) |
| **entry (compound)** | Metabolite/substrate/product | **Place** (passive holder) |
| **entry (map)** | Link to another pathway | Reference/annotation |
| **entry (group)** | Complex of multiple entries | Grouped transitions |
| **relation** | Interaction/regulation between entries | Arc (may indicate inhibition) |
| **reaction** | Metabolic transformation | Transition with substrate/product arcs |
| **substrate** | Input to reaction | **Input arc** to transition |
| **product** | Output of reaction | **Output arc** from transition |

## Biochemical Pathway → Petri Net Mapping Strategy

### Core Mapping Rules

#### 1. **Compounds → Places**
- Each compound (metabolite) becomes a **Place**
- Initial marking represents concentration/availability
- Label: compound name (e.g., "Glucose", "ATP")
- ID: KEGG compound ID (e.g., "C00031" for D-Glucose)

#### 2. **Enzymes/Reactions → Transitions**
- Each enzymatic reaction becomes a **Transition**
- Label: enzyme name or EC number (e.g., "Hexokinase", "EC:2.7.1.1")
- ID: KEGG reaction ID (e.g., "R01600")
- Type: Can be immediate, timed, or stochastic

#### 3. **Substrate Relationships → Input Arcs**
- Connect compound (place) to enzyme (transition)
- Weight: stoichiometric coefficient (default = 1)
- For "A + B → C", create arcs from places A and B to transition

#### 4. **Product Relationships → Output Arcs**
- Connect enzyme (transition) to compound (place)
- Weight: stoichiometric coefficient
- For "A → B + C", create arcs from transition to places B and C

### Advanced Mapping Considerations

#### Reversible Reactions
```
A ⇌ B  (reaction R00001)
```
**Option 1**: Two transitions (forward and reverse)
```
A --→ [R00001_fwd] --→ B
A ←-- [R00001_rev] ←-- B
```

**Option 2**: Single transition with bidirectional arcs (simpler)
```
A ←→ [R00001] ←→ B
```

#### Regulation and Inhibition
```
Enzyme A activates Enzyme B
Compound C inhibits Enzyme D
```
**Petri Net Representation**:
- Test arcs (read without consuming)
- Inhibitor arcs (prevent firing when present)
- OR: Store as metadata for simulation engine

#### Stoichiometry
```
2 ATP + Glucose → 2 ADP + Glucose-6-phosphate
```
**Arc weights**:
- Input arc from ATP: weight = 2
- Input arc from Glucose: weight = 1
- Output arc to ADP: weight = 2
- Output arc to Glucose-6-phosphate: weight = 1

#### Cofactors (ATP, NAD+, etc.)
**Challenge**: Many reactions use ATP/NAD+, creating highly connected graphs

**Option 1**: Include all cofactors (accurate but cluttered)
**Option 2**: Omit ubiquitous cofactors (cleaner but less accurate)
**Option 3**: Make cofactors optional via import settings

## API Access Strategy

### Endpoint URLs

```python
# List all pathways for organism
list_url = f"https://rest.kegg.jp/list/pathway/{organism}"

# Get KGML for specific pathway
kgml_url = f"https://rest.kegg.jp/get/{pathway_id}/kgml"

# Get pathway image (optional, for reference)
image_url = f"https://www.kegg.jp/kegg/pathway/{org}/{pathway_id}.png"
```

### Example Pathway IDs

| Pathway | Reference | Human | Description |
|---------|-----------|-------|-------------|
| Glycolysis | `map00010` | `hsa00010` | Glucose breakdown |
| TCA Cycle | `map00020` | `hsa00020` | Citric acid cycle |
| Glycolysis | `ko00010` | - | KO-based reference |

## Implementation Architecture

### Module Structure

```
src/shypn/import/
├── __init__.py
├── kegg/
│   ├── __init__.py
│   ├── api_client.py       # HTTP requests to KEGG API
│   ├── kgml_parser.py      # XML parsing (using xml.etree.ElementTree)
│   ├── pathway_converter.py # KGML → DocumentModel conversion
│   ├── mapping_rules.py    # Biochemical → Petri net rules
│   └── models.py           # Data classes for KGML elements
└── dialogs/
    └── kegg_import_dialog.py # GTK dialog for import
```

### Core Classes

```python
# models.py
@dataclass
class KEGGEntry:
    id: str
    name: str  # KEGG identifier (e.g., "hsa:226", "cpd:C00031")
    type: str  # "gene", "enzyme", "compound", "map", "group"
    reaction: Optional[str]
    graphics: dict  # x, y, width, height, label

@dataclass
class KEGGReaction:
    id: str
    name: str  # e.g., "rn:R01068"
    type: str  # "reversible" or "irreversible"
    substrates: List[Tuple[str, str]]  # (entry_id, compound_id)
    products: List[Tuple[str, str]]

@dataclass
class KEGGRelation:
    entry1: str
    entry2: str
    type: str  # "ECrel", "PPrel", "GErel", etc.
    subtypes: List[Tuple[str, str]]  # (name, value)

@dataclass
class KEGGPathway:
    id: str
    name: str
    organism: str
    title: str
    entries: Dict[str, KEGGEntry]
    reactions: List[KEGGReaction]
    relations: List[KEGGRelation]
```

### Conversion Workflow

```python
def import_kegg_pathway(pathway_id: str, options: dict) -> DocumentModel:
    """
    Import KEGG pathway and convert to Petri net.
    
    Args:
        pathway_id: e.g., "hsa00010"
        options: {
            'include_cofactors': bool,
            'reversible_as_two_transitions': bool,
            'scale_coordinates': float,
            'add_initial_marking': bool
        }
    
    Returns:
        DocumentModel with places, transitions, arcs
    """
    # 1. Fetch KGML from KEGG API
    kgml_xml = fetch_kgml(pathway_id)
    
    # 2. Parse KGML into structured data
    pathway = parse_kgml(kgml_xml)
    
    # 3. Convert to Petri net
    document = convert_pathway_to_petri_net(pathway, options)
    
    return document
```

## Layout and Coordinates

### KEGG Graphics Coordinates
- KGML provides `x`, `y` coordinates for each entry
- Origin: top-left corner
- Scale: pixels (typical map size ~800x600 pixels)

### Adaptation for shypn
- **Scale factor**: KEGG coordinates → shypn world coordinates
  - Example: multiply by 2.5 to spread out nodes
- **Origin adjustment**: May need to shift for better centering
- **Overlap handling**: KEGG maps may have overlapping elements

## Import Dialog Design

### UI Elements

```
┌─────────────────────────────────────────┐
│  Import KEGG Pathway                    │
├─────────────────────────────────────────┤
│                                         │
│  Pathway ID: [hsa00010          ] [?]  │
│              (e.g., hsa00010, map00020) │
│                                         │
│  Organism:   [hsa ▼] (Homo sapiens)    │
│                                         │
│  Options:                               │
│  ☑ Include cofactors (ATP, NAD+, etc.) │
│  ☑ Add initial marking (1 token each)  │
│  ☐ Split reversible reactions          │
│  ☐ Include regulatory relations         │
│                                         │
│  Coordinate scaling: [2.5] (1.0-5.0)    │
│                                         │
│  Preview:                               │
│  ┌────────────────────────────────────┐ │
│  │ Glycolysis / Gluconeogenesis       │ │
│  │ Places: 28, Transitions: 35        │ │
│  └────────────────────────────────────┘ │
│                                         │
│           [Cancel]  [Import]            │
└─────────────────────────────────────────┘
```

## Challenges and Solutions

### Challenge 1: Graph Complexity
**Problem**: Large pathways can have 100+ nodes, creating cluttered models

**Solutions**:
- Auto-layout algorithms (force-directed, hierarchical)
- Pathway filtering (import only selected reactions)
- Hierarchical decomposition (sub-pathways)

### Challenge 2: Semantic Mapping
**Problem**: Biochemical concepts don't map 1:1 to Petri nets

**Solutions**:
- Multiple mapping strategies (user selectable)
- Metadata preservation (keep KEGG IDs for reference)
- Documentation of mapping rules

### Challenge 3: Simulation Accuracy
**Problem**: Petri net simulation may not reflect real kinetics

**Solutions**:
- Stochastic transitions for probabilistic reactions
- Timed transitions with delays
- Integration with rate constants (future feature)

### Challenge 4: API Rate Limiting
**Problem**: KEGG API may have rate limits

**Solutions**:
- Caching downloaded KGML files
- Progress indicators for slow downloads
- Batch import option

## Testing Strategy

### Phase 1: Simple Pathways
- **map00010**: Glycolysis (linear, well-known)
- **map00020**: TCA cycle (circular)
- Test basic mapping, coordinate scaling

### Phase 2: Complex Pathways
- **map01100**: Metabolic pathways (large, interconnected)
- **map04010**: MAPK signaling (regulatory)
- Test performance, layout, regulation handling

### Phase 3: Validation
- Compare with published Petri net models
- Check biochemical correctness with domain experts
- User testing with biologists

## Future Enhancements

1. **SBML Export**: Convert to Systems Biology Markup Language
2. **Kinetic Parameters**: Import rate constants from other databases
3. **Colored Petri Nets**: Use colors to represent different metabolite types
4. **Hierarchical Pathways**: Import pathway hierarchies
5. **BioPAX Support**: Alternative to KEGG (more open)
6. **Reaction Annotations**: Add enzyme mechanisms, regulatory details

## Academic Use Compliance

⚠️ **Important**: KEGG API is for **academic use only**

**Implementation Requirements**:
- Add license notice in import dialog
- User must confirm academic use
- Include attribution to KEGG in exported models
- Respect API usage guidelines (no bulk downloading)

## References

- **KEGG API Documentation**: https://www.kegg.jp/kegg/rest/keggapi.html
- **KGML Specification**: https://www.kegg.jp/kegg/xml/
- **Petri Nets in Systems Biology**: Chaouiya (2007), Koch & Heiner (2008)
- **Biochemical Pathway Databases**: Kanehisa et al. (2021), Nucleic Acids Research

## Next Steps

1. ✅ Complete this analysis
2. ⬜ Fetch and examine sample KGML files (glycolysis, TCA)
3. ⬜ Design `KEGGPathway` and related data classes
4. ⬜ Implement `kgml_parser.py` (XML → Python objects)
5. ⬜ Implement basic `pathway_converter.py` (compounds → places, reactions → transitions)
6. ⬜ Test conversion with simple pathway
7. ⬜ Implement import dialog UI
8. ⬜ Add to File menu
9. ⬜ User documentation

---

**Status**: Ready to proceed with implementation
