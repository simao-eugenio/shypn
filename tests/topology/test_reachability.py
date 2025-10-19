"""Tests for reachability analyzer."""

import pytest
from unittest.mock import Mock

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer
from shypn.topology.base.exceptions import TopologyAnalysisError


def create_mock_place(place_id, name, marking=0):
    """Helper to create mock place."""
    place = Mock()
    place.id = place_id
    place.name = name
    place.marking = marking
    return place


def create_mock_transition(trans_id, name):
    """Helper to create mock transition."""
    trans = Mock()
    trans.id = trans_id
    trans.name = name
    return trans


def create_mock_arc(source_id, target_id, weight=1):
    """Helper to create mock arc."""
    arc = Mock()
    arc.source_id = source_id
    arc.target_id = target_id
    arc.weight = weight
    return arc


def test_simple_linear_net():
    """Test reachability in simple linear net."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('total_states') == 2  # Initial and after firing t1
    assert result.get('total_transitions') >= 1
    assert result.get('is_bounded')


def test_simple_cycle():
    """Test reachability in cyclic net."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    # Self-loop: P1→T1→P1
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p1')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze(max_states=10)
    
    assert result.success
    assert result.get('total_states') == 1  # Only one reachable state
    assert result.get('is_bounded')


def test_deadlock_detection():
    """Test detection of deadlock states."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    # Linear: P1→T1→P2 (deadlocks at P2)
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    deadlocks = result.get('deadlock_states', [])
    assert len(deadlocks) == 1  # Final state is deadlock


def test_no_deadlock():
    """Test net with no deadlock states."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    # Cycle with no deadlock
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p1')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    deadlocks = result.get('deadlock_states', [])
    assert len(deadlocks) == 0


def test_empty_model():
    """Test reachability on empty model."""
    model = Mock()
    model.places = []
    model.transitions = []
    model.arcs = []
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('total_states') == 0
    assert result.get('is_bounded')


def test_max_states_limit():
    """Test that max_states limit is respected."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 10)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    # Can generate many states
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze(max_states=5)
    
    assert result.success
    assert result.get('total_states') <= 5


def test_max_depth_limit():
    """Test that max_depth limit is respected."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 10)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze(max_depth=3)
    
    assert result.success
    assert result.get('max_depth_reached') <= 3


def test_graph_computation():
    """Test reachability graph computation."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze(compute_graph=True)
    
    assert result.success
    graph = result.get('reachability_graph')
    assert graph is not None
    assert 'nodes' in graph
    assert 'edges' in graph
    assert len(graph['nodes']) == 2
    assert len(graph['edges']) >= 1


def test_graph_computation_disabled():
    """Test that graph is not computed when disabled."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p1')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze(compute_graph=False)
    
    assert result.success
    assert result.get('reachability_graph') is None


def test_initial_marking():
    """Test that initial marking is captured."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    p2 = create_mock_place('p2', 'P2', 3)
    
    model.places = [p1, p2]
    model.transitions = []
    model.arcs = []
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    # Initial marking uses total_states when no transitions
    assert result.get('total_states') == 1
    # Can also check the initial state exists
    states = result.get('states', [])
    if states:
        # Initial marking is the first state
        initial = states[0]
        # Check structure exists
        assert 'p1' in initial or 'marking' in initial


def test_weighted_arcs():
    """Test reachability with weighted arcs."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1', 3),  # Requires 3 tokens
        create_mock_arc('t1', 'p2', 2)   # Produces 2 tokens
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    # Should be able to fire at least once
    assert result.get('total_states') >= 1


def test_exploration_complete():
    """Test exploration_complete flag."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze(max_states=100, max_depth=100)
    
    assert result.success
    # Small net should complete exploration
    assert result.get('exploration_complete')


def test_get_reachability_statistics():
    """Test reachability statistics method."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.get_reachability_statistics()
    
    assert result.success
    assert 'total_states' in result.data
    assert 'total_transitions' in result.data
    assert 'deadlock_count' in result.data
    assert 'average_branching_factor' in result.data


def test_deadlock_detection_disabled():
    """Test analysis with deadlock detection disabled."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze(find_deadlocks=False)
    
    assert result.success
    deadlocks = result.get('deadlock_states', [])
    assert len(deadlocks) == 0  # Not computed


def test_error_handling():
    """Test error handling for invalid model."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 5)
    ]
    model.transitions = [
        create_mock_transition('t1', 'T1')
    ]
    # Simulate error during analysis
    model.arcs = Mock(side_effect=Exception("Test error"))
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze()
    
    assert not result.success
    assert len(result.errors) > 0


def test_metadata():
    """Test that metadata is properly populated."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p1')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze(max_states=100, max_depth=50)
    
    assert result.success
    assert 'analysis_time' in result.metadata
    assert result.metadata['max_states_limit'] == 100
    assert result.metadata['max_depth_limit'] == 50


def test_multiple_enabled_transitions():
    """Test exploration with multiple enabled transitions."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 2)
    p2 = create_mock_place('p2', 'P2', 0)
    p3 = create_mock_place('p3', 'P3', 0)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    
    model.places = [p1, p2, p3]
    model.transitions = [t1, t2]
    # Both transitions enabled initially
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2'),
        create_mock_arc('p1', 't2'),
        create_mock_arc('t2', 'p3')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    # Should explore multiple paths
    assert result.get('total_states') > 1


def test_performance_reasonable_size():
    """Test performance on reasonable size net."""
    model = Mock()
    
    # Create 5 places
    model.places = [
        create_mock_place(f'p{i}', f'P{i}', i % 3)
        for i in range(5)
    ]
    
    # Create 4 transitions
    model.transitions = [
        create_mock_transition(f't{i}', f'T{i}')
        for i in range(4)
    ]
    
    # Create arcs
    model.arcs = [
        create_mock_arc('p0', 't0'),
        create_mock_arc('t0', 'p1'),
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2'),
        create_mock_arc('p2', 't2'),
        create_mock_arc('t2', 'p3'),
        create_mock_arc('p3', 't3'),
        create_mock_arc('t3', 'p4')
    ]
    
    analyzer = ReachabilityAnalyzer(model)
    result = analyzer.analyze(max_states=50)
    
    assert result.success
    assert result.get('total_states') > 0
    # Should complete quickly


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
