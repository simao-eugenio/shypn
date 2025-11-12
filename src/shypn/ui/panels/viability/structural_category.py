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
    
    def _get_human_readable_name(self, kb, element_id, element_type="unknown"):
        """Convert element ID to human-readable name with biological context.
        
        Args:
            kb: Knowledge base
            element_id: Place or transition ID
            element_type: "place" or "transition"
            
        Returns:
            str: Human-readable name like "P5 (Glucose / C00031)" or "T3 (Hexokinase / R00200)"
        """
        if element_type == "place" or element_id.startswith('P'):
            place = kb.places.get(element_id)
            if place:
                parts = [element_id]
                
                # Add compound name if available
                if place.compound_id:
                    compound = kb.compounds.get(place.compound_id)
                    if compound and compound.name:
                        parts.append(compound.name)
                    else:
                        parts.append(place.compound_id)
                
                # Add label if available and different from compound
                if hasattr(place, 'label') and place.label and place.label != place.compound_id:
                    if not any(place.label in p for p in parts):
                        parts.append(place.label)
                
                return " / ".join(parts) if len(parts) > 1 else element_id
        
        elif element_type == "transition" or element_id.startswith('T'):
            trans = kb.transitions.get(element_id)
            if trans:
                parts = [element_id]
                
                # Add reaction name if available
                if trans.reaction_name:
                    parts.append(trans.reaction_name)
                elif trans.reaction_id:
                    parts.append(trans.reaction_id)
                
                # Add label if available and different
                if hasattr(trans, 'label') and trans.label:
                    if not any(trans.label in p for p in parts):
                        parts.append(trans.label)
                
                return " / ".join(parts) if len(parts) > 1 else element_id
        
        return element_id
    
    def _get_dead_from_simulation(self):
        """Get transitions that never fired during simulation.
        
        Returns:
            List[str]: Transition IDs that never fired
        """
        kb = self.get_knowledge_base()
        if not kb:
            return []
        
        # Get simulation data from model_canvas
        if not self.model_canvas:
            return []
        
        try:
            # Check if we have simulation data
            model_manager = getattr(self.model_canvas, 'model_manager', None)
            if not model_manager:
                return []
            
            controller = getattr(model_manager, 'controller', None)
            if not controller:
                return []
            
            data_collector = getattr(controller, 'data_collector', None)
            if not data_collector:
                return []
                
            has_data = data_collector.has_data()
            
            if not has_data:
                return []
            
            # Get transitions that never fired
            dead_transitions = []
            for trans_id in kb.transitions.keys():
                firings = data_collector.get_total_firings(trans_id)
                if firings == 0:
                    dead_transitions.append(trans_id)
            
            print(f"[STRUCTURAL] Simulation analysis: {len(dead_transitions)}/{len(kb.transitions)} transitions never fired")
            return dead_transitions
            
        except Exception as e:
            print(f"[Structural] Error getting simulation data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _build_content(self):
        """Build structural category content."""
        # Status section
        status_frame = Gtk.Frame(label="CURRENT STATUS")
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box.set_margin_start(12)
        status_box.set_margin_end(12)
        status_box.set_margin_top(12)
        status_box.set_margin_bottom(12)
        
        self.status_label = Gtk.Label(label="Expand category to scan for structural issues...")
        self.status_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.status_label, False, False, 0)
        
        status_frame.add(status_box)
        self.content_box.pack_start(status_frame, False, False, 0)
        
        # Action buttons
        button_box = self._create_action_buttons()
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
        """Scan for structural issues using multiple data sources.
        
        Intelligent multi-source analysis:
        1. Liveness analyzer (if available)
        2. Simulation data (transitions that never fired)
        3. Siphon analysis (if available)
        4. P-invariants coverage
        
        Returns:
            List[Issue]: Detected structural issues
        """
        kb = self.get_knowledge_base()
        if not kb:
            return []
        
        issues = []
        
        # SOURCE 1: Liveness analyzer (may be disabled for large models)
        dead_from_liveness = kb.get_dead_transitions()
        
        # SOURCE 2: Simulation data (transitions that never fired)
        dead_from_simulation = self._get_dead_from_simulation()
        
        # Diagnostic
        print(f"[STRUCTURAL] Scanning: liveness={len(dead_from_liveness)}, simulation={len(dead_from_simulation)}")
        
        # Combine sources (union of both)
        all_dead = set(dead_from_liveness) | set(dead_from_simulation)
        
        # Update status
        self.status_label.set_markup(
            f"<b>Data Sources:</b>\n"
            f"  • Liveness analyzer: {len(dead_from_liveness)} dead (may be disabled)\n"
            f"  • Simulation data: {len(dead_from_simulation)} never fired\n"
            f"  • Combined: {len(all_dead)} transitions\n"
            f"  • P-invariants: {len(kb.p_invariants)}\n"
            f"  • Siphons: {len(kb.siphons)}"
        )
        
        # Scan for dead transitions (using combined sources)
        for trans_id in list(all_dead)[:10]:  # Limit to 10
            trans = kb.transitions.get(trans_id)
            if trans:
                # Get human-readable name
                trans_name = self._get_human_readable_name(kb, trans_id, "transition")
                
                # Analyze WHY the transition is dead
                diagnosis = self._diagnose_dead_transition(kb, trans_id)
                
                # Create Issue dataclass with specific diagnosis
                issue = Issue(
                    id=f"dead_{trans_id}",
                    category="structural",
                    severity="critical",
                    title=f"{trans_name} is DEAD: {diagnosis['reason']}",
                    description=diagnosis['description'],
                    element_id=trans_id,
                    element_type="transition",
                    locality_id=self.selected_locality_id
                )
                
                # Add multiple specific suggestions based on diagnosis
                issue.suggestions = diagnosis['suggestions']
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
        
        return issues
    
    def _diagnose_dead_transition(self, kb, trans_id):
        """Diagnose WHY a transition is dead and suggest specific fixes.
        
        Analyzes:
        1. Input places - do they have tokens?
        2. Arc weights - are they too high?
        3. Priority conflicts - is another transition always firing first?
        4. Guards/conditions - are they too restrictive?
        
        Args:
            kb: Knowledge base
            trans_id: Transition ID to diagnose
            
        Returns:
            dict: {
                'reason': str,
                'description': str,
                'suggestions': List[Suggestion]
            }
        """
        suggestions = []
        
        # Get input arcs and places
        input_arcs = [arc for arc in kb.arcs.values() 
                     if arc.target_id == trans_id and arc.arc_type == "place_to_transition"]
        
        if not input_arcs:
            # SOURCE transition (no inputs) - check if it should be a source
            trans_name = self._get_human_readable_name(kb, trans_id, "transition")
            transition = kb.transitions.get(trans_id)
            has_rate = hasattr(transition, 'rate') and transition.rate > 0
            
            if not has_rate:
                return {
                    'reason': 'Source transition with no rate',
                    'description': f'{trans_name} is a source with no input places and no firing rate.',
                    'suggestions': [
                        Suggestion(
                            action="set_rate_or_add_inputs",
                            category="structural",
                            parameters={'transition_id': trans_id, 'suggested_rate': 1.0},
                            confidence=0.85,
                            reasoning="Source transitions need a firing rate to fire spontaneously, or add input places if not truly a source",
                            preview_elements=[trans_id]
                        )
                    ]
                }
            else:
                return {
                    'reason': 'Source transition unused',
                    'description': f'{trans_name} has rate={transition.rate} but never fired during simulation.',
                    'suggestions': [
                        Suggestion(
                            action="check_source_usage",
                            category="structural",
                            parameters={'transition_id': trans_id, 'current_rate': transition.rate},
                            confidence=0.6,
                            reasoning="Source might be unused boundary condition, or rate too low, or simulation time too short",
                            preview_elements=[trans_id]
                        )
                    ]
                }
        
        # Analyze each input place
        insufficient_tokens = []
        high_weight_arcs = []
        zero_token_places = []
        
        for arc in input_arcs:
            place_id = arc.source_id
            place = kb.places.get(place_id)
            arc_weight = arc.current_weight
            
            if place:
                current_tokens = place.current_marking
                
                if current_tokens == 0:
                    zero_token_places.append((place_id, arc_weight))
                elif current_tokens < arc_weight:
                    insufficient_tokens.append((place_id, current_tokens, arc_weight))
                
                if arc_weight > 1:
                    high_weight_arcs.append((place_id, arc_weight))
        
        # DIAGNOSIS 1: Zero tokens in input places
        if zero_token_places:
            place_ids = [p[0] for p in zero_token_places]
            
            # Build human-readable place names
            place_names = [self._get_human_readable_name(kb, pid, "place") for pid in place_ids]
            
            # Suggest adding initial marking
            suggestions.append(Suggestion(
                action="add_initial_marking",
                category="structural",
                parameters={
                    'place_ids': place_ids,
                    'tokens': max(w for _, w in zero_token_places)  # At least enough for arc weight
                },
                confidence=0.9,
                reasoning=f"Add {max(w for _, w in zero_token_places)} tokens to: {', '.join(place_names)}",
                preview_elements=place_ids + [trans_id]
            ))
            
            return {
                'reason': 'Input places empty',
                'description': f'{len(zero_token_places)} input place(s) have zero tokens: {", ".join(place_names)}',
                'suggestions': suggestions
            }
        
        # DIAGNOSIS 2: Insufficient tokens vs arc weights
        if insufficient_tokens:
            place_id, tokens, weight = insufficient_tokens[0]
            place_name = self._get_human_readable_name(kb, place_id, "place")
            
            # Option A: Add more tokens
            suggestions.append(Suggestion(
                action="add_initial_marking",
                category="structural",
                parameters={'place_id': place_id, 'tokens': weight - tokens},
                confidence=0.7,
                reasoning=f"{place_name} has {tokens} tokens but needs {weight} — add {weight - tokens} tokens",
                preview_elements=[place_id, trans_id]
            ))
            
            # Option B: Reduce arc weight
            suggestions.append(Suggestion(
                action="reduce_arc_weight",
                category="structural",
                parameters={'arc_id': f"{place_id}→{trans_id}", 'from_weight': weight, 'to_weight': tokens},
                confidence=0.8,
                reasoning=f"Reduce arc weight from {weight} to {tokens} for {place_name}",
                preview_elements=[place_id, trans_id]
            ))
            
            return {
                'reason': 'Insufficient tokens',
                'description': f'{place_name} has {tokens} tokens but arc requires {weight}',
                'suggestions': suggestions
            }
        
        # DIAGNOSIS 3: High arc weights (stoichiometry issue)
        if high_weight_arcs:
            place_id, weight = high_weight_arcs[0]
            place_name = self._get_human_readable_name(kb, place_id, "place")
            
            suggestions.append(Suggestion(
                action="reduce_arc_weight",
                category="structural",
                parameters={'arc_id': f"{place_id}→{trans_id}", 'from_weight': weight, 'to_weight': 1},
                confidence=0.6,
                reasoning=f"Arc from {place_name} has weight {weight} — verify stoichiometry or reduce to 1",
                preview_elements=[place_id, trans_id]
            ))
            
            return {
                'reason': 'High arc weights',
                'description': f'Input arcs have weights > 1 (max: {max(w for _, w in high_weight_arcs)})',
                'suggestions': suggestions
            }
        
        # DIAGNOSIS 4: Priority conflict (another transition consuming tokens first)
        # Check if there are competing transitions
        competing_transitions = self._find_competing_transitions(kb, trans_id, input_arcs)
        
        if competing_transitions:
            comp_trans_id = competing_transitions[0]
            comp_trans_name = self._get_human_readable_name(kb, comp_trans_id, "transition")
            target_trans_name = self._get_human_readable_name(kb, trans_id, "transition")
            
            suggestions.append(Suggestion(
                action="adjust_priority",
                category="structural",
                parameters={
                    'transition_id': trans_id,
                    'from_priority': 0,
                    'to_priority': 10,
                    'reason': f'competing_with_{comp_trans_id}'
                },
                confidence=0.7,
                reasoning=f"Increase {target_trans_name} priority to fire before {comp_trans_name}",
                preview_elements=[trans_id, comp_trans_id]
            ))
            
            # Alternative: Reduce competitor's priority
            suggestions.append(Suggestion(
                action="adjust_priority",
                category="structural",
                parameters={
                    'transition_id': comp_trans_id,
                    'from_priority': 0,
                    'to_priority': -10,
                    'reason': f'yield_to_{trans_id}'
                },
                confidence=0.6,
                reasoning=f"Reduce {comp_trans_name} priority to let {target_trans_name} fire first",
                preview_elements=[trans_id, comp_trans_id]
            ))
            
            comp_names = [self._get_human_readable_name(kb, tid, "transition") for tid in competing_transitions[:3]]
            
            return {
                'reason': 'Priority conflict',
                'description': f'Competing with {len(competing_transitions)} transition(s): {", ".join(comp_names)}',
                'suggestions': suggestions
            }
        
        # DIAGNOSIS 5: Unknown cause - generic suggestions
        first_place_id = input_arcs[0].source_id
        first_place_name = self._get_human_readable_name(kb, first_place_id, "place")
        
        suggestions.append(Suggestion(
            action="add_initial_marking",
            category="structural",
            parameters={'place_id': first_place_id, 'tokens': 5},
            confidence=0.5,
            reasoning=f"General suggestion: add 5 tokens to {first_place_name} to enable firing",
            preview_elements=[first_place_id, trans_id]
        ))
        
        return {
            'reason': 'Unknown cause',
            'description': f'Has {len(input_arcs)} input(s) with tokens, but still inactive — check simulation rates',
            'suggestions': suggestions
        }
    
    def _find_competing_transitions(self, kb, trans_id, input_arcs):
        """Find transitions competing for same input tokens.
        
        Args:
            kb: Knowledge base
            trans_id: Target transition ID
            input_arcs: Input arcs of target transition
            
        Returns:
            List[str]: IDs of competing transitions
        """
        competitors = []
        input_place_ids = {arc.source_id for arc in input_arcs}
        
        # Find other transitions that also consume from these places
        for other_trans_id, other_trans in kb.transitions.items():
            if other_trans_id == trans_id:
                continue
            
            # Check if this transition has arcs from same input places
            other_input_arcs = [arc for arc in kb.arcs.values()
                               if arc.target_id == other_trans_id and arc.arc_type == "place_to_transition"]
            
            other_input_places = {arc.source_id for arc in other_input_arcs}
            
            # If they share input places, they're competing
            if input_place_ids & other_input_places:  # Set intersection
                competitors.append(other_trans_id)
        
        return competitors

