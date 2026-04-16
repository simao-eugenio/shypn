"""Basic continuous transition tests.

Tests fundamental continuous behavior: constant rates, integration accuracy,
enablement logic, and source/sink transitions.
"""

import pytest
from shypn.engine.simulation.controller import SimulationController


class TestBasicContinuous:
    """Basic continuous transition behavior tests."""
    
    def test_constant_rate_flow(self, constant_rate_model):
        """Test continuous flow with constant rate.
        
        Setup:
            P1(10) --[rate=2.0]--> P2(0)
        
        Expected:
            After 1.0 sec, ~2.0 tokens transferred (rate * time)
            Token conservation maintained
        """
        manager, p1, t1, p2, arc_in, arc_out = constant_rate_model
        controller = SimulationController(manager)
        
        places = list(manager.document_controller.places)
        initial_total = sum(p.tokens for p in places)
        p1_initial = p1.tokens
        
        # Run for 1.0 second with small time steps
        time_step = 0.01
        total_time = 1.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        # Verify tokens transferred (rate=2.0, time=1.0 -> ~2.0 tokens)
        expected_transfer = 2.0
        actual_transfer = p2.tokens
        assert abs(actual_transfer - expected_transfer) < 0.1, \
            f"Expected ~{expected_transfer} tokens in P2, got {actual_transfer}"
        
        # Verify conservation
        final_total = sum(p.tokens for p in places)
        assert abs(final_total - initial_total) < 1e-6, \
            f"Tokens not conserved: {initial_total} -> {final_total}"
        
        # Verify P1 decreased by same amount
        assert abs((p1_initial - p1.tokens) - expected_transfer) < 0.1
    
    def test_integration_accuracy(self, constant_rate_model):
        """Test numerical integration accuracy with different step sizes.
        
        Verify that smaller step sizes give more accurate results.
        """
        manager, p1, t1, p2, arc_in, arc_out = constant_rate_model
        
        # Test with large steps
        controller1 = SimulationController(manager)
        time_step_large = 0.1
        total_time = 1.0
        steps_large = int(total_time / time_step_large)
        
        for _ in range(steps_large):
            controller1.step(time_step=time_step_large)
        
        p2_large_step = p2.tokens
        
        # Reset and test with small steps
        p1.set_tokens(10.0)
        p2.set_tokens(0.0)
        controller2 = SimulationController(manager)
        
        time_step_small = 0.01
        steps_small = int(total_time / time_step_small)
        
        for _ in range(steps_small):
            controller2.step(time_step=time_step_small)
        
        p2_small_step = p2.tokens
        
        # Both should be close to 2.0, small step should be more accurate
        expected = 2.0
        error_large = abs(p2_large_step - expected)
        error_small = abs(p2_small_step - expected)
        
        # Small step error should be smaller (or at least not significantly worse)
        assert error_small <= error_large + 0.01, \
            f"Small step error {error_small} should be <= large step error {error_large}"
        
        # Both should be reasonably close
        assert abs(p2_large_step - expected) < 0.15
        assert abs(p2_small_step - expected) < 0.05
    
    def test_continuous_enablement(self, constant_rate_model):
        """Test continuous transition enablement logic.
        
        Continuous transitions require positive tokens (> 0), not >= weight.
        """
        manager, p1, t1, p2, arc_in, arc_out = constant_rate_model
        controller = SimulationController(manager)
        
        # Initially enabled (P1 has 10 tokens)
        behavior = controller.behavior_cache.get(t1.id)
        if behavior is None:
            # Trigger initialization
            controller.step(time_step=0.001)
            behavior = controller.behavior_cache.get(t1.id)
        
        assert behavior is not None, "Behavior should be initialized"
        can_fire, reason = behavior.can_fire()
        assert can_fire, f"Should be enabled initially: {reason}"
        assert "enabled" in reason.lower() or "continuous" in reason.lower()
        
        # Drain P1 almost completely
        time_step = 0.01
        for _ in range(500):  # 5 seconds
            if p1.tokens <= 0.1:
                break
            controller.step(time_step=time_step)
        
        # Should become disabled when P1 reaches 0
        p1.set_tokens(0.0)
        can_fire, reason = behavior.can_fire()
        assert not can_fire, "Should be disabled when input is empty"
        assert "empty" in reason.lower() or "not" in reason.lower()
    
    def test_source_transition(self, source_sink_model):
        """Test source transition (generates tokens from outside).
        
        Source transitions are always enabled and don't consume from input.
        """
        manager, p1, t_source, t_sink, arc_source_out, arc_sink_in = source_sink_model
        controller = SimulationController(manager)
        
        p1_initial = p1.tokens
        
        # Run for 1.0 second (source rate = 1.0)
        time_step = 0.01
        total_time = 1.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        # P1 should have gained tokens from source (~1.0)
        # But also lost some to sink (~0.5)
        # Net change: +1.0 - 0.5 = +0.5
        p1_final = p1.tokens
        net_change = p1_final - p1_initial
        
        # Should be positive (source produces more than sink consumes)
        assert net_change > 0.3, f"Expected net increase, got {net_change}"
        assert net_change < 0.7, f"Expected ~0.5 increase, got {net_change}"
    
    def test_sink_transition(self, source_sink_model):
        """Test sink transition (removes tokens from system).
        
        Sink transitions consume but don't produce output.
        """
        manager, p1, t_source, t_sink, arc_source_out, arc_sink_in = source_sink_model
        controller = SimulationController(manager)
        
        # Disable source to test sink in isolation
        t_source.properties['rate_function'] = '0.0'  # Stop source
        
        p1_initial = p1.tokens  # 5.0
        
        # Run for 1.0 second (sink rate = 0.5)
        time_step = 0.01
        total_time = 1.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        # P1 should have lost ~0.5 tokens
        p1_final = p1.tokens
        consumed = p1_initial - p1_final
        
        assert abs(consumed - 0.5) < 0.1, f"Expected ~0.5 consumed, got {consumed}"
    
    def test_zero_rate_no_flow(self, constant_rate_model):
        """Test that zero rate produces no flow.
        
        When rate function evaluates to 0, no tokens should move.
        """
        manager, p1, t1, p2, arc_in, arc_out = constant_rate_model
        
        # Set rate to zero
        t1.properties['rate_function'] = '0.0'
        
        controller = SimulationController(manager)
        
        p1_initial = p1.tokens
        p2_initial = p2.tokens
        
        # Run for some time
        time_step = 0.01
        for _ in range(100):
            controller.step(time_step=time_step)
        
        p1_final = p1.tokens
        p2_final = p2.tokens
        
        # No change should occur
        assert abs(p1_final - p1_initial) < 1e-6
        assert abs(p2_final - p2_initial) < 1e-6
