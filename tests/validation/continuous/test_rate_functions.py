"""Rate function tests for continuous transitions.

Tests different types of rate functions: constant, linear, saturated,
and time-dependent.
"""

import pytest
import math
from shypn.engine.simulation.controller import SimulationController


class TestRateFunctions:
    """Tests for different rate function types."""
    
    def test_constant_rate(self, constant_rate_model):
        """Test constant rate function.
        
        Rate = 2.0 (constant)
        Should produce linear token flow.
        """
        manager, p1, t1, p2, arc_in, arc_out = constant_rate_model
        controller = SimulationController(manager)
        
        # Sample token counts at different times
        samples = []
        time_step = 0.01
        sample_times = [0.0, 0.5, 1.0, 1.5]
        
        steps_taken = 0
        for target_time in sample_times:
            # Calculate steps needed
            steps_needed = int(target_time / time_step) - steps_taken
            
            for _ in range(steps_needed):
                controller.step(time_step=time_step)
            
            steps_taken += steps_needed
            samples.append((target_time, p2.tokens))
        
        # Verify linear growth (rate = 2.0)
        for i in range(1, len(samples)):
            time_diff = samples[i][0] - samples[i-1][0]
            token_diff = samples[i][1] - samples[i-1][1]
            rate = token_diff / time_diff if time_diff > 0 else 0
            
            assert abs(rate - 2.0) < 0.3, \
                f"Expected constant rate ~2.0, got {rate} between t={samples[i-1][0]} and t={samples[i][0]}"
    
    def test_linear_rate(self, token_dependent_model):
        """Test linear rate function (proportional to tokens).
        
        Rate = 0.5 * P1
        Should produce exponential decay of P1.
        """
        manager, p1, t1, p2, arc_in, arc_out = token_dependent_model
        controller = SimulationController(manager)
        
        p1_initial = p1.tokens  # 10.0
        
        # Run for time t
        time_step = 0.01
        total_time = 1.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        p1_final = p1.tokens
        
        # Exponential decay: P1(t) = P1(0) * exp(-k*t), where k = 0.5
        # P1(1.0) = 10 * exp(-0.5) ≈ 6.065
        expected = p1_initial * math.exp(-0.5 * total_time)
        
        # Allow 5% error due to numerical integration
        tolerance = expected * 0.05
        assert abs(p1_final - expected) < tolerance, \
            f"Expected exponential decay to ~{expected}, got {p1_final}"
    
    def test_saturated_rate(self, saturated_rate_model):
        """Test saturated rate function with min().
        
        Rate = min(5.0, P1)
        Should saturate at 5.0 when P1 > 5.
        """
        manager, p1, t1, p2, arc_in, arc_out = saturated_rate_model
        controller = SimulationController(manager)
        
        # Phase 1: P1 > 5, rate should be 5.0
        time_step = 0.01
        
        # Trigger initialization
        controller.step(time_step=0.001)
        t1_behavior = controller.behavior_cache.get(t1.id)
        assert t1_behavior is not None, "Behavior should be initialized"
        
        rate_initial = t1_behavior.evaluate_current_rate()
        assert abs(rate_initial - 5.0) < 0.1, \
            f"Rate should be saturated at 5.0, got {rate_initial}"
        
        # Run until P1 < 5
        for _ in range(600):  # 6 seconds max
            controller.step(time_step=time_step)
            if p1.tokens < 5.0:
                break
        
        # Phase 2: P1 < 5, rate should equal P1
        rate_unsaturated = t1_behavior.evaluate_current_rate()
        p1_current = p1.tokens
        
        assert abs(rate_unsaturated - p1_current) < 0.3, \
            f"Rate should equal P1={p1_current}, got {rate_unsaturated}"
    
    def test_time_dependent_rate(self, time_dependent_model):
        """Test time-dependent rate function.
        
        Rate = 1.0 + 0.5 * time
        Rate should increase linearly with time.
        """
        manager, p1, t1, p2, arc_in, arc_out = time_dependent_model
        controller = SimulationController(manager)
        
        # Trigger initialization
        controller.step(time_step=0.001)
        t1_behavior = controller.behavior_cache.get(t1.id)
        assert t1_behavior is not None, "Behavior should be initialized"
        
        # Sample rates at different times
        time_step = 0.1
        sample_times = [0.0, 1.0, 2.0]
        rate_samples = []
        
        for target_time in sample_times:
            # Step to target time
            current_time = controller.time
            while current_time < target_time - time_step/2:
                controller.step(time_step=time_step)
                current_time = controller.time
            
            rate = t1_behavior.evaluate_current_rate()
            rate_samples.append((controller.time, rate))
        
        # Verify rate increases linearly
        for time, rate in rate_samples:
            expected_rate = 1.0 + 0.5 * time
            assert abs(rate - expected_rate) < 0.2, \
                f"At t={time}, expected rate ~{expected_rate}, got {rate}"
    
    def test_rate_clamping(self, saturated_rate_model):
        """Test that rates are clamped to [min_rate, max_rate].
        
        Model has max_rate=10.0, min_rate=0.0.
        """
        manager, p1, t1, p2, arc_in, arc_out = saturated_rate_model
        controller = SimulationController(manager)
        
        # Trigger initialization
        controller.step(time_step=0.001)
        t1_behavior = controller.behavior_cache.get(t1.id)
        assert t1_behavior is not None, "Behavior should be initialized"
        
        # Test that rate respects max_rate
        p1.set_tokens(100.0)  # Very large value
        
        rate = t1_behavior.evaluate_current_rate()
        max_rate = t1.properties.get('max_rate', float('inf'))
        
        assert rate <= max_rate + 0.01, \
            f"Rate {rate} should be clamped to max_rate {max_rate}"
        
        # Test that rate respects min_rate
        p1.set_tokens(0.0)  # Zero tokens (should disable, but check rate if we force eval)
        # Note: can't easily test min_rate without custom negative rate function
        # This test verifies max_rate clamping
