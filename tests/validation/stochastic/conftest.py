"""Shared fixtures for stochastic transition validation tests."""

import pytest
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController


@pytest.fixture
def stochastic_ptp_model():
    """Create a basic Place → Stochastic Transition → Place model.
    
    Returns:
        Tuple of (manager, controller, P0, T, P1) where:
        - manager: ModelCanvasManager instance
        - controller: SimulationController instance  
        - P0: Source place
        - T: Stochastic transition
        - P1: Target place
    """
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P0 = doc_ctrl.add_place(x=100, y=200, label="P0")
    P1 = doc_ctrl.add_place(x=300, y=200, label="P1")
    
    # Create stochastic transition with rate=1.0
    T = doc_ctrl.add_transition(x=200, y=200, label="T")
    T.transition_type = "stochastic"
    T.properties = {'rate': 1.0, 'max_burst': 1}  # Start with burst=1 for predictability
    
    # Connect arcs
    doc_ctrl.add_arc(source=P0, target=T)
    doc_ctrl.add_arc(source=T, target=P1)
    
    # Create controller
    controller = SimulationController(manager)
    
    return manager, controller, P0, T, P1


@pytest.fixture
def run_stochastic_simulation():
    """Helper to run simulation steps until a condition is met or timeout.
    
    Returns:
        Function that takes (controller, max_steps, check_func) and runs simulation
    """
    def _run(controller, max_steps=1000, check_func=None, time_step=0.1):
        """Run simulation for up to max_steps.
        
        Args:
            controller: SimulationController instance
            max_steps: Maximum number of steps to run
            check_func: Optional function(controller) -> bool to check completion
            time_step: Time step size (default 0.1)
            
        Returns:
            Tuple of (steps_taken, final_time, converged)
        """
        for step in range(max_steps):
            controller.step(time_step=time_step)
            
            if check_func and check_func(controller):
                return step + 1, controller.time, True
        
        return max_steps, controller.time, False
    
    return _run


@pytest.fixture
def assert_stochastic_tokens():
    """Verify token counts in stochastic model.
    
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
def get_stochastic_info():
    """Get stochastic information for a transition.
    
    Returns:
        Function that takes (controller, transition) and returns stochastic dict
    """
    def _get_info(controller, transition):
        """Get stochastic information for transition.
        
        Args:
            controller: SimulationController instance
            transition: Transition object
            
        Returns:
            Dict with stochastic information (rate, scheduled time, etc.)
        """
        behavior = controller._get_behavior(transition)
        if hasattr(behavior, 'get_stochastic_info'):
            return behavior.get_stochastic_info()
        
        # Manual extraction if no method available
        info = {
            'rate': getattr(behavior, 'rate', None),
            'max_burst': getattr(behavior, 'max_burst', None),
            'enablement_time': getattr(behavior, '_enablement_time', None),
            'scheduled_fire_time': getattr(behavior, '_scheduled_fire_time', None),
            'sampled_burst': getattr(behavior, '_sampled_burst', None),
            'current_time': controller.time
        }
        return info
    
    return _get_info
