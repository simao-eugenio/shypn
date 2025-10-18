"""
Unit Tests for Simulation State Detection

Tests the OOP architecture for state-based behavior queries.
"""

import unittest
from unittest.mock import Mock
from shypn.engine.simulation.state import (
    SimulationState,
    SimulationStateDetector,
    StructureEditQuery,
    TokenManipulationQuery,
    ObjectMovementQuery
)


class MockStateProvider:
    """Mock state provider for testing."""
    
    def __init__(self, time=0.0, running=False, duration=None):
        self._time = time
        self._running = running
        self._duration = duration
    
    @property
    def time(self):
        return self._time
    
    @property
    def running(self):
        return self._running
    
    @property
    def duration(self):
        return self._duration


class TestSimulationState(unittest.TestCase):
    """Test SimulationState enum."""
    
    def test_idle_state_properties(self):
        """Test IDLE state properties."""
        state = SimulationState.IDLE
        self.assertTrue(state.is_editing_allowed)
        self.assertFalse(state.is_simulation_active)
        self.assertTrue(state.allows_token_manipulation)
    
    def test_running_state_properties(self):
        """Test RUNNING state properties."""
        state = SimulationState.RUNNING
        self.assertFalse(state.is_editing_allowed)
        self.assertTrue(state.is_simulation_active)
        self.assertTrue(state.allows_token_manipulation)
    
    def test_started_state_properties(self):
        """Test STARTED (paused) state properties."""
        state = SimulationState.STARTED
        self.assertFalse(state.is_editing_allowed)
        self.assertTrue(state.is_simulation_active)
        self.assertTrue(state.allows_token_manipulation)


class TestSimulationStateDetector(unittest.TestCase):
    """Test SimulationStateDetector."""
    
    def test_idle_state_detection(self):
        """Test detection of IDLE state (time = 0)."""
        provider = MockStateProvider(time=0.0, running=False)
        detector = SimulationStateDetector(provider)
        
        self.assertEqual(detector.state, SimulationState.IDLE)
        self.assertTrue(detector.is_idle())
        self.assertFalse(detector.has_started())
        self.assertFalse(detector.is_running())
    
    def test_running_state_detection(self):
        """Test detection of RUNNING state."""
        provider = MockStateProvider(time=5.0, running=True)
        detector = SimulationStateDetector(provider)
        
        self.assertEqual(detector.state, SimulationState.RUNNING)
        self.assertFalse(detector.is_idle())
        self.assertTrue(detector.has_started())
        self.assertTrue(detector.is_running())
    
    def test_started_state_detection(self):
        """Test detection of STARTED (paused) state."""
        provider = MockStateProvider(time=5.0, running=False)
        detector = SimulationStateDetector(provider)
        
        self.assertEqual(detector.state, SimulationState.STARTED)
        self.assertFalse(detector.is_idle())
        self.assertTrue(detector.has_started())
        self.assertFalse(detector.is_running())
    
    def test_can_edit_structure_in_idle(self):
        """Test that structure editing is allowed in IDLE."""
        provider = MockStateProvider(time=0.0)
        detector = SimulationStateDetector(provider)
        
        self.assertTrue(detector.can_edit_structure())
        self.assertIsNone(detector.get_restriction_message("create place"))
    
    def test_cannot_edit_structure_when_started(self):
        """Test that structure editing is blocked when simulation started."""
        provider = MockStateProvider(time=5.0, running=False)
        detector = SimulationStateDetector(provider)
        
        self.assertFalse(detector.can_edit_structure())
        message = detector.get_restriction_message("create place")
        self.assertIsNotNone(message)
        self.assertIn("reset", message.lower())
    
    def test_token_manipulation_always_allowed(self):
        """Test that token manipulation is always allowed."""
        # Test in IDLE
        provider = MockStateProvider(time=0.0)
        detector = SimulationStateDetector(provider)
        self.assertTrue(detector.can_manipulate_tokens())
        
        # Test when RUNNING
        provider._time = 5.0
        provider._running = True
        self.assertTrue(detector.can_manipulate_tokens())
        
        # Test when STARTED
        provider._running = False
        self.assertTrue(detector.can_manipulate_tokens())
    
    def test_state_change_notification(self):
        """Test that state changes trigger observer notifications."""
        provider = MockStateProvider(time=0.0)
        detector = SimulationStateDetector(provider)
        
        # Mock observer
        observer = Mock()
        observer.on_state_changed = Mock()
        detector.add_observer(observer)
        
        # Change state
        provider._time = 5.0
        provider._running = True
        changed = detector.update_state()
        
        self.assertTrue(changed)
        observer.on_state_changed.assert_called_once()
        args = observer.on_state_changed.call_args[0]
        self.assertEqual(args[0], SimulationState.IDLE)  # old state
        self.assertEqual(args[1], SimulationState.RUNNING)  # new state


class TestStateQueries(unittest.TestCase):
    """Test concrete state query classes."""
    
    def test_structure_edit_query(self):
        """Test StructureEditQuery."""
        provider = MockStateProvider(time=0.0)
        detector = SimulationStateDetector(provider)
        query = StructureEditQuery(detector)
        
        # Allowed in IDLE
        allowed, reason = query.check()
        self.assertTrue(allowed)
        self.assertIsNone(reason)
        self.assertTrue(bool(query))  # Test __bool__
        
        # Not allowed when started
        provider._time = 5.0
        allowed, reason = query.check()
        self.assertFalse(allowed)
        self.assertIsNotNone(reason)
        self.assertFalse(bool(query))
    
    def test_token_manipulation_query(self):
        """Test TokenManipulationQuery."""
        provider = MockStateProvider(time=5.0, running=True)
        detector = SimulationStateDetector(provider)
        query = TokenManipulationQuery(detector)
        
        # Always allowed
        allowed, reason = query.check()
        self.assertTrue(allowed)
        self.assertIsNone(reason)
        self.assertTrue(bool(query))
    
    def test_object_movement_query(self):
        """Test ObjectMovementQuery."""
        provider = MockStateProvider(time=0.0)
        detector = SimulationStateDetector(provider)
        query = ObjectMovementQuery(detector)
        
        # Allowed in IDLE
        allowed, reason = query.check()
        self.assertTrue(allowed)
        self.assertIsNone(reason)
        
        # Not allowed when started
        provider._time = 5.0
        allowed, reason = query.check()
        self.assertFalse(allowed)
        self.assertIsNotNone(reason)


if __name__ == '__main__':
    unittest.main()
