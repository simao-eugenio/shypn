"""Tests for fix sequencer."""
import pytest
from shypn.ui.panels.viability.investigation import Suggestion
from shypn.ui.panels.viability.fixes.fix_sequencer import FixSequencer, FixSequence


def test_fix_sequencer_creation():
    """Test creating fix sequencer."""
    sequencer = FixSequencer()
    assert sequencer is not None
    assert len(sequencer.fix_graph) == 0
    assert len(sequencer.fix_map) == 0


def test_sequence_empty():
    """Test sequencing empty list."""
    sequencer = FixSequencer()
    sequence = sequencer.sequence([])
    
    assert sequence.total_fixes == 0
    assert len(sequence.batches) == 0


def test_sequence_single_fix():
    """Test sequencing single fix."""
    sequencer = FixSequencer()
    
    suggestion = Suggestion(
        category='structural',
        action="Balance arc weights",
        impact="Improves balance",
        target_element_id="T1"
    )
    
    sequence = sequencer.sequence([suggestion])
    
    assert sequence.total_fixes == 1
    assert len(sequence.batches) == 1
    assert len(sequence.get_batch(0)) == 1


def test_sequence_by_category_priority():
    """Test sequencing respects category priority."""
    sequencer = FixSequencer()
    
    # Structural should come before kinetic
    structural = Suggestion(
        category='structural',
        action="Balance weights",
        impact="Structure fix",
        target_element_id="T1"
    )
    
    kinetic = Suggestion(
        category='kinetic',
        action="Increase rate",
        impact="Rate fix",
        target_element_id="T1"  # Same element
    )
    
    sequence = sequencer.sequence([kinetic, structural])  # Pass in reverse order
    
    # Should have 2 batches due to dependency
    assert len(sequence.batches) >= 1
    
    # Structural should come first (lower priority number)
    all_fixes = sequence.get_all_fixes()
    structural_idx = all_fixes.index(structural)
    kinetic_idx = all_fixes.index(kinetic)
    assert structural_idx < kinetic_idx


def test_sequence_parallel_fixes():
    """Test independent fixes can be in same batch."""
    sequencer = FixSequencer()
    
    # Two fixes on different elements - no dependencies
    fix1 = Suggestion(
        category='kinetic',
        action="Increase rate",
        impact="Fix T1",
        target_element_id="T1"
    )
    
    fix2 = Suggestion(
        category='kinetic',
        action="Increase rate",
        impact="Fix T2",
        target_element_id="T2"
    )
    
    sequence = sequencer.sequence([fix1, fix2])
    
    # Should be in same batch (no dependencies)
    assert len(sequence.batches) == 1
    assert len(sequence.get_batch(0)) == 2


def test_sequence_cascading_fix():
    """Test cascading fixes are sequenced correctly."""
    sequencer = FixSequencer()
    
    # Root cause fix
    root = Suggestion(
        category='flow',
        action="Fix root cause",
        impact="Resolves cascade",
        target_element_id="T1",
        details={'is_root_cause': True, 'affected_transitions': ['T2', 'T3']}
    )
    
    # Downstream fix
    downstream = Suggestion(
        category='flow',
        action="Fix downstream",
        impact="Local fix",
        target_element_id="T2"
    )
    
    sequence = sequencer.sequence([downstream, root])
    
    # Root should come before downstream
    all_fixes = sequence.get_all_fixes()
    root_idx = all_fixes.index(root)
    downstream_idx = all_fixes.index(downstream)
    assert root_idx < downstream_idx


def test_sequence_bottleneck_before_balance():
    """Test bottleneck fixes come before flow balance."""
    sequencer = FixSequencer()
    
    bottleneck = Suggestion(
        category='flow',
        action="Fix bottleneck at T1",
        impact="Improve throughput",
        target_element_id="T1"
    )
    
    balance = Suggestion(
        category='flow',
        action="Balance flow rates",
        impact="Balance production/consumption",
        target_element_id="T1"
    )
    
    sequence = sequencer.sequence([balance, bottleneck])
    
    # Bottleneck should come first
    all_fixes = sequence.get_all_fixes()
    bottleneck_idx = all_fixes.index(bottleneck)
    balance_idx = all_fixes.index(balance)
    assert bottleneck_idx < balance_idx


def test_detect_conflicts():
    """Test conflict detection."""
    sequencer = FixSequencer()
    
    # Contradictory fixes: increase vs decrease
    increase = Suggestion(
        category='kinetic',
        action="Increase rate",
        impact="Speed up",
        target_element_id="T1"
    )
    
    decrease = Suggestion(
        category='kinetic',
        action="Decrease rate",
        impact="Slow down",
        target_element_id="T1"
    )
    
    sequence = sequencer.sequence([increase, decrease])
    
    assert len(sequence.conflicts) > 0
    assert sequence.has_conflicts()


def test_detect_add_remove_conflict():
    """Test detecting add vs remove conflict."""
    sequencer = FixSequencer()
    
    add = Suggestion(
        category='structural',
        action="Add arc",
        impact="Add connection",
        target_element_id="T1"
    )
    
    remove = Suggestion(
        category='structural',
        action="Remove arc",
        impact="Remove connection",
        target_element_id="T1"
    )
    
    sequence = sequencer.sequence([add, remove])
    
    assert sequence.has_conflicts()


def test_get_all_fixes():
    """Test getting all fixes in order."""
    sequencer = FixSequencer()
    
    fixes = [
        Suggestion(category='structural', action=f"Fix {i}", impact="Impact", 
                  target_element_id=f"T{i}")
        for i in range(5)
    ]
    
    sequence = sequencer.sequence(fixes)
    all_fixes = sequence.get_all_fixes()
    
    assert len(all_fixes) == 5


def test_explain_sequence():
    """Test sequence explanation generation."""
    sequencer = FixSequencer()
    
    fixes = [
        Suggestion(category='structural', action="Fix structure", impact="Impact1", 
                  target_element_id="T1"),
        Suggestion(category='kinetic', action="Fix rate", impact="Impact2", 
                  target_element_id="T2"),
    ]
    
    sequence = sequencer.sequence(fixes)
    explanation = sequencer.explain_sequence(sequence)
    
    assert "Fix Sequence" in explanation
    assert "Batch" in explanation
    assert len(explanation) > 0
