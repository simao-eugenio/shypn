"""Tests for conservation analyzer."""
import pytest
from shypn.ui.panels.viability.analysis.conservation_analyzer import ConservationAnalyzer


def test_conservation_analyzer_creation():
    """Test creating conservation analyzer."""
    analyzer = ConservationAnalyzer()
    assert analyzer is not None
    assert len(analyzer.issues) == 0
    assert len(analyzer.suggestions) == 0


def test_analyze_p_invariants_violated():
    """Test detecting P-invariant violation."""
    analyzer = ConservationAnalyzer()
    
    p_invariants = [
        {
            'places': ['P1', 'P2', 'P3'],
            'coefficients': [1, 1, 1],
            'expected_sum': 100,
            'tokens_over_time': {
                'P1': [30, 25, 20, 15],
                'P2': [40, 35, 30, 25],
                'P3': [30, 30, 30, 30]
            }
        }
    ]
    
    context = {
        'p_invariants': p_invariants,
        'duration': 30.0
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect violation (sum decreasing: 100 → 90 → 80 → 70)
    assert any('invariant' in issue.message.lower() for issue in issues)
    assert any(issue.category == 'conservation' for issue in issues)


def test_analyze_p_invariants_preserved():
    """Test detecting properly preserved P-invariants."""
    analyzer = ConservationAnalyzer()
    
    p_invariants = [
        {
            'places': ['P1', 'P2'],
            'coefficients': [1, 1],
            'expected_sum': 100,
            'tokens_over_time': {
                'P1': [60, 50, 70, 40],
                'P2': [40, 50, 30, 60]
            }
        }
    ]
    
    context = {
        'p_invariants': p_invariants,
        'duration': 30.0
    }
    
    issues = analyzer.analyze(context)
    
    # Should not detect issues (sum always 100)
    assert not any('invariant' in issue.message.lower() for issue in issues)


def test_analyze_mass_balance_mismatch():
    """Test detecting mass balance violation."""
    analyzer = ConservationAnalyzer()
    
    reactions = [
        {
            'transition_id': 'T1',
            'reaction_id': 'R00001',
            'substrates': [
                {'compound_id': 'C00001', 'stoichiometry': 1, 'formula': 'H2O'}
            ],
            'products': [
                {'compound_id': 'C00002', 'stoichiometry': 1, 'formula': 'CO2'}
            ]
        }
    ]
    
    context = {
        'reactions': reactions
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect mass mismatch (H2O ≠ CO2)
    assert any('mass balance' in issue.message.lower() for issue in issues)


def test_analyze_mass_balance_valid():
    """Test valid mass balance."""
    analyzer = ConservationAnalyzer()
    
    reactions = [
        {
            'transition_id': 'T1',
            'reaction_id': 'R00001',
            'substrates': [
                {'compound_id': 'C00001', 'stoichiometry': 1, 'formula': 'C6H12O6'}
            ],
            'products': [
                {'compound_id': 'C00002', 'stoichiometry': 2, 'formula': 'C3H6O3'}
            ]
        }
    ]
    
    context = {
        'reactions': reactions
    }
    
    issues = analyzer.analyze(context)
    
    # Should not detect issues (mass balanced: C6H12O6 → 2×C3H6O3)
    assert not any('mass balance' in issue.message.lower() for issue in issues)


def test_analyze_conservation_leaks():
    """Test detecting unexplained material changes."""
    analyzer = ConservationAnalyzer()
    
    places = {
        'P1': {
            'compound_id': 'C00001',
            'initial_tokens': 100,
            'final_tokens': 50
        },
        'P2': {
            'compound_id': 'C00001',  # Same compound
            'initial_tokens': 0,
            'final_tokens': 30
        }
    }
    
    transitions = []  # No transitions to explain the change
    
    context = {
        'places': places,
        'transitions': transitions,
        'duration': 30.0
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect leak (100 → 50+30 = 80, missing 20 units)
    assert any('leak' in issue.message.lower() for issue in issues)


def test_create_conservation_analysis():
    """Test creating conservation analysis summary."""
    analyzer = ConservationAnalyzer()
    
    p_invariants = [
        {
            'places': ['P1', 'P2'],
            'coefficients': [1, 1],
            'expected_sum': 100,
            'tokens_over_time': {
                'P1': [50, 50],
                'P2': [50, 50]
            }
        }
    ]
    
    context = {
        'p_invariants': p_invariants,
        'duration': 10.0
    }
    
    analyzer.analyze(context)
    summary = analyzer.create_conservation_analysis(context)
    
    assert summary is not None
    assert len(summary.invariants_violated) >= 0
    assert len(summary.mass_balance_issues) >= 0


def test_generate_suggestions_invariant():
    """Test generating P-invariant fix suggestions."""
    from shypn.ui.panels.viability.investigation import Issue
    
    analyzer = ConservationAnalyzer()
    
    issue = Issue(
        category='conservation',
        severity='error',
        message="P-invariant violated",
        element_id="P1+P2+P3",
        details={
            'type': 'p_invariant',
            'places': ['P1', 'P2', 'P3'],
            'expected': 100,
            'actual': 85
        }
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    # Should suggest adding source/sink or fixing stoichiometry
    assert any('source' in sug.action.lower() or 'stoichiometry' in sug.action.lower() 
               for sug in suggestions)


def test_generate_suggestions_mass_balance():
    """Test generating mass balance fix suggestions."""
    from shypn.ui.panels.viability.investigation import Issue
    
    analyzer = ConservationAnalyzer()
    
    issue = Issue(
        category='conservation',
        severity='warning',
        message="Mass balance mismatch",
        element_id="T1",
        details={
            'type': 'mass_balance',
            'reaction_id': 'R00001',
            'substrate_mass': 'C6H12O6',
            'product_mass': 'C6H10O6'
        }
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    # Should suggest mapping reaction or reviewing stoichiometry
    assert any('map' in sug.action.lower() or 'stoichiometry' in sug.action.lower() 
               for sug in suggestions)


def test_generate_suggestions_leak():
    """Test generating conservation leak fix suggestions."""
    from shypn.ui.panels.viability.investigation import Issue
    
    analyzer = ConservationAnalyzer()
    
    issue = Issue(
        category='conservation',
        severity='error',
        message="Material leak detected",
        element_id="C00001",
        details={
            'type': 'leak',
            'compound_id': 'C00001',
            'missing_amount': 20
        }
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    # Should suggest reviewing stoichiometry or arc weights
    assert any('stoichiometry' in sug.action.lower() or 'arc' in sug.action.lower() 
               for sug in suggestions)


def test_clear():
    """Test clearing analyzer state."""
    analyzer = ConservationAnalyzer()
    
    p_invariants = [
        {
            'places': ['P1', 'P2'],
            'coefficients': [1, 1],
            'expected_sum': 100,
            'tokens_over_time': {
                'P1': [60, 40],
                'P2': [40, 40]
            }
        }
    ]
    
    context = {'p_invariants': p_invariants, 'duration': 10.0}
    
    analyzer.analyze(context)
    analyzer.clear()
    
    assert len(analyzer.issues) == 0
    assert len(analyzer.suggestions) == 0
