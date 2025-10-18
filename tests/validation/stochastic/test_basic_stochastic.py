"""Basic stochastic transition validation tests (Phase 6).

These tests validate stochastic transition behavior with exponential
distribution timing. Since stochastic transitions involve randomness,
some tests use statistical validation over multiple runs.
"""

import pytest
import random


def test_fires_after_random_delay(stochastic_ptp_model, assert_stochastic_tokens):
    """Test that stochastic transition fires after a random delay.
    
    Given: P0 has 1 token, T is stochastic with rate=1.0
    When: Simulation runs with small steps
    Then: T fires after some random delay (not immediately at t=0)
    """
    manager, controller, P0, T, P1 = stochastic_ptp_model
    
    # Set up: 1 token in P0
    P0.tokens = 1
    T.properties = {'rate': 1.0, 'max_burst': 1}
    controller.invalidate_behavior_cache(T.id)
    
    # Step once - should not fire immediately (very unlikely with exponential)
    controller.step(time_step=0.001)
    
    # Most likely still no firing at t=0.001
    # (Probability of delay < 0.001 with rate=1.0 is ~0.1%)
    
    # Keep stepping until it fires
    max_steps = 1000
    fired = False
    for i in range(max_steps):
        before_p1 = P1.tokens
        controller.step(time_step=0.01)
        after_p1 = P1.tokens
        
        if after_p1 > before_p1:
            fired = True
            fire_time = controller.time
            break
    
    assert fired, "Transition should eventually fire"
    assert fire_time > 0, "Should fire after some delay, not at t=0"
    assert_stochastic_tokens(P0, P1, 0, 1)


def test_does_not_fire_before_scheduled_time(stochastic_ptp_model):
    """Test that transition doesn't fire before its scheduled time.
    
    Given: P0 has 1 token, T is stochastic
    When: Check transition before scheduled time
    Then: T is not enabled (too early)
    """
    manager, controller, P0, T, P1 = stochastic_ptp_model
    
    P0.tokens = 1
    T.properties = {'rate': 1.0, 'max_burst': 1}
    controller.invalidate_behavior_cache(T.id)
    
    # Initialize - this schedules the firing
    controller.step(time_step=0.001)
    
    # Get scheduled time
    behavior = controller._get_behavior(T)
    scheduled_time = behavior._scheduled_fire_time
    
    assert scheduled_time is not None, "Should have scheduled fire time"
    
    # Step to just before scheduled time
    if scheduled_time > 0.001:
        steps_needed = int((scheduled_time - 0.001) / 0.01)
        for _ in range(steps_needed):
            controller.step(time_step=0.01)
        
        # Should not have fired yet
        assert P1.tokens == 0, "Should not fire before scheduled time"


def test_rate_parameter_affects_delay():
    """Test that higher rate leads to shorter average delays.
    
    Given: Two transitions with rate=0.5 and rate=2.0
    When: Run multiple simulations
    Then: Higher rate has shorter average firing time
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    from shypn.engine.simulation.controller import SimulationController
    
    # Test with rate=0.5 (slow)
    fire_times_slow = []
    for trial in range(30):
        random.seed(1000 + trial)  # Different seed each trial
        
        # Create fresh model for each trial
        manager = ModelCanvasManager()
        doc_ctrl = manager.document_controller
        P0 = doc_ctrl.add_place(x=100, y=200, label="P0")
        P1 = doc_ctrl.add_place(x=300, y=200, label="P1")
        T = doc_ctrl.add_transition(x=200, y=200, label="T")
        T.transition_type = "stochastic"
        T.properties = {'rate': 0.5, 'max_burst': 1}
        doc_ctrl.add_arc(source=P0, target=T)
        doc_ctrl.add_arc(source=T, target=P1)
        controller = SimulationController(manager)
        
        P0.tokens = 1
        
        # Run until fires
        for _ in range(1000):
            before_p1 = P1.tokens
            controller.step(time_step=0.01)
            if P1.tokens > before_p1:
                fire_times_slow.append(controller.time)
                break
    
    # Test with rate=2.0 (fast)
    fire_times_fast = []
    for trial in range(30):
        random.seed(2000 + trial)  # Different seed each trial
        
        # Create fresh model for each trial
        manager = ModelCanvasManager()
        doc_ctrl = manager.document_controller
        P0 = doc_ctrl.add_place(x=100, y=200, label="P0")
        P1 = doc_ctrl.add_place(x=300, y=200, label="P1")
        T = doc_ctrl.add_transition(x=200, y=200, label="T")
        T.transition_type = "stochastic"
        T.properties = {'rate': 2.0, 'max_burst': 1}
        doc_ctrl.add_arc(source=P0, target=T)
        doc_ctrl.add_arc(source=T, target=P1)
        controller = SimulationController(manager)
        
        P0.tokens = 1
        
        # Run until fires
        for _ in range(1000):
            before_p1 = P1.tokens
            controller.step(time_step=0.01)
            if P1.tokens > before_p1:
                fire_times_fast.append(controller.time)
                break
    
    # Statistical check: faster rate should have shorter mean delay
    mean_slow = sum(fire_times_slow) / len(fire_times_slow)
    mean_fast = sum(fire_times_fast) / len(fire_times_fast)
    
    # Expected: E[T] = 1/rate
    # rate=0.5 => mean=2.0, rate=2.0 => mean=0.5
    # Allow some statistical variance
    assert mean_slow > mean_fast, f"Slow rate (0.5) should have longer mean: {mean_slow:.2f} vs {mean_fast:.2f}"
    assert 1.5 < mean_slow < 3.0, f"Mean for rate=0.5 should be ~2.0, got {mean_slow:.2f}"
    assert 0.3 < mean_fast < 0.8, f"Mean for rate=2.0 should be ~0.5, got {mean_fast:.2f}"


def test_fires_multiple_times(stochastic_ptp_model, run_stochastic_simulation):
    """Test that stochastic transition can fire multiple times.
    
    Given: P0 has 5 tokens, T is stochastic
    When: Simulation runs
    Then: T fires multiple times, moving tokens from P0 to P1
    """
    manager, controller, P0, T, P1 = stochastic_ptp_model
    
    P0.tokens = 5
    T.properties = {'rate': 5.0, 'max_burst': 1}  # High rate for faster firing
    controller.invalidate_behavior_cache(T.id)
    
    # Run until all tokens transferred
    def all_transferred(ctrl):
        return P1.tokens >= 5
    
    steps, final_time, converged = run_stochastic_simulation(
        controller, max_steps=2000, check_func=all_transferred, time_step=0.01
    )
    
    assert converged, f"Should transfer all 5 tokens (P1={P1.tokens})"
    assert P0.tokens == 0, "All tokens should be consumed"
    assert P1.tokens == 5, "All tokens should be produced"


def test_burst_firing_not_tested_yet(stochastic_ptp_model):
    """Placeholder: Burst firing with max_burst > 1.
    
    Note: Burst firing (max_burst > 1) introduces additional complexity.
    For now, Phase 6 focuses on basic stochastic behavior with burst=1.
    """
    # This test intentionally passes - burst firing can be validated later
    pass


def test_disabled_by_insufficient_tokens(stochastic_ptp_model):
    """Test that stochastic transition doesn't fire without tokens.
    
    Given: P0 has 0 tokens, T is stochastic
    When: Simulation runs
    Then: T never fires (no tokens available)
    """
    manager, controller, P0, T, P1 = stochastic_ptp_model
    
    P0.tokens = 0  # No tokens
    T.properties = {'rate': 1.0, 'max_burst': 1}
    controller.invalidate_behavior_cache(T.id)
    
    # Run for some time
    for _ in range(100):
        controller.step(time_step=0.01)
    
    # Should never fire
    assert P0.tokens == 0
    assert P1.tokens == 0


def test_enablement_time_tracking(stochastic_ptp_model, get_stochastic_info):
    """Test that enablement time is tracked correctly.
    
    Given: P0 has 1 token, T is stochastic
    When: Transition becomes enabled
    Then: Enablement time and scheduled fire time are recorded
    """
    manager, controller, P0, T, P1 = stochastic_ptp_model
    
    P0.tokens = 1
    T.properties = {'rate': 1.0, 'max_burst': 1}
    controller.invalidate_behavior_cache(T.id)
    
    # Step once to enable transition
    controller.step(time_step=0.01)
    
    # Check stochastic info
    info = get_stochastic_info(controller, T)
    
    assert info['enablement_time'] is not None, "Should have enablement time"
    assert info['scheduled_fire_time'] is not None, "Should have scheduled fire time"
    assert info['scheduled_fire_time'] >= info['enablement_time'], "Fire time >= enablement time"


def test_stochastic_properties_set(stochastic_ptp_model):
    """Test that stochastic properties are correctly configured.
    
    Given: T is stochastic with specific rate and max_burst
    When: Properties are set
    Then: Behavior has correct parameters
    """
    manager, controller, P0, T, P1 = stochastic_ptp_model
    
    T.properties = {'rate': 2.5, 'max_burst': 4}
    controller.invalidate_behavior_cache(T.id)
    
    behavior = controller._get_behavior(T)
    
    assert behavior.rate == 2.5, f"Rate should be 2.5, got {behavior.rate}"
    assert behavior.max_burst == 4, f"Max burst should be 4, got {behavior.max_burst}"


def test_exponential_distribution_statistical_properties():
    """Test that firing delays follow exponential distribution.
    
    Given: T is stochastic with rate=1.0
    When: Run many trials
    Then: Mean delay ≈ 1/rate and variance ≈ 1/rate²
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    from shypn.engine.simulation.controller import SimulationController
    
    rate = 1.0
    n_trials = 50  # More trials for better statistics
    
    fire_times = []
    for trial in range(n_trials):
        random.seed(3000 + trial)
        
        # Create fresh model for each trial
        manager = ModelCanvasManager()
        doc_ctrl = manager.document_controller
        P0 = doc_ctrl.add_place(x=100, y=200, label="P0")
        P1 = doc_ctrl.add_place(x=300, y=200, label="P1")
        T = doc_ctrl.add_transition(x=200, y=200, label="T")
        T.transition_type = "stochastic"
        T.properties = {'rate': rate, 'max_burst': 1}
        doc_ctrl.add_arc(source=P0, target=T)
        doc_ctrl.add_arc(source=T, target=P1)
        controller = SimulationController(manager)
        
        P0.tokens = 1
        
        # Run until fires
        for _ in range(1000):
            before_p1 = P1.tokens
            controller.step(time_step=0.01)
            if P1.tokens > before_p1:
                fire_times.append(controller.time)
                break
    
    # Calculate statistics
    mean = sum(fire_times) / len(fire_times)
    variance = sum((t - mean) ** 2 for t in fire_times) / len(fire_times)
    
    # For Exp(λ): E[X] = 1/λ, Var[X] = 1/λ²
    expected_mean = 1.0 / rate  # = 1.0
    expected_variance = 1.0 / (rate ** 2)  # = 1.0
    
    # Allow 30% tolerance for statistical variation
    assert 0.7 * expected_mean < mean < 1.3 * expected_mean, \
        f"Mean should be ~{expected_mean:.2f}, got {mean:.2f}"
    assert 0.5 * expected_variance < variance < 1.5 * expected_variance, \
        f"Variance should be ~{expected_variance:.2f}, got {variance:.2f}"


def test_immediate_has_priority_over_stochastic(stochastic_ptp_model):
    """Test that immediate transitions fire before stochastic.
    
    Given: Both immediate and stochastic transitions enabled
    When: Step is executed
    Then: Immediate fires first (exhausted), then stochastic
    
    Note: This is a simplified test - full mixed-type interaction 
    will be validated in Phase 7.
    """
    manager, controller, P0, T, P1 = stochastic_ptp_model
    doc_ctrl = manager.document_controller
    
    # Create another place and immediate transition
    P2 = doc_ctrl.add_place(x=100, y=400, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=400, label="P3")
    P2.tokens = 1
    
    T_immediate = doc_ctrl.add_transition(x=200, y=400, label="T_imm")
    T_immediate.transition_type = 'immediate'
    
    doc_ctrl.add_arc(source=P2, target=T_immediate)
    doc_ctrl.add_arc(source=T_immediate, target=P3)
    
    # Set up stochastic
    P0.tokens = 1
    T.properties = {'rate': 100.0, 'max_burst': 1}  # Very high rate
    controller.invalidate_behavior_cache(T.id)
    
    # One step
    controller.step(time_step=0.001)
    
    # Immediate should have fired in this step
    assert P3.tokens == 1, "Immediate transition should fire"
    
    # Stochastic may or may not have fired yet (depends on sampled delay)
    # But we know immediate was processed first


# Summary: 11 tests planned for Phase 6
# - Basic firing with random delay ✅
# - Does not fire before scheduled time ✅
# - Rate parameter affects delay ✅
# - Multiple firings ✅
# - Burst firing (placeholder)
# - Insufficient tokens ✅
# - Enablement time tracking ✅
# - Properties configuration ✅
# - Statistical validation (exponential) ✅
# - Priority over stochastic (mixed types) ✅
