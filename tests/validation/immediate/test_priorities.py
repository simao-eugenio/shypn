"""
Validation tests for transition priorities and conflict resolution.

Tests verify that immediate transitions correctly handle priority-based
selection when multiple transitions are enabled simultaneously.
"""

import pytest


def test_two_transitions_different_priorities():
    """
    Test that higher priority transition fires first.
    
    Given: P1(10) → T1(priority=1) → P2
           P1(10) → T2(priority=5) → P3
    When: Both enabled
    Then: T2 fires first (higher priority)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=150, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    
    P1.tokens = 10
    
    # Create transitions with different priorities
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    
    T1.transition_type = "immediate"
    T2.transition_type = "immediate"
    T1.priority = 1
    T2.priority = 5  # Higher priority
    
    # Create arcs
    A1 = doc_ctrl.add_arc(source=P1, target=T1)
    A2 = doc_ctrl.add_arc(source=T1, target=P2)
    A3 = doc_ctrl.add_arc(source=P1, target=T2)
    A4 = doc_ctrl.add_arc(source=T2, target=P3)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    controller = SimulationController(manager)
    controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
    
    # Single step - should fire T2 (higher priority)
    controller.step(time_step=0.001)
    
    # T2 should have fired first
    assert P3.tokens >= 1, "T2 (priority=5) should fire first"
    
    # Run to completion
    while controller.time < 1.0:
        fired = controller.step(time_step=0.001)
        if not fired:
            break
    
    # All tokens consumed
    assert P1.tokens == 0, "All tokens should be consumed"
    assert P2.tokens + P3.tokens == 10, "Total tokens conserved"


def test_three_transitions_ascending_priorities():
    """
    Test three transitions with ascending priorities.
    
    Given: T1(priority=1), T2(priority=5), T3(priority=10)
    When: All enabled
    Then: T3 fires first (highest priority)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create shared source place
    P1 = doc_ctrl.add_place(x=100, y=200, label="P1")
    P1.tokens = 15
    
    # Create output places
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    P4 = doc_ctrl.add_place(x=300, y=300, label="P4")
    
    # Create transitions with ascending priorities
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    T3 = doc_ctrl.add_transition(x=200, y=300, label="T3")
    
    T1.transition_type = "immediate"
    T2.transition_type = "immediate"
    T3.transition_type = "immediate"
    T1.priority = 1
    T2.priority = 5
    T3.priority = 10  # Highest priority
    
    # Create arcs (all from P1)
    doc_ctrl.add_arc(source=P1, target=T1)
    doc_ctrl.add_arc(source=T1, target=P2)
    doc_ctrl.add_arc(source=P1, target=T2)
    doc_ctrl.add_arc(source=T2, target=P3)
    doc_ctrl.add_arc(source=P1, target=T3)
    doc_ctrl.add_arc(source=T3, target=P4)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    controller = SimulationController(manager)
    controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
    
    # First step - should fire T3 (highest priority)
    controller.step(time_step=0.001)
    
    assert P4.tokens >= 1, "T3 (priority=10) should fire first"


def test_equal_priorities():
    """
    Test transitions with equal priorities (conflict resolution).
    
    Given: T1(priority=5), T2(priority=5)
    When: Both enabled
    Then: One fires (deterministic selection based on implementation)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=150, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    
    P1.tokens = 10
    
    # Create transitions with equal priorities
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    
    T1.transition_type = "immediate"
    T2.transition_type = "immediate"
    T1.priority = 5
    T2.priority = 5  # Same priority
    
    # Create arcs
    doc_ctrl.add_arc(source=P1, target=T1)
    doc_ctrl.add_arc(source=T1, target=P2)
    doc_ctrl.add_arc(source=P1, target=T2)
    doc_ctrl.add_arc(source=T2, target=P3)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    controller = SimulationController(manager)
    controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
    
    # Single step - one should fire
    controller.step(time_step=0.001)
    
    # Exactly one transition should have fired
    fired_count = (1 if P2.tokens > 0 else 0) + (1 if P3.tokens > 0 else 0)
    assert fired_count == 1, "Exactly one transition should fire with equal priorities"
    
    # Run to completion
    while controller.time < 1.0:
        fired = controller.step(time_step=0.001)
        if not fired:
            break
    
    # All tokens consumed
    assert P1.tokens == 0
    assert P2.tokens + P3.tokens == 10


def test_priority_with_insufficient_tokens():
    """
    Test that lower priority can fire if higher priority lacks tokens.
    
    Given: T1(priority=10, needs 20 tokens), T2(priority=1, needs 5 tokens)
           P1 has 10 tokens
    When: Both enabled by structure
    Then: T2 fires (T1 blocked by insufficient tokens)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=150, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    
    P1.tokens = 10
    
    # Create transitions
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    
    T1.transition_type = "immediate"
    T2.transition_type = "immediate"
    T1.priority = 10  # Higher priority but needs more tokens
    T2.priority = 1   # Lower priority
    
    # Create arcs with different weights
    A1 = doc_ctrl.add_arc(source=P1, target=T1)
    A1.weight = 20  # T1 needs 20 tokens (more than available)
    doc_ctrl.add_arc(source=T1, target=P2)
    
    A3 = doc_ctrl.add_arc(source=P1, target=T2)
    A3.weight = 5  # T2 needs 5 tokens (available)
    doc_ctrl.add_arc(source=T2, target=P3)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(manager)
    
    # Step - T2 should fire (T1 cannot due to insufficient tokens)
    controller.step(time_step=0.001)
    
    assert P3.tokens >= 1, "T2 should fire despite lower priority (T1 blocked)"
    assert P2.tokens == 0, "T1 should not fire (insufficient tokens)"


def test_priority_with_guards():
    """
    Test priority interaction with guards.
    
    Given: T1(priority=10, guard=False), T2(priority=1, guard=True)
    When: Both checked
    Then: T2 fires (T1 blocked by guard)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=150, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    
    P1.tokens = 10
    
    # Create transitions
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    
    T1.transition_type = "immediate"
    T2.transition_type = "immediate"
    T1.priority = 10  # Higher priority
    T2.priority = 1
    
    T1.guard = lambda: False  # Blocked by guard
    T2.guard = lambda: True   # Allowed by guard
    
    # Create arcs
    doc_ctrl.add_arc(source=P1, target=T1)
    doc_ctrl.add_arc(source=T1, target=P2)
    doc_ctrl.add_arc(source=P1, target=T2)
    doc_ctrl.add_arc(source=T2, target=P3)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(manager)
    
    # Step - T2 should fire (T1 blocked by guard)
    controller.step(time_step=0.001)
    
    assert P3.tokens >= 1, "T2 should fire (T1 blocked by guard)"
    assert P2.tokens == 0, "T1 should not fire (guard=False)"


def test_priority_levels():
    """
    Test various priority levels (0, 1, 5, 10, 100).
    
    Given: Five transitions with different priority levels
    When: All enabled
    Then: Fire in descending priority order
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create source place
    P0 = doc_ctrl.add_place(x=100, y=300, label="P0")
    P0.tokens = 5
    
    # Create 5 output places
    places = []
    transitions = []
    priorities = [100, 10, 5, 1, 0]
    
    for i, priority in enumerate(priorities):
        # Create place
        p = doc_ctrl.add_place(x=300, y=100 + i*100, label=f"P{i+1}")
        places.append(p)
        
        # Create transition
        t = doc_ctrl.add_transition(x=200, y=100 + i*100, label=f"T{i+1}")
        t.transition_type = "immediate"
        t.priority = priority
        transitions.append(t)
        
        # Create arcs
        doc_ctrl.add_arc(source=P0, target=t)
        doc_ctrl.add_arc(source=t, target=p)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    controller = SimulationController(manager)
    controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
    
    # Single step - all immediate transitions exhaust in priority order
    controller.step(time_step=0.001)
    
    # Check that all fired (P0 empty, all outputs have tokens)
    assert P0.tokens == 0, "All tokens should be consumed"
    total_out = sum(p.tokens for p in places)
    assert total_out == 5, f"All 5 tokens should be distributed, got {total_out}"
    
    # With PRIORITY policy, highest priority fires first and exhausts all tokens
    # So P1 (priority=100) gets all 5 tokens, others get nothing
    assert places[0].tokens == 5, f"P1 (priority=100) should have all 5 tokens, got {places[0].tokens}"
    for i in range(1, 5):
        assert places[i].tokens == 0, f"P{i+1} (lower priority) should have 0 tokens, got {places[i].tokens}"


def test_zero_priority():
    """
    Test transition with priority=0 (lowest priority).
    
    Given: T1(priority=0), T2(priority=1)
    When: Both enabled
    Then: T2 fires first
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=150, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    
    P1.tokens = 2
    
    # Create transitions
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    
    T1.transition_type = "immediate"
    T2.transition_type = "immediate"
    T1.priority = 0  # Lowest
    T2.priority = 1
    
    # Create arcs
    doc_ctrl.add_arc(source=P1, target=T1)
    doc_ctrl.add_arc(source=T1, target=P2)
    doc_ctrl.add_arc(source=P1, target=T2)
    doc_ctrl.add_arc(source=T2, target=P3)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    controller = SimulationController(manager)
    controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
    
    # First step
    controller.step(time_step=0.001)
    
    # T2 should fire first (higher priority)
    assert P3.tokens >= 1, "T2 (priority=1) should fire before T1 (priority=0)"


def test_conflict_resolution_same_priority():
    """
    Test conflict resolution when multiple transitions have same priority.
    
    Given: Three transitions, all priority=5
    When: All enabled
    Then: One fires (deterministic based on implementation)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P0 = doc_ctrl.add_place(x=100, y=200, label="P0")
    P0.tokens = 3
    
    P1 = doc_ctrl.add_place(x=300, y=100, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=200, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=300, label="P3")
    
    # Create transitions (all same priority)
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    T3 = doc_ctrl.add_transition(x=200, y=300, label="T3")
    
    for t in [T1, T2, T3]:
        t.transition_type = "immediate"
        t.priority = 5  # All same priority
    
    # Create arcs
    doc_ctrl.add_arc(source=P0, target=T1)
    doc_ctrl.add_arc(source=T1, target=P1)
    doc_ctrl.add_arc(source=P0, target=T2)
    doc_ctrl.add_arc(source=T2, target=P2)
    doc_ctrl.add_arc(source=P0, target=T3)
    doc_ctrl.add_arc(source=T3, target=P3)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    controller = SimulationController(manager)
    controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
    
    # First step - exactly one should fire
    controller.step(time_step=0.001)
    
    fired_count = sum([1 if p.tokens > 0 else 0 for p in [P1, P2, P3]])
    assert fired_count == 1, "Exactly one transition should fire per step"
    
    # Complete simulation
    while controller.time < 1.0:
        fired = controller.step(time_step=0.001)
        if not fired:
            break
    
    # All tokens distributed
    assert P0.tokens == 0
    assert P1.tokens + P2.tokens + P3.tokens == 3


def test_mixed_priority_levels():
    """
    Test stratified conflict resolution with mixed priorities.
    
    Given: T1(p=10), T2(p=10), T3(p=5), T4(p=5), T5(p=1)
    When: All enabled
    Then: Fires in priority order: 10, 10, 5, 5, 1
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create source
    P0 = doc_ctrl.add_place(x=100, y=300, label="P0")
    P0.tokens = 5
    
    # Create transitions with mixed priorities
    priorities = [10, 10, 5, 5, 1]
    transitions = []
    places = []
    
    for i, priority in enumerate(priorities):
        p = doc_ctrl.add_place(x=300, y=100 + i*80, label=f"P{i+1}")
        places.append(p)
        
        t = doc_ctrl.add_transition(x=200, y=100 + i*80, label=f"T{i+1}")
        t.transition_type = "immediate"
        t.priority = priority
        transitions.append(t)
        
        doc_ctrl.add_arc(source=P0, target=t)
        doc_ctrl.add_arc(source=t, target=p)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    controller = SimulationController(manager)
    controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
    
    # Track firing order by priority
    fired_priorities = []
    
    for step in range(5):
        tokens_before = [p.tokens for p in places]
        fired = controller.step(time_step=0.001)
        if not fired:
            break
        tokens_after = [p.tokens for p in places]
        
        for i, (before, after) in enumerate(zip(tokens_before, tokens_after)):
            if after > before:
                fired_priorities.append(priorities[i])
                break
    
    # Check priorities are non-increasing (stratified)
    for i in range(len(fired_priorities) - 1):
        assert fired_priorities[i] >= fired_priorities[i+1], \
            f"Priorities should be non-increasing: {fired_priorities}"


def test_priority_exhaustion():
    """
    Test immediate exhaustion with priorities.
    
    Given: T1(p=10) and T2(p=5) both enabled
    When: Single step called
    Then: All immediate transitions exhaust in priority order
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=150, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    
    P1.tokens = 5
    
    # Create transitions
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    
    T1.transition_type = "immediate"
    T2.transition_type = "immediate"
    T1.priority = 10
    T2.priority = 5
    
    # Create arcs
    doc_ctrl.add_arc(source=P1, target=T1)
    doc_ctrl.add_arc(source=T1, target=P2)
    doc_ctrl.add_arc(source=P1, target=T2)
    doc_ctrl.add_arc(source=T2, target=P3)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(manager)
    
    # Single step should exhaust all immediate transitions
    controller.step(time_step=0.001)
    
    # All tokens should be consumed
    assert P1.tokens == 0, "All immediate transitions should exhaust in one step"
    assert P2.tokens + P3.tokens == 5, "All tokens distributed"


def test_default_priority():
    """
    Test transitions without explicit priority (should use default).
    
    Given: T1 (no priority set), T2 (no priority set)
    When: Both enabled
    Then: Both fire (default priority behavior)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=150, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    
    P1.tokens = 2
    
    # Create transitions (no explicit priority)
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    
    T1.transition_type = "immediate"
    T2.transition_type = "immediate"
    # No priority set - should use default (typically 0 or 1)
    
    # Create arcs
    doc_ctrl.add_arc(source=P1, target=T1)
    doc_ctrl.add_arc(source=T1, target=P2)
    doc_ctrl.add_arc(source=P1, target=T2)
    doc_ctrl.add_arc(source=T2, target=P3)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(manager)
    
    # Run to completion
    while controller.time < 1.0:
        fired = controller.step(time_step=0.001)
        if not fired:
            break
    
    # Both should eventually fire
    assert P1.tokens == 0, "All tokens consumed"
    assert P2.tokens + P3.tokens == 2, "All tokens distributed"


def test_priority_stability():
    """
    Test that same priority gives consistent firing order.
    
    Given: Three transitions with same priority
    When: Run multiple times
    Then: Same order each time (deterministic)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    from shypn.engine.simulation.controller import SimulationController
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    
    def run_simulation():
        """Run simulation and return firing order."""
        manager = ModelCanvasManager()
        doc_ctrl = manager.document_controller
        
        # Create places
        P0 = doc_ctrl.add_place(x=100, y=200, label="P0")
        P0.tokens = 3
        
        P1 = doc_ctrl.add_place(x=300, y=100, label="P1")
        P2 = doc_ctrl.add_place(x=300, y=200, label="P2")
        P3 = doc_ctrl.add_place(x=300, y=300, label="P3")
        
        # Create transitions (same priority, specific order)
        T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
        T2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
        T3 = doc_ctrl.add_transition(x=200, y=300, label="T3")
        
        for t in [T1, T2, T3]:
            t.transition_type = "immediate"
            t.priority = 5
        
        # Create arcs
        doc_ctrl.add_arc(source=P0, target=T1)
        doc_ctrl.add_arc(source=T1, target=P1)
        doc_ctrl.add_arc(source=P0, target=T2)
        doc_ctrl.add_arc(source=T2, target=P2)
        doc_ctrl.add_arc(source=P0, target=T3)
        doc_ctrl.add_arc(source=T3, target=P3)
        
        # Run simulation
        controller = SimulationController(manager)
        controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
        
        firing_order = []
        while controller.time < 1.0:
            tokens_before = [P1.tokens, P2.tokens, P3.tokens]
            fired = controller.step(time_step=0.001)
            if not fired:
                break
            tokens_after = [P1.tokens, P2.tokens, P3.tokens]
            
            for i, (before, after) in enumerate(zip(tokens_before, tokens_after)):
                if after > before:
                    firing_order.append(i + 1)  # 1, 2, or 3
                    break
        
        return firing_order
    
    # Run simulation multiple times
    first_order = run_simulation()
    
    for _ in range(3):
        order = run_simulation()
        assert order == first_order, \
            f"Firing order should be deterministic: {first_order} vs {order}"


def test_complex_priority_scenario():
    """
    Test complex scenario with 5 transitions and 3 priority levels.
    
    Given: Multiple transitions at different priority levels
           with different token requirements
    When: Simulation runs
    Then: Fires in correct priority order respecting constraints
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P0 = doc_ctrl.add_place(x=100, y=300, label="P0")
    P0.tokens = 20
    
    # Output places
    outputs = []
    for i in range(5):
        p = doc_ctrl.add_place(x=300, y=100 + i*80, label=f"OUT{i+1}")
        outputs.append(p)
    
    # Create transitions with mixed priorities and weights
    configs = [
        ("T1", 10, 2),   # priority=10, weight=2
        ("T2", 10, 3),   # priority=10, weight=3
        ("T3", 5, 1),    # priority=5, weight=1
        ("T4", 5, 5),    # priority=5, weight=5
        ("T5", 1, 2),    # priority=1, weight=2
    ]
    
    for i, (name, priority, weight) in enumerate(configs):
        t = doc_ctrl.add_transition(x=200, y=100 + i*80, label=name)
        t.transition_type = "immediate"
        t.priority = priority
        
        # Input arc with specific weight
        a_in = doc_ctrl.add_arc(source=P0, target=t)
        a_in.weight = weight
        
        # Output arc (same weight for token conservation)
        a_out = doc_ctrl.add_arc(source=t, target=outputs[i])
        a_out.weight = weight  # Match input weight for conservation
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    controller = SimulationController(manager)
    controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
    
    while controller.time < 1.0:
        fired = controller.step(time_step=0.001)
        if not fired:
            break
    
    # Verify all tokens distributed
    total_out = sum(p.tokens for p in outputs)
    assert P0.tokens + total_out == 20, f"Token conservation: P0={P0.tokens}, total_out={total_out}"
    
    # At least some transitions should have fired
    fired_count = sum(1 for p in outputs if p.tokens > 0)
    assert fired_count > 0, "At least one transition should fire"


def test_priority_with_guards_complex():
    """
    Test complex interaction between priorities and guards.
    
    Given: Multiple transitions with priorities and token-based guards
    When: Guards change as tokens move
    Then: Priority selection respects current guard states
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create places
    P1 = doc_ctrl.add_place(x=100, y=200, label="P1")
    P2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    P3 = doc_ctrl.add_place(x=300, y=300, label="P3")
    
    P1.tokens = 15
    P2.tokens = 0
    
    # Create transitions
    T1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    T2 = doc_ctrl.add_transition(x=200, y=300, label="T2")
    
    T1.transition_type = "immediate"
    T2.transition_type = "immediate"
    T1.priority = 10  # Higher priority
    T2.priority = 5
    
    # Guards based on token distribution
    T1.guard = lambda: P1.tokens > 10  # Fires while P1 > 10
    T2.guard = lambda: P1.tokens <= 10  # Fires when P1 <= 10
    
    # Create arcs
    doc_ctrl.add_arc(source=P1, target=T1)
    doc_ctrl.add_arc(source=T1, target=P2)
    doc_ctrl.add_arc(source=P1, target=T2)
    doc_ctrl.add_arc(source=T2, target=P3)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(manager)
    
    while controller.time < 1.0:
        fired = controller.step(time_step=0.001)
        if not fired:
            break
    
    # T1 should fire first (higher priority, guard true initially)
    # Then T2 fires (when P1 <= 10)
    assert P2.tokens > 0, "T1 should fire when P1 > 10"
    assert P3.tokens > 0, "T2 should fire when P1 <= 10"
    assert P1.tokens == 0, "All tokens consumed"
    assert P2.tokens + P3.tokens == 15, "Token conservation"


def test_priority_ordering_verification():
    """
    Verify that priority ordering is strictly enforced.
    
    Given: Transitions with priorities 10, 5, 3, 1, 0
    When: All enabled simultaneously
    Then: Fire in exact priority order (no inversions)
    """
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create source
    P0 = doc_ctrl.add_place(x=100, y=300, label="P0")
    P0.tokens = 5
    
    # Create transitions with specific priorities
    priorities = [10, 5, 3, 1, 0]
    places = []
    
    for i, priority in enumerate(priorities):
        p = doc_ctrl.add_place(x=300, y=100 + i*80, label=f"P{i+1}")
        places.append(p)
        
        t = doc_ctrl.add_transition(x=200, y=100 + i*80, label=f"T{priority}")
        t.transition_type = "immediate"
        t.priority = priority
        
        doc_ctrl.add_arc(source=P0, target=t)
        doc_ctrl.add_arc(source=t, target=p)
    
    # Run simulation
    from shypn.engine.simulation.controller import SimulationController
    from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
    controller = SimulationController(manager)
    controller.set_conflict_policy(ConflictResolutionPolicy.PRIORITY)
    
    # Single step - all immediate transitions should exhaust
    controller.step(time_step=0.001)
    
    # Check that all tokens consumed
    assert P0.tokens == 0, f"All source tokens consumed, got {P0.tokens}"
    
    # Verify all tokens distributed
    total_out = sum(p.tokens for p in places)
    assert total_out == 5, f"All 5 tokens distributed, got {total_out}"
    
    # With PRIORITY policy, highest priority fires first and exhausts all tokens
    # T10 (priority=10) should consume all 5 tokens before lower priority transitions fire
    P1, P2, P3, P4, P5 = places
    assert P1.tokens == 5, f"P1 (T10 priority=10) should have all 5 tokens, got {P1.tokens}"
    assert P2.tokens == 0, f"P2 (T5 priority=5) should have 0 tokens, got {P2.tokens}"
    assert P3.tokens == 0, f"P3 (T3 priority=3) should have 0 tokens, got {P3.tokens}"
    assert P4.tokens == 0, f"P4 (T1 priority=1) should have 0 tokens, got {P4.tokens}"
    assert P5.tokens == 0, f"P5 (T0 priority=0) should have 0 tokens, got {P5.tokens}"
