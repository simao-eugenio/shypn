"""
Shared pytest fixtures for immediate transition benchmark tests.

This module provides reusable fixtures optimized for performance benchmarking.
"""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from shypn.netobjs import Place, Transition, Arc
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController


@pytest.fixture
def ptp_model():
    """
    Create a simple P-T-P (Place-Transition-Place) model for benchmarking.
    
    Model structure:
        [P1] --[A1]--> [T1] --[A2]--> [P2]
    
    Returns:
        tuple: (manager, P1, T1, P2, A1, A2)
    """
    # Create canvas manager with document controller
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P1.tokens = 0
    P2.tokens = 0
    
    # Create immediate transition
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T1.transition_type = "immediate"
    
    # Create arcs
    A1 = doc_ctrl.add_arc(source=P1, target=T1, weight=1)
    A2 = doc_ctrl.add_arc(source=T1, target=P2, weight=1)
    
    return manager, P1, T1, P2, A1, A2


@pytest.fixture
def large_ptp_model():
    """
    Create a P-T-P model with large initial token count for stress testing.
    
    Model structure:
        [P1(1000)] --[A1]--> [T1] --[A2]--> [P2]
    
    Returns:
        tuple: (manager, P1, T1, P2, A1, A2)
    """
    manager, P1, T1, P2, A1, A2 = ptp_model()
    P1.tokens = 1000
    return manager, P1, T1, P2, A1, A2


@pytest.fixture
def parallel_model():
    """
    Create a model with parallel transitions for concurrency testing.
    
    Model structure:
        [P1] --+--> [T1] --> [P2]
             |
             +--> [T2] --> [P3]
             |
             +--> [T3] --> [P4]
    
    Returns:
        tuple: (model, P1, [T1, T2, T3], [P2, P3, P4])
    """
    model = DocumentModel()
    
    # Source place
    P1 = model.create_place(x=100, y=200, label="P1")
    P1.tokens = 0
    
    # Parallel transitions and target places
    transitions = []
    places = []
    
    for i in range(3):
        T = model.create_transition(x=200, y=100 + i*100, label=f"T{i+1}")
        T.transition_type = "immediate"
        
        P = model.create_place(x=300, y=100 + i*100, label=f"P{i+2}")
        P.tokens = 0
        
        A_in = model.create_arc(source=P1, target=T, weight=1)
        A_out = model.create_arc(source=T, target=P, weight=1)
        
        transitions.append(T)
        places.append(P)
    
    return model, P1, transitions, places


@pytest.fixture
def run_simulation():
    """
    Fixture for running simulation and collecting results.
    
    Returns:
        function: Simulation runner that takes (manager, max_time, max_firings)
    """
    def _run(manager, max_time=10.0, max_firings=None):
        """Run simulation on model canvas manager."""
        controller = SimulationController(manager)
        
        firings = []
        steps = 0
        max_steps = max_firings if max_firings else 100000
        
        # Step-based execution for benchmarking
        time_step = 0.001
        
        while controller.time < max_time and steps < max_steps:
            fired = controller.step(time_step=time_step)
            
            if fired:
                firings.append({
                    'time': controller.time,
                    'step': steps
                })
            
            steps += 1
            
            if max_firings and len(firings) >= max_firings:
                break
        
        # Collect results
        results = {
            'firings': firings,
            'final_time': controller.time,
            'places': {p.name: p.tokens for p in manager.places}
        }
        
        return results
    
    return _run


@pytest.fixture
def benchmark_config():
    """
    Configuration for pytest-benchmark.
    
    Returns:
        dict: Benchmark configuration settings
    """
    return {
        'min_rounds': 5,           # Minimum benchmark rounds
        'min_time': 0.000005,      # Minimum time per round (5μs)
        'max_time': 1.0,           # Maximum time per round
        'warmup': True,            # Enable warmup rounds
        'warmup_iterations': 2,    # Number of warmup iterations
        'calibration_precision': 10,  # Calibration precision
        'disable_gc': True,        # Disable GC during benchmark
    }


@pytest.fixture
def assert_performance():
    """
    Custom assertion for performance requirements.
    
    Returns:
        function: Assertion function for performance bounds
    
    Example:
        >>> assert_performance(stats, max_time=0.001)  # Max 1ms
    """
    def _assert(stats, max_time=None, max_stddev_pct=None):
        """
        Assert performance meets requirements.
        
        Args:
            stats: pytest-benchmark stats object
            max_time: Maximum mean time (seconds)
            max_stddev_pct: Maximum stddev as percentage of mean
        """
        if max_time is not None:
            mean = stats.stats.mean
            assert mean <= max_time, \
                f"Mean time {mean:.6f}s exceeds limit {max_time:.6f}s"
        
        if max_stddev_pct is not None:
            mean = stats.stats.mean
            stddev = stats.stats.stddev
            stddev_pct = (stddev / mean) * 100
            assert stddev_pct <= max_stddev_pct, \
                f"Stddev {stddev_pct:.2f}% exceeds limit {max_stddev_pct}%"
    
    return _assert


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "stress: marks tests as stress tests with large workloads"
    )
    config.addinivalue_line(
        "markers", "memory: marks tests that check memory usage"
    )
