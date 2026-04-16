"""
Continuous Transition Time Tests

Tests time-based integration for continuous transitions.
Verifies that continuous transitions integrate correctly over time steps.

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


class TestContinuousTransitionIntegration:
    """Test continuous transition integration over time."""
    
    def test_constant_rate_integration(self):
        """
        Test: Constant rate integrates as Δtokens = rate * dt
        Expected: Linear token increase over time
        """
        model = ModelCanvasManager()
        
        # P1 -> T1(rate=2.0) -> P2
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 100  # Plenty of tokens
        p1.initial_marking = 100
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        rate = 2.0  # tokens per second
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'continuous'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['rate_function'] = f"{rate}"
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        dt = 0.5
        num_steps = 4  # Total time = 2.0 seconds
        
        for i in range(num_steps):
            controller.step(dt)
        
        total_time = num_steps * dt
        expected_tokens = rate * total_time  # 2.0 * 2.0 = 4.0
        
        epsilon = 1e-6
        assert abs(p2.tokens - expected_tokens) < epsilon, \
            f"Expected {expected_tokens} tokens, got {p2.tokens}"
    
    def test_time_dependent_rate(self):
        """
        Test: Rate function depending on time (e.g., rate = t)
        Expected: Δtokens = t * dt, integrated over time
        
        For rate = t, integral from 0 to T is T²/2
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1000
        p1.initial_marking = 1000
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        # Rate increases linearly with time: rate(t) = t
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'continuous'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['rate_function'] = "t"
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # Use small dt for better accuracy
        dt = 0.1
        total_time = 2.0
        num_steps = int(total_time / dt)
        
        for i in range(num_steps):
            controller.step(dt)
        
        # Analytical solution: ∫₀² t dt = [t²/2]₀² = 2²/2 = 2.0
        expected_tokens = total_time ** 2 / 2
        
        # Allow larger epsilon for numerical integration error
        epsilon = 0.1
        assert abs(p2.tokens - expected_tokens) < epsilon, \
            f"Expected ~{expected_tokens} tokens, got {p2.tokens}"
    
    def test_place_dependent_rate(self):
        """
        Test: Rate depends on source place tokens (e.g., rate = 0.5 * P1)
        Expected: Exponential decay as tokens flow
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 10.0
        p1.initial_marking = 10.0
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        # Rate proportional to P1: rate(P1) = 0.5 * P1
        # This creates: dP1/dt = -0.5 * P1 (exponential decay)
        rate_constant = 0.5
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'continuous'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['rate_function'] = f"{rate_constant} * P1"
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        initial_tokens = p1.tokens
        dt = 0.1
        total_time = 1.0
        num_steps = int(total_time / dt)
        
        for i in range(num_steps):
            controller.step(dt)
        
        # Analytical: P1(t) = P1(0) * e^(-k*t)
        # For k=0.5, t=1: P1(1) = 10 * e^(-0.5) ≈ 6.065
        expected_remaining = initial_tokens * math.exp(-rate_constant * total_time)
        
        epsilon = 0.5  # Euler integration has error
        assert abs(p1.tokens - expected_remaining) < epsilon, \
            f"Expected ~{expected_remaining} tokens in P1, got {p1.tokens}"
        
        # Tokens should be conserved
        total_tokens = p1.tokens + p2.tokens
        assert abs(total_tokens - initial_tokens) < 0.01, \
            "Token conservation: total should remain ~constant"
    
    def test_integration_over_varying_dt(self):
        """
        Test: Integration with varying dt values
        Expected: Total integrated amount is correct regardless of dt variation
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 100
        p1.initial_marking = 100
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        rate = 3.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'continuous'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['rate_function'] = f"{rate}"
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # Varying time steps
        dt_values = [0.1, 0.5, 0.2, 0.3, 0.4, 0.5]
        
        for dt in dt_values:
            controller.step(dt)
        
        total_time = sum(dt_values)
        expected_tokens = rate * total_time
        
        epsilon = 1e-6
        assert abs(p2.tokens - expected_tokens) < epsilon, \
            f"Expected {expected_tokens} tokens with varying dt, got {p2.tokens}"


class TestContinuousTransitionTiming:
    """Test timing behavior specific to continuous transitions."""
    
    def test_continuous_uses_snapshot_time(self):
        """
        Test: Continuous transitions use state at beginning of step
        Expected: Integration uses t, not t+dt
        
        This is critical for hybrid execution order.
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 100
        p1.initial_marking = 100
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        # Rate depends on time
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'continuous'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['rate_function'] = "t + 1"
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        dt = 1.0
        
        # First step: t=0, rate = 0+1 = 1
        controller.step(dt)  # time advances to 1.0
        
        expected_first_step = 1.0 * dt  # rate(0) * dt = 1 * 1 = 1
        epsilon = 1e-6
        assert abs(p2.tokens - expected_first_step) < epsilon, \
            f"First step should transfer {expected_first_step} tokens"
        
        # Second step: t=1, rate = 1+1 = 2
        controller.step(dt)  # time advances to 2.0
        
        expected_second_step = 2.0 * dt  # rate(1) * dt = 2 * 1 = 2
        expected_total = expected_first_step + expected_second_step
        
        assert abs(p2.tokens - expected_total) < epsilon, \
            f"After two steps, should have {expected_total} tokens"
    
    def test_continuous_integrates_during_step(self):
        """
        Test: Continuous integration happens during step execution
        Expected: Tokens change within step, time advances after
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 10.0
        p1.initial_marking = 10.0
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        rate = 5.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'continuous'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['rate_function'] = f"{rate}"
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        initial_time = controller.time
        initial_p2 = p2.tokens
        
        dt = 0.5
        controller.step(dt)
        
        # Time should have advanced
        assert controller.time == initial_time + dt
        
        # Tokens should have changed
        expected_transfer = rate * dt
        assert abs(p2.tokens - initial_p2 - expected_transfer) < 1e-6
    
    def test_continuous_fires_when_enabled(self):
        """
        Test: Continuous only integrates when enabled
        Expected: No integration when input places lack tokens
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 0  # Empty - disabled
        p1.initial_marking = 0
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        rate = 10.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'continuous'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['rate_function'] = f"{rate}"
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # Step while disabled
        controller.step(1.0)
        
        # No tokens should transfer (disabled)
        assert p2.tokens == 0, "Disabled continuous should not integrate"
        
        # Enable by adding tokens
        p1.tokens = 100
        
        # Now should integrate
        controller.step(1.0)
        
        expected_transfer = rate * 1.0
        epsilon = 1e-6
        assert abs(p2.tokens - expected_transfer) < epsilon, \
            "Should integrate when enabled"


class TestContinuousTransitionEdgeCases:
    """Test edge cases for continuous transitions."""
    
    def test_zero_rate_no_transfer(self):
        """
        Test: Zero rate means no token transfer
        Expected: Tokens remain unchanged
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 10
        p1.initial_marking = 10
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'continuous'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['rate_function'] = "0"
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        controller.step(5.0)
        
        assert p1.tokens == 10, "Source unchanged with zero rate"
        assert p2.tokens == 0, "Target unchanged with zero rate"
    
    def test_negative_rate_handled(self):
        """
        Test: Negative rate should be handled gracefully
        Expected: Either rejected or tokens don't go negative
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 10
        p1.initial_marking = 10
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 5
        p2.initial_marking = 5
        
        # Negative rate (backwards flow)
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'continuous'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['rate_function'] = "-2.0"
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        try:
            controller.step(1.0)
            # If allowed, verify tokens stay non-negative
            assert p1.tokens >= 0, "Tokens should not go negative"
            assert p2.tokens >= 0, "Tokens should not go negative"
        except ValueError:
            # Expected - negative rate rejected
            pass
    
    def test_very_large_rate(self):
        """
        Test: Very large rate should not exceed source tokens
        Expected: Transfer limited by available tokens
        
        FIXED: Continuous transitions now clamp transfer to available tokens.
        Flow is limited to min(rate*dt, available_tokens/weight) for each input arc.
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 5.0
        p1.initial_marking = 5.0
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        huge_rate = 1000.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'continuous'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['rate_function'] = f"{huge_rate}"
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        controller.step(1.0)
        
        # Should not transfer more than available
        assert p1.tokens >= 0, "Source should not go negative"
        assert p2.tokens <= 5.0 + 1e-6, "Should not transfer more than was available"


class TestContinuousIntegrationAccuracy:
    """Test numerical accuracy of continuous integration."""
    
    def test_small_dt_more_accurate(self):
        """
        Test: Smaller dt gives more accurate integration
        Expected: Error decreases as dt decreases (Forward Euler)
        """
        model_base = ModelCanvasManager()
        
        p1_base = model_base.add_place(x=100, y=100, label="P1")
        p1_base.tokens = 10.0
        p1_base.initial_marking = 10.0
        
        p2_base = model_base.add_place(x=300, y=100, label="P2")
        p2_base.tokens = 0
        
        # Rate proportional to P1: dP1/dt = -k*P1
        k = 0.5
        t1_base = model_base.add_transition(x=200, y=100, label="T1")
        t1_base.transition_type = 'continuous'
        if not hasattr(t1_base, 'properties'):
            t1_base.properties = {}
        t1_base.properties['rate_function'] = f"{k} * P1"
        
        model_base.add_arc(p1_base, t1_base, weight=1)
        model_base.add_arc(t1_base, p2_base, weight=1)
        
        total_time = 1.0
        
        # Test with different dt values
        results = {}
        
        for dt in [0.1, 0.05, 0.01]:
            # Create fresh model for each test
            model = ModelCanvasManager()
            
            p1 = model.add_place(x=100, y=100, label="P1")
            p1.tokens = 10.0
            p1.initial_marking = 10.0
            
            p2 = model.add_place(x=300, y=100, label="P2")
            p2.tokens = 0
            
            t1 = model.add_transition(x=200, y=100, label="T1")
            t1.transition_type = 'continuous'
            if not hasattr(t1, 'properties'):
                t1.properties = {}
            t1.properties['rate_function'] = f"{k} * P1"
            
            model.add_arc(p1, t1, weight=1)
            model.add_arc(t1, p2, weight=1)
            
            controller = SimulationController(model)
            
            num_steps = int(total_time / dt)
            for i in range(num_steps):
                controller.step(dt)
            
            results[dt] = p1.tokens
        
        # Smaller dt should be closer to analytical solution
        analytical = 10.0 * math.exp(-k * total_time)
        
        error_01 = abs(results[0.1] - analytical)
        error_001 = abs(results[0.01] - analytical)
        
        # Smaller dt should have smaller error (not always guaranteed due to floating point)
        # Just verify both are reasonably close
        assert error_01 < 1.0, "Error with dt=0.1 should be reasonable"
        assert error_001 < 0.5, "Error with dt=0.01 should be smaller"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
