#!/usr/bin/env python3
"""Kinetic Inference Category.

Provides kinetic parameter inference using:
- BRENDA database (Km, Kcat, Vmax)
- SABIO-RK database (rate laws)
- EC numbers from KEGG
- Enzyme kinetics literature

Suggests:
- Firing rates (based on Vmax, Kcat)
- Km values for substrates
- Inhibition parameters
- Rate law equations

Author: Simão Eugénio
Date: November 10, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseViabilityCategory
from .viability_dataclasses import Issue, Suggestion


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
        status_frame = Gtk.Frame(label="CURRENT STATUS")
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box.set_margin_start(12)
        status_box.set_margin_end(12)
        status_box.set_margin_top(12)
        status_box.set_margin_bottom(12)
        
        self.status_label = Gtk.Label(label="Expand category to scan for kinetic issues...")
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
        missing_rate_trans = []
        for trans_id, trans in kb.transitions.items():
            if trans.current_rate is None and trans_id not in kb.kinetic_parameters:
                missing_rate_trans.append(trans_id)
        
        if missing_rate_trans:
            issue = Issue(
                id="missing_rates",
                category="kinetic",
                severity='warning' if coverage_pct > 50 else 'critical',
                title=f"{len(missing_rate_trans)} transitions without firing rates",
                description=f"Cannot run quantitative simulation (coverage: {coverage_pct:.0f}%)",
                element_id="missing_rates",
                element_type="transition",
                locality_id=self.selected_locality_id
            )
            
            # Add suggestion to use default rate for first transition
            if missing_rate_trans:
                suggestion = Suggestion(
                    action="add_firing_rate",
                    category="kinetic",
                    parameters={'rate': 1.0},
                    confidence=0.3,
                    reasoning="Use default firing rate of 1.0 (requires BRENDA query for accuracy)",
                    preview_elements=missing_rate_trans[:5]  # Preview first 5
                )
                issue.suggestions = [suggestion]
            
            issues.append(issue)
        
        # Scan for low confidence parameters
        low_confidence_trans = []
        for trans_id, params in kb.kinetic_parameters.items():
            if params.confidence < 0.5:
                low_confidence_trans.append(trans_id)
        
        if low_confidence_trans:
            issue = Issue(
                id="low_confidence_rates",
                category="kinetic",
                severity="info",
                title=f"{len(low_confidence_trans)} transitions have low confidence rates",
                description="Consider querying BRENDA/SABIO-RK for better parameters",
                element_id="low_confidence_rates",
                element_type="transition",
                locality_id=self.selected_locality_id
            )
            issues.append(issue)
        
        print(f"[Kinetic] Found {len(issues)} issues")
        return issues
    
    def _refresh(self):
        """Refresh kinetic category content.
        
        Returns:
            False: To stop GLib.idle_add from repeating
        """
        # Re-scan issues if category is expanded
        if self.expander.get_expanded():
            self._on_scan_clicked(None)
        return False
