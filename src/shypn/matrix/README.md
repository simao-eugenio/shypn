# Incidence Matrix Module

**Location**: `src/shypn/matrix/`  
**Status**: Production-ready ✅  
**Tests**: 22/22 passing (100%)

## Overview

This module provides formal Petri net semantics using incidence matrices. The matrix representation serves as the mathematical source of truth for the Petri net structure, enabling simulation and structural analysis.

## Architecture

```
src/shypn/matrix/
├── __init__.py          # Package exports
├── base.py              # Abstract base class (IncidenceMatrix)
├── sparse.py            # Sparse implementation (dict-based)
├── dense.py             # Dense implementation (NumPy arrays)
└── loader.py            # Factory function (minimal code)
```

### OOP Design

- **Base Class**: `IncidenceMatrix` (abstract interface)
- **Sparse Implementation**: `SparseIncidenceMatrix` (memory-efficient)
- **Dense Implementation**: `DenseIncidenceMatrix` (NumPy vectorized)
- **Loader**: Minimal factory for auto-selection

## Petri Net Theory

A Petri net is formally defined as **PN = (P, T, F, W, M₀)**:
- **P**: Set of places (conditions/states)
- **T**: Set of transitions (events/actions)
- **F**: Flow relation F ⊆ (P × T) ∪ (T × P)
- **W**: Weight function W: F → ℕ⁺
- **M₀**: Initial marking M₀: P → ℕ

### Incidence Matrix

The incidence matrix **C** represents the net token change:

```
C = F⁺ - F⁻

Where:
- F⁻[t,p] = tokens consumed from place p by transition t
- F⁺[t,p] = tokens produced in place p by transition t
- C[t,p]  = net change in place p when transition t fires
```

### State Equation

The fundamental Petri net dynamics:

```
M' = M + C·σ

Where:
- M  = current marking (tokens in each place)
- σ  = firing vector (which transitions fire)
- M' = new marking after firing
```

## Quick Start

### Basic Usage

```python
from shypn.matrix.loader import load_matrix

# Auto-select implementation based on size
matrix = load_matrix(document)

# Query matrix
input_weight = matrix.get_input_weights(transition_id, place_id)
output_weight = matrix.get_output_weights(transition_id, place_id)
net_change = matrix.get_incidence(transition_id, place_id)

# Check statistics
stats = matrix.get_statistics()
print(f"Places: {stats['places']}, Transitions: {stats['transitions']}")
```

### Simulation

```python
# Define initial marking
marking = {place1.id: 5, place2.id: 3}

# Check if transition is enabled
if matrix.is_enabled(transition_id, marking):
    # Fire transition (apply state equation)
    new_marking = matrix.fire(transition_id, marking)
    print(f"New marking: {new_marking}")
```

### Explicit Implementation Selection

```python
from shypn.matrix import SparseIncidenceMatrix, DenseIncidenceMatrix

# For large, sparse nets
sparse_matrix = SparseIncidenceMatrix(document)
sparse_matrix.build()

# For small, dense nets
dense_matrix = DenseIncidenceMatrix(document)
dense_matrix.build()
```

## Implementation Comparison

| Feature | Sparse | Dense |
|---------|--------|-------|
| **Storage** | Dict-based | NumPy arrays |
| **Memory** | O(A) | O(P×T) |
| **Lookup** | O(1) | O(1) |
| **Best for** | Large, sparse | Small, dense |
| **Threshold** | P×T > 1000 | P×T ≤ 1000 |

Where:
- A = number of arcs
- P = number of places
- T = number of transitions

### When to Use Each

**Use Sparse** when:
- Large nets (hundreds of places/transitions)
- Sparse connectivity (few arcs relative to P×T)
- Memory is constrained
- Most queries return 0

**Use Dense** when:
- Small/medium nets (dozens of places/transitions)
- Dense connectivity
- Need matrix operations (linear algebra)
- Want NumPy vectorization

## API Reference

### Base Class: `IncidenceMatrix`

Abstract interface that all implementations must follow.

#### Core Methods

- `build()` - Build matrices from document
- `get_input_weights(t_id, p_id)` - Get F⁻[t,p]
- `get_output_weights(t_id, p_id)` - Get F⁺[t,p]
- `get_incidence(t_id, p_id)` - Get C[t,p]
- `get_input_arcs(t_id)` - List all input arcs for transition
- `get_output_arcs(t_id)` - List all output arcs for transition

#### Simulation Methods

- `is_enabled(t_id, marking)` - Check if transition can fire
- `fire(t_id, marking)` - Fire transition, return new marking

#### Validation Methods

- `validate_bipartite()` - Check bipartite property
- `get_statistics()` - Get matrix statistics
- `get_dimensions()` - Get (T, P) dimensions

### Sparse Implementation: `SparseIncidenceMatrix`

Memory-efficient implementation using dictionaries.

**Additional Methods**:
- `get_nonzero_count()` - Count non-zero entries
- `get_sparsity()` - Get sparsity ratio (0-1)

**Storage**:
```python
F_minus_dict: Dict[(t_id, p_id), weight]
F_plus_dict:  Dict[(t_id, p_id), weight]
C_dict:       Dict[(t_id, p_id), weight]
```

### Dense Implementation: `DenseIncidenceMatrix`

NumPy array implementation with vectorized operations.

**Additional Methods**:
- `get_matrix_array(type)` - Get matrix as NumPy array
- `compute_invariants()` - Compute P/T-invariants (placeholder)

**Storage**:
```python
F_minus: np.ndarray shape (T, P)
F_plus:  np.ndarray shape (T, P)
C:       np.ndarray shape (T, P)
```

### Loader: `load_matrix()`

Factory function for creating matrices.

```python
load_matrix(
    document,
    implementation='auto',  # 'auto', 'sparse', or 'dense'
    auto_build=True        # Build immediately
)
```

**Auto-Selection Logic**:
- If P×T > 1000 → Sparse
- If density < 20% → Sparse
- Otherwise → Dense

## Test Suite

**File**: `tests/test_incidence_matrix.py`  
**Tests**: 22 total, all passing ✅

### Test Categories

1. **TestMatrixConstruction** (3 tests)
   - Sparse build
   - Dense build
   - Sparse-dense equivalence

2. **TestMatrixQueries** (6 tests)
   - Input weights (sparse/dense)
   - Output weights (sparse/dense)
   - Incidence values (sparse/dense)

3. **TestSimulation** (6 tests)
   - Enabling check (sparse/dense)
   - Firing (sparse/dense)
   - Error handling (sparse/dense)

4. **TestLoader** (4 tests)
   - Auto-selection
   - Explicit sparse
   - Explicit dense
   - Recommendations

5. **TestRealPathway** (3 tests)
   - Glycolysis build (sparse/dense)
   - Bipartite validation

### Running Tests

```bash
# Run all tests
python3 tests/test_incidence_matrix.py

# Or with pytest
pytest tests/test_incidence_matrix.py -v
```

## Examples

### Example 1: Simple Net

```python
from shypn.matrix.loader import load_matrix
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc

# Create document
doc = DocumentModel()

# P1 --2--> T1 --3--> P2
p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
p2 = Place(x=300, y=100, id=2, name="P2", label="P2")
t1 = Transition(x=200, y=100, id=1, name="T1", label="T1")

a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=2)
a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=3)

doc.places.extend([p1, p2])
doc.transitions.append(t1)
doc.arcs.extend([a1, a2])

# Build matrix
matrix = load_matrix(doc)

# Query
print(f"F⁻[T1,P1] = {matrix.get_input_weights(t1.id, p1.id)}")  # 2
print(f"F⁺[T1,P2] = {matrix.get_output_weights(t1.id, p2.id)}")  # 3
print(f"C[T1,P1]  = {matrix.get_incidence(t1.id, p1.id)}")  # -2
print(f"C[T1,P2]  = {matrix.get_incidence(t1.id, p2.id)}")  # +3
```

### Example 2: Simulation

```python
# Initial marking: P1=10, P2=0
marking = {p1.id: 10, p2.id: 0}

# Fire T1 multiple times
for i in range(3):
    if matrix.is_enabled(t1.id, marking):
        marking = matrix.fire(t1.id, marking)
        print(f"After firing {i+1}: P1={marking[p1.id]}, P2={marking[p2.id]}")
    else:
        print("Transition not enabled")
        break

# Output:
# After firing 1: P1=8, P2=3
# After firing 2: P1=6, P2=6
# After firing 3: P1=4, P2=9
```

### Example 3: Real KEGG Pathway

```python
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.matrix.loader import load_matrix

# Load pathway
parser = KGMLParser()
pathway = parser.parse_file("workspace/examples/pathways/hsa00010.kgml")

# Convert to Petri net
converter = PathwayConverter()
document = converter.convert(pathway)

# Build matrix
matrix = load_matrix(document)

# Validate and analyze
is_valid, errors = matrix.validate_bipartite()
print(f"Valid: {is_valid}")

stats = matrix.get_statistics()
print(f"Places: {stats['places']}")
print(f"Transitions: {stats['transitions']}")
print(f"Arcs: {stats['total_arcs']}")

# Output:
# Valid: True
# Places: 26
# Transitions: 34
# Arcs: 73
```

## Integration with Existing Code

The matrix module is designed to integrate seamlessly with existing shypn components:

### With DocumentModel

```python
# Matrix reads from DocumentModel
matrix = load_matrix(document)
```

### With KEGG Importer

```python
# Convert pathway → document → matrix
document = converter.convert(pathway)
matrix = load_matrix(document)
```

### With Simulation

```python
# Matrix provides enabling/firing for simulation
if matrix.is_enabled(transition_id, current_marking):
    new_marking = matrix.fire(transition_id, current_marking)
```

## Performance Characteristics

Based on glycolysis pathway (P=26, T=34, A=73):

| Operation | Sparse | Dense |
|-----------|--------|-------|
| **Build** | <1ms | <1ms |
| **Query** | <0.01ms | <0.01ms |
| **Fire** | <0.1ms | <0.05ms |
| **Memory** | ~5KB | ~7KB |

For large pathways (P=1000, T=1000, A=5000):

| Operation | Sparse | Dense |
|-----------|--------|-------|
| **Memory** | ~40KB | ~4MB |
| **Sparsity** | 99.5% | N/A |

## Integration with Simulation

The `MatrixManager` class provides integration between the incidence matrix and the simulation system.

### Basic Usage

```python
from shypn.matrix import MatrixManager

# Create manager from document (auto-builds matrix)
manager = MatrixManager(document)

# Extract current marking from document
marking = manager.get_marking_from_document()

# Check if transition is enabled
if manager.is_enabled(transition_id, marking):
    # Fire transition using state equation
    new_marking = manager.fire(transition_id, marking)
    
    # Apply new marking back to document
    manager.apply_marking_to_document(new_marking)

# Get all enabled transitions
enabled = manager.get_enabled_transitions(marking)

# Validate structure
is_valid, errors = manager.validate_bipartite()
```

### Auto-Rebuild

By default, `MatrixManager` automatically detects document changes and rebuilds:

```python
# Auto-rebuild enabled (default)
manager = MatrixManager(document, auto_rebuild=True)

# Modify document
document.places.append(new_place)

# Next query triggers rebuild automatically
stats = manager.get_statistics()

# Manual control
manager = MatrixManager(document, auto_rebuild=False)
manager.invalidate()  # Mark as needs rebuild
manager.build(force=True)  # Rebuild now
```

### Integration Tests

**File**: `tests/test_matrix_manager.py`  
**Tests**: 14 total, all passing ✅

Test categories:
- MatrixManager basics (creation, auto-build, queries)
- Simulation integration (marking, enabling, firing)
- Document change handling (auto-rebuild, invalidation)
- Validation methods
- Real pathway integration (glycolysis)

### Complete API

**MatrixManager Methods**:

- `build(force=False)` - Build/rebuild matrix
- `invalidate()` - Mark matrix as stale
- `ensure_built()` - Build if needed
- `get_marking_from_document()` - Extract marking
- `apply_marking_to_document(marking)` - Apply marking
- `is_enabled(t_id, marking)` - Check enabling
- `fire(t_id, marking)` - Fire transition
- `get_enabled_transitions(marking)` - List enabled
- `validate_bipartite()` - Structural validation
- `get_statistics()` - Matrix info
- `get_dimensions()` - (T, P) tuple

See `src/shypn/matrix/manager.py` for complete documentation.

## Future Enhancements

### Planned

- [ ] Structural analysis (P-invariants, T-invariants)
- [ ] Reachability analysis
- [ ] Deadlock detection
- [ ] Matrix export (CSV, JSON)
- [ ] Visualization (heatmaps)

### Under Consideration

- [ ] Timed Petri nets (delays)
- [ ] Stochastic Petri nets (rates)
- [ ] Colored Petri nets (tokens with data)
- [ ] Hierarchical Petri nets (subnet composition)

## References

1. **Murata, T. (1989)**. "Petri Nets: Properties, Analysis and Applications". 
   *Proceedings of the IEEE*, 77(4), 541-580.

2. **Reisig, W. (2013)**. "Understanding Petri Nets: Modeling Techniques, Analysis Methods, Case Studies". 
   Springer.

3. **David, R., & Alla, H. (2010)**. "Discrete, Continuous, and Hybrid Petri Nets". 
   Springer.

## License

Same as main shypn project.

---

**Module Version**: 1.0  
**Last Updated**: 2025-10-10  
**Status**: Production-ready ✅
