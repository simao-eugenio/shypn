# Petri Net Property Validation

**Date:** October 17, 2025  
**Status:** Planning Phase  
**Goal:** Systematic validation of all Petri net transition types and properties

---

## Overview

This directory contains comprehensive benchmark and validation plans for Petri net properties in SHYpn. The validation framework uses simple P-T-P (Place-Transition-Place) models to isolate and test specific properties of each transition type.

---

## Transition Types

SHYpn supports four transition types, each with specific properties:

1. **Immediate** ✅ **[Current Focus]** - Fires instantly (zero delay)
2. **Timed** 🔜 - Fires after deterministic delay
3. **Stochastic** 🔜 - Fires with exponential distribution
4. **Continuous** 🔜 - Continuous token flow (ODEs)

---

## Current Status

### ✅ Immediate Transition Benchmark Plan (COMPLETE)

**Document:** [IMMEDIATE_TRANSITION_BENCHMARK_PLAN.md](IMMEDIATE_TRANSITION_BENCHMARK_PLAN.md)

**Coverage:**
- **7 test categories** with 40+ test cases
- Basic firing mechanism (3 tests)
- Guard function evaluation (6 tests)
- Priority resolution (3 tests)
- Arc weight interaction (5 tests)
- Source/sink behavior (3 tests)
- Persistence & serialization (3 tests)
- Edge cases (5 tests)

**Test Model:** Simple P-T-P structure
```
[P1] --[weight]--> [T1] --[weight]--> [P2]
```

**Properties Under Test:**
- `transition_type` = 'immediate'
- `guard` - Boolean condition (None, boolean, numeric, expression)
- `priority` - Conflict resolution (int, default=0)
- `enabled` - Can fire? (boolean, default=True)
- `firing_policy` - 'earliest' or 'latest'
- `is_source` - Generates tokens without input
- `is_sink` - Consumes tokens without output

---

## Validation Approach

### P-T-P Model Benefits

✅ **Minimal Complexity** - Isolates single transition behavior  
✅ **Clear I/O** - Easy token flow verification  
✅ **No Interference** - Single transition = deterministic  
✅ **Extensible** - Add complexity incrementally  
✅ **Reproducible** - Predictable for automated testing  

### Test Categories

Each transition type is tested across these categories:

1. **Basic Mechanism** - Core firing behavior
2. **Guard Functions** - Conditional firing (all guard types)
3. **Priority/Conflict** - Multiple transition interactions
4. **Arc Weights** - Token consumption/production ratios
5. **Special Behaviors** - Source/sink, custom properties
6. **Persistence** - Save/load/reload validation
7. **Edge Cases** - Boundary conditions, error handling

---

## Implementation Roadmap

### Phase 1: Immediate Transitions ✅ PLANNED
- [x] Benchmark plan created
- [ ] Test infrastructure setup
- [ ] Basic tests implementation
- [ ] Advanced tests implementation
- [ ] Integration tests
- [ ] Documentation

**Timeline:** 3 weeks

### Phase 2: Timed Transitions 🔜
- [ ] Benchmark plan
- [ ] Delay property tests
- [ ] Timeout mechanism tests
- [ ] Clock-based validation

**Timeline:** 2 weeks

### Phase 3: Stochastic Transitions 🔜
- [ ] Benchmark plan
- [ ] Exponential distribution tests
- [ ] Rate parameter tests
- [ ] Statistical validation

**Timeline:** 2 weeks

### Phase 4: Continuous Transitions 🔜
- [ ] Benchmark plan
- [ ] Rate function tests
- [ ] ODE solver validation
- [ ] Time-dependent behaviors

**Timeline:** 3 weeks

### Phase 5: Integration Testing 🔜
- [ ] Mixed transition types
- [ ] Complex network topologies
- [ ] Performance benchmarks
- [ ] Comprehensive validation suite

**Timeline:** 2 weeks

---

## Success Criteria

### Per-Transition Type

- ✅ **100% property coverage** - All properties tested
- ✅ **All guard types** - Boolean, numeric, expression, function
- ✅ **All arc weight types** - Constant, numeric, expression, function
- ✅ **Edge cases handled** - No crashes, graceful degradation
- ✅ **Performance acceptable** - Large models handled efficiently

### Overall Framework

- ✅ **Automated test suite** - CI/CD integration ready
- ✅ **Comprehensive documentation** - User and developer guides
- ✅ **Validation reports** - Coverage and pass/fail summary
- ✅ **Benchmark results** - Performance baselines established

---

## Test Infrastructure

### Directory Structure

```
tests/validation/
├── immediate/           # Immediate transition tests
│   ├── test_basic_firing.py
│   ├── test_guards.py
│   ├── test_priority.py
│   ├── test_arc_weights.py
│   ├── test_source_sink.py
│   ├── test_persistence.py
│   └── test_edge_cases.py
├── timed/              # Timed transition tests
├── stochastic/         # Stochastic transition tests
├── continuous/         # Continuous transition tests
├── integration/        # Cross-type integration tests
├── fixtures/           # Test model generators
│   ├── ptp_generator.py
│   └── complex_models.py
└── utils/              # Test utilities
    ├── assertions.py
    ├── simulation_runner.py
    └── report_generator.py
```

### Test Framework

**Technology:** pytest with custom fixtures  
**Coverage:** pytest-cov  
**Reporting:** HTML reports + markdown summaries  
**CI/CD:** GitHub Actions integration  

---

## Documentation

### Benchmark Plans
- [IMMEDIATE_TRANSITION_BENCHMARK_PLAN.md](IMMEDIATE_TRANSITION_BENCHMARK_PLAN.md) - Detailed test plan for immediate transitions
- TIMED_TRANSITION_BENCHMARK_PLAN.md - 🔜 Coming soon
- STOCHASTIC_TRANSITION_BENCHMARK_PLAN.md - 🔜 Coming soon
- CONTINUOUS_TRANSITION_BENCHMARK_PLAN.md - 🔜 Coming soon

### Implementation Guides
- Guard Function Implementation - See `/doc/GUARD_FUNCTION_GUIDE.md`
- Arc Weight Specification - See `/doc/behaviors/README.md`
- Rate Function Implementation - See `/doc/GUARD_RATE_PERSISTENCE_FIX.md`

### Reference Documentation
- Transition Behaviors - `/doc/behaviors/`
- Default Values - `/doc/DEFAULT_VALUES_FIX.md`
- Persistence - `/doc/GUARD_RATE_PERSISTENCE_FIX.md`

---

## Quick Start

### 1. Read the Immediate Transition Plan
```bash
cat doc/validation/IMMEDIATE_TRANSITION_BENCHMARK_PLAN.md
```

### 2. Run Tests (when implemented)
```bash
cd tests/validation
pytest immediate/ -v --cov
```

### 3. Generate Report
```bash
pytest --cov-report=html
open htmlcov/index.html
```

---

## Contributing

When adding new tests:

1. **Follow P-T-P model pattern** - Keep tests simple and isolated
2. **Document expected behavior** - Clear assertions with comments
3. **Test all property combinations** - Comprehensive coverage
4. **Handle edge cases** - Boundary conditions, errors
5. **Add to benchmark plan** - Update documentation

---

## Next Action

**Immediate Priority:** Implement test infrastructure for immediate transitions

1. Create `tests/validation/immediate/` directory
2. Implement P-T-P model generator fixture
3. Create basic firing tests (Category 1)
4. Validate against current implementation
5. Document any findings or issues

---

## Related Documentation

- `/doc/GUARD_FUNCTION_GUIDE.md` - Guard implementation details
- `/doc/DEFAULT_VALUES_FIX.md` - Default property values
- `/doc/behaviors/README.md` - Transition behaviors overview
- `/doc/GUARD_RATE_PERSISTENCE_FIX.md` - Persistence implementation

---

## Summary

**Immediate Transition Validation** is the foundation of this framework:

✅ **Comprehensive plan** - 40+ test cases across 7 categories  
✅ **Simple methodology** - P-T-P models for clarity  
✅ **Clear success criteria** - Measurable outcomes  
✅ **Incremental approach** - Build confidence step by step  

**This systematic validation ensures SHYpn's simulation engine is robust and reliable!** 🎯
