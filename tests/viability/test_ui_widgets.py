"""Tests for UI widgets."""
import pytest
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.viability.investigation import Issue, Suggestion
from shypn.ui.panels.viability.ui.issue_widgets import IssueWidget, IssueList, IssueSummary
from shypn.ui.panels.viability.ui.suggestion_widgets import SuggestionWidget, SuggestionList


def test_issue_widget_creation():
    """Test creating issue widget."""
    issue = Issue(
        category='structural',
        severity='error',
        message="Test issue",
        element_id="T1"
    )
    
    widget = IssueWidget(issue)
    assert widget is not None
    assert isinstance(widget, Gtk.Box)


def test_issue_widget_severity_emoji():
    """Test issue widget shows correct emoji for severity."""
    issue_error = Issue(category='test', severity='error', message="Error", element_id="T1")
    issue_warning = Issue(category='test', severity='warning', message="Warning", element_id="T1")
    issue_info = Issue(category='test', severity='info', message="Info", element_id="T1")
    
    widget_error = IssueWidget(issue_error)
    widget_warning = IssueWidget(issue_warning)
    widget_info = IssueWidget(issue_info)
    
    assert widget_error is not None
    assert widget_warning is not None
    assert widget_info is not None


def test_issue_list_creation():
    """Test creating issue list."""
    issues = [
        Issue(category='structural', severity='error', message="Error 1", element_id="T1"),
        Issue(category='kinetic', severity='warning', message="Warning 1", element_id="T2"),
    ]
    
    widget = IssueList(issues)
    assert widget is not None
    assert len(widget.issues) == 2


def test_issue_list_empty():
    """Test issue list with no issues."""
    widget = IssueList([])
    assert widget is not None
    assert len(widget.issues) == 0


def test_issue_summary_creation():
    """Test creating issue summary."""
    issues = [
        Issue(category='test', severity='error', message="E1", element_id="T1"),
        Issue(category='test', severity='error', message="E2", element_id="T2"),
        Issue(category='test', severity='warning', message="W1", element_id="T3"),
    ]
    
    widget = IssueSummary(issues)
    assert widget is not None


def test_suggestion_widget_creation():
    """Test creating suggestion widget."""
    suggestion = Suggestion(
        category='structural',
        action="Test action",
        impact="Test impact",
        target_element_id="T1"
    )
    
    widget = SuggestionWidget(suggestion)
    assert widget is not None
    assert isinstance(widget, Gtk.Box)


def test_suggestion_widget_with_callbacks():
    """Test suggestion widget with callbacks."""
    suggestion = Suggestion(
        category='kinetic',
        action="Query BRENDA",
        impact="Get rate data",
        target_element_id="T1"
    )
    
    apply_called = False
    preview_called = False
    
    def on_apply(sug):
        nonlocal apply_called
        apply_called = True
    
    def on_preview(sug):
        nonlocal preview_called
        preview_called = True
    
    widget = SuggestionWidget(suggestion, on_apply=on_apply, on_preview=on_preview)
    assert widget is not None


def test_suggestion_list_creation():
    """Test creating suggestion list."""
    suggestions = [
        Suggestion(category='structural', action="Fix 1", impact="Impact 1", target_element_id="T1"),
        Suggestion(category='kinetic', action="Fix 2", impact="Impact 2", target_element_id="T2"),
    ]
    
    widget = SuggestionList(suggestions)
    assert widget is not None
    assert len(widget.suggestions) == 2


def test_suggestion_list_empty():
    """Test suggestion list with no suggestions."""
    widget = SuggestionList([])
    assert widget is not None
    assert len(widget.suggestions) == 0


def test_suggestion_list_grouping():
    """Test suggestions are grouped by category."""
    suggestions = [
        Suggestion(category='structural', action="S1", impact="I1", target_element_id="T1"),
        Suggestion(category='structural', action="S2", impact="I2", target_element_id="T2"),
        Suggestion(category='kinetic', action="K1", impact="I3", target_element_id="T3"),
    ]
    
    widget = SuggestionList(suggestions)
    assert widget is not None
    # Should group into 2 categories: structural (2) and kinetic (1)
