"""
Shared fixtures for mixed transition type validation tests.
"""
import pytest


@pytest.fixture
def manager():
    """Create a ModelCanvasManager instance with SimulationController."""
    from shypn.data.model_canvas_manager import ModelCanvasManager
    from shypn.engine.simulation.controller import SimulationController
    
    mgr = ModelCanvasManager()
    controller = SimulationController(mgr)
    
    # Attach controller and convenience methods
    mgr._controller = controller
    mgr.step = controller.step
    
    # Make current_time accessible as attribute
    @property
    def current_time(self):
        return self._controller.time
    
    mgr.__class__.current_time = current_time
    
    return mgr


@pytest.fixture
def document_controller(manager):
    """Get the document controller from the manager."""
    return manager.document_controller


@pytest.fixture
def mixed_immediate_timed_model(manager):
    """
    Model with both immediate and timed transitions:
    
        P1 ──→ T1(immediate) ──→ P2 ──→ T2(timed) ──→ P3
        
    Initial: P1=1, P2=0, P3=0
    T1: immediate (priority 5)
    T2: timed [earliest=1.0, latest=2.0]
    """
    doc_ctrl = manager.document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=500, y=100, label="P3")
    
    # Set initial marking
    p1.tokens = 1
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t2 = doc_ctrl.add_transition(x=400, y=100, label="T2")
    
    # Configure T1 as immediate with priority 5
    t1.transition_type = "immediate"
    t1.priority = 5
    
    # Configure T2 as timed [1.0, 2.0]
    t2.transition_type = "timed"
    t2.properties = {'earliest': 1.0, 'latest': 2.0}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1)
    doc_ctrl.add_arc(source=p2, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p3, weight=1)
    
    return manager


@pytest.fixture
def mixed_immediate_stochastic_model(manager):
    """
    Model with both immediate and stochastic transitions:
    
        P1 ──→ T1(immediate) ──→ P2 ──→ T2(stochastic) ──→ P3
        
    Initial: P1=1, P2=0, P3=0
    T1: immediate (priority 5)
    T2: stochastic (rate=2.0)
    """
    doc_ctrl = manager.document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=500, y=100, label="P3")
    
    # Set initial marking
    p1.tokens = 1
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t2 = doc_ctrl.add_transition(x=400, y=100, label="T2")
    
    # Configure T1 as immediate with priority 5
    t1.transition_type = "immediate"
    t1.priority = 5
    
    # Configure T2 as stochastic with rate=2.0
    t2.transition_type = "stochastic"
    t2.properties = {'rate': 2.0, 'max_burst': 1}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1)
    doc_ctrl.add_arc(source=p2, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p3, weight=1)
    
    return manager


@pytest.fixture
def mixed_timed_stochastic_model(manager):
    """
    Model with both timed and stochastic transitions:
    
        P1 ──→ T1(timed) ──→ P2 ──→ T2(stochastic) ──→ P3
        
    Initial: P1=1, P2=0, P3=0
    T1: timed [earliest=0.5, latest=1.0]
    T2: stochastic (rate=2.0)
    """
    doc_ctrl = manager.document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=500, y=100, label="P3")
    
    # Set initial marking
    p1.tokens = 1
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t2 = doc_ctrl.add_transition(x=400, y=100, label="T2")
    
    # Configure T1 as timed [0.5, 1.0]
    t1.transition_type = "timed"
    t1.properties = {'earliest': 0.5, 'latest': 1.0}
    
    # Configure T2 as stochastic with rate=2.0
    t2.transition_type = "stochastic"
    t2.properties = {'rate': 2.0, 'max_burst': 1}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1)
    doc_ctrl.add_arc(source=p2, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p3, weight=1)
    
    return manager


@pytest.fixture
def mixed_all_types_model(manager):
    """
    Model with all three transition types:
    
        P1 ──→ T1(immediate) ──→ P2 ──→ T2(timed) ──→ P3 ──→ T3(stochastic) ──→ P4
        
    Initial: P1=1, P2=0, P3=0, P4=0
    T1: immediate (priority 5)
    T2: timed [earliest=1.0, latest=2.0]
    T3: stochastic (rate=2.0)
    """
    doc_ctrl = manager.document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=100, label="P1")
    p2 = doc_ctrl.add_place(x=250, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=400, y=100, label="P3")
    p4 = doc_ctrl.add_place(x=550, y=100, label="P4")
    
    # Set initial marking
    p1.tokens = 1
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=175, y=100, label="T1")
    t2 = doc_ctrl.add_transition(x=325, y=100, label="T2")
    t3 = doc_ctrl.add_transition(x=475, y=100, label="T3")
    
    # Configure T1 as immediate with priority 5
    t1.transition_type = "immediate"
    t1.priority = 5
    
    # Configure T2 as timed [1.0, 2.0]
    t2.transition_type = "timed"
    t2.properties = {'earliest': 1.0, 'latest': 2.0}
    
    # Configure T3 as stochastic with rate=2.0
    t3.transition_type = "stochastic"
    t3.properties = {'rate': 2.0, 'max_burst': 1}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1)
    doc_ctrl.add_arc(source=p2, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p3, weight=1)
    doc_ctrl.add_arc(source=p3, target=t3, weight=1)
    doc_ctrl.add_arc(source=t3, target=p4, weight=1)
    
    return manager


@pytest.fixture
def mixed_priority_conflict_model(manager):
    """
    Model with competing transitions of different types:
    
             ┌──→ T1(immediate, priority 10) ──→ P2
        P1 ──┼──→ T2(timed [0.5, 1.0]) ──→ P3
             └──→ T3(stochastic, rate=2.0) ──→ P4
        
    Initial: P1=3
    All transitions compete for tokens from P1
    Tests priority across different types
    """
    doc_ctrl = manager.document_controller
    
    # Create places
    p1 = doc_ctrl.add_place(x=100, y=200, label="P1")
    p2 = doc_ctrl.add_place(x=300, y=100, label="P2")
    p3 = doc_ctrl.add_place(x=300, y=200, label="P3")
    p4 = doc_ctrl.add_place(x=300, y=300, label="P4")
    
    # Set initial marking
    p1.tokens = 3
    
    # Create transitions
    t1 = doc_ctrl.add_transition(x=200, y=100, label="T1")
    t2 = doc_ctrl.add_transition(x=200, y=200, label="T2")
    t3 = doc_ctrl.add_transition(x=200, y=300, label="T3")
    
    # Configure T1 as immediate with priority 10
    t1.transition_type = "immediate"
    t1.priority = 10
    
    # Configure T2 as timed [0.5, 1.0]
    t2.transition_type = "timed"
    t2.properties = {'earliest': 0.5, 'latest': 1.0}
    
    # Configure T3 as stochastic with rate=2.0
    t3.transition_type = "stochastic"
    t3.properties = {'rate': 2.0, 'max_burst': 1}
    
    # Create arcs
    doc_ctrl.add_arc(source=p1, target=t1, weight=1)
    doc_ctrl.add_arc(source=t1, target=p2, weight=1)
    doc_ctrl.add_arc(source=p1, target=t2, weight=1)
    doc_ctrl.add_arc(source=t2, target=p3, weight=1)
    doc_ctrl.add_arc(source=p1, target=t3, weight=1)
    doc_ctrl.add_arc(source=t3, target=p4, weight=1)
    
    return manager


@pytest.fixture
def run_mixed_simulation(manager):
    """Helper to run simulation up to a condition or time limit."""
    def _run(condition_fn, max_time=10.0, max_steps=100):
        """
        Run simulation until condition_fn returns True or limits reached.
        Returns (success, steps, final_time).
        """
        steps = 0
        while steps < max_steps and manager.current_time < max_time:
            if condition_fn():
                return True, steps, manager.current_time
            
            if not manager.step():
                break
            steps += 1
        
        return condition_fn(), steps, manager.current_time
    
    return _run


@pytest.fixture
def assert_mixed_tokens(manager):
    """Helper to assert token counts in mixed models."""
    def _assert(expected_tokens):
        """
        Assert token counts match expected values.
        expected_tokens: dict {place_label: expected_count}
        """
        places = manager.places
        for label, expected in expected_tokens.items():
            place = next((p for p in places if p.label == label), None)
            assert place is not None, f"Place {label} not found"
            actual = place.tokens
            assert actual == expected, \
                f"Place {label}: expected {expected} tokens, got {actual}"
    
    return _assert


@pytest.fixture
def get_mixed_transition_info(manager):
    """Helper to get transition information in mixed models."""
    def _get(label):
        """
        Get transition info by label.
        Returns dict with type, priority, timing info, etc.
        """
        transitions = manager.transitions
        transition = next((t for t in transitions if t.label == label), None)
        if transition is None:
            return None
        
        info = {
            "id": transition.id,
            "label": transition.label,
            "type": transition.transition_type,
            "enabled": transition.is_enabled(),
        }
        
        # Add type-specific info
        if transition.transition_type == "immediate":
            info["priority"] = transition.priority
        elif transition.transition_type == "timed":
            info["earliest"] = transition.earliest_fire_time
            info["latest"] = transition.latest_fire_time
            if hasattr(transition, 'enablement_time'):
                info["enablement_time"] = transition.enablement_time
        elif transition.transition_type == "stochastic":
            info["rate"] = transition.rate
            if hasattr(transition, 'enablement_time'):
                info["enablement_time"] = transition.enablement_time
        
        return info
    
    return _get
