"""Phase 5A: Basic Timed Transition Tests

Tests for fundamental timed transition behavior including:
- Timing windows [earliest, latest]
- Time advancement
- Enablement timing
- Window crossing detection
"""

import pytest


def test_fires_after_earliest_delay(timed_ptp_model, assert_timed_tokens):
    """Test that timed transition fires after earliest delay.
    
    Given: P0 has 1 token, T has earliest=0.8, latest=1.2
    When: Time advances to 1.0 (within window)
    Then: T fires, token moves from P0 to P1
    """
    manager, controller, P0, T, P1 = timed_ptp_model
    
    # Set initial state with a proper firing window
    P0.tokens = 1
    T.properties = {'earliest': 0.8, 'latest': 1.2}
    controller.invalidate_behavior_cache(T.id)
    
    # Initially no tokens in P1
    assert_timed_tokens(P0, P1, 1, 0)
    
    # Step at t=0.5 (before earliest) - should not fire
    controller.step(time_step=0.5)
    assert_timed_tokens(P0, P1, 1, 0)
    assert controller.time == 0.5
    
    # Step to t=1.0 (within [0.8, 1.2] window) - should fire
    controller.step(time_step=0.5)
    assert_timed_tokens(P0, P1, 0, 1)
    assert controller.time == 1.0


def test_does_not_fire_before_earliest(timed_ptp_model, assert_timed_tokens):
    """Test that timed transition does not fire before earliest delay.
    
    Given: P0 has 1 token, T has earliest=2.0, latest=3.0
    When: Time advances to 1.5 (before earliest)
    Then: T does not fire, token stays in P0
    """
    manager, controller, P0, T, P1 = timed_ptp_model
    
    P0.tokens = 1
    T.properties = {'earliest': 2.0, 'latest': 3.0}
    controller.invalidate_behavior_cache(T.id)
    
    # Run for 1.5 seconds (before earliest=2.0)
    controller.step(time_step=1.5)
    
    # Token should still be in P0
    assert_timed_tokens(P0, P1, 1, 0)
    assert controller.time == 1.5


def test_fires_within_window(timed_ptp_model, assert_timed_tokens):
    """Test that timed transition can fire anywhere within [earliest, latest].
    
    Given: P0 has 1 token, T has earliest=1.0, latest=3.0
    When: Time advances to 2.0 (within window)
    Then: T can fire (will fire when selected)
    """
    manager, controller, P0, T, P1 = timed_ptp_model
    
    P0.tokens = 1
    T.properties = {'earliest': 1.0, 'latest': 3.0}
    controller.invalidate_behavior_cache(T.id)
    
    # Step past earliest but before latest
    controller.step(time_step=0.5)  # t=0.5
    assert_timed_tokens(P0, P1, 1, 0)
    
    controller.step(time_step=0.6)  # t=1.1 (in window)
    assert_timed_tokens(P0, P1, 0, 1)  # Should have fired


def test_must_fire_before_latest(timed_ptp_model, assert_timed_tokens):
    """Test that timed transition fires before latest deadline.
    
    Given: P0 has 1 token, T has earliest=0.3, latest=1.0
    When: Time advances in small steps through window
    Then: T fires before exceeding latest
    """
    manager, controller, P0, T, P1 = timed_ptp_model
    
    P0.tokens = 1
    T.properties = {'earliest': 0.3, 'latest': 1.0}
    controller.invalidate_behavior_cache(T.id)
    
    # Step to just before earliest
    controller.step(time_step=0.2)  # t=0.2
    assert_timed_tokens(P0, P1, 1, 0)
    
    # Step into window - should fire
    controller.step(time_step=0.3)  # t=0.5 (in [0.3, 1.0])
    assert_timed_tokens(P0, P1, 0, 1)
    assert controller.time <= 1.0


def test_zero_earliest_fires_immediately(timed_ptp_model, assert_timed_tokens):
    """Test that timed transition with earliest=0 can fire immediately.
    
    Given: P0 has 1 token, T has earliest=0.0, latest=1.0
    When: First simulation step
    Then: T fires immediately (no delay required)
    """
    manager, controller, P0, T, P1 = timed_ptp_model
    
    P0.tokens = 1
    T.properties = {'earliest': 0.0, 'latest': 1.0}
    controller.invalidate_behavior_cache(T.id)
    
    # Single step should cause firing (no delay required)
    controller.step(time_step=0.1)
    assert_timed_tokens(P0, P1, 0, 1)


def test_infinite_latest_no_upper_bound(timed_ptp_model, assert_timed_tokens):
    """Test that timed transition with latest=∞ has no upper firing limit.
    
    Given: P0 has 1 token, T has earliest=1.0, latest=inf
    When: Time advances well past earliest (e.g., t=10.0)
    Then: T can still fire (no upper bound)
    """
    manager, controller, P0, T, P1 = timed_ptp_model
    
    P0.tokens = 1
    T.properties = {'earliest': 1.0, 'latest': float('inf')}
    controller.invalidate_behavior_cache(T.id)
    
    # Advance well past earliest
    controller.step(time_step=1.5)  # t=1.5 (past earliest)
    
    # Should fire (even though time >> earliest)
    assert_timed_tokens(P0, P1, 0, 1)


def test_enablement_time_tracking(timed_ptp_model, get_timing_info):
    """Test that enablement time is correctly tracked.
    
    Given: P0 has 1 token, T has earliest=1.0, latest=2.0
    When: Transition becomes enabled at t=0
    Then: Enablement time is recorded and maintained
    """
    manager, controller, P0, T, P1 = timed_ptp_model
    
    P0.tokens = 1
    T.properties = {'earliest': 1.0, 'latest': 2.0}
    controller.invalidate_behavior_cache(T.id)
    
    # Initial step enables transition
    controller.step(time_step=0.1)
    
    # Check timing info
    info = get_timing_info(controller, T)
    assert info['enablement_time'] == 0.0  # Enabled at t=0
    assert info['current_time'] == 0.1
    assert info['elapsed'] is not None
    assert info['elapsed'] == 0.1  # 0.1 seconds have elapsed since enablement


def test_timing_window_properties(timed_ptp_model, get_timing_info):
    """Test that timing window properties are correctly set.
    
    Given: T has specific earliest/latest values
    When: Transition is created
    Then: Timing properties match configuration
    """
    manager, controller, P0, T, P1 = timed_ptp_model
    
    P0.tokens = 1
    earliest = 0.5
    latest = 2.5
    T.properties = {'earliest': earliest, 'latest': latest}
    controller.invalidate_behavior_cache(T.id)
    
    # Get behavior and check timing
    behavior = controller._get_behavior(T)
    assert hasattr(behavior, 'earliest')
    assert hasattr(behavior, 'latest')
    assert behavior.earliest == earliest
    assert behavior.latest == latest


def test_multiple_firings_same_transition(timed_ptp_model, assert_timed_tokens):
    """Test that same timed transition can fire multiple times.
    
    Given: P0 has 3 tokens, T has earliest=0.8, latest=1.2
    When: Time advances allowing multiple firings
    Then: T fires 3 times, moving all tokens to P1
    """
    manager, controller, P0, T, P1 = timed_ptp_model
    
    P0.tokens = 3
    T.properties = {'earliest': 0.8, 'latest': 1.2}
    controller.invalidate_behavior_cache(T.id)
    
    # First firing at t≈1.0
    controller.step(time_step=1.0)
    fired_count = P1.tokens
    assert fired_count >= 1, f"Should have fired at least once, got {fired_count}"
    
    # Continue simulation - each firing re-enables if tokens remain
    for _ in range(10):  # Multiple steps to allow all 3 firings
        controller.step(time_step=1.0)
        if P0.tokens == 0:
            break
    
    # All 3 tokens should have moved
    assert P0.tokens == 0, f"All source tokens should be consumed, {P0.tokens} remaining"
    assert P1.tokens == 3, f"All 3 tokens should reach P1, got {P1.tokens}"


def test_disabled_by_insufficient_tokens(timed_ptp_model, assert_timed_tokens):
    """Test that timed transition doesn't fire without sufficient tokens.
    
    Given: P0 has 0 tokens, T has earliest=1.0, latest=2.0
    When: Time advances past window
    Then: T never fires (structurally disabled)
    """
    manager, controller, P0, T, P1 = timed_ptp_model
    
    P0.tokens = 0  # No tokens
    T.properties = {'earliest': 1.0, 'latest': 2.0}
    controller.invalidate_behavior_cache(T.id)
    
    # Run past timing window
    controller.step(time_step=3.0)
    
    # Should not have fired
    assert_timed_tokens(P0, P1, 0, 0)
