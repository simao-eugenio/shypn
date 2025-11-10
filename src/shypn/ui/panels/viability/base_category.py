#!/usr/bin/env python3
"""Base Category for Viability Panel.

Provides common infrastructure for all viability categories
(Structural, Biological, Kinetic, Diagnosis).

Author: Simão Eugénio
Date: November 10, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Optional, List, Dict, Any

from shypn.ui.category_frame import CategoryFrame
from .viability_dataclasses import Issue, Suggestion, Change


class BaseViabilityCategory:
    """Base class for viability analysis categories.
    
    Provides:
    - Expandable category frame (like topology categories)
    - Knowledge base access
    - Locality filtering support
    - Issue display infrastructure
    - Apply/Preview/Undo buttons
    
    Subclasses implement:
    - _build_content(): Create category-specific UI
    - _scan_issues(): Run category-specific analysis
    - _refresh(): Update UI with current data
    """
    
    def __init__(self, model_canvas=None, expanded=False):
        """Initialize base category.
        
        Args:
            model_canvas: ModelCanvas instance for accessing model and KB
            expanded: Whether category starts expanded
        """
        self.model_canvas = model_canvas
        self.parent_panel = None  # Will be set by parent ViabilityPanel
        
        # Issue tracking (using dataclasses)
        self.current_issues: List[Issue] = []
        self.selected_locality_id = None  # None = full model
        
        # Undo stack (using Change dataclass)
        self.change_history: List[Change] = []
        
        # UI Components
        self.category_frame = None
        self.content_box = None
        self.issues_listbox = None
        self.scan_button = None
        self.undo_button = None
        
        # Build UI using CategoryFrame
        self._build_frame(expanded)
    
    def _build_frame(self, expanded):
        """Build category frame using CategoryFrame widget.
        
        Args:
            expanded: Whether to start expanded
        """
        # Use CategoryFrame for consistent styling with other panels
        self.category_frame = CategoryFrame(
            title=self.get_category_name(),
            expanded=expanded
        )
        
        # Main content box
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_margin_start(12)
        self.content_box.set_margin_end(12)
        self.content_box.set_margin_top(12)
        self.content_box.set_margin_bottom(12)
        
        # Build category-specific content
        self._build_content()
        
        # Set content in CategoryFrame
        self.category_frame.set_content(self.content_box)
    
    def get_widget(self):
        """Get the main widget for this category.
        
        Returns:
            CategoryFrame: The category frame
        """
        return self.category_frame
    
    def get_category_name(self):
        """Get category display name.
        
        Subclasses must override.
        
        Returns:
            str: Category name with emoji
        """
        raise NotImplementedError("Subclass must implement get_category_name()")
    
    def get_knowledge_base(self):
        """Get the knowledge base for the current model.
        
        Returns:
            ModelKnowledgeBase: The knowledge base, or None
        """
        print(f"[BaseCategory] get_knowledge_base() called")
        print(f"  model_canvas: {self.model_canvas}")
        print(f"  has get_current_knowledge_base: {hasattr(self.model_canvas, 'get_current_knowledge_base') if self.model_canvas else False}")
        
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_knowledge_base'):
            kb = self.model_canvas.get_current_knowledge_base()
            print(f"  KB returned: {kb}")
            if kb:
                print(f"  KB has {len(kb.places)} places, {len(kb.transitions)} transitions")
                return kb
        print(f"  Returning None")
        return None
    
    def _build_content(self):
        """Build category-specific content.
        
        Subclasses must override to create their UI.
        """
        raise NotImplementedError("Subclass must implement _build_content()")
    
    def _on_expansion_changed(self, expander, param):
        """Handle expander state change.
        
        When a category is expanded, automatically scan for issues.
        
        Args:
            expander: Gtk.Expander that changed
            param: Parameter spec (not used)
        """
        if expander.get_expanded():
            # Category was expanded - automatically scan
            print(f"[{self.get_category_name()}] Category expanded, auto-scanning...")
            GLib.idle_add(self._on_scan_clicked, None)
    
    def _refresh(self):
        """Refresh category content.
        
        Subclasses should override to update their UI.
        
        Returns:
            False: To stop GLib.idle_add from repeating
        """
        return False
    
    def _scan_issues(self):
        """Scan for category-specific issues.
        
        Must be implemented by subclasses.
        
        Returns:
            List[Issue]: List of Issue dataclass instances
        """
        raise NotImplementedError("Subclass must implement _scan_issues()")
    
    def _create_action_buttons(self):
        """Create common action buttons (Scan, Undo, etc.).
        
        Returns:
            Gtk.Box: Button box
        """
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.START)
        
        # Scan button
        self.scan_button = Gtk.Button(label="SCAN FOR ISSUES")
        self.scan_button.connect('clicked', self._on_scan_clicked)
        button_box.pack_start(self.scan_button, False, False, 0)
        
        # Undo button
        self.undo_button = Gtk.Button(label="UNDO LAST")
        self.undo_button.set_sensitive(False)  # Initially disabled
        self.undo_button.connect('clicked', self._on_undo_clicked)
        button_box.pack_start(self.undo_button, False, False, 0)
        
        # Clear button
        clear_button = Gtk.Button(label="CLEAR ALL")
        clear_button.connect('clicked', self._on_clear_clicked)
        button_box.pack_start(clear_button, False, False, 0)
        
        return button_box
    
    def _on_scan_clicked(self, button):
        """Handle scan button click.
        
        Args:
            button: Button that was clicked
        """
        # Clear previous issues
        self.current_issues = []
        
        # Scan for new issues
        issues = self._scan_issues()
        
        if issues:
            self.current_issues = issues
            self._display_issues(issues)
            print(f"[{self.get_category_name()}] Found {len(issues)} issues")
        else:
            self._show_no_issues_message()
            print(f"[{self.get_category_name()}] No issues found")
    
    def _on_undo_clicked(self, button):
        """Handle undo button click.
        
        Args:
            button: Button that was clicked
        """
        if self.change_history:
            change = self.change_history.pop()
            self._apply_undo(change)
            
            # Disable undo button if history is empty
            if not self.change_history:
                self.undo_button.set_sensitive(False)
            
            print(f"[{self.get_category_name()}] Undid change: {change}")
    
    def _on_clear_clicked(self, button):
        """Handle clear button click.
        
        Args:
            button: Button that was clicked
        """
        self.current_issues = []
        if self.issues_listbox:
            # Clear all rows
            for child in self.issues_listbox.get_children():
                self.issues_listbox.remove(child)
    
    def _display_issues(self, issues: List[Issue]):
        """Display issues in the UI.
        
        Args:
            issues: List of Issue dataclass instances
        """
        if not self.issues_listbox:
            return
        
        # Clear existing rows
        for child in self.issues_listbox.get_children():
            self.issues_listbox.remove(child)
        
        if not issues:
            self._show_no_issues_message()
            return
        
        # Add issue rows
        for issue in issues:
            row = self._create_issue_row(issue)
            self.issues_listbox.add(row)
        
        self.issues_listbox.show_all()
    
    def _create_issue_row(self, issue: Issue) -> Gtk.ListBoxRow:
        """Create a ListBoxRow for an issue.
        
        Args:
            issue: Issue dataclass instance
            
        Returns:
            Gtk.ListBoxRow with issue details
        """
        row = Gtk.ListBoxRow()
        row.set_selectable(False)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Title with severity icon
        severity_icons = {
            "critical": "🔴",
            "warning": "⚠️",
            "info": "💡"
        }
        icon = severity_icons.get(issue.severity, "")
        
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{icon} {issue.title}</b>")
        title_label.set_xalign(0)
        box.pack_start(title_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label(label=issue.description)
        desc_label.set_line_wrap(True)
        desc_label.set_xalign(0)
        box.pack_start(desc_label, False, False, 0)
        
        # Suggestions (if any)
        if issue.suggestions:
            for suggestion in issue.suggestions:
                suggestion_widget = self._create_suggestion_widget(suggestion, issue)
                box.pack_start(suggestion_widget, False, False, 0)
        
        row.add(box)
        return row
    
    def _create_suggestion_widget(self, suggestion: Suggestion, issue: Issue) -> Gtk.Widget:
        """Create a widget for a suggestion.
        
        Args:
            suggestion: Suggestion dataclass instance
            issue: Parent Issue instance
            
        Returns:
            Gtk.Widget with suggestion details and action buttons
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        box.set_margin_start(20)
        box.set_margin_top(6)
        
        # Reasoning
        reason_label = Gtk.Label()
        reason_label.set_markup(f"<i>{suggestion.reasoning}</i> ({suggestion.confidence:.0%} confidence)")
        reason_label.set_line_wrap(True)
        reason_label.set_xalign(0)
        box.pack_start(reason_label, False, False, 0)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_margin_top(3)
        
        apply_button = Gtk.Button(label="Apply")
        apply_button.connect('clicked', self._on_apply_suggestion, suggestion, issue)
        button_box.pack_start(apply_button, False, False, 0)
        
        preview_button = Gtk.Button(label="Preview")
        preview_button.connect('clicked', self._on_preview_suggestion, suggestion)
        button_box.pack_start(preview_button, False, False, 0)
        
        box.pack_start(button_box, False, False, 0)
        
        return box
    
    def _on_apply_suggestion(self, button, suggestion: Suggestion, issue: Issue):
        """Handle Apply button click for a suggestion.
        
        Uses KB inference methods to apply the suggestion and records
        the change for undo.
        
        Args:
            button: Button that was clicked
            suggestion: Suggestion to apply
            issue: Parent issue
        """
        kb = self.get_knowledge_base()
        if not kb:
            print(f"[{self.get_category_name()}] ⚠️ Cannot apply: No KB available")
            return
        
        print(f"[{self.get_category_name()}] Applying suggestion: {suggestion.action}")
        print(f"  Category: {suggestion.category}, Element: {issue.element_id}")
        
        # Get the model for direct updates
        manager = None
        if self.model_canvas:
            drawing_area = self.model_canvas.get_current_document()
            if drawing_area:
                manager = self.model_canvas.get_canvas_manager(drawing_area)
        
        # Apply based on action type
        try:
            if suggestion.action == "add_initial_marking":
                self._apply_add_initial_marking(suggestion, issue, kb, manager)
            elif suggestion.action == "add_source_transition":
                self._apply_add_source_transition(suggestion, issue, kb, manager)
            elif suggestion.action == "add_firing_rate":
                self._apply_add_firing_rate(suggestion, issue, kb, manager)
            elif suggestion.action == "add_arc_weight":
                self._apply_add_arc_weight(suggestion, issue, kb, manager)
            else:
                print(f"  ⚠️ Unknown action: {suggestion.action}")
                return
            
            # Refresh display after successful application
            GLib.idle_add(self._refresh)
            print(f"  ✅ Applied successfully")
            
        except Exception as e:
            print(f"  ❌ Error applying suggestion: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_preview_suggestion(self, button, suggestion: Suggestion):
        """Handle Preview button click for a suggestion.
        
        Temporarily highlights the elements affected by this suggestion on the canvas.
        
        Args:
            button: Button that was clicked
            suggestion: Suggestion to preview
        """
        print(f"[{self.get_category_name()}] Preview suggestion: {suggestion.action}")
        print(f"  Highlight elements: {suggestion.preview_elements}")
        
        # Get canvas manager for highlighting
        if not self.model_canvas:
            print(f"  ⚠️ No model_canvas available for preview")
            return
        
        drawing_area = self.model_canvas.get_current_document()
        if not drawing_area:
            print(f"  ⚠️ No active drawing area")
            return
        
        manager = self.model_canvas.get_canvas_manager(drawing_area)
        if not manager:
            print(f"  ⚠️ No canvas manager available")
            return
        
        # Temporarily highlight preview elements (yellow glow)
        self._highlight_preview_elements(manager, drawing_area, suggestion.preview_elements)
        
        # Auto-clear after 3 seconds
        GLib.timeout_add(3000, lambda: self._clear_preview_highlights(manager, drawing_area))
    
    def _highlight_preview_elements(self, manager, drawing_area, element_ids):
        """Highlight elements on canvas for preview.
        
        Args:
            manager: Canvas manager
            drawing_area: Drawing area widget
            element_ids: List of element IDs to highlight
        """
        if not element_ids:
            return
        
        # Store old selection state
        if not hasattr(self, '_preview_old_selection'):
            self._preview_old_selection = {}
        
        # Clear existing selection
        manager.selection_manager.clear_selection()
        
        # Highlight preview elements (yellow) by temporarily selecting them
        for element_id in element_ids:
            # Find element
            element = None
            for p in manager.places:
                if p.id == element_id:
                    element = p
                    break
            if not element:
                for t in manager.transitions:
                    if t.id == element_id:
                        element = t
                        break
            if not element:
                for a in manager.arcs:
                    if a.id == element_id:
                        element = a
                        break
            
            if element:
                # Store old selection state
                self._preview_old_selection[element_id] = getattr(element, 'selected', False)
                # Mark as selected (will be rendered with selection color)
                element.selected = True
                print(f"  Highlighted: {element_id}")
        
        # Trigger redraw
        drawing_area.queue_draw()
    
    def _clear_preview_highlights(self, manager, drawing_area):
        """Clear preview highlights.
        
        Args:
            manager: Canvas manager
            drawing_area: Drawing area widget
        """
        if not hasattr(self, '_preview_old_selection'):
            return False
        
        # Restore old selection state
        for element_id, was_selected in self._preview_old_selection.items():
            # Find element
            element = None
            for p in manager.places:
                if p.id == element_id:
                    element = p
                    break
            if not element:
                for t in manager.transitions:
                    if t.id == element_id:
                        element = t
                        break
            if not element:
                for a in manager.arcs:
                    if a.id == element_id:
                        element = a
                        break
            
            if element:
                element.selected = was_selected
        
        # Clear stored state
        self._preview_old_selection = {}
        
        # Trigger redraw
        drawing_area.queue_draw()
        print(f"[{self.get_category_name()}] Preview highlights cleared")
        
        return False  # Don't repeat timeout
    
    # ============================================================================
    # Suggestion Application Methods
    # ============================================================================
    
    def _apply_add_initial_marking(self, suggestion, issue, kb, manager):
        """Apply 'add_initial_marking' suggestion.
        
        Args:
            suggestion: Suggestion with parameters
            issue: Parent issue
            kb: Knowledge base
            manager: Canvas manager
        """
        place_id = issue.element_id
        tokens = suggestion.parameters.get('tokens', 0)
        
        print(f"  Setting initial marking: {place_id} = {tokens} tokens")
        
        # Get current marking for undo
        place = kb.places.get(place_id)
        if not place:
            print(f"  ⚠️ Place {place_id} not found in KB")
            return
        
        old_marking = place.current_marking
        
        # Update KB
        place.current_marking = tokens
        
        # Update model if manager is available
        if manager:
            for p in manager.places:
                if p.id == place_id:
                    p.tokens = tokens
                    print(f"  Updated model place {place_id}: {old_marking} → {tokens} tokens")
                    break
        
        # Record change for undo
        change = Change(
            element_id=place_id,
            property="current_marking",
            old_value=old_marking,
            new_value=tokens,
            category=suggestion.category,
            locality_id=self.selected_locality_id
        )
        self._record_change(change)
    
    def _apply_add_source_transition(self, suggestion, issue, kb, manager):
        """Apply 'add_source_transition' suggestion.
        
        This creates a new transition and arc to add tokens to a place.
        
        Args:
            suggestion: Suggestion with parameters
            issue: Parent issue
            kb: Knowledge base
            manager: Canvas manager
        """
        place_id = issue.element_id
        tokens = suggestion.parameters.get('tokens', 5)
        
        print(f"  Adding source transition for {place_id} with {tokens} tokens/firing")
        
        # For now, just suggest using initial marking instead
        # (Creating new elements requires more complex canvas integration)
        print(f"  ⚠️ Creating new transitions not yet implemented")
        print(f"  💡 Consider using 'add_initial_marking' instead")
    
    def _apply_add_firing_rate(self, suggestion, issue, kb, manager):
        """Apply 'add_firing_rate' suggestion.
        
        Args:
            suggestion: Suggestion with parameters
            issue: Parent issue
            kb: Knowledge base
            manager: Canvas manager
        """
        transition_id = issue.element_id
        rate = suggestion.parameters.get('rate', 1.0)
        
        print(f"  Setting firing rate: {transition_id} = {rate}")
        
        # Get current rate for undo
        transition = kb.transitions.get(transition_id)
        if not transition:
            print(f"  ⚠️ Transition {transition_id} not found in KB")
            return
        
        old_rate = transition.firing_rate
        
        # Update KB
        transition.firing_rate = rate
        
        # Update model if manager is available
        if manager:
            for t in manager.transitions:
                if t.id == transition_id:
                    # Store rate in transition metadata
                    if not hasattr(t, 'metadata'):
                        t.metadata = {}
                    t.metadata['firing_rate'] = rate
                    print(f"  Updated model transition {transition_id}: {old_rate} → {rate}")
                    break
        
        # Record change for undo
        change = Change(
            element_id=transition_id,
            property="firing_rate",
            old_value=old_rate,
            new_value=rate,
            category=suggestion.category,
            locality_id=self.selected_locality_id
        )
        self._record_change(change)
    
    def _apply_add_arc_weight(self, suggestion, issue, kb, manager):
        """Apply 'add_arc_weight' suggestion.
        
        Args:
            suggestion: Suggestion with parameters
            issue: Parent issue
            kb: Knowledge base
            manager: Canvas manager
        """
        arc_id = issue.element_id
        weight = suggestion.parameters.get('weight', 1)
        
        print(f"  Setting arc weight: {arc_id} = {weight}")
        
        # Get current weight for undo
        arc = kb.arcs.get(arc_id)
        if not arc:
            print(f"  ⚠️ Arc {arc_id} not found in KB")
            return
        
        old_weight = arc.weight
        
        # Update KB
        arc.weight = weight
        
        # Update model if manager is available
        if manager:
            for a in manager.arcs:
                if a.id == arc_id:
                    a.weight = weight
                    print(f"  Updated model arc {arc_id}: {old_weight} → {weight}")
                    break
        
        # Record change for undo
        change = Change(
            element_id=arc_id,
            property="weight",
            old_value=old_weight,
            new_value=weight,
            category=suggestion.category,
            locality_id=self.selected_locality_id
        )
        self._record_change(change)
    
    def _show_no_issues_message(self):
        """Show message when no issues are found."""
        if self.issues_listbox:
            # Clear existing content
            for child in self.issues_listbox.get_children():
                self.issues_listbox.remove(child)
            
            # Add "no issues" message
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="NO ISSUES DETECTED")
            label.set_margin_start(12)
            label.set_margin_end(12)
            label.set_margin_top(12)
            label.set_margin_bottom(12)
            row.add(label)
            self.issues_listbox.add(row)
            self.issues_listbox.show_all()
    
    def _apply_undo(self, change: Change):
        """Apply an undo operation.
        
        Reverts the change to its old value and updates both KB and model.
        
        Args:
            change: Change dataclass instance to undo
        """
        kb = self.get_knowledge_base()
        if not kb:
            print(f"[{self.get_category_name()}] ⚠️ Cannot undo: No KB available")
            return
        
        print(f"[{self.get_category_name()}] Undo: {change.element_id}.{change.property}")
        print(f"  Reverting: {change.new_value} → {change.old_value}")
        
        # Get the model for direct updates
        manager = None
        if self.model_canvas:
            drawing_area = self.model_canvas.get_current_document()
            if drawing_area:
                manager = self.model_canvas.get_canvas_manager(drawing_area)
        
        try:
            # Update based on property type
            if change.property == "current_marking":
                place = kb.places.get(change.element_id)
                if place:
                    place.current_marking = change.old_value
                    # Update model
                    if manager:
                        for p in manager.places:
                            if p.id == change.element_id:
                                p.tokens = change.old_value
                                break
                                
            elif change.property == "firing_rate":
                transition = kb.transitions.get(change.element_id)
                if transition:
                    transition.firing_rate = change.old_value
                    # Update model
                    if manager:
                        for t in manager.transitions:
                            if t.id == change.element_id:
                                if hasattr(t, 'metadata'):
                                    t.metadata['firing_rate'] = change.old_value
                                break
                                
            elif change.property == "weight":
                arc = kb.arcs.get(change.element_id)
                if arc:
                    arc.weight = change.old_value
                    # Update model
                    if manager:
                        for a in manager.arcs:
                            if a.id == change.element_id:
                                a.weight = change.old_value
                                break
            
            # Remove from history
            if change in self.change_history:
                self.change_history.remove(change)
            
            # Disable undo button if no more changes
            if not self.change_history:
                self.undo_button.set_sensitive(False)
            
            # Refresh display
            GLib.idle_add(self._refresh)
            print(f"  ✅ Undo successful")
            
        except Exception as e:
            print(f"  ❌ Error during undo: {e}")
            import traceback
            traceback.print_exc()
    
    def _record_change(self, change: Change):
        """Record a change to the undo history.
        
        Args:
            change: Change dataclass instance to record
        """
        self.change_history.append(change)
        self.undo_button.set_sensitive(True)
        print(f"[{self.get_category_name()}] Recorded change: {change}")
    
    def set_locality(self, locality_id):
        """Set the locality filter for this category.
        
        Args:
            locality_id: Locality ID, or None for full model
        """
        self.selected_locality_id = locality_id
        # Refresh if category is expanded
        if self.category_frame and self.category_frame.is_expanded():
            GLib.idle_add(self._refresh)
