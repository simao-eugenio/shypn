# Concurrency and Maximal Concurrent Sets Documentation

**Phase 2: Complete ✅**  
**Date**: October 11, 2025

---

## Overview

This directory contains documentation for **Phase 2: Maximal Concurrent Sets** — finding which transitions can fire together in parallel.

**Phase 2** focuses on **concurrent set computation**: Given independent transitions (from Phase 1), find the maximal sets that can fire together.

For **Phase 3 (Atomic Execution)**, see: `../atomicity/` — documentation on firing these sets atomically with ACID guarantees.

---

## Core Concepts

### Maximal Concurrent Set (Phase 2)

```
A MAXIMAL CONCURRENT SET is a set of independent transitions that
CANNOT BE EXTENDED without introducing conflicts.

Formally: S is maximal ⟺ S is concurrent ∧ ∄t ∈ (E \ S): S ∪ {t} is concurrent

Where:
  - S is concurrent: All pairs in S are independent (don't share places)
  - Cannot extend: Adding any transition not in S creates a conflict
```

**For atomic execution of these sets**, see: `../atomicity/` (Phase 3 documentation)

---

## Documents

### 1. PHASE2_ALGORITHM_DESIGN.md (~70 pages)
**Detailed algorithm design and analysis**

- **Contents**:
  - Problem definition and mathematical formulation
  - Algorithm options comparison (Greedy, Bron-Kerbosch, Hybrid)
  - Recommended hybrid approach specification
  - Complexity analysis (O(n²) vs exponential)
  - Detailed examples with network diagrams
  - Edge cases and testing strategy
  - Integration with Phase 1

- **Who should read**:
  - Algorithm developers
  - Anyone modifying the maximal set algorithm
  - Computer science researchers/educators
  - Performance optimization engineers

- **Key Sections**:
  - §3: Algorithm Options (3 approaches compared)
  - §4: Recommended Hybrid Approach (chosen solution)
  - §6: Examples (Fork, Chain, Clique networks)
  - §8: Design Decisions (Why hybrid? Why max_sets=5?)

### 2. PHASE2_MAXIMAL_CONCURRENT_SETS_COMPLETE.md (~60 pages)
**Complete implementation documentation**

- **Contents**:
  - Executive summary
  - Implementation details with code
  - Test suite results (7/7 tests passed)
  - Performance analysis
  - Usage examples
  - Integration with Phase 1
  - API reference

- **Who should read**:
  - All developers using concurrent sets
  - Anyone implementing Phase 3 (atomic execution, see `../atomicity/`)
  - Performance optimization engineers

- **Key Sections**:
  - §2: Implementation Details
  - §3: Test Suite (7 tests)
  - §4: Performance Analysis
  - §5: Usage Examples
  - §7: Integration with Phase 1

---

## Phase 3: Atomic Execution

**Phase 3 documentation has moved to `../atomicity/`**

For atomic maximal step execution with ACID guarantees, see:
- `../atomicity/README.md` - Overview and quick reference
- `../atomicity/PHASE3_ALGORITHM_DESIGN.md` - Three-phase commit protocol
- `../atomicity/PHASE3_MAXIMAL_STEP_EXECUTION_COMPLETE.md` - Implementation details

---

## Quick Reference

### Phase 2: Find Maximal Concurrent Sets

```python
from shypn.engine.simulation.controller import SimulationController

controller = SimulationController(model)
enabled = controller._find_enabled_transitions()

# Find up to 5 maximal concurrent sets
maximal_sets = controller._find_maximal_concurrent_sets(enabled, max_sets=5)

print(f"Found {len(maximal_sets)} maximal concurrent sets:")
for i, mset in enumerate(maximal_sets, 1):
    print(f"  Set {i}: {[t.id for t in mset]}")
```

**For Phase 3 (atomic execution)**, see: `../atomicity/README.md`

---

## Implementation Status

### ✅ Phase 2: Maximal Concurrent Sets (COMPLETE)

### 2. PHASE2_MAXIMAL_CONCURRENT_SETS_COMPLETE.md (~80 pages)
**Comprehensive implementation documentation**

- **Contents**:
  - Executive summary
  - Implementation details (4 methods with full code)
  - Hybrid algorithm strategy explanation
  - Test suite results (7/7 tests passed)
  - Complexity analysis (time and space)
  - Network examples and real-world scenarios
  - Design decisions and trade-offs
  - Performance analysis and benchmarks
  - Integration guide
  - Limitations and future work

- **Who should read**:
  - Developers implementing Phase 3 (execution)
  - Anyone wanting to understand the implementation
  - Performance optimization engineers
  - QA engineers validating the system

- **Key Sections**:
  - §2: Implementation Details (4 methods explained)
  - §3: Test Suite (7 tests, all passing)
  - §4: Algorithm Analysis (hybrid approach breakdown)
  - §7: Examples and Scenarios (manufacturing, communication)
  - §11: Performance Analysis (empirical results)

---

## Quick Reference

### Find Maximal Concurrent Sets

```python
from shypn.engine.simulation.controller import SimulationController

controller = SimulationController(model)
enabled = controller._find_enabled_transitions()

# Find up to 5 maximal concurrent sets
maximal_sets = controller._find_maximal_concurrent_sets(enabled, max_sets=5)

print(f"Found {len(maximal_sets)} maximal concurrent sets:")
for i, mset in enumerate(maximal_sets, 1):
    ids = [t.id for t in mset]
    print(f"  Set {i}: {ids} ({len(ids)} transitions can fire together)")
```

### Example Output

```
Found 3 maximal concurrent sets:
  Set 1: ['T1', 'T3', 'T5'] (3 transitions can fire together)
  Set 2: ['T2', 'T4'] (2 transitions can fire together)
  Set 3: ['T1', 'T4', 'T6'] (3 transitions can fire together)
```

---

## Implementation Status

### ✅ Phase 2: Maximal Concurrent Sets (COMPLETE)

**Implementation**: `src/shypn/engine/simulation/controller.py` (lines ~720-965)

**Methods Implemented**:
1. ✅ `_find_maximal_concurrent_sets(enabled, max_sets=5)`
   - Hybrid algorithm with 4 strategies
   - Returns diverse maximal sets
   - O(n²) complexity

2. ✅ `_greedy_maximal_set(transitions, conflicts, start_index)`
   - Core greedy builder
   - Guaranteed maximal result
   - Order-dependent exploration

3. ✅ `_sort_by_conflict_degree(transitions, conflicts, ascending)`
   - Sort by conflict count
   - Enables different strategies
   - O(n log n) complexity

4. ✅ `_is_concurrent_set_maximal(set, all_enabled, conflicts)`
   - Maximality validator
   - Used in testing and debugging
   - O(n²) complexity

**Test Results**: 7/7 passed ✅
- Greedy maximal set building ✅
- Conflict degree sorting ✅
- Maximality validation ✅
- Fork network (partial conflicts) ✅
- Chain network (transitive conflicts) ✅
- Clique network (all conflicts) ✅
- Independent network (no conflicts) ✅

**Test Suite**: `tests/test_maximal_concurrent_sets.py` (~700 lines)

---

### ✅ Phase 3: Maximal Step Execution (COMPLETE)

**Implementation**: `src/shypn/engine/simulation/controller.py` (lines ~965-1230)

**Test Results**: 7/7 passed ✅
- Empty set handling ✅
- Single transition ✅
- Fork network (fully parallel) ✅
- Chain network (partially parallel) ✅
- Clique network (no parallelism) ✅
- Max sets limit (capped at 5) ✅
- Integration with Phase 1 ✅

**Test Suite**: `tests/test_maximal_concurrent_sets.py` (~350 lines)

**Performance**: 
- Time: O(n²) typical
- Space: O(n²) for conflict graph
- Finds 1-5 diverse maximal sets efficiently

---

## Algorithm Overview

### Phase 2: Hybrid Approach (4 Strategies)

Phase 2 uses a **hybrid algorithm** that finds multiple diverse maximal sets efficiently:

**Strategy 1: Natural Order**
```python
# Start with original order
greedy([T1, T2, T3, T4], start=0) → [T1, T3]
```

**Strategy 2: Rotated Starts**
```python
# Try different starting points
greedy([T2, T3, T4, T1], start=0) → [T2, T4]
greedy([T3, T4, T1, T2], start=0) → [T3, T1]
# Different orderings → different maximal sets
```

**Strategy 3: High-Conflict First**
```python
# Sort by most conflicts first
sort_by_conflicts(descending=True)
# Handle constrained transitions first
```

**Strategy 4: Low-Conflict First**
```python
# Sort by least conflicts first
sort_by_conflicts(ascending=True)
# Maximize set size
```

**Result**: Finds 1-5 diverse maximal sets in O(n²) time (instead of exponential for complete enumeration).

**For Phase 3 (atomic execution with three-phase commit)**, see: `../atomicity/README.md`

---

## Network Pattern Examples

### Pattern 1: Fork Structure
```
T1: {P1, P2}
T2: {P1, P3}  (conflicts with T1 on P1)
T3: {P4, P5}  (independent of T1, T2)

Maximal Concurrent Sets:
  {T1, T3} ✅ Cannot add T2 (conflicts with T1)
  {T2, T3} ✅ Cannot add T1 (conflicts with T2)
```

### Pattern 2: Chain Structure
```
T1: {P1, P2}
T2: {P2, P3}  (conflicts with T1 on P2)
T3: {P3, P4}  (conflicts with T2 on P3)

Note: T1 and T3 are independent (don't share places)!

Maximal Concurrent Sets:
  {T1, T3} ✅ Can fire together (no shared places)
  {T2}     ✅ Alone (conflicts with both T1 and T3)
```

### Pattern 3: Clique (All Conflict)
```
All transitions share central place P0

T1: {P0, P1}
T2: {P0, P2}
T3: {P0, P3}

Maximal Concurrent Sets:
  {T1} ✅ Each singleton is maximal
  {T2} ✅
  {T3} ✅
```

### Pattern 4: Independent (No Conflicts)
```
T1: {P1, P2}
T2: {P3, P4}
T3: {P5, P6}

No shared places!

Maximal Concurrent Sets:
  {T1, T2, T3} ✅ All can fire together
```

---

## Performance

### Time Complexity

**Phase 2: Maximal Concurrent Sets**

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Single greedy pass | O(n²) | n = transitions |
| Conflict degree sort | O(n log n) | Standard sort |
| Hybrid (k strategies) | O(k × n²) | k = max_sets (default 5) |
| **Overall** | **O(n²)** | k is small constant |

**For Phase 3 complexity**, see: `../atomicity/README.md`

### Space Complexity

**Phase 2: Maximal Concurrent Sets**

| Structure | Space | Notes |
|-----------|-------|-------|
| Conflict sets | O(n²) | Worst case (clique) |
| Maximal sets | O(k × n) | k sets of size ≤ n |
| Working storage | O(n) | Temporary arrays |
| **Total** | **O(n²)** | Dominated by conflicts |

**For Phase 3 space complexity**, see: `../atomicity/README.md`

### Comparison with Alternatives

| Algorithm | Time | Completeness | Practical Use |
|-----------|------|--------------|---------------|
| **Hybrid (Phase 2)** | O(n²) | k sets | ✅ **Implemented** |
| Single Greedy | O(n²) | 1 set | Too limited |
| Bron-Kerbosch | O(3^(n/3)) | All sets | Too slow |

---

## Test Suites

### Run Phase 2 Tests

```bash
cd /home/simao/projetos/shypn
python3 tests/test_maximal_concurrent_sets.py
```

**Expected Output**:
```
======================================================================
MAXIMAL CONCURRENT SET ALGORITHM - PHASE 2 TESTS
======================================================================

✅ TEST 1: _greedy_maximal_set()
✅ TEST 2: _sort_by_conflict_degree()
✅ TEST 3: _is_concurrent_set_maximal()
✅ TEST 4: Fork network
✅ TEST 5: Chain network
✅ TEST 6: Clique network
✅ TEST 7: Independent network

======================================================================
SUMMARY
======================================================================
Total tests: 7
✅ Passed: 7
❌ Failed: 0

🎉 ALL TESTS PASSED!
```

**For Phase 3 tests**, see: `../atomicity/README.md` or run `tests/test_maximal_step_execution.py`

---

## Integration with Phase 1 and Phase 3

Phases 1-3 work together to enable parallel execution:

```python
# Phase 1: Independence Detection (from ../independency/)
conflict_sets = self._build_conflict_graph(enabled)  # O(n²)
independent = self._are_independent(t1, t2)          # O(1)

# Phase 2: Maximal Concurrent Sets (this directory)
maximal_sets = self._find_maximal_concurrent_sets(enabled)  # O(n²)

# Phase 3: Maximal Step Execution (from ../atomicity/)
# See ../atomicity/README.md for atomic execution details

# Each maximal set uses Phase 1's conflict graph internally
for mset in maximal_sets:
    # All pairs in mset are independent (Phase 1 guarantee)
    # Cannot add more without conflict (Phase 2 guarantee)
```

**Dependency Chain**:
```
Phase 1: Independence Detection (../independency/)
    ↓ (conflict graph)
    Provides: which pairs conflict/are independent
    ↓
Phase 2: Maximal Concurrent Sets (this directory)
    ↓ (maximal sets)
    Provides: sets of transitions that can fire together
    ↓
Phase 3: Maximal Step Execution (../atomicity/)
    ↓ (atomic firing)
    Provides: parallel execution with ACID guarantees
    ↓
Phase 4: Settings Integration (TODO)
    Provides: user configuration and UI
```

---

## Real-World Applications

### Manufacturing Process

```python
# Network:
T1: Assemble_Widget_A  {Machine1, PartBin1}
T2: Assemble_Widget_B  {Machine1, PartBin2}  # Conflicts with T1 (Machine1)
T3: Package_Products   {PackStation, Boxes}  # Independent
T4: Quality_Check      {TestBench, Reports}  # Independent

# Maximal Concurrent Sets:
Set 1: [T1, T3, T4]  # Assemble A while packaging and testing
Set 2: [T2, T3, T4]  # Assemble B while packaging and testing

# Benefit: Can do 3 things at once instead of sequentially!
```

### Communication Protocol

```python
# Network:
T1: Send_Packet_ChA    {ChannelA, Buffer}
T2: Receive_Packet_ChA {ChannelA, Queue}    # Conflicts with T1 (ChannelA)
T3: Send_Packet_ChB    {ChannelB, Buffer}   # Conflicts with T1 (Buffer)
T4: Process_Data       {Queue, CPU}         # Independent

# Maximal Concurrent Sets:
Set 1: [T1, T4]  # Send on A while processing
Set 2: [T2, T4]  # Receive on A while processing
Set 3: [T3, T4]  # Send on B while processing

# Cannot have T1+T2 (share ChannelA) or T1+T3 (share Buffer)
```

---

## Future Work

### Phase 3: Maximal Step Execution (TODO)

**Goal**: Execute all transitions in a maximal set atomically

**Key Challenges**:
1. **Atomic firing**: All succeed or all fail
2. **Token management**: Update all places consistently
3. **Failure handling**: Rollback on conflict
4. **Selection strategy**: Which maximal set to fire?

**Estimated Complexity**: 6 hours

**Preview**:
```python
# Phase 3 will enable:
maximal_sets = controller._find_maximal_concurrent_sets(enabled)
selected_set = controller._select_maximal_set(maximal_sets)  # Choose best
success = controller._execute_maximal_step(selected_set)     # Fire atomically

if success:
    print(f"Fired {len(selected_set)} transitions in parallel!")
else:
    print("Rollback - conflict detected")
```

### Phase 4: Settings Integration (TODO)

**Goal**: User configuration for execution mode

**Features**:
- Choose between "Interleaving" (current) vs "Maximal Step" (new)
- Configure max_sets parameter
- Monitor parallelism statistics
- Performance profiling

**Estimated Complexity**: 6 hours

---

## Related Documentation

### In This Repository

**Independence (Phase 1)**:
- `../independency/PHASE1_INDEPENDENCE_DETECTION_COMPLETE.md`
- `../independency/IMPLEMENTATION_GUIDE.md`
- `../independency/README.md`

**Background**:
- `../LOCALITY_PARALLEL_PROCESSING_ANALYSIS.md`
- `../LOCALITY_CONCERNS_CLARIFICATION.md`

### Test Suites

**Phase 1**: `tests/test_locality_independence.py` (8/8 tests passed)
**Phase 2**: `tests/test_maximal_concurrent_sets.py` (7/7 tests passed)

### Implementation

**Core Code**: `src/shypn/engine/simulation/controller.py`
- Lines ~540-720: Phase 1 methods
- Lines ~720-965: Phase 2 methods

---

## See Also

**Related Documentation**:
- `../independency/README.md` - Phase 1: Independence detection
- `../atomicity/README.md` - Phase 3: Atomic execution with ACID guarantees
- `../PARALLEL_EXECUTION_OVERVIEW.md` - Complete pipeline overview
- `tests/test_maximal_concurrent_sets.py` - Phase 2 test suite

**Phase 3 Documentation** (moved to `../atomicity/`):
- `../atomicity/PHASE3_ALGORITHM_DESIGN.md` - Three-phase commit protocol
- `../atomicity/PHASE3_MAXIMAL_STEP_EXECUTION_COMPLETE.md` - Implementation details
- `tests/test_maximal_step_execution.py` - Phase 3 test suite

---

## Contact and Questions

For questions about maximal concurrent sets:

1. **Quick answers**: Read this README
2. **Algorithm details**: Read `PHASE2_ALGORITHM_DESIGN.md`
3. **Implementation details**: Read `PHASE2_MAXIMAL_CONCURRENT_SETS_COMPLETE.md`
4. **Code examples**: Check `tests/test_maximal_concurrent_sets.py`
5. **Phase 1 dependency**: Read `../independency/README.md`
6. **Phase 3 execution**: Read `../atomicity/README.md`

---

**Last Updated**: October 11, 2025  
**Status**: ✅ Phase 2 Complete and Tested (7/7 tests passed)  
**Next**: See `../atomicity/` for Phase 3 (atomic execution, complete ✅)

