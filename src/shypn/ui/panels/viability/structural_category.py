#!/usr/bin/env python3
"""Structural Inference Category.

Provides topology-based inference using:
- P-invariants (conservation laws)
- T-invariants (firing sequences)
- Siphons and traps (deadlock analysis)
- Liveness levels (dead transitions)

Suggests:
- Initial marking (tokens to add)
- Source transitions (for empty siphons)
- Structural fixes (enable dead transitions)

Author: Simão Eugénio
Date: November 10, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseViabilityCategory


class StructuralCategory(BaseViabilityCategory):
    """Structural inference category.
    
    Uses topology analysis (P-invariants, liveness, siphons)
    to suggest structural fixes.
    """
    
    def get_category_name(self):
        """Get category display name.
        
        Returns:
            str: Category name
        """
        return "STRUCTURAL INFERENCE"
    
    def _build_content(self):
        """Build structural category content."""
        # Status section
        status_frame = Gtk.Frame(label="CURRENT STATUS")
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box.set_margin_start(12)
        status_box.set_margin_end(12)
        status_box.set_margin_top(12)
        status_box.set_margin_bottom(12)
        
        self.status_label = Gtk.Label(label="Click 'Scan for Issues' to analyze")
        self.status_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.status_label, False, False, 0)
        
        status_frame.add(status_box)
        self.content_box.pack_start(status_frame, False, False, 0)
        
        # Action buttons
        button_box = self._create_action_buttons()
        self.content_box.pack_start(button_box, False, False, 0)
        
        # Issues list
        issues_frame = Gtk.Frame(label="ISSUES DETECTED")
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        self.issues_listbox = Gtk.ListBox()
        self.issues_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.add(self.issues_listbox)
        
        issues_frame.add(scrolled)
        self.content_box.pack_start(issues_frame, True, True, 0)
    
    def _scan_issues(self):
        """Scan for structural issues.
        
        Returns:
            List[Issue]: Detected structural issues
        """
        kb = self.get_knowledge_base()
        if not kb:
            print("[Structural] No knowledge base available")
            return []
        
        issues = []
        
        # Update status
        self.status_label.set_markup(
            f"<b>KB Status:</b>\n"
            f"  • P-invariants: {len(kb.p_invariants)}\n"
            f"  • T-invariants: {len(kb.t_invariants)}\n"
            f"  • Siphons: {len(kb.siphons)}\n"
            f"  • Dead transitions: {len(kb.get_dead_transitions())}"
        )
        
        # Scan for dead transitions
        dead_transitions = kb.get_dead_transitions()
        for trans_id in dead_transitions:
            trans = kb.transitions.get(trans_id)
            if trans:
                # Create issue (simplified for now)
                issues.append({
                    'severity': 'critical',
                    'title': f'Transition {trans_id} is DEAD',
                    'description': f'Cannot fire due to missing input tokens',
                    'element_id': trans_id,
                    'suggestions': []  # Will be populated by inference methods
                })
        
        # Scan for empty siphons
        for idx, siphon in enumerate(kb.siphons):
            if not siphon.is_properly_marked:
                issues.append({
                    'severity': 'warning',
                    'title': f'Empty siphon detected',
                    'description': f'Siphon {idx} with {len(siphon.place_ids)} places',
                    'element_id': f'siphon_{idx}',
                    'suggestions': []
                })
        
        return issues
    
    def _display_issues(self, issues):
        """Display structural issues in the UI.
        
        Args:
            issues: List of issue dictionaries
        """
        # Clear existing issues
        for child in self.issues_listbox.get_children():
            self.issues_listbox.remove(child)
        
        if not issues:
            self._show_no_issues_message()
            return
        
        # Add each issue as a row
        for issue in issues:
            row = self._create_issue_row(issue)
            self.issues_listbox.add(row)
        
        self.issues_listbox.show_all()
    
    def _create_issue_row(self, issue):
        """Create a row widget for an issue.
        
        Args:
            issue: Issue dictionary
            
        Returns:
            Gtk.ListBoxRow: Row widget
        """
        row = Gtk.ListBoxRow()
        row.set_selectable(False)
        
        # Main box
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Title with severity icon
        severity_icons = {
            'critical': '🔴',
            'warning': '⚠️',
            'suggestion': '💡'
        }
        icon = severity_icons.get(issue['severity'], '•')
        
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{icon} {issue['title']}</b>")
        title_label.set_halign(Gtk.Align.START)
        box.pack_start(title_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label(label=issue['description'])
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_line_wrap(True)
        box.pack_start(desc_label, False, False, 0)
        
        # Suggestions (if any)
        if issue.get('suggestions'):
            for suggestion in issue['suggestions']:
                suggestion_box = self._create_suggestion_widget(suggestion)
                box.pack_start(suggestion_box, False, False, 0)
        
        row.add(box)
        return row
    
    def _create_suggestion_widget(self, suggestion):
        """Create a widget for a suggestion.
        
        Args:
            suggestion: Suggestion dictionary
            
        Returns:
            Gtk.Box: Suggestion widget
        """
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_margin_start(24)
        
        # Suggestion text
        label = Gtk.Label(label=f"→ {suggestion.get('reasoning', 'No details')}")
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        box.pack_start(label, True, True, 0)
        
        # Apply button
        apply_button = Gtk.Button(label="Apply")
        apply_button.connect('clicked', self._on_apply_suggestion, suggestion)
        box.pack_start(apply_button, False, False, 0)
        
        return box
    
    def _on_apply_suggestion(self, button, suggestion):
        """Handle applying a suggestion.
        
        Args:
            button: Button that was clicked
            suggestion: Suggestion dictionary
        """
        print(f"[Structural] Applying suggestion: {suggestion}")
        # TODO: Implement actual application logic
    
    def _refresh(self):
        """Refresh structural category content.
        
        Returns:
            False: To stop GLib.idle_add from repeating
        """
        # Re-scan issues if category is expanded
        if self.expander.get_expanded():
            self._on_scan_clicked(None)
        return False
