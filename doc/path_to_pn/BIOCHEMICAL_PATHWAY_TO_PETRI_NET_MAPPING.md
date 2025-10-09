# Biochemical Pathway Notation to Petri Net Mapping

**Document Version**: 1.0  
**Date**: October 9, 2025  
**Status**: Comprehensive Reference Documentation

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Biochemical Pathway Notations](#biochemical-pathway-notations)
3. [Petri Net Fundamentals](#petri-net-fundamentals)
4. [Mapping Semantics](#mapping-semantics)
5. [KEGG Pathway Implementation](#kegg-pathway-implementation)
6. [Advanced Mapping Patterns](#advanced-mapping-patterns)
7. [Examples](#examples)
8. [References](#references)

---

## Executive Summary

This document provides a comprehensive analysis of the semantic mapping between biochemical pathway notations (primarily KEGG and SBGN) and Petri net representations. It describes the mathematical foundations, conversion algorithms, and implementation details used in the ShypN application.

### Key Findings

- **Biochemical pathways** can be faithfully represented as **Petri nets**
- **Places** represent metabolites/compounds/molecules
- **Transitions** represent biochemical reactions/transformations
- **Tokens** represent concentration/quantity of molecules
- **Arcs** represent stoichiometric relationships
- **Firing rules** model reaction kinetics

---

## Biochemical Pathway Notations

### 1. KEGG (Kyoto Encyclopedia of Genes and Genomes)

**Standard**: KGML (KEGG Markup Language) XML format

#### KEGG Entry Types

| Entry Type | Biological Meaning | Examples |
|-----------|-------------------|----------|
| **compound** | Metabolite, small molecule | Glucose, ATP, NADH |
| **enzyme** | Enzyme, catalytic protein | Hexokinase, Phosphofructokinase |
| **gene** | Gene product, protein | hsa:226 (human aldolase) |
| **reaction** | Biochemical transformation | R01068 (glucose phosphorylation) |
| **map** | Pathway cross-reference | Glycolysis, TCA cycle |
| **group** | Protein complex | Cytochrome c oxidase complex |
| **ortholog** | KEGG Orthology (KO) | K00844 (hexokinase) |

#### KEGG Reaction Representation

```xml
<reaction id="1" name="rn:R01068" type="reversible">
  <substrate id="2" name="cpd:C00031"/>  <!-- Glucose -->
  <substrate id="5" name="cpd:C00002"/>  <!-- ATP -->
  <product id="3" name="cpd:C00668"/>    <!-- Glucose-6-phosphate -->
  <product id="6" name="cpd:C00008"/>    <!-- ADP -->
</reaction>
```

**Semantics**:
- **Substrate**: Input molecules consumed by reaction
- **Product**: Output molecules produced by reaction
- **Type**: `reversible` or `irreversible`
- **Stoichiometry**: Implicit 1:1 unless specified

---

### 2. SBGN (Systems Biology Graphical Notation)

**Standard**: Three complementary languages

#### SBGN Languages

1. **Process Description (PD)**
   - Represents molecular entities and processes
   - Includes complexes, compartments, modulation
   - Most similar to KEGG representation

2. **Entity Relationship (ER)**
   - Focuses on relationships between entities
   - Useful for regulatory networks
   - Abstract, no explicit processes

3. **Activity Flow (AF)**
   - Represents flow of information
   - High-level view of biological activities
   - Used for signaling pathways

#### SBGN Entity Types (PD)

| Glyph | Entity Type | Examples |
|-------|------------|----------|
| ⬭ (circle) | Simple chemical | ATP, Glucose |
| ⬬ (rounded rect) | Macromolecule | Protein, Enzyme |
| ⬒ (compartment) | Cellular location | Cytoplasm, Mitochondria |
| ⬓ (complex) | Molecular complex | Ribosome, Proteasome |
| ■ (process node) | Biochemical process | Phosphorylation, Binding |

---

### 3. BioPAX (Biological Pathway Exchange)

**Standard**: RDF/OWL ontology format

- Semantic web representation
- Machine-readable pathway knowledge
- Extensive metadata and annotations
- Interoperable with multiple databases

---

## Petri Net Fundamentals

### Definition

A **Petri net** is a mathematical modeling language defined as a 5-tuple:

```
PN = (P, T, F, W, M₀)
```

Where:
- **P**: Finite set of places (states)
- **T**: Finite set of transitions (events)
- **F ⊆ (P × T) ∪ (T × P)**: Flow relation (arcs)
- **W: F → ℕ**: Weight function (stoichiometry)
- **M₀: P → ℕ**: Initial marking (initial state)

### Formal Semantics

#### Enabling Rule

A transition `t ∈ T` is **enabled** at marking `M` if:

```
∀p ∈ •t: M(p) ≥ W(p, t)
```

Where `•t` denotes the **preset** (input places) of transition `t`.

#### Firing Rule

When enabled transition `t` fires, the new marking `M'` is:

```
M'(p) = M(p) - W(p, t) + W(t, p)
```

For all places `p ∈ P`.

### Biological Interpretation

| Petri Net Element | Biochemical Meaning | Formal Representation |
|------------------|--------------------|-----------------------|
| **Place** | Metabolite/Compound | `p ∈ P` |
| **Transition** | Biochemical Reaction | `t ∈ T` |
| **Token** | Molecule Count/Concentration | `M(p) ∈ ℕ` |
| **Arc Weight** | Stoichiometric Coefficient | `W(p,t), W(t,p) ∈ ℕ` |
| **Marking** | System State (concentrations) | `M: P → ℕ` |
| **Firing** | Reaction Occurrence | `M →ᵗ M'` |

---

## Mapping Semantics

### Core Mapping Rules

#### Rule 1: Compound → Place

```
∀c ∈ Compounds: ∃p ∈ P such that p represents c
```

**Implementation**:
```python
def map_compound_to_place(compound: KEGGEntry) -> Place:
    place = Place(
        id=f"P{place_counter}",
        name=compound.graphics.name,
        x=compound.graphics.x * coordinate_scale,
        y=compound.graphics.y * coordinate_scale,
        tokens=initial_tokens if add_marking else 0
    )
    return place
```

**Semantic Preservation**:
- **Identity**: Compound ID → Place ID
- **Location**: KEGG coordinates → Canvas coordinates (scaled)
- **Initial state**: Optional initial marking (tokens)

---

#### Rule 2: Reaction → Transition

```
∀r ∈ Reactions: ∃t ∈ T such that t represents r
```

**Implementation**:
```python
def map_reaction_to_transition(reaction: KEGGReaction) -> Transition:
    transition = Transition(
        id=f"T{transition_counter}",
        name=get_enzyme_name(reaction) or reaction.name,
        x=calculate_midpoint_x(substrates, products),
        y=calculate_midpoint_y(substrates, products),
        transition_type='timed' if has_kinetics else 'immediate'
    )
    return transition
```

**Semantic Preservation**:
- **Catalysis**: Enzyme name → Transition label
- **Location**: Between substrates and products
- **Timing**: Immediate (abstract) or timed (with kinetics)

---

#### Rule 3: Stoichiometry → Arc Weights

```
∀(s, r) ∈ Substrate_Relations: ∃arc(p_s, t_r) with weight w_s
∀(r, p) ∈ Product_Relations: ∃arc(t_r, p_p) with weight w_p
```

**Implementation**:
```python
def create_arcs(reaction, transition, place_map):
    arcs = []
    
    # Input arcs (substrate → transition)
    for substrate in reaction.substrates:
        if substrate.id in place_map:
            arc = Arc(
                source=place_map[substrate.id],
                target=transition,
                weight=substrate.stoichiometry or 1
            )
            arcs.append(arc)
    
    # Output arcs (transition → product)
    for product in reaction.products:
        if product.id in place_map:
            arc = Arc(
                source=transition,
                target=place_map[product.id],
                weight=product.stoichiometry or 1
            )
            arcs.append(arc)
    
    return arcs
```

**Semantic Preservation**:
- **Stoichiometry**: Reaction coefficients → Arc weights
- **Direction**: Substrate/Product roles → Arc direction
- **Conservation**: Mass balance preserved

---

#### Rule 4: Reversible Reactions

**Option A: Single Transition (Default)**
```
Reversible reaction ↔ Bidirectional transition
```

**Option B: Two Transitions (Split)**
```
Reversible reaction ↔ Forward transition + Reverse transition
```

**Implementation**:
```python
def handle_reversible(reaction, split_reversible):
    if reaction.type == 'reversible':
        if split_reversible:
            # Create two transitions
            forward = create_forward_transition(reaction)
            reverse = create_reverse_transition(reaction)
            return [forward, reverse]
        else:
            # Create single bidirectional transition
            transition = create_transition(reaction)
            return [transition]
    else:
        # Irreversible - single transition
        transition = create_transition(reaction)
        return [transition]
```

---

### Advanced Semantic Mappings

#### Enzymatic Catalysis

**KEGG Representation**:
```xml
<entry id="10" type="enzyme" reaction="rn:R01068">
  <graphics name="HK, hk" />
</entry>
```

**Petri Net Representation**:
- **Option 1**: Enzyme name → Transition label (current implementation)
- **Option 2**: Enzyme → Test arc (catalytic, not consumed)
- **Option 3**: Enzyme → Separate place with read arc

---

#### Regulatory Interactions

**KEGG Relation Types**:
- **activation**: Positive regulation
- **inhibition**: Negative regulation
- **expression**: Gene expression control
- **repression**: Gene expression inhibition

**Petri Net Representation**:
- **Activation**: Read arc (test arc) enabling transition
- **Inhibition**: Inhibitor arc preventing firing
- **Expression**: High-level arc to gene product place

**Not currently implemented** - potential future enhancement.

---

#### Cofactor Handling

**Common Cofactors**:
- ATP/ADP, NAD+/NADH, NADP+/NADPH
- CoA, FAD/FADH₂, H₂O, H+

**Filtering Strategy**:
```python
COMMON_COFACTORS = {
    'cpd:C00002',  # ATP
    'cpd:C00008',  # ADP
    'cpd:C00003',  # NAD+
    'cpd:C00004',  # NADH
    'cpd:C00006',  # NADP+
    'cpd:C00005',  # NADPH
    'cpd:C00010',  # CoA
    'cpd:C00001',  # H2O
    # ... etc
}

def should_include_compound(entry, options):
    if not options.include_cofactors:
        return entry.name not in COMMON_COFACTORS
    return True
```

**Rationale**:
- Cofactors are recycled, not consumed
- Including them clutters the network
- Can be modeled separately if needed

---

## KEGG Pathway Implementation

### Conversion Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PathwayConverter                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           ConversionStrategy (ABC)                     │ │
│  │                                                        │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │ Compound     │  │  Reaction    │  │    Arc      │ │ │
│  │  │   Mapper     │  │   Mapper     │  │  Builder    │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────────┐
        │       DocumentModel                   │
        │  ┌────────┐ ┌────────────┐ ┌──────┐ │
        │  │ Places │ │Transitions │ │ Arcs │ │
        │  └────────┘ └────────────┘ └──────┘ │
        └──────────────────────────────────────┘
```

### Conversion Algorithm

```python
Algorithm: KEGG_to_Petri_Net(pathway, options)
Input: KEGGPathway pathway, ConversionOptions options
Output: DocumentModel document

1. Initialize:
   document ← new DocumentModel()
   place_map ← empty dictionary

2. Phase 1 - Create Places:
   compounds ← pathway.get_compounds()
   for each entry in compounds:
       if compound_mapper.should_include(entry, options):
           place ← compound_mapper.create_place(entry, options)
           document.places.append(place)
           place_map[entry.id] ← place

3. Phase 2 - Create Transitions and Arcs:
   for each reaction in pathway.reactions:
       transitions ← reaction_mapper.create_transitions(reaction, pathway, options)
       
       for each transition in transitions:
           document.transitions.append(transition)
           
           arcs ← arc_builder.create_arcs(reaction, transition, place_map, pathway, options)
           document.arcs.extend(arcs)

4. Phase 3 - Update Counters:
   document._next_place_id ← len(document.places) + 1
   document._next_transition_id ← len(document.transitions) + 1
   document._next_arc_id ← len(document.arcs) + 1

5. Return document
```

### Coordinate Transformation

**KEGG Coordinates** → **Canvas Coordinates**

```python
def transform_coordinates(kegg_x, kegg_y, options):
    """Transform KEGG pixel coordinates to canvas world coordinates.
    
    KEGG uses:
    - Origin: Top-left (0, 0)
    - Units: Pixels in pathway image
    - Scale: Variable (typically 50-500 pixels wide)
    
    Canvas uses:
    - Origin: Center or arbitrary (configurable)
    - Units: World coordinates (mm or logical units)
    - Scale: DPI-aware
    """
    # Apply scaling factor
    canvas_x = kegg_x * options.coordinate_scale + options.center_x
    canvas_y = kegg_y * options.coordinate_scale + options.center_y
    
    return canvas_x, canvas_y
```

**Default Scale Factor**: 2.5  
**Rationale**: KEGG coordinates are compact; scaling spreads them for visibility

---

## Advanced Mapping Patterns

### Pattern 1: Pathway Cross-References

**KEGG**:
```xml
<entry id="50" type="map" link="http://www.kegg.jp/pathway/hsa00020">
  <graphics name="TCA cycle" />
</entry>
```

**Petri Net**:
- **Option A**: Macro transition (hierarchical Petri net)
- **Option B**: Interface places (input/output)
- **Option C**: Ignore (current implementation)

---

### Pattern 2: Protein Complexes

**KEGG**:
```xml
<entry id="60" type="group">
  <component id="61"/>
  <component id="62"/>
  <component id="63"/>
</entry>
```

**Petri Net**:
- **Colored Petri Net**: Token colors represent subunits
- **Hierarchical**: Nested sub-net for complex
- **Simplified**: Treat as single entity (current)

---

### Pattern 3: Compartmentalization

**Biological Reality**:
- Cytoplasm, mitochondria, nucleus, etc.
- Transport reactions cross compartments
- Different concentrations in each compartment

**Petri Net Representation**:
- **Colored Petri Nets**: Token colors = compartments
- **Hierarchical**: Separate net per compartment
- **Flattened**: Suffix place names with compartment

**Current Implementation**: Not explicitly modeled

---

### Pattern 4: Gene Expression

**KEGG Relation**:
```xml
<relation entry1="10" entry2="20" type="expression">
  <subtype name="expression" />
</relation>
```

**Petri Net**:
- Gene (place) → Transcription (transition) → mRNA (place)
- mRNA (place) → Translation (transition) → Protein (place)

**Current Implementation**: Not modeled (pathways focus on metabolism)

---

## Examples

### Example 1: Simple Reaction

**Biochemical Notation**:
```
Glucose + ATP → Glucose-6-P + ADP
(Catalyzed by Hexokinase)
```

**Petri Net Representation**:
```
Places:
  P1: Glucose (tokens = 10)
  P2: ATP (tokens = 100)
  P3: Glucose-6-P (tokens = 0)
  P4: ADP (tokens = 0)

Transitions:
  T1: Hexokinase

Arcs:
  P1 → T1 (weight = 1)
  P2 → T1 (weight = 1)
  T1 → P3 (weight = 1)
  T1 → P4 (weight = 1)
```

**Firing Semantics**:
- T1 enabled if: M(P1) ≥ 1 AND M(P2) ≥ 1
- After firing: M'(P1) = M(P1) - 1, M'(P2) = M(P2) - 1, M'(P3) = M(P3) + 1, M'(P4) = M(P4) + 1

---

### Example 2: Reversible Reaction

**Biochemical Notation**:
```
Fructose-6-P ⇌ Glucose-6-P
(Catalyzed by Phosphoglucoisomerase)
```

**Petri Net Representation (Single Transition)**:
```
Places:
  P1: Fructose-6-P
  P2: Glucose-6-P

Transition:
  T1: Phosphoglucoisomerase (reversible)

Arcs:
  P1 → T1 → P2  (forward direction)
  P2 → T1 → P1  (reverse direction, implicit in bidirectional transition)
```

**Petri Net Representation (Split)**:
```
Places:
  P1: Fructose-6-P
  P2: Glucose-6-P

Transitions:
  T1_forward: Phosphoglucoisomerase (→)
  T1_reverse: Phosphoglucoisomerase (←)

Arcs:
  P1 → T1_forward → P2
  P2 → T1_reverse → P1
```

---

### Example 3: Complex Stoichiometry

**Biochemical Notation**:
```
2 H₂O₂ → 2 H₂O + O₂
(Catalyzed by Catalase)
```

**Petri Net Representation**:
```
Places:
  P1: H₂O₂
  P2: H₂O
  P3: O₂

Transition:
  T1: Catalase

Arcs:
  P1 → T1 (weight = 2)  # Consume 2 H₂O₂
  T1 → P2 (weight = 2)  # Produce 2 H₂O
  T1 → P3 (weight = 1)  # Produce 1 O₂
```

**Firing Semantics**:
- T1 enabled if: M(P1) ≥ 2
- After firing: M'(P1) = M(P1) - 2, M'(P2) = M(P2) + 2, M'(P3) = M(P3) + 1

---

## References

### Primary Literature

1. **Petri Nets for Systems Biology**
   - Heiner, M., Gilbert, D., & Donaldson, R. (2008)
   - "Petri nets for systems and synthetic biology"
   - *Lecture Notes in Computer Science*, 5016, 215-264

2. **KEGG Database**
   - Kanehisa, M., & Goto, S. (2000)
   - "KEGG: Kyoto Encyclopedia of Genes and Genomes"
   - *Nucleic Acids Research*, 28(1), 27-30

3. **SBGN Standard**
   - Le Novère, N., et al. (2009)
   - "The Systems Biology Graphical Notation"
   - *Nature Biotechnology*, 27(8), 735-741

4. **Petri Net Theory**
   - Murata, T. (1989)
   - "Petri nets: Properties, analysis and applications"
   - *Proceedings of the IEEE*, 77(4), 541-580

### Implementation References

5. **ShypN KEGG Importer**
   - Location: `src/shypn/importer/kegg/`
   - Main converter: `pathway_converter.py`
   - Models: `models.py`
   - Mappers: `compound_mapper.py`, `reaction_mapper.py`

6. **ShypN Petri Net Objects**
   - Location: `src/shypn/netobjs/`
   - Place: `place.py`
   - Transition: `transition.py`
   - Arc: `arc.py`

---

## Appendix: Conversion Options

### ConversionOptions Configuration

```python
@dataclass
class ConversionOptions:
    """
    coordinate_scale: float = 2.5
        Scaling factor for KEGG coordinates
        Range: 1.0 - 10.0
        Default: 2.5 (good balance for most pathways)
    
    include_cofactors: bool = True
        Include common cofactors (ATP, NADH, etc.)
        True: Full biochemical detail
        False: Simplified network (recommended for large pathways)
    
    split_reversible: bool = False
        Split reversible reactions into two transitions
        True: More precise kinetic modeling
        False: Simpler representation (recommended)
    
    add_initial_marking: bool = False
        Add initial tokens to places
        True: Ready for simulation
        False: Abstract structure only
    
    initial_tokens: int = 1
        Number of initial tokens per place
        Only used if add_initial_marking = True
    
    include_relations: bool = False
        Include regulatory relations
        True: Include activation/inhibition
        False: Only reactions (current implementation)
    
    center_x: float = 0.0
        X offset for centering pathway on canvas
    
    center_y: float = 0.0
        Y offset for centering pathway on canvas
    """
```

### Usage Examples

```python
# Example 1: Default conversion (balanced)
converter = PathwayConverter()
options = ConversionOptions()
document = converter.convert(pathway, options)

# Example 2: Simplified network (for large pathways)
options = ConversionOptions(
    coordinate_scale=3.0,
    include_cofactors=False,
    split_reversible=False
)
document = converter.convert(pathway, options)

# Example 3: Simulation-ready (with initial marking)
options = ConversionOptions(
    add_initial_marking=True,
    initial_tokens=10,
    split_reversible=True
)
document = converter.convert(pathway, options)

# Example 4: Centered on canvas
options = ConversionOptions(
    center_x=1000.0,  # Center of 2000x2000 canvas
    center_y=1000.0
)
document = converter.convert(pathway, options)
```

---

## Conclusion

The mapping between biochemical pathway notations and Petri nets is **mathematically sound** and **biologically meaningful**. The ShypN implementation provides a **flexible**, **extensible** framework for converting KEGG pathways to executable Petri net models.

**Key Strengths**:
- ✅ Formal semantic preservation
- ✅ Configurable conversion options
- ✅ Clean OOP architecture
- ✅ Extensible mapper pattern

**Future Enhancements**:
- Regulatory relations (activation/inhibition)
- Compartmentalization support
- SBGN import
- Timed/stochastic Petri nets with kinetic parameters
- Hierarchical pathway composition

---

**Document Maintainer**: ShypN Development Team  
**Last Updated**: October 9, 2025
