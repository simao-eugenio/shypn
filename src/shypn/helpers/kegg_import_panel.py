#!/usr/bin/env python3
"""KEGG Import Panel Controller.

This module provides the controller for the KEGG Import tab within the Pathway panel.
It handles:
  - Fetching pathways from KEGG API
  - Parsing KGML data
  - Converting to Petri net (DocumentModel)
  - Loading into canvas

This follows the MVC pattern:
  - Model: KEGGAPIClient + KGMLParser + PathwayConverter (business logic)
  - View: pathway_panel.ui Import tab (GTK XML)
  - Controller: KEGGImportPanel (this file)
"""
import os
import sys
import logging
import threading
from typing import Optional

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f'ERROR: GTK3 not available in kegg_import_panel: {e}', file=sys.stderr)
    sys.exit(1)

# Import KEGG backend modules
try:
    from shypn.importer.kegg import KEGGAPIClient, KGMLParser, PathwayConverter
except ImportError as e:
    print(f'Warning: KEGG importer not available: {e}', file=sys.stderr)
    KEGGAPIClient = None
    KGMLParser = None
    PathwayConverter = None


class KEGGImportPanel:
    """Controller for KEGG import functionality.
    
    Connects KEGG import API (model) to GTK UI (view).
    Does NOT create widgets - only gets references and connects signals.
    
    Attributes:
        builder: GTK Builder instance (UI references)
        model_canvas: ModelCanvasManager for loading imported pathways
        project: Current Project instance for pathway metadata tracking
        api_client: KEGGAPIClient for fetching pathways
        parser: KGMLParser for parsing KGML XML
        converter: PathwayConverter for converting to Petri net
        current_pathway: Currently fetched pathway data (KEGGPathway)
        current_pathway_doc: PathwayDocument for current import
    """
    
    def __init__(self, builder: Gtk.Builder, model_canvas=None, project=None):
        """Initialize the KEGG import panel controller.
        
        Args:
            builder: GTK Builder with loaded pathway_panel.ui
            model_canvas: Optional ModelCanvasManager for loading pathways
            project: Optional Project instance for metadata tracking
        """
        self.builder = builder
        self.model_canvas = model_canvas
        self.project = project
        self.file_panel_loader = None  # Will be set by main app to enable file tree refresh
        
        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize backend components
        if KEGGAPIClient and KGMLParser and PathwayConverter:
            self.api_client = KEGGAPIClient()
            self.parser = KGMLParser()
            self.converter = PathwayConverter()
        else:
            self.api_client = None
            self.parser = None
            self.converter = None
            print("Warning: KEGG import backend not available", file=sys.stderr)
        
        # Current pathway data
        self.current_pathway = None
        self.current_kgml = None
        self.current_pathway_id = None  # Store pathway ID for later saving
        self.current_pathway_doc = None  # PathwayDocument for metadata tracking
        
        # Callback for notifying parent (PathwayOperationsPanel) when import completes
        self.import_complete_callback = None
        
        # Lazy loading: store canvas info for later model injection
        self._pending_canvas_info = None
        
        # Get widget references
        self._get_widgets()
        
        # Connect signals
        self._connect_signals()
    
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
        # Input widgets
        self.pathway_id_entry = self.builder.get_object('pathway_id_entry')
        self.organism_combo = self.builder.get_object('organism_combo')
        
        # Options widgets
        self.filter_cofactors_check = self.builder.get_object('filter_cofactors_check')
        self.scale_spin = self.builder.get_object('scale_spin')
        self.include_relations_check = self.builder.get_object('include_relations_check')
        
        # Enhancement options widgets
        self.enhancement_layout_check = self.builder.get_object('enhancement_layout_check')
        self.enhancement_arcs_check = self.builder.get_object('enhancement_arcs_check')
        self.enhancement_metadata_check = self.builder.get_object('enhancement_metadata_check')
        
        # Preview and status
        self.preview_text = self.builder.get_object('preview_text')
        self.import_status_label = self.builder.get_object('import_status_label')
        
        # Action buttons
        # Note: fetch_button removed in unified flow - only kegg_import_button exists
        self.fetch_button = None  # Legacy - no longer in UI
        self.import_button = self.builder.get_object('kegg_import_button')
    
    def _connect_signals(self):
        """Connect widget signals to handlers."""
        if self.fetch_button:
            self.fetch_button.connect('clicked', self._on_fetch_clicked)
        
        if self.import_button:
            self.import_button.connect('clicked', self._on_import_clicked)
        
        # Enable import button when pathway ID is entered
        if self.pathway_id_entry:
            self.pathway_id_entry.connect('changed', self._on_pathway_id_changed)
    
    def set_model_canvas(self, model_canvas):
        """Set or update the model canvas for loading imported pathways.
        
        Args:
            model_canvas: ModelCanvasManager instance
        """
        self.model_canvas = model_canvas
    
    def _on_pathway_id_changed(self, entry):
        """Handle pathway ID entry changes."""
        # Could enable fetch button when ID is valid
        pathway_id = entry.get_text().strip()
        if self.fetch_button:
            self.fetch_button.set_sensitive(len(pathway_id) > 0)
    
    def _on_fetch_clicked(self, button):
        """Handle fetch button click - download pathway from KEGG."""
        if not self.api_client:
            self._show_status("Error: KEGG importer not available", error=True)
            return
        
        # Get pathway ID
        pathway_id = self.pathway_id_entry.get_text().strip()
        if not pathway_id:
            self._show_status("Please enter a pathway ID", error=True)
            return
        
        # Disable buttons during fetch
        if self.fetch_button:
            self.fetch_button.set_sensitive(False)
        self.import_button.set_sensitive(False)
        self._show_status(f"🔄 Fetching pathway {pathway_id} from KEGG...")
        
        # Fetch in background thread to avoid blocking UI
        def fetch_thread():
            try:
                # Fetch KGML from API (BLOCKING network request)
                kgml_data = self.api_client.fetch_kgml(pathway_id)
                
                if not kgml_data:
                    # Update UI in main thread
                    GLib.idle_add(self._on_fetch_failed, pathway_id)
                    return
                
                # Parse KGML
                parsed_pathway = self.parser.parse(kgml_data)
                
                # Update UI in main thread
                GLib.idle_add(self._on_fetch_complete, pathway_id, kgml_data, parsed_pathway)
                
            except Exception as e:
                # Show error in main thread
                GLib.idle_add(self._on_fetch_error, pathway_id, str(e))
        
        # Start daemon thread (non-blocking)
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def _on_fetch_complete(self, pathway_id, kgml_data, parsed_pathway):
        """Called in main thread after fetch completes successfully."""
        self.current_kgml = kgml_data
        self.current_pathway = parsed_pathway
        
        # Store pathway_id for later saving (after successful import)
        self.current_pathway_id = pathway_id
        
        # Update preview
        self._update_preview()
        
        # Enable import button
        self.import_button.set_sensitive(True)
        # Note: Don't show "loaded successfully" here - wait for final save message with file path
        
        # Re-enable fetch button
        if self.fetch_button:
            self.fetch_button.set_sensitive(True)
        return False  # Don't repeat
    
    def _on_fetch_failed(self, pathway_id):
        """Called in main thread when fetch fails."""
        self._show_status(f"❌ Failed to fetch pathway {pathway_id}", error=True)
        if self.fetch_button:
            self.fetch_button.set_sensitive(True)
        return False  # Don't repeat
    
    def _on_fetch_error(self, pathway_id, error_msg):
        """Called in main thread when fetch encounters an error."""
        self._show_status(f"❌ Error: {error_msg}", error=True)
        self.current_pathway = None
        self.current_kgml = None
        if self.fetch_button:
            self.fetch_button.set_sensitive(True)
        return False  # Don't repeat
    
    def _update_preview(self):
        """Update preview text with pathway information."""
        if not self.current_pathway or not self.preview_text:
            return
        
        pathway = self.current_pathway
        
        # Build preview text
        lines = []
        lines.append(f"Pathway: {pathway.name}")
        lines.append(f"Organism: {pathway.org}")
        lines.append(f"Number: {pathway.number}")
        lines.append("")
        lines.append(f"Entries: {len(pathway.entries)}")
        lines.append(f"Reactions: {len(pathway.reactions)}")
        lines.append(f"Relations: {len(pathway.relations)}")
        lines.append("")
        
        # Count entry types (pathway.entries is a dict, iterate over values)
        compounds = sum(1 for e in pathway.entries.values() if e.type == 'compound')
        genes = sum(1 for e in pathway.entries.values() if e.type == 'gene')
        enzymes = sum(1 for e in pathway.entries.values() if e.type == 'enzyme')
        lines.append(f"  Compounds: {compounds}")
        lines.append(f"  Genes: {genes}")
        lines.append(f"  Enzymes: {enzymes}")
        
        preview_text = "\n".join(lines)
        
        # Set text in TextView
        buffer = self.preview_text.get_buffer()
        buffer.set_text(preview_text)
    
    def _on_import_clicked(self, button):
        """Handle unified import button click.
        
        CURRENT FLOW:
        1. Convert pathway to DocumentModel
        2. Save .shy file to project/models/
        3. Save raw KGML to project/pathways/
        4. User must manually open file via File → Open or double-click in file explorer
        
        NOTE: Does NOT auto-load to canvas. File must be explicitly opened.
        This is intentional design for user control and avoiding state issues.
        """
        # Check if we already have a fetched pathway
        if self.current_pathway and self.current_kgml:
            # Pathway already fetched - go straight to conversion and save
            self._do_import_and_save()
        else:
            # No pathway fetched yet - need to fetch first
            pathway_id = self.pathway_id_entry.get_text().strip()
            if not pathway_id:
                self._show_status("Please enter a pathway ID", error=True)
                return
            
            # Fetch and then import when complete
            self._fetch_and_import(pathway_id)
    
    def _fetch_and_import(self, pathway_id):
        """Fetch pathway and then import it automatically."""
        if not self.api_client:
            self._show_status("Error: KEGG importer not available", error=True)
            return
        
        # Disable buttons during fetch
        if self.fetch_button:
            self.fetch_button.set_sensitive(False)
        self.import_button.set_sensitive(False)
        self._show_status(f"🔄 Fetching pathway {pathway_id} from KEGG...")
        
        # Fetch in background thread
        def fetch_thread():
            try:
                # Fetch KGML from API
                kgml_data = self.api_client.fetch_kgml(pathway_id)
                
                if not kgml_data:
                    GLib.idle_add(self._on_fetch_failed, pathway_id)
                    return
                
                # Parse KGML
                parsed_pathway = self.parser.parse(kgml_data)
                
                # Update UI and trigger import
                GLib.idle_add(self._fetch_and_import_complete, kgml_data, parsed_pathway, pathway_id)
                
            except Exception as e:
                GLib.idle_add(self._on_fetch_error, pathway_id, str(e))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def _fetch_and_import_complete(self, kgml_data, parsed_pathway, pathway_id):
        """Called after fetch completes - store data and immediately save."""
        self.current_kgml = kgml_data
        self.current_pathway = parsed_pathway
        self.current_pathway_id = pathway_id
        
        # Update preview
        self._update_preview()
        
        self._show_status(f"✅ Fetched {pathway_id}, now converting and saving...")
        
        # Now convert and save (no canvas creation)
        self._do_import_and_save()
        
        return False  # Don't repeat
    
    def _do_import_and_save(self):
        """Convert current pathway to model and save .shy file.
        
        CURRENT BEHAVIOR:
        - Saves .shy model file to project/models/
        - Saves raw .xml KGML to project/pathways/
        - Sets metadata['data_source'] = 'kegg_import' for Report color coding
        - Does NOT auto-load to canvas
        - User must explicitly open via File → Open or file explorer double-click
        
        This is intentional design to give users control over when models load
        and to avoid canvas state synchronization issues during import.
        """
        self.logger.info("=== _do_import_and_save called ===")
        
        if not self.current_pathway or not self.converter:
            self.logger.error(f"Missing requirements - pathway: {self.current_pathway is not None}, converter: {self.converter is not None}")
            self._show_status("No pathway loaded", error=True)
            return
        
        if not self.project:
            self.logger.error("No project available")
            self._show_status("❌ No project available", error=True)
            return
        
        self.logger.info(f"Starting conversion for pathway: {self.current_pathway_id}")
        
        # Disable buttons during import
        if self.fetch_button:
            self.fetch_button.set_sensitive(False)
        self.import_button.set_sensitive(False)
        
        # Import in background thread to avoid blocking UI
        def import_thread():
            try:
                self.logger.info("Import thread started")
                
                # Get conversion options from UI
                filter_cofactors = self.filter_cofactors_check.get_active()
                coordinate_scale = self.scale_spin.get_value()
                enable_layout = self.enhancement_layout_check.get_active() if self.enhancement_layout_check else True
                enable_arcs = False  # KEGG import: Always use straight arcs
                enable_metadata = self.enhancement_metadata_check.get_active() if self.enhancement_metadata_check else True
                
                self.logger.info(f"Conversion options - scale: {coordinate_scale}, filter_cofactors: {filter_cofactors}")
                
                # Create enhancement options
                from shypn.pathway.options import EnhancementOptions
                enhancement_options = EnhancementOptions(
                    enable_layout_optimization=enable_layout,
                    enable_arc_routing=enable_arcs,
                    enable_metadata_enhancement=enable_metadata
                )
                
                self.logger.info("Starting pathway conversion...")
                
                # Convert pathway to DocumentModel (BLOCKING operation)
                from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
                document_model = convert_pathway_enhanced(
                    self.current_pathway,
                    coordinate_scale=coordinate_scale,
                    include_cofactors=filter_cofactors,
                    enhancement_options=enhancement_options
                )
                
                self.logger.info(f"Conversion complete - model has {len(document_model.places) if document_model else 0} places")
                
                # Update UI in main thread
                GLib.idle_add(self._on_import_and_save_complete, document_model)
                
            except Exception as e:
                # Show error in main thread
                self.logger.error(f"Import thread error: {e}")
                import traceback
                traceback.print_exc()
                GLib.idle_add(self._on_import_error, str(e))
        
        # Start daemon thread (non-blocking)
        threading.Thread(target=import_thread, daemon=True).start()
    
    def _on_import_and_save_complete(self, document_model):
        """Called in main thread after conversion completes - save file only."""
        self.logger.info("=== _on_import_and_save_complete called ===")
        try:
            if not document_model:
                self.logger.error("No document_model provided")
                self._show_status("❌ Conversion failed - no data", error=True)
                if self.fetch_button:
                    self.fetch_button.set_sensitive(True)
                self.import_button.set_sensitive(True)
                return False
            
            # Save KGML and model to project
            if not self.project or not self.current_kgml or not self.current_pathway:
                self._show_status("❌ Project or pathway data not available", error=True)
                if self.fetch_button:
                    self.fetch_button.set_sensitive(True)
                self.import_button.set_sensitive(True)
                return False
            
            try:
                # Verify project has valid base path
                if not self.project.base_path:
                    raise ValueError("Project base_path not set - cannot save files")
                
                self.logger.info(f"Project base path: {self.project.base_path}")
                
                # 1. Save raw KGML file to project/pathways/ using project method
                kgml_filename = f"{self.current_pathway_id}.kgml"
                self.logger.info(f"Saving KGML file: {kgml_filename}")
                kgml_path = self.project.save_pathway_file(kgml_filename, self.current_kgml)
                self.logger.info(f"KGML saved to: {kgml_path}")
                
                # 2. Save .shy model file to project/models/ using project-aware path
                pathway_name = self.current_pathway.title or self.current_pathway.name
                model_filename = f"{self.current_pathway_id}.shy"
                
                # Get models directory from project (creates if needed)
                models_dir = self.project.get_models_dir()
                if not models_dir:
                    raise ValueError("Project models directory not available - base_path may be None")
                
                self.logger.info(f"Models directory: {models_dir}")
                os.makedirs(models_dir, exist_ok=True)
                model_filepath = os.path.join(models_dir, model_filename)
                
                self.logger.info(f"Saving model file to: {model_filepath}")
                document_model.save_to_file(model_filepath)
                self.logger.info(f"Model saved successfully to: {model_filepath}")
                
                # 3. Create PathwayDocument with metadata
                from shypn.data.pathway_document import PathwayDocument
                self.current_pathway_doc = PathwayDocument(
                    source_type="kegg",
                    source_id=self.current_pathway_id,
                    source_organism=self.current_pathway.org,
                    name=pathway_name
                )
                
                # Set file paths
                self.current_pathway_doc.raw_file = kgml_filename
                self.current_pathway_doc.model_file = model_filename
                
                # Add metadata notes
                self.current_pathway_doc.notes = f"KEGG pathway: {pathway_name}\n"
                self.current_pathway_doc.notes += f"Entries: {len(self.current_pathway.entries)}, "
                self.current_pathway_doc.notes += f"Reactions: {len(self.current_pathway.reactions)}, "
                self.current_pathway_doc.notes += f"Relations: {len(self.current_pathway.relations)}"
                
                # Link pathway to model
                if hasattr(document_model, 'id'):
                    self.current_pathway_doc.link_to_model(document_model.id)
                
                # Register with project and save
                self.project.add_pathway(self.current_pathway_doc)
                self.project.save()
                
                # Refresh file tree to show new files
                if self.file_panel_loader and hasattr(self.file_panel_loader, 'file_explorer'):
                    if hasattr(self.file_panel_loader.file_explorer, '_load_current_directory'):
                        self.file_panel_loader.file_explorer._load_current_directory()
                        self.logger.info("File tree refreshed after save")
                
                # Success message with file location
                self._show_status(
                    f"Model {model_filename} saved on {model_filepath}\n"
                    f"Use File → Open to load the model"
                )
                
                # Notify parent (PathwayOperationsPanel) that import is complete
                # This triggers Report panel refresh
                if self.import_complete_callback:
                    import_data = {
                        'pathway_id': self.current_pathway_id,
                        'file_path': model_filepath,
                        'organism': self.current_pathway.org if self.current_pathway else None
                    }
                    self.import_complete_callback(import_data)
                
            except Exception as save_error:
                import traceback
                traceback.print_exc()
                self._show_status(f"❌ Failed to save files: {save_error}", error=True)
                if self.fetch_button:
                    self.fetch_button.set_sensitive(True)
                self.import_button.set_sensitive(True)
                return False
            
            # Re-enable buttons
            if self.fetch_button:
                self.fetch_button.set_sensitive(True)
            self.import_button.set_sensitive(True)
            
            return False  # Don't repeat
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_status(f"❌ Import failed: {e}", error=True)
            if self.fetch_button:
                self.fetch_button.set_sensitive(True)
            self.import_button.set_sensitive(True)
            return False
    
    def _do_import_to_canvas(self):
        """DEPRECATED: Old direct-to-canvas import.
        
        HISTORY:
        - Previously loaded KEGG pathway directly to canvas
        - Caused Wayland rendering issues and state synchronization bugs
        - Replaced with file-based workflow (save then open)
        
        CURRENT APPROACH:
        - Import now saves to .shy file only (_do_import_and_save)
        - User explicitly opens via File → Open or file explorer
        - This avoids canvas state issues and gives user control
        
        This function kept for reference only. Not called in current code.
        """
        # Show deprecation message
        self._show_status("⚠️ Direct canvas import disabled - use File → Open instead", error=True)
    
    def _on_import_error(self, error_msg):
        """Called in main thread when import encounters an error."""
        self._show_status(f"❌ Import error: {error_msg}", error=True)
        if self.fetch_button:
            self.fetch_button.set_sensitive(True)
        self.import_button.set_sensitive(True)
        return False  # Don't repeat
    
    def _show_status(self, message: str, error: bool = False):
        """Show status message in label.
        
        Args:
            message: Status message to display
            error: If True, display as error (red text)
        """
        if not self.import_status_label:
            return
        
        self.import_status_label.set_text(message)
        
        # Apply error styling if needed
        if error:
            self.import_status_label.set_markup(f'<span foreground="red">{message}</span>')
        else:
            self.import_status_label.set_text(message)
