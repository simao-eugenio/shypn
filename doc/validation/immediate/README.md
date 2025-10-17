# Immediate Transition Validation

**Transition Type:** Immediate  
**Status:** Planning Phase  
**Last Updated:** October 17, 2025

---

## Overview

This directory contains all validation documentation and test plans specific to **immediate transitions** in SHYpn Petri nets.

**Immediate transitions** fire instantaneously (zero delay) when enabled. They are the simplest transition type and serve as the foundation for validating the entire transition behavior framework.

---

## Characteristics

### Definition
An immediate transition fires at time t=0 (or immediately when enabled) if:
1. ✅ **Guard condition passes** (if guard defined)
2. ✅ **Input places have sufficient tokens** (unless is_source=True)
3. ✅ **Highest priority** among competing immediate transitions

### Key Properties

| Property | Type | Default | Tested |
|----------|------|---------|--------|
| `transition_type` | string | 'immediate' | ✅ |
| `enabled` | boolean | True | ✅ |
| `guard` | expression | None | ✅ |
| `priority` | int | 0 | ✅ |
| `firing_policy` | string | 'earliest' | ✅ |
| `is_source` | boolean | False | ✅ |
| `is_sink` | boolean | False | ✅ |

**Note:** The `rate` property is **ignored** for immediate transitions (they fire instantly).

---

## Documentation

### Benchmark Plan
**File:** [BENCHMARK_PLAN.md](BENCHMARK_PLAN.md)

Comprehensive test plan with:
- **7 test categories**
- **40+ test cases**
- P-T-P model methodology
- Clear validation criteria

**Categories:**
1. Basic Firing Mechanism (3 tests)
2. Guard Function Evaluation (6 tests)
3. Priority Resolution (3 tests)
4. Arc Weight Interaction (5 tests)
5. Source/Sink Behavior (3 tests)
6. Persistence & Serialization (3 tests)
7. Edge Cases (5 tests)

---

## Test Model

### Simple P-T-P Structure

```
[P1] --[weight=1]--> [T1] --[weight=1]--> [P2]
```

**Where:**
- **P1** = Input place (configurable initial tokens)
- **T1** = Immediate transition (properties under test)
- **P2** = Output place (initial tokens = 0)

**Benefits:**
- ✅ Isolates transition behavior
- ✅ Clear input/output verification
- ✅ No interference from other transitions
- ✅ Deterministic and reproducible
- ✅ Easy to extend with complexity

---

## Test Categories Breakdown

### 1. Basic Firing Mechanism
Tests fundamental immediate firing without guards or special properties.

**Test Cases:**
- Single fire (1 token)
- Multiple firings (5 tokens)
- Insufficient tokens (0 tokens)

### 2. Guard Function Evaluation
Tests all guard types and their evaluation.

**Guard Types:**
- Boolean: `True` / `False`
- Numeric: `5` (threshold > 0)
- Expression: `"P1 > 5"`
- Complex: `"P1 > 5 and P1 < 20"`
- Time-dependent: `"t > 5.0"`
- Function-based: `"sigmoid(P1, 50, 10)"`

### 3. Priority Resolution
Tests conflict resolution when multiple transitions compete.

**Scenarios:**
- Single transition (priority irrelevant)
- Two transitions, different priorities (higher wins)
- Equal priority (non-deterministic choice)

### 4. Arc Weight Interaction
Tests token consumption/production with various weights.

**Weight Types:**
- Input weight > 1 (requires more tokens)
- Output weight > 1 (produces more tokens)
- Both weights > 1 (ratio effects)
- Numeric expression: `"2*2"` → 4
- Function expression: `"min(P1, 3)"`

### 5. Source/Sink Behavior
Tests infinite token generation/consumption.

**Scenarios:**
- Source transition (no input required)
- Sink transition (no output produced)
- Source + Sink (passthrough)

### 6. Persistence & Serialization
Tests property preservation across save/load cycles.

**What's Tested:**
- Basic properties (type, priority)
- Guard functions (string expressions)
- Properties dict (custom data)

### 7. Edge Cases
Tests boundary conditions and error handling.

**Scenarios:**
- Disabled transition (`enabled=False`)
- Invalid guard expression (syntax error)
- Negative priority
- Very large token count (1M tokens)
- Firing policy variations

---

## Implementation Status

### Planning ✅
- [x] Benchmark plan created
- [x] Test categories defined
- [x] Success criteria established
- [x] Documentation structure set up

### Infrastructure 🔜
- [ ] Test directory created (`tests/validation/immediate/`)
- [ ] P-T-P model generator fixture
- [ ] Assertion utilities
- [ ] Test harness setup (pytest)

### Test Implementation 🔜
- [ ] Category 1: Basic firing (3 tests)
- [ ] Category 2: Guards (6 tests)
- [ ] Category 3: Priority (3 tests)
- [ ] Category 4: Arc weights (5 tests)
- [ ] Category 5: Source/sink (3 tests)
- [ ] Category 6: Persistence (3 tests)
- [ ] Category 7: Edge cases (5 tests)

### Validation 🔜
- [ ] All tests passing
- [ ] Coverage report generated
- [ ] Issues documented
- [ ] Findings summarized

---

## Success Criteria

### Coverage
- ✅ 100% of immediate transition properties tested
- ✅ All guard types validated
- ✅ All arc weight scenarios covered
- ✅ Source/sink behaviors confirmed

### Quality
- ✅ No crashes or undefined behavior
- ✅ All edge cases handled gracefully
- ✅ Performance within acceptable limits (<10s for 1M tokens)
- ✅ Clear error messages for invalid states

### Documentation
- ✅ All test cases documented
- ✅ Expected behaviors clearly defined
- ✅ Edge cases and limitations noted
- ✅ User guide updated

---

## Timeline

**Estimated Duration:** 3 weeks

| Week | Phase | Tasks |
|------|-------|-------|
| 1 | Infrastructure | Test setup, P-T-P generator, basic tests |
| 2 | Advanced Testing | Guards, priority, weights, source/sink |
| 3 | Integration | Persistence, edge cases, documentation |

---

## Related Documentation

### In This Directory
- [BENCHMARK_PLAN.md](BENCHMARK_PLAN.md) - Complete test plan with all 40+ test cases

### External References
- `/doc/GUARD_FUNCTION_GUIDE.md` - Guard implementation and usage
- `/doc/DEFAULT_VALUES_FIX.md` - Default property values
- `/doc/GUARD_RATE_PERSISTENCE_FIX.md` - Persistence implementation
- `/doc/behaviors/README.md` - Transition behaviors overview

### Source Code
- `/src/shypn/netobjs/transition.py` - Transition class definition
- `/src/shypn/engine/transition_behavior.py` - Behavior base class
- `/src/shypn/engine/immediate_behavior.py` - Immediate-specific behavior

---

## Quick Reference

### Immediate Transition Properties

```python
# Create immediate transition
t = Transition(x=100, y=100, id=1, name='T1')
t.transition_type = 'immediate'  # Default

# Core properties
t.enabled = True           # Can fire?
t.guard = None             # No guard (always enabled)
t.priority = 0             # Default priority
t.firing_policy = 'earliest'  # Default policy

# Special behaviors
t.is_source = False        # Not a source
t.is_sink = False          # Not a sink

# Properties dict (for advanced features)
t.properties = {
    'guard_function': 'P1 > 5',  # String expression
    'custom_data': 'value'       # Custom metadata
}
```

### Expected Behavior

```python
# With tokens in P1
P1.tokens = 10
# Immediate transition fires at t=0
assert firing_time == 0.0
assert P1.tokens == 9  # Consumed 1
assert P2.tokens == 1  # Produced 1

# With guard
t.guard = "P1 > 5"
P1.tokens = 3
assert t.can_fire() == False  # Guard blocks

P1.tokens = 10
assert t.can_fire() == True   # Guard passes
```

---

## Next Steps

1. **Create test infrastructure** - Set up pytest framework
2. **Implement P-T-P generator** - Model creation fixture
3. **Write basic tests** - Category 1 (firing mechanism)
4. **Validate against implementation** - Find and fix issues
5. **Expand to advanced tests** - Categories 2-7
6. **Document findings** - Issues, edge cases, recommendations

---

## Summary

**Immediate transition validation** establishes the foundation for the entire Petri net validation framework:

✅ **Comprehensive coverage** - 40+ tests across 7 categories  
✅ **Simple methodology** - P-T-P models for clarity  
✅ **Clear criteria** - Measurable success indicators  
✅ **Systematic approach** - Incremental, manageable phases  

**Validating immediate transitions thoroughly ensures the simulation engine is robust and reliable!** 🎯
