"""UI components for viability investigations.

This module contains GTK3 widgets for displaying investigation results,
including issues, suggestions, and interactive fix application.

All components are Wayland-safe (no X11 dependencies).
"""

from .suggestion_widgets import SuggestionWidget, SuggestionList, SuggestionAppliedBanner
from .issue_widgets import IssueWidget, IssueList, IssueSummary
from .investigation_view import InvestigationView, LocalityOverviewCard
from .subnet_view import SubnetView
from .topology_viewer import TopologyViewer, TopologyViewerWithLegend

__all__ = [
    'SuggestionWidget',
    'SuggestionList',
    'SuggestionAppliedBanner',
    'IssueWidget',
    'IssueList',
    'IssueSummary',
    'InvestigationView',
    'LocalityOverviewCard',
    'SubnetView',
    'TopologyViewer',
    'TopologyViewerWithLegend',
]
