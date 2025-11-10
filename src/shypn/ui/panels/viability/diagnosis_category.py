#!/usr/bin/env python3
"""Diagnosis & Repair Category.

Provides multi-domain diagnosis with locality awareness:
- Combines structural + biological + kinetic knowledge
- Supports locality filtering for focused analysis
- Shows health scores across domains
- Provides multi-domain suggestions (all perspectives at once)
- Batch operations ("Fix All")

This is the main/primary category that integrates all others.

Author: Simão Eugénio
Date: November 10, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseViabilityCategory


class DiagnosisCategory(BaseViabilityCategory):
    """Diagnosis & repair category with locality support.
    
    Main category that provides:
    - Full model or locality-focused diagnosis
    - Multi-domain issue analysis
    - Boundary analysis for localities
    - Health score calculation
    - Batch operations
    """
    
    def __init__(self, model_canvas=None, expanded=False):
        """Initialize diagnosis category.
        
        Args:
            model_canvas: ModelCanvas instance
            expanded: Whether to start expanded
        """
        super().__init__(model_canvas, expanded)
        self.analyses_panel = None  # For locality access
    
    def get_category_name(self):
        """Get category display name.
        
        Returns:
            str: Category name
        """
        return "DIAGNOSIS & REPAIR"
    
    def _build_content(self):
        """Build diagnosis category content."""
        # Locality selection
        locality_frame = Gtk.Frame(label="DIAGNOSIS SCOPE")
        locality_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        locality_box.set_margin_start(12)
        locality_box.set_margin_end(12)
        locality_box.set_margin_top(12)
        locality_box.set_margin_bottom(12)
        
        # Radio buttons for scope
        self.full_model_radio = Gtk.RadioButton.new_with_label_from_widget(
            None, "Full Model"
        )
        self.full_model_radio.set_active(True)
        self.full_model_radio.connect('toggled', self._on_scope_changed)
        locality_box.pack_start(self.full_model_radio, False, False, 0)
        
        self.locality_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.full_model_radio, "Selected Locality:"
        )
        self.locality_radio.connect('toggled', self._on_scope_changed)
        locality_box.pack_start(self.locality_radio, False, False, 0)
        
        # Locality dropdown (indented)
        locality_dropdown_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        locality_dropdown_box.set_margin_start(24)
        
        self.locality_combo = Gtk.ComboBoxText()
        self.locality_combo.append_text("(No localities available)")
        self.locality_combo.set_active(0)
        self.locality_combo.set_sensitive(False)
        self.locality_combo.connect('changed', self._on_locality_selected)
        locality_dropdown_box.pack_start(self.locality_combo, True, True, 0)
        
        manage_button = Gtk.Button(label="Manage Localities")
        manage_button.set_sensitive(False)
        locality_dropdown_box.pack_start(manage_button, False, False, 0)
        
        locality_box.pack_start(locality_dropdown_box, False, False, 0)
        
        locality_frame.add(locality_box)
        self.content_box.pack_start(locality_frame, False, False, 0)
        
        # Health score section
        health_frame = Gtk.Frame(label="HEALTH SCORE")
        health_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        health_box.set_margin_start(12)
        health_box.set_margin_end(12)
        health_box.set_margin_top(12)
        health_box.set_margin_bottom(12)
        
        self.health_label = Gtk.Label(label="Run diagnosis to calculate health")
        self.health_label.set_halign(Gtk.Align.START)
        health_box.pack_start(self.health_label, False, False, 0)
        
        health_frame.add(health_box)
        self.content_box.pack_start(health_frame, False, False, 0)
        
        # Action buttons
        button_box = self._create_action_buttons()
        # Customize scan button label
        self.scan_button.set_label("RUN FULL DIAGNOSIS")
        
        # Add batch operation button
        batch_button = Gtk.Button(label="APPLY ALL FIXES")
        batch_button.set_tooltip_text("Apply all high-confidence suggestions (>70%)")
        batch_button.connect('clicked', self._on_apply_all_clicked)
        button_box.pack_start(batch_button, False, False, 0)
        
        self.content_box.pack_start(button_box, False, False, 0)
        
        # Issues list with multi-domain view
        issues_frame = Gtk.Frame(label="ISSUES DETECTED")
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        
        self.issues_listbox = Gtk.ListBox()
        self.issues_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.add(self.issues_listbox)
        
        issues_frame.add(scrolled)
        self.content_box.pack_start(issues_frame, True, True, 0)
    
    def _on_scope_changed(self, radio_button):
        """Handle scope radio button change.
        
        Args:
            radio_button: Radio button that was toggled
        """
        if self.locality_radio.get_active():
            self.locality_combo.set_sensitive(True)
            # Use selected locality
            if self.locality_combo.get_active() >= 0:
                # TODO: Get actual locality ID
                self.selected_locality_id = "locality_example"
        else:
            self.locality_combo.set_sensitive(False)
            self.selected_locality_id = None
    
    def _on_locality_selected(self, combo):
        """Handle locality selection change.
        
        Args:
            combo: ComboBox that changed
        """
        if combo.get_active() >= 0:
            # TODO: Get actual locality ID from combo
            self.selected_locality_id = "locality_example"
            print(f"[Diagnosis] Selected locality: {self.selected_locality_id}")
    
    def set_analyses_panel(self, analyses_panel):
        """Set reference to analyses panel for locality access.
        
        Args:
            analyses_panel: AnalysesPanel instance
        """
        self.analyses_panel = analyses_panel
        # TODO: Populate locality dropdown from analyses_panel
    
    def _scan_issues(self):
        """Scan for issues across all domains.
        
        Returns:
            List[Issue]: Detected issues from all categories
        """
        kb = self.get_knowledge_base()
        if not kb:
            print("[Diagnosis] No knowledge base available")
            return []
        
        issues = []
        
        # Calculate health scores
        structural_health = self._calculate_structural_health(kb)
        biological_health = self._calculate_biological_health(kb)
        kinetic_health = self._calculate_kinetic_health(kb)
        overall_health = (structural_health + biological_health + kinetic_health) / 3
        
        # Update health display
        self.health_label.set_markup(
            f"<b>Overall Health: {overall_health:.0f}%</b>\n\n"
            f"  Structural:  {self._health_bar(structural_health)} {structural_health:.0f}%\n"
            f"  Biological:  {self._health_bar(biological_health)} {biological_health:.0f}%\n"
            f"  Kinetic:     {self._health_bar(kinetic_health)} {kinetic_health:.0f}%"
        )
        
        # Scan for critical issues (multi-domain)
        dead_transitions = kb.get_dead_transitions()
        if dead_transitions:
            issues.append({
                'severity': 'critical',
                'title': f'{len(dead_transitions)} transitions are DEAD',
                'description': 'Blocks pathway execution',
                'element_id': 'dead_transitions',
                'multi_domain': True,
                'suggestions': {
                    'structural': [],
                    'biological': [],
                    'kinetic': []
                }
            })
        
        # Scan for kinetic coverage issues
        total_trans = len(kb.transitions)
        trans_with_kinetics = len(kb.kinetic_parameters)
        if trans_with_kinetics < total_trans * 0.5:  # Less than 50%
            issues.append({
                'severity': 'critical' if trans_with_kinetics < total_trans * 0.25 else 'warning',
                'title': 'Missing kinetic parameters',
                'description': f'{total_trans - trans_with_kinetics}/{total_trans} transitions have no rates',
                'element_id': 'missing_kinetics',
                'multi_domain': False
            })
        
        return issues
    
    def _calculate_structural_health(self, kb):
        """Calculate structural health score.
        
        Args:
            kb: Knowledge base
            
        Returns:
            float: Health percentage (0-100)
        """
        if not kb.transitions:
            return 100.0
        
        score = 100.0
        
        # Penalty for dead transitions
        dead_count = len(kb.get_dead_transitions())
        if dead_count > 0:
            score -= min(50, dead_count * 10)  # -10% per dead transition, max -50%
        
        # Bonus for P-invariants
        if kb.p_invariants:
            score = min(100, score + 10)
        
        return max(0, score)
    
    def _calculate_biological_health(self, kb):
        """Calculate biological health score.
        
        Args:
            kb: Knowledge base
            
        Returns:
            float: Health percentage (0-100)
        """
        if not kb.places:
            return 100.0
        
        # Coverage of compound mappings
        mapped_count = sum(1 for p in kb.places.values() if p.compound_id)
        coverage = (mapped_count / len(kb.places)) * 100
        
        return coverage
    
    def _calculate_kinetic_health(self, kb):
        """Calculate kinetic health score.
        
        Args:
            kb: Knowledge base
            
        Returns:
            float: Health percentage (0-100)
        """
        if not kb.transitions:
            return 100.0
        
        # Coverage of kinetic parameters
        coverage = (len(kb.kinetic_parameters) / len(kb.transitions)) * 100
        
        return coverage
    
    def _health_bar(self, percentage):
        """Create a text-based health bar.
        
        Args:
            percentage: Health percentage (0-100)
            
        Returns:
            str: Bar representation
        """
        filled = int(percentage / 10)
        empty = 10 - filled
        return '█' * filled + '░' * empty
    
    def _display_issues(self, issues):
        """Display issues in the UI.
        
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
        
        # Multi-domain suggestions (if available)
        if issue.get('multi_domain'):
            box.pack_start(self._create_multi_domain_widget(issue), False, False, 0)
        
        row.add(box)
        return row
    
    def _create_multi_domain_widget(self, issue):
        """Create multi-domain suggestions widget.
        
        Args:
            issue: Issue dictionary
            
        Returns:
            Gtk.Box: Widget showing all domain perspectives
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_top(6)
        
        label = Gtk.Label()
        label.set_markup("<b>Multi-Domain Suggestions:</b>")
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)
        
        # Show placeholders for now
        for domain in ['STRUCTURAL', 'BIOLOGICAL', 'KINETIC']:
            domain_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            domain_box.set_margin_start(12)
            
            domain_label = Gtk.Label(label=f"{domain}: (suggestions coming soon)")
            domain_label.set_halign(Gtk.Align.START)
            domain_box.pack_start(domain_label, True, True, 0)
            
            box.pack_start(domain_box, False, False, 0)
        
        return box
    
    def _on_apply_all_clicked(self, button):
        """Handle applying all fixes.
        
        Args:
            button: Button that was clicked
        """
        print("[Diagnosis] Apply All clicked - not implemented yet")
    
    def _refresh(self):
        """Refresh diagnosis category content.
        
        Returns:
            False: To stop GLib.idle_add from repeating
        """
        # Re-scan issues if category is expanded
        if self.expander.get_expanded():
            self._on_scan_clicked(None)
        return False
