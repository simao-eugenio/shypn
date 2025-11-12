"""Tests for dependency analyzer."""
import pytest
from shypn.ui.panels.viability.analysis.dependency_analyzer import DependencyAnalyzer
from shypn.ui.panels.viability.investigation import Dependency


def test_dependency_analyzer_creation():
    """Test creating dependency analyzer."""
    analyzer = DependencyAnalyzer()
    assert analyzer is not None
    assert len(analyzer.issues) == 0
    assert len(analyzer.suggestions) == 0


def test_analyze_flow_balance_imbalance():
    """Test detecting flow imbalance."""
    analyzer = DependencyAnalyzer()
    
    # Create dependency with imbalanced rates
    dep = Dependency(
        source_transition_id="T1",
        target_transition_id="T2",
        shared_place_id="P1",
        flow_direction="T1 → P1 → T2"
    )
    
    sim_data = {
        'T1': {'rate': 10.0},  # T1 produces at 10/s
        'T2': {'rate': 2.0},   # T2 consumes at 2/s -> imbalance!
        'P1': {'tokens_over_time': [0, 5, 15, 30, 50]}  # Accumulating
    }
    
    context = {
        'dependencies': [dep],
        'sim_data': sim_data
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect imbalance
    assert any('imbalance' in issue.message.lower() for issue in issues)
    assert any(issue.category == 'flow' for issue in issues)


def test_analyze_bottleneck():
    """Test detecting bottleneck transition."""
    analyzer = DependencyAnalyzer()
    
    dep1 = Dependency("T1", "T2", "P1", "T1 → P1 → T2")
    dep2 = Dependency("T2", "T3", "P2", "T2 → P2 → T3")
    
    sim_data = {
        'T1': {'rate': 10.0},
        'T2': {'rate': 1.0},  # Bottleneck!
        'T3': {'rate': 8.0},
        'P1': {'tokens_over_time': [0, 5, 15, 30]},  # Accumulating before T2
        'P2': {'tokens_over_time': [10, 8, 5, 2]}    # Depleting after T2
    }
    
    context = {
        'dependencies': [dep1, dep2],
        'sim_data': sim_data
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect T2 as bottleneck
    assert any('bottleneck' in issue.message.lower() for issue in issues)
    assert any('T2' in issue.element_id for issue in issues)


def test_analyze_cascading_issues():
    """Test detecting cascading issues."""
    analyzer = DependencyAnalyzer()
    
    dep1 = Dependency("T1", "T2", "P1", "T1 → P1 → T2")
    dep2 = Dependency("T2", "T3", "P2", "T2 → P2 → T3")
    
    # T1 has issue -> affects T2 -> affects T3
    locality_issues = {
        'T1': [{'severity': 'error', 'message': 'Never fired'}],
        'T2': [{'severity': 'warning', 'message': 'Low rate'}],
        'T3': [{'severity': 'warning', 'message': 'Low rate'}]
    }
    
    context = {
        'dependencies': [dep1, dep2],
        'locality_issues': locality_issues
    }
    
    issues = analyzer.analyze(context)
    
    # Should detect cascade from T1
    assert any('cascading' in issue.message.lower() or 'downstream' in issue.message.lower() 
               for issue in issues)


def test_generate_suggestions_flow():
    """Test generating flow balance suggestions."""
    from shypn.ui.panels.viability.investigation import Issue
    
    analyzer = DependencyAnalyzer()
    
    issue = Issue(
        category='flow',
        severity='warning',
        message="Flow imbalance",
        element_id="T1→P1→T2",
        details={
            'producer_rate': 10.0,
            'consumer_rate': 2.0,
            'source': 'T1',
            'target': 'T2'
        }
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    # Should suggest adjusting rates
    assert any('rate' in sug.action.lower() for sug in suggestions)


def test_generate_suggestions_bottleneck():
    """Test generating bottleneck suggestions."""
    from shypn.ui.panels.viability.investigation import Issue
    
    analyzer = DependencyAnalyzer()
    
    issue = Issue(
        category='flow',
        severity='error',
        message="Bottleneck detected",
        element_id="T2",
        details={
            'is_bottleneck': True,
            'current_rate': 1.0,
            'required_rate': 8.0
        }
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    # Should suggest increasing rate or checking enablement
    assert any('increase' in sug.action.lower() or 'enablement' in sug.action.lower() 
               for sug in suggestions)


def test_generate_suggestions_cascade():
    """Test generating cascade fix suggestions."""
    from shypn.ui.panels.viability.investigation import Issue
    
    analyzer = DependencyAnalyzer()
    
    issue = Issue(
        category='flow',
        severity='warning',
        message="Cascading issues detected",
        element_id="T1",
        details={
            'is_root_cause': True,
            'affected_transitions': ['T2', 'T3']
        }
    )
    
    context = {}
    suggestions = analyzer.generate_suggestions([issue], context)
    
    assert len(suggestions) > 0
    # Should suggest fixing root cause
    assert any('root cause' in sug.action.lower() for sug in suggestions)


def test_clear():
    """Test clearing analyzer state."""
    analyzer = DependencyAnalyzer()
    
    dep = Dependency("T1", "T2", "P1", "T1 → P1 → T2")
    context = {'dependencies': [dep], 'sim_data': {}}
    
    analyzer.analyze(context)
    analyzer.clear()
    
    assert len(analyzer.issues) == 0
    assert len(analyzer.suggestions) == 0
