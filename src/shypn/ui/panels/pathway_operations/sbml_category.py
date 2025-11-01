#!/usr/bin/env python3
"""SBML Category for Pathway Operations Panel.

This module provides the SBML import category within the Pathway Operations panel.
It handles:
  - Local file selection and BioModels fetching
  - SBML parsing and validation
  - Layout algorithm selection (auto/hierarchical/force-directed)
  - Post-processing (layout, colors, units)
  - Converting to Petri net and loading to canvas
  - Project integration and file tree refresh

Follows the CategoryFrame pattern used across all panels (Topology, Dynamic Analyses, Report).
"""
import os
import sys
import time
import threading
import logging
from typing import Optional

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f'ERROR: GTK3 not available in sbml_category: {e}', file=sys.stderr)
    sys.exit(1)

from .base_pathway_category import BasePathwayCategory

# Import SBML backend modules
try:
    from shypn.data.pathway.sbml_parser import SBMLParser
    from shypn.data.pathway.pathway_validator import PathwayValidator
    from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
    from shypn.data.pathway.pathway_converter import PathwayConverter
    from shypn.data.pathway_document import PathwayDocument
except ImportError as e:
    print(f'Warning: SBML backend not available: {e}', file=sys.stderr)
    SBMLParser = None
    PathwayValidator = None
    PathwayPostProcessor = None
    PathwayConverter = None
    PathwayDocument = None


class SBMLCategory(BasePathwayCategory):
    """SBML import category for Pathway Operations panel.
    
    Provides complete SBML import workflow with local file and BioModels support.
    Inherits threading, status, and project integration from BasePathwayCategory.
    
    Attributes:
        parser: SBMLParser for parsing SBML files
        validator: PathwayValidator for validating pathway data
        converter: PathwayConverter for converting to Petri net
        current_filepath: Currently selected SBML file path
        parsed_pathway: Parsed PathwayData from SBML file
        processed_pathway: Post-processed PathwayData with layout
    """
    
    def __init__(self, workspace_settings=None, parent_window=None):
        """Initialize SBML category.
        
        Args:
            workspace_settings: Optional WorkspaceSettings for last query
            parent_window: Optional parent window for dialogs (Wayland fix)
        """
        # Set attributes BEFORE calling super().__init__()
        # because _build_content() is called during super().__init__()
        self.workspace_settings = workspace_settings
        self.parent_window = parent_window
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize backend components
        if SBMLParser and PathwayValidator and PathwayConverter:
            self.parser = SBMLParser()
            self.validator = PathwayValidator()
            self.converter = PathwayConverter()
        else:
            self.parser = None
            self.validator = None
            self.converter = None
            print("Warning: SBML import backend not available", file=sys.stderr)
        
        # Current state
        self.current_filepath = None
        self.parsed_pathway = None
        self.processed_pathway = None
        self.current_pathway_doc = None
        
        # Workflow flags
        self._import_button_flow = False
        self._fetch_in_progress = False
        
        # Now call super().__init__() which will call _build_content()
        super().__init__(category_name="SBML")
    
    def _build_content(self) -> Gtk.Widget:
        """Build the SBML category content with unified interface.
        
        Returns:
            Gtk.Box containing all SBML import UI elements
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
        preview_box = self._build_preview_section()
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
        
        main_box.show_all()
        
        # Load last BioModels query
        self._load_last_biomodels_query()
        
        # Update UI state based on project availability
        # This must happen after widgets are created
        GLib.idle_add(self._update_ui_for_project_state)
        
        return main_box
    
    def _build_source_selection(self) -> Gtk.Box:
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
        
        self.local_radio = Gtk.RadioButton(label="Local File")
        self.local_radio.set_active(True)
        self.local_radio.connect('toggled', self._on_mode_changed)
        radio_box.pack_start(self.local_radio, False, False, 0)
        
        self.biomodels_radio = Gtk.RadioButton(group=self.local_radio, label="Remote (BioModels)")
        self.biomodels_radio.connect('toggled', self._on_mode_changed)
        radio_box.pack_start(self.biomodels_radio, False, False, 0)
        
        box.pack_start(radio_box, False, False, 0)
        
        return box
    
    def _build_accession_input(self) -> Gtk.Box:
        """Build accession number input section.
        
        Returns:
            Gtk.Box: Accession input widgets
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label()
        label.set_markup("<b>Accession Number:</b>")
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)
        
        self.file_entry = Gtk.Entry()
        self.file_entry.set_placeholder_text("Path to SBML file or BioModels ID")
        self.file_entry.connect('changed', self._on_file_entry_changed)
        box.pack_start(self.file_entry, False, False, 0)
        
        # Help text that changes based on mode
        self.source_info = Gtk.Label()
        self.source_info.set_markup(
            '<span size="small">Enter full path to local SBML file (.sbml or .xml)</span>'
        )
        self.source_info.set_xalign(0)
        self.source_info.get_style_context().add_class("dim-label")
        self.source_info.set_line_wrap(True)
        box.pack_start(self.source_info, False, False, 0)
        
        return box
    
    def _build_options(self) -> Gtk.Box:
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
        
        return box
        

    
    def _build_preview_section(self) -> Gtk.Widget:
        """Build preview text view."""
        frame = Gtk.Frame()
        frame.set_label("Preview")
        
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
        
        # Set initial placeholder text
        buffer = self.preview_text.get_buffer()
        buffer.set_text(
            "Model information will appear here after import...\n\n"
            "The preview will show:\n"
            "• Model name and organism\n"
            "• Number of species and reactions\n"
            "• Compartments and metadata"
        )
        
        scrolled.add(self.preview_text)
        
        frame.add(scrolled)
        return frame
    
    # Event handlers
    
    def _on_mode_changed(self, radio_button):
        """Handle mode radio button changes."""
        if not radio_button.get_active():
            return
        
        if self.local_radio.get_active():
            # Local mode
            self.file_entry.set_placeholder_text("Path to SBML file")
            self.source_info.set_markup(
                '<span size="small">Enter full path to local SBML file (.sbml or .xml)</span>'
            )
        else:
            # BioModels mode
            self.file_entry.set_placeholder_text("BioModels ID (e.g., BIOMD0000000001)")
            self.source_info.set_markup(
                '<span size="small">Enter a <a href="https://www.ebi.ac.uk/biomodels/">BioModels</a> ID</span>'
            )
    
    def _on_file_entry_changed(self, entry):
        """Handle accession entry text changes."""
        text = entry.get_text().strip()
        
        if self.local_radio.get_active():
            # Local mode - check if file exists
            self.import_button.set_sensitive(bool(text and os.path.exists(text)))
        else:
            # BioModels mode - check if ID is not empty
            self.import_button.set_sensitive(len(text) > 0)
        
        # Also check project state
        if not self.project:
            self.import_button.set_sensitive(False)
    
    def _update_ui_for_project_state(self):
        """Update UI based on project availability.
        
        Disables import button and shows guidance message if no project.
        """
        if self.project:
            # Project available - enable button if input is valid
            text = self.file_entry.get_text().strip()
            if self.local_radio.get_active():
                self.import_button.set_sensitive(bool(text and os.path.exists(text)))
            else:
                self.import_button.set_sensitive(len(text) > 0)
            self._show_status("Ready to import SBML")
        else:
            # No project - disable button and show guidance
            self.import_button.set_sensitive(False)
            self._show_status(
                "⚠️ Please open or create a project first (File → New Project or File → Open Project)\n"
                "A project is required to save imported pathways.",
                error=True
            )
    
    def _on_import_clicked(self, button):
        """Handle Save to Project button click.
        
        Unified workflow for both Local and BioModels:
        1. Get filepath or BioModels ID
        2. If BioModels, fetch first (background thread)
        3. Parse SBML
        4. Convert to Petri net
        5. Save to project/models/
        
        Args:
            button: The clicked button widget
        """
        if not self.project:
            self._show_error(
                "No project available. Please open or create a project first:\n"
                "File → New Project or File → Open Project"
            )
            return
        
        text = self.file_entry.get_text().strip()
        if not text:
            self._show_error("Please enter a file path or BioModels ID")
            return
        
        # Disable button during import
        self.import_button.set_sensitive(False)
        
        if self.local_radio.get_active():
            # Local file - process directly
            if not os.path.exists(text):
                self._show_error(f"File not found: {text}")
                self.import_button.set_sensitive(True)
                return
            
            self._show_status(f"Processing {os.path.basename(text)}...")
            self._process_sbml_file(text)
        else:
            # BioModels - fetch first
            biomodels_id = text
            self._show_status(f"Fetching {biomodels_id} from BioModels...")
            self._fetch_biomodels(biomodels_id)
    
    def _process_sbml_file(self, filepath: str):
        """Process a local SBML file in background thread.
        
        Args:
            filepath: Path to SBML file
        """
        def parse_and_convert():
            try:
                self.logger.info(f"Parsing SBML file: {filepath}")
                
                # 1. Parse SBML → PathwayData
                parsed_pathway = self.parser.parse_file(filepath)
                
                # 2. Post-process → ProcessedPathwayData
                self.logger.info("Post-processing pathway data...")
                postprocessor = PathwayPostProcessor(scale_factor=1.0)
                processed_pathway = postprocessor.process(parsed_pathway)
                
                # 3. Convert to Petri net → DocumentModel
                self.logger.info("Converting to Petri net...")
                document_model = self.converter.convert(processed_pathway)
                
                return {
                    'filepath': filepath,
                    'parsed_pathway': processed_pathway,
                    'document_model': document_model
                }
                
            except Exception as e:
                self.logger.error(f"SBML processing failed: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Run in background thread
        self._run_in_thread(
            parse_and_convert,
            on_complete=self._on_sbml_import_complete,
            on_error=self._on_sbml_import_error
        )
    
    def _fetch_biomodels(self, biomodels_id: str):
        """Fetch model from BioModels in background thread.
        
        Args:
            biomodels_id: BioModels accession ID
        """
        def fetch():
            try:
                import urllib.request
                import urllib.error
                import tempfile
                
                urls = [
                    f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}_url.xml",
                    f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}.xml",
                    f"https://www.ebi.ac.uk/biomodels-main/download?mid={biomodels_id}",
                ]
                
                # Save to temp location
                dest_path = os.path.join(tempfile.gettempdir(), f"{biomodels_id}.xml")
                
                # Try URLs in order
                success = False
                last_error = None
                
                for url in urls:
                    try:
                        self.logger.debug(f"Trying URL: {url}")
                        urllib.request.urlretrieve(url, dest_path)
                        
                        # Verify it's XML
                        with open(dest_path, 'r', encoding='utf-8') as f:
                            content = f.read(100)
                            if '<' in content and 'xml' in content.lower():
                                success = True
                                break
                    except Exception as e:
                        last_error = e
                        continue
                
                if not success:
                    error_msg = f"Could not fetch {biomodels_id}"
                    if last_error:
                        error_msg += f": {last_error}"
                    raise ValueError(error_msg)
                
                return {'biomodels_id': biomodels_id, 'filepath': dest_path}
                
            except Exception as e:
                self.logger.error(f"BioModels fetch failed: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Run in background thread
        self._run_in_thread(
            fetch,
            on_complete=self._on_biomodels_fetch_complete,
            on_error=self._on_sbml_import_error
        )
    
    def _on_biomodels_fetch_complete(self, result):
        """Called after BioModels fetch completes - now process the file.
        
        Args:
            result: Dict with biomodels_id and filepath
        """
        biomodels_id = result['biomodels_id']
        filepath = result['filepath']
        
        self._save_biomodels_query(biomodels_id)
        self._show_status(f"Processing {biomodels_id}...")
        
        # Now process the downloaded file
        self._process_sbml_file(filepath)
    
    def _on_sbml_import_complete(self, result):
        """Called in main thread after SBML import completes successfully.
        
        Args:
            result: Dict with import results
        """
        try:
            filepath = result['filepath']
            parsed_pathway = result['parsed_pathway']
            document_model = result['document_model']
            
            self.logger.info(f"SBML import complete, saving files...")
            self.logger.info(f"Pathway type: {type(parsed_pathway)}")
            
            # Save files to project FIRST
            saved_filepath = self._save_to_project(filepath, parsed_pathway, document_model)
            
            if not saved_filepath:
                self._show_error("Failed to save files to project")
                self.import_button.set_sensitive(True)
                return
            
            # Update preview AFTER save succeeds
            try:
                self._update_preview(parsed_pathway)
                self.logger.info("Preview updated successfully")
            except Exception as preview_error:
                self.logger.error(f"Failed to update preview: {preview_error}")
                import traceback
                traceback.print_exc()
            
            # ===== AUTO-LOAD MODEL TO CANVAS =====
            # Load the saved model into canvas automatically (same as KEGG import)
            try:
                from shypn.helpers.model_canvas_loader import ModelCanvasLoader
                canvas_loader = self.app_window.canvas_loader
                
                # Get base name for tab
                base_name = os.path.splitext(os.path.basename(saved_filepath))[0]
                
                # Check if current tab is empty and can be reused
                current_drawing_area = canvas_loader.get_current_drawing_area()
                current_manager = None
                if current_drawing_area:
                    current_manager = canvas_loader.get_canvas_manager(current_drawing_area)
                
                canvas_manager = None
                
                # If current tab is empty, reuse it
                if current_manager and current_manager.is_empty():
                    canvas_manager = current_manager
                    self.logger.info("Reusing empty tab for SBML import")
                    # CRITICAL: Reset manager state before loading
                    canvas_loader._reset_manager_for_load(canvas_manager, base_name)
                else:
                    # Create new tab
                    self.logger.info("Creating new tab for SBML import")
                    page_index, drawing_area = canvas_loader.add_document(filename=base_name)
                    canvas_manager = canvas_loader.get_canvas_manager(drawing_area)
                
                if not canvas_manager:
                    raise ValueError("Failed to get canvas manager after tab creation")
                
                # Load objects using UNIFIED path (same as KEGG and File→Open)
                canvas_manager.load_objects(
                    places=document_model.places,
                    transitions=document_model.transitions,
                    arcs=document_model.arcs
                )
                
                # Set change callback for proper state management
                canvas_manager.document_controller.set_change_callback(
                    canvas_manager._on_object_changed
                )
                
                # Set filepath and mark as clean (just imported/saved)
                canvas_manager.set_filepath(saved_filepath)
                canvas_manager.mark_clean()
                
                # Mark as imported
                canvas_manager.mark_as_imported(base_name)
                
                # Fit to page to show entire model (with padding)
                canvas_manager.fit_to_page(
                    padding_percent=15,
                    deferred=True,
                    horizontal_offset_percent=30,
                    vertical_offset_percent=10
                )
                
                # Force redraw
                if hasattr(canvas_manager, 'drawing_area'):
                    canvas_manager.drawing_area.queue_draw()
                
                self._show_status(
                    f"✅ Model loaded to canvas: {base_name}\n"
                    f"💡 Use View → Fit to Page (Ctrl+0) to adjust view if needed"
                )
                
            except Exception as load_error:
                self.logger.error(f"Failed to auto-load model to canvas: {load_error}")
                import traceback
                traceback.print_exc()
                # Show fallback message
                self._show_status(
                    f"✅ Model saved to {saved_filepath}\n"
                    f"⚠️ Auto-load failed, use File → Open to load manually\n"
                    f"💡 Use View → Fit to Page (Ctrl+0) to see the entire model"
                )
            
            # Re-enable button
            self.import_button.set_sensitive(True)
            
        except Exception as e:
            self.logger.error(f"Post-import processing failed: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(f"Import failed: {e}")
            self.import_button.set_sensitive(True)
    
    def _on_sbml_import_error(self, error):
        """Called in main thread if SBML import fails.
        
        Args:
            error: The exception that occurred
        """
        self.logger.error(f"SBML import error: {error}")
        self._show_error(f"Import failed: {error}")
        self.import_button.set_sensitive(True)
    
    def _on_fetch_complete(self, filepath: str, biomodels_id: str):
        """Callback when fetch completes successfully."""
        self._fetch_in_progress = False
        self.fetch_button.set_sensitive(True)
        
        self.current_filepath = filepath
        self.parsed_pathway = None
        self.processed_pathway = None
        
        self._show_status(f"Fetched {biomodels_id} successfully", error=False)
        
        # Auto-continue to parse
        if self._import_button_flow:
            self._on_parse_clicked(None)
        else:
            # Just enable import button
            self.import_button.set_sensitive(True)
    
    def _on_fetch_error(self, error_msg: str):
        """Callback when fetch fails."""
        self._fetch_in_progress = False
        self.fetch_button.set_sensitive(True)
        self.import_button.set_sensitive(False)
        self._show_status(error_msg, error=True)
    
    def _on_parse_clicked(self, button):
        """Handle parse button click (or auto-called from browse/fetch)."""
        if not self.parser or not self.validator:
            self._show_status("SBML backend not available", error=True)
            return
        
        if not self.current_filepath:
            self._show_status("No file selected", error=True)
            return
        
        self._show_status("Parsing SBML file...")
        
        # Run parse in background thread
        self._run_in_thread(
            task_func=self._parse_and_process,
            on_complete=self._on_parse_complete,
            on_error=self._on_parse_error
        )
    
    def _parse_and_process(self):
        """Background task to parse and process SBML file."""
        # Parse SBML
        pathway_data = self.parser.parse_file(self.current_filepath)
        
        # Validate (returns ValidationResult object, not dict)
        validation_result = self.validator.validate(pathway_data)
        if not validation_result.is_valid:
            raise ValueError(f"Validation failed: {', '.join(validation_result.errors)}")
        
        # Get layout options
        algorithm = self.layout_combo.get_active_id()
        
        layout_options = {}
        if algorithm == "hierarchical":
            layout_options = {
                'algorithm': 'hierarchical',
                'layer_spacing': self.layer_spacing_spin.get_value(),
                'node_spacing': self.node_spacing_spin.get_value()
            }
        elif algorithm == "force_directed":
            layout_options = {
                'algorithm': 'force_directed',
                'iterations': int(self.iterations_spin.get_value()),
                'k_factor': self.k_factor_spin.get_value(),
                'canvas_scale': self.canvas_scale_spin.get_value()
            }
        else:
            layout_options = {'algorithm': 'auto'}
        
        # Post-process (assigns arbitrary positions, Swiss Palette will handle real layout)
        postprocessor = PathwayPostProcessor()
        processed_pathway = postprocessor.process(pathway_data)
        
        return {
            'parsed': pathway_data,
            'processed': processed_pathway
        }
    
    def _on_parse_complete(self, result):
        """Callback when parse completes successfully."""
        self.parsed_pathway = result['parsed']
        self.processed_pathway = result['processed']
        
        # Update preview
        preview = self._generate_preview(self.parsed_pathway)
        buffer = self.preview_text.get_buffer()
        buffer.set_text(preview)
        
        self._show_status("Parsed successfully. Ready to import.", error=False)
        self.import_button.set_sensitive(True)
        
        # Auto-continue to import if in unified flow
        if self._import_button_flow:
            self._load_to_canvas()
    
    def _on_parse_error(self, error):
        """Callback when parse fails."""
        self._show_status(f"Parse failed: {error}", error=True)
        self.import_button.set_sensitive(False)
    
    def _save_to_project(self, filepath: str, parsed_pathway, doc_model):
        """Save imported pathway to project.
        
        Saves:
        1. Copy SBML file to project/pathways/
        2. Save .shy model to project/models/
        3. Create PathwayDocument metadata
        
        This follows the proven workflow: save files, then user opens via File → Open.
        This ensures complete canvas initialization (data_collector, plot panels, etc.)
        
        Args:
            filepath: Path to original SBML file
            parsed_pathway: Parsed pathway data
            doc_model: Document model to save
        
        Returns:
            str: Absolute path to the saved .shy file, or None if save failed
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
            filename = os.path.basename(filepath)
            base_name = os.path.splitext(filename)[0]
            
            # 1. Copy SBML file to project/pathways/
            pathways_dir = self.project.get_pathways_dir()
            if not pathways_dir:
                raise ValueError("Project pathways directory not available")
            
            os.makedirs(pathways_dir, exist_ok=True)
            dest_sbml_path = os.path.join(pathways_dir, filename)
            
            # Always copy/overwrite the SBML file to project
            if filepath and os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        sbml_content = f.read()
                    
                    with open(dest_sbml_path, 'w', encoding='utf-8') as f:
                        f.write(sbml_content)
                    
                    self.logger.info(f"SBML file saved to: {dest_sbml_path}")
                except Exception as copy_error:
                    self.logger.error(f"Failed to copy SBML file: {copy_error}")
                    raise ValueError(f"Could not save SBML file: {copy_error}")
            else:
                raise ValueError(f"Source file not found: {filepath}")
            
            # 2. Save .shy model file to project/models/
            model_filename = f"{base_name}.shy"
            models_dir = self.project.get_models_dir()
            if not models_dir:
                raise ValueError("Project models directory not available")
            
            os.makedirs(models_dir, exist_ok=True)
            model_filepath = os.path.join(models_dir, model_filename)
            
            self.logger.info(f"Saving model file: {model_filepath}")
            
            # Add metadata to help with viewport on load
            # SBML models may have varying coordinate ranges that benefit from fit-to-page
            if not hasattr(doc_model, 'metadata'):
                doc_model.metadata = {}
            doc_model.metadata['source'] = 'sbml_import'
            doc_model.metadata['original_file'] = filename
            doc_model.metadata['requires_fit_to_page'] = True  # Signal to auto-fit on load
            
            doc_model.save_to_file(model_filepath)
            self.logger.info(f"Model saved successfully to: {model_filepath}")
            
            # Verify the file was created
            if not os.path.exists(model_filepath):
                raise ValueError(f"Model file was not created: {model_filepath}")
            
            self.logger.info(f"Verified model file exists: {os.path.getsize(model_filepath)} bytes")
            
            # 3. Create PathwayDocument with metadata
            from shypn.data.pathway_document import PathwayDocument
            
            # Get organism from metadata
            organism = "Unknown"
            if parsed_pathway:
                if hasattr(parsed_pathway, 'organism'):
                    organism = parsed_pathway.organism or "Unknown"
                elif isinstance(parsed_pathway, dict) and 'organism' in parsed_pathway:
                    organism = parsed_pathway.get('organism', "Unknown")
            
            # Get pathway name
            pathway_name = base_name
            if parsed_pathway:
                if hasattr(parsed_pathway, 'name'):
                    pathway_name = parsed_pathway.name or base_name
                elif isinstance(parsed_pathway, dict) and 'name' in parsed_pathway:
                    pathway_name = parsed_pathway.get('name', base_name)
            
            pathway_doc = PathwayDocument(
                source_type="sbml",
                source_id=base_name,
                source_organism=organism,
                name=pathway_name
            )
            
            # Set file paths
            pathway_doc.raw_file = filename
            pathway_doc.model_file = model_filename
            
            # Add notes with pathway statistics
            notes_parts = [f"SBML model: {pathway_name}"]
            if parsed_pathway:
                if isinstance(parsed_pathway, dict):
                    species_count = len(parsed_pathway.get('species', []))
                    reactions_count = len(parsed_pathway.get('reactions', []))
                else:
                    species_count = len(getattr(parsed_pathway, 'species', []))
                    reactions_count = len(getattr(parsed_pathway, 'reactions', []))
                notes_parts.append(f"Species: {species_count}, Reactions: {reactions_count}")
            pathway_doc.notes = "\n".join(notes_parts)
            
            # Link pathway to model
            if hasattr(doc_model, 'id'):
                pathway_doc.link_to_model(doc_model.id)
            
            # Register with project and save
            self.project.add_pathway(pathway_doc)
            self.project.save()
            
            self.logger.info(f"Pathway metadata saved to project")
            self.logger.info(f"Files saved - SBML: {dest_sbml_path}, Model: {model_filepath}")
            
            # Verify both files exist
            if not os.path.exists(dest_sbml_path):
                self.logger.error(f"SBML file missing after save: {dest_sbml_path}")
            if not os.path.exists(model_filepath):
                self.logger.error(f"Model file missing after save: {model_filepath}")
            
            return model_filepath
            
        except Exception as save_error:
            import traceback
            traceback.print_exc()
            self._show_status(f"❌ Failed to save files: {save_error}", error=True)
            return None
    
    def _generate_preview(self, pathway_data) -> str:
        """Generate preview text from pathway data.
        
        Args:
            pathway_data: PathwayData object or dict with pathway information
        """
        if not pathway_data:
            return "No data"
        
        lines = []
        
        # Handle both PathwayData objects and dicts
        if hasattr(pathway_data, 'metadata'):
            # PathwayData object
            name = pathway_data.metadata.get('name', 'Unnamed')
            source = pathway_data.metadata.get('source', 'SBML')
            species = pathway_data.species
            reactions = pathway_data.reactions
        elif isinstance(pathway_data, dict):
            # Dictionary format
            name = pathway_data.get('name', 'Unnamed')
            source = pathway_data.get('source', 'SBML')
            species = pathway_data.get('species', [])
            reactions = pathway_data.get('reactions', [])
        else:
            return "Invalid data format"
        
        lines.append(f"Name: {name}")
        lines.append(f"Source: {source}")
        lines.append("")
        lines.append(f"Species: {len(species)}")
        lines.append(f"Reactions: {len(reactions)}")
        lines.append("")
        
        if species:
            lines.append("Sample species:")
            for s in list(species)[:5]:
                # Handle both Species objects and dicts
                if hasattr(s, 'name'):
                    species_name = s.name or s.id
                elif isinstance(s, dict):
                    species_name = s.get('name', s.get('id', 'Unknown'))
                else:
                    species_name = str(s)
                lines.append(f"  - {species_name}")
            if len(species) > 5:
                lines.append(f"  ... and {len(species) - 5} more")
        
        return "\n".join(lines)
    
    def _update_preview(self, pathway):
        """Update preview with comprehensive pathway information.
        
        Args:
            pathway: PathwayData object from parser
        """
        def do_update():
            try:
                if not pathway:
                    buffer = self.preview_text.get_buffer()
                    buffer.set_text("No pathway data available")
                    return False
                
                lines = []
                
                # Debug: Log what we received
                self.logger.debug(f"Preview pathway type: {type(pathway)}")
                self.logger.debug(f"Preview pathway dir: {dir(pathway)[:10]}...")  # First 10 attributes
                
                # === PATHWAY INFORMATION ===
                lines.append("=== PATHWAY INFORMATION ===")
                
                # Try multiple ways to get name/ID
                name = None
                if hasattr(pathway, 'name'):
                    name = pathway.name
                elif hasattr(pathway, 'id'):
                    name = pathway.id
                elif hasattr(pathway, 'model_name'):
                    name = pathway.model_name
                elif isinstance(pathway, dict):
                    name = pathway.get('name') or pathway.get('id') or pathway.get('model_name')
                
                lines.append(f"Name: {name or 'Unknown'}")
                
                # Organism (if available)
                organism = None
                if hasattr(pathway, 'organism'):
                    organism = pathway.organism
                elif isinstance(pathway, dict):
                    organism = pathway.get('organism')
                
                if organism:
                    lines.append(f"Organism: {organism}")
                
                # Model ID (for BioModels)
                model_id = None
                if hasattr(pathway, 'model_id'):
                    model_id = pathway.model_id
                elif isinstance(pathway, dict):
                    model_id = pathway.get('model_id')
                
                if model_id:
                    lines.append(f"Model ID: {model_id}")
                
                lines.append("")
                
                # === CONTENT STATISTICS ===
                lines.append("=== CONTENT STATISTICS ===")
                
                # Species
                species = []
                if hasattr(pathway, 'species'):
                    species = pathway.species or []
                elif isinstance(pathway, dict):
                    species = pathway.get('species', [])
                
                lines.append(f"Species: {len(species)}")
                
                # Reactions
                reactions = []
                if hasattr(pathway, 'reactions'):
                    reactions = pathway.reactions or []
                elif isinstance(pathway, dict):
                    reactions = pathway.get('reactions', [])
                
                lines.append(f"Reactions: {len(reactions)}")
                
                # Compartments (if available)
                compartments = []
                if hasattr(pathway, 'compartments'):
                    compartments = pathway.compartments or []
                elif isinstance(pathway, dict):
                    compartments = pathway.get('compartments', [])
                
                if compartments:
                    lines.append(f"Compartments: {len(compartments)}")
                
                lines.append("")
                
                # === ENTRY TYPES ===
                lines.append("=== ENTRY TYPES ===")
                
                # Breakdown by type if available
                if species:
                    # Count by type if species have types
                    type_counts = {}
                    for s in species:
                        stype = None
                        if hasattr(s, 'type'):
                            stype = s.type
                        elif isinstance(s, dict):
                            stype = s.get('type')
                        
                        if stype:
                            type_counts[stype] = type_counts.get(stype, 0) + 1
                    
                    if type_counts:
                        for stype, count in sorted(type_counts.items()):
                            lines.append(f"  {stype}: {count}")
                    else:
                        lines.append(f"  Total Species: {len(species)}")
                
                if reactions:
                    lines.append(f"  Total Reactions: {len(reactions)}")
                
                lines.append("")
                
                # === METADATA ===
                lines.append("=== METADATA ===")
                lines.append(f"Source: SBML File")
                
                # Notes (if available)
                notes = None
                if hasattr(pathway, 'notes'):
                    notes = pathway.notes
                elif isinstance(pathway, dict):
                    notes = pathway.get('notes')
                
                if notes:
                    # Truncate long notes
                    notes_str = str(notes)[:200]
                    if len(str(notes)) > 200:
                        notes_str += "..."
                    lines.append(f"Notes: {notes_str}")
                
                preview_text = "\n".join(lines)
                
                self.logger.info(f"Preview text generated: {len(preview_text)} characters")
                
                # Set text in TextView
                buffer = self.preview_text.get_buffer()
                buffer.set_text(preview_text)
                
                self.logger.info("Preview buffer updated")
                
            except Exception as e:
                self.logger.error(f"Error updating preview: {e}")
                import traceback
                traceback.print_exc()
                buffer = self.preview_text.get_buffer()
                buffer.set_text(f"Error updating preview: {e}")
            
            return False  # Don't repeat
        
        # Execute on main thread
        GLib.idle_add(do_update)
    
    def _show_status(self, message: str, error: bool = False):
        """Update status label (Wayland-safe)."""
        def update():
            if error:
                self.status_label.set_markup(f"<span foreground='red'>{message}</span>")
            else:
                self.status_label.set_markup(f"<span foreground='gray'>{message}</span>")
        
        GLib.idle_add(update)
    
    def _load_last_biomodels_query(self):
        """Load last BioModels query from settings."""
        if not self.workspace_settings:
            return
        
        try:
            last_query = self.workspace_settings.get_setting("sbml_import.last_biomodels_id", "")
            if last_query:
                # Note: biomodels_entry no longer exists in unified interface
                # Just log for debugging
                self.logger.debug(f"Loaded last BioModels query: {last_query}")
        except Exception as e:
            self.logger.warning(f"Could not load last BioModels query: {e}")
    
    def _save_biomodels_query(self, biomodels_id: str):
        """Save BioModels query to settings."""
        if not self.workspace_settings:
            return
        
        try:
            self.workspace_settings.set_setting("sbml_import.last_biomodels_id", biomodels_id)
            self.logger.debug(f"Saved BioModels query: {biomodels_id}")
        except Exception as e:
            self.logger.warning(f"Could not save BioModels query: {e}")
    
    def _show_error(self, message: str):
        """Show error message in status label.
        
        Args:
            message: Error message to display
        """
        self._show_status(f"❌ {message}", error=True)
    
    def _show_progress(self, message: str):
        """Show progress message in status label.
        
        Args:
            message: Progress message to display
        """
        self._show_status(f"⏳ {message}", error=False)
    
    def set_parent_window(self, parent_window):
        """Set parent window for dialogs (Wayland compatibility).
        
        Args:
            parent_window: Gtk.Window or Gtk.ApplicationWindow to use as parent
        """
        self.parent_window = parent_window
        self.logger.debug(f"Parent window set: {parent_window}")
