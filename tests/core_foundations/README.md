# Core Foundations Test Suite

## Purpose
Validate the theoretical foundations of the hybrid Petri net platform for **scientific manuscript submission**.

## What We Test

### 1. Signal Hierarchy Theory ⚠️ CRITICAL
- Signal places modulate rates WITHOUT consumption
- Distinction between signal carriers and signal places
- Hierarchical signal cascades
- **Files**: `test_signal_hierarchy.py`

### 2. Weak Independence Theory ⚠️ CRITICAL
- Transitions fire based on LOCAL enabling
- No global state dependencies
- Concurrent enabling of independent transitions
- **Files**: `test_weak_independence.py`

### 3. Type System (TODO)
- Place types: normal, signal, source, sink
- Transition types: stochastic, continuous, immediate, timed
- Arc types: normal, test, inhibitor, read
- **Files**: `test_place_types.py`, `test_transition_types.py`, `test_arc_types.py`

### 4. Integration (TODO)
- Complete metabolic pathways
- Glycolysis with ATP signal hierarchy
- **Files**: `test_integration.py`

## Running Tests

```bash
# Run all foundation tests
python -m pytest tests/core_foundations/ -v

# Run specific test file
python -m pytest tests/core_foundations/test_signal_hierarchy.py -v

# Run with detailed output
python -m pytest tests/core_foundations/ -v --tb=long
```

## Current Status

| Test File | Tests | Pass | Fail | Status |
|-----------|-------|------|------|--------|
| test_signal_hierarchy.py | 3 | 0 | 0 | 🟡 Structural only |
| test_weak_independence.py | 3 | 0 | 0 | 🟡 Structural only |
| test_place_types.py | - | - | - | ⚪ TODO |
| test_transition_types.py | - | - | - | ⚪ TODO |
| test_arc_types.py | - | - | - | ⚪ TODO |
| test_integration.py | - | - | - | ⚪ TODO |

**Legend**: 🟢 All pass | 🟡 Partial | 🔴 Failures | ⚪ Not started

## Next Steps

1. **Implement simulation engine integration** in tests
   - Add `is_enabled()` checks
   - Add `fire()` method calls
   - Verify token flow

2. **Add remaining test files**
   - Place types
   - Transition types
   - Arc types
   - Integration tests

3. **Run full audit**
   - Fix all failures
   - Document results
   - Update manuscript

## Critical for Manuscript

These tests validate the **theoretical foundations** that the manuscript claims:
- ✅ Weak independence (Petri net semantics)
- ✅ Signal hierarchy (regulatory networks)
- ✅ Type system correctness (hybrid model)

**Without these tests passing, the manuscript lacks empirical validation of its core claims.**
