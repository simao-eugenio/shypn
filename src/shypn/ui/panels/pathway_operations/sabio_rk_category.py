#!/usr/bin/env python3
"""SABIO-RK Category for Pathway Operations Panel.

Provides SABIO-RK enrichment category within Pathway Operations panel.
Handles:
- Querying SABIO-RK by EC number or reaction ID (no authentication needed)
- Displaying available kinetic parameters
- Manual selection of parameters to apply
- Safe enrichment (respects SBML curated data)

Follows CategoryFrame pattern - SABIO-RK is a free public database.
"""

import sys
import logging
import threading
from typing import Optional, Dict, List, Any

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f'ERROR: GTK3 not available in sabio_rk_category: {e}', file=sys.stderr)
    sys.exit(1)

from .base_pathway_category import BasePathwayCategory


class SabioRKCategory(BasePathwayCategory):
    """SABIO-RK enrichment category for Pathway Operations panel.
    
    Provides workflow:
    1. User queries by EC number, reaction ID, or all transitions
    2. User reviews available kinetic parameters
    3. User selects which parameters to apply (checkboxes)
    4. User explicitly applies to model
    
    Never auto-modifies curated models (SBML with locked=true).
    
    Attributes:
        sabio_controller: SabioRKEnrichmentController for business logic
        current_results: Current SABIO-RK query results
        selected_params: Dict of parameter checkboxes
    """
    
    def __init__(self, workspace_settings=None, parent_window=None):
        """Initialize SABIO-RK category.
        
        Args:
            workspace_settings: Optional WorkspaceSettings for storing prefs
            parent_window: Optional parent window for dialogs
        """
        # Set attributes BEFORE calling super().__init__()
        self.workspace_settings = workspace_settings
        self.parent_window = parent_window
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize backend
        try:
            from shypn.helpers.sabio_rk_enrichment_controller import SabioRKEnrichmentController
            self.sabio_controller = SabioRKEnrichmentController()
        except ImportError as e:
            self.logger.error(f"Cannot import SABIO-RK controller: {e}")
            self.sabio_controller = None
        
        # State
        self.current_results = []
        self.selected_params = {}  # transition_id -> checkbox widgets
        
        # Store transition ID from context menu (for result display)
        self._context_transition_id = None
        
        # Now call super().__init__() which will call _build_content()
        super().__init__(category_name="SABIO-RK")
    
    def _build_content(self) -> Gtk.Widget:
        """Build the SABIO-RK category content.
        
        Layout:
        1. Info section (no auth required!)
        2. Query section (manual OR batch all)
        3. Results section (table with checkboxes)
        4. Apply section (override options + Apply button)
        
        Returns:
            Gtk.Box containing all UI elements
        """
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        
        # 1. Info section (no authentication!)
        info_section = self._build_info_section()
        main_box.pack_start(info_section, False, False, 0)
        
        # 2. Query section
        query_section = self._build_query_section()
        main_box.pack_start(query_section, False, False, 0)
        
        # 3. Results section (scrollable table)
        results_section = self._build_results_section()
        main_box.pack_start(results_section, True, True, 0)
        
        # 4. Apply section
        apply_section = self._build_apply_section()
        main_box.pack_start(apply_section, False, False, 0)
        
        main_box.show_all()
        
        return main_box
    
    def _build_info_section(self) -> Gtk.Widget:
        """Build info section - no authentication required."""
        frame = Gtk.Frame()
        frame.set_label("SABIO-RK Database")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup(
            '<b>SABIO-RK</b> is a free public database with ~40,000 kinetic laws.\n'
            '<i>No authentication required!</i> '
            '<a href="https://sabiork.h-its.org/">Visit SABIO-RK</a>'
        )
        info_label.set_line_wrap(True)
        info_label.set_xalign(0.0)
        box.pack_start(info_label, False, False, 0)
        
        # API status
        self.api_status = Gtk.Label()
        self.api_status.set_markup("<span foreground='gray'>Testing API connection...</span>")
        self.api_status.set_xalign(0.0)
        box.pack_start(self.api_status, False, False, 0)
        
        # Test connection in background
        threading.Thread(target=self._test_connection, daemon=True).start()
        
        frame.add(box)
        return frame
    
    def _test_connection(self):
        """Test SABIO-RK API connection in background thread."""
        try:
            if self.sabio_controller and self.sabio_controller.sabio_client:
                is_online = self.sabio_controller.sabio_client.test_connection()
                
                def update_status():
                    if is_online:
                        self.api_status.set_markup("<span foreground='green'>✓ API connected</span>")
                    else:
                        self.api_status.set_markup("<span foreground='red'>✗ API offline</span>")
                
                GLib.idle_add(update_status)
        except Exception as e:
            self.logger.error(f"Error testing connection: {e}")
    
    def _build_query_section(self) -> Gtk.Widget:
        """Build query section with manual and batch options."""
        frame = Gtk.Frame()
        frame.set_label("Query SABIO-RK")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Batch query button
        batch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.query_all_button = Gtk.Button(label="🔬 Query All Transitions")
        self.query_all_button.set_tooltip_text("Query SABIO-RK for all transitions with EC numbers or reaction IDs")
        self.query_all_button.connect('clicked', self._on_query_all_clicked)
        batch_box.pack_start(self.query_all_button, True, True, 0)
        
        box.pack_start(batch_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(separator, False, False, 3)
        
        # Manual query section
        manual_label = Gtk.Label()
        manual_label.set_markup("<b>Manual Query</b>")
        manual_label.set_xalign(0.0)
        box.pack_start(manual_label, False, False, 0)
        
        # EC number entry
        ec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ec_label = Gtk.Label(label="EC Number:")
        ec_label.set_size_request(100, -1)
        ec_label.set_xalign(0.0)
        ec_box.pack_start(ec_label, False, False, 0)
        
        self.ec_entry = Gtk.Entry()
        self.ec_entry.set_placeholder_text("e.g., 2.7.1.1")
        self.ec_entry.set_hexpand(True)
        ec_box.pack_start(self.ec_entry, True, True, 0)
        
        box.pack_start(ec_box, False, False, 0)
        
        # Organism filter
        organism_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        organism_label = Gtk.Label(label="Organism:")
        organism_label.set_size_request(100, -1)
        organism_label.set_xalign(0.0)
        organism_box.pack_start(organism_label, False, False, 0)
        
        self.organism_combo = Gtk.ComboBoxText()
        self.organism_combo.append_text("All organisms")
        self.organism_combo.append_text("Homo sapiens")
        self.organism_combo.append_text("Mus musculus")
        self.organism_combo.append_text("Saccharomyces cerevisiae")
        self.organism_combo.append_text("Escherichia coli")
        self.organism_combo.set_active(1)  # Default to Homo sapiens to avoid timeouts
        organism_box.pack_start(self.organism_combo, True, True, 0)
        
        box.pack_start(organism_box, False, False, 0)
        
        # Search button
        self.search_button = Gtk.Button(label="Search")
        self.search_button.connect('clicked', self._on_search_clicked)
        box.pack_start(self.search_button, False, False, 0)
        
        frame.add(box)
        return frame
    
    def _build_results_section(self) -> Gtk.Widget:
        """Build scrollable results table."""
        frame = Gtk.Frame()
        frame.set_label("Results")
        
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        container.set_margin_start(10)
        container.set_margin_end(10)
        container.set_margin_top(10)
        container.set_margin_bottom(10)
        
        # Header with results counter
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.results_count_label = Gtk.Label()
        self.results_count_label.set_markup("<i>0 results</i>")
        self.results_count_label.set_xalign(0.0)
        header_box.pack_start(self.results_count_label, True, True, 0)
        
        container.pack_start(header_box, False, False, 0)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        # Create tree view with parameters as columns
        self.results_store = Gtk.ListStore(
            bool,    # 0: Select checkbox (radio button style - only 1 per transition)
            str,     # 1: Transition ID (internal model ID)
            str,     # 2: Organism
            str,     # 3: Substrate
            str,     # 4: Temperature
            str,     # 5: pH
            str,     # 6: Km
            str,     # 7: Vmax
            str,     # 8: Kcat
            str,     # 9: Ki
            str,     # 10: Score
            object   # 11: Parameter set data (hidden)
        )
        
        self.results_tree = Gtk.TreeView(model=self.results_store)
        self.results_tree.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        
        # Connect row-activated for double-click behavior
        self.results_tree.connect('row-activated', self._on_row_activated)
        
        # Checkbox column with clickable header for Select All/Deselect All
        checkbox_renderer = Gtk.CellRendererToggle()
        checkbox_renderer.connect('toggled', self._on_result_toggled)
        checkbox_col = Gtk.TreeViewColumn("☐", checkbox_renderer, active=0)
        checkbox_col.set_fixed_width(40)
        checkbox_col.set_clickable(True)
        checkbox_col.connect('clicked', self._on_select_all_header_clicked)
        self.results_tree.append_column(checkbox_col)
        self.select_column = checkbox_col
        self._all_selected = False
        
        # Parameter columns with better sizing
        columns = [
            ("ID", 1, 80),           # Transition internal ID
            ("Organism", 2, 140),    # Organism name
            ("Substrate", 3, 100),   # Substrate name
            ("Temp", 4, 60),         # Temperature
            ("pH", 5, 50),           # pH value
            ("Km", 6, 100),          # Km value + units
            ("Vmax", 7, 100),        # Vmax value + units
            ("Kcat", 8, 100),        # Kcat value + units
            ("Ki", 9, 100),          # Ki value + units
            ("Score", 10, 60)        # Completeness score
        ]
        
        for title, col_id, width in columns:
            renderer = Gtk.CellRendererText()
            renderer.set_property('ellipsize', 3)  # ELLIPSIZE_END
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_resizable(True)
            column.set_fixed_width(width)
            self.results_tree.append_column(column)
        
        scrolled.add(self.results_tree)
        container.pack_start(scrolled, True, True, 0)
        
        frame.add(container)
        return frame
    
    def _build_apply_section(self) -> Gtk.Widget:
        """Build apply section with status and controls."""
        frame = Gtk.Frame()
        frame.set_label("Apply Parameters")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>No results to display</i>")
        self.status_label.set_xalign(0.0)
        box.pack_start(self.status_label, False, False, 0)
        
        # Override options
        self.override_kegg_check = Gtk.CheckButton(label="Override KEGG heuristics (always recommended)")
        self.override_kegg_check.set_active(True)
        box.pack_start(self.override_kegg_check, False, False, 0)
        
        self.override_sbml_check = Gtk.CheckButton(label="Override SBML curated data (use with caution)")
        self.override_sbml_check.set_active(False)
        box.pack_start(self.override_sbml_check, False, False, 0)
        
        # Apply button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.END)
        
        self.apply_button = Gtk.Button(label="Apply Selected")
        self.apply_button.set_sensitive(False)
        self.apply_button.connect('clicked', self._on_apply_clicked)
        self.apply_button.get_style_context().add_class('suggested-action')
        button_box.pack_end(self.apply_button, False, False, 0)
        
        box.pack_start(button_box, False, False, 0)
        
        frame.add(box)
        return frame
    
    def _on_query_all_clicked(self, button):
        """Handle Query All button click."""
        if not self.sabio_controller:
            self._show_error("SABIO-RK controller not available")
            return
        
        # Get current model
        document_model = self._get_current_model()
        if not document_model:
            self._show_error("No model loaded")
            return
        
        # Count enrichable transitions first
        enrichable = self.sabio_controller.scan_transitions(document_model)
        total_count = len(enrichable)
        
        if total_count == 0:
            self._show_error("No enrichable transitions found (need EC numbers or reaction IDs)")
            return
        
        if total_count > 30:
            # Warn user about large batches
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text=f"Query {total_count} transitions?"
            )
            dialog.format_secondary_text(
                f"This will query SABIO-RK {total_count} times.\n"
                f"Processing in batches of 10 with 2-second pauses.\n"
                f"This may take several minutes. Continue?"
            )
            response = dialog.run()
            dialog.destroy()
            
            if response != Gtk.ResponseType.OK:
                return
        
        # Disable button during query
        button.set_sensitive(False)
        self.status_label.set_markup(f"<i>Querying SABIO-RK: 0/{total_count} transitions...</i>")
        
        # Run query in background thread
        def query_thread():
            try:
                # Get organism filter
                organism = None
                organism_text = self.organism_combo.get_active_text()
                if organism_text != "All organisms":
                    organism = organism_text
                
                # Query all transitions (with progress updates)
                # We'll need to modify the controller to support progress callbacks
                results = self.sabio_controller.query_all_transitions(
                    document_model, 
                    organism,
                    batch_size=10  # Process 10 at a time
                )
                
                # Update UI in main thread
                GLib.idle_add(self._populate_results, results, button)
                
            except Exception as e:
                self.logger.error(f"Error querying SABIO-RK: {e}")
                import traceback
                traceback.print_exc()
                GLib.idle_add(self._show_error, f"Query failed: {e}")
                GLib.idle_add(button.set_sensitive, True)
        
        threading.Thread(target=query_thread, daemon=True).start()
    
    def _on_search_clicked(self, button):
        """Handle manual Search button click."""
        ec_number = self.ec_entry.get_text().strip()
        
        if not ec_number:
            self._show_error("Please enter an EC number")
            return
        
        if not self.sabio_controller:
            self._show_error("SABIO-RK controller not available")
            return
        
        # Disable button during query
        button.set_sensitive(False)
        self.status_label.set_markup(f"<i>Querying EC {ec_number}...</i>")
        
        # Run query in background
        def query_thread():
            try:
                organism = None
                organism_text = self.organism_combo.get_active_text()
                if organism_text != "All organisms":
                    organism = organism_text
                
                # Query by EC number
                result = self.sabio_controller.sabio_client.query_by_ec_number(ec_number, organism)
                
                if result:
                    # Create pseudo transition info for display
                    # Use stored transition ID from context menu if available
                    transition_id = self._context_transition_id or f'EC_{ec_number}'
                    transition_obj = self._context_transition  # Get stored transition object
                    
                    self.logger.info(f"[SABIO-RK] Creating result with transition_obj: {transition_obj}")
                    if transition_obj:
                        self.logger.info(f"[SABIO-RK] Transition ID: {transition_obj.id if hasattr(transition_obj, 'id') else 'NO ID'}")
                    
                    # Get current params if we have the transition object
                    current_params = {}
                    if transition_obj and hasattr(self.sabio_controller, '_get_current_params'):
                        current_params = self.sabio_controller._get_current_params(transition_obj)
                    
                    results = [{
                        'transition_id': transition_id,
                        'transition_name': f'EC {ec_number}',
                        'identifiers': {'ec_number': ec_number},
                        'sabio_data': result,
                        'transition': transition_obj,  # Use stored transition from context menu
                        'current_params': current_params
                    }]
                    GLib.idle_add(self._populate_results, results, button)
                    
                    # DON'T clear context transition yet - we need it for Apply Selected
                    # It will be cleared in _on_apply_clicked after parameters are applied
                else:
                    # Show more specific error message
                    if organism:
                        msg = f"<span foreground='red'>No data found for EC {ec_number} in {organism}. "\
                              f"Query may have too many results (&gt;200) or no data available.</span>"
                    else:
                        msg = f"<span foreground='red'>No data found for EC {ec_number}. "\
                              f"Try selecting a specific organism to reduce results.</span>"
                    GLib.idle_add(self.status_label.set_markup, msg)
                    GLib.idle_add(button.set_sensitive, True)
                
            except Exception as e:
                self.logger.error(f"Error searching: {e}")
                GLib.idle_add(self._show_error, f"Search failed: {e}")
                GLib.idle_add(button.set_sensitive, True)
        
        threading.Thread(target=query_thread, daemon=True).start()
    
    def _on_result_toggled(self, renderer, path):
        """Handle checkbox toggle in results table."""
        self.results_store[path][0] = not self.results_store[path][0]
        self._update_apply_button()
    
    def _on_select_all_header_clicked(self, column):
        """Handle click on checkbox column header to select/deselect all.
        
        Toggles between selecting all rows and deselecting all rows.
        Updates header icon to show current state (☐ = none selected, ☑ = all selected).
        """
        # Toggle state
        self._all_selected = not self._all_selected
        
        # Update all rows
        iter = self.results_store.get_iter_first()
        while iter:
            self.results_store.set_value(iter, 0, self._all_selected)
            iter = self.results_store.iter_next(iter)
        
        # Update header icon
        if self._all_selected:
            column.set_title("☑")
        else:
            column.set_title("☐")
        
        # Update apply button state
        self._update_apply_button()
    
    def _on_row_activated(self, tree_view, path, column):
        """Handle double-click on a result row to apply parameters immediately.
        
        This matches BRENDA behavior: double-clicking a row toggles its selection.
        """
        try:
            # Toggle selection on double-click
            self.results_store[path][0] = not self.results_store[path][0]
            self._update_apply_button()
        except Exception as e:
            self.logger.error(f"Error handling row activation: {e}")
    

    
    def _on_apply_clicked(self, button):
        """Handle Apply Selected button click."""
        # Get selected parameter options
        selected = []
        iter = self.results_store.get_iter_first()
        while iter:
            if self.results_store.get_value(iter, 0):  # Checkbox selected
                transition_id = self.results_store.get_value(iter, 1)
                param_set = self.results_store.get_value(iter, 11)  # Column 11 has parameter set
                selected.append({
                    'transition_id': transition_id,
                    'param_set': param_set
                })
            iter = self.results_store.iter_next(iter)
        
        if not selected:
            self._show_error("No parameter options selected")
            return
        
        # Get override settings
        override_kegg = self.override_kegg_check.get_active()
        override_sbml = self.override_sbml_check.get_active()
        
        # Apply each selected parameter set
        success_count = 0
        failed_count = 0
        
        for item in selected:
            transition_id = item['transition_id']
            param_set = item['param_set']
            
            # Find transition_info from current_results
            transition_info = None
            for result in self.current_results:
                if result['transition_id'] == transition_id:
                    transition_info = result
                    break
            
            if not transition_info:
                self.logger.error(f"[SABIO-RK UI] No transition_info found for {transition_id}")
                failed_count += 1
                continue
            
            # Apply selected parameter set
            try:
                success = self.sabio_controller.apply_selected_parameter_set(
                    transition_info,
                    param_set,
                    override_kegg,
                    override_sbml
                )
                
                if success:
                    success_count += 1
                    self.logger.info(f"[SABIO-RK UI] Applied parameters to {transition_id}")
                else:
                    failed_count += 1
                    self.logger.warning(f"[SABIO-RK UI] Failed to apply parameters to {transition_id}")
            except Exception as e:
                failed_count += 1
                self.logger.error(f"[SABIO-RK UI] Error applying parameters to {transition_id}: {e}")
        
        # Build summary
        summary = {
            'success': success_count,
            'failed': failed_count,
            'skipped': 0,
            'total': len(selected)
        }
        
        # Clear context transition after apply
        self._context_transition_id = None
        self._context_transition = None
        
        # CRITICAL: Reset simulation state after applying parameters
        # This clears cached behaviors that might have old parameter values
        # See: CANVAS_STATE_ISSUES_COMPARISON.md for historical context
        if success_count > 0:
            self._reset_simulation_after_parameter_changes()
        
        # Show summary dialog
        self._show_apply_summary(summary)
        
        # Refresh Report panel if available
        self._trigger_report_refresh()
    
    def _populate_results(self, results: List[Dict[str, Any]], button=None):
        """Populate results table with parameter options (up to 15 per transition).
        
        Args:
            results: List of enrichment results from query_all_transitions
            button: Optional button to re-enable
        """
        # Clear existing results
        self.results_store.clear()
        self.current_results = results
        
        self.logger.info(f"[SABIO-RK UI] Populating results table with {len(results)} results")
        
        if not results:
            self.status_label.set_markup("<i>No results found</i>")
            if button:
                button.set_sensitive(True)
            return
        
        # Get all transition IDs from results
        all_transition_ids = [r['transition_id'] for r in results]
        
        # Get override settings (use current UI state)
        override_kegg = self.override_kegg_check.get_active()
        override_sbml = self.override_sbml_check.get_active()
        
        # Call apply_batch to get parameter options (up to 15 per transition)
        self.logger.info(f"[SABIO-RK UI] Getting parameter options for {len(all_transition_ids)} transitions")
        parameter_options_result = self.sabio_controller.apply_batch(
            results,
            all_transition_ids,
            override_kegg,
            override_sbml
        )
        
        parameter_options = parameter_options_result.get('parameter_options', [])
        
        if not parameter_options:
            self.status_label.set_markup("<i>No parameter options available</i>")
            if button:
                button.set_sensitive(True)
            return
        
        # Flatten parameter options into table rows
        total_rows = 0
        for option in parameter_options:
            transition_id = option['transition_id']
            parameter_sets = option['parameter_sets']
            
            self.logger.info(f"[SABIO-RK UI] {transition_id}: Adding {len(parameter_sets)} parameter options")
            
            for param_set in parameter_sets:
                # Extract display values
                organism = param_set.get('organism', 'Unknown')[:30]
                substrate = param_set.get('substrate', 'Unknown')[:25]
                temperature = param_set.get('temperature', 'N/A')
                ph = param_set.get('pH', 'N/A')
                score = param_set.get('completeness_score', 0)
                
                # Format temperature (only if numeric)
                if temperature != 'N/A' and isinstance(temperature, (int, float)):
                    temperature = f"{temperature}\u00b0C"
                else:
                    temperature = str(temperature)
                
                # Extract parameters
                params = param_set.get('parameters', {})
                
                def format_param(param_dict):
                    if not param_dict:
                        return '-'
                    value = param_dict.get('value')
                    units = param_dict.get('units', '')
                    if value is None:
                        return '-'
                    return f"{value:.3g} {units}".strip()
                
                km_str = format_param(params.get('Km'))
                vmax_str = format_param(params.get('Vmax'))
                kcat_str = format_param(params.get('Kcat'))
                ki_str = format_param(params.get('Ki'))
                score_str = str(score)
                
                # Add row to table
                self.results_store.append([
                    False,  # Checkbox (user selects which to apply)
                    transition_id,
                    organism,
                    substrate,
                    temperature,
                    str(ph),
                    km_str,
                    vmax_str,
                    kcat_str,
                    ki_str,
                    score_str,
                    param_set  # Store full parameter set for apply
                ])
                total_rows += 1
        
        self.logger.info(f"[SABIO-RK UI] Added {total_rows} parameter option rows")
        
        # Update status
        self.status_label.set_markup(
            f"<b>Found {len(parameter_options)} transitions with {total_rows} parameter options</b>"
        )
        
        # Update results counter
        self.results_count_label.set_markup(f"<i>{total_rows} parameter options</i>")
        
        # Enable apply button
        self._update_apply_button()
        
        # Re-enable query button
        if button:
            button.set_sensitive(True)
    
    def _update_apply_button(self):
        """Update Apply button sensitivity based on selection."""
        has_selection = False
        iter = self.results_store.get_iter_first()
        while iter:
            if self.results_store.get_value(iter, 0):
                has_selection = True
                break
            iter = self.results_store.iter_next(iter)
        
        self.apply_button.set_sensitive(has_selection)
    
    def _show_error(self, message: str):
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            parent=self.parent_window,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="SABIO-RK Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _show_apply_summary(self, summary: Dict[str, Any]):
        """Show summary dialog after applying parameters."""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="SABIO-RK Enrichment Complete"
        )
        
        message = (
            f"Successfully applied: {summary['success']}\n"
            f"Failed: {summary['failed']}\n"
            f"Skipped: {summary['skipped']}\n"
            f"Total selected: {summary['total']}"
        )
        
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _get_current_model(self):
        """Get current document model from canvas."""
        if not hasattr(self, 'model_canvas') or not self.model_canvas:
            return None
        
        try:
            drawing_area = self.model_canvas.get_current_document()
            if not drawing_area:
                return None
            
            if hasattr(drawing_area, 'document_model'):
                return drawing_area.document_model
            
            # Try to get from canvas manager
            if hasattr(self.model_canvas, 'canvas_managers'):
                manager = self.model_canvas.canvas_managers.get(drawing_area)
                if manager and hasattr(manager, 'to_document_model'):
                    return manager.to_document_model()
        except Exception as e:
            self.logger.error(f"Error getting current model: {e}")
        
        return None
    
    def _trigger_report_refresh(self):
        """Trigger Report panel refresh if callback is set."""
        # This will be called by parent PathwayOperationsPanel
        pass
    
    def set_query_from_transition(self, ec_number: str = "", reaction_id: str = "", 
                                   organism: str = "", transition_id: str = "", transition=None):
        """Pre-fill query fields from transition metadata (context menu).
        
        This method is called from the context menu handler when user
        right-clicks a transition and selects "Enrich with SABIO-RK".
        
        Args:
            ec_number: EC number to query
            reaction_id: KEGG reaction ID or other identifier
            organism: Organism name (e.g., "Homo sapiens")
            transition_id: Transition ID for reference
            transition: Actual transition object (needed for Apply)
        """
        self.logger.info(f"[SABIO-RK] Pre-filling query from transition {transition_id}")
        
        # Clear previous results table
        self.results_store.clear()
        self.current_results = []
        self.status_label.set_markup("<i>Ready to query</i>")
        
        # Store transition ID and object for use in search results
    
    def on_tab_switched(self):
        """Called when the user switches to a different model tab.
        
        Updates the SABIO-RK panel to reflect the currently active model:
        - Refreshes button states
        - Updates status labels
        - Ensures correct model is targeted for queries
        """
        self.logger.debug("Tab switched, updating SABIO-RK panel state")
        
        # Get current model/document
        canvas_manager = self._get_current_model()
        document = None
        if canvas_manager and hasattr(canvas_manager, 'document'):
            document = canvas_manager.document
        
        # Update buttons based on new active model
        if document:
            # Enable buttons if model is loaded
            self.search_button.set_sensitive(True)
            self.query_all_button.set_sensitive(True)
            
            # Count transitions in new model
            transition_count = 0
            if canvas_manager and hasattr(canvas_manager, 'transitions'):
                transition_count = len(canvas_manager.transitions)
            
            self.status_label.set_markup(
                f'<span size="small">Model loaded - {transition_count} transitions</span>'
            )
        else:
            # No document - disable buttons
            self.search_button.set_sensitive(False)
            self.query_all_button.set_sensitive(False)
            self.status_label.set_markup(
                '<span size="small">No model loaded</span>'
            )

    def _reset_simulation_after_parameter_changes(self):
        """Reset simulation to initial state after applying parameter changes.
        
        CRITICAL for correct simulation behavior:
        When parameters are applied to transitions via SABIO-RK enrichment,
        the simulation controller's behavior cache contains old TransitionBehavior 
        instances with old parameter values. If we don't reset the simulation, 
        these cached behaviors continue to be used, causing transitions to fire 
        incorrectly or not at all.
        
        This is the same root cause as:
        - Behavior Cache Bug (commit 864ae92) - transitions not firing after reload
        - Canvas Freeze Bug (commit df037a6) - canvas frozen after save/reload
        - Comprehensive Reset (commit be02ff5) - stale state across model loads
        
        See: CANVAS_STATE_ISSUES_COMPARISON.md for detailed analysis.
        
        The fix: Call controller.reset() which clears behavior cache AND resets
        place tokens to initial marking, ensuring a clean slate for testing the
        new parameter values.
        """
        try:
            # Get current document and canvas manager
            if not hasattr(self, 'model_canvas') or not self.model_canvas:
                self.logger.warning("No model canvas available for simulation reset")
                return
            
            drawing_area = self.model_canvas.get_current_document()
            if not drawing_area:
                self.logger.warning("No active document for simulation reset")
                return
            
            # Find simulation controller for this drawing area
            if hasattr(self.model_canvas, 'simulation_controllers'):
                if drawing_area in self.model_canvas.simulation_controllers:
                    controller = self.model_canvas.simulation_controllers[drawing_area]
                    
                    # Get the canvas manager
                    canvas_manager = self.model_canvas.canvas_managers.get(drawing_area)
                    
                    if canvas_manager:
                        # CRITICAL: Use reset_for_new_model() instead of reset()
                        # This recreates the model adapter and clears ALL caches
                        # After applying parameters, the transition objects have changed
                        # and we need to rebuild the entire simulation state
                        controller.reset_for_new_model(canvas_manager)
                        
                        self.logger.info("Simulation fully reset after SABIO-RK parameter changes (model adapter recreated)")
                    else:
                        # Fallback to basic reset if we can't get canvas_manager
                        controller.reset()
                        self.logger.info("Simulation reset to initial state after SABIO-RK parameter changes")
                    
                    # Refresh canvas to show reset token values
                    if drawing_area:
                        drawing_area.queue_draw()
                else:
                    self.logger.debug("No simulation controller for current document")
            else:
                self.logger.warning("Canvas loader has no simulation_controllers attribute")
                
        except Exception as e:
            self.logger.error(f"Error resetting simulation after parameter changes: {e}", exc_info=True)


def create_sabio_rk_category(workspace_settings=None, parent_window=None) -> SabioRKCategory:
    """Create SABIO-RK category instance.
    
    Args:
        workspace_settings: Optional WorkspaceSettings
        parent_window: Optional parent window
    
    Returns:
        SabioRKCategory instance
    """
    return SabioRKCategory(workspace_settings, parent_window)
