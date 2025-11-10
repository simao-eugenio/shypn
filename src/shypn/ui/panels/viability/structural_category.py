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
from .viability_dataclasses import Issue, Suggestion


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
        for trans_id in dead_transitions[:10]:  # Limit to 10
            trans = kb.transitions.get(trans_id)
            if trans:
                # Create Issue dataclass
                issue = Issue(
                    id=f"dead_{trans_id}",
                    category="structural",
                    severity="critical",
                    title=f"Transition {trans_id} is DEAD",
                    description="Cannot fire due to missing input tokens or structural issues",
                    element_id=trans_id,
                    element_type="transition",
                    locality_id=self.selected_locality_id
                )
                
                # Add suggestion to add tokens to input places
                input_places = [arc.source_id for arc in kb.arcs.values() 
                               if arc.target_id == trans_id and arc.arc_type == "place_to_transition"]
                
                if input_places:
                    suggestion = Suggestion(
                        action="add_initial_marking",
                        category="structural",
                        parameters={'tokens': 5, 'place_id': input_places[0]},
                        confidence=0.7,
                        reasoning=f"Add tokens to input place {input_places[0]} to enable firing",
                        preview_elements=[input_places[0], trans_id]
                    )
                    issue.suggestions = [suggestion]
                
                issues.append(issue)
        
        # Scan for empty siphons
        for idx, siphon in enumerate(kb.siphons[:5]):  # Limit to 5
            if not siphon.is_properly_marked:
                issue = Issue(
                    id=f"siphon_{idx}",
                    category="structural",
                    severity="warning",
                    title=f"Empty siphon detected (#{idx})",
                    description=f"Siphon with {len(siphon.place_ids)} places lacks initial marking",
                    element_id=f"siphon_{idx}",
                    element_type="siphon",
                    locality_id=self.selected_locality_id
                )
                
                # Suggest adding tokens to one of the siphon places
                if siphon.place_ids:
                    place_id = list(siphon.place_ids)[0]
                    suggestion = Suggestion(
                        action="add_initial_marking",
                        category="structural",
                        parameters={'tokens': 3, 'place_id': place_id},
                        confidence=0.8,
                        reasoning=f"Add tokens to {place_id} to prevent deadlock",
                        preview_elements=list(siphon.place_ids)
                    )
                    issue.suggestions = [suggestion]
                
                issues.append(issue)
        
        print(f"[Structural] Found {len(issues)} issues")
        return issues
