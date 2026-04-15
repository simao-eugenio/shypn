"""Test Phase 1: Core Parallel BFS with work-stealing.

Tests the OOP refactored parallel reachability implementation.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer


class MockPlace:
    """Mock place for testing."""
    def __init__(self, place_id, tokens=0):
        self.id = place_id
        self.marking = tokens
        self.tokens = tokens


class MockTransition:
    """Mock transition for testing."""
    def __init__(self, trans_id, name=None):
        self.id = trans_id
        self.name = name or f"T{trans_id}"


class MockArc:
    """Mock arc for testing."""
    def __init__(self, source_id, target_id, weight=1):
        self.source_id = source_id
        self.target_id = target_id
        self.weight = weight


class MockModel:
    """Mock Petri net model for testing."""
    def __init__(self):
        # Simple 3-place producer-consumer model
        # P1 --[w=1]--> T1 --[w=1]--> P2 --[w=1]--> T2 --[w=1]--> P3
        self.places = [
            MockPlace('P1', tokens=2),
            MockPlace('P2', tokens=0),
            MockPlace('P3', tokens=0)
        ]
        
        self.transitions = [
            MockTransition('T1', 'Produce'),
            MockTransition('T2', 'Consume')
        ]
        
        self.arcs = [
            MockArc('P1', 'T1', weight=1),
            MockArc('T1', 'P2', weight=1),
            MockArc('P2', 'T2', weight=1),
            MockArc('T2', 'P3', weight=1)
        ]


def test_sequential_exploration():
    """Test sequential exploration (baseline)."""
    model = MockModel()
    analyzer = ReachabilityAnalyzer(model)
    
    result = analyzer.analyze(
        max_states=100,
        max_depth=10,
        compute_graph=True,
        find_deadlocks=True,
        parallel=False
    )
    
    assert result.success
    assert result.get('total_states') > 0
    assert result.get('total_transitions') >= 0
    assert result.metadata['mode'] == 'sequential'
    assert result.metadata['num_workers'] == 1
    print(f"✓ Sequential: {result.get('total_states')} states, {result.get('total_transitions')} transitions")


def test_parallel_basic_exploration():
    """Test Phase 1: Basic work-stealing parallel exploration."""
    model = MockModel()
    analyzer = ReachabilityAnalyzer(model)
    
    result = analyzer.analyze(
        max_states=100,
        max_depth=10,
        compute_graph=True,
        find_deadlocks=True,
        parallel=True,  # Phase 1: basic work-stealing
        num_workers=2
    )
    
    assert result.success
    assert result.get('total_states') > 0
    assert result.metadata['mode'] == 'parallel_basic'
    assert result.metadata['num_workers'] == 2
    print(f"✓ Parallel Basic: {result.get('total_states')} states, {result.get('total_transitions')} transitions")


def test_parallel_maximal_exploration():
    """Test Phase 2: Maximal concurrent sets exploration."""
    model = MockModel()
    analyzer = ReachabilityAnalyzer(model)
    
    result = analyzer.analyze(
        max_states=100,
        max_depth=10,
        compute_graph=True,
        find_deadlocks=True,
        parallel='maximal',  # Phase 2: maximal concurrent sets
        num_workers=2
    )
    
    assert result.success
    assert result.get('total_states') > 0
    assert result.metadata['mode'] == 'parallel_maximal'
    assert result.metadata['num_workers'] == 2
    print(f"✓ Parallel Maximal: {result.get('total_states')} states, {result.get('total_transitions')} transitions")


def test_results_consistency():
    """Test that all strategies produce same state count."""
    model = MockModel()
    analyzer = ReachabilityAnalyzer(model)
    
    # Run all three strategies
    seq_result = analyzer.analyze(max_states=100, parallel=False)
    basic_result = analyzer.analyze(max_states=100, parallel=True, num_workers=2)
    maximal_result = analyzer.analyze(max_states=100, parallel='maximal', num_workers=2)
    
    # All should find same number of states
    seq_states = seq_result.get('total_states')
    basic_states = basic_result.get('total_states')
    maximal_states = maximal_result.get('total_states')
    
    assert seq_states == basic_states, f"Sequential ({seq_states}) != Basic ({basic_states})"
    assert seq_states == maximal_states, f"Sequential ({seq_states}) != Maximal ({maximal_states})"
    
    print(f"✓ Consistency: All strategies found {seq_states} states")


def test_deadlock_detection():
    """Test deadlock detection works in parallel mode."""
    # Create model with deadlock
    model = MockModel()
    model.places[0].marking = 0  # No tokens in P1 - immediate deadlock
    model.places[0].tokens = 0
    
    analyzer = ReachabilityAnalyzer(model)
    
    result = analyzer.analyze(
        max_states=10,
        find_deadlocks=True,
        parallel=True,
        num_workers=2
    )
    
    assert result.success
    deadlocks = result.get('deadlock_states', [])
    assert len(deadlocks) > 0, "Should find at least one deadlock state"
    print(f"✓ Deadlock detection: Found {len(deadlocks)} deadlock(s)")


if __name__ == '__main__':
    print("Testing Phase 1: Parallel BFS Implementation")
    print("=" * 60)
    
    try:
        test_sequential_exploration()
        test_parallel_basic_exploration()
        test_parallel_maximal_exploration()
        test_results_consistency()
        test_deadlock_detection()
        
        print("=" * 60)
        print("✅ All Phase 1 tests passed!")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
