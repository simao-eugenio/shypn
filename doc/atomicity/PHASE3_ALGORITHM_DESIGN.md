# Phase 3: Maximal Step Execution - Algorithm Design

**Date**: October 11, 2025  
**Status**: Design Phase  
**Dependencies**: Phase 1 (Independence Detection), Phase 2 (Maximal Concurrent Sets)

## Executive Summary

Phase 3 implements **maximal step execution** - the ability to fire multiple independent transitions atomically in a single simulation step. This is the culmination of the parallel execution capability:

- **Phase 1** detects which transitions can fire together (independence)
- **Phase 2** finds maximal sets of concurrent transitions
- **Phase 3** executes those sets atomically with rollback guarantees

### Key Concepts

**Maximal Step Execution**: Fire all transitions in a maximal concurrent set simultaneously, ensuring:
1. **Atomicity**: All transitions fire or none fire
2. **Consistency**: Net state remains valid throughout
3. **Isolation**: No partial states visible
4. **Durability**: Committed changes persist

These are ACID properties applied to Petri net execution.

---

## Problem Definition

### Input
- A **maximal concurrent set** S = {t₁, t₂, ..., tₖ} from Phase 2
- Current **marking** M (token distribution)
- Net structure (places, arcs, weights)

### Goal
Execute all transitions in S atomically such that:

1. **Pre-condition**: All tᵢ ∈ S are enabled in M
2. **Atomic execution**: All transitions fire together
3. **Post-condition**: New marking M' reflects all firings
4. **Rollback**: If any transition fails, revert to M

### Formal Definition

**Maximal Step Firing Rule**:
```
M --S--> M'  ⟺  ∀tᵢ ∈ S: enabled(tᵢ, M) ∧ 
                   M' = M - Σ(inputs(tᵢ)) + Σ(outputs(tᵢ))
```

Where:
- `enabled(t, M)`: Transition t is enabled in marking M
- `inputs(tᵢ)`: Tokens consumed by tᵢ from input places
- `outputs(tᵢ)`: Tokens produced by tᵢ to output places
- Σ: Sum over all transitions in S

**Atomicity Property**:
```
∀tᵢ ∈ S: (fire(tᵢ) succeeds) ∨ (∀tⱼ ∈ S: fire(tⱼ) rolls back)
```

---

## Algorithm Design

### Overview: Three-Phase Commit

Phase 3 uses a **three-phase commit protocol** inspired by distributed transactions:

```
1. VALIDATE phase: Check all transitions can fire
   └─> If any fail → ABORT (no changes)
   
2. PREPARE phase: Create snapshot and lock state
   └─> Snapshot current marking for rollback
   
3. COMMIT phase: Execute all transitions
   └─> If any fail → ROLLBACK to snapshot
   └─> If all succeed → COMMIT new marking
```

### Algorithm 1: Maximal Step Execution (Main)

```python
def execute_maximal_step(transition_set):
    """
    Execute all transitions in set atomically.
    
    Returns: (success: bool, fired_transitions: List, error: str)
    """
    # PHASE 1: VALIDATE
    if not _validate_all_can_fire(transition_set):
        return (False, [], "Pre-condition failed: Not all transitions enabled")
    
    # PHASE 2: PREPARE (snapshot for rollback)
    snapshot = _snapshot_marking()
    
    try:
        # PHASE 3: COMMIT (execute atomically)
        fired = []
        for transition in transition_set:
            # Remove input tokens
            for place, arc in transition.input_arcs.items():
                tokens_needed = arc.weight
                if place.tokens < tokens_needed:
                    # Should not happen (validated), but safety check
                    raise ExecutionError(f"{transition.id} cannot fire")
                place.tokens -= tokens_needed
            
            # Execute transition behavior (if any)
            if transition.behavior:
                transition.behavior.execute()
            
            # Add output tokens
            for place, arc in transition.output_arcs.items():
                place.tokens += arc.weight
            
            fired.append(transition)
        
        # SUCCESS: All transitions fired
        return (True, fired, "")
        
    except Exception as e:
        # ROLLBACK: Restore snapshot
        _restore_marking(snapshot)
        return (False, [], f"Execution failed: {e}, rolled back")
```

**Complexity**: O(k × (I + O)) where:
- k = |S| (number of transitions in set)
- I = average input arcs per transition
- O = average output arcs per transition

**Typical**: O(k) for most nets (bounded arcs per transition)

---

### Algorithm 2: Selection Strategy

Before execution, we need to **choose which maximal set to fire** when Phase 2 returns multiple options.

```python
def select_maximal_set(maximal_sets, strategy='largest'):
    """
    Select which maximal set to execute.
    
    Args:
        maximal_sets: List of maximal concurrent sets from Phase 2
        strategy: Selection strategy
        
    Strategies:
        - 'largest': Fire most transitions (maximize parallelism)
        - 'priority': Fire highest priority transitions
        - 'random': Random selection (for exploration)
        - 'first': First set found (deterministic)
        - 'user': User chooses (interactive mode)
    
    Returns: Selected maximal set
    """
    if not maximal_sets:
        return []
    
    if strategy == 'largest':
        # Maximize parallelism
        return max(maximal_sets, key=len)
    
    elif strategy == 'priority':
        # Maximize sum of priorities
        def total_priority(tset):
            return sum(t.priority for t in tset)
        return max(maximal_sets, key=total_priority)
    
    elif strategy == 'random':
        # Random for exploration
        import random
        return random.choice(maximal_sets)
    
    elif strategy == 'first':
        # Deterministic (natural order from Phase 2)
        return maximal_sets[0]
    
    elif strategy == 'user':
        # Interactive selection
        return _prompt_user_selection(maximal_sets)
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
```

**Complexity**: O(k × m) where:
- k = average set size
- m = number of maximal sets (typically ≤ 5)

**Typical**: O(1) for constant m

---

### Algorithm 3: Validation (All Can Fire)

```python
def _validate_all_can_fire(transition_set):
    """
    Check if all transitions in set are enabled.
    
    Returns: True if all can fire, False otherwise
    """
    for transition in transition_set:
        # Check each input place has enough tokens
        for place, arc in transition.input_arcs.items():
            tokens_needed = arc.weight
            if place.tokens < tokens_needed:
                return False  # Not enough tokens
        
        # Check guard condition (if any)
        if transition.guard:
            if not transition.guard.evaluate():
                return False  # Guard prevents firing
    
    return True  # All transitions can fire
```

**Complexity**: O(k × I) where:
- k = number of transitions
- I = average input arcs

**Purpose**: Pre-flight check before snapshot (avoid rollback overhead)

---

### Algorithm 4: Snapshot and Rollback

```python
def _snapshot_marking():
    """
    Create snapshot of current marking for rollback.
    
    Returns: Dictionary mapping place_id -> token_count
    """
    return {place.id: place.tokens for place in self.net.places}

def _restore_marking(snapshot):
    """
    Restore marking from snapshot (rollback).
    
    Args:
        snapshot: Dictionary from _snapshot_marking()
    """
    for place in self.net.places:
        if place.id in snapshot:
            place.tokens = snapshot[place.id]
```

**Complexity**: O(P) where P = number of places

**Space**: O(P) for snapshot

**Trade-off**: Slight overhead for safety guarantee

---

## Design Decisions

### Decision 1: Why Three-Phase Commit?

**Options Considered**:

1. **Direct Execution** (no validation, no rollback)
   - ✅ Simple, fast
   - ❌ Unsafe: Partial firings possible
   - ❌ Inconsistent states

2. **Two-Phase (Validate + Execute)**
   - ✅ Catches most errors
   - ❌ Still vulnerable to runtime failures
   - ❌ No rollback for behaviors

3. **Three-Phase (Validate + Snapshot + Execute)** ✓ CHOSEN
   - ✅ Safe: Rollback guarantee
   - ✅ Consistent: ACID properties
   - ✅ Handles all failure modes
   - ⚖️ Small overhead (O(P) for snapshot)

**Rationale**: Safety over speed. The O(P) overhead is negligible compared to execution time, and correctness is critical for simulation.

---

### Decision 2: Why Multiple Selection Strategies?

**Use Cases**:

| Strategy | Use Case |
|----------|----------|
| **largest** | Maximize parallelism (performance) |
| **priority** | Respect transition priorities (user control) |
| **random** | Explore state space (debugging/testing) |
| **first** | Deterministic behavior (reproducibility) |
| **user** | Interactive simulation (step-through) |

**Default**: `largest` - Most users want maximum parallelism

**Configuration**: Strategy can be set via settings (Phase 4)

---

### Decision 3: Rollback Granularity

**Question**: What to rollback on failure?

**Options**:
1. Rollback entire simulation run → Too coarse
2. Rollback current step → ✓ CHOSEN
3. Rollback individual transition → Not atomic

**Chosen**: Rollback current step (entire maximal set)

**Rationale**: Maintains step atomicity while limiting blast radius

---

### Decision 4: Behavior Execution Order

**Question**: When multiple transitions have behaviors, what order to execute them?

**Options**:
1. Parallel execution (threads) → Complex, race conditions
2. Sequential in arbitrary order → Non-deterministic
3. Sequential in priority order → ✓ CHOSEN
4. Sequential in ID order → Deterministic but ignores priorities

**Chosen**: Sequential in priority order (with ID as tie-breaker)

**Rationale**:
- Preserves user-specified priorities
- Deterministic (same input → same output)
- Avoids concurrency issues
- Behaviors typically don't interact

**Note**: True parallel behavior execution deferred to future work

---

## Failure Modes and Handling

### Failure Mode 1: Validation Fails

**Cause**: Transition not enabled (insufficient tokens or guard fails)

**Detection**: `_validate_all_can_fire()` returns False

**Handling**: 
- Return immediately (no snapshot, no execution)
- Status: `(False, [], "Pre-condition failed")`
- Cost: O(k × I) validation only

**Recovery**: Caller should not attempt execution

---

### Failure Mode 2: Token Consumption Fails

**Cause**: Race condition or logic error (should not happen if validated)

**Detection**: `place.tokens < tokens_needed` during execution

**Handling**:
- Raise `ExecutionError`
- Rollback to snapshot
- Status: `(False, [], "Token error: ...")`

**Recovery**: Full rollback, net state unchanged

---

### Failure Mode 3: Behavior Execution Fails

**Cause**: Exception in user-defined behavior code

**Detection**: `transition.behavior.execute()` raises exception

**Handling**:
- Catch exception
- Rollback to snapshot
- Status: `(False, [], "Behavior failed: ...")`

**Recovery**: Full rollback, behavior side effects may persist

**Warning**: Behaviors with side effects (file I/O, network) cannot be rolled back. Document this limitation.

---

### Failure Mode 4: Output Token Addition Fails

**Cause**: Overflow (place.tokens > MAX_INT) or capacity constraints

**Detection**: Check before addition or catch exception

**Handling**:
- Rollback to snapshot
- Status: `(False, [], "Output overflow: ...")`

**Recovery**: Full rollback, net state unchanged

---

## Examples

### Example 1: Fork Network (Success Case)

**Network**:
```
P1(2) ---> T1 ---> P2(0)
      \        /
       +---> T3 ---> P4(0)
      /        \
P3(1) ---> T2 ---> P5(0)
```

**Maximal Sets** (from Phase 2):
- S₁ = {T1, T3}
- S₂ = {T2, T3}

**Execution** (select S₁ = {T1, T3}, strategy='largest'):

```python
# Phase 1: Validate
validate({T1, T3}) 
  → T1: P1.tokens(2) >= 1 ✓
  → T3: P1.tokens(2) >= 1 ✓
  → Result: True

# Phase 2: Snapshot
snapshot = {P1: 2, P2: 0, P3: 1, P4: 0, P5: 0}

# Phase 3: Execute
# Fire T1: P1(2→1), P2(0→1)
# Fire T3: P1(1→0), P4(0→1)

# Result: Success
M' = {P1: 0, P2: 1, P3: 1, P4: 1, P5: 0}
Status: (True, [T1, T3], "")
```

**Parallelism**: 2 transitions in 1 step (2× speedup)

---

### Example 2: Chain Network (Rollback Case)

**Network**:
```
P1(1) ---> T1 ---> P2(0) ---> T2 ---> P3(0)
                     |
                   Guard: P2.tokens > 1
```

**Maximal Set**: S = {T1, T3} (T1 and T3 independent)

**Execution** (assume T3 has failing behavior):

```python
# Phase 1: Validate
validate({T1, T3})
  → T1: P1.tokens(1) >= 1 ✓
  → T3: enabled ✓
  → Result: True

# Phase 2: Snapshot
snapshot = {P1: 1, P2: 0, P3: 0, ...}

# Phase 3: Execute
# Fire T1: P1(1→0), P2(0→1) ✓
# Fire T3: behavior.execute() → EXCEPTION ✗

# Rollback
restore_marking(snapshot)
→ {P1: 1, P2: 0, P3: 0, ...}  # Reverted

# Result: Failure
Status: (False, [], "Behavior failed: ValueError")
```

**Guarantee**: No partial firing, net consistent

---

### Example 3: Priority-Based Selection

**Network**:
```
     T1(priority=10)
    /               \
P1(3)               P2(0)
    \               /
     T2(priority=5) 
    /               \
P3(2)               P4(0)
    \               /
     T3(priority=1)
```

**Maximal Sets**:
- S₁ = {T1} (size=1, priority=10)
- S₂ = {T2} (size=1, priority=5)
- S₃ = {T3} (size=1, priority=1)

**Selection**:
```python
# Strategy: 'largest'
select_maximal_set([S₁, S₂, S₃], 'largest')
→ Any set (all size 1) → S₁ (first)

# Strategy: 'priority'
select_maximal_set([S₁, S₂, S₃], 'priority')
→ S₁ (priority=10 > 5 > 1)
```

**Use Case**: User wants T1 to fire first (highest priority)

---

## Performance Analysis

### Time Complexity

| Operation | Complexity | Typical |
|-----------|------------|---------|
| **validate_all_can_fire** | O(k × I) | O(k) |
| **snapshot_marking** | O(P) | O(P) |
| **execute_transitions** | O(k × (I + O)) | O(k) |
| **restore_marking** | O(P) | O(P) |
| **select_maximal_set** | O(k × m) | O(1) |
| **TOTAL (success)** | O(k + P) | O(k + P) |
| **TOTAL (failure)** | O(k + 2P) | O(k + P) |

Where:
- k = transitions in maximal set (typically 2-10)
- P = places in net (typically 10-100)
- I, O = arcs per transition (typically 2-5)
- m = maximal sets (typically ≤ 5)

**Typical**: O(k + P) ≈ O(n) where n = max(k, P)

---

### Space Complexity

| Structure | Space | Persistent |
|-----------|-------|------------|
| **Snapshot** | O(P) | No (temporary) |
| **Transition set** | O(k) | No (input) |
| **Fired list** | O(k) | No (output) |
| **TOTAL** | O(P + k) | O(P) peak |

**Memory**: Dominated by snapshot (O(P) integers)

**Typical**: <1KB for P=100 places (100×4 bytes = 400 bytes)

---

### Comparison: Sequential vs Maximal Step

**Example**: Fork network, 5 concurrent transitions

| Metric | Sequential | Maximal Step | Speedup |
|--------|-----------|--------------|---------|
| **Steps** | 5 | 1 | 5× |
| **Validation** | 5× | 1× | 5× |
| **Snapshot** | 0 | 1× | - |
| **Token updates** | 5× | 5× | 1× |
| **Wall time** | 5t | t + ε | ~5× |

Where:
- t = time per transition fire
- ε = snapshot overhead (negligible)

**Speedup**: Approaches k× for k concurrent transitions

**Best case**: Fully parallel net (all independent)
**Worst case**: Sequential net (no parallelism) → No speedup, slight overhead

---

## Integration with Phases 1-2

### Data Flow

```
Phase 1: Independence Detection
    ↓
    enabled_transitions = find_enabled()
    conflict_graph = _build_conflict_graph(enabled_transitions)
    ↓
Phase 2: Maximal Concurrent Sets
    ↓
    maximal_sets = _find_maximal_concurrent_sets(enabled_transitions)
    ↓
Phase 3: Maximal Step Execution
    ↓
    selected_set = _select_maximal_set(maximal_sets, strategy)
    (success, fired, error) = _execute_maximal_step(selected_set)
    ↓
    If success: Update simulation state
    If failure: Log error, try alternative set or fall back to sequential
```

### API Example

```python
# User code: Run simulation with maximal steps
def run_simulation_with_maximal_steps(controller, max_steps=100):
    for step in range(max_steps):
        # Phase 1: Find enabled and build conflict graph
        enabled = controller._find_enabled_transitions()
        if not enabled:
            break  # Deadlock
        
        # Phase 2: Find maximal concurrent sets
        maximal_sets = controller._find_maximal_concurrent_sets(enabled)
        
        if maximal_sets:
            # Phase 3: Select and execute maximal step
            selected = controller._select_maximal_set(maximal_sets, 'largest')
            success, fired, error = controller._execute_maximal_step(selected)
            
            if success:
                print(f"Step {step}: Fired {len(fired)} transitions: {[t.id for t in fired]}")
            else:
                print(f"Step {step}: Failed - {error}, falling back to sequential")
                # Fall back: Fire one transition
                controller._fire_transition(enabled[0])
        else:
            # No maximal sets (all conflict) → Fire one transition
            controller._fire_transition(enabled[0])
```

---

## Edge Cases

### Edge Case 1: Empty Maximal Set

**Scenario**: Phase 2 returns empty list (no enabled transitions)

**Handling**:
```python
if not maximal_sets:
    return (False, [], "No enabled transitions")
```

**Status**: Simulation terminates (deadlock or final state)

---

### Edge Case 2: Single Transition Set

**Scenario**: Maximal set contains only one transition (no parallelism)

**Handling**: Execute normally (no overhead, just validation + snapshot)

**Performance**: Minimal overhead (~10% slower than sequential)

**Decision**: Accept overhead for uniform code path

---

### Edge Case 3: Behavior with Side Effects

**Scenario**: Transition behavior writes to file, sends network request

**Problem**: Cannot rollback external side effects

**Handling**:
1. Execute behaviors (may cause side effects)
2. If later transition fails, rollback tokens but NOT side effects
3. Log warning: "Partial rollback: External side effects persist"

**Documentation**: Warn users that behaviors with side effects are risky in maximal steps

**Mitigation**: Encourage idempotent behaviors (can safely retry)

---

### Edge Case 4: Concurrent Modification

**Scenario**: Behavior modifies net structure (adds/removes places/transitions)

**Problem**: Invalidates snapshot and execution state

**Handling**:
1. Detect modification (version counter or dirty flag)
2. Abort execution immediately
3. Status: `(False, [], "Net modified during execution")`

**Prevention**: Lock net structure during execution (future enhancement)

---

### Edge Case 5: Infinite Loop in Behavior

**Scenario**: Behavior enters infinite loop (while True: ...)

**Problem**: Execution hangs, cannot rollback

**Handling**:
1. Set timeout for behavior execution (default: 1 second)
2. If timeout expires, raise `TimeoutError`
3. Rollback and report failure

**Implementation**: Use `signal.alarm()` (Unix) or `threading.Timer()` (cross-platform)

---

## Testing Strategy

### Unit Tests

1. **test_validate_all_can_fire()**
   - All enabled → True
   - One disabled → False
   - Guard failure → False

2. **test_snapshot_restore()**
   - Snapshot creates copy
   - Restore reverts changes
   - Multiple snapshots (nested)

3. **test_select_maximal_set()**
   - Strategy: largest → Biggest set
   - Strategy: priority → Highest priority
   - Strategy: random → Valid set
   - Strategy: first → First in list

4. **test_execute_maximal_step_success()**
   - All transitions fire
   - Tokens updated correctly
   - Returns success status

5. **test_execute_maximal_step_rollback()**
   - Force failure (remove token during execution)
   - Verify rollback to snapshot
   - Returns failure status

---

### Integration Tests

1. **test_fork_network_parallel()**
   - Fork with 2 independent branches
   - Execute both branches in 1 step
   - Verify 2× speedup

2. **test_chain_network_sequential()**
   - Chain of dependent transitions
   - Only 1 transition per step
   - Verify no speedup (no parallelism)

3. **test_behavior_failure_rollback()**
   - Transition with failing behavior
   - Verify rollback
   - Verify net consistent

4. **test_guard_failure_prevention()**
   - Maximal set with guarded transition
   - Guard fails during execution
   - Verify rollback and error

---

### Performance Tests

1. **test_large_maximal_set()**
   - 100 independent transitions
   - Execute all in 1 step
   - Measure time vs sequential (expect ~100× speedup)

2. **test_snapshot_overhead()**
   - Large net (1000 places)
   - Measure snapshot time
   - Should be <10ms

3. **test_rollback_overhead()**
   - Force rollback after partial execution
   - Measure restore time
   - Should be <10ms

---

## Limitations and Future Work

### Current Limitations

1. **Behavior Side Effects**: Cannot rollback external changes (file I/O, network)
2. **Sequential Behaviors**: Behaviors execute sequentially, not truly parallel
3. **Net Modification**: Cannot handle structural changes during execution
4. **No Timeouts**: Infinite loop in behavior hangs execution
5. **No Nested Steps**: Cannot fire maximal steps within behaviors

### Future Enhancements (Phase 4+)

1. **Parallel Behavior Execution**: True parallelism with thread pool
2. **Compensating Transactions**: Rollback side effects with undo actions
3. **Partial Execution**: Continue after some failures (relax atomicity)
4. **Optimistic Locking**: Avoid snapshot for common case (no rollback needed)
5. **Distributed Execution**: Fire transitions across multiple machines

---

## Implementation Roadmap

### Step 1: Core Methods (2 hours)
- `_validate_all_can_fire()`
- `_snapshot_marking()`
- `_restore_marking()`
- `_execute_maximal_step()`

### Step 2: Selection Strategies (1 hour)
- `_select_maximal_set()` with 5 strategies

### Step 3: Error Handling (1 hour)
- Exception types
- Rollback paths
- Status reporting

### Step 4: Testing (2 hours)
- Unit tests (5 tests)
- Integration tests (4 tests)
- Performance tests (3 tests)

### Step 5: Documentation (30 min)
- Completion document
- Update README files
- API examples

**Total**: ~6.5 hours

---

## Summary

Phase 3 implements **atomic maximal step execution** with:

1. **Three-phase commit** (Validate → Snapshot → Execute)
2. **Rollback guarantee** (all fire or none fire)
3. **Multiple selection strategies** (largest, priority, random, first, user)
4. **Comprehensive error handling** (5 failure modes)
5. **ACID properties** (atomic, consistent, isolated, durable)

**Key Formulas**:

**Maximal Step Firing**:
```
M --S--> M'  ⟺  ∀tᵢ ∈ S: enabled(tᵢ, M) ∧ M' = M - Σ(inputs(tᵢ)) + Σ(outputs(tᵢ))
```

**Atomicity**:
```
∀tᵢ ∈ S: fire(tᵢ) succeeds  ∨  (∀tⱼ ∈ S: rollback(tⱼ))
```

**Complexity**: O(k + P) typical, where k = transitions, P = places

**Speedup**: Up to k× for k concurrent transitions

**Status**: Ready for implementation ✓

