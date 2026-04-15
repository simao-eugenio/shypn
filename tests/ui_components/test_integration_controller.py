"""
Integration tests for mode elimination architecture.

Tests the integration of SimulationController with state detection and
buffered settings systems.
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.state import SimulationState
from shypn.engine.simulation.buffered import ValidationError


class MockModelCanvasManager:
    """Mock model for testing."""
    
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []
    
    def register_observer(self, callback):
        pass


class TestControllerIntegration:
    """Test SimulationController integration with new architecture."""
    
    def test_controller_has_state_detector(self):
        """Test controller initializes with state detector."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        assert hasattr(controller, 'state_detector')
        assert controller.state_detector is not None
    
    def test_controller_has_buffered_settings(self):
        """Test controller initializes with buffered settings."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        assert hasattr(controller, 'buffered_settings')
        assert controller.buffered_settings is not None
    
    def test_controller_has_interaction_guard(self):
        """Test controller initializes with interaction guard."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        assert hasattr(controller, 'interaction_guard')
        assert controller.interaction_guard is not None
    
    def test_controller_implements_state_provider(self):
        """Test controller implements StateProvider interface."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        # Check StateProvider interface properties exist
        assert hasattr(controller, 'time')
        assert hasattr(controller, 'running')
        assert hasattr(controller, 'duration')
        
        # Test properties work
        assert controller.time == 0.0
        assert controller.running == False
        assert controller.duration is None  # No duration set
    
    def test_state_detection_idle_when_time_zero(self):
        """Test state detector returns IDLE when time=0."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        state = controller.state_detector.state  # Use property, not method
        assert state == SimulationState.IDLE
    
    def test_state_detection_started_when_paused(self):
        """Test state detector returns STARTED when time>0 but not running."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        # Advance time but don't run
        controller.time = 5.0
        
        state = controller.state_detector.state  # Use property, not method
        assert state == SimulationState.STARTED
    
    def test_state_detection_running_when_executing(self):
        """Test state detector returns RUNNING when executing."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        # Advance time and mark as running
        controller.time = 5.0
        controller._running = True
        
        state = controller.state_detector.state  # Use property, not method
        assert state == SimulationState.RUNNING
    
    def test_buffered_settings_isolation(self):
        """Test buffered settings don't affect live until commit."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        # Get initial value
        original_scale = controller.settings.time_scale
        
        # Change in buffer
        controller.buffered_settings.buffer.time_scale = 100.0
        controller.buffered_settings.mark_dirty()
        
        # Live settings unchanged
        assert controller.settings.time_scale == original_scale
        
        # Commit
        controller.buffered_settings.commit()
        
        # Now live settings updated
        assert controller.settings.time_scale == 100.0
    
    def test_buffered_settings_rollback(self):
        """Test buffered settings rollback discards changes."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        original_scale = controller.settings.time_scale
        
        # Change in buffer
        controller.buffered_settings.buffer.time_scale = 100.0
        controller.buffered_settings.mark_dirty()
        
        # Rollback
        controller.buffered_settings.rollback()
        
        # Commit does nothing (buffer empty)
        controller.buffered_settings.commit()
        
        # Live settings unchanged
        assert controller.settings.time_scale == original_scale
    
    def test_buffered_settings_validation(self):
        """Test buffered settings validate before commit."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        # SimulationSettings validates on property assignment,
        # so invalid values raise ValueError immediately (not on commit).
        # This is correct behavior - validation happens as early as possible.
        with pytest.raises(ValueError, match="Time scale must be positive"):
            controller.buffered_settings.buffer.time_scale = -1.0
        
        # Live settings unchanged (never dirty)
        assert controller.settings.time_scale > 0
    
    def test_can_edit_structure_in_idle(self):
        """Test structure editing allowed in IDLE state."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        can_edit = controller.state_detector.can_edit_structure()
        assert can_edit == True
    
    def test_cannot_edit_structure_when_running(self):
        """Test structure editing blocked when running."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        # Start running
        controller.time = 1.0
        controller._running = True
        
        can_edit = controller.state_detector.can_edit_structure()
        assert can_edit == False
    
    def test_can_manipulate_tokens_always(self):
        """Test token manipulation allowed in all states."""
        model = MockModelCanvasManager()
        controller = SimulationController(model)
        
        # IDLE
        can_manipulate = controller.state_detector.can_manipulate_tokens()
        assert can_manipulate == True
        
        # STARTED
        controller.time = 1.0
        can_manipulate = controller.state_detector.can_manipulate_tokens()
        assert can_manipulate == True
        
        # RUNNING
        controller._running = True
        can_manipulate = controller.state_detector.can_manipulate_tokens()
        assert can_manipulate == True


class TestDialogIntegration:
    """Test SimulationSettingsDialog integration (if GTK available)."""
    
    def test_dialog_imports_successfully(self):
        """Test dialog module can be imported."""
        try:
            from shypn.dialogs.simulation_settings_dialog import SimulationSettingsDialog
            assert SimulationSettingsDialog is not None
        except ImportError as e:
            pytest.skip(f"GTK not available: {e}")
    
    def test_dialog_uses_buffered_settings(self):
        """Test dialog creates buffered settings."""
        try:
            from shypn.dialogs.simulation_settings_dialog import SimulationSettingsDialog
            from shypn.engine.simulation.settings import SimulationSettings
            
            settings = SimulationSettings()
            
            # Create dialog (without showing)
            dialog = SimulationSettingsDialog(settings)
            
            # Check it has buffered settings
            assert hasattr(dialog, 'buffered_settings')
            assert dialog.buffered_settings is not None
            
            # Cleanup
            dialog.destroy()
            
        except ImportError as e:
            pytest.skip(f"GTK not available: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
