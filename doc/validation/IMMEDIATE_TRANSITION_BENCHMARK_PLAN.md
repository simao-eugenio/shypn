# Immediate Transition Benchmark Plan

**Date:** October 17, 2025  
**Purpose:** Systematic validation of immediate transition properties in Petri nets  
**Scope:** Benchmark and test all properties specific to immediate transitions

---

## Overview

This document outlines a comprehensive benchmarking plan for **immediate transitions**, the first transition type to be validated in the Petri net property validation framework.

### Transition Types in SHYpn

1. **Immediate** ← **Starting here**
2. Timed
3. Stochastic  
4. Continuous

---

## Immediate Transition Characteristics

### Definition
An **immediate transition** fires instantaneously (zero delay) when:
- Guard condition passes (if defined)
- All input places have sufficient tokens
- Highest priority among enabled immediate transitions

### Key Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `transition_type` | string | 'immediate' | Must be 'immediate' |
| `enabled` | boolean | True | Can transition fire? |
| `guard` | expression/None | None | Boolean condition for firing |
| `priority` | int | 0 | Conflict resolution (higher wins) |
| `firing_policy` | string | 'earliest' | 'earliest' or 'latest' |
| `is_source` | boolean | False | Generates tokens without input |
| `is_sink` | boolean | False | Consumes tokens without output |

**Note:** `rate` property is **ignored** for immediate transitions (fires instantly).

---

## Benchmark Model: P-T-P (Place-Transition-Place)

### Simple Model Structure

```
[P1] --[weight=1]--> [T1] --[weight=1]--> [P2]
```

**Components:**
- **P1** (input place) - Initial tokens: configurable
- **T1** (immediate transition) - Properties under test
- **P2** (output place) - Initial tokens: 0

### Why This Model?

- ✅ **Minimal complexity** - Isolates transition behavior
- ✅ **Clear inputs/outputs** - Easy to verify token flow
- ✅ **Single transition** - No interference from other transitions
- ✅ **Deterministic** - Predictable behavior for validation
- ✅ **Extensible** - Can add complexity (guards, priorities) incrementally

---

## Test Categories

### 1. Basic Firing Mechanism
Test immediate firing without guard or special properties.

### 2. Guard Function Evaluation
Test guard types: boolean, numeric, expression.

### 3. Priority Resolution
Test conflict resolution with multiple immediate transitions.

### 4. Arc Weight Interaction
Test token consumption/production with various weights.

### 5. Source/Sink Behavior
Test infinite token generation/consumption.

### 6. Persistence & Serialization
Test property persistence across save/load cycles.

### 7. Edge Cases
Test boundary conditions and error handling.

---

## Detailed Test Plan

### Category 1: Basic Firing Mechanism

#### Test 1.1: Single Fire (Zero Delay)
**Model:** P1(tokens=1) → T1(immediate) → P2(tokens=0)  
**Expected:**
- T1 fires immediately when simulation starts
- P1: 1 → 0 (consumes 1 token)
- P2: 0 → 1 (produces 1 token)
- Firing time: t=0

**Validation:**
```python
assert P1.tokens == 0
assert P2.tokens == 1
assert firing_time == 0.0
```

#### Test 1.2: Multiple Firings
**Model:** P1(tokens=5) → T1(immediate) → P2(tokens=0)  
**Expected:**
- T1 fires 5 times consecutively at t=0
- P1: 5 → 0
- P2: 0 → 5

**Validation:**
```python
assert P1.tokens == 0
assert P2.tokens == 5
assert len(firing_events) == 5
assert all(event.time == 0.0 for event in firing_events)
```

#### Test 1.3: Insufficient Tokens
**Model:** P1(tokens=0) → T1(immediate) → P2(tokens=0)  
**Expected:**
- T1 does **not** fire (no tokens available)
- P1: 0 → 0
- P2: 0 → 0

**Validation:**
```python
assert P1.tokens == 0
assert P2.tokens == 0
assert len(firing_events) == 0
```

---

### Category 2: Guard Function Evaluation

#### Test 2.1: Boolean Guard (True)
**Model:** P1(tokens=1) → T1(immediate, guard=True) → P2  
**Expected:**
- T1 fires (guard passes)
- P1: 1 → 0
- P2: 0 → 1

**Validation:**
```python
T1.guard = True
assert T1.can_fire() == True
assert P2.tokens == 1
```

#### Test 2.2: Boolean Guard (False)
**Model:** P1(tokens=1) → T1(immediate, guard=False) → P2  
**Expected:**
- T1 does **not** fire (guard blocks)
- P1: 1 → 1
- P2: 0 → 0

**Validation:**
```python
T1.guard = False
assert T1.can_fire() == False
assert P1.tokens == 1
assert P2.tokens == 0
```

#### Test 2.3: Numeric Guard (Threshold)
**Model:** P1(tokens=10) → T1(immediate, guard=5) → P2  
**Expected:**
- Guard evaluates as `5 > 0` → True
- T1 fires normally

**Validation:**
```python
T1.guard = 5  # Threshold > 0 passes
assert T1.can_fire() == True
```

#### Test 2.4: Expression Guard (Token-Based)
**Model:** P1(tokens=10) → T1(immediate, guard="P1 > 5") → P2  
**Expected:**
- Guard evaluates: `10 > 5` → True
- T1 fires

**Validation:**
```python
T1.guard = "P1 > 5"
P1.tokens = 10
assert T1.can_fire() == True

P1.tokens = 3
assert T1.can_fire() == False
```

#### Test 2.5: Complex Expression Guard
**Model:** P1(tokens=10) → T1(immediate, guard="P1 > 5 and P1 < 20") → P2  
**Expected:**
- Guard evaluates: `10 > 5 and 10 < 20` → True
- T1 fires

**Validation:**
```python
T1.guard = "P1 > 5 and P1 < 20"
P1.tokens = 10
assert T1.can_fire() == True

P1.tokens = 25
assert T1.can_fire() == False
```

#### Test 2.6: Guard with Time Dependency
**Model:** P1(tokens=1) → T1(immediate, guard="t > 5.0") → P2  
**Expected:**
- At t=0: Guard fails (0 > 5.0 → False)
- At t=6: Guard passes (6 > 5.0 → True)
- **Note:** Immediate transitions at t>0 is unusual but valid

**Validation:**
```python
T1.guard = "t > 5.0"
at time=0: assert T1.can_fire() == False
at time=6: assert T1.can_fire() == True
```

---

### Category 3: Priority Resolution

#### Test 3.1: Single Transition Priority
**Model:** P1(tokens=1) → T1(immediate, priority=5) → P2  
**Expected:**
- Priority has no effect (single transition)
- T1 fires normally

**Validation:**
```python
T1.priority = 5
assert T1.can_fire() == True
assert P2.tokens == 1
```

#### Test 3.2: Two Transitions, Different Priorities
**Model:**
```
        /--[T1(priority=10)]-->[P2]
P1(tokens=1)
        \--[T2(priority=5)]--->[P3]
```
**Expected:**
- Only **T1** fires (higher priority)
- P1: 1 → 0
- P2: 0 → 1
- P3: 0 → 0

**Validation:**
```python
assert T1.priority > T2.priority
assert P2.tokens == 1
assert P3.tokens == 0
```

#### Test 3.3: Equal Priority (Non-Deterministic)
**Model:**
```
        /--[T1(priority=5)]-->[P2]
P1(tokens=1)
        \--[T2(priority=5)]--->[P3]
```
**Expected:**
- **Either** T1 or T2 fires (not both)
- P1: 1 → 0
- P2: 1 XOR P3: 1 (one of them)

**Validation:**
```python
assert P1.tokens == 0
assert (P2.tokens == 1) != (P3.tokens == 1)  # XOR
```

---

### Category 4: Arc Weight Interaction

#### Test 4.1: Input Arc Weight > 1
**Model:** P1(tokens=5) --[weight=3]--> T1(immediate) → P2  
**Expected:**
- T1 requires 3 tokens to fire
- Fires once: P1: 5 → 2, P2: 0 → 1
- Cannot fire again (2 < 3)

**Validation:**
```python
input_arc.weight = 3
assert P1.tokens == 2
assert P2.tokens == 1
assert T1.can_fire() == False
```

#### Test 4.2: Output Arc Weight > 1
**Model:** P1(tokens=1) → T1(immediate) --[weight=5]--> P2  
**Expected:**
- T1 consumes 1 token, produces 5 tokens
- P1: 1 → 0
- P2: 0 → 5

**Validation:**
```python
output_arc.weight = 5
assert P1.tokens == 0
assert P2.tokens == 5
```

#### Test 4.3: Both Weights > 1
**Model:** P1(tokens=10) --[weight=3]--> T1 --[weight=2]--> P2  
**Expected:**
- Each firing: P1 -3, P2 +2
- Fires 3 times: P1: 10 → 1, P2: 0 → 6

**Validation:**
```python
input_arc.weight = 3
output_arc.weight = 2
assert P1.tokens == 1  # 10 - 3*3 = 1
assert P2.tokens == 6  # 0 + 3*2 = 6
```

#### Test 4.4: Numeric Expression Weight
**Model:** P1(tokens=10) --[weight="2*2"]--> T1 → P2  
**Expected:**
- Weight evaluates to 4
- Each firing: P1 -4, P2 +1
- Fires 2 times: P1: 10 → 2

**Validation:**
```python
input_arc.weight = "2*2"  # Evaluates to 4
assert P1.tokens == 2
assert P2.tokens == 2
```

#### Test 4.5: Function Expression Weight
**Model:** P1(tokens=10) --[weight="min(P1, 3)"]--> T1 → P2  
**Expected:**
- First fire: weight=min(10,3)=3, P1: 10→7
- Second fire: weight=min(7,3)=3, P1: 7→4
- Third fire: weight=min(4,3)=3, P1: 4→1

**Validation:**
```python
input_arc.weight = "min(P1, 3)"
# Run simulation
assert P1.tokens == 1
assert P2.tokens == 3
```

---

### Category 5: Source/Sink Behavior

#### Test 5.1: Source Transition (No Input)
**Model:** [T1(immediate, is_source=True)] → P2  
**Expected:**
- T1 fires even without input place
- P2 receives tokens from "nowhere"
- Fires once per simulation step

**Validation:**
```python
T1.is_source = True
# No input arcs
assert len(T1.input_arcs) == 0
assert T1.can_fire() == True
assert P2.tokens > 0
```

#### Test 5.2: Sink Transition (No Output)
**Model:** P1 → [T1(immediate, is_sink=True)]  
**Expected:**
- T1 consumes tokens without producing any
- P1 tokens decrease
- No output place needed

**Validation:**
```python
T1.is_sink = True
P1.tokens = 10
# No output arcs
assert len(T1.output_arcs) == 0
assert T1.can_fire() == True
# After firing
assert P1.tokens == 9  # Token consumed
```

#### Test 5.3: Source + Sink (Passthrough)
**Model:** [T1(immediate, is_source=True, is_sink=True)]  
**Expected:**
- T1 fires without input or output
- Infinite firing (needs termination condition)

**Validation:**
```python
T1.is_source = True
T1.is_sink = True
assert len(T1.input_arcs) == 0
assert len(T1.output_arcs) == 0
assert T1.can_fire() == True
# Requires max_firings limit to prevent infinite loop
```

---

### Category 6: Persistence & Serialization

#### Test 6.1: Save/Load Basic Properties
**Model:** P1 → T1(immediate, priority=10) → P2  
**Actions:**
1. Set T1.priority = 10
2. Save model to file
3. Close application
4. Reload model from file
**Expected:**
- T1.transition_type == 'immediate'
- T1.priority == 10

**Validation:**
```python
# After reload
assert T1.transition_type == 'immediate'
assert T1.priority == 10
assert T1.rate == 1.0  # Default
```

#### Test 6.2: Save/Load Guard Function
**Model:** P1 → T1(immediate, guard="P1 > 5") → P2  
**Actions:**
1. Set T1.guard = "P1 > 5"
2. Save model
3. Reload model
**Expected:**
- T1.guard == "P1 > 5" (string preserved)
- Guard evaluation still works

**Validation:**
```python
# After reload
assert T1.guard == "P1 > 5"
P1.tokens = 10
assert T1.can_fire() == True
```

#### Test 6.3: Save/Load Properties Dict
**Model:** T1 with custom properties  
**Actions:**
1. Set T1.properties = {'guard_function': 'P1 > 0', 'custom': 'value'}
2. Save model
3. Reload model
**Expected:**
- T1.properties dict preserved
- All custom keys/values intact

**Validation:**
```python
# After reload
assert 'guard_function' in T1.properties
assert T1.properties['guard_function'] == 'P1 > 0'
assert T1.properties['custom'] == 'value'
```

---

### Category 7: Edge Cases

#### Test 7.1: Enabled Flag (Disabled Transition)
**Model:** P1(tokens=1) → T1(immediate, enabled=False) → P2  
**Expected:**
- T1 does **not** fire (disabled)
- Tokens remain in P1

**Validation:**
```python
T1.enabled = False
assert T1.can_fire() == False
assert P1.tokens == 1
assert P2.tokens == 0
```

#### Test 7.2: Invalid Guard Expression
**Model:** T1(immediate, guard="invalid syntax !")  
**Expected:**
- Guard evaluation fails
- T1 does **not** fire (fail-safe)

**Validation:**
```python
T1.guard = "invalid syntax !"
# Should not crash
passes, reason = T1._evaluate_guard()
assert passes == False
assert "error" in reason.lower()
```

#### Test 7.3: Negative Priority
**Model:** T1(immediate, priority=-5)  
**Expected:**
- Valid (lower than default 0)
- Works normally but loses conflicts

**Validation:**
```python
T1.priority = -5
assert T1.can_fire() == True
# In conflict with T2(priority=0), T2 wins
```

#### Test 7.4: Very Large Token Count
**Model:** P1(tokens=1000000) → T1(immediate) → P2  
**Expected:**
- T1 fires 1M times
- No overflow or performance issues

**Validation:**
```python
P1.tokens = 1000000
# Run simulation
assert P1.tokens == 0
assert P2.tokens == 1000000
assert simulation_time < 10.0  # Performance check
```

#### Test 7.5: Firing Policy (Earliest vs Latest)
**Model:** P1 → T1(immediate, firing_policy='latest') → P2  
**Expected:**
- For immediate transitions, policy typically has no effect
- Document expected behavior

**Validation:**
```python
T1.firing_policy = 'latest'
# Behavior should be same as 'earliest' for immediate
assert T1.can_fire() == True
```

---

## Implementation Plan

### Phase 1: Test Infrastructure (Week 1)
- [ ] Create `tests/validation/` directory
- [ ] Implement P-T-P model generator
- [ ] Create assertion framework for token validation
- [ ] Set up test harness with pytest

### Phase 2: Basic Tests (Week 1)
- [ ] Implement Category 1 tests (basic firing)
- [ ] Implement Category 2 tests (guards)
- [ ] Document any failures or unexpected behaviors

### Phase 3: Advanced Tests (Week 2)
- [ ] Implement Category 3 tests (priority)
- [ ] Implement Category 4 tests (arc weights)
- [ ] Implement Category 5 tests (source/sink)

### Phase 4: Integration Tests (Week 2)
- [ ] Implement Category 6 tests (persistence)
- [ ] Implement Category 7 tests (edge cases)
- [ ] Performance benchmarking

### Phase 5: Documentation & Reporting (Week 3)
- [ ] Generate test coverage report
- [ ] Document all findings
- [ ] Create validation summary
- [ ] Update user documentation

---

## Success Criteria

### Code Coverage
- ✅ 100% coverage of immediate transition properties
- ✅ All guard types tested
- ✅ All arc weight scenarios tested
- ✅ Source/sink behaviors validated

### Test Results
- ✅ All basic tests pass
- ✅ All edge cases handled gracefully
- ✅ No crashes or undefined behavior
- ✅ Performance within acceptable limits

### Documentation
- ✅ All test cases documented
- ✅ Expected behaviors clearly defined
- ✅ Edge cases and limitations noted
- ✅ User guide updated

---

## Next Steps

After completing immediate transition validation:

1. **Timed Transitions** - Add delay/timeout properties
2. **Stochastic Transitions** - Add exponential distribution
3. **Continuous Transitions** - Add rate functions, ODEs
4. **Cross-Type Interactions** - Mixed transition types in one model

---

## Related Documentation

- `/doc/GUARD_FUNCTION_GUIDE.md` - Guard implementation details
- `/doc/DEFAULT_VALUES_FIX.md` - Default property values
- `/doc/GUARD_RATE_PERSISTENCE_FIX.md` - Persistence implementation
- `/doc/behaviors/README.md` - Transition behaviors overview

---

## Summary

This benchmark plan provides a **systematic, comprehensive approach** to validating immediate transitions:

✅ **Simple P-T-P model** - Clear, isolated testing  
✅ **7 test categories** - Complete coverage  
✅ **40+ test cases** - Thorough validation  
✅ **Incremental implementation** - Manageable workload  
✅ **Clear success criteria** - Measurable outcomes  

**Immediate transitions are the foundation** - validating them thoroughly ensures the entire simulation framework is solid! 🎯
