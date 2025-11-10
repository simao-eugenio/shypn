#!/usr/bin/env python3
"""Kinetic Inference Category.

Provides kinetic parameter inference using:
- BRENDA database (Km, Vmax, Kcat)
- EC numbers
- HeuristicDatabase (local SQLite)
- SABIO-RK data

Suggests:
- Firing rates for transitions
- Rate estimation from Kcat
- Default mass action rates
- BRENDA query suggestions

Author: Simão Eugénio
Date: November 10, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseViabilityCategory


class KineticCategory(BaseViabilityCategory):
    """Kinetic inference category.
    
    Uses BRENDA data to suggest firing rates.
    """
    
    def get_category_name(self):
        """Get category display name.
        
        Returns:
            str: Category name
        """
        return "KINETIC INFERENCE"
    
    def _build_content(self):
        """Build kinetic category content."""
        # Status section
        status_frame = Gtk.Frame(label="CURRENT PARAMETERS")
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box.set_margin_start(12)
        status_box.set_margin_end(12)
        status_box.set_margin_top(12)
        status_box.set_margin_bottom(12)
        
        self.status_label = Gtk.Label(label="Click 'Scan Kinetics' to analyze")
        self.status_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.status_label, False, False, 0)
        
        status_frame.add(status_box)
        self.content_box.pack_start(status_frame, False, False, 0)
        
        # Action buttons
        button_box = self._create_action_buttons()
        # Customize scan button label
        self.scan_button.set_label("SCAN KINETICS")
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
        """Scan for kinetic parameter issues.
        
        Returns:
            List[Issue]: Detected kinetic issues
        """
        kb = self.get_knowledge_base()
        if not kb:
            print("[Kinetic] No knowledge base available")
            return []
        
        issues = []
        
        # Count transitions with/without kinetics
        total_transitions = len(kb.transitions)
        transitions_with_kinetics = len(kb.kinetic_parameters)
        coverage_pct = (transitions_with_kinetics / total_transitions * 100) if total_transitions > 0 else 0
        
        # Update status
        self.status_label.set_markup(
            f"<b>KB Status:</b>\n"
            f"  • Transitions with kinetics: {transitions_with_kinetics} / {total_transitions}\n"
            f"  • Coverage: {coverage_pct:.0f}%\n"
            f"  • Database: HeuristicDatabase (offline)"
        )
        
        # Scan for transitions without rates
        missing_rate_count = 0
        for trans_id, trans in kb.transitions.items():
            if trans.current_rate is None and trans_id not in kb.kinetic_parameters:
                missing_rate_count += 1
        
        if missing_rate_count > 0:
            issues.append({
                'severity': 'warning' if coverage_pct > 50 else 'critical',
                'title': f'{missing_rate_count} transitions without firing rates',
                'description': f'Cannot run quantitative simulation (coverage: {coverage_pct:.0f}%)',
                'element_id': 'missing_rates',
                'suggestions': []
            })
        
        # Scan for low confidence parameters
        low_confidence_count = 0
        for trans_id, params in kb.kinetic_parameters.items():
            if params.confidence < 0.5:
                low_confidence_count += 1
        
        if low_confidence_count > 0:
            issues.append({
                'severity': 'suggestion',
                'title': f'{low_confidence_count} transitions have low confidence rates',
                'description': 'Consider querying BRENDA for better parameters',
                'element_id': 'low_confidence_rates',
                'suggestions': []
            })
        
        return issues
    
    def _display_issues(self, issues):
        """Display kinetic issues in the UI.
        
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
        
        row.add(box)
        return row
    
    def _refresh(self):
        """Refresh kinetic category content.
        
        Returns:
            False: To stop GLib.idle_add from repeating
        """
        # Re-scan issues if category is expanded
        if self.expander.get_expanded():
            self._on_scan_clicked(None)
        return False
