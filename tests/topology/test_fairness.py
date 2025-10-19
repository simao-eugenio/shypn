"""Tests for fairness analyzer."""

import pytest
from unittest.mock import Mock

from shypn.topology.behavioral.fairness import FairnessAnalyzer
from shypn.topology.base.exceptions import TopologyAnalysisError


def create_mock_place(place_id, name, marking=0):
    """Helper to create mock place."""
    place = Mock()
    place.id = place_id
    place.name = name
    place.marking = marking
    return place


def create_mock_transition(trans_id, name, priority=0):
    """Helper to create mock transition."""
    trans = Mock()
    trans.id = trans_id
    trans.name = name
    trans.priority = priority
    return trans


def create_mock_arc(source_id, target_id, weight=1):
    """Helper to create mock arc."""
    arc = Mock()
    arc.source_id = source_id
    arc.target_id = target_id
    arc.weight = weight
    return arc


def test_no_conflicts_strong_fairness():
    """Test net with no conflicts has strong fairness."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    p2 = create_mock_place('p2', 'P2', 3)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    
    model.places = [p1, p2]
    model.transitions = [t1, t2]
    # No conflicts: each transition has its own input place
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('p2', 't2')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('is_fair')
    assert result.get('fairness_level') == 'strong'
    assert len(result.get('conflicting_transitions', [])) == 0


def test_simple_conflict():
    """Test detection of simple conflict (two transitions sharing a place)."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    
    model.places = [p1]
    model.transitions = [t1, t2]
    # Both transitions consume from P1 (conflict)
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('p1', 't2')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    conflicts = result.get('conflicting_transitions', [])
    assert len(conflicts) == 1
    assert conflicts[0]['place_id'] == 'p1'
    assert set(conflicts[0]['transition_ids']) == {'t1', 't2'}
    assert conflicts[0]['conflict_size'] == 2


def test_large_conflict_high_starvation_risk():
    """Test large conflict set triggers high starvation risk."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 2)
    transitions = [create_mock_transition(f't{i}', f'T{i}') for i in range(6)]
    
    model.places = [p1]
    model.transitions = transitions
    # 6 transitions competing for same place
    model.arcs = [
        create_mock_arc('p1', f't{i}')
        for i in range(6)
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('fairness_level') == 'none'  # High starvation risk
    starvation = result.get('starvation_risk', [])
    assert len(starvation) == 6
    assert all(r['risk_level'] == 'high' for r in starvation)


def test_medium_conflict_weak_fairness():
    """Test medium conflict leads to weak fairness."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    t3 = create_mock_transition('t3', 'T3')
    
    model.places = [p1]
    model.transitions = [t1, t2, t3]
    # 3 transitions in conflict
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('p1', 't2'),
        create_mock_arc('p1', 't3')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('fairness_level') == 'weak'


def test_priority_conflicts():
    """Test detection of priority-based conflicts."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1', priority=10)
    t2 = create_mock_transition('t2', 'T2', priority=1)
    
    model.places = [p1]
    model.transitions = [t1, t2]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('p1', 't2')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    priority_conflicts = result.get('priority_conflicts', [])
    assert len(priority_conflicts) == 1
    assert priority_conflicts[0]['place_id'] == 'p1'


def test_limited_tokens_starvation_risk():
    """Test limited tokens with conflicts increases starvation risk."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)  # Only 1 token
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    t3 = create_mock_transition('t3', 'T3')
    
    model.places = [p1]
    model.transitions = [t1, t2, t3]
    # 3 transitions competing for 1 token
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('p1', 't2'),
        create_mock_arc('p1', 't3')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    starvation = result.get('starvation_risk', [])
    assert len(starvation) == 3
    assert all(r['risk_level'] == 'medium' for r in starvation)


def test_empty_model():
    """Test fairness analysis on empty model."""
    model = Mock()
    model.places = []
    model.transitions = []
    model.arcs = []
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('is_fair')
    assert result.get('fairness_level') == 'strong'
    assert result.get('total_transitions') == 0


def test_check_transition_fairness():
    """Test checking fairness of specific transition."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 2)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    
    model.places = [p1]
    model.transitions = [t1, t2]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('p1', 't2')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.check_transition_fairness('t1')
    
    assert result.success
    assert result.get('transition_id') == 't1'
    assert result.get('in_conflict')
    # Should be fair (enough tokens for both)
    assert result.get('is_fair')


def test_multiple_conflicts():
    """Test detection of multiple independent conflicts."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    p2 = create_mock_place('p2', 'P2', 3)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    t3 = create_mock_transition('t3', 'T3')
    t4 = create_mock_transition('t4', 'T4')
    
    model.places = [p1, p2]
    model.transitions = [t1, t2, t3, t4]
    # Two independent conflicts
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('p1', 't2'),
        create_mock_arc('p2', 't3'),
        create_mock_arc('p2', 't4')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    conflicts = result.get('conflicting_transitions', [])
    assert len(conflicts) == 2
    assert result.get('total_conflicts') == 2


def test_no_conflicts_with_arcs():
    """Test that output arcs don't create conflicts."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    
    model.places = [p1, p2]
    model.transitions = [t1, t2]
    # Both transitions produce to P2 (not a conflict)
    model.arcs = [
        create_mock_arc('t1', 'p2'),
        create_mock_arc('t2', 'p2')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    conflicts = result.get('conflicting_transitions', [])
    assert len(conflicts) == 0  # Output arcs don't create conflicts


def test_conflicts_check_disabled():
    """Test analysis with conflict check disabled."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    
    model.places = [p1]
    model.transitions = [t1, t2]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('p1', 't2')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze(check_conflicts=False)
    
    assert result.success
    assert not result.metadata.get('checked_conflicts')


def test_starvation_check_disabled():
    """Test analysis with starvation check disabled."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze(check_starvation=False)
    
    assert result.success
    assert not result.metadata.get('checked_starvation')


def test_priorities_check_disabled():
    """Test analysis with priority check disabled."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze(check_priorities=False)
    
    assert result.success
    assert not result.metadata.get('checked_priorities')


def test_classify_fairness_disabled():
    """Test analysis with fairness classification disabled."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze(classify_fairness=False)
    
    assert result.success
    # Should have default values when classification disabled
    assert 'fairness_level' in result.data


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
    
    analyzer = FairnessAnalyzer(model)
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
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert 'analysis_time' in result.metadata
    assert result.metadata['checked_conflicts']
    assert result.metadata['checked_starvation']
    assert result.metadata['checked_priorities']


def test_transition_without_priority():
    """Test handling of transitions without priority attribute."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 5)
    t1 = Mock(spec=['id', 'name'])  # No priority attribute
    t1.id = 't1'
    t1.name = 'T1'
    t2 = create_mock_transition('t2', 'T2', priority=5)
    
    model.places = [p1]
    model.transitions = [t1, t2]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('p1', 't2')
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    # Should handle missing priority gracefully


def test_fairness_violations_list():
    """Test that fairness violations are properly listed."""
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    transitions = [create_mock_transition(f't{i}', f'T{i}') for i in range(6)]
    
    model.places = [p1]
    model.transitions = transitions
    model.arcs = [
        create_mock_arc('p1', f't{i}')
        for i in range(6)
    ]
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    violations = result.get('fairness_violations', [])
    assert len(violations) > 0
    assert any('starvation' in str(v).lower() for v in violations)


def test_performance_large_model():
    """Test performance on larger model."""
    model = Mock()
    
    # Create 20 places
    model.places = [
        create_mock_place(f'p{i}', f'P{i}', i % 5)
        for i in range(20)
    ]
    
    # Create 30 transitions
    model.transitions = [
        create_mock_transition(f't{i}', f'T{i}')
        for i in range(30)
    ]
    
    # Create arcs (some conflicts)
    model.arcs = []
    for i in range(30):
        model.arcs.append(create_mock_arc(f'p{i % 20}', f't{i}'))
    
    analyzer = FairnessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('total_transitions') == 30
    # Should complete in reasonable time


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
