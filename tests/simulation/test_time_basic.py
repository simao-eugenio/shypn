"""
Basic Time Advancement Tests

Tests fundamental time computation and advancement in simulation.
Verifies that time moves forward correctly with fixed time steps.

Part of Phase 1 - Critical Tests
"""

import sys
import os
import pytest
import math

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

from shypn.engine.simulation.controller import SimulationController
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc


class TestBasicTimeAdvancement:
    """Test basic time advancement mechanisms."""
    
    def test_initial_time_is_zero(self):
        """
        Test: Time starts at zero
        Expected: controller.time == 0.0 initially
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        assert controller.time == 0.0, "Initial time should be 0.0"
    
    def test_time_advances_by_fixed_step(self):
        """
        Test: Time advances by exactly dt each step
        Expected: After step(dt), time increases by dt
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        dt = 0.5
        initial_time = controller.time
        
        controller.step(dt)
        
        expected_time = initial_time + dt
        assert controller.time == expected_time, \
            f"Time should advance by {dt}, got {controller.time}"
    
    def test_time_advances_multiple_steps(self):
        """
        Test: Time accumulates correctly over multiple steps
        Expected: After N steps of dt, time == N * dt
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        dt = 0.1
        num_steps = 10
        
        for i in range(num_steps):
            controller.step(dt)
        
        expected_time = num_steps * dt
        # Use small epsilon for floating-point comparison
        epsilon = 1e-9
        assert abs(controller.time - expected_time) < epsilon, \
            f"After {num_steps} steps of {dt}, time should be {expected_time}, got {controller.time}"
    
    def test_time_advances_with_varying_dt(self):
        """
        Test: Time advances correctly with varying dt values
        Expected: Time == sum of all dt values
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        dt_values = [0.1, 0.5, 0.2, 1.0, 0.3]
        
        for dt in dt_values:
            controller.step(dt)
        
        expected_time = sum(dt_values)
        epsilon = 1e-9
        assert abs(controller.time - expected_time) < epsilon, \
            f"Time should be {expected_time}, got {controller.time}"
    
    def test_time_is_monotonic(self):
        """
        Test: Time never decreases
        Expected: time(t+1) >= time(t) for all steps
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        dt = 0.5
        num_steps = 20
        
        previous_time = controller.time
        times = [previous_time]
        
        for i in range(num_steps):
            controller.step(dt)
            current_time = controller.time
            
            assert current_time >= previous_time, \
                f"Time decreased from {previous_time} to {current_time} at step {i}"
            
            times.append(current_time)
            previous_time = current_time
        
        # Verify strictly increasing (with positive dt)
        for i in range(1, len(times)):
            assert times[i] > times[i-1], \
                f"Time did not increase at step {i}: {times[i-1]} -> {times[i]}"
    
    def test_time_precision_accumulation(self):
        """
        Test: Floating-point error accumulation over many steps
        Expected: Error remains bounded (< 1e-6 after 1000 steps)
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        dt = 0.001
        num_steps = 1000
        
        for i in range(num_steps):
            controller.step(dt)
        
        expected_time = num_steps * dt  # 1.0
        actual_time = controller.time
        error = abs(actual_time - expected_time)
        
        # Allow for small floating-point accumulation
        max_error = 1e-6
        assert error < max_error, \
            f"Accumulated error {error} exceeds threshold {max_error} after {num_steps} steps"


class TestTimeWithEmptyModel:
    """Test time advancement with no transitions."""
    
    def test_time_advances_without_transitions(self):
        """
        Test: Time advances even with empty model
        Expected: Time increases normally, no transitions fire
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        dt = 1.0
        num_steps = 5
        
        for i in range(num_steps):
            controller.step(dt)
        
        expected_time = num_steps * dt
        assert controller.time == expected_time, \
            f"Time should advance without transitions"


class TestTimeWithSimpleModel:
    """Test time advancement with simple transitions."""
    
    def test_time_advances_with_disabled_transition(self):
        """
        Test: Time advances even when transition is disabled
        Expected: Time increases, transition doesn't fire
        """
        model = ModelCanvasManager()
        
        # Create place and transition (transition will be disabled - no input arc)
        place = model.add_place(x=100, y=100, label="P1")
        place.tokens = 0
        place.initial_marking = 0
        
        transition = model.add_transition(x=200, y=100, label="T1")
        transition.transition_type = 'immediate'
        
        controller = SimulationController(model)
        
        dt = 0.5
        num_steps = 10
        
        for i in range(num_steps):
            controller.step(dt)
        
        expected_time = num_steps * dt
        epsilon = 1e-9
        assert abs(controller.time - expected_time) < epsilon, \
            f"Time should advance normally with disabled transition"
        
        # Verify place tokens unchanged (transition never fired)
        assert place.tokens == 0, "Tokens should not change"


class TestTimeStepValidation:
    """Test time step parameter validation."""
    
    def test_zero_time_step(self):
        """
        Test: Zero dt causes no time advancement
        Expected: Time remains unchanged after step(0)
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        initial_time = controller.time
        controller.step(0.0)
        
        assert controller.time == initial_time, \
            "Time should not advance with dt=0"
    
    def test_negative_time_step_rejected(self):
        """
        Test: Negative dt should be rejected or handled safely
        Expected: Raises ValueError or time remains non-negative
        
        NOTE: This was a CRITICAL safety test that found a bug.
        **BUG FIXED**: Now properly raises ValueError for negative dt!
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        initial_time = controller.time
        
        # Try negative time step - should raise ValueError
        try:
            controller.step(-1.0)
            pytest.fail("Should have raised ValueError for negative time step")
        except ValueError as e:
            # Expected behavior - negative dt rejected
            assert "negative" in str(e).lower() or "non-negative" in str(e).lower(), \
                f"Exception should mention negative dt: {e}"
            # Time should not have changed
            assert controller.time == initial_time, \
                "Time should not change when error is raised"
    
    def test_very_large_time_step(self):
        """
        Test: Very large dt should work but may need warnings
        Expected: Time advances correctly, though may miss events
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        large_dt = 1000.0
        controller.step(large_dt)
        
        assert controller.time == large_dt, \
            "Time should advance even with large dt"
    
    def test_very_small_time_step(self):
        """
        Test: Very small dt should work without precision loss
        Expected: Time advances by exact dt
        """
        model = ModelCanvasManager()
        controller = SimulationController(model)
        
        small_dt = 1e-10
        controller.step(small_dt)
        
        # For very small dt, floating-point precision matters
        assert controller.time > 0, \
            "Time should advance even with very small dt"
        assert controller.time <= small_dt * 2, \
            "Time should not advance more than dt"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
