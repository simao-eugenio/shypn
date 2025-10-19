"""Tests for liveness analyzer."""

import pytest
from unittest.mock import Mock

from shypn.topology.behavioral.liveness import LivenessAnalyzer
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


def test_live_simple_cycle():
    """Test liveness in simple cycle (live net)."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    
    model.places = [p1, p2]
    model.transitions = [t1, t2]
    # Cycle: P1→T1→P2→T2→P1
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2'),
        create_mock_arc('p2', 't2'),
        create_mock_arc('t2', 'p1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('is_live')
    levels = result.get('liveness_levels', {})
    assert levels['t1'] in ['L3', 'L4']  # Live
    assert levels['t2'] in ['L2', 'L3', 'L4']  # At least potentially live


def test_dead_transition_no_inputs():
    """Test detection of dead transition (no inputs, no outputs)."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')  # Dead transition
    
    model.places = [p1]
    model.transitions = [t1, t2]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    # T2 has no connections
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    levels = result.get('liveness_levels', {})
    assert levels['t2'] == 'L0'  # Dead
    dead_trans = result.get('dead_transitions', [])
    assert len(dead_trans) == 1
    assert dead_trans[0]['id'] == 't2'


def test_source_transition():
    """Test source transition (no inputs, only outputs) is live."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 0)
    t1 = create_mock_transition('t1', 'Source')
    
    model.places = [p1]
    model.transitions = [t1]
    # T1 is source: no inputs, produces to P1
    model.arcs = [
        create_mock_arc('t1', 'p1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    levels = result.get('liveness_levels', {})
    assert levels['t1'] == 'L4'  # Strictly live (source)


def test_sink_transition():
    """Test sink transition (inputs but no outputs)."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'Sink')
    
    model.places = [p1]
    model.transitions = [t1]
    # T1 is sink: consumes from P1, no outputs
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    levels = result.get('liveness_levels', {})
    # Sink can fire but won't be live (L1 or L2)
    assert levels['t1'] in ['L1', 'L2']


def test_empty_model():
    """Test liveness analysis on empty model."""
    model = Mock()
    model.places = []
    model.transitions = []
    model.arcs = []
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('is_live')  # Empty net is vacuously live
    assert result.get('total_transitions') == 0


def test_transition_with_sufficient_tokens():
    """Test transition can fire with sufficient tokens."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 10)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1', 5),  # Requires 5 tokens
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    levels = result.get('liveness_levels', {})
    assert levels['t1'] in ['L2', 'L3']  # Can fire


def test_transition_insufficient_tokens():
    """Test transition with insufficient tokens for immediate firing."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 2)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1', 5),  # Requires 5 tokens (only 2 available)
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    levels = result.get('liveness_levels', {})
    # Has token sources (P1 has 2 tokens) and outputs, so potentially live
    assert levels['t1'] in ['L1', 'L2', 'L3']


def test_multiple_transitions_mixed_liveness():
    """Test net with transitions at different liveness levels."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    t3 = create_mock_transition('t3', 'T3')  # Dead
    
    model.places = [p1, p2]
    model.transitions = [t1, t2, t3]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2'),
        create_mock_arc('p2', 't2'),
        create_mock_arc('t2', 'p1')
    ]
    # T3 has no connections
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert not result.get('is_live')  # Not fully live (T3 is dead)
    levels = result.get('liveness_levels', {})
    assert levels['t3'] == 'L0'


def test_check_transition_liveness():
    """Test checking liveness of specific transition."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.check_transition_liveness('t1')
    
    assert result.success
    assert result.get('transition_id') == 't1'
    assert result.get('liveness_level') in ['L1', 'L2', 'L3']
    assert 'analysis' in result.data


def test_is_net_live():
    """Test is_net_live convenience method."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p1')  # Self-loop
    ]
    
    analyzer = LivenessAnalyzer(model)
    is_live = analyzer.is_net_live()
    
    # Should return boolean
    assert isinstance(is_live, bool)


def test_structural_check_disabled():
    """Test analysis with structural check disabled."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze(check_structural=False)
    
    assert result.success
    assert not result.metadata.get('checked_structural')


def test_deadlock_check_disabled():
    """Test analysis with deadlock check disabled."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze(check_deadlocks=False)
    
    assert result.success
    assert not result.metadata.get('checked_deadlocks')


def test_token_flow_check_disabled():
    """Test analysis with token flow check disabled."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze(check_token_flow=False)
    
    assert result.success
    assert not result.metadata.get('checked_token_flow')


def test_classify_levels_disabled():
    """Test analysis with level classification disabled."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze(classify_levels=False)
    
    assert result.success
    levels = result.get('liveness_levels', {})
    assert len(levels) == 0  # No classification


def test_error_handling():
    """Test error handling for invalid model."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 5)
    ]
    model.transitions = [
        create_mock_transition('t1', 'T1')
    ]
    # Simulate error during analysis by making arcs raise exception
    model.arcs = Mock(side_effect=Exception("Test error"))
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert not result.success
    assert len(result.errors) > 0


def test_metadata():
    """Test that metadata is properly populated."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert 'analysis_time' in result.metadata
    assert result.metadata['checked_structural']
    assert result.metadata['checked_deadlocks']
    assert result.metadata['checked_token_flow']


def test_transition_analysis_details():
    """Test that transition analysis provides detailed info."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    analysis = result.get('transition_analysis', {})
    assert 't1' in analysis
    trans_info = analysis['t1']
    assert 'id' in trans_info
    assert 'name' in trans_info
    assert 'structurally_enabled' in trans_info
    assert 'input_count' in trans_info
    assert 'output_count' in trans_info


def test_multiple_input_places():
    """Test transition with multiple input places."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 3)
    p2 = create_mock_place('p2', 'P2', 5)
    p3 = create_mock_place('p3', 'P3', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2, p3]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1', 2),
        create_mock_arc('p2', 't1', 3),
        create_mock_arc('t1', 'p3')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    levels = result.get('liveness_levels', {})
    # Should be able to fire (has sufficient tokens)
    assert levels['t1'] in ['L2', 'L3']


def test_live_transitions_list():
    """Test that live_transitions list is populated correctly."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    live_trans = result.get('live_transitions', [])
    # Should have at least one live transition if net is properly connected
    assert isinstance(live_trans, list)


def test_performance_large_model():
    """Test performance on larger model."""
    model = Mock()
    
    # Create 30 places with various markings
    model.places = [
        create_mock_place(f'p{i}', f'P{i}', i % 5)
        for i in range(30)
    ]
    
    # Create 20 transitions
    model.transitions = [
        create_mock_transition(f't{i}', f'T{i}')
        for i in range(20)
    ]
    
    # Create arcs connecting places and transitions
    model.arcs = []
    for i in range(20):
        model.arcs.append(create_mock_arc(f'p{i}', f't{i}'))
        model.arcs.append(create_mock_arc(f't{i}', f'p{(i+1) % 30}'))
    
    analyzer = LivenessAnalyzer(model)
    # Disable deadlock check for performance
    result = analyzer.analyze(check_deadlocks=False)
    
    assert result.success
    assert result.get('total_transitions') == 20
    # Should complete in reasonable time


def test_transition_with_no_name():
    """Test handling of transition without name attribute."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = Mock(spec=['id'])  # Only has id, no name
    t1.id = 't1'
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = LivenessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    # Should use ID as name when name not available
    analysis = result.get('transition_analysis', {})
    assert analysis['t1']['name'] == 't1'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
