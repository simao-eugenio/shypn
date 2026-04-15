"""
Shared pytest fixtures for immediate transition validation tests.

This module provides reusable fixtures for creating test models,
running simulations, and performing common assertions.
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
    Create a simple P-T-P (Place-Transition-Place) model.
    
    Model structure:
        [P1] --[A1]--> [T1] --[A2]--> [P2]
    
    Returns:
        tuple: (manager, P1, T1, P2, A1, A2)
            - manager: ModelCanvasManager instance
            - P1: Input place (tokens=0)
            - T1: Immediate transition
            - P2: Output place (tokens=0)
            - A1: Input arc (P1 → T1, weight=1)
            - A2: Output arc (T1 → P2, weight=1)
    
    Example:
        >>> manager, P1, T1, P2, A1, A2 = ptp_model
        >>> P1.tokens = 5
        >>> # Run simulation
        >>> assert P2.tokens == 5
    """
    # Create canvas manager with document controller
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    # Create places using document controller
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
def run_simulation():
    """
    Fixture for running simulation and collecting results.
    
    Returns:
        function: Simulation runner that takes (manager, max_time, max_firings)
    
    Example:
        >>> results = run_simulation(manager, max_time=10.0)
        >>> assert len(results['firings']) > 0
    """
    def _run(manager, max_time=10.0, max_firings=None):
        """
        Run simulation on model canvas manager.
        
        Args:
            manager: ModelCanvasManager instance with Petri net model
            max_time: Maximum simulation time
            max_firings: Maximum number of firings (None = unlimited)
        
        Returns:
            dict: Simulation results
                - 'firings': List of firing events
                - 'final_time': Final simulation time
                - 'places': Dict of place_name -> final_tokens
        """
        controller = SimulationController(manager)
        
        firings = []
        steps = 0
        max_steps = max_firings if max_firings else 100000
        
        # Step-based execution (no GLib dependency for testing)
        # Each step advances by small time increment
        time_step = 0.001  # 1ms steps
        
        while controller.time < max_time and steps < max_steps:
            # Execute one simulation step
            fired = controller.step(time_step=time_step)
            
            # Record firing if it occurred
            if fired:
                firings.append({
                    'time': controller.time,
                    'step': steps
                })
            
            steps += 1
            
            # Safety: if too many steps, break
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
def assert_tokens():
    """
    Custom assertion for place token counts.
    
    Returns:
        function: Assertion function that takes (place, expected_tokens)
    
    Example:
        >>> assert_tokens(P1, 5)
    """
    def _assert(place, expected):
        """Assert place has expected token count."""
        assert place.tokens == expected, \
            f"Expected {place.name}.tokens == {expected}, got {place.tokens}"
    
    return _assert


@pytest.fixture
def assert_firing_count():
    """
    Custom assertion for number of firings.
    
    Returns:
        function: Assertion function that takes (results, expected_count)
    
    Example:
        >>> assert_firing_count(results, 5)
    """
    def _assert(results, expected):
        """Assert number of firings matches expected."""
        actual = len(results['firings'])
        assert actual == expected, \
            f"Expected {expected} firings, got {actual}"
    
    return _assert


@pytest.fixture
def assert_firing_time():
    """
    Custom assertion for firing time.
    
    Returns:
        function: Assertion function that takes (results, index, expected_time)
    
    Example:
        >>> assert_firing_time(results, 0, 0.0)  # First firing at t=0
    """
    def _assert(results, index, expected_time):
        """Assert firing occurred at expected time."""
        firings = results['firings']
        assert len(firings) > index, \
            f"No firing at index {index}, only {len(firings)} firings occurred"
        
        actual_time = firings[index]['time']
        assert actual_time == expected_time, \
            f"Expected firing {index} at t={expected_time}, got t={actual_time}"
    
    return _assert


@pytest.fixture
def mock_persistency_manager():
    """
    Mock persistency manager for UI dialog tests.
    
    Returns:
        MockPersistencyManager: Mock with is_dirty flag
    
    Example:
        >>> pm = mock_persistency_manager
        >>> pm.mark_dirty()
        >>> assert pm.is_dirty == True
    """
    class MockPersistencyManager:
        def __init__(self):
            self.is_dirty = False
        
        def mark_dirty(self):
            self.is_dirty = True
        
        def mark_clean(self):
            self.is_dirty = False
    
    return MockPersistencyManager()


@pytest.fixture
def mock_data_collector():
    """
    Mock data collector for simulation diagnostics.
    
    Returns:
        MockDataCollector: Mock with recording capability
    
    Example:
        >>> dc = mock_data_collector
        >>> dc.record_event('firing', {...})
    """
    class MockDataCollector:
        def __init__(self):
            self.events = []
        
        def record_event(self, event_type, data):
            self.events.append({
                'type': event_type,
                'data': data
            })
        
        def get_events(self, event_type=None):
            if event_type:
                return [e for e in self.events if e['type'] == event_type]
            return self.events
    
    return MockDataCollector()


@pytest.fixture
def priority_policy():
    """
    Return PRIORITY conflict resolution policy for explicit priority testing.
    
    Returns:
        ConflictResolutionPolicy.PRIORITY
    
    Example:
        >>> controller = SimulationController(manager)
        >>> controller.set_conflict_policy(priority_policy)
    """
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    return ConflictResolutionPolicy.PRIORITY


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests that require UI/GTK (deselect with '-m \"not ui\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
