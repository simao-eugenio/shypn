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
        self.organism_combo.set_active(0)
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
        
        # Header with results counter and Select All/Deselect All buttons
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.results_count_label = Gtk.Label()
        self.results_count_label.set_markup("<i>0 results</i>")
        self.results_count_label.set_xalign(0.0)
        header_box.pack_start(self.results_count_label, True, True, 0)
        
        self.select_all_button = Gtk.Button(label="Select All")
        self.select_all_button.set_sensitive(False)
        self.select_all_button.set_tooltip_text("Select all results")
        self.select_all_button.connect('clicked', self._on_select_all_clicked)
        header_box.pack_end(self.select_all_button, False, False, 0)
        
        self.deselect_all_button = Gtk.Button(label="Deselect All")
        self.deselect_all_button.set_sensitive(False)
        self.deselect_all_button.set_tooltip_text("Deselect all results")
        self.deselect_all_button.connect('clicked', self._on_deselect_all_clicked)
        header_box.pack_end(self.deselect_all_button, False, False, 0)
        
        container.pack_start(header_box, False, False, 0)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        # Create tree view with parameters as columns
        self.results_store = Gtk.ListStore(
            bool,    # 0: Select checkbox
            str,     # 1: Transition ID (internal model ID)
            str,     # 2: Reaction ID (KEGG R-ID)
            str,     # 3: EC Number
            str,     # 4: Vmax
            str,     # 5: Km
            str,     # 6: Kcat
            str,     # 7: Ki
            str,     # 8: Organism
            object   # 9: Result data (hidden)
        )
        
        self.results_tree = Gtk.TreeView(model=self.results_store)
        self.results_tree.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        
        # Checkbox column
        checkbox_renderer = Gtk.CellRendererToggle()
        checkbox_renderer.connect('toggled', self._on_result_toggled)
        checkbox_col = Gtk.TreeViewColumn("☑", checkbox_renderer, active=0)
        checkbox_col.set_fixed_width(40)
        self.results_tree.append_column(checkbox_col)
        
        # Parameter columns with better sizing
        columns = [
            ("ID", 1, 80),           # Transition internal ID
            ("Reaction", 2, 100),    # KEGG R-ID
            ("EC", 3, 90),           # EC number
            ("Vmax", 4, 120),        # Vmax value + units
            ("Km", 5, 120),          # Km value + units
            ("Kcat", 6, 120),        # Kcat value + units
            ("Ki", 7, 120),          # Ki value + units
            ("Organism", 8, 150)     # Organism name
        ]
        
        for title, col_id, width in columns:
            renderer = Gtk.CellRendererText()
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
                    
                    results = [{
                        'transition_id': transition_id,
                        'transition_name': f'EC {ec_number}',
                        'identifiers': {'ec_number': ec_number},
                        'sabio_data': result,
                        'transition': None  # Manual query, no transition
                    }]
                    GLib.idle_add(self._populate_results, results, button)
                    
                    # Clear stored transition ID after use
                    self._context_transition_id = None
                else:
                    # Show more specific error message
                    if organism:
                        msg = f"<span foreground='red'>No data found for EC {ec_number} in {organism}. "\
                              f"Query may have too many results (&gt;150) or no data available.</span>"
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
    
    def _on_select_all_clicked(self, button):
        """Select all results."""
        iter = self.results_store.get_iter_first()
        while iter:
            self.results_store.set_value(iter, 0, True)
            iter = self.results_store.iter_next(iter)
        self._update_apply_button()
    
    def _on_deselect_all_clicked(self, button):
        """Deselect all results."""
        iter = self.results_store.get_iter_first()
        while iter:
            self.results_store.set_value(iter, 0, False)
            iter = self.results_store.iter_next(iter)
        self._update_apply_button()
    
    def _on_apply_clicked(self, button):
        """Handle Apply Selected button click."""
        # Get selected results
        selected = []
        iter = self.results_store.get_iter_first()
        while iter:
            if self.results_store.get_value(iter, 0):  # Checkbox selected
                result_data = self.results_store.get_value(iter, 6)
                selected.append(result_data)
            iter = self.results_store.iter_next(iter)
        
        if not selected:
            self._show_error("No results selected")
            return
        
        # Get override settings
        override_kegg = self.override_kegg_check.get_active()
        override_sbml = self.override_sbml_check.get_active()
        
        # Get selected transition IDs
        selected_ids = [r['transition_id'] for r in selected]
        
        # Apply parameters
        summary = self.sabio_controller.apply_batch(
            selected,
            selected_ids,
            override_kegg,
            override_sbml
        )
        
        # CRITICAL: Reset simulation state after applying parameters
        # This clears cached behaviors that might have old parameter values
        # See: CANVAS_STATE_ISSUES_COMPARISON.md for historical context
        if summary.get('success', 0) > 0:
            self._reset_simulation_after_parameter_changes()
        
        # Show summary dialog
        self._show_apply_summary(summary)
        
        # Refresh Report panel if available
        self._trigger_report_refresh()
    
    def _populate_results(self, results: List[Dict[str, Any]], button=None):
        """Populate results table with SABIO-RK data.
        
        Args:
            results: List of enrichment results
            button: Optional button to re-enable
        """
        # Clear existing results
        self.results_store.clear()
        self.current_results = results
        
        if not results:
            self.status_label.set_markup("<i>No results found</i>")
            if button:
                button.set_sensitive(True)
            return
        
        # Populate table - DEDUPLICATE by (EC number, Organism) to reduce confusion
        # Group ALL parameters by unique (EC, Organism) combination
        from collections import defaultdict
        
        # Key: (ec_number, organism), Value: aggregated data
        unique_entries = defaultdict(lambda: {
            'transition_id': None,
            'kegg_reaction_ids': set(),  # Collect all KEGG R-IDs
            'ec_number': None,
            'organism': None,
            'Vmax': [],
            'Km': [],
            'Kcat': [],
            'Ki': [],
            'raw_parameters': []  # Store ALL numeric parameters for Apply Selected
        })
        
        for result in results:
            sabio_data = result.get('sabio_data', {})
            parameters = sabio_data.get('parameters', [])
            query_organism = sabio_data.get('query_organism')  # Organism from query filter
            ec_number = result.get('identifiers', {}).get('ec_number', 'N/A')
            transition_id = result.get('transition_id', 'N/A')
            
            if not parameters:
                continue
            
            for param in parameters:
                param_type = param.get('parameter_type', 'other')
                param_organism = param.get('organism')
                organism = param_organism or query_organism or 'Unknown'
                
                # Create unique key: (EC, Organism)
                key = (ec_number, organism)
                
                # Store metadata (first occurrence)
                if not unique_entries[key]['transition_id']:
                    unique_entries[key]['transition_id'] = transition_id
                    unique_entries[key]['ec_number'] = ec_number
                    unique_entries[key]['organism'] = organism
                
                # Collect KEGG reaction IDs
                kegg_id = param.get('kegg_reaction_id')
                if kegg_id:
                    unique_entries[key]['kegg_reaction_ids'].add(kegg_id)
                
                # Collect parameter values by type (with units)
                value = param.get('value')
                units = param.get('units', '')
                if value is not None:
                    # Store formatted value for display
                    if param_type in unique_entries[key]:
                        unique_entries[key][param_type].append(f"{value:.3g} {units}".strip())
                    
                    # Store raw numeric parameter for Apply Selected
                    unique_entries[key]['raw_parameters'].append(param)
        
        # Add one row per unique (EC, Organism) combination
        for (ec_number, organism), entry_data in unique_entries.items():
            # Skip entries with no parameters
            if not any([entry_data['Vmax'], entry_data['Km'], 
                       entry_data['Kcat'], entry_data['Ki']]):
                continue
            
            # Format KEGG reaction IDs (show up to 3)
            kegg_ids = sorted(entry_data['kegg_reaction_ids'])
            kegg_display = ', '.join(kegg_ids[:3])
            if len(kegg_ids) > 3:
                kegg_display += f' (+{len(kegg_ids)-3} more)'
            kegg_display = kegg_display or 'N/A'
            
            # Format parameter columns (show first 2 values if multiple)
            vmax = ', '.join(entry_data['Vmax'][:2]) if entry_data['Vmax'] else '-'
            km = ', '.join(entry_data['Km'][:2]) if entry_data['Km'] else '-'
            kcat = ', '.join(entry_data['Kcat'][:2]) if entry_data['Kcat'] else '-'
            ki = ', '.join(entry_data['Ki'][:2]) if entry_data['Ki'] else '-'
            
            # Add count if more parameters available
            if len(entry_data['Vmax']) > 2:
                vmax += f' (+{len(entry_data["Vmax"])-2})'
            if len(entry_data['Km']) > 2:
                km += f' (+{len(entry_data["Km"])-2})'
            if len(entry_data['Kcat']) > 2:
                kcat += f' (+{len(entry_data["Kcat"])-2})'
            if len(entry_data['Ki']) > 2:
                ki += f' (+{len(entry_data["Ki"])-2})'
            
            # Truncate long values
            vmax = vmax[:35] + '...' if len(vmax) > 35 else vmax
            km = km[:35] + '...' if len(km) > 35 else km
            kcat = kcat[:35] + '...' if len(kcat) > 35 else kcat
            ki = ki[:35] + '...' if len(ki) > 35 else ki
            
            self.results_store.append([
                True,  # Selected by default
                entry_data['transition_id'],  # Internal model transition ID (T32, etc.)
                kegg_display,  # KEGG R-IDs (may be multiple)
                ec_number,  # EC number
                vmax,
                    km,
                    kcat,
                    ki,
                    organism[:30],  # Organism (truncated)
                    result  # Store full result data
                ])
        
        # Update status
        self.status_label.set_markup(f"<b>Found {len(results)} transitions with SABIO-RK data</b>")
        
        # Update results counter
        self.results_count_label.set_markup(f"<i>{len(results)} results</i>")
        
        # Enable Select All/Deselect All buttons
        has_results = len(results) > 0
        self.select_all_button.set_sensitive(has_results)
        self.deselect_all_button.set_sensitive(has_results)
        
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
            parent=self.parent_window,
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
                                   organism: str = "", transition_id: str = ""):
        """Pre-fill query fields from transition metadata (context menu).
        
        This method is called from the context menu handler when user
        right-clicks a transition and selects "Enrich with SABIO-RK".
        
        Args:
            ec_number: EC number to query
            reaction_id: KEGG reaction ID or other identifier
            organism: Organism name (e.g., "Homo sapiens")
            transition_id: Transition ID for reference
        """
        self.logger.info(f"[SABIO-RK] Pre-filling query from transition {transition_id}")
        
        # Store transition ID for use in search results
        self._context_transition_id = transition_id if transition_id else None
        
        # Pre-fill EC number (use reaction_id if it looks like EC format)
        if ec_number:
            self.ec_entry.set_text(ec_number)
            self.logger.info(f"[SABIO-RK] Set EC number: {ec_number}")
        elif reaction_id:
            # If reaction_id is EC format, use it as EC number
            import re
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', reaction_id):
                self.ec_entry.set_text(reaction_id)
                self.logger.info(f"[SABIO-RK] Set EC number from reaction_id: {reaction_id}")
            else:
                self.logger.warning(f"[SABIO-RK] Reaction ID '{reaction_id}' not in EC format")
                # Clear EC field if we can't use it
                self.ec_entry.set_text("")
        else:
            self.ec_entry.set_text("")
            self.logger.warning(f"[SABIO-RK] No EC number or reaction_id for transition {transition_id}")
        
        # Pre-fill organism if provided and valid
        if organism and hasattr(self, 'organism_combo'):
            # Try to find matching organism in combo box
            model = self.organism_combo.get_model()
            found = False
            
            if model:
                for i, row in enumerate(model):
                    if organism.lower() in row[0].lower() or row[0].lower() in organism.lower():
                        self.organism_combo.set_active(i)
                        found = True
                        self.logger.info(f"[SABIO-RK] Set organism: {row[0]}")
                        break
            
            if not found:
                # Set to "All organisms" if not found
                self.organism_combo.set_active(0)
                self.logger.warning(f"[SABIO-RK] Organism '{organism}' not found in list, using 'All organisms'")
        else:
            # No organism specified, recommend adding one
            if hasattr(self, 'organism_combo'):
                self.organism_combo.set_active(0)  # "All organisms"
            self.logger.info(f"[SABIO-RK] No organism specified for transition {transition_id}")
        
        # Update status to guide user
        if hasattr(self, 'status_label'):
            if ec_number or reaction_id:
                self.status_label.set_markup(
                    f"<i>Query pre-filled from transition {transition_id}. "
                    f"Recommend selecting organism filter before searching.</i>"
                )
            else:
                self.status_label.set_markup(
                    f"<span foreground='red'>No EC number found for transition {transition_id}. "
                    f"Please enter EC number manually.</span>"
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
            if not self.canvas_loader:
                self.logger.warning("No canvas loader available for simulation reset")
                return
            
            drawing_area = self.canvas_loader.get_current_document()
            if not drawing_area:
                self.logger.warning("No active document for simulation reset")
                return
            
            # Find simulation controller for this drawing area
            if hasattr(self.canvas_loader, 'simulation_controllers'):
                if drawing_area in self.canvas_loader.simulation_controllers:
                    controller = self.canvas_loader.simulation_controllers[drawing_area]
                    
                    # Get the canvas manager
                    canvas_manager = self.canvas_loader.canvas_managers.get(drawing_area)
                    
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
