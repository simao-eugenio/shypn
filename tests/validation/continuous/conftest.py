"""Fixtures for continuous transition validation tests."""

import pytest
from shypn.netobjs import Place, Transition, Arc
from shypn.data.model_canvas_manager import ModelCanvasManager


@pytest.fixture
def constant_rate_model():
    """Model with constant rate continuous transition.
    
    Structure:
        P1 --[weight=1]--> T1(continuous, rate=2.0) --[weight=1]--> P2
    
    Usage:
        - P1 starts with 10 tokens
        - T1 transfers at constant rate of 2.0 tokens/sec
        - P2 receives tokens
    """
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    p1.tokens = 10.0
    p2.tokens = 0.0
    
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t1.transition_type = "continuous"
    t1.properties = {'rate_function': '2.0'}  # Constant rate
    
    arc_in = doc_ctrl.add_arc(source=p1, target=t1, weight=1.0)
    arc_out = doc_ctrl.add_arc(source=t1, target=p2, weight=1.0)
    
    return manager, p1, t1, p2, arc_in, arc_out


@pytest.fixture
def token_dependent_model():
    """Model with token-dependent rate function.
    
    Structure:
        P1 --[weight=1]--> T1(continuous, rate=0.5*P1) --[weight=1]--> P2
    
    Usage:
        - Rate proportional to P1 tokens (linear draining)
        - Should follow exponential decay
    """
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    p1.tokens = 10.0
    p2.tokens = 0.0
    
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t1.transition_type = "continuous"
    t1.properties = {'rate_function': '0.5 * P1'}  # Linear in P1 tokens
    
    arc_in = doc_ctrl.add_arc(source=p1, target=t1, weight=1.0)
    arc_out = doc_ctrl.add_arc(source=t1, target=p2, weight=1.0)
    
    return manager, p1, t1, p2, arc_in, arc_out


@pytest.fixture
def time_dependent_model():
    """Model with time-dependent rate function.
    
    Structure:
        P1 --[weight=1]--> T1(continuous, rate=1.0+0.5*time) --[weight=1]--> P2
    
    Usage:
        - Rate increases linearly with time
        - Flow accelerates over time
    """
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    p1.tokens = 100.0  # Large initial amount
    p2.tokens = 0.0
    
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t1.transition_type = "continuous"
    t1.properties = {'rate_function': '1.0 + 0.5 * time'}  # Time-dependent
    
    arc_in = doc_ctrl.add_arc(source=p1, target=t1, weight=1.0)
    arc_out = doc_ctrl.add_arc(source=t1, target=p2, weight=1.0)
    
    return manager, p1, t1, p2, arc_in, arc_out


@pytest.fixture
def saturated_rate_model():
    """Model with saturated (min/max) rate function.
    
    Structure:
        P1 --[weight=1]--> T1(continuous, rate=min(5.0, P1)) --[weight=1]--> P2
    
    Usage:
        - Rate saturates at 5.0 when P1 > 5
        - Tests rate clamping behavior
    """
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    p1.tokens = 10.0
    p2.tokens = 0.0
    
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t1.transition_type = "continuous"
    t1.properties = {
        'rate_function': 'min(5.0, P1)',
        'max_rate': 10.0,  # Additional clamp
        'min_rate': 0.0
    }
    
    arc_in = doc_ctrl.add_arc(source=p1, target=t1, weight=1.0)
    arc_out = doc_ctrl.add_arc(source=t1, target=p2, weight=1.0)
    
    return manager, p1, t1, p2, arc_in, arc_out


@pytest.fixture
def source_sink_model():
    """Model with source and sink continuous transitions.
    
    Structure:
        T_source(rate=1.0) --> P1 --> T_sink(rate=0.5)
    
    Usage:
        - T_source generates tokens (no input)
        - T_sink consumes tokens (no output)
        - Tests source/sink enablement
    """
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    p1 = doc_ctrl.add_place(x=200, y=100, label="P1")
    p1.tokens = 5.0
    
    t_source = doc_ctrl.add_transition(x=100, y=100, label="T_source")
    t_source.transition_type = "continuous"
    t_source.is_source = True
    t_source.properties = {'rate_function': '1.0'}
    
    t_sink = doc_ctrl.add_transition(x=300, y=100, label="T_sink")
    t_sink.transition_type = "continuous"
    t_sink.is_sink = True
    t_sink.properties = {'rate_function': '0.5'}
    
    arc_source_out = doc_ctrl.add_arc(source=t_source, target=p1, weight=1.0)  # T_source -> P1
    arc_sink_in = doc_ctrl.add_arc(source=p1, target=t_sink, weight=1.0)       # P1 -> T_sink
    
    return manager, p1, t_source, t_sink, arc_source_out, arc_sink_in


@pytest.fixture
def hybrid_continuous_immediate():
    """Hybrid model with continuous and immediate transitions.
    
    Structure:
        P1 --continuous(rate=1.0)--> P2 --immediate--> P3
    
    Usage:
        - Continuous flow from P1 to P2
        - Immediate transfer from P2 to P3 when enabled
        - Tests interaction between continuous and discrete
    """
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    doc_ctrl = manager.document_controller
    
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=200, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=300, y=100, label="P3")
    p1.tokens = 10.0
    p2.tokens = 0.0
    p3.tokens = 0.0
    
    t1 = doc_ctrl.add_transition(x=150, y=100, label="T1_continuous")
    t1.transition_type = "continuous"
    t1.properties = {'rate_function': '1.0'}
    
    t2 = doc_ctrl.add_transition(x=250, y=100, label="T2_immediate")
    t2.transition_type = "immediate"
    t2.priority = 1
    
    arc1_in = doc_ctrl.add_arc(source=p1, target=t1, weight=1.0)
    arc1_out = doc_ctrl.add_arc(source=t1, target=p2, weight=1.0)
    arc2_in = doc_ctrl.add_arc(source=p2, target=t2, weight=1.0)
    arc2_out = doc_ctrl.add_arc(source=t2, target=p3, weight=1.0)
    
    return manager, p1, p2, p3, t1, t2


# ============================================================================
# Helper Functions
# ============================================================================

def get_continuous_transition(manager, label):
    """Get transition by label and verify it's continuous."""
    t = next((t for t in manager.document_controller.transitions if t.label == label), None)
    assert t is not None, f"Transition {label} not found"
    assert t.transition_type == "continuous", f"Transition {label} is not continuous"
    return t


def verify_token_conservation(manager, initial_total, tolerance=1e-6):
    """Verify total token count is conserved (for closed systems)."""
    current_total = sum(p.tokens for p in manager.document_controller.places)
    assert abs(current_total - initial_total) < tolerance, \
        f"Tokens not conserved: {initial_total} -> {current_total}"


def verify_continuous_flow(p_source, p_target, expected_transfer, tolerance=0.1):
    """Verify expected token flow between places (with numerical tolerance)."""
    # This allows for numerical integration error
    actual_transfer = p_target.tokens
    assert abs(actual_transfer - expected_transfer) < tolerance, \
        f"Expected transfer ~{expected_transfer}, got {actual_transfer}"
