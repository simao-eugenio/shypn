# Petri Net Formal Approach: Incidence Matrix

## Petri Net Theory Foundation

### Formal Definition

A Petri Net is a 5-tuple: **PN = (P, T, F, W, M₀)**

Where:
- **P** = Set of Places
- **T** = Set of Transitions  
- **F** = Flow relation: F ⊆ (P × T) ∪ (T × P) (bipartite property)
- **W** = Weight function: F → ℕ⁺ (arc weights)
- **M₀** = Initial marking: P → ℕ (token distribution)

### Incidence Matrix Representation

The **Forward Incidence Matrix** **F⁺** is a |T| × |P| matrix where:
- **F⁺[t, p]** = weight of arc from transition t to place p
- **F⁺[t, p]** = 0 if no arc exists

The **Backward Incidence Matrix** **F⁻** is a |T| × |P| matrix where:
- **F⁻[t, p]** = weight of arc from place p to transition t
- **F⁻[t, p]** = 0 if no arc exists

The **Incidence Matrix** **C** is defined as:
```
C = F⁺ - F⁻
```

Where:
- **C[t, p] > 0**: Transition t produces tokens in place p
- **C[t, p] < 0**: Transition t consumes tokens from place p
- **C[t, p] = 0**: Transition t doesn't affect place p

---

## Current Problem: Graph-Based vs Matrix-Based

### Current Approach (WRONG)
```python
# Graph-based: Just connecting dots
arc = Arc(source, target)
manager.arcs.append(arc)

# Problems:
# 1. No validation of bipartite property
# 2. No incidence matrix representation
# 3. Can create invalid connections
# 4. No formal verification
```

### Correct Approach (Matrix-Based)
```python
# Matrix-based: Formal Petri net construction
incidence_matrix = IncidenceMatrix(places, transitions)
incidence_matrix.add_arc(place, transition, weight)  # Validates bipartite
incidence_matrix.add_arc(transition, place, weight)  # Validates bipartite

# Arc creation from matrix
arcs = incidence_matrix.generate_arcs()

# Benefits:
# 1. Enforces bipartite property at construction
# 2. Validates Petri net correctness
# 3. Enables structural analysis
# 4. Supports simulation algorithms
```

---

## Proposed Solution: Dual Representation

### Architecture

```
Petri Net Model
├── Incidence Matrix (F⁺, F⁻, C)  ← Primary representation
│   ├── Enforces bipartite property
│   ├── Validates arc weights
│   └── Enables analysis algorithms
│
└── Visual Graph (Places, Transitions, Arcs)  ← Secondary (derived)
    ├── Generated from incidence matrix
    ├── Used for rendering
    └── Used for user interaction
```

### Workflow

**1. Construction (Matrix-First)**
```python
# User creates/imports Petri net
model = PetriNetModel()
model.add_place("P1")
model.add_transition("T1")
model.add_arc("P1", "T1", weight=2)  # Validated against incidence matrix

# Matrix validates:
# - P1 is a Place
# - T1 is a Transition
# - Connection is Place → Transition (valid)
# - Weight is positive integer
```

**2. Validation**
```python
# Validate Petri net structure
if model.is_valid():
    # Check bipartite property
    # Check no place-to-place arcs
    # Check no transition-to-transition arcs
    # Check all weights > 0
```

**3. Rendering**
```python
# Generate visual graph from matrix
graph = model.generate_visual_graph()
# Graph contains Arc objects for rendering
# But matrix is the source of truth
```

---

## Implementation Plan

### Phase 0.5: Incidence Matrix Foundation (NEW)

#### 1. Create Incidence Matrix Module

**New File: `src/shypn/petri/incidence_matrix.py`**

```python
"""Incidence matrix representation for Petri nets.

This module provides formal Petri net semantics through incidence matrices.
The incidence matrix is the primary representation; visual graph is derived.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np


class IncidenceMatrix:
    """Incidence matrix representation of a Petri net.
    
    Maintains F⁺ (forward), F⁻ (backward), and C (incidence) matrices.
    Enforces bipartite property and validates Petri net structure.
    """
    
    def __init__(self, places: List, transitions: List):
        """Initialize incidence matrices.
        
        Args:
            places: List of Place objects
            transitions: List of Transition objects
        """
        self.places = places
        self.transitions = transitions
        
        # Create index mappings
        self.place_index = {p.id: i for i, p in enumerate(places)}
        self.transition_index = {t.id: i for i, t in enumerate(transitions)}
        
        # Initialize matrices (|T| × |P|)
        num_transitions = len(transitions)
        num_places = len(places)
        
        self.F_plus = np.zeros((num_transitions, num_places), dtype=int)   # T → P
        self.F_minus = np.zeros((num_transitions, num_places), dtype=int)  # P → T
        self.C = np.zeros((num_transitions, num_places), dtype=int)        # F⁺ - F⁻
    
    def add_arc_place_to_transition(self, place_id: str, transition_id: str, weight: int = 1):
        """Add arc from place to transition (input arc).
        
        Updates F⁻ matrix: F⁻[t, p] = weight
        
        Args:
            place_id: Place identifier
            transition_id: Transition identifier
            weight: Arc weight (default 1)
            
        Raises:
            ValueError: If place/transition not found or weight invalid
        """
        if weight < 1:
            raise ValueError(f"Arc weight must be ≥ 1, got {weight}")
        
        if place_id not in self.place_index:
            raise ValueError(f"Place {place_id} not found")
        
        if transition_id not in self.transition_index:
            raise ValueError(f"Transition {transition_id} not found")
        
        p_idx = self.place_index[place_id]
        t_idx = self.transition_index[transition_id]
        
        self.F_minus[t_idx, p_idx] = weight
        self._update_incidence_matrix()
    
    def add_arc_transition_to_place(self, transition_id: str, place_id: str, weight: int = 1):
        """Add arc from transition to place (output arc).
        
        Updates F⁺ matrix: F⁺[t, p] = weight
        
        Args:
            transition_id: Transition identifier
            place_id: Place identifier
            weight: Arc weight (default 1)
            
        Raises:
            ValueError: If place/transition not found or weight invalid
        """
        if weight < 1:
            raise ValueError(f"Arc weight must be ≥ 1, got {weight}")
        
        if place_id not in self.place_index:
            raise ValueError(f"Place {place_id} not found")
        
        if transition_id not in self.transition_index:
            raise ValueError(f"Transition {transition_id} not found")
        
        p_idx = self.place_index[place_id]
        t_idx = self.transition_index[transition_id]
        
        self.F_plus[t_idx, p_idx] = weight
        self._update_incidence_matrix()
    
    def _update_incidence_matrix(self):
        """Update incidence matrix C = F⁺ - F⁻."""
        self.C = self.F_plus - self.F_minus
    
    def validate_bipartite_property(self) -> Tuple[bool, List[str]]:
        """Validate bipartite property of Petri net.
        
        Returns:
            (is_valid, errors): Tuple of validation result and error messages
        """
        errors = []
        
        # All arcs must be Place↔Transition only
        # This is enforced by matrix structure (no place-to-place possible)
        
        # Check for self-loops (would be invalid)
        # In bipartite graph, no element can connect to itself
        
        # Check that F⁺ and F⁻ don't overlap (would indicate bidirectional arc)
        overlap = np.logical_and(self.F_plus > 0, self.F_minus > 0)
        if np.any(overlap):
            t_idx, p_idx = np.where(overlap)
            for t, p in zip(t_idx, p_idx):
                trans = self.transitions[t]
                place = self.places[p]
                errors.append(
                    f"Bidirectional arc between {place.id} and {trans.id} "
                    f"(both F⁺ and F⁻ > 0)"
                )
        
        return len(errors) == 0, errors
    
    def get_input_places(self, transition_id: str) -> List[Tuple[str, int]]:
        """Get input places for a transition (• t).
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            List of (place_id, weight) tuples
        """
        if transition_id not in self.transition_index:
            return []
        
        t_idx = self.transition_index[transition_id]
        inputs = []
        
        for p_idx, weight in enumerate(self.F_minus[t_idx]):
            if weight > 0:
                place = self.places[p_idx]
                inputs.append((place.id, int(weight)))
        
        return inputs
    
    def get_output_places(self, transition_id: str) -> List[Tuple[str, int]]:
        """Get output places for a transition (t •).
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            List of (place_id, weight) tuples
        """
        if transition_id not in self.transition_index:
            return []
        
        t_idx = self.transition_index[transition_id]
        outputs = []
        
        for p_idx, weight in enumerate(self.F_plus[t_idx]):
            if weight > 0:
                place = self.places[p_idx]
                outputs.append((place.id, int(weight)))
        
        return outputs
    
    def generate_arc_list(self) -> List[Tuple[str, str, int, str]]:
        """Generate list of arcs from incidence matrices.
        
        Returns:
            List of (source_id, target_id, weight, arc_type) tuples
            arc_type is either 'input' (P→T) or 'output' (T→P)
        """
        arcs = []
        
        # Input arcs (P → T): From F⁻ matrix
        for t_idx, transition in enumerate(self.transitions):
            for p_idx, weight in enumerate(self.F_minus[t_idx]):
                if weight > 0:
                    place = self.places[p_idx]
                    arcs.append((place.id, transition.id, int(weight), 'input'))
        
        # Output arcs (T → P): From F⁺ matrix
        for t_idx, transition in enumerate(self.transitions):
            for p_idx, weight in enumerate(self.F_plus[t_idx]):
                if weight > 0:
                    place = self.places[p_idx]
                    arcs.append((transition.id, place.id, int(weight), 'output'))
        
        return arcs
    
    def to_sparse_representation(self) -> Dict:
        """Export to sparse matrix representation for storage.
        
        Returns:
            Dictionary with matrix data in sparse format
        """
        return {
            'places': [p.id for p in self.places],
            'transitions': [t.id for t in self.transitions],
            'F_plus': self._matrix_to_sparse(self.F_plus),
            'F_minus': self._matrix_to_sparse(self.F_minus),
        }
    
    def _matrix_to_sparse(self, matrix: np.ndarray) -> List[Tuple[int, int, int]]:
        """Convert matrix to sparse representation.
        
        Args:
            matrix: NumPy array
            
        Returns:
            List of (row, col, value) tuples for non-zero entries
        """
        rows, cols = np.where(matrix > 0)
        return [(int(r), int(c), int(matrix[r, c])) for r, c in zip(rows, cols)]
    
    def __str__(self) -> str:
        """String representation showing matrices."""
        lines = ["Incidence Matrix Representation:"]
        lines.append(f"  Places: {len(self.places)}")
        lines.append(f"  Transitions: {len(self.transitions)}")
        lines.append(f"  Input arcs (P→T): {np.count_nonzero(self.F_minus)}")
        lines.append(f"  Output arcs (T→P): {np.count_nonzero(self.F_plus)}")
        return '\n'.join(lines)
```

#### 2. Integrate with Model

**Modify: `src/shypn/data/model_canvas_manager.py`**

```python
class ModelCanvasManager:
    """Canvas manager with incidence matrix backing."""
    
    def __init__(self):
        # Existing code...
        
        # Add incidence matrix (optional, for validation)
        self._incidence_matrix: Optional[IncidenceMatrix] = None
        self._matrix_dirty = True  # Flag to rebuild matrix
    
    def build_incidence_matrix(self) -> IncidenceMatrix:
        """Build incidence matrix from current Petri net state.
        
        Returns:
            IncidenceMatrix representation
        """
        matrix = IncidenceMatrix(self.places, self.transitions)
        
        # Populate matrix from arcs
        for arc in self.arcs:
            source_id = arc.source.id
            target_id = arc.target.id
            weight = arc.weight
            
            # Determine arc type
            if isinstance(arc.source, Place) and isinstance(arc.target, Transition):
                # Input arc: P → T
                matrix.add_arc_place_to_transition(source_id, target_id, weight)
            elif isinstance(arc.source, Transition) and isinstance(arc.target, Place):
                # Output arc: T → P
                matrix.add_arc_transition_to_place(source_id, target_id, weight)
            else:
                # This should never happen if Arc validation is correct
                raise ValueError(f"Invalid arc: {source_id} → {target_id}")
        
        self._incidence_matrix = matrix
        self._matrix_dirty = False
        return matrix
    
    def validate_petri_net_structure(self) -> Tuple[bool, List[str]]:
        """Validate Petri net using incidence matrix.
        
        Returns:
            (is_valid, errors): Validation result and error messages
        """
        if self._matrix_dirty or self._incidence_matrix is None:
            self.build_incidence_matrix()
        
        return self._incidence_matrix.validate_bipartite_property()
    
    def add_arc(self, source, target):
        """Add arc with matrix validation."""
        # Existing arc creation...
        arc = Arc(source, target, ...)
        self.arcs.append(arc)
        
        # Mark matrix as dirty for rebuild
        self._matrix_dirty = True
        
        return arc
```

#### 3. KEGG Converter Integration

**Modify: `src/shypn/importer/kegg/pathway_converter.py`**

```python
def convert(self, pathway: KEGGPathway, options: ConversionOptions) -> DocumentModel:
    """Convert using incidence matrix approach."""
    
    # Phase 1: Create places and transitions
    places = []
    transitions = []
    # ... existing code ...
    
    # Phase 2: Build incidence matrix
    matrix = IncidenceMatrix(places, transitions)
    
    # Phase 3: Populate matrix from reactions
    for reaction in pathway.reactions:
        for substrate in reaction.substrates:
            # Input arc: Place → Transition
            matrix.add_arc_place_to_transition(
                substrate.id,
                transition.id,
                weight=1  # Can extract from KEGG if available
            )
        
        for product in reaction.products:
            # Output arc: Transition → Place
            matrix.add_arc_transition_to_place(
                transition.id,
                product.id,
                weight=1
            )
    
    # Phase 4: Validate bipartite property
    is_valid, errors = matrix.validate_bipartite_property()
    if not is_valid:
        raise ValueError(f"Invalid Petri net structure: {errors}")
    
    # Phase 5: Generate Arc objects from matrix
    arc_list = matrix.generate_arc_list()
    arcs = []
    
    for source_id, target_id, weight, arc_type in arc_list:
        if arc_type == 'input':
            source = place_map[source_id]
            target = transition_map[target_id]
        else:  # output
            source = transition_map[source_id]
            target = place_map[target_id]
        
        arc = Arc(source, target, arc_id, "", weight=weight)
        arcs.append(arc)
    
    # Phase 6: Build document
    document = DocumentModel()
    document.places = places
    document.transitions = transitions
    document.arcs = arcs
    
    return document
```

---

## Benefits of Matrix-Based Approach

### 1. Formal Correctness
✅ Enforces bipartite property at construction
✅ Validates Petri net structure mathematically
✅ Prevents place-to-place connections
✅ Prevents transition-to-transition connections

### 2. Simulation Ready
✅ Incidence matrix directly used in simulation
✅ Enables state equation: M' = M + C·σ (where σ is firing vector)
✅ Supports reachability analysis
✅ Enables P-invariant and T-invariant calculation

### 3. Analysis Capabilities
✅ Structural analysis (siphons, traps)
✅ Boundedness checking
✅ Liveness analysis
✅ Reversibility checking

### 4. Clean Architecture
✅ Separation of concerns: Matrix (semantics) vs Graph (visualization)
✅ Matrix is source of truth
✅ Visual graph is derived representation
✅ Prevents semantic violations

---

## Updated Implementation Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 0.5: Incidence Matrix** | **1 week** | **Matrix-based Petri net** |
| Phase 0: Parser Investigation | 3 days | No spurious lines from parser |
| Phase 1: Core Geometry | 1 week | Perimeter intersection |
| Phase 2: Remove Legacy | 3 days | Clean parallel arc code |
| Phase 3: Arc Transform | 2 days | Manual transformation |
| Phase 4: Hit Detection | 2 days | Selectable long arcs |
| Phase 5: Testing | 1 week | All tests passing |
| Phase 6: Documentation | 2 days | Complete docs |

**Total: ~4.5 weeks** (includes matrix foundation)

---

## Conclusion

You're absolutely correct - Petri nets are not just "connecting dots over graph elements." They have formal mathematical semantics defined by the incidence matrix. The matrix representation:

1. **Enforces correctness** - Bipartite property is structural
2. **Enables analysis** - Matrix operations for simulation and analysis
3. **Prevents errors** - Invalid connections caught at construction
4. **Supports theory** - Aligns with formal Petri net literature

The visual graph (Arc objects) should be **derived** from the incidence matrix, not the other way around. This ensures semantic correctness at all times.

**Next step**: Implement incidence matrix foundation (Phase 0.5)?
