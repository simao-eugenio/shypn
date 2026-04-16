"""Tests for InteractionGuard - state-based permission control."""

import pytest
from shypn.ui.interaction import InteractionGuard
from shypn.engine.simulation.state import SimulationStateDetector, SimulationState


class MockController:
    """Mock controller for testing."""
    
    def __init__(self):
        self.time = 0.0
        self._running = False
        self.duration = None
    
    @property
    def running(self):
        return self._running


class TestInteractionGuardToolActivation:
    """Test tool activation permissions."""
    
    def test_structural_tools_allowed_in_idle(self):
        """Structural tools (place/transition/arc) should be allowed in IDLE state."""
        controller = MockController()
        controller.time = 0.0
        controller._running = False
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        assert guard.can_activate_tool('place') is True
        assert guard.can_activate_tool('transition') is True
        assert guard.can_activate_tool('arc') is True
    
    def test_structural_tools_blocked_when_running(self):
        """Structural tools should be blocked when simulation is RUNNING."""
        controller = MockController()
        controller.time = 5.0
        controller._running = True
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        assert guard.can_activate_tool('place') is False
        assert guard.can_activate_tool('transition') is False
        assert guard.can_activate_tool('arc') is False
    
    def test_structural_tools_blocked_when_started(self):
        """Structural tools should be blocked when simulation is STARTED (paused)."""
        controller = MockController()
        controller.time = 5.0
        controller._running = False
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        assert guard.can_activate_tool('place') is False
        assert guard.can_activate_tool('transition') is False
        assert guard.can_activate_tool('arc') is False
    
    def test_selection_tools_always_allowed(self):
        """Selection tools should be allowed in all states."""
        controller = MockController()
        
        # Test in IDLE
        controller.time = 0.0
        controller._running = False
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        assert guard.can_activate_tool('select') is True
        assert guard.can_activate_tool('lasso') is True
        
        # Test in RUNNING
        controller.time = 5.0
        controller._running = True
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        assert guard.can_activate_tool('select') is True
        assert guard.can_activate_tool('lasso') is True
    
    def test_token_tools_always_allowed(self):
        """Token manipulation tools should be allowed in all states."""
        controller = MockController()
        
        # Test in IDLE
        controller.time = 0.0
        controller._running = False
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        assert guard.can_activate_tool('add_token') is True
        assert guard.can_activate_tool('remove_token') is True
        
        # Test in RUNNING
        controller.time = 5.0
        controller._running = True
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        assert guard.can_activate_tool('add_token') is True
        assert guard.can_activate_tool('remove_token') is True


class TestInteractionGuardObjectOperations:
    """Test object-level operation permissions."""
    
    def test_delete_allowed_in_idle(self):
        """Object deletion should be allowed in IDLE state."""
        controller = MockController()
        controller.time = 0.0
        controller._running = False
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        assert guard.can_delete_object(None) is True
    
    def test_delete_blocked_when_running(self):
        """Object deletion should be blocked when RUNNING."""
        controller = MockController()
        controller.time = 5.0
        controller._running = True
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        assert guard.can_delete_object(None) is False
    
    def test_move_always_allowed(self):
        """Moving objects should always be allowed (for animation/visualization)."""
        controller = MockController()
        
        # Test in IDLE
        controller.time = 0.0
        controller._running = False
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        assert guard.can_move_object(None) is True
        
        # Test in RUNNING
        controller.time = 5.0
        controller._running = True
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        assert guard.can_move_object(None) is True
    
    def test_edit_properties_blocked_when_running(self):
        """Property editing should be blocked when RUNNING (conservative policy)."""
        controller = MockController()
        controller.time = 5.0
        controller._running = True
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        assert guard.can_edit_properties(None) is False


class TestInteractionGuardTransformHandles:
    """Test transformation handle visibility."""
    
    def test_handles_shown_in_idle(self):
        """Transform handles should be shown in IDLE state."""
        controller = MockController()
        controller.time = 0.0
        controller._running = False
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        assert guard.can_show_transform_handles() is True
    
    def test_handles_hidden_when_running(self):
        """Transform handles should be hidden when RUNNING."""
        controller = MockController()
        controller.time = 5.0
        controller._running = True
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        assert guard.can_show_transform_handles() is False


class TestInteractionGuardReasons:
    """Test human-readable blocking reasons."""
    
    def test_block_reason_for_structural_tools(self):
        """Should provide reason when structural tools are blocked."""
        controller = MockController()
        controller.time = 5.0
        controller._running = True
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        reason = guard.get_block_reason('place')
        assert reason is not None
        assert 'running' in reason.lower() or 'structure' in reason.lower()
    
    def test_no_reason_when_allowed(self):
        """Should return None when action is allowed."""
        controller = MockController()
        controller.time = 0.0
        controller._running = False
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        reason = guard.get_block_reason('place')
        assert reason is None
    
    def test_check_tool_activation_returns_tuple(self):
        """check_tool_activation should return (allowed, reason) tuple."""
        controller = MockController()
        controller.time = 0.0
        controller._running = False
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        # Allowed case
        allowed, reason = guard.check_tool_activation('place')
        assert allowed is True
        assert reason is None
        
        # Blocked case
        controller.time = 5.0
        controller._running = True
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        allowed, reason = guard.check_tool_activation('place')
        assert allowed is False
        assert reason is not None


class TestInteractionGuardStateTransitions:
    """Test guard behavior across state transitions."""
    
    def test_permissions_update_with_state(self):
        """Permissions should update when simulation state changes."""
        controller = MockController()
        controller.time = 0.0
        controller._running = False
        
        detector = SimulationStateDetector(controller)
        guard = InteractionGuard(detector)
        
        # Initially IDLE - structural tools allowed
        assert guard.can_activate_tool('place') is True
        assert detector.state == SimulationState.IDLE
        
        # Start simulation - structural tools blocked
        controller.time = 1.0
        controller._running = True
        assert guard.can_activate_tool('place') is False
        assert detector.state == SimulationState.RUNNING
        
        # Pause simulation - still blocked
        controller._running = False
        assert guard.can_activate_tool('place') is False
        assert detector.state == SimulationState.STARTED
        
        # Reset to IDLE - structural tools allowed again
        controller.time = 0.0
        assert guard.can_activate_tool('place') is True
        assert detector.state == SimulationState.IDLE


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
