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
        self.locality_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
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
        """Handle locality list row selection.
        
        Args:
            listbox: ListBox that fired the signal
            row: Selected ListBoxRow (or None)
        """
        if row:
            # Get the transition and locality objects stored in the row
            transition = getattr(row, 'transition_obj', None)
            locality = getattr(row, 'locality_obj', None)
            
            if transition:
                self.selected_transition = transition
                self.selected_locality = locality
                self.selected_locality_id = transition.id
                print(f"[DiagnosisCategory] Selected transition: {transition.id}")
                # Enable RUN SELECTED and CLEAR buttons
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
    
    def _on_clear_selection_clicked(self, button):
        """Handle CLEAR button click - clear locality listbox selection.
        
        Args:
            button: Button that was clicked
        """
        print("[DiagnosisCategory] Clearing locality selection")
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
            print("[DiagnosisCategory] No locality selected")
            return
        
        print(f"[DiagnosisCategory] Running diagnosis for locality: {self.selected_transition.id}")
        self._run_selected_diagnosis()
    
    def _on_run_full_diagnose_clicked(self, button):
        """Handle RUN FULL DIAGNOSE button click - run diagnosis on entire model.
        
        This triggers the parent panel's on_analyze_all method which was previously
        connected to the header button.
        
        Args:
            button: Button that was clicked
        """
        print("[DiagnosisCategory] Running full model diagnosis")
        
        # Clear any locality scope
        self.selected_locality_id = None
        
        # Trigger parent panel's analyze all (batch mode)
        if hasattr(self, 'parent_panel') and self.parent_panel:
            if hasattr(self.parent_panel, 'on_analyze_all'):
                self.parent_panel.on_analyze_all(button)
            else:
                print("[DiagnosisCategory] Warning: parent_panel has no on_analyze_all method")
        else:
            print("[DiagnosisCategory] Warning: No parent_panel available")
    
    def _run_selected_diagnosis(self):
        """Run diagnosis scoped to the selected locality.
        
        This will:
        1. Analyze the selected transition and its locality (input/output places)
        2. Populate all category suggestions filtered to this scope
        3. Trigger all categories to show suggestions for this locality
        """
        if not self.selected_transition or not self.selected_locality:
            print("[DiagnosisCategory] No locality selected for diagnosis")
            return
        
        print(f"[DiagnosisCategory] Running scoped diagnosis for transition: {self.selected_transition.id}")
        
        # Store the scope for this diagnosis
        kb = self.get_knowledge_base()
        if not kb:
            print("[DiagnosisCategory] No knowledge base available")
            return
        
        # Set the locality scope for filtering
        self.selected_locality_id = self.selected_transition.id
        
        # Run diagnosis (will use selected_locality_id for filtering)
        issues = self._scan_issues()
        
        # Display issues
        self._display_issues(issues)
        
        # Notify parent panel to trigger other categories with locality scope
        if hasattr(self, 'parent_panel') and self.parent_panel:
            print(f"[DiagnosisCategory] Notifying parent to scan with locality: {self.selected_transition.id}")
            # Trigger other categories to scan with this locality scope
            for category in self.parent_panel.categories:
                if category != self and hasattr(category, 'scan_with_locality'):
                    category.scan_with_locality(
                        transition=self.selected_transition,
                        locality=self.selected_locality
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
        print(f"[DIAGNOSIS_CATEGORY] add_transition_for_analysis called with: {transition.id}")
        
        # Get model
        model = None
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_model'):
            model = self.model_canvas.get_current_model()
        
        if not model:
            print("[DIAGNOSIS_CATEGORY] No model available")
            return
        
        # Use LocalityDetector to get THIS transition's locality (same as plotting)
        from shypn.diagnostic.locality_detector import LocalityDetector
        detector = LocalityDetector(model)
        locality = detector.get_locality_for_transition(transition)
        
        if not locality.is_valid:
            print(f"[DIAGNOSIS_CATEGORY] Transition {transition.id} has no valid locality")
            return
        
        print(f"[DIAGNOSIS_CATEGORY] Locality for {transition.id}: {len(locality.input_places)} inputs, {len(locality.output_places)} outputs")
        
        # Check if this transition is already in the list
        for child in self.locality_listbox.get_children():
            trans_obj = getattr(child, 'transition_obj', None)
            if trans_obj and trans_obj.id == transition.id:
                print(f"[DIAGNOSIS_CATEGORY] Transition {transition.id} already in list")
                return
        
        # Add this transition with its locality places (hierarchical display)
        self._add_transition_with_locality_to_list(transition, locality)
        
        # Switch to locality mode
        self.locality_radio.set_active(True)
        self.locality_listbox.set_sensitive(True)
        
        print(f"[DIAGNOSIS_CATEGORY] ✓ Added transition {transition.id} with locality to list")
    
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
        print(f"[DIAGNOSIS_CATEGORY] Removing transition {transition.id} and its places")
        
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
        print("[DIAGNOSIS_CATEGORY] _populate_localities called")
        
        # Clear existing rows
        for child in self.locality_listbox.get_children():
            self.locality_listbox.remove(child)
        
        # Get model
        model = None
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_model'):
            model = self.model_canvas.get_current_model()
        
        if not model or not hasattr(model, 'transitions'):
            print("[DIAGNOSIS_CATEGORY] No model available")
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
        
        print(f"[DIAGNOSIS_CATEGORY] Model has {len(model.transitions)} transitions")
        
        # Use LocalityDetector to get all valid localities (same as plotting)
        from shypn.diagnostic.locality_detector import LocalityDetector
        detector = LocalityDetector(model)
        localities = detector.get_all_localities()
        
        print(f"[DIAGNOSIS_CATEGORY] LocalityDetector found {len(localities)} valid localities")
        
        if not localities:
            print("[DIAGNOSIS_CATEGORY] No valid localities found")
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
                
                print(f"[DIAGNOSIS_CATEGORY] Adding {trans_id}: {len(locality.input_places)} inputs, {len(locality.output_places)} outputs")
                
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
            print(f"[DIAGNOSIS_CATEGORY] Added {len(localities)} localities to listbox")
        
        self.locality_listbox.show_all()
        print(f"[DIAGNOSIS_CATEGORY] _populate_localities complete")
    
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
            print(f"[DIAGNOSIS_CATEGORY] Getting locality for transition: {trans_id}")
            
            # Get model
            if not self.model_canvas or not hasattr(self.model_canvas, 'get_current_model'):
                print(f"[DIAGNOSIS_CATEGORY] No model_canvas available")
                return None
            
            model = self.model_canvas.get_current_model()
            if not model or not hasattr(model, 'arcs'):
                print(f"[DIAGNOSIS_CATEGORY] No model or model has no arcs")
                return None
            
            # Scan all arcs to find those connected to this transition
            input_places = []
            output_places = []
            input_arcs = []
            output_arcs = []
            
            print(f"[DIAGNOSIS_CATEGORY] Scanning {len(model.arcs)} arcs...")
            
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
                        print(f"[DIAGNOSIS_CATEGORY]   Input: {place_id} → {trans_id}")
                
                # Output arc: transition → place
                elif arc.source == transition:
                    output_arcs.append(arc)
                    if arc.target not in output_places:
                        output_places.append(arc.target)
                        place_id = arc.target.id if hasattr(arc.target, 'id') else 'unknown'
                        print(f"[DIAGNOSIS_CATEGORY]   Output: {trans_id} → {place_id}")
            
            print(f"[DIAGNOSIS_CATEGORY] Locality for {trans_id}: {len(input_places)} inputs, {len(output_places)} outputs")
            
            if not input_places and not output_places:
                print(f"[DIAGNOSIS_CATEGORY] WARNING: No places found for transition {trans_id}")
                return None
            
            return Locality(
                transition=transition,
                input_places=input_places,
                output_places=output_places,
                input_arcs=input_arcs,
                output_arcs=output_arcs
            )
        except Exception as e:
            print(f"[DIAGNOSIS_CATEGORY] Error getting locality: {e}")
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
        
        # DEBUG: Check KB state
        
        # Update multi-domain engine with current KB
        self.multi_domain_engine.kb = kb
        
        issues = []
        
        # Calculate health scores
        structural_health = self._calculate_structural_health(kb)
        biological_health = self._calculate_biological_health(kb)
        kinetic_health = self._calculate_kinetic_health(kb)
        overall_health = (structural_health + biological_health + kinetic_health) / 3
        
        # Update health display
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
        
        # Check for dead transitions
        dead_transitions = kb.get_dead_transitions() if hasattr(kb, 'get_dead_transitions') else []
        if dead_transitions:
            for trans_id in dead_transitions[:5]:  # Limit to first 5
                issue = Issue(
                    id=f"dead_{trans_id}",
                    category="structural",
                    severity="critical",
                    title=f"Transition {trans_id} is DEAD",
                    description="This transition can never fire, blocking pathway execution",
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
                    reasoning="Add source transition to enable firing",
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
        # TODO: Query KB for unmapped compounds, stoichiometry mismatches
        return []
    
    def _scan_kinetic_issues(self, kb) -> List[Issue]:
        """Scan for kinetic issues.
        
        Args:
            kb: Knowledge base
            
        Returns:
            List[Issue]: Kinetic issues with suggestions
        """
        # TODO: Query KB for missing rates, low confidence parameters
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
