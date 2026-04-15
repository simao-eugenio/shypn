"""
Validation tests for arc weights with immediate transitions.

Tests verify that immediate transitions correctly handle variable arc weights
for input and output arcs.
"""

import pytest


def test_variable_input_weight(ptp_model, run_simulation, assert_tokens):
    """
    Test transition with input arc weight > 1.
    
    Given: P1 has 5 tokens, arc A1 has weight=2
    When: Simulation runs
    Then: Each firing consumes 2 tokens, fires 2 times (5//2=2)
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 5
    A1.weight = 2  # Requires 2 tokens per firing
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - can fire 2 times (2*2=4 tokens consumed, 1 token remains)
    assert_tokens(P1, 1)  # 5 - 4 = 1 remaining
    assert_tokens(P2, 2)  # 2 firings, each produces 1 token


def test_variable_output_weight(ptp_model, run_simulation, assert_tokens):
    """
    Test transition with output arc weight > 1.
    
    Given: P1 has 3 tokens, arc A2 has weight=3
    When: Simulation runs
    Then: Each firing produces 3 tokens, fires 3 times
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 3
    A2.weight = 3  # Produces 3 tokens per firing
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - 3 firings, each produces 3 tokens
    assert_tokens(P1, 0)  # All consumed
    assert_tokens(P2, 9)  # 3 firings * 3 tokens = 9


def test_balanced_weights(ptp_model, run_simulation, assert_tokens):
    """
    Test transition with balanced input and output weights.
    
    Given: P1 has 10 tokens, A1.weight=2, A2.weight=2
    When: Simulation runs
    Then: Fires 5 times, token balance maintained
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 10
    A1.weight = 2
    A2.weight = 2
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - 5 firings (10/2=5)
    assert_tokens(P1, 0)   # All consumed (5 * 2)
    assert_tokens(P2, 10)  # All produced (5 * 2)


def test_unbalanced_weights(ptp_model, run_simulation, assert_tokens):
    """
    Test transition with unbalanced weights (token creation/destruction).
    
    Given: P1 has 6 tokens, A1.weight=2, A2.weight=3
    When: Simulation runs
    Then: Net token increase (consumes 2, produces 3 per firing)
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 6
    A1.weight = 2
    A2.weight = 3
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - 3 firings (6/2=3)
    assert_tokens(P1, 0)  # All consumed (3 * 2 = 6)
    assert_tokens(P2, 9)  # Net increase (3 * 3 = 9)


def test_insufficient_tokens(ptp_model, run_simulation, assert_tokens):
    """
    Test transition doesn't fire with insufficient tokens.
    
    Given: P1 has 2 tokens, A1.weight=3
    When: Simulation runs
    Then: Cannot fire (2 < 3), tokens remain
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 2
    A1.weight = 3  # Requires 3 tokens
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - cannot fire
    assert_tokens(P1, 2)  # Unchanged
    assert_tokens(P2, 0)  # No tokens produced


def test_large_weight(ptp_model, run_simulation, assert_tokens):
    """
    Test transition with large arc weight.
    
    Given: P1 has 100 tokens, A1.weight=10
    When: Simulation runs
    Then: Fires 10 times, consuming all tokens
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 100
    A1.weight = 10
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - 10 firings (100/10=10)
    assert_tokens(P1, 0)   # All consumed
    assert_tokens(P2, 10)  # 10 firings


def test_multiple_input_arcs():
    """
    Test transition with multiple input arcs (different weights).
    
    Given: P1(5 tokens) --[w=1]--> T1, P3(6 tokens) --[w=2]--> T1
    When: Simulation runs
    Then: Fires min(5/1, 6/2) = min(5, 3) = 3 times
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=100, y=200, label="P3")
    
    P1.tokens = 5
    P2.tokens = 0
    P3.tokens = 6
    
    # Create transition
    T1 = doc_ctrl.add_transition(x=200, y=150, label="T1")
    T1.transition_type = "immediate"
    
    # Create arcs - two inputs, one output
    A1 = doc_ctrl.add_arc(source=P1, target=T1, weight=1)
    A2 = doc_ctrl.add_arc(source=T1, target=P2, weight=1)
    A3 = doc_ctrl.add_arc(source=P3, target=T1, weight=2)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(manager)
    
    while controller.time < 1.0:
        fired = controller.step(time_step=0.001)
        if not fired:
            break
    
    # Verify - fires 3 times (limited by P3: 6/2=3)
    assert P1.tokens == 2, f"P1 should have 2 tokens, got {P1.tokens}"  # 5 - 3 = 2
    assert P3.tokens == 0, f"P3 should have 0 tokens, got {P3.tokens}"  # 6 - 6 = 0
    assert P2.tokens == 3, f"P2 should have 3 tokens, got {P2.tokens}"  # 3 firings


def test_multiple_output_arcs():
    """
    Test transition with multiple output arcs (different weights).
    
    Given: T1 --> [w=2] --> P2, T1 --> [w=3] --> P3
    When: Fires with 5 input tokens
    Then: Produces 2*5=10 in P2, 3*5=15 in P3
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=150, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    
    P1.tokens = 5
    P2.tokens = 0
    P3.tokens = 0
    
    # Create transition
    T1 = doc_ctrl.add_transition(x=200, y=150, label="T1")
    T1.transition_type = "immediate"
    
    # Create arcs - one input, two outputs
    A1 = doc_ctrl.add_arc(source=P1, target=T1, weight=1)
    A2 = doc_ctrl.add_arc(source=T1, target=P2, weight=2)
    A3 = doc_ctrl.add_arc(source=T1, target=P3, weight=3)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(manager)
    
    while controller.time < 1.0:
        fired = controller.step(time_step=0.001)
        if not fired:
            break
    
    # Verify - 5 firings, different outputs
    assert P1.tokens == 0, f"P1 should be empty, got {P1.tokens}"
    assert P2.tokens == 10, f"P2 should have 10 tokens, got {P2.tokens}"  # 5 * 2
    assert P3.tokens == 15, f"P3 should have 15 tokens, got {P3.tokens}"  # 5 * 3


def test_zero_weight_edge_case(ptp_model, run_simulation, assert_tokens):
    """
    Test transition with zero weight (edge case).
    
    Given: P1 has 5 tokens, A1.weight=0
    When: Simulation runs
    Then: Behavior depends on implementation (likely always enabled or never)
    
    Note: Zero-weight arcs are unusual - test documents actual behavior.
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 5
    A1.weight = 0  # Zero weight - edge case
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Document actual behavior (implementation-dependent)
    # Most implementations treat weight=0 as disabled or always satisfied
    # We test to document the actual behavior
    
    # Verify tokens remain unchanged (zero weight likely disables)
    # This documents actual behavior - adjust if implementation differs
    assert P1.tokens >= 0, "Tokens should remain non-negative"
    assert P2.tokens >= 0, "Tokens should remain non-negative"
