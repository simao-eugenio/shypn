# Matrix Module - Quick Reference

**Version**: 1.0  
**Status**: Production Ready ✅  
**Tests**: 36/36 passing

---

## Quick Start

### Installation

The matrix module is included in shypn:

```python
from shypn.matrix import load_matrix, MatrixManager
```

### Basic Usage (5 lines)

```python
from shypn.matrix import MatrixManager

manager = MatrixManager(document)
marking = manager.get_marking_from_document()
enabled = manager.get_enabled_transitions(marking)
new_marking = manager.fire(enabled[0], marking)
manager.apply_marking_to_document(new_marking)
```

---

## API Cheat Sheet

### Load Matrix (Foundation)

```python
from shypn.matrix import load_matrix

# Auto-select implementation (recommended)
matrix = load_matrix(document)

# Force sparse
matrix = load_matrix(document, implementation='sparse')

# Force dense
matrix = load_matrix(document, implementation='dense')
```

### Query Structure

```python
# Input weights (F⁻)
weight = matrix.get_input_weights(t_id, p_id)

# Output weights (F⁺)
weight = matrix.get_output_weights(t_id, p_id)

# Incidence (C = F⁺ - F⁻)
incidence = matrix.get_incidence(t_id, p_id)
```

### Simulation (Low-level)

```python
# Create marking dict
marking = {place.id: place.tokens for place in document.places}

# Check if enabled
if matrix.is_enabled(transition_id, marking):
    # Fire transition (returns new marking)
    new_marking = matrix.fire(transition_id, marking)
```

### MatrixManager (High-level)

```python
from shypn.matrix import MatrixManager

# Create manager
manager = MatrixManager(document, auto_rebuild=True)

# Extract marking from document
marking = manager.get_marking_from_document()

# Get enabled transitions
enabled = manager.get_enabled_transitions(marking)

# Fire transition
new_marking = manager.fire(transition_id, marking)

# Apply marking to document
manager.apply_marking_to_document(new_marking)

# Validate structure
is_valid, errors = manager.validate_bipartite()

# Get statistics
stats = manager.get_statistics()
# {'built': True, 'places': 10, 'transitions': 8, ...}
```

---

## Common Patterns

### Pattern 1: Single Simulation Step

```python
manager = MatrixManager(document)
marking = manager.get_marking_from_document()

enabled = manager.get_enabled_transitions(marking)
if enabled:
    marking = manager.fire(enabled[0], marking)
    manager.apply_marking_to_document(marking)
```

### Pattern 2: Simulation Loop

```python
manager = MatrixManager(document)

for step in range(max_steps):
    marking = manager.get_marking_from_document()
    enabled = manager.get_enabled_transitions(marking)
    
    if not enabled:
        break
    
    marking = manager.fire(enabled[0], marking)
    manager.apply_marking_to_document(marking)
```

### Pattern 3: Validation Before Simulation

```python
manager = MatrixManager(document)

is_valid, errors = manager.validate_bipartite()
if not is_valid:
    print(f"Invalid structure: {errors}")
    return

# Proceed with simulation...
```

### Pattern 4: Document Change Handling

```python
# Auto-rebuild enabled (default)
manager = MatrixManager(document, auto_rebuild=True)

# Modify document
document.places.append(new_place)

# Manager detects change and rebuilds automatically
stats = manager.get_statistics()
```

### Pattern 5: Manual Control

```python
# Disable auto-rebuild
manager = MatrixManager(document, auto_rebuild=False)

# Modify document
document.places.append(new_place)

# Manually invalidate and rebuild
manager.invalidate()
manager.build(force=True)
```

---

## Implementation Selection Guide

### Auto-Selection Logic

```python
matrix = load_matrix(document)  # Auto-selects based on:
```

**Selects Sparse if**:
- P × T > 1000 (large matrix)
- OR density < 20% (sparse matrix)

**Selects Dense otherwise**:
- Small matrices (fast)
- Dense matrices (memory OK)

### When to Force Sparse

```python
matrix = load_matrix(document, implementation='sparse')
```

Use when:
- Very large networks (P > 1000 or T > 1000)
- Memory is constrained
- Network is very sparse (< 10% density)

### When to Force Dense

```python
matrix = load_matrix(document, implementation='dense')
```

Use when:
- Small networks (P < 100, T < 100)
- Need vectorized operations
- Network is dense (> 50% density)
- Want to compute invariants later

---

## State Equation Reference

### Formal Definition

**State Equation**:
```
M' = M + C·σ
```

Where:
- `M` = current marking vector
- `M'` = new marking vector
- `C` = incidence matrix (F⁺ - F⁻)
- `σ` = firing vector (1 for fired transition)

**Enabling Rule**:
```
∀p ∈ P: M(p) ≥ F⁻(t,p)
```

**Firing Rule**:
```
M'(p) = M(p) - F⁻(t,p) + F⁺(t,p)
```

### Python Implementation

```python
# Check enabling
def is_enabled(t_id, marking):
    for p_id in places:
        if marking[p_id] < matrix.get_input_weights(t_id, p_id):
            return False
    return True

# Fire transition
def fire(t_id, marking):
    new_marking = marking.copy()
    for p_id in places:
        new_marking[p_id] += matrix.get_incidence(t_id, p_id)
    return new_marking
```

---

## Performance Tips

### Tip 1: Use Auto-Selection

```python
# Good: Let loader choose
matrix = load_matrix(document)

# Bad: Forcing without reason
matrix = load_matrix(document, implementation='dense')
```

### Tip 2: Enable Auto-Rebuild

```python
# Good: Changes handled automatically
manager = MatrixManager(document, auto_rebuild=True)

# Use case: More efficient if document changes rarely
manager = MatrixManager(document, auto_rebuild=False)
```

### Tip 3: Reuse Manager

```python
# Good: Create once, use many times
manager = MatrixManager(document)
for i in range(1000):
    marking = manager.get_marking_from_document()
    # ...

# Bad: Creating new manager every time
for i in range(1000):
    manager = MatrixManager(document)
    # ...
```

### Tip 4: Batch Operations

```python
# Good: Get all enabled at once
enabled = manager.get_enabled_transitions(marking)
for t_id in enabled:
    # Process...

# Bad: Check each transition individually
for t in transitions:
    if manager.is_enabled(t.id, marking):
        # Process...
```

---

## Error Handling

### Common Errors

**Not Enabled Error**:
```python
try:
    new_marking = matrix.fire(t_id, marking)
except ValueError as e:
    print(f"Transition not enabled: {e}")
```

**Invalid Structure**:
```python
is_valid, errors = manager.validate_bipartite()
if not is_valid:
    for error in errors:
        print(f"Structure error: {error}")
```

**Document Changed**:
```python
# With auto_rebuild=True, handled automatically
manager = MatrixManager(document, auto_rebuild=True)
document.places.append(new_place)
# Next query triggers rebuild

# With auto_rebuild=False, must rebuild manually
manager = MatrixManager(document, auto_rebuild=False)
document.places.append(new_place)
manager.build(force=True)
```

---

## Testing

### Run All Tests

```bash
pytest tests/test_incidence_matrix.py tests/test_matrix_manager.py -v
```

### Run Specific Test Category

```bash
# Foundation tests only
pytest tests/test_incidence_matrix.py -v

# Integration tests only
pytest tests/test_matrix_manager.py -v

# Specific test class
pytest tests/test_matrix_manager.py::TestSimulationIntegration -v
```

### Run Example

```bash
python3 examples/matrix_integration_example.py
```

---

## Debugging

### Enable Verbose Output

```python
import logging
logging.basicConfig(level=logging.DEBUG)

manager = MatrixManager(document)
# Now shows debug info about rebuilds, etc.
```

### Inspect Matrix State

```python
manager = MatrixManager(document)

# Get statistics
stats = manager.get_statistics()
print(f"Matrix: {stats}")

# Get dimensions
num_t, num_p = manager.get_dimensions()
print(f"Dimensions: {num_t} transitions × {num_p} places")

# Print incidence matrix
print("\nIncidence Matrix C:")
for t in document.transitions:
    print(f"{t.label:10} ", end="")
    for p in document.places:
        c = manager.get_incidence(t.id, p.id)
        print(f"{c:4} ", end="")
    print()
```

### Check What Changed

```python
manager = MatrixManager(document)
old_hash = manager._last_build_hash

# Modify document
document.places.append(new_place)

# Check if changed
new_hash = manager._compute_document_hash()
if old_hash != new_hash:
    print("Document has changed!")
```

---

## Examples

### Example 1: Simple Producer-Consumer

```python
doc = DocumentModel()

# P1 → T1 → P2
p1 = Place(x=100, y=100, id=1, name="P1")
p2 = Place(x=300, y=100, id=2, name="P2")
t1 = Transition(x=200, y=100, id=1, name="T1")

p1.tokens = 5
a1 = Arc(source=p1, target=t1, id=1, weight=1)
a2 = Arc(source=t1, target=p2, id=2, weight=1)

doc.places.extend([p1, p2])
doc.transitions.append(t1)
doc.arcs.extend([a1, a2])

manager = MatrixManager(doc)
marking = manager.get_marking_from_document()

for _ in range(5):
    if manager.is_enabled(1, marking):
        marking = manager.fire(1, marking)

manager.apply_marking_to_document(marking)
print(f"P1: {p1.tokens}, P2: {p2.tokens}")  # P1: 0, P2: 5
```

### Example 2: Load from KEGG

```python
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import PathwayConverter

parser = KGMLParser()
pathway = parser.parse_file("pathway.kgml")

converter = PathwayConverter()
document = converter.convert(pathway)

manager = MatrixManager(document)
stats = manager.get_statistics()

print(f"Loaded pathway: {stats['places']}P, {stats['transitions']}T")
```

---

## Further Reading

- **Module Documentation**: `src/shypn/matrix/README.md`
- **Integration Guide**: `doc/PHASE0_5B_MATRIX_INTEGRATION.md`
- **Complete Summary**: `doc/PHASE0_5_COMPLETE_SUMMARY.md`
- **Theory**: Murata, T. (1989). "Petri Nets: Properties, Analysis and Applications"

---

**Quick Reference Version**: 1.0  
**Last Updated**: 2025-10-10  
**Status**: Production Ready ✅
