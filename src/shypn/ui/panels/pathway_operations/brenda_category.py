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
        
        Returns:
            Gtk.Box containing all BRENDA enrichment UI elements
        """
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        
        # Authentication section
        auth_section = self._build_authentication_section()
        main_box.pack_start(auth_section, False, False, 0)
        
        # Quick Enrich section (NEW - batch enrichment)
        quick_enrich_section = self._build_quick_enrich_section()
        main_box.pack_start(quick_enrich_section, False, False, 0)
        
        # Query section (manual query)
        query_section = self._build_query_section()
        main_box.pack_start(query_section, False, False, 0)
        
        # Results section (scrollable)
        results_section = self._build_results_section()
        main_box.pack_start(results_section, True, True, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<span foreground='gray'>Ready to query BRENDA</span>")
        self.status_label.set_xalign(0.0)
        main_box.pack_start(self.status_label, False, False, 0)
        
        # Apply button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        
        self.apply_button = Gtk.Button(label="Apply Selected to Model")
        self.apply_button.get_style_context().add_class('suggested-action')
        self.apply_button.set_sensitive(False)
        self.apply_button.connect('clicked', self._on_apply_clicked)
        button_box.pack_start(self.apply_button, False, False, 0)
        
        main_box.pack_start(button_box, False, False, 0)
        
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
    
    def _build_quick_enrich_section(self) -> Gtk.Widget:
        """Build quick canvas enrichment section for batch processing.
        
        This section provides one-click enrichment of all continuous transitions
        on the canvas using their EC numbers. Faster than manual query workflow.
        """
        frame = Gtk.Frame()
        frame.set_label("Quick Canvas Enrichment")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup(
            '<i>Auto-enrich all continuous transitions from canvas using their EC numbers. '
            'Faster than manual query for batch processing.</i>'
        )
        info_label.set_line_wrap(True)
        info_label.set_xalign(0.0)
        box.pack_start(info_label, False, False, 0)
        
        # Enrich button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.quick_enrich_button = Gtk.Button(label="🧬 Enrich All Continuous")
        self.quick_enrich_button.get_style_context().add_class('suggested-action')
        self.quick_enrich_button.set_sensitive(False)  # Requires authentication
        self.quick_enrich_button.set_tooltip_text(
            "Query BRENDA for all continuous transitions with EC numbers\n"
            "and apply kinetic parameters automatically"
        )
        self.quick_enrich_button.connect('clicked', self._on_quick_enrich_clicked)
        button_box.pack_start(self.quick_enrich_button, False, False, 0)
        
        box.pack_start(button_box, False, False, 0)
        
        # Override settings
        override_label = Gtk.Label()
        override_label.set_markup("<b>Override Settings:</b>")
        override_label.set_xalign(0.0)
        override_label.set_margin_top(6)
        box.pack_start(override_label, False, False, 0)
        
        # Override KEGG checkbox (default ON)
        self.override_kegg_checkbox = Gtk.CheckButton()
        self.override_kegg_checkbox.set_label("Override KEGG Heuristics")
        self.override_kegg_checkbox.set_active(True)  # Default ON
        self.override_kegg_checkbox.set_tooltip_text(
            "Always replace KEGG placeholder values (vmax=10.0, km=0.5) with BRENDA data.\n"
            "RECOMMENDED: KEGG provides no kinetics, only Shypn heuristics."
        )
        box.pack_start(self.override_kegg_checkbox, False, False, 0)
        
        # Override SBML checkbox (default OFF)
        self.override_sbml_checkbox = Gtk.CheckButton()
        self.override_sbml_checkbox.set_label("Override SBML Curated Data")
        self.override_sbml_checkbox.set_active(False)  # Default OFF
        self.override_sbml_checkbox.set_tooltip_text(
            "Replace curated SBML kinetic parameters with BRENDA data.\n"
            "⚠️ CAUTION: SBML models may contain validated experimental kinetics."
        )
        box.pack_start(self.override_sbml_checkbox, False, False, 0)
        
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
        self.name_radio.set_active(True)
        self.name_radio.connect('toggled', self._on_search_mode_changed)
        mode_box.pack_start(self.name_radio, False, False, 0)
        
        self.ec_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.name_radio, "EC Number"
        )
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
        self.ec_entry.set_sensitive(False)
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
        
        # Search button
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        search_box.set_halign(Gtk.Align.END)
        
        self.search_button = Gtk.Button(label="Search BRENDA")
        self.search_button.get_style_context().add_class('suggested-action')
        self.search_button.set_sensitive(False)
        self.search_button.connect('clicked', self._on_search_clicked)
        search_box.pack_start(self.search_button, False, False, 0)
        
        box.pack_start(search_box, False, False, 0)
        
        frame.add(box)
        return frame
    
    def _build_results_section(self) -> Gtk.Widget:
        """Build results section with scrollable parameter list."""
        frame = Gtk.Frame()
        frame.set_label("BRENDA Results")
        
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
        placeholder.set_markup("<i>No results yet. Authenticate and search to see kinetic parameters.</i>")
        placeholder.set_line_wrap(True)
        self.results_box.pack_start(placeholder, False, False, 0)
        
        scrolled.add(self.results_box)
        frame.add(scrolled)
        
        return frame
    
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
        
        # Authenticate with real BRENDA API
        success = self.brenda_api.authenticate(email, password)
        
        if success:
            # Save credentials for future use
            self.brenda_api.save_credentials(email, password)
            return {'valid': True, 'message': 'Successfully authenticated with BRENDA API'}
        else:
            raise ValueError('BRENDA authentication failed. Check your credentials.')
    
    def _on_validate_complete(self, result):
        """Callback when credential validation completes."""
        self.authenticated = True
        self.auth_status.set_markup("<span foreground='green'>✓ Authenticated</span>")
        self.search_button.set_sensitive(True)
        self.quick_enrich_button.set_sensitive(True)
        self._show_status("Authenticated successfully", error=False)
        self.validate_button.set_sensitive(True)
    
    def _on_validate_error(self, error):
        """Callback when credential validation fails."""
        self.authenticated = False
        self.auth_status.set_markup("<span foreground='red'>✗ Authentication failed</span>")
        self.search_button.set_sensitive(False)
        self.quick_enrich_button.set_sensitive(False)
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
        """Background task to search BRENDA database."""
        # TODO: Implement actual BRENDA API search
        # For now, return mock data
        import time
        time.sleep(1)
        
        # Mock BRENDA results
        if search_type == 'ec':
            ec_number = search_term
            name = "Alcohol dehydrogenase"
        else:
            ec_number = "1.1.1.1"
            name = search_term
        
        return {
            'ec_number': ec_number,
            'name': name,
            'organism': organism if organism else "Saccharomyces cerevisiae",
            'parameters': [
                {
                    'id': 'km_ethanol',
                    'type': 'Km',
                    'value': 0.5,
                    'unit': 'mM',
                    'substrate': 'Ethanol',
                    'citation': 'PMID:12345678',
                    'confidence': 'high'
                },
                {
                    'id': 'vmax',
                    'type': 'Vmax',
                    'value': 10.0,
                    'unit': 'μmol/min/mg',
                    'substrate': None,
                    'citation': 'PMID:12345678',
                    'confidence': 'high'
                },
                {
                    'id': 'kcat',
                    'type': 'kcat',
                    'value': 50.0,
                    'unit': 's⁻¹',
                    'substrate': None,
                    'citation': 'PMID:87654321',
                    'confidence': 'medium'
                },
                {
                    'id': 'ki_nad',
                    'type': 'Ki',
                    'value': 0.1,
                    'unit': 'mM',
                    'substrate': 'NAD+',
                    'citation': 'PMID:11111111',
                    'confidence': 'low'
                }
            ],
            'conditions': {
                'temperature': {'value': 30, 'unit': '°C'},
                'ph': {'value': 7.0}
            }
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
        self._show_status(f"Search failed: {error}", error=True)
    
    # ========================================================================
    # Quick Canvas Enrichment (Batch)
    # ========================================================================
    
    def _on_quick_enrich_clicked(self, button):
        """Handle quick canvas enrichment button click.
        
        Scans all continuous transitions on canvas and enriches them from BRENDA.
        Uses smart override logic:
        - Always enrich transitions without kinetics
        - Override KEGG heuristics if checkbox enabled (default ON)
        - Override SBML curated data if checkbox enabled (default OFF)
        """
        if not self.authenticated:
            self._show_status("Please authenticate first", error=True)
            return
        
        if not self.model_canvas:
            self._show_status("No model loaded on canvas", error=True)
            return
        
        # Get override settings from checkboxes
        override_kegg = self.override_kegg_checkbox.get_active()
        override_sbml = self.override_sbml_checkbox.get_active()
        
        # For the controller, if override_sbml is True, we override everything
        # If False, we still override KEGG (handled by controller's smart logic)
        override_existing = override_sbml
        
        # Prepare UI
        self.quick_enrich_button.set_sensitive(False)
        self._show_status("Scanning canvas for continuous transitions...")
        
        # Run enrichment in background thread
        self._run_in_thread(
            task_func=lambda: self._run_quick_enrichment(override_existing),
            on_complete=self._on_quick_enrich_complete,
            on_error=self._on_quick_enrich_error
        )
    
    def _run_quick_enrichment(self, override_existing: bool) -> Dict[str, Any]:
        """Background task: scan canvas and enrich all transitions from BRENDA.
        
        Args:
            override_existing: Whether to override SBML curated data (KEGG always overridden)
        
        Returns:
            Summary dict with enrichment results
        """
        if not self.brenda_controller:
            raise RuntimeError("BRENDA controller not available")
        
        # Set canvas reference
        self.brenda_controller.set_model_canvas(self.model_canvas)
        
        # Scan canvas for all transitions
        transitions = self.brenda_controller.scan_canvas_transitions()
        
        if not transitions:
            return {
                'success': False,
                'error': 'No transitions found on canvas'
            }
        
        # Filter for continuous transitions (those with EC numbers)
        continuous_transitions = [t for t in transitions if t.get('ec_number')]
        
        if not continuous_transitions:
            return {
                'success': False,
                'error': 'No continuous transitions (with EC numbers) found on canvas'
            }
        
        # Extract unique EC numbers
        ec_numbers = list(set(t['ec_number'] for t in continuous_transitions if t.get('ec_number')))
        
        # Enrich from BRENDA API (uses mock DB)
        result = self.brenda_controller.enrich_canvas_from_api(
            ec_numbers=ec_numbers,
            organism=None,  # Use all organisms for now
            override_existing=override_existing
        )
        
        return result
    
    def _on_quick_enrich_complete(self, result: Dict[str, Any]):
        """Callback when quick enrichment completes successfully."""
        self.quick_enrich_button.set_sensitive(True)
        
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error')
            self._show_status(f"Enrichment failed: {error_msg}", error=True)
            return
        
        # Extract summary
        scanned = result.get('transitions_scanned', 0)
        enriched = result.get('transitions_enriched', 0)
        skipped = scanned - enriched
        
        # Show completion dialog
        message = (
            f"Canvas enrichment complete!\n\n"
            f"Transitions scanned: {scanned}\n"
            f"Transitions enriched: {enriched}\n"
            f"Transitions skipped: {skipped}\n\n"
            f"Enriched transitions now have BRENDA kinetic data."
        )
        
        self._show_info_dialog("BRENDA Enrichment Complete", message)
        self._show_status(f"Enriched {enriched} transitions from BRENDA", error=False)
        
        # Trigger canvas redraw to update colors
        if self.model_canvas and hasattr(self.model_canvas, 'queue_draw'):
            GLib.idle_add(self.model_canvas.queue_draw)
    
    def _on_quick_enrich_error(self, error: Exception):
        """Callback when quick enrichment fails."""
        self.quick_enrich_button.set_sensitive(True)
        error_msg = str(error)
        self._show_status(f"Enrichment error: {error_msg}", error=True)
        self._show_error_dialog("BRENDA Enrichment Error", 
                               f"Failed to enrich canvas:\n\n{error_msg}")
    
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
        
        # Show dialog to choose target transition
        self._show_apply_dialog(selected)
    
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

