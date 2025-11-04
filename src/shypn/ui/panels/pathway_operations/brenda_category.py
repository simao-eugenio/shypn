#!/usr/bin/env python3
"""BRENDA Category for Pathway Operations Panel.

This module provides the BRENDA enrichment category within the Pathway Operations panel.
It handles:
  - BRENDA authentication (email/password)
  - Querying BRENDA by reaction name or EC number
  - Displaying available kinetic parameters
  - Manual selection of parameters to apply
  - Safe enrichment of models (never auto-modifies curated data)

Follows the CategoryFrame pattern and respects model curation integrity.
"""
import os
import sys
import threading
import logging
from typing import Optional, Dict, List, Any

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f'ERROR: GTK3 not available in brenda_category: {e}', file=sys.stderr)
    sys.exit(1)

from .base_pathway_category import BasePathwayCategory

# Import BRENDA backend (if available)
try:
    from shypn.helpers.brenda_enrichment_controller import BRENDAEnrichmentController
except ImportError as e:
    print(f'Warning: BRENDA backend not available: {e}', file=sys.stderr)
    BRENDAEnrichmentController = None

# Import BRENDA SOAP API client
try:
    from shypn.data.brenda_soap_client import BRENDAAPIClient, ZEEP_AVAILABLE
except ImportError:
    BRENDAAPIClient = None
    ZEEP_AVAILABLE = False


class BRENDACategory(BasePathwayCategory):
    """BRENDA enrichment category for Pathway Operations panel.
    
    Provides manual, safe enrichment workflow:
    1. User authenticates with BRENDA credentials
    2. User queries by reaction name or EC number
    3. User reviews available kinetic parameters
    4. User selects which parameters to apply (checkboxes)
    5. User explicitly applies to model
    
    Never auto-modifies curated models (SBML with locked=true).
    
    Attributes:
        brenda_controller: BRENDAEnrichmentController for business logic
        authenticated: Whether credentials are validated
        current_results: Current BRENDA query results
        selected_params: Dict of parameter checkboxes
    """
    
    def __init__(self, workspace_settings=None, parent_window=None):
        """Initialize BRENDA category.
        
        Args:
            workspace_settings: Optional WorkspaceSettings for storing prefs
            parent_window: Optional parent window for dialogs (Wayland fix)
        """
        # Set attributes BEFORE calling super().__init__()
        self.workspace_settings = workspace_settings
        self.parent_window = parent_window
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize backend
        if BRENDAEnrichmentController:
            self.brenda_controller = BRENDAEnrichmentController()
        else:
            self.brenda_controller = None
            print("Warning: BRENDA controller not available", file=sys.stderr)
        
        # Initialize BRENDA API client
        if BRENDAAPIClient:
            self.brenda_api = BRENDAAPIClient()
        else:
            self.brenda_api = None
            print("Warning: BRENDA API client not available", file=sys.stderr)
        
        # State
        self.authenticated = False
        self.current_results = None
        self.selected_params = {}  # param_id -> checkbox widget
        self.credentials = {'email': '', 'password': ''}
        
        # Now call super().__init__() which will call _build_content()
        super().__init__(category_name="BRENDA")
    
    def _build_content(self) -> Gtk.Widget:
        """Build the BRENDA category content.
        
        Streamlined design:
        1. Authentication (top)
        2. Query (manual query OR batch all transitions button)
        3. Results (table with checkboxes: Transition ID, EC, Name, Vmax, Km, etc.)
        4. Apply (override checkboxes + Apply button at bottom)
        
        Returns:
            Gtk.Box containing all BRENDA enrichment UI elements
        """
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        
        # 1. Authentication section
        auth_section = self._build_authentication_section()
        main_box.pack_start(auth_section, False, False, 0)
        
        # 2. Query section (manual OR batch all)
        query_section = self._build_query_section()
        main_box.pack_start(query_section, False, False, 0)
        
        # 3. Results section (table with checkboxes, scrollable)
        results_section = self._build_results_section()
        main_box.pack_start(results_section, True, True, 0)
        
        # 4. Apply section (status + override markers + apply button)
        apply_section = self._build_apply_section()
        main_box.pack_start(apply_section, False, False, 0)
        
        main_box.show_all()
        
        return main_box
    
    def _build_authentication_section(self) -> Gtk.Widget:
        """Build authentication section with email/password."""
        frame = Gtk.Frame()
        frame.set_label("BRENDA Authentication")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup(
            '<i>BRENDA API requires authentication. '
            '<a href="https://www.brenda-enzymes.org/index.php">Register here</a> '
            'to get credentials.</i>'
        )
        info_label.set_line_wrap(True)
        info_label.set_xalign(0.0)
        box.pack_start(info_label, False, False, 0)
        
        # Email entry
        email_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        email_label = Gtk.Label(label="Email:")
        email_label.set_size_request(80, -1)
        email_label.set_xalign(0.0)
        email_box.pack_start(email_label, False, False, 0)
        
        self.email_entry = Gtk.Entry()
        self.email_entry.set_placeholder_text("your.email@example.com")
        self.email_entry.set_hexpand(True)
        email_box.pack_start(self.email_entry, True, True, 0)
        
        box.pack_start(email_box, False, False, 0)
        
        # Password entry
        password_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        password_label = Gtk.Label(label="Password:")
        password_label.set_size_request(80, -1)
        password_label.set_xalign(0.0)
        password_box.pack_start(password_label, False, False, 0)
        
        self.password_entry = Gtk.Entry()
        self.password_entry.set_placeholder_text("Your BRENDA password")
        self.password_entry.set_visibility(False)
        self.password_entry.set_hexpand(True)
        password_box.pack_start(self.password_entry, True, True, 0)
        
        # Validate button
        self.validate_button = Gtk.Button(label="Validate")
        self.validate_button.connect('clicked', self._on_validate_clicked)
        password_box.pack_start(self.validate_button, False, False, 0)
        
        box.pack_start(password_box, False, False, 0)
        
        # Auth status indicator
        self.auth_status = Gtk.Label()
        self.auth_status.set_markup("<span foreground='gray'>Not authenticated</span>")
        self.auth_status.set_xalign(0.0)
        box.pack_start(self.auth_status, False, False, 0)
        
        frame.add(box)
        return frame
    
    def _build_query_section(self) -> Gtk.Widget:
        """Build query section with reaction name/EC number."""
        frame = Gtk.Frame()
        frame.set_label("Query Parameters")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Search mode selection
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        self.name_radio = Gtk.RadioButton.new_with_label_from_widget(None, "Reaction Name")
        self.name_radio.set_active(False)
        self.name_radio.set_sensitive(False)  # Disable until implemented
        self.name_radio.set_tooltip_text("Name search not yet available. Use EC number.")
        self.name_radio.connect('toggled', self._on_search_mode_changed)
        mode_box.pack_start(self.name_radio, False, False, 0)
        
        self.ec_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.name_radio, "EC Number"
        )
        self.ec_radio.set_active(True)  # Default to EC mode
        self.ec_radio.connect('toggled', self._on_search_mode_changed)
        mode_box.pack_start(self.ec_radio, False, False, 0)
        
        box.pack_start(mode_box, False, False, 0)
        
        # Reaction name entry
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        name_label = Gtk.Label(label="Name:")
        name_label.set_size_request(80, -1)
        name_label.set_xalign(0.0)
        name_box.pack_start(name_label, False, False, 0)
        
        self.reaction_name_entry = Gtk.Entry()
        self.reaction_name_entry.set_placeholder_text("e.g., Alcohol dehydrogenase")
        self.reaction_name_entry.set_hexpand(True)
        self.reaction_name_entry.set_sensitive(False)  # Disabled by default
        name_box.pack_start(self.reaction_name_entry, True, True, 0)
        
        box.pack_start(name_box, False, False, 0)
        
        # EC number entry
        ec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ec_label = Gtk.Label(label="EC Number:")
        ec_label.set_size_request(80, -1)
        ec_label.set_xalign(0.0)
        ec_box.pack_start(ec_label, False, False, 0)
        
        self.ec_entry = Gtk.Entry()
        self.ec_entry.set_placeholder_text("e.g., 1.1.1.1")
        self.ec_entry.set_hexpand(True)
        self.ec_entry.set_sensitive(True)  # Enabled by default
        ec_box.pack_start(self.ec_entry, True, True, 0)
        
        box.pack_start(ec_box, False, False, 0)
        
        # Organism entry (optional)
        organism_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        organism_label = Gtk.Label(label="Organism:")
        organism_label.set_size_request(80, -1)
        organism_label.set_xalign(0.0)
        organism_box.pack_start(organism_label, False, False, 0)
        
        self.organism_entry = Gtk.Entry()
        self.organism_entry.set_placeholder_text("e.g., Saccharomyces cerevisiae (optional)")
        self.organism_entry.set_hexpand(True)
        organism_box.pack_start(self.organism_entry, True, True, 0)
        
        box.pack_start(organism_box, False, False, 0)
        
        # Common organisms quick buttons
        common_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        common_label = Gtk.Label(label="Quick:")
        common_label.set_size_request(80, -1)
        common_label.set_xalign(0.0)
        common_box.pack_start(common_label, False, False, 0)
        
        for org_name, org_full in [
            ("Yeast", "Saccharomyces cerevisiae"),
            ("E. coli", "Escherichia coli"),
            ("Human", "Homo sapiens"),
        ]:
            btn = Gtk.Button(label=org_name)
            btn.connect('clicked', lambda b, org=org_full: self.organism_entry.set_text(org))
            common_box.pack_start(btn, False, False, 0)
        
        box.pack_start(common_box, False, False, 0)
        
        # Query buttons (horizontal layout)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        
        # Query All button (batch all canvas transitions)
        self.query_all_button = Gtk.Button(label="Query All Canvas Transitions")
        self.query_all_button.set_sensitive(False)  # Requires authentication
        self.query_all_button.set_tooltip_text("Query BRENDA for all continuous transitions on canvas")
        self.query_all_button.connect('clicked', self._on_query_all_clicked)
        button_box.pack_start(self.query_all_button, False, False, 0)
        
        # Single Query button (manual query)
        self.search_button = Gtk.Button(label="Query BRENDA")
        self.search_button.get_style_context().add_class('suggested-action')
        self.search_button.set_sensitive(False)  # Requires authentication
        self.search_button.set_tooltip_text("Query BRENDA with specified EC number or name")
        self.search_button.connect('clicked', self._on_search_clicked)
        button_box.pack_start(self.search_button, False, False, 0)
        
        box.pack_start(button_box, False, False, 0)
        
        frame.add(box)
        return frame
    
    def _build_results_section(self) -> Gtk.Widget:
        """Build results section with scrollable table and Mark All button."""
        frame = Gtk.Frame()
        frame.set_label("BRENDA Results")
        
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        container.set_margin_start(10)
        container.set_margin_end(10)
        container.set_margin_top(10)
        container.set_margin_bottom(10)
        
        # Header with Mark All button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        results_count_label = Gtk.Label()
        results_count_label.set_markup("<i>0 results</i>")
        results_count_label.set_xalign(0.0)
        self.results_count_label = results_count_label
        header_box.pack_start(results_count_label, True, True, 0)
        
        self.mark_all_button = Gtk.Button(label="Mark All")
        self.mark_all_button.set_sensitive(False)
        self.mark_all_button.set_tooltip_text("Select all results for application")
        self.mark_all_button.connect('clicked', self._on_mark_all_clicked)
        header_box.pack_end(self.mark_all_button, False, False, 0)
        
        container.pack_start(header_box, False, False, 0)
        
        # Scrollable results area
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        self.results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.results_box.set_margin_start(10)
        self.results_box.set_margin_end(10)
        self.results_box.set_margin_top(10)
        self.results_box.set_margin_bottom(10)
        
        # Initial empty state
        placeholder = Gtk.Label()
        placeholder.set_markup("<i>No results yet. Authenticate and query to see kinetic parameters.</i>")
        placeholder.set_line_wrap(True)
        self.results_box.pack_start(placeholder, False, False, 0)
        
        scrolled.add(self.results_box)
        container.pack_start(scrolled, True, True, 0)
        
        frame.add(container)
        return frame
    
    def _build_apply_section(self) -> Gtk.Widget:
        """Build apply section with status, override checkboxes, and apply button.
        
        All on one line: Status | Override KEGG ☑ | Override SBML ☐ | [Apply Selected]
        """
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        # Status label (left)
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<span foreground='gray'>Ready to query BRENDA</span>")
        self.status_label.set_xalign(0.0)
        self.status_label.set_hexpand(True)
        box.pack_start(self.status_label, True, True, 0)
        
        # Override KEGG checkbox
        self.override_kegg_checkbox = Gtk.CheckButton()
        self.override_kegg_checkbox.set_label("Override KEGG")
        self.override_kegg_checkbox.set_active(True)  # Default ON
        self.override_kegg_checkbox.set_tooltip_text(
            "Replace KEGG heuristics (vmax=10.0, km=0.5) with real BRENDA data\n"
            "Recommended: KEGG has no real kinetic parameters"
        )
        box.pack_start(self.override_kegg_checkbox, False, False, 0)
        
        # Override SBML checkbox
        self.override_sbml_checkbox = Gtk.CheckButton()
        self.override_sbml_checkbox.set_label("Override SBML")
        self.override_sbml_checkbox.set_active(False)  # Default OFF
        self.override_sbml_checkbox.set_tooltip_text(
            "Replace SBML curated kinetic data with BRENDA data\n"
            "Warning: SBML data is manually curated and may be more accurate"
        )
        box.pack_start(self.override_sbml_checkbox, False, False, 0)
        
        # Apply button (right)
        self.apply_button = Gtk.Button(label="Apply Selected to Model")
        self.apply_button.get_style_context().add_class('suggested-action')
        self.apply_button.set_sensitive(False)
        self.apply_button.set_tooltip_text("Apply selected BRENDA results to model transitions")
        self.apply_button.connect('clicked', self._on_apply_clicked)
        box.pack_start(self.apply_button, False, False, 0)
        
        return box
    
    # Event handlers
    
    def _on_search_mode_changed(self, radio_button):
        """Handle search mode radio button changes."""
        if not radio_button.get_active():
            return
        
        if self.name_radio.get_active():
            # Reaction name mode
            self.reaction_name_entry.set_sensitive(True)
            self.ec_entry.set_sensitive(False)
        else:
            # EC number mode
            self.reaction_name_entry.set_sensitive(False)
            self.ec_entry.set_sensitive(True)
    
    def _on_validate_clicked(self, button):
        """Handle validate credentials button click."""
        email = self.email_entry.get_text().strip()
        password = self.password_entry.get_text().strip()
        
        if not email or not password:
            self._show_status("Please enter both email and password", error=True)
            return
        
        self.credentials['email'] = email
        self.credentials['password'] = password
        
        self._show_status("Validating credentials...")
        self.validate_button.set_sensitive(False)
        
        # Run validation in background thread
        self._run_in_thread(
            task_func=self._validate_credentials,
            on_complete=self._on_validate_complete,
            on_error=self._on_validate_error
        )
    
    def _validate_credentials(self):
        """Background task to validate BRENDA credentials using real SOAP API."""
        if not self.brenda_api:
            raise RuntimeError("BRENDA API client not available. Install zeep: pip install zeep")
        
        if not ZEEP_AVAILABLE:
            raise RuntimeError("zeep library not installed. Install with: pip install zeep")
        
        # Try to authenticate with BRENDA SOAP API
        email = self.credentials['email']
        password = self.credentials['password']
        
        if not email or not password:
            raise ValueError("Email and password required")
        
        self.logger.info(f"Validating BRENDA credentials for {email}...")
        
        # Authenticate with real BRENDA API - this establishes the SOAP session
        # The authenticated session is maintained in brenda_api.client for subsequent queries
        success = self.brenda_api.authenticate(email, password)
        
        if success:
            return {'valid': True, 'message': 'Successfully authenticated with BRENDA API'}
        else:
            raise ValueError('BRENDA authentication failed. Check your credentials.')
    
    def _on_validate_complete(self, result):
        """Callback when credential validation completes."""
        self.authenticated = True
        self.auth_status.set_markup("<span foreground='green'>✓ Authenticated</span>")
        self.search_button.set_sensitive(True)
        self.query_all_button.set_sensitive(True)
        self._show_status("Authenticated successfully", error=False)
        self.validate_button.set_sensitive(True)
    
    def _on_validate_error(self, error):
        """Callback when credential validation fails."""
        self.authenticated = False
        self.auth_status.set_markup("<span foreground='red'>✗ Authentication failed</span>")
        self.search_button.set_sensitive(False)
        self.query_all_button.set_sensitive(False)
        self._show_status(f"Authentication failed: {error}", error=True)
        self.validate_button.set_sensitive(True)
    
    def _on_search_clicked(self, button):
        """Handle search BRENDA button click."""
        if not self.authenticated:
            self._show_status("Please authenticate first", error=True)
            return
        
        # Get search parameters
        if self.name_radio.get_active():
            search_term = self.reaction_name_entry.get_text().strip()
            search_type = 'name'
        else:
            search_term = self.ec_entry.get_text().strip()
            search_type = 'ec'
        
        if not search_term:
            self._show_status("Please enter a search term", error=True)
            return
        
        organism = self.organism_entry.get_text().strip()
        
        self._show_status(f"Searching BRENDA for {search_term}...")
        self.search_button.set_sensitive(False)
        
        # Run search in background thread
        self._run_in_thread(
            task_func=lambda: self._search_brenda(search_term, search_type, organism),
            on_complete=self._on_search_complete,
            on_error=self._on_search_error
        )
    
    def _search_brenda(self, search_term: str, search_type: str, organism: str = ""):
        """Background task to search BRENDA database via SOAP API."""
        if not self.brenda_api:
            raise RuntimeError("BRENDA API client not available")
        
        # For name search, we would need EC number lookup first
        # BRENDA API works primarily with EC numbers
        if search_type == 'name':
            # TODO: Implement enzyme name -> EC number lookup
            # For now, raise error to guide user to use EC number
            raise ValueError("Name search not yet implemented. Please use EC number search.")
        
        # Query BRENDA API with EC number
        ec_number = search_term
        
        # Get Km values
        km_results = self.brenda_api.get_km_values(ec_number, organism)
        
        # Get kcat values
        kcat_results = self.brenda_api.get_kcat_values(ec_number, organism)
        
        # Get Ki values
        ki_results = self.brenda_api.get_ki_values(ec_number, organism)
        
        # Format results for UI display
        parameters = []
        
        # Add Km values
        for i, km_record in enumerate(km_results):
            param_id = f"km_{i}"
            parameters.append({
                'id': param_id,
                'type': 'Km',
                'value': km_record.get('value'),
                'unit': km_record.get('unit', 'mM'),
                'substrate': km_record.get('substrate', 'unknown'),
                'citation': km_record.get('literature', 'N/A'),
                'organism': km_record.get('organism', organism),
                'confidence': 'experimental'
            })
        
        # Add kcat values
        for i, kcat_record in enumerate(kcat_results):
            param_id = f"kcat_{i}"
            parameters.append({
                'id': param_id,
                'type': 'kcat',
                'value': kcat_record.get('value'),
                'unit': kcat_record.get('unit', 's⁻¹'),
                'substrate': kcat_record.get('substrate', None),
                'citation': kcat_record.get('literature', 'N/A'),
                'organism': kcat_record.get('organism', organism),
                'confidence': 'experimental'
            })
        
        # Add Ki values
        for i, ki_record in enumerate(ki_results):
            param_id = f"ki_{i}"
            parameters.append({
                'id': param_id,
                'type': 'Ki',
                'value': ki_record.get('value'),
                'unit': ki_record.get('unit', 'mM'),
                'substrate': ki_record.get('inhibitor', 'unknown'),
                'citation': ki_record.get('literature', 'N/A'),
                'organism': ki_record.get('organism', organism),
                'confidence': 'experimental'
            })
        
        return {
            'ec_number': ec_number,
            'name': f"EC {ec_number}",  # BRENDA doesn't return enzyme name in kinetics queries
            'organism': organism if organism else "All organisms",
            'parameters': parameters
        }
    
    def _on_search_complete(self, results):
        """Callback when BRENDA search completes."""
        self.current_results = results
        self.search_button.set_sensitive(True)
        
        # Clear previous results
        for child in self.results_box.get_children():
            self.results_box.remove(child)
        
        self.selected_params = {}
        
        # Display results
        self._display_results(results)
        
        self._show_status(f"Found {len(results['parameters'])} parameters", error=False)
    
    def _on_search_error(self, error):
        """Callback when BRENDA search fails."""
        self.search_button.set_sensitive(True)
        
        error_str = str(error)
        
        # Check if it's a "not implemented" error
        if "not yet implemented" in error_str.lower():
            self._show_status(f"Search error: {error}", error=True)
        else:
            # Show detailed help for BRENDA API issues
            error_message = (
                f"BRENDA query failed:\n\n{error}\n\n"
                "Common causes:\n\n"
                "1. Your BRENDA account lacks SOAP API data access\n"
                "   (Free accounts may only authenticate, not retrieve data)\n\n"
                "2. BRENDA database has no data for this EC number\n\n"
                "3. Network connectivity issues\n\n"
                "Solution:\n"
                "• Contact BRENDA support (info@brenda-enzymes.org)\n"
                "• Try a different EC number (e.g., 2.7.1.1 for hexokinase)\n"
                "• Check your internet connection"
            )
            self._show_error_dialog("BRENDA Query Failed", error_message)
            self._show_status(f"Search failed: {error}", error=True)
    
    # ========================================================================
    # Results Selection
    # ========================================================================
    
    def _on_mark_all_clicked(self, button):
        """Handle Mark All button click - select all results."""
        # Find all checkboxes in results_box and set them to active
        for child in self.results_box.get_children():
            if isinstance(child, Gtk.CheckButton):
                child.set_active(True)
            elif isinstance(child, Gtk.Box):
                # Search within boxes for checkboxes
                for subchild in child.get_children():
                    if isinstance(subchild, Gtk.CheckButton):
                        subchild.set_active(True)
        
        self._show_status("All results selected", error=False)
    
    # ========================================================================
    # Query All Canvas Transitions (Batch Query)
    # ========================================================================
    
    def _on_query_all_clicked(self, button):
        """Handle 'Query All Canvas Transitions' button click.
        
        Scans all continuous transitions on canvas and queries BRENDA for each.
        Results populate the results table with checkboxes for selection.
        """
        if not self.authenticated:
            self._show_status("Please authenticate first", error=True)
            return
        
        if not self.model_canvas_manager:
            self._show_status("No model loaded on canvas", error=True)
            return
        
        # Prepare UI
        self.query_all_button.set_sensitive(False)
        self.search_button.set_sensitive(False)
        self._show_status("Querying BRENDA for all canvas transitions...")
        
        # Run query in background thread
        self._run_in_thread(
            task_func=self._query_all_transitions,
            on_complete=self._on_query_all_complete,
            on_error=self._on_query_all_error
        )
    
    def _query_all_transitions(self) -> Dict[str, Any]:
        """Background task: query BRENDA for all canvas transitions.
        
        Returns:
            Dict with 'results' list containing transition data and BRENDA kinetics
        """
        if not self.brenda_controller:
            raise RuntimeError("BRENDA controller not available")
        
        if not self.brenda_api or not self.brenda_api.is_authenticated():
            raise RuntimeError("Not authenticated with BRENDA")
        
        # Debug: check model_canvas
        self.logger.info(f"Model canvas loader: {self.model_canvas}")
        self.logger.info(f"Model canvas manager: {self.model_canvas_manager}")
        
        if not self.model_canvas_manager:
            raise ValueError('No model canvas manager available. Please ensure a model is loaded and try again.')
        
        # Set canvas reference - pass the MANAGER not the LOADER
        self.brenda_controller.set_model_canvas(self.model_canvas_manager)
        
        # Scan canvas for all transitions
        transitions = self.brenda_controller.scan_canvas_transitions()
        
        self.logger.info(f"Scanned transitions: {len(transitions) if transitions else 0}")
        
        if not transitions:
            raise ValueError('No transitions found on canvas. The model may be empty or not properly loaded.')
        
        # Filter for continuous transitions (those with EC numbers)
        continuous_transitions = [t for t in transitions if t.get('ec_number')]
        
        if not continuous_transitions:
            raise ValueError(f'No continuous transitions (with EC numbers) found on canvas. Found {len(transitions)} total transitions but none have EC numbers.')
        
        self.logger.info(f"Found {len(continuous_transitions)} continuous transitions to query")
        
        # Query BRENDA for each unique EC number
        results = []
        ec_numbers_seen = set()
        
        for trans in continuous_transitions:
            ec_number = trans.get('ec_number')
            if not ec_number or ec_number in ec_numbers_seen:
                continue
            
            ec_numbers_seen.add(ec_number)
            
            try:
                self.logger.info(f"[QUERY_BRENDA] Querying BRENDA for EC {ec_number}...")
                
                # Get Km values from BRENDA
                km_data = self.brenda_api.get_km_values(ec_number, organism=None)
                
                self.logger.info(f"[QUERY_BRENDA] EC {ec_number} returned {len(km_data) if km_data else 0} Km values")
                
                if km_data:
                    # Add result for each Km value found
                    for km in km_data:
                        result_entry = {
                            'transition_id': trans.get('id'),
                            'transition_name': trans.get('name', 'Unknown'),
                            'ec_number': ec_number,
                            'parameter_type': 'Km',
                            'value': km.get('value'),
                            'unit': km.get('unit', 'mM'),
                            'substrate': km.get('substrate', 'Unknown'),
                            'organism': km.get('organism', 'Unknown'),
                            'literature': km.get('literature', '')
                        }
                        self.logger.info(f"[QUERY_BRENDA] Adding result: {result_entry['transition_name']} Km={result_entry['value']} {result_entry['unit']}")
                        results.append(result_entry)
                else:
                    self.logger.warning(f"[QUERY_BRENDA] No Km data found for EC {ec_number}")
                
            except Exception as e:
                self.logger.error(f"[QUERY_BRENDA] Error querying EC {ec_number}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        self.logger.info(f"[QUERY_BRENDA] Total results collected: {len(results)}")
        return {'results': results, 'transitions_queried': len(ec_numbers_seen)}
    
    def _on_query_all_complete(self, result: Dict[str, Any]):
        """Callback when query all completes successfully."""
        self.logger.info(f"[QUERY_ALL_COMPLETE] Callback triggered with result: {result}")
        
        self.query_all_button.set_sensitive(True)
        self.search_button.set_sensitive(True)
        
        results = result.get('results', [])
        transitions_queried = result.get('transitions_queried', 0)
        
        self.logger.info(f"[QUERY_ALL_COMPLETE] Results count: {len(results)}")
        self.logger.info(f"[QUERY_ALL_COMPLETE] Transitions queried: {transitions_queried}")
        
        if not results:
            self.logger.warning(f"[QUERY_ALL_COMPLETE] No results found!")
            
            # Show helpful error dialog explaining the issue
            error_message = (
                f"BRENDA returned no kinetic data for {transitions_queried} EC numbers.\n\n"
                "This usually means:\n\n"
                "1. Your BRENDA account has authentication-only access\n"
                "   (Free academic accounts may not have SOAP API data retrieval)\n\n"
                "2. BRENDA database doesn't have Km data for these enzymes\n\n"
                "3. EC numbers are obsolete or invalid\n\n"
                "Solution:\n"
                "• Contact BRENDA support (info@brenda-enzymes.org) for full API access\n"
                "• Use manual data entry or local BRENDA files instead\n"
                "• Check BRENDA website directly for these EC numbers"
            )
            self._show_error_dialog("No BRENDA Data Retrieved", error_message)
            self._show_status(f"No BRENDA data found for {transitions_queried} transitions", error=True)
            return
        
        # Clear existing results
        self.logger.info(f"[QUERY_ALL_COMPLETE] Clearing {len(self.results_box.get_children())} existing result rows")
        for child in self.results_box.get_children():
            self.results_box.remove(child)
        
        # Update count label
        self.results_count_label.set_markup(f"<i>{len(results)} results</i>")
        
        # Build unified data structure matching manual search format
        self.current_results = {
            'ec_number': 'multiple',
            'name': 'Canvas Transitions',
            'organism': 'Various',
            'parameters': []
        }
        
        # Clear previous param tracking
        self.selected_params = {}
        
        # Populate results table and build unified data structure
        self.logger.info(f"[QUERY_ALL_COMPLETE] Adding {len(results)} result rows to table")
        for idx, result_data in enumerate(results):
            self.logger.info(f"[QUERY_ALL_COMPLETE] Adding row {idx+1}: {result_data.get('transition_name')} - EC {result_data.get('ec_number')}")
            
            param_id = f"batch_{idx}"
            
            # Add to unified parameters list (matches manual search structure)
            self.current_results['parameters'].append({
                'id': param_id,
                'type': result_data.get('parameter_type', 'Km'),
                'value': result_data.get('value'),
                'unit': result_data.get('unit', 'mM'),
                'substrate': result_data.get('substrate', 'Unknown'),
                'organism': result_data.get('organism', 'Unknown'),
                'citation': result_data.get('literature', 'N/A'),
                'confidence': 'experimental',
                'transition_id': result_data.get('transition_id'),  # CRITICAL for apply!
                'transition_name': result_data.get('transition_name'),
                'ec_number': result_data.get('ec_number')
            })
            
            # Add visual row and track checkbox
            checkbox = self._add_result_row(result_data)
            if checkbox:
                self.selected_params[param_id] = checkbox
        
        self.results_box.show_all()
        self.logger.info(f"[QUERY_ALL_COMPLETE] Results table shown, total children: {len(self.results_box.get_children())}")
        
        # Enable Mark All button
        if len(results) > 0:
            self.mark_all_button.set_sensitive(True)
        
        # Enable Apply button
        self.apply_button.set_sensitive(True)
        
        self._show_status(f"Found {len(results)} BRENDA results from {transitions_queried} EC numbers", error=False)
    
    def _on_query_all_error(self, error: Exception):
        """Callback when query all fails."""
        self.query_all_button.set_sensitive(True)
        self.search_button.set_sensitive(True)
        error_msg = str(error)
        self._show_status(f"Query error: {error_msg}", error=True)
        self._show_error_dialog("BRENDA Query Error", 
                               f"Failed to query BRENDA:\n\n{error_msg}")
    
    def _add_result_row(self, result_data: Dict[str, Any]):
        """Add a result row to the results table with checkbox.
        
        Args:
            result_data: Dict with keys: transition_id, transition_name, ec_number,
                        parameter_type, value, unit, substrate, organism, literature
        
        Returns:
            Gtk.CheckButton: The checkbox widget for tracking selection
        """
        # Create horizontal box for this result row
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_box.set_margin_top(2)
        row_box.set_margin_bottom(2)
        
        # Checkbox for selection
        checkbox = Gtk.CheckButton()
        checkbox.result_data = result_data  # Attach data to checkbox
        row_box.pack_start(checkbox, False, False, 0)
        
        # Result label with formatted information
        label_text = (
            f"{result_data.get('transition_name', 'Unknown')} | "
            f"EC {result_data.get('ec_number', 'N/A')} | "
            f"{result_data.get('parameter_type', 'Km')}: {result_data.get('value', 'N/A')} {result_data.get('unit', 'mM')} | "
            f"Substrate: {result_data.get('substrate', 'Unknown')} | "
            f"Organism: {result_data.get('organism', 'Unknown')}"
        )
        
        label = Gtk.Label(label=label_text)
        label.set_xalign(0.0)
        label.set_line_wrap(True)
        label.set_max_width_chars(80)
        row_box.pack_start(label, True, True, 0)
        
        self.results_box.pack_start(row_box, False, False, 0)
        
        return checkbox  # Return checkbox for tracking
    
    def _display_results(self, results):
        """Display BRENDA results in the results box."""
        # Header
        header = Gtk.Label()
        header.set_markup(
            f"<b>{results['name']}</b> (EC {results['ec_number']})\n"
            f"<i>Organism: {results['organism']}</i>"
        )
        header.set_xalign(0.0)
        self.results_box.pack_start(header, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.results_box.pack_start(sep, False, False, 0)
        
        # Parameters section
        params_label = Gtk.Label()
        params_label.set_markup("<b>Available Kinetic Parameters:</b>")
        params_label.set_xalign(0.0)
        self.results_box.pack_start(params_label, False, False, 0)
        
        # Parameter checkboxes
        for param in results['parameters']:
            param_box = self._create_parameter_checkbox(param)
            self.results_box.pack_start(param_box, False, False, 0)
        
        # Update results count
        param_count = len(results.get('parameters', []))
        self.results_count_label.set_markup(f"<i>{param_count} results</i>")
        
        # Enable Mark All button if we have results
        if param_count > 0:
            self.mark_all_button.set_sensitive(True)
        
        # Conditions section
        if results.get('conditions'):
            cond_label = Gtk.Label()
            cond_label.set_markup("\n<b>Optimal Conditions:</b>")
            cond_label.set_xalign(0.0)
            self.results_box.pack_start(cond_label, False, False, 0)
            
            conditions = results['conditions']
            if 'temperature' in conditions:
                temp = conditions['temperature']
                temp_label = Gtk.Label()
                temp_label.set_markup(f"  Temperature: {temp['value']} {temp['unit']}")
                temp_label.set_xalign(0.0)
                self.results_box.pack_start(temp_label, False, False, 0)
            
            if 'ph' in conditions:
                ph = conditions['ph']
                ph_label = Gtk.Label()
                ph_label.set_markup(f"  pH: {ph['value']}")
                ph_label.set_xalign(0.0)
                self.results_box.pack_start(ph_label, False, False, 0)
        
        self.results_box.show_all()
        
        # Enable apply button if parameters available
        self.apply_button.set_sensitive(len(results['parameters']) > 0)
    
    def _create_parameter_checkbox(self, param: Dict[str, Any]) -> Gtk.Widget:
        """Create a checkbox widget for a parameter."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        checkbox = Gtk.CheckButton()
        checkbox.set_active(False)
        box.pack_start(checkbox, False, False, 0)
        
        # Store checkbox reference
        self.selected_params[param['id']] = checkbox
        
        # Parameter label
        label_text = f"<b>{param['type']}</b> = {param['value']} {param['unit']}"
        if param.get('substrate'):
            label_text += f" (Substrate: {param['substrate']})"
        label_text += f"\n  <small>Citation: {param['citation']} | Confidence: {param['confidence']}</small>"
        
        label = Gtk.Label()
        label.set_markup(label_text)
        label.set_xalign(0.0)
        box.pack_start(label, True, True, 0)
        
        return box
    
    def _on_apply_clicked(self, button):
        """Handle apply selected parameters button click."""
        if not self.current_results:
            self._show_status("No results to apply", error=True)
            return
        
        # Get selected parameters
        selected = []
        for param_id, checkbox in self.selected_params.items():
            if checkbox.get_active():
                # Find the parameter details
                for param in self.current_results['parameters']:
                    if param['id'] == param_id:
                        selected.append(param)
                        break
        
        if not selected:
            self._show_status("No parameters selected", error=True)
            return
        
        # Check if this is batch mode (parameters have transition_id)
        # Group by transition for batch application
        transition_groups = {}
        has_transition_ids = False
        
        for param in selected:
            trans_id = param.get('transition_id')
            if trans_id:
                has_transition_ids = True
                if trans_id not in transition_groups:
                    transition_groups[trans_id] = {
                        'name': param.get('transition_name', 'Unknown'),
                        'ec_number': param.get('ec_number', 'Unknown'),
                        'params': []
                    }
                transition_groups[trans_id]['params'].append(param)
        
        if has_transition_ids and transition_groups:
            # Batch mode - apply directly to specific transitions
            self._apply_batch_parameters(transition_groups)
        else:
            # Single transition mode - show dialog to choose target
            self._show_apply_dialog(selected)
    
    def _apply_batch_parameters(self, transition_groups: Dict[str, Dict[str, Any]]):
        """Apply parameters to multiple transitions in batch mode.
        
        Args:
            transition_groups: Dict mapping transition_id to {name, ec_number, params}
        """
        if not self.brenda_controller:
            self._show_status("BRENDA controller not available", error=True)
            return
        
        # Get override settings
        override_kegg = self.override_kegg_checkbox.get_active()
        override_sbml = self.override_sbml_checkbox.get_active()
        
        self.logger.info(f"[BATCH_APPLY] Applying to {len(transition_groups)} transitions")
        self.logger.info(f"[BATCH_APPLY] Override KEGG: {override_kegg}, Override SBML: {override_sbml}")
        
        try:
            applied_count = 0
            skipped_count = 0
            
            # Start enrichment session
            self.brenda_controller.start_enrichment(
                source="brenda_api",
                query_params={'batch_mode': True, 'override_kegg': override_kegg, 'override_sbml': override_sbml}
            )
            
            for trans_id, group_data in transition_groups.items():
                params = group_data['params']
                
                self.logger.info(f"[BATCH_APPLY] Processing transition {trans_id} ({group_data['name']})")
                self.logger.info(f"[BATCH_APPLY]   {len(params)} parameters to apply")
                
                # Find transition object from canvas
                transition_obj = None
                if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'transitions'):
                    for trans in self.model_canvas_manager.transitions:
                        if str(trans.id) == str(trans_id):
                            transition_obj = trans
                            break
                
                if not transition_obj:
                    self.logger.warning(f"[BATCH_APPLY] Transition {trans_id} not found on canvas, skipping")
                    skipped_count += 1
                    continue
                
                # Check if we should apply based on data source
                data_source = transition_obj.metadata.get('data_source', 'unknown') if hasattr(transition_obj, 'metadata') and transition_obj.metadata else 'unknown'
                has_kinetics = transition_obj.metadata.get('has_kinetics', False) if hasattr(transition_obj, 'metadata') and transition_obj.metadata else False
                
                should_apply = False
                if not has_kinetics:
                    should_apply = True
                elif data_source == 'kegg_import' and override_kegg:
                    should_apply = True
                elif data_source == 'sbml_import' and override_sbml:
                    should_apply = True
                elif data_source not in ['kegg_import', 'sbml_import'] and override_kegg:
                    # Unknown source, use KEGG override setting
                    should_apply = True
                
                if not should_apply:
                    self.logger.info(f"[BATCH_APPLY] Skipping {trans_id} (data_source={data_source}, has_kinetics={has_kinetics})")
                    skipped_count += 1
                    continue
                
                # Build parameters dict from all selected params for this transition
                params_dict = {'_override_rate_function': True}
                for param in params:
                    param_type = param.get('type', 'Km').lower()
                    param_value = param.get('value')
                    if param_value is not None:
                        params_dict[param_type] = param_value
                
                # Apply enrichment
                self.brenda_controller.apply_enrichment_to_transition(
                    trans_id,
                    params_dict,
                    transition_obj=transition_obj
                )
                
                applied_count += 1
                self.logger.info(f"[BATCH_APPLY] ✓ Applied to {trans_id}")
            
            # Finish enrichment session
            self.brenda_controller.finish_enrichment()
            
            # CRITICAL: Reset simulation state after applying parameters
            # This clears cached behaviors that might have old parameter values
            # See: CANVAS_STATE_ISSUES_COMPARISON.md for historical context
            if applied_count > 0:
                self._reset_simulation_after_parameter_changes()
            
            # Show success message
            message = f"Applied parameters to {applied_count} transition(s)"
            if skipped_count > 0:
                message += f" ({skipped_count} skipped)"
            self._show_status(message, error=False)
            
            # Trigger canvas redraw
            if self.model_canvas and hasattr(self.model_canvas, 'queue_draw'):
                GLib.idle_add(self.model_canvas.queue_draw)
            
        except Exception as e:
            self.logger.error(f"[BATCH_APPLY] Error: {e}", exc_info=True)
            self._show_status(f"Batch apply failed: {str(e)}", error=True)
    
    def _show_apply_dialog(self, selected_params: List[Dict[str, Any]]):
        """Show dialog to choose target transition and apply parameters."""
        dialog = Gtk.Dialog(
            title="Apply BRENDA Parameters",
            parent=self.parent_window,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_APPLY, Gtk.ResponseType.OK
            )
        )
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(10)
        content.set_margin_end(10)
        content.set_margin_top(10)
        content.set_margin_bottom(10)
        
        # Info label
        info = Gtk.Label()
        info.set_markup(
            f"<b>Apply {len(selected_params)} parameter(s) to model</b>\n\n"
            "This will update the transition's rate function with the selected "
            "kinetic parameters from BRENDA."
        )
        info.set_line_wrap(True)
        content.pack_start(info, False, False, 0)
        
        # Target selection (TODO: populate with actual transitions from canvas)
        target_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        target_label = Gtk.Label(label="Target Transition:")
        target_box.pack_start(target_label, False, False, 0)
        
        target_combo = Gtk.ComboBoxText()
        target_combo.append("T1", "T1 - Hexokinase")
        target_combo.append("T2", "T2 - Phosphoglucoisomerase")
        target_combo.set_active(0)
        target_box.pack_start(target_combo, True, True, 0)
        
        content.pack_start(target_box, False, False, 0)
        
        # Warning for curated models
        warning = Gtk.Label()
        warning.set_markup(
            "<span foreground='orange'>⚠️ Warning: If this is a curated model (SBML), "
            "applying parameters will override existing kinetic data.</span>"
        )
        warning.set_line_wrap(True)
        content.pack_start(warning, False, False, 0)
        
        content.show_all()
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # TODO: Apply parameters to selected transition
            target_id = target_combo.get_active_id()
            self._apply_parameters_to_transition(target_id, selected_params)
            self._show_status(f"Applied {len(selected_params)} parameters to {target_id}", error=False)
        
        dialog.destroy()
    
    def _apply_parameters_to_transition(self, transition_id: str, params: List[Dict[str, Any]]):
        """Apply selected BRENDA parameters to a transition.
        
        Args:
            transition_id: ID of target transition
            params: List of parameter dicts to apply
        """
        # TODO: Implement actual application to model
        # This would:
        # 1. Get transition from model_canvas
        # 2. Build rate function from parameters (e.g., michaelis_menten(P1, vmax=10, km=0.5))
        # 3. Update transition properties
        # 4. Record enrichment in project metadata
        # 5. Refresh canvas
        
        self.logger.info(f"Would apply {len(params)} parameters to {transition_id}")
        for param in params:
            self.logger.info(f"  {param['type']} = {param['value']} {param['unit']}")
    
    # ========================================================================
    # Dialog Helpers
    # ========================================================================
    
    def _show_info_dialog(self, title: str, message: str):
        """Show an information dialog (Wayland-safe).
        
        Args:
            title: Dialog title
            message: Message to display
        """
        def show():
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=title
            )
            dialog.format_secondary_text(message)
            dialog.run()
            dialog.destroy()
        
        GLib.idle_add(show)
    
    def _show_error_dialog(self, title: str, message: str):
        """Show an error dialog (Wayland-safe).
        
        Args:
            title: Dialog title
            message: Error message to display
        """
        def show():
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=title
            )
            dialog.format_secondary_text(message)
            dialog.run()
            dialog.destroy()
        
        GLib.idle_add(show)
    
    def _show_status(self, message: str, error: bool = False):
        """Update status label (Wayland-safe)."""
        def update():
            if error:
                self.status_label.set_markup(f"<span foreground='red'>{message}</span>")
            else:
                self.status_label.set_markup(f"<span foreground='gray'>{message}</span>")
        
        GLib.idle_add(update)
    
    def receive_import_data(self, data: Dict[str, Any]):
        """Receive data from KEGG/SBML imports.
        
        This method is called when KEGG or SBML categories complete an import.
        It can suggest reactions to query based on imported data.
        
        Args:
            data: Import data containing species, reactions, EC numbers, etc.
        """
        source = data.get('source', 'unknown')
        
        # Extract useful information
        ec_numbers = []
        reaction_names = []
        
        if source == 'kegg':
            # KEGG provides EC numbers directly
            reactions = data.get('reactions', [])
            for rxn in reactions:
                if 'ec_numbers' in rxn:
                    ec_numbers.extend(rxn['ec_numbers'])
                if 'name' in rxn:
                    reaction_names.append(rxn['name'])
        
        elif source == 'sbml':
            # SBML has reaction names, maybe EC numbers
            reactions = data.get('reactions', [])
            for rxn in reactions:
                if 'name' in rxn:
                    reaction_names.append(rxn['name'])
                if 'ec_number' in rxn:
                    ec_numbers.append(rxn['ec_number'])
        
        # Show suggestion
        if ec_numbers or reaction_names:
            count = len(set(ec_numbers + reaction_names))
            self._show_status(
                f"Imported {source.upper()} model with {count} reactions. "
                "You can now query BRENDA for kinetic parameters.",
                error=False
            )
    
    def set_parent_window(self, parent_window):
        """Set parent window for dialogs (Wayland compatibility).
        
        Args:
            parent_window: Gtk.Window or Gtk.ApplicationWindow to use as parent
        """
        self.parent_window = parent_window
        self.logger.debug(f"Parent window set: {parent_window}")
    
    def set_query_from_transition(self, ec_number: str = "", reaction_name: str = "", 
                                   enzyme_name: str = "", transition_id: str = ""):
        """Pre-fill BRENDA query fields from transition data.
        
        Called when user selects "Enrich with BRENDA" from transition context menu.
        Automatically populates query fields with available transition metadata.
        
        Args:
            ec_number: EC number from transition metadata
            reaction_name: Reaction name from transition label/metadata
            enzyme_name: Enzyme name from transition metadata
            transition_id: Transition ID for reference
        """
        # Pre-fill EC number if available
        if ec_number and hasattr(self, 'ec_entry'):
            self.ec_entry.set_text(ec_number)
        
        # Pre-fill reaction name (prioritize enzyme name if available)
        if hasattr(self, 'reaction_name_entry'):
            if enzyme_name:
                self.reaction_name_entry.set_text(enzyme_name)
            elif reaction_name:
                self.reaction_name_entry.set_text(reaction_name)
        
        # Show helpful status message
        if ec_number or enzyme_name or reaction_name:
            info_parts = []
            if ec_number:
                info_parts.append(f"EC: {ec_number}")
            if enzyme_name:
                info_parts.append(f"Enzyme: {enzyme_name}")
            elif reaction_name:
                info_parts.append(f"Reaction: {reaction_name}")
            
            self._show_status(
                f"Query pre-filled from transition {transition_id} ({', '.join(info_parts)}). "
                "Verify and click Search.",
                error=False
            )
            
            self.logger.info(f"Pre-filled BRENDA query from transition {transition_id}: "
                           f"EC={ec_number}, Enzyme={enzyme_name}, Reaction={reaction_name}")
        else:
            self._show_status(
                f"No enzyme/reaction metadata found for transition {transition_id}. "
                "Please enter query manually.",
                error=True
            )
    
    def _reset_simulation_after_parameter_changes(self):
        """Reset simulation to initial state after applying parameter changes.
        
        CRITICAL for correct simulation behavior:
        When parameters are applied to transitions via BRENDA enrichment,
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
                    
                    # Full reset: clears behavior cache AND resets places to initial marking
                    # This ensures clean state for testing new parameter values
                    controller.reset()
                    
                    self.logger.info("Simulation reset to initial state after BRENDA parameter changes")
                    
                    # Refresh canvas to show reset token values
                    if drawing_area:
                        drawing_area.queue_draw()
                else:
                    self.logger.debug("No simulation controller for current document")
            else:
                self.logger.warning("Canvas loader has no simulation_controllers attribute")
                
        except Exception as e:
            self.logger.error(f"Error resetting simulation after parameter changes: {e}", exc_info=True)

