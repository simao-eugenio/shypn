"""
Validation tests for transition guards with immediate transitions.

Tests verify that immediate transitions correctly evaluate guard conditions
and only fire when guards are satisfied.
"""

import pytest
import math


def test_guard_always_true(ptp_model, run_simulation, assert_tokens):
    """
    Test transition with guard that always returns True.
    
    Given: P1 has 3 tokens, T1.guard = lambda: True
    When: Simulation runs
    Then: Fires normally (3 times)
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 3
    T1.guard = lambda: True
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - fires normally
    assert_tokens(P1, 0)
    assert_tokens(P2, 3)


def test_guard_always_false(ptp_model, run_simulation, assert_tokens):
    """
    Test transition with guard that always returns False.
    
    Given: P1 has 3 tokens, T1.guard = lambda: False
    When: Simulation runs
    Then: Never fires (guard prevents firing)
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 3
    T1.guard = lambda: False
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - never fires
    assert_tokens(P1, 3)  # Unchanged
    assert_tokens(P2, 0)  # No tokens produced


def test_guard_with_token_condition(ptp_model, run_simulation, assert_tokens):
    """
    Test guard that checks token count.
    
    Given: P1 has 10 tokens, guard = lambda: P1.tokens > 5
    When: Simulation runs
    Then: Fires while P1.tokens > 5, stops at 5
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 10
    T1.guard = lambda: P1.tokens > 5
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - fires 5 times (10, 9, 8, 7, 6 → stops at 6 since guard becomes false)
    assert_tokens(P1, 5)  # Stops when guard becomes false
    assert_tokens(P2, 5)  # 5 firings


def test_guard_with_place_comparison(ptp_model, run_simulation, assert_tokens):
    """
    Test guard comparing two place token counts.
    
    Given: P1=10, P2=0, guard = lambda: P1.tokens >= P2.tokens + 3
    When: Simulation runs
    Then: Fires while difference >= 3, stops when difference < 3
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 10
    P2.tokens = 0
    # Guard: P1 must have at least 3 more tokens than P2
    T1.guard = lambda: P1.tokens >= P2.tokens + 3
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - fires while P1 >= P2 + 3
    # Fires: 10>=3✓, 9>=4✓, 8>=5✓, 7>=6✓, 6>=7✗ (stops at 4th firing)
    assert_tokens(P1, 6)  # 10 - 4
    assert_tokens(P2, 4)  # 4 firings


def test_guard_with_multiple_conditions(ptp_model, run_simulation, assert_tokens):
    """
    Test guard with AND logic.
    
    Given: P1=10, guard = lambda: P1.tokens > 3 and P1.tokens < 8
    When: Simulation runs
    Then: Fires only when 3 < tokens < 8
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 10
    # Guard: fires only when tokens in range (3, 8)
    T1.guard = lambda: P1.tokens > 3 and P1.tokens < 8
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - starts at 10 (false), never fires
    assert_tokens(P1, 10)  # Initial value out of range
    assert_tokens(P2, 0)


def test_guard_prevents_firing(ptp_model, run_simulation, assert_tokens):
    """
    Test that false guard completely prevents firing.
    
    Given: P1=100 tokens, guard = lambda: False
    When: Simulation runs
    Then: Never fires despite abundant tokens
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup - lots of tokens but guard prevents firing
    P1.tokens = 100
    T1.guard = lambda: False
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - guard overrides token availability
    assert_tokens(P1, 100)  # Unchanged
    assert_tokens(P2, 0)


def test_guard_with_math_expression():
    """
    Test guard using mathematical expressions.
    
    Given: P1=9 tokens, guard = lambda: math.sqrt(P1.tokens) >= 2
    When: Simulation runs
    Then: Fires while sqrt(tokens) >= 2 (tokens >= 4)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create model
    P1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    
    A1 = doc_ctrl.add_arc(source=P1, target=T1)
    A2 = doc_ctrl.add_arc(source=T1, target=P2)
    
    # Setup
    P1.tokens = 9
    T1.transition_type = "immediate"
    T1.guard = lambda: math.sqrt(P1.tokens) >= 2  # sqrt(tokens) >= 2, so tokens >= 4
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(manager)
    
    while controller.time < 1.0:
        fired = controller.step(time_step=0.001)
        if not fired:
            break
    
    # Verify - fires while sqrt(tokens) >= 2
    # Fires: sqrt(9)=3✓, sqrt(8)=2.83✓, sqrt(7)=2.65✓, sqrt(6)=2.45✓, 
    #        sqrt(5)=2.24✓, sqrt(4)=2✓, sqrt(3)=1.73✗ (stops after 6th firing)
    assert P1.tokens == 3, f"P1 should have 3 tokens, got {P1.tokens}"
    assert P2.tokens == 6, f"P2 should have 6 tokens, got {P2.tokens}"


def test_guard_with_modulo_operation(ptp_model, run_simulation, assert_tokens):
    """
    Test guard with modulo operation (fire only on even tokens).
    
    Given: P1=10 tokens, guard = lambda: P1.tokens % 2 == 0
    When: Simulation runs
    Then: Fires only when P1 has even token count
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 10
    T1.guard = lambda: P1.tokens % 2 == 0  # Fire only on even counts
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - fires: 10(even)→9(odd,stop), 1 firing only
    assert_tokens(P1, 9)  # One firing, then stops (9 is odd)
    assert_tokens(P2, 1)


def test_guard_with_arc_weight_condition(ptp_model, run_simulation, assert_tokens):
    """
    Test guard checking sufficient tokens for arc weight.
    
    Given: P1=10, A1.weight=3, guard = lambda: P1.tokens >= A1.weight * 2
    When: Simulation runs
    Then: Fires while tokens >= weight * 2 (>= 6)
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 10
    A1.weight = 3
    # Guard: need at least 2x the arc weight
    T1.guard = lambda: P1.tokens >= A1.weight * 2
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - fires while tokens >= 6
    # Fires at: 10, 7 (stops at 4 since 4 < 6)
    assert_tokens(P1, 4)  # 10 - 3 - 3 = 4
    assert_tokens(P2, 2)  # 2 firings


def test_guard_with_time_dependency():
    """
    Test guard that depends on simulation time.
    
    Given: guard = lambda: controller.time > 0.5
    When: Simulation runs
    Then: Only fires after time > 0.5
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create model
    P1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    
    A1 = doc_ctrl.add_arc(source=P1, target=T1)
    A2 = doc_ctrl.add_arc(source=T1, target=P2)
    
    # Setup
    P1.tokens = 100  # Lots of tokens
    T1.transition_type = "immediate"
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(manager)
    
    # Guard depends on controller time
    T1.guard = lambda: controller.time > 0.5
    
    # Step through time
    while controller.time < 1.0:
        fired = controller.step(time_step=0.1)
        if controller.time <= 0.5 and fired:
            pytest.fail("Transition should not fire before time 0.5")
    
    # Verify - should have fired after time 0.5
    assert P2.tokens > 0, "Transition should fire after time 0.5"
    assert P1.tokens < 100, "Tokens should have been consumed"


def test_guard_with_division(ptp_model, run_simulation, assert_tokens):
    """
    Test guard with division operation.
    
    Given: P1=20, guard = lambda: P1.tokens / 2 > 5
    When: Simulation runs
    Then: Fires while tokens / 2 > 5 (tokens > 10)
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 20
    T1.guard = lambda: P1.tokens / 2 > 5  # tokens > 10
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - fires while tokens > 10, stops at 10
    assert_tokens(P1, 10)
    assert_tokens(P2, 10)


def test_guard_none_treated_as_always_true(ptp_model, run_simulation, assert_tokens):
    """
    Test that None guard is treated as always true (no restriction).
    
    Given: P1=3 tokens, T1.guard = None
    When: Simulation runs
    Then: Fires normally (None = no guard = always enabled)
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 3
    T1.guard = None  # No guard specified
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - fires normally without guard
    assert_tokens(P1, 0)
    assert_tokens(P2, 3)


def test_guard_changes_during_execution(ptp_model, run_simulation, assert_tokens):
    """
    Test that guards are re-evaluated each step.
    
    Given: Guard expression using current token value
    When: Tokens change during simulation
    Then: Guard re-evaluated with new token values
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 15
    # Guard: fire while tokens > 10
    T1.guard = lambda: P1.tokens > 10
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - guard re-evaluated each step
    # Fires at: 15, 14, 13, 12, 11 (stops at 11 since guard becomes false)
    assert_tokens(P1, 10)  # Stops when guard becomes false
    assert_tokens(P2, 5)


def test_multiple_transitions_different_guards():
    """
    Test multiple transitions with different guard conditions.
    
    Given: P1 → T1 → P2 (guard: tokens > 5)
           P1 → T2 → P3 (guard: tokens <= 5)
    When: Simulation runs
    Then: T1 fires first (high tokens), then T2 (low tokens)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=150, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    
    # Create transitions with different guards
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    
    T1.transition_type = "immediate"
    T2.transition_type = "immediate"
    
    # Guards
    T1.guard = lambda: P1.tokens > 5  # Fire when many tokens
    T2.guard = lambda: P1.tokens <= 5  # Fire when few tokens
    
    # Create arcs
    A1 = doc_ctrl.add_arc(source=P1, target=T1)
    A2 = doc_ctrl.add_arc(source=T1, target=P2)
    A3 = doc_ctrl.add_arc(source=P1, target=T2)
    A4 = doc_ctrl.add_arc(source=T2, target=P3)
    
    # Setup
    P1.tokens = 10
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(manager)
    
    while controller.time < 1.0:
        fired = controller.step(time_step=0.001)
        if not fired:
            break
    
    # Verify - T1 fires first (high tokens), then T2 (low tokens)
    assert P1.tokens == 0, f"P1 should be empty, got {P1.tokens}"
    assert P2.tokens > 0, f"P2 should have tokens from T1, got {P2.tokens}"
    assert P3.tokens > 0, f"P3 should have tokens from T2, got {P3.tokens}"
    # Total should be 10
    assert P2.tokens + P3.tokens == 10, "Total tokens should be conserved"


def test_guard_with_comparison_chain(ptp_model, run_simulation, assert_tokens):
    """
    Test guard with chained comparison.
    
    Given: P1=10, guard = lambda: 3 < P1.tokens < 8
    When: Simulation runs
    Then: Never fires (initial value out of range)
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 10
    T1.guard = lambda: 3 < P1.tokens < 8  # Chained comparison
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - 10 is not in range (3, 8)
    assert_tokens(P1, 10)
    assert_tokens(P2, 0)


def test_guard_with_logical_or(ptp_model, run_simulation, assert_tokens):
    """
    Test guard with OR logic.
    
    Given: P1=7, guard = lambda: P1.tokens < 3 or P1.tokens > 10
    When: Simulation runs
    Then: Never fires (7 is not < 3 and not > 10)
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 7
    T1.guard = lambda: P1.tokens < 3 or P1.tokens > 10
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - 7 doesn't satisfy either condition
    assert_tokens(P1, 7)
    assert_tokens(P2, 0)


def test_guard_with_not_operator(ptp_model, run_simulation, assert_tokens):
    """
    Test guard with NOT operator.
    
    Given: P1=10, guard = lambda: not (P1.tokens < 5)
    When: Simulation runs
    Then: Fires while NOT (tokens < 5), i.e., while tokens >= 5
    """
    manager, P1, T1, P2, A1, A2 = ptp_model
    
    # Setup
    P1.tokens = 10
    T1.guard = lambda: not (P1.tokens < 5)  # NOT operator
    
    # Execute
    results = run_simulation(manager, max_time=1.0)
    
    # Verify - fires while NOT (tokens < 5), i.e., while tokens >= 5
    # Fires: not(10<5)✓, not(9<5)✓, ..., not(5<5)✓, not(4<5)✗ (stops after 6th firing)
    assert_tokens(P1, 4)
    assert_tokens(P2, 6)
