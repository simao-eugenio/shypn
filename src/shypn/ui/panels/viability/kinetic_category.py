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
    
    def _get_simulation_statistics(self):
        """Get firing statistics from simulation data.
        
        Returns:
            dict: Statistics with keys:
                - total_firings: Total number of firings
                - zero_firing: List of transitions that never fired
                - low_rate: List of transitions with < 1 firing per time unit
        """
        kb = self.get_knowledge_base()
        stats = {
            'total_firings': 0,
            'zero_firing': [],
            'low_rate': []
        }
        
        if not kb or not self.model_canvas:
            return stats
        
        try:
            # Get simulation data
            model_manager = getattr(self.model_canvas, 'model_manager', None)
            if not model_manager:
                return stats
            
            controller = getattr(model_manager, 'controller', None)
            if not controller:
                return stats
            
            data_collector = getattr(controller, 'data_collector', None)
            if not data_collector or not data_collector.has_data():
                return stats
            
            # Get duration
            duration = getattr(controller, 'time', 60.0)  # Default 60s
            
            # Analyze each transition
            for trans_id in kb.transitions.keys():
                firings = data_collector.get_total_firings(trans_id)
                stats['total_firings'] += firings
                
                if firings == 0:
                    stats['zero_firing'].append(trans_id)
                elif firings / duration < 1.0:
                    stats['low_rate'].append(trans_id)
            
            return stats
            
        except Exception as e:
            return stats
    
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
        
        # Issues table with TreeView
        issues_frame = Gtk.Frame(label="ISSUES DETECTED")
        issues_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create TreeView table with selection checkboxes
        scrolled, tree, store = self._create_issues_treeview()
        issues_vbox.pack_start(scrolled, True, True, 0)
        
        # Action buttons at bottom (like Heuristic panel)
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        action_box.set_margin_start(6)
        action_box.set_margin_end(6)
        action_box.set_margin_top(6)
        action_box.set_margin_bottom(6)
        
        self.repair_button = Gtk.Button(label="🔧 Repair Selected")
        self.repair_button.set_tooltip_text("Apply selected suggestions")
        self.repair_button.set_sensitive(False)
        self.repair_button.connect('clicked', self._on_repair_clicked)
        action_box.pack_start(self.repair_button, True, True, 0)
        
        issues_vbox.pack_start(action_box, False, False, 0)
        
        issues_frame.add(issues_vbox)
        self.content_box.pack_start(issues_frame, True, True, 0)
    
    def _scan_issues(self):
        """Scan for kinetic parameter issues using multiple data sources.
        
        Intelligent multi-source analysis:
        1. KB kinetic_parameters (BRENDA/database)
        2. Simulation data (actual firing rates)
        3. Zero-firing transitions (may need rate adjustments)
        
        Returns:
            List[Issue]: Detected kinetic issues
        """
        kb = self.get_knowledge_base()
        if not kb:
            return []
        
        issues = []
        
        # Count transitions with/without kinetics
        total_transitions = len(kb.transitions)
        transitions_with_kinetics = len(kb.kinetic_parameters)
        coverage_pct = (transitions_with_kinetics / total_transitions * 100) if total_transitions > 0 else 0
        
        # Get simulation data
        sim_stats = self._get_simulation_statistics()
        
        # Update status
        self.status_label.set_markup(
            f"<b>Data Sources:</b>\n"
            f"  • KB kinetics: {transitions_with_kinetics} / {total_transitions} ({coverage_pct:.0f}%)\n"
            f"  • Simulation: {sim_stats['total_firings']} firings recorded\n"
            f"  • Zero-firing: {len(sim_stats['zero_firing'])} transitions\n"
            f"  • Database: HeuristicDatabase (offline)"
        )
        
        # ISSUE 1: Transitions without rates (KB-based)
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
        
        # ISSUE 2: Transitions that never fired in simulation (simulation-based)
        if sim_stats['zero_firing']:
            issue = Issue(
                id="zero_firing_transitions",
                category="kinetic",
                severity="warning",
                title=f"{len(sim_stats['zero_firing'])} transitions never fired in simulation",
                description="May need rate increase, input tokens, or structural fixes",
                element_id="zero_firing",
                element_type="transition",
                locality_id=self.selected_locality_id
            )
            
            # Suggest rate increase for first zero-firing transition
            if sim_stats['zero_firing']:
                first_trans = sim_stats['zero_firing'][0]
                suggestion = Suggestion(
                    action="add_firing_rate",
                    category="kinetic",
                    parameters={'rate': 10.0},
                    confidence=0.4,
                    reasoning=f"Increase rate to enable firing (verify structural connectivity first)",
                    preview_elements=[first_trans]
                )
                issue.suggestions = [suggestion]
            
            issues.append(issue)
        
        # ISSUE 3: Low confidence parameters
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
