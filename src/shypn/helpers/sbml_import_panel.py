#!/usr/bin/env python3
"""SBML Import Panel Controller.

This module provides the controller for the SBML Import tab within the Pathway panel.
It handles:
  - File selection via FileChooser
  - Parsing SBML files
  - Validating pathway data
  - Post-processing (layout, colors, units)
  - Converting to Petri net (DocumentModel)
  - Loading into canvas

This follows the MVC pattern:
  - Model: SBMLParser + PathwayValidator + PathwayPostProcessor + PathwayConverter (business logic)
  - View: pathway_panel.ui SBML tab (GTK XML)
  - Controller: SBMLImportPanel (this file)
"""
import os
import sys
import logging
from typing import Optional

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f'ERROR: GTK3 not available in sbml_import_panel: {e}', file=sys.stderr)
    sys.exit(1)

# Import SBML backend modules
try:
    from shypn.data.pathway.sbml_parser import SBMLParser
    from shypn.data.pathway.pathway_validator import PathwayValidator
    from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
    from shypn.data.pathway.pathway_converter import PathwayConverter
except ImportError as e:
    print(f'Warning: SBML importer not available: {e}', file=sys.stderr)
    SBMLParser = None
    PathwayValidator = None
    PathwayPostProcessor = None
    PathwayConverter = None


class SBMLImportPanel:
    """Controller for SBML import functionality.
    
    Connects SBML import pipeline (model) to GTK UI (view).
    Does NOT create widgets - only gets references and connects signals.
    
    Attributes:
        builder: GTK Builder instance (UI references)
        model_canvas: ModelCanvasManager for loading imported pathways
        parser: SBMLParser for parsing SBML files
        validator: PathwayValidator for validating pathway data
        postprocessor: PathwayPostProcessor for layout and colors
        converter: PathwayConverter for converting to Petri net
        current_filepath: Currently selected SBML file path
        parsed_pathway: Parsed PathwayData from SBML file
        processed_pathway: Post-processed PathwayData with layout and colors
    """
    
    def __init__(self, builder: Gtk.Builder, model_canvas=None, workspace_settings=None):
        """Initialize the SBML import panel controller.
        
        Args:
            builder: GTK Builder with loaded pathway_panel.ui
            model_canvas: Optional ModelCanvasManager for loading pathways
            workspace_settings: Optional WorkspaceSettings for remembering last query
        """
        self.builder = builder
        self.model_canvas = model_canvas
        self.workspace_settings = workspace_settings
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize backend components
        if SBMLParser and PathwayValidator and PathwayPostProcessor and PathwayConverter:
            self.parser = SBMLParser()
            self.validator = PathwayValidator()
            self.postprocessor = None  # Created when needed with user options
            self.converter = PathwayConverter()
        else:
            self.parser = None
            self.validator = None
            self.postprocessor = None
            self.converter = None
            print("Warning: SBML import backend not available", file=sys.stderr)
        
        # Current state
        self.current_filepath = None
        self.parsed_pathway = None
        self.processed_pathway = None
        
        # Get widget references
        self._get_widgets()
        
        # Connect signals
        self._connect_signals()
        
        # Load last BioModels query from settings
        self._load_last_biomodels_query()
    
    def _get_widgets(self):
        """Get references to UI widgets from builder."""
        # Mode selection widgets
        self.sbml_local_radio = self.builder.get_object('sbml_local_radio')
        self.sbml_biomodels_radio = self.builder.get_object('sbml_biomodels_radio')
        
        # Local file widgets
        self.sbml_local_box = self.builder.get_object('sbml_local_box')
        self.sbml_file_entry = self.builder.get_object('sbml_file_entry')
        self.sbml_browse_button = self.builder.get_object('sbml_browse_button')
        
        # BioModels widgets
        self.sbml_biomodels_box = self.builder.get_object('sbml_biomodels_box')
        self.sbml_biomodels_entry = self.builder.get_object('sbml_biomodels_entry')
        self.sbml_fetch_button = self.builder.get_object('sbml_fetch_button')
        
        # Info label
        self.sbml_source_info = self.builder.get_object('sbml_source_info')
        
        # Layout algorithm selection
        self.sbml_layout_algorithm_combo = self.builder.get_object('sbml_layout_algorithm_combo')
        
        # Layout parameter boxes (for showing/hiding based on algorithm)
        self.sbml_auto_params_box = self.builder.get_object('sbml_auto_params_box')
        self.sbml_hierarchical_params_box = self.builder.get_object('sbml_hierarchical_params_box')
        self.sbml_force_params_box = self.builder.get_object('sbml_force_params_box')
        
        # Hierarchical layout parameters
        self.sbml_layer_spacing_spin = self.builder.get_object('sbml_layer_spacing_spin')
        self.sbml_node_spacing_spin = self.builder.get_object('sbml_node_spacing_spin')
        
        # Force-directed layout parameters
        self.sbml_iterations_spin = self.builder.get_object('sbml_iterations_spin')
        self.sbml_k_factor_spin = self.builder.get_object('sbml_k_factor_spin')
        self.sbml_canvas_scale_spin = self.builder.get_object('sbml_canvas_scale_spin')
        
        # Legacy/optional widgets (may not exist in UI, handle gracefully)
        self.sbml_spacing_spin = None  # Legacy widget removed from UI
        self.sbml_scale_spin = self.builder.get_object('sbml_scale_spin')
        self.sbml_scale_example = self.builder.get_object('sbml_scale_example')
        self.sbml_enrich_check = self.builder.get_object('sbml_enrich_check')  # Exists but disabled
        
        # Preview and status
        self.sbml_preview_text = self.builder.get_object('sbml_preview_text')
        self.sbml_status_label = self.builder.get_object('sbml_status_label')
        
        # Action buttons
        self.sbml_parse_button = self.builder.get_object('sbml_parse_button')
        # Note: sbml_import_button removed in v2.0 - Parse now auto-loads to canvas
    
    def _connect_signals(self):
        """Connect widget signals to handlers."""
        # Mode selection
        if self.sbml_local_radio:
            self.sbml_local_radio.connect('toggled', self._on_mode_changed)
        
        if self.sbml_biomodels_radio:
            self.sbml_biomodels_radio.connect('toggled', self._on_mode_changed)
        
        # Local file mode
        if self.sbml_browse_button:
            self.sbml_browse_button.connect('clicked', self._on_browse_clicked)
        
        if self.sbml_file_entry:
            self.sbml_file_entry.connect('changed', self._on_file_entry_changed)
        
        # BioModels mode
        if self.sbml_biomodels_entry:
            self.sbml_biomodels_entry.connect('changed', self._on_biomodels_entry_changed)
        
        if self.sbml_fetch_button:
            self.sbml_fetch_button.connect('clicked', self._on_fetch_clicked)
        
        # Parse and import
        if self.sbml_parse_button:
            self.sbml_parse_button.connect('clicked', self._on_parse_clicked)
        
        # NOTE: Import button removed in v2.0 - Parse now auto-loads to canvas
        # if self.sbml_import_button:
        #     self.sbml_import_button.connect('clicked', self._on_import_clicked)
        
        # Scale changes
        if self.sbml_scale_spin:
            self.sbml_scale_spin.connect('value-changed', self._on_scale_changed)
        
        # Layout algorithm selection
        if self.sbml_layout_algorithm_combo:
            self.sbml_layout_algorithm_combo.connect('changed', self._on_layout_algorithm_changed)
        
        # Enable parse button when user types in entry
        if self.sbml_file_entry:
            self.sbml_file_entry.connect('changed', self._on_file_entry_changed)
    
    def _load_last_biomodels_query(self):
        """Load the last BioModels query from workspace settings."""
        if not self.workspace_settings or not self.sbml_biomodels_entry:
            return
        
        try:
            last_query = self.workspace_settings.get_setting("sbml_import.last_biomodels_id", "")
            if last_query:
                self.sbml_biomodels_entry.set_text(last_query)
                self.logger.debug(f"Loaded last BioModels query: {last_query}")
        except Exception as e:
            self.logger.warning(f"Could not load last BioModels query: {e}")
    
    def _save_biomodels_query(self, biomodels_id: str):
        """Save the BioModels query to workspace settings.
        
        Args:
            biomodels_id: BioModels ID to remember
        """
        if not self.workspace_settings:
            return
        
        try:
            self.workspace_settings.set_setting("sbml_import.last_biomodels_id", biomodels_id)
            self.logger.debug(f"Saved BioModels query: {biomodels_id}")
        except Exception as e:
            self.logger.warning(f"Could not save BioModels query: {e}")
    
    def set_model_canvas(self, model_canvas):
        """Set or update the model canvas for loading imported pathways.
        
        Args:
            model_canvas: ModelCanvasManager instance
        """
        self.model_canvas = model_canvas
    
    def _on_mode_changed(self, radio_button):
        """Handle mode radio button changes (Local vs BioModels)."""
        if not radio_button.get_active():
            return  # Only handle the activated button
        
        if self.sbml_local_radio and self.sbml_local_radio.get_active():
            # Switch to local file mode
            if self.sbml_local_box:
                self.sbml_local_box.set_visible(True)
            if self.sbml_biomodels_box:
                self.sbml_biomodels_box.set_visible(False)
            if self.sbml_source_info:
                self.sbml_source_info.set_text("Browse for a local SBML file (.sbml or .xml)")
        else:
            # Switch to BioModels mode
            if self.sbml_local_box:
                self.sbml_local_box.set_visible(False)
            if self.sbml_biomodels_box:
                self.sbml_biomodels_box.set_visible(True)
            if self.sbml_source_info:
                self.sbml_source_info.set_markup(
                    'Enter a <a href="https://www.ebi.ac.uk/biomodels/">BioModels</a> ID '
                    '(e.g., BIOMD0000000001 for glycolysis)'
                )
    
    def _on_file_entry_changed(self, entry):
        """Handle file entry text changes - enable parse if path exists."""
        filepath = entry.get_text().strip()
        if filepath and os.path.exists(filepath):
            if self.sbml_parse_button:
                self.sbml_parse_button.set_sensitive(True)
        else:
            if self.sbml_parse_button:
                self.sbml_parse_button.set_sensitive(False)
    
    def _on_biomodels_entry_changed(self, entry):
        """Handle BioModels ID entry changes - enable fetch button."""
        biomodels_id = entry.get_text().strip()
        if self.sbml_fetch_button:
            self.sbml_fetch_button.set_sensitive(len(biomodels_id) > 0)
    
    def _on_browse_clicked(self, button):
        """Handle browse button click - open file chooser."""
        # Create file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Select SBML File",
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
        )
        
        # Add file filters
        filter_sbml = Gtk.FileFilter()
        filter_sbml.set_name("SBML Files")
        filter_sbml.add_pattern("*.sbml")
        filter_sbml.add_pattern("*.xml")
        dialog.add_filter(filter_sbml)
        
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        
        # Run dialog
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            
            # Update entry
            if self.sbml_file_entry:
                self.sbml_file_entry.set_text(filepath)
            
            # Store filepath
            self.current_filepath = filepath
            
            # Enable parse button
            if self.sbml_parse_button:
                self.sbml_parse_button.set_sensitive(True)
            
            # Clear previous state
            self.parsed_pathway = None
            self.processed_pathway = None
            
            # Clear preview
            if self.sbml_preview_text:
                buffer = self.sbml_preview_text.get_buffer()
                buffer.set_text("")
            
            self._show_status(f"Selected: {os.path.basename(filepath)}")
        
        dialog.destroy()
    
    def _on_fetch_clicked(self, button):
        """Handle fetch button click - download model from BioModels."""
        if not self.sbml_biomodels_entry:
            return
        
        biomodels_id = self.sbml_biomodels_entry.get_text().strip()
        if not biomodels_id:
            self._show_status("Please enter a BioModels ID", error=True)
            return
        
        # Save query to workspace settings
        self._save_biomodels_query(biomodels_id)
        
        # Disable buttons during fetch
        self.sbml_fetch_button.set_sensitive(False)
        self.sbml_parse_button.set_sensitive(False)
        self._show_status(f"Fetching {biomodels_id} from BioModels...")
        
        # Fetch in REAL background thread (not idle_add which blocks UI)
        import threading
        thread = threading.Thread(target=self._fetch_biomodels_background, args=(biomodels_id,), daemon=True)
        thread.start()
    
    def _fetch_biomodels_background(self, biomodels_id: str):
        """Background task to fetch model from BioModels.
        
        Runs in a separate thread to avoid blocking the UI.
        Uses GLib.idle_add() to safely update UI from background thread.
        
        Args:
            biomodels_id: BioModels identifier (e.g., BIOMD0000000001)
        """
        try:
            import urllib.request
            import urllib.error
            import socket
            import tempfile
            
            # Set timeout to prevent hanging indefinitely
            socket.setdefaulttimeout(30)  # 30 seconds timeout
            
            # BioModels REST API URL
            url = f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}_url.xml"
            
            # Download to temporary file
            temp_dir = tempfile.gettempdir()
            temp_filepath = os.path.join(temp_dir, f"{biomodels_id}.xml")
            
            # Update status (safe from background thread)
            GLib.idle_add(lambda: self._show_status(f"Downloading {biomodels_id}..."))
            
            # Fetch the file (blocking operation, but we're in a background thread)
            try:
                urllib.request.urlretrieve(url, temp_filepath)
            except socket.timeout:
                GLib.idle_add(lambda: self._show_status(f"Download timeout for {biomodels_id} (30s)", error=True))
                GLib.idle_add(self.sbml_fetch_button.set_sensitive, True)
                return
            
            # Verify file exists and has content
            if not os.path.exists(temp_filepath) or os.path.getsize(temp_filepath) == 0:
                GLib.idle_add(lambda: self._show_status(f"Failed to download {biomodels_id}", error=True))
                GLib.idle_add(self.sbml_fetch_button.set_sensitive, True)
                return
            
            # Store filepath
            self.current_filepath = temp_filepath
            
            # Update UI elements (must use GLib.idle_add from background thread)
            def update_ui_success():
                # Update file entry to show the temp path
                if self.sbml_file_entry:
                    self.sbml_file_entry.set_text(temp_filepath)
                
                # Enable parse button
                if self.sbml_parse_button:
                    self.sbml_parse_button.set_sensitive(True)
                
                # Re-enable fetch button
                if self.sbml_fetch_button:
                    self.sbml_fetch_button.set_sensitive(True)
                
                self._show_status(f"✓ Downloaded {biomodels_id} successfully")
                return False  # Don't repeat
            
            GLib.idle_add(update_ui_success)
            
        except urllib.error.HTTPError as e:
            def show_http_error():
                if e.code == 404:
                    self._show_status(f"Model {biomodels_id} not found in BioModels", error=True)
                else:
                    self._show_status(f"HTTP error {e.code}: {e.reason}", error=True)
                if self.sbml_fetch_button:
                    self.sbml_fetch_button.set_sensitive(True)
                return False
            GLib.idle_add(show_http_error)
            
        except socket.timeout:
            def show_timeout_error():
                self._show_status(f"Network timeout while fetching {biomodels_id}", error=True)
                if self.sbml_fetch_button:
                    self.sbml_fetch_button.set_sensitive(True)
                return False
            GLib.idle_add(show_timeout_error)
            
        except Exception as e:
            def show_error():
                self._show_status(f"Fetch error: {str(e)}", error=True)
                if self.sbml_fetch_button:
                    self.sbml_fetch_button.set_sensitive(True)
                return False
            GLib.idle_add(show_error)
    
    def _on_scale_changed(self, spin_button):
        """Handle scale factor spin button changes - update example."""
        if not self.sbml_scale_example:
            return
        
        scale = spin_button.get_value()
        example_concentration = 5.0  # mM (millimolar)
        tokens = round(example_concentration * scale)
        
        self.sbml_scale_example.set_text(
            f"Example: {example_concentration} mM glucose → {tokens} tokens"
        )
    
    def _on_layout_algorithm_changed(self, combo):
        """Handle layout algorithm selection changes - show/hide parameter boxes."""
        if not combo:
            return
        
        active_index = combo.get_active()
        
        # Hide all parameter boxes
        if self.sbml_auto_params_box:
            self.sbml_auto_params_box.set_visible(False)
        if self.sbml_hierarchical_params_box:
            self.sbml_hierarchical_params_box.set_visible(False)
        if self.sbml_force_params_box:
            self.sbml_force_params_box.set_visible(False)
        
        # Show appropriate parameter box based on selection
        # 0 = Auto, 1 = Hierarchical, 2 = Force-Directed
        if active_index == 0 and self.sbml_auto_params_box:
            self.sbml_auto_params_box.set_visible(True)
        elif active_index == 1 and self.sbml_hierarchical_params_box:
            self.sbml_hierarchical_params_box.set_visible(True)
        elif active_index == 2 and self.sbml_force_params_box:
            self.sbml_force_params_box.set_visible(True)
    
    def _quick_load_to_canvas(self):
        """Load parsed pathway to canvas with arbitrary positions.
        
        New Simplified Workflow (v2.0):
        1. Parse SBML → PathwayData (species, reactions, connections)
        2. Post-process with minimal PathwayPostProcessor (arbitrary positions, colors, units)
        3. Convert to Petri net (places, transitions, arcs with stoichiometry weights)
        4. Load to canvas
        5. User applies Swiss Palette → Force-Directed for physics-based layout
        
        IMPORTANT: Initial positions are ARBITRARY - force-directed will recalculate everything.
        This is now the MAIN import path (not a testing mode anymore).
        """
        if not self.parsed_pathway:
            self.logger.warning("No parsed pathway to load")
            return
        
        if not self.model_canvas or not self.converter:
            self.logger.warning("Canvas or converter not available for load")
            return
        
        try:
            self.logger.info("Loading pathway to canvas with arbitrary positions")
            
            # Get scale factor from UI
            scale_factor = self.sbml_scale_spin.get_value() if self.sbml_scale_spin else 1.0
            
            # Post-process: arbitrary positions, colors, unit normalization
            # This uses the NEW simplified PathwayPostProcessor (v2.0)
            self._show_status("Preparing pathway data...")
            from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
            postprocessor = PathwayPostProcessor(scale_factor=scale_factor)
            processed = postprocessor.process(self.parsed_pathway)
            
            self.logger.info(f"Post-processing complete: {len(processed.positions)} arbitrary positions")
            
            # Convert ProcessedPathwayData to Petri net
            self._show_status("Converting to Petri net...")
            document_model = self.converter.convert(processed)
            self.logger.info(f"Converted to Petri net: {len(document_model.places)} places, {len(document_model.transitions)} transitions")
            
            # Load to canvas - create new tab
            self._show_status("Loading to canvas...")
            pathway_name = self.parsed_pathway.metadata.get('name', 'Pathway')
            page_index, drawing_area = self.model_canvas.add_document(filename=pathway_name)
            
            # Wire sbml_panel to ModelCanvasLoader (if not already wired)
            # This allows Swiss Palette Layout tools to read parameters from SBML Import Options
            if not hasattr(self.model_canvas, 'sbml_panel') or self.model_canvas.sbml_panel is None:
                self.model_canvas.sbml_panel = self
                self.logger.info("Wired SBML panel to ModelCanvasLoader")
            
            # Get canvas manager for this tab
            manager = self.model_canvas.get_canvas_manager(drawing_area)
            
            if manager:
                # ===== UNIFIED OBJECT LOADING =====
                # Use load_objects() for consistent, unified initialization path
                # This replaces direct assignment + manual notification loop
                # Benefits: Single code path, automatic notifications, proper references
                manager.load_objects(
                    places=document_model.places,
                    transitions=document_model.transitions,
                    arcs=document_model.arcs
                )
                
                # CRITICAL: Set on_changed callback on all loaded objects
                # This is required for proper object state management and dirty tracking
                manager.document_controller.set_change_callback(manager._on_object_changed)
                
                # Fit imported content to page (SBML models often have extreme coordinates)
                # Use 15% padding for better visibility of large imported models
                # Use 30% horizontal offset to shift right (accounting for right panel)
                # Use +10% vertical offset to shift UP in Cartesian space (increase Y)
                # Offsets are calculated in screen space, so they remain constant regardless of zoom
                # DEFERRED: Wait until viewport dimensions are set on first draw
                manager.fit_to_page(padding_percent=15, deferred=True, horizontal_offset_percent=30, vertical_offset_percent=10)
                
                # Mark as imported so "Save" triggers "Save As" behavior
                manager.mark_as_imported(pathway_name)
                
                # Trigger redraw
                drawing_area.queue_draw()
                
                self.logger.info(f"Canvas loaded: {len(manager.places)} places, {len(manager.transitions)} transitions")
                self._show_status(f"✓ Loaded {len(manager.places)} places, {len(manager.transitions)} transitions - Use Swiss Palette → Force-Directed for layout")
            else:
                self.logger.error("Failed to get canvas manager")
                self._show_status("Error: Failed to get canvas manager", error=True)
            
        except Exception as e:
            self.logger.error(f"Load failed: {e}")
            self._show_status(f"Load error: {str(e)}", error=True)
            import traceback
            traceback.print_exc()
    
    def _on_parse_clicked(self, button):
        """Handle parse button click - parse and validate SBML file."""
        if not self.parser or not self.validator:
            self._show_status("Error: SBML importer not available", error=True)
            return
        
        if not self.current_filepath:
            self._show_status("Please select an SBML file", error=True)
            return
        
        # Validate file exists
        if not os.path.exists(self.current_filepath):
            self._show_status(f"File not found: {self.current_filepath}", error=True)
            return
        
        # Disable parse button during parsing
        self.sbml_parse_button.set_sensitive(False)
        self._show_status(f"Parsing {os.path.basename(self.current_filepath)}...")
        
        # Parse in background to avoid blocking UI
        GLib.idle_add(self._parse_pathway_background)
    
    def _parse_pathway_background(self):
        """Background task to parse and validate SBML file.
        
        Returns:
            False to stop GLib.idle_add from repeating
        """
        try:
            # Parse SBML file directly (enrichment removed - heterogeneity intractable)
            self._show_status(f"Parsing SBML...")
            self.parsed_pathway = self.parser.parse_file(self.current_filepath)
            
            if not self.parsed_pathway:
                self._show_status("Failed to parse SBML file", error=True)
                self.sbml_parse_button.set_sensitive(True)
                return False
            
            # Validate pathway
            validation_result = self.validator.validate(self.parsed_pathway)
            
            # Check for errors
            if not validation_result.is_valid:
                # Show errors in status
                error_count = len(validation_result.errors)
                warning_count = len(validation_result.warnings)
                
                error_msg = f"Validation failed: {error_count} error(s), {warning_count} warning(s)"
                self._show_status(error_msg, error=True)
                
                # Show detailed errors in preview
                self._show_validation_errors(validation_result)
                
                self.sbml_parse_button.set_sensitive(True)
                return False
            
            # Show warnings if any
            if validation_result.warnings:
                warning_count = len(validation_result.warnings)
                self._show_status(f"✓ Parsed with {warning_count} warning(s)")
            else:
                self._show_status(f"✓ Parsed and validated successfully")
            
            # Update preview with pathway info
            self._update_preview()
            
            # Load to canvas after parse (NEW: always enabled, not a testing mode)
            if self.model_canvas:
                self.logger.info("Auto-loading to canvas after parse")
                GLib.idle_add(self._quick_load_to_canvas)
            else:
                self.logger.debug("Canvas not available, skipping auto-load")
            
        except Exception as e:
            self._show_status(f"Parse error: {str(e)}", error=True)
            self.parsed_pathway = None
            
            import traceback
            traceback.print_exc()
        
        finally:
            # Re-enable parse button
            if self.sbml_parse_button:
                self.sbml_parse_button.set_sensitive(True)
        
        return False  # Don't repeat
    
    def _show_validation_errors(self, validation_result):
        """Show validation errors and warnings in preview area.
        
        Args:
            validation_result: ValidationResult with errors and warnings
        """
        if not self.sbml_preview_text:
            return
        
        lines = []
        lines.append("VALIDATION ERRORS:")
        lines.append("")
        
        # Show errors
        if validation_result.errors:
            lines.append("Errors:")
            for error in validation_result.errors:
                lines.append(f"  ❌ {error}")
            lines.append("")
        
        # Show warnings
        if validation_result.warnings:
            lines.append("Warnings:")
            for warning in validation_result.warnings:
                lines.append(f"  ⚠ {warning}")
        
        error_text = "\n".join(lines)
        buffer = self.sbml_preview_text.get_buffer()
        buffer.set_text(error_text)
    
    def _update_preview(self):
        """Update preview text with pathway information."""
        if not self.parsed_pathway or not self.sbml_preview_text:
            return
        
        pathway = self.parsed_pathway
        
        # Build preview text
        lines = []
        # Get name from metadata (PathwayData stores it there)
        pathway_name = pathway.metadata.get('name', 'Unnamed')
        lines.append(f"Pathway: {pathway_name}")
        
        # Get description from metadata if available
        pathway_desc = pathway.metadata.get('description')
        if pathway_desc:
            lines.append(f"Description: {pathway_desc}")
        lines.append("")
        
        # Species info
        lines.append(f"Species: {len(pathway.species)}")
        if pathway.species:
            # Group by compartment
            compartments = {}
            for species in pathway.species:
                comp = species.compartment or "Unknown"
                if comp not in compartments:
                    compartments[comp] = []
                compartments[comp].append(species)
            
            for comp, species_list in compartments.items():
                lines.append(f"  {comp}: {len(species_list)} species")
                # Show first few species
                for i, species in enumerate(species_list[:3]):
                    conc_str = f" ({species.initial_concentration} mM)" if species.initial_concentration else ""
                    lines.append(f"    • {species.name or species.id}{conc_str}")
                if len(species_list) > 3:
                    lines.append(f"    ... and {len(species_list) - 3} more")
        lines.append("")
        
        # Reactions info
        lines.append(f"Reactions: {len(pathway.reactions)}")
        if pathway.reactions:
            # Show first few reactions
            for i, reaction in enumerate(pathway.reactions[:3]):
                kinetic_type = reaction.kinetic_law.rate_type if reaction.kinetic_law else "none"
                lines.append(f"  • {reaction.name or reaction.id} ({kinetic_type})")
            if len(pathway.reactions) > 3:
                lines.append(f"  ... and {len(pathway.reactions) - 3} more")
        lines.append("")
        
        # Compartments info
        if pathway.compartments:
            lines.append(f"Compartments: {len(pathway.compartments)}")
            # pathway.compartments is a dict {id: name}, not a list
            comp_items = list(pathway.compartments.items())[:5]
            for comp_id, comp_name in comp_items:
                lines.append(f"  • {comp_name or comp_id}")
            if len(pathway.compartments) > 5:
                lines.append(f"  ... and {len(pathway.compartments) - 5} more")
        
        preview_text = "\n".join(lines)
        
        # Set text in TextView
        buffer = self.sbml_preview_text.get_buffer()
        buffer.set_text(preview_text)
    
    # NOTE: _on_import_clicked and _import_pathway_background removed in v2.0
    # The old Import button workflow used hierarchical/grid/force layout algorithms
    # NEW workflow: Parse → _quick_load_to_canvas → Swiss Palette → Force-Directed
    # See PIPELINE_REFACTORING_PLAN.md for details
    
    def _show_status(self, message: str, error: bool = False):
        """Show status message in label.
        
        Args:
            message: Status message to display
            error: If True, display as error (red text)
        """
        if not self.sbml_status_label:
            return
        
        if error:
            self.sbml_status_label.set_markup(f'<span foreground="red">{message}</span>')
        else:
            self.sbml_status_label.set_text(message)
    
    def get_layout_parameters_for_algorithm(self, algorithm: str) -> dict:
        """Get layout parameters from UI for the specified algorithm.
        
        This allows Swiss Palette Layout tools to use the same parameters
        that were configured in the SBML Import Options.
        
        Args:
            algorithm: Algorithm name ('auto', 'hierarchical', 'force_directed')
            
        Returns:
            Dictionary of algorithm-specific parameters
        """
        params = {}
        
        if algorithm == 'hierarchical':
            if self.sbml_layer_spacing_spin:
                params['layer_spacing'] = self.sbml_layer_spacing_spin.get_value()
            if self.sbml_node_spacing_spin:
                params['node_spacing'] = self.sbml_node_spacing_spin.get_value()
                
        elif algorithm == 'force_directed':
            if self.sbml_iterations_spin:
                params['iterations'] = int(self.sbml_iterations_spin.get_value())
            if self.sbml_k_factor_spin:
                # k_factor is a multiplier, will be used to calculate actual k
                k_multiplier = self.sbml_k_factor_spin.get_value()
                params['k_multiplier'] = k_multiplier
                # Note: actual k is calculated as: k = sqrt(area/nodes) * k_multiplier
                # We don't set 'k' directly, let the algorithm calculate it
            if self.sbml_canvas_scale_spin:
                params['scale'] = self.sbml_canvas_scale_spin.get_value()
        
        return params
