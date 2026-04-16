"""Tests for boundedness analyzer."""

import pytest
from unittest.mock import Mock

from shypn.topology.behavioral.boundedness import BoundednessAnalyzer
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


def test_bounded_safe_net():
    """Test detection of safe (1-bounded) net."""
    # Net where all places have ≤1 token
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 1),
        create_mock_place('p2', 'P2', 0),
        create_mock_place('p3', 'P3', 1)
    ]
    model.transitions = [
        create_mock_transition('t1', 'T1')
    ]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('is_bounded')
    assert result.get('is_safe')  # 1-bounded
    assert result.get('boundedness_level') == 1
    assert result.get('unbounded_places') == []
    assert not result.get('overflow_risk')


def test_bounded_k_bounded_net():
    """Test detection of k-bounded net (k > 1)."""
    # Net where max tokens per place is 5
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 5),
        create_mock_place('p2', 'P2', 3),
        create_mock_place('p3', 'P3', 2)
    ]
    model.transitions = [
        create_mock_transition('t1', 'T1')
    ]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('is_bounded')
    assert not result.get('is_safe')  # Not 1-bounded
    assert result.get('boundedness_level') == 5
    assert result.get('unbounded_places') == []


def test_unbounded_exceeds_max():
    """Test detection of unbounded place exceeding max_bound."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 150),  # Exceeds default max of 100
        create_mock_place('p2', 'P2', 50)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze(max_bound=100)
    
    assert result.success
    assert not result.get('is_bounded')
    assert result.get('boundedness_level') is None
    unbounded = result.get('unbounded_places', [])
    assert len(unbounded) == 1
    assert unbounded[0]['id'] == 'p1'
    assert 'exceeds max_bound' in unbounded[0]['reason']


def test_unbounded_source_place():
    """Test that isolated places are bounded by current marking."""
    model = Mock()
    p1 = create_mock_place('p1', 'Source', 10)
    p2 = create_mock_place('p2', 'P2', 5)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    # P1 is isolated (no input arcs, no output arcs)
    model.arcs = [
        create_mock_arc('p2', 't1')
    ]
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze(check_conservation=True)
    
    assert result.success
    # Isolated places are considered bounded by current marking
    assert result.get('is_bounded')
    assert result.get('boundedness_level') == 10


def test_empty_model():
    """Test boundedness analysis on empty model."""
    model = Mock()
    model.places = []
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('is_bounded')
    assert result.get('is_safe')
    assert result.get('boundedness_level') == 0
    assert result.get('unbounded_places') == []


def test_conservative_net():
    """Test detection of conservative net (requires P-invariants)."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 3),
        create_mock_place('p2', 'P2', 2)
    ]
    model.transitions = [
        create_mock_transition('t1', 'T1')
    ]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    analyzer = BoundednessAnalyzer(model)
    # Note: This will attempt to use PInvariantAnalyzer if available
    result = analyzer.analyze(check_conservation=True)
    
    assert result.success
    # Just check it runs, conservation check depends on P-invariant analyzer


def test_overflow_risk_detection():
    """Test detection of overflow risk."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 85),  # 85% of max_bound=100
        create_mock_place('p2', 'P2', 50)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze(max_bound=100)
    
    assert result.success
    assert result.get('overflow_risk')  # >80% threshold


def test_no_overflow_risk():
    """Test no overflow risk when markings are low."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 10),
        create_mock_place('p2', 'P2', 20)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze(max_bound=100)
    
    assert result.success
    assert not result.get('overflow_risk')


def test_place_bounds_mapping():
    """Test that place_bounds correctly maps place IDs to markings."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 5),
        create_mock_place('p2', 'P2', 10),
        create_mock_place('p3', 'P3', 0)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    bounds = result.get('place_bounds', {})
    assert bounds['p1'] == 5
    assert bounds['p2'] == 10
    assert bounds['p3'] == 0


def test_check_place_boundedness():
    """Test checking boundedness of specific place."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 5),
        create_mock_place('p2', 'P2', 10)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.check_place_boundedness('p1')
    
    assert result.success
    assert result.get('place_id') == 'p1'
    assert result.get('is_bounded')
    assert result.get('current_marking') == 5
    assert not result.get('is_unbounded')


def test_check_unbounded_place():
    """Test checking boundedness of place exceeding max_bound."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 150),  # Exceeds max
        create_mock_place('p2', 'P2', 10)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    # Use max_bound to detect unboundedness
    result = analyzer.analyze(max_bound=100)
    
    assert result.success
    assert not result.get('is_bounded')
    
    # Check specific place
    place_result = analyzer.check_place_boundedness('p1')
    assert place_result.success
    assert place_result.get('place_id') == 'p1'
    assert place_result.get('current_marking') == 150


def test_structural_check_disabled():
    """Test analysis with structural check disabled."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 5)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze(check_structural=False)
    
    assert result.success
    assert not result.metadata.get('checked_structural')


def test_conservation_check_disabled():
    """Test analysis with conservation check disabled."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 5)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze(check_conservation=False)
    
    assert result.success
    assert not result.metadata.get('checked_conservation')


def test_current_marking_check_disabled():
    """Test analysis with current marking check disabled."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 5)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze(check_current_marking=False)
    
    assert result.success
    bounds = result.get('place_bounds', {})
    assert len(bounds) == 0  # No bounds collected


def test_error_handling():
    """Test error handling for invalid model."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 5)
    ]
    model.transitions = []
    # Simulate error during analysis by making arcs raise exception
    model.arcs = Mock(side_effect=Exception("Test error"))
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze()
    
    assert not result.success
    assert len(result.errors) > 0


def test_metadata():
    """Test that metadata is properly populated."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 5)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert 'analysis_time' in result.metadata
    assert result.metadata['checked_conservation']
    assert result.metadata['checked_structural']


def test_source_and_sink_detection():
    """Test structural detection of sources and sinks."""
    model = Mock()
    p1 = create_mock_place('p1', 'Source', 5)
    p2 = create_mock_place('p2', 'Middle', 3)
    p3 = create_mock_place('p3', 'Sink', 2)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    
    model.places = [p1, p2, p3]
    model.transitions = [t1, t2]
    # P1→T1→P2→T2→P3 (P1 is source, P3 is sink)
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2'),
        create_mock_arc('p2', 't2'),
        create_mock_arc('t2', 'p3')
    ]
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    # Sources and sinks are detected but may not affect boundedness
    # if they have connections


def test_performance_large_model():
    """Test performance on larger model."""
    model = Mock()
    
    # Create 50 places with various markings
    model.places = [
        create_mock_place(f'p{i}', f'P{i}', i % 10)
        for i in range(50)
    ]
    
    # Create 30 transitions
    model.transitions = [
        create_mock_transition(f't{i}', f'T{i}')
        for i in range(30)
    ]
    
    # Create arcs connecting places and transitions
    model.arcs = [
        create_mock_arc(f'p{i}', f't{i % 30}')
        for i in range(50)
    ]
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('total_places') == 50
    # Should complete in reasonable time


def test_zero_marking_places():
    """Test net with all places having zero marking."""
    model = Mock()
    model.places = [
        create_mock_place('p1', 'P1', 0),
        create_mock_place('p2', 'P2', 0),
        create_mock_place('p3', 'P3', 0)
    ]
    model.transitions = []
    model.arcs = []
    
    analyzer = BoundednessAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('is_bounded')
    assert result.get('boundedness_level') == 0
    assert result.get('is_safe')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
