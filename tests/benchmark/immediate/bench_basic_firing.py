"""
Benchmark tests for basic firing performance of immediate transitions.

Tests measure firing performance under various conditions.
"""

import pytest


def test_single_firing_performance(benchmark, ptp_model, run_simulation):
    """
    Benchmark single firing of immediate transition.
    
    Measures time to fire once with 1 token.
    Performance target: < 1ms
    """
    model, P1, T1, P2, A1, A2 = ptp_model
    P1.tokens = 1
    
    # Benchmark
    result = benchmark(run_simulation, model, max_time=1.0)
    
    # Verify correctness
    assert P2.tokens == 1
    assert len(result['firings']) == 1


def test_multiple_firings_performance(benchmark, ptp_model, run_simulation):
    """
    Benchmark multiple firings of immediate transition.
    
    Measures time to fire 100 times.
    Performance target: < 10ms
    """
    model, P1, T1, P2, A1, A2 = ptp_model
    P1.tokens = 100
    
    # Benchmark
    result = benchmark(run_simulation, model, max_time=1.0)
    
    # Verify correctness
    assert P2.tokens == 100
    assert len(result['firings']) == 100


@pytest.mark.slow
def test_high_volume_firing_performance(benchmark, ptp_model, run_simulation):
    """
    Benchmark high-volume firing (1000 firings).
    
    Stress test with 1000 tokens.
    Performance target: < 100ms
    """
    model, P1, T1, P2, A1, A2 = ptp_model
    P1.tokens = 1000
    
    # Benchmark
    result = benchmark(run_simulation, model, max_time=10.0)
    
    # Verify correctness
    assert P2.tokens == 1000
    assert len(result['firings']) == 1000


def test_firing_with_empty_input(benchmark, ptp_model, run_simulation):
    """
    Benchmark handling of disabled transition.
    
    Measures overhead of checking disabled transition.
    Performance target: < 0.1ms
    """
    model, P1, T1, P2, A1, A2 = ptp_model
    P1.tokens = 0
    
    # Benchmark
    result = benchmark(run_simulation, model, max_time=1.0)
    
    # Verify correctness
    assert P2.tokens == 0
    assert len(result['firings']) == 0


@pytest.mark.stress
def test_sequential_firings_stress(benchmark, ptp_model, run_simulation):
    """
    Stress test with 10000 sequential firings.
    
    Tests performance at scale.
    Performance target: < 1s
    """
    model, P1, T1, P2, A1, A2 = ptp_model
    P1.tokens = 10000
    
    # Benchmark
    result = benchmark(run_simulation, model, max_time=100.0)
    
    # Verify correctness
    assert P2.tokens == 10000
    assert len(result['firings']) == 10000
