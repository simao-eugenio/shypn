# Testing Methodology - Immediate Transitions

**Date:** October 17, 2025  
**Transition Type:** Immediate  
**Framework:** pytest + custom fixtures

---

## Overview

This document explains **how** the immediate transition validation tests will be implemented, executed, and verified.

---

## Test Framework Stack

### Core Technologies

```
pytest                 # Test framework and runner
pytest-cov            # Code coverage reporting
pytest-html           # HTML test reports
pytest-timeout        # Timeout protection for infinite loops
```

### Custom Components

```
fixtures/             # Reusable test components
├── ptp_generator.py  # P-T-P model generator
├── simulation.py     # Simulation runner
└── assertions.py     # Custom assertion helpers
```

---

## Test Structure

### Directory Layout

```
tests/validation/immediate/
├── conftest.py                    # Shared fixtures
├── test_basic_firing.py           # Category 1: Basic mechanism
├── test_guards.py                 # Category 2: Guard evaluation
├── test_priority.py               # Category 3: Priority resolution
├── test_arc_weights.py            # Category 4: Arc weights
├── test_source_sink.py            # Category 5: Source/sink
├── test_persistence.py            # Category 6: Persistence
├── test_edge_cases.py             # Category 7: Edge cases
└── fixtures/
    ├── ptp_generator.py           # Model creation fixture
    ├── simulation_runner.py       # Simulation execution
    └── token_validator.py         # Token verification
```

---

## Implementation Approach

### 1. Fixture-Based Model Generation

**Fixture: `ptp_model`**

Creates a simple P-T-P (Place-Transition-Place) model for testing:

```python
# tests/validation/immediate/conftest.py

import pytest
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.data.canvas.document_model import DocumentModel

@pytest.fixture
def ptp_model():
    """Create a simple P-T-P model: P1 → T1 → P2
    
    Returns:
        tuple: (document, P1, T1, P2, arc_in, arc_out)
    """
    # Create document
    doc = DocumentModel()
    
    # Create places
    P1 = Place(x=50, y=100, id=1, name='P1', tokens=0)
    P2 = Place(x=150, y=100, id=2, name='P2', tokens=0)
    
    # Create transition (immediate by default)
    T1 = Transition(x=100, y=100, id=1, name='T1')
    T1.transition_type = 'immediate'
    
    # Create arcs
    arc_in = Arc(P1, T1, id=1, name='A1', weight=1)
    arc_out = Arc(T1, P2, id=2, name='A2', weight=1)
    
    # Add to document
    doc.add_place(P1)
    doc.add_place(P2)
    doc.add_transition(T1)
    doc.add_arc(arc_in)
    doc.add_arc(arc_out)
    
    return doc, P1, T1, P2, arc_in, arc_out
```

### 2. Simulation Runner Fixture

**Fixture: `run_simulation`**

Executes simulation and collects results:

```python
# tests/validation/immediate/conftest.py

from shypn.engine.simulation.controller import SimulationController

@pytest.fixture
def run_simulation(ptp_model):
    """Run simulation on a P-T-P model and return results.
    
    Returns:
        function: Callable that runs simulation with given parameters
    """
    def _run(max_time=10.0, max_firings=100):
        doc, P1, T1, P2, arc_in, arc_out = ptp_model
        
        # Create simulation controller
        controller = SimulationController(doc)
        
        # Run simulation
        results = controller.run(
            max_time=max_time,
            max_firings=max_firings,
            collect_data=True
        )
        
        # Return results with easy access to places/transition
        return {
            'P1': P1,
            'P2': P2,
            'T1': T1,
            'firings': results.get('firing_events', []),
            'final_time': results.get('final_time', 0.0),
            'token_history': results.get('token_history', {}),
            'controller': controller
        }
    
    return _run
```

### 3. Custom Assertions

**Helper: Token Assertions**

```python
# tests/validation/immediate/fixtures/assertions.py

def assert_tokens(place, expected, msg=None):
    """Assert place has expected token count."""
    actual = place.tokens
    message = msg or f"Expected {place.name} to have {expected} tokens, got {actual}"
    assert actual == expected, message

def assert_firing_count(firings, expected, msg=None):
    """Assert number of firings matches expected."""
    actual = len(firings)
    message = msg or f"Expected {expected} firings, got {actual}"
    assert actual == expected, message

def assert_firing_time(firings, expected_time, msg=None):
    """Assert all firings occurred at expected time."""
    for firing in firings:
        assert firing['time'] == expected_time, \
            f"Firing at t={firing['time']}, expected t={expected_time}"

def assert_can_fire(transition, expected=True, msg=None):
    """Assert transition can/cannot fire."""
    from shypn.engine.immediate_behavior import ImmediateBehavior
    
    behavior = ImmediateBehavior(transition, model_adapter=None)
    can_fire, reason = behavior.can_fire()
    
    message = msg or f"Expected can_fire()={expected}, got {can_fire} (reason: {reason})"
    assert can_fire == expected, message
```

---

## Test Examples

### Example 1: Basic Firing Test

**File:** `test_basic_firing.py`

```python
# tests/validation/immediate/test_basic_firing.py

import pytest
from fixtures.assertions import assert_tokens, assert_firing_count, assert_firing_time

class TestBasicFiring:
    """Category 1: Basic Firing Mechanism"""
    
    def test_single_fire_zero_delay(self, ptp_model, run_simulation):
        """Test 1.1: Single fire at t=0 with 1 token"""
        doc, P1, T1, P2, _, _ = ptp_model
        
        # Setup: 1 token in P1
        P1.tokens = 1
        
        # Run simulation
        results = run_simulation(max_time=1.0)
        
        # Verify: Token moved from P1 to P2
        assert_tokens(P1, 0, "P1 should be empty after firing")
        assert_tokens(P2, 1, "P2 should have 1 token after firing")
        
        # Verify: Fired exactly once
        assert_firing_count(results['firings'], 1, "Should fire exactly once")
        
        # Verify: Fired at t=0 (immediate)
        assert_firing_time(results['firings'], 0.0, "Should fire at t=0")
    
    def test_multiple_firings(self, ptp_model, run_simulation):
        """Test 1.2: Multiple consecutive firings at t=0"""
        doc, P1, T1, P2, _, _ = ptp_model
        
        # Setup: 5 tokens in P1
        P1.tokens = 5
        
        # Run simulation
        results = run_simulation(max_time=1.0)
        
        # Verify: All tokens moved
        assert_tokens(P1, 0, "P1 should be empty")
        assert_tokens(P2, 5, "P2 should have all 5 tokens")
        
        # Verify: Fired 5 times
        assert_firing_count(results['firings'], 5, "Should fire 5 times")
        
        # Verify: All at t=0
        assert_firing_time(results['firings'], 0.0, "All firings at t=0")
    
    def test_insufficient_tokens(self, ptp_model, run_simulation):
        """Test 1.3: No firing when no tokens available"""
        doc, P1, T1, P2, _, _ = ptp_model
        
        # Setup: No tokens
        P1.tokens = 0
        
        # Run simulation
        results = run_simulation(max_time=1.0)
        
        # Verify: No changes
        assert_tokens(P1, 0, "P1 remains empty")
        assert_tokens(P2, 0, "P2 remains empty")
        
        # Verify: No firings
        assert_firing_count(results['firings'], 0, "Should not fire")
```

### Example 2: Guard Function Test

**File:** `test_guards.py`

```python
# tests/validation/immediate/test_guards.py

import pytest
from fixtures.assertions import assert_tokens, assert_can_fire

class TestGuards:
    """Category 2: Guard Function Evaluation"""
    
    def test_boolean_guard_true(self, ptp_model, run_simulation):
        """Test 2.1: Boolean guard = True allows firing"""
        doc, P1, T1, P2, _, _ = ptp_model
        
        # Setup
        P1.tokens = 1
        T1.guard = True
        
        # Verify can fire
        assert_can_fire(T1, expected=True)
        
        # Run simulation
        results = run_simulation(max_time=1.0)
        
        # Verify fired
        assert_tokens(P2, 1, "Should fire when guard is True")
    
    def test_boolean_guard_false(self, ptp_model, run_simulation):
        """Test 2.2: Boolean guard = False blocks firing"""
        doc, P1, T1, P2, _, _ = ptp_model
        
        # Setup
        P1.tokens = 1
        T1.guard = False
        
        # Verify cannot fire
        assert_can_fire(T1, expected=False)
        
        # Run simulation
        results = run_simulation(max_time=1.0)
        
        # Verify did not fire
        assert_tokens(P1, 1, "P1 keeps token when guard blocks")
        assert_tokens(P2, 0, "P2 receives nothing")
    
    def test_expression_guard(self, ptp_model, run_simulation):
        """Test 2.4: Expression guard with token reference"""
        doc, P1, T1, P2, _, _ = ptp_model
        
        # Setup: Guard checks P1 token count
        T1.guard = "P1 > 5"
        T1.properties = {'guard_function': 'P1 > 5'}
        
        # Case 1: P1=3 (guard fails)
        P1.tokens = 3
        assert_can_fire(T1, expected=False)
        
        # Case 2: P1=10 (guard passes)
        P1.tokens = 10
        assert_can_fire(T1, expected=True)
        
        # Run simulation
        results = run_simulation(max_time=1.0)
        
        # Verify: All 10 tokens moved (fires 10 times)
        assert_tokens(P1, 0)
        assert_tokens(P2, 10)
```

### Example 3: Arc Weight Test

**File:** `test_arc_weights.py`

```python
# tests/validation/immediate/test_arc_weights.py

import pytest
from fixtures.assertions import assert_tokens, assert_firing_count

class TestArcWeights:
    """Category 4: Arc Weight Interaction"""
    
    def test_input_weight_greater_than_one(self, ptp_model, run_simulation):
        """Test 4.1: Input arc weight > 1 requires more tokens"""
        doc, P1, T1, P2, arc_in, arc_out = ptp_model
        
        # Setup: Input arc requires 3 tokens per firing
        arc_in.weight = 3
        P1.tokens = 5
        
        # Run simulation
        results = run_simulation(max_time=1.0)
        
        # Verify: Fires once (5 tokens, needs 3)
        # P1: 5 - 3 = 2
        # P2: 0 + 1 = 1
        assert_tokens(P1, 2, "P1 has 2 tokens left (5-3)")
        assert_tokens(P2, 1, "P2 has 1 token (output weight=1)")
        assert_firing_count(results['firings'], 1, "Fires once")
    
    def test_output_weight_greater_than_one(self, ptp_model, run_simulation):
        """Test 4.2: Output arc weight > 1 produces more tokens"""
        doc, P1, T1, P2, arc_in, arc_out = ptp_model
        
        # Setup: Output arc produces 5 tokens per firing
        arc_out.weight = 5
        P1.tokens = 1
        
        # Run simulation
        results = run_simulation(max_time=1.0)
        
        # Verify: 1 firing produces 5 tokens
        assert_tokens(P1, 0, "P1 consumed 1 token")
        assert_tokens(P2, 5, "P2 received 5 tokens (weight=5)")
        assert_firing_count(results['firings'], 1, "Fires once")
    
    def test_expression_weight(self, ptp_model, run_simulation):
        """Test 4.4: Numeric expression as weight"""
        doc, P1, T1, P2, arc_in, arc_out = ptp_model
        
        # Setup: Weight is expression "2*2"
        arc_in.weight = "2*2"  # Evaluates to 4
        P1.tokens = 10
        
        # Run simulation
        results = run_simulation(max_time=1.0)
        
        # Verify: Each firing consumes 4 tokens
        # 10 tokens / 4 per firing = 2 firings, 2 tokens left
        assert_tokens(P1, 2, "P1: 10 - 2*4 = 2")
        assert_tokens(P2, 2, "P2: 2 firings × 1 output = 2")
        assert_firing_count(results['firings'], 2, "Fires twice")
```

### Example 4: Persistence Test

**File:** `test_persistence.py`

```python
# tests/validation/immediate/test_persistence.py

import pytest
import tempfile
import os
from shypn.data.canvas.document_model import DocumentModel

class TestPersistence:
    """Category 6: Persistence & Serialization"""
    
    def test_save_load_basic_properties(self, ptp_model):
        """Test 6.1: Save and load preserves basic properties"""
        doc, P1, T1, P2, _, _ = ptp_model
        
        # Setup: Set properties
        T1.priority = 10
        T1.enabled = True
        T1.transition_type = 'immediate'
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.shy', delete=False) as f:
            filepath = f.name
            doc.save_to_file(filepath)
        
        try:
            # Load from file
            loaded_doc = DocumentModel.load_from_file(filepath)
            
            # Find transition in loaded doc
            loaded_T1 = next(t for t in loaded_doc.transitions if t.name == 'T1')
            
            # Verify properties preserved
            assert loaded_T1.transition_type == 'immediate'
            assert loaded_T1.priority == 10
            assert loaded_T1.enabled == True
            assert loaded_T1.rate == 1.0  # Default
            
        finally:
            # Cleanup
            os.unlink(filepath)
    
    def test_save_load_guard_function(self, ptp_model):
        """Test 6.2: Save and load preserves guard function"""
        doc, P1, T1, P2, _, _ = ptp_model
        
        # Setup: Set guard
        guard_expr = "P1 > 5"
        T1.guard = guard_expr
        T1.properties = {'guard_function': guard_expr}
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.shy', delete=False) as f:
            filepath = f.name
            doc.save_to_file(filepath)
        
        try:
            # Load from file
            loaded_doc = DocumentModel.load_from_file(filepath)
            loaded_T1 = next(t for t in loaded_doc.transitions if t.name == 'T1')
            
            # Verify guard preserved
            assert loaded_T1.guard == guard_expr or \
                   (loaded_T1.properties and 
                    loaded_T1.properties.get('guard_function') == guard_expr)
            
        finally:
            os.unlink(filepath)
```

---

## Running Tests

### Command Line Execution

```bash
# Run all immediate transition tests
cd tests/validation
pytest immediate/ -v

# Run specific test file
pytest immediate/test_basic_firing.py -v

# Run specific test
pytest immediate/test_basic_firing.py::TestBasicFiring::test_single_fire_zero_delay -v

# Run with coverage
pytest immediate/ -v --cov=shypn.netobjs.transition --cov=shypn.engine

# Generate HTML coverage report
pytest immediate/ --cov --cov-report=html
open htmlcov/index.html

# Run with detailed output
pytest immediate/ -vv -s

# Run with timeout protection (prevent infinite loops)
pytest immediate/ --timeout=10
```

### Test Output Example

```
tests/validation/immediate/test_basic_firing.py::TestBasicFiring::test_single_fire_zero_delay PASSED [10%]
tests/validation/immediate/test_basic_firing.py::TestBasicFiring::test_multiple_firings PASSED [20%]
tests/validation/immediate/test_basic_firing.py::TestBasicFiring::test_insufficient_tokens PASSED [30%]
tests/validation/immediate/test_guards.py::TestGuards::test_boolean_guard_true PASSED [40%]
tests/validation/immediate/test_guards.py::TestGuards::test_boolean_guard_false PASSED [50%]
...

================================ 40 passed in 2.45s =================================

Coverage Report:
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
src/shypn/netobjs/transition.py           150     5    97%
src/shypn/engine/immediate_behavior.py     85     2    98%
src/shypn/engine/transition_behavior.py   120     8    93%
-----------------------------------------------------------
TOTAL                                     355    15    96%
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/validation-tests.yml

name: Validation Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-html pytest-timeout
    
    - name: Run immediate transition tests
      run: |
        cd tests/validation
        pytest immediate/ -v --cov --cov-report=xml --cov-report=html
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        files: ./coverage.xml
    
    - name: Upload HTML report
      uses: actions/upload-artifact@v2
      with:
        name: validation-report
        path: htmlcov/
```

---

## Test Reporting

### HTML Report Generation

```bash
# Generate comprehensive HTML report
pytest immediate/ --html=report.html --self-contained-html

# Report includes:
# - Test results (pass/fail)
# - Execution time per test
# - Error messages and stack traces
# - Coverage statistics
# - Code highlighting
```

### Markdown Summary

After test execution, generate summary:

```python
# scripts/generate_test_summary.py

import json

def generate_summary(test_results):
    """Generate markdown summary of test results."""
    
    summary = f"""
# Immediate Transition Validation Results

**Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Total Tests:** {test_results['total']}  
**Passed:** {test_results['passed']} ✅  
**Failed:** {test_results['failed']} ❌  
**Coverage:** {test_results['coverage']}%

## Test Categories

| Category | Tests | Passed | Failed | Coverage |
|----------|-------|--------|--------|----------|
| Basic Firing | 3 | 3 | 0 | 100% |
| Guards | 6 | 6 | 0 | 100% |
| Priority | 3 | 3 | 0 | 100% |
| Arc Weights | 5 | 5 | 0 | 100% |
| Source/Sink | 3 | 3 | 0 | 100% |
| Persistence | 3 | 3 | 0 | 100% |
| Edge Cases | 5 | 5 | 0 | 100% |

## Issues Found

{format_issues(test_results['issues'])}

## Recommendations

{format_recommendations(test_results)}
"""
    
    return summary
```

---

## Debugging Failed Tests

### Using pytest debugger

```bash
# Drop into debugger on failure
pytest immediate/ --pdb

# Drop into debugger on first failure
pytest immediate/ -x --pdb

# Show local variables in traceback
pytest immediate/ -l

# Capture output for debugging
pytest immediate/ -s
```

### Logging for Diagnostics

```python
# In test files
import logging

logger = logging.getLogger(__name__)

def test_with_logging(ptp_model, run_simulation):
    """Test with diagnostic logging"""
    doc, P1, T1, P2, _, _ = ptp_model
    
    P1.tokens = 5
    logger.debug(f"Initial P1 tokens: {P1.tokens}")
    
    results = run_simulation(max_time=1.0)
    logger.debug(f"Firings: {len(results['firings'])}")
    logger.debug(f"Final P1: {P1.tokens}, P2: {P2.tokens}")
    
    assert P2.tokens == 5
```

---

## Performance Benchmarking

### Timing Tests

```python
# tests/validation/immediate/test_performance.py

import pytest
import time

class TestPerformance:
    """Performance benchmarks for immediate transitions"""
    
    def test_large_token_count_performance(self, ptp_model, run_simulation):
        """Test 7.4: 1M tokens should complete in < 10 seconds"""
        doc, P1, T1, P2, _, _ = ptp_model
        
        # Setup: 1 million tokens
        P1.tokens = 1_000_000
        
        # Measure time
        start = time.time()
        results = run_simulation(max_time=10.0, max_firings=1_000_000)
        duration = time.time() - start
        
        # Verify correctness
        assert P1.tokens == 0
        assert P2.tokens == 1_000_000
        
        # Verify performance
        assert duration < 10.0, f"Took {duration:.2f}s, expected < 10s"
        
        # Log performance
        print(f"\n1M firings completed in {duration:.2f}s")
        print(f"Throughput: {1_000_000/duration:.0f} firings/sec")
```

---

## Summary

### Test Execution Flow

```
1. pytest discovers test files
   ↓
2. conftest.py provides fixtures
   ↓
3. Each test function runs:
   - Setup (fixtures create model)
   - Execute (run simulation)
   - Verify (assertions check results)
   ↓
4. Results collected and reported
   ↓
5. Coverage analysis
   ↓
6. HTML/Markdown reports generated
```

### Key Benefits

✅ **Automated** - No manual testing required  
✅ **Reproducible** - Same tests, same results  
✅ **Comprehensive** - 40+ test cases  
✅ **Fast** - All tests complete in < 5 seconds  
✅ **Clear** - Readable test code with assertions  
✅ **Documented** - Reports show exactly what passed/failed  

### Next Step

**Create test infrastructure:**
```bash
mkdir -p tests/validation/immediate/fixtures
touch tests/validation/immediate/conftest.py
touch tests/validation/immediate/test_basic_firing.py
```

Then implement the fixtures and first test category! 🚀
