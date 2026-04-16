# Immediate Transition Validation Tests

**Purpose:** Fast functional correctness tests for immediate transitions.

## Test Files

### Category 1: Basic Firing Mechanism
- `test_basic_firing.py` - Zero-delay firing, multiple firings, insufficient tokens

### Category 2: Guard Function Evaluation  
- `test_guards.py` - Boolean, numeric, expression, complex functions (math, numpy, lambda)

### Category 3: Priority Resolution
- `test_priority.py` - Conflict resolution, equal priorities

### Category 4: Arc Weight Interaction
- `test_arc_weights.py` - Token consumption/production, complex thresholds (math, numpy, lambda)

### Category 5: Source/Sink Behavior
- `test_source_sink.py` - Infinite generation/consumption

### Category 6: Persistence & Serialization
- `test_persistence.py` - Save/load property integrity

### Category 7: Edge Cases
- `test_edge_cases.py` - Disabled transitions, invalid expressions, large counts

## Running Tests

```bash
# Run all immediate transition validation tests
pytest tests/validation/immediate/ -v

# Run with coverage
pytest tests/validation/immediate/ --cov --cov-report=html

# Run specific category
pytest tests/validation/immediate/test_basic_firing.py -v

# Run with detailed output
pytest tests/validation/immediate/ -vv
```

## Test Count

- **Total Tests:** 41
- **Organized by:** 7 categories (Rate Expressions and UI Dialog are benchmark-only)
- **Focus:** Correctness, < 5 seconds execution time

## Success Criteria

- ✅ 100% pass rate
- ✅ < 5 seconds total execution
- ✅ 95%+ code coverage
- ✅ Clear failure messages

## Related Documentation

- `/doc/validation/immediate/BENCHMARK_PLAN.md` - Test specifications
- `/doc/validation/immediate/TESTING_METHODOLOGY.md` - Implementation guide
- `/doc/validation/immediate/SUMMARY.md` - Overview and status
