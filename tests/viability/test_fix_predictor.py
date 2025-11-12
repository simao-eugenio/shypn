"""Tests for fix predictor."""
import pytest
from shypn.ui.panels.viability.investigation import Suggestion
from shypn.ui.panels.viability.fixes.fix_predictor import (
    FixPredictor, FixPrediction, ImpactLevel, ChangeType
)


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


def test_fix_predictor_creation():
    """Test creating fix predictor."""
    kb = MockKB()
    predictor = FixPredictor(kb)
    
    assert predictor is not None
    assert predictor.kb == kb


def test_predict_rate_increase():
    """Test predicting rate increase."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=1.0)
    
    predictor = FixPredictor(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Increase rate",
        impact="Speed up transition",
        target_element_id="T1",
        details={'multiplier': 2.0}
    )
    
    prediction = predictor.predict(suggestion)
    
    assert prediction is not None
    assert len(prediction.direct_changes) > 0
    
    # Should predict rate change
    rate_change = prediction.direct_changes[0]
    assert rate_change.change_type == ChangeType.RATE
    assert rate_change.old_value == 1.0
    assert rate_change.new_value == 2.0


def test_predict_compound_mapping():
    """Test predicting compound mapping."""
    kb = MockKB()
    kb.places['P1'] = MockPlace('P1')
    
    predictor = FixPredictor(kb)
    
    suggestion = Suggestion(
        category='biological',
        action="Map compound to KEGG",
        impact="Add biological context",
        target_element_id="P1",
        details={'compound_id': 'C00001'}
    )
    
    prediction = predictor.predict(suggestion)
    
    assert len(prediction.direct_changes) > 0
    mapping_change = prediction.direct_changes[0]
    assert mapping_change.change_type == ChangeType.MAPPING
    assert mapping_change.new_value == 'C00001'


def test_predict_add_element():
    """Test predicting element addition."""
    kb = MockKB()
    predictor = FixPredictor(kb)
    
    suggestion = Suggestion(
        category='structural',
        action="Add source transition",
        impact="Provide input",
        target_element_id="P1"
    )
    
    prediction = predictor.predict(suggestion)
    
    assert len(prediction.direct_changes) > 0
    add_change = prediction.direct_changes[0]
    assert add_change.change_type == ChangeType.ADD_ELEMENT
    assert 'source' in add_change.description.lower()


def test_impact_level_low():
    """Test low impact prediction."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=1.0)
    
    predictor = FixPredictor(kb)
    
    # Simple rate change - should be low impact
    suggestion = Suggestion(
        category='kinetic',
        action="Increase rate slightly",
        impact="Minor adjustment",
        target_element_id="T1",
        details={'multiplier': 1.1}
    )
    
    prediction = predictor.predict(suggestion)
    
    assert prediction.impact_level == ImpactLevel.LOW


def test_impact_level_high_with_cascades():
    """Test high impact when cascades exist."""
    kb = MockKB()
    
    # Create network: T1 -> P1 -> T2 -> P2 -> T3
    kb.transitions['T1'] = MockTransition('T1')
    kb.transitions['T2'] = MockTransition('T2')
    kb.transitions['T3'] = MockTransition('T3')
    kb.places['P1'] = MockPlace('P1')
    kb.places['P2'] = MockPlace('P2')
    
    kb.arcs['A1'] = MockArc('A1', 'T1', 'P1')
    kb.arcs['A2'] = MockArc('A2', 'P1', 'T2')
    kb.arcs['A3'] = MockArc('A3', 'T2', 'P2')
    kb.arcs['A4'] = MockArc('A4', 'P2', 'T3')
    
    predictor = FixPredictor(kb)
    
    # Changing T1 should cascade
    suggestion = Suggestion(
        category='kinetic',
        action="Increase rate dramatically",
        impact="Large change",
        target_element_id="T1",
        details={'multiplier': 10.0}
    )
    
    prediction = predictor.predict(suggestion)
    
    # Should predict cascades
    assert len(prediction.cascade_changes) > 0
    assert prediction.impact_level in [ImpactLevel.MEDIUM, ImpactLevel.HIGH, ImpactLevel.CRITICAL]


def test_risk_assessment_low():
    """Test low risk assessment."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=1.0)
    
    predictor = FixPredictor(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Minor rate adjustment",
        impact="Small change",
        target_element_id="T1",
        details={'multiplier': 1.1}
    )
    
    prediction = predictor.predict(suggestion)
    
    assert prediction.risk_level == "low"


def test_risk_assessment_high_topology():
    """Test high risk for topology changes."""
    kb = MockKB()
    predictor = FixPredictor(kb)
    
    suggestion = Suggestion(
        category='structural',
        action="Add multiple arcs",
        impact="Change topology",
        target_element_id="T1"
    )
    
    prediction = predictor.predict(suggestion)
    
    # Topology changes should increase risk
    assert prediction.risk_level in ["medium", "high"]


def test_warnings_generated():
    """Test warning generation."""
    kb = MockKB()
    
    # Create larger network for high impact
    for i in range(15):
        kb.transitions[f'T{i}'] = MockTransition(f'T{i}')
        kb.places[f'P{i}'] = MockPlace(f'P{i}')
    
    # Create connections
    for i in range(14):
        kb.arcs[f'A{i}'] = MockArc(f'A{i}', f'T{i}', f'P{i}')
        kb.arcs[f'B{i}'] = MockArc(f'B{i}', f'P{i}', f'T{i+1}')
    
    predictor = FixPredictor(kb)
    
    # Large change that affects many elements
    suggestion = Suggestion(
        category='structural',
        action="Major topology change",
        impact="Affects entire subnet",
        target_element_id="T0"
    )
    
    prediction = predictor.predict(suggestion)
    
    # Should generate warnings
    assert prediction.has_warnings()
    assert len(prediction.warnings) > 0


def test_get_all_changes():
    """Test getting all changes."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=1.0)
    kb.transitions['T2'] = MockTransition('T2', rate=1.0)
    
    # Add connection T1 -> P1 -> T2
    kb.places['P1'] = MockPlace('P1')
    kb.arcs['A1'] = MockArc('A1', 'T1', 'P1')
    kb.arcs['A2'] = MockArc('A2', 'P1', 'T2')
    
    predictor = FixPredictor(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Increase rate",
        impact="Affects downstream",
        target_element_id="T1",
        details={'multiplier': 3.0}
    )
    
    prediction = predictor.predict(suggestion)
    
    all_changes = prediction.get_all_changes()
    
    # Should include direct + cascade changes
    assert len(all_changes) >= len(prediction.direct_changes)


def test_affected_elements():
    """Test affected elements tracking."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=1.0)
    
    predictor = FixPredictor(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Increase rate",
        impact="Speed up",
        target_element_id="T1",
        details={'multiplier': 2.0}
    )
    
    prediction = predictor.predict(suggestion)
    
    # Should track T1 as affected
    assert 'T1' in prediction.affected_elements
    assert len(prediction.affected_elements) >= 1


def test_balance_rates_prediction():
    """Test predicting rate balancing."""
    kb = MockKB()
    kb.transitions['T1'] = MockTransition('T1', rate=10.0)
    kb.transitions['T2'] = MockTransition('T2', rate=2.0)
    
    predictor = FixPredictor(kb)
    
    suggestion = Suggestion(
        category='flow',
        action="Balance rates",
        impact="Balance production/consumption",
        target_element_id="T1",
        details={'source': 'T1', 'target': 'T2'}
    )
    
    prediction = predictor.predict(suggestion)
    
    # Should predict changes to both T1 and T2
    assert len(prediction.direct_changes) >= 2
    assert 'T1' in prediction.affected_elements
    assert 'T2' in prediction.affected_elements


def test_prediction_has_warnings():
    """Test has_warnings method."""
    kb = MockKB()
    predictor = FixPredictor(kb)
    
    suggestion = Suggestion(
        category='kinetic',
        action="Minor change",
        impact="Small",
        target_element_id="T1"
    )
    
    prediction = FixPrediction(suggestion=suggestion)
    
    # No warnings
    assert not prediction.has_warnings()
    
    # Add warning
    prediction.warnings.append("Test warning")
    assert prediction.has_warnings()
