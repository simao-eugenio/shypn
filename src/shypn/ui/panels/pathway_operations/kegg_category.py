#!/usr/bin/env python3
"""KEGG Import Category for Pathway Operations Panel.

Handles KEGG pathway import workflow:
1. User enters pathway ID (e.g., "hsa00010")
2. Fetch KGML data from KEGG API (background thread)
3. Parse and convert to Petri net
4. Save to project/models/
5. Notify BRENDA category of imported species/reactions

Author: Simão Eugénio
Date: 2025-10-29
"""
import os
import sys
import logging
import threading
from typing import Optional, Dict, Any

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from .base_pathway_category import BasePathwayCategory

# Import KEGG backend modules
try:
    from shypn.importer.kegg import KEGGAPIClient, KGMLParser, PathwayConverter
    from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
    from shypn.pathway.options import EnhancementOptions
except ImportError as e:
    print(f'Warning: KEGG importer not available: {e}', file=sys.stderr)
    KEGGAPIClient = None
    KGMLParser = None
    PathwayConverter = None
    convert_pathway_enhanced = None
    EnhancementOptions = None

try:
    from shypn.data.pathway_document import PathwayDocument
except ImportError:
    PathwayDocument = None


class KEGGCategory(BasePathwayCategory):
    """KEGG import category for Pathway Operations Panel.
    
    Contains:
    - Pathway ID input
    - Import options (cofactor filtering, coordinate scaling)
    - Preview area (pathway info)
    - Import button (fetch + convert + save)
    - Status display
    """
    
    def __init__(self, expanded=False, model_canvas=None, project=None):
        """Initialize KEGG category.
        
        Args:
            expanded: Whether category starts expanded
            model_canvas: ModelCanvasManager instance (optional)
            project: Project instance for metadata tracking (optional)
        """
        # Initialize attributes BEFORE calling super().__init__()
        # because _build_content() is called during super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set project and canvas
        self.model_canvas = model_canvas
        self.project = project
        
        # Initialize backend components
        if KEGGAPIClient and KGMLParser and PathwayConverter:
            self.api_client = KEGGAPIClient()
            self.parser = KGMLParser()
            self.converter = PathwayConverter()
        else:
            self.api_client = None
            self.parser = None
            self.converter = None
            self.logger.warning("KEGG import backend not available")
        
        # Current pathway data
        self.current_pathway = None
        self.current_kgml = None
        self.current_pathway_id = None
        self.current_pathway_doc = None
        
        # File panel loader reference (for file tree refresh)
        self.file_panel_loader = None
        
        # NOW call super().__init__() which will call _build_content()
        super().__init__(category_name="KEGG", expanded=expanded)
    
    def set_file_panel_loader(self, file_panel_loader):
        """Set file panel loader reference to enable file tree refresh after save.
        
        Args:
            file_panel_loader: FilePanelLoader instance
        """
        self.file_panel_loader = file_panel_loader
    
    def _build_content(self):
        """Build and return the content widget.
        
        Returns:
            Gtk.Box: The content to display in this category
        """
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        
        # Source selection (Local/Remote)
        source_box = self._build_source_selection()
        main_box.pack_start(source_box, False, False, 0)
        
        # Accession input section
        accession_box = self._build_accession_input()
        main_box.pack_start(accession_box, False, False, 0)
        
        # Options section
        options_box = self._build_options()
        main_box.pack_start(options_box, False, False, 0)
        
        # Preview section
        preview_box = self._build_preview()
        main_box.pack_start(preview_box, True, True, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self.status_label.set_line_wrap(True)
        self.status_label.get_style_context().add_class("dim-label")
        main_box.pack_start(self.status_label, False, False, 0)
        
        # Save to Project button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.END)
        
        self.import_button = Gtk.Button(label="Save to Project")
        self.import_button.set_size_request(150, -1)
        self.import_button.connect('clicked', self._on_import_clicked)
        button_box.pack_start(self.import_button, False, False, 0)
        
        main_box.pack_start(button_box, False, False, 0)
        
        # Show all widgets (required for content to be visible)
        main_box.show_all()
        
        # Update UI state based on project availability
        # This must happen after widgets are created
        GLib.idle_add(self._update_ui_for_project_state)
        
        return main_box
    
    def _build_source_selection(self):
        """Build source selection (Local/Remote).
        
        Returns:
            Gtk.Box: Source selection widgets
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label()
        label.set_markup("<b>Source:</b>")
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)
        
        radio_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        # Local option (selectable but will show message that it's not available)
        self.local_radio = Gtk.RadioButton(label="Local")
        self.local_radio.set_active(False)
        self.local_radio.connect('toggled', self._on_source_changed)
        radio_box.pack_start(self.local_radio, False, False, 0)
        
        # Remote option - default for KEGG
        self.remote_radio = Gtk.RadioButton.new_with_label_from_widget(self.local_radio, "Remote (KEGG API)")
        self.remote_radio.set_active(True)
        self.remote_radio.connect('toggled', self._on_source_changed)
        radio_box.pack_start(self.remote_radio, False, False, 0)
        
        box.pack_start(radio_box, False, False, 0)
        
        return box
    
    def _build_accession_input(self):
        """Build accession number input section.
        
        Returns:
            Gtk.Box: Accession input widgets
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label()
        label.set_markup("<b>Accession Number:</b>")
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)
        
        self.pathway_id_entry = Gtk.Entry()
        self.pathway_id_entry.set_placeholder_text("e.g., hsa00010, eco00020")
        self.pathway_id_entry.connect('changed', self._on_accession_entry_changed)
        box.pack_start(self.pathway_id_entry, False, False, 0)
        
        # Help text (will change based on mode)
        self.accession_help_label = Gtk.Label()
        self.accession_help_label.set_markup(
            '<span size="small">Enter KEGG pathway ID (organism code + pathway number)\n'
            'Examples: hsa00010 (human glycolysis), eco00020 (E.coli TCA cycle)</span>'
        )
        self.accession_help_label.set_xalign(0)
        self.accession_help_label.get_style_context().add_class("dim-label")
        self.accession_help_label.set_line_wrap(True)
        box.pack_start(self.accession_help_label, False, False, 0)
        
        return box
    
    def _build_options(self):
        """Build import options section.
        
        Returns:
            Gtk.Box: Options widgets
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label()
        label.set_markup("<b>Options:</b>")
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)
        
        # Include cofactors checkbox (metadata only, not in reaction chain)
        self.filter_cofactors_check = Gtk.CheckButton(label="Include cofactors (metadata only)")
        self.filter_cofactors_check.set_active(False)
        self.filter_cofactors_check.set_tooltip_text(
            "Include common cofactors (ATP, NADH, etc.) for reference.\n"
            "They are not part of the main reaction chain."
        )
        box.pack_start(self.filter_cofactors_check, False, False, 0)
        
        # Show catalysts checkbox (Biological Petri Net mode)
        self.show_catalysts_check = Gtk.CheckButton(label="Show catalysts (Biological Petri Net)")
        self.show_catalysts_check.set_active(False)
        self.show_catalysts_check.set_tooltip_text(
            "Create enzyme/catalyst places with test arcs (dashed lines).\n"
            "Enables Biological Petri Net analysis but increases visual complexity.\n\n"
            "When disabled: Clean layout matching KEGG visualization (default)\n"
            "When enabled: Explicit enzyme places with non-consuming test arcs"
        )
        box.pack_start(self.show_catalysts_check, False, False, 0)
        
        return box
    
    def _build_preview(self):
        """Build preview section showing comprehensive import details.
        
        Returns:
            Gtk.Box: Preview widgets
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label()
        label.set_markup("<b>Preview:</b>")
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)
        label.set_xalign(0)
        label.set_markup("<b>Preview:</b>")
        box.pack_start(label, False, False, 0)
        
        # Scrolled window for preview text
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 150)
        
        self.preview_text = Gtk.TextView()
        self.preview_text.set_editable(False)
        self.preview_text.set_wrap_mode(Gtk.WrapMode.WORD)
        self.preview_text.set_left_margin(6)
        self.preview_text.set_right_margin(6)
        self.preview_text.set_top_margin(6)
        self.preview_text.set_bottom_margin(6)
        
        # Initial placeholder text
        buffer = self.preview_text.get_buffer()
        buffer.set_text("Pathway information will appear here after import...\n\n"
                       "The preview will show:\n"
                       "• Pathway name and organism\n"
                       "• Number of entries (compounds, enzymes, genes)\n"
                       "• Number of reactions and relations")
        
        scrolled.add(self.preview_text)
        box.pack_start(scrolled, True, True, 0)
        
        self.preview_widget = self.preview_text
        
        return box
    
    def _get_status_widget(self):
        """Get the status label widget.
        
        Returns:
            Gtk.Label: Status label
        """
        return self.status_label
    
    def _on_source_changed(self, radio_button):
        """Handle source radio button changes.
        
        Args:
            radio_button: The radio button that was toggled
        """
        if not radio_button.get_active():
            return
        
        if self.local_radio.get_active():
            # Local mode - update UI for file selection
            self.pathway_id_entry.set_placeholder_text("Path to local KGML file")
            self.accession_help_label.set_markup(
                '<span size="small">Enter full path to local KGML file (.kgml or .xml)\n'
                'Local files may exist in project/pathways/ from previous imports</span>'
            )
            # Check if valid file path entered
            self._on_accession_entry_changed(self.pathway_id_entry)
        else:
            # Remote mode - update UI for KEGG API
            self.pathway_id_entry.set_placeholder_text("e.g., hsa00010, eco00020")
            self.accession_help_label.set_markup(
                '<span size="small">Enter KEGG pathway ID (organism code + pathway number)\n'
                'Examples: hsa00010 (human glycolysis), eco00020 (E.coli TCA cycle)</span>'
            )
            # Check project state
            self._update_ui_for_project_state()
    
    def _on_accession_entry_changed(self, entry):
        """Handle accession entry text changes.
        
        Args:
            entry: The entry widget that changed
        """
        text = entry.get_text().strip()
        
        if self.local_radio.get_active():
            # Local mode - check if file exists
            if text and os.path.exists(text):
                if self.project:
                    self.import_button.set_sensitive(True)
                    self._show_status(f"Ready to import {os.path.basename(text)}")
                else:
                    self.import_button.set_sensitive(False)
                    self._show_status(
                        "⚠️ Please open or create a project first",
                        error=True
                    )
            else:
                self.import_button.set_sensitive(False)
                if text:
                    self._show_status(f"File not found: {text}", error=True)
        else:
            # Remote mode - just check if not empty and project available
            if text and self.project:
                self.import_button.set_sensitive(True)
                self._show_status("Ready to import from KEGG API")
            elif text and not self.project:
                self.import_button.set_sensitive(False)
                self._show_status(
                    "⚠️ Please open or create a project first",
                    error=True
                )
            else:
                self.import_button.set_sensitive(False)
    
    def _update_ui_for_project_state(self):
        """Update UI based on project availability.
        
        Disables import button and shows guidance message if no project.
        """
        if self.project:
            # Project available - enable button
            self.import_button.set_sensitive(True)
            self._show_status("Ready to import from KEGG API")
        else:
            # No project - disable button and show guidance
            self.import_button.set_sensitive(False)
            self._show_status(
                "⚠️ Please open or create a project first (File → New Project or File → Open Project)\n"
                "A project is required to save imported pathways.",
                error=True
            )
    
    def _on_import_clicked(self, button):
        """Handle import button click.
        
        Unified workflow for both Local and Remote:
        1. Get pathway ID or file path
        2. If Remote: Fetch KGML from KEGG (background thread)
        3. If Local: Read KGML from file
        4. Parse and convert to Petri net
        5. Save to project/models/
        6. Notify BRENDA category
        
        Args:
            button: The clicked button widget
        """
        if not self.parser or not self.converter:
            self._show_error("KEGG import backend not available")
            return
        
        if not self.project:
            self._show_error(
                "No project available. Please open or create a project first:\n"
                "File → New Project or File → Open Project"
            )
            return
        
        # Get input text
        input_text = self.pathway_id_entry.get_text().strip()
        if not input_text:
            self._show_error("Please enter a pathway ID or file path")
            return
        
        # Disable button during import
        self.import_button.set_sensitive(False)
        self.import_in_progress = True
        
        if self.local_radio.get_active():
            # Local mode - read from file
            if not os.path.exists(input_text):
                self._show_error(f"File not found: {input_text}")
                self.import_button.set_sensitive(True)
                self.import_in_progress = False
                return
            
            self._show_progress(f"Processing local file {os.path.basename(input_text)}...")
            self._process_local_kgml(input_text)
        else:
            # Remote mode - fetch from KEGG API
            if not self.api_client:
                self._show_error("KEGG API client not available")
                self.import_button.set_sensitive(True)
                self.import_in_progress = False
                return
            
            pathway_id = input_text
            self._show_progress(f"Fetching pathway {pathway_id} from KEGG...")
            self._fetch_and_import_remote(pathway_id)
    
    def _process_local_kgml(self, filepath):
        """Process a local KGML file in background thread.
        
        Args:
            filepath: Path to KGML file
        """
        def parse_and_convert():
            try:
                self.logger.info(f"Processing local KGML file: {filepath}")
                
                # 1. Read KGML from file
                with open(filepath, 'r', encoding='utf-8') as f:
                    kgml_data = f.read()
                
                # Extract pathway ID from filename (e.g., hsa00010.kgml -> hsa00010)
                filename = os.path.basename(filepath)
                pathway_id = os.path.splitext(filename)[0]
                
                # 2. Parse KGML
                parsed_pathway = self.parser.parse(kgml_data)
                
                # 3. Convert to Petri net
                filter_cofactors = self.filter_cofactors_check.get_active()
                show_catalysts = self.show_catalysts_check.get_active()
                coordinate_scale = 2.5  # Optimal default scale for KEGG coordinates
                
                enhancement_options = EnhancementOptions(
                    enable_layout_optimization=True,
                    enable_arc_routing=False,  # KEGG import: straight arcs
                    enable_metadata_enhancement=True
                )
                
                self.logger.info(f"Converting pathway (cofactors={filter_cofactors}, catalysts={show_catalysts})")
                document_model = convert_pathway_enhanced(
                    parsed_pathway,
                    coordinate_scale=coordinate_scale,
                    include_cofactors=filter_cofactors,
                    filter_isolated_compounds=True,
                    create_enzyme_places=show_catalysts,  # ← NEW: Pass catalyst option
                    enhancement_options=enhancement_options
                )
                
                # Return all data for main thread processing
                return {
                    'pathway_id': pathway_id,
                    'kgml_data': kgml_data,
                    'parsed_pathway': parsed_pathway,
                    'document_model': document_model,
                    'coordinate_scale': coordinate_scale,
                    'source': 'local'
                }
                
            except Exception as e:
                self.logger.error(f"Local KGML processing failed: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Run in background thread with callbacks
        self._run_in_thread(
            parse_and_convert,
            on_complete=self._on_import_thread_complete,
            on_error=self._on_import_thread_error
        )
    
    def _fetch_and_import_remote(self, pathway_id):
        """Fetch and import pathway from KEGG API in background thread.
        
        Args:
            pathway_id: KEGG pathway ID
        """
        def fetch_and_import():
            try:
                self.logger.info(f"Fetching KEGG pathway: {pathway_id}")
                
                # 1. Fetch KGML from API (BLOCKING network request)
                kgml_data = self.api_client.fetch_kgml(pathway_id)
                if not kgml_data:
                    raise ValueError(f"Failed to fetch pathway {pathway_id}")
                
                # 2. Parse KGML
                parsed_pathway = self.parser.parse(kgml_data)
                
                # 3. Convert to Petri net
                filter_cofactors = self.filter_cofactors_check.get_active()
                show_catalysts = self.show_catalysts_check.get_active()
                coordinate_scale = 2.5  # Optimal default scale for KEGG coordinates
                
                enhancement_options = EnhancementOptions(
                    enable_layout_optimization=True,
                    enable_arc_routing=False,  # KEGG import: straight arcs
                    enable_metadata_enhancement=True
                )
                
                self.logger.info(f"Converting pathway (cofactors={filter_cofactors}, catalysts={show_catalysts})")
                document_model = convert_pathway_enhanced(
                    parsed_pathway,
                    coordinate_scale=coordinate_scale,
                    include_cofactors=filter_cofactors,
                    filter_isolated_compounds=True,  # Remove isolated places/compounds
                    create_enzyme_places=show_catalysts,  # ← NEW: Pass catalyst option
                    enhancement_options=enhancement_options
                )
                
                # Return all data for main thread processing
                return {
                    'pathway_id': pathway_id,
                    'kgml_data': kgml_data,
                    'parsed_pathway': parsed_pathway,
                    'document_model': document_model,
                    'coordinate_scale': coordinate_scale,
                    'source': 'remote'
                }
                
            except Exception as e:
                self.logger.error(f"Remote import failed: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Run in background thread with callbacks
        self._run_in_thread(
            fetch_and_import,
            on_complete=self._on_import_thread_complete,
            on_error=self._on_import_thread_error
        )
    
    def _on_import_thread_complete(self, result):
        """Called in main thread after import completes successfully.
        
        Args:
            result: Dict with import results
        """
        try:
            pathway_id = result['pathway_id']
            kgml_data = result['kgml_data']
            parsed_pathway = result['parsed_pathway']
            document_model = result['document_model']
            coordinate_scale = result.get('coordinate_scale', 2.5)  # Get scale, default to 2.5
            
            self.logger.info(f"Import complete, saving files...")
            
            # Store current data
            self.current_pathway_id = pathway_id
            self.current_kgml = kgml_data
            self.current_pathway = parsed_pathway
            
            # Update preview
            self._update_preview(parsed_pathway)
            
            # Save files to project (so they're available later)
            saved_filepath = self._save_to_project(pathway_id, kgml_data, parsed_pathway, document_model, coordinate_scale)
            
            # Auto-load model into canvas if available
            # Note: self.model_canvas might be a loader, not a manager
            canvas_loader = None
            canvas_manager = None
            
            if self.model_canvas:
                if hasattr(self.model_canvas, 'get_current_model'):
                    # It's a loader - save reference and get current manager
                    canvas_loader = self.model_canvas
                    canvas_manager = canvas_loader.get_current_model()
                    self.logger.info(f"Auto-load: Detected canvas loader, current manager={canvas_manager is not None}")
                else:
                    # It's already a manager
                    canvas_manager = self.model_canvas
                    self.logger.info("Auto-load: Direct canvas manager provided")
            
            self.logger.info(f"Auto-load check: model_canvas={self.model_canvas is not None}, "
                           f"canvas_loader={canvas_loader is not None}, "
                           f"canvas_manager={canvas_manager is not None}, "
                           f"document_model={document_model is not None}, "
                           f"saved_filepath={saved_filepath is not None}")
            
            # For auto-load, we need the canvas_loader to create a new tab
            # (like File → Open does)
            if canvas_loader and document_model and saved_filepath:
                try:
                    self.logger.info("✓ Auto-loading imported model into new canvas tab...")
                    
                    import os
                    filename = os.path.basename(saved_filepath)
                    base_name = os.path.splitext(filename)[0]
                    
                    # UNIFIED APPROACH: Always create fresh canvas via add_document()
                    # This ensures IDENTICAL initialization to File→New and File→Open:
                    # - Fresh ModelCanvasManager
                    # - Proper controller wiring
                    # - Report Panel creation and registration
                    # - Callback setup
                    # Benefits: No reuse logic complexity, consistent behavior, no stale state
                    self.logger.info(f"Creating fresh canvas for KEGG import: {base_name}")
                    page_index, drawing_area = canvas_loader.add_document(filename=base_name)
                    canvas_manager = canvas_loader.get_canvas_manager(drawing_area)
                    
                    if not canvas_manager:
                        raise ValueError("Failed to get canvas manager after tab creation")
                    
                    # ===== UNIFIED OBJECT LOADING =====
                    # Use load_objects() for consistent initialization (same as File → Open)
                    canvas_manager.load_objects(
                        places=document_model.places,
                        transitions=document_model.transitions,
                        arcs=document_model.arcs
                    )
                    
                    # CRITICAL: Set change callback for proper state management
                    # (This is what File → Open does)
                    canvas_manager.document_controller.set_change_callback(
                        canvas_manager._on_object_changed
                    )
                    
                    # Set filepath and mark as clean (just imported/saved)
                    canvas_manager.set_filepath(saved_filepath)
                    canvas_manager.mark_clean()
                    
                    # Mark as imported (Canvas Health standard)
                    canvas_manager.mark_as_imported(base_name)
                    
                    # CRITICAL: Ensure callbacks are enabled before display
                    # (Should already be False from setup, but verify)
                    if hasattr(canvas_manager, '_suppress_callbacks'):
                        canvas_manager._suppress_callbacks = False
                        self.logger.info(f"Callbacks enabled: _suppress_callbacks={canvas_manager._suppress_callbacks}")
                    
                    # CRITICAL: Ensure simulation is reset BEFORE display operations
                    # This guarantees clean initial state and proper token display
                    if canvas_loader and hasattr(canvas_loader, '_ensure_simulation_reset'):
                        # Get the drawing_area for the canvas_manager we just loaded into
                        target_drawing_area = None
                        for da, mgr in canvas_loader.canvas_managers.items():
                            if mgr == canvas_manager:
                                target_drawing_area = da
                                break
                        
                        if target_drawing_area:
                            canvas_loader._ensure_simulation_reset(target_drawing_area)
                            self.logger.info("Simulation reset completed")
                        else:
                            self.logger.warning("Could not find drawing_area for simulation reset")
                    
                    # Fit to page to show entire model (with padding)
                    self.logger.info("Calling fit_to_page...")
                    canvas_manager.fit_to_page(
                        padding_percent=15,
                        deferred=True,
                        horizontal_offset_percent=30,
                        vertical_offset_percent=10
                    )
                    
                    # Force redraw to display loaded objects
                    self.logger.info("Calling mark_needs_redraw...")
                    canvas_manager.mark_needs_redraw()
                    
                    # REPORT PANEL: Trigger refresh after KEGG import (deferred)
                    # Use GLib.idle_add to ensure this happens AFTER tab switch completes
                    if drawing_area in canvas_loader.overlay_managers:
                        from gi.repository import GLib
                        
                        def refresh_report_panel():
                            """Deferred refresh to ensure tab switch completes first."""
                            overlay_manager = canvas_loader.overlay_managers.get(drawing_area)
                            if overlay_manager and hasattr(overlay_manager, 'report_panel_loader'):
                                report_panel_loader = overlay_manager.report_panel_loader
                                if report_panel_loader and hasattr(report_panel_loader, 'panel'):
                                    self.logger.info("Triggering Report Panel refresh after KEGG import (deferred)")
                                    simulation_controller = getattr(overlay_manager, 'simulation_controller', None)
                                    if simulation_controller and hasattr(report_panel_loader.panel, 'set_controller'):
                                        report_panel_loader.panel.set_controller(simulation_controller)
                                        self.logger.info("✅ Report Panel refreshed")
                            return False  # Don't repeat
                        
                        GLib.idle_add(refresh_report_panel)
                        self.logger.info("Report Panel refresh scheduled (idle)")
                    
                    self.logger.info(
                        f"Model auto-loaded: {len(document_model.places)} places, "
                        f"{len(document_model.transitions)} transitions, "
                        f"{len(document_model.arcs)} arcs (including test arcs)"
                    )
                    
                except Exception as e:
                    self.logger.error(f"Failed to auto-load model into canvas: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # Auto-load didn't happen - explain why
                if not canvas_loader:
                    self.logger.warning("Auto-load skipped: No canvas loader available (model_canvas might be a manager, not loader)")
                elif not document_model:
                    self.logger.warning("Auto-load skipped: No document_model")
                elif not saved_filepath:
                    self.logger.warning("Auto-load skipped: No saved_filepath")
            
            # Show success message
            auto_load_success = (canvas_loader is not None and document_model is not None and saved_filepath is not None)
            
            if saved_filepath:
                if auto_load_success:
                    # Auto-load happened
                    self._show_status(
                        f"✅ Model imported and loaded!\n"
                        f"Saved to: {saved_filepath}\n"
                        f"💡 Use mouse wheel to zoom, drag to pan"
                    )
                else:
                    # Auto-load didn't happen
                    self._show_status(
                        f"✅ Model saved to {saved_filepath}\n"
                        f"Use File → Open to load the model\n"
                        f"💡 Use View → Fit to Page (Ctrl+0) to see the entire model"
                    )
            else:
                self._show_status(
                    "✅ Import complete\n"
                    "Use File → Open to load the model"
                )
            
            # Refresh file tree to show new files
            if self.file_panel_loader and hasattr(self.file_panel_loader, 'file_explorer'):
                try:
                    if hasattr(self.file_panel_loader.file_explorer, '_load_current_directory'):
                        self.file_panel_loader.file_explorer._load_current_directory()
                        self.logger.info("File tree refreshed after import")
                except Exception as e:
                    self.logger.warning(f"Could not refresh file tree: {e}")
            
            # Re-enable button
            self.import_button.set_sensitive(True)
            self.import_in_progress = False
            
            # Notify parent panel (for BRENDA integration)
            imported_data = {
                'source': 'kegg',
                'pathway_id': pathway_id,
                'pathway': parsed_pathway,
                'model': document_model
            }
            self._on_import_complete(imported_data)
            
            # CRITICAL: Trigger callback for Report panel refresh
            # This must happen AFTER model is loaded to canvas (above)
            self._trigger_import_complete(imported_data)
            
        except Exception as e:
            self.logger.error(f"Failed to save import: {e}")
            import traceback
            traceback.print_exc()
            self._on_import_thread_error(e)
        
        return False  # Don't repeat
    
    def _on_import_thread_error(self, error):
        """Called in main thread when import encounters an error.
        
        Args:
            error: Exception object
        """
        self.import_button.set_sensitive(True)
        self.import_in_progress = False
        self._show_error(f"Import failed: {error}")
        self._on_import_error(error)
        return False  # Don't repeat
    
    def _update_preview(self, pathway):
        """Update preview text with comprehensive pathway information and metadata.
        
        Args:
            pathway: Parsed KEGG pathway object
        """
        if not pathway or not self.preview_text:
            return
        
        # Build comprehensive preview text
        lines = []
        
        # === BASIC INFORMATION ===
        lines.append("=== PATHWAY INFORMATION ===")
        lines.append(f"Name: {pathway.name}")
        lines.append(f"Title: {pathway.title or 'N/A'}")
        lines.append(f"Organism: {pathway.org}")
        lines.append(f"Number: {pathway.number}")
        lines.append("")
        
        # === CONTENT STATISTICS ===
        lines.append("=== CONTENT ===")
        lines.append(f"Total Entries: {len(pathway.entries)}")
        lines.append(f"Reactions: {len(pathway.reactions)}")
        lines.append(f"Relations: {len(pathway.relations)}")
        lines.append("")
        
        # Count entry types
        compounds = sum(1 for e in pathway.entries.values() if e.type == 'compound')
        genes = sum(1 for e in pathway.entries.values() if e.type == 'gene')
        enzymes = sum(1 for e in pathway.entries.values() if e.type == 'enzyme')
        maps = sum(1 for e in pathway.entries.values() if e.type == 'map')
        groups = sum(1 for e in pathway.entries.values() if e.type == 'group')
        
        lines.append(f"Entry Types:")
        lines.append(f"  Compounds: {compounds}")
        lines.append(f"  Genes: {genes}")
        lines.append(f"  Enzymes: {enzymes}")
        if maps > 0:
            lines.append(f"  Maps: {maps}")
        if groups > 0:
            lines.append(f"  Groups: {groups}")
        lines.append("")
        
        # === METADATA ===
        lines.append("=== METADATA ===")
        lines.append(f"Source: KEGG API")
        lines.append(f"Pathway ID: {pathway.name}")
        lines.append(f"Image Available: {pathway.image or 'No'}")
        lines.append(f"Link: {pathway.link or 'N/A'}")
        
        preview_text = "\n".join(lines)
        
        # Set text in TextView
        buffer = self.preview_text.get_buffer()
        buffer.set_text(preview_text)
    
    def _save_to_project(self, pathway_id, kgml_data, parsed_pathway, document_model, coordinate_scale=2.5):
        """Save imported pathway files to project.
        
        Saves:
        1. Raw KGML file to project/pathways/
        2. Converted .shy model to project/models/
        3. PathwayDocument metadata to project
        
        This follows the proven workflow: save files, then user opens via File → Open.
        This ensures complete canvas initialization (data_collector, plot panels, etc.)
        
        Args:
            pathway_id: KEGG pathway ID
            kgml_data: Raw KGML XML content
            parsed_pathway: Parsed KEGGPathway object
            document_model: Converted DocumentModel
            coordinate_scale: Coordinate scaling factor used in conversion
        
        Returns:
            str: Path to saved .shy file, or None if no project
        """
        if not self.project:
            self.logger.warning("No project available for saving")
            self._show_status(
                "❌ No project available. Please open or create a project first:\n"
                "File → New Project or File → Open Project",
                error=True
            )
            return None
        
        try:
            # 1. Save raw KGML file to project/pathways/
            kgml_filename = f"{pathway_id}.kgml"
            self.logger.info(f"Saving KGML file: {kgml_filename}")
            kgml_path = self.project.save_pathway_file(kgml_filename, kgml_data)
            self.logger.info(f"KGML saved to: {kgml_path}")
            
            # 2. Save .shy model file to project/models/
            pathway_name = parsed_pathway.title or parsed_pathway.name
            model_filename = f"{pathway_id}.shy"
            
            # Get models directory from project (creates if needed)
            models_dir = self.project.get_models_dir()
            if not models_dir:
                raise ValueError("Project models directory not available")
            
            os.makedirs(models_dir, exist_ok=True)
            model_filepath = os.path.join(models_dir, model_filename)
            
            self.logger.info(f"Saving model file: {model_filepath}")
            
            # Add metadata to help with viewport on load
            # KEGG models often have large coordinate ranges that need fit-to-page
            if not hasattr(document_model, 'metadata'):
                document_model.metadata = {}
            document_model.metadata['source'] = 'kegg_import'
            document_model.metadata['pathway_id'] = pathway_id
            document_model.metadata['requires_fit_to_page'] = True  # Signal to auto-fit on load
            document_model.metadata['coordinate_scale'] = coordinate_scale
            
            document_model.save_to_file(model_filepath)
            self.logger.info(f"Model saved successfully")
            
            # 3. Create PathwayDocument with metadata
            from shypn.data.pathway_document import PathwayDocument
            pathway_doc = PathwayDocument(
                source_type="kegg",
                source_id=pathway_id,
                source_organism=parsed_pathway.org,
                name=pathway_name
            )
            
            # Set file paths
            pathway_doc.raw_file = kgml_filename
            pathway_doc.model_file = model_filename
            
            # Add metadata notes
            pathway_doc.notes = f"KEGG pathway: {pathway_name}\n"
            pathway_doc.notes += f"Entries: {len(parsed_pathway.entries)}, "
            pathway_doc.notes += f"Reactions: {len(parsed_pathway.reactions)}, "
            pathway_doc.notes += f"Relations: {len(parsed_pathway.relations)}"
            
            # Link pathway to model
            if hasattr(document_model, 'id'):
                pathway_doc.link_to_model(document_model.id)
            
            # Register with project and save
            self.project.add_pathway(pathway_doc)
            self.project.save()
            
            self.logger.info(f"Pathway metadata saved to project")
            return model_filepath
            
        except Exception as save_error:
            import traceback
            traceback.print_exc()
            self._show_status(f"❌ Failed to save files: {save_error}", error=True)
            return None