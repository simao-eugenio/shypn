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
    
    def __init__(self, builder: Gtk.Builder, model_canvas=None):
        """Initialize the SBML import panel controller.
        
        Args:
            builder: GTK Builder with loaded pathway_panel.ui
            model_canvas: Optional ModelCanvasManager for loading pathways
        """
        self.builder = builder
        self.model_canvas = model_canvas
        
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
        
        # Options widgets
        self.sbml_spacing_spin = self.builder.get_object('sbml_spacing_spin')
        self.sbml_scale_spin = self.builder.get_object('sbml_scale_spin')
        self.sbml_scale_example = self.builder.get_object('sbml_scale_example')
        
        # Preview and status
        self.sbml_preview_text = self.builder.get_object('sbml_preview_text')
        self.sbml_status_label = self.builder.get_object('sbml_status_label')
        
        # Action buttons
        self.sbml_parse_button = self.builder.get_object('sbml_parse_button')
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
        
        if self.sbml_import_button:
            self.sbml_import_button.connect('clicked', self._on_import_clicked)
        
        # Scale changes
        if self.sbml_scale_spin:
            self.sbml_scale_spin.connect('value-changed', self._on_scale_changed)
        
        # Enable parse button when user types in entry
        if self.sbml_file_entry:
            self.sbml_file_entry.connect('changed', self._on_file_entry_changed)
    
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
            
            # Disable import button until parsed
            if self.sbml_import_button:
                self.sbml_import_button.set_sensitive(False)
            
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
        
        # Disable buttons during fetch
        self.sbml_fetch_button.set_sensitive(False)
        self.sbml_parse_button.set_sensitive(False)
        self._show_status(f"Fetching {biomodels_id} from BioModels...")
        
        # Fetch in background
        GLib.idle_add(self._fetch_biomodels_background, biomodels_id)
    
    def _fetch_biomodels_background(self, biomodels_id: str):
        """Background task to fetch model from BioModels.
        
        Args:
            biomodels_id: BioModels identifier (e.g., BIOMD0000000001)
            
        Returns:
            False to stop GLib.idle_add from repeating
        """
        try:
            import urllib.request
            import tempfile
            
            # BioModels REST API URL
            url = f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}_url.xml"
            
            # Download to temporary file
            temp_dir = tempfile.gettempdir()
            temp_filepath = os.path.join(temp_dir, f"{biomodels_id}.xml")
            
            # Fetch the file
            self._show_status(f"Downloading {biomodels_id}...")
            urllib.request.urlretrieve(url, temp_filepath)
            
            # Verify file exists and has content
            if not os.path.exists(temp_filepath) or os.path.getsize(temp_filepath) == 0:
                self._show_status(f"Failed to download {biomodels_id}", error=True)
                self.sbml_fetch_button.set_sensitive(True)
                return False
            
            # Store filepath
            self.current_filepath = temp_filepath
            
            # Update file entry to show the temp path
            if self.sbml_file_entry:
                self.sbml_file_entry.set_text(temp_filepath)
            
            # Enable parse button
            if self.sbml_parse_button:
                self.sbml_parse_button.set_sensitive(True)
            
            self._show_status(f"✓ Downloaded {biomodels_id} successfully")
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self._show_status(f"Model {biomodels_id} not found in BioModels", error=True)
            else:
                self._show_status(f"HTTP error {e.code}: {e.reason}", error=True)
        except Exception as e:
            self._show_status(f"Fetch error: {str(e)}", error=True)
        
        finally:
            # Re-enable fetch button
            if self.sbml_fetch_button:
                self.sbml_fetch_button.set_sensitive(True)
        
        return False  # Don't repeat
    
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
        
        # Disable buttons during parsing
        self.sbml_parse_button.set_sensitive(False)
        self.sbml_import_button.set_sensitive(False)
        self._show_status(f"Parsing {os.path.basename(self.current_filepath)}...")
        
        # Parse in background to avoid blocking UI
        GLib.idle_add(self._parse_pathway_background)
    
    def _parse_pathway_background(self):
        """Background task to parse and validate SBML file.
        
        Returns:
            False to stop GLib.idle_add from repeating
        """
        try:
            # Parse SBML file
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
                self._show_status(f"Parsed successfully with {warning_count} warning(s)")
            else:
                self._show_status("✓ Parsed and validated successfully")
            
            # Update preview with pathway info
            self._update_preview()
            
            # Enable import button
            if self.sbml_import_button:
                self.sbml_import_button.set_sensitive(True)
            
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
            for comp in pathway.compartments[:5]:
                lines.append(f"  • {comp.name or comp.id}")
            if len(pathway.compartments) > 5:
                lines.append(f"  ... and {len(pathway.compartments) - 5} more")
        
        preview_text = "\n".join(lines)
        
        # Set text in TextView
        buffer = self.sbml_preview_text.get_buffer()
        buffer.set_text(preview_text)
    
    def _on_import_clicked(self, button):
        """Handle import button click - post-process, convert, and load into canvas."""
        if not self.parsed_pathway:
            self._show_status("No pathway parsed", error=True)
            return
        
        if not self.model_canvas:
            self._show_status("Error: No canvas available for import", error=True)
            return
        
        if not self.converter:
            self._show_status("Error: Pathway converter not available", error=True)
            return
        
        # Disable buttons during import
        self.sbml_parse_button.set_sensitive(False)
        self.sbml_import_button.set_sensitive(False)
        self._show_status("Converting pathway to Petri net...")
        
        # Import in background
        GLib.idle_add(self._import_pathway_background)
    
    def _import_pathway_background(self):
        """Background task to post-process, convert, and load into canvas.
        
        Returns:
            False to stop GLib.idle_add from repeating
        """
        try:
            # Get options from UI
            spacing = self.sbml_spacing_spin.get_value() if self.sbml_spacing_spin else 150.0
            scale_factor = self.sbml_scale_spin.get_value() if self.sbml_scale_spin else 1.0
            
            # Post-process: layout, colors, unit normalization, etc.
            self._show_status("Calculating layout and colors...")
            self.postprocessor = PathwayPostProcessor(
                spacing=spacing,
                scale_factor=scale_factor
            )
            self.processed_pathway = self.postprocessor.process(self.parsed_pathway)
            
            # Convert to DocumentModel
            self._show_status("Converting to Petri net...")
            document_model = self.converter.convert(self.processed_pathway)
            
            # Load into canvas
            self._show_status("Loading to canvas...")
            if self.model_canvas:
                # Create a new tab for this pathway
                # Get name from metadata (PathwayData stores it there)
                pathway_name = self.parsed_pathway.metadata.get('name') or os.path.basename(self.current_filepath)
                page_index, drawing_area = self.model_canvas.add_document(filename=pathway_name)
                
                # Get the canvas manager for this tab
                manager = self.model_canvas.get_canvas_manager(drawing_area)
                if manager:
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
                    
                    self._show_status(f"✓ Imported: {len(document_model.places)} places, "
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
            if self.sbml_parse_button:
                self.sbml_parse_button.set_sensitive(True)
            if self.sbml_import_button:
                self.sbml_import_button.set_sensitive(True)
        
        return False  # Don't repeat
    
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
