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

### 2. Guard Function Evaluation ⭐ ENHANCED
Test guard types: boolean, numeric, expression, **complex boolean functions (math, numpy, lambda)**.

### 3. Priority Resolution
Test conflict resolution with multiple immediate transitions.

### 4. Arc Weight Interaction ⭐ ENHANCED
Test token consumption/production with various weights, **complex threshold functions (math, numpy, lambda)**.

### 5. Source/Sink Behavior
Test infinite token generation/consumption.

### 6. Persistence & Serialization
Test property persistence across save/load cycles.

### 7. Rate Expression Evaluation
Test all rate expression types: numeric, string, function, lambda, dictionary forms.

### 7. Rate Expression Evaluation ⭐ **NEW**
Test all rate expression types: numeric, string, function, lambda, dictionary forms.

### 8. Edge Cases
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

**Note:** Guards are boolean variables/expressions that must evaluate to True/False. They can be simple booleans or complex functions using math, numpy, or custom logic.

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

#### Test 2.5: Complex Expression Guard (Logical AND/OR)
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

#### Test 2.7: Complex Boolean Function (Math) ⭐ NEW
**Model:** P1(tokens=10) → T1(guard="math.sqrt(P1) > 3.0") → P2  
**Expected:**
- Guard uses math library function
- Evaluates: `sqrt(10) ≈ 3.16 > 3.0` → True
- Returns boolean value

**Validation:**
```python
import math
T1.guard = "math.sqrt(P1) > 3.0"
P1.tokens = 10
assert T1.can_fire() == True  # sqrt(10) > 3.0

P1.tokens = 4
assert T1.can_fire() == False  # sqrt(4) = 2.0 < 3.0
```

#### Test 2.8: Complex Boolean Function (Multi-Place) ⭐ NEW
**Model:** P1(10), P2(5) → T1(guard="(P1 + P2) / 2 > 7") → P3  
**Expected:**
- Guard evaluates multi-place expression
- Returns: `(10 + 5) / 2 = 7.5 > 7` → True

**Validation:**
```python
T1.guard = "(P1 + P2) / 2 > 7"
P1.tokens = 10
P2.tokens = 5
assert T1.can_fire() == True  # 7.5 > 7

P1.tokens = 5
P2.tokens = 5
assert T1.can_fire() == False  # 5.0 < 7
```

#### Test 2.9: Complex Boolean Function (Numpy) ⭐ NEW
**Model:** P1(tokens=100) → T1(guard="np.log10(P1) >= 2.0") → P2  
**Expected:**
- Guard uses numpy function
- Evaluates: `log10(100) = 2.0 >= 2.0` → True
- Returns boolean

**Validation:**
```python
import numpy as np
T1.guard = "np.log10(P1) >= 2.0"
P1.tokens = 100
assert T1.can_fire() == True  # log10(100) = 2.0

P1.tokens = 50
assert T1.can_fire() == False  # log10(50) ≈ 1.7 < 2.0
```

#### Test 2.10: Complex Boolean Function (Conditional) ⭐ NEW
**Model:** P1(10), P2(20) → T1(guard="P1 > 5 if t > 0 else P2 > 15") → P3  
**Expected:**
- Guard with nested conditional
- Returns boolean based on time

**Validation:**
```python
T1.guard = "P1 > 5 if t > 0 else P2 > 15"
P1.tokens = 10
P2.tokens = 20

at time=0: assert T1.can_fire() == True   # P2 > 15
at time=1: assert T1.can_fire() == True   # P1 > 5
```

#### Test 2.11: Complex Boolean Function (Lambda) ⭐ NEW
**Model:** P1(10) → T1(guard=lambda m, t: m['P1'] % 2 == 0) → P2  
**Expected:**
- Guard as lambda function returning boolean
- Checks if P1 tokens are even

**Validation:**
```python
T1.guard = lambda m, t: m['P1'] % 2 == 0
P1.tokens = 10
assert T1.can_fire() == True   # 10 is even

P1.tokens = 11
assert T1.can_fire() == False  # 11 is odd
```

#### Test 2.12: Complex Boolean Function (Trigonometric) ⭐ NEW
**Model:** P1(10) → T1(guard="math.sin(t) > 0.5") → P2  
**Expected:**
- Guard uses trigonometric function
- Returns boolean based on sine wave

**Validation:**
```python
import math
T1.guard = "math.sin(t) > 0.5"

at time=math.pi/6:  assert T1.can_fire() == False  # sin(π/6) = 0.5
at time=math.pi/3:  assert T1.can_fire() == True   # sin(π/3) ≈ 0.87
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

**Note:** Arc weights can be numeric constants or complex evaluation functions (math, numpy) that return numeric threshold values for token consumption/production.

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

#### Test 4.6: Complex Math Weight (sqrt) ⭐ NEW
**Model:** P1(tokens=100) --[weight="int(math.sqrt(P1))"]--> T1 → P2  
**Expected:**
- Weight uses math function returning numeric threshold
- First fire: weight=int(sqrt(100))=10, P1: 100→90
- Dynamic weight changes with P1 value

**Validation:**
```python
import math
input_arc.weight = "int(math.sqrt(P1))"
P1.tokens = 100

# First firing: sqrt(100) = 10
# Should consume 10 tokens
after_first_fire = 90
assert P1.tokens == after_first_fire
```

#### Test 4.7: Complex Math Weight (ceiling) ⭐ NEW
**Model:** P1(tokens=15) --[weight="math.ceil(P1 / 3)"]--> T1 → P2  
**Expected:**
- Weight evaluates to ceiling division
- First fire: weight=ceil(15/3)=5, P1: 15→10

**Validation:**
```python
import math
input_arc.weight = "math.ceil(P1 / 3)"
P1.tokens = 15

# ceil(15/3) = 5
assert P1.tokens == 10  # After first fire
```

#### Test 4.8: Complex Numpy Weight (log) ⭐ NEW
**Model:** P1(tokens=1000) --[weight="int(np.log10(P1))"]--> T1 → P2  
**Expected:**
- Weight uses numpy logarithm
- First fire: weight=int(log10(1000))=3

**Validation:**
```python
import numpy as np
input_arc.weight = "int(np.log10(P1))"
P1.tokens = 1000

# log10(1000) = 3
assert P1.tokens == 997  # After first fire
```

#### Test 4.9: Complex Weight (Max/Min) ⭐ NEW
**Model:** P1(20), P2(10) --[weight="max(1, min(P1/10, 5))"]--> T1 → P3  
**Expected:**
- Weight uses nested min/max functions
- Returns threshold value between 1 and 5

**Validation:**
```python
input_arc.weight = "max(1, min(P1/10, 5))"
P1.tokens = 20

# min(20/10, 5) = min(2, 5) = 2
# max(1, 2) = 2
# Should consume 2 tokens
assert P1.tokens == 18  # After first fire
```

#### Test 4.10: Complex Weight (Conditional Threshold) ⭐ NEW
**Model:** P1(tokens=50) --[weight="2 if P1 > 30 else 1"]--> T1 → P2  
**Expected:**
- Weight changes based on condition
- Returns numeric threshold value

**Validation:**
```python
input_arc.weight = "2 if P1 > 30 else 1"
P1.tokens = 50

# P1 > 30, so weight = 2
assert P1.tokens == 48  # After first fire

# Continue until P1 <= 30
# Then weight becomes 1
```

#### Test 4.11: Complex Weight (Trigonometric) ⭐ NEW
**Model:** P1(tokens=10) --[weight="max(1, int(3 * math.sin(t) + 2))"]--> T1 → P2  
**Expected:**
- Weight varies with time using trig function
- Returns numeric threshold (always >= 1)

**Validation:**
```python
import math
input_arc.weight = "max(1, int(3 * math.sin(t) + 2))"

# At different times, weight varies
at time=0: weight = max(1, int(3*0 + 2)) = 2
at time=pi/2: weight = max(1, int(3*1 + 2)) = 5
```

#### Test 4.12: Complex Weight (Lambda Threshold) ⭐ NEW
**Model:** P1(tokens=100) --[weight=lambda m, t: int(m['P1'] * 0.1)]--> T1 → P2  
**Expected:**
- Weight as lambda returning numeric value
- Returns 10% of P1 tokens as threshold

**Validation:**
```python
input_arc.weight = lambda m, t: int(m['P1'] * 0.1)
P1.tokens = 100

# weight = int(100 * 0.1) = 10
assert P1.tokens == 90  # After first fire
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

### Category 7: Rate Expression Evaluation

**Note:** While immediate transitions ignore `rate` for firing delay (fire instantly), the rate expression evaluation mechanism needs comprehensive testing for use in other transition types.

#### Test 7.1: Numeric Rate (Constant)
**Model:** P1(tokens=1) → T1(immediate, rate=1.5) → P2  
**Expected:**
- Rate property accepts numeric value
- Expression evaluates correctly
- No errors during simulation

**Validation:**
```python
T1.rate = 1.5
assert T1.rate == 1.5
assert isinstance(T1.rate, (int, float))
```

#### Test 7.2: Numeric Rate (Dictionary Form)
**Model:** P1 → T1(immediate, rate={'rate': 2.5}) → P2  
**Expected:**
- Rate accepts dictionary with 'rate' key
- Numeric value extracted correctly

**Validation:**
```python
T1.rate = {'rate': 2.5}
assert T1.rate['rate'] == 2.5
```

#### Test 7.3: Expression Rate (String - Simple)
**Model:** P1 → T1(immediate, rate="2 * 3.14") → P2  
**Expected:**
- String expression parsed correctly
- Evaluates to 6.28

**Validation:**
```python
T1.rate = "2 * 3.14"
evaluated = eval_rate_expression(T1.rate, {}, 0)
assert abs(evaluated - 6.28) < 0.01
```

#### Test 7.4: Expression Rate (String - Place-Dependent)
**Model:** P1(tokens=10) → T1(immediate, rate="P1 * 0.5") → P2  
**Expected:**
- Expression references place tokens
- Evaluates to 5.0 when P1=10

**Validation:**
```python
T1.rate = "P1 * 0.5"
P1.tokens = 10
evaluated = eval_rate_expression(T1.rate, {'P1': 10}, 0)
assert evaluated == 5.0
```

#### Test 7.5: Expression Rate (String - Time-Dependent)
**Model:** P1 → T1(immediate, rate="t * 2.0") → P2  
**Expected:**
- Expression references simulation time
- Evaluates correctly at different times

**Validation:**
```python
T1.rate = "t * 2.0"
evaluated_t0 = eval_rate_expression(T1.rate, {}, 0.0)
evaluated_t5 = eval_rate_expression(T1.rate, {}, 5.0)
assert evaluated_t0 == 0.0
assert evaluated_t5 == 10.0
```

#### Test 7.6: Function Rate (Built-in - min/max)
**Model:** P1(tokens=10) → T1(immediate, rate="min(P1, 5)") → P2  
**Expected:**
- Built-in function evaluates correctly
- Result is 5 when P1=10

**Validation:**
```python
T1.rate = "min(P1, 5)"
P1.tokens = 10
evaluated = eval_rate_expression(T1.rate, {'P1': 10}, 0)
assert evaluated == 5
```

#### Test 7.7: Function Rate (Multi-Place)
**Model:** P1(10), P2(20) → T1(rate="max(P1, P2) / 2") → P3  
**Expected:**
- Expression uses multiple places
- Evaluates to 10.0 (max(10,20)/2)

**Validation:**
```python
T1.rate = "max(P1, P2) / 2"
evaluated = eval_rate_expression(T1.rate, {'P1': 10, 'P2': 20}, 0)
assert evaluated == 10.0
```

#### Test 7.8: Function Rate (Mathematical - exp)
**Model:** P1 → T1(immediate, rate="exp(-t/10)") → P2  
**Expected:**
- Exponential function evaluates correctly
- Decays over time

**Validation:**
```python
import math
T1.rate = "exp(-t/10)"
evaluated_t0 = eval_rate_expression(T1.rate, {}, 0.0)
evaluated_t10 = eval_rate_expression(T1.rate, {}, 10.0)
assert abs(evaluated_t0 - 1.0) < 0.01
assert abs(evaluated_t10 - math.exp(-1)) < 0.01
```

#### Test 7.9: Complex Expression (Conditional)
**Model:** P1(tokens=15) → T1(rate="P1 * 0.5 if P1 > 10 else 0.1") → P2  
**Expected:**
- Conditional expression evaluates correctly
- Returns 7.5 when P1=15

**Validation:**
```python
T1.rate = "P1 * 0.5 if P1 > 10 else 0.1"
evaluated_high = eval_rate_expression(T1.rate, {'P1': 15}, 0)
evaluated_low = eval_rate_expression(T1.rate, {'P1': 5}, 0)
assert evaluated_high == 7.5
assert evaluated_low == 0.1
```

#### Test 7.10: Complex Expression (Multi-Variable)
**Model:** P1(10), P2(5) → T1(rate="(P1 + P2) / (P1 * P2 + 1)") → P3  
**Expected:**
- Multi-variable expression evaluates
- Result is (10+5)/(10*5+1) = 15/51 ≈ 0.294

**Validation:**
```python
T1.rate = "(P1 + P2) / (P1 * P2 + 1)"
evaluated = eval_rate_expression(T1.rate, {'P1': 10, 'P2': 5}, 0)
assert abs(evaluated - 0.294) < 0.01
```

#### Test 7.11: Complex Expression (Trigonometric)
**Model:** P1(10) → T1(rate="sin(t * 3.14 / 10) * P1") → P2  
**Expected:**
- Trigonometric function evaluates
- Oscillates over time

**Validation:**
```python
import math
T1.rate = "sin(t * 3.14 / 10) * P1"
P1.tokens = 10
evaluated_t0 = eval_rate_expression(T1.rate, {'P1': 10}, 0.0)
evaluated_t5 = eval_rate_expression(T1.rate, {'P1': 10}, 5.0)
assert abs(evaluated_t0 - 0.0) < 0.01  # sin(0) = 0
assert abs(evaluated_t5 - 10 * math.sin(math.pi/2)) < 0.01  # sin(π/2) = 1
```

#### Test 7.12: Lambda Function Rate (Simple)
**Model:** P1(10) → T1(rate=lambda marking, t: marking['P1'] * 0.5) → P2  
**Expected:**
- Lambda function evaluates correctly
- Returns 5.0 when P1=10

**Validation:**
```python
T1.rate = lambda marking, t: marking['P1'] * 0.5
P1.tokens = 10
evaluated = T1.rate({'P1': 10}, 0)
assert evaluated == 5.0
```

#### Test 7.13: Lambda Function Rate (Complex)
**Model:** P1(10), P2(5) → T1(rate=lambda m, t: min(m['P1'], m['P2']) / t if t > 0 else 0) → P3  
**Expected:**
- Complex lambda with conditional
- Handles division by zero gracefully

**Validation:**
```python
T1.rate = lambda m, t: min(m['P1'], m['P2']) / t if t > 0 else 0
evaluated_t0 = T1.rate({'P1': 10, 'P2': 5}, 0.0)
evaluated_t5 = T1.rate({'P1': 10, 'P2': 5}, 5.0)
assert evaluated_t0 == 0
assert evaluated_t5 == 1.0  # min(10,5)/5 = 1
```

#### Test 7.14: Dictionary Rate (Expression)
**Model:** P1(10) → T1(rate={'rate': "P1 * 0.5"}) → P2  
**Expected:**
- Dictionary form with expression string
- Evaluates correctly

**Validation:**
```python
T1.rate = {'rate': "P1 * 0.5"}
P1.tokens = 10
evaluated = eval_rate_expression(T1.rate['rate'], {'P1': 10}, 0)
assert evaluated == 5.0
```

#### Test 7.15: Dictionary Rate (Function)
**Model:** P1(10) → T1(rate={'rate': "min(P1, 5)"}) → P2  
**Expected:**
- Dictionary form with function expression
- Evaluates correctly

**Validation:**
```python
T1.rate = {'rate': "min(P1, 5)"}
P1.tokens = 10
evaluated = eval_rate_expression(T1.rate['rate'], {'P1': 10}, 0)
assert evaluated == 5
```

#### Test 7.16: Dictionary Rate (Lambda)
**Model:** P1(10) → T1(rate={'rate': lambda m, t: m['P1'] * 0.5}) → P2  
**Expected:**
- Dictionary form with lambda
- Evaluates correctly

**Validation:**
```python
T1.rate = {'rate': lambda m, t: m['P1'] * 0.5}
P1.tokens = 10
evaluated = T1.rate['rate']({'P1': 10}, 0)
assert evaluated == 5.0
```

#### Test 7.17: Invalid Expression (Syntax Error)
**Model:** T1(rate="invalid syntax !")  
**Expected:**
- Expression evaluation fails gracefully
- Returns default rate or raises informative error

**Validation:**
```python
T1.rate = "invalid syntax !"
try:
    evaluated = eval_rate_expression(T1.rate, {}, 0)
    assert evaluated == 1.0  # Default fallback
except SyntaxError as e:
    assert "syntax" in str(e).lower()
```

#### Test 7.18: Invalid Expression (Undefined Variable)
**Model:** T1(rate="P99 * 0.5")  # P99 doesn't exist
**Expected:**
- Undefined variable handled gracefully
- Returns default or raises informative error

**Validation:**
```python
T1.rate = "P99 * 0.5"
try:
    evaluated = eval_rate_expression(T1.rate, {'P1': 10}, 0)
    assert evaluated == 1.0  # Default fallback
except NameError as e:
    assert "P99" in str(e)
```

#### Test 7.19: Expression Performance (Large Token Count)
**Model:** P1(tokens=1000000) → T1(rate="P1 * 0.5") → P2  
**Expected:**
- Expression evaluates efficiently
- No performance degradation with large numbers

**Validation:**
```python
import time
T1.rate = "P1 * 0.5"
P1.tokens = 1000000

start = time.time()
evaluated = eval_rate_expression(T1.rate, {'P1': 1000000}, 0)
duration = time.time() - start

assert evaluated == 500000
assert duration < 0.01  # Should be fast
```

#### Test 7.20: Expression Caching (Repeated Evaluation)
**Model:** P1 → T1(rate="P1 * 0.5 + t") → P2  
**Expected:**
- Repeated evaluations use cached parsing
- Performance improvement on subsequent calls

**Validation:**
```python
import time
T1.rate = "P1 * 0.5 + t"

# First evaluation (parsing + eval)
start1 = time.time()
eval1 = eval_rate_expression(T1.rate, {'P1': 10}, 1.0)
duration1 = time.time() - start1

# Second evaluation (cached + eval)
start2 = time.time()
eval2 = eval_rate_expression(T1.rate, {'P1': 10}, 2.0)
duration2 = time.time() - start2

assert eval1 == 6.0  # 10*0.5 + 1
assert eval2 == 7.0  # 10*0.5 + 2
# Second should be faster (cached)
assert duration2 <= duration1
```

---

### Category 9: UI Dialog & Data Validation ⭐ NEW

**Note:** Tests for the transition properties dialog UI, ensuring correct input validation, data persistence, and property updates.

#### Test 9.1: Dialog Opens Successfully
**Setup:** Create immediate transition T1  
**Expected:**
- Dialog opens without errors
- All widgets are properly loaded
- Initial values match transition properties

**Validation:**
```python
T1 = Transition(name="T1", transition_type="immediate")
dialog = TransitionPropDialogLoader(T1)
assert dialog.dialog is not None
assert dialog.builder is not None
```

#### Test 9.2: Name Field (Read-Only)
**Setup:** Open dialog for T1  
**Expected:**
- Name entry shows "T1"
- Name field is not editable (read-only)
- Cannot modify name through UI

**Validation:**
```python
name_entry = dialog.builder.get_object('name_entry')
assert name_entry.get_text() == "T1"
assert name_entry.get_editable() == False
```

#### Test 9.3: Label Field (Editable)
**Setup:** Open dialog, modify label  
**Expected:**
- Label can be edited
- Changes persist after OK
- Empty label becomes None

**Validation:**
```python
label_entry = dialog.builder.get_object('transition_label_entry')
label_entry.set_text("My Transition")
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.label == "My Transition"

# Test empty label
label_entry.set_text("")
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.label is None
```

#### Test 9.4: Transition Type Selection
**Setup:** Change transition type via combo box  
**Expected:**
- All 4 types available: immediate, timed, stochastic, continuous
- Selected type persists after OK
- Type change updates transition object

**Validation:**
```python
type_combo = dialog.builder.get_object('prop_transition_type_combo')

# Test immediate (index 0)
type_combo.set_active(0)
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.transition_type == "immediate"

# Test timed (index 1)
type_combo.set_active(1)
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.transition_type == "timed"
```

#### Test 9.5: Priority Spin Button Validation
**Setup:** Modify priority value  
**Expected:**
- Accepts integer values
- Positive and negative values allowed
- Value persists after OK

**Validation:**
```python
priority_spin = dialog.builder.get_object('priority_spin')

# Test positive priority
priority_spin.set_value(10)
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.priority == 10

# Test negative priority
priority_spin.set_value(-5)
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.priority == -5
```

#### Test 9.6: Firing Policy Selection
**Setup:** Change firing policy via combo box  
**Expected:**
- Both policies available: earliest, latest
- Selected policy persists after OK

**Validation:**
```python
policy_combo = dialog.builder.get_object('firing_policy_combo')

# Test earliest (index 0)
policy_combo.set_active(0)
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.firing_policy == "earliest"

# Test latest (index 1)
policy_combo.set_active(1)
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.firing_policy == "latest"
```

#### Test 9.7: Source/Sink Checkboxes
**Setup:** Toggle source and sink checkboxes  
**Expected:**
- Checkboxes work independently
- Values persist after OK
- Boolean properties updated correctly

**Validation:**
```python
source_check = dialog.builder.get_object('is_source_check')
sink_check = dialog.builder.get_object('is_sink_check')

# Test source
source_check.set_active(True)
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.is_source == True

# Test sink
sink_check.set_active(True)
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.is_sink == True

# Test both false
source_check.set_active(False)
sink_check.set_active(False)
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.is_source == False
assert T1.is_sink == False
```

#### Test 9.8: Rate Entry - Numeric Input
**Setup:** Enter numeric rate value  
**Expected:**
- Accepts integer and float values
- Numeric string parsed correctly
- Value persists after OK

**Validation:**
```python
rate_entry = dialog.builder.get_object('rate_entry')

# Test integer
rate_entry.set_text("5")
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.rate == 5

# Test float
rate_entry.set_text("1.5")
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.rate == 1.5
```

#### Test 9.9: Rate Entry - Expression Input
**Setup:** Enter expression string for rate  
**Expected:**
- Expression string stored as-is
- No premature evaluation
- Value persists after OK

**Validation:**
```python
rate_entry = dialog.builder.get_object('rate_entry')

rate_entry.set_text("P1 * 0.5")
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.rate == "P1 * 0.5"
assert isinstance(T1.rate, str)
```

#### Test 9.10: Rate Entry - Dictionary Input
**Setup:** Enter JSON dictionary for rate  
**Expected:**
- JSON parsed correctly
- Dictionary structure preserved
- Value persists after OK

**Validation:**
```python
rate_entry = dialog.builder.get_object('rate_entry')

rate_entry.set_text('{"rate": 1.5}')
dialog.dialog.response(Gtk.ResponseType.OK)
assert isinstance(T1.rate, dict)
assert T1.rate['rate'] == 1.5
```

#### Test 9.11: Rate Entry - Empty/None
**Setup:** Clear rate entry  
**Expected:**
- Empty string results in None
- Previous value cleared
- No errors on empty input

**Validation:**
```python
rate_entry = dialog.builder.get_object('rate_entry')

T1.rate = 5.0  # Set initial value
rate_entry.set_text("")
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.rate is None or T1.rate == 5.0  # May keep old value
```

#### Test 9.12: Guard TextView - Boolean Input
**Setup:** Enter boolean guard  
**Expected:**
- "True" or "False" parsed as boolean expression
- Value stored correctly
- Persists after OK

**Validation:**
```python
guard_textview = dialog.builder.get_object('guard_textview')
buffer = guard_textview.get_buffer()

buffer.set_text("True")
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.guard == "True" or T1.guard == True
```

#### Test 9.13: Guard TextView - Expression Input
**Setup:** Enter complex guard expression  
**Expected:**
- Expression stored as string
- No premature evaluation
- Value persists after OK

**Validation:**
```python
guard_textview = dialog.builder.get_object('guard_textview')
buffer = guard_textview.get_buffer()

buffer.set_text("P1 > 5 and P1 < 20")
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.guard == "P1 > 5 and P1 < 20"
assert isinstance(T1.guard, str)
```

#### Test 9.14: Guard TextView - Math Function Input ⭐
**Setup:** Enter guard with math function  
**Expected:**
- Math expression stored correctly
- No syntax errors during storage
- Value persists after OK

**Validation:**
```python
guard_textview = dialog.builder.get_object('guard_textview')
buffer = guard_textview.get_buffer()

buffer.set_text("math.sqrt(P1) > 3.0")
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.guard == "math.sqrt(P1) > 3.0"
```

#### Test 9.15: Guard TextView - Numpy Function Input ⭐
**Setup:** Enter guard with numpy function  
**Expected:**
- Numpy expression stored correctly
- No import errors during storage
- Value persists after OK

**Validation:**
```python
guard_textview = dialog.builder.get_object('guard_textview')
buffer = guard_textview.get_buffer()

buffer.set_text("np.log10(P1) >= 2.0")
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.guard == "np.log10(P1) >= 2.0"
```

#### Test 9.16: Color Picker Integration
**Setup:** Change transition border color  
**Expected:**
- Color picker widget works
- Selected color persists after OK
- RGB values in correct range (0.0-1.0)

**Validation:**
```python
color_picker = dialog.color_picker
assert color_picker is not None

# Simulate color selection
test_color = (0.5, 0.2, 0.8)  # RGB
color_picker.emit('color-selected', test_color)
dialog.dialog.response(Gtk.ResponseType.OK)
assert T1.border_color == test_color
```

#### Test 9.17: Persistency - Mark Dirty
**Setup:** Modify any property and click OK  
**Expected:**
- Document marked as dirty
- Persistency manager notified
- Unsaved changes indicator appears

**Validation:**
```python
persistency_manager = MockPersistencyManager()
dialog = TransitionPropDialogLoader(T1, persistency_manager=persistency_manager)

label_entry = dialog.builder.get_object('transition_label_entry')
label_entry.set_text("Modified")
dialog.dialog.response(Gtk.ResponseType.OK)

assert persistency_manager.is_dirty == True
```

#### Test 9.18: Persistency - Cancel No Changes
**Setup:** Modify properties but click Cancel  
**Expected:**
- Changes discarded
- Document NOT marked as dirty
- Original values retained

**Validation:**
```python
original_label = T1.label
label_entry = dialog.builder.get_object('transition_label_entry')
label_entry.set_text("Modified")
dialog.dialog.response(Gtk.ResponseType.CANCEL)

assert T1.label == original_label
assert persistency_manager.is_dirty == False
```

#### Test 9.19: Properties Signal Emission
**Setup:** Modify properties and click OK  
**Expected:**
- 'properties-changed' signal emitted
- Observers notified (canvas redraw)
- Signal emitted once per OK

**Validation:**
```python
signal_count = 0
def on_properties_changed():
    nonlocal signal_count
    signal_count += 1

dialog.connect('properties-changed', lambda d: on_properties_changed())
label_entry = dialog.builder.get_object('transition_label_entry')
label_entry.set_text("Modified")
dialog.dialog.response(Gtk.ResponseType.OK)

assert signal_count == 1
```

#### Test 9.20: Invalid JSON Input Handling
**Setup:** Enter malformed JSON in rate/guard  
**Expected:**
- Invalid JSON handled gracefully
- Either rejected with error or treated as string
- No crash or data corruption

**Validation:**
```python
rate_entry = dialog.builder.get_object('rate_entry')

rate_entry.set_text('{"rate": invalid}')
dialog.dialog.response(Gtk.ResponseType.OK)

# Should either keep old value, set to string, or show error
assert T1.rate is not None  # No crash
```

---

### Category 8: Edge Cases

#### Test 8.1: Enabled Flag (Disabled Transition)
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

#### Test 8.2: Invalid Guard Expression
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

#### Test 8.3: Negative Priority
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

#### Test 8.4: Very Large Token Count
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

#### Test 8.5: Firing Policy (Earliest vs Latest)
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
✅ **9 test categories** - Complete coverage (includes UI validation)  
✅ **81 test cases** - Thorough validation (20 UI/dialog tests added)  
✅ **Incremental implementation** - Manageable workload  
✅ **Clear success criteria** - Measurable outcomes  
✅ **Complex function testing** ⭐ - Boolean guards (math, numpy, lambda) & threshold weights  
✅ **UI validation** ⭐ **NEW** - Dialog input validation, data persistence, property updates  

**Immediate transitions are the foundation** - validating them thoroughly ensures the entire simulation framework is solid! 🎯

---

## Test Distribution

| Category | Test Count | Focus | New Tests |
|----------|------------|-------|-----------|
| 1. Basic Firing | 3 | Correctness | - |
| 2. Guards | 12 | ⭐ Boolean functions | +6 complex |
| 3. Priority | 3 | Conflict resolution | - |
| 4. Arc Weights | 12 | ⭐ Threshold functions | +7 complex |
| 5. Source/Sink | 3 | Special behavior | - |
| 6. Persistence | 3 | Save/load | - |
| 7. Rate Expressions | 20 | Expression evaluation | - |
| 8. Edge Cases | 5 | Error handling | - |
| 9. UI Dialog ⭐ | 20 | **UI validation** | **+20 NEW** |
| **Total** | **81** | **Comprehensive** | **+33 tests** |

**Key Enhancements:**
- **Category 2 (Guards):** 6→12 tests - Added complex boolean functions (math.sqrt, numpy.log10, lambda, conditionals, trig)
- **Category 4 (Weights):** 5→12 tests - Added complex threshold functions (math.ceil, numpy.log, lambda, conditionals, trig)
- **Category 9 (UI Dialog):** ⭐ **NEW** - 20 tests for dialog widgets, input validation, persistency

**UI Test Coverage:**
- Widget loading & initialization (2 tests)
- Property input validation (10 tests)
- Data persistence & dirty marking (2 tests)
- Signal emission (1 test)
- Error handling (2 tests)
- Complex expressions in UI (3 tests)

**Note:** UI validation ensures data correctness from user input through to model persistence!
