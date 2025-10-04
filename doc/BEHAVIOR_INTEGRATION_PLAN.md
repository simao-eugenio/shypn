# Integration Plan: Transition Behaviors OOP Architecture

## Fundamental Principles

### **Principle 1: Locality Independence**
**Each transition depends ONLY on its locality (input/output places).**

- A transition's enablement is determined by its local neighborhood
- No transition needs knowledge of other transitions
- Type mixing is natural: immediate, timed, stochastic, and continuous transitions coexist in the same net
- **Independence**: Each transition evaluates `can_fire()` based solely on its local state

### **Principle 2: Global Time, Local Frequencies**
**All transitions share ONE global simulation time, but fire at their own frequencies.**

- **Global Time**: `model.time` advances uniformly for all transitions
- **Local Frequency**: Each transition type has its own firing frequency:
  - Immediate: fires instantly when enabled (infinite frequency)
  - Timed: fires within `[earliest, latest]` window (constrained timing)
  - Stochastic: fires at `rate λ` (exponential frequency)
  - Continuous: flows continuously at `r(t)` (continuous frequency)
- **No Type Priority**: Transition types don't compete; they coexist based on locality

### **Architectural Implication**
The controller must:
1. Advance **ONE global time** for all transitions
2. Query each transition's **locality** independently
3. Let each behavior determine its **own firing frequency**
4. Allow **concurrent execution** where localities don't conflict

---

## Current State Analysis

### Existing Code Structure

```
Current Implementation:
├── src/shypn/netobjs/
│   └── transition.py              # Transition class (data model)
│       - Properties: type, enabled, guard, rate
│       - No behavior logic
│
├── src/shypn/engine/
│   ├── simulation/
│   │   └── controller.py          # SimulationController (orchestrator)
│   │       - _find_enabled_transitions()  # Basic locality check
│   │       - _is_transition_enabled()     # Simple token check
│   │       - _fire_transition()           # Simple token transfer
│   │       - step(), run(), stop(), reset()
│   │
│   ├── behavior_factory.py        # Factory pattern ✅
│   ├── transition_behavior.py     # ABC base class ✅
│   ├── immediate_behavior.py      # Immediate firing ✅
│   ├── timed_behavior.py          # TPN with [earliest, latest] ✅
│   ├── stochastic_behavior.py     # FSPN with Exp(λ) ✅
│   └── continuous_behavior.py     # SHPN with RK4 ✅
│
└── src/shypn/data/
    └── model_canvas_manager.py    # Model (places, transitions, arcs)
```

### Gap Analysis

**✅ Already Implemented:**
- All 4 behavior classes with complete algorithms
- Factory pattern for behavior creation
- Locality-based methods in behaviors
- Independence algorithms in behaviors
- Time tracking in SimulationController

**❌ Not Integrated:**
- SimulationController still uses **simple token transfer** (ignores behavior classes)
- No dispatch to behavior.can_fire() or behavior.fire()
- No time/rate/locality awareness in controller
- No independence algorithm selection
- Transition.type property not used for behavior selection

---

## OOP Design Principles

### 1. **Single Responsibility Principle (SRP)**

**Current:**
- ✅ `Transition`: Data model only (position, type, properties)
- ✅ `TransitionBehavior`: Firing logic only (can_fire, fire)
- ✅ `SimulationController`: Orchestration only (step, run, stop)

**Target:**
- Keep same separation
- Controller delegates firing decisions to behaviors

### 2. **Open/Closed Principle (OCP)**

**Current:**
- ✅ Behaviors are extensible (new types can be added)
- ❌ Controller is closed (hardcoded simple firing logic)

**Target:**
- Controller uses polymorphic behavior dispatch
- Adding new transition types requires no controller changes

### 3. **Liskov Substitution Principle (LSP)**

**Current:**
- ✅ All behaviors implement same interface
- Can be substituted for each other

**Target:**
- Controller treats all behaviors uniformly
- No type-specific conditionals in controller

### 4. **Dependency Inversion Principle (DIP)**

**Current:**
- ❌ Controller depends on concrete implementation (token transfer)

**Target:**
- Controller depends on `TransitionBehavior` abstraction
- Behaviors injected via factory

---

## Integration Plan

### **Phase 1: Minimal Integration** (Basic Behavior Dispatch)

**Goal**: Replace simple firing with behavior-based firing

**Changes:**

#### 1.1 Update SimulationController._is_transition_enabled()
```python
# BEFORE (simple token check)
def _is_transition_enabled(self, transition) -> bool:
    for arc in input_arcs:
        if place.tokens < required_tokens:
            return False
    return True

# AFTER (behavior-based check)
def _is_transition_enabled(self, transition) -> bool:
    from shypn.engine.behavior_factory import create_behavior
    
    behavior = create_behavior(transition, self.model)
    can_fire, reason = behavior.can_fire()
    
    return can_fire
```

#### 1.2 Update SimulationController._fire_transition()
```python
# BEFORE (simple token transfer)
def _fire_transition(self, transition):
    for arc in input_arcs:
        place.tokens -= weight
    for arc in output_arcs:
        place.tokens += weight

# AFTER (behavior-based firing)
def _fire_transition(self, transition):
    from shypn.engine.behavior_factory import create_behavior
    
    behavior = create_behavior(transition, self.model)
    
    # Get arcs using behavior's locality methods
    input_arcs = behavior.get_input_arcs()
    output_arcs = behavior.get_output_arcs()
    
    # Fire using behavior's algorithm
    success, details = behavior.fire(input_arcs, output_arcs)
    
    if success:
        print(f"[SimulationController] Fired {transition.name}: {details}")
    else:
        print(f"[SimulationController] Failed to fire {transition.name}: {details['reason']}")
    
    return success
```

#### 1.3 Fix Transition.type Property
```python
# In transition.py, change from:
self.type = 'stochastic'

# To:
self.transition_type = 'immediate'  # Match behavior_factory expectation
```

**Testing Phase 1:**
- Create net with immediate transitions
- Run simulation
- Verify behavior-based firing works
- Check token counts correct

---

### **Phase 2: Time-Based Behaviors** (Timed & Stochastic)

**Goal**: Add time awareness with locality-based scheduling

**Changes:**

#### 2.1 Add Per-Transition Time Tracking (Locality-Based)
```python
class SimulationController:
    def __init__(self, model):
        # ... existing code ...
        # Track enablement per transition (locality-specific)
        self.transition_states = {}  # {transition_id: TransitionState}

class TransitionState:
    """State for a single transition (locality-based)."""
    def __init__(self):
        self.enablement_time = None    # When this transition became enabled
        self.scheduled_time = None     # When this transition should fire (stochastic)
        self.last_fire_time = None     # When this transition last fired
```

#### 2.2 Update step() - Locality-Based Evaluation
```python
def step(self, time_step: float = 0.1) -> bool:
    """Execute one simulation step.
    
    Key: Each transition evaluated independently based on its locality.
    """
    # LOCALITY PRINCIPLE: Query each transition independently
    for transition in self.model.transitions:
        behavior = self._get_behavior(transition)
        
        # Check structural enablement (locality check)
        if self._is_locally_enabled(transition, behavior):
            # Track enablement time if newly enabled
            state = self._get_or_create_state(transition)
            if state.enablement_time is None:
                state.enablement_time = self.time
                
                # Let behavior initialize (e.g., stochastic samples delay)
                if hasattr(behavior, 'set_enablement_time'):
                    behavior.set_enablement_time(self.time)
        else:
            # Clear state if disabled
            self._clear_state(transition)
    
    # GLOBAL TIME: All transitions see same current time
    # LOCAL FREQUENCY: Each behavior decides if it fires NOW
    
    transitions_to_fire = []
    
    for transition in self.model.transitions:
        behavior = self._get_behavior(transition)
        can_fire, reason = behavior.can_fire()
        
        if can_fire:
            transitions_to_fire.append(transition)
    
    # Fire all enabled transitions (locality-based concurrency)
    fired_count = 0
    for transition in transitions_to_fire:
        if self._fire_transition(transition):
            fired_count += 1
    
    # GLOBAL TIME: Advance by time_step
    self.time += time_step
    self._notify_step_listeners()
    
    return fired_count > 0
```

#### 2.3 Locality Conflict Resolution
```python
def _check_locality_conflict(self, t1, t2) -> bool:
    """Check if two transitions have conflicting localities.
    
    Conflict exists if they share input places (both try to consume).
    
    Args:
        t1, t2: Transitions to check
        
    Returns:
        bool: True if localities conflict, False otherwise
    """
    t1_inputs = set(arc.source.id for arc in self.model.arcs if arc.target == t1)
    t2_inputs = set(arc.source.id for arc in self.model.arcs if arc.target == t2)
    
    # Conflict if shared input places
    return len(t1_inputs & t2_inputs) > 0

def _resolve_conflicts(self, enabled_transitions: List) -> List:
    """Resolve locality conflicts among enabled transitions.
    
    If transitions share input places, only one can fire.
    Strategy: Random selection (can be replaced with priority-based).
    
    Args:
        enabled_transitions: List of transitions that want to fire
        
    Returns:
        List of transitions that can fire without conflict
    """
    if len(enabled_transitions) <= 1:
        return enabled_transitions
    
    non_conflicting = []
    used_places = set()
    
    # Shuffle for fairness (random selection)
    import random
    candidates = list(enabled_transitions)
    random.shuffle(candidates)
    
    for transition in candidates:
        # Get input places (locality)
        input_places = set(arc.source.id for arc in self.model.arcs 
                          if arc.target == transition)
        
        # Check if any input place already used
        if not (input_places & used_places):
            non_conflicting.append(transition)
            used_places.update(input_places)
    
    return non_conflicting
```

#### 2.4 Updated step() with Conflict Resolution
```python
def step(self, time_step: float = 0.1) -> bool:
    """Execute one simulation step with locality-based conflict resolution."""
    
    # Update enablement states (locality-based)
    self._update_enablement_states()
    
    # Find all enabled transitions (LOCALITY: each checks its own state)
    enabled_transitions = []
    for transition in self.model.transitions:
        behavior = self._get_behavior(transition)
        can_fire, reason = behavior.can_fire()
        if can_fire:
            enabled_transitions.append(transition)
    
    # Resolve locality conflicts (shared input places)
    fireable = self._resolve_conflicts(enabled_transitions)
    
    # Fire all non-conflicting transitions
    # (They have independent localities, can fire concurrently)
    fired_count = 0
    for transition in fireable:
        if self._fire_transition(transition):
            fired_count += 1
    
    # GLOBAL TIME: Single time advancement
    self.time += time_step
    self._notify_step_listeners()
    
    return fired_count > 0
```

**Key Changes from Original Plan:**
- ❌ Removed type-based grouping (immediate/timed/stochastic groups)
- ✅ All transitions evaluated based on locality only
- ✅ Conflict resolution based on shared places, not types
- ✅ Multiple transitions can fire per step if localities independent

**Testing Phase 2:**
- Create net with mixed types (immediate + timed + stochastic)
- Verify transitions with independent localities fire concurrently
- Verify transitions with shared places conflict properly
- Check global time advances uniformly

---

### **Phase 3: Continuous Integration** (SHPN Support)

**Goal**: Add continuous transitions with locality-based parallel integration

**Changes:**

#### 3.1 Add Continuous Integration (Locality-Based)
```python
def _integrate_continuous_step(self, time_step: float):
    """Integrate all enabled continuous transitions.
    
    Key: Continuous transitions integrate in parallel if localities independent.
    """
    continuous_transitions = [t for t in self.model.transitions 
                             if t.transition_type == 'continuous']
    
    for transition in continuous_transitions:
        behavior = self._get_behavior(transition)
        
        # LOCALITY CHECK: Can this transition's locality support flow?
        can_flow, reason = behavior.can_fire()
        
        if can_flow:
            # Get locality (input/output arcs)
            input_arcs = behavior.get_input_arcs()
            output_arcs = behavior.get_output_arcs()
            
            # Integrate (RK4 step) - operates on transition's locality only
            success, details = behavior.integrate_step(
                dt=time_step,
                input_arcs=input_arcs,
                output_arcs=output_arcs
            )
            
            if success:
                print(f"[SimulationController] Integrated {transition.name}: flow={details.get('flow_rate', 0):.3f}")
```

#### 3.2 Updated step() - Discrete + Continuous
```python
def step(self, time_step: float = 0.1) -> bool:
    """Execute one simulation step.
    
    LOCALITY PRINCIPLE: 
    - Discrete transitions fire if locally enabled
    - Continuous transitions integrate if locally enabled
    - Both types coexist, evaluated independently
    
    GLOBAL TIME:
    - Single time advancement for all
    """
    
    # === DISCRETE TRANSITIONS ===
    # (immediate, timed, stochastic)
    
    # Update enablement states
    self._update_enablement_states()
    
    # Find enabled discrete transitions (locality check)
    discrete_transitions = [t for t in self.model.transitions 
                           if t.transition_type in ['immediate', 'timed', 'stochastic']]
    
    enabled_discrete = []
    for transition in discrete_transitions:
        behavior = self._get_behavior(transition)
        can_fire, reason = behavior.can_fire()
        if can_fire:
            enabled_discrete.append(transition)
    
    # Resolve locality conflicts
    fireable = self._resolve_conflicts(enabled_discrete)
    
    # Fire discrete transitions
    discrete_fired = 0
    for transition in fireable:
        if self._fire_transition(transition):
            discrete_fired += 1
    
    # === CONTINUOUS TRANSITIONS ===
    # (continuous - always integrate if enabled)
    
    self._integrate_continuous_step(time_step)
    
    # === GLOBAL TIME ADVANCEMENT ===
    self.time += time_step
    self._notify_step_listeners()
    
    return discrete_fired > 0 or self._has_continuous_flow()
```

#### 3.3 Continuous-Discrete Interaction
```python
def _has_continuous_flow(self) -> bool:
    """Check if any continuous transition had non-zero flow.
    
    Returns:
        bool: True if continuous activity occurred
    """
    continuous = [t for t in self.model.transitions 
                  if t.transition_type == 'continuous']
    
    for transition in continuous:
        behavior = self._get_behavior(transition)
        if behavior.can_fire()[0]:
            return True
    
    return False
```

**Key Principles Applied:**
- ✅ **Locality**: Discrete and continuous transitions evaluated independently
- ✅ **Global Time**: Same time_step for both discrete and continuous
- ✅ **Coexistence**: Types mix naturally without priority
- ✅ **Parallel Execution**: Continuous transitions integrate simultaneously

**Testing Phase 3:**
- Create hybrid net (discrete + continuous)
- Verify discrete firings don't break continuous flow
- Check continuous flow doesn't interfere with discrete enablement
- Test locality independence (continuous on one side, discrete on other)

---

### **Phase 4: Locality Optimization** (Performance)

**Goal**: Cache behavior instances and locality queries

**Changes:**

#### 4.1 Add Behavior Cache
```python
class SimulationController:
    def __init__(self, model):
        # ... existing code ...
        self.behavior_cache = {}  # {transition_id: behavior_instance}
```

#### 4.2 Cache Behaviors
```python
def _get_behavior(self, transition):
    """Get or create behavior for transition (cached).
    
    Args:
        transition: Transition object
        
    Returns:
        TransitionBehavior instance
    """
    if transition.id not in self.behavior_cache:
        from shypn.engine.behavior_factory import create_behavior
        self.behavior_cache[transition.id] = create_behavior(transition, self.model)
    
    return self.behavior_cache[transition.id]
```

#### 4.3 Update All Methods to Use Cache
```python
def _is_transition_enabled(self, transition) -> bool:
    behavior = self._get_behavior(transition)  # Use cache
    can_fire, reason = behavior.can_fire()
    return can_fire

def _fire_transition(self, transition):
    behavior = self._get_behavior(transition)  # Use cache
    # ... rest of logic ...
```

#### 4.4 Clear Cache on Model Changes
```python
def reset(self):
    # ... existing reset logic ...
    self.behavior_cache.clear()  # Invalidate cache
```

**Testing Phase 4:**
- Performance testing with large nets (100+ transitions)
- Verify cache hit rates
- Check memory usage

---

### **Phase 5: Formula Evaluation** (Guard/Rate Expressions)

**Goal**: Support dynamic guard and rate expressions

**Changes:**

#### 5.1 Add Expression Evaluator Utility
```python
# src/shypn/engine/expression_evaluator.py

import ast
import operator
import math

class ExpressionEvaluator:
    """Safe evaluator for guard/rate expressions."""
    
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        # ... more operators ...
    }
    
    SAFE_FUNCTIONS = {
        'min': min,
        'max': max,
        'abs': abs,
        'exp': math.exp,
        'log': math.log,
        'sin': math.sin,
        'cos': math.cos,
        # ... more functions ...
    }
    
    @staticmethod
    def evaluate(expression: str, context: Dict[str, Any]) -> Any:
        """Evaluate expression with runtime context.
        
        Args:
            expression: String expression like "P1 + P2 > 5"
            context: Dict with variables like {'P1': 3, 'P2': 7, 't': 1.5}
            
        Returns:
            Evaluated result
        """
        # Parse and evaluate safely (no exec/eval)
        # Use AST visitor pattern
        pass
```

#### 5.2 Integrate with Behaviors
```python
# In transition_behavior.py base class

def evaluate_guard(self, expression: str, context: Dict) -> bool:
    """Evaluate guard expression.
    
    Args:
        expression: Guard expression string
        context: Runtime context (place tokens, time, etc.)
        
    Returns:
        bool: True if guard passes
    """
    from shypn.engine.expression_evaluator import ExpressionEvaluator
    
    try:
        result = ExpressionEvaluator.evaluate(expression, context)
        return bool(result)
    except Exception as e:
        print(f"[Guard] Evaluation error: {e}")
        return False  # Guard fails on error
```

**Testing Phase 5:**
- Create transitions with guard expressions
- Test rate function evaluation
- Verify safety (no arbitrary code execution)

---

## Implementation Timeline

### Week 1: Phase 1 (Basic Integration)
- **Day 1-2**: Update controller methods
- **Day 3**: Fix transition.type property
- **Day 4-5**: Testing and bug fixes

### Week 2: Phase 2 (Time-Based)
- **Day 1-2**: Add time tracking
- **Day 3-4**: Implement independence algorithms
- **Day 5**: Testing

### Week 3: Phase 3 (Continuous)
- **Day 1-2**: Add integration methods
- **Day 3-4**: Test hybrid nets
- **Day 5**: Performance testing

### Week 4: Phase 4 (Optimization)
- **Day 1-2**: Implement caching
- **Day 3-4**: Performance testing
- **Day 5**: Profiling and tuning

### Week 5: Phase 5 (Formulas)
- **Day 1-3**: Expression evaluator
- **Day 4-5**: Integration and testing

---

## Risk Mitigation

### Risk 1: Breaking Existing Simulation
**Mitigation**: 
- Keep old methods as `_legacy_fire_transition()` 
- Add feature flag: `USE_BEHAVIOR_DISPATCH = True`
- Easy rollback if issues found

### Risk 2: Performance Degradation
**Mitigation**:
- Profile before/after each phase
- Implement caching early (Phase 4)
- Benchmark large nets (1000+ elements)

### Risk 3: Behavior Creation Overhead
**Mitigation**:
- Cache behavior instances per transition
- Reuse behaviors across steps
- Only recreate if model structure changes

### Risk 4: Time Tracking Complexity
**Mitigation**:
- Start simple (immediate only)
- Add time tracking incrementally
- Test each transition type in isolation

---

## Success Metrics

### Phase 1:
- ✅ All immediate transitions work via behaviors
- ✅ Token counts correct after firing
- ✅ No performance regression

### Phase 2:
- ✅ Timed transitions respect [earliest, latest] windows
- ✅ Stochastic transitions use exponential delays
- ✅ Race condition algorithm selects correct transition

### Phase 3:
- ✅ Continuous transitions integrate in parallel
- ✅ Hybrid nets (discrete + continuous) work
- ✅ RK4 integration produces smooth evolution

### Phase 4:
- ✅ 50%+ performance improvement via caching
- ✅ Memory usage acceptable (<100MB for 1000 transitions)

### Phase 5:
- ✅ Guard expressions block/allow firing
- ✅ Rate expressions affect continuous flow
- ✅ No security vulnerabilities (no arbitrary code execution)

---

## Testing Strategy

### Unit Tests:
```python
# tests/test_behavior_integration.py

def test_immediate_firing():
    """Test immediate transition fires via behavior."""
    model = create_test_model()
    controller = SimulationController(model)
    
    # Create immediate transition
    t1 = model.transitions[0]
    t1.transition_type = 'immediate'
    
    # Should fire immediately
    assert controller.step()
    assert t1 was_fired

def test_timed_window():
    """Test timed transition respects timing window."""
    # ... test code ...

def test_stochastic_race():
    """Test stochastic race condition."""
    # ... test code ...

def test_continuous_integration():
    """Test continuous parallel integration."""
    # ... test code ...
```

### Integration Tests:
- Run full simulation workflows
- Test mode palette integration
- Verify UI updates correctly

### Performance Tests:
- Benchmark large nets (100, 500, 1000 transitions)
- Profile memory usage
- Test long-running simulations

---

## Documentation Updates

### 1. Architecture Diagrams
- Update to show behavior dispatch
- Show independence algorithm flow

### 2. API Documentation
- Document controller methods
- Explain behavior factory usage
- Show examples for each transition type

### 3. User Guide
- How to set transition types
- How to write guard/rate expressions
- Troubleshooting guide

---

## Summary

**Current State**: 
- Behaviors fully implemented but not used
- Controller uses simple token transfer

**Target State**:
- Controller delegates to behaviors
- Full time/rate/locality/independence support
- Performance optimized with caching

**Approach**:
- Incremental integration (5 phases)
- Each phase independently testable
- Backward compatibility maintained

**Key OOP Principles**:
- SRP: Each class has single responsibility
- OCP: Extensible without modification
- LSP: Behaviors substitutable
- DIP: Depend on abstractions

**Estimated Time**: 5 weeks (25 working days)

**Priority**: Phase 1 (immediate integration) should be done first to validate the approach before proceeding to more complex phases.

---

**Document Created**: October 4, 2025  
**Status**: Ready for implementation - awaiting approval to proceed with Phase 1
