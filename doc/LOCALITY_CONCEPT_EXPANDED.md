# Locality Concept - Comprehensive Definition

**Date**: October 12, 2025  
**Status**: ✅ Complete Specification  
**Version**: 2.0 (Expanded to include minimal patterns)

---

## Core Concept

**Locality** = A transition-centered neighborhood consisting of its connected places via input and output arcs.

### Mathematical Definition

Given a transition **T**, its locality **L(T)** is defined as:

```
L(T) = •T ∪ T•
```

Where:
- **•T** (preset) = Set of input places (places with arcs TO the transition)
- **T•** (postset) = Set of output places (places with arcs FROM the transition)

### Validity Condition

A locality **L(T)** is **valid** if and only if:

```
|•T| ≥ 1  OR  |T•| ≥ 1
```

In other words: **A transition forms a valid locality if it has at least one connected place** (either input or output).

---

## Locality Patterns

### Pattern 1: Normal Transition (P→T→P)

**Definition**: Transition with both input and output places

**Structure**:
```
P1, P2, ..., Pn → T → Pm+1, Pm+2, ..., Pm+k
```

**Constraints**:
- **n ≥ 1** (at least one input place)
- **k ≥ 1** (at least one output place)

**Locality**:
```
L(T) = {P1, P2, ..., Pn, Pm+1, Pm+2, ..., Pm+k}
|L(T)| = n + k ≥ 2
```

**Example**:
```
Place1 →
         T1 → Place3
Place2 →

Locality(T1) = {Place1, Place2, Place3}
Type: Normal
Inputs: 2, Outputs: 1
```

### Pattern 2: Source Transition (T→P)

**Definition**: Transition with only output places (no inputs)

**Structure**:
```
T → P1, P2, ..., Pk
```

**Constraints**:
- **•T = ∅** (no input places)
- **|T•| ≥ 1** (at least one output place)

**Locality**:
```
L(T) = T• = {P1, P2, ..., Pk}
|L(T)| = k ≥ 1
```

**Example**:
```
T1(source) → Place1
           → Place2

Locality(T1) = {Place1, Place2}
Type: Source
Inputs: 0, Outputs: 2
```

**Use Cases**:
- Token generation (system initialization)
- External input modeling
- Resource creation
- Signal generation

### Pattern 3: Sink Transition (P→T)

**Definition**: Transition with only input places (no outputs)

**Structure**:
```
P1, P2, ..., Pn → T
```

**Constraints**:
- **|•T| ≥ 1** (at least one input place)
- **T• = ∅** (no output places)

**Locality**:
```
L(T) = •T = {P1, P2, ..., Pn}
|L(T)| = n ≥ 1
```

**Example**:
```
Place1 →
         T1(sink)
Place2 →

Locality(T1) = {Place1, Place2}
Type: Sink
Inputs: 2, Outputs: 0
```

**Use Cases**:
- Token consumption (termination)
- External output modeling
- Resource destruction
- Signal absorption

### Pattern 4: Multiple-Source Pattern (T→P←T)

**Definition**: Multiple transitions sharing a common output place

**Structure**:
```
T1 →
     P (shared)
T2 →
```

**Localities**:
```
L(T1) = T1• = {P}  (may have other outputs too)
L(T2) = T2• = {P}  (may have other outputs too)
```

**Key Properties**:
- Place **P** appears in multiple localities
- Each transition's locality is computed **independently**
- Shared places are **allowed** (organic system structure)

**Example**:
```
T1 → Place1 (shared)
T2 → Place1 (shared)
T3 → Place2

Locality(T1) = {Place1}
Locality(T2) = {Place1}
Locality(T3) = {Place2}

Place1 is shared between L(T1) and L(T2)
```

**Use Cases**:
- Multiple producers to one consumer
- Resource pooling
- Choice/merge patterns
- Convergent workflows

---

## Shared Places Principle

### Key Concept

**Places can be shared between multiple localities**

This is fundamental to organic Petri net systems and reflects biological/natural system organization where resources are shared between multiple processes.

### Sharing Types

#### Input Sharing (Multiple Consumer)

```
           → T1
P (shared)
           → T2

Locality(T1) = {P, ...}
Locality(T2) = {P, ...}
```

Place **P** is in the **preset** (•T) of multiple transitions.

#### Output Sharing (Multiple Producer)

```
T1 →
     P (shared)
T2 →

Locality(T1) = {..., P}
Locality(T2) = {..., P}
```

Place **P** is in the **postset** (T•) of multiple transitions.

#### Bidirectional Sharing (Complex)

```
T1 → P → T2
     ↑
     T3

Locality(T1) = {..., P}
Locality(T2) = {P, ...}
Locality(T3) = {..., P}
```

Place **P** is shared across three localities in different roles.

---

## Validation Rules

### Valid Localities

A transition **T** forms a valid locality **L(T)** if:

```python
len(input_places) >= 1  OR  len(output_places) >= 1
```

**Examples of VALID localities**:

| Inputs | Outputs | Type | Valid? |
|--------|---------|------|--------|
| 2 | 3 | Normal | ✅ Yes |
| 1 | 1 | Normal | ✅ Yes |
| 0 | 2 | Source | ✅ Yes |
| 0 | 1 | Source | ✅ Yes |
| 3 | 0 | Sink | ✅ Yes |
| 1 | 0 | Sink | ✅ Yes |
| 1 | 5 | Normal | ✅ Yes |
| 10 | 1 | Normal | ✅ Yes |

### Invalid Localities

A transition **T** has an **invalid** (empty) locality if:

```python
len(input_places) == 0  AND  len(output_places) == 0
```

**Example of INVALID locality**:

| Inputs | Outputs | Type | Valid? |
|--------|---------|------|--------|
| 0 | 0 | Isolated | ❌ No |

An isolated transition (no connected arcs) does not form a locality.

---

## Implementation Requirements

### Locality Detection

The `LocalityDetector` must correctly identify:

1. **Input arcs**: `arc.target == transition`  
   These define **•T** (preset)

2. **Output arcs**: `arc.source == transition`  
   These define **T•** (postset)

3. **Input places**: Extract `arc.source` from input arcs  
   Remove duplicates (same place may have multiple arcs)

4. **Output places**: Extract `arc.target` from output arcs  
   Remove duplicates (same place may have multiple arcs)

### Validation Logic

```python
@property
def is_valid(self) -> bool:
    """A locality is valid if it has at least one place."""
    return len(self.input_places) >= 1 or len(self.output_places) >= 1
```

**NOT**:
```python
# ❌ WRONG - This rejects source and sink transitions
return len(self.input_places) >= 1 and len(self.output_places) >= 1
```

### Type Classification

```python
@property
def locality_type(self) -> str:
    """Classify locality type."""
    has_inputs = len(self.input_places) >= 1
    has_outputs = len(self.output_places) >= 1
    
    if not has_inputs and not has_outputs:
        return 'invalid'  # Isolated transition
    elif not has_inputs and has_outputs:
        return 'source'   # T→P pattern
    elif has_inputs and not has_outputs:
        return 'sink'     # P→T pattern
    else:
        return 'normal'   # P→T→P pattern
```

---

## Usage in Simulation

### Token Flow

Localities define the **scope of token movement** during transition firing:

1. **Input places** (•T): Where tokens are **removed**
2. **Output places** (T•): Where tokens are **added**

### Enablement Check

A transition is **enabled** if:

```python
for place in input_places:
    if place.tokens < arc.weight:
        return False  # Not enough tokens
return True  # All input places have sufficient tokens
```

Source transitions (•T = ∅) are **always enabled** (no input requirements).

### Firing Rule

```python
# Remove tokens from input places
for arc in input_arcs:
    arc.source.tokens -= arc.weight

# Add tokens to output places
for arc in output_arcs:
    arc.target.tokens += arc.weight
```

Sink transitions (T• = ∅) only remove tokens (termination).

---

## Usage in Analysis

### Transition Rate Panel

When adding a transition to the plot list:

1. Detect its locality: `locality = detector.get_locality_for_transition(transition)`
2. Check validity: `if locality.is_valid:`
3. Add all connected places for plotting:
   - Input places (green curves)
   - Output places (blue curves)
   - Transition rate/firing (red curve)

### Search Mechanism

When searching for a transition:

1. If exactly one match found, automatically add its locality
2. Display locality summary: `"2 inputs → TransitionName → 3 outputs"`
3. Allow plotting all places in the locality together

### Locality Independence

Transitions with **disjoint localities** can fire **independently** (concurrently):

```python
def are_independent(locality1, locality2) -> bool:
    """Check if two localities are independent."""
    places1 = set(locality1.input_places + locality1.output_places)
    places2 = set(locality2.input_places + locality2.output_places)
    return places1.isdisjoint(places2)
```

Used for parallel execution and conflict detection.

---

## Formal Petri Net Theory

### Terminology

| Symbol | Name | Definition |
|--------|------|------------|
| **•t** | Preset | Input places of transition t |
| **t•** | Postset | Output places of transition t |
| **•p** | Preset | Input transitions of place p |
| **p•** | Postset | Output transitions of place p |

### Locality as Neighborhood

In graph theory terms, a locality is the **1-hop neighborhood** of a transition node in the bipartite Petri net graph.

### Structural Properties

- **Minimal locality size**: 1 (source or sink with 1 place)
- **Maximal locality size**: Unbounded (depends on model)
- **Typical locality size**: 2-5 places for well-structured nets

---

## Examples from Real Systems

### Biochemical Pathways

```
ATP → PhosphorylationReaction → ADP
                              → Phosphate

Locality = {ATP, ADP, Phosphate}
Type: Normal (1 input, 2 outputs)
```

### Manufacturing

```
Assembly → 
           Product → PackagingStation
Components →

Locality(Assembly) = {Components, Product}
Locality(PackagingStation) = {Product, ...}

Product is shared between localities
```

### Communication Protocol

```
SendMessage(source) → MessageQueue
ReceiveMessage → MessageQueue
                 ProcessMessage

Locality(SendMessage) = {MessageQueue}      (source)
Locality(ReceiveMessage) = {MessageQueue}   (sink)
```

---

## Migration Notes

### Old Definition (INCORRECT)

```python
# ❌ Old: Required BOTH inputs AND outputs
def is_valid(self):
    return len(self.input_places) >= 1 and len(self.output_places) >= 1
```

This **rejected** source and sink transitions as invalid localities.

### New Definition (CORRECT)

```python
# ✅ New: Requires at least ONE place (input OR output)
def is_valid(self):
    return len(self.input_places) >= 1 or len(self.output_places) >= 1
```

This **accepts** all connected transitions as valid localities.

### Impact

- More transitions recognized as having valid localities
- Source/sink transitions can now be analyzed properly
- Plot lists show correct locality places for all transition types
- Search mechanism works for all pattern types

---

## Summary

### Key Principles

1. ✅ **Locality = transition + connected places** (input and/or output)
2. ✅ **Valid if has at least ONE place** (not both required)
3. ✅ **Four patterns**: Normal, Source, Sink, Multiple-source
4. ✅ **Shared places allowed** (organic system structure)
5. ✅ **Type classification**: Based on presence of inputs/outputs
6. ✅ **Minimal size = 1** (one transition + one place)

### Patterns Recognized

| Pattern | Notation | Min Places | Example |
|---------|----------|------------|---------|
| Normal | P→T→P | 2 | P1→T1→P2 |
| Source | T→P | 1 | T1→P1 |
| Sink | P→T | 1 | P1→T1 |
| Multiple-source | T→P←T | 1 (shared) | T1→P1←T2 |

### Code Locations to Update

1. **`src/shypn/diagnostic/locality_detector.py`**
   - Fix `Locality.is_valid` property (line ~91)
   - Update docstrings to reflect new definition

2. **`src/shypn/analyses/transition_rate_panel.py`**
   - Verify `add_locality_places()` works for all patterns
   - Update locality display for source/sink transitions

3. **`src/shypn/engine/simulation/controller.py`**
   - Verify `_get_transition_locality_places()` logic
   - Ensure independence detection works for all patterns

4. **`src/shypn/diagnostic/__init__.py`**
   - Update module docstring with new definition

---

**Next Action**: Apply fixes to codebase to implement expanded locality definition.
