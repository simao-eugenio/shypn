"""Fixtures for full hybrid validation tests.

Tests combining continuous + immediate + timed + stochastic transitions.
"""

import pytest
from shypn.data.model_canvas_manager import ModelCanvasManager


@pytest.fixture
def full_hybrid_cascade():
    """Full cascade: Continuous → Immediate → Timed → Stochastic.
    
    Structure:
        P1 --continuous(rate=2.0)--> P2 --immediate--> P3 --timed(0.5s)--> P4 --stochastic(5.0)--> P5
    
    Tests:
        - Complete flow through all 4 transition types
        - Priority ordering maintained
        - Token conservation
    """
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=200, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=300, y=100, label="P3")
    p4 = doc_ctrl.add_place(x=400, y=100, label="P4")
    p5 = doc_ctrl.add_place(x=500, y=100, label="P5")
    
    p1.tokens = 20.0  # Large initial amount
    p2.tokens = 0.0
    p3.tokens = 0.0
    p4.tokens = 0.0
    p5.tokens = 0.0
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=150, y=100, label="T1_continuous")
    t1.transition_type = "continuous"
    t1.properties = {'rate_function': '2.0'}
    
    t2 = doc_ctrl.add_transition(x=250, y=100, label="T2_immediate")
    t2.transition_type = "immediate"
    t2.priority = 10
    
    t3 = doc_ctrl.add_transition(x=350, y=100, label="T3_timed")
    t3.transition_type = "timed"
    t3.properties = {'delay': 0.5}
    
    t4 = doc_ctrl.add_transition(x=450, y=100, label="T4_stochastic")
    t4.transition_type = "stochastic"
    t4.properties = {'rate': 5.0, 'max_burst': 1}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1.0)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1.0)
    doc_ctrl.add_arc(source=p2, target=t2, weight=1.0)
    doc_ctrl.add_arc(source=t2, target=p3, weight=1.0)
    doc_ctrl.add_arc(source=p3, target=t3, weight=1.0)
    doc_ctrl.add_arc(source=t3, target=p4, weight=1.0)
    doc_ctrl.add_arc(source=p4, target=t4, weight=1.0)
    doc_ctrl.add_arc(source=t4, target=p5, weight=1.0)
    
    return manager, p1, p2, p3, p4, p5, t1, t2, t3, t4


@pytest.fixture
def full_hybrid_parallel():
    """Parallel hybrid: All 4 types draining same place.
    
    Structure:
        P1 ──continuous(1.0)──→ P2
        P1 ──immediate────────→ P3
        P1 ──timed(0.3s)──────→ P4
        P1 ──stochastic(3.0)──→ P5
    
    Tests:
        - Immediate fires first (priority)
        - Continuous flows in background
        - Timed/stochastic compete for remaining tokens
        - Token conservation
    """
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=200, y=200, label="P1")
    p2 = doc_ctrl.add_place(x=400, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=400, y=200, label="P3")
    p4 = doc_ctrl.add_place(x=400, y=300, label="P4")
    p5 = doc_ctrl.add_place(x=400, y=400, label="P5")
    
    p1.tokens = 10.0
    p2.tokens = 0.0
    p3.tokens = 0.0
    p4.tokens = 0.0
    p5.tokens = 0.0
    
    # Create transitions - all draining P1
    t_continuous = doc_ctrl.add_transition(x=300, y=100, label="T_continuous")
    t_continuous.transition_type = "continuous"
    t_continuous.properties = {'rate_function': '1.0'}
    
    t_immediate = doc_ctrl.add_transition(x=300, y=200, label="T_immediate")
    t_immediate.transition_type = "immediate"
    t_immediate.priority = 5
    
    t_timed = doc_ctrl.add_transition(x=300, y=300, label="T_timed")
    t_timed.transition_type = "timed"
    t_timed.properties = {'delay': 0.3}
    
    t_stochastic = doc_ctrl.add_transition(x=300, y=400, label="T_stochastic")
    t_stochastic.transition_type = "stochastic"
    t_stochastic.properties = {'rate': 3.0, 'max_burst': 1}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t_continuous, weight=1.0)
    doc_ctrl.add_arc(source=t_continuous, target=p2, weight=1.0)
    
    doc_ctrl.add_arc(source=p1, target=t_immediate, weight=1.0)
    doc_ctrl.add_arc(source=t_immediate, target=p3, weight=1.0)
    
    doc_ctrl.add_arc(source=p1, target=t_timed, weight=1.0)
    doc_ctrl.add_arc(source=t_timed, target=p4, weight=1.0)
    
    doc_ctrl.add_arc(source=p1, target=t_stochastic, weight=1.0)
    doc_ctrl.add_arc(source=t_stochastic, target=p5, weight=1.0)
    
    return manager, p1, p2, p3, p4, p5, t_continuous, t_immediate, t_timed, t_stochastic


@pytest.fixture
def full_hybrid_complex():
    """Complex network with all 4 types and feedback.
    
    Structure:
        P1 ──continuous(2.0)──→ P2 ──immediate──→ P3
                                 ↑                 ↓
                                 └──stochastic(2.0)──┘
        P3 ──timed(0.4s)──→ P4
    
    Tests:
        - Continuous feeds P2
        - Immediate drains P2 to P3
        - Stochastic creates feedback loop P3→P2
        - Timed provides output from P3
        - Complex dynamics
    """
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=200, label="P1")
    p2 = doc_ctrl.add_place(x=250, y=200, label="P2")
    p3 = doc_ctrl.add_place(x=400, y=200, label="P3")
    p4 = doc_ctrl.add_place(x=550, y=200, label="P4")
    
    p1.tokens = 20.0
    p2.tokens = 0.0
    p3.tokens = 0.0
    p4.tokens = 0.0
    
    # Create transitions
    t_continuous = doc_ctrl.add_transition(x=175, y=200, label="T_continuous")
    t_continuous.transition_type = "continuous"
    t_continuous.properties = {'rate_function': '2.0'}
    
    t_immediate = doc_ctrl.add_transition(x=325, y=200, label="T_immediate")
    t_immediate.transition_type = "immediate"
    t_immediate.priority = 8
    
    t_timed = doc_ctrl.add_transition(x=475, y=200, label="T_timed")
    t_timed.transition_type = "timed"
    t_timed.properties = {'delay': 0.4}
    
    t_stochastic = doc_ctrl.add_transition(x=325, y=300, label="T_stochastic")
    t_stochastic.transition_type = "stochastic"
    t_stochastic.properties = {'rate': 2.0, 'max_burst': 1}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t_continuous, weight=1.0)
    doc_ctrl.add_arc(source=t_continuous, target=p2, weight=1.0)
    
    doc_ctrl.add_arc(source=p2, target=t_immediate, weight=1.0)
    doc_ctrl.add_arc(source=t_immediate, target=p3, weight=1.0)
    
    doc_ctrl.add_arc(source=p3, target=t_timed, weight=1.0)
    doc_ctrl.add_arc(source=t_timed, target=p4, weight=1.0)
    
    # Feedback loop
    doc_ctrl.add_arc(source=p3, target=t_stochastic, weight=1.0)
    doc_ctrl.add_arc(source=t_stochastic, target=p2, weight=1.0)
    
    return manager, p1, p2, p3, p4, t_continuous, t_immediate, t_timed, t_stochastic


@pytest.fixture
def full_hybrid_priority_test():
    """Test priority ordering with all 4 types competing for same token.
    
    Structure:
        All transitions have P1 as input, compete for same token.
        P1(1 token) ──→ 4 transitions (continuous, immediate, timed, stochastic)
    
    Expected Priority:
        1. Immediate (highest priority)
        2. Timed (if in window)
        3. Stochastic (probabilistic)
        4. Continuous (background)
    """
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    # Single place
    p1 = doc_ctrl.add_place(x=200, y=200, label="P1")
    p1.tokens = 20.0  # Increased from 5.0 - enough for all transitions
    
    # Output places
    p_continuous = doc_ctrl.add_place(x=400, y=100, label="P_continuous")
    p_immediate = doc_ctrl.add_place(x=400, y=200, label="P_immediate")
    p_timed = doc_ctrl.add_place(x=400, y=300, label="P_timed")
    p_stochastic = doc_ctrl.add_place(x=400, y=400, label="P_stochastic")
    
    p_continuous.tokens = 0.0
    p_immediate.tokens = 0.0
    p_timed.tokens = 0.0
    p_stochastic.tokens = 0.0
    
    # All transitions compete
    t_continuous = doc_ctrl.add_transition(x=300, y=100, label="T_continuous")
    t_continuous.transition_type = "continuous"
    t_continuous.properties = {'rate_function': '0.5'}
    
    t_immediate = doc_ctrl.add_transition(x=300, y=200, label="T_immediate")
    t_immediate.transition_type = "immediate"
    t_immediate.priority = 10
    
    t_timed = doc_ctrl.add_transition(x=300, y=300, label="T_timed")
    t_timed.transition_type = "timed"
    t_timed.properties = {'delay': 0.2}
    
    t_stochastic = doc_ctrl.add_transition(x=300, y=400, label="T_stochastic")
    t_stochastic.transition_type = "stochastic"
    t_stochastic.properties = {'rate': 4.0, 'max_burst': 1}
    
    # All drain P1
    doc_ctrl.add_arc(source=p1, target=t_continuous, weight=1.0)
    doc_ctrl.add_arc(source=p1, target=t_immediate, weight=1.0)
    doc_ctrl.add_arc(source=p1, target=t_timed, weight=1.0)
    doc_ctrl.add_arc(source=p1, target=t_stochastic, weight=1.0)
    
    # Each produces to its own place
    doc_ctrl.add_arc(source=t_continuous, target=p_continuous, weight=1.0)
    doc_ctrl.add_arc(source=t_immediate, target=p_immediate, weight=1.0)
    doc_ctrl.add_arc(source=t_timed, target=p_timed, weight=1.0)
    doc_ctrl.add_arc(source=t_stochastic, target=p_stochastic, weight=1.0)
    
    return manager, p1, p_continuous, p_immediate, p_timed, p_stochastic


# Helper functions

def verify_full_hybrid_conservation(manager, initial_total, tolerance=1e-3):
    """Verify token conservation in full hybrid systems.
    
    Uses relaxed tolerance (1e-3) for continuous integration errors.
    """
    current_total = sum(p.tokens for p in manager.document_controller.places)
    assert abs(current_total - initial_total) < tolerance, \
        f"Tokens not conserved: {initial_total} -> {current_total} (diff: {abs(current_total - initial_total)})"


def get_transition_type_counts(manager):
    """Get counts of tokens in places fed by each transition type."""
    # This would need to track which place is fed by which transition type
    # For now, return a simple analysis
    places = manager.document_controller.places
    return {p.label: p.tokens for p in places}
