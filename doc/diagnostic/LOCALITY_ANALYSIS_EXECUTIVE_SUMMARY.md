# Locality and Parallel Processing - Executive Summary
**Date**: October 11, 2025  
**Context**: Analysis of locality-based parallel processing in Petri net simulation  
**Full Analysis**: `LOCALITY_PARALLEL_PROCESSING_ANALYSIS.md`

---

## Quick Answers to Your 6 Questions

### 1. **"Every locality in the system is isolated from others"**

**YES** ✅ - Localities are isolated when they don't share places.

**Current Implementation**:
- `LocalityDetector` class identifies neighborhoods: `(•t, t, t•)`
- Localities that share NO places are **structurally independent**
- Example: `P1→T1→P2` and `P3→T2→P4` are completely isolated

**Formalism**:
```
Locality₁ ⊥ Locality₂  ⟺  (•t₁ ∪ t₁•) ∩ (•t₂ ∪ t₂•) = ∅
```

---

### 2. **"All locality has its own behavior"**

**YES** ✅ - Each transition has type-specific behavior.

**Current Implementation**:
```python
class TransitionBehavior:  # Base
    - can_fire()     # LOCAL enablement check
    - fire()         # LOCAL token transfer

class ImmediateBehavior:  # Zero-delay
class TimedBehavior:      # [earliest, latest] windows
class StochasticBehavior: # Exponential distribution
class ContinuousBehavior: # Continuous flow
```

**Behavior depends ONLY on**:
- Local marking (tokens in •t)
- Local timing state (enablement time)
- Local arc weights (Pre/Post matrices)

---

### 3. **"Locality instantiates its own behavior"**

**YES** ✅ - Each transition instantiates and owns its behavior.

**Current Implementation**:
```python
def _get_behavior(self, transition):
    if transition.id not in self._behaviors:
        # INSTANTIATE behavior based on type
        self._behaviors[transition.id] = behavior_factory(transition, model)
    return self._behaviors[transition.id]
```

**Properties**:
- One behavior instance per transition (1:1 mapping)
- Behavior has private state (`enablement_time`, `scheduled_time`)
- Cached for efficiency but isolated per locality

---

### 4. **"By 2 and 3, this implies parallel processing"**

**YES in theory, PARTIAL in practice** ⚠️

**Theory** (Maximal Step Semantics):
```
Fire ALL non-conflicting enabled transitions simultaneously:
    {T1, T2, T3} → fire in parallel at time t
```

**Current Implementation**:
- ✅ **Continuous transitions**: Parallel (maximal step)
- ❌ **Discrete transitions** (immediate/timed/stochastic): Sequential (interleaving)

**Example**:
```
Network:
    P1(5) → T1 → P2  (immediate)
    P3(5) → T2 → P4  (immediate)  ← T1 and T2 are independent!
```

**Current behavior** (interleaving):
```
Step 1: Fire T1 only
Step 2: Fire T2 only
Step 3: Fire T1 only
...
```

**Maximal step** (what's possible):
```
Step 1: Fire {T1, T2} simultaneously
Step 2: Fire {T1, T2} simultaneously
...
```

**Gap**: Discrete transitions could fire in parallel but currently don't.

---

### 5. **"By 1, 2, 4, how do localities relate with global time?"**

**Localities share GLOBAL TIME** (τ_sim) **with LOCAL TIMING CONSTRAINTS** ✅

**Three-Time Architecture** (from time scale implementation):
```
τ_real      : Real-world phenomenon time (24 hours)
τ_sim       : Simulation/model time (0 → duration)
τ_playback  : Wall-clock viewing time (τ_sim / time_scale)
```

**Global Time**: `controller.time` (τ_sim)
- Advances uniformly: `self.time += time_step`
- Shared by ALL localities

**Local Timing Constraints** (per transition):
```python
class TransitionState:
    enablement_time: float   # When became enabled (in τ_sim)
    scheduled_time: float    # When scheduled to fire (in τ_sim)
```

**Example**:
```
At τ_sim = 5.0:
    T1: enabled at 3.0, window [4.0, 6.0] → CAN FIRE (in window)
    T2: enabled at 4.5, window [5.0, 7.0] → CAN FIRE (just entered)
    T3: enabled at 2.0, window [3.0, 4.0] → TOO LATE (window passed)

Maximal step: {T1, T2} if non-conflicting
```

**Key**: NO local time per locality, just local constraints on global time.

---

### 6. **"By 1, 2, 3, 4, 5, how do localities relate to firing?"**

**Firing semantics**: Currently **INTERLEAVING**, could support **MAXIMAL STEP**

**Current Implementation** (`controller.step()`):
```python
# Phase 1: Exhaust immediate transitions (sequential)
for iteration in range(max):
    enabled = find_enabled_immediate()
    if not enabled: break
    transition = select_one(enabled)  # ← SELECT ONE
    fire(transition)                  # ← FIRE ONE

# Phase 2: Fire discrete transition (sequential)
enabled = find_enabled_discrete()
if enabled:
    transition = select_one(enabled)  # ← SELECT ONE
    fire(transition)                  # ← FIRE ONE

# Phase 3: Continuous transitions (PARALLEL!)
for transition in continuous:
    if can_fire(transition):
        integrate(transition, dt)     # ← ALL FIRE
```

**Key Observation**: Continuous already does maximal step!

**What's Missing for Discrete**:
```python
# Maximal Step Algorithm (NOT implemented for discrete)
def compute_maximal_concurrent_set(enabled):
    maximal = []
    for t in enabled:
        if not conflicts_with_any(t, maximal):
            maximal.append(t)
    return maximal

def conflicts_with(t1, t2):
    """Two transitions conflict if they share input places."""
    return (•t1 ∩ •t2) ≠ ∅
```

---

## Architecture Assessment

### ✅ **Strengths**

| Component | Status | Implementation |
|-----------|--------|----------------|
| **Locality Detection** | ✅ Complete | `LocalityDetector` class |
| **Behavior Encapsulation** | ✅ Complete | `TransitionBehavior` hierarchy |
| **Behavior Instantiation** | ✅ Complete | `behavior_factory` with caching |
| **Global Time** | ✅ Correct | Shared `controller.time` |
| **Continuous Parallelism** | ✅ Complete | Maximal step for continuous |
| **Architecture Extensibility** | ✅ Ready | Easy to add maximal step |

---

### ⚠️ **Gaps**

| Component | Status | Impact |
|-----------|--------|--------|
| **Discrete Parallelism** | ⚠️ Sequential | Could fire more transitions per step |
| **Conflict Detection** | ⚠️ Missing | No explicit conflict graph computation |
| **Concurrency Analysis** | ⚠️ Missing | Doesn't identify independent localities |

---

## Implementation Plan (Optional)

### Phase 1: Conflict Detection (4 hours)
```python
def _compute_conflicts(self, transitions):
    """Build conflict graph for transitions."""
    conflicts = {t.id: set() for t in transitions}
    
    for t1 in transitions:
        inputs_1 = {arc.source_id for arc in get_input_arcs(t1)}
        for t2 in transitions:
            if t1 == t2: continue
            inputs_2 = {arc.source_id for arc in get_input_arcs(t2)}
            
            if inputs_1 & inputs_2:  # Share input places?
                conflicts[t1.id].add(t2.id)
    
    return conflicts

def _are_concurrent(self, t1, t2):
    """Check if two transitions can fire simultaneously."""
    inputs_1 = {arc.source_id for arc in get_input_arcs(t1)}
    inputs_2 = {arc.source_id for arc in get_input_arcs(t2)}
    return len(inputs_1 & inputs_2) == 0  # NO shared inputs
```

---

### Phase 2: Maximal Concurrent Set (4 hours)
```python
def _compute_maximal_concurrent_set(self, enabled):
    """Find maximal set of non-conflicting transitions.
    
    Uses greedy algorithm: O(n²) time complexity.
    """
    if len(enabled) <= 1:
        return enabled
    
    maximal = []
    for transition in enabled:
        # Check if conflicts with any in maximal set
        can_add = all(
            self._are_concurrent(transition, selected)
            for selected in maximal
        )
        if can_add:
            maximal.append(transition)
    
    return maximal
```

---

### Phase 3: Maximal Step Execution (6 hours)
```python
def step_maximal(self, time_step=None):
    """Execute with maximal step semantics."""
    # Phase 1: Exhaust immediates (maximal step)
    for iteration in range(max_iter):
        enabled = find_enabled_immediate()
        if not enabled: break
        
        maximal = compute_maximal_concurrent_set(enabled)  # ← NEW
        
        for transition in maximal:  # ← FIRE ALL
            fire(transition)
    
    # Phase 2: Fire discrete (maximal step)
    enabled = find_enabled_discrete()
    if enabled:
        maximal = compute_maximal_concurrent_set(enabled)  # ← NEW
        
        for transition in maximal:  # ← FIRE ALL
            fire(transition)
    
    # Phase 3: Continuous (already maximal)
    for transition in continuous:
        if can_fire(transition):
            integrate(transition, dt)
    
    self.time += time_step
```

---

### Phase 4: Settings Integration (2 hours)
```python
class ExecutionSemantics(Enum):
    INTERLEAVING = "interleaving"  # Current (sequential)
    MAXIMAL_STEP = "maximal_step"  # New (parallel)

class SimulationSettings:
    def __init__(self):
        self.execution_semantics = ExecutionSemantics.INTERLEAVING  # Default
```

**UI**:
```
Settings Panel:
┌─ Execution Semantics ────────┐
│ ● Interleaving (Sequential)  │  ← Default (backward compatible)
│ ○ Maximal Step (Concurrent)  │  ← Advanced (true concurrency)
└───────────────────────────────┘
```

---

## Decision Matrix

| Scenario | Recommendation |
|----------|----------------|
| **Small models** (< 20 transitions) | Keep interleaving (sufficient) |
| **Large models** (100+ transitions) | Implement maximal step (performance) |
| **Teaching/learning** | Keep interleaving (easier to understand) |
| **Research/analysis** | Implement maximal step (theoretical correctness) |
| **Production systems** | Make optional (user choice) |

---

## Summary

### What Works Now ✅

1. **Locality detection**: Fully implemented (`LocalityDetector`)
2. **Behavior encapsulation**: Each locality has isolated behavior
3. **Behavior instantiation**: One behavior per transition
4. **Global time**: Correct shared time with local constraints
5. **Continuous parallelism**: Already fires all enabled continuously

### What's Missing ⚠️

1. **Discrete parallelism**: Fires one at a time (sequential)
2. **Conflict detection**: No explicit conflict graph
3. **Maximal concurrent set**: Not computed

### What's Possible 🎯

1. **Implement maximal step** (2-3 days effort)
2. **Make it optional** (backward compatible)
3. **Provide user choice** (settings panel)

### Recommendation 🎯

**OPTION 1**: Keep current (simplest)
- ✅ Works correctly
- ✅ Backward compatible
- ✅ Easy to understand
- ❌ Slower for large models

**OPTION 2**: Implement maximal step (best of both)
- ✅ Theoretically correct
- ✅ Better performance
- ✅ Optional (user choice)
- ⚠️ 2-3 days implementation
- ⚠️ More complex

**OPTION 3**: Document and defer (pragmatic)
- ✅ Analysis complete (this document)
- ✅ Can implement later if needed
- ✅ Focus on other priorities

---

## Next Steps

1. **User decision**: Which option to pursue?
2. **If Option 2**: Execute 4-phase plan (2-3 days)
3. **If Option 3**: Archive analysis, focus elsewhere

---

**Full Analysis**: See `LOCALITY_PARALLEL_PROCESSING_ANALYSIS.md` (70+ pages)  
**Related Docs**: 
- `doc/time/REAL_WORLD_TIME_PLAYBACK_ANALYSIS.md` (global time)
- `src/shypn/diagnostic/locality_detector.py` (locality detection)
- `src/shypn/engine/simulation/controller.py` (current firing)

**Status**: ✅ Analysis complete, awaiting decision
