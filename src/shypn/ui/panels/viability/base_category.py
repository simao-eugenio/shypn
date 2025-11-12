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
        
        # Locality scope tracking (for filtered scans)
        self.scoped_transition = None
        self.scoped_locality = None
        
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
        
        # Show all widgets
        self.content_box.show_all()
        
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
        
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_knowledge_base'):
            kb = self.model_canvas.get_current_knowledge_base()
            if kb:
                return kb
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
        """Create common action buttons (Scan, Clear).
        
        Returns:
            Gtk.Box: Button box
        """
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.START)
        
        # Scan button
        self.scan_button = Gtk.Button(label="SCAN FOR ISSUES")
        self.scan_button.connect('clicked', self._on_scan_clicked)
        button_box.pack_start(self.scan_button, False, False, 0)
        
        # Clear button
        clear_button = Gtk.Button(label="CLEAR ALL")
        clear_button.connect('clicked', self._on_clear_clicked)
        button_box.pack_start(clear_button, False, False, 0)
        
        return button_box
    
    def _create_issues_treeview(self):
        """Create TreeView for displaying issues with selection checkboxes.
        
        Creates a table with columns:
        - [☐] Selection checkbox
        - Icon (severity indicator)
        - Title
        - Description
        - Confidence
        
        Returns:
            tuple: (scrolled_window, treeview, liststore)
        """
        # Create ListStore: Selected, Icon, Title, Description, Confidence, Issue object
        self.issues_store = Gtk.ListStore(
            bool,      # 0: Selected
            str,       # 1: Icon
            str,       # 2: Title
            str,       # 3: Description
            str,       # 4: Confidence
            object     # 5: Issue object
        )
        
        # Create TreeView
        self.issues_tree = Gtk.TreeView(model=self.issues_store)
        self.issues_tree.set_headers_visible(True)
        self.issues_tree.set_enable_search(False)
        
        # Selection column with checkbox
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.set_activatable(True)
        renderer_toggle.connect('toggled', self._on_issue_selection_toggled)
        
        column_select = Gtk.TreeViewColumn("☐", renderer_toggle, active=0)
        column_select.set_fixed_width(40)
        column_select.set_clickable(True)
        column_select.connect('clicked', self._on_header_column_clicked)
        self.issues_tree.append_column(column_select)
        
        # Store reference for updating header label
        self.select_column = column_select
        self._all_selected = False
        
        # Icon column
        renderer_icon = Gtk.CellRendererText()
        column_icon = Gtk.TreeViewColumn("", renderer_icon, text=1)
        column_icon.set_fixed_width(40)
        column_icon.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.issues_tree.append_column(column_icon)
        
        # Title column
        renderer_title = Gtk.CellRendererText()
        renderer_title.set_property("weight", 600)  # Bold
        column_title = Gtk.TreeViewColumn("Issue", renderer_title, text=2)
        column_title.set_resizable(True)
        column_title.set_fixed_width(200)
        column_title.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.issues_tree.append_column(column_title)
        
        # Description column
        renderer_desc = Gtk.CellRendererText()
        renderer_desc.set_property("wrap-mode", 2)  # Word wrap
        renderer_desc.set_property("wrap-width", 300)
        column_desc = Gtk.TreeViewColumn("Description", renderer_desc, text=3)
        column_desc.set_resizable(True)
        column_desc.set_expand(True)
        self.issues_tree.append_column(column_desc)
        
        # Confidence column
        renderer_conf = Gtk.CellRendererText()
        column_conf = Gtk.TreeViewColumn("Confidence", renderer_conf, text=4)
        column_conf.set_fixed_width(100)
        column_conf.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.issues_tree.append_column(column_conf)
        
        # Wrap in ScrolledWindow
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.add(self.issues_tree)
        
        return scrolled, self.issues_tree, self.issues_store
    
    def _on_issue_selection_toggled(self, renderer, path):
        """Handle selection checkbox toggle for an issue row.
        
        Args:
            renderer: CellRendererToggle
            path: Tree path string
        """
        # Toggle the selected state
        iter = self.issues_store.get_iter(path)
        current_value = self.issues_store.get_value(iter, 0)
        new_value = not current_value
        self.issues_store.set_value(iter, 0, new_value)
        
        # Update button sensitivity and header based on selection
        has_selection = False
        all_selected = True
        total_rows = 0
        iter = self.issues_store.get_iter_first()
        while iter:
            total_rows += 1
            selected = self.issues_store.get_value(iter, 0)
            if selected:
                has_selection = True
            else:
                all_selected = False
            iter = self.issues_store.iter_next(iter)
        
        # Update header label based on selection state
        if all_selected and total_rows > 0:
            self.select_column.set_title("☑")  # All checked
            self._all_selected = True
        elif has_selection:
            self.select_column.set_title("☒")  # Some checked (indeterminate)
            self._all_selected = False
        else:
            self.select_column.set_title("☐")  # None checked
            self._all_selected = False
        
        # Update repair button sensitivity
        if hasattr(self, 'repair_button'):
            self.repair_button.set_sensitive(has_selection)
    
    def _on_header_column_clicked(self, column):
        """Handle header column click (select/deselect all issues).
        
        Args:
            column: The TreeViewColumn that was clicked
        """
        # Toggle selection state
        self._all_selected = not self._all_selected
        
        # Update all checkboxes
        iter = self.issues_store.get_iter_first()
        while iter:
            self.issues_store.set_value(iter, 0, self._all_selected)
            iter = self.issues_store.iter_next(iter)
        
        # Update header label
        if self._all_selected:
            column.set_title("☑")  # Checked
        else:
            column.set_title("☐")  # Unchecked
        
        # Update repair button sensitivity
        if hasattr(self, 'repair_button'):
            self.repair_button.set_sensitive(self._all_selected)
    
    def _on_scan_clicked(self, button):
        """Handle scan button click.
        
        Args:
            button: Button that was clicked
        """
        print(f"\n{'='*80}")
        print(f"[{self.get_category_name()}] _on_scan_clicked CALLED")
        print(f"{'='*80}")
        
        # Clear previous issues
        self.current_issues = []
        
        # Verify TreeView exists before scanning
        if not hasattr(self, 'issues_store') or self.issues_store is None:
            print(f"[{self.get_category_name()}] ❌ CRITICAL: TreeView not initialized!")
            print(f"[{self.get_category_name()}] _create_issues_treeview() was not called in _build_content()!")
            return
        
        print(f"[{self.get_category_name()}] ✓ TreeView verified (issues_store exists)")
        
        # Scan for new issues
        print(f"[{self.get_category_name()}] Calling _scan_issues()...")
        issues = self._scan_issues()
        print(f"[{self.get_category_name()}] _scan_issues() returned {len(issues)} issues")
        
        # Diagnostic output
        category_name = self.get_category_name()
        if issues:
            print(f"[{category_name}] ✓ Found {len(issues)} issues")
            self.current_issues = issues
            print(f"[{category_name}] Calling _display_issues({len(issues)})...")
            self._display_issues(issues)
            print(f"[{category_name}] ✓ _display_issues() completed")
        else:
            print(f"[{category_name}] No issues found")
            self._show_no_issues_message()
        
        print(f"[{category_name}] _on_scan_clicked COMPLETE")
        print(f"{'='*80}\n")
    
    def scan_with_locality(self, transition=None, locality=None, additional_ids=None):
        """Scan for issues scoped to a specific locality.
        
        This method is called by the diagnosis category when running
        a locality-scoped diagnosis (RUN SELECTED mode).
        
        Args:
            transition: Transition object for the locality
            locality: Locality object with input/output places
            additional_ids: Optional set of additional element IDs to include in scope (for multiple selection)
        """
        if not transition or not locality:
            print(f"[{self.get_category_name()}] ❌ No locality provided for scoped scan")
            return
        
        print(f"[{self.get_category_name()}] ========== SCAN WITH LOCALITY ==========")
        print(f"[{self.get_category_name()}] Transition: {transition.id}")
        print(f"[{self.get_category_name()}] Input places: {[p.id for p in locality.input_places] if hasattr(locality, 'input_places') else 'none'}")
        print(f"[{self.get_category_name()}] Output places: {[p.id for p in locality.output_places] if hasattr(locality, 'output_places') else 'none'}")
        if additional_ids:
            print(f"[{self.get_category_name()}] Additional IDs from multi-select: {len(additional_ids)} elements")
        
        # IMPORTANT: Clear existing display first
        print(f"[{self.get_category_name()}] → Clearing existing issues...")
        if hasattr(self, 'issues_store') and self.issues_store:
            self.issues_store.clear()
        
        # Store the locality scope (including additional IDs)
        self.selected_locality_id = transition.id
        self.scoped_transition = transition
        self.scoped_locality = locality
        self.additional_scope_ids = additional_ids  # Store for filtering
        
        # Run scan (subclass implementation will filter by locality)
        print(f"[{self.get_category_name()}] → Calling _scan_issues()...")
        issues = self._scan_issues()
        print(f"[{self.get_category_name()}] ← _scan_issues() returned {len(issues)} issues")
        
        # Filter issues to only those related to this locality
        print(f"[{self.get_category_name()}] → Filtering issues to locality...")
        filtered_issues = self._filter_issues_by_locality(issues, transition, locality)
        print(f"[{self.get_category_name()}] ← Filtered to {len(filtered_issues)} issues in locality")
        
        self.current_issues = filtered_issues
        print(f"[{self.get_category_name()}] → Calling _display_issues({len(filtered_issues)})...")
        self._display_issues(filtered_issues)
        print(f"[{self.get_category_name()}] ✓ Display complete")
    
    def _filter_issues_by_locality(self, issues, transition, locality):
        """Filter issues to only those related to the given locality.
        
        Args:
            issues: List of Issue objects
            transition: Transition object
            locality: Locality object with input/output places
            
        Returns:
            List[Issue]: Filtered issues
        """
        if not issues:
            print(f"[{self.get_category_name()}] No issues to filter")
            return []
        
        # Build set of relevant element IDs
        relevant_ids = {transition.id}
        if locality:
            if hasattr(locality, 'input_places'):
                input_ids = [p.id for p in locality.input_places if hasattr(p, 'id')]
                relevant_ids.update(input_ids)
                print(f"[{self.get_category_name()}] Relevant input places: {input_ids}")
            if hasattr(locality, 'output_places'):
                output_ids = [p.id for p in locality.output_places if hasattr(p, 'id')]
                relevant_ids.update(output_ids)
                print(f"[{self.get_category_name()}] Relevant output places: {output_ids}")
        
        # Add additional IDs if provided (from multiple selection)
        if hasattr(self, 'additional_scope_ids') and self.additional_scope_ids:
            relevant_ids.update(self.additional_scope_ids)
            print(f"[{self.get_category_name()}] Added {len(self.additional_scope_ids)} additional IDs from multi-select")
        
        print(f"[{self.get_category_name()}] All relevant IDs: {relevant_ids}")
        
        # Filter issues
        filtered = []
        for issue in issues:
            element_id = getattr(issue, 'element_id', None)
            if element_id:
                is_relevant = element_id in relevant_ids
                print(f"[{self.get_category_name()}] Issue '{getattr(issue, 'title', 'no title')}' element_id={element_id} relevant={is_relevant}")
                if is_relevant:
                    filtered.append(issue)
            else:
                print(f"[{self.get_category_name()}] Issue '{getattr(issue, 'title', 'no title')}' has no element_id")
        
        print(f"[{self.get_category_name()}] Filtered {len(issues)} → {len(filtered)} issues")
        return filtered
    
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
            
    
    def _on_clear_clicked(self, button):
        """Handle clear button click.
        
        Args:
            button: Button that was clicked
        """
        self.current_issues = []
        
        # Clear TreeView if using new format
        if hasattr(self, 'issues_store') and self.issues_store:
            self.issues_store.clear()
            if hasattr(self, 'select_column'):
                self.select_column.set_title("☐")
                self._all_selected = False
            if hasattr(self, 'repair_button'):
                self.repair_button.set_sensitive(False)
        
        # Clear ListBox if using old format
        if hasattr(self, 'issues_listbox') and self.issues_listbox:
            for child in self.issues_listbox.get_children():
                self.issues_listbox.remove(child)
    
    def _on_repair_clicked(self, button):
        """Handle repair button click - applies selected suggestions.
        
        Args:
            button: Button that was clicked
        """
        # Get selected issues from TreeView
        selected_issues = []
        if hasattr(self, 'issues_store') and self.issues_store:
            iter = self.issues_store.get_iter_first()
            while iter:
                selected = self.issues_store.get_value(iter, 0)
                if selected:
                    issue = self.issues_store.get_value(iter, 5)  # Get issue object
                    selected_issues.append(issue)
                iter = self.issues_store.iter_next(iter)
        else:
            # Fallback to all issues if using old ListBox
            selected_issues = self.current_issues
        
        if not selected_issues:
            print(f"[{self.get_category_name()}] No issues selected for repair")
            return
        
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Apply {len(selected_issues)} selected suggestion(s)?"
        )
        dialog.format_secondary_text(
            f"This will apply the selected suggestions to fix the model.\n"
            "This action can be undone."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Apply selected suggestions
            applied_count = 0
            for issue in selected_issues:
                if self._apply_suggestion(issue):
                    applied_count += 1
            
            print(f"[{self.get_category_name()}] Applied {applied_count}/{len(selected_issues)} suggestions")
            
            # Show result
            result_dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=f"Repair Complete"
            )
            result_dialog.format_secondary_text(
                f"Successfully applied {applied_count} suggestion(s)."
            )
            result_dialog.run()
            result_dialog.destroy()
            
            # Clear current issues after applying
            self._on_clear_clicked(None)
    
    def _apply_suggestion(self, issue):
        """Apply a suggestion from an issue.
        
        Subclasses should override this to implement specific repair logic.
        
        Args:
            issue: Issue dict or object containing the suggestion
            
        Returns:
            bool: True if successfully applied
        """
        print(f"[{self.get_category_name()}] _apply_suggestion not implemented")
        return False
    
    def _display_issues(self, issues: List[Issue]):
        """Display issues in the TreeView table.
        
        Args:
            issues: List of Issue dataclass instances
        """
        print(f"[{self.get_category_name()}] _display_issues called with {len(issues)} issues")
        print(f"[{self.get_category_name()}] has issues_store: {hasattr(self, 'issues_store')}")
        print(f"[{self.get_category_name()}] issues_store is not None: {hasattr(self, 'issues_store') and self.issues_store is not None}")
        
        if not hasattr(self, 'issues_store') or self.issues_store is None:
            # TreeView not initialized - this shouldn't happen if _build_content was called
            print(f"[{self.get_category_name()}] ❌ ERROR: issues_store not found, TreeView was not created!")
            print(f"[{self.get_category_name()}] This means _create_issues_treeview() was not called in _build_content()")
            print(f"[{self.get_category_name()}] Falling back to ListBox display (old format)")
            return self._display_issues_listbox(issues)
        
        # Clear existing rows
        print(f"[{self.get_category_name()}] Clearing issues_store...")
        self.issues_store.clear()
        
        if not issues:
            print(f"[{self.get_category_name()}] No issues to display")
            self._show_no_issues_message()
            # Disable repair button and reset header
            if hasattr(self, 'repair_button'):
                self.repair_button.set_sensitive(False)
            if hasattr(self, 'select_column'):
                self.select_column.set_title("☐")
                self._all_selected = False
            return
        
        print(f"[{self.get_category_name()}] Adding {len(issues)} rows to TreeView...")
        
        # Add issue rows to TreeView
        for issue in issues:
            # Determine icon based on severity or confidence
            if isinstance(issue, dict):
                print(f"[{self.get_category_name()}] Processing DICT issue: {list(issue.keys())}")
                # New suggestion dict format
                confidence = issue.get('confidence', 0.5)
                if confidence > 0.8:
                    icon = "💡"
                elif confidence > 0.5:
                    icon = "⚠️"
                else:
                    icon = "🔴"
                title = issue.get('title', 'No title')
                description = issue.get('description', '')
                reasoning = issue.get('reasoning', '')
                confidence_str = f"{confidence:.0%}"
                print(f"[{self.get_category_name()}]   Title: {title}")
                print(f"[{self.get_category_name()}]   Desc: {description}")
                print(f"[{self.get_category_name()}]   Reasoning: {reasoning}")
            else:
                print(f"[{self.get_category_name()}] Processing OBJECT issue: {type(issue)}")
                # Issue object format
                severity_icons = {
                    "critical": "🔴",
                    "warning": "⚠️",
                    "info": "💡"
                }
                icon = severity_icons.get(getattr(issue, 'severity', 'info'), "💡")
                title = getattr(issue, 'title', 'No title')
                description = getattr(issue, 'description', '')
                
                # Get confidence from first suggestion if available
                confidence_str = ""
                if hasattr(issue, 'suggestions') and issue.suggestions:
                    confidence = getattr(issue.suggestions[0], 'confidence', 0)
                    confidence_str = f"{confidence:.0%}"
            
            # Append row: Selected, Icon, Title, Description, Confidence, Issue
            self.issues_store.append([
                False,           # Not selected by default
                icon,
                title,
                description,
                confidence_str,
                issue            # Store issue object
            ])
        
        print(f"[{self.get_category_name()}] ✓ Added {len(issues)} rows to TreeView")
        
        # Reset header and button state
        self._all_selected = False
        if hasattr(self, 'select_column'):
            self.select_column.set_title("☐")
        if hasattr(self, 'repair_button'):
            self.repair_button.set_sensitive(False)  # No selection yet
        
        # Force UI update
        if hasattr(self, 'content_box'):
            self.content_box.show_all()
        
        print(f"[{self.get_category_name()}] ✓ _display_issues complete")
    
    def _display_issues_listbox(self, issues: List[Issue]):
        """Fallback method: Display issues in the old ListBox format.
        
        Args:
            issues: List of Issue dataclass instances
        """
        print(f"[{self.get_category_name()}] _display_issues_listbox called (FALLBACK)")
        print(f"[{self.get_category_name()}] has issues_listbox: {hasattr(self, 'issues_listbox')}")
        print(f"[{self.get_category_name()}] issues_listbox value: {getattr(self, 'issues_listbox', 'NOT_FOUND')}")
        
        if not hasattr(self, 'issues_listbox') or not self.issues_listbox:
            # ListBox also not available - print to console as last resort
            print(f"[{self.get_category_name()}] ❌ ERROR: Neither TreeView nor ListBox available!")
            print(f"[{self.get_category_name()}] Falling back to console output:")
            print(f"[{self.get_category_name()}] ========== {len(issues)} ISSUES DETECTED ==========")
            for i, issue in enumerate(issues, 1):
                if isinstance(issue, dict):
                    print(f"[{self.get_category_name()}] {i}. {issue.get('title', 'No title')}")
                    print(f"[{self.get_category_name()}]    {issue.get('description', 'No description')}")
                else:
                    print(f"[{self.get_category_name()}] {i}. {getattr(issue, 'title', 'No title')}")
                    print(f"[{self.get_category_name()}]    {getattr(issue, 'description', 'No description')}")
            return
        
        # Clear existing rows
        for child in self.issues_listbox.get_children():
            self.issues_listbox.remove(child)
        
        if not issues:
            self._show_no_issues_message()
            # Disable repair button
            if hasattr(self, 'repair_button'):
                self.repair_button.set_sensitive(False)
            return
        
        # Enable repair button if we have issues
        if hasattr(self, 'repair_button'):
            self.repair_button.set_sensitive(True)
        
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
        
        # Title with icon based on confidence (if dict) or severity (if Issue object)
        if isinstance(issue, dict):
            # New suggestion dict format
            confidence = issue.get('confidence', 0.5)
            if confidence > 0.8:
                icon = "💡"
            elif confidence > 0.5:
                icon = "⚠️"
            else:
                icon = "🔴"
            title = issue.get('title', 'No title')
            description = issue.get('description', '')
            suggestions = []  # Suggestions are now the issue itself
        else:
            # Old Issue object format (for backward compatibility)
            severity_icons = {
                "critical": "🔴",
                "warning": "⚠️",
                "info": "💡"
            }
            icon = severity_icons.get(issue.severity, "")
            title = issue.title
            description = issue.description
            suggestions = issue.suggestions if hasattr(issue, 'suggestions') else []
        
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{icon} {title}</b>")
        title_label.set_xalign(0)
        box.pack_start(title_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label(label=description)
        desc_label.set_line_wrap(True)
        desc_label.set_xalign(0)
        box.pack_start(desc_label, False, False, 0)
        
        # Suggestions (if any) - only for old Issue format
        if suggestions:
            for suggestion in suggestions:
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
            return
        
        
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
                return
            
            # Refresh display after successful application
            GLib.idle_add(self._refresh)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _on_preview_suggestion(self, button, suggestion: Suggestion):
        """Handle Preview button click for a suggestion.
        
        Temporarily highlights the elements affected by this suggestion on the canvas.
        
        Args:
            button: Button that was clicked
            suggestion: Suggestion to preview
        """
        
        # Get canvas manager for highlighting
        if not self.model_canvas:
            return
        
        drawing_area = self.model_canvas.get_current_document()
        if not drawing_area:
            return
        
        manager = self.model_canvas.get_canvas_manager(drawing_area)
        if not manager:
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
        
        
        # Get current marking for undo
        place = kb.places.get(place_id)
        if not place:
            return
        
        old_marking = place.current_marking
        
        # Update KB
        place.current_marking = tokens
        
        # Update model if manager is available
        if manager:
            for p in manager.places:
                if p.id == place_id:
                    p.tokens = tokens
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
        
        
        # For now, just suggest using initial marking instead
        # (Creating new elements requires more complex canvas integration)
    
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
        
        
        # Get current rate for undo
        transition = kb.transitions.get(transition_id)
        if not transition:
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
        
        
        # Get current weight for undo
        arc = kb.arcs.get(arc_id)
        if not arc:
            return
        
        old_weight = arc.weight
        
        # Update KB
        arc.weight = weight
        
        # Update model if manager is available
        if manager:
            for a in manager.arcs:
                if a.id == arc_id:
                    a.weight = weight
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
        print(f"[{self.get_category_name()}] _show_no_issues_message called")
        
        # Clear TreeView if it exists
        if hasattr(self, 'issues_store') and self.issues_store:
            print(f"[{self.get_category_name()}] Clearing TreeView (issues_store)")
            self.issues_store.clear()
            
            # Disable repair button
            if hasattr(self, 'repair_button'):
                self.repair_button.set_sensitive(False)
            
            # Reset header
            if hasattr(self, 'select_column'):
                self.select_column.set_title("☐")
                self._all_selected = False
            
            print(f"[{self.get_category_name()}] ✓ TreeView cleared, showing empty table")
            return
        
        # Fallback to ListBox if TreeView doesn't exist
        if hasattr(self, 'issues_listbox') and self.issues_listbox:
            print(f"[{self.get_category_name()}] Using ListBox (fallback)")
            # Clear existing content
            for child in self.issues_listbox.get_children():
                self.issues_listbox.remove(child)
            
            # Add "no issues" message
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="✓ NO ISSUES DETECTED")
            label.set_margin_start(12)
            label.set_margin_end(12)
            label.set_margin_top(12)
            label.set_margin_bottom(12)
            row.add(label)
            self.issues_listbox.add(row)
            self.issues_listbox.show_all()
            return
        
        # Neither TreeView nor ListBox available
        print(f"[{self.get_category_name()}] ✓ NO ISSUES DETECTED (console only)")
    
    def _apply_undo(self, change: Change):
        """Apply an undo operation.
        
        Reverts the change to its old value and updates both KB and model.
        
        Args:
            change: Change dataclass instance to undo
        """
        kb = self.get_knowledge_base()
        if not kb:
            return
        
        
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
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _record_change(self, change: Change):
        """Record a change to the undo history.
        
        Args:
            change: Change dataclass instance to record
        """
        self.change_history.append(change)
        self.undo_button.set_sensitive(True)
    
    def set_locality(self, locality_id):
        """Set the locality filter for this category.
        
        Args:
            locality_id: Locality ID, or None for full model
        """
        self.selected_locality_id = locality_id
        # Refresh if category is expanded
        if self.category_frame and self.category_frame.is_expanded():
            GLib.idle_add(self._refresh)
    
    def _on_observer_update(self, issues):
        """Callback for observer updates.
        
        This is called by the ViabilityObserver when new suggestions are
        available. The observer continuously monitors events and calls this
        method dynamically.
        
        Args:
            issues: List of Issue dataclasses from the observer
        """
        print(f"[VIABILITY_CATEGORY] ========== _on_observer_update() CALLED ==========")
        print(f"[VIABILITY_CATEGORY] Category: {self.__class__.__name__}")
        print(f"[VIABILITY_CATEGORY] Received {len(issues)} issues")
        print(f"[VIABILITY_CATEGORY] Expanded: {self.category_frame.expanded if self.category_frame else 'N/A'}")
        
        # Update the category with new issues
        self.current_issues = issues
        
        # Update UI if category is expanded
        if self.category_frame and self.category_frame.expanded:
            print(f"[VIABILITY_CATEGORY] Scheduling UI update via GLib.idle_add...")
            GLib.idle_add(self._display_issues, issues)
        else:
            print(f"[VIABILITY_CATEGORY] Not expanded - UI update skipped")
