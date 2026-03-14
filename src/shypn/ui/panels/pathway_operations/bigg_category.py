"""BiGG Models import category.

Thin orchestrator that coordinates BiGG services and UI components.
Follows BasePathwayCategory pattern for consistency.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import logging
import threading
from typing import Optional

from shypn.ui.panels.pathway_operations.base_pathway_category import BasePathwayCategory
from shypn.data.project_models import get_project_manager
from shypn.importer.bigg.bigg_model_fetcher import BiGGModelFetcher, BiGGModelInfo
from shypn.importer.bigg.bigg_downloader import BiGGDownloader
from shypn.importer.bigg.bigg_signal_classifier import BiGGSignalClassifier
from .bigg.bigg_model_browser import BiGGModelBrowser
from .bigg.bigg_metadata_panel import BiGGMetadataPanel
from .bigg.bigg_options_panel import BiGGOptionsPanel

# SBML parsing backend (shared with SBML category)
import os
try:
    from shypn.data.pathway.sbml_parser import SBMLParser
    from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
    from shypn.data.pathway.pathway_converter import PathwayConverter
    from shypn.services.sbml_compartment_module_service import SBMLCompartmentModuleService
except ImportError as e:
    print(f'Warning: SBML backend not available for BiGG: {e}')
    SBMLParser = None
    PathwayPostProcessor = None
    PathwayConverter = None
    SBMLCompartmentModuleService = None


class BiGGCategory(BasePathwayCategory):
    """BiGG Models import category.
    
    Thin orchestrator that delegates to services and UI components.
    Follows Wayland-safe patterns with proper lifecycle management.
    
    Architecture:
        - Services (business logic): BiGGModelFetcher, BiGGDownloader, BiGGSignalClassifier
        - UI Components (presentation): BiGGModelBrowser, BiGGMetadataPanel, BiGGOptionsPanel
        - Category (orchestration): Wires everything together, minimal logic
    """
    
    def __init__(self, workspace_settings=None, parent_window=None):
        """Initialize BiGG category.
        
        Args:
            workspace_settings: Optional WorkspaceSettings for last query
            parent_window: Optional parent window for dialogs (Wayland fix)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set parent window before super().__init__()
        self.workspace_settings = workspace_settings
        self.parent_window = parent_window
        
        # Services (business logic, no UI)
        self.fetcher = BiGGModelFetcher()
        self.downloader = BiGGDownloader()
        self.classifier = BiGGSignalClassifier()
        
        # SBML parsing backend (shared with SBML category)
        if SBMLParser:
            self.sbml_parser = SBMLParser()
            self.postprocessor = PathwayPostProcessor()
            self.converter = PathwayConverter()
        else:
            self.sbml_parser = None
            self.postprocessor = None
            self.converter = None
            self.logger.warning("SBML parsing backend not available")
        
        # UI components (initialized in _build_content)
        self.model_browser: Optional[BiGGModelBrowser] = None
        self.metadata_panel: Optional[BiGGMetadataPanel] = None
        self.options_panel: Optional[BiGGOptionsPanel] = None
        self.import_button: Optional[Gtk.Button] = None
        
        # Widget tracking for Wayland-safe cleanup
        self._widgets = []
        self._signal_handlers = []
        
        # Call parent init (will call _build_content)
        super().__init__(category_name="BiGG Models", expanded=False)
        
        self.logger.info("BiGG category initialized")
    
    def _build_content(self):
        """Build BiGG-specific UI (thin orchestrator pattern).
        
        Returns:
            Gtk.Widget: Content widget for this category
        """
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.set_margin_top(6)
        main_box.set_margin_bottom(6)
        
        # Source selection (Local/Remote)
        source_box = self._build_source_selection()
        main_box.pack_start(source_box, False, False, 0)
        
        # Accession input (unified for both local and remote)
        accession_box = self._build_accession_input()
        main_box.pack_start(accession_box, False, False, 0)
        
        # SBML Metadata Inspector (expandable, shows parsed SBML data in table format)
        self.sbml_metadata_expander = Gtk.Expander(label="SBML Metadata Inspector")
        self.sbml_metadata_expander.set_expanded(False)
        
        # Connect to expansion event - populate metadata when user expands
        self.sbml_metadata_expander.connect("notify::expanded", self._on_metadata_expander_toggled)
        
        # Create tree store for metadata
        self.sbml_metadata_store = Gtk.TreeStore(str, str, str, str, str, bool, str)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 250)
        
        # TreeStore: [icon, category, name, value, type, editable, object_id]
        self.sbml_metadata_store = Gtk.TreeStore(str, str, str, str, str, bool, str)
        self.sbml_metadata_tree = Gtk.TreeView(model=self.sbml_metadata_store)
        self.sbml_metadata_tree.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.sbml_metadata_tree.set_enable_tree_lines(True)
        
        # Icon column
        icon_renderer = Gtk.CellRendererText()
        icon_col = Gtk.TreeViewColumn("", icon_renderer, text=0)
        icon_col.set_fixed_width(30)
        self.sbml_metadata_tree.append_column(icon_col)
        
        # Category column
        category_renderer = Gtk.CellRendererText()
        category_col = Gtk.TreeViewColumn("Category", category_renderer, text=1)
        category_col.set_resizable(True)
        category_col.set_min_width(120)
        self.sbml_metadata_tree.append_column(category_col)
        
        # Name column
        name_renderer = Gtk.CellRendererText()
        name_col = Gtk.TreeViewColumn("Name/ID", name_renderer, text=2)
        name_col.set_resizable(True)
        name_col.set_expand(True)
        self.sbml_metadata_tree.append_column(name_col)
        
        # Value column (editable)
        value_renderer = Gtk.CellRendererText()
        value_renderer.set_property("family", "monospace")
        value_renderer.set_property("editable", True)
        value_renderer.connect("edited", self._on_sbml_metadata_edited)
        value_col = Gtk.TreeViewColumn("Value", value_renderer, text=3, editable=5)
        value_col.set_resizable(True)
        value_col.set_expand(True)
        self.sbml_metadata_tree.append_column(value_col)
        
        # Type column
        type_renderer = Gtk.CellRendererText()
        type_col = Gtk.TreeViewColumn("Type", type_renderer, text=4)
        type_col.set_resizable(True)
        type_col.set_min_width(80)
        self.sbml_metadata_tree.append_column(type_col)
        
        scrolled.add(self.sbml_metadata_tree)
        self.sbml_metadata_expander.add(scrolled)
        main_box.pack_start(self.sbml_metadata_expander, False, False, 0)
        
        # Options panel
        self.options_panel = BiGGOptionsPanel()
        self._widgets.append(self.options_panel)
        main_box.pack_start(self.options_panel, False, False, 0)
        
        # Import button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.import_button = Gtk.Button(label="Import to Project")
        self.import_button.set_sensitive(False)  # Disabled until model selected
        handler_id = self.import_button.connect("clicked", self._on_import_clicked)
        self._signal_handlers.append((handler_id, self.import_button))
        button_box.pack_end(self.import_button, False, False, 0)
        
        main_box.pack_start(button_box, False, False, 0)
        
        # Status label (at the end)
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self.status_label.set_markup("<i>Select a model to import</i>")
        main_box.pack_start(self.status_label, False, False, 0)
        
        return main_box
    
    def _on_model_selected(self, model: BiGGModelInfo):
        """Handle model selection (delegates to UI components).
        
        Args:
            model: Selected BiGGModelInfo
        """
        self.logger.info(f"Model selected: {model.id}")
        
        # Update metadata panel
        self.metadata_panel.update_model(model)
        
        # Enable import button
        self.import_button.set_sensitive(True)
        
        # Update status
        self.status_label.set_text(f"Ready to import {model.id}")
    
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
        
        # Local file option
        self.local_radio = Gtk.RadioButton(label="Local File")
        self.local_radio.set_active(False)
        self.local_radio.connect('toggled', self._on_source_changed)
        radio_box.pack_start(self.local_radio, False, False, 0)
        
        # Remote BiGG database option (default)
        self.remote_radio = Gtk.RadioButton.new_with_label_from_widget(self.local_radio, "Remote (BiGG Database)")
        self.remote_radio.set_active(True)
        self.remote_radio.connect('toggled', self._on_source_changed)
        radio_box.pack_start(self.remote_radio, False, False, 0)
        
        box.pack_start(radio_box, False, False, 0)
        
        return box
    
    def _build_accession_input(self):
        """Build accession number input section (unified for local/remote).
        
        Returns:
            Gtk.Box: Accession input widgets
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label()
        label.set_markup("<b>Accession Number:</b>")
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)
        
        # Entry with browse button
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.accession_entry = Gtk.Entry()
        self.accession_entry.set_placeholder_text("BiGG model ID or path to SBML file")
        self.accession_entry.connect('changed', self._on_accession_entry_changed)
        entry_box.pack_start(self.accession_entry, True, True, 0)
        
        # Browse button (only visible in local mode)
        self.browse_button = Gtk.Button(label="Browse...")
        self.browse_button.set_no_show_all(True)
        self.browse_button.set_visible(False)  # Hidden by default (remote is default)
        self.browse_button.connect('clicked', self._on_browse_clicked)
        entry_box.pack_start(self.browse_button, False, False, 0)
        
        box.pack_start(entry_box, False, False, 0)
        
        # Help text (changes based on mode)
        self.accession_help_label = Gtk.Label()
        self.accession_help_label.set_markup(
            '<span size="small">Enter BiGG model ID (e.g., e_coli_core, iJO1366) from http://bigg.ucsd.edu</span>'
        )
        self.accession_help_label.set_xalign(0)
        self.accession_help_label.get_style_context().add_class("dim-label")
        self.accession_help_label.set_line_wrap(True)
        box.pack_start(self.accession_help_label, False, False, 0)
        
        return box
    
    def _on_source_changed(self, radio_button):
        """Handle source mode change (Local/Remote).
        
        Args:
            radio_button: The radio button that was toggled
        """
        if not radio_button.get_active():
            return
        
        if self.local_radio.get_active():
            # Local mode: show browse button, update help text
            self.browse_button.set_visible(True)
            self.accession_entry.set_placeholder_text("Path to local SBML file")
            self.accession_help_label.set_markup(
                '<span size="small">Select a local SBML file (.xml or .sbml)</span>'
            )
            self.import_button.set_sensitive(False)
            self.status_label.set_markup("<i>Select a local SBML file to import</i>")
        else:
            # Remote mode: hide browse button, update help text
            self.browse_button.set_visible(False)
            self.accession_entry.set_placeholder_text("BiGG model ID (e.g., e_coli_core, iJO1366)")
            self.accession_help_label.set_markup(
                '<span size="small">Enter BiGG model ID from http://bigg.ucsd.edu</span>'
            )
            self.import_button.set_sensitive(False)
            self.status_label.set_markup("<i>Enter a BiGG model ID to import</i>")
    
    def _on_accession_entry_changed(self, entry):
        """Handle accession entry text changes.
        
        Args:
            entry: The accession entry widget
        """
        value = entry.get_text().strip()
        
        if self.local_radio.get_active():
            # Local mode: check if file exists
            if value and os.path.exists(value):
                # Trigger preview parse
                self._parse_and_preview_sbml(value)
                
                self.import_button.set_sensitive(True)
                self.status_label.set_text(f"Ready to import {os.path.basename(value)}")
            else:
                self.import_button.set_sensitive(False)
                if value:
                    self.status_label.set_text("File not found")
                else:
                    self.status_label.set_markup("<i>Select a local SBML file to import</i>")
        else:
            # Remote mode: check if model ID is provided
            if value:
                self.import_button.set_sensitive(True)
                self.status_label.set_text(f"Ready to import {value}")
            else:
                self.import_button.set_sensitive(False)
                self.status_label.set_markup("<i>Enter a BiGG model ID to import</i>")

    def _on_browse_clicked(self, button):
        """Open SBML file chooser and populate the accession entry."""
        self._open_sbml_file_dialog(self.accession_entry)

    def _parse_and_preview_sbml(self, filepath):
        """Parse a local SBML file in background and populate metadata preview.
        
        This method is called when browsing local files to show a preview
        before importing.
        
        Args:
            filepath: Path to SBML file
        """
        def parse_in_background():
            try:
                self.logger.info(f"Parsing SBML file for preview: {filepath}")
                
                # Parse SBML file
                parsed_pathway = self.sbml_parser.parse_file(filepath)
                
                # Cache for later import
                self.parsed_pathway = parsed_pathway
                self.current_filepath = filepath
                
                # Update metadata tree on main thread
                GLib.idle_add(self._update_sbml_metadata_view, parsed_pathway)
                # Metadata will be visible when user expands the inspector
                
                self.logger.info("SBML preview completed successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to parse SBML for preview: {e}")
                import traceback
                traceback.print_exc()
        
        # Run parse in background thread to avoid UI freeze
        thread = threading.Thread(target=parse_in_background, daemon=True)
        thread.start()
    
    def _update_sbml_metadata_view(self, parsed_pathway):
        """Update SBML metadata inspector with parsed data in table format.
        
        Args:
            parsed_pathway: PathwayData from SBML parser
        """
        try:
            self.logger.info("Updating SBML metadata inspector...")
            
            if not parsed_pathway:
                self.logger.error("No parsed pathway provided")
                return False
            
            self.sbml_metadata_store.clear()
            
            # Store parsed pathway for editing
            self.current_parsed_pathway = parsed_pathway
            
            # Compartments section
            if hasattr(parsed_pathway, 'compartments') and parsed_pathway.compartments:
                comp_parent = self.sbml_metadata_store.append(None, [
                    "📦", "Compartments", f"{len(parsed_pathway.compartments)} total", "", "Section", False, "compartments"
                ])
                for comp_id, comp in parsed_pathway.compartments.items():
                    name = comp.name if hasattr(comp, 'name') and comp.name else comp_id
                    size = comp.size if hasattr(comp, 'size') else 'N/A'
                    self.sbml_metadata_store.append(comp_parent, [
                        "🔹", "Compartment", name, str(size), "float", True, f"comp:{comp_id}"
                    ])
                self.logger.info(f"  Added {len(parsed_pathway.compartments)} compartments")
            
            # Species section (show all)
            if hasattr(parsed_pathway, 'species') and parsed_pathway.species:
                species_parent = self.sbml_metadata_store.append(None, [
                    "🧬", "Species", f"{len(parsed_pathway.species)} total", "", "Section", False, "species"
                ])
                for species in parsed_pathway.species:
                    comp = species.compartment if hasattr(species, 'compartment') else 'N/A'
                    tokens = species.initial_tokens if hasattr(species, 'initial_tokens') else 0
                    self.sbml_metadata_store.append(species_parent, [
                        "🔸", f"Species [{comp}]", species.id, str(tokens), "float", True, f"species:{species.id}"
                    ])
                self.logger.info(f"  Added {len(parsed_pathway.species)} species")
            
            # Reactions section (show all)
            if hasattr(parsed_pathway, 'reactions') and parsed_pathway.reactions:
                reactions_parent = self.sbml_metadata_store.append(None, [
                    "⚡", "Reactions", f"{len(parsed_pathway.reactions)} total", "", "Section", False, "reactions"
                ])
                for reaction in parsed_pathway.reactions:
                    rev = "⇌" if getattr(reaction, 'reversible', False) else "→"
                    self.sbml_metadata_store.append(reactions_parent, [
                        "🔹", "Reaction", f"{reaction.id} {rev}", reaction.name, "string", False, f"reaction:{reaction.id}"
                    ])
                self.logger.info(f"  Added {len(parsed_pathway.reactions)} reactions")
            
            # Global parameters section
            if hasattr(parsed_pathway, 'parameters') and parsed_pathway.parameters:
                param_parent = self.sbml_metadata_store.append(None, [
                    "⚙️", "Global Parameters", f"{len(parsed_pathway.parameters)} total", "", "Section", False, "parameters"
                ])
                for param_id, param_value in parsed_pathway.parameters.items():
                    # Determine if constant or variable
                    param_type = "constant" if hasattr(parsed_pathway, 'constants') and param_id in getattr(parsed_pathway, 'constants', {}) else "variable"
                    self.sbml_metadata_store.append(param_parent, [
                        "🔧", param_type.capitalize(), param_id, str(param_value), "float", True, f"param:{param_id}"
                    ])
                self.logger.info(f"  Added {len(parsed_pathway.parameters)} parameters")
            
            # Local parameters (from reaction kinetics)
            if hasattr(parsed_pathway, 'reactions') and parsed_pathway.reactions:
                local_params = {}
                for reaction in parsed_pathway.reactions:
                    if hasattr(reaction, 'local_parameters') and reaction.local_parameters:
                        for param_id, param_value in reaction.local_parameters.items():
                            full_id = f"{reaction.id}.{param_id}"
                            local_params[full_id] = param_value
                
                if local_params:
                    local_parent = self.sbml_metadata_store.append(None, [
                        "🔩", "Local Parameters", f"{len(local_params)} total", "", "Section", False, "local_parameters"
                    ])
                    for param_id, param_value in local_params.items():
                        self.sbml_metadata_store.append(local_parent, [
                            "🔸", "Parameter", param_id, str(param_value), "float", True, f"local_param:{param_id}"
                        ])
                    self.logger.info(f"  Added {len(local_params)} local parameters")
            
            # Constants section (if separate from parameters)
            if hasattr(parsed_pathway, 'constants') and parsed_pathway.constants:
                const_parent = self.sbml_metadata_store.append(None, [
                    "🔒", "Constants", f"{len(parsed_pathway.constants)} total", "", "Section", False, "constants"
                ])
                for const_id, const_value in parsed_pathway.constants.items():
                    self.sbml_metadata_store.append(const_parent, [
                        "🔹", "Constant", const_id, str(const_value), "float", False, f"const:{const_id}"
                    ])
                self.logger.info(f"  Added {len(parsed_pathway.constants)} constants")
            
            # Function definitions
            if hasattr(parsed_pathway, 'metadata') and 'function_definitions_count' in parsed_pathway.metadata:
                count = parsed_pathway.metadata['function_definitions_count']
                if count > 0:
                    func_parent = self.sbml_metadata_store.append(None, [
                        "📐", "Function Definitions", f"{count} total", "", "Section", False, "functions"
                    ])
                    if 'function_definitions' in parsed_pathway.metadata:
                        for func in parsed_pathway.metadata['function_definitions']:
                            func_id = func.get('id', 'N/A')
                            func_formula = func.get('formula', '')
                            self.sbml_metadata_store.append(func_parent, [
                                "🔹", "Function", func_id, func_formula, "formula", False, f"func:{func_id}"
                            ])
                    self.logger.info(f"  Added {count} function definitions")
            
            # Expand all tree rows to show the metadata
            self.sbml_metadata_tree.expand_all()
            
            # Metadata will be visible when user expands the inspector
            self.logger.info("✓ SBML metadata inspector updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to update SBML metadata inspector: {e}")
            import traceback
            traceback.print_exc()
        
        return False
    
    def _on_sbml_metadata_edited(self, renderer, path, new_text):
        """Handle editing of SBML metadata values.
        
        Args:
            renderer: The CellRendererText
            path: TreePath of the edited row
            new_text: New value as string
        """
        iter_obj = self.sbml_metadata_store.get_iter(path)
        object_id = self.sbml_metadata_store.get_value(iter_obj, 6)  # object_id
        value_type = self.sbml_metadata_store.get_value(iter_obj, 4)  # type
        
        try:
            # Convert to appropriate type
            if value_type == "float":
                new_value = float(new_text)
            elif value_type == "int":
                new_value = int(new_text)
            else:
                new_value = new_text
            
            # Update the store
            self.sbml_metadata_store.set_value(iter_obj, 3, str(new_value))
            
            # Update the underlying data structure
            if object_id.startswith("comp:"):
                comp_id = object_id.split(":", 1)[1]
                if hasattr(self.current_parsed_pathway, 'compartments'):
                    if comp_id in self.current_parsed_pathway.compartments:
                        self.current_parsed_pathway.compartments[comp_id].size = new_value
                        self.logger.info(f"Updated compartment {comp_id} size to {new_value}")
            
            elif object_id.startswith("species:"):
                species_id = object_id.split(":", 1)[1]
                if hasattr(self.current_parsed_pathway, 'species'):
                    for species in self.current_parsed_pathway.species:
                        if species.id == species_id:
                            species.initial_tokens = new_value
                            self.logger.info(f"Updated species {species_id} initial tokens to {new_value}")
                            break
            
            elif object_id.startswith("param:"):
                param_id = object_id.split(":", 1)[1]
                if hasattr(self.current_parsed_pathway, 'parameters'):
                    self.current_parsed_pathway.parameters[param_id] = new_value
                    self.logger.info(f"Updated parameter {param_id} to {new_value}")
            
            elif object_id.startswith("local_param:"):
                full_id = object_id.split(":", 1)[1]
                reaction_id, param_id = full_id.rsplit(".", 1)
                if hasattr(self.current_parsed_pathway, 'reactions'):
                    for reaction in self.current_parsed_pathway.reactions:
                        if reaction.id == reaction_id and hasattr(reaction, 'local_parameters'):
                            reaction.local_parameters[param_id] = new_value
                            self.logger.info(f"Updated local parameter {full_id} to {new_value}")
                            break
            
        except ValueError as e:
            self.logger.error(f"Invalid value '{new_text}' for type {value_type}: {e}")
            # Show error dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=f"Invalid value: {e}"
            )
            dialog.run()
            dialog.destroy()
    
    def _on_import_clicked(self, button):
        """Handle import button click with full SBML parsing workflow.
        
        Full workflow:
        1. Download SBML from BiGG (remote) or load local file
        2. Parse SBML → PathwayData
        3. Apply BiGG signal classification
        4. Convert to DocumentModel (Petri net)
        5. Save to project
        6. Auto-load to canvas
        """
        # Check mode
        if self.local_radio.get_active():
            # Local mode - get file path from accession entry
            filepath = self.accession_entry.get_text().strip()
            if not filepath or not os.path.exists(filepath):
                self._show_status("Please select a valid SBML file", error=True)
                return
            model_id = os.path.splitext(os.path.basename(filepath))[0]
            sbml_source_path = filepath
        else:
            # Remote mode - get model ID from accession entry
            model_id = self.accession_entry.get_text().strip()
            if not model_id:
                self._show_status("Please enter a BiGG model ID", error=True)
                return
            sbml_source_path = None  # Will download
        
        if not self.project:
            self._show_status(
                "No project open. Please open or create a project first: "
                "File → New Project or File → Open Project",
                error=True
            )
            return
        
        if not self.sbml_parser:
            self._show_status(
                "❌ SBML parsing backend not available",
                error=True
            )
            return
        
        self.logger.info(f"Starting import of {model_id}")
        
        # Disable button during import
        self.import_button.set_sensitive(False)
        
        if sbml_source_path:
            self._show_status(f"Loading {model_id}...", error=False)
        else:
            self._show_status(f"Downloading {model_id}...", error=False)
        
        # Import in background thread
        def import_thread():
            try:
                # Get options
                use_cache = self.options_panel.get_use_cache() if not sbml_source_path else False
                classify_energy = self.options_panel.get_classify_energy()
                
                self.logger.info(f"  Options: use_cache={use_cache}, classify_energy={classify_energy}")
                
                # Step 1: Download SBML or use local file
                if sbml_source_path:
                    self.logger.info(f"Step 1: Using local SBML file: {sbml_source_path}")
                    sbml_path = sbml_source_path
                else:
                    self.logger.info(f"Step 1: Downloading SBML for {model_id}")
                    sbml_path = self.downloader.download_sbml(
                        model_id=model_id,
                        use_cache=use_cache
                    )
                sbml_size = os.path.getsize(sbml_path)
                self.logger.info(f"  Using: {sbml_path} ({sbml_size} bytes)")
                
                # Step 2: Parse SBML → PathwayData
                # Check if we already parsed this file in preview
                if (hasattr(self, 'parsed_pathway') and self.parsed_pathway and 
                    hasattr(self, 'current_filepath') and self.current_filepath == sbml_path):
                    self.logger.info("  Reusing cached parsed pathway from preview")
                    parsed_pathway = self.parsed_pathway
                else:
                    self.logger.info("Step 2: Parsing SBML")
                    parsed_pathway = self.sbml_parser.parse_file(sbml_path)
                    self.logger.info(f"  Parsed: {len(parsed_pathway.species)} species, "
                                   f"{len(parsed_pathway.reactions)} reactions")
                    
                    # Check memory requirements for large models
                    from shypn.data.pathway.memory_optimizer import estimate_memory_requirements
                    mem_est = estimate_memory_requirements(
                        len(parsed_pathway.species),
                        len(parsed_pathway.reactions)
                    )
                    if mem_est['use_optimization']:
                        self.logger.warning(f"  Large model detected: {mem_est['estimated_memory_mb']} MB estimated")
                        self.logger.warning(f"  {mem_est['recommendation']}")
                        # Force garbage collection before conversion
                        import gc
                        gc.collect()
                
                # Update SBML metadata inspector (on main thread)
                GLib.idle_add(self._update_sbml_metadata_view, parsed_pathway)
                
                # Step 3: Post-process → ProcessedPathwayData
                self.logger.info("Step 3: Post-processing pathway")
                processed_pathway = self.postprocessor.process(parsed_pathway)
                
                # Step 4: Convert to Petri net → DocumentModel
                self.logger.info("Step 4: Converting to Petri net")
                
                # Check if this is a large model requiring memory optimization
                species_count = len(processed_pathway.species)
                reaction_count = len(processed_pathway.reactions)
                
                if species_count > 500 or reaction_count > 500:
                    # Use memory-optimized conversion for large models
                    self.logger.info("  Using memory-optimized conversion (large model)")
                    from shypn.data.pathway.memory_optimizer import optimize_large_model_import
                    document_model = optimize_large_model_import(
                        processed_pathway, 
                        self.converter, 
                        self.logger
                    )
                else:
                    # Standard conversion for smaller models
                    document_model = self.converter.convert(processed_pathway)
                
                self.logger.info(f"  Converted: {len(document_model.places)} places, "
                               f"{len(document_model.transitions)} transitions")
                
                # Add metadata to document model for later identification
                if not hasattr(document_model, 'metadata'):
                    document_model.metadata = {}
                document_model.metadata['source'] = 'bigg_import'
                document_model.metadata['data_source'] = 'bigg_import'
                document_model.metadata['model_id'] = model_id
                
                # Save minimal SBML data for metadata inspector
                try:
                    bigg_sbml_data = {
                        'model_id': model_id,
                        'compartments_count': len(getattr(parsed_pathway, 'compartments', {})),
                        'species_count': len(getattr(parsed_pathway, 'species', [])),
                        'reactions_count': len(getattr(parsed_pathway, 'reactions', [])),
                        'parameters_count': len(getattr(parsed_pathway, 'parameters', {}))
                    }
                    document_model.metadata['bigg_sbml_data'] = bigg_sbml_data
                    self.logger.info(f"Saved BiGG SBML data to metadata: {len(bigg_sbml_data)} keys")
                except Exception as e:
                    self.logger.warning(f"Could not serialize BiGG SBML data: {e}")
                
                # Step 5: Apply BiGG signal classification (if enabled)
                if classify_energy:
                    self.logger.info("Step 5: Applying BiGG signal classification")
                    from shypn.netobjs.signal_type import SignalType
                    classified_places = self.classifier.classify_energy_signals(document_model.places)
                    energy_count = sum(1 for p in classified_places 
                                      if hasattr(p, 'signal_type') and p.signal_type == SignalType.ENERGY)
                    self.logger.info(f"  Classified {energy_count} energy signals (Layer 0)")
                else:
                    self.logger.info("Step 5: Signal classification skipped (user option)")
                
                # Step 5.5: Convert arcs to/from signal places to SignalFlowArcs
                if classify_energy:
                    self.logger.info("Step 5.5: Converting arcs to signal places to SignalFlowArcs")
                    from shypn.netobjs.signal_flow_arc import SignalFlowArc
                    from shypn.netobjs.arc import Arc
                    
                    signal_places = [p for p in document_model.places if getattr(p, 'is_signal_place', False)]
                    signal_place_set = set(signal_places)
                    
                    converted_count = 0
                    new_arcs = []
                    
                    for arc in document_model.arcs:
                        # Check if arc connects to/from a signal place
                        if isinstance(arc, Arc) and not isinstance(arc, SignalFlowArc):
                            if arc.source in signal_place_set or arc.target in signal_place_set:
                                # Convert to SignalFlowArc (light gray)
                                arc_id = getattr(arc, 'id', f'arc_{id(arc)}')
                                arc_name = getattr(arc, 'name', '')
                                signal_arc = SignalFlowArc(
                                    source=arc.source,
                                    target=arc.target,
                                    id=arc_id,
                                    name=arc_name,
                                    weight=arc.weight
                                )
                                # Copy metadata
                                if hasattr(arc, 'metadata'):
                                    signal_arc.metadata = arc.metadata
                                new_arcs.append(signal_arc)
                                converted_count += 1
                            else:
                                new_arcs.append(arc)
                        else:
                            new_arcs.append(arc)
                    
                    document_model.arcs = new_arcs
                    self.logger.info(f"  Converted {converted_count} arcs to SignalFlowArcs")
                
                # Step 5.6: Enforce color schema on all entities
                # Color priority: Signal > Compartment > Regulatory > Default
                # - Signal places (ATP, NAD, etc.): Blue border (0.0, 0.4, 0.8)
                # - Compartment places (non-cytosol): Violet border (0.5, 0.0, 0.5)
                # - Regular places (cytosol): Black border (0.0, 0.0, 0.0)
                # - SignalFlowArcs: Light gray (0.7, 0.7, 0.7)
                self.logger.info("Step 5.6: Enforcing color schema on all entities")
                from shypn.utils.color_schema_manager import ColorSchemaManager
                
                # Apply colors to all places (signal, compartment, regulatory)
                for place in document_model.places:
                    ColorSchemaManager.reset_place_color(place)
                
                # Apply colors to all arcs (regular, test, signal flow, inhibitor)
                for arc in document_model.arcs:
                    ColorSchemaManager.reset_arc_color(arc)
                
                # Apply colors to all transitions (regular, source/sink)
                for transition in document_model.transitions:
                    border_color, fill_color = ColorSchemaManager.get_transition_colors(transition)
                    transition.border_color = border_color
                    transition.fill_color = fill_color
                
                self.logger.info(f"  Applied color schema to {len(document_model.places)} places, "
                               f"{len(document_model.transitions)} transitions, {len(document_model.arcs)} arcs")
                
                # Step 6: Convert SBML compartments to modules
                if SBMLCompartmentModuleService:
                    try:
                        self.logger.info("Step 6: Converting compartments to modules")
                        # Build species_id → Place mapping
                        species_to_place = {}
                        for place in document_model.places:
                            if hasattr(place, 'metadata') and place.metadata:
                                original_species_id = place.metadata.get('original_species_id')
                                if original_species_id:
                                    species_to_place[original_species_id] = place
                        
                        # Build reaction_id → Transition mapping
                        reaction_to_transition = {}
                        for transition in document_model.transitions:
                            if hasattr(transition, 'metadata') and transition.metadata:
                                reaction_id = transition.metadata.get('reaction_id')
                                if reaction_id:
                                    reaction_to_transition[reaction_id] = transition
                        
                        module_service = SBMLCompartmentModuleService()
                        conversion_result = module_service.convert_compartments_to_modules(
                            document=document_model,
                            pathway=processed_pathway,
                            species_to_place=species_to_place,
                            reaction_to_transition=reaction_to_transition,
                            auto_detect_signals=True,
                            validate=False  # BiGG models have cross-compartment arcs by design
                        )
                        
                        if conversion_result and conversion_result.get('success'):
                            modules = conversion_result.get('modules', [])
                            for module in modules:
                                document_model.add_module(module)
                            self.logger.info(f"  Created {len(modules)} compartment modules")
                    except Exception as e:
                        self.logger.warning(f"Module conversion failed: {e}")
                
                # Return result
                result = {
                    'model_id': model_id,
                    'sbml_path': sbml_path,
                    'sbml_size': sbml_size,
                    'processed_pathway': processed_pathway,
                    'document_model': document_model
                }
                
                GLib.idle_add(self._on_import_complete, result)
                
            except Exception as e:
                self.logger.error(f"Import error: {e}", exc_info=True)
                import traceback
                traceback.print_exc()
                GLib.idle_add(self._on_import_error, str(e))
        
        thread = threading.Thread(target=import_thread, daemon=True)
        thread.start()
    
    def _on_import_complete(self, result):
        """Handle successful import (runs in main thread).
        
        Args:
            result: Dict with import results (model_id, sbml_path, document_model, etc.)
        """
        try:
            model_id = result['model_id']
            sbml_path = result['sbml_path']
            processed_pathway = result['processed_pathway']
            document_model = result['document_model']
            
            self.logger.info(f"Import complete, saving to project: {model_id}")
            
            # Save to project
            saved_filepath = self._save_to_project(
                sbml_path,
                processed_pathway,
                document_model
            )
            
            if not saved_filepath:
                self._show_status("❌ Failed to save to project", error=True)
                self.import_button.set_sensitive(True)
                return False
            
            self.logger.info(f"Saved to: {saved_filepath}")
            
            # Auto-load to canvas (same pattern as SBML category)
            self._auto_load_to_canvas(
                model_id=model_id,
                saved_filepath=saved_filepath,
                document_model=document_model
            )
            
            # Notify parent if callback set (for BRENDA integration)
            if self.import_complete_callback:
                import_data = {
                    'model_id': model_id,
                    'filepath': saved_filepath,
                    'document_model': document_model
                }
                self.import_complete_callback(import_data)
            
        except Exception as e:
            self.logger.error(f"Post-import processing failed: {e}")
            import traceback
            traceback.print_exc()
            self._show_status(f"❌ Post-import failed: {e}", error=True)
            self.import_button.set_sensitive(True)
        
        return False
    
    def _on_import_error(self, error_msg: str):
        """Handle import error (runs in main thread).
        
        Args:
            error_msg: Error message
        """
        self._show_status(f"✗ Import failed: {error_msg}", error=True)
        self.import_button.set_sensitive(True)
        return False
    
    def _show_status(self, message: str, error: bool = False):
        """Show status message (Wayland-safe).
        
        Args:
            message: Status message
            error: If True, display as error (red text)
        """
        if error:
            self.status_label.set_markup(f"<span color='red'>{message}</span>")
        else:
            self.status_label.set_text(message)
    
    def _save_to_project(self, sbml_path: str, processed_pathway, doc_model):
        """Save imported BiGG model to project.
        
        Saves:
        1. Copy SBML file to project/pathways/
        2. Save .shy model to project/models/
        
        Args:
            sbml_path: Path to downloaded SBML file
            processed_pathway: Processed pathway data
            doc_model: Document model to save
        
        Returns:
            str: Absolute path to saved .shy file, or None if failed
        """
        if not self.project:
            self.logger.warning("No project available for saving")
            return None
        
        try:
            filename = os.path.basename(sbml_path)
            base_name = os.path.splitext(filename)[0]
            
            # 1. Copy SBML file to project/pathways/
            pathways_dir = self.project.get_pathways_dir()
            if not pathways_dir:
                raise ValueError("Project pathways directory not available")
            
            os.makedirs(pathways_dir, exist_ok=True)
            dest_sbml_path = os.path.join(pathways_dir, filename)
            
            # Copy SBML file
            if os.path.exists(sbml_path):
                with open(sbml_path, 'r', encoding='utf-8') as f:
                    sbml_content = f.read()
                
                with open(dest_sbml_path, 'w', encoding='utf-8') as f:
                    f.write(sbml_content)
                
                self.logger.info(f"SBML file saved to: {dest_sbml_path}")
            else:
                raise ValueError(f"Source file not found: {sbml_path}")
            
            # 2. Save .shy model file to project/models/
            model_filename = f"{base_name}.shy"
            models_dir = self.project.get_models_dir()
            if not models_dir:
                raise ValueError("Project models directory not available")
            
            os.makedirs(models_dir, exist_ok=True)
            dest_model_path = os.path.join(models_dir, model_filename)
            
            # Save model
            doc_model.save_to_file(dest_model_path)
            self.logger.info(f"Model saved to: {dest_model_path}")
            
            return dest_model_path
            
        except Exception as e:
            self.logger.error(f"Failed to save to project: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _auto_load_to_canvas(self, model_id: str, saved_filepath: str, document_model):
        """Auto-load imported model to canvas (same pattern as SBML category).
        
        Args:
            model_id: BiGG model ID
            saved_filepath: Path to saved .shy file
            document_model: DocumentModel to load
        """
        self.logger.info("=== Starting BiGG canvas auto-load ===")
        
        # Use normalized method to get canvas loader
        canvas_loader = self._get_canvas_loader()
        
        if self.model_canvas:
            self.logger.info(f"model_canvas type: {type(self.model_canvas).__name__}")
            self.logger.info(f"canvas_loader available: {canvas_loader is not None}")
        else:
            self.logger.error("model_canvas is None! Cannot auto-load to canvas.")
        
        if not canvas_loader:
            self.logger.warning("Canvas auto-load skipped: model_canvas not available or doesn't have add_document")
            self._show_status(
                f"✅ Model saved successfully:\n{saved_filepath}\n\n"
                f"💡 Open the model: File → Open or double-click in file explorer"
            )
            self.import_button.set_sensitive(True)
            return
        
        def do_canvas_load():
            """Deferred canvas loading to keep UI responsive."""
            try:
                self.logger.info(f"✓ Auto-loading {model_id} into new canvas tab...")
                
                # CRITICAL: Create canvas with temporary filename to avoid loading
                # stale view state from previous imports of same model
                self.logger.info("[BIGG AUTO-LOAD] Step 1: Calling add_document()...")
                page_index, drawing_area = canvas_loader.add_document(filename="importing_temp")
                self.logger.info(f"[BIGG AUTO-LOAD] Step 2: add_document() returned page_index={page_index}, drawing_area={id(drawing_area) if drawing_area else 'None'}")
                
                if drawing_area is None:
                    raise ValueError("add_document() returned None for drawing_area")
                
                canvas_manager = canvas_loader.get_canvas_manager(drawing_area)
                self.logger.info(f"[BIGG AUTO-LOAD] Step 3: get_canvas_manager() returned canvas_manager={canvas_manager is not None} (type={type(canvas_manager).__name__ if canvas_manager else 'None'})")
                if not canvas_manager:
                    raise ValueError("get_canvas_manager() returned None")
                
                # CRITICAL: Set filepath FIRST before load_objects
                # This ensures the correct filename is used for any auto-save operations
                self.logger.info(f"[BIGG AUTO-LOAD] Step 4: Setting filepath to {saved_filepath}")
                canvas_manager.set_filepath(saved_filepath)
                
                # Load objects to canvas
                self.logger.info(f"[BIGG AUTO-LOAD] Step 5: Loading objects (places={len(document_model.places)}, transitions={len(document_model.transitions)}, arcs={len(document_model.arcs)})")
                canvas_manager.load_objects(
                    places=document_model.places,
                    transitions=document_model.transitions,
                    arcs=document_model.arcs,
                    modules=document_model.modules
                )
                self.logger.info("[BIGG AUTO-LOAD] Step 6: load_objects() completed successfully")
                
                # CRITICAL: Copy metadata to canvas manager's document
                # This ensures metadata is available for tab-switch and metadata inspector
                if hasattr(canvas_manager, 'document') and hasattr(document_model, 'metadata'):
                    # Copy metadata keys individually (document.metadata is a property)
                    for key, value in document_model.metadata.items():
                        canvas_manager.document.metadata[key] = value
                    self.logger.info(f"Copied metadata to canvas document ({len(document_model.metadata)} keys)")
                
                # Set change callback
                if hasattr(canvas_manager, 'document_controller') and canvas_manager.document_controller:
                    canvas_manager.document_controller.set_change_callback(
                        canvas_manager._on_object_changed
                    )
                
                # Mark clean and as imported
                canvas_manager.mark_clean()
                canvas_manager.mark_as_imported(model_id)
                
                # CRITICAL: Ensure callbacks are enabled before display
                # (Should already be False from setup, but verify)
                if hasattr(canvas_manager, '_suppress_callbacks'):
                    canvas_manager._suppress_callbacks = False
                    self.logger.info(f"Callbacks enabled: _suppress_callbacks={canvas_manager._suppress_callbacks}")
                
                # Fit to page
                canvas_manager.fit_to_page(
                    padding_percent=15,
                    deferred=True,
                    horizontal_offset_percent=30,
                    vertical_offset_percent=-10
                )
                
                # Force redraw
                canvas_manager.mark_needs_redraw()
                
                # Ensure simulation reset
                if hasattr(canvas_loader, '_ensure_simulation_reset'):
                    canvas_loader._ensure_simulation_reset(drawing_area)
                
                # REPORT PANEL: Trigger refresh after BiGG import (deferred)
                # Use GLib.idle_add to ensure this happens AFTER tab switch completes
                if drawing_area in canvas_loader.overlay_managers:
                    from gi.repository import GLib
                    
                    def refresh_report_panel():
                        """Deferred refresh to ensure tab switch completes first."""
                        overlay_manager = canvas_loader.overlay_managers.get(drawing_area)
                        if overlay_manager and hasattr(overlay_manager, 'report_panel_loader'):
                            report_panel_loader = overlay_manager.report_panel_loader
                            if report_panel_loader and hasattr(report_panel_loader, 'panel'):
                                self.logger.info("Triggering Report Panel refresh after BiGG import (deferred)")
                                simulation_controller = getattr(overlay_manager, 'simulation_controller', None)
                                if simulation_controller:
                                    from shypn.events import EventBus
                                    from shypn.core.document_id import doc_id
                                    EventBus.emit('simulation.controller_ready',
                                                  {'controller': simulation_controller},
                                                  document_id=doc_id(drawing_area))
                                    self.logger.info("✅ Report Panel controller notified")
                                
                                # CRITICAL: Call on_file_opened to load metadata (same as File→Open)
                                # Determine metadata path based on project structure
                                if self.project and hasattr(self.project, 'get_metadata_dir'):
                                    metadata_dir = self.project.get_metadata_dir()
                                    if metadata_dir:
                                        # Look for metadata in project/metadata/ directory
                                        import os
                                        model_filename = f"{model_id}.shypn"
                                        shypn_path = os.path.join(metadata_dir, model_filename)
                                    else:
                                        # Fallback: look alongside model file
                                        shypn_path = saved_filepath.replace('.shy', '.shypn')
                                else:
                                    # No project context: look alongside model file
                                    shypn_path = saved_filepath.replace('.shy', '.shypn')
                                
                                if hasattr(report_panel_loader.panel, 'on_file_opened'):
                                    report_panel_loader.panel.on_file_opened(shypn_path)
                                    self.logger.info(f"✅ Metadata loaded from: {shypn_path}")
                            return False  # Don't repeat
                        
                        GLib.idle_add(refresh_report_panel)
                        self.logger.info("Report Panel refresh scheduled (idle)")
                
                self.logger.info("=== BiGG canvas auto-load COMPLETED ===")
                self._show_status(
                    f"✅ Model loaded to canvas: {model_id}\n"
                    f"💡 Use View → Fit to Page (Ctrl+0) to adjust view if needed"
                )
                self.import_button.set_sensitive(True)
                
            except Exception as load_error:
                self.logger.error("=== BiGG canvas auto-load FAILED ===")
                self.logger.error(f"Failed to auto-load: {load_error}")
                import traceback
                traceback.print_exc()
                self._show_status(
                    f"✅ Model saved to {saved_filepath}\n"
                    f"⚠️ Auto-load failed, use File → Open to load manually"
                )
                self.import_button.set_sensitive(True)
            
            return False  # Don't repeat GLib.idle_add
        
        # Schedule canvas loading on idle
        self.logger.info(f"[BIGG] Scheduling do_canvas_load() via GLib.idle_add (canvas_loader={canvas_loader is not None}, document_model={document_model is not None}, saved_filepath={saved_filepath})")
        GLib.idle_add(do_canvas_load)
        self.logger.info("[BIGG] GLib.idle_add(do_canvas_load) called successfully")
    
    # ========================================================================
    # Category Interface (from BasePathwayCategory)
    # ========================================================================
    
    def set_project(self, project):
        """Set current project (called by PathwayOperationsPanel).
        
        Args:
            project: Current project instance
        """
        self.project = project
        self.logger.debug(f"Project set: {project}")
    
    def set_model_canvas(self, model_canvas):
        """Set model canvas (called by PathwayOperationsPanel).
        
        Args:
            model_canvas: ModelCanvas instance
        """
        self.model_canvas = model_canvas
        self.logger.debug(f"Model canvas set: {model_canvas}")
    
    def _on_metadata_expander_toggled(self, expander, param):
        """Called when user expands/collapses the metadata inspector.
        Populates metadata only when expanded to avoid cascade issues.
        
        Args:
            expander: The Gtk.Expander widget
            param: The parameter (notify signal)
        """
        if expander.get_expanded():
            self.refresh_metadata_inspector()
    
    def on_tab_switched(self):
        """Handle tab switch event (called by PathwayOperationsPanel).
        
        Note: Metadata inspector refresh is deferred until user expands it.
        
        Updates the BiGG panel to reflect the currently active model:
        - Updates status labels
        """
        self.logger.debug("Tab switched, updating BiGG panel state")
    
    def refresh_metadata_inspector(self):
        """Refresh BiGG Metadata Inspector for the currently active document.
        This method is called when the user expands the metadata inspector.
        It populates the metadata tree and summary from the current document.
        """
        # Get current document using normalized method
        document = None
        canvas_manager = self._get_canvas_manager()
        
        if canvas_manager:
            try:
                # Always use _document_model (document property returns self)
                if hasattr(canvas_manager, '_document_model'):
                    document = canvas_manager._document_model
            except Exception as e:
                self.logger.warning(f"Could not get document for metadata refresh: {e}")
        
        # Update metadata based on active document
        if document:
            # Check if BiGG model
            is_bigg = False
            if hasattr(document, 'metadata') and document.metadata:
                source = document.metadata.get('source')
                data_source = document.metadata.get('data_source')
                is_bigg = (source == 'bigg_import' or data_source == 'bigg_import')
            
            if is_bigg:
                self.status_label.set_text("BiGG model loaded")
                
                # Load SBML metadata from document metadata if available
                sbml_data = document.metadata.get('bigg_sbml_data')
                if sbml_data:
                    self._load_sbml_metadata_from_dict(sbml_data)
                    self.logger.debug(f"Metadata inspector refreshed for BiGG model: {document.metadata.get('model_id', 'unknown')}")
                else:
                    # Clear for old BiGG models without saved metadata
                    self.sbml_metadata_store.clear()
                    self.status_label.set_text("BiGG model (legacy import - metadata not saved)")
            else:
                self.status_label.set_markup(
                    '<span size="small">Not a BiGG model</span>'
                )
                # Clear metadata tree for non-BiGG models
                self.sbml_metadata_store.clear()
        else:
            # No document - clear metadata
            self.status_label.set_markup(
                '<span size="small">No model loaded</span>'
            )
            self.sbml_metadata_store.clear()
    
    def _load_sbml_metadata_from_dict(self, sbml_data):
        """Load and display SBML metadata from saved dictionary.
        
        Args:
            sbml_data: Dictionary with saved BiGG/SBML pathway data
        """
        def do_update():
            try:
                self.sbml_metadata_store.clear()
                
                # Model Info section
                if 'model_id' in sbml_data or 'model_name' in sbml_data:
                    info_root = self.sbml_metadata_store.append(None, [
                        "🆔", "Model Info", "",
                        "", "Section", False, "model_info"
                    ])
                    if 'model_id' in sbml_data:
                        self.sbml_metadata_store.append(info_root, [
                            "🆔", "Model ID", sbml_data['model_id'],
                            "", "Text", False, "model_id"
                        ])
                    if 'model_name' in sbml_data:
                        self.sbml_metadata_store.append(info_root, [
                            "📝", "Name", sbml_data['model_name'],
                            "", "Text", False, "model_name"
                        ])
                
                # Statistics section
                stats_root = self.sbml_metadata_store.append(None, [
                    "📊", "Statistics", "",
                    "", "Section", False, "statistics"
                ])
                
                # Compartments
                if 'compartments_count' in sbml_data:
                    self.sbml_metadata_store.append(stats_root, [
                        "📦", "Compartments", str(sbml_data['compartments_count']),
                        "", "Number", False, "compartments_count"
                    ])
                
                # Species
                if 'species_count' in sbml_data:
                    self.sbml_metadata_store.append(stats_root, [
                        "🧬", "Species", str(sbml_data['species_count']),
                        "", "Number", False, "species_count"
                    ])
                
                # Reactions
                if 'reactions_count' in sbml_data:
                    self.sbml_metadata_store.append(stats_root, [
                        "⚡", "Reactions", str(sbml_data['reactions_count']),
                        "", "Number", False, "reactions_count"
                    ])
                
                # Parameters
                if 'parameters_count' in sbml_data:
                    self.sbml_metadata_store.append(stats_root, [
                        "⚙️", "Parameters", str(sbml_data['parameters_count']),
                        "", "Number", False, "parameters_count"
                    ])
                
                # Expand all tree rows
                self.sbml_metadata_tree.expand_all()
                
                self.logger.info("BiGG metadata inspector updated from saved data")
                
            except Exception as e:
                self.logger.error(f"Failed to load BiGG metadata from dict: {e}")
                import traceback
                traceback.print_exc()
        
        # Use idle_add to ensure GTK updates on main thread
        from gi.repository import GLib
        GLib.idle_add(do_update)
    
    # ========================================================================
    # Wayland-Safe Cleanup
    # ========================================================================
    
    def cleanup(self):
        """Clean up all widgets and signal handlers (Wayland-safe)."""
        self.logger.debug("Cleaning up BiGG category")
        
        # Disconnect signal handlers
        for handler_id, widget in self._signal_handlers:
            try:
                if widget and not widget.is_destroyed():
                    widget.disconnect(handler_id)
            except (AttributeError, TypeError) as e:
                # Widget already destroyed or invalid
                import logging
                logging.getLogger(__name__).debug(f"Signal disconnect failed: {e}")
                pass
        self._signal_handlers.clear()
        
        # Clean up child widgets
        for widget in self._widgets:
            if widget and not widget.is_destroyed():
                if hasattr(widget, 'cleanup'):
                    widget.cleanup()
                widget.destroy()
        self._widgets.clear()
        
        self.logger.debug("BiGG category cleanup complete")
    
    def __del__(self):
        """Ensure cleanup on garbage collection."""
        try:
            self.cleanup()
        except (AttributeError, TypeError) as e:
            # Cleanup failed during garbage collection
            import logging
            logging.getLogger(__name__).debug(f"Cleanup in __del__ failed: {e}")
            pass
