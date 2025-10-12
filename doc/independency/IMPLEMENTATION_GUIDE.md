# Independence Detection - Implementation Guide

**Quick Reference for Developers**

---

## Core Concept

```
TWO TRANSITIONS ARE INDEPENDENT ⟺ DON'T SHARE PLACES

t1 ⊥ t2  ⟺  (•t1 ∪ t1•) ∩ (•t2 ∪ t2•) = ∅
```

Place-sharing is the KEY to independence. If transitions don't share input or output places, they can potentially fire in parallel.

---

## API Reference

### Check if Two Transitions are Independent

```python
from shypn.engine.simulation.controller import SimulationController

controller = SimulationController(model)
t1 = model.get_transition('T1')
t2 = model.get_transition('T2')

# Check independence
if controller._are_independent(t1, t2):
    print("T1 and T2 are independent (don't share places)")
else:
    print("T1 and T2 conflict (share at least one place)")
```

### Get Places for a Transition

```python
# Get all places in transition's locality (•t ∪ t•)
places = controller._get_all_places_for_transition(t1)
print(f"T1 interacts with places: {places}")
```

### Build Conflict Graph

```python
# Get all enabled transitions
enabled = controller._find_enabled_transitions()

# Build conflict graph
conflict_sets = controller._compute_conflict_sets(enabled)
print(f"Conflicts: {conflict_sets}")

# Example output:
# {'T1': {'T2'}, 'T2': {'T1'}, 'T3': set(), 'T4': set()}
# Meaning: T1↔T2 conflict, T3 and T4 are independent of all
```

### Group Independent Transitions

```python
# Group transitions into independent sets
groups = controller._get_independent_transitions(enabled)
print(f"Independent groups: {groups}")

# Example output:
# [['T1', 'T3'], ['T2', 'T4']]
# Meaning: [T1, T3] can fire together, [T2, T4] can fire together
```

---

## Common Patterns

### Pattern 1: Linear Chain (No Parallelism)

```
P1 → T1 → P2 → T2 → P3

Analysis:
  T1: {P1, P2}
  T2: {P2, P3}
  
  T1 ∩ T2 = {P2}  ← CONFLICT
  
Result: Must execute sequentially
```

### Pattern 2: Fork (High Parallelism)

```
     ↗ T1 → P2
P1 →   T2 → P3
     ↘ T3 → P4

Analysis:
  T1: {P1, P2}
  T2: {P1, P3}
  T3: {P1, P4}
  
  All share P1 ← CONFLICT
  
Result: Must execute sequentially (token competition)
```

### Pattern 3: Parallel Pipelines (Full Parallelism)

```
P1 → T1 → P2

P3 → T2 → P4

Analysis:
  T1: {P1, P2}
  T2: {P3, P4}
  
  T1 ∩ T2 = ∅  ← INDEPENDENT
  
Result: Can execute in parallel
```

### Pattern 4: Shared Output

```
T1 → P3 ← T2

Analysis:
  T1: {P1, P3}
  T2: {P2, P3}
  
  T1 ∩ T2 = {P3}  ← CONFLICT
  
Result: Must sequence to avoid race on P3
```

---

## Implementation Phases

### ✅ Phase 1: Detection (COMPLETE)
- Detect independence
- Build conflict graph
- Group independent transitions
- **Status**: Tested and working

### ⏭️ Phase 2: Maximal Concurrent Sets (TODO)
- Find largest sets of enabled, independent transitions
- Handle complex dependencies
- Optimize for maximum parallelism

### ⏭️ Phase 3: Maximal Step Execution (TODO)
- Execute concurrent sets atomically
- Handle failures and rollback
- Update tokens correctly

### ⏭️ Phase 4: Settings Integration (TODO)
- Add execution mode to settings
- User choice: Interleaving vs Maximal Step
- Performance monitoring

---

## Testing

### Run Phase 1 Tests

```bash
cd /home/simao/projetos/shypn
python3 tests/test_locality_independence.py
```

Expected output:
```
✅ Passed: 8
❌ Failed: 0
```

### Create Test Networks

```python
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc

# Create simple independent network
p1 = Place(0, 0, 'P1', 'P1', label='P1')
p1.tokens = 10
p2 = Place(100, 0, 'P2', 'P2', label='P2')
p3 = Place(0, 100, 'P3', 'P3', label='P3')
p4 = Place(100, 100, 'P4', 'P4', label='P4')

t1 = Transition(50, 0, 'T1', 'T1', label='T1')
t1.transition_type = 'immediate'
t2 = Transition(50, 100, 'T2', 'T2', label='T2')
t2.transition_type = 'immediate'

# P1 → T1 → P2 (independent pipeline)
arc1 = Arc(p1, t1, 'A1', 'A1', weight=1)
arc2 = Arc(t1, p2, 'A2', 'A2', weight=1)

# P3 → T2 → P4 (independent pipeline)
arc3 = Arc(p3, t2, 'A3', 'A3', weight=1)
arc4 = Arc(t2, p4, 'A4', 'A4', weight=1)

# Test independence
assert controller._are_independent(t1, t2) == True
```

---

## Key Properties

### Mathematical Properties

1. **Symmetry**: `t1 ⊥ t2 ⟺ t2 ⊥ t1` ✅
   - Independence is bidirectional

2. **Non-Reflexive**: `t ⊥ t = False` ✅
   - Transition conflicts with itself

3. **Not Transitive**: ⚠️
   ```
   t1 ⊥ t2 ∧ t2 ⊥ t3  ⇏  t1 ⊥ t3
   ```
   - Need conflict graph, not just pairwise checks

### Behavior Instantiation

**Important**: Each transition has its OWN behavior instance.

```python
# Continuous transitions
behavior_T1 = ContinuousBehavior(T1, model)  # Own RK4₁
behavior_T2 = ContinuousBehavior(T2, model)  # Own RK4₂

# Even if independent, separate algorithms
# Even if conflicting, separate algorithms
# Instantiation is orthogonal to independence!
```

---

## Performance Considerations

### Time Complexity

- **Place extraction**: O(m) where m = arcs per transition
- **Pairwise check**: O(p) where p = places per transition
- **Conflict graph**: O(n² × p) where n = transitions
- **Grouping**: O(n² × p) (greedy algorithm)

### Space Complexity

- **Place sets**: O(n × p)
- **Conflict graph**: O(n²) worst case (fully connected)
- **Groups**: O(n)

### Optimization Opportunities

1. **Cache place sets**: Recompute only on structural change
2. **Cache conflict graph**: Reuse across simulation steps
3. **Better grouping**: Replace greedy with graph coloring
4. **Parallel computation**: Build conflict graph in parallel

---

## Troubleshooting

### Issue: False independence detected

**Symptom**: Transitions marked independent but share places

**Diagnosis**:
```python
# Check place extraction
places_t1 = controller._get_all_places_for_transition(t1)
places_t2 = controller._get_all_places_for_transition(t2)
print(f"T1 places: {places_t1}")
print(f"T2 places: {places_t2}")
print(f"Intersection: {places_t1 & places_t2}")
```

**Common causes**:
- Arc connection issues
- Behavior not properly registered
- Place ID mismatch

### Issue: Too many conflicts detected

**Symptom**: All transitions marked as conflicting

**Diagnosis**:
```python
# Check conflict graph
conflicts = controller._compute_conflict_sets(transitions)
print(f"Conflicts: {conflicts}")

# Verify network structure
for t in transitions:
    places = controller._get_all_places_for_transition(t)
    print(f"{t.id}: {places}")
```

**Common causes**:
- Central place connected to all transitions
- Hub-and-spoke topology
- This may be correct structure!

### Issue: Groups too small

**Symptom**: Many single-transition groups

**Reason**: Greedy algorithm limitation

**Solution**: Accept for Phase 1, improve in Phase 2 with better algorithm

---

## Future Extensions

### Dynamic Independence

Consider token state, not just structure:
```python
# Current (structural):
t1 ⊥ t2  ⟺  (•t1 ∪ t1•) ∩ (•t2 ∪ t2•) = ∅

# Future (dynamic):
t1 ⊥ t2 at state M  ⟺  structural independence
                         AND different token colors
                         AND sufficient tokens
```

### Colored Independence

For colored Petri nets:
```python
# Two transitions may share place but different colors
T1 reads RED tokens from P1
T2 reads BLUE tokens from P1
→ Can fire in parallel (different resources)
```

### Time-Based Independence

For timed transitions:
```python
# Two transitions may be independent at time t
# But conflict at time t+Δt due to timing
→ Need temporal analysis
```

---

## Related Documentation

- **Complete Details**: `PHASE1_INDEPENDENCE_DETECTION_COMPLETE.md`
- **Theoretical Analysis**: `../LOCALITY_PARALLEL_PROCESSING_ANALYSIS.md`
- **Concerns Clarification**: `../LOCALITY_CONCERNS_CLARIFICATION.md`
- **Test Suite**: `/home/simao/projetos/shypn/test_locality_independence.py`

---

**Quick Start**: Just use `controller._are_independent(t1, t2)` to check if two transitions don't share places!

**Document Version**: 1.0  
**Last Updated**: October 11, 2025
