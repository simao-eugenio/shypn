# Revised Integration Plan Summary - Locality-Based Architecture

## Implementation Status

**Status**: ✅ **COMPLETE - Phase 4 Finished (January 2025)**

### Completed Phases

| Phase | Description | Tests | Status |
|-------|-------------|-------|--------|
| Phase 1 | Behavior Integration | 7/7 ✅ | Complete |
| Phase 2 | Conflict Resolution | 7/7 ✅ | Complete |
| Phase 3 | Time-Aware Behaviors | 6/6 ✅ | Complete |
| Phase 4 | Continuous Integration | 5/5 ✅ | **Complete** |

**Total Test Coverage**: **25/25 tests passing (100%)**

### Key Achievements

✅ Hybrid discrete-continuous Petri net simulation  
✅ Locality-based conflict resolution  
✅ Time-aware behavior management  
✅ RK4 numerical integration for continuous flows  
✅ Full backward compatibility maintained  
✅ Production-ready implementation  

### Documentation

- `doc/phase1_behavior_integration.md` - Behavior factory integration
- `doc/phase2_conflict_resolution.md` - Conflict policies
- `doc/phase3_time_aware_behaviors.md` - Time-aware execution
- `doc/phase3_summary.md` - Phase 3 summary
- `doc/phase4_continuous_integration.md` - Hybrid execution ⭐ **NEW**
- `doc/phase4_summary.md` - Phase 4 summary ⭐ **NEW**

---

## Core Principles (Revised Understanding)

### **Principle 1: Locality Independence**
**Each transition depends ONLY on its locality.**

```
Transition T1:
- Locality = {input places: •T1, output places: T1•}
- Enablement = function(•T1 only)
- Firing = function(•T1, T1• only)
- NO dependency on other transitions
- NO knowledge of net structure beyond locality
```

**Implication**: 
- Mixed transition types (immediate, timed, stochastic, continuous) coexist naturally
- No type-based priorities or grouping
- Transitions with disjoint localities can fire concurrently

### **Principle 2: Global Time, Local Frequencies**
**ONE global time for all transitions, each fires at its own frequency.**

```
Global Time: model.time (advances uniformly)
├── T1 (immediate):   fires instantly if enabled (∞ frequency)
├── T2 (timed):       fires in [t+α, t+β] window
├── T3 (stochastic):  fires at rate λ (Exp(λ) delays)
└── T4 (continuous):  flows at rate r(t) continuously

Time Step: Δt = 0.1s (same for all)
```

**Implication**:
- Controller advances ONE time variable
- Each behavior computes its own firing condition relative to global time
- No type-based scheduling; locality + time determines firing

---

## Simplified Architecture

### **Key Change: No Type-Based Grouping**

#### ❌ OLD (Incorrect):
```python
# Group by type (wrong!)
immediate = [t for t in enabled if t.type == 'immediate']
timed = [t for t in enabled if t.type == 'timed']
stochastic = [t for t in enabled if t.type == 'stochastic']

# Priority-based firing (wrong!)
if immediate:
    fire_one(immediate)
elif timed:
    fire_one(timed)
```

#### ✅ NEW (Locality-Based):
```python
# Evaluate ALL transitions independently (locality-based)
for transition in model.transitions:
    behavior = get_behavior(transition)
    
    # Each checks its own locality
    if behavior.can_fire():  # Based on LOCAL state
        enabled.append(transition)

# Resolve LOCALITY conflicts (shared places)
fireable = resolve_conflicts(enabled)  # Based on place overlap, not type

# Fire ALL non-conflicting (concurrent execution)
for transition in fireable:
    fire(transition)  # Multiple can fire if localities independent

# Advance GLOBAL time
model.time += time_step
```

---

## Revised Integration Plan

### **Phase 1: Basic Locality-Based Dispatch** (Week 1)

**Goal**: Replace type-agnostic firing with locality-based behavior dispatch

**Key Code Changes:**

```python
# Step 1.1: Add behavior cache
class SimulationController:
    def __init__(self, model):
        self.model = model
        self.time = 0.0
        self.behavior_cache = {}  # {transition_id: behavior}
        self.transition_states = {}  # {transition_id: TransitionState}

    def _get_behavior(self, transition):
        """Get cached behavior for transition."""
        if transition.id not in self.behavior_cache:
            from shypn.engine.behavior_factory import create_behavior
            self.behavior_cache[transition.id] = create_behavior(transition, self.model)
        return self.behavior_cache[transition.id]

# Step 1.2: Locality-based enablement check
def _is_transition_enabled(self, transition) -> bool:
    """Check using behavior's locality-based can_fire()."""
    behavior = self._get_behavior(transition)
    can_fire, reason = behavior.can_fire()
    return can_fire

# Step 1.3: Behavior-based firing
def _fire_transition(self, transition):
    """Fire using behavior's algorithm."""
    behavior = self._get_behavior(transition)
    input_arcs = behavior.get_input_arcs()
    output_arcs = behavior.get_output_arcs()
    
    success, details = behavior.fire(input_arcs, output_arcs)
    return success

# Step 1.4: Simple step() - all types treated equally
def step(self, time_step: float = 0.1) -> bool:
    """Execute one step - locality-based."""
    
    # Find ALL enabled transitions (locality check)
    enabled = []
    for transition in self.model.transitions:
        if self._is_transition_enabled(transition):
            enabled.append(transition)
    
    if not enabled:
        return False
    
    # For now: fire one randomly (Phase 2 adds conflict resolution)
    transition = random.choice(enabled)
    success = self._fire_transition(transition)
    
    # Global time advance
    self.time += time_step
    self._notify_step_listeners()
    
    return success
```

**Testing Phase 1:**
- Create net with immediate transitions only
- Verify behavior dispatch works
- Check token counts correct

---

### **Phase 2: Locality Conflict Resolution** (Week 2)

**Goal**: Enable concurrent firing for independent localities

**Key Concept**: 
- Transitions conflict if they share input places (same locality)
- Transitions with disjoint input places can fire simultaneously

**Key Code Changes:**

```python
def _get_input_places(self, transition) -> set:
    """Get set of input place IDs (locality)."""
    return set(arc.source.id for arc in self.model.arcs 
               if arc.target == transition)

def _resolve_conflicts(self, enabled: List) -> List:
    """Select non-conflicting subset based on locality overlap."""
    if len(enabled) <= 1:
        return enabled
    
    fireable = []
    used_places = set()  # Track which input places are "claimed"
    
    # Random order for fairness
    candidates = list(enabled)
    random.shuffle(candidates)
    
    for transition in candidates:
        input_places = self._get_input_places(transition)
        
        # Can fire if no input place already claimed
        if not (input_places & used_places):
            fireable.append(transition)
            used_places.update(input_places)
    
    return fireable

def step(self, time_step: float = 0.1) -> bool:
    """Execute one step with concurrent firing."""
    
    # Find all enabled (locality-based)
    enabled = [t for t in self.model.transitions 
               if self._is_transition_enabled(t)]
    
    # Resolve locality conflicts
    fireable = self._resolve_conflicts(enabled)
    
    # Fire ALL non-conflicting
    fired_count = 0
    for transition in fireable:
        if self._fire_transition(transition):
            fired_count += 1
    
    # Global time
    self.time += time_step
    self._notify_step_listeners()
    
    return fired_count > 0
```

**Testing Phase 2:**
- Create net with independent branches (disjoint localities)
- Verify multiple transitions fire concurrently
- Create net with shared places (conflicting localities)
- Verify conflict resolution works

---

### **Phase 3: Time-Aware Behaviors** (Week 3)

**Goal**: Add time tracking for timed/stochastic transitions

**Key Concept**:
- All transitions see same global time
- Each tracks its own enablement time
- Behaviors compute firing readiness relative to global time

**Key Code Changes:**

```python
class TransitionState:
    """Per-transition state (locality-specific)."""
    def __init__(self):
        self.enablement_time = None  # When locally enabled
        self.scheduled_time = None   # For stochastic only

def _update_enablement_states(self):
    """Update enablement tracking for all transitions."""
    for transition in self.model.transitions:
        behavior = self._get_behavior(transition)
        
        # Check LOCALITY enablement (structural)
        input_arcs = behavior.get_input_arcs()
        locally_enabled = all(
            arc.source.tokens >= arc.weight 
            for arc in input_arcs
        )
        
        state = self._get_or_create_state(transition)
        
        if locally_enabled:
            # Newly enabled: record time
            if state.enablement_time is None:
                state.enablement_time = self.time
                
                # Notify behavior (for stochastic sampling)
                if hasattr(behavior, 'set_enablement_time'):
                    behavior.set_enablement_time(self.time)
        else:
            # Disabled: clear state
            state.enablement_time = None
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()

def step(self, time_step: float = 0.1) -> bool:
    """Execute one step with time-aware behaviors."""
    
    # Update time-based states
    self._update_enablement_states()
    
    # Find enabled (behavior decides based on global time + local state)
    enabled = []
    for transition in self.model.transitions:
        behavior = self._get_behavior(transition)
        can_fire, reason = behavior.can_fire()  # Uses self.model.time internally
        if can_fire:
            enabled.append(transition)
    
    # Resolve and fire
    fireable = self._resolve_conflicts(enabled)
    fired_count = sum(1 for t in fireable if self._fire_transition(t))
    
    # Global time
    self.time += time_step
    self._notify_step_listeners()
    
    return fired_count > 0
```

**Testing Phase 3:**
- Create net with timed transitions (test timing windows)
- Create net with stochastic transitions (test exponential delays)
- Mix all types in one net (verify coexistence)

---

### **Phase 4: Continuous Integration** (Week 4)

**Goal**: Add continuous transitions with locality-based integration

**Key Concept**:
- Continuous transitions integrate in parallel (don't "fire")
- Use same global time step
- Operate independently on their localities

**Key Code Changes:**

```python
def step(self, time_step: float = 0.1) -> bool:
    """Execute one step: discrete + continuous."""
    
    # === DISCRETE TRANSITIONS (fire) ===
    self._update_enablement_states()
    
    discrete = [t for t in self.model.transitions 
                if t.transition_type in ['immediate', 'timed', 'stochastic']]
    
    enabled_discrete = [t for t in discrete 
                       if self._get_behavior(t).can_fire()[0]]
    
    fireable = self._resolve_conflicts(enabled_discrete)
    discrete_fired = sum(1 for t in fireable if self._fire_transition(t))
    
    # === CONTINUOUS TRANSITIONS (integrate) ===
    continuous = [t for t in self.model.transitions 
                  if t.transition_type == 'continuous']
    
    continuous_active = 0
    for transition in continuous:
        behavior = self._get_behavior(transition)
        
        # Locality check (can flow?)
        if behavior.can_fire()[0]:
            input_arcs = behavior.get_input_arcs()
            output_arcs = behavior.get_output_arcs()
            
            # Integrate (operates on locality only)
            success, details = behavior.integrate_step(
                dt=time_step,
                input_arcs=input_arcs,
                output_arcs=output_arcs
            )
            if success:
                continuous_active += 1
    
    # Global time
    self.time += time_step
    self._notify_step_listeners()
    
    return discrete_fired > 0 or continuous_active > 0
```

**Testing Phase 4:**
- Create hybrid net (discrete + continuous)
- Verify independent operation
- Test locality independence (continuous on one path, discrete on another)

---

### **Phase 5: Optimization & Formula Evaluation** (Week 5)

**Goal**: Performance tuning and expression support

**Key Changes:**
- Behavior cache already implemented (Phase 1)
- Add expression evaluator for guard/rate formulas
- Profile and optimize

---

## Summary: Key Differences from Original Plan

### ❌ Removed (Incorrect Assumptions):
1. Type-based grouping (immediate, timed, stochastic groups)
2. Type-based priorities (immediate fires before timed)
3. Race condition between types
4. Sequential execution by type

### ✅ Added (Locality Principles):
1. **Locality independence**: Each transition evaluated independently
2. **Global time**: Single time variable for all
3. **Locality conflicts**: Resolution based on place overlap, not type
4. **Concurrent firing**: Multiple transitions fire if localities disjoint
5. **Type coexistence**: All types treated equally, mixed naturally

### Architecture Summary:

```
Controller.step():
│
├─ Update Enablement States (per-transition, locality-based)
│  └─ For each transition:
│     └─ Check local input places → update enablement_time
│
├─ Find Enabled Transitions (behavior-based)
│  └─ For each transition:
│     └─ behavior.can_fire() → uses global time + local state
│
├─ Resolve Locality Conflicts (place-based)
│  └─ Select subset with non-overlapping input places
│
├─ Fire All Non-Conflicting (concurrent)
│  └─ For each in fireable:
│     └─ behavior.fire() → operates on locality only
│
└─ Advance Global Time
   └─ model.time += time_step (uniform for all)
```

---

## Timeline: 4-5 Weeks

**Week 1**: Phase 1 (Basic locality dispatch)  
**Week 2**: Phase 2 (Conflict resolution)  
**Week 3**: Phase 3 (Time awareness)  
**Week 4**: Phase 4 (Continuous integration)  
**Week 5**: Phase 5 (Optimization)

---

**Document Updated**: October 4, 2025  
**Status**: Revised based on locality independence and global time principles  
**Ready**: Phase 1 implementation can start immediately
