#!/usr/bin/env python3
"""Biological Inference Category.

Provides biochemical semantic inference using:
- KEGG compound metadata
- KEGG reaction metadata
- Stoichiometry from reactions
- Conservation laws (P-invariants)

Suggests:
- Arc weights (stoichiometry)
- Compound mappings
- Conservation law compliance
- Basal concentrations

Author: Simão Eugénio
Date: November 10, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseViabilityCategory
from .viability_dataclasses import Issue, Suggestion


class BiologicalCategory(BaseViabilityCategory):
    """Biological inference category.
    
    Uses KEGG metadata to suggest semantic fixes.
    """
    
    def get_category_name(self):
        """Get category display name.
        
        Returns:
            str: Category name
        """
        return "BIOLOGICAL INFERENCE"
    
    def _get_place_activity_statistics(self):
        """Get place activity statistics from simulation data.
        
        Returns:
            dict: Statistics with keys:
                - active_places: Number of places that changed
                - inactive_places: List of places that never changed
        """
        kb = self.get_knowledge_base()
        stats = {
            'active_places': 0,
            'inactive_places': []
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
            
            # Check each place for activity
            for place_id in kb.places.keys():
                try:
                    # Get token history
                    times, tokens = data_collector.get_place_data(place_id)
                    if len(tokens) > 0:
                        # Check if tokens changed
                        initial = tokens[0]
                        changed = any(t != initial for t in tokens)
                        
                        if changed:
                            stats['active_places'] += 1
                        else:
                            stats['inactive_places'].append(place_id)
                except:
                    pass
            
            print(f"[Biological] Place activity: {stats['active_places']} active, "
                  f"{len(stats['inactive_places'])} inactive")
            return stats
            
        except Exception as e:
            print(f"[Biological] Error getting place activity: {e}")
            return stats
    
    def _build_content(self):
        """Build biological category content."""
        # Status section
        status_frame = Gtk.Frame(label="CURRENT STATUS")
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box.set_margin_start(12)
        status_box.set_margin_end(12)
        status_box.set_margin_top(12)
        status_box.set_margin_bottom(12)
        
        self.status_label = Gtk.Label(label="Expand category to scan for biological issues...")
        self.status_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.status_label, False, False, 0)
        
        status_frame.add(status_box)
        self.content_box.pack_start(status_frame, False, False, 0)
        
        # Action buttons
        button_box = self._create_action_buttons()
        # Customize scan button label
        self.scan_button.set_label("SCAN SEMANTICS")
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
        """Scan for biological/semantic issues using multiple data sources.
        
        Intelligent multi-source analysis:
        1. KB compounds and reactions (KEGG metadata)
        2. Simulation data (places that never changed)
        3. Stoichiometry validation
        
        Returns:
            List[Issue]: Detected biological issues
        """
        kb = self.get_knowledge_base()
        if not kb:
            print("[Biological] No knowledge base available")
            return []
        
        issues = []
        
        # Get simulation data
        sim_stats = self._get_place_activity_statistics()
        
        # Update status
        self.status_label.set_markup(
            f"<b>Data Sources:</b>\n"
            f"  • KB compounds: {len(kb.compounds)}\n"
            f"  • KB reactions: {len(kb.reactions)}\n"
            f"  • Simulation: {sim_stats['active_places']} / {len(kb.places)} active places\n"
            f"  • Pathway: {kb.pathway_info.name if kb.pathway_info else 'None'}"
        )
        
        # ISSUE 1: Unmapped compounds (KB-based)
        unmapped_places = [p_id for p_id, p in kb.places.items() if p.compound_id is None]
        if unmapped_places:
            issue = Issue(
                id="unmapped_compounds",
                category="biological",
                severity="info",
                title=f"{len(unmapped_places)} places without compound mapping",
                description="These places are not linked to biological compounds (KEGG)",
                element_id="unmapped_compounds",
                element_type="place",
                locality_id=self.selected_locality_id
            )
            issues.append(issue)
        
        # ISSUE 2: Inactive places (simulation-based)
        if sim_stats['inactive_places']:
            issue = Issue(
                id="inactive_places",
                category="biological",
                severity="info",
                title=f"{len(sim_stats['inactive_places'])} compounds never changed in simulation",
                description="These places maintained constant token count (may be isolated)",
                element_id="inactive_places",
                element_type="place",
                locality_id=self.selected_locality_id
            )
            issues.append(issue)
        
        # ISSUE 3: Stoichiometry mismatches (KB-based)
        for arc_id, arc in list(kb.arcs.items())[:10]:  # Limit to 10
            if arc.stoichiometry and arc.current_weight != arc.stoichiometry:
                issue = Issue(
                    id=f"stoich_{arc_id}",
                    category="biological",
                    severity="warning",
                    title=f"Stoichiometry mismatch: {arc_id}",
                    description=f"Arc weight ({arc.current_weight}) differs from reaction stoichiometry ({arc.stoichiometry})",
                    element_id=arc_id,
                    element_type="arc",
                    locality_id=self.selected_locality_id
                )
                
                # Suggest fixing the arc weight
                suggestion = Suggestion(
                    action="add_arc_weight",
                    category="biological",
                    parameters={'weight': arc.stoichiometry},
                    confidence=0.9,
                    reasoning=f"Update arc weight to match stoichiometry: {arc.stoichiometry}",
                    preview_elements=[arc_id]
                )
                issue.suggestions = [suggestion]
                issues.append(issue)
        
        print(f"[Biological] Found {len(issues)} issues")
        return issues
    
    def _refresh(self):
        """Refresh biological category content.
        
        Returns:
            False: To stop GLib.idle_add from repeating
        """
        # Re-scan issues if category is expanded
        if self.expander.get_expanded():
            self._on_scan_clicked(None)
        return False
