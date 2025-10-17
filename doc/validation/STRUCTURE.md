# Validation & Benchmark Structure

**Date:** October 17, 2025  
**Purpose:** Organize validation tests and performance benchmarks

---

## Directory Organization

### Validation Tests vs Benchmarks

The testing framework is split into two complementary structures:

```
tests/
├── validation/              # Functional correctness tests
│   ├── immediate/          # Immediate transition validation
│   │   ├── conftest.py                # Shared fixtures
│   │   ├── test_basic_firing.py       # Correctness tests
│   │   ├── test_guards.py
│   │   ├── test_priority.py
│   │   ├── test_arc_weights.py
│   │   ├── test_source_sink.py
│   │   ├── test_persistence.py
│   │   └── test_edge_cases.py
│   │
│   ├── timed/              # Timed transition validation
│   ├── stochastic/         # Stochastic transition validation
│   └── continuous/         # Continuous transition validation
│
└── benchmark/              # Performance & systematic evaluation
    ├── immediate/          # Immediate transition benchmarks
    │   ├── conftest.py                # Shared benchmark fixtures
    │   ├── bench_basic_firing.py      # Performance tests
    │   ├── bench_guards.py            # Guard evaluation benchmarks
    │   ├── bench_rate_expressions.py  # Complex rate evaluation
    │   ├── bench_priority.py
    │   ├── bench_arc_weights.py
    │   ├── bench_source_sink.py
    │   └── bench_edge_cases.py
    │
    ├── timed/              # Timed transition benchmarks
    ├── stochastic/         # Stochastic transition benchmarks
    └── continuous/         # Continuous transition benchmarks
```

---

## Purpose of Each Structure

### `/tests/validation/` - Functional Correctness

**Goal:** Verify that transitions behave correctly according to Petri net semantics.

**Focus:**
- ✅ Correct token flow
- ✅ Guard evaluation accuracy
- ✅ Priority resolution correctness
- ✅ Arc weight calculations
- ✅ Source/sink behavior
- ✅ Persistence integrity
- ✅ Edge case handling

**Execution:**
```bash
# Run all validation tests
pytest tests/validation/ -v

# Run specific transition type
pytest tests/validation/immediate/ -v

# With coverage
pytest tests/validation/immediate/ --cov --cov-report=html
```

**Test Characteristics:**
- Fast execution (< 5 seconds total)
- Deterministic results
- Clear pass/fail assertions
- CI/CD integration

---

### `/tests/benchmark/` - Performance & Systematic Evaluation

**Goal:** Measure performance, stress-test edge cases, and evaluate complex expressions.

**Focus:**
- ⚡ Performance metrics (execution time, memory)
- 📊 Scalability (large token counts, many transitions)
- 🔬 Complex expression evaluation
- 🧪 Systematic property exploration
- 📈 Comparative analysis across implementations

**Execution:**
```bash
# Run all benchmarks
pytest tests/benchmark/ --benchmark-only

# Run specific transition type
pytest tests/benchmark/immediate/ --benchmark-only

# With detailed output
pytest tests/benchmark/immediate/ --benchmark-verbose
```

**Test Characteristics:**
- Longer execution (seconds to minutes)
- Performance-focused
- Statistical analysis
- Generates performance reports

---

## Rate Expression Evaluation (Benchmark Focus)

### Enhanced Rate Testing

While immediate transitions ignore the `rate` property for firing delay, the **rate expression evaluation mechanism** itself needs systematic testing.

### Rate Expression Types

#### 1. Numeric Rate
```python
T1.rate = 1.5  # Constant numeric value
T1.rate = {'rate': 1.5}  # Dictionary form
```

#### 2. Expression String
```python
T1.rate = "2 * 3.14"  # Simple expression
T1.rate = {'rate': "2 * 3.14"}

T1.rate = "P1 * 0.5"  # Place-dependent
T1.rate = {'rate': "P1 * 0.5"}

T1.rate = "t * 2.0"  # Time-dependent
T1.rate = {'rate': "t * 2.0"}
```

#### 3. Function Expression
```python
T1.rate = "min(P1, 5)"  # Built-in function
T1.rate = {'rate': "min(P1, 5)"}

T1.rate = "max(P1, P2) / 2"  # Multi-place
T1.rate = {'rate': "max(P1, P2) / 2"}

T1.rate = "exp(-t/10)"  # Exponential decay
T1.rate = {'rate': "exp(-t/10)"}
```

#### 4. Complex Expression
```python
T1.rate = "P1 * 0.5 if P1 > 10 else 0.1"  # Conditional
T1.rate = {'rate': "P1 * 0.5 if P1 > 10 else 0.1"}

T1.rate = "(P1 + P2) / (P1 * P2 + 1)"  # Multi-variable
T1.rate = {'rate': "(P1 + P2) / (P1 * P2 + 1)"}

T1.rate = "sin(t * 3.14 / 10) * P1"  # Trigonometric
T1.rate = {'rate': "sin(t * 3.14 / 10) * P1"}
```

#### 5. Lambda Function (Advanced)
```python
T1.rate = lambda marking, t: marking['P1'] * 0.5
T1.rate = {'rate': lambda marking, t: marking['P1'] * 0.5}

T1.rate = lambda marking, t: min(marking['P1'], marking['P2']) / t if t > 0 else 0
T1.rate = {'rate': lambda marking, t: min(marking['P1'], marking['P2']) / t if t > 0 else 0}
```

---

## Benchmark Test Categories

### 1. Expression Parsing Performance
- Time to parse various expression types
- Memory usage during parsing
- Caching effectiveness

### 2. Expression Evaluation Performance
- Evaluation time for different expression complexities
- Impact of place/transition count on evaluation
- Comparison: string vs lambda vs numeric

### 3. Expression Correctness
- Numeric accuracy (float precision)
- Edge cases (division by zero, overflow)
- Complex expression validation

### 4. Scalability Testing
- Large token counts (1M+ tokens)
- Many transitions (100+ transitions)
- Deep expression nesting
- Long simulation times

### 5. Rate Expression Variety
- All expression types tested systematically
- Combinations of numeric, string, function, lambda
- Error handling for invalid expressions

---

## Example Benchmark Test

### File: `/tests/benchmark/immediate/bench_rate_expressions.py`

```python
import pytest
from fixtures.ptp_model import create_ptp_model
from src.simulation.controller import SimulationController

class TestRateExpressionBenchmark:
    """Benchmark rate expression evaluation performance."""
    
    def bench_numeric_rate(self, benchmark):
        """Benchmark numeric rate evaluation."""
        doc, P1, T1, P2, _, _ = create_ptp_model()
        T1.rate = 1.5
        P1.tokens = 1000
        
        def run():
            controller = SimulationController(doc)
            controller.run(max_time=1.0)
            return P2.tokens
        
        result = benchmark(run)
        assert result == 1000
    
    def bench_expression_rate(self, benchmark):
        """Benchmark expression rate evaluation."""
        doc, P1, T1, P2, _, _ = create_ptp_model()
        T1.rate = {'rate': "P1 * 0.5"}
        P1.tokens = 1000
        
        def run():
            controller = SimulationController(doc)
            controller.run(max_time=1.0)
            return P2.tokens
        
        result = benchmark(run)
        assert result == 1000
    
    def bench_function_rate(self, benchmark):
        """Benchmark function rate evaluation."""
        doc, P1, T1, P2, _, _ = create_ptp_model()
        T1.rate = {'rate': "min(P1, 100)"}
        P1.tokens = 1000
        
        def run():
            controller = SimulationController(doc)
            controller.run(max_time=1.0)
            return P2.tokens
        
        result = benchmark(run)
        assert result == 1000
    
    def bench_lambda_rate(self, benchmark):
        """Benchmark lambda rate evaluation."""
        doc, P1, T1, P2, _, _ = create_ptp_model()
        T1.rate = lambda marking, t: marking['P1'] * 0.5
        P1.tokens = 1000
        
        def run():
            controller = SimulationController(doc)
            controller.run(max_time=1.0)
            return P2.tokens
        
        result = benchmark(run)
        assert result == 1000
    
    @pytest.mark.parametrize("expression", [
        "1.5",
        "P1 * 0.5",
        "min(P1, 100)",
        "max(P1, P2) / 2",
        "exp(-t/10)",
        "P1 * 0.5 if P1 > 10 else 0.1",
        "sin(t * 3.14 / 10) * P1",
    ])
    def bench_expression_variety(self, benchmark, expression):
        """Benchmark various expression types."""
        doc, P1, T1, P2, _, _ = create_ptp_model()
        T1.rate = {'rate': expression}
        P1.tokens = 100
        
        def run():
            controller = SimulationController(doc)
            controller.run(max_time=1.0)
            return P2.tokens
        
        result = benchmark(run)
        # Just verify it runs without error
        assert isinstance(result, (int, float))
```

---

## Implementation Plan Updates

### Phase 1: Validation Tests (Week 1)
- ✅ Create `tests/validation/immediate/` structure
- ✅ Implement basic correctness tests
- ✅ Set up pytest infrastructure

### Phase 2: Benchmark Tests (Week 2)
- [ ] Create `tests/benchmark/immediate/` structure
- [ ] Implement performance benchmarks
- [ ] Add rate expression evaluation tests
- [ ] Set up pytest-benchmark infrastructure

### Phase 3: Rate Expression Testing (Week 2-3)
- [ ] Test all expression types (numeric, string, function, lambda)
- [ ] Test expression parsing performance
- [ ] Test expression evaluation accuracy
- [ ] Test edge cases and error handling

### Phase 4: Scalability Testing (Week 3)
- [ ] Large token count tests (1M+)
- [ ] Many transition tests (100+)
- [ ] Long simulation time tests
- [ ] Memory profiling

### Phase 5: Reporting (Week 3-4)
- [ ] Generate performance reports
- [ ] Create comparison charts
- [ ] Document performance characteristics
- [ ] Identify optimization opportunities

---

## Running Tests

### Validation Only
```bash
# Fast correctness tests
pytest tests/validation/ -v
```

### Benchmarks Only
```bash
# Performance tests
pytest tests/benchmark/ --benchmark-only
```

### Both
```bash
# Everything
pytest tests/ -v
```

### With Reports
```bash
# HTML coverage + benchmark report
pytest tests/validation/ --cov --cov-report=html
pytest tests/benchmark/ --benchmark-only --benchmark-save=baseline
pytest tests/benchmark/ --benchmark-only --benchmark-compare=baseline
```

---

## Success Metrics

### Validation Tests
- ✅ 100% pass rate
- ✅ < 5 seconds total execution
- ✅ 95%+ code coverage
- ✅ Clear failure messages

### Benchmark Tests
- ✅ Consistent performance baselines
- ✅ No performance regressions
- ✅ Scalability within acceptable limits
- ✅ All expression types tested

---

## Related Documentation

- `/doc/validation/README.md` - Validation framework overview
- `/doc/validation/immediate/BENCHMARK_PLAN.md` - Test cases (WHAT to test)
- `/doc/validation/immediate/TESTING_METHODOLOGY.md` - Implementation guide (HOW to test)
- `/doc/validation/immediate/README.md` - Immediate transition overview

---

**Next:** Create benchmark structure and implement rate expression evaluation tests! 🚀
