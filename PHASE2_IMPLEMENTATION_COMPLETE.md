# Phase 2: Conflict Resolution - Implementation Complete ✓

## Date: October 4, 2025

## Overview
Successfully implemented configurable conflict resolution policies for handling multiple enabled transitions competing for the same resources.

## Key Implementation Details

### 1. Conflict Resolution Policy Enum
**File:** `src/shypn/engine/simulation/conflict_policy.py`

Created `ConflictResolutionPolicy` enum with 4 strategies:
- **RANDOM** (default): Random selection, non-deterministic, fair over many iterations
- **PRIORITY**: Priority-based selection using `transition.priority` attribute
- **TYPE_BASED**: Type priority (immediate > timed > stochastic > continuous)
- **ROUND_ROBIN**: Fair cycling through enabled transitions

### 2. Controller Updates
**File:** `src/shypn/engine/simulation/controller.py`

**Added:**
- `self.conflict_policy = DEFAULT_POLICY` - Current policy
- `self._round_robin_index = 0` - Counter for round-robin
- `set_conflict_policy(policy)` - Method to change policy
- `_select_transition(enabled_transitions)` - Selection algorithm

**Modified:**
- `step()` - Now uses `_select_transition()` instead of `random.choice()`
- Made GLib import optional (allows testing without GUI)

### 3. Transition Priority Attribute
**File:** `src/shypn/netobjs/transition.py`

Added `self.priority = 0` attribute for priority-based conflict resolution.

## Selection Algorithm

```python
def _select_transition(self, enabled_transitions: List) -> Any:
    """Select one transition based on policy."""
    
    if len(enabled_transitions) == 1:
        return enabled_transitions[0]  # No conflict
    
    if policy == RANDOM:
        return random.choice(enabled_transitions)
    
    elif policy == PRIORITY:
        return max(enabled_transitions, key=lambda t: t.priority)
    
    elif policy == TYPE_BASED:
        return max(enabled_transitions, 
                  key=lambda t: TYPE_PRIORITIES[t.transition_type])
    
    elif policy == ROUND_ROBIN:
        selected = enabled_transitions[self._round_robin_index % len(enabled)]
        self._round_robin_index += 1
        return selected
```

## Test Results

**Test File:** `tests/test_phase2_conflict_resolution.py`

All 7 tests passed:
1. ✓ **Conflict Detection** - Correctly detects when 2+ transitions compete
2. ✓ **Random Selection** - 43/57 distribution over 100 trials (within 30-70% range)
3. ✓ **Priority Selection** - Higher priority wins 100% (20/20 trials)
4. ✓ **Type-Based Selection** - Immediate beats stochastic 100% (20/20 trials)
5. ✓ **Round-Robin Selection** - Perfect alternation: T1→T2→T1→T2...
6. ✓ **No Conflict** - Single enabled transition works with all policies
7. ✓ **Policy Switching** - Can change policies during simulation

## Conflict Scenarios Tested

### Simple Conflict (Choice)
```
    P1 (1 token)
   /  \
  T1  T2  (both need 1 token, only one can fire)
  |    |
  P2  P3
```
- Both transitions enabled
- Conflict detected
- Policy determines which fires

### Type-Based Conflict
```
    P1 (1 token)
   /  \
  T1  T2  (T1=immediate, T2=stochastic)
  |    |
  P2  P3
```
- With TYPE_BASED policy, immediate always fires first
- Matches standard Petri net semantics

## Locality Preservation

### Key Principle
Conflict resolution is the **only global operation**:
- **Local**: Enablement checking (each transition checks its inputs)
- **Local**: Firing (each transition affects its inputs/outputs)
- **Global**: Selection (choose from all enabled transitions)

### Why Global Selection is Necessary
- Conflicts arise from shared resources (places)
- Cannot resolve locally without coordination
- Selection needs global view of all enabled transitions

### Implementation
```python
def step(self):
    # Local: Each transition checks its inputs independently
    enabled = self._find_enabled_transitions()
    
    # Global: Select one from all enabled (conflict resolution)
    transition = self._select_transition(enabled)
    
    # Local: Fire affects only transition's inputs/outputs
    self._fire_transition(transition)
```

## Policy Characteristics

### RANDOM (Default)
- **Pros**: Simple, exploratory, fair over time
- **Cons**: Non-deterministic, non-reproducible
- **Use Case**: General simulation, state space exploration

### PRIORITY
- **Pros**: Deterministic, reproducible, matches real systems
- **Cons**: May cause starvation, requires manual priority assignment
- **Use Case**: Real-time systems, protocols, scheduled processes

### TYPE_BASED
- **Pros**: Natural priority, matches PN semantics
- **Cons**: May starve lower-priority types
- **Use Case**: Hybrid models with multiple transition types

### ROUND_ROBIN
- **Pros**: Fair, no starvation, deterministic
- **Cons**: Artificial, may not model real systems well
- **Use Case**: Resource allocation, fair scheduling

## Code Changes Summary

### New Files (2)
1. `src/shypn/engine/simulation/conflict_policy.py` - Policy enum and constants
2. `tests/test_phase2_conflict_resolution.py` - 7 comprehensive tests

### Modified Files (3)
1. `src/shypn/engine/simulation/controller.py` - Added selection algorithm
2. `src/shypn/netobjs/transition.py` - Added priority attribute
3. `src/shypn/engine/simulation/__init__.py` - Export conflict_policy (if needed)

## Backward Compatibility

- Default policy is RANDOM (same as Phase 1 behavior)
- Existing code works without changes
- Policy configurable via `controller.set_conflict_policy()`
- No breaking changes

## Performance

- Selection is O(n) where n = number of enabled transitions
- Typically n < 10, so negligible overhead
- Conflict detection is implicit (no explicit check needed)
- Round-robin uses simple modulo indexing

## Usage Examples

### Random Selection (Default)
```python
controller = SimulationController(model)
controller.step()  # Random selection
```

### Priority-Based Selection
```python
t1.priority = 10
t2.priority = 5
controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
controller.step()  # T1 fires (higher priority)
```

### Type-Based Selection
```python
t1.transition_type = 'immediate'
t2.transition_type = 'stochastic'
controller.set_conflict_policy(ConflictResolutionPolicy.TYPE_BASED)
controller.step()  # T1 fires (immediate > stochastic)
```

### Round-Robin Selection
```python
controller.set_conflict_policy(ConflictResolutionPolicy.ROUND_ROBIN)
controller.step()  # T1 fires
controller.step()  # T2 fires
controller.step()  # T1 fires (alternates)
```

## Design Insights

### Separation of Concerns
- **Enablement** is local (behavior.can_fire())
- **Selection** is global (policy-based)
- **Firing** is local (behavior.fire())

### Extensibility
Easy to add new policies:
```python
class ConflictResolutionPolicy(Enum):
    AGE_BASED = "age_based"  # Fire longest-waiting transition
    CUSTOM = "custom"         # User-defined function
```

### Configuration Over Convention
- Policies are configurable at runtime
- No hard-coded priorities
- User controls conflict resolution strategy

## Future Extensions

### Maximal Step Semantics
Fire **all** non-conflicting transitions in one step:
```python
def step_maximal(self):
    enabled = self._find_enabled_transitions()
    non_conflicting = self._find_non_conflicting_set(enabled)
    for t in non_conflicting:
        self._fire_transition(t)
```

### Custom Selection Functions
```python
controller.set_custom_selector(lambda transitions: my_logic(transitions))
```

### Conflict-Free Subnets
Detect subnets where no conflicts can occur, fire in parallel:
```python
subnets = self._partition_by_conflicts(enabled)
for subnet in subnets:
    fire_all(subnet)  # Parallel firing
```

## Verification

```bash
cd /home/simao/projetos/shypn
python3 tests/test_phase2_conflict_resolution.py
```

**Result:** All 7 tests pass ✓

## Status: COMPLETE ✓

Phase 2 implementation is production-ready. The simulation controller now supports configurable conflict resolution with 4 built-in policies, preserving locality while adding global selection capability.
