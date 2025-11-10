#!/usr/bin/env python3
"""Diagnosis View - Display model issues in tree view.

Shows issues categorized by severity (Critical/Warning/Info).

Author: Simão Eugénio
Date: November 9, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class DiagnosisView(Gtk.ScrolledWindow):
    """Tree view displaying model viability issues.
    
    Organizes issues by severity:
    - 🔴 Critical (must fix)
    - 🟡 Warning (should review)
    - 🟢 Info (suggestions)
    """
    
    def __init__(self):
        """Initialize diagnosis view."""
        super().__init__()
        
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.set_size_request(-1, 300)
        
        # Create tree store: icon, severity, type, description, id
        self.store = Gtk.TreeStore(str, str, str, str, str)
        
        # Create tree view
        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_headers_visible(True)
        
        # Column 1: Icon + Description
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Issue", renderer_text, text=0)
        column.add_attribute(renderer_text, "text", 3)  # Description
        self.tree_view.append_column(column)
        
        # Column 2: Type
        renderer_type = Gtk.CellRendererText()
        column_type = Gtk.TreeViewColumn("Type", renderer_type, text=2)
        self.tree_view.append_column(column_type)
        
        self.add(self.tree_view)
    
    def display_issues(self, issues):
        """Display list of issues in tree view.
        
        Args:
            issues: List of dicts with keys: severity, type, description, id
        """
        self.clear()
        
        if not issues:
            # No issues found
            self.store.append(None, [
                '✓',
                'info',
                'viable',
                'No issues detected - model is viable',
                'none'
            ])
            return
        
        # Group by severity
        critical = [i for i in issues if i['severity'] == 'critical']
        warnings = [i for i in issues if i['severity'] == 'warning']
        info = [i for i in issues if i['severity'] == 'info']
        
        # Add critical issues
        if critical:
            critical_parent = self.store.append(None, [
                '🔴',
                'critical',
                'category',
                f'Critical Issues ({len(critical)})',
                'critical_cat'
            ])
            for issue in critical:
                self.store.append(critical_parent, [
                    '  🔴',
                    issue['severity'],
                    issue['type'],
                    issue['description'],
                    issue['id']
                ])
        
        # Add warnings
        if warnings:
            warning_parent = self.store.append(None, [
                '🟡',
                'warning',
                'category',
                f'Warnings ({len(warnings)})',
                'warning_cat'
            ])
            for issue in warnings:
                self.store.append(warning_parent, [
                    '  🟡',
                    issue['severity'],
                    issue['type'],
                    issue['description'],
                    issue['id']
                ])
        
        # Add info
        if info:
            info_parent = self.store.append(None, [
                '🟢',
                'info',
                'category',
                f'Information ({len(info)})',
                'info_cat'
            ])
            for issue in info:
                self.store.append(info_parent, [
                    '  🟢',
                    issue['severity'],
                    issue['type'],
                    issue['description'],
                    issue['id']
                ])
        
        # Expand all by default
        self.tree_view.expand_all()
    
    def clear(self):
        """Clear all issues from view."""
        self.store.clear()
    
    def get_issue_count(self):
        """Get total number of issues (excluding category headers).
        
        Returns:
            int: Number of issues
        """
        count = 0
        def count_children(model, path, iter, data):
            # Only count leaf nodes (issues, not categories)
            if not model.iter_has_child(iter):
                data[0] += 1
        
        data = [0]
        self.store.foreach(count_children, data)
        return data[0]
