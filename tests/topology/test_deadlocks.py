"""Tests for Deadlock analyzer."""

import pytest
from unittest.mock import Mock

from shypn.topology.behavioral.deadlocks import DeadlockAnalyzer


@pytest.fixture
def deadlock_model():
    """Create a model in deadlock state (no tokens, cycle structure).
    
    Structure: P1→T1→P2→T2→P1 (cycle with no tokens)
    """
    model = Mock()
    
    p1 = Mock(id='P1', name='P1', marking=0)
    p2 = Mock(id='P2', name='P2', marking=0)
    model.places = [p1, p2]
    
    t1 = Mock(id='T1', name='T1')
    t2 = Mock(id='T2', name='T2')
    model.transitions = [t1, t2]
    
    arcs = [
        Mock(source_id='P1', target_id='T1', weight=1),
        Mock(source_id='T1', target_id='P2', weight=1),
        Mock(source_id='P2', target_id='T2', weight=1),
        Mock(source_id='T2', target_id='P1', weight=1),
    ]
    model.arcs = arcs
    
    return model


@pytest.fixture
def no_deadlock_model():
    """Create a model without deadlock (has tokens).
    
    Structure: P1→T1→P2→T2→P1 (cycle with tokens)
    """
    model = Mock()
    
    p1 = Mock(id='P1', name='P1', marking=5)
    p2 = Mock(id='P2', name='P2', marking=3)
    model.places = [p1, p2]
    
    t1 = Mock(id='T1', name='T1')
    t2 = Mock(id='T2', name='T2')
    model.transitions = [t1, t2]
    
    arcs = [
        Mock(source_id='P1', target_id='T1', weight=1),
        Mock(source_id='T1', target_id='P2', weight=1),
        Mock(source_id='P2', target_id='T2', weight=1),
        Mock(source_id='T2', target_id='P1', weight=1),
    ]
    model.arcs = arcs
    
    return model


@pytest.fixture
def partial_deadlock_model():
    """Create a model with some transitions disabled.
    
    Structure: Two transitions, only one can fire
    """
    model = Mock()
    
    p1 = Mock(id='P1', name='P1', marking=5)
    p2 = Mock(id='P2', name='P2', marking=0)
    p3 = Mock(id='P3', name='P3', marking=0)
    model.places = [p1, p2, p3]
    
    t1 = Mock(id='T1', name='T1')  # Can fire (P1 has tokens)
    t2 = Mock(id='T2', name='T2')  # Cannot fire (P2 has no tokens)
    model.transitions = [t1, t2]
    
    arcs = [
        Mock(source_id='P1', target_id='T1', weight=1),
        Mock(source_id='T1', target_id='P3', weight=1),
        Mock(source_id='P2', target_id='T2', weight=1),
        Mock(source_id='T2', target_id='P3', weight=1),
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


def test_deadlock_detected(deadlock_model):
    """Test detection of deadlock state."""
    analyzer = DeadlockAnalyzer(deadlock_model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('has_deadlock') is True
    assert result.get('deadlock_type') in ['structural', 'behavioral']
    assert result.get('severity') in ['critical', 'high']


def test_no_deadlock(no_deadlock_model):
    """Test model without deadlock."""
    analyzer = DeadlockAnalyzer(no_deadlock_model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('has_deadlock') is False
    assert result.get('deadlock_type') == 'none'
    assert result.get('severity') == 'none'


def test_partial_deadlock(partial_deadlock_model):
    """Test model with some transitions disabled."""
    analyzer = DeadlockAnalyzer(partial_deadlock_model)
    result = analyzer.analyze()
    
    assert result.success
    
    disabled = result.get('disabled_transitions', [])
    # T2 should be disabled (P2 has no tokens)
    assert len(disabled) > 0
    
    # But not all transitions disabled, so not full deadlock
    total_trans = result.get('total_transitions', 0)
    enabled_trans = result.get('enabled_transitions', 0)
    assert enabled_trans > 0
    assert enabled_trans < total_trans


def test_empty_model(empty_model):
    """Test empty model (considered deadlocked)."""
    analyzer = DeadlockAnalyzer(empty_model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('has_deadlock') is True
    assert result.get('deadlock_type') == 'structural'
    assert result.get('severity') == 'critical'


def test_structural_vs_behavioral():
    """Test distinction between structural and behavioral deadlocks."""
    # Structural: Empty siphon
    model1 = Mock()
    p1 = Mock(id='P1', name='P1', marking=0)
    p2 = Mock(id='P2', name='P2', marking=0)
    model1.places = [p1, p2]
    t1 = Mock(id='T1', name='T1')
    t2 = Mock(id='T2', name='T2')
    model1.transitions = [t1, t2]
    model1.arcs = [
        Mock(source_id='P1', target_id='T1', weight=1),
        Mock(source_id='T1', target_id='P2', weight=1),
        Mock(source_id='P2', target_id='T2', weight=1),
        Mock(source_id='T2', target_id='P1', weight=1),
    ]
    
    analyzer1 = DeadlockAnalyzer(model1)
    result1 = analyzer1.analyze(check_siphons=True)
    
    if result1.get('has_deadlock'):
        # If deadlock detected, should be structural due to empty siphon
        empty_siphons = result1.get('empty_siphons', [])
        if len(empty_siphons) > 0:
            assert result1.get('deadlock_type') == 'structural'


def test_disabled_transitions_detection(deadlock_model):
    """Test detection of disabled transitions."""
    analyzer = DeadlockAnalyzer(deadlock_model)
    result = analyzer.analyze(check_enablement=True)
    
    assert result.success
    
    disabled = result.get('disabled_transitions', [])
    # In deadlock model (no tokens), all transitions should be disabled
    assert len(disabled) == len(deadlock_model.transitions)
    
    # Each disabled transition should have info
    for trans in disabled:
        assert 'id' in trans
        assert 'name' in trans
        assert 'reason' in trans


def test_deadlock_places_identification(deadlock_model):
    """Test identification of places involved in deadlock."""
    analyzer = DeadlockAnalyzer(deadlock_model)
    result = analyzer.analyze()
    
    assert result.success
    
    deadlock_places = result.get('deadlock_places', [])
    assert len(deadlock_places) > 0
    
    # Each place should have info
    for place in deadlock_places:
        assert 'id' in place
        assert 'name' in place
        assert 'marking' in place


def test_severity_classification():
    """Test severity classification levels."""
    # Critical: All transitions disabled
    model1 = Mock()
    model1.places = [Mock(id='P1', name='P1', marking=0)]
    model1.transitions = [Mock(id='T1', name='T1')]
    model1.arcs = [Mock(source_id='P1', target_id='T1', weight=1)]
    
    analyzer1 = DeadlockAnalyzer(model1)
    result1 = analyzer1.analyze()
    
    if result1.get('has_deadlock'):
        assert result1.get('severity') in ['critical', 'high']


def test_recovery_suggestions(deadlock_model):
    """Test generation of recovery suggestions."""
    analyzer = DeadlockAnalyzer(deadlock_model)
    result = analyzer.analyze(suggest_recovery=True)
    
    assert result.success
    
    if result.get('has_deadlock'):
        suggestions = result.get('recovery_suggestions', [])
        assert len(suggestions) > 0
        
        # Suggestions should be strings
        assert all(isinstance(s, str) for s in suggestions)


def test_no_recovery_suggestions_when_disabled():
    """Test that recovery suggestions are empty when disabled."""
    model = Mock()
    model.places = [Mock(id='P1', name='P1', marking=0)]
    model.transitions = [Mock(id='T1', name='T1')]
    model.arcs = [Mock(source_id='P1', target_id='T1', weight=1)]
    
    analyzer = DeadlockAnalyzer(model)
    result = analyzer.analyze(suggest_recovery=False)
    
    assert result.success
    suggestions = result.get('recovery_suggestions', [])
    assert len(suggestions) == 0


def test_check_deadlock_freedom(no_deadlock_model):
    """Test deadlock freedom check."""
    analyzer = DeadlockAnalyzer(no_deadlock_model)
    result = analyzer.check_for_deadlock_freedom()
    
    assert result.success
    # Model with tokens should be potentially deadlock-free
    # (though it depends on structure and siphons)


def test_enablement_check_disabled():
    """Test analyzer with enablement check disabled."""
    model = Mock()
    model.places = [Mock(id='P1', name='P1', marking=0)]
    model.transitions = [Mock(id='T1', name='T1')]
    model.arcs = [Mock(source_id='P1', target_id='T1', weight=1)]
    
    analyzer = DeadlockAnalyzer(model)
    result = analyzer.analyze(check_enablement=False)
    
    assert result.success
    # Should still succeed even if enablement check is off


def test_siphon_check_disabled():
    """Test analyzer with siphon check disabled."""
    model = Mock()
    model.places = [Mock(id='P1', name='P1', marking=0)]
    model.transitions = [Mock(id='T1', name='T1')]
    model.arcs = [Mock(source_id='P1', target_id='T1', weight=1)]
    
    analyzer = DeadlockAnalyzer(model)
    result = analyzer.analyze(check_siphons=False)
    
    assert result.success
    empty_siphons = result.get('empty_siphons', [])
    assert len(empty_siphons) == 0  # Should be empty when check disabled


def test_error_handling():
    """Test error handling for invalid model."""
    model = Mock()
    # Missing required attributes
    
    analyzer = DeadlockAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success is False
    assert len(result.errors) > 0


def test_metadata(deadlock_model):
    """Test metadata in analysis result."""
    analyzer = DeadlockAnalyzer(deadlock_model)
    result = analyzer.analyze()
    
    assert result.success
    
    metadata = result.metadata
    assert 'analysis_time' in metadata
    assert 'checked_siphons' in metadata
    assert 'checked_enablement' in metadata


def test_transition_enablement_with_weights():
    """Test transition enablement with arc weights > 1."""
    model = Mock()
    
    p1 = Mock(id='P1', name='P1', marking=2)  # Only 2 tokens
    model.places = [p1]
    
    t1 = Mock(id='T1', name='T1')
    model.transitions = [t1]
    
    # T1 requires 3 tokens from P1
    arcs = [Mock(source_id='P1', target_id='T1', weight=3)]
    model.arcs = arcs
    
    analyzer = DeadlockAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    
    disabled = result.get('disabled_transitions', [])
    # T1 should be disabled (needs 3, has 2)
    assert len(disabled) == 1
    assert disabled[0]['id'] == 'T1'


def test_multiple_input_places():
    """Test transition with multiple input places."""
    model = Mock()
    
    p1 = Mock(id='P1', name='P1', marking=5)
    p2 = Mock(id='P2', name='P2', marking=0)  # P2 is empty
    model.places = [p1, p2]
    
    t1 = Mock(id='T1', name='T1')
    model.transitions = [t1]
    
    # T1 requires both P1 and P2
    arcs = [
        Mock(source_id='P1', target_id='T1', weight=1),
        Mock(source_id='P2', target_id='T1', weight=1),
    ]
    model.arcs = arcs
    
    analyzer = DeadlockAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    
    disabled = result.get('disabled_transitions', [])
    # T1 should be disabled (P2 is empty)
    assert len(disabled) == 1
    assert disabled[0]['id'] == 'T1'
    
    required = disabled[0].get('required_tokens', {})
    assert 'P2' in required


def test_performance_large_model():
    """Test analyzer performance with larger model."""
    model = Mock()
    
    # Create 20 places and 20 transitions
    n = 20
    places = [Mock(id=f'P{i}', name=f'P{i}', marking=i % 3) for i in range(n)]
    model.places = places
    
    transitions = [Mock(id=f'T{i}', name=f'T{i}') for i in range(n)]
    model.transitions = transitions
    
    # Create cycle
    arcs = []
    for i in range(n):
        next_i = (i + 1) % n
        arcs.append(Mock(source_id=f'P{i}', target_id=f'T{i}', weight=1))
        arcs.append(Mock(source_id=f'T{i}', target_id=f'P{next_i}', weight=1))
    model.arcs = arcs
    
    analyzer = DeadlockAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    
    # Check that analysis completed
    metadata = result.metadata
    assert 'analysis_time' in metadata
    assert metadata['analysis_time'] >= 0
