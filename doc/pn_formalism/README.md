# Petri Net Formalism Documentation

This directory contains formal documentation about Petri net theory and implementation in SHYPN.

## Documents

### 0. [SHPN_FORMALISM_CANONICAL.md](SHPN_FORMALISM_CANONICAL.md) ⭐ CANONICAL
**Signal Hierarchical Petri Net (SHPN) — Canonical 13-tuple, enablement, firing rule, basin boundary, invariants.**

The single source of truth for the SHYPN Petri-net formalism inside the
codebase, mirrored from
[`workspace/projects/My_Project/signal_hierarchy/manuscript/main_plos_one.tex`](../../workspace/projects/My_Project/signal_hierarchy/manuscript/main_plos_one.tex).
Defines the 13-tuple `SPN = (P, T, F, W, M₀, Φ, C, F_t, Ψ, F_s, W_s, λ, θ)`,
the four-predicate enablement condition, the firing rule (including the
dual-arc case), the commitment-threshold formula
`M_commit = θ(t) + W_s((p_s, t))`, and the implementation invariants every
engine PR must respect.

**Supersedes** the tuple definition in
[`doc/EXTENDED_PETRI_NET_FORMALISM_SUMMARY.md`](../EXTENDED_PETRI_NET_FORMALISM_SUMMARY.md);
that document remains useful for the signal-place taxonomy and bug-fix
history but is no longer authoritative for the tuple itself.

### 1. [PETRI_NET_INCIDENCE_MATRIX_APPROACH.md](PETRI_NET_INCIDENCE_MATRIX_APPROACH.md)
**Formal Petri Net Semantics Using Incidence Matrices**

Describes the mathematical foundation of Petri nets and proposes a matrix-based approach:
- Formal definition: PN = (P, T, F, W, M₀)
- Incidence matrix representation (F⁺, F⁻, C)
- Matrix-first architecture (matrix as source of truth)
- Integration with current codebase
- Simulation-ready design

**Key Concept**: Petri nets are not just "connecting dots" - they have formal semantics defined by the incidence matrix. The visual graph should be derived from the matrix, not the other way around.

### 2. [PARAMETER_PLACES_NON_FORMAL.md](PARAMETER_PLACES_NON_FORMAL.md)
**Parameter Places: Model-File Metadata, Not Petri-Net Elements**

Normative definition pinning down that "parameter places" (e.g. `LOADING_DOSE`,
`AGE`, `pH`) are **metadata stored in the place table for convenience** and
are **not** members of the formal sets `P`, `T`, `F`, `F_t`, `F_s`, or `Ψ`.
Specifies the invariants that the simulator, renderer, importers, and
analysis layers must respect, and explicitly retires the
`is_signal_place = True` workaround that importers currently use just to get
a non-circle shape.

**Key Concept**: parameter places are invisible to the simulator. They carry
a name, a scalar value, and a canvas position — nothing else. They must be
visually distinguishable from formal places (circles) and from signal places
(hexagons).

### 3. [EXPERIMENT_PLAN_VS_OBJECT_NET.md](EXPERIMENT_PLAN_VS_OBJECT_NET.md) ⭐ STRICT RULE
**Architectural separation between the object-net (biology) and the experiment
plan (parameter places + events).**

A `.shy` file bundles two artifacts: the reusable object-net (whose dynamics
emerge entirely from its own topology) and the run-specific experiment plan
(parameter places + events). The two must remain separable. Specifies the
forbidden patterns (parameter-place names in object-net rate functions,
$F$/$F_s$/$F_t$ arcs to/from parameter places, `is_environment_aware`
backdoors), the only legal bridge (events), the canvas contract (rounded
square ▢ for parameter places vs. circle ○ for biological places vs.
hexagon ⬡ for signal places), and the sweep ↔ model superposition rule
(sweep value canonical for the dispatch, model static value suppressed,
explicit `superposition_intent` declaration required for any exception).

**Key Concept**: object-net dynamics MUST emerge from topology alone.
A failure to reach a desired fixed point is a topology bug, not a parameter
bug. Never patch via parameter-place multipliers in rate strings.

### 4. [ARC_FAMILY_REVISION_PLAN.md](ARC_FAMILY_REVISION_PLAN.md)
**Comprehensive Plan for Arc Geometry and Rendering Refactoring**

Technical plan addressing arc-related issues:
- Phase 0: Parser investigation (spurious lines)
- Phase 1: Perimeter-based arc geometry
- Phase 2: Remove legacy auto-curved arcs
- Phase 3: Manual arc transformation
- Phase 4: Fix hit detection for long arcs
- Phase 5: Testing and validation

**Key Issues Addressed**:
- Incorrect center-to-center geometry
- Non-selectable long arcs
- Legacy automatic curved arc conversion
- Formal validation using incidence matrix

## Implementation Phases

### Phase 0: Parser Investigation (3 days)
- ✅ Test 1: Verify relations are NOT converted to arcs
- ✅ Test 2: Search for spurious rendering code
- Ensure parser creates only valid Place↔Transition arcs

### Phase 0.5: Incidence Matrix Foundation (1 week)
- Implement `IncidenceMatrix` class
- Integrate with `ModelCanvasManager`
- Update `PathwayConverter` to use matrix-first approach
- Validate bipartite property structurally

### Phase 1-6: Arc Geometry & Rendering (3 weeks)
- See ARC_FAMILY_REVISION_PLAN.md for details

## Theory References

### Petri Net Basics
- **Bipartite Property**: F ⊆ (P × T) ∪ (T × P)
- **No Self-Loops**: Places only connect to Transitions and vice versa
- **Flow Relation**: Directed connections between Places and Transitions

### Incidence Matrix
- **Forward Matrix F⁺**: Transition → Place connections
- **Backward Matrix F⁻**: Place → Transition connections  
- **Incidence Matrix C**: C = F⁺ - F⁻
- **State Equation**: M' = M + C·σ (where σ is firing vector)

### Matrix Properties
- **C[t, p] > 0**: Transition t produces tokens in place p
- **C[t, p] < 0**: Transition t consumes tokens from place p
- **C[t, p] = 0**: Transition t doesn't affect place p

## Implementation Guidelines

### 1. Always Enforce Bipartite Property
```python
# WRONG: Allows any connection
arc = Arc(obj1, obj2)

# CORRECT: Validates bipartite property
if isinstance(source, Place) and isinstance(target, Transition):
    matrix.add_arc_place_to_transition(source.id, target.id, weight)
elif isinstance(source, Transition) and isinstance(target, Place):
    matrix.add_arc_transition_to_place(source.id, target.id, weight)
else:
    raise ValueError("Invalid arc: must be Place↔Transition")
```

### 2. Matrix as Source of Truth
```python
# Build incidence matrix first
matrix = IncidenceMatrix(places, transitions)
matrix.add_arc_place_to_transition(p1, t1, weight=2)

# Validate structure
is_valid, errors = matrix.validate_bipartite_property()

# Generate visual arcs from matrix
arcs = matrix.generate_arc_list()
```

### 3. Separate Semantics from Visualization
```
Incidence Matrix (F⁺, F⁻, C)  ← What the Petri net MEANS
        ↓
Arc Objects (source, target)   ← How it LOOKS
        ↓
Cairo Rendering (cr.line_to)   ← How it's DRAWN
```

## Testing Strategy

### Unit Tests
- `test_incidence_matrix.py` - Matrix operations
- `test_bipartite_validation.py` - Structure validation
- `test_arc_geometry.py` - Perimeter intersection

### Integration Tests
- `test_kegg_parser_no_spurious_lines.py` - Parser correctness
- `test_petri_net_construction.py` - Matrix-based construction
- `test_arc_selection.py` - Hit detection on long arcs

### Validation Tests
- Verify NO place-to-place arcs in converted models
- Verify incidence matrix matches visual graph
- Verify simulation uses matrix correctly

## Future Work

### Structural Analysis
- P-invariants and T-invariants calculation
- Siphons and traps detection
- Boundedness checking
- Liveness analysis

### Simulation Enhancements
- Matrix-based state equation: M' = M + C·σ
- Reachability graph generation
- Performance optimization using sparse matrices

### Advanced Features
- Colored Petri nets (CPN)
- Hierarchical Petri nets
- Time Petri nets (TPN)
- Stochastic Petri nets (SPN)

## Related Documentation

- See `doc/` for general architecture documentation
- See `tests/` for test implementations
- See `src/shypn/petri/` for implementation (future)

---

**Status**: Planning phase - Implementation starts with Phase 0.5

**Last Updated**: October 2025
