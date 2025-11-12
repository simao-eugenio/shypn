"""Tests for locality analyzer."""
import pytest
from shypn.ui.panels.viability.analysis.locality_analyzer import LocalityAnalyzer
from shypn.ui.panels.viability.investigation import Issue, Suggestion


class MockKB:
    """Mock knowledge base."""
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.compounds = {}


def test_locality_analyzer_creation():
    """Test creating locality analyzer."""
    analyzer = LocalityAnalyzer()
    assert analyzer is not None
    assert len(analyzer.issues) == 0
    assert len(analyzer.suggestions) == 0


def test_analyze_structural_no_inputs(simple_locality):
    """Test detecting transition with no inputs."""
    from tests.viability.conftest import MockTransition, MockLocality
    
    # Create transition with no inputs
    t1 = MockTransition(id="T1", label="Source")
    loc = MockLocality(t1, [], simple_locality.output_places, [], simple_locality.output_arcs)
    
    analyzer = LocalityAnalyzer()
    kb = MockKB()
    
    context = {
        'transition': t1,
        'locality': loc,
        'kb': kb
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect source transition
    assert any('no input places' in issue.message for issue in issues)
    assert any(issue.severity == 'warning' for issue in issues)


def test_analyze_structural_no_outputs(simple_locality):
    """Test detecting transition with no outputs."""
    from tests.viability.conftest import MockTransition, MockLocality
    
    # Create transition with no outputs
    t1 = MockTransition(id="T1", label="Sink")
    loc = MockLocality(t1, simple_locality.input_places, [], simple_locality.input_arcs, [])
    
    analyzer = LocalityAnalyzer()
    kb = MockKB()
    
    context = {
        'transition': t1,
        'locality': loc,
        'kb': kb
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect sink transition
    assert any('no output places' in issue.message for issue in issues)


def test_analyze_biological_unmapped(simple_locality):
    """Test detecting unmapped compounds."""
    analyzer = LocalityAnalyzer()
    kb = MockKB()
    
    context = {
        'transition': simple_locality.transition,
        'locality': simple_locality,
        'kb': kb
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect unmapped places
    assert any('unmapped' in issue.message.lower() for issue in issues)
    assert any(issue.category == 'biological' for issue in issues)


def test_analyze_kinetic_never_fired(simple_locality):
    """Test detecting transition that never fired."""
    analyzer = LocalityAnalyzer()
    kb = MockKB()
    
    sim_data = {
        'firing_count': 0,
        'duration': 60.0
    }
    
    context = {
        'transition': simple_locality.transition,
        'locality': simple_locality,
        'kb': kb,
        'sim_data': sim_data
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect zero firings
    assert any('never fired' in issue.message for issue in issues)
    assert any(issue.category == 'kinetic' for issue in issues)
    assert any(issue.severity == 'error' for issue in issues)


def test_analyze_kinetic_low_rate(simple_locality):
    """Test detecting low firing rate."""
    analyzer = LocalityAnalyzer()
    kb = MockKB()
    
    sim_data = {
        'firing_count': 3,  # Only 3 firings
        'duration': 60.0
    }
    
    context = {
        'transition': simple_locality.transition,
        'locality': simple_locality,
        'kb': kb,
        'sim_data': sim_data
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect low rate (< 0.1 firings/s)
    assert any('low firing rate' in issue.message for issue in issues)


def test_generate_suggestions_structural(simple_locality):
    """Test generating structural suggestions."""
    analyzer = LocalityAnalyzer()
    
    issue = Issue(
        category='structural',
        severity='warning',
        message="Test issue",
        element_id="T1",
        details={'is_source': True}
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    assert any(sug.category == 'structural' for sug in suggestions)


def test_generate_suggestions_kinetic(simple_locality):
    """Test generating kinetic suggestions."""
    analyzer = LocalityAnalyzer()
    
    issue = Issue(
        category='kinetic',
        severity='error',
        message="Never fired",
        element_id="T1",
        details={'firing_count': 0, 'needs_rate': True}
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    # Should suggest BRENDA query or rate investigation
    assert any('brenda' in sug.action.lower() or 'enablement' in sug.action.lower() 
               for sug in suggestions)


def test_clear(simple_locality):
    """Test clearing analyzer state."""
    analyzer = LocalityAnalyzer()
    kb = MockKB()
    
    context = {
        'transition': simple_locality.transition,
        'locality': simple_locality,
        'kb': kb
    }
    
    analyzer.analyze(context)
    assert len(analyzer.issues) > 0
    
    analyzer.clear()
    assert len(analyzer.issues) == 0
    assert len(analyzer.suggestions) == 0
