# Phase 4: Continuous Integration - Implementation Documentation

## Overview

Phase 4 implements hybrid execution that combines discrete and continuous Petri net transitions in a single simulation. This allows modeling systems with both instantaneous events (discrete) and continuous flow processes (continuous).

## Architecture

### Hybrid Execution Model

The simulation controller executes a **hybrid step** that interleaves discrete and continuous behaviors:

```
┌─────────────────────────────────────────────┐
│         Simulation Step (dt = 0.1)          │
├─────────────────────────────────────────────┤
│                                             │
│  1. Update Enablement States                │
│     - Track discrete transition states      │
│                                             │
│  2. Identify Continuous Transitions         │
│     - Check enablement BEFORE state changes │
│     - Snapshot continuous flows             │
│                                             │
│  3. Execute Discrete Transition             │
│     - Fire ONE discrete transition          │
│     - Apply conflict resolution             │
│     - Instantaneous token change            │
│                                             │
│  4. Integrate Continuous Transitions        │
│     - Execute ALL pre-identified flows      │
│     - Use RK4 integration (dt)              │
│     - Parallel independent flows            │
│                                             │
│  5. Advance Time: t += dt                   │
│                                             │
└─────────────────────────────────────────────┘
```

### Key Design Decision: Continuous Enablement Snapshot

**Critical**: Continuous transitions are identified **before** discrete transitions fire. This ensures:

1. **Consistency**: Continuous integration is based on the state at the beginning of the step
2. **Locality Independence**: Discrete and continuous transitions in separate localities don't interfere
3. **Predictability**: Continuous flow doesn't react to mid-step discrete changes

### Transition Type Separation

```python
# Discrete transitions: fire one per step
discrete_transitions = ['immediate', 'timed', 'stochastic']

# Continuous transitions: integrate all in parallel
continuous_transitions = ['continuous']
```

## Implementation Details

### Step Method Structure

```python
def step(self, time_step: float = 0.1) -> bool:
    """Hybrid discrete + continuous execution."""
    
    # Phase 1: Update state tracking
    self._update_enablement_states()
    
    # Phase 2: Identify continuous transitions (BEFORE discrete changes)
    continuous_to_integrate = []
    for transition in continuous_transitions:
        behavior = self._get_behavior(transition)
        can_flow, reason = behavior.can_fire()
        if can_flow:
            # Snapshot arcs for integration
            input_arcs = behavior.get_input_arcs()
            output_arcs = behavior.get_output_arcs()
            continuous_to_integrate.append((transition, behavior, input_arcs, output_arcs))
    
    # Phase 3: Execute discrete transitions (one fires)
    enabled_discrete = [t for t in discrete_transitions 
                       if self._is_transition_enabled(t)]
    if enabled_discrete:
        transition = self._select_transition(enabled_discrete)  # Conflict resolution
        self._fire_transition(transition)
        discrete_fired = True
    
    # Phase 4: Integrate continuous transitions (all pre-identified)
    for transition, behavior, input_arcs, output_arcs in continuous_to_integrate:
        success, details = behavior.integrate_step(
            dt=time_step,
            input_arcs=input_arcs,
            output_arcs=output_arcs
        )
    
    # Phase 5: Advance time
    self.time += time_step
    
    return discrete_fired or continuous_active > 0
```

### Continuous Behavior Integration

Continuous transitions use **RK4 (Runge-Kutta 4th order)** numerical integration:

```python
# From ContinuousBehavior.integrate_step()
def integrate_step(self, dt, input_arcs, output_arcs):
    """Integrate continuous flow over time step dt."""
    
    # Evaluate rate at current state
    rate = self._evaluate_rate(input_arcs, output_arcs)
    
    # RK4 integration
    k1 = rate * dt
    # ... (RK4 intermediate steps)
    
    # Update tokens
    for arc in input_arcs:
        place.tokens -= flow_amount
    for arc in output_arcs:
        place.tokens += flow_amount
    
    return True, {'rate': rate, 'flow': flow_amount}
```

## Test Coverage

### Test Suite: `tests/test_phase4_continuous.py`

**5 comprehensive tests** covering all hybrid execution scenarios:

#### 1. **test_continuous_integration**
- **Purpose**: Verify basic continuous flow integration
- **Setup**: P1(10) → T1(continuous, rate=2.0) → P2(0)
- **Execution**: 3 steps @ dt=0.1
- **Validation**:
  - Token transfer: 0.2 tokens per step (rate × dt = 2.0 × 0.1)
  - Conservation: P1 + P2 = 10.0 (constant)
  - Flow accuracy: ±0.01 tolerance

#### 2. **test_hybrid_discrete_continuous**
- **Purpose**: Verify discrete and continuous coexistence
- **Setup**: 
  - P1(5) → T1(immediate) → P2(0)
  - P2 → T2(continuous, rate=1.0) → P3(0)
- **Execution**: 12 steps
- **Validation**:
  - T1 fires discretely (1 token at a time)
  - T2 flows continuously ONLY when P2 has tokens
  - First step: T1 fires but T2 doesn't (P2 empty at step start)
  - Subsequent steps: Both T1 and T2 can execute

#### 3. **test_parallel_locality_independence**
- **Purpose**: Verify parallel paths don't interfere
- **Setup**:
  - Discrete path: P1(5) → T1(immediate) → P2(0)
  - Continuous path: P3(10.0) → T2(continuous, rate=2.0) → P4(0.0)
- **Execution**: 5 steps
- **Validation**:
  - Discrete: P1 depletes, P2 accumulates (5 firings)
  - Continuous: P3 flows to P4 (1.0 tokens transferred)
  - Independence: Both execute simultaneously
  - Conservation: Each path maintains total

#### 4. **test_continuous_depletion**
- **Purpose**: Verify continuous transition stops when source depletes
- **Setup**: P1(10.0) → T1(continuous, rate=2.0) → P2(0.0)
- **Execution**: 50 steps @ dt=0.1 (total time = 5.0)
- **Validation**:
  - P1 depletes exactly at t=5.0 (10.0 ÷ 2.0 = 5.0s)
  - T1 stops flowing when P1 reaches 0
  - Final: P1=0.000, P2=10.000
  - Conservation throughout

#### 5. **test_continuous_rate_function**
- **Purpose**: Verify rate function evaluation mechanism
- **Setup**: P1(10.0) → T1(continuous, rate_function='2.0') → P2(0.0)
- **Execution**: 1 step @ dt=0.1
- **Validation**:
  - Rate correctly evaluated: 2.0
  - Transfer amount: rate × dt = 0.2
  - Rate function access working

## Results

### Test Execution Summary

```
======================================================================
PHASE 4: CONTINUOUS INTEGRATION TEST SUITE
======================================================================

test_continuous_integration              ✓ PASSED
test_hybrid_discrete_continuous          ✓ PASSED
test_parallel_locality_independence      ✓ PASSED
test_continuous_depletion                ✓ PASSED
test_continuous_rate_function            ✓ PASSED

======================================================================
RESULTS: 5 passed, 0 failed out of 5 tests
======================================================================
✓ ALL TESTS PASSED!
```

### Backward Compatibility

All previous phase tests remain passing:

- **Phase 1: Behavior Integration** - 7/7 tests ✓
- **Phase 2: Conflict Resolution** - 7/7 tests ✓
- **Phase 3: Time-Aware Behaviors** - 6/6 tests ✓
- **Phase 4: Continuous Integration** - 5/5 tests ✓

**Total: 25/25 tests passing**

## Technical Achievements

### 1. Hybrid Execution Semantics

Successfully implemented the **hybrid Petri net semantics** where:
- **Discrete transitions** fire atomically (instantaneous token changes)
- **Continuous transitions** integrate smoothly (continuous token flow)
- Both types coexist without interference

### 2. Locality Independence

The implementation correctly handles **parallel localities**:
- Independent paths execute simultaneously
- No cross-contamination between discrete and continuous paths
- Token conservation maintained in each locality

### 3. Numerical Stability

Continuous integration uses **RK4** for numerical accuracy:
- 4th-order accuracy in time step
- Stable integration even with varying rates
- Exact token conservation (within floating-point precision)

### 4. Enablement Snapshot Design

The **snapshot before execution** design ensures:
- Continuous transitions don't react to mid-step changes
- Predictable behavior (no race conditions)
- Clean separation between discrete and continuous execution

## Performance Considerations

### Time Complexity

- **Per step**: O(T_d + T_c)
  - T_d = number of discrete transitions (one selected)
  - T_c = number of continuous transitions (all integrate)

### Numerical Integration Cost

- **RK4**: 4 evaluations per continuous transition
- **Total**: 4 × T_c rate evaluations per step

### Optimization Opportunities

1. **Parallel Integration**: Continuous transitions are independent → can parallelize
2. **Adaptive Stepping**: Could vary dt based on rate magnitudes
3. **Caching**: Rate functions could be cached between evaluations

## Design Rationale

### Why Snapshot Continuous Enablement?

**Alternative considered**: Check continuous enablement AFTER discrete firing

**Rejected because**:
- Creates race conditions (continuous reacts to discrete mid-step)
- Violates locality principle (coupled execution)
- Makes behavior order-dependent (non-deterministic)

**Chosen approach**: Snapshot BEFORE discrete execution

**Advantages**:
- Consistent with mathematical definition of hybrid Petri nets
- Clean separation of concerns
- Predictable and testable behavior

### Why RK4 Integration?

**Alternatives**: Euler, RK2, adaptive methods

**RK4 chosen because**:
- Good balance of accuracy vs. cost (4th order, 4 evaluations)
- Stable for most practical systems
- Well-understood and widely used
- Exact for constant rates (typical case)

## Usage Example

```python
from shypn.engine.simulation.controller import SimulationController

# Create hybrid net (discrete + continuous)
model = create_hybrid_petri_net()

# Initialize controller
controller = SimulationController(model)

# Run simulation
for i in range(100):
    success = controller.step(time_step=0.1)
    if not success:
        print("Simulation deadlocked or completed")
        break
    
    print(f"Step {i}: time={controller.time:.2f}")
    print(f"  Places: {[p.tokens for p in model.places]}")
```

## Future Enhancements

### Potential Phase 5+

1. **Adaptive Time Stepping**: Vary dt based on system dynamics
2. **Higher-Order Integration**: RK5, RK8 for higher accuracy
3. **Stiff Systems**: Implicit methods for stiff ODEs
4. **Parallel Execution**: GPU acceleration for large continuous systems
5. **Hybrid Events**: Discrete events triggered by continuous thresholds

## Conclusion

Phase 4 successfully implements **hybrid discrete-continuous Petri net simulation** with:

✓ Clean separation of discrete and continuous execution  
✓ Correct locality independence semantics  
✓ Numerical stability (RK4 integration)  
✓ Comprehensive test coverage (5/5 tests)  
✓ Full backward compatibility (25/25 total tests)  
✓ Production-ready implementation  

The hybrid execution model provides a solid foundation for modeling complex systems with both discrete events and continuous processes.
