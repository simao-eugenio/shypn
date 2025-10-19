"""Tests for T-Invariant analyzer."""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock

from shypn.topology.structural.t_invariants import TInvariantAnalyzer
from shypn.topology.base.exceptions import TopologyAnalysisError


@pytest.fixture
def simple_cycle_model():
    """Create a simple cyclic model: P1→T1→P2→T2→P1"""
    model = Mock()
    
    # Places
    p1 = Mock(id='P1', name='P1')
    p2 = Mock(id='P2', name='P2')
    model.places = [p1, p2]
    
    # Transitions
    t1 = Mock(id='T1', name='T1')
    t2 = Mock(id='T2', name='T2')
    model.transitions = [t1, t2]
    
    # Arcs: P1→T1, T1→P2, P2→T2, T2→P1
    arc1 = Mock(source_id='P1', target_id='T1', weight=1)
    arc2 = Mock(source_id='T1', target_id='P2', weight=1)
    arc3 = Mock(source_id='P2', target_id='T2', weight=1)
    arc4 = Mock(source_id='T2', target_id='P1', weight=1)
    model.arcs = [arc1, arc2, arc3, arc4]
    
    return model


@pytest.fixture
def complex_cycle_model():
    """Create model with multiple cycles."""
    model = Mock()
    
    # Places
    places = [Mock(id=f'P{i}', name=f'P{i}') for i in range(1, 6)]
    model.places = places
    
    # Transitions
    transitions = [Mock(id=f'T{i}', name=f'T{i}') for i in range(1, 6)]
    model.transitions = transitions
    
    # Create two overlapping cycles
    # Cycle 1: P1→T1→P2→T2→P1
    # Cycle 2: P2→T3→P3→T4→P2
    # Plus: T5 connects P3→P4→P5 (linear path)
    arcs = [
        Mock(source_id='P1', target_id='T1', weight=1),
        Mock(source_id='T1', target_id='P2', weight=1),
        Mock(source_id='P2', target_id='T2', weight=1),
        Mock(source_id='T2', target_id='P1', weight=1),
        Mock(source_id='P2', target_id='T3', weight=1),
        Mock(source_id='T3', target_id='P3', weight=1),
        Mock(source_id='P3', target_id='T4', weight=1),
        Mock(source_id='T4', target_id='P2', weight=1),
        Mock(source_id='P3', target_id='T5', weight=1),
        Mock(source_id='T5', target_id='P4', weight=1),
    ]
    model.arcs = arcs
    
    return model


@pytest.fixture
def dag_model():
    """Create a DAG (no cycles): P1→T1→P2→T2→P3"""
    model = Mock()
    
    # Places
    p1 = Mock(id='P1', name='P1')
    p2 = Mock(id='P2', name='P2')
    p3 = Mock(id='P3', name='P3')
    model.places = [p1, p2, p3]
    
    # Transitions
    t1 = Mock(id='T1', name='T1')
    t2 = Mock(id='T2', name='T2')
    model.transitions = [t1, t2]
    
    # Arcs: P1→T1→P2→T2→P3 (linear)
    arc1 = Mock(source_id='P1', target_id='T1', weight=1)
    arc2 = Mock(source_id='T1', target_id='P2', weight=1)
    arc3 = Mock(source_id='P2', target_id='T2', weight=1)
    arc4 = Mock(source_id='T2', target_id='P3', weight=1)
    model.arcs = [arc1, arc2, arc3, arc4]
    
    return model


@pytest.fixture
def empty_model():
    """Create an empty model with no transitions."""
    model = Mock()
    model.places = []
    model.transitions = []
    model.arcs = []
    return model


def test_t_invariant_simple_cycle(simple_cycle_model):
    """Test T-invariant detection on simple cycle."""
    analyzer = TInvariantAnalyzer(simple_cycle_model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('count', 0) > 0
    
    invariants = result.get('t_invariants', [])
    assert len(invariants) > 0
    
    # Check first invariant
    inv = invariants[0]
    assert 'transition_ids' in inv
    assert 'transition_names' in inv
    assert 'weights' in inv
    assert 'firing_sequence' in inv
    assert 'type' in inv
    
    # Simple cycle should have both transitions
    assert len(inv['transition_ids']) == 2
    assert set(inv['transition_ids']) == {'T1', 'T2'}


def test_t_invariant_complex_cycles(complex_cycle_model):
    """Test T-invariant detection with multiple cycles."""
    analyzer = TInvariantAnalyzer(complex_cycle_model)
    result = analyzer.analyze(max_invariants=10)
    
    assert result.success
    
    invariants = result.get('t_invariants', [])
    # Should find at least 2 cycles
    assert len(invariants) >= 2
    
    # Check that invariants have correct structure
    for inv in invariants:
        assert len(inv['transition_ids']) >= 2
        assert inv['size'] >= 2
        assert len(inv['weights']) == len(inv['transition_ids'])


def test_t_invariant_dag(dag_model):
    """Test T-invariant on DAG (should find none)."""
    analyzer = TInvariantAnalyzer(dag_model)
    result = analyzer.analyze()
    
    assert result.success
    
    # DAG has no cycles, so no T-invariants
    invariants = result.get('t_invariants', [])
    assert len(invariants) == 0
    
    # Should have warning about no invariants
    assert len(result.warnings) > 0
    assert 'DAG' in result.summary or 'No T-invariants' in result.summary


def test_t_invariant_empty_model(empty_model):
    """Test T-invariant on empty model."""
    analyzer = TInvariantAnalyzer(empty_model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('count', 0) == 0
    assert 'No transitions' in result.summary


def test_t_invariant_min_support(simple_cycle_model):
    """Test min_support parameter."""
    analyzer = TInvariantAnalyzer(simple_cycle_model)
    
    # Should find invariants with at least 2 transitions
    result = analyzer.analyze(min_support=2)
    assert result.success
    
    invariants = result.get('t_invariants', [])
    for inv in invariants:
        assert inv['size'] >= 2


def test_t_invariant_max_invariants(complex_cycle_model):
    """Test max_invariants parameter."""
    analyzer = TInvariantAnalyzer(complex_cycle_model)
    
    # Limit to 1 invariant
    result = analyzer.analyze(max_invariants=1)
    assert result.success
    
    invariants = result.get('t_invariants', [])
    assert len(invariants) <= 1
    
    # Check if truncated
    if result.get('truncated', False):
        assert 'truncated' in result.summary.lower()


def test_t_invariant_normalization(simple_cycle_model):
    """Test invariant normalization."""
    analyzer = TInvariantAnalyzer(simple_cycle_model)
    
    # With normalization
    result = analyzer.analyze(normalize=True)
    assert result.success
    
    invariants = result.get('t_invariants', [])
    if len(invariants) > 0:
        # Weights should be smallest positive integers
        for inv in invariants:
            weights = inv['weights']
            gcd = np.gcd.reduce(weights)
            assert gcd == 1  # Should be normalized


def test_t_invariant_classification(simple_cycle_model):
    """Test invariant type classification."""
    analyzer = TInvariantAnalyzer(simple_cycle_model)
    result = analyzer.analyze(classify=True)
    
    assert result.success
    
    invariants = result.get('t_invariants', [])
    if len(invariants) > 0:
        inv = invariants[0]
        assert 'type' in inv
        # Simple 2-transition cycle should be classified
        assert inv['type'] in ['simple-cycle', 'small-cycle']


def test_t_invariant_coverage(complex_cycle_model):
    """Test transition coverage statistics."""
    analyzer = TInvariantAnalyzer(complex_cycle_model)
    result = analyzer.analyze()
    
    assert result.success
    
    # Should have coverage statistics
    assert 'covered_transitions' in result.data
    assert 'coverage_ratio' in result.data
    
    covered = result.get('covered_transitions', 0)
    ratio = result.get('coverage_ratio', 0)
    
    assert covered >= 0
    assert 0 <= ratio <= 1


def test_find_invariants_containing_transition(simple_cycle_model):
    """Test finding invariants containing specific transition."""
    analyzer = TInvariantAnalyzer(simple_cycle_model)
    result = analyzer.find_invariants_containing_transition('T1', max_invariants=5)
    
    assert result.success
    
    invariants = result.get('t_invariants', [])
    # All returned invariants should contain T1
    for inv in invariants:
        assert 'T1' in inv['transition_ids']


def test_find_invariants_nonexistent_transition(simple_cycle_model):
    """Test finding invariants for non-existent transition."""
    analyzer = TInvariantAnalyzer(simple_cycle_model)
    result = analyzer.find_invariants_containing_transition('T999', max_invariants=5)
    
    assert result.success
    # Should return empty list (no invariants with T999)
    invariants = result.get('t_invariants', [])
    assert len(invariants) == 0


def test_t_invariant_firing_sequence(simple_cycle_model):
    """Test firing sequence string generation."""
    analyzer = TInvariantAnalyzer(simple_cycle_model)
    result = analyzer.analyze()
    
    assert result.success
    
    invariants = result.get('t_invariants', [])
    if len(invariants) > 0:
        inv = invariants[0]
        assert 'firing_sequence' in inv
        assert isinstance(inv['firing_sequence'], str)
        # Should contain transition names
        for name in inv['transition_names']:
            assert name in inv['firing_sequence']


def test_t_invariant_total_firings(simple_cycle_model):
    """Test total firings calculation."""
    analyzer = TInvariantAnalyzer(simple_cycle_model)
    result = analyzer.analyze()
    
    assert result.success
    
    invariants = result.get('t_invariants', [])
    if len(invariants) > 0:
        inv = invariants[0]
        assert 'total_firings' in inv
        # Total should equal sum of weights
        assert inv['total_firings'] == sum(inv['weights'])


def test_t_invariant_metadata(simple_cycle_model):
    """Test metadata in analysis result."""
    analyzer = TInvariantAnalyzer(simple_cycle_model)
    result = analyzer.analyze(
        min_support=1,
        max_invariants=50,
        normalize=True,
        classify=True
    )
    
    assert result.success
    
    metadata = result.metadata
    assert 'analysis_time' in metadata
    assert 'min_support' in metadata
    assert 'max_invariants' in metadata
    assert 'normalize' in metadata
    assert 'classify' in metadata
    
    # Check parameter values
    assert metadata['min_support'] == 1
    assert metadata['max_invariants'] == 50
    assert metadata['normalize'] is True
    assert metadata['classify'] is True


def test_t_invariant_error_handling():
    """Test error handling with invalid model."""
    # Model with None transitions
    bad_model = Mock()
    bad_model.places = [Mock(id='P1', name='P1')]
    bad_model.transitions = None  # Invalid
    bad_model.arcs = []
    
    analyzer = TInvariantAnalyzer(bad_model)
    result = analyzer.analyze()
    
    # Should fail gracefully
    assert not result.success
    assert len(result.errors) > 0


def test_t_invariant_vs_p_invariant():
    """Test that T-invariants differ from P-invariants (kernel of C vs C^T)."""
    # This is a conceptual test to ensure we're computing the right thing
    # T-invariants: C * x = 0 (kernel of C)
    # P-invariants: C^T * y = 0 (kernel of C^T)
    
    model = Mock()
    p1 = Mock(id='P1', name='P1')
    p2 = Mock(id='P2', name='P2')
    model.places = [p1, p2]
    
    t1 = Mock(id='T1', name='T1')
    t2 = Mock(id='T2', name='T2')
    model.transitions = [t1, t2]
    
    # Simple cycle
    arc1 = Mock(source_id='P1', target_id='T1', weight=1)
    arc2 = Mock(source_id='T1', target_id='P2', weight=1)
    arc3 = Mock(source_id='P2', target_id='T2', weight=1)
    arc4 = Mock(source_id='T2', target_id='P1', weight=1)
    model.arcs = [arc1, arc2, arc3, arc4]
    
    analyzer = TInvariantAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    # Should find T-invariant (the cycle T1→T2→T1)
    assert result.get('count', 0) > 0
