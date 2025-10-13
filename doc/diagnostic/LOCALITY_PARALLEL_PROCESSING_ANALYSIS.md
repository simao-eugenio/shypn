# Locality and Parallel Processing Analysis
**Date**: October 11, 2025  
**Context**: Analysis of locality semantics, parallel processing, and global time coordination  
**Related**: Time Scale Implementation (Phase 1 Complete)

---

## Executive Summary

This document analyzes **locality** in Petri nets—the fundamental concept that transitions operate on **isolated neighborhoods** (input places → transition → output places) and explores implications for:

1. **Locality Isolation**: Are localities independent?
2. **Local Behavior**: Does each locality have its own behavior?
3. **Behavior Instantiation**: Does locality instantiate its own behavior?
4. **Parallel Processing**: Can independent localities fire concurrently?
5. **Global Time Coordination**: How do localities relate to global simulation time?
6. **Firing Semantics**: How do localities relate to the firing mechanism?

**Key Finding**: Current implementation uses **interleaving semantics** (sequential firing) but architecture supports future **maximal step semantics** (parallel firing).

---

## Part 1: User Requirements - The 6 Locality Statements

### Statement 1: "Every locality in the system is isolated from others"

**Interpretation**: 
- Each locality operates on its **own neighborhood** (input/output places)
- Localities that do **NOT share places** are **structurally independent**
- Changes in one locality don't directly affect another (unless they share places)

**Petri Net Formalism**:
```
Locality_i = (•t_i, t_i, t_i•)
    •t_i  = input places of transition t_i
    t_i•  = output places of transition t_i
```

**Independence Condition**:
```
Locality_i ⊥ Locality_j  ⟺  (•t_i ∪ t_i•) ∩ (•t_j ∪ t_j•) = ∅
```
If localities share NO places, they are **isolated/independent**.

**Example**:
```
    P1 --→ T1 --→ P2      (Locality 1)
    P3 --→ T2 --→ P4      (Locality 2)
```
These localities are **completely isolated** (no shared places).

```
    P1 --→ T1 --→ P2      (Locality 1)
           ↑
    P3 --→ T2             (Locality 2)
```
These localities **share P2** → NOT isolated (they can conflict).

---

### Statement 2: "All locality has its own behavior"

**Interpretation**:
- Each transition (center of locality) has a **type** (immediate, timed, stochastic, continuous)
- Behavior is **local** to the transition
- Behavior depends ONLY on:
  - Local marking (tokens in •t)
  - Local timing state (enablement time for t)
  - Local arc weights (Pre/Post matrices for t)

**Current Implementation** (`TransitionBehavior` hierarchy):
```python
class TransitionBehavior:  # Base class
    - can_fire()  # Checks LOCAL enablement
    - fire()      # Executes LOCAL token transfer
    - get_input_arcs()   # LOCAL input neighborhood
    - get_output_arcs()  # LOCAL output neighborhood

class ImmediateBehavior:  # Zero-delay behavior
class TimedBehavior:      # [earliest, latest] window behavior
class StochasticBehavior: # Exponential distribution behavior
class ContinuousBehavior: # Continuous flow behavior
```

**Locality Principle**: ✅ **Each locality encapsulates its own behavior**

---

### Statement 3: "Locality instantiates its own behavior"

**Interpretation**:
- Each transition **creates/owns** its behavior instance
- Behavior object is **bound** to transition (not shared)
- Behavior has **private state** (e.g., enablement_time, scheduled_fire_time)

**Current Implementation** (from `controller.py`):
```python
def _get_behavior(self, transition) -> TransitionBehavior:
    """Get behavior instance for transition."""
    if transition.id not in self._behaviors:
        # INSTANTIATE behavior based on transition type
        self._behaviors[transition.id] = behavior_factory(
            transition, 
            self.model_adapter
        )
    return self._behaviors[transition.id]
```

**Key Design**:
- Each transition has **exactly ONE** behavior instance (cached)
- Behavior instance **persists** across firings (maintains state)
- Behavior is **lazy-initialized** on first access

**Locality Principle**: ✅ **Each locality instantiates and owns its behavior**

---

### Statement 4: "By 2 and 3, this implies parallel processing"

**Interpretation**:
- If localities have **independent behaviors** (Statement 2)
- And each locality **instantiates its own behavior** (Statement 3)
- Then localities **CAN** be evaluated/fired **in parallel** (if isolated per Statement 1)

**Petri Net Theory**:

**Interleaving Semantics** (current):
```
Fire one transition at a time in sequence:
    T1 → T2 → T3 → ...
```

**Maximal Step Semantics** (parallel):
```
Fire all enabled, non-conflicting transitions simultaneously:
    {T1, T2, T3} fired in parallel at time t
```

**True Concurrency** (Petri net advantage over automata):
```
If •T1 ∩ •T2 = ∅ and T1• ∩ T2• = ∅
Then T1 and T2 can fire TRULY concurrently
```

**Current Implementation Analysis**:

`controller.py` `step()` method (simplified):
```python
def step(self, time_step):
    # Phase 1: Exhaust immediate transitions (sequential loop)
    for iteration in range(max_iterations):
        enabled = [t for t in immediates if can_fire(t)]
        if not enabled:
            break
        transition = select_one(enabled)  # ← SELECT ONE
        fire(transition)                  # ← FIRE ONE
    
    # Phase 2: Fire one discrete transition (timed/stochastic)
    enabled_discrete = [t for t in discrete if can_fire(t)]
    if enabled_discrete:
        transition = select_one(enabled_discrete)  # ← SELECT ONE
        fire(transition)                          # ← FIRE ONE
    
    # Phase 3: Integrate all continuous transitions (parallel!)
    for transition in continuous:
        if can_fire(transition):
            integrate(transition, time_step)  # ← ALL FIRE
    
    self.time += time_step
```

**Key Observations**:
1. **Immediate/Discrete**: Sequential (interleaving) - fires ONE per step
2. **Continuous**: Parallel - fires ALL simultaneously
3. **Continuous phase** already implements parallel locality processing!

**Gap**: Discrete transitions (immediate, timed, stochastic) currently use **interleaving**, not **maximal step**.

---

### Statement 5: "By 1, 2, 4, how do localities relate with global time?"

**Interpretation**:
- Global time τ_sim advances uniformly for all localities
- Each locality may have **local timing state** (enablement time, scheduled fire time)
- Question: Is there a **local time** concept, or just **local timing constraints** on global time?

**Time Architecture** (from recent time scale implementation):

**Three-Time Concept**:
```
τ_real       : Real-world phenomenon time (24 hours)
τ_sim        : Simulation/model time (variable, 0 → duration)
τ_playback   : Playback/wall-clock time (τ_sim / time_scale)
```

**Global Time**: `SimulationController.time` (τ_sim)
- Advances uniformly: `self.time += time_step`
- Shared by ALL transitions/localities
- Used for:
  - Enablement tracking (`t_enable`)
  - Scheduling (`t_fire = t_enable + delay`)
  - Timing windows (`[t_enable + α, t_enable + β]`)

**Local Timing State** (per-transition):
```python
class TransitionState:
    enablement_time: Optional[float]  # When became enabled (in τ_sim)
    scheduled_time: Optional[float]   # When scheduled to fire (in τ_sim)
```

**Relationship**:
```
Global: τ_sim = 0 → 1 → 2 → 3 → ... (advances uniformly)

Local (T1): 
    t_enable = 1.5
    t_fire ∈ [2.5, 3.5]  (timing window in τ_sim)

Local (T2):
    t_enable = 2.0
    t_scheduled = 2.8    (sampled fire time in τ_sim)
```

**Answer**: 
- **NO separate local time** (no τ_local per locality)
- **Only local timing constraints** (enablement, windows, schedules) **expressed in global time**
- All localities **share the same global time reference** (τ_sim)

**Implication for Parallel Processing**:
```
At τ_sim = 5.0:
    T1: enabled at 3.0, window [4.0, 6.0] → CAN FIRE NOW
    T2: enabled at 4.5, window [5.0, 7.0] → CAN FIRE NOW
    T3: enabled at 2.0, window [3.0, 4.0] → TOO LATE (disabled)

Maximal Step at τ=5.0: {T1, T2} (if non-conflicting)
```

**Petri Net Standard**: Uses **global time** with **local constraints**.

---

### Statement 6: "By 1, 2, 3, 4, 5, how do localities relate to firing?"

**Interpretation**:
- Given all previous statements, how does the **firing mechanism** work across localities?
- Can multiple localities fire simultaneously?
- How are conflicts resolved?
- What are the firing semantics?

**Firing Semantics - Theory**:

**Sequential Firing** (Automata-like):
```
At each step:
1. Find ALL enabled transitions
2. SELECT ONE transition (conflict resolution)
3. FIRE that transition
4. Repeat
```
→ **Total ordering** of firings (T1 → T2 → T3)

**Maximal Step Semantics** (True concurrency):
```
At each step:
1. Find ALL enabled transitions
2. Compute MAXIMAL NON-CONFLICTING SET
3. FIRE ALL transitions in that set SIMULTANEOUSLY
4. Advance time
```
→ **Partial ordering** of firings (concurrent events are unordered)

**Maximal Non-Conflicting Set**:
```python
def compute_maximal_step(enabled_transitions):
    """Find largest set of transitions that can fire concurrently."""
    maximal_set = []
    for t in enabled_transitions:
        # Check if t conflicts with any transition in maximal_set
        if not conflicts_with_any(t, maximal_set):
            maximal_set.append(t)
    return maximal_set

def conflicts_with(t1, t2):
    """Two transitions conflict if they share input places."""
    return (•t1 ∩ •t2) ≠ ∅
```

**Example**:
```
    P1(10) --→ T1 --→ P2      (needs 5 tokens)
    P1(10) --→ T2 --→ P3      (needs 5 tokens)
    P4(10) --→ T3 --→ P5      (independent)
```

**Sequential**: Fire one per step
```
t=0: Fire T1 → P1=5, P2=5
t=1: Fire T2 → Fails (P1 has only 5, needs 5) or succeeds
t=2: Fire T3 → P4=5, P5=5
```

**Maximal Step**: Fire all non-conflicting
```
t=0: T1 and T2 CONFLICT (share P1) but T3 is independent
     Option 1: Fire {T1, T3}
     Option 2: Fire {T2, T3}
     Option 3: Fire {T1} only if T1 > priority(T2)
```

**Current Implementation** (from analysis above):

✅ **Continuous transitions**: Maximal step (all fire simultaneously)
```python
for transition in continuous_to_integrate:
    behavior.integrate(time_step)  # All fire in parallel
```

❌ **Discrete transitions** (immediate, timed, stochastic): Sequential
```python
transition = select_one(enabled)  # Pick ONE
fire(transition)                  # Fire ONE
```

---

## Part 2: Current Implementation Architecture

### Locality Detection (Already Implemented)

**`LocalityDetector` class** (`src/shypn/diagnostic/locality_detector.py`):
```python
class Locality:
    """Represents a transition-centered locality."""
    transition: Any          # Central transition
    input_places: List[Any]  # •t (input neighborhood)
    output_places: List[Any] # t• (output neighborhood)
    input_arcs: List[Any]    # Arcs from places to t
    output_arcs: List[Any]   # Arcs from t to places

class LocalityDetector:
    """Detector for transition-centered localities."""
    
    def get_locality_for_transition(self, transition) -> Locality:
        """Extract locality for a specific transition."""
        # Scans all arcs, identifies inputs/outputs
        
    def get_all_localities(self) -> List[Locality]:
        """Detect all valid localities in model."""
        
    def find_shared_places(self) -> Dict[str, List]:
        """Find places shared between multiple localities."""
```

**Usage**:
```python
detector = LocalityDetector(model)
locality = detector.get_locality_for_transition(t1)
print(locality.get_summary())  # "2 inputs → T1 → 3 outputs"
```

**Status**: ✅ **Locality detection fully implemented**

---

### Behavior System (Per-Locality Behavior)

**Behavior Factory** (`src/shypn/engine/__init__.py`):
```python
def behavior_factory(transition, model) -> TransitionBehavior:
    """Create behavior instance based on transition type."""
    transition_type = transition.transition_type
    
    if transition_type == 'immediate':
        return ImmediateBehavior(transition, model)
    elif transition_type == 'timed':
        return TimedBehavior(transition, model)
    elif transition_type == 'stochastic':
        return StochasticBehavior(transition, model)
    elif transition_type == 'continuous':
        return ContinuousBehavior(transition, model)
    else:
        return ImmediateBehavior(transition, model)  # Default
```

**Behavior Interface**:
```python
class TransitionBehavior:
    def can_fire(self) -> Tuple[bool, str]:
        """Check LOCAL enablement (tokens, timing, guard)."""
        
    def fire(self, input_arcs, output_arcs) -> Tuple[bool, Dict]:
        """Execute LOCAL token transfer."""
        
    def get_input_arcs(self) -> List[Arc]:
        """Get LOCAL input arcs (defines •t)."""
        
    def get_output_arcs(self) -> List[Arc]:
        """Get LOCAL output arcs (defines t•)."""
```

**Key Properties**:
- ✅ Each locality has **isolated behavior** (encapsulation)
- ✅ Behavior only accesses **local neighborhood** (•t, t•)
- ✅ Behavior is **instantiated per transition** (one-to-one mapping)
- ✅ Behavior has **private state** (e.g., `_enablement_time`)

**Status**: ✅ **Per-locality behavior fully implemented**

---

### Simulation Controller (Firing Mechanism)

**`SimulationController.step()` phases**:

```python
def step(self, time_step):
    # === PHASE 1: Exhaust Immediate Transitions ===
    # Sequential firing until no immediate transitions enabled
    for iteration in range(max_iterations):
        enabled_immediate = [t for t in immediates if can_fire(t)]
        if not enabled_immediate:
            break
        transition = select_one(enabled_immediate)  # ← ONE
        fire(transition)                            # ← FIRE
        update_enablements()
    
    # === PHASE 2: Timed Window Crossing ===
    # Fire timed transitions whose windows are being crossed
    for timed_transition in timed_transitions:
        if will_cross_window(timed_transition, time_step):
            fire(timed_transition)  # ← Sequential (one at a time)
    
    # === PHASE 3: Identify Continuous Transitions ===
    # BEFORE discrete firing, identify continuous transitions
    continuous_to_integrate = []
    for continuous_t in continuous_transitions:
        if can_fire(continuous_t):
            continuous_to_integrate.append(continuous_t)
    
    # === PHASE 4: Fire ONE Discrete Transition ===
    # Timed and stochastic transitions (sequential)
    enabled_discrete = [t for t in discrete if can_fire(t)]
    if enabled_discrete:
        transition = select_one(enabled_discrete)  # ← ONE
        fire(transition)                          # ← FIRE
    
    # === PHASE 5: Integrate ALL Continuous Transitions ===
    # Uses state BEFORE discrete firing (parallel integration)
    for (transition, behavior, in_arcs, out_arcs) in continuous_to_integrate:
        behavior.integrate(time_step)  # ← ALL FIRE SIMULTANEOUSLY
    
    # === PHASE 6: Advance Global Time ===
    self.time += time_step
    
    # === PHASE 7: Notify Listeners ===
    notify_step_listeners()
```

**Conflict Resolution** (`_select_transition`):
```python
def _select_transition(self, enabled_transitions):
    if len(enabled_transitions) == 1:
        return enabled_transitions[0]
    
    if policy == RANDOM:
        return random.choice(enabled_transitions)
    elif policy == PRIORITY:
        return max(enabled_transitions, key=lambda t: t.priority)
    elif policy == TYPE_BASED:
        return max(enabled_transitions, key=lambda t: TYPE_PRIORITIES[t.type])
    elif policy == ROUND_ROBIN:
        return enabled_transitions[round_robin_index % len(enabled_transitions)]
```

**Key Observations**:
1. **Immediate/Discrete**: Uses **interleaving** (sequential firing)
2. **Continuous**: Uses **maximal step** (all fire simultaneously)
3. **Conflict resolution**: Only chooses between **conflicting** transitions
4. **No independence detection**: Doesn't identify non-conflicting transitions that could fire together

---

## Part 3: Gaps Analysis - Theory vs Implementation

### Gap 1: Sequential Discrete Firing

**Theory**: Maximal step semantics allows **concurrent firing** of non-conflicting transitions

**Current**: Fires **ONE discrete transition per step**

**Example Impact**:
```
Network:
    P1(5) --→ T1 --→ P2  (immediate, needs 1 token)
    P3(5) --→ T2 --→ P4  (immediate, needs 1 token)
```

**Current Behavior** (interleaving):
```
t=0: Fire T1 → P1=4, P2=1
t=1: Fire T2 → P3=4, P4=1
t=2: Fire T1 → P1=3, P2=2
...
Total: 5 simulation steps to fire all instances
```

**Maximal Step Behavior** (parallel):
```
t=0: Fire {T1, T2} → P1=4, P2=1, P3=4, P4=1
t=1: Fire {T1, T2} → P1=3, P2=2, P3=3, P4=2
...
Total: 5 simulation steps, but semantically different
     (T1 and T2 fire TRULY concurrently, not sequentially)
```

**Consequence**: 
- Simulation is **correct** (same final marking)
- But **not maximally concurrent** (misses parallelism)
- May affect **performance** (more steps needed)
- May affect **time-dependent behaviors** (if timing matters)

---

### Gap 2: No Conflict Analysis

**Theory**: Compute **conflict sets** and **maximal concurrent sets**

**Current**: Conflict resolution only when **selecting ONE** from **all enabled**

**What's Missing**:
```python
def compute_conflicts(enabled_transitions):
    """Build conflict graph."""
    conflict_graph = {}
    for t1 in enabled_transitions:
        conflict_graph[t1] = []
        for t2 in enabled_transitions:
            if t1 != t2 and shares_input_places(t1, t2):
                conflict_graph[t1].append(t2)
    return conflict_graph

def compute_maximal_concurrent_set(enabled_transitions):
    """Find maximal independent set in conflict graph."""
    conflicts = compute_conflicts(enabled_transitions)
    
    # Greedy algorithm (can be improved with graph algorithms)
    maximal_set = []
    for t in enabled_transitions:
        # Check if t conflicts with any transition in maximal_set
        if not any(t in conflicts[m] for m in maximal_set):
            maximal_set.append(t)
    
    return maximal_set
```

**Current `_select_transition`**: Doesn't compute conflict sets, just picks ONE.

---

### Gap 3: Local Time Tracking (Not Needed)

**Theory**: Each locality could have **local clock**

**Current**: Uses **global time** with **local timing constraints**

**Analysis**: ✅ **No gap** - Petri net standard uses global time
- Timed transitions: `[t_enable + α, t_enable + β]` in global time
- Stochastic transitions: `t_fire = t_enable + delay` in global time
- Continuous transitions: Integrate over `[t, t + Δt]` in global time

**Conclusion**: Current approach is **correct and standard**.

---

## Part 4: Implementation Plan (Optional)

### Should We Implement Maximal Step Semantics?

**Arguments FOR**:
1. ✅ **Theoretical correctness**: True Petri net concurrency semantics
2. ✅ **Performance**: Fewer simulation steps needed
3. ✅ **Scalability**: Large models with many independent localities
4. ✅ **Parallel execution**: Could leverage multi-core CPUs

**Arguments AGAINST**:
1. ⚠️ **Complexity**: More complex conflict detection and resolution
2. ⚠️ **Determinism**: Maximal step may be non-deterministic (multiple choices)
3. ⚠️ **Current system works**: Interleaving is correct (just slower)
4. ⚠️ **User expectation**: Most users expect sequential execution

**Recommendation**: **Make it OPTIONAL**
- Default: Interleaving (current behavior)
- Advanced: Maximal step (opt-in via settings)

---

### Phase 1: Conflict Detection (Foundation)

**Goal**: Identify which transitions conflict (share input places)

**Implementation**:

```python
# In SimulationController

def _compute_conflict_sets(self, transitions: List) -> Dict[str, Set[str]]:
    """Compute conflict sets for transitions.
    
    Two transitions conflict if they share at least one input place.
    
    Returns:
        Dict mapping transition ID to set of conflicting transition IDs
    """
    conflict_sets = {t.id: set() for t in transitions}
    
    for i, t1 in enumerate(transitions):
        behavior1 = self._get_behavior(t1)
        input_places_1 = {arc.source_id for arc in behavior1.get_input_arcs()}
        
        for t2 in transitions[i+1:]:
            behavior2 = self._get_behavior(t2)
            input_places_2 = {arc.source_id for arc in behavior2.get_input_arcs()}
            
            # Check for shared input places
            if input_places_1 & input_places_2:  # Intersection
                conflict_sets[t1.id].add(t2.id)
                conflict_sets[t2.id].add(t1.id)
    
    return conflict_sets

def _are_concurrent(self, t1, t2) -> bool:
    """Check if two transitions are concurrent (non-conflicting).
    
    Returns:
        True if transitions can fire simultaneously
    """
    behavior1 = self._get_behavior(t1)
    behavior2 = self._get_behavior(t2)
    
    input_places_1 = {arc.source_id for arc in behavior1.get_input_arcs()}
    input_places_2 = {arc.source_id for arc in behavior2.get_input_arcs()}
    
    # Concurrent if NO shared input places
    return len(input_places_1 & input_places_2) == 0
```

**Testing**:
```python
# test_conflict_detection.py
def test_conflicting_transitions():
    """Test conflict detection for transitions sharing input place."""
    # P1 → T1 → P2
    # P1 → T2 → P3
    # T1 and T2 conflict (share P1)
    
    controller = SimulationController(model)
    assert not controller._are_concurrent(t1, t2)

def test_concurrent_transitions():
    """Test concurrent detection for independent transitions."""
    # P1 → T1 → P2
    # P3 → T2 → P4
    # T1 and T2 are concurrent (no shared places)
    
    controller = SimulationController(model)
    assert controller._are_concurrent(t1, t2)
```

---

### Phase 2: Maximal Concurrent Set

**Goal**: Compute maximal set of non-conflicting enabled transitions

**Implementation**:

```python
def _compute_maximal_concurrent_set(
    self, 
    enabled_transitions: List
) -> List:
    """Compute maximal set of non-conflicting transitions.
    
    Uses greedy algorithm to find a maximal independent set in the
    conflict graph. This is not necessarily the MAXIMUM set (which
    is NP-hard), but a maximal set (no more can be added).
    
    Args:
        enabled_transitions: List of enabled transitions
        
    Returns:
        List of transitions that can fire concurrently
    """
    if len(enabled_transitions) <= 1:
        return enabled_transitions
    
    maximal_set = []
    
    for transition in enabled_transitions:
        # Check if this transition conflicts with any in maximal_set
        can_add = True
        for selected in maximal_set:
            if not self._are_concurrent(transition, selected):
                can_add = False
                break
        
        if can_add:
            maximal_set.append(transition)
    
    return maximal_set
```

**Algorithm Properties**:
- **Greedy**: May not find globally optimal set (but acceptable)
- **Deterministic**: Same input → same output (order-dependent)
- **Polynomial time**: O(n²) where n = |enabled_transitions|

**Alternative**: Use **graph coloring** or **maximum independent set** algorithms (more complex).

---

### Phase 3: Maximal Step Execution

**Goal**: Fire all transitions in maximal concurrent set simultaneously

**Implementation**:

```python
def step_maximal(self, time_step: float = None) -> bool:
    """Execute simulation step with maximal step semantics.
    
    Fires all non-conflicting enabled transitions simultaneously.
    
    Returns:
        bool: True if any transitions fired
    """
    if time_step is None:
        time_step = self.get_effective_dt()
    
    self._update_enablement_states()
    
    # === PHASE 1: Exhaust Immediate Transitions (Maximal Step) ===
    immediate_fired = 0
    max_iterations = 1000
    
    for iteration in range(max_iterations):
        immediate_transitions = [
            t for t in self.model.transitions 
            if t.transition_type == 'immediate'
        ]
        enabled_immediate = [
            t for t in immediate_transitions 
            if self._is_transition_enabled(t)
        ]
        
        if not enabled_immediate:
            break
        
        # COMPUTE MAXIMAL CONCURRENT SET
        maximal_set = self._compute_maximal_concurrent_set(enabled_immediate)
        
        # FIRE ALL TRANSITIONS IN MAXIMAL SET
        for transition in maximal_set:
            self._fire_transition(transition)
            immediate_fired += 1
        
        self._update_enablement_states()
    
    # === PHASE 2: Fire Maximal Set of Discrete Transitions ===
    discrete_transitions = [
        t for t in self.model.transitions 
        if t.transition_type in ['timed', 'stochastic']
    ]
    enabled_discrete = [
        t for t in discrete_transitions 
        if self._is_transition_enabled(t)
    ]
    
    if enabled_discrete:
        # COMPUTE MAXIMAL CONCURRENT SET
        maximal_set = self._compute_maximal_concurrent_set(enabled_discrete)
        
        # FIRE ALL TRANSITIONS IN MAXIMAL SET
        for transition in maximal_set:
            self._fire_transition(transition)
    
    # === PHASE 3: Integrate Continuous (Same as Before) ===
    continuous_transitions = [
        t for t in self.model.transitions 
        if t.transition_type == 'continuous'
    ]
    for transition in continuous_transitions:
        behavior = self._get_behavior(transition)
        if behavior.can_fire()[0]:
            behavior.integrate(time_step)
    
    # === PHASE 4: Advance Time ===
    self.time += time_step
    self._notify_step_listeners()
    
    return immediate_fired > 0 or len(enabled_discrete) > 0
```

**Key Changes**:
1. **Compute maximal set** instead of selecting one
2. **Fire all in set** (loop over maximal_set)
3. **Update enablements** after each maximal step

---

### Phase 4: Settings Integration

**Goal**: Allow user to choose execution semantics

**Implementation**:

```python
# In SimulationSettings

class ExecutionSemantics(Enum):
    """Execution semantics for discrete transitions."""
    INTERLEAVING = "interleaving"  # Fire one per step (current)
    MAXIMAL_STEP = "maximal_step"  # Fire all non-conflicting

class SimulationSettings:
    def __init__(self):
        # ... existing settings ...
        self.execution_semantics = ExecutionSemantics.INTERLEAVING
```

**Controller**:

```python
def step(self, time_step: float = None) -> bool:
    """Execute simulation step with configured semantics."""
    if self.settings.execution_semantics == ExecutionSemantics.MAXIMAL_STEP:
        return self.step_maximal(time_step)
    else:
        return self.step_interleaving(time_step)  # Current implementation

def step_interleaving(self, time_step: float = None) -> bool:
    """Current implementation (renamed for clarity)."""
    # ... existing step() code ...
```

**UI Integration** (settings panel):
```
┌─ Execution Semantics ────────┐
│ ○ Interleaving (Sequential)  │  ← Default (backward compatible)
│ ○ Maximal Step (Concurrent)  │  ← Advanced (true concurrency)
└───────────────────────────────┘
```

---

## Part 5: Summary and Recommendations

### Answers to User's 6 Questions

| # | Question | Answer | Current Status |
|---|----------|--------|----------------|
| 1 | **Locality isolation**? | YES - Localities operate on independent neighborhoods if they don't share places | ✅ Implemented (LocalityDetector) |
| 2 | **Own behavior**? | YES - Each locality has type-specific behavior (immediate, timed, stochastic, continuous) | ✅ Implemented (TransitionBehavior hierarchy) |
| 3 | **Instantiates behavior**? | YES - Each transition instantiates and owns its behavior instance | ✅ Implemented (behavior_factory, cached) |
| 4 | **Parallel processing**? | YES in theory - Independent localities CAN fire concurrently | ⚠️ Partial: Continuous=parallel, Discrete=sequential |
| 5 | **Global time relation**? | Localities share global time (τ_sim) but have local timing constraints | ✅ Correct (standard Petri net approach) |
| 6 | **Firing relation**? | Current: Interleaving. Possible: Maximal step | ⚠️ Gap: Could support maximal step |

---

### Current Architecture Strengths

✅ **Locality Detection**: Fully implemented  
✅ **Behavior Encapsulation**: Each locality has isolated behavior  
✅ **Behavior Instantiation**: One-to-one mapping transition ↔ behavior  
✅ **Global Time**: Correct use of shared time reference  
✅ **Continuous Transitions**: Already use maximal step (parallel)  
✅ **Extensible**: Easy to add maximal step for discrete transitions  

---

### Gaps

⚠️ **Discrete Transition Parallelism**: Uses interleaving, not maximal step  
⚠️ **Conflict Detection**: Doesn't explicitly compute conflict sets  
⚠️ **Concurrency Analysis**: Doesn't identify independent localities  

---

### Recommendations

**Recommendation 1**: **DOCUMENT current behavior** ✅ (this document)

**Recommendation 2**: **Implement maximal step as OPTIONAL** 
- Priority: MEDIUM (nice-to-have, not critical)
- Effort: 2-3 days
- Phases:
  1. Conflict detection (4 hours)
  2. Maximal concurrent set (4 hours)
  3. Maximal step execution (6 hours)
  4. Settings integration (2 hours)
  5. Testing (8 hours)

**Recommendation 3**: **Default to interleaving** (backward compatible)

**Recommendation 4**: **Provide user education**
- Explain difference between interleaving vs maximal step
- When to use each mode
- Performance implications

---

### Decision Tree

```
┌─ Should we implement maximal step semantics? ─┐
│                                                │
│  Is parallelism important for your models?    │
│  ├─ YES → Implement (Phases 1-4)              │
│  └─ NO  → Document and defer                  │
│                                                │
│  Do users understand true concurrency?        │
│  ├─ YES → Make it default (advanced users)    │
│  └─ NO  → Keep interleaving default           │
│                                                │
│  Do you have large models (100+ transitions)? │
│  ├─ YES → High priority (performance gain)    │
│  └─ NO  → Low priority (minor benefit)        │
└────────────────────────────────────────────────┘
```

---

## Part 6: Technical References

### Petri Net Concurrency Literature

1. **Merlin & Farber (1976)**: Time Petri Nets
   - Introduced [earliest, latest] timing windows
   - Defined global time with local constraints

2. **Ajmone Marsan et al. (1995)**: Generalized Stochastic Petri Nets
   - Exponential firing distributions
   - Conflict resolution policies

3. **Reisig (2013)**: Understanding Petri Nets
   - Maximal step semantics (Section 3.4)
   - Conflict and confusion (Section 3.5)
   - True concurrency vs interleaving

4. **Petri (1962)**: Original thesis
   - Concept of independent concurrent actions
   - Place-transition locality

### Key Algorithms

**Maximal Independent Set** (Graph Theory):
```
Given: Conflict graph G = (V, E) where:
    V = enabled transitions
    E = conflicts (share input places)

Find: Maximal independent set I ⊆ V such that:
    ∀t₁, t₂ ∈ I: (t₁, t₂) ∉ E  (no conflicts in I)
    ∀t ∈ V \ I: ∃s ∈ I: (t, s) ∈ E  (can't add more without conflict)

Complexity: NP-hard for maximum set, polynomial for maximal set
```

**Greedy Algorithm** (Used in this plan):
```python
maximal_set = []
for t in enabled:
    if not conflicts_with_any(t, maximal_set):
        maximal_set.append(t)
return maximal_set
```

Time: O(n²), Space: O(n)

---

## Conclusion

**The system architecture SUPPORTS locality-based parallel processing**:

✅ **Localities are isolated** (LocalityDetector proves it)  
✅ **Each locality has its own behavior** (TransitionBehavior hierarchy)  
✅ **Behavior is instantiated per transition** (behavior_factory)  
✅ **Continuous transitions already fire in parallel** (maximal step implemented)  
⚠️ **Discrete transitions use interleaving** (sequential, not maximal step)  

**The gap is NOT fundamental—it's a design choice**:
- Current: Safe, simple, deterministic (interleaving)
- Possible: Concurrent, efficient, closer to theory (maximal step)

**Next steps depend on user priorities**:
- **If performance matters**: Implement maximal step (2-3 days)
- **If simplicity matters**: Document current behavior (done!)
- **If backward compatibility matters**: Make it optional (best of both)

---

**End of Analysis**  
**Date**: October 11, 2025  
**Status**: Ready for discussion and decision  
**Related Documents**: 
- `doc/time/REAL_WORLD_TIME_PLAYBACK_ANALYSIS.md` (global time architecture)
- `src/shypn/diagnostic/locality_detector.py` (locality detection implementation)
- `src/shypn/engine/simulation/controller.py` (current firing semantics)
