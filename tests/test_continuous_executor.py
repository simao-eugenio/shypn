"""Unit tests for ContinuousExecutor strategy class.

Tests the continuous execution strategy extracted from SimulationController
as part of Phase 2.3.1 quality improvements.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from shypn.engine.simulation.executors import ContinuousExecutor


class TestContinuousExecutor:
    """Test suite for ContinuousExecutor class."""
    
    def setup_method(self):
        """Create mock controller for each test."""
        self.mock_controller = Mock()
        self.mock_controller._running = False
        self.mock_controller._stop_requested = False
        self.mock_controller._max_steps = None
        self.mock_controller._steps_executed = 0
        self.mock_controller._time_step = 0.1
        self.mock_controller._steps_per_callback = 1
        self.mock_controller._timeout_id = None
        self.mock_controller.time = 0.0
        self.mock_controller.data_collector = None
        self.mock_controller.validator_manager = None
        self.mock_controller.on_simulation_complete = None
        self.mock_controller.transition_states = {}
        self.mock_controller.behavior_cache = {}
        
        # Mock model with transitions
        self.mock_controller.model = Mock()
        self.mock_controller.model.transitions = []
        self.mock_controller.model.places = []
        
        # Mock settings
        self.mock_controller.settings = Mock()
        self.mock_controller.settings.time_scale = 1.0
        self.mock_controller.settings.estimate_step_count = Mock(return_value=1000)
        
        # Mock methods
        self.mock_controller.get_effective_dt = Mock(return_value=0.1)
        self.mock_controller.step = Mock(return_value=True)
        self.mock_controller._update_enablement_states = Mock()
        self.mock_controller._get_behavior = Mock()
        
        self.executor = ContinuousExecutor(self.mock_controller)
    
    def test_initialization(self):
        """Test executor initializes with controller reference."""
        assert self.executor.controller == self.mock_controller
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', False)
    def test_run_without_glib(self):
        """Test run() returns False when GLib is unavailable."""
        result = self.executor.run()
        assert result is False
        assert not self.mock_controller._running
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_run_already_running(self, mock_glib):
        """Test run() returns False when simulation already running."""
        self.mock_controller._running = True
        result = self.executor.run()
        assert result is False
        mock_glib.timeout_add.assert_not_called()
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_run_success(self, mock_glib):
        """Test run() starts simulation successfully."""
        mock_glib.timeout_add = Mock(return_value=123)
        
        result = self.executor.run(time_step=0.1, max_steps=100)
        
        assert result is True
        assert self.mock_controller._running is True
        assert self.mock_controller._stop_requested is False
        assert self.mock_controller._max_steps == 100
        assert self.mock_controller._steps_executed == 0
        assert self.mock_controller._time_step == 0.1
        self.mock_controller._update_enablement_states.assert_called_once()
        mock_glib.timeout_add.assert_called_once_with(100, self.executor._simulation_loop)
        assert self.mock_controller._timeout_id == 123
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_run_uses_effective_dt(self, mock_glib):
        """Test run() uses get_effective_dt() when time_step is None."""
        mock_glib.timeout_add = Mock(return_value=123)
        self.mock_controller.get_effective_dt = Mock(return_value=0.05)
        
        result = self.executor.run(time_step=None)
        
        assert result is True
        self.mock_controller.get_effective_dt.assert_called_once()
        assert self.mock_controller._time_step == 0.05
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_run_calculates_max_steps_deterministic(self, mock_glib):
        """Test run() calculates max_steps for deterministic simulations."""
        mock_glib.timeout_add = Mock(return_value=123)
        self.mock_controller.settings.estimate_step_count = Mock(return_value=500)
        self.mock_controller.model.transitions = []  # No stochastic transitions
        
        result = self.executor.run(time_step=0.1, max_steps=None)
        
        assert result is True
        assert self.mock_controller._max_steps == 500  # Normal estimate
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_run_calculates_max_steps_stochastic(self, mock_glib):
        """Test run() calculates higher max_steps for stochastic simulations."""
        mock_glib.timeout_add = Mock(return_value=123)
        self.mock_controller.settings.estimate_step_count = Mock(return_value=500)
        
        # Add stochastic transition
        mock_transition = Mock()
        mock_transition.transition_type = 'stochastic'
        self.mock_controller.model.transitions = [mock_transition]
        
        result = self.executor.run(time_step=0.1, max_steps=None)
        
        assert result is True
        assert self.mock_controller._max_steps == 50000  # 100x estimate for tau-leaping
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_run_starts_data_collection(self, mock_glib):
        """Test run() starts data collection and records initial state."""
        mock_glib.timeout_add = Mock(return_value=123)
        self.mock_controller.data_collector = Mock()
        self.mock_controller.time = 0.0
        
        result = self.executor.run()
        
        assert result is True
        self.mock_controller.data_collector.start_collection.assert_called_once()
        self.mock_controller.data_collector.record_state.assert_called_once_with(0.0)
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_run_calculates_steps_per_callback(self, mock_glib):
        """Test run() calculates adaptive step batching for smooth animation."""
        mock_glib.timeout_add = Mock(return_value=123)
        self.mock_controller.settings.time_scale = 60.0  # 60x speedup
        
        result = self.executor.run(time_step=1.0)
        
        assert result is True
        # gui_interval_s = 0.1, time_scale = 60.0, time_step = 1.0
        # model_time_per_gui_update = 0.1 * 60.0 = 6.0
        # steps_per_callback = max(1, int(6.0 / 1.0)) = 6
        assert self.mock_controller._steps_per_callback == 6
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_run_caps_steps_per_callback(self, mock_glib):
        """Test run() caps steps_per_callback at 1000 to prevent UI freeze."""
        mock_glib.timeout_add = Mock(return_value=123)
        self.mock_controller.settings.time_scale = 100000.0  # Extreme speedup
        
        result = self.executor.run(time_step=0.001)
        
        assert result is True
        # Would calculate to 10000 steps, but capped at 1000
        assert self.mock_controller._steps_per_callback == 1000
    
    def test_simulation_loop_stop_requested(self):
        """Test _simulation_loop() stops when stop requested."""
        self.mock_controller._stop_requested = True
        
        result = self.executor._simulation_loop()
        
        assert result is False
        assert self.mock_controller._running is False
        assert self.mock_controller._timeout_id is None
        self.mock_controller.step.assert_not_called()
    
    def test_simulation_loop_max_steps_reached(self):
        """Test _simulation_loop() stops when max_steps reached."""
        self.mock_controller._max_steps = 10
        self.mock_controller._steps_executed = 10
        self.mock_controller._steps_per_callback = 1
        
        result = self.executor._simulation_loop()
        
        assert result is False
        assert self.mock_controller._running is False
        assert self.mock_controller._timeout_id is None
        self.mock_controller.step.assert_not_called()
    
    def test_simulation_loop_step_success(self):
        """Test _simulation_loop() executes steps and continues."""
        self.mock_controller._steps_per_callback = 3
        self.mock_controller._max_steps = 100
        self.mock_controller._steps_executed = 0
        self.mock_controller.step = Mock(return_value=True)
        
        result = self.executor._simulation_loop()
        
        assert result is True  # Continue looping
        assert self.mock_controller.step.call_count == 3
        assert self.mock_controller._steps_executed == 3
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_simulation_loop_step_failure_completes(self, mock_glib):
        """Test _simulation_loop() handles simulation completion (step returns False)."""
        mock_glib.idle_add = Mock()
        self.mock_controller._steps_per_callback = 1
        self.mock_controller.step = Mock(return_value=False)  # Duration reached
        self.mock_controller.data_collector = Mock()
        self.mock_controller.data_collector.is_collecting = True
        self.mock_controller.time = 100.0
        
        result = self.executor._simulation_loop()
        
        assert result is False  # Stop looping
        assert self.mock_controller._running is False
        assert self.mock_controller._timeout_id is None
        self.mock_controller.data_collector.record_state.assert_called_once_with(100.0, force=True)
        self.mock_controller.data_collector.stop_collection.assert_called_once()
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_simulation_loop_runs_validation(self, mock_glib):
        """Test _simulation_loop() runs thermodynamic validation on completion."""
        mock_glib.idle_add = Mock()
        self.mock_controller._steps_per_callback = 1
        self.mock_controller.step = Mock(return_value=False)
        
        # Setup validator
        self.mock_controller.validator_manager = Mock()
        self.mock_controller.validator_manager.__len__ = Mock(return_value=2)
        self.mock_controller.validator_manager.validate_all = Mock()
        self.mock_controller.validator_manager.get_summary = Mock(return_value={'summary': 'data'})
        self.mock_controller.data_collector = Mock()
        
        result = self.executor._simulation_loop()
        
        assert result is False
        self.mock_controller.validator_manager.validate_all.assert_called_once()
        assert self.mock_controller.data_collector.validation_results == {'summary': 'data'}
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_simulation_loop_calls_completion_callback(self, mock_glib):
        """Test _simulation_loop() calls on_simulation_complete callback."""
        mock_glib.idle_add = Mock()
        self.mock_controller._steps_per_callback = 1
        self.mock_controller.step = Mock(return_value=False)
        self.mock_controller.on_simulation_complete = Mock()
        
        result = self.executor._simulation_loop()
        
        assert result is False
        # Verify GLib.idle_add was called with a callback function
        assert mock_glib.idle_add.called
        callback = mock_glib.idle_add.call_args[0][0]
        
        # Execute the deferred callback
        callback()
        self.mock_controller.on_simulation_complete.assert_called_once()
    
    def test_stop_not_running(self):
        """Test stop() does nothing when not running."""
        self.mock_controller._running = False
        
        self.executor.stop()
        
        # Should return early, no state changes
        assert self.mock_controller._stop_requested is False
    
    def test_stop_sets_flag_and_clears_states(self):
        """Test stop() sets flag and clears enablement states."""
        self.mock_controller._running = True
        
        # Create mock transition states
        state1 = Mock()
        state1.enablement_time = 1.0
        state1.scheduled_time = 2.0
        state2 = Mock()
        state2.enablement_time = 3.0
        state2.scheduled_time = 4.0
        self.mock_controller.transition_states = {
            'trans1': state1,
            'trans2': state2
        }
        
        # Create mock behaviors
        behavior1 = Mock()
        behavior1.clear_enablement = Mock()
        behavior2 = Mock()
        behavior2.clear_enablement = Mock()
        self.mock_controller.behavior_cache = {
            'trans1': behavior1,
            'trans2': behavior2
        }
        
        self.executor.stop()
        
        assert self.mock_controller._stop_requested is True
        
        # Verify states cleared
        assert state1.enablement_time is None
        assert state1.scheduled_time is None
        assert state2.enablement_time is None
        assert state2.scheduled_time is None
        
        # Verify behaviors cleared
        behavior1.clear_enablement.assert_called_once()
        behavior2.clear_enablement.assert_called_once()
    
    def test_stop_stops_data_collection(self):
        """Test stop() stops data collection."""
        self.mock_controller._running = True
        self.mock_controller.data_collector = Mock()
        
        self.executor.stop()
        
        self.mock_controller.data_collector.stop_collection.assert_called_once()
    
    @patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True)
    @patch('shypn.engine.simulation.executors.continuous_executor.GLib')
    def test_stop_calls_completion_callback(self, mock_glib):
        """Test stop() calls on_simulation_complete callback."""
        mock_glib.idle_add = Mock()
        self.mock_controller._running = True
        self.mock_controller.on_simulation_complete = Mock()
        
        self.executor.stop()
        
        # Verify GLib.idle_add was called with a callback function
        assert mock_glib.idle_add.called
        callback = mock_glib.idle_add.call_args[0][0]
        
        # Execute the deferred callback
        callback()
        self.mock_controller.on_simulation_complete.assert_called_once()
    
    def test_stop_callback_exception_handling(self):
        """Test stop() handles exceptions in completion callback gracefully."""
        with patch('shypn.engine.simulation.executors.continuous_executor.GLIB_AVAILABLE', True):
            with patch('shypn.engine.simulation.executors.continuous_executor.GLib') as mock_glib:
                mock_glib.idle_add = Mock()
                self.mock_controller._running = True
                self.mock_controller.on_simulation_complete = Mock(side_effect=RuntimeError("Callback error"))
                
                self.executor.stop()
                
                # Get the deferred callback
                callback = mock_glib.idle_add.call_args[0][0]
                
                # Should not raise, but log exception
                result = callback()
                assert result is False  # Don't repeat


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
