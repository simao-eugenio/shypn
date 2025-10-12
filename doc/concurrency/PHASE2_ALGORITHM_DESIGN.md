# Phase 2: Maximal Concurrent Set Algorithm - Design

**Date**: October 11, 2025  
**Status**: 🔨 In Design  
**Prerequisites**: Phase 1 Complete ✅

---

## 1. Objective

Design and implement an algorithm to find **maximal concurrent sets** of transitions that can fire together in a Petri net.

### 1.1 Problem Definition

**Input**: 
- Set of enabled transitions E = {t₁, t₂, ..., tₙ}
- Conflict graph C (from Phase 1)

**Output**: 
- List of maximal concurrent sets M = {S₁, S₂, ..., Sₖ}

**Constraints**:
1. Each set Sᵢ contains only **independent** transitions (no place sharing)
2. Each set Sᵢ is **maximal** (cannot add more transitions without conflict)
3. Sets may overlap (same transition can appear in multiple maximal sets)
4. Union covers all enabled transitions: ⋃Sᵢ = E

---

## 2. Mathematical Foundation

### 2.1 Definitions

**Concurrent Set**:
```
A set S ⊆ E is concurrent ⟺ ∀t₁, t₂ ∈ S: t₁ ⊥ t₂
(All pairs in S are independent)
```

**Maximal Concurrent Set**:
```
A set S is maximal ⟺ S is concurrent ∧ ∄t ∈ (E \ S): S ∪ {t} is concurrent
(Cannot add any transition without breaking independence)
```

### 2.2 Graph Theory Perspective

The problem is equivalent to finding **maximal independent sets** in the conflict graph:

```
Conflict Graph G = (V, E_c) where:
  V = enabled transitions
  E_c = {(t₁, t₂) | t₁ and t₂ share places}

Maximal Independent Set:
  Set of vertices with no edges between them,
  and cannot be extended without adding an edge.
```

**Known Complexity**: This is the **Maximal Independent Set** problem.
- Listing all maximal independent sets: NP-hard in general
- Finding one maximal set: Polynomial (greedy algorithm)
- Our approach: Find multiple maximal sets (not necessarily all)

---

## 3. Algorithm Options

### 3.1 Option A: Greedy Algorithm (Fast, Non-Optimal)

```python
def find_maximal_concurrent_sets_greedy(enabled, conflicts):
    """Find maximal concurrent sets using greedy approach."""
    maximal_sets = []
    remaining = set(enabled)
    
    while remaining:
        # Start new set with first remaining transition
        current_set = {remaining.pop()}
        
        # Greedily add compatible transitions
        for t in list(remaining):
            if is_independent_of_all(t, current_set, conflicts):
                current_set.add(t)
                remaining.remove(t)
        
        maximal_sets.append(current_set)
    
    return maximal_sets
```

**Pros**:
- Simple and fast: O(n²)
- Guaranteed to find at least one maximal set per transition
- No duplication (each transition in exactly one set)

**Cons**:
- Order-dependent (different orderings give different results)
- May miss important maximal sets
- Not optimal (may not find largest maximal set)

### 3.2 Option B: Bron-Kerbosch Algorithm (Complete, Slower)

```python
def bron_kerbosch(R, P, X, conflicts):
    """Find ALL maximal independent sets."""
    if not P and not X:
        yield R  # Found maximal independent set
        return
    
    for v in list(P):
        neighbors = conflicts[v]
        yield from bron_kerbosch(
            R | {v},
            P & non_neighbors(v, conflicts),
            X & non_neighbors(v, conflicts),
            conflicts
        )
        P = P - {v}
        X = X | {v}
```

**Pros**:
- Finds ALL maximal independent sets
- Optimal and complete
- Well-studied algorithm

**Cons**:
- Exponential worst-case: O(3^(n/3)) maximal sets possible
- Can be very slow for large networks
- May produce too many sets (overwhelming)

### 3.3 Option C: Hybrid Approach (Recommended)

```python
def find_maximal_concurrent_sets_hybrid(enabled, conflicts, max_sets=10):
    """Find multiple maximal sets using multiple greedy passes."""
    maximal_sets = []
    
    # Strategy 1: Greedy from different starting points
    for start_idx in range(min(len(enabled), 5)):
        ordered = rotate_list(enabled, start_idx)
        maximal_set = greedy_maximal_from_order(ordered, conflicts)
        if maximal_set not in maximal_sets:
            maximal_sets.append(maximal_set)
    
    # Strategy 2: Prioritize high-degree vertices (most conflicts)
    ordered = sort_by_conflict_degree(enabled, conflicts, descending=True)
    maximal_set = greedy_maximal_from_order(ordered, conflicts)
    if maximal_set not in maximal_sets:
        maximal_sets.append(maximal_set)
    
    # Strategy 3: Prioritize low-degree vertices (least conflicts)
    ordered = sort_by_conflict_degree(enabled, conflicts, descending=False)
    maximal_set = greedy_maximal_from_order(ordered, conflicts)
    if maximal_set not in maximal_sets:
        maximal_sets.append(maximal_set)
    
    return maximal_sets[:max_sets]
```

**Pros**:
- Finds multiple diverse maximal sets
- Controlled complexity (limit number of sets)
- Better than single greedy pass
- Practical and efficient

**Cons**:
- Not guaranteed to find all maximal sets
- Still some heuristic choices

---

## 4. Recommended Approach: Hybrid with Progressive Refinement

### 4.1 Core Algorithm

```python
def _find_maximal_concurrent_sets(self, enabled_transitions, max_sets=5):
    """
    Find maximal concurrent sets of enabled transitions.
    
    Uses hybrid approach with multiple strategies to find diverse
    maximal sets.
    
    Args:
        enabled_transitions: List of enabled Transition objects
        max_sets: Maximum number of maximal sets to find
        
    Returns:
        List of lists, each inner list is a maximal concurrent set
        
    Example:
        enabled = [T1, T2, T3, T4]
        conflicts = {T1: {T2}, T2: {T1}, T3: {T4}, T4: {T3}}
        
        Result: [[T1, T3], [T2, T4], [T1, T4], [T2, T3]]
        All are maximal (cannot add more without conflict)
    """
    if not enabled_transitions:
        return []
    
    if len(enabled_transitions) == 1:
        return [[enabled_transitions[0]]]
    
    # Build conflict graph
    conflict_sets = self._compute_conflict_sets(enabled_transitions)
    transitions_by_id = {t.id: t for t in enabled_transitions}
    
    maximal_sets = []
    seen_sets = set()  # To avoid duplicates
    
    # Strategy 1: Standard greedy from natural order
    maximal_set = self._greedy_maximal_set(
        enabled_transitions, conflict_sets, start_index=0
    )
    if maximal_set:
        set_key = frozenset(t.id for t in maximal_set)
        seen_sets.add(set_key)
        maximal_sets.append(maximal_set)
    
    # Strategy 2: Try different starting points (rotation)
    for start_idx in range(1, min(len(enabled_transitions), max_sets)):
        maximal_set = self._greedy_maximal_set(
            enabled_transitions, conflict_sets, start_index=start_idx
        )
        if maximal_set:
            set_key = frozenset(t.id for t in maximal_set)
            if set_key not in seen_sets:
                seen_sets.add(set_key)
                maximal_sets.append(maximal_set)
                if len(maximal_sets) >= max_sets:
                    break
    
    # Strategy 3: Prioritize by conflict degree (high to low)
    if len(maximal_sets) < max_sets:
        ordered = self._sort_by_conflict_degree(
            enabled_transitions, conflict_sets, ascending=False
        )
        maximal_set = self._greedy_maximal_set(
            ordered, conflict_sets, start_index=0
        )
        if maximal_set:
            set_key = frozenset(t.id for t in maximal_set)
            if set_key not in seen_sets:
                seen_sets.add(set_key)
                maximal_sets.append(maximal_set)
    
    # Strategy 4: Prioritize by conflict degree (low to high)
    if len(maximal_sets) < max_sets:
        ordered = self._sort_by_conflict_degree(
            enabled_transitions, conflict_sets, ascending=True
        )
        maximal_set = self._greedy_maximal_set(
            ordered, conflict_sets, start_index=0
        )
        if maximal_set:
            set_key = frozenset(t.id for t in maximal_set)
            if set_key not in seen_sets:
                seen_sets.add(set_key)
                maximal_sets.append(maximal_set)
    
    return maximal_sets
```

### 4.2 Helper: Greedy Maximal Set

```python
def _greedy_maximal_set(self, transitions, conflict_sets, start_index=0):
    """
    Build one maximal concurrent set using greedy algorithm.
    
    Args:
        transitions: List of Transition objects to consider
        conflict_sets: Dict mapping transition IDs to conflicting IDs
        start_index: Index to start greedy selection
        
    Returns:
        List of Transition objects forming maximal concurrent set
    """
    if not transitions:
        return []
    
    # Rotate to start from different position
    ordered = transitions[start_index:] + transitions[:start_index]
    
    maximal_set = [ordered[0]]
    maximal_set_ids = {ordered[0].id}
    
    # Try to add each remaining transition
    for t in ordered[1:]:
        # Check if t is independent of all in current set
        can_add = True
        for tid in maximal_set_ids:
            if t.id in conflict_sets[tid]:
                can_add = False
                break
        
        if can_add:
            maximal_set.append(t)
            maximal_set_ids.add(t.id)
    
    return maximal_set
```

### 4.3 Helper: Sort by Conflict Degree

```python
def _sort_by_conflict_degree(self, transitions, conflict_sets, ascending=True):
    """
    Sort transitions by number of conflicts (degree in conflict graph).
    
    Args:
        transitions: List of Transition objects
        conflict_sets: Dict mapping transition IDs to conflicting IDs
        ascending: If True, least conflicts first; if False, most conflicts first
        
    Returns:
        Sorted list of Transition objects
    """
    def conflict_degree(t):
        return len(conflict_sets.get(t.id, set()))
    
    return sorted(transitions, key=conflict_degree, reverse=not ascending)
```

### 4.4 Helper: Check Maximality

```python
def _is_concurrent_set_maximal(self, concurrent_set, all_enabled, conflict_sets):
    """
    Check if a concurrent set is maximal (cannot be extended).
    
    Args:
        concurrent_set: List of Transition objects in the set
        all_enabled: List of all enabled transitions
        conflict_sets: Dict mapping transition IDs to conflicting IDs
        
    Returns:
        True if maximal, False if can be extended
    """
    set_ids = {t.id for t in concurrent_set}
    
    # Try to add each transition not in the set
    for t in all_enabled:
        if t.id in set_ids:
            continue  # Already in set
        
        # Check if t is independent of all in set
        can_add = True
        for tid in set_ids:
            if t.id in conflict_sets[tid]:
                can_add = False
                break
        
        if can_add:
            return False  # Can extend, so not maximal
    
    return True  # Cannot extend, is maximal
```

---

## 5. Complexity Analysis

### 5.1 Time Complexity

**Per Strategy**:
- Greedy maximal set: O(n²) where n = |enabled|
- Conflict degree sort: O(n log n + n²) = O(n²)

**Overall**:
- k strategies, each O(n²)
- Total: O(k × n²) where k ≤ max_sets (typically 5-10)
- Practical: O(n²) for reasonable k

### 5.2 Space Complexity

- Conflict sets: O(n²) worst case
- Maximal sets: O(k × n) where k = number of sets
- Working storage: O(n)
- Total: O(n²)

### 5.3 Comparison with Alternatives

| Algorithm | Time | Space | Completeness | Practical |
|-----------|------|-------|--------------|-----------|
| Single Greedy | O(n²) | O(n²) | 1 set | ✅ Fast |
| Hybrid (k=5) | O(n²) | O(n²) | k sets | ✅ Good balance |
| Bron-Kerbosch | O(3^(n/3)) | O(n²) | All sets | ⚠️ Slow for large n |

---

## 6. Examples

### 6.1 Example 1: Simple Fork

```
Network:
  T1: {P1, P2}
  T2: {P1, P3}
  T3: {P4, P5}

Conflicts:
  T1 ↔ T2 (share P1)
  T3 independent of all

Maximal Concurrent Sets:
  S1 = {T1, T3}  ✅ Maximal (cannot add T2 - conflicts with T1)
  S2 = {T2, T3}  ✅ Maximal (cannot add T1 - conflicts with T2)
  S3 = {T3}      ❌ NOT maximal (can add T1 or T2)
```

### 6.2 Example 2: Complex Network

```
Network:
  T1: {P1, P2}
  T2: {P2, P3}
  T3: {P3, P4}
  T4: {P5, P6}

Conflicts:
  T1 ↔ T2 (share P2)
  T2 ↔ T3 (share P3)
  T4 independent of all

Maximal Concurrent Sets:
  S1 = {T1, T3, T4}  ✅ Maximal
  S2 = {T2, T4}      ✅ Maximal
  S3 = {T1, T4}      ❌ NOT maximal (can add T3)
  S4 = {T3, T4}      ❌ NOT maximal (can add T1)
```

### 6.3 Example 3: Fully Connected (Clique)

```
Network:
  All transitions share central place P1

Conflicts:
  Every transition conflicts with every other

Maximal Concurrent Sets:
  S1 = {T1}  ✅ Maximal
  S2 = {T2}  ✅ Maximal
  S3 = {T3}  ✅ Maximal
  ...
  (Each singleton is maximal)
```

---

## 7. Implementation Strategy

### 7.1 Phase 2A: Core Algorithm (2 hours)

1. ✅ Design algorithm (this document)
2. ⏳ Implement `_greedy_maximal_set()`
3. ⏳ Implement `_sort_by_conflict_degree()`
4. ⏳ Implement `_find_maximal_concurrent_sets()`

### 7.2 Phase 2B: Helpers and Validation (1 hour)

1. ⏳ Implement `_is_concurrent_set_maximal()`
2. ⏳ Add maximality validation in debug mode

### 7.3 Phase 2C: Testing (1 hour)

1. ⏳ Create test suite
2. ⏳ Test with simple networks
3. ⏳ Test with complex networks
4. ⏳ Verify maximality property

---

## 8. Design Decisions

### 8.1 Why Hybrid Approach?

**Decision**: Use multiple greedy strategies instead of Bron-Kerbosch

**Rationale**:
1. **Performance**: O(n²) vs O(3^(n/3)) for large nets
2. **Practicality**: Finding 5-10 good maximal sets is sufficient
3. **Control**: Can limit output size (avoid overwhelming user)
4. **Diversity**: Different strategies find different maximal sets

### 8.2 How Many Maximal Sets?

**Decision**: Default max_sets = 5, configurable

**Rationale**:
1. **Execution**: In Phase 3, we'll select ONE set to fire
2. **Options**: 5 sets give good selection options
3. **Overhead**: More sets = more computation for diminishing returns
4. **UI**: If exposed to user, 5 options is manageable

### 8.3 Which Greedy Strategies?

**Selected**:
1. Natural order (deterministic baseline)
2. Rotated starts (explore different orderings)
3. High-conflict first (handle constrained transitions)
4. Low-conflict first (maximize set size)

**Not Selected**:
- Random order (non-deterministic, testing issues)
- Priority-based (mixing concerns)
- Type-based (not relevant to independence)

### 8.4 Duplicate Detection

**Decision**: Use frozenset of IDs to detect duplicate sets

**Implementation**:
```python
seen_sets = set()
set_key = frozenset(t.id for t in maximal_set)
if set_key not in seen_sets:
    seen_sets.add(set_key)
    maximal_sets.append(maximal_set)
```

**Rationale**: O(n) hash comparison, prevents redundant sets

---

## 9. Testing Strategy

### 9.1 Test Cases

1. **Empty input**: [] → []
2. **Single transition**: [T1] → [[T1]]
3. **Two independent**: [T1, T2] (no conflict) → [[T1, T2]]
4. **Two conflicting**: [T1, T2] (conflict) → [[T1], [T2]] or [[T2], [T1]]
5. **Fork**: T1 ↔ T2, T3 independent → [[T1, T3], [T2, T3]]
6. **Chain**: T1 ↔ T2 ↔ T3 → [[T1, T3], [T2]]
7. **Clique**: All conflict → [[T1], [T2], [T3], ...]
8. **Complex**: Mixed patterns → Multiple maximal sets

### 9.2 Properties to Verify

1. **Concurrency**: Each set contains only independent transitions ✅
2. **Maximality**: Cannot extend any set ✅
3. **Coverage**: All enabled transitions appear in at least one set ✅
4. **No duplicates**: All returned sets are unique ✅
5. **Correctness**: Manual verification for small examples ✅

---

## 10. Integration with Phase 1

### 10.1 Dependencies

Phase 2 uses Phase 1 methods:
```python
# From Phase 1:
conflict_sets = self._compute_conflict_sets(enabled_transitions)
independent = self._are_independent(t1, t2)

# Phase 2 builds on top:
maximal_sets = self._find_maximal_concurrent_sets(enabled_transitions)
```

### 10.2 Code Organization

```
SimulationController:
├── Phase 1: Independence Detection
│   ├── _get_all_places_for_transition()
│   ├── _are_independent()
│   ├── _compute_conflict_sets()
│   └── _get_independent_transitions()
├── Phase 2: Maximal Concurrent Sets  ← NEW
│   ├── _find_maximal_concurrent_sets()
│   ├── _greedy_maximal_set()
│   ├── _sort_by_conflict_degree()
│   └── _is_concurrent_set_maximal()
└── Phase 3: Execution (Future)
    └── _execute_maximal_step()
```

---

## 11. Future Extensions

### 11.1 Dynamic Weighting

Assign weights to transitions for prioritization:
```python
def _greedy_maximal_set_weighted(transitions, conflicts, weights):
    # Sort by weight (higher weight = higher priority)
    ordered = sorted(transitions, key=lambda t: weights[t.id], reverse=True)
    # Then greedy as normal
```

### 11.2 Conflict-Aware Optimization

Track conflict frequency and avoid high-conflict transitions:
```python
# Track which transitions are frequently in conflict
conflict_history = Counter()
# Deprioritize frequently conflicting transitions
```

### 11.3 Complete Enumeration (Optional)

Implement Bron-Kerbosch for small nets:
```python
if len(enabled_transitions) <= 15:
    # Use complete algorithm
    return self._bron_kerbosch_all_maximal_sets(...)
else:
    # Use hybrid heuristic
    return self._find_maximal_concurrent_sets_hybrid(...)
```

---

## 12. Next Steps

### Immediate (Phase 2 Implementation):

1. ✅ Design complete (this document)
2. ⏳ Implement 4 methods in controller.py
3. ⏳ Create test suite
4. ⏳ Run tests and validate
5. ⏳ Document completion

### Follow-up (Phase 3):

1. Select ONE maximal set to fire
2. Execute all transitions in set atomically
3. Handle failures and rollback
4. Document Phase 3

---

**Document Version**: 1.0  
**Status**: Design Complete, Ready for Implementation  
**Next Action**: Implement `_greedy_maximal_set()` method  
**Estimated Time**: 4 hours total for Phase 2
