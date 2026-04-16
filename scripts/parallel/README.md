# Parallel Reachability Scripts

Utility scripts for testing, benchmarking, and validating parallel reachability analysis.

## Scripts

### `validate_correctness.py`

Validates that parallel exploration produces identical results to sequential baseline.

**Usage:**
```bash
python validate_correctness.py [--verbose] [--models all] [--workers 4]
```

**Checks:**
- State count matches sequential
- State sets are identical (no missing/extra states)
- Deadlock detection consistency
- Graph structure matches

**Example:**
```bash
# Validate all models with 4 workers
python validate_correctness.py --verbose

# Validate specific models
python validate_correctness.py --models simple,medium

# Test with 8 workers
python validate_correctness.py --workers 8
```

### `benchmark_reachability.py`

Measures performance characteristics and speedup across different configurations.

**Usage:**
```bash
python benchmark_reachability.py [--workers 1,2,4,8] [--sizes small,medium,large] [--plot]
```

**Metrics:**
- Wall-clock time per configuration
- Speedup vs sequential baseline
- Parallel efficiency (%)
- States/second throughput

**Example:**
```bash
# Benchmark with default settings
python benchmark_reachability.py

# Test scaling from 1 to 16 workers
python benchmark_reachability.py --workers 1,2,4,8,16

# Generate plots
python benchmark_reachability.py --plot

# Benchmark large state spaces
python benchmark_reachability.py --max-states 50000 --sizes large
```

**Output:**
- CSV file with detailed timing data
- Console report with speedup metrics
- Performance plots (if `--plot` and matplotlib available)

## Test Models

Scripts use standardized test models:

| Model | Places | Description | Expected Speedup |
|-------|--------|-------------|------------------|
| `simple` | 5-10 | Minimal structure | 2× (overhead dominates) |
| `medium` | 20-50 | Moderate branching | 4-6× (sweet spot) |
| `large` | 100-200 | Complex structure | 6× (maximum) |
| `deadlock` | Variable | Terminal states | N/A (correctness) |
| `concurrent` | Variable | Independent transitions | High (stress test) |

## Requirements

**Core:**
- Python 3.8+
- shypn library

**Optional:**
- matplotlib (for plots)
- pandas (for advanced analysis)

## Performance Expectations

### Expected Speedup Characteristics

```
Workers  | Small | Medium | Large
---------|-------|--------|-------
1        | 1.0×  | 1.0×   | 1.0×
2        | 1.5×  | 1.8×   | 1.9×
4        | 2.0×  | 3.5×   | 3.8×
8        | 2.5×  | 6.0×   | 6.5×
16       | 2.5×  | 6.5×   | 7.0×
```

### Efficiency Guidelines

- **Small nets (<20 places):** Overhead dominates, sequential often faster
- **Medium nets (20-100 places):** 60-80% efficiency with 4-8 workers
- **Large nets (>100 places):** 70-90% efficiency with 8+ workers

### Overhead Sources

1. **Process spawn:** ~50ms per worker
2. **Manager operations:** ~10ms per shared dict access
3. **Serialization:** Proportional to marking size
4. **Context switching:** Increases with worker count

## Troubleshooting

### Low Speedup

**Symptoms:** Parallel slower than sequential

**Causes:**
- Network too small (overhead dominates)
- Too many workers (>2× CPU count)
- High serialization cost (large markings)

**Solutions:**
- Use fewer workers for small nets
- Limit to CPU count workers
- Consider sequential mode for tiny models

### Incorrect Results

**Symptoms:** State count mismatch, missing states

**Causes:**
- Race condition in state discovery
- Queue synchronization issue
- Manager dict inconsistency

**Solutions:**
- Run `validate_correctness.py --verbose`
- Check worker logs for exceptions
- Verify multiprocessing.Manager working correctly

### Memory Issues

**Symptoms:** Out of memory errors

**Causes:**
- Each worker duplicates model
- Large state space in memory
- Queue accumulation

**Solutions:**
- Reduce `num_workers`
- Lower `max_states` limit
- Use streaming mode (Phase 3)

## Development

### Adding New Test Models

Edit `create_test_models()` in each script:

```python
def create_test_models():
    return {
        'my_model': create_my_test_model(),
        # ... existing models ...
    }

def create_my_test_model():
    # Build and return model
    pass
```

### Custom Benchmarks

Extend `ReachabilityBenchmark` class:

```python
class MyBenchmark(ReachabilityBenchmark):
    def benchmark_custom(self, model):
        # Custom benchmark logic
        pass
```

## See Also

- **Implementation:** `src/shypn/topology/behavioral/parallel_reachability.py`
- **Tests:** `tests/topology/behavioral/test_parallel_reachability.py`
- **Documentation:** `doc/features/PARALLEL_REACHABILITY_IMPLEMENTATION.md`
- **Plan:** `doc/features/PARALLEL_REACHABILITY_ANALYSIS.md`
