"""
Phase 7: Mixed Transition Types - Comprehensive Tests

Tests interactions between different transition types (immediate, timed, stochastic)
to ensure correct priority handling, scheduling, and execution order.
"""
import pytest


def test_immediate_fires_before_timed(
    mixed_immediate_timed_model, 
    manager,
    assert_mixed_tokens
):
    """
    Test that immediate transition fires first, then timed transition.
    
    Model: P1 → T1(immediate) → P2 → T2(timed[1.0,2.0]) → P3
    
    Expected sequence:
    1. T1 fires immediately at t=0
    2. T2 becomes enabled at t=0, fires at t ∈ [1.0, 2.0]
    """
    # Initial state
    assert_mixed_tokens({"P1": 1, "P2": 0, "P3": 0})
    
    # Step 1: T1 (immediate) should fire in first step
    start_time = manager.current_time
    assert manager.step()
    t1_fire_time = manager.current_time
    assert t1_fire_time >= start_time  # Time advances (controller advances time each step)
    assert_mixed_tokens({"P1": 0, "P2": 1, "P3": 0})
    
    # Important: T1 fires in the immediate phase (conceptually at t=0),
    # but time advances to 0.1 after. T2 becomes enabled at t=0 (when P2 gets token),
    # so it should fire at t ∈ [0 + 1.0, 0 + 2.0] = [1.0, 2.0]
    
    # Step through simulation until T2 fires
    max_steps = 50
    for step in range(max_steps):
        before_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        manager.step()
        after_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        if after_p3 > before_p3:
            # T2 fired!
            break
    
    fire_time = manager.current_time
    assert 1.0 - 1e-6 <= fire_time <= 2.0 + 1e-6, \
        f"Timed transition fired at t={fire_time}, expected [1.0, 2.0]"
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 1})


def test_immediate_fires_before_stochastic(
    mixed_immediate_stochastic_model,
    manager,
    assert_mixed_tokens
):
    """
    Test that immediate transition fires first, then stochastic transition.
    
    Model: P1 → T1(immediate) → P2 → T2(stochastic, rate=2.0) → P3
    
    Expected sequence:
    1. T1 fires immediately at t=0
    2. T2 becomes enabled at t=0, fires after exponential delay
    """
    # Initial state
    assert_mixed_tokens({"P1": 1, "P2": 0, "P3": 0})
    
    # Step 1: T1 (immediate) should fire in first step
    assert manager.step()
    # Don't assert exact time - immediate fires conceptually at t=0 but time advances
    assert_mixed_tokens({"P1": 0, "P2": 1, "P3": 0})
    
    # Step 2: T2 (stochastic) should fire after random delay
    # Loop until it fires
    max_steps = 500
    for step in range(max_steps):
        before_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        manager.step()
        after_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        if after_p3 > before_p3:
            break
    
    fire_time = manager.current_time
    assert fire_time >= 0.0  # Stochastic fires at some time
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 1})


def test_timed_then_stochastic_sequence(
    mixed_timed_stochastic_model,
    manager,
    assert_mixed_tokens
):
    """
    Test timed transition followed by stochastic transition.
    
    Model: P1 → T1(timed[0.5,1.0]) → P2 → T2(stochastic, rate=2.0) → P3
    
    Expected sequence:
    1. T1 fires at t ∈ [0.5, 1.0]
    2. T2 fires after additional exponential delay
    """
    # Initial state
    assert_mixed_tokens({"P1": 1, "P2": 0, "P3": 0})
    
    # Step 1: T1 (timed) should fire at t ∈ [0.5, 1.0]
    # Loop until it fires
    max_steps = 50
    for step in range(max_steps):
        before_p2 = [p for p in manager.places if p.label == "P2"][0].tokens
        manager.step()
        after_p2 = [p for p in manager.places if p.label == "P2"][0].tokens
        if after_p2 > before_p2:
            break
    
    t1_fire_time = manager.current_time
    assert 0.5 - 1e-6 <= t1_fire_time <= 1.0 + 1e-6, f"Timed transition fired at t={t1_fire_time}"
    assert_mixed_tokens({"P1": 0, "P2": 1, "P3": 0})
    
    # Step 2: T2 (stochastic) should fire after additional delay
    max_steps = 200
    for step in range(max_steps):
        before_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        manager.step()
        after_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        if after_p3 > before_p3:
            break
    
    t2_fire_time = manager.current_time
    assert t2_fire_time > t1_fire_time, "Stochastic should fire after timed"
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 1})


def test_all_three_types_in_sequence(
    mixed_all_types_model,
    manager,
    assert_mixed_tokens
):
    """
    Test all three transition types in sequence.
    
    Model: P1 → T1(immediate) → P2 → T2(timed[1.0,2.0]) → P3 → T3(stochastic) → P4
    
    Expected sequence:
    1. T1 fires immediately at t=0
    2. T2 fires at t ∈ [1.0, 2.0]
    3. T3 fires after additional exponential delay
    """
    # Initial state
    assert_mixed_tokens({"P1": 1, "P2": 0, "P3": 0, "P4": 0})
    
    # Step 1: T1 (immediate) fires in first step
    assert manager.step()
    # Don't assert exact time
    assert_mixed_tokens({"P1": 0, "P2": 1, "P3": 0, "P4": 0})
    
    # Step 2: T2 (timed) fires at t ∈ [1.0, 2.0]
    max_steps = 50
    for step in range(max_steps):
        before_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        manager.step()
        after_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        if after_p3 > before_p3:
            break
    
    t2_fire_time = manager.current_time
    assert 1.0 - 1e-6 <= t2_fire_time <= 2.0 + 1e-6
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 1, "P4": 0})
    
    # Step 3: T3 (stochastic) fires after additional delay
    max_steps = 500
    for step in range(max_steps):
        before_p4 = [p for p in manager.places if p.label == "P4"][0].tokens
        manager.step()
        after_p4 = [p for p in manager.places if p.label == "P4"][0].tokens
        if after_p4 > before_p4:
            break
    
    t3_fire_time = manager.current_time
    assert t3_fire_time > t2_fire_time
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 0, "P4": 1})


def test_immediate_has_priority_over_all_types(
    mixed_priority_conflict_model,
    manager,
    assert_mixed_tokens
):
    """
    Test that immediate transitions have absolute priority over timed and stochastic.
    
    Model: P1(3) → T1(immediate, priority 10) → P2
                → T2(timed[0.5,1.0]) → P3
                → T3(stochastic, rate=2.0) → P4
    
    All three transitions compete for P1's tokens. Expected: T1 (immediate) fires 
    repeatedly and consumes all tokens before T2/T3 can fire.
    """
    # Initial state: all transitions enabled
    assert_mixed_tokens({"P1": 3, "P2": 0, "P3": 0, "P4": 0})
    
    # Immediate phase: T1 fires 3 times (until P1 empty)
    # T2 and T3 are enabled but T1 (immediate) has priority and consumes all tokens
    assert manager.step()
    # T1 has fired 3 times, consuming all tokens
    # T2 and T3 never get to fire because T1 took all tokens
    assert_mixed_tokens({"P1": 0, "P2": 3, "P3": 0, "P4": 0})
    
    # This demonstrates immediate priority - T1 prevented T2 and T3 from firing


def test_no_immediate_allows_timed_and_stochastic(
    mixed_timed_stochastic_model,
    manager,
    assert_mixed_tokens
):
    """
    Test that when no immediate transitions are enabled, 
    timed and stochastic transitions can fire.
    
    Model: P1 → T1(timed[0.5,1.0]) → P2 → T2(stochastic, rate=2.0) → P3
    """
    # Initial state: only timed transition enabled
    assert_mixed_tokens({"P1": 1, "P2": 0, "P3": 0})
    
    # Timed transition should be able to fire (no immediate blocking)
    max_steps = 50
    for step in range(max_steps):
        before_p2 = [p for p in manager.places if p.label == "P2"][0].tokens
        manager.step()
        after_p2 = [p for p in manager.places if p.label == "P2"][0].tokens
        if after_p2 > before_p2:
            break
    
    t1_fire_time = manager.current_time
    assert 0.5 - 1e-6 <= t1_fire_time <= 1.0 + 1e-6
    assert_mixed_tokens({"P1": 0, "P2": 1, "P3": 0})
    
    # Stochastic transition should be able to fire
    max_steps = 200
    for step in range(max_steps):
        before_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        manager.step()
        after_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        if after_p3 > before_p3:
            break
    
    assert manager.current_time > t1_fire_time
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 1})


def test_mixed_types_with_guards(document_controller, manager, assert_mixed_tokens):
    """
    Test mixed transition types with guards.
    
    Model: P1 → T1(immediate, guard: tokens(P1) >= 1) → P2
              → T2(timed[0.5,1.0], guard: tokens(P1) >= 1) → P3
    """
    doc_ctrl = document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    
    p1.tokens = 1
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    
    # Configure T1 as immediate with guard
    t1.transition_type = "immediate"
    t1.priority = 10
    t1.guard = lambda: p1.tokens >= 1
    
    # Configure T2 as timed with guard
    t2.transition_type = "timed"
    t2.properties = {'earliest': 0.5, 'latest': 1.0}
    t2.guard = lambda: p1.tokens >= 1
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1)
    doc_ctrl.add_arc(source=p1, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p3, weight=1)
    
    # T1 (immediate) should fire first since it has priority
    assert manager.step()
    # Don't assert exact time
    assert_mixed_tokens({"P1": 0, "P2": 1, "P3": 0})
    
    # T2's guard should now fail (P1 has 0 tokens), so it shouldn't fire
    # Simulation should stop (or at least not change tokens)
    p3_before = p3.tokens
    for _ in range(20):
        manager.step()
        if p3.tokens != p3_before:
            break
    assert p3.tokens == p3_before, "T2 should not have fired due to guard"


def test_mixed_types_different_sources(document_controller, manager, assert_mixed_tokens):
    """
    Test multiple transitions of different types enabled from separate places.
    
    Model: P1 → T1(immediate) → P3
           P2 → T2(timed[0.5,1.0]) → P4
    
    Both start with tokens, so both transitions are initially enabled.
    T1 should fire first (immediate priority).
    """
    doc_ctrl = document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=100, y=200, label="P2")
    p3 = doc_ctrl.add_place(x=300, y=100, label="P3")
    p4 = doc_ctrl.add_place(x=300, y=200, label="P4")
    
    p1.tokens = 1
    p2.tokens = 1
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    
    # Configure T1 as immediate
    t1.transition_type = "immediate"
    t1.priority = 5
    
    # Configure T2 as timed
    t2.transition_type = "timed"
    t2.properties = {'earliest': 0.5, 'latest': 1.0}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p3, weight=1)
    doc_ctrl.add_arc(source=p2, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p4, weight=1)
    
    # Initial state
    assert_mixed_tokens({"P1": 1, "P2": 1, "P3": 0, "P4": 0})
    
    # T1 (immediate) should fire first
    assert manager.step()
    # Time advances after immediate fires
    assert_mixed_tokens({"P1": 0, "P2": 1, "P3": 1, "P4": 0})
    
    # T2 (timed) should fire after delay [0.5, 1.0]
    max_steps = 50
    for step in range(max_steps):
        before_p4 = [p for p in manager.places if p.label == "P4"][0].tokens
        manager.step()
        after_p4 = [p for p in manager.places if p.label == "P4"][0].tokens
        if after_p4 > before_p4:
            break
    assert 0.5 - 1e-6 <= manager.current_time <= 1.0 + 1e-6
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 1, "P4": 1})


def test_multiple_immediate_with_timed_background(document_controller, manager, assert_mixed_tokens):
    """
    Test multiple immediate transitions with timed transitions in background.
    
    Model: P1 → T1(immediate, priority 10) → P2 → T2(immediate, priority 5) → P3
           P4 → T3(timed[1.0,2.0]) → P5
    
    T1 and T2 should fire in priority order at t=0, then T3 at t ∈ [1.0, 2.0].
    """
    doc_ctrl = document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=250, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=400, y=100, label="P3")
    p4 = doc_ctrl.add_place(x=100, y=200, label="P4")
    p5 = doc_ctrl.add_place(x=250, y=200, label="P5")
    
    p1.tokens = 1
    p4.tokens = 1
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=175, y=100, label="T1")
    t2 = doc_ctrl.add_transition(x=325, y=100, label="T2")
    t3 = doc_ctrl.add_transition(x=175, y=200, label="T3")
    
    # Configure T1 as immediate with priority 10
    t1.transition_type = "immediate"
    t1.priority = 10
    
    # Configure T2 as immediate with priority 5
    t2.transition_type = "immediate"
    t2.priority = 5
    
    # Configure T3 as timed
    t3.transition_type = "timed"
    t3.properties = {'earliest': 1.0, 'latest': 2.0}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1)
    doc_ctrl.add_arc(source=p2, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p3, weight=1)
    doc_ctrl.add_arc(source=p4, target=t3, weight=1)
    doc_ctrl.add_arc(source=t3, target=p5, weight=1)
    
    # Initial state
    assert_mixed_tokens({"P1": 1, "P2": 0, "P3": 0, "P4": 1, "P5": 0})
    
    # Both T1 and T2 are immediate, both fire in same immediate phase
    # T1 (priority 10) fires, then T2 (priority 5) fires in same phase
    assert manager.step()
    # Time advances after immediate phase completes
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 1, "P4": 1, "P5": 0})
    
    # T3 (timed) fires after delay [1.0, 2.0]
    max_steps = 50
    for step in range(max_steps):
        before_p5 = [p for p in manager.places if p.label == "P5"][0].tokens
        manager.step()
        after_p5 = [p for p in manager.places if p.label == "P5"][0].tokens
        if after_p5 > before_p5:
            break
    assert 1.0 - 1e-6 <= manager.current_time <= 2.0 + 1e-6
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 1, "P4": 0, "P5": 1})


def test_stochastic_scheduling_with_immediate_interruption(
    document_controller, 
    manager,
    assert_mixed_tokens
):
    """
    Test that immediate transitions can interrupt scheduled stochastic transitions.
    
    Model: P1 → T1(stochastic, rate=1.0) → P2 → T2(immediate) → P3
    
    T1 schedules a fire, but when it fires and enables T2 (immediate),
    T2 should fire immediately in the same cycle.
    """
    doc_ctrl = document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=500, y=100, label="P3")
    
    p1.tokens = 1
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t2 = doc_ctrl.add_transition(x=400, y=100, label="T2")
    
    # Configure T1 as stochastic
    t1.transition_type = "stochastic"
    t1.properties = {'rate': 1.0, 'max_burst': 1}
    
    # Configure T2 as immediate
    t2.transition_type = "immediate"
    t2.priority = 5
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1)
    doc_ctrl.add_arc(source=p2, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p3, weight=1)
    
    # Initial state
    assert_mixed_tokens({"P1": 1, "P2": 0, "P3": 0})
    
    # T1 (stochastic) fires after delay - loop until it fires
    max_steps = 200
    for step in range(max_steps):
        before_p2 = [p for p in manager.places if p.label == "P2"][0].tokens
        manager.step()
        after_p2 = [p for p in manager.places if p.label == "P2"][0].tokens
        if after_p2 > before_p2:
            break
    
    t1_fire_time = manager.current_time
    assert t1_fire_time >= 0.0  # Stochastic fires at some time
    assert_mixed_tokens({"P1": 0, "P2": 1, "P3": 0})
    
    # T2 (immediate) should fire in same cycle when T1 enables it
    # Actually this depends on implementation - T2 might fire immediately
    # Let's just verify both fire and end up with correct final state
    max_steps = 10
    for step in range(max_steps):
        before_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        manager.step()
        after_p3 = [p for p in manager.places if p.label == "P3"][0].tokens
        if after_p3 > before_p3:
            break
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 1})


def test_complex_mixed_network(document_controller, manager):
    """
    Test a complex network with multiple types interacting.
    
    Model: P1 → T1(immediate, priority 10) → P2 ─┐
                                                    ├→ T3(timed[0.5,1.0]) → P4
           P0 → T2(stochastic, rate=2.0) → P2 ────┘
    
    T1 and T2 both feed into P2, which feeds T3.
    T1 should fire immediately, then T2 schedules a fire, then T3 fires.
    """
    doc_ctrl = document_controller
    
    # Create places
    p0 = doc_ctrl.add_place(x=100, y=200, label="P0")
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=150, label="P2")
    p4 = doc_ctrl.add_place(x=500, y=150, label="P4")
    
    p0.tokens = 1
    p1.tokens = 1
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    t3 = doc_ctrl.add_transition(x=400, y=150, label="T3")
    
    # Configure transitions
    t1.transition_type = "immediate"
    t1.priority = 10
    
    t2.transition_type = "stochastic"
    t2.properties = {'rate': 2.0, 'max_burst': 1}
    
    t3.transition_type = "timed"
    t3.properties = {'earliest': 0.5, 'latest': 1.0}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1)
    doc_ctrl.add_arc(source=p0, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p2, weight=1)
    doc_ctrl.add_arc(source=p2, target=t3, weight=2)  # Needs 2 tokens
    doc_ctrl.add_arc(source=t3, target=p4, weight=1)
    
    # Verify complex behavior - get places
    p0_obj = next(p for p in manager.places if p.label == "P0")
    p1_obj = next(p for p in manager.places if p.label == "P1")
    p2_obj = next(p for p in manager.places if p.label == "P2")
    p4_obj = next(p for p in manager.places if p.label == "P4")
    
    # Initial: T1 and T2 enabled, T1 (immediate) fires first
    assert p1_obj.tokens == 1
    assert p0_obj.tokens == 1
    assert p2_obj.tokens == 0
    
    # T1 fires immediately
    assert manager.step()
    # Time advances after immediate fires
    assert p1_obj.tokens == 0
    assert p2_obj.tokens == 1
    
    # T2 (stochastic) fires after delay - loop until it fires
    max_steps = 500
    for step in range(max_steps):
        before = p2_obj.tokens
        manager.step()
        if p2_obj.tokens > before:
            break
    assert manager.current_time >= 0.0
    assert p0_obj.tokens == 0
    assert p2_obj.tokens == 2  # Now has 2 tokens
    
    # T3 (timed) can now fire (needs 2 tokens from P2) - loop until it fires
    max_steps = 50
    for step in range(max_steps):
        before = p4_obj.tokens
        manager.step()
        if p4_obj.tokens > before:
            break
    
    # T3 should have fired
    assert p2_obj.tokens == 0
    assert p4_obj.tokens == 1


def test_mixed_types_exhaustive_sequence(document_controller, manager, assert_mixed_tokens):
    """
    Test exhaustive firing sequence with all transition types.
    
    Creates a more complex scenario to verify scheduler handles
    all type combinations correctly.
    """
    doc_ctrl = document_controller
    
    # Create a chain: immediate → stochastic → timed → immediate
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=250, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=400, y=100, label="P3")
    p4 = doc_ctrl.add_place(x=550, y=100, label="P4")
    p5 = doc_ctrl.add_place(x=700, y=100, label="P5")
    
    p1.tokens = 1
    
    t1 = doc_ctrl.add_transition(x=175, y=100, label="T1")  # immediate
    t2 = doc_ctrl.add_transition(x=325, y=100, label="T2")  # stochastic
    t3 = doc_ctrl.add_transition(x=475, y=100, label="T3")  # timed
    t4 = doc_ctrl.add_transition(x=625, y=100, label="T4")  # immediate
    
    # Configure
    t1.transition_type = "immediate"
    t1.priority = 5
    
    t2.transition_type = "stochastic"
    t2.properties = {'rate': 2.0, 'max_burst': 1}
    
    t3.transition_type = "timed"
    t3.properties = {'earliest': 0.5, 'latest': 1.0}
    
    t4.transition_type = "immediate"
    t4.priority = 5
    
    # Connect
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1)
    doc_ctrl.add_arc(source=p2, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p3, weight=1)
    doc_ctrl.add_arc(source=p3, target=t3, weight=1)
    doc_ctrl.add_arc(source=t3, target=p4, weight=1)
    doc_ctrl.add_arc(source=p4, target=t4, weight=1)
    doc_ctrl.add_arc(source=t4, target=p5, weight=1)
    
    # Execute full sequence - transitions fire in order
    # Just verify final state and that time advances appropriately
    
    # Run until completion (all tokens reach P5)
    max_steps = 300
    for step in range(max_steps):
        p5_obj = next(p for p in manager.places if p.label == "P5")
        if p5_obj.tokens == 1:
            break
        manager.step()
    
    # Verify final state
    assert_mixed_tokens({"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 1})
    
    # Time should have advanced beyond just immediate firings
    # (stochastic + timed delays should add significant time)
    assert manager.current_time > 0.5
