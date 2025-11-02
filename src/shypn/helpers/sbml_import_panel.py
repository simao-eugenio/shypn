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
import time
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
    
    def __init__(self, builder: Gtk.Builder, model_canvas=None, workspace_settings=None, parent_window=None, project=None):
        """Initialize the SBML import panel controller.
        
        Args:
            builder: GTK Builder with loaded pathway_panel.ui
            model_canvas: Optional ModelCanvasManager for loading pathways
            workspace_settings: Optional WorkspaceSettings for remembering last query
            parent_window: Optional parent window for dialogs (WAYLAND FIX)
            project: Optional Project instance for metadata tracking
        """
        self.builder = builder
        self.model_canvas = model_canvas
        self.workspace_settings = workspace_settings
        self.parent_window = parent_window  # WAYLAND FIX: Store parent for dialogs
        self.project = project
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
        # Core state
        self.current_filepath = None
        self.parsed_pathway = None
        self.processed_pathway = None
        self.current_pathway_doc = None  # PathwayDocument tracking metadata
        self.file_panel_loader = None  # Will be set by main app to enable file tree refresh
        
        # Workflow state: track if we're in unified import button flow
        self._import_button_flow = False
        self._fetch_in_progress = False
        
        # Get widget references
        self._get_widgets()
        
        # Connect signals
        self._connect_signals()
        
        # Load last BioModels query from settings
        self._load_last_biomodels_query()
    
    def set_project(self, project):
        """Set or update the current project for metadata tracking.
        
        Args:
            project: Project instance
        """
        self.project = project
    
    def set_file_panel_loader(self, file_panel_loader):
        """Set file panel loader reference to enable file tree refresh after save.
        
        Args:
            file_panel_loader: FilePanelLoader instance
        """
        self.file_panel_loader = file_panel_loader
    
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
        self.sbml_parse_button = self.builder.get_object('sbml_parse_button')  # May be None if using unified import
        self.sbml_import_button = self.builder.get_object('sbml_import_button')
    
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
        
        # Unified import button (handles both fetch/browse + parse + load to canvas)
        if self.sbml_import_button:
            self.sbml_import_button.connect('clicked', self._on_import_clicked)
        
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
        # WAYLAND FIX: Use parent window for dialog
        dialog = Gtk.FileChooserDialog(
            title="Select SBML File",
            parent=self.parent_window,
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
        
        # WAYLAND FIX: Use async signal-based approach instead of blocking run()
        # This avoids Error 71 (Protocol error) on Wayland
        result_container = [None]  # Mutable container for result
        
        def on_response(dlg, response_id):
            if response_id == Gtk.ResponseType.OK:
                result_container[0] = dlg.get_filename()
            dlg.destroy()
            Gtk.main_quit()  # Exit nested main loop
        
        dialog.connect('response', on_response)
        dialog.show()
        Gtk.main()  # Run nested event loop until dialog responds
        
        filepath = result_container[0]
        if filepath:
            # If we have a project, copy the SBML file to project/pathways/ immediately
            if self.project:
                try:
                    filename = os.path.basename(filepath)
                    
                    # Read the SBML content
                    with open(filepath, 'r', encoding='utf-8') as f:
                        sbml_content = f.read()
                    
                    # Save to project/pathways/
                    dest_path = self.project.save_pathway_file(filename, sbml_content)
                    
                    # Use the project copy as the working file
                    filepath = dest_path
                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    # Continue with original file if copy fails
            
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
            
            # Auto-continue to parse if triggered by unified import button
            # NOTE: We're already in main thread (dialog callback), so call directly
            if self._import_button_flow:
                self._on_parse_clicked(button)

    
    def _on_fetch_clicked(self, button):
        """Handle fetch button click - download model from BioModels."""
        if not self.sbml_biomodels_entry:
            return
        
        biomodels_id = self.sbml_biomodels_entry.get_text().strip()
        if not biomodels_id:
            self._show_status("Please enter a BioModels ID", error=True)
            return
        
        # Prevent duplicate fetches
        if self._fetch_in_progress:
            return
        
        # Save query to workspace settings
        self._save_biomodels_query(biomodels_id)
        
        # Disable buttons during fetch
        self.sbml_fetch_button.set_sensitive(False)
        if self.sbml_parse_button:
            self.sbml_parse_button.set_sensitive(False)
        self._show_status(f"Fetching {biomodels_id} from BioModels...")
        
        # Set fetch flag
        self._fetch_in_progress = True
        
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
            import tempfile
            
            # BioModels API endpoint - try multiple formats for compatibility
            # Format 1: Specific file download (returns XML directly)
            # Format 2: Alternative filename patterns
            # Format 3: Legacy format for backwards compatibility
            # NOTE: URL without filename parameter returns COMBINE archive (ZIP), not XML
            urls = [
                f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}_url.xml",
                f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}.xml",
                f"https://www.ebi.ac.uk/biomodels-main/download?mid={biomodels_id}",
            ]
            
            # Determine save location based on whether we have a project
            if self.project:
                # Save directly to project/pathways/
                pathways_dir = self.project.get_pathways_dir()
                if pathways_dir:
                    os.makedirs(pathways_dir, exist_ok=True)
                    temp_filepath = os.path.join(pathways_dir, f"{biomodels_id}.xml")
                else:
                    # Fallback to temp if project has no pathways dir
                    temp_dir = tempfile.gettempdir()
                    temp_filepath = os.path.join(temp_dir, f"{biomodels_id}.xml")
            else:
                # No project - use temp directory
                temp_dir = tempfile.gettempdir()
                temp_filepath = os.path.join(temp_dir, f"{biomodels_id}.xml")
            
            # Update status (safe from background thread)
            GLib.idle_add(lambda: self._show_status(f"Downloading {biomodels_id}..."))
            
            # Try each URL format until one works
            success = False
            last_error = None
            
            for url_idx, url in enumerate(urls):
                try:
                    # Create request with proper headers
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'SHYpn/2.0 (Python urllib)')
                    req.add_header('Accept', 'application/xml, text/xml, */*')
                    
                    # Open URL with 90 second timeout for large models
                    response = urllib.request.urlopen(req, timeout=90)
                    
                    # Read content and write to file
                    content = response.read()
                    
                    # Verify we got XML content, not a ZIP archive
                    if not content or len(content) < 100:
                        raise ValueError(f"Downloaded content too small: {len(content)} bytes")
                    
                    # Check for ZIP/COMBINE archive (BioModels now returns these by default)
                    if content[:2] == b'PK':  # ZIP magic number
                        raise ValueError("Downloaded content is a ZIP archive (COMBINE format), not SBML XML. Try a different URL format.")
                    
                    if b'<?xml' not in content[:200] and b'<sbml' not in content[:500]:
                        raise ValueError("Downloaded content does not appear to be SBML/XML")
                    
                    # Write to file
                    with open(temp_filepath, 'wb') as f:
                        f.write(content)
                    
                    success = True
                    break
                    
                except urllib.error.URLError as e:
                    last_error = e
                    if hasattr(e, 'reason') and 'timed out' in str(e.reason).lower():
                        # Timeout - try next URL
                        continue
                    elif hasattr(e, 'code'):
                        # HTTP error - try next URL
                        continue
                    else:
                        # Network error - try next URL
                        continue
                        
                except Exception as e:
                    last_error = e
                    continue
            
            if not success:
                # All URLs failed - provide helpful message
                error_msg = f"⚠ BioModels download failed for {biomodels_id}"
                
                if last_error:
                    if hasattr(last_error, 'reason') and 'timed out' in str(last_error.reason).lower():
                        error_msg = f"⚠ Timeout downloading {biomodels_id}. The BioModels server may be slow or temporarily unavailable."
                    elif hasattr(last_error, 'code'):
                        if last_error.code == 404:
                            error_msg = f"⚠ Model {biomodels_id} not found. Check the ID is correct."
                        elif last_error.code >= 500:
                            error_msg = f"⚠ BioModels server error ({last_error.code}). The service may be temporarily down."
                        else:
                            error_msg = f"⚠ HTTP error {last_error.code} for {biomodels_id}"
                    else:
                        error_msg = f"⚠ Network error: {str(last_error)}"
                
                # Add manual download suggestion
                error_msg += f"\n\nTip: Visit https://www.ebi.ac.uk/biomodels/{biomodels_id} to manually download the SBML file, then use 'Browse' to load it."
                
                GLib.idle_add(lambda msg=error_msg: self._show_status(msg, error=True))
                GLib.idle_add(self.sbml_fetch_button.set_sensitive, True)
                self._fetch_in_progress = False
                return
            
            # Verify file was written successfully
            if not os.path.exists(temp_filepath) or os.path.getsize(temp_filepath) == 0:
                GLib.idle_add(lambda: self._show_status(f"Failed to save {biomodels_id}", error=True))
                GLib.idle_add(self.sbml_fetch_button.set_sensitive, True)
                self._fetch_in_progress = False
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
                
                # Auto-continue to parse if triggered by unified import button
                # NOTE: We're already in main thread (queued by idle_add), so call directly
                if self._import_button_flow:
                    self._on_parse_clicked(None)
                
                # Clear fetch flag
                self._fetch_in_progress = False
                
                return False  # Don't repeat
            
            GLib.idle_add(update_ui_success)
            
        except Exception as e:
            def show_error():
                self._show_status(f"Fetch error: {str(e)}", error=True)
                if self.sbml_fetch_button:
                    self.sbml_fetch_button.set_sensitive(True)
                self._fetch_in_progress = False
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
    
    def _on_load_clicked(self, button):
        """Handle load button click - convert and save to file.
        
        NEW APPROACH: Convert pathway and save .shy file, skip canvas creation.
        
        Operations run in background thread to avoid blocking UI.
        """
        if not self.parsed_pathway:
            self.logger.warning("No parsed pathway to load")
            self._show_status("No parsed pathway available", error=True)
            return
        
        if not self.converter:
            self.logger.warning("Converter not available")
            self._show_status("Converter not available", error=True)
            return
        
        # Get pathway name and parameters
        pathway_name = self.parsed_pathway.metadata.get('name', 'Pathway')
        scale_factor = self.sbml_scale_spin.get_value() if self.sbml_scale_spin else 1.0
        parsed_pathway = self.parsed_pathway
        
        self._show_status("🔄 Converting to Petri net...")
        
        # Convert and save in background thread
        def load_thread():
            try:
                # Post-process: arbitrary positions, colors, unit normalization
                from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
                postprocessor = PathwayPostProcessor(scale_factor=scale_factor)
                processed = postprocessor.process(parsed_pathway)
                
                # Convert ProcessedPathwayData to Petri net
                document_model = self.converter.convert(processed)
                
                # Pass results back to main thread for saving
                GLib.idle_add(self._on_load_and_save_complete, document_model, pathway_name)
                
            except Exception as e:
                GLib.idle_add(self._on_load_error, str(e))
        
        import threading
        threading.Thread(target=load_thread, daemon=True).start()
    
    def _on_load_and_save_complete(self, document_model, pathway_name):
        """Handle successful conversion - save files only (NO canvas loading).
        
        NEW FLOW: Convert → Save Files → Guide user to File → Open
        
        Args:
            document_model: The converted DocumentModel with places/transitions/arcs
            pathway_name: Name for the pathway
            
        Returns:
            False to stop GLib.idle_add from repeating
        """
        try:
            self._show_status("💾 Saving files...")
            
            # ============================================================================
            # SAVE FILES: Raw SBML and converted .shy model
            # ============================================================================
            if self.project and self.current_filepath and self.parsed_pathway:
                try:
                    # Verify project has valid base path
                    if not self.project.base_path:
                        raise ValueError("Project base_path not set - cannot save files")
                    
                    self.logger.info(f"Project base path: {self.project.base_path}")
                    
                    filename = os.path.basename(self.current_filepath)
                    
                    # 1. Save raw SBML file to project/pathways/
                    pathways_dir = self.project.get_pathways_dir()
                    expected_path = os.path.join(pathways_dir, filename) if pathways_dir else None
                    
                    if expected_path and not os.path.exists(expected_path):
                        # Copy SBML file to project using project method
                        if self.current_filepath and os.path.exists(self.current_filepath):
                            try:
                                sbml_content = open(self.current_filepath, 'r', encoding='utf-8').read()
                                dest_path = self.project.save_pathway_file(filename, sbml_content)
                                self.current_filepath = dest_path
                                self.logger.info(f"SBML file saved to: {dest_path}")
                            except Exception as copy_error:
                                import traceback
                                traceback.print_exc()
                    
                    # 2. Save .shy model file to project/models/ using project-aware path
                    base_name = os.path.splitext(filename)[0]  # Remove .xml extension
                    model_filename = f"{base_name}.shy"
                    
                    # Get models directory from project (creates if needed)
                    models_dir = self.project.get_models_dir()
                    if not models_dir:
                        raise ValueError("Project models directory not available - base_path may be None")
                    
                    self.logger.info(f"Models directory: {models_dir}")
                    os.makedirs(models_dir, exist_ok=True)
                    model_filepath = os.path.join(models_dir, model_filename)
                    
                    # Save document model to file
                    self.logger.info(f"Saving model file to: {model_filepath}")
                    document_model.save_to_file(model_filepath)
                    self.logger.info(f"Model saved successfully to: {model_filepath}")
                    
                    # 3. Create and register PathwayDocument metadata
                    from shypn.data.pathway_document import PathwayDocument
                    
                    # Get organism from metadata
                    organism = "Unknown"
                    if hasattr(self.parsed_pathway, 'organism'):
                        organism = self.parsed_pathway.organism or "Unknown"
                    elif hasattr(self.parsed_pathway, 'metadata') and 'organism' in self.parsed_pathway.metadata:
                        organism = self.parsed_pathway.metadata.get('organism', "Unknown")
                    
                    # Get pathway name
                    if hasattr(self.parsed_pathway, 'name'):
                        pathway_name = self.parsed_pathway.name or filename
                    elif hasattr(self.parsed_pathway, 'metadata') and 'name' in self.parsed_pathway.metadata:
                        pathway_name = self.parsed_pathway.metadata.get('name', filename)
                    else:
                        pathway_name = filename
                    
                    self.current_pathway_doc = PathwayDocument(
                        source_type="sbml",
                        source_id=os.path.splitext(filename)[0],
                        source_organism=organism,
                        name=pathway_name
                    )
                    
                    # Set file paths
                    self.current_pathway_doc.raw_file = filename
                    self.current_pathway_doc.model_file = model_filename
                    
                    # Add notes with pathway statistics
                    notes_parts = [f"SBML model: {pathway_name}"]
                    if self.parsed_pathway:
                        species_count = len(self.parsed_pathway.species)
                        reactions_count = len(self.parsed_pathway.reactions)
                        notes_parts.append(f"Species: {species_count}, Reactions: {reactions_count}")
                    self.current_pathway_doc.notes = "\n".join(notes_parts)
                    
                    # Register with project
                    self.project.add_pathway(self.current_pathway_doc)
                    self.project.save()
                    
                    # Refresh file tree to show new files
                    if self.file_panel_loader and hasattr(self.file_panel_loader, 'file_explorer'):
                        if hasattr(self.file_panel_loader.file_explorer, '_load_current_directory'):
                            self.file_panel_loader.file_explorer._load_current_directory()
                            self.logger.info("File tree refreshed after save")
                        
                        # Trigger file open event to notify Report panel and other observers
                        # This properly loads the model to canvas and triggers all connected events
                        if hasattr(self.file_panel_loader.file_explorer, 'on_file_open_requested'):
                            self.logger.info(f"Triggering on_file_open_requested: {model_filepath}")
                            self.file_panel_loader.file_explorer.on_file_open_requested(model_filepath)
                            self.logger.info("File open event triggered - Report panel should populate")
                    
                    # Success message
                    self._show_status(f"✅ {model_filename} imported and loaded to canvas")
                    
                except Exception as save_error:
                    import traceback
                    traceback.print_exc()
                    self._show_status(f"❌ Save error: {save_error}", error=True)
            else:
                # No project - can't save
                if not self.project:
                    self._show_status("❌ No project - please create or open a project first", error=True)
                else:
                    self._show_status("❌ No file loaded for saving", error=True)
            
            # Clear import button flow flag - workflow complete
            self._import_button_flow = False
                
        except Exception as e:
            self.logger.error(f"Save failed: {e}")
            self._show_status(f"❌ Save error: {str(e)}", error=True)
            import traceback
            traceback.print_exc()
            self._import_button_flow = False
        
        return False
    
    def _on_load_error(self, error_message):
        """Handle load error (called in main thread).
        
        Args:
            error_message: The error message string
            
        Returns:
            False to stop GLib.idle_add from repeating
        """
        self._show_status(f"❌ Load error: {error_message}", error=True)
        return False
    
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
        if self.sbml_parse_button:
            self.sbml_parse_button.set_sensitive(False)
        
        filepath = self.current_filepath
        filename = os.path.basename(filepath)
        self._show_status(f"🔄 Parsing {filename}...")
        
        # Parse in background thread to avoid blocking UI
        def parse_thread():
            try:
                # Parse SBML file
                parsed_pathway = self.parser.parse_file(filepath)
                
                if not parsed_pathway:
                    GLib.idle_add(self._on_parse_error, "Failed to parse SBML file")
                    return
                
                # Validate pathway
                validation_result = self.validator.validate(parsed_pathway)
                
                # Pass results back to main thread
                GLib.idle_add(self._on_parse_complete, parsed_pathway, validation_result)
                
            except Exception as e:
                GLib.idle_add(self._on_parse_error, str(e))
        
        import threading
        threading.Thread(target=parse_thread, daemon=True).start()
    
    def _on_parse_complete(self, parsed_pathway, validation_result):
        """Handle successful parse completion (called in main thread).
        
        Args:
            parsed_pathway: The parsed PathwayData object
            validation_result: ValidationResult with errors and warnings
            
        Returns:
            False to stop GLib.idle_add from repeating
        """
        # Store the parsed pathway
        self.parsed_pathway = parsed_pathway
        
        # Update PathwayDocument with parsed metadata if available
        if self.project and self.current_pathway_doc and parsed_pathway:
            try:
                pathway_name = parsed_pathway.metadata.get('name', 'Unnamed')
                pathway_desc = parsed_pathway.metadata.get('description', '')
                organism = parsed_pathway.metadata.get('organism', 'Unknown')
                
                # Update pathway document
                self.current_pathway_doc.name = pathway_name
                self.current_pathway_doc.source_organism = organism
                if pathway_desc:
                    self.current_pathway_doc.description = pathway_desc
                
                # Add metadata about pathway content
                self.current_pathway_doc.metadata['species_count'] = len(parsed_pathway.species)
                self.current_pathway_doc.metadata['reactions_count'] = len(parsed_pathway.reactions)
                self.current_pathway_doc.metadata['compartments'] = list(parsed_pathway.compartments.keys())
                
                # Save updated metadata
                self.project.save()
                
            except Exception as e:
                import traceback
                traceback.print_exc()
        
        # Check for validation errors
        if not validation_result.is_valid:
            error_count = len(validation_result.errors)
            warning_count = len(validation_result.warnings)
            error_msg = f"❌ Validation failed: {error_count} error(s), {warning_count} warning(s)"
            self._show_status(error_msg, error=True)
            self._show_validation_errors(validation_result)
            if self.sbml_parse_button:
                self.sbml_parse_button.set_sensitive(True)
            return False
        
        # Show warnings if any
        if validation_result.warnings:
            warning_count = len(validation_result.warnings)
            self._show_status(f"✅ Parsed with {warning_count} warning(s)")
        else:
            self._show_status(f"✅ Parsed and validated successfully")
        
        # Update preview with pathway info
        self._update_preview()
        
        # Re-enable parse button
        if self.sbml_parse_button:
            self.sbml_parse_button.set_sensitive(True)
        
        # Auto-load to canvas after parse
        # NOTE: Canvas was already created in _on_import_clicked() for lazy loading
        if self.model_canvas:
            self.logger.info("Auto-loading to canvas after parse")
            self._on_load_clicked(None)
        else:
            self.logger.debug("Canvas not available, skipping auto-load")
        
        return False
    
    def _on_parse_error(self, error_message):
        """Handle parse error (called in main thread).
        
        Args:
            error_message: The error message string
            
        Returns:
            False to stop GLib.idle_add from repeating
        """
        self._show_status(f"❌ Parse error: {error_message}", error=True)
        self.parsed_pathway = None
        if self.sbml_parse_button:
            self.sbml_parse_button.set_sensitive(True)
        return False
    
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
    
    def set_parent_window(self, window):
        """Set parent window for dialogs (WAYLAND FIX).
        
        Args:
            window: Parent window for FileChooser and other dialogs
        """
        self.parent_window = window
    
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
    
    def _on_import_clicked(self, button):
        """Handle unified import button click.
        
        CURRENT FLOW:
        1. Browse/fetch SBML file
        2. Parse and convert to DocumentModel
        3. Save .shy file to project/models/
        4. Auto-load model to canvas by triggering on_file_open_requested
        5. Report panel populates automatically with imported data
        
        This provides seamless workflow: Import → Model loaded → Report populated.
        """
        # Set flag to enable auto-continue workflow
        self._import_button_flow = True
        
        # Check if we already have a file selected or fetched
        if self.current_filepath and os.path.exists(self.current_filepath):
            # File already selected - go straight to parse
            self._on_parse_clicked(button)
        else:
            # No file selected yet - need to browse or fetch
            if self.sbml_local_radio and self.sbml_local_radio.get_active():
                # Local file mode - trigger browse (will auto-continue to parse)
                self._on_browse_clicked(button)
            elif self.sbml_biomodels_radio and self.sbml_biomodels_radio.get_active():
                # BioModels mode - trigger fetch (will auto-continue to parse)
                biomodels_id = self.sbml_biomodels_entry.get_text().strip() if self.sbml_biomodels_entry else ""
                if biomodels_id:
                    # ID entered - fetch it
                    self._on_fetch_clicked(button)
                else:
                    self._show_status("Please enter a BioModels ID", error=True)
                    self._import_button_flow = False  # Clear flag on error
            else:
                self._show_status("Please select an SBML file or enter a BioModels ID", error=True)
                self._import_button_flow = False  # Clear flag on error

