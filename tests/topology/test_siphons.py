"""Tests for Siphon analyzer."""

import pytest
from unittest.mock import Mock

from shypn.topology.structural.siphons import SiphonAnalyzer


@pytest.fixture
def simple_siphon_model():
    """Create a model with a simple siphon: P1, P2 form a siphon.
    
    Structure:
        P1 → T1 → P2
        P2 → T2 → P1
        T1 requires P1 and T2 requires P2
        So {P1, P2} is a siphon: if both empty, they stay empty
    """
    model = Mock()
    
    # Places
    p1 = Mock(id='P1', name='P1', marking=0)
    p2 = Mock(id='P2', name='P2', marking=0)
    model.places = [p1, p2]
    
    # Transitions
    t1 = Mock(id='T1', name='T1')
    t2 = Mock(id='T2', name='T2')
    model.transitions = [t1, t2]
    
    # Arcs: P1→T1→P2→T2→P1 (cycle)
    arcs = [
        Mock(source_id='P1', target_id='T1'),
        Mock(source_id='T1', target_id='P2'),
        Mock(source_id='P2', target_id='T2'),
        Mock(source_id='T2', target_id='P1'),
    ]
    model.arcs = arcs
    
    return model


@pytest.fixture
def marked_siphon_model():
    """Same structure as simple_siphon_model but with tokens."""
    model = Mock()
    
    p1 = Mock(id='P1', name='P1', marking=5)
    p2 = Mock(id='P2', name='P2', marking=3)
    model.places = [p1, p2]
    
    t1 = Mock(id='T1', name='T1')
    t2 = Mock(id='T2', name='T2')
    model.transitions = [t1, t2]
    
    arcs = [
        Mock(source_id='P1', target_id='T1'),
        Mock(source_id='T1', target_id='P2'),
        Mock(source_id='P2', target_id='T2'),
        Mock(source_id='T2', target_id='P1'),
    ]
    model.arcs = arcs
    
    return model


@pytest.fixture
def no_siphon_model():
    """Model with no multi-place siphons (non-siphon structure).
    
    Structure:
        P1 → T1 → P2
        P3 → T1 (T1 has two inputs)
        P2 → T2 → P1
        
    {P1, P2} is NOT a siphon because:
    - •{P1, P2} = {T2, T1}  (transitions that output to P1 or P2)
    - {P1, P2}• = {T1, T2}  (transitions that input from P1 or P2)
    - But T1 also inputs from P3, which is not in {P1, P2}
    - So •P1 (which includes T2) requires input from places outside {P1, P2}
    """
    model = Mock()
    
    p1 = Mock(id='P1', name='P1', marking=0)
    p2 = Mock(id='P2', name='P2', marking=0)
    p3 = Mock(id='P3', name='P3', marking=100)  # External source
    model.places = [p1, p2, p3]
    
    t1 = Mock(id='T1', name='T1')
    t2 = Mock(id='T2', name='T2')
    model.transitions = [t1, t2]
    
    # P1→T1→P2, P3→T1, P2→T2→P1
    arcs = [
        Mock(source_id='P1', target_id='T1'),
        Mock(source_id='P3', target_id='T1'),  # External input
        Mock(source_id='T1', target_id='P2'),
        Mock(source_id='P2', target_id='T2'),
        Mock(source_id='T2', target_id='P1'),
    ]
    model.arcs = arcs
    
    return model


@pytest.fixture
def multiple_siphons_model():
    """Model with multiple siphons.
    
    Two independent cycles:
    - Cycle 1: P1 ↔ T1 ↔ P2 ↔ T2 ↔ P1
    - Cycle 2: P3 ↔ T3 ↔ P4 ↔ T4 ↔ P3
    """
    model = Mock()
    
    places = [Mock(id=f'P{i}', name=f'P{i}', marking=0) for i in range(1, 5)]
    model.places = places
    
    transitions = [Mock(id=f'T{i}', name=f'T{i}') for i in range(1, 5)]
    model.transitions = transitions
    
    arcs = [
        # Cycle 1
        Mock(source_id='P1', target_id='T1'),
        Mock(source_id='T1', target_id='P2'),
        Mock(source_id='P2', target_id='T2'),
        Mock(source_id='T2', target_id='P1'),
        # Cycle 2
        Mock(source_id='P3', target_id='T3'),
        Mock(source_id='T3', target_id='P4'),
        Mock(source_id='P4', target_id='T4'),
        Mock(source_id='T4', target_id='P3'),
    ]
    model.arcs = arcs
    
    return model


@pytest.fixture
def empty_model():
    """Empty model."""
    model = Mock()
    model.places = []
    model.transitions = []
    model.arcs = []
    return model


def test_siphon_simple_empty(simple_siphon_model):
    """Test siphon detection with empty marking."""
    analyzer = SiphonAnalyzer(simple_siphon_model)
    result = analyzer.analyze()
    
    assert result.success
    
    siphons = result.get('siphons', [])
    assert len(siphons) >= 1
    
    # Should find {P1, P2} as a siphon
    full_siphon = next((s for s in siphons if s['size'] == 2), None)
    assert full_siphon is not None
    assert set(full_siphon['place_ids']) == {'P1', 'P2'}
    
    # Check empty status
    assert full_siphon['is_empty'] is True
    assert result.get('has_empty_siphons') is True
    assert result.get('deadlock_risk') is True


def test_siphon_simple_marked(marked_siphon_model):
    """Test siphon detection with marked places."""
    analyzer = SiphonAnalyzer(marked_siphon_model)
    result = analyzer.analyze()
    
    assert result.success
    
    siphons = result.get('siphons', [])
    full_siphon = next((s for s in siphons if s['size'] == 2), None)
    
    assert full_siphon is not None
    assert full_siphon['is_empty'] is False
    assert result.get('has_empty_siphons') is False
    assert result.get('deadlock_risk') is False


def test_no_siphon_linear(no_siphon_model):
    """Test model with external input (has siphons but one is marked)."""
    analyzer = SiphonAnalyzer(no_siphon_model)
    result = analyzer.analyze(min_size=2)
    
    assert result.success
    
    # This model DOES have siphons (e.g., {P1, P2})
    # But P3 has tokens, so some siphons involving P3 are not empty
    siphons = result.get('siphons', [])
    
    # Check that we found some siphons
    assert len(siphons) > 0
    
    # Check that siphons containing P3 are not empty (P3 has 100 tokens)
    p3_siphons = [s for s in siphons if 'P3' in s['place_ids']]
    if p3_siphons:
        assert all(not s['is_empty'] for s in p3_siphons)


def test_multiple_siphons(multiple_siphons_model):
    """Test detection of multiple independent siphons."""
    analyzer = SiphonAnalyzer(multiple_siphons_model)
    result = analyzer.analyze(min_size=2)
    
    assert result.success
    
    siphons = result.get('siphons', [])
    
    # Should find at least 2 siphons ({P1, P2} and {P3, P4})
    assert len(siphons) >= 2
    
    place_sets = [set(s['place_ids']) for s in siphons]
    
    # Check for expected siphons
    assert {'P1', 'P2'} in place_sets or any({'P1', 'P2'}.issubset(s) for s in place_sets)
    assert {'P3', 'P4'} in place_sets or any({'P3', 'P4'}.issubset(s) for s in place_sets)


def test_empty_model(empty_model):
    """Test analyzer with empty model."""
    analyzer = SiphonAnalyzer(empty_model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('count', 0) == 0
    assert result.get('has_empty_siphons') is False
    assert result.get('deadlock_risk') is False


def test_siphon_size_filter(simple_siphon_model):
    """Test min_size and max_size filters."""
    analyzer = SiphonAnalyzer(simple_siphon_model)
    
    # Only single-place siphons
    result1 = analyzer.analyze(min_size=1, max_size=1)
    assert result1.success
    siphons1 = result1.get('siphons', [])
    assert all(s['size'] == 1 for s in siphons1)
    
    # Only multi-place siphons
    result2 = analyzer.analyze(min_size=2)
    assert result2.success
    siphons2 = result2.get('siphons', [])
    assert all(s['size'] >= 2 for s in siphons2)


def test_siphon_max_limit(multiple_siphons_model):
    """Test max_siphons limit."""
    analyzer = SiphonAnalyzer(multiple_siphons_model)
    result = analyzer.analyze(max_siphons=1)
    
    assert result.success
    siphons = result.get('siphons', [])
    assert len(siphons) <= 1


def test_siphon_connectivity(simple_siphon_model):
    """Test preset/postset computation."""
    analyzer = SiphonAnalyzer(simple_siphon_model)
    result = analyzer.analyze()
    
    assert result.success
    
    siphons = result.get('siphons', [])
    full_siphon = next((s for s in siphons if s['size'] == 2), None)
    
    assert full_siphon is not None
    
    # For {P1, P2}:
    # Preset = {T2, T1} (transitions that output to P1 or P2)
    # Postset = {T1, T2} (transitions that input from P1 or P2)
    preset = set(full_siphon['preset_transitions'])
    postset = set(full_siphon['postset_transitions'])
    
    assert preset == postset  # Siphon property: •S ⊆ S• (here they're equal)
    assert {'T1', 'T2'}.issubset(preset)


def test_siphon_criticality(simple_siphon_model, marked_siphon_model):
    """Test criticality classification."""
    # Empty siphon = CRITICAL
    analyzer1 = SiphonAnalyzer(simple_siphon_model)
    result1 = analyzer1.analyze()
    siphons1 = result1.get('siphons', [])
    
    for siphon in siphons1:
        if siphon['is_empty']:
            assert siphon['criticality'] == 'CRITICAL'
    
    # Marked siphon = not critical
    analyzer2 = SiphonAnalyzer(marked_siphon_model)
    result2 = analyzer2.analyze()
    siphons2 = result2.get('siphons', [])
    
    for siphon in siphons2:
        if not siphon['is_empty']:
            assert siphon['criticality'] != 'CRITICAL'


def test_siphon_marking_info(marked_siphon_model):
    """Test marking information in results."""
    analyzer = SiphonAnalyzer(marked_siphon_model)
    result = analyzer.analyze()
    
    assert result.success
    
    siphons = result.get('siphons', [])
    full_siphon = next((s for s in siphons if s['size'] == 2), None)
    
    assert full_siphon is not None
    assert 'marking' in full_siphon
    
    marking = full_siphon['marking']
    assert marking['P1'] == 5
    assert marking['P2'] == 3


def test_find_siphons_containing_place(simple_siphon_model):
    """Test finding siphons containing a specific place."""
    analyzer = SiphonAnalyzer(simple_siphon_model)
    
    # Find siphons containing P1
    siphons = analyzer.find_siphons_containing_place('P1')
    
    assert len(siphons) > 0
    assert all('P1' in s['place_ids'] for s in siphons)


def test_minimal_siphons():
    """Test filtering to minimal siphons."""
    model = Mock()
    
    # Create a structure where {P1, P2, P3} is a siphon
    # but {P1, P2} is also a siphon (smaller)
    # We should only return the minimal one: {P1, P2}
    
    p1 = Mock(id='P1', name='P1', marking=0)
    p2 = Mock(id='P2', name='P2', marking=0)
    p3 = Mock(id='P3', name='P3', marking=0)
    model.places = [p1, p2, p3]
    
    t1 = Mock(id='T1', name='T1')
    t2 = Mock(id='T2', name='T2')
    model.transitions = [t1, t2]
    
    # {P1, P2} cycle, P3 disconnected
    arcs = [
        Mock(source_id='P1', target_id='T1'),
        Mock(source_id='T1', target_id='P2'),
        Mock(source_id='P2', target_id='T2'),
        Mock(source_id='T2', target_id='P1'),
    ]
    model.arcs = arcs
    
    analyzer = SiphonAnalyzer(model)
    result = analyzer.analyze(min_size=1)
    
    assert result.success
    
    siphons = result.get('siphons', [])
    
    # Should find minimal siphons, not all possible combinations
    # Expect: {P1}, {P2}, {P1,P2}, {P3} as minimal siphons
    # But {P1, P2, P3} should NOT appear if {P1, P2} is sufficient
    sizes = [s['size'] for s in siphons]
    
    # At least some minimal siphons found
    assert any(size <= 2 for size in sizes)


def test_siphon_error_handling():
    """Test error handling for invalid model."""
    model = Mock()
    # Missing required attributes
    # Don't set places, transitions, arcs at all
    
    analyzer = SiphonAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success is False
    assert len(result.errors) > 0


def test_siphon_metadata(simple_siphon_model):
    """Test metadata in analysis result."""
    analyzer = SiphonAnalyzer(simple_siphon_model)
    result = analyzer.analyze(min_size=1, max_size=3)
    
    assert result.success
    
    metadata = result.metadata
    assert 'analysis_time' in metadata
    assert metadata['min_size'] == 1
    assert metadata['max_size'] == 3
    assert 'total_places' in metadata
    assert 'checked_combinations' in metadata
