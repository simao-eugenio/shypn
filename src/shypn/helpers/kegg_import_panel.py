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
        self._show_status(f"✅ Pathway {pathway_id} loaded successfully")
        
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
        
        This is the main entry point for KEGG import that does:
        1. Fetch pathway from KEGG (if not already fetched)
        2. Convert to Petri net
        3. Load to canvas
        
        All in one smooth flow.
        """
        # Check if we already have a fetched pathway
        if self.current_pathway and self.current_kgml:
            # Pathway already fetched - go straight to conversion and loading
            self._do_import_to_canvas()
        else:
            # No pathway fetched yet - fetch first, then import
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
                GLib.idle_add(self._on_fetch_complete_and_import, pathway_id, kgml_data, parsed_pathway)
                
            except Exception as e:
                GLib.idle_add(self._on_fetch_error, pathway_id, str(e))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def _on_fetch_complete_and_import(self, pathway_id, kgml_data, parsed_pathway):
        """Called after fetch completes - store data and immediately import."""
        self.current_kgml = kgml_data
        self.current_pathway = parsed_pathway
        self.current_pathway_id = pathway_id
        
        # Update preview
        self._update_preview()
        
        self._show_status(f"✅ Fetched {pathway_id}, now importing...")
        
        # Now import to canvas
        self._do_import_to_canvas()
        
        return False  # Don't repeat
    
    def _do_import_to_canvas(self):
        """Convert and load current pathway into canvas."""
        if not self.current_pathway or not self.converter:
            self._show_status("No pathway loaded", error=True)
            return
        
        if not self.model_canvas:
            self._show_status("Error: No canvas available for import", error=True)
            return
        
        # Disable buttons during import
        if self.fetch_button:
            self.fetch_button.set_sensitive(False)
        self.import_button.set_sensitive(False)
        
        # PRE-CREATE CANVAS BEFORE PARSING (ARCHITECTURAL CHANGE)
        # This ensures the widget hierarchy is fully established before any user interaction
        # can trigger property dialogs, preventing Wayland Error 71 and dialog crashes
        pathway_name = self.current_pathway.title or self.current_pathway.name
        
        try:
            # Create empty canvas tab from UI template
            page_index, drawing_area = self.model_canvas.add_document(filename=pathway_name)
            
            # Get the canvas manager for state initialization
            manager = self.model_canvas.get_canvas_manager(drawing_area)
            if not manager:
                self._show_status("❌ Failed to initialize canvas", error=True)
                if self.fetch_button:
                    self.fetch_button.set_sensitive(True)
                self.import_button.set_sensitive(True)
                return
            
            # CRITICAL: Initialize canvas state IMMEDIATELY (before background parsing)
            # This prevents property dialog crashes on imported canvases
            manager.mark_clean()  # Mark as clean (no unsaved changes yet)
            manager.mark_as_imported(pathway_name)  # Mark as imported
            
            # Set filepath if project exists (for proper state initialization)
            if self.project:
                import os
                pathways_dir = self.project.get_pathways_dir()
                if pathways_dir:
                    temp_path = os.path.join(pathways_dir, f"{pathway_name}.shy")
                    manager.set_filepath(temp_path)
            
            # Switch to the newly created tab to show progress
            notebook = self.model_canvas.notebook
            notebook.set_current_page(page_index)
            
            # WAYLAND FIX: Force GTK to process pending events to ensure canvas is fully mapped
            # On Wayland, widgets must be mapped (visible) before dialogs can attach
            # Simply realizing isn't enough - need to process events to complete mapping
            while Gtk.events_pending():
                Gtk.main_iteration()
            
            # Store canvas info for background thread completion handler
            self._pending_canvas_info = {
                'page_index': page_index,
                'drawing_area': drawing_area,
                'manager': manager,
                'pathway_name': pathway_name
            }
            
        except Exception as tab_error:
            import traceback
            traceback.print_exc()
            self._show_status(f"❌ Failed to create canvas tab: {tab_error}", error=True)
            if self.fetch_button:
                self.fetch_button.set_sensitive(True)
            self.import_button.set_sensitive(True)
            return
        
        self._show_status("🔄 Converting pathway to Petri net...")
        
        # Import in background thread to avoid blocking UI
        def import_thread():
            try:
                # Get conversion options from UI (must read from main thread before thread starts)
                filter_cofactors = self.filter_cofactors_check.get_active()
                coordinate_scale = self.scale_spin.get_value()
                enable_layout = self.enhancement_layout_check.get_active() if self.enhancement_layout_check else True
                enable_arcs = False  # KEGG import: Always use straight arcs
                enable_metadata = self.enhancement_metadata_check.get_active() if self.enhancement_metadata_check else True
                
                # Create enhancement options
                from shypn.pathway.options import EnhancementOptions
                enhancement_options = EnhancementOptions(
                    enable_layout_optimization=enable_layout,
                    enable_arc_routing=enable_arcs,
                    enable_metadata_enhancement=enable_metadata
                )
                
                # Convert pathway to DocumentModel (BLOCKING operation)
                from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
                document_model = convert_pathway_enhanced(
                    self.current_pathway,
                    coordinate_scale=coordinate_scale,
                    include_cofactors=filter_cofactors,
                    enhancement_options=enhancement_options
                )
                
                # Update UI in main thread
                GLib.idle_add(self._on_import_complete, document_model)
                
            except Exception as e:
                # Show error in main thread
                GLib.idle_add(self._on_import_error, str(e))
                import traceback
                traceback.print_exc()
        
        # Start daemon thread (non-blocking)
        threading.Thread(target=import_thread, daemon=True).start()
    
    def _on_import_complete(self, document_model):
        """Called in main thread after import completes successfully."""
        try:
            if not document_model:
                self._show_status("❌ Conversion failed - no data", error=True)
                if self.fetch_button:
                    self.fetch_button.set_sensitive(True)
                self.import_button.set_sensitive(True)
                return False
            
            # USE PRE-CREATED CANVAS (don't create new one)
            if not hasattr(self, '_pending_canvas_info') or not self._pending_canvas_info:
                self._show_status("❌ Canvas initialization error", error=True)
                if self.fetch_button:
                    self.fetch_button.set_sensitive(True)
                self.import_button.set_sensitive(True)
                return False
            
            # Extract pre-created canvas components
            canvas_info = self._pending_canvas_info
            manager = canvas_info['manager']
            drawing_area = canvas_info['drawing_area']
            pathway_name = canvas_info['pathway_name']
            
            try:
                manager.load_objects(
                    places=document_model.places,
                    transitions=document_model.transitions,
                    arcs=document_model.arcs
                )
            except Exception as load_error:
                import traceback
                traceback.print_exc()
                self._show_status(f"❌ Failed to load objects: {load_error}", error=True)
                if self.fetch_button:
                    self.fetch_button.set_sensitive(True)
                self.import_button.set_sensitive(True)
                return False
            
            # Set change callback for object state management
            manager.document_controller.set_change_callback(manager._on_object_changed)
            
            # Fit imported content to page
            manager.fit_to_page(padding_percent=15, deferred=True, horizontal_offset_percent=30, vertical_offset_percent=10)
            
            # Trigger redraw to display imported objects
            drawing_area.queue_draw()
            
            # NOW save KGML and metadata to project (after successful import)
            if self.project and self.current_kgml and self.current_pathway:
                try:
                    # Save raw KGML file to project/pathways/
                    filename = f"{self.current_pathway_id}.kgml"
                    self.project.save_pathway_file(filename, self.current_kgml)
                    
                    # Create PathwayDocument with metadata
                    from shypn.data.pathway_document import PathwayDocument
                    self.current_pathway_doc = PathwayDocument(
                        source_type="kegg",
                        source_id=self.current_pathway_id,
                        source_organism=self.current_pathway.org,
                        name=self.current_pathway.title or self.current_pathway.name
                    )
                    
                    # Set file paths and notes
                    self.current_pathway_doc.raw_file = filename
                    self.current_pathway_doc.notes = f"KEGG pathway: {self.current_pathway.title or self.current_pathway.name}\n"
                    self.current_pathway_doc.notes += f"Entries: {len(self.current_pathway.entries)}, "
                    self.current_pathway_doc.notes += f"Reactions: {len(self.current_pathway.reactions)}, "
                    self.current_pathway_doc.notes += f"Relations: {len(self.current_pathway.relations)}"
                    
                    # Get model ID from document_model and link
                    model_id = document_model.id if hasattr(document_model, 'id') else None
                    if not model_id:
                        # Try to get from manager
                        model_id = manager.document_controller.document.id if hasattr(manager.document_controller.document, 'id') else None
                    
                    if model_id:
                        # Link pathway to model
                        self.current_pathway_doc.link_to_model(model_id)
                    
                    # Register with project
                    self.project.add_pathway(self.current_pathway_doc)
                    self.project.save()
                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
            
            self._show_status(f"✅ Pathway imported: {len(document_model.places)} places, "
                            f"{len(document_model.transitions)} transitions, "
                            f"{len(document_model.arcs)} arcs")
            
            # Clean up pending canvas info
            self._pending_canvas_info = None
            
            # Re-enable buttons
            if self.fetch_button:
                self.fetch_button.set_sensitive(True)
            self.import_button.set_sensitive(True)
        
        except Exception as e:
            self._show_status(f"❌ Import error: {str(e)}", error=True)
            import traceback
            traceback.print_exc()
        
        finally:
            # Re-enable buttons
            if self.fetch_button:
                self.fetch_button.set_sensitive(True)
            self.import_button.set_sensitive(True)
        
        return False  # Don't repeat
    
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
