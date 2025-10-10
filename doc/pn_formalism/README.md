# Petri Net Formalism Documentation

This directory contains formal documentation about Petri net theory and implementation in SHYPN.

## Documents

### 1. [PETRI_NET_INCIDENCE_MATRIX_APPROACH.md](PETRI_NET_INCIDENCE_MATRIX_APPROACH.md)
**Formal Petri Net Semantics Using Incidence Matrices**

Describes the mathematical foundation of Petri nets and proposes a matrix-based approach:
- Formal definition: PN = (P, T, F, W, M₀)
- Incidence matrix representation (F⁺, F⁻, C)
- Matrix-first architecture (matrix as source of truth)
- Integration with current codebase
- Simulation-ready design

**Key Concept**: Petri nets are not just "connecting dots" - they have formal semantics defined by the incidence matrix. The visual graph should be derived from the matrix, not the other way around.

### 2. [ARC_FAMILY_REVISION_PLAN.md](ARC_FAMILY_REVISION_PLAN.md)
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
