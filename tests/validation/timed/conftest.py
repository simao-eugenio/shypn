"""Shared fixtures for timed transition validation tests.

This module provides reusable test fixtures for timed transition behavior validation,
following the same pattern as the immediate transition tests.
"""

import pytest


@pytest.fixture
def timed_ptp_model():
    """Create a basic Place → Timed Transition → Place model.
    
    Returns:
        Tuple of (manager, controller, P0, T, P1)
        - manager: ModelCanvasManager instance
        - controller: SimulationController instance
        - P0: Source place
        - T: Timed transition
        - P1: Target place
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    from shypn.engine.simulation.controller import SimulationController
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P0 = doc_ctrl.add_place(x=100, y=200, label="P0")
    P1 = doc_ctrl.add_place(x=300, y=200, label="P1")
    
    # Create timed transition
    T = doc_ctrl.add_transition(x=200, y=200, label="T")
    T.transition_type = "timed"
    # Default timing: earliest=1.0, latest=1.0
    
    # Connect arcs
    doc_ctrl.add_arc(source=P0, target=T)
    doc_ctrl.add_arc(source=T, target=P1)
    
    # Create controller
    controller = SimulationController(manager)
    
    return (manager, controller, P0, T, P1)


@pytest.fixture
def run_timed_simulation():
    """Execute simulation for specified time.
    
    Returns:
        Function that takes (controller, duration, step_size) and runs simulation
    """
    def _run(controller, duration, step_size=0.1):
        """Run simulation for specified duration.
        
        Args:
            controller: SimulationController instance
            duration: Total simulation time
            step_size: Time step for each iteration (default 0.1)
        """
        steps = int(duration / step_size)
        for _ in range(steps):
            controller.step(time_step=step_size)
    
    return _run


@pytest.fixture
def assert_timed_tokens():
    """Verify token counts with timing information.
    
    Returns:
        Function that takes (P0, P1, expected_p0, expected_p1) and asserts
    """
    def _assert(P0, P1, expected_p0, expected_p1):
        """Assert token counts match expected values.
        
        Args:
            P0: Source place
            P1: Target place
            expected_p0: Expected tokens in P0
            expected_p1: Expected tokens in P1
        """
        assert P0.tokens == expected_p0, f"P0 should have {expected_p0} tokens, got {P0.tokens}"
        assert P1.tokens == expected_p1, f"P1 should have {expected_p1} tokens, got {P1.tokens}"
    
    return _assert


@pytest.fixture
def get_timing_info():
    """Get timing information for a transition.
    
    Returns:
        Function that takes (controller, transition) and returns timing dict
    """
    def _get_info(controller, transition):
        """Get timing information for transition.
        
        Args:
            controller: SimulationController instance
            transition: Transition object
            
        Returns:
            Dict with timing information
        """
        behavior = controller._get_behavior(transition)
        if hasattr(behavior, 'get_timing_info'):
            return behavior.get_timing_info()
        return {}
    
    return _get_info
