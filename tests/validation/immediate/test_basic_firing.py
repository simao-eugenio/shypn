"""
Validation tests for basic firing behavior of immediate transitions.

Tests verify that immediate transitions fire correctly under basic conditions.
"""

import pytest


def test_fires_when_enabled(ptp_model, run_simulation, assert_tokens, assert_firing_count):
    """
    Test that an enabled immediate transition fires.
    
    Given: P1 has 1 token
    When: Simulation runs
    Then: T1 fires once, P2 receives 1 token
    """
    model, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 1
    
    # Execute
    results = run_simulation(model, max_time=1.0)
    
    # Verify
    assert_tokens(P1, 0)
    assert_tokens(P2, 1)
    assert_firing_count(results, 1)


def test_does_not_fire_when_disabled(ptp_model, run_simulation, assert_tokens, assert_firing_count):
    """
    Test that a disabled immediate transition does not fire.
    
    Given: P1 has 0 tokens (transition disabled)
    When: Simulation runs
    Then: T1 does not fire
    """
    model, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup (P1 already has 0 tokens)
    
    # Execute
    results = run_simulation(model, max_time=1.0)
    
    # Verify
    assert_tokens(P1, 0)
    assert_tokens(P2, 0)
    assert_firing_count(results, 0)


def test_fires_immediately_at_t0(ptp_model, run_simulation):
    """
    Test that immediate transitions fire in first simulation step.
    
    Given: P1 has 1 token at t=0
    When: Simulation runs
    Then: T1 fires in first step, token moves to P2
    
    Note: Immediate transitions fire in "zero time" but are recorded
    after the time step advances (t=0.001 with default time_step).
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 1
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify firing occurred in first step
    assert len(results['firings']) > 0, "At least one firing should occur"
    assert results['firings'][0]['time'] <= 0.001, "First firing in first step"
    assert P2.tokens == 1, "Token should move to output place"


def test_fires_multiple_times(ptp_model, run_simulation, assert_tokens):
    """
    Test that immediate transitions exhaust all available tokens.
    
    Given: P1 has 3 tokens
    When: Simulation runs
    Then: All 3 tokens move to P2
    
    Note: Immediate transitions fire exhaustively in one step() call.
    All enabled immediate transitions fire in "zero time" until none
    remain enabled. We test the state change, not event count.
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 3
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify all tokens moved (immediate transitions exhaust)
    assert_tokens(P1, 0)
    assert_tokens(P2, 3)


def test_consumes_tokens_correctly(ptp_model, run_simulation, assert_tokens):
    """
    Test that firing correctly consumes input tokens.
    
    Given: P1 has 5 tokens, arc weight=1
    When: Simulation runs
    Then: P1 consumes 5 tokens (one per firing)
    """
    model, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    initial_tokens = 5
    P1.tokens = initial_tokens
    
    # Execute
    results = run_simulation(model, max_time=1.0)
    
    # Verify
    assert_tokens(P1, 0)
    assert P1.tokens == 0, "Input place should be empty after firing"


def test_produces_tokens_correctly(ptp_model, run_simulation, assert_tokens):
    """
    Test that firing correctly produces output tokens.
    
    Given: P1 has 5 tokens, arc weight=1
    When: Simulation runs
    Then: P2 produces 5 tokens (one per firing)
    """
    model, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    initial_tokens = 5
    P1.tokens = initial_tokens
    
    # Execute
    results = run_simulation(model, max_time=1.0)
    
    # Verify
    assert_tokens(P2, initial_tokens)
    assert P2.tokens == initial_tokens, \
        f"Output place should have {initial_tokens} tokens"
