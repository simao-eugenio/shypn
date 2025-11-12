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
from typing import List

from .base_category import BaseViabilityCategory
from .multi_domain_engine import MultiDomainEngine
from .viability_dataclasses import Issue, Suggestion, MultiDomainSuggestion


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
        
        # Multi-domain engine (the key innovation!)
        self.multi_domain_engine = MultiDomainEngine()
        
        # Track selected transition and locality objects
        self.selected_transition = None
        self.selected_locality = None
    
    def get_category_name(self):
        """Get category display name.
        
        Returns:
            str: Category name
        """
        return "DIAGNOSIS & REPAIR"
    
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
    
    def _diagnose_dead_transition(self, kb, trans_id):
        """Diagnose WHY a transition is dead/inactive and suggest specific fixes.
        
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
                'suggestions': List[dict] with action, parameters, confidence, reasoning
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
                    'suggestions': [{
                        'action': "set_rate_or_add_inputs",
                        'category': "structural",
                        'parameters': {'transition_id': trans_id, 'suggested_rate': 1.0},
                        'confidence': 0.85,
                        'reasoning': "Source transitions need a firing rate to fire spontaneously, or add input places if not truly a source",
                        'preview_elements': [trans_id]
                    }]
                }
            else:
                return {
                    'reason': 'Source transition unused',
                    'description': f'{trans_name} has rate={transition.rate} but never fired during simulation.',
                    'suggestions': [{
                        'action': "check_source_usage",
                        'category': "structural",
                        'parameters': {'transition_id': trans_id, 'current_rate': transition.rate},
                        'confidence': 0.6,
                        'reasoning': "Source might be unused boundary condition, or rate too low, or simulation time too short",
                        'preview_elements': [trans_id]
                    }]
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
            place_names = [self._get_human_readable_name(kb, pid, "place") for pid in place_ids]
            tokens_needed = max(w for _, w in zero_token_places)
            
            suggestions.append({
                'action': "add_initial_marking",
                'category': "structural",
                'parameters': {
                    'place_ids': place_ids,
                    'tokens': tokens_needed
                },
                'confidence': 0.9,
                'reasoning': f"Add {tokens_needed} tokens to: {', '.join(place_names)}",
                'preview_elements': place_ids + [trans_id]
            })
            
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
            suggestions.append({
                'action': "add_initial_marking",
                'category': "structural",
                'parameters': {'place_id': place_id, 'tokens': weight - tokens},
                'confidence': 0.7,
                'reasoning': f"{place_name} has {tokens} tokens but needs {weight} — add {weight - tokens} tokens",
                'preview_elements': [place_id, trans_id]
            })
            
            # Option B: Reduce arc weight
            suggestions.append({
                'action': "reduce_arc_weight",
                'category': "structural",
                'parameters': {'arc_id': f"{place_id}→{trans_id}", 'from_weight': weight, 'to_weight': tokens},
                'confidence': 0.8,
                'reasoning': f"Reduce arc weight from {weight} to {tokens} for {place_name}",
                'preview_elements': [place_id, trans_id]
            })
            
            return {
                'reason': 'Insufficient tokens',
                'description': f'{place_name} has {tokens} tokens but arc requires {weight}',
                'suggestions': suggestions
            }
        
        # DIAGNOSIS 3: High arc weights (stoichiometry issue)
        if high_weight_arcs:
            place_id, weight = high_weight_arcs[0]
            place_name = self._get_human_readable_name(kb, place_id, "place")
            
            suggestions.append({
                'action': "reduce_arc_weight",
                'category': "structural",
                'parameters': {'arc_id': f"{place_id}→{trans_id}", 'from_weight': weight, 'to_weight': 1},
                'confidence': 0.6,
                'reasoning': f"Arc from {place_name} has weight {weight} — verify stoichiometry or reduce to 1",
                'preview_elements': [place_id, trans_id]
            })
            
            return {
                'reason': 'High arc weights',
                'description': f'Input arcs have weights > 1 (max: {max(w for _, w in high_weight_arcs)})',
                'suggestions': suggestions
            }
        
        # DIAGNOSIS 4: Priority conflict
        competing_transitions = self._find_competing_transitions(kb, trans_id, input_arcs)
        
        if competing_transitions:
            comp_trans_id = competing_transitions[0]
            comp_trans_name = self._get_human_readable_name(kb, comp_trans_id, "transition")
            target_trans_name = self._get_human_readable_name(kb, trans_id, "transition")
            
            suggestions.append({
                'action': "adjust_priority",
                'category': "structural",
                'parameters': {
                    'transition_id': trans_id,
                    'from_priority': 0,
                    'to_priority': 10,
                    'reason': f'competing_with_{comp_trans_id}'
                },
                'confidence': 0.7,
                'reasoning': f"Increase {target_trans_name} priority to fire before {comp_trans_name}",
                'preview_elements': [trans_id, comp_trans_id]
            })
            
            suggestions.append({
                'action': "adjust_priority",
                'category': "structural",
                'parameters': {
                    'transition_id': comp_trans_id,
                    'from_priority': 0,
                    'to_priority': -10,
                    'reason': f'yield_to_{trans_id}'
                },
                'confidence': 0.6,
                'reasoning': f"Reduce {comp_trans_name} priority to let {target_trans_name} fire first",
                'preview_elements': [trans_id, comp_trans_id]
            })
            
            comp_names = [self._get_human_readable_name(kb, tid, "transition") for tid in competing_transitions[:3]]
            
            return {
                'reason': 'Priority conflict',
                'description': f'Competing with {len(competing_transitions)} transition(s): {", ".join(comp_names)}',
                'suggestions': suggestions
            }
        
        # DIAGNOSIS 5: Unknown cause
        first_place_id = input_arcs[0].source_id
        first_place_name = self._get_human_readable_name(kb, first_place_id, "place")
        
        suggestions.append({
            'action': "add_initial_marking",
            'category': "structural",
            'parameters': {'place_id': first_place_id, 'tokens': 5},
            'confidence': 0.5,
            'reasoning': f"General suggestion: add 5 tokens to {first_place_name} to enable firing",
            'preview_elements': [first_place_id, trans_id]
        })
        
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
            if input_place_ids & other_input_places:
                competitors.append(other_trans_id)
        
        return competitors
    
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
        
        # Locality list (indented) - replaces combo box
        locality_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        locality_list_box.set_margin_start(24)
        
        # Scrolled window for locality list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(150)
        scrolled.set_max_content_height(300)
        
        # ListBox to hold transitions with their localities
        self.locality_listbox = Gtk.ListBox()
        self.locality_listbox.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.locality_listbox.connect('row-selected', self._on_locality_row_selected)
        self.locality_listbox.set_sensitive(False)
        scrolled.add(self.locality_listbox)
        
        locality_list_box.pack_start(scrolled, True, True, 0)
        
        # Clear button to clear selection
        self.clear_selection_button = Gtk.Button(label="CLEAR")
        self.clear_selection_button.set_tooltip_text("Clear locality selection")
        self.clear_selection_button.set_sensitive(False)
        self.clear_selection_button.connect('clicked', self._on_clear_selection_clicked)
        locality_list_box.pack_start(self.clear_selection_button, False, False, 0)
        
        locality_box.pack_start(locality_list_box, True, True, 0)
        
        locality_frame.add(locality_box)
        self.content_box.pack_start(locality_frame, False, False, 0)
        
        # Action buttons - Override to add RUN SELECTED
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_margin_start(12)
        button_box.set_margin_end(12)
        button_box.set_margin_top(6)
        button_box.set_margin_bottom(6)
        
        # RUN SELECTED button - for locality-scoped diagnosis
        self.run_selected_button = Gtk.Button(label="RUN SELECTED")
        self.run_selected_button.set_tooltip_text("Run diagnosis for selected locality")
        self.run_selected_button.set_sensitive(False)
        self.run_selected_button.connect('clicked', self._on_run_selected_clicked)
        button_box.pack_start(self.run_selected_button, True, True, 0)
        
        # RUN FULL DIAGNOSE button - for global diagnosis
        self.scan_button = Gtk.Button(label="RUN FULL DIAGNOSE")
        self.scan_button.set_tooltip_text("Run complete diagnosis on entire model")
        self.scan_button.connect('clicked', self._on_run_full_diagnose_clicked)
        button_box.pack_start(self.scan_button, True, True, 0)
        
        # Clear button
        self.clear_button = Gtk.Button(label="Clear Issues")
        self.clear_button.set_tooltip_text("Clear all displayed issues")
        self.clear_button.set_sensitive(False)
        self.clear_button.connect('clicked', self._on_clear_clicked)
        button_box.pack_start(self.clear_button, True, True, 0)
        
        self.content_box.pack_start(button_box, False, False, 0)
        
        # Issues table with TreeView for multi-domain view
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
    
    def _on_scope_changed(self, radio_button):
        """Handle scope radio button change.
        
        Args:
            radio_button: Radio button that was toggled
        """
        if self.locality_radio.get_active():
            self.locality_listbox.set_sensitive(True)
            # Use selected locality
            selected_row = self.locality_listbox.get_selected_row()
            if selected_row:
                # Get transition and locality from row data
                transition = getattr(selected_row, 'transition_obj', None)
                locality = getattr(selected_row, 'locality_obj', None)
                if transition:
                    self.selected_transition = transition
                    self.selected_locality = locality
                    self.selected_locality_id = transition.id
                    self.run_selected_button.set_sensitive(True)
                    self.clear_selection_button.set_sensitive(True)
                else:
                    self.selected_transition = None
                    self.selected_locality = None
                    self.selected_locality_id = None
                    self.run_selected_button.set_sensitive(False)
                    self.clear_selection_button.set_sensitive(False)
            else:
                self.selected_transition = None
                self.selected_locality = None
                self.selected_locality_id = None
                self.run_selected_button.set_sensitive(False)
                self.clear_selection_button.set_sensitive(False)
        else:
            self.locality_listbox.set_sensitive(False)
            self.selected_transition = None
            self.selected_locality = None
            self.selected_locality_id = None
            self.run_selected_button.set_sensitive(False)
            self.clear_selection_button.set_sensitive(False)
    
    def _on_locality_row_selected(self, listbox, row):
        """Handle locality list row selection (supports multiple selections).
        
        Collects ALL selected transition rows and prepares for multi-locality analysis.
        
        Args:
            listbox: ListBox that fired the signal
            row: Recently selected/deselected ListBoxRow (or None)
        """
        # Get ALL selected rows (not just the triggering row)
        selected_rows = self.locality_listbox.get_selected_rows()
        
        if not selected_rows:
            # No selections
            self.selected_transition = None
            self.selected_locality = None
            self.selected_locality_id = None
            self.selected_transitions = []
            self.selected_localities = []
            self.run_selected_button.set_sensitive(False)
            self.clear_selection_button.set_sensitive(False)
            return
        
        # Collect all selected transitions (filter out place rows)
        selected_transitions = []
        selected_localities = []
        
        for row in selected_rows:
            # Only process transition rows (parent rows), skip place rows (children)
            if getattr(row, 'is_transition_row', False):
                transition = getattr(row, 'transition_obj', None)
                locality = getattr(row, 'locality_obj', None)
                
                if transition and locality:
                    selected_transitions.append(transition)
                    selected_localities.append(locality)
            
            # If user clicked a place row, find its parent transition
            elif getattr(row, 'is_place_row', False):
                parent_transition = getattr(row, 'parent_transition', None)
                
                if parent_transition:
                    # Find the transition row to get its locality
                    for child_row in self.locality_listbox.get_children():
                        if getattr(child_row, 'is_transition_row', False):
                            trans_obj = getattr(child_row, 'transition_obj', None)
                            if trans_obj and trans_obj.id == parent_transition.id:
                                locality = getattr(child_row, 'locality_obj', None)
                                
                                # Add if not already in list
                                if trans_obj not in selected_transitions:
                                    selected_transitions.append(trans_obj)
                                    selected_localities.append(locality)
                                break
        
        # Store selections
        self.selected_transitions = selected_transitions
        self.selected_localities = selected_localities
        
        if selected_transitions:
            # For backward compatibility, store first selection as primary
            self.selected_transition = selected_transitions[0]
            self.selected_locality = selected_localities[0]
            self.selected_locality_id = selected_transitions[0].id
            
            trans_ids = [t.id for t in selected_transitions]
            self.run_selected_button.set_sensitive(True)
            self.clear_selection_button.set_sensitive(True)
        else:
            # No valid selections (only place rows selected)
            self.selected_transition = None
            self.selected_locality = None
            self.selected_locality_id = None
            self.run_selected_button.set_sensitive(False)
            self.clear_selection_button.set_sensitive(False)
    
    def _on_clear_selection_clicked(self, button):
        """Handle CLEAR button click - clear locality listbox selection.
        
        Args:
            button: Button that was clicked
        """
        self.locality_listbox.unselect_all()
        self.selected_transition = None
        self.selected_locality = None
        self.selected_locality_id = None
        self.run_selected_button.set_sensitive(False)
        self.clear_selection_button.set_sensitive(False)
    
    def _on_run_selected_clicked(self, button):
        """Handle RUN SELECTED button click - run diagnosis for selected locality.
        
        Args:
            button: Button that was clicked
        """
        if not self.selected_transition or not self.selected_locality:
            return
        
        self._run_selected_diagnosis()
    
    def _on_run_full_diagnose_clicked(self, button):
        """Handle RUN FULL DIAGNOSE button click - run diagnosis on entire model.
        
        This triggers the parent panel's on_analyze_all method which was previously
        connected to the header button.
        
        Args:
            button: Button that was clicked
        """
        
        # Clear any locality scope
        self.selected_locality_id = None
        
        # Trigger parent panel's analyze all (batch mode)
        if hasattr(self, 'parent_panel') and self.parent_panel:
            if hasattr(self.parent_panel, 'on_analyze_all'):
                self.parent_panel.on_analyze_all(button)
    
    def _run_selected_diagnosis(self):
        """Run diagnosis scoped to the selected locality/localities (supports multiple).
        
        This will:
        1. Analyze the selected transition(s) and their localities (input/output places)
        2. Populate all category suggestions filtered to this scope
        3. Trigger all categories to show suggestions for these localities
        """
        # Support both single and multiple selections
        transitions = getattr(self, 'selected_transitions', [])
        localities = getattr(self, 'selected_localities', [])
        
        # Fallback to single selection for backward compatibility
        if not transitions and hasattr(self, 'selected_transition') and self.selected_transition:
            transitions = [self.selected_transition]
            localities = [self.selected_locality]
        
        if not transitions or not localities:
            return
        
        trans_ids = [t.id for t in transitions]
        
        # Store the scope for this diagnosis
        kb = self.get_knowledge_base()
        if not kb:
            return
        
        # Build combined locality scope (all selected transitions and their places)
        all_relevant_ids = set()
        for transition, locality in zip(transitions, localities):
            all_relevant_ids.add(transition.id)
            all_relevant_ids.update(p.id for p in locality.input_places)
            all_relevant_ids.update(p.id for p in locality.output_places)
        
        
        # Run diagnosis (scan all issues)
        issues = self._scan_issues()
        
        # Filter issues to combined locality scope
        filtered_issues = [
            issue for issue in issues 
            if hasattr(issue, 'element_id') and issue.element_id in all_relevant_ids
        ]
        
        # Display filtered issues
        self._display_issues(filtered_issues)
        
        # Notify parent panel to trigger other categories with locality scope
        if hasattr(self, 'parent_panel') and self.parent_panel:
            
            # Trigger other categories to scan with each locality scope
            for i, category in enumerate(self.parent_panel.categories):
                category_name = category.get_category_name() if hasattr(category, 'get_category_name') else str(category)
                
                if category != self and hasattr(category, 'scan_with_locality'):
                    # For multiple selections, scan with first transition but filter by all_relevant_ids
                    
                    # Use first transition as representative, but category will filter by all_relevant_ids
                    category.scan_with_locality(
                        transition=transitions[0],
                        locality=localities[0],
                        additional_ids=all_relevant_ids  # Pass combined scope
                    )
    
    def set_analyses_panel(self, analyses_panel):
        """Set reference to analyses panel for locality access.
        
        Args:
            analyses_panel: AnalysesPanel instance
        """
        self.analyses_panel = analyses_panel
        # Populate locality dropdown from analyses_panel
        self._populate_localities()
    
    def add_transition_for_analysis(self, transition):
        """Add a specific transition with its locality to the analysis list.
        
        This is called from the context menu "Add to Viability Analysis".
        Shows transition with indented places (like plotting system), allowing
        multiple localities to be selected for sub-network analysis.
        
        Args:
            transition: Transition object from context menu
        """
        
        # Get model
        model = None
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_model'):
            model = self.model_canvas.get_current_model()
        
        if not model:
            return
        
        # Use LocalityDetector to get THIS transition's locality (same as plotting)
        from shypn.diagnostic.locality_detector import LocalityDetector
        detector = LocalityDetector(model)
        locality = detector.get_locality_for_transition(transition)
        
        if not locality.is_valid:
            return
        
        
        # Check if this transition is already in the list
        for child in self.locality_listbox.get_children():
            trans_obj = getattr(child, 'transition_obj', None)
            if trans_obj and trans_obj.id == transition.id:
                return
        
        # Add this transition with its locality places (hierarchical display)
        self._add_transition_with_locality_to_list(transition, locality)
        
        # Switch to locality mode
        self.locality_radio.set_active(True)
        self.locality_listbox.set_sensitive(True)
        
    
    def _add_transition_with_locality_to_list(self, transition, locality):
        """Add a transition and its locality places to the listbox (hierarchical tree view).
        
        Creates a display like plotting:
        🔄 T6: R03270
           ← Input: P5 (C00118)
           ← Input: P7 (C00267)  
           → Output: P10 (C00036)
        
        Args:
            transition: Transition object
            locality: Locality object with input/output places
        """
        trans_id = transition.id
        trans_label = getattr(transition, 'label', '') or ''
        is_source = getattr(transition, 'is_source', False)
        is_sink = getattr(transition, 'is_sink', False)
        
        # Add transition row (parent)
        trans_row = Gtk.ListBoxRow()
        trans_row.transition_obj = transition
        trans_row.locality_obj = locality
        trans_row.is_transition_row = True  # Mark as parent row
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        hbox.set_margin_top(3)
        hbox.set_margin_bottom(3)
        
        # Transition icon
        icon_label = Gtk.Label(label="🔄")
        hbox.pack_start(icon_label, False, False, 0)
        
        # Transition info
        display_text = trans_id
        if trans_label:
            display_text += f": {trans_label}"
        if is_source:
            display_text += " [SOURCE]"
        elif is_sink:
            display_text += " [SINK]"
            
        label = Gtk.Label(label=display_text)
        label.set_xalign(0)
        hbox.pack_start(label, True, True, 0)
        
        # Remove button
        remove_btn = Gtk.Button(label="✕")
        remove_btn.set_relief(Gtk.ReliefStyle.NONE)
        remove_btn.connect('clicked', self._on_remove_locality_clicked, transition)
        hbox.pack_start(remove_btn, False, False, 0)
        
        trans_row.add(hbox)
        self.locality_listbox.add(trans_row)
        
        # Add indented input places
        if not is_source:  # Source transitions have no inputs
            for place in locality.input_places:
                self._add_place_row_to_list(place, "← Input:", transition)
        
        # Add indented output places
        if not is_sink:  # Sink transitions have no outputs
            for place in locality.output_places:
                self._add_place_row_to_list(place, "→ Output:", transition)
        
        self.locality_listbox.show_all()
    
    def _add_place_row_to_list(self, place, label_prefix, parent_transition):
        """Add an indented place row under its parent transition.
        
        Args:
            place: Place object
            label_prefix: "← Input:" or "→ Output:"
            parent_transition: Parent Transition object
        """
        place_row = Gtk.ListBoxRow()
        place_row.place_obj = place
        place_row.parent_transition = parent_transition
        place_row.is_place_row = True  # Mark as child row
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.set_margin_start(40)  # Indent to show hierarchy
        hbox.set_margin_end(6)
        hbox.set_margin_top(1)
        hbox.set_margin_bottom(1)
        
        # Place icon (smaller)
        icon_label = Gtk.Label(label="●")
        icon_label.get_style_context().add_class('dim-label')
        hbox.pack_start(icon_label, False, False, 0)
        
        # Place info
        place_name = getattr(place, 'name', '') or ''
        place_label = getattr(place, 'label', '') or ''
        
        display_text = f"{label_prefix} {place.id}"
        if place_label:
            display_text += f" ({place_label})"
        elif place_name:
            display_text += f" ({place_name})"
        
        label = Gtk.Label(label=display_text)
        label.set_xalign(0)
        label.get_style_context().add_class('dim-label')
        hbox.pack_start(label, True, True, 0)
        
        place_row.add(hbox)
        self.locality_listbox.add(place_row)
    
    def _on_remove_locality_clicked(self, button, transition):
        """Remove a transition and its locality places from the list.
        
        Args:
            button: Button widget (unused)
            transition: Transition object to remove
        """
        
        # Remove transition row and all its place rows
        children = self.locality_listbox.get_children()
        rows_to_remove = []
        
        for row in children:
            # Remove transition row
            if getattr(row, 'is_transition_row', False):
                trans_obj = getattr(row, 'transition_obj', None)
                if trans_obj and trans_obj.id == transition.id:
                    rows_to_remove.append(row)
            # Remove place rows belonging to this transition
            elif getattr(row, 'is_place_row', False):
                parent_trans = getattr(row, 'parent_transition', None)
                if parent_trans and parent_trans.id == transition.id:
                    rows_to_remove.append(row)
        
        for row in rows_to_remove:
            self.locality_listbox.remove(row)
        
        # If list is now empty, add placeholder
        if not self.locality_listbox.get_children():
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="(No localities selected)")
            label.get_style_context().add_class('dim-label')
            label.set_margin_start(6)
            label.set_margin_end(6)
            label.set_margin_top(6)
            label.set_margin_bottom(6)
            row.add(label)
            self.locality_listbox.add(row)
            self.locality_listbox.set_sensitive(False)
        
        self.locality_listbox.show_all()
    
    def _populate_localities(self):
        """Populate the locality list using LocalityDetector (same as plotting system)."""
        
        # Clear existing rows
        for child in self.locality_listbox.get_children():
            self.locality_listbox.remove(child)
        
        # Get model
        model = None
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_model'):
            model = self.model_canvas.get_current_model()
        
        if not model or not hasattr(model, 'transitions'):
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="(No model available)")
            label.get_style_context().add_class('dim-label')
            label.set_margin_start(6)
            label.set_margin_end(6)
            label.set_margin_top(6)
            label.set_margin_bottom(6)
            row.add(label)
            self.locality_listbox.add(row)
            self.locality_listbox.set_sensitive(False)
            self.locality_listbox.show_all()
            return
        
        
        # Use LocalityDetector to get all valid localities (same as plotting)
        from shypn.diagnostic.locality_detector import LocalityDetector
        detector = LocalityDetector(model)
        localities = detector.get_all_localities()
        
        
        if not localities:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="(No localities available)")
            label.get_style_context().add_class('dim-label')
            label.set_margin_start(6)
            label.set_margin_end(6)
            label.set_margin_top(6)
            label.set_margin_bottom(6)
            row.add(label)
            self.locality_listbox.add(row)
            self.locality_listbox.set_sensitive(False)
        else:
            # Add each valid locality to the listbox
            for locality in localities:
                transition = locality.transition
                trans_id = getattr(transition, 'id', 'unknown')
                trans_label = getattr(transition, 'label', '') or ''
                
                
                # Create row
                row = Gtk.ListBoxRow()
                
                # Store objects in row for later retrieval
                row.transition_obj = transition
                row.locality_obj = locality
                
                # Create row content
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                hbox.set_margin_start(6)
                hbox.set_margin_end(6)
                hbox.set_margin_top(3)
                hbox.set_margin_bottom(3)
                
                # Transition icon
                icon_label = Gtk.Label(label="🔄")
                hbox.pack_start(icon_label, False, False, 0)
                
                # Transition info
                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                
                # Main label (ID + label if available)
                display_text = trans_id
                if trans_label:
                    display_text += f": {trans_label}"
                main_label = Gtk.Label(label=display_text)
                main_label.set_xalign(0)
                main_label.set_ellipsize(3)  # Ellipsize at end
                info_box.pack_start(main_label, False, False, 0)
                
                # Locality summary
                n_inputs = len(locality.input_places)
                n_outputs = len(locality.output_places)
                summary_label = Gtk.Label(label=f"   ↓ {n_inputs} inputs, {n_outputs} outputs →")
                summary_label.set_xalign(0)
                summary_label.get_style_context().add_class('dim-label')
                info_box.pack_start(summary_label, False, False, 0)
                
                hbox.pack_start(info_box, True, True, 0)
                row.add(hbox)
                
                self.locality_listbox.add(row)
            
            self.locality_listbox.set_sensitive(True)
        
        self.locality_listbox.show_all()
    
    def _get_transition_locality(self, transition):
        """Get locality object for a transition by scanning model arcs.
        
        Args:
            transition: Transition object (from model)
            
        Returns:
            Locality object or None
        """
        try:
            from shypn.diagnostic.locality_detector import Locality
            
            trans_id = transition.id if hasattr(transition, 'id') else str(transition)
            
            # Get model
            if not self.model_canvas or not hasattr(self.model_canvas, 'get_current_model'):
                return None
            
            model = self.model_canvas.get_current_model()
            if not model or not hasattr(model, 'arcs'):
                return None
            
            # Scan all arcs to find those connected to this transition
            input_places = []
            output_places = []
            input_arcs = []
            output_arcs = []
            
            
            for arc in model.arcs:
                # Skip test arcs (catalysts) - they don't define locality
                if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
                    continue
                
                # Skip arcs involving catalyst places
                if getattr(arc.source, 'is_catalyst', False) or getattr(arc.target, 'is_catalyst', False):
                    continue
                
                # Input arc: place → transition
                if arc.target == transition:
                    input_arcs.append(arc)
                    if arc.source not in input_places:
                        input_places.append(arc.source)
                        place_id = arc.source.id if hasattr(arc.source, 'id') else 'unknown'
                
                # Output arc: transition → place
                elif arc.source == transition:
                    output_arcs.append(arc)
                    if arc.target not in output_places:
                        output_places.append(arc.target)
                        place_id = arc.target.id if hasattr(arc.target, 'id') else 'unknown'
            
            
            if not input_places and not output_places:
                return None
            
            return Locality(
                transition=transition,
                input_places=input_places,
                output_places=output_places,
                input_arcs=input_arcs,
                output_arcs=output_arcs
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None
    
    def set_selected_locality(self, transition_id, auto_scan=True):
        """Set locality from canvas context menu (right-click on transition).
        
        This is called when user right-clicks a transition and selects
        "Analyze Locality" from the context menu. It automatically:
        1. Switches to "Selected Locality" mode
        2. Populates the dropdown with the transition's locality
        3. Optionally triggers diagnosis scan
        
        Args:
            transition_id: ID of the selected transition
            auto_scan: Whether to automatically run diagnosis (default: True)
        """
        kb = self.get_knowledge_base()
        if not kb:
            return
        
        # Get locality for this transition
        locality = self._get_locality_for_transition(kb, transition_id)
        if not locality:
            return
        
        # Switch to locality mode
        self.locality_radio.set_active(True)
        
        # Update dropdown selection
        self._populate_locality_dropdown([locality])
        self.locality_combo.set_active(0)  # Select the first (only) item
        
        # Store the selection
        self.selected_locality_id = locality['id']
        
        
        # Auto-scan if requested
        if auto_scan:
            self._on_scan_clicked(None)
    
    def _get_locality_for_transition(self, kb, transition_id):
        """Get locality information for a specific transition.
        
        Args:
            kb: Knowledge base
            transition_id: Transition ID
            
        Returns:
            dict: Locality info {'id': ..., 'name': ..., 'transitions': [...]}
            or None if not found
        """
        # TODO: Query KB for localities containing this transition
        # For now, return a placeholder
        return {
            'id': f'locality_{transition_id}',
            'name': f'Locality around {transition_id}',
            'transitions': [transition_id]
        }
    
    def _populate_locality_dropdown(self, localities):
        """Populate locality dropdown with available localities.
        
        Args:
            localities: List of locality dicts
        """
        # Clear existing entries
        self.locality_combo.remove_all()
        
        if not localities:
            self.locality_combo.append_text("(No localities available)")
            self.locality_combo.set_active(0)
            self.locality_combo.set_sensitive(False)
            return
        
        # Add localities
        for locality in localities:
            display_name = locality.get('name', locality.get('id', 'Unknown'))
            self.locality_combo.append_text(display_name)
        
        self.locality_combo.set_sensitive(True)
    
    def _scan_issues(self):
        """Scan for issues across all domains.
        
        Returns:
            List[Issue]: Detected issues from all categories
        """
        kb = self.get_knowledge_base()
        if not kb:
            return []
        
        
        # Update multi-domain engine with current KB
        self.multi_domain_engine.kb = kb
        
        issues = []
        
        # Calculate health scores
        structural_health = self._calculate_structural_health(kb)
        biological_health = self._calculate_biological_health(kb)
        kinetic_health = self._calculate_kinetic_health(kb)
        overall_health = (structural_health + biological_health + kinetic_health) / 3
        
        
        # Update health display (if widget exists)
        if hasattr(self, 'health_label') and self.health_label:
            self.health_label.set_markup(
                f"<b>Overall Health: {overall_health:.0f}%</b>\n\n"
                f"  STRUCTURAL:  {self._health_bar(structural_health)} {structural_health:.0f}%\n"
                f"  BIOLOGICAL:  {self._health_bar(biological_health)} {biological_health:.0f}%\n"
                f"  KINETIC:     {self._health_bar(kinetic_health)} {kinetic_health:.0f}%"
            )
        
        # Collect issues from all categories (using dataclasses now)
        issues.extend(self._scan_structural_issues(kb))
        issues.extend(self._scan_biological_issues(kb))
        issues.extend(self._scan_kinetic_issues(kb))
        
        # Generate multi-domain suggestions (KEY INNOVATION!)
        if issues:
            multi_domain_suggestions = self.multi_domain_engine.get_multi_domain_suggestions(
                issues=issues,
                locality_id=self.selected_locality_id
            )
            
            
            # Add multi-domain suggestions to issues
            for mds in multi_domain_suggestions:
                # Create a special issue to display the multi-domain suggestion
                multi_issue = Issue(
                    id=f"multi_{mds.element_id}",
                    category="multi-domain",
                    severity="info",
                    title=f"Multi-Domain Analysis: {mds.element_id}",
                    description=mds.combined_reasoning,
                    element_id=mds.element_id,
                    element_type="place",  # TODO: detect from element_id
                    locality_id=self.selected_locality_id
                )
                
                # Add combined suggestion
                combined_suggestion = Suggestion(
                    action="apply_multi_domain",
                    category="multi-domain",
                    parameters={
                        "structural": mds.structural_suggestion.parameters if mds.structural_suggestion else {},
                        "biological": mds.biological_suggestion.parameters if mds.biological_suggestion else {},
                        "kinetic": mds.kinetic_suggestion.parameters if mds.kinetic_suggestion else {}
                    },
                    confidence=mds.combined_confidence,
                    reasoning=mds.combined_reasoning,
                    preview_elements=[mds.element_id]
                )
                
                multi_issue.suggestions = [combined_suggestion]
                issues.append(multi_issue)
        
        return issues
    
    def _scan_structural_issues(self, kb) -> List[Issue]:
        """Scan for structural issues.
        
        Args:
            kb: Knowledge base
            
        Returns:
            List[Issue]: Structural issues with suggestions
        """
        issues = []
        
        # PRIORITY 1: Check transitions that never fired in simulation
        # This is more reliable than topology liveness for complex models
        inactive_transitions = kb.get_inactive_transitions() if hasattr(kb, 'get_inactive_transitions') else []
        
        if inactive_transitions:
            for trans_id in inactive_transitions[:10]:  # Limit to first 10
                # Get human-readable name
                trans_name = self._get_human_readable_name(kb, trans_id, "transition")
                
                # Get detailed diagnosis
                diagnosis = self._diagnose_dead_transition(kb, trans_id)
                
                issue = Issue(
                    id=f"inactive_{trans_id}",
                    category="structural",
                    severity="warning",
                    title=f"{trans_name} never fired: {diagnosis.get('reason', 'Unknown')}",
                    description=diagnosis.get('description', "This transition did not fire during simulation"),
                    element_id=trans_id,
                    element_type="transition",
                    locality_id=self.selected_locality_id
                )
                
                # Add smart suggestions from diagnosis
                for suggestion_data in diagnosis.get('suggestions', []):
                    suggestion = Suggestion(
                        action=suggestion_data['action'],
                        category="structural",
                        parameters=suggestion_data['parameters'],
                        confidence=suggestion_data['confidence'],
                        reasoning=suggestion_data['reasoning'],
                        preview_elements=[trans_id]
                    )
                    issue.suggestions.append(suggestion)
                
                issues.append(issue)
        
        # PRIORITY 2: Check for topology-detected dead transitions (if liveness was run)
        dead_transitions = kb.get_dead_transitions() if hasattr(kb, 'get_dead_transitions') else []
        
        if dead_transitions:
            for trans_id in dead_transitions[:5]:  # Limit to first 5
                # Skip if already added as inactive
                if any(issue.element_id == trans_id for issue in issues):
                    continue
                
                # Get human-readable name
                trans_name = self._get_human_readable_name(kb, trans_id, "transition")
                    
                issue = Issue(
                    id=f"dead_{trans_id}",
                    category="structural",
                    severity="critical",
                    title=f"{trans_name} is DEAD (topology)",
                    description="This transition can never fire structurally, blocking pathway execution",
                    element_id=trans_id,
                    element_type="transition",
                    locality_id=self.selected_locality_id
                )
                
                # Add suggestion to fix initial marking
                suggestion = Suggestion(
                    action="add_source",
                    category="structural",
                    parameters={"transition_id": trans_id, "rate": 1.0},
                    confidence=0.80,
                    reasoning=f"Add source transition to {trans_name} to enable firing",
                    preview_elements=[trans_id]
                )
                issue.suggestions.append(suggestion)
                issues.append(issue)
        
        return issues
    
    def _scan_biological_issues(self, kb) -> List[Issue]:
        """Scan for biological issues.
        
        Args:
            kb: Knowledge base
            
        Returns:
            List[Issue]: Biological issues with suggestions
        """
        issues = []
        
        # Check for places without compound mappings
        for place_id, place_obj in kb.places.items():
            has_compound = hasattr(place_obj, 'compound_id') and place_obj.compound_id
            
            if not has_compound:
                place_name = self._get_human_readable_name(kb, place_id, "place")
                
                issue = Issue(
                    id=f"no_compound_{place_id}",
                    category="biological",
                    severity="info",
                    title=f"{place_name} not mapped to compound",
                    description=f"Place lacks biological compound annotation",
                    element_id=place_id,
                    element_type="place",
                    locality_id=self.selected_locality_id
                )
                
                # Add suggestion to map compound
                suggestion = Suggestion(
                    action="map_compound",
                    category="biological",
                    parameters={"place_id": place_id},
                    confidence=0.60,
                    reasoning=f"Map {place_name} to KEGG compound for pathway validation",
                    preview_elements=[place_id]
                )
                issue.suggestions.append(suggestion)
                issues.append(issue)
        
        return issues
    
    def _scan_kinetic_issues(self, kb) -> List[Issue]:
        """Scan for kinetic issues.
        
        Args:
            kb: Knowledge base
            
        Returns:
            List[Issue]: Kinetic issues with suggestions
        """
        issues = []
        
        # Check for transitions without rates
        for trans_id, trans_obj in kb.transitions.items():
            has_rate = hasattr(trans_obj, 'rate') and trans_obj.rate is not None and trans_obj.rate > 0
            
            if not has_rate:
                trans_name = self._get_human_readable_name(kb, trans_id, "transition")
                
                issue = Issue(
                    id=f"no_rate_{trans_id}",
                    category="kinetic",
                    severity="warning",
                    title=f"{trans_name} has no firing rate",
                    description=f"Transition lacks kinetic parameters for timed simulation",
                    element_id=trans_id,
                    element_type="transition",
                    locality_id=self.selected_locality_id
                )
                
                # Add suggestion to query BRENDA
                suggestion = Suggestion(
                    action="query_brenda",
                    category="kinetic",
                    parameters={"transition_id": trans_id},
                    confidence=0.70,
                    reasoning=f"Query BRENDA database for {trans_name} kinetic parameters",
                    preview_elements=[trans_id]
                )
                issue.suggestions.append(suggestion)
                issues.append(issue)
        
        return issues
        return []
    
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
    
    def _refresh(self):
        """Refresh diagnosis category content.
        
        Returns:
            False: To stop GLib.idle_add from repeating
        """
        # Re-scan issues if category is expanded
        if self.category_frame.expanded:
            self._on_run_full_diagnose_clicked(None)
        return False
