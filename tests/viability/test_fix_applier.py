"""Tests for fix applier."""
import pytest
from shypn.ui.panels.viability.investigation import Suggestion
from shypn.ui.panels.viability.fixes.fix_applier import FixApplier, AppliedFix, FixStatus


class MockKB:
    """Mock knowledge base for testing."""
    def __init__(self):
        self.transitions = {}
        self.places = {}
        self.arcs = {}


class MockTransition:
    """Mock transition."""
    def __init__(self, id, rate=1.0):
        self.id = id
        self.rate = rate


class MockPlace:
    """Mock place."""
    def __init__(self, id):
        self.id = id


class MockArc:
    """Mock arc."""
    def __init__(self, id, source, target, weight=1.0):
        self.id = id
        self.source = source
        self.target = target
        self.weight = weight


def test_fix_applier_creation():
    """Test creating fix applier."""
    kb = MockKB()
    applier = FixApplier(kb)
    
    assert applier is not None
    assert applier.kb == kb
    assert len(applier.applied_fixes) == 0


def test_apply_rate_increase():
    """Test applying rate increase."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=1.0)
    
    applier = FixApplier(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Increase rate",
        impact="Speed up",
        target_element_id="T1",
        details={'multiplier': 2.0}
    )
    
    applied = applier.apply(suggestion)
    
    assert applied.status == FixStatus.APPLIED
    assert applied.applied_at is not None
    assert kb.transitions['T1'].rate == 2.0
    assert applied.previous_state['rate']['old_value'] == 1.0


def test_apply_rate_set():
    """Test setting specific rate."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=1.0)
    
    applier = FixApplier(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Set rate",
        impact="Set specific rate",
        target_element_id="T1",
        details={'rate': 5.0}
    )
    
    applied = applier.apply(suggestion)
    
    assert applied.status == FixStatus.APPLIED
    assert kb.transitions['T1'].rate == 5.0


def test_apply_balance_rates():
    """Test balancing rates between transitions."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=10.0)
    kb.transitions['T2'] = MockTransition('T2', rate=2.0)
    
    applier = FixApplier(kb)
    
    suggestion = Suggestion(
        category='flow',
        action="Balance rates",
        impact="Balance production/consumption",
        target_element_id="T1",
        details={'source': 'T1', 'target': 'T2'}
    )
    
    applied = applier.apply(suggestion)
    
    assert applied.status == FixStatus.APPLIED
    # Both should be set to average (6.0)
    assert kb.transitions['T1'].rate == 6.0
    assert kb.transitions['T2'].rate == 6.0


def test_apply_compound_mapping():
    """Test applying compound mapping."""
    kb = MockKB()
    kb.places['P1'] = MockPlace('P1')
    
    applier = FixApplier(kb)
    
    suggestion = Suggestion(
        category='biological',
        action="Map compound",
        impact="Add KEGG mapping",
        target_element_id="P1",
        details={'compound_id': 'C00001'}
    )
    
    applied = applier.apply(suggestion)
    
    assert applied.status == FixStatus.APPLIED
    assert kb.places['P1'].compound_id == 'C00001'


def test_apply_reaction_mapping():
    """Test applying reaction mapping."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1')
    
    applier = FixApplier(kb)
    
    suggestion = Suggestion(
        category='biological',
        action="Map reaction",
        impact="Add KEGG reaction",
        target_element_id="T1",
        details={'reaction_id': 'R00001'}
    )
    
    applied = applier.apply(suggestion)
    
    assert applied.status == FixStatus.APPLIED
    assert kb.transitions['T1'].reaction_id == 'R00001'


def test_apply_manual_action():
    """Test applying fix requiring manual action."""
    kb = MockKB()
    applier = FixApplier(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Query BRENDA for rate data",
        impact="Get kinetic parameters",
        target_element_id="T1"
    )
    
    applied = applier.apply(suggestion)
    
    assert applied.status == FixStatus.APPLIED
    assert applied.previous_state.get('requires_manual_action') is True


def test_revert_rate_change():
    """Test reverting rate change."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=1.0)
    
    applier = FixApplier(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Increase rate",
        impact="Speed up",
        target_element_id="T1",
        details={'multiplier': 3.0}
    )
    
    applied = applier.apply(suggestion)
    assert kb.transitions['T1'].rate == 3.0
    
    # Revert
    success = applier.revert(applied)
    
    assert success is True
    assert applied.status == FixStatus.REVERTED
    assert applied.reverted_at is not None
    assert kb.transitions['T1'].rate == 1.0


def test_revert_mapping():
    """Test reverting mapping change."""
    kb = MockKB()
    kb.places['P1'] = MockPlace('P1')
    
    applier = FixApplier(kb)
    
    suggestion = Suggestion(
        category='biological',
        action="Map compound",
        impact="Add mapping",
        target_element_id="P1",
        details={'compound_id': 'C00001'}
    )
    
    applied = applier.apply(suggestion)
    assert kb.places['P1'].compound_id == 'C00001'
    
    # Revert
    success = applier.revert(applied)
    
    assert success is True
    assert not hasattr(kb.places['P1'], 'compound_id')


def test_cannot_revert_failed():
    """Test cannot revert failed fix."""
    kb = MockKB()
    applier = FixApplier(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Increase rate",
        impact="Speed up",
        target_element_id="T_NONEXISTENT"  # Doesn't exist
    )
    
    applied = applier.apply(suggestion)
    
    assert applied.status == FixStatus.FAILED
    assert not applied.can_revert()
    
    success = applier.revert(applied)
    assert success is False


def test_get_history():
    """Test getting fix history."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=1.0)
    
    applier = FixApplier(kb)
    
    # Apply multiple fixes
    for i in range(3):
        suggestion = Suggestion(
            category='kinetic',
            action=f"Fix {i}",
            impact="Impact",
            target_element_id="T1",
            details={'multiplier': 2.0}
        )
        applier.apply(suggestion)
    
    history = applier.get_history()
    
    assert len(history) == 3
    assert all(fix.status == FixStatus.APPLIED for fix in history)


def test_clear_history():
    """Test clearing fix history."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=1.0)
    
    applier = FixApplier(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Fix",
        impact="Impact",
        target_element_id="T1",
        details={'multiplier': 2.0}
    )
    applier.apply(suggestion)
    
    assert len(applier.get_history()) == 1
    
    applier.clear_history()
    
    assert len(applier.get_history()) == 0


def test_applied_fix_can_revert():
    """Test can_revert method."""
    suggestion = Suggestion(
        category='kinetic',
        action="Fix",
        impact="Impact",
        target_element_id="T1"
    )
    
    # Applied fix with state
    applied = AppliedFix(
        suggestion=suggestion,
        status=FixStatus.APPLIED,
        previous_state={'rate': {'old_value': 1.0}}
    )
    assert applied.can_revert() is True
    
    # Failed fix
    failed = AppliedFix(
        suggestion=suggestion,
        status=FixStatus.FAILED
    )
    assert failed.can_revert() is False
    
    # Reverted fix
    reverted = AppliedFix(
        suggestion=suggestion,
        status=FixStatus.REVERTED,
        previous_state={'rate': {'old_value': 1.0}}
    )
    assert reverted.can_revert() is False
