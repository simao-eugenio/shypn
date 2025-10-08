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
        api_client: KEGGAPIClient for fetching pathways
        parser: KGMLParser for parsing KGML XML
        converter: PathwayConverter for converting to Petri net
        current_pathway: Currently fetched pathway data (KEGGPathway)
    """
    
    def __init__(self, builder: Gtk.Builder, model_canvas=None):
        """Initialize the KEGG import panel controller.
        
        Args:
            builder: GTK Builder with loaded pathway_panel.ui
            model_canvas: Optional ModelCanvasManager for loading pathways
        """
        self.builder = builder
        self.model_canvas = model_canvas
        
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
        
        # Get widget references
        self._get_widgets()
        
        # Connect signals
        self._connect_signals()
    
    def _get_widgets(self):
        """Get references to UI widgets from builder."""
        # Input widgets
        self.pathway_id_entry = self.builder.get_object('pathway_id_entry')
        self.organism_combo = self.builder.get_object('organism_combo')
        
        # Options widgets
        self.filter_cofactors_check = self.builder.get_object('filter_cofactors_check')
        self.scale_spin = self.builder.get_object('scale_spin')
        self.include_relations_check = self.builder.get_object('include_relations_check')
        
        # Preview and status
        self.preview_text = self.builder.get_object('preview_text')
        self.import_status_label = self.builder.get_object('import_status_label')
        
        # Action buttons
        self.fetch_button = self.builder.get_object('fetch_button')
        self.import_button = self.builder.get_object('import_button')
    
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
        self.fetch_button.set_sensitive(False)
        self.import_button.set_sensitive(False)
        self._show_status(f"Fetching pathway {pathway_id}...")
        
        # Fetch in background to avoid blocking UI
        GLib.idle_add(self._fetch_pathway_background, pathway_id)
    
    def _fetch_pathway_background(self, pathway_id: str):
        """Background task to fetch pathway from KEGG.
        
        Args:
            pathway_id: KEGG pathway ID (e.g., "hsa00010")
            
        Returns:
            False to stop GLib.idle_add from repeating
        """
        try:
            # Fetch KGML from API
            kgml_data = self.api_client.fetch_kgml(pathway_id)
            
            if not kgml_data:
                self._show_status(f"Failed to fetch pathway {pathway_id}", error=True)
                self.fetch_button.set_sensitive(True)
                return False
            
            # Parse KGML
            self.current_kgml = kgml_data
            self.current_pathway = self.parser.parse(kgml_data)
            
            # Update preview
            self._update_preview()
            
            # Enable import button
            self.import_button.set_sensitive(True)
            self._show_status(f"Pathway {pathway_id} loaded successfully")
            
        except Exception as e:
            self._show_status(f"Error: {str(e)}", error=True)
            self.current_pathway = None
            self.current_kgml = None
        
        finally:
            # Re-enable fetch button
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
        """Handle import button click - convert and load into canvas."""
        if not self.current_pathway or not self.converter:
            self._show_status("No pathway loaded", error=True)
            return
        
        if not self.model_canvas:
            self._show_status("Error: No canvas available for import", error=True)
            return
        
        # Disable buttons during import
        self.fetch_button.set_sensitive(False)
        self.import_button.set_sensitive(False)
        self._show_status("Converting pathway to Petri net...")
        
        # Import in background
        GLib.idle_add(self._import_pathway_background)
    
    def _import_pathway_background(self):
        """Background task to convert pathway and load into canvas.
        
        Returns:
            False to stop GLib.idle_add from repeating
        """
        try:
            # Get conversion options from UI
            filter_cofactors = self.filter_cofactors_check.get_active()
            coordinate_scale = self.scale_spin.get_value()
            
            # Convert pathway to DocumentModel
            from shypn.importer.kegg.converter_base import ConversionOptions
            options = ConversionOptions(
                include_cofactors=filter_cofactors,  # Note: UI says "filter" but option is "include"
                coordinate_scale=coordinate_scale
            )
            
            document_model = self.converter.convert(self.current_pathway, options)
            
            # Load into canvas using the same method as file operations
            if self.model_canvas:
                # Create a new tab for this pathway
                pathway_name = self.current_pathway.title or self.current_pathway.name
                page_index, drawing_area = self.model_canvas.add_document(filename=pathway_name)
                
                # Get the canvas manager for this tab
                manager = self.model_canvas.get_canvas_manager(drawing_area)
                if manager:
                    print(f"[KEGGImport] Loading pathway into canvas manager")
                    print(f"[KEGGImport] Pathway has {len(document_model.places)} places, "
                          f"{len(document_model.transitions)} transitions, {len(document_model.arcs)} arcs")
                    
                    # Load the document model into the manager
                    manager.places = list(document_model.places)
                    manager.transitions = list(document_model.transitions)
                    manager.arcs = list(document_model.arcs)
                    
                    # Update ID counters
                    manager._next_place_id = document_model._next_place_id
                    manager._next_transition_id = document_model._next_transition_id
                    manager._next_arc_id = document_model._next_arc_id
                    
                    # Ensure arc references are properly set
                    manager.ensure_arc_references()
                    
                    # Mark as dirty to ensure redraw
                    manager.mark_dirty()
                    
                    print(f"[KEGGImport] Pathway loaded successfully")
                    self._show_status(f"Pathway imported: {len(document_model.places)} places, "
                                    f"{len(document_model.transitions)} transitions, "
                                    f"{len(document_model.arcs)} arcs")
                else:
                    self._show_status("Error: Could not get canvas manager", error=True)
            else:
                self._show_status("Error: No canvas available for import", error=True)
            
        except Exception as e:
            self._show_status(f"Import error: {str(e)}", error=True)
            import traceback
            traceback.print_exc()
        
        finally:
            # Re-enable buttons
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
