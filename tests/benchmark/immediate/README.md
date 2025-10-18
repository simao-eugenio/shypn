# Immediate Transition Benchmark Tests

**Purpose:** Performance and systematic evaluation tests for immediate transitions.

## Test Files

### Category 1: Basic Firing Mechanism
- `bench_basic_firing.py` - Performance tests for immediate firing behavior

### Category 2: Guard Function Evaluation
- `bench_guards.py` - Boolean guards and complex function evaluation

### Category 3: Priority Resolution
- `bench_priority.py` - Conflict resolution and priority handling

### Category 4: Arc Weight Interaction
- `bench_arc_weights.py` - Token consumption/production with complex thresholds

### Category 5: Source/Sink Behavior
- `bench_source_sink.py` - Infinite generation/consumption

### Category 6: Persistence & Serialization
- `bench_persistence.py` - Save/load property integrity

### Category 7: Rate Expression Evaluation
- `bench_rate_expressions.py` - All rate expression types (20 tests)

### Category 8: Edge Cases
- `bench_edge_cases.py` - Boundary conditions and error handling

### Category 9: UI Dialog & Data Validation
- `bench_ui_dialog.py` - Dialog input validation and persistence

## Running Tests

```bash
# Run all immediate transition benchmarks
pytest tests/benchmark/immediate/ --benchmark-only -v

# Run specific category
pytest tests/benchmark/immediate/bench_basic_firing.py --benchmark-only -v

# With verbose output and statistics
pytest tests/benchmark/immediate/ --benchmark-verbose

# Save baseline
pytest tests/benchmark/immediate/ --benchmark-save=immediate_baseline

# Compare with baseline
pytest tests/benchmark/immediate/ --benchmark-compare=immediate_baseline
```

## Test Count

- **Total Tests:** 81
- **Organized by:** 9 categories
- **Focus:** Performance, scalability, complex expressions

## Related Documentation

- `/doc/validation/immediate/BENCHMARK_PLAN.md` - Test specifications
- `/doc/validation/immediate/TESTING_METHODOLOGY.md` - Implementation guide
- `/doc/validation/immediate/SUMMARY.md` - Overview and status
