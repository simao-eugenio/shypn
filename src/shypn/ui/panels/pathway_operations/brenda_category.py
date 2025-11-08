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

# Import BRENDA data filter
try:
    from shypn.helpers.brenda_data_filter import BRENDADataFilter
except ImportError:
    BRENDADataFilter = None

# Import heuristic database
try:
    from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
except ImportError:
    HeuristicDatabase = None

# Import KEGG EC fetcher for converting KEGG reaction IDs to EC numbers
try:
    from shypn.data.kegg_ec_fetcher import KEGGECFetcher
except ImportError:
    KEGGECFetcher = None


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
    
    def __init__(self, workspace_settings=None, parent_window=None, model_canvas_loader=None):
        """Initialize BRENDA category.
        
        Args:
            workspace_settings: Optional WorkspaceSettings for storing prefs
            parent_window: Optional parent window for dialogs (Wayland fix)
            model_canvas_loader: Reference to model canvas loader for simulation reset
        """
        # Set attributes BEFORE calling super().__init__()
        self.workspace_settings = workspace_settings
        self.parent_window = parent_window
        self.model_canvas_loader = model_canvas_loader
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
        
        # Initialize heuristic database
        if HeuristicDatabase:
            try:
                self.heuristic_db = HeuristicDatabase()
                self.logger.info("Heuristic database initialized")
            except Exception as e:
                self.heuristic_db = None
                self.logger.warning(f"Failed to initialize heuristic database: {e}")
        else:
            self.heuristic_db = None
        
        # Initialize KEGG EC fetcher
        if KEGGECFetcher:
            try:
                self.kegg_ec_fetcher = KEGGECFetcher()
                self.logger.info("KEGG EC fetcher initialized")
            except Exception as e:
                self.kegg_ec_fetcher = None
                self.logger.warning(f"Failed to initialize KEGG EC fetcher: {e}")
        else:
            self.kegg_ec_fetcher = None
        
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
        self.ec_entry.set_placeholder_text("e.g., 1.1.1.1 or R00754 (KEGG)")
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
        """Build results section with TreeView for better data management."""
        frame = Gtk.Frame()
        frame.set_label("BRENDA Results")
        
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        container.set_margin_start(10)
        container.set_margin_end(10)
        container.set_margin_top(10)
        container.set_margin_bottom(10)
        
        # Header with results count
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        # Selected transition label (shows which transition is being enriched)
        selected_trans_label = Gtk.Label()
        selected_trans_label.set_markup("<b>Target:</b> <i>None</i>")
        selected_trans_label.set_xalign(0.0)
        self.selected_trans_label = selected_trans_label
        header_box.pack_start(selected_trans_label, False, False, 0)
        
        # Separator
        separator_label = Gtk.Label(label=" | ")
        header_box.pack_start(separator_label, False, False, 0)
        
        # Results count
        results_count_label = Gtk.Label()
        results_count_label.set_markup("<i>0 results</i>")
        results_count_label.set_xalign(0.0)
        self.results_count_label = results_count_label
        header_box.pack_start(results_count_label, True, True, 0)
        
        container.pack_start(header_box, False, False, 0)
        
        # Scrollable TreeView for results
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(250)
        
        # TreeView columns:
        # 0: Selected (bool)
        # 1: Transition ID (str)
        # 2: EC Number (str)
        # 3: Km Value (str)
        # 4: Kcat Value (str)
        # 5: Ki Value (str)
        # 6: Substrate (str)
        # 7: Organism (str)
        # 8: Quality Score (str)
        # 9: Literature (str)
        # 10: Raw data object
        self.results_store = Gtk.ListStore(
            bool,    # 0: Selected
            str,     # 1: Transition ID
            str,     # 2: EC Number
            str,     # 3: Km Value (with unit)
            str,     # 4: Kcat Value (with unit)
            str,     # 5: Ki Value (with unit)
            str,     # 6: Substrate
            str,     # 7: Organism
            str,     # 8: Quality Score
            str,     # 9: Literature
            object   # 10: Raw data object
        )
        
        self.results_tree = Gtk.TreeView(model=self.results_store)
        self.results_tree.set_headers_visible(True)
        self.results_tree.set_enable_search(True)
        self.results_tree.set_search_column(2)  # Search by EC Number
        
        # Selected column with checkbox
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.set_activatable(True)
        renderer_toggle.connect('toggled', self._on_result_selection_toggled)
        
        column_select = Gtk.TreeViewColumn("☐", renderer_toggle, active=0)
        column_select.set_fixed_width(40)
        column_select.set_clickable(True)
        column_select.connect('clicked', self._on_select_all_header_clicked)
        self.results_tree.append_column(column_select)
        self.select_column = column_select
        self._all_selected = False
        
        # Define data columns with widths
        columns = [
            ("Transition ID", 1, 120),
            ("EC", 2, 80),
            ("Km", 3, 90),
            ("Kcat", 4, 90),
            ("Ki", 5, 90),
            ("Substrate", 6, 120),
            ("Organism", 7, 150),
            ("Quality", 8, 80),
            ("Reference", 9, 100)
        ]
        
        for title, col_id, width in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_resizable(True)
            column.set_fixed_width(width)
            column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            column.set_sort_column_id(col_id)
            self.results_tree.append_column(column)
        
        scrolled.add(self.results_tree)
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
        
        # Clear previous results before new query
        self.results_store.clear()
        self.current_results = None
        self.selected_params = {}
        
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
        import re
        
        if not self.brenda_api:
            raise RuntimeError("BRENDA API client not available")
        
        # For name search, we would need EC number lookup first
        # BRENDA API works primarily with EC numbers
        if search_type == 'name':
            # TODO: Implement enzyme name -> EC number lookup
            # For now, raise error to guide user to use EC number
            raise ValueError("Name search not yet implemented. Please use EC number search.")
        
        # Check if search_term is a KEGG reaction ID (e.g., R00754)
        ec_number = search_term
        if re.match(r'^R\d{5}$', search_term):
            self.logger.info(f"Detected KEGG reaction ID: {search_term}")
            if self.kegg_ec_fetcher:
                self.logger.info(f"Converting KEGG reaction {search_term} to EC number...")
                try:
                    ec_numbers = self.kegg_ec_fetcher.fetch_ec_numbers(search_term)
                    if ec_numbers:
                        ec_number = ec_numbers[0]
                        self.logger.info(f"Converted {search_term} to EC {ec_number}")
                        # Update UI status (must use GLib.idle_add for thread safety)
                        GLib.idle_add(self._show_status, 
                                     f"Converted KEGG {search_term} to EC {ec_number}, querying BRENDA...", 
                                     False)
                    else:
                        raise ValueError(f"No EC number found for KEGG reaction {search_term}. "
                                       f"This reaction may not have an associated enzyme.")
                except Exception as e:
                    raise ValueError(f"Failed to convert KEGG reaction {search_term} to EC number: {e}")
            else:
                raise ValueError(f"KEGG reaction ID detected ({search_term}) but KEGG EC fetcher not available. "
                               f"Please enter an EC number directly.")
        
        # Query BRENDA API with EC number
        
        # Get Km values
        km_results = self.brenda_api.get_km_values(ec_number, organism)
        
        # Get kcat values
        kcat_results = self.brenda_api.get_kcat_values(ec_number, organism)
        
        # Get Ki values
        ki_results = self.brenda_api.get_ki_values(ec_number, organism)
        
        # Group parameters by organism + substrate + literature reference
        # This groups Km, Kcat, Ki that were measured together in the same experiment
        parameter_groups = {}
        
        def get_group_key(record, substrate_key='substrate'):
            """Create a key to group parameters from the same measurement."""
            org = (record.get('organism') or '').strip().lower()
            substrate = (record.get(substrate_key) or '').strip().lower()
            lit = (record.get('literature') or '').strip()
            # Group by organism + substrate (literature may vary slightly)
            return f"{org}|{substrate}"
        
        # Process Km values
        for km_record in km_results:
            key = get_group_key(km_record, 'substrate')
            if key not in parameter_groups:
                parameter_groups[key] = {
                    'organism': km_record.get('organism', organism),
                    'substrate': km_record.get('substrate', 'unknown'),
                    'citation': km_record.get('literature', 'N/A'),
                    'commentary': km_record.get('commentary', ''),
                    'km': None,
                    'km_unit': 'mM',
                    'kcat': None,
                    'kcat_unit': 's⁻¹',
                    'ki': None,
                    'ki_unit': 'mM'
                }
            parameter_groups[key]['km'] = km_record.get('value')
            parameter_groups[key]['km_unit'] = km_record.get('unit', 'mM')
            # Use the first literature reference found
            if not parameter_groups[key]['citation'] or parameter_groups[key]['citation'] == 'N/A':
                parameter_groups[key]['citation'] = km_record.get('literature', 'N/A')
        
        # Process Kcat values
        for kcat_record in kcat_results:
            key = get_group_key(kcat_record, 'substrate')
            if key not in parameter_groups:
                parameter_groups[key] = {
                    'organism': kcat_record.get('organism', organism),
                    'substrate': kcat_record.get('substrate', 'unknown'),
                    'citation': kcat_record.get('literature', 'N/A'),
                    'commentary': kcat_record.get('commentary', ''),
                    'km': None,
                    'km_unit': 'mM',
                    'kcat': None,
                    'kcat_unit': 's⁻¹',
                    'ki': None,
                    'ki_unit': 'mM'
                }
            parameter_groups[key]['kcat'] = kcat_record.get('value')
            parameter_groups[key]['kcat_unit'] = kcat_record.get('unit', 's⁻¹')
            if not parameter_groups[key]['citation'] or parameter_groups[key]['citation'] == 'N/A':
                parameter_groups[key]['citation'] = kcat_record.get('literature', 'N/A')
        
        # Process Ki values
        for ki_record in ki_results:
            key = get_group_key(ki_record, 'inhibitor')
            if key not in parameter_groups:
                parameter_groups[key] = {
                    'organism': ki_record.get('organism', organism),
                    'substrate': ki_record.get('inhibitor', 'unknown'),  # Ki uses 'inhibitor' field
                    'citation': ki_record.get('literature', 'N/A'),
                    'commentary': ki_record.get('commentary', ''),
                    'km': None,
                    'km_unit': 'mM',
                    'kcat': None,
                    'kcat_unit': 's⁻¹',
                    'ki': None,
                    'ki_unit': 'mM'
                }
            parameter_groups[key]['ki'] = ki_record.get('value')
            parameter_groups[key]['ki_unit'] = ki_record.get('unit', 'mM')
            if not parameter_groups[key]['citation'] or parameter_groups[key]['citation'] == 'N/A':
                parameter_groups[key]['citation'] = ki_record.get('literature', 'N/A')
        
        # Convert grouped parameters to list
        parameters = []
        for i, (key, group) in enumerate(parameter_groups.items()):
            param_id = f"param_{i}"
            parameters.append({
                'id': param_id,
                'organism': group['organism'],
                'substrate': group['substrate'],
                'citation': group['citation'],
                'commentary': group['commentary'],
                'km': group['km'],
                'km_unit': group['km_unit'],
                'kcat': group['kcat'],
                'kcat_unit': group['kcat_unit'],
                'ki': group['ki'],
                'ki_unit': group['ki_unit'],
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
        
        # Note: Results already cleared at query start in _on_search_clicked()
        
        # Auto-save to database if available
        if self.heuristic_db and results and 'parameters' in results:
            try:
                # Convert to database format
                db_results = []
                for param in results['parameters']:
                    db_results.append({
                        'ec_number': results.get('ec_number', ''),
                        'parameter_type': param.get('type', ''),
                        'value': param.get('value', 0.0),
                        'unit': param.get('unit', ''),
                        'substrate': param.get('substrate', ''),
                        'organism': param.get('organism', ''),
                        'literature': param.get('citation', ''),
                        'commentary': '',
                        'quality': 0.5  # Default quality for single queries
                    })
                
                if db_results:
                    inserted_count = self.heuristic_db.insert_brenda_raw_data(db_results)
                    self.logger.info(f"Saved {inserted_count} BRENDA results to local database")
                    
                    # Calculate statistics
                    ec_number = results.get('ec_number', '')
                    if ec_number:
                        stats = self.heuristic_db.calculate_brenda_statistics(
                            ec_number=ec_number,
                            parameter_type='Km'  # Assume Km for now
                        )
                        if stats:
                            self.logger.info(f"Calculated statistics for {ec_number}: "
                                           f"mean={stats['mean_value']:.3f}, n={stats['count']}")
                
            except Exception as e:
                self.logger.error(f"Failed to save BRENDA results to database: {e}")
        
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
    
    def _on_result_selection_toggled(self, renderer, path):
        """Handle individual result row selection toggle."""
        self.results_store[path][0] = not self.results_store[path][0]
        self._update_apply_button()
    
    def _on_select_all_header_clicked(self, column):
        """Handle select all header click (toggle all checkboxes)."""
        # Toggle all rows
        self._all_selected = not self._all_selected
        
        for row in self.results_store:
            row[0] = self._all_selected
        
        # Update header label
        self.select_column.set_title("☑" if self._all_selected else "☐")
        self._update_apply_button()
    
    def _update_apply_button(self):
        """Update apply button sensitivity based on selection."""
        has_selection = any(row[0] for row in self.results_store)
        self.apply_button.set_sensitive(has_selection)
    
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
        
        # Clear previous results before new query
        self.results_store.clear()
        self.current_results = None
        self.selected_params = {}
        
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
        
        # Build unified data structure for display
        unified_results = {
            'ec_number': 'multiple',
            'name': 'Canvas Transitions',
            'organism': 'Various',
            'parameters': []
        }
        
        # Convert batch results to parameter format
        for idx, result_data in enumerate(results):
            unified_results['parameters'].append({
                'id': f"batch_{idx}",
                'type': result_data.get('parameter_type', 'Km'),
                'value': result_data.get('value'),
                'unit': result_data.get('unit', 'mM'),
                'substrate': result_data.get('substrate', 'Unknown'),
                'organism': result_data.get('organism', 'Unknown'),
                'citation': result_data.get('literature', 'N/A'),
                'confidence': 'experimental',
                'transition_id': result_data.get('transition_id'),
                'transition_name': result_data.get('transition_name'),
                'ec_number': result_data.get('ec_number')
            })
        
        # Auto-save to database if available
        if self.heuristic_db and results:
            try:
                inserted_count = self.heuristic_db.insert_brenda_raw_data(results)
                self.logger.info(f"Saved {inserted_count} BRENDA results to local database")
                
                # Calculate and cache statistics for each unique EC number
                unique_ecs = set(r.get('ec_number') for r in results if r.get('ec_number'))
                stats_calculated = 0
                for ec_number in unique_ecs:
                    # Calculate stats for Km, kcat, Ki if present
                    for param_type in ['Km', 'kcat', 'Ki']:
                        ec_results = [r for r in results 
                                     if r.get('ec_number') == ec_number 
                                     and r.get('parameter_type') == param_type]
                        if ec_results:
                            stats = self.heuristic_db.calculate_brenda_statistics(
                                ec_number=ec_number,
                                parameter_type=param_type
                            )
                            if stats:
                                stats_calculated += 1
                                self.logger.info(f"Calculated {param_type} statistics for {ec_number}: "
                                               f"mean={stats['mean_value']:.3f}, n={stats['count']}")
                
                # Show database summary in status
                db_summary = self.heuristic_db.get_brenda_summary()
                self.logger.info(f"Database now contains {db_summary['total_records']} BRENDA records "
                               f"from {db_summary['unique_ec_numbers']} EC numbers")
                
            except Exception as e:
                self.logger.error(f"Failed to save BRENDA results to database: {e}")
        
        # Display in TreeView
        self._display_results(unified_results)
        
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
        """Display BRENDA results in the TreeView with smart ranking."""
        # Clear existing results
        self.results_store.clear()
        
        # Store current results for application
        self.current_results = results
        
        total_param_count = len(results.get('parameters', []))
        
        if total_param_count == 0:
            self.results_count_label.set_markup(f"<i>0 results</i>")
            return
        
        # Import filter for quality scoring
        from shypn.helpers.brenda_data_filter import BRENDADataFilter
        filter_engine = BRENDADataFilter(model_organism=results.get('organism'))
        
        # Get transition context for smart filtering (if available)
        context = getattr(self, '_transition_context', {})
        context_organism = context.get('organism', '')
        context_substrates = context.get('substrates', [])
        
        # Calculate quality scores and relevance for all parameters
        scored_params = []
        filtered_count = 0
        
        for param in results['parameters']:
            # FILTER: Only include parameter sets that have Kcat
            # Kcat is needed to calculate Vmax for rate function generation
            # Skip parameters that don't have Kcat (cannot generate complete rate function)
            if param.get('kcat') is None:
                filtered_count += 1
                self.logger.info(f"[BRENDA_FILTER] Skipping parameter set without Kcat: "
                               f"organism={param.get('organism')}, substrate={param.get('substrate')}, "
                               f"km={param.get('km')}, ki={param.get('ki')}")
                continue
            
            # Calculate quality score (0-100%) based on data completeness
            quality_data = {
                'organism': param.get('organism', ''),
                'substrate': param.get('substrate', ''),
                'value': param.get('km') or param.get('kcat') or param.get('ki'),  # Use any available value
                'literature': param.get('citation', '')
            }
            quality_score = filter_engine._calculate_quality_score(
                quality_data,
                results.get('organism') or context_organism,
                param.get('substrate')
            )
            
            # Bonus for having multiple parameters (Km + Kcat is better than just Km)
            completeness_bonus = 0.0
            param_count = sum([
                1 if param.get('km') is not None else 0,
                1 if param.get('kcat') is not None else 0,
                1 if param.get('ki') is not None else 0
            ])
            if param_count >= 2:
                completeness_bonus = 0.15  # 15% bonus for having 2+ parameters
            if param_count == 3:
                completeness_bonus = 0.25  # 25% bonus for having all 3 parameters
            
            quality_score = min(1.0, quality_score + completeness_bonus)
            
            # Calculate relevance score based on model context
            relevance_score = self._calculate_relevance_score(
                param,
                context_organism,
                context_substrates
            )
            
            # Combined score (weighted: quality 60%, relevance 40%)
            combined_score = (quality_score * 0.6) + (relevance_score * 0.4)
            
            scored_params.append({
                'param': param,
                'quality_score': quality_score,
                'relevance_score': relevance_score,
                'combined_score': combined_score
            })
        
        # Log filtering summary
        if filtered_count > 0:
            self.logger.info(f"[BRENDA_FILTER] Filtered out {filtered_count} parameter sets without Kcat")
            self.logger.info(f"[BRENDA_FILTER] Showing {len(scored_params)} parameter sets with Kcat (usable for rate functions)")
        
        # Update results count label to show filtering info
        total_params = len(results.get('parameters', []))
        usable_params = len(scored_params)
        if filtered_count > 0:
            self.results_count_label.set_markup(
                f"<i>{usable_params} usable results (filtered {filtered_count} without Kcat)</i>"
            )
        else:
            self.results_count_label.set_markup(f"<i>{usable_params} results</i>")
        
        # Sort by combined score (highest first)
        scored_params.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Get transition ID from context (single transition mode)
        context_transition_id = context.get('transition_id', '')
        
        # Populate TreeView with sorted results
        for item in scored_params:
            param = item['param']
            quality_str = f"{int(item['quality_score'] * 100)}%"
            
            # Determine transition ID to display:
            # - For single transition queries: use context transition_id
            # - For batch queries: use param's transition_id
            # - Fallback: use transition_name or 'N/A'
            trans_id_display = context_transition_id or param.get('transition_name', param.get('transition_id', 'N/A'))
            
            # FIX: Ensure param dict has transition_id for self-contained parameter application
            # This makes BRENDA flow work like Heuristic flow (stores ID with params)
            if context_transition_id and 'transition_id' not in param:
                param['transition_id'] = context_transition_id
            elif not param.get('transition_id') and trans_id_display != 'N/A':
                # For batch queries, ensure transition_id is set
                param['transition_id'] = trans_id_display
            
            # Format parameter values with units
            km_str = f"{param['km']:.4f} {param['km_unit']}" if param.get('km') is not None else "—"
            kcat_str = f"{param['kcat']:.2f} {param['kcat_unit']}" if param.get('kcat') is not None else "—"
            ki_str = f"{param['ki']:.4f} {param['ki_unit']}" if param.get('ki') is not None else "—"
            
            # Add row to TreeView
            # Columns: Selected, TransID, EC, Km, Kcat, Ki, Substrate, Organism, Quality, Lit, Object
            self.results_store.append([
                False,  # Not selected by default
                trans_id_display,
                param.get('ec_number', results.get('ec_number', 'N/A')),
                km_str,
                kcat_str,
                ki_str,
                param.get('substrate', 'Unknown'),
                param.get('organism', 'Unknown'),
                quality_str,
                param.get('citation', 'N/A'),
                param  # Store full param object (now includes transition_id and all parameters)
            ])
        
        # Show helpful message about ranking
        if context_organism or context_substrates:
            rank_info = []
            if context_organism:
                rank_info.append(f"organism: {context_organism}")
            if context_substrates:
                rank_info.append(f"substrates: {', '.join(context_substrates[:3])}")
            self.logger.info(f"Results ranked by relevance to model context ({', '.join(rank_info)})")
        
        # Enable apply button
        self.apply_button.set_sensitive(False)  # Require selection first
    
    def _calculate_relevance_score(self, param, model_organism, model_substrates):
        """Calculate how relevant this parameter is to the model context.
        
        Args:
            param: BRENDA parameter dict
            model_organism: Organism from model metadata
            model_substrates: List of substrate names from model
            
        Returns:
            Relevance score 0.0-1.0
        """
        score = 0.0
        factors = 0
        
        # Factor 1: Organism match (most important)
        if model_organism:
            param_organism = param.get('organism', '').lower()
            model_org_lower = model_organism.lower()
            
            if param_organism == model_org_lower:
                score += 1.0  # Perfect match
            elif model_org_lower in param_organism or param_organism in model_org_lower:
                score += 0.7  # Partial match
            elif any(word in param_organism for word in model_org_lower.split()):
                score += 0.5  # Genus/family match
            else:
                score += 0.0  # No match
            factors += 1
        
        # Factor 2: Substrate match
        if model_substrates:
            param_substrate = param.get('substrate', '').lower()
            best_match = 0.0
            
            for model_sub in model_substrates:
                model_sub_lower = model_sub.lower()
                if model_sub_lower in param_substrate or param_substrate in model_sub_lower:
                    best_match = max(best_match, 1.0)  # Full match
                elif any(word in param_substrate for word in model_sub_lower.split() if len(word) > 3):
                    best_match = max(best_match, 0.6)  # Partial word match
            
            score += best_match
            factors += 1
        
        # Factor 3: Has literature reference (indicates reliability)
        if param.get('citation') and param.get('citation') != 'N/A':
            score += 0.5
            factors += 0.5  # Half weight
        
        # Return normalized score
        return score / factors if factors > 0 else 0.5  # Default to 0.5 if no context
    
    def _on_apply_clicked(self, button):
        """Handle apply selected parameters button click."""
        if not self.current_results:
            self._show_status("No results to apply", error=True)
            return
        
        # Get selected parameters from TreeView
        selected = []
        for row in self.results_store:
            if row[0]:  # If selected
                param = row[10]  # Get stored param object
                selected.append(param)
        
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
            
            # CRITICAL: Update controller's canvas reference to ensure it has current model
            # This is essential in case user switched tabs or models since the last query
            self.logger.info(f"[BATCH_APPLY] Updating controller's model canvas reference...")
            self.brenda_controller.set_model_canvas(self.model_canvas_manager)
            
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
                # NEW: Each param now contains km, kcat, ki in the same object
                params_dict = {'_override_rate_function': True}
                
                for param in params:
                    # Extract all available parameters from the grouped object
                    if param.get('km') is not None:
                        params_dict['km'] = param['km']
                        self.logger.info(f"[BATCH_APPLY]   Km = {param['km']} {param.get('km_unit', 'mM')}")
                    
                    if param.get('kcat') is not None:
                        params_dict['kcat'] = param['kcat']
                        self.logger.info(f"[BATCH_APPLY]   Kcat = {param['kcat']} {param.get('kcat_unit', 's⁻¹')}")
                    
                    if param.get('ki') is not None:
                        params_dict['ki'] = param['ki']
                        self.logger.info(f"[BATCH_APPLY]   Ki = {param['ki']} {param.get('ki_unit', 'mM')}")
                
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
            
            # Mark model as dirty (modified) so changes are saved
            if applied_count > 0:
                if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'mark_dirty'):
                    self.model_canvas_manager.mark_dirty()
                    self.logger.info(f"[BATCH_APPLY] ✓ Marked model as dirty")
            
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
            
            # Clear enrichment transition selection (user finished applying parameters)
            self._clear_enrichment_highlight()
            
        except Exception as e:
            self.logger.error(f"[BATCH_APPLY] Error: {e}", exc_info=True)
            self._show_status(f"Batch apply failed: {str(e)}", error=True)
    
    def _show_apply_dialog(self, selected_params: List[Dict[str, Any]]):
        """Show dialog to choose target transition and apply parameters."""
        # Get the enrichment transition (the one user right-clicked to enrich)
        enrichment_transition = getattr(self, '_enrichment_transition', None)
        
        self.logger.info(f"[APPLY_DIALOG] _enrichment_transition: {enrichment_transition}")
        if enrichment_transition:
            self.logger.info(f"[APPLY_DIALOG] _enrichment_transition.id: {enrichment_transition.id}")
        
        # If we have an enrichment transition, apply directly to it
        # BUT: Re-fetch from canvas manager to ensure we have current instance
        if enrichment_transition:
            target_id = enrichment_transition.id
            self.logger.info(f"[APPLY_DIALOG] Enrichment transition detected: {target_id}")
            
            # Re-fetch the transition from canvas manager (ensure fresh instance)
            target_transition = None
            if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'transitions'):
                for trans in self.model_canvas_manager.transitions:
                    if str(trans.id) == str(target_id):
                        target_transition = trans
                        self.logger.info(f"[APPLY_DIALOG] Found matching transition in canvas manager: {trans.id}")
                        break
            
            if target_transition:
                self._apply_single_transition_parameters(target_transition, selected_params)
            else:
                self.logger.error(f"[APPLY_DIALOG] Could not find transition {target_id} in canvas manager!")
                self._show_status(f"Transition {target_id} not found on canvas", error=True)
            return
        
        # Otherwise, show dialog to select target (fallback for manual queries)
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
        
        # Get available transitions from canvas
        target_combo = Gtk.ComboBoxText()
        if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'transitions'):
            for trans in self.model_canvas_manager.transitions:
                label = f"{trans.id}"
                if trans.label:
                    label += f" - {trans.label}"
                target_combo.append(trans.id, label)
        
        if target_combo.get_model().iter_n_children(None) > 0:
            target_combo.set_active(0)
        else:
            # No transitions available
            dialog.destroy()
            self._show_status("No transitions available on canvas", error=True)
            return
        
        target_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        target_label = Gtk.Label(label="Target Transition:")
        target_box.pack_start(target_label, False, False, 0)
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
            # Find selected transition object
            target_id = target_combo.get_active_id()
            target_transition = None
            if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'transitions'):
                for trans in self.model_canvas_manager.transitions:
                    if trans.id == target_id:
                        target_transition = trans
                        break
            
            if target_transition:
                self._apply_single_transition_parameters(target_transition, selected_params)
            else:
                self._show_status(f"Transition {target_id} not found", error=True)
            
            # Clear enrichment transition selection (user finished applying parameters)
            self._clear_enrichment_highlight()
        
        dialog.destroy()
    
    def _apply_single_transition_parameters(self, transition, params: List[Dict[str, Any]]):
        """Apply selected BRENDA parameters to a single transition.
        
        Args:
            transition: Transition object (may be stale reference)
            params: List of parameter dicts to apply
        """
        if not self.brenda_controller:
            self._show_status("BRENDA controller not available", error=True)
            return
        
        # CRITICAL: Re-fetch transition from canvas manager to ensure we have current object
        # The passed transition might be a stale reference from before a file reload
        self.logger.info(f"[SINGLE_APPLY] Looking for transition with id: {transition.id} (type: {type(transition.id)})")
        
        fresh_transition = None
        if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'transitions'):
            self.logger.info(f"[SINGLE_APPLY] Canvas manager has {len(self.model_canvas_manager.transitions)} transitions")
            
            # Debug: Show first few transition IDs
            for i, t in enumerate(self.model_canvas_manager.transitions[:5]):
                self.logger.info(f"[SINGLE_APPLY]   Transition {i}: id={t.id} (type: {type(t.id)})")
            
            # Try to find the transition
            for t in self.model_canvas_manager.transitions:
                # Compare both as strings to handle int vs string mismatch
                if str(t.id) == str(transition.id):
                    fresh_transition = t
                    self.logger.info(f"[SINGLE_APPLY] Found matching transition: {t.id}")
                    break
        
        if not fresh_transition:
            self.logger.error(f"[SINGLE_APPLY] Could not find transition {transition.id} in canvas manager")
            self.logger.error(f"[SINGLE_APPLY] Available transition IDs: {[t.id for t in self.model_canvas_manager.transitions] if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'transitions') else 'N/A'}")
            self._show_status(f"Transition {transition.id} not found", error=True)
            return
        
        # Use fresh transition from now on
        transition = fresh_transition
        
        # Get override settings
        override_kegg = self.override_kegg_checkbox.get_active()
        override_sbml = self.override_sbml_checkbox.get_active()
        
        self.logger.info(f"[SINGLE_APPLY] Applying {len(params)} parameters to transition {transition.id}")
        self.logger.info(f"[SINGLE_APPLY] Override KEGG: {override_kegg}, Override SBML: {override_sbml}")
        
        try:
            # Check if we should apply based on data source
            data_source = transition.metadata.get('data_source', 'unknown') if hasattr(transition, 'metadata') and transition.metadata else 'unknown'
            has_kinetics = transition.metadata.get('has_kinetics', False) if hasattr(transition, 'metadata') and transition.metadata else False
            
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
                self.logger.info(f"[SINGLE_APPLY] Skipping transition {transition.id} (data_source={data_source}, has_kinetics={has_kinetics}, override_kegg={override_kegg}, override_sbml={override_sbml})")
                self._show_status(f"Skipped {transition.id} - enable override to replace existing kinetics", error=True)
                return
            
            # CRITICAL: Update controller's canvas reference to ensure it has current model
            # This is essential in case user switched tabs or models since the last query
            self.logger.info(f"[SINGLE_APPLY] Updating controller's model canvas reference...")
            self.brenda_controller.set_model_canvas(self.model_canvas_manager)
            
            # Start enrichment session
            self.brenda_controller.start_enrichment(
                source="brenda_api",
                query_params={'single_mode': True, 'override_kegg': override_kegg, 'override_sbml': override_sbml}
            )
            
            # Build parameters dict from all selected params
            params_dict = {'_override_rate_function': True}
            self.logger.info(f"[SINGLE_APPLY] Building params_dict from {len(params)} parameters")
            
            for param in params:
                param_type = param.get('type', 'Km').lower()
                param_value = param.get('value')
                
                # Convert value to float if it's a string
                if param_value is not None:
                    if isinstance(param_value, str):
                        try:
                            param_value = float(param_value)
                        except (ValueError, TypeError):
                            self.logger.warning(f"[SINGLE_APPLY] Could not convert value '{param_value}' to float")
                            continue
                    
                    params_dict[param_type] = param_value
                    self.logger.info(f"[SINGLE_APPLY]   {param_type} = {param_value} ({type(param_value).__name__})")
            
            self.logger.info(f"[SINGLE_APPLY] Final params_dict: {params_dict}")
            
            # Apply parameters to transition
            self.logger.info(f"[SINGLE_APPLY] Applying to transition {transition.id}")
            self.brenda_controller.apply_enrichment_to_transition(
                transition.id,
                params_dict,
                transition_obj=transition
            )
            
            # VERIFICATION: Check if rate_function was actually set
            # IMPORTANT: Re-fetch the transition from canvas manager to ensure we check the updated object
            self.logger.info(f"[SINGLE_APPLY] ========== VERIFICATION ==========")
            self.logger.info(f"[SINGLE_APPLY] Re-fetching transition {transition.id} from canvas manager...")
            
            # Get fresh transition object from canvas manager
            verified_transition = None
            if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'transitions'):
                for t in self.model_canvas_manager.transitions:
                    if str(t.id) == str(transition.id):
                        verified_transition = t
                        break
            
            if not verified_transition:
                self.logger.warning(f"[SINGLE_APPLY] Could not re-fetch transition {transition.id} for verification")
                verified_transition = transition  # Fallback to original
            
            self.logger.info(f"[SINGLE_APPLY] Checking transition {verified_transition.id} after apply...")
            self.logger.info(f"[SINGLE_APPLY]   transition object: {verified_transition}")
            self.logger.info(f"[SINGLE_APPLY]   hasattr(properties): {hasattr(verified_transition, 'properties')}")
            
            if hasattr(verified_transition, 'properties'):
                self.logger.info(f"[SINGLE_APPLY]   transition.properties: {verified_transition.properties}")
                
                if verified_transition.properties:
                    rate_func = verified_transition.properties.get('rate_function')
                    rate_source = verified_transition.properties.get('rate_function_source')
                    self.logger.info(f"[SINGLE_APPLY]   rate_function: {rate_func}")
                    self.logger.info(f"[SINGLE_APPLY]   rate_function_source: {rate_source}")
                    
                    if rate_func:
                        self.logger.info(f"[SINGLE_APPLY] ✓ Rate function successfully applied!")
                    else:
                        self.logger.warning(f"[SINGLE_APPLY] ✗ Rate function is None or empty!")
                else:
                    self.logger.warning(f"[SINGLE_APPLY] ✗ properties exists but is empty/None!")
            else:
                self.logger.warning(f"[SINGLE_APPLY] ✗ Transition has no properties attribute!")
            
            trans_type = getattr(verified_transition, 'transition_type', 'unknown')
            self.logger.info(f"[SINGLE_APPLY]   transition_type: {trans_type}")
            
            if hasattr(verified_transition, 'metadata') and verified_transition.metadata:
                km_value = verified_transition.metadata.get('km')
                vmax_value = verified_transition.metadata.get('vmax')
                self.logger.info(f"[SINGLE_APPLY]   metadata.km: {km_value}")
                self.logger.info(f"[SINGLE_APPLY]   metadata.vmax: {vmax_value}")
            
            self.logger.info(f"[SINGLE_APPLY] =====================================")
            
            # Finish enrichment session
            self.brenda_controller.finish_enrichment()
            
            # Mark model as dirty (modified) so changes are saved
            if self.model_canvas_manager and hasattr(self.model_canvas_manager, 'mark_dirty'):
                self.model_canvas_manager.mark_dirty()
                self.logger.info(f"[SINGLE_APPLY] ✓ Marked model as dirty")
            
            # CRITICAL: Reset simulation state after applying parameters
            self._reset_simulation_after_parameter_changes()
            
            # Show success message
            self._show_status(f"Applied {len(params)} parameters to {transition.id}", error=False)
            
            # Trigger canvas redraw
            if self.model_canvas and hasattr(self.model_canvas, 'queue_draw'):
                GLib.idle_add(self.model_canvas.queue_draw)
            
            # Clear enrichment transition selection (user finished applying parameters)
            self._clear_enrichment_highlight()
            
        except Exception as e:
            self.logger.error(f"[SINGLE_APPLY] Error: {e}", exc_info=True)
            self._show_status(f"Apply failed: {str(e)}", error=True)
    
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
                                   enzyme_name: str = "", transition_id: str = "",
                                   organism: str = "", substrates: list = None,
                                   products: list = None):
        """Pre-fill BRENDA query fields from transition data.
        
        Called when user selects "Enrich with BRENDA" from transition context menu.
        Automatically populates query fields with available transition metadata.
        
        Args:
            ec_number: EC number from transition metadata
            reaction_name: Reaction name from transition label/metadata (could be KEGG ID)
            enzyme_name: Enzyme name from transition metadata
            transition_id: Transition ID for reference
            organism: Model organism (e.g., "Homo sapiens", "Saccharomyces cerevisiae")
            substrates: List of substrate names connected to this transition
            products: List of product names connected to this transition
        """
        import re
        
        # Clear previous enrichment highlight if user selects a different transition
        self._clear_enrichment_highlight()
        
        # Store context for smart filtering later
        self._transition_context = {
            'organism': organism,
            'substrates': substrates or [],
            'products': products or [],
            'transition_id': transition_id
        }
        
        # Update the selected transition label in the results header
        if hasattr(self, 'selected_trans_label'):
            trans_display = f"<b>Target:</b> <i>{transition_id or 'None'}</i>"
            if enzyme_name:
                trans_display += f" <span size='small'>({enzyme_name})</span>"
            elif reaction_name and not re.match(r'^R\d{5}$', reaction_name):
                trans_display += f" <span size='small'>({reaction_name})</span>"
            self.selected_trans_label.set_markup(trans_display)
        
        # Clear all query fields first (remove previous transition data)
        if hasattr(self, 'ec_entry'):
            self.ec_entry.set_text("")
        if hasattr(self, 'reaction_name_entry'):
            self.reaction_name_entry.set_text("")
        if hasattr(self, 'organism_entry'):
            self.organism_entry.set_text("")
        
        # Clear previous results
        self.results_store.clear()
        self.current_results = None
        self.selected_params = {}
        
        # Check if reaction_name is a KEGG reaction ID (e.g., R00754)
        # If so, put it in EC field for automatic conversion
        kegg_reaction_name = None
        if reaction_name and re.match(r'^R\d{5}$', reaction_name) and not ec_number:
            ec_number = reaction_name
            self.logger.info(f"Detected KEGG reaction ID in reaction_name: {reaction_name}")
            
            # Try to fetch the reaction name from KEGG API
            if self.kegg_ec_fetcher:
                try:
                    kegg_reaction_name = self.kegg_ec_fetcher.fetch_reaction_name(reaction_name)
                    if kegg_reaction_name:
                        self.logger.info(f"Fetched KEGG reaction name: {kegg_reaction_name}")
                except Exception as e:
                    self.logger.warning(f"Could not fetch KEGG reaction name for {reaction_name}: {e}")
        
        # Pre-fill EC number if available (including KEGG reaction IDs)
        if ec_number and hasattr(self, 'ec_entry'):
            self.ec_entry.set_text(ec_number)
            # Select EC number radio button
            if hasattr(self, 'ec_radio'):
                self.ec_radio.set_active(True)
        
        # Pre-fill organism if available (helps filter BRENDA results)
        if organism and hasattr(self, 'organism_entry'):
            self.organism_entry.set_text(organism)
            self.logger.info(f"Pre-filled organism: {organism}")
        
        # Pre-fill reaction name (prioritize enzyme name if available)
        # Skip if reaction_name was a KEGG ID (already in EC field)
        if hasattr(self, 'reaction_name_entry'):
            if enzyme_name:
                self.reaction_name_entry.set_text(enzyme_name)
                # Select name radio button if no EC number
                if not ec_number and hasattr(self, 'name_radio'):
                    self.name_radio.set_active(True)
            elif kegg_reaction_name:
                # Use fetched KEGG reaction name
                self.reaction_name_entry.set_text(kegg_reaction_name)
            elif reaction_name and not re.match(r'^R\d{5}$', reaction_name):
                # Only set reaction_name if it's not a KEGG ID
                self.reaction_name_entry.set_text(reaction_name)
                # Select name radio button if no EC number
                if not ec_number and hasattr(self, 'name_radio'):
                    self.name_radio.set_active(True)
        
        # Show helpful status message
        if ec_number or enzyme_name or reaction_name:
            info_parts = []
            if ec_number:
                info_parts.append(f"EC: {ec_number}")
            if enzyme_name:
                info_parts.append(f"Enzyme: {enzyme_name}")
            elif reaction_name:
                info_parts.append(f"Reaction: {reaction_name}")
            if organism:
                info_parts.append(f"Organism: {organism}")
            
            status_msg = f"Query pre-filled from transition {transition_id} ({', '.join(info_parts)}). "
            if organism or substrates or products:
                status_msg += "Results will be ranked by relevance. "
            status_msg += "Verify and click Search."
            
            self._show_status(status_msg, error=False)
            
            self.logger.info(f"Pre-filled BRENDA query from transition {transition_id}: "
                           f"EC={ec_number}, Enzyme={enzyme_name}, Reaction={reaction_name}, "
                           f"Organism={organism}, Substrates={substrates}, Products={products}")
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
            if not self.model_canvas_loader:
                self.logger.warning("No canvas loader available for simulation reset")
                return
            
            drawing_area = self.model_canvas_loader.get_current_document()
            if not drawing_area:
                self.logger.warning("No active document for simulation reset")
                return
            
            # Find simulation controller for this drawing area
            if hasattr(self.model_canvas_loader, 'simulation_controllers'):
                if drawing_area in self.model_canvas_loader.simulation_controllers:
                    controller = self.model_canvas_loader.simulation_controllers[drawing_area]
                    
                    # Get the canvas manager
                    canvas_manager = self.model_canvas_loader.canvas_managers.get(drawing_area)
                    
                    if canvas_manager:
                        # CRITICAL: Use reset_for_new_model() instead of reset()
                        # This recreates the model adapter and clears ALL caches
                        # After applying parameters, the transition objects have changed
                        # and we need to rebuild the entire simulation state
                        controller.reset_for_new_model(canvas_manager)
                        
                        self.logger.info("Simulation fully reset after BRENDA parameter changes (model adapter recreated)")
                    else:
                        # Fallback to basic reset if we can't get canvas_manager
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
    
    def _clear_enrichment_highlight(self):
        """Clear the transition selection highlight after parameters are applied.
        
        This is called when the user finishes applying BRENDA parameters to a transition.
        It deselects the transition that was being enriched and triggers a canvas redraw.
        """
        if hasattr(self, '_enrichment_transition') and self._enrichment_transition:
            try:
                # Deselect the transition
                self._enrichment_transition.selected = False
                self._enrichment_transition = None
                
                # Reset the transition label to show no active enrichment
                if hasattr(self, 'selected_trans_label'):
                    self.selected_trans_label.set_markup("<b>Target:</b> <i>None</i>")
                
                # Trigger canvas redraw to remove selection highlight
                if hasattr(self, 'model_canvas_loader') and self.model_canvas_loader:
                    if hasattr(self.model_canvas_loader, 'canvas_managers'):
                        for drawing_area, manager in self.model_canvas_loader.canvas_managers.items():
                            drawing_area.queue_draw()
                            break
                        
                self.logger.debug("Cleared enrichment transition highlight")
                
            except Exception as e:
                self.logger.warning(f"Error clearing enrichment highlight: {e}")

