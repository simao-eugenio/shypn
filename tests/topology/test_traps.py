"""Tests for Trap analyzer."""

import pytest
from unittest.mock import Mock

from shypn.topology.structural.traps import TrapAnalyzer


@pytest.fixture
def simple_trap_model():
    """Create a model with a simple trap: {P1, P2} form a trap.
    
    Structure:
        P1 → T1 → P2
        P2 → T2 → P1
        T1 requires P1 and T2 requires P2
        So {P1, P2} is a trap: if either has tokens, they always will
    """
    model = Mock()
    
    # Places
    p1 = Mock(id='P1', name='P1', marking=5)
    p2 = Mock(id='P2', name='P2', marking=3)
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
def empty_trap_model():
    """Same structure as simple_trap_model but with no tokens."""
    model = Mock()
    
    p1 = Mock(id='P1', name='P1', marking=0)
    p2 = Mock(id='P2', name='P2', marking=0)
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
def accumulation_model():
    """Model with trap that has many tokens (accumulation risk).
    
    Structure: Same cycle but with high token count
    """
    model = Mock()
    
    p1 = Mock(id='P1', name='P1', marking=150)
    p2 = Mock(id='P2', name='P2', marking=200)
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
def multiple_traps_model():
    """Model with multiple independent traps.
    
    Two independent cycles:
    - Cycle 1: P1 ↔ T1 ↔ P2 ↔ T2 ↔ P1
    - Cycle 2: P3 ↔ T3 ↔ P4 ↔ T4 ↔ P3
    """
    model = Mock()
    
    places = [Mock(id=f'P{i}', name=f'P{i}', marking=i*2) for i in range(1, 5)]
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


def test_trap_simple_marked(simple_trap_model):
    """Test trap detection with marked places."""
    analyzer = TrapAnalyzer(simple_trap_model)
    result = analyzer.analyze()
    
    assert result.success
    
    traps = result.get('traps', [])
    assert len(traps) >= 1
    
    # Should find {P1, P2} as a trap
    full_trap = next((t for t in traps if t['size'] == 2), None)
    assert full_trap is not None
    assert set(full_trap['place_ids']) == {'P1', 'P2'}
    
    # Check marked status
    assert full_trap['is_marked'] is True
    assert result.get('has_marked_traps') is True
    assert result.get('accumulation_risk') is True


def test_trap_simple_empty(empty_trap_model):
    """Test trap detection with empty places."""
    analyzer = TrapAnalyzer(empty_trap_model)
    result = analyzer.analyze()
    
    assert result.success
    
    traps = result.get('traps', [])
    full_trap = next((t for t in traps if t['size'] == 2), None)
    
    assert full_trap is not None
    assert full_trap['is_marked'] is False
    assert result.get('has_marked_traps') is False
    assert result.get('accumulation_risk') is False


def test_trap_accumulation_risk(accumulation_model):
    """Test trap with high token count (accumulation risk)."""
    analyzer = TrapAnalyzer(accumulation_model)
    result = analyzer.analyze()
    
    assert result.success
    
    traps = result.get('traps', [])
    full_trap = next((t for t in traps if t['size'] == 2), None)
    
    assert full_trap is not None
    assert full_trap['is_marked'] is True
    assert full_trap['total_tokens'] == 350
    assert full_trap['risk_level'] in ['HIGH', 'medium']


def test_multiple_traps(multiple_traps_model):
    """Test detection of multiple independent traps."""
    analyzer = TrapAnalyzer(multiple_traps_model)
    result = analyzer.analyze(min_size=2)
    
    assert result.success
    
    traps = result.get('traps', [])
    
    # Should find at least 2 traps ({P1, P2} and {P3, P4})
    assert len(traps) >= 2
    
    place_sets = [set(t['place_ids']) for t in traps]
    
    # Check for expected traps
    assert {'P1', 'P2'} in place_sets or any({'P1', 'P2'}.issubset(t) for t in place_sets)
    assert {'P3', 'P4'} in place_sets or any({'P3', 'P4'}.issubset(t) for t in place_sets)


def test_empty_model(empty_model):
    """Test analyzer with empty model."""
    analyzer = TrapAnalyzer(empty_model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('count', 0) == 0
    assert result.get('has_marked_traps') is False
    assert result.get('accumulation_risk') is False


def test_trap_size_filter(simple_trap_model):
    """Test min_size and max_size filters."""
    analyzer = TrapAnalyzer(simple_trap_model)
    
    # Only single-place traps
    result1 = analyzer.analyze(min_size=1, max_size=1)
    assert result1.success
    traps1 = result1.get('traps', [])
    assert all(t['size'] == 1 for t in traps1)
    
    # Only multi-place traps
    result2 = analyzer.analyze(min_size=2)
    assert result2.success
    traps2 = result2.get('traps', [])
    assert all(t['size'] >= 2 for t in traps2)


def test_trap_max_limit(multiple_traps_model):
    """Test max_traps limit."""
    analyzer = TrapAnalyzer(multiple_traps_model)
    result = analyzer.analyze(max_traps=1)
    
    assert result.success
    traps = result.get('traps', [])
    assert len(traps) <= 1


def test_trap_connectivity(simple_trap_model):
    """Test preset/postset computation."""
    analyzer = TrapAnalyzer(simple_trap_model)
    result = analyzer.analyze()
    
    assert result.success
    
    traps = result.get('traps', [])
    full_trap = next((t for t in traps if t['size'] == 2), None)
    
    assert full_trap is not None
    
    # For {P1, P2}:
    # Postset = {T1, T2} (transitions that input from P1 or P2)
    # Preset = {T2, T1} (transitions that output to P1 or P2)
    postset = set(full_trap['postset_transitions'])
    preset = set(full_trap['preset_transitions'])
    
    assert postset == preset  # Trap property: S• ⊆ •S (here they're equal)
    assert {'T1', 'T2'}.issubset(postset)


def test_trap_risk_classification(simple_trap_model, empty_trap_model, accumulation_model):
    """Test risk level classification."""
    # Marked trap = risk present
    analyzer1 = TrapAnalyzer(simple_trap_model)
    result1 = analyzer1.analyze()
    traps1 = result1.get('traps', [])
    
    for trap in traps1:
        if trap['is_marked']:
            assert trap['risk_level'] in ['low', 'medium', 'HIGH']
    
    # Empty trap = no risk
    analyzer2 = TrapAnalyzer(empty_trap_model)
    result2 = analyzer2.analyze()
    traps2 = result2.get('traps', [])
    
    for trap in traps2:
        if not trap['is_marked']:
            assert trap['risk_level'] == 'none'
    
    # High token count = HIGH risk
    analyzer3 = TrapAnalyzer(accumulation_model)
    result3 = analyzer3.analyze()
    traps3 = result3.get('traps', [])
    
    for trap in traps3:
        if trap['total_tokens'] > 100:
            assert trap['risk_level'] == 'HIGH'


def test_trap_marking_info(simple_trap_model):
    """Test marking information in results."""
    analyzer = TrapAnalyzer(simple_trap_model)
    result = analyzer.analyze()
    
    assert result.success
    
    traps = result.get('traps', [])
    full_trap = next((t for t in traps if t['size'] == 2), None)
    
    assert full_trap is not None
    assert 'marking' in full_trap
    
    marking = full_trap['marking']
    assert marking['P1'] == 5
    assert marking['P2'] == 3
    assert full_trap['total_tokens'] == 8


def test_find_traps_containing_place(simple_trap_model):
    """Test finding traps containing a specific place."""
    analyzer = TrapAnalyzer(simple_trap_model)
    
    # Find traps containing P1
    traps = analyzer.find_traps_containing_place('P1')
    
    assert len(traps) > 0
    assert all('P1' in t['place_ids'] for t in traps)


def test_minimal_traps():
    """Test filtering to minimal traps."""
    model = Mock()
    
    # Create a structure where {P1, P2, P3} is a trap
    # but {P1, P2} is also a trap (smaller)
    # We should only return the minimal one: {P1, P2}
    
    p1 = Mock(id='P1', name='P1', marking=1)
    p2 = Mock(id='P2', name='P2', marking=1)
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
    
    analyzer = TrapAnalyzer(model)
    result = analyzer.analyze(min_size=1)
    
    assert result.success
    
    traps = result.get('traps', [])
    
    # Should find minimal traps
    sizes = [t['size'] for t in traps]
    
    # At least some minimal traps found
    assert any(size <= 2 for size in sizes)


def test_trap_error_handling():
    """Test error handling for invalid model."""
    model = Mock()
    # Missing required attributes
    
    analyzer = TrapAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success is False
    assert len(result.errors) > 0


def test_trap_metadata(simple_trap_model):
    """Test metadata in analysis result."""
    analyzer = TrapAnalyzer(simple_trap_model)
    result = analyzer.analyze(min_size=1, max_size=3)
    
    assert result.success
    
    metadata = result.metadata
    assert 'analysis_time' in metadata
    assert metadata['min_size'] == 1
    assert metadata['max_size'] == 3
    assert 'total_places' in metadata
    assert 'checked_combinations' in metadata


def test_trap_vs_siphon_duality():
    """Test that traps and siphons are dual concepts.
    
    In a symmetric cycle, the same set should be both a trap and a siphon.
    """
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
    
    # Analyze as trap
    trap_analyzer = TrapAnalyzer(model)
    trap_result = trap_analyzer.analyze()
    
    # Analyze as siphon
    from shypn.topology.structural.siphons import SiphonAnalyzer
    siphon_analyzer = SiphonAnalyzer(model)
    siphon_result = siphon_analyzer.analyze()
    
    # Both should find {P1, P2}
    trap_sets = [set(t['place_ids']) for t in trap_result.get('traps', [])]
    siphon_sets = [set(s['place_ids']) for s in siphon_result.get('siphons', [])]
    
    assert {'P1', 'P2'} in trap_sets
    assert {'P1', 'P2'} in siphon_sets


def test_large_trap():
    """Test trap with many places (performance check)."""
    model = Mock()
    
    # Create a large cycle: P1→T1→P2→T2→...→P10→T10→P1
    n = 10
    places = [Mock(id=f'P{i}', name=f'P{i}', marking=i) for i in range(1, n+1)]
    model.places = places
    
    transitions = [Mock(id=f'T{i}', name=f'T{i}') for i in range(1, n+1)]
    model.transitions = transitions
    
    arcs = []
    for i in range(1, n+1):
        next_i = (i % n) + 1
        arcs.append(Mock(source_id=f'P{i}', target_id=f'T{i}'))
        arcs.append(Mock(source_id=f'T{i}', target_id=f'P{next_i}'))
    model.arcs = arcs
    
    analyzer = TrapAnalyzer(model)
    result = analyzer.analyze(min_size=5)  # Only large traps
    
    assert result.success
    traps = result.get('traps', [])
    
    # Should find the full cycle as a trap
    large_traps = [t for t in traps if t['size'] >= 5]
    assert len(large_traps) > 0
