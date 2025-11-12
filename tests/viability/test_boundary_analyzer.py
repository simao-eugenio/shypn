"""Tests for boundary analyzer."""
import pytest
from shypn.ui.panels.viability.analysis.boundary_analyzer import BoundaryAnalyzer


def test_boundary_analyzer_creation():
    """Test creating boundary analyzer."""
    analyzer = BoundaryAnalyzer()
    assert analyzer is not None
    assert len(analyzer.issues) == 0
    assert len(analyzer.suggestions) == 0


def test_analyze_accumulation():
    """Test detecting accumulation at boundary."""
    analyzer = BoundaryAnalyzer()
    
    boundary_places = {
        'P1': {
            'type': 'output',  # Subnet output
            'initial_tokens': 10,
            'tokens_over_time': [10, 15, 25, 40]  # Accumulating!
        }
    }
    
    context = {
        'boundary_places': boundary_places,
        'duration': 30.0
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect accumulation (> 2x initial)
    assert any('accumulation' in issue.message.lower() for issue in issues)
    assert any(issue.severity == 'warning' for issue in issues)


def test_analyze_depletion():
    """Test detecting depletion at boundary."""
    analyzer = BoundaryAnalyzer()
    
    boundary_places = {
        'P1': {
            'type': 'input',  # Subnet input
            'initial_tokens': 100,
            'tokens_over_time': [100, 80, 40, 10]  # Depleting!
        }
    }
    
    context = {
        'boundary_places': boundary_places,
        'duration': 30.0
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect depletion (< 50% initial)
    assert any('depletion' in issue.message.lower() for issue in issues)


def test_analyze_critical_depletion():
    """Test detecting critical depletion (near empty)."""
    analyzer = BoundaryAnalyzer()
    
    boundary_places = {
        'P1': {
            'type': 'input',
            'initial_tokens': 100,
            'tokens_over_time': [100, 50, 8, 2]  # Near empty!
        }
    }
    
    context = {
        'boundary_places': boundary_places,
        'duration': 30.0
    }
    
    issues = analyzer.analyze(context)
    
    # Should be error severity (< 10% initial)
    assert any(issue.severity == 'error' for issue in issues)


def test_analyze_balance():
    """Test analyzing subnet input/output balance."""
    analyzer = BoundaryAnalyzer()
    
    boundary_places = {
        'P_in': {
            'type': 'input',
            'initial_tokens': 100,
            'tokens_over_time': [100, 90, 80, 70]  # Consuming 30
        },
        'P_out': {
            'type': 'output',
            'initial_tokens': 0,
            'tokens_over_time': [0, 5, 10, 15]  # Producing 15
        }
    }
    
    context = {
        'boundary_places': boundary_places,
        'duration': 30.0
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect imbalance (30 consumed, 15 produced)
    assert any('balance' in issue.message.lower() or 'leak' in issue.message.lower() 
               for issue in issues)


def test_create_boundary_analysis():
    """Test creating boundary analysis summary."""
    analyzer = BoundaryAnalyzer()
    
    boundary_places = {
        'P_in': {
            'type': 'input',
            'initial_tokens': 100,
            'tokens_over_time': [100, 90, 80, 70]
        },
        'P_out': {
            'type': 'output',
            'initial_tokens': 0,
            'tokens_over_time': [0, 8, 18, 30]
        }
    }
    
    context = {
        'boundary_places': boundary_places,
        'duration': 30.0
    }
    
    analyzer.analyze(context)
    summary = analyzer.create_boundary_analysis(context)
    
    assert summary is not None
    assert 'P_in' in summary.inputs or 'P_in' in summary.outputs
    assert 'P_out' in summary.inputs or 'P_out' in summary.outputs


def test_generate_suggestions_accumulation():
    """Test generating accumulation fix suggestions."""
    from shypn.ui.panels.viability.investigation import Issue
    
    analyzer = BoundaryAnalyzer()
    
    issue = Issue(
        category='boundary',
        severity='warning',
        message="Accumulation detected",
        element_id="P1",
        details={
            'type': 'accumulation',
            'initial': 10,
            'final': 50,
            'change': 40
        }
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    # Should suggest adding sink or reviewing storage
    assert any('sink' in sug.action.lower() or 'storage' in sug.action.lower() 
               for sug in suggestions)


def test_generate_suggestions_depletion():
    """Test generating depletion fix suggestions."""
    from shypn.ui.panels.viability.investigation import Issue
    
    analyzer = BoundaryAnalyzer()
    
    issue = Issue(
        category='boundary',
        severity='error',
        message="Critical depletion",
        element_id="P1",
        details={
            'type': 'depletion',
            'initial': 100,
            'final': 5,
            'change': -95
        }
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    # Should suggest adding source
    assert any('source' in sug.action.lower() for sug in suggestions)


def test_generate_suggestions_balance():
    """Test generating balance fix suggestions."""
    from shypn.ui.panels.viability.investigation import Issue
    
    analyzer = BoundaryAnalyzer()
    
    issue = Issue(
        category='boundary',
        severity='warning',
        message="Input/output imbalance",
        element_id="subnet",
        details={
            'type': 'balance',
            'total_input_change': -50,
            'total_output_change': 20
        }
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    # Should suggest balancing flows
    assert any('balance' in sug.action.lower() for sug in suggestions)


def test_clear():
    """Test clearing analyzer state."""
    analyzer = BoundaryAnalyzer()
    
    boundary_places = {
        'P1': {
            'type': 'input',
            'initial_tokens': 100,
            'tokens_over_time': [100, 80, 40, 10]
        }
    }
    
    context = {'boundary_places': boundary_places, 'duration': 30.0}
    
    analyzer.analyze(context)
    assert len(analyzer.issues) > 0
    
    analyzer.clear()
    assert len(analyzer.issues) == 0
    assert len(analyzer.suggestions) == 0
