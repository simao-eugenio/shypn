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
        """Scan for biological/semantic issues.
        
        Returns:
            List[Issue]: Detected biological issues
        """
        kb = self.get_knowledge_base()
        if not kb:
            print("[Biological] No knowledge base available")
            return []
        
        issues = []
        
        # Update status
        self.status_label.set_markup(
            f"<b>KB Status:</b>\n"
            f"  • Compounds: {len(kb.compounds)}\n"
            f"  • Reactions: {len(kb.reactions)}\n"
            f"  • Pathway: {kb.pathway_info.name if kb.pathway_info else 'None'}"
        )
        
        # Scan for unmapped compounds
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
        
        # Scan for stoichiometry mismatches
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
