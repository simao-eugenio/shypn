# Independence Detection Documentation

**Phase 1: Complete ✅**  
**Date**: October 11, 2025

---

## Overview

This directory contains documentation for the **independence detection** system (Phase 1) in the Shypn Petri net simulator. The system analyzes which transitions can potentially fire in parallel by detecting place-sharing patterns.

**Note**: Phase 2 (Maximal Concurrent Sets) documentation has been moved to `../concurrency/`.

---

## Core Principle

```
Two transitions are INDEPENDENT ⟺ They DON'T SHARE PLACES

Formally: t1 ⊥ t2  ⟺  (•t1 ∪ t1•) ∩ (•t2 ∪ t2•) = ∅
```

Place-sharing is the key to independence. Transitions that don't share input or output places can potentially fire in parallel without interference.

---

## Documents

### 1. PHASE1_INDEPENDENCE_DETECTION_COMPLETE.md
**Comprehensive documentation of Phase 1 implementation**

- **Contents**: 
  - Executive summary
  - Implementation details (4 methods)
  - Test suite results (8/8 passed)
  - Theoretical foundation
  - Mathematical properties
  - Use cases and applications
  - Limitations and future work

- **Who should read**: 
  - Developers working on parallel execution
  - Anyone wanting to understand the independence system
  - Researchers interested in theoretical foundations

- **Length**: ~80 pages

### 2. PHASE2_MAXIMAL_CONCURRENT_SETS_COMPLETE.md
**→ MOVED TO** `../concurrency/PHASE2_MAXIMAL_CONCURRENT_SETS_COMPLETE.md`

Phase 2 documentation has been moved to the `concurrency` directory.
See `../concurrency/README.md` for maximal concurrent set documentation.

### 3. PHASE2_ALGORITHM_DESIGN.md
**→ MOVED TO** `../concurrency/PHASE2_ALGORITHM_DESIGN.md`

Algorithm design documentation has been moved to the `concurrency` directory.

### 4. IMPLEMENTATION_GUIDE.md
**Quick reference for developers**

- **Contents**:
  - API reference with code examples
  - Common patterns (linear, fork, parallel, shared output)
  - Testing instructions
  - Troubleshooting guide
  - Performance considerations

- **Who should read**:
  - Developers using the independence API
  - Anyone implementing new features on top of Phases 1-2
  - Quick lookup for method signatures

- **Length**: ~20 pages

---

## Quick Start

### Check if Two Transitions are Independent (Phase 1)

```python
from shypn.engine.simulation.controller import SimulationController

controller = SimulationController(model)
t1 = model.get_transition('T1')
t2 = model.get_transition('T2')

if controller._are_independent(t1, t2):
    print("Can fire in parallel")
else:
    print("Must be sequenced")
```

### Find Maximal Concurrent Sets (Phase 2)

```python
from shypn.engine.simulation.controller import SimulationController

controller = SimulationController(model)
enabled = controller._find_enabled_transitions()

# Find up to 5 maximal concurrent sets
maximal_sets = controller._find_maximal_concurrent_sets(enabled, max_sets=5)

print(f"Found {len(maximal_sets)} maximal concurrent sets:")
for i, mset in enumerate(maximal_sets, 1):
    ids = [t.id for t in mset]
    print(f"  Set {i}: {ids} ({len(ids)} transitions)")
```

### Run Tests

**Phase 1 Tests**:
```bash
cd /home/simao/projetos/shypn
python3 tests/test_locality_independence.py
```
Expected: `✅ Passed: 8 | ❌ Failed: 0`

**Phase 2 Tests**:
```bash
cd /home/simao/projetos/shypn
python3 tests/test_maximal_concurrent_sets.py
```
Expected: `✅ Passed: 7 | ❌ Failed: 0`

---

## Implementation Status

### ✅ Phase 1: Independence Detection (COMPLETE)

**Implementation**: `src/shypn/engine/simulation/controller.py` (lines ~540-720)

**Methods**:
1. ✅ `_get_all_places_for_transition(transition)` - Extract locality
2. ✅ `_are_independent(t1, t2)` - Check place sharing
3. ✅ `_compute_conflict_sets(transitions)` - Build conflict graph
4. ✅ `_get_independent_transitions(transitions)` - Group for parallelism

**Tests**: 8/8 passed
- Place extraction ✅
- Independence detection ✅
- Conflict detection (input) ✅
- Conflict detection (output) ✅
- Conflict graph ✅
- Independent grouping ✅
- Symmetry property ✅
- Reflexivity property ✅

**Documentation**: Complete
- Comprehensive guide (80 pages) ✅
- Implementation guide (20 pages) ✅
- Test suite (500 lines) ✅

### ✅ Phase 2: Maximal Concurrent Sets (COMPLETE)

**→ Documentation moved to** `../concurrency/`

Phase 2 has been completed and its documentation moved to the `concurrency` directory.

**Quick Links**:
- **Overview**: `../concurrency/README.md`
- **Algorithm Design**: `../concurrency/PHASE2_ALGORITHM_DESIGN.md`
- **Complete Docs**: `../concurrency/PHASE2_MAXIMAL_CONCURRENT_SETS_COMPLETE.md`
- **Test Suite**: `tests/test_maximal_concurrent_sets.py` (7/7 passed)

**Implementation**: `src/shypn/engine/simulation/controller.py` (lines ~720-965)

**Summary**: Finds maximal sets of transitions that can fire together using hybrid algorithm with O(n²) complexity.

**Goal**: Find largest sets of enabled, independent transitions

**Estimated time**: 4 hours

**Prerequisites**: Phase 1 complete ✅

### ⏭️ Phase 3: Maximal Step Execution (TODO)

**Goal**: Execute concurrent sets atomically

**Estimated time**: 6 hours

**Prerequisites**: Phases 1-2 complete

### ⏭️ Phase 4: Settings Integration (TODO)

**Goal**: User configuration for execution mode

**Estimated time**: 6 hours

**Prerequisites**: Phases 1-3 complete

---

## Key Concepts

### Locality
A transition's **locality** is the set of all places it interacts with:
```
Locality(t) = •t ∪ t•

Where:
  •t  = Input places (pre-set)
  t•  = Output places (post-set)
```

### Independence
Two transitions are **independent** if their localities don't overlap:
```
t1 ⊥ t2  ⟺  Locality(t1) ∩ Locality(t2) = ∅
```

### Conflict
Two transitions **conflict** if they share at least one place:
```
t1 conflicts with t2  ⟺  NOT (t1 ⊥ t2)
```

### Behavior Instantiation
Each transition has its own behavior instance (e.g., own RK4 integrator):
```python
behavior_T1 = ContinuousBehavior(T1, model)  # Has RK4₁
behavior_T2 = ContinuousBehavior(T2, model)  # Has RK4₂
# Separate objects, separate algorithms!
```

---

## Network Patterns

### Pattern 1: Independent Pipelines (Full Parallelism)
```
P1 → T1 → P2

P3 → T2 → P4

Result: T1 ⊥ T2 (no shared places)
Can fire in parallel ✅
```

### Pattern 2: Shared Input (Conflict)
```
P1 → T1 → P2
P1 → T2 → P3

Result: T1 and T2 share P1
Must be sequenced ❌
```

### Pattern 3: Shared Output (Conflict)
```
P1 → T1 → P3
P2 → T2 → P3

Result: T1 and T2 share P3
Must be sequenced ❌
```

### Pattern 4: Linear Chain (No Parallelism)
```
P1 → T1 → P2 → T2 → P3

Result: T1 and T2 share P2
Sequential by nature ❌
```

---

## Mathematical Properties

### Verified Properties ✅

1. **Symmetry**: 
   ```
   t1 ⊥ t2  ⟺  t2 ⊥ t1
   ```
   Independence is bidirectional

2. **Non-Reflexive**: 
   ```
   t ⊥ t = False
   ```
   Transition conflicts with itself

3. **Not Transitive** ⚠️:
   ```
   t1 ⊥ t2 ∧ t2 ⊥ t3  ⇏  t1 ⊥ t3
   
   Example:
     T1: {P1, P2}
     T2: {P3, P4}  (T1 ⊥ T2)
     T3: {P1, P5}  (T2 ⊥ T3, but NOT T1 ⊥ T3)
   ```
   This is why we need conflict graphs!

---

## Performance

### Time Complexity
- **Pairwise check**: O(p) where p = places per transition
- **Conflict graph**: O(n² × p) where n = transitions
- **Grouping**: O(n² × p) (greedy algorithm)

### Space Complexity
- **Place sets**: O(n × p)
- **Conflict graph**: O(n²) worst case
- **Groups**: O(n)

### Optimization Opportunities
1. Cache place sets (recompute only on structural change)
2. Cache conflict graph (reuse across steps)
3. Better grouping algorithm (graph coloring)
4. Parallel conflict graph construction

---

## Test Results

### Phase 1 Tests (8/8 Passed)

```
✅ TEST 1: _get_all_places_for_transition()
   Correctly extracts input and output places

✅ TEST 2: Independent transitions
   T1: {P1, P2}, T2: {P3, P4} → Independent: True

✅ TEST 3: Conflicting input place
   T1: {P1, P2}, T2: {P1, P3} → Independent: False

✅ TEST 4: Conflicting output place
   T1: {P1, P2}, T2: {P3, P2} → Independent: False

✅ TEST 5: Conflict sets
   Correctly builds bidirectional conflict graph

✅ TEST 6: Independent groups
   Correctly groups mutually independent transitions

✅ TEST 7: Symmetry
   t1⊥t2 ⟺ t2⊥t1

✅ TEST 8: Reflexivity
   t⊥t = False (expected)
```

---

## Related Documentation

### In This Repository
- **Complete Analysis**: `../LOCALITY_PARALLEL_PROCESSING_ANALYSIS.md`
- **Concerns Clarification**: `../LOCALITY_CONCERNS_CLARIFICATION.md`
- **Final Summary**: `../LOCALITY_FINAL_SUMMARY_REVISED.md`

### External
- **Test Suites**:
  - Phase 1: `tests/test_locality_independence.py`
  - Phase 2: `tests/test_maximal_concurrent_sets.py`
- **Implementation**: `src/shypn/engine/simulation/controller.py`

---

## Future Work

### Phase 3: Maximal Step Execution (TODO)
Execute all transitions in a maximal set atomically:
```python
maximal_sets = controller._find_maximal_concurrent_sets(enabled)
selected_set = controller._select_maximal_set(maximal_sets)
controller._execute_maximal_step(selected_set)
# All fire together or none fire
```

**Estimated time**: 6 hours

### Phase 4: Settings Integration (TODO)
User choice between execution modes:
```python
execution_mode = "maximal_step"  # or "interleaving"
controller.set_execution_mode(execution_mode)
```

**Estimated time**: 6 hours

---

## Contact and Questions

For questions about independence detection:
1. Read `IMPLEMENTATION_GUIDE.md` for quick answers
2. Read `PHASE1_INDEPENDENCE_DETECTION_COMPLETE.md` for Phase 1 details
3. **For Phase 2**: See `../concurrency/README.md` for maximal concurrent sets
4. Check test suites for examples:
   - `tests/test_locality_independence.py` (Phase 1)
   - `tests/test_maximal_concurrent_sets.py` (Phase 2)

---

**Last Updated**: October 11, 2025  
**Phase 1 Status**: ✅ Complete and Tested (8/8 tests passed)  
**Phase 2 Status**: ✅ Complete and Tested (7/7 tests passed) - See `../concurrency/`  
**Next Phase**: Phase 3 - Maximal Step Execution (in `../concurrency/`)
