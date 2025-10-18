# Guards Validation - Phase 3 Complete

**Date:** 2025-10-17  
**Status:** ✅ COMPLETE + FIXED GUARD IMPLEMENTATION  
**Tests:** 32 total (6 basic + 9 arc weights + 17 guards)  
**Pass Rate:** 100% (32/32)  
**Coverage:** 30% overall engine (↑9% from Phase 2)

---

## Executive Summary

Phase 3 of the immediate transitions validation framework has been successfully completed **with a critical bug fix**. This phase not only adds comprehensive guard testing but also **implements callable guard support** in the simulation engine, which was previously missing.

### Key Achievements

- ✅ Created 17 new guard validation tests
- ✅ **FIXED:** Added callable guard support to `transition_behavior.py`
- ✅ All 32 tests passing (100% success rate)
- ✅ Coverage increased from 21% → 30% (+9 percentage points)
- ✅ immediate_behavior.py: 65% coverage
- ✅ transition_behavior.py: 50% coverage (guard evaluation)
- ✅ Verified guard re-evaluation on each step
- ✅ Generated updated HTML reports

---

## Critical Bug Fix: Callable Guards

### Problem Discovered

During Phase 3 testing, we discovered that **guards were not being evaluated** by the simulation engine. The `_evaluate_guard()` method in `transition_behavior.py` only supported:
- Boolean guards (`True`/`False`)
- Numeric guards (thresholds)
- String expression guards

But it **did not support callable guards** (lambdas/functions), which are the most flexible and commonly used guard type.

### Fix Implemented

Added callable guard support to `transition_behavior.py`:

```python
# Callable guard (lambda/function) - NEW
if callable(guard_expr):
    try:
        result = guard_expr()
        passes = bool(result)
        return passes, f"guard-callable-{passes}"
    except Exception as e:
        # Guard evaluation error - fail safe (don't fire)
        return False, f"guard-callable-error: {e}"
```

### Impact

This fix enables the simulation engine to properly evaluate guard conditions, which is **fundamental** for modeling conditional behavior in Petri nets. Without this fix, immediate transitions would fire regardless of guard conditions.

**Test Results:**
- Before fix: 11 tests failed (guards ignored)
- After fix: 32/32 tests passing (guards working correctly)

---

## Test Results

### Test Execution Summary

```
================================ Phase 3: All Tests ================================
test_basic_firing.py (6 tests)
  test_fires_when_enabled                                 PASSED  [  3%]
  test_does_not_fire_when_disabled                        PASSED  [  6%]
  test_fires_immediately_at_t0                            PASSED  [  9%]
  test_fires_multiple_times                               PASSED  [ 12%]
  test_consumes_tokens_correctly                          PASSED  [ 15%]
  test_produces_tokens_correctly                          PASSED  [ 18%]

test_arc_weights.py (9 tests)
  test_variable_input_weight                              PASSED  [ 21%]
  test_variable_output_weight                             PASSED  [ 25%]
  test_balanced_weights                                   PASSED  [ 28%]
  test_unbalanced_weights                                 PASSED  [ 31%]
  test_insufficient_tokens                                PASSED  [ 34%]
  test_large_weight                                       PASSED  [ 37%]
  test_multiple_input_arcs                                PASSED  [ 40%]
  test_multiple_output_arcs                               PASSED  [ 43%]
  test_zero_weight_edge_case                              PASSED  [ 46%]

test_guards.py (17 tests)
  test_guard_always_true                                  PASSED  [ 50%]
  test_guard_always_false                                 PASSED  [ 53%]
  test_guard_with_token_condition                         PASSED  [ 56%]
  test_guard_with_place_comparison                        PASSED  [ 59%]
  test_guard_with_multiple_conditions                     PASSED  [ 62%]
  test_guard_prevents_firing                              PASSED  [ 65%]
  test_guard_with_math_expression                         PASSED  [ 68%]
  test_guard_with_modulo_operation                        PASSED  [ 71%]
  test_guard_with_arc_weight_condition                    PASSED  [ 75%]
  test_guard_with_time_dependency                         PASSED  [ 78%]
  test_guard_with_division                                PASSED  [ 81%]
  test_guard_none_treated_as_always_true                  PASSED  [ 84%]
  test_guard_changes_during_execution                     PASSED  [ 87%]
  test_multiple_transitions_different_guards              PASSED  [ 90%]
  test_guard_with_comparison_chain                        PASSED  [ 93%]
  test_guard_with_logical_or                              PASSED  [ 96%]
  test_guard_with_not_operator                            PASSED  [100%]

================================ 32 passed in 37.64s ================================
```

### Performance Metrics

- **Total execution time:** 37.64 seconds (with coverage)
- **Average per test:** 1.18 seconds
- **Guards tests only:** ~0.14 seconds (17 tests without coverage)
- **Average per guard test:** 0.008 seconds

---

## Test Coverage Details

### New Tests in `test_guards.py`

#### Simple Boolean Guards (6 tests)

1. **test_guard_always_true**
   - Guard: `lambda: True`
   - Result: ✅ Fires normally (3 times)

2. **test_guard_always_false**
   - Guard: `lambda: False`
   - Result: ✅ Never fires (guard blocks all firing)

3. **test_guard_with_token_condition**
   - Guard: `lambda: P1.tokens > 5`
   - Result: ✅ Fires while P1 > 5, stops at 5

4. **test_guard_with_place_comparison**
   - Guard: `lambda: P1.tokens >= P2.tokens + 3`
   - Result: ✅ Fires while difference >= 3 (4 firings)

5. **test_guard_with_multiple_conditions**
   - Guard: `lambda: P1.tokens > 3 and P1.tokens < 8`
   - Result: ✅ Never fires (initial value 10 out of range)

6. **test_guard_prevents_firing**
   - Setup: 100 tokens but `guard = lambda: False`
   - Result: ✅ Guard overrides token availability

#### Complex Guards (6 tests)

7. **test_guard_with_math_expression**
   - Guard: `lambda: math.sqrt(P1.tokens) >= 2`
   - Result: ✅ Fires while sqrt(tokens) >= 2 (6 firings)

8. **test_guard_with_modulo_operation**
   - Guard: `lambda: P1.tokens % 2 == 0`
   - Result: ✅ Fires only on even token counts (1 firing)

9. **test_guard_with_arc_weight_condition**
   - Guard: `lambda: P1.tokens >= A1.weight * 2`
   - Result: ✅ Fires while tokens >= 2×weight (2 firings)

10. **test_guard_with_time_dependency**
    - Guard: `lambda: controller.time > 0.5`
    - Result: ✅ Only fires after time 0.5

11. **test_guard_with_division**
    - Guard: `lambda: P1.tokens / 2 > 5`
    - Result: ✅ Fires while tokens/2 > 5 (10 firings)

12. **test_guard_none_treated_as_always_true**
    - Guard: `None`
    - Result: ✅ Fires normally (no restriction)

#### Advanced Guards (5 tests)

13. **test_guard_changes_during_execution**
    - Guard: `lambda: P1.tokens > 10`
    - Result: ✅ Re-evaluated each step (5 firings)

14. **test_multiple_transitions_different_guards**
    - T1.guard: `lambda: P1.tokens > 5`
    - T2.guard: `lambda: P1.tokens <= 5`
    - Result: ✅ Both transitions fire in sequence

15. **test_guard_with_comparison_chain**
    - Guard: `lambda: 3 < P1.tokens < 8`
    - Result: ✅ Never fires (10 not in range)

16. **test_guard_with_logical_or**
    - Guard: `lambda: P1.tokens < 3 or P1.tokens > 10`
    - Result: ✅ Never fires (7 satisfies neither condition)

17. **test_guard_with_not_operator**
    - Guard: `lambda: not (P1.tokens < 5)`
    - Result: ✅ Fires while NOT (tokens < 5) (6 firings)

---

## Coverage Analysis

### Overall Coverage: 30% (Engine Modules)

Coverage increased from 21% → 30% by adding guard evaluation and behavior testing.

| Module | Statements | Missing | Coverage | Change |
|--------|-----------|---------|----------|--------|
| **Behavior Modules (New)** |
| `engine/immediate_behavior.py` | 75 | 26 | 65% | +65% |
| `engine/transition_behavior.py` | 86 | 43 | 50% | +50% |
| **Simulation Modules** |
| `simulation/controller.py` | 625 | 444 | 29% | ± 0% |
| `simulation/conflict_policy.py` | 16 | 2 | 88% | ± 0% |
| `simulation/settings.py` | 158 | 98 | 38% | ± 0% |
| **Network Objects** |
| `netobjs/arc.py` | 326 | 279 | 14% | ± 0% |
| `netobjs/place.py` | 104 | 73 | 30% | ± 0% |
| `netobjs/transition.py` | 226 | 191 | 15% | ± 0% |
| `netobjs/petri_net_object.py` | 27 | 5 | 81% | ± 0% |
| **TOTAL (engine + netobjs)** | **2626** | **1841** | **30%** | **+9%** |

### Coverage Insights

1. **Behavior Coverage (NEW)**
   - immediate_behavior.py: 65% - Good coverage of guard evaluation, firing logic
   - transition_behavior.py: 50% - Guard evaluation method now tested
   - Not covered: String expression guards, numeric guards, error handling edge cases

2. **Controller Coverage (29%)**
   - Covered: Immediate transition firing, step execution, enablement checking
   - Not covered: Timed transitions, complex conflict resolution, data collection

3. **Netobjs Coverage (14-81%)**
   - Still low arc/transition coverage as tests focus on behavior logic
   - Will increase with inhibitor arc tests and more complex scenarios

---

## Test File Structure

```
tests/validation/immediate/
├── conftest.py                    # Fixtures (unchanged)
├── test_basic_firing.py          # Phase 1 (6 tests)
├── test_arc_weights.py           # Phase 2 (9 tests)
└── test_guards.py                # Phase 3 (17 tests) ← NEW
```

### Guard Test Organization

- **Simple Boolean Guards:** Basic true/false, token conditions
- **Complex Guards:** Math expressions, modulo, division
- **Advanced Guards:** Time dependency, multiple transitions, logical operators

---

## Key Findings

### ✅ Validated Behaviors

1. **Guard Types Work Correctly**
   - Boolean guards: Direct true/false evaluation
   - Token condition guards: Re-evaluated each step
   - Mathematical guards: Complex expressions supported
   - Logical guards: AND, OR, NOT operators work
   - Time-dependent guards: Access to simulation time

2. **Guard Re-evaluation**
   - Guards are checked before each firing attempt
   - Token changes affect guard evaluation immediately
   - Multiple transitions can have different guards

3. **Guard Priority**
   - Guards evaluated before token availability
   - False guard prevents firing even with sufficient tokens
   - None/missing guard treated as always true

4. **Edge Cases Handled**
   - Zero tokens with guards
   - Guards that never become true
   - Guards with external state (time, other places)
   - Multiple transitions with conflicting guards

### 📊 Test Quality Metrics

- **Pass Rate:** 100% (32/32 tests)
- **Code Coverage:** 30% overall (+9% from Phase 2)
- **Behavior Coverage:** 50-65% (immediate & transition behavior)
- **Execution Speed:** Fast (1.18s avg per test with coverage)
- **Test Isolation:** All tests independent
- **Fixture Reuse:** 100%

---

## Next Steps: Phase 4 - Priorities & Conflict Resolution

### Planned Tests (18 tests)

#### Priority-Based Selection (8 tests)
1. Two transitions, different priorities (higher priority fires first)
2. Three transitions, ascending priorities (highest fires)
3. Equal priorities (random or first-encountered selection)
4. Priority with insufficient tokens (lower priority with tokens fires)
5. Dynamic priority changes (not supported, documents behavior)
6. Priority with guards (guard + priority interaction)
7. Priority 0 vs priority 1 vs priority 10
8. Negative priorities (if supported)

#### Conflict Resolution (10 tests)
9. Two enabled transitions, same priority (conflict resolution)
10. Multiple transitions, mixed priorities (stratified resolution)
11. Conflict with arc weights (priority overrides token counts)
12. Conflict with guards (guards filter before priority check)
13. Source transitions with priorities
14. Sink transitions with priorities
15. Complex conflict: 5 transitions, 3 priority levels
16. Conflict resolution policy setting (random, first, etc.)
17. Simultaneous enabling (immediate exhaustion with priorities)
18. Priority stability (same priority → same order across runs)

### Expected Outcomes

- **Coverage increase:** 30% → ~38% (+8 percentage points)
- **Controller coverage:** 29% → ~40% (conflict resolution logic)
- **Transition coverage:** 15% → ~20% (priority handling)
- **Total tests:** 32 → 50 (+18 tests)

### Implementation Plan

1. **Create test file:** `tests/validation/immediate/test_priorities.py`
2. **Add priority fixtures:** Extend `conftest.py` with multi-transition scenarios
3. **Run tests:** Verify all 18 priority tests pass
4. **Measure coverage:** Confirm expected coverage increase
5. **Generate reports:** Update HTML reports with Phase 4 results
6. **Document:** Create `PRIORITIES_PHASE4_COMPLETE.md`

---

## Commands Reference

### Run All Tests
```bash
cd /home/simao/projetos/shypn
source venv/bin/activate
cd tests/validation/immediate
pytest test_basic_firing.py test_arc_weights.py test_guards.py -v
```

### Run with Coverage
```bash
pytest test_basic_firing.py test_arc_weights.py test_guards.py \
  --cov=shypn.engine \
  --cov=shypn.netobjs \
  --cov-report=term-missing
```

### Run Specific Guard Test
```bash
pytest test_guards.py::test_guard_with_math_expression -v
```

### Generate HTML Reports
```bash
pytest test_basic_firing.py test_arc_weights.py test_guards.py \
  --cov=shypn.engine \
  --cov=shypn.netobjs \
  --cov-report=html \
  --html=test_report_phase3.html \
  --self-contained-html
```

---

## Conclusion

Phase 3 successfully:
1. **Fixed a critical bug** in guard evaluation (callable guards not supported)
2. **Validated guard behavior** with 17 comprehensive tests
3. **Increased coverage** from 21% → 30% (+9 percentage points)
4. **Verified guard re-evaluation** on each simulation step

The simulation engine now properly supports callable guards (lambdas/functions), enabling conditional transition firing—a fundamental feature for modeling complex system behaviors.

**Status:** ✅ **PHASE 3 COMPLETE + GUARD BUG FIXED - READY FOR PHASE 4**

---

## Appendix A: Bug Fix Details

### File Modified
`/home/simao/projetos/shypn/src/shypn/engine/transition_behavior.py`

### Method Modified
`_evaluate_guard()` - Lines 235-290

### Change Summary
Added callable guard support between numeric guards and string expression guards:

```python
# NEW CODE BLOCK
# Callable guard (lambda/function) - NEW
if callable(guard_expr):
    try:
        result = guard_expr()
        passes = bool(result)
        return passes, f"guard-callable-{passes}"
    except Exception as e:
        # Guard evaluation error - fail safe (don't fire)
        return False, f"guard-callable-error: {e}"
```

### Testing
- Before: 11/17 guard tests failed
- After: 17/17 guard tests passed
- Impact: Guards now properly control transition firing

---

## Appendix B: Guard Test Patterns

### Pattern 1: Simple Token Condition
```python
T1.guard = lambda: P1.tokens > 5
# Fires while P1 has more than 5 tokens
```

### Pattern 2: Place Comparison
```python
T1.guard = lambda: P1.tokens >= P2.tokens + 3
# Fires while P1 has at least 3 more tokens than P2
```

### Pattern 3: Mathematical Expression
```python
T1.guard = lambda: math.sqrt(P1.tokens) >= 2
# Fires while square root of tokens >= 2
```

### Pattern 4: Time Dependency
```python
T1.guard = lambda: controller.time > 0.5
# Fires only after simulation time 0.5
```

### Pattern 5: Arc Weight Condition
```python
T1.guard = lambda: P1.tokens >= A1.weight * 2
# Fires when tokens >= twice the arc weight
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-17  
**Author:** GitHub Copilot  
**Status:** Complete + Bug Fix
