# Phase 2: Conflict Resolution - Analysis and Design

## Conflict Scenarios in Petri Nets

### What is a Conflict?
A **conflict** occurs when:
1. Multiple transitions are enabled (have sufficient input tokens)
2. They share at least one input place
3. Firing one transition disables others (insufficient tokens remain)

### Example Conflict Scenario
```
    P1 (tokens=1)
   /  \
  /    \
 T1    T2  (both enabled, but only one can fire)
  \    /
   \  /
    P2
```
- P1 has 1 token
- Both T1 and T2 need 1 token from P1
- Only one can fire per step
- **Conflict!** Which one should fire?

### Types of Conflicts

#### 1. Simple Conflict (Choice)
- 2+ transitions share exactly one input place
- Example: routing decision, alternative paths

#### 2. Symmetric Conflict
- Multiple transitions with identical input requirements
- Example: parallel resources, worker selection

#### 3. Asymmetric Conflict
- Transitions have different input requirements but overlap
- Example: T1 needs {P1}, T2 needs {P1, P2}

#### 4. Multi-way Conflict
- 3+ transitions competing for shared resources
- Complex conflict graph

## Conflict Resolution Strategies

### Strategy 1: Random Selection (Stochastic)
**Approach:** Select one enabled transition randomly
**Pros:**
- Simple to implement
- Models non-deterministic systems
- Fair over many iterations
- Good for simulation exploration

**Cons:**
- Non-reproducible (unless seeded)
- No control over priorities
- May not match real system behavior

**Use Case:** General-purpose simulation, exploration

### Strategy 2: Priority-Based Selection
**Approach:** Assign priorities to transitions, select highest priority
**Pros:**
- Deterministic (given priorities)
- Models real systems with precedence
- Reproducible results
- Control over execution order

**Cons:**
- Requires manual priority assignment
- May cause starvation (low priority never fires)
- Less exploratory

**Use Case:** Real-time systems, protocols, scheduled processes

### Strategy 3: Round-Robin (Fair Scheduling)
**Approach:** Cycle through transitions in order, preventing starvation
**Pros:**
- Fair (all transitions eventually fire)
- No starvation
- Deterministic

**Cons:**
- Artificial (doesn't model real systems well)
- More complex state tracking
- May not respect urgency

**Use Case:** Resource allocation, fair scheduling

### Strategy 4: Age-Based (Longest Waiting First)
**Approach:** Track how long each transition has been enabled, fire oldest
**Pros:**
- Fair (prevents starvation)
- Natural (respects causality)
- Good for queue modeling

**Cons:**
- Requires time tracking per transition
- More complex state
- Overhead

**Use Case:** Queueing systems, process scheduling

### Strategy 5: Immediate > Timed > Stochastic (Type-Based Priority)
**Approach:** Fire immediate transitions first, then timed, then stochastic
**Pros:**
- Matches common Petri net semantics
- Natural priority ordering
- Good for hybrid models

**Cons:**
- May cause starvation of lower-priority types
- Less flexible

**Use Case:** Time Petri nets, Stochastic Petri nets

## Recommended Approach for Phase 2

### Default: Random Selection
- Simple, general-purpose
- Matches current implementation (already uses `random.choice`)
- Good starting point

### Extension: Configurable Policy
```python
class ConflictResolutionPolicy(Enum):
    RANDOM = "random"              # Random selection
    PRIORITY = "priority"          # Use transition.priority attribute
    TYPE_BASED = "type_based"      # Immediate > Timed > Stochastic
    ROUND_ROBIN = "round_robin"    # Fair cycling
```

### Implementation Plan

#### Step 1: Detect Conflicts
```python
def _detect_conflicts(self, enabled_transitions):
    """Check if enabled transitions share input places."""
    conflicts = []
    for i, t1 in enumerate(enabled_transitions):
        for t2 in enabled_transitions[i+1:]:
            if self._share_input_places(t1, t2):
                conflicts.append((t1, t2))
    return conflicts
```

#### Step 2: Selection Algorithm
```python
def _select_transition(self, enabled_transitions):
    """Select one transition from enabled set based on policy."""
    if self.conflict_policy == ConflictResolutionPolicy.RANDOM:
        return random.choice(enabled_transitions)
    
    elif self.conflict_policy == ConflictResolutionPolicy.PRIORITY:
        return max(enabled_transitions, key=lambda t: t.priority)
    
    elif self.conflict_policy == ConflictResolutionPolicy.TYPE_BASED:
        # Sort by type priority: immediate > timed > stochastic > continuous
        priority_order = {'immediate': 4, 'timed': 3, 'stochastic': 2, 'continuous': 1}
        return max(enabled_transitions, key=lambda t: priority_order.get(t.transition_type, 0))
    
    elif self.conflict_policy == ConflictResolutionPolicy.ROUND_ROBIN:
        return self._round_robin_select(enabled_transitions)
```

#### Step 3: Update Controller
```python
class SimulationController:
    def __init__(self, model):
        # ... existing code ...
        self.conflict_policy = ConflictResolutionPolicy.RANDOM
        self.round_robin_index = 0
```

#### Step 4: Modify step() Method
```python
def step(self, time_step: float = 0.1) -> bool:
    # Find all enabled transitions
    enabled_transitions = self._find_enabled_transitions()
    
    if not enabled_transitions:
        return False
    
    # Select one transition based on conflict resolution policy
    transition = self._select_transition(enabled_transitions)
    
    # Fire the selected transition
    self._fire_transition(transition)
    
    # Update time and notify
    self.time += time_step
    self._notify_step_listeners()
    
    return True
```

## Locality Principle in Conflict Resolution

### Key Insight
Conflict resolution is the **only global operation** in the simulation:
- Enablement checking is **local** (each transition checks its input places)
- Firing is **local** (each transition affects its input/output places)
- Selection is **global** (choose from all enabled transitions)

### Why Global Selection is Necessary
- Conflicts arise from shared resources (places)
- Cannot resolve locally without coordination
- Selection algorithm needs global view of enabled transitions

### Preserving Locality
- Enablement checking remains local (behavior.can_fire())
- Firing remains local (behavior.fire())
- Only add global selection step between find_enabled and fire

## Testing Strategy

### Test Cases

#### Test 1: Simple Conflict Detection
```
P1(1) -> T1 -> P2
      -> T2 -> P3
```
- Verify both T1 and T2 are enabled
- Verify conflict is detected
- Verify only one fires per step

#### Test 2: Random Selection Distribution
- Run 1000 steps with same initial marking
- Verify statistical distribution (~50/50 for symmetric conflict)

#### Test 3: Priority-Based Selection
- Assign priorities: T1=10, T2=5
- Verify T1 always fires when both enabled

#### Test 4: Type-Based Priority
- T1=immediate, T2=stochastic
- Verify immediate always fires first

#### Test 5: No Conflict (Independent)
```
P1 -> T1 -> P2
P3 -> T2 -> P4
```
- Verify no conflict detected
- Verify behavior unchanged (random selection doesn't matter)

#### Test 6: Multi-way Conflict
```
    P1(1)
   / | \
  T1 T2 T3
```
- Verify all three detected as enabled
- Verify only one fires
- Verify fair distribution (random) or priority order

## Implementation Notes

### Backward Compatibility
- Default policy: RANDOM (matches current behavior)
- No breaking changes to existing code
- Policy configurable via `controller.conflict_policy`

### Performance
- Conflict detection is O(n²) for n enabled transitions
- Typically n is small (< 10)
- Negligible overhead for most nets

### Future Extensions
- Conflict-free subnets (fire multiple non-conflicting transitions per step)
- Maximal step semantics (fire all non-conflicting transitions)
- Custom selection functions (user-defined policies)

## Summary

Phase 2 adds **configurable conflict resolution** to the simulation controller while preserving the locality principle. The default random selection matches current behavior, with extensions for priority-based and type-based selection available for advanced use cases.
