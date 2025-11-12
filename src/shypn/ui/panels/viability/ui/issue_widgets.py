"""Widgets for displaying analysis issues."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from typing import List, Optional
from shypn.ui.panels.viability.investigation import Issue


class IssueWidget(Gtk.Box):
    """Widget for displaying a single issue.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ 🔴 Transition T1 never fired during simulation          │
    │    Category: kinetic | Element: T1                      │
    │    Details: No enabling conditions met                  │
    └─────────────────────────────────────────────────────────┘
    """
    
    SEVERITY_EMOJIS = {
        'error': '🔴',
        'warning': '🟡',
        'info': '🟢'
    }
    
    SEVERITY_CSS_CLASSES = {
        'error': 'issue-error',
        'warning': 'issue-warning',
        'info': 'issue-info'
    }
    
    def __init__(self, issue: Issue, expandable: bool = True):
        """Initialize issue widget.
        
        Args:
            issue: The issue to display
            expandable: Whether details are expandable
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        self.issue = issue
        self.expandable = expandable
        
        # Add CSS classes
        severity_class = self.SEVERITY_CSS_CLASSES.get(issue.severity, 'issue-info')
        self.get_style_context().add_class('issue-widget')
        self.get_style_context().add_class(severity_class)
        
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the widget UI."""
        # Main message row
        message_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        # Severity emoji
        emoji = self.SEVERITY_EMOJIS.get(self.issue.severity, '🟢')
        emoji_label = Gtk.Label(label=emoji)
        message_box.pack_start(emoji_label, False, False, 0)
        
        # Message text
        message_label = Gtk.Label(label=self.issue.message)
        message_label.set_line_wrap(True)
        message_label.set_max_width_chars(70)
        message_label.set_xalign(0)
        message_box.pack_start(message_label, True, True, 0)
        
        self.pack_start(message_box, False, False, 0)
        
        # Metadata row (category and element)
        meta_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        meta_box.set_margin_start(24)  # Indent under emoji
        
        category_label = Gtk.Label(label=f"Category: {self.issue.category}")
        category_label.set_xalign(0)
        category_label.get_style_context().add_class('dim-label')
        meta_box.pack_start(category_label, False, False, 0)
        
        if self.issue.element_id:
            element_label = Gtk.Label(label=f"Element: {self.issue.element_id}")
            element_label.set_xalign(0)
            element_label.get_style_context().add_class('dim-label')
            meta_box.pack_start(element_label, False, False, 0)
        
        self.pack_start(meta_box, False, False, 0)
        
        # Details (if present)
        if self.issue.details and self.expandable:
            details_expander = Gtk.Expander(label="Details")
            details_expander.set_margin_start(24)
            
            details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            details_box.set_margin_start(8)
            
            for key, value in self.issue.details.items():
                detail_label = Gtk.Label(label=f"{key}: {value}")
                detail_label.set_xalign(0)
                detail_label.set_line_wrap(True)
                detail_label.set_max_width_chars(60)
                detail_label.get_style_context().add_class('dim-label')
                details_box.pack_start(detail_label, False, False, 0)
            
            details_expander.add(details_box)
            self.pack_start(details_expander, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(4)
        self.pack_start(separator, False, False, 0)


class IssueList(Gtk.Box):
    """Scrollable list of issues grouped by severity.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ Issues (8)                              [Filter: All ▼] │
    ├─────────────────────────────────────────────────────────┤
    │ ▼ Errors (3)                                            │
    │   🔴 Transition T1 never fired...                       │
    │   🔴 Missing input arc for T2...                        │
    │                                                          │
    │ ▼ Warnings (5)                                          │
    │   🟡 Low firing rate for T3...                          │
    │   🟡 Unmapped compound C00001...                        │
    │                                                          │
    │ ▼ Info (0)                                              │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, issues: List[Issue] = None):
        """Initialize issue list.
        
        Args:
            issues: List of issues to display
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.issues = issues or []
        self.filter_severity = None  # None = show all
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the widget UI."""
        # Header with count and filter
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.set_margin_start(8)
        header.set_margin_end(8)
        header.set_margin_top(8)
        header.set_margin_bottom(8)
        
        filtered_issues = self._get_filtered_issues()
        title_label = Gtk.Label(label=f"Issues ({len(filtered_issues)})")
        title_label.set_xalign(0)
        title_label.get_style_context().add_class('title')
        header.pack_start(title_label, True, True, 0)
        
        # Filter dropdown
        filter_combo = Gtk.ComboBoxText()
        filter_combo.append("all", "All")
        filter_combo.append("error", "Errors")
        filter_combo.append("warning", "Warnings")
        filter_combo.append("info", "Info")
        filter_combo.set_active_id("all")
        filter_combo.connect('changed', self._on_filter_changed)
        header.pack_end(filter_combo, False, False, 0)
        
        self.pack_start(header, False, False, 0)
        
        # Scrolled window for issues
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        # Container for grouped issues
        self.issues_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._populate_issues()
        
        scrolled.add(self.issues_container)
        self.pack_start(scrolled, True, True, 0)
    
    def _get_filtered_issues(self) -> List[Issue]:
        """Get issues filtered by severity."""
        if self.filter_severity is None:
            return self.issues
        return [issue for issue in self.issues if issue.severity == self.filter_severity]
    
    def _populate_issues(self):
        """Populate issues grouped by severity."""
        # Clear existing
        for child in self.issues_container.get_children():
            self.issues_container.remove(child)
        
        filtered_issues = self._get_filtered_issues()
        
        # Group by severity
        from collections import defaultdict
        grouped = defaultdict(list)
        for issue in filtered_issues:
            grouped[issue.severity].append(issue)
        
        # Display in severity order: error > warning > info
        severity_order = ['error', 'warning', 'info']
        for severity in severity_order:
            if severity in grouped:
                expander = self._create_severity_expander(severity, grouped[severity])
                self.issues_container.pack_start(expander, False, False, 0)
        
        self.issues_container.show_all()
    
    def _create_severity_expander(self, severity: str, issues: List[Issue]) -> Gtk.Expander:
        """Create expander for a severity group."""
        expander = Gtk.Expander()
        expander.set_label(f"{severity.capitalize()} ({len(issues)})")
        expander.set_expanded(severity == 'error')  # Expand errors by default
        expander.set_margin_start(8)
        expander.set_margin_end(8)
        expander.set_margin_top(4)
        expander.set_margin_bottom(4)
        
        # Container for issues in this severity
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_start(12)
        
        for issue in issues:
            widget = IssueWidget(issue, expandable=True)
            box.pack_start(widget, False, False, 0)
        
        expander.add(box)
        return expander
    
    def _on_filter_changed(self, combo):
        """Handle filter dropdown change."""
        active_id = combo.get_active_id()
        if active_id == "all":
            self.filter_severity = None
        else:
            self.filter_severity = active_id
        
        # Repopulate with new filter
        self._populate_issues()
        
        # Update count in header
        filtered_issues = self._get_filtered_issues()
        for child in self.get_children():
            if isinstance(child, Gtk.Box):
                for subchild in child.get_children():
                    if isinstance(subchild, Gtk.Label):
                        subchild.set_text(f"Issues ({len(filtered_issues)})")
                        break
                break
    
    def update_issues(self, issues: List[Issue]):
        """Update the displayed issues.
        
        Args:
            issues: New list of issues
        """
        self.issues = issues
        self._populate_issues()
        
        # Update header count
        filtered_issues = self._get_filtered_issues()
        for child in self.get_children():
            if isinstance(child, Gtk.Box):
                for subchild in child.get_children():
                    if isinstance(subchild, Gtk.Label):
                        subchild.set_text(f"Issues ({len(filtered_issues)})")
                        break
                break


class IssueSummary(Gtk.Box):
    """Compact summary of issues by severity.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ 🔴 3 errors    🟡 5 warnings    🟢 2 info               │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, issues: List[Issue]):
        """Initialize issue summary.
        
        Args:
            issues: List of issues to summarize
        """
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        
        self.issues = issues
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the widget UI."""
        # Count by severity
        counts = {'error': 0, 'warning': 0, 'info': 0}
        for issue in self.issues:
            counts[issue.severity] = counts.get(issue.severity, 0) + 1
        
        # Display each severity count
        for severity in ['error', 'warning', 'info']:
            count = counts[severity]
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            
            emoji = IssueWidget.SEVERITY_EMOJIS.get(severity, '🟢')
            emoji_label = Gtk.Label(label=emoji)
            box.pack_start(emoji_label, False, False, 0)
            
            text = f"{count} {severity}{'s' if count != 1 else ''}"
            label = Gtk.Label(label=text)
            label.set_xalign(0)
            
            # Dim if count is 0
            if count == 0:
                label.get_style_context().add_class('dim-label')
            
            box.pack_start(label, False, False, 0)
            self.pack_start(box, False, False, 0)
