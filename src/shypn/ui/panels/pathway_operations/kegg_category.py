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
from __future__ import annotations

import os
import sys
import time
import logging
import threading
from typing import Optional, Dict, Any
import gi  # type: ignore[import-untyped]
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, GLib, Pango  # type: ignore[import-untyped]
from .base_pathway_category import BasePathwayCategory
from shypn.data.project_models import get_project_manager
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
class KEGGCategory(BasePathwayCategory):  # type: ignore[misc]
    """KEGG import category for Pathway Operations Panel.
    Contains:
    - Pathway ID input
    - Import options (cofactor filtering, coordinate scaling)
    - Preview area (pathway info)
    - Import button (fetch + convert + save)
    - Status display
    """
    def __init__(self, expanded=False, model_canvas=None, project=None, parent_window=None):
        """Initialize KEGG category.
        Args:
            expanded: Whether category starts expanded
            model_canvas: ModelCanvasManager instance (optional)
            project: Project instance for metadata tracking (optional)
            parent_window: Parent window for dialogs (Wayland fix)
        """
        # Initialize attributes BEFORE calling super().__init__()
        # because _build_content() is called during super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        # Set project, canvas, and parent window
        self.model_canvas = model_canvas
        self.project = project
        self.parent_window = parent_window
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
    def on_model_loaded(self):
        """Called when a model is loaded into the canvas.
        Updates enrichment button states based on the loaded model.
        This should be called by the canvas loader after any model is opened.
        """
        # Check if it's a KEGG model by checking transitions for KEGG metadata
        document = None
        # Use normalized method to get canvas manager
        canvas_manager = self._get_canvas_manager()
        if canvas_manager:
            try:
                if hasattr(canvas_manager, 'document'):
                    document = canvas_manager.document
            except Exception as e:
                self.logger.warning(f"Could not get document: {e}")
        if not document:
            # No document loaded, disable buttons
            self.enrich_button.set_sensitive(False)
            self.stoich_enrich_button.set_sensitive(False)
            return
        # Check if it's a KEGG import by looking for KEGG metadata
        is_kegg = False
        if hasattr(document, 'metadata') and document.metadata:
            is_kegg = document.metadata.get('data_source') == 'kegg_import'
        # Also check transitions for KEGG reaction IDs
        if not is_kegg and document.transitions:
            for t in document.transitions[:5]:  # Check first few
                if hasattr(t, 'metadata') and t.metadata:
                    if t.metadata.get('kegg_reaction_id') or t.metadata.get('data_source') == 'kegg_import':
                        is_kegg = True
                        break
        if is_kegg:
            self.logger.info("KEGG model detected, enabling enrichment buttons")
            self.stoich_enrich_button.set_sensitive(True)
            self._check_stoich_enrichment_candidates()
        else:
            self.logger.info("Non-KEGG model loaded, disabling KEGG enrichment buttons")
            self.stoich_enrich_button.set_sensitive(False)
    
    def on_tab_switched(self):
        """Called when the user switches to a different model tab.
        Updates the KEGG panel to reflect the currently active model:
        - Refreshes enrichment button states
        - Updates status labels
        - Clears old pathway info if model changed
        
        Note: Metadata inspector refresh is deferred until user expands it.
        """
        self.logger.debug("Tab switched, updating KEGG panel state")
        
        # Update enrichment buttons only (not metadata display)
        self._update_enrichment_buttons()
        
        # Get current document
        document = None
        # Use normalized method to get canvas manager
        canvas_manager = self._get_canvas_manager()
        if canvas_manager:
            try:
                if hasattr(canvas_manager, 'document'):
                    document = canvas_manager.document
            except Exception as e:
                self.logger.warning(f"Could not get document on tab switch: {e}")
        # Update enrichment buttons based on new active model
        if document:
            # Check if KEGG model
            is_kegg = False
            if hasattr(document, 'metadata') and document.metadata:
                is_kegg = document.metadata.get('data_source') == 'kegg_import'
            if is_kegg:
                self.stoich_enrich_button.set_sensitive(True)
                self._check_stoich_enrichment_candidates()
            else:
                self.stoich_enrich_button.set_sensitive(False)
                self.stoich_status_label.set_markup(
                    '<span size="small">Not a KEGG model</span>'
                )
        else:
            # No document - disable buttons
            self.stoich_enrich_button.set_sensitive(False)
            self.stoich_status_label.set_markup(
                '<span size="small">No model loaded</span>'
            )
    def on_model_closed(self):
        """Called when the active model/tab is closed.
        Clears all KEGG panel state to prevent stale data.
        """
        self.logger.debug("Model closed, clearing KEGG panel")
        self.clear_panel()
    def clear_panel(self):
        """Clear all KEGG panel state.
        This should be called when:
        - A model is closed
        - User switches to a different model tab
        - Panel needs to be reset
        """
        self.logger.debug("Clearing KEGG panel state")
        # Clear current pathway data
        self.current_pathway = None
        self.current_kgml = None
        self.current_pathway_id = None
        self.current_pathway_doc = None
        # Clear input
        self.accession_entry.set_text("")
        # Clear preview
        self.preview_label.set_text("No pathway loaded")
        # Clear status
        self.status_label.set_text("")
        # Disable and clear enrichment states
        self.stoich_enrich_button.set_sensitive(False)
        self.stoich_status_label.set_markup(
            '<span size="small">No model loaded</span>'
        )
        # Reset import button
        self.import_button.set_sensitive(True)
        self.import_button.set_label("Import")
    
    def set_model_canvas(self, model_canvas):
        """Override to handle tab switching.
        Called when the active model canvas changes (tab switch).
        Updates panel state to reflect the current model.
        
        Note: Metadata inspector refresh is deferred until user expands it.
        
        Args:
            model_canvas: ModelCanvasLoader or ModelCanvasManager instance
        """
        # Call parent implementation to update model_canvas reference
        super().set_model_canvas(model_canvas)
        
        # Store current expanded state before refresh
        was_expanded = self.expanded
        
        # Trigger tab switch handling (enrichment buttons only)
        self.on_tab_switched()
        
        # Restore expanded state if it was expanded (don't auto-collapse during import)
        if was_expanded:
            self.set_expanded(True)

    def _update_enrichment_buttons(self):
        """Update enrichment button states based on current document.
        Separated from metadata refresh to avoid cascade issues.
        """
        # Get current document using normalized method
        document = None
        canvas_manager = self._get_canvas_manager()
        if canvas_manager:
            try:
                if hasattr(canvas_manager, 'document'):
                    document = canvas_manager.document
                elif hasattr(canvas_manager, '_document_model'):
                    document = canvas_manager._document_model
            except Exception as e:
                self.logger.warning(f"Could not get document for button update: {e}")
        
        # Update enrichment buttons based on active document
        if document:
            # Check if KEGG model
            is_kegg = False
            if hasattr(document, 'metadata') and document.metadata:
                is_kegg = (document.metadata.get('source') == 'kegg_import' or 
                          document.metadata.get('data_source') == 'kegg_import')
            
            if is_kegg:
                # Enable enrichment for KEGG models
                self.stoich_enrich_button.set_sensitive(True)
                self._check_stoich_enrichment_candidates()
            else:
                # Not a KEGG model - disable buttons
                self.stoich_enrich_button.set_sensitive(False)
                self.stoich_status_label.set_markup('<span size="small">Not a KEGG model</span>')
        else:
            # No document - disable buttons
            self.stoich_enrich_button.set_sensitive(False)
            self.stoich_status_label.set_markup('<span size="small">No model loaded</span>')
    
    def _is_signaling_pathway(self, pathway_id: str) -> bool:
        """Detect if a pathway is a signaling pathway based on KEGG classification.
        KEGG pathway classification:
        - 01xxx: Metabolism (need filtering to remove isolated compounds)
        - 02xxx: Genetic Information Processing
        - 03xxx: Environmental Information Processing  
        - 04xxx: Cellular Processes (mostly signaling, no filtering)
        - 05xxx: Human Diseases
        Signaling pathways (04xxx) have many proteins with only regulatory relations
        (no reactions), so filtering would remove most of the network.
        Args:
            pathway_id: KEGG pathway ID (e.g., 'hsa04010', 'hsa00010')
        Returns:
            True if signaling pathway (should NOT be filtered), False otherwise
        """
        # Extract numeric part (e.g., 'hsa04010' -> '04010')
        numeric_id = ''.join(c for c in pathway_id if c.isdigit())
        if len(numeric_id) >= 5:
            # Check first two digits
            category = numeric_id[:2]
            return category == '04'  # Signaling and cellular processes
        return False
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
        main_box.pack_start(preview_box, False, False, 0)
        # Save to Project button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.END)
        self.import_button = Gtk.Button(label="Save to Project")
        self.import_button.set_size_request(150, -1)
        self.import_button.connect('clicked', self._on_import_clicked)
        button_box.pack_start(self.import_button, False, False, 0)
        main_box.pack_start(button_box, False, False, 0)
        # Status label (at the end)
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self.status_label.set_line_wrap(True)
        self.status_label.get_style_context().add_class("dim-label")
        main_box.pack_start(self.status_label, False, False, 0)
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
        # Entry with browse button for local mode
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.pathway_id_entry = Gtk.Entry()
        self.pathway_id_entry.set_placeholder_text("e.g., hsa00010, eco00020")
        self.pathway_id_entry.connect('changed', self._on_accession_entry_changed)
        entry_box.pack_start(self.pathway_id_entry, True, True, 0)
        # Browse button (only visible in local mode)
        self.browse_button = Gtk.Button(label="Browse...")
        self.browse_button.set_no_show_all(True)  # Hidden by default
        self.browse_button.set_visible(False)
        self.browse_button.connect('clicked', self._on_browse_clicked)
        entry_box.pack_start(self.browse_button, False, False, 0)
        box.pack_start(entry_box, False, False, 0)
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
        # NOTE: Cofactor inclusion removed - now handled by Stoichiometry Enrichment
        # NOTE: Catalyst places removed - always shown (Biological Petri Net mode)
        # Both options deprecated as of 2026-01-01
        # Separator before enrichment section
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(separator, False, False, 6)
        # NOTE: "Enrich Names from KEGG API" button removed - deprecated as of 2026-01-01
        # Name enrichment now handled automatically via cross-reference database
        # See: thermodynamics/database/xref/
        # Stoichiometry enrichment button (add cofactors)
        stoich_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.stoich_enrich_button = Gtk.Button(label="Enrich Stoichiometry (Add Cofactors)")
        self.stoich_enrich_button.set_sensitive(False)  # Enabled after import
        self.stoich_enrich_button.set_tooltip_text(
            "Add missing cofactors (ATP, NADH, CoA, etc.) to reactions.\n\n"
            "KEGG KGML files omit cofactors to keep visualizations clean,\n"
            "but this makes models incomplete for signal hierarchy and thermodynamic analysis.\n\n"
            "This operation queries KEGG REACTION database (~1-2s per reaction)\n"
            "to get complete stoichiometry and adds missing compounds to the model.\n\n"
            "⚠️ IMPORTANT: Run this BEFORE signal hierarchy analysis!"
        )
        self.stoich_enrich_button.connect('clicked', self._on_enrich_stoichiometry_clicked)
        stoich_box.pack_start(self.stoich_enrich_button, False, False, 0)
        # Stoichiometry enrichment status label
        self.stoich_status_label = Gtk.Label()
        self.stoich_status_label.set_xalign(0)
        self.stoich_status_label.set_line_wrap(True)
        self.stoich_status_label.get_style_context().add_class("dim-label")
        stoich_box.pack_start(self.stoich_status_label, True, True, 0)
        box.pack_start(stoich_box, False, False, 0)
        return box
    def _build_preview(self):
        """Build preview section with metadata tree view.
        Returns:
            Gtk.Expander: Preview widgets under expander
        """
        self.metadata_expander = Gtk.Expander(label="KEGG Metadata Inspector")
        self.metadata_expander.set_expanded(False)
        
        # Connect to expansion event - populate metadata when user expands
        self.metadata_expander.connect("notify::expanded", self._on_metadata_expander_toggled)
        
        # Main container with notebook for tabs
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        # Tab 1: Tree view for structured metadata
        tree_scroll = Gtk.ScrolledWindow()
        tree_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        tree_scroll.set_size_request(-1, 200)
        # Tree store: [icon, name, value, type, object_id, tooltip]
        self.metadata_store = Gtk.TreeStore(str, str, str, str, str, str)
        self.metadata_tree = Gtk.TreeView(model=self.metadata_store)
        self.metadata_tree.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.metadata_tree.set_enable_tree_lines(True)
        self.metadata_tree.set_tooltip_column(5)  # Tooltip from column 5
        # Icon column
        icon_renderer = Gtk.CellRendererText()
        icon_col = Gtk.TreeViewColumn("", icon_renderer, text=0)
        icon_col.set_fixed_width(30)
        self.metadata_tree.append_column(icon_col)
        # Name column
        name_renderer = Gtk.CellRendererText()
        name_col = Gtk.TreeViewColumn("Name", name_renderer, text=1)
        name_col.set_resizable(True)
        name_col.set_expand(True)
        self.metadata_tree.append_column(name_col)
        # Value column
        value_renderer = Gtk.CellRendererText()
        value_renderer.set_property("family", "monospace")
        value_col = Gtk.TreeViewColumn("Value", value_renderer, text=2)
        value_col.set_resizable(True)
        value_col.set_expand(True)
        self.metadata_tree.append_column(value_col)
        # Connect click handler for details
        self.metadata_tree.connect("row-activated", self._on_metadata_row_clicked)
        tree_scroll.add(self.metadata_tree)
        notebook.append_page(tree_scroll, Gtk.Label(label="📊 Metadata Tree"))
        # Tab 2: Text view for summary
        text_scroll = Gtk.ScrolledWindow()
        text_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.preview_text = Gtk.TextView()
        self.preview_text.set_editable(False)
        self.preview_text.set_wrap_mode(Pango.WrapMode.WORD)
        self.preview_text.set_left_margin(6)
        self.preview_text.set_right_margin(6)
        self.preview_text.set_top_margin(6)
        self.preview_text.set_bottom_margin(6)
        buffer = self.preview_text.get_buffer()
        buffer.set_text(
            "Pathway summary will appear here after import...\n\n"
            "Click the 'Metadata Tree' tab to see detailed KEGG information."
        )
        text_scroll.add(self.preview_text)
        notebook.append_page(text_scroll, Gtk.Label(label="📄 Summary"))
        self.preview_widget = self.preview_text
        self.metadata_expander.add(notebook)
        return self.metadata_expander
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
            self.browse_button.set_visible(True)
            self.accession_help_label.set_markup(
                '<span size="small">Enter full path to local KGML file (.kgml or .xml)\n'
                'Local files may exist in project/pathways/ from previous imports</span>'
            )
            # Check if valid file path entered
            self._on_accession_entry_changed(self.pathway_id_entry)
        else:
            # Remote mode - update UI for KEGG API
            self.pathway_id_entry.set_placeholder_text("e.g., hsa00010, eco00020")
            self.browse_button.set_visible(False)
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
                # Trigger preview parse
                self._parse_and_preview_kgml(text)
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
    def _on_browse_clicked(self, button):
        """Handle browse button click - open file chooser for KGML files."""
        dialog = Gtk.FileChooserDialog(
            title="Select KEGG File",
            transient_for=self.parent_window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Set initial directory to project's pathways folder if project is open
        project_manager = get_project_manager()
        if project_manager.current_project:
            pathways_dir = os.path.join(project_manager.current_project.base_path, 'pathways')
            if os.path.exists(pathways_dir):
                dialog.set_current_folder(pathways_dir)
            else:
                dialog.set_current_folder(project_manager.current_project.base_path)
        
        # Add file filters
        filter_kegg = Gtk.FileFilter()
        filter_kegg.set_name("KEGG Files")
        filter_kegg.add_pattern("*.kgml")
        filter_kegg.add_pattern("*.xml")
        dialog.add_filter(filter_kegg)
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        
        # Focus on filename entry instead of search
        dialog.set_current_name("")
        
        # Wayland-safe async approach
        result_container = [None]
        def on_response(dlg, response_id):
            if response_id == Gtk.ResponseType.OK:
                result_container[0] = dlg.get_filename()
            dlg.destroy()
            Gtk.main_quit()
        dialog.connect('response', on_response)
        dialog.show()
        Gtk.main()
        filepath = result_container[0]
        if filepath:
            self.pathway_id_entry.set_text(filepath)
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
                "No project open. Please open or create a project first:\n"
                "File → New Project or File → Open Project"
            )
            return
        # Get input text
        input_text = self.pathway_id_entry.get_text().strip()
        if not input_text:
            self._show_error("Please enter a pathway ID or file path")
            return
        # Check if user entered a BioModels ID by mistake
        if input_text.upper().startswith('BIOMD'):
            self._show_error(
                f"'{input_text}' appears to be a BioModels ID.\n\n"
                "BioModels use SBML format, not KEGG format.\n"
                "Please use the SBML category above to import BioModels."
            )
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
    def _parse_and_preview_kgml(self, filepath):
        """Parse a local KGML file in background and populate metadata preview.
        This method is called when browsing local files to show a preview
        before importing. Similar to SBML's preview functionality.
        Args:
            filepath: Path to KGML file
        """
        def parse_in_background():
            try:
                self.logger.info(f"Parsing KGML file for preview: {filepath}")
                # Read KGML from file
                with open(filepath, 'r', encoding='utf-8') as f:
                    kgml_data = f.read()
                # Parse KGML (no conversion, just parse for metadata)
                parsed_pathway = self.parser.parse(kgml_data)
                # Cache for later import
                self.parsed_pathway = parsed_pathway
                self.current_filepath = filepath
                
                # Update metadata tree on main thread (no auto-expansion)
                def update_metadata():
                    self._update_metadata_tree_from_parsed(parsed_pathway)
                    return False
                GLib.idle_add(update_metadata)
                
                # Update preview text
                def update_preview_text():
                    buffer = self.preview_text.get_buffer()
                    summary = f"KEGG Pathway Preview\\n{'='*50}\\n\\n"
                    summary += f"Pathway ID: {parsed_pathway.name}\\n"
                    summary += f"Title: {parsed_pathway.title}\\n"
                    summary += f"Organism: {parsed_pathway.org}\\n\\n"
                    entry_counts = parsed_pathway.count_entry_types()
                    summary += "Entries:\\n"
                    summary += "".join(
                        f"  {entry_type}: {count}\\n"
                        for entry_type, count in entry_counts.items()
                    )
                    summary += f"\\nReactions: {len(parsed_pathway.reactions)}\\n"
                    summary += f"Relations: {len(parsed_pathway.relations)}\\n"
                    buffer.set_text(summary)
                    return False
                GLib.idle_add(update_preview_text)
                self.logger.info("KGML preview completed successfully")
            except Exception as e:
                self.logger.error(f"Failed to parse KGML for preview: {e}")
                import traceback
                traceback.print_exc()
                def show_error():
                    buffer = self.preview_text.get_buffer()
                    buffer.set_text(f"Error parsing KGML file:\\n{str(e)}")
                    return False
                GLib.idle_add(show_error)
        # Run parse in background thread to avoid UI freeze
        thread = threading.Thread(target=parse_in_background, daemon=True)
        thread.start()
    def _process_local_kgml(self, filepath):
        """Process a local KGML file in background thread.
        Args:
            filepath: Path to KGML file
        """
        def parse_and_convert():
            try:
                self.logger.info(f"Processing local KGML file: {filepath}")
                # Check if we already parsed this file in preview
                if (hasattr(self, 'parsed_pathway') and self.parsed_pathway and 
                    hasattr(self, 'current_filepath') and self.current_filepath == filepath):
                    self.logger.info("Reusing cached parsed pathway from preview")
                    parsed_pathway = self.parsed_pathway
                    kgml_data = None  # Will read if needed later
                else:
                    # 1. Read KGML from file
                    with open(filepath, 'r', encoding='utf-8') as f:
                        kgml_data = f.read()
                    # 2. Parse KGML
                    parsed_pathway = self.parser.parse(kgml_data)
                # Extract pathway ID from filename (e.g., hsa00010.kgml -> hsa00010)
                filename = os.path.basename(filepath)
                pathway_id = os.path.splitext(filename)[0]
                # 2.5. Check for reversible reactions and show dialog
                # Reversible KEGG reactions can produce negative rates with mass-action kinetics
                reversible_reactions = [r for r in parsed_pathway.reactions if r.is_reversible()]
                if reversible_reactions:
                    # Create synthetic validation issues for dialog compatibility
                    validation_warning = {
                        'category': 'reversible_reactions',
                        'severity': 'warning',
                        'message': f'Reversible reactions detected ({len(reversible_reactions)} reactions)',
                        'reactions': [r.name for r in reversible_reactions]
                    }
                    # Show dialog on main thread and wait for user choice
                    user_choice_holder = [None]
                    def show_dialog_on_main_thread():
                        user_choice = self._show_stochastic_warning_dialog([validation_warning])
                        user_choice_holder[0] = user_choice
                        return False
                    GLib.idle_add(show_dialog_on_main_thread)
                    # Wait for user choice (with timeout)
                    timeout = 60
                    elapsed = 0
                    while user_choice_holder[0] is None and elapsed < timeout:
                        time.sleep(0.1)
                        elapsed += 0.1
                    user_choice = user_choice_holder[0]
                    if user_choice == 'cancel' or user_choice is None:
                        raise ValueError("Import cancelled by user")
                    elif user_choice in ['convert_continuous', 'convert_hybrid']:
                        # Store user choice in metadata for converter to apply
                        choice_map = {
                            'convert_continuous': 'continuous',
                            'convert_hybrid': 'hybrid',
                            'proceed_anyway': 'stochastic'
                        }
                        # Store in parsed_pathway metadata (will be passed to converter)
                        if not hasattr(parsed_pathway, 'metadata'):
                            parsed_pathway.metadata = {}
                        parsed_pathway.metadata['user_choice_transition_type'] = choice_map[user_choice]
                # VALIDATION: Check if pathway has reactions
                # shypn models biochemical and gene regulatory networks (with reactions/transitions)
                # Pure signaling pathways (only relations, no reactions) are not yet supported
                if not parsed_pathway.reactions:
                    is_signaling = self._is_signaling_pathway(pathway_id)
                    if is_signaling:
                        raise ValueError(
                            f"Pure signaling pathway detected ({pathway_id}).\n\n"
                            f"shypn is designed for biochemical and gene regulatory networks "
                            f"that have metabolic reactions or gene expression reactions.\n\n"
                            f"This pathway has {len(parsed_pathway.relations)} regulatory relations "
                            f"but no reactions to regulate.\n\n"
                            f"Signaling-only networks (protein-protein interactions without biochemical "
                            f"reactions) are not yet supported in the current model."
                        )
                    else:
                        raise ValueError(
                            f"No reactions found in pathway {pathway_id}. "
                            f"Cannot convert pathway without reactions."
                        )
                # 3. Convert to Petri net
                filter_cofactors = True  # Always include cofactors (mandatory)
                show_catalysts = True  # Always show enzyme places (mandatory)
                coordinate_scale = 2.5  # Optimal default scale for KEGG coordinates
                enhancement_options = EnhancementOptions(
                    enable_layout_optimization=True,
                    enable_arc_routing=False,  # KEGG import: straight arcs
                    enable_metadata_enhancement=True
                )
                # Apply filtering for metabolic pathways to remove isolated compounds
                # (cleaner visualization)
                self.logger.info(f"Converting pathway (cofactors={filter_cofactors}, catalysts={show_catalysts})")
                document_model = convert_pathway_enhanced(
                    parsed_pathway,
                    coordinate_scale=coordinate_scale,
                    include_cofactors=filter_cofactors,
                    filter_isolated_compounds=True,  # Filter isolated compounds for cleaner layout
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
                    'source': 'local',
                    'filepath': filepath  # Pass filepath for cache read if needed
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
                # 2.5. Reversible reactions handling (dialog disabled for now)
                # Reversible KEGG reactions can produce negative rates with mass-action kinetics
                # For now, proceed with default stochastic transitions
                # TODO: Re-enable dialog if user feedback requires it
                # VALIDATION: Check if pathway has reactions
                # shypn models biochemical and gene regulatory networks (with reactions/transitions)
                # Pure signaling pathways (only relations, no reactions) are not yet supported
                if not parsed_pathway.reactions:
                    is_signaling = self._is_signaling_pathway(pathway_id)
                    if is_signaling:
                        raise ValueError(
                            f"Pure signaling pathway detected ({pathway_id}).\n\n"
                            f"shypn is designed for biochemical and gene regulatory networks "
                            f"that have metabolic reactions or gene expression reactions.\n\n"
                            f"This pathway has {len(parsed_pathway.relations)} regulatory relations "
                            f"but no reactions to regulate.\n\n"
                            f"Signaling-only networks (protein-protein interactions without biochemical "
                            f"reactions) are not yet supported in the current model."
                        )
                    else:
                        raise ValueError(
                            f"No reactions found in pathway {pathway_id}. "
                            f"Cannot convert pathway without reactions."
                        )
                # 3. Convert to Petri net
                filter_cofactors = True  # Always include cofactors (mandatory)
                show_catalysts = True  # Always show enzyme places (mandatory)
                coordinate_scale = 2.5  # Optimal default scale for KEGG coordinates
                enhancement_options = EnhancementOptions(
                    enable_layout_optimization=True,
                    enable_arc_routing=False,  # KEGG import: straight arcs
                    enable_metadata_enhancement=True
                )
                # Apply filtering for metabolic pathways to remove isolated compounds
                # (cleaner visualization)
                self.logger.info(f"Converting pathway (cofactors={filter_cofactors}, catalysts={show_catalysts})")
                document_model = convert_pathway_enhanced(
                    parsed_pathway,
                    coordinate_scale=coordinate_scale,
                    include_cofactors=filter_cofactors,
                    filter_isolated_compounds=True,  # Filter isolated compounds for cleaner layout
                    create_enzyme_places=show_catalysts,
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
            # CRITICAL: Add metadata to document BEFORE saving/loading
            # This ensures metadata is available when tab-switch happens during auto-load
            if not hasattr(document_model, 'metadata'):
                document_model.metadata = {}
            document_model.metadata['source'] = 'kegg_import'
            document_model.metadata['data_source'] = 'kegg_import'
            document_model.metadata['pathway_id'] = pathway_id
            document_model.metadata['requires_fit_to_page'] = True
            document_model.metadata['coordinate_scale'] = coordinate_scale
            # Save KEGG PathwayData for metadata inspector
            if parsed_pathway:
                try:
                    pathway_dict = {
                        'pathway_id': pathway_id,
                        'name': getattr(parsed_pathway, 'name', pathway_id),
                        'title': getattr(parsed_pathway, 'title', ''),
                        'organism': getattr(parsed_pathway, 'org', 'Unknown'),
                        'entries_count': len(getattr(parsed_pathway, 'entries', [])),
                        'reactions_count': len(getattr(parsed_pathway, 'reactions', [])),
                        'relations_count': len(getattr(parsed_pathway, 'relations', [])),
                        'coordinate_scale': coordinate_scale
                    }
                    document_model.metadata['kegg_pathway_data'] = pathway_dict
                    document_model.metadata['source'] = 'kegg_import'  # CRITICAL: Mark as KEGG model for metadata inspector
                    self.logger.info(f"Stored KEGG metadata in document for tab-switch: {len(pathway_dict)} keys")
                except Exception as e:
                    self.logger.warning(f"Could not serialize KEGG metadata: {e}")
            # Update preview (populates metadata inspector in UI)
            self._update_preview(parsed_pathway)
            # If we don't have kgml_data (because we reused cache), read it now for saving
            if kgml_data is None:
                # Use filepath from result if available, otherwise use current_filepath from cache
                file_to_read = result.get('filepath') or self.current_filepath
                if file_to_read:
                    with open(file_to_read, 'r', encoding='utf-8') as f:
                        kgml_data = f.read()
                else:
                    self.logger.error("No filepath available to read KGML data")
                    raise ValueError("Cannot save pathway: no KGML data and no filepath to read from")
            # Save files to project (so they're available later)
            saved_filepath = self._save_to_project(pathway_id, kgml_data, parsed_pathway, document_model, coordinate_scale)
            # Auto-load model into canvas if available
            # Note: self.model_canvas should be a loader (ModelCanvasLoader), not a manager
            # Use normalized methods to get loader and manager
            canvas_loader = self._get_canvas_loader()
            canvas_manager = self._get_canvas_manager()
            if canvas_loader or canvas_manager:
                if canvas_loader:
                    self.logger.info(f"Auto-load: Using canvas loader")
                if canvas_manager:
                    self.logger.info(f"Auto-load: Using canvas manager")
                # Handle both cases
                if canvas_loader:
                    # It's a loader - can create new document
                    self.logger.info(f"Auto-load: Detected canvas loader")
                elif canvas_manager:
                    # Direct manager reference
                    self.logger.warning("Auto-load: Direct canvas manager provided (expected loader)")
            else:
                self.logger.error("model_canvas is None! Cannot auto-load to canvas.")
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
                    # CRITICAL: Create canvas with temporary filename to avoid loading
                    # stale view state from previous imports of same pathway ID
                    page_index, drawing_area = canvas_loader.add_document(filename="importing_temp")
                    canvas_manager = canvas_loader.get_canvas_manager(drawing_area)
                    if not canvas_manager:
                        raise ValueError("Failed to get canvas manager after tab creation")
                    # CRITICAL: Set filepath FIRST before load_objects
                    # This ensures the correct filename is used for any auto-save operations
                    canvas_manager.set_filepath(saved_filepath)
                    # ===== UNIFIED OBJECT LOADING =====
                    # Use load_objects() for consistent initialization (same as File → Open)
                    canvas_manager.load_objects(
                        places=document_model.places,
                        transitions=document_model.transitions,
                        arcs=document_model.arcs
                    )
                    # CRITICAL: Copy metadata to canvas manager's document
                    # This ensures metadata is available for tab-switch and metadata inspector
                    if hasattr(canvas_manager, 'document') and hasattr(document_model, 'metadata'):
                        # Copy metadata keys individually (document.metadata is a property)
                        for key, value in document_model.metadata.items():
                            canvas_manager.document.metadata[key] = value
                        self.logger.info(f"Copied metadata to canvas document ({len(document_model.metadata)} keys)")
                    # CRITICAL: Restore viewport from document (center on model)
                    # KEGG models are positioned in KEGG coordinate space (not at origin)
                    # The converter already calculated optimal viewport (centered on model bounds)
                    # This MUST happen AFTER load_objects to override any auto-centering
                    if hasattr(document_model, 'view_state') and document_model.view_state:
                        self.logger.info(f"Restoring viewport: pan=({document_model.view_state.get('pan_x', 0):.1f}, {document_model.view_state.get('pan_y', 0):.1f})")
                        canvas_manager.set_view_state(document_model.view_state)
                    # CRITICAL: Set change callback for proper state management
                    # (This is what File → Open does)
                    canvas_manager.document_controller.set_change_callback(
                        canvas_manager._on_object_changed
                    )
                    # Mark as clean (just imported/saved)
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
                    # NOTE: We do NOT call fit_to_page() here because the converter already
                    # set the optimal viewport (centered on model bounds at zoom=1.0).
                    # fit_to_page() would recalculate and apply offsets which could push
                    # the model out of view. User can manually fit if needed (Ctrl+0).
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
                                    simulation_controller = getattr(overlay_manager, 'simulation_controller', None)
                                    if simulation_controller:
                                        from shypn.events import EventBus
                                        from shypn.core.document_id import doc_id
                                        EventBus.emit('simulation.controller_ready',
                                                      {'controller': simulation_controller},
                                                      document_id=doc_id(drawing_area))
                                    # CRITICAL: Call on_file_opened to load metadata (same as File→Open)
                                    # Determine metadata path based on project structure
                                    if self.project and hasattr(self.project, 'get_metadata_dir'):
                                        metadata_dir = self.project.get_metadata_dir()
                                        if metadata_dir:
                                            # Look for metadata in project/metadata/ directory
                                            import os
                                            model_filename = f"{base_name}.shypn"
                                            shypn_path = os.path.join(metadata_dir, model_filename)
                                        else:
                                            # Fallback: look alongside model file
                                            shypn_path = saved_filepath.replace('.shy', '.shypn')
                                    else:
                                        # No project context: look alongside model file
                                        shypn_path = saved_filepath.replace('.shy', '.shypn')
                                    if hasattr(report_panel_loader.panel, 'on_file_opened'):
                                        report_panel_loader.panel.on_file_opened(shypn_path)
                                    # CRITICAL: Refresh KEGG metadata inspector for imported model
                                    # This ensures the metadata tree is populated after import
                                    self.refresh_metadata_inspector()
                            return False  # Don't repeat
                        GLib.idle_add(refresh_report_panel)
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
            # Store reference to imported document for enrichment
            self.current_pathway_doc = document_model
            # Enable stoichiometry enrichment button
            self.stoich_enrich_button.set_sensitive(True)
            self._check_stoich_enrichment_candidates()
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
            # PHASE 3: Auto-map compounds for thermodynamic validation
            if document_model:
                try:
                    from shypn.thermodynamics.mappers import CompoundMapperService
                    mapper_service = CompoundMapperService()
                    mappings, confidences = mapper_service.map_all_places(document_model)
                    summary = mapper_service.get_mapping_summary(mappings, confidences)
                    self.logger.info(
                        f"Thermodynamic mapping: {summary['total_mapped']}/{len(document_model.places)} places mapped "
                        f"(avg confidence: {summary['average_confidence']:.0%})"
                    )
                except Exception as e:
                    self.logger.warning(f"Compound mapping failed (non-critical): {e}")
            
            # Metadata will be populated when user expands the inspector
            
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
        """Update preview with comprehensive pathway information.
        Updates both the metadata tree and text summary tabs.
        Args:
            pathway: Parsed KEGG pathway object (KEGGPathway)
        """
        if not pathway:
            return
        
        # Update both tabs
        self._populate_metadata_tree(pathway)
        self._update_text_summary(pathway)
        # Metadata will be visible when user expands the inspector
    
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
            # CRITICAL: Save KEGG PathwayData for metadata inspector
            # Store serialized pathway data in metadata so it can be loaded later
            if parsed_pathway:
                try:
                    # Serialize the essential pathway data for the metadata inspector
                    pathway_dict = {
                        'pathway_id': pathway_id,
                        'name': getattr(parsed_pathway, 'name', pathway_id),
                        'title': getattr(parsed_pathway, 'title', ''),
                        'organism': getattr(parsed_pathway, 'org', 'Unknown'),
                        'entries_count': len(getattr(parsed_pathway, 'entries', [])),
                        'reactions_count': len(getattr(parsed_pathway, 'reactions', [])),
                        'relations_count': len(getattr(parsed_pathway, 'relations', [])),
                        'coordinate_scale': coordinate_scale
                    }
                    document_model.metadata['kegg_pathway_data'] = pathway_dict
                    self.logger.info(f"Saved KEGG PathwayData to metadata: {len(pathway_dict)} keys")
                except Exception as e:
                    self.logger.warning(f"Could not serialize KEGG PathwayData: {e}")
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
    def _check_stoich_enrichment_candidates(self):
        """Check how many reactions can be enriched with stoichiometry."""
        # Get document from canvas (where loaded models are)
        document = None
        canvas_manager = self._get_canvas_manager()
        if canvas_manager:
            try:
                if hasattr(canvas_manager, 'document'):
                    document = canvas_manager.document
                elif hasattr(canvas_manager, 'get_document'):
                    document = canvas_manager.get_document()
            except Exception as e:
                self.logger.warning(f"Could not get document from canvas: {e}")
        # Fallback to stored reference from recent import
        if not document:
            document = self.current_pathway_doc
        if not document:
            self.stoich_status_label.set_text("")
            return
        # Count transitions with KEGG reaction IDs
        reactions_to_enrich = [
            t for t in document.transitions
            if hasattr(t, 'metadata') and t.metadata and
               t.metadata.get('kegg_reaction_id') and
               t.metadata.get('data_source') == 'kegg_import'
        ]
        total = len(reactions_to_enrich)
        # Check if already enriched
        already_enriched = (
            hasattr(document, 'metadata') and
            document.metadata and
            document.metadata.get('stoichiometry_enriched', False)
        )
        if already_enriched:
            self.stoich_status_label.set_markup(
                '<span size="small">✅ Already enriched</span>'
            )
        elif total > 0:
            est_time = total * 1.5  # ~1.5s per reaction
            self.stoich_status_label.set_markup(
                f'<span size="small">{total} reactions can be enriched '
                f'(~{est_time:.0f}s)</span>'
            )
        else:
            self.stoich_status_label.set_markup(
                '<span size="small">No reactions to enrich</span>'
            )
    
    def _on_enrich_stoichiometry_clicked(self, button):
        """Handle stoichiometry enrichment button click.
        Adds missing cofactors (ATP, NADH, etc.) to transitions by querying
        KEGG REACTION database for complete stoichiometry.
        """
        # Get document from canvas (where loaded models are)
        document = None
        # Use normalized method to get canvas manager
        canvas_manager = self._get_canvas_manager()
        # CRITICAL: Use the canvas manager itself as the document
        # The enricher expects an object with .places, .transitions, .arcs
        # The ModelCanvasManager has these via properties delegating to DocumentController
        if canvas_manager:
            try:
                # Check if it has the required attributes
                if (hasattr(canvas_manager, 'places') and 
                    hasattr(canvas_manager, 'transitions') and 
                    hasattr(canvas_manager, 'arcs')):
                    document = canvas_manager
                    self.logger.info(
                        f"Using canvas manager as document: {len(document.places)} places, "
                        f"{len(document.transitions)} transitions"
                    )
                elif hasattr(canvas_manager, 'document'):
                    document = canvas_manager.document
                elif hasattr(canvas_manager, 'get_document'):
                    document = canvas_manager.get_document()
            except Exception as e:
                self.logger.warning(f"Could not get document from canvas: {e}")
                import traceback
                traceback.print_exc()
        if document:
            self.logger.info(
                f"Retrieved document: {len(document.places)} places, "
                f"{len(document.transitions)} transitions"
            )
        # Fallback: use stored reference from recent import
        if not document:
            document = self.current_pathway_doc
            if document:
                self.logger.info("Using stored pathway document from import")
        if not document:
            self._show_error("No model loaded. Open a KEGG model from the file browser or import one.")
            return
        # Import enrichment service
        try:
            from shypn.services.enrichment import KEGGStoichiometryEnricher
        except ImportError as e:
            self._show_error(f"Stoichiometry enrichment service not available: {e}")
            return
        # Check if already enriched
        if hasattr(document, 'metadata') and \
           document.metadata and \
           document.metadata.get('stoichiometry_enriched'):
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Model already enriched"
            )
            dialog.format_secondary_text(
                "This model has already been enriched with stoichiometry.\n"
                "Running again may create duplicate cofactors.\n\n"
                "Continue anyway?"
            )
            response = dialog.run()
            dialog.destroy()
            if response != Gtk.ResponseType.YES:
                return
        # Disable button during enrichment
        self.stoich_enrich_button.set_sensitive(False)
        self.stoich_status_label.set_text("Enriching...")
        def enrich_in_thread():
            """Run enrichment in background thread."""
            try:
                # Progress callback to update UI
                def progress(current, total, message):
                    GLib.idle_add(
                        self.stoich_status_label.set_text,
                        f"[{current}/{total}] {message[:40]}..."
                    )
                # Create enricher
                enricher = KEGGStoichiometryEnricher(
                    progress_callback=progress,
                    position_strategy='cluster'  # Position cofactors near transitions
                )
                # Run enrichment
                result = enricher.enrich_document(document)
                return result
            except Exception as e:
                self.logger.error(f"Stoichiometry enrichment failed: {e}")
                import traceback
                traceback.print_exc()
                raise
        # Run in background with callbacks
        self._run_in_thread(
            enrich_in_thread,
            on_complete=self._on_stoich_enrichment_complete,
            on_error=self._on_stoich_enrichment_error
        )
    def _on_stoich_enrichment_complete(self, result):
        """Called when stoichiometry enrichment completes successfully.
        Args:
            result: EnrichmentResult object
        """
        self.logger.info(
            f"Stoichiometry enrichment complete: "
            f"{result.statistics.get('places_added', 0)} places, "
            f"{result.statistics.get('arcs_added', 0)} arcs in "
            f"{result.duration_seconds:.1f}s"
        )
        # Re-enable button
        self.stoich_enrich_button.set_sensitive(True)
        # Update status
        places_added = result.statistics.get('places_added', 0)
        arcs_added = result.statistics.get('arcs_added', 0)
        reactions_enriched = result.statistics.get('reactions_enriched', 0)
        if result.success and places_added > 0:
            self.stoich_status_label.set_markup(
                f'<span size="small">✅ Added {places_added} cofactors '
                f'({arcs_added} arcs) in {result.duration_seconds:.0f}s</span>'
            )
            # Update main status with detailed statistics
            status_msg = f"✅ Stoichiometry enrichment complete!\n"
            status_msg += f"Reactions enriched: {reactions_enriched}\n"
            status_msg += f"Places added: {places_added}\n"
            status_msg += f"Arcs added: {arcs_added}\n"
            status_msg += f"Duration: {result.duration_seconds:.1f}s\n"
            # Show cofactor breakdown
            if 'cofactor_counts' in result.statistics:
                cofactor_counts = result.statistics['cofactor_counts']
                top_cofactors = sorted(
                    cofactor_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                if top_cofactors:
                    cofactor_parts = ["\nTop cofactors:\n"] + [
                        f"  \u2022 {compound_id}: {count} reactions\n"
                        for compound_id, count in top_cofactors
                    ]
                    status_msg += "".join(cofactor_parts)
            status_msg += "\n💡 Model updated in memory. Save to persist changes."
            if result.warnings:
                warning_parts = [f"\n\n⚠️ {len(result.warnings)} warnings:\n"] + [
                    f"  • {w}\n" for w in result.warnings[:3]
                ]
                status_msg += "".join(warning_parts)
            self._show_status(status_msg)
            # Trigger canvas redraw if model is loaded
            # Use GLib.idle_add to schedule on main thread (enrichment runs in background)
            def refresh_canvas():
                """Refresh canvas on main thread."""
                canvas_manager = self._get_canvas_manager()
                if canvas_manager:
                    try:
                        # Mark canvas as needing redraw (will call queue_draw via callback)
                        if hasattr(canvas_manager, 'mark_needs_redraw'):
                            canvas_manager.mark_needs_redraw()
                            self.logger.info("Marked canvas for redraw after enrichment")
                        # Mark model as dirty (needs save)
                        if hasattr(canvas_manager, 'mark_dirty'):
                            canvas_manager.mark_dirty()
                            self.logger.info("Marked model as dirty after enrichment")
                        # CRITICAL: Force simulation reset to recognize new objects
                        # New places/arcs won't be in enablement calculations until reset
                        if hasattr(canvas_manager, '_request_simulation_reset'):
                            canvas_manager._request_simulation_reset()
                            self.logger.info("Requested simulation reset after enrichment")
                        self.logger.info("Canvas refresh complete after stoichiometry enrichment")
                    except Exception as e:
                        self.logger.warning(f"Could not redraw canvas: {e}")
                        import traceback
                        traceback.print_exc()
                return False  # Don't repeat
            # Schedule on main GTK thread
            GLib.idle_add(refresh_canvas)
        else:
            self.stoich_status_label.set_markup(
                '<span size="small">No cofactors were added</span>'
            )
            self._show_status(f"Enrichment completed but no cofactors were added.\n{result.message}")
        return False  # Don't repeat
    def _on_stoich_enrichment_error(self, error):
        """Called when stoichiometry enrichment encounters an error.
        Args:
            error: Exception object
        """
        self.logger.error(f"Stoichiometry enrichment error: {error}")
        # Re-enable button
        self.stoich_enrich_button.set_sensitive(True)
        # Update status
        self.stoich_status_label.set_markup(
            '<span size="small">❌ Enrichment failed</span>'
        )
        self._show_error(f"Stoichiometry enrichment failed: {error}")
        return False  # Don't repeat
    def _update_metadata_after_enrichment(self, canvas_manager, result):
        """Update metadata inspector with enrichment statistics.
        Adds enrichment info to the existing metadata tree without
        losing the original import data.
        Args:
            canvas_manager: Canvas manager with document
            result: EnrichmentResult object
        """
        try:
            # Find or create enrichment section in metadata tree
            model = self.metadata_store
            enrichment_root = None
            # Look for existing enrichment section
            iter = model.get_iter_first()
            while iter:
                name = model.get_value(iter, 1)
                if name == "Enrichment History":
                    enrichment_root = iter
                    break
                iter = model.iter_next(iter)
            # If not found, create new section at the top
            if not enrichment_root:
                enrichment_root = model.insert(0, None, [
                    "✨", "Enrichment History", "Recent enrichments",
                    "section", "", "Stoichiometry enrichment history"
                ])
            # Add this enrichment as a timestamped entry
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            enrich_iter = model.append(enrichment_root, [
                "🔬", f"Stoichiometry @ {timestamp}",
                f"{result.places_enriched + result.transitions_enriched} objects",
                "enrichment", "", 
                f"Added {result.places_enriched} places, {result.arcs_added} arcs in {result.duration_seconds:.1f}s"
            ])
            model.append(enrich_iter, [
                "⏱️", "Duration",
                f"{result.duration_seconds:.1f}s",
                "stat", "", "Time taken to enrich"
            ])
            model.append(enrich_iter, [
                "🔷", "Places Added",
                str(result.places_enriched),
                "stat", "", "New metabolite places created"
            ])
            model.append(enrich_iter, [
                "🔗", "Arcs Added",
                str(result.arcs_added),
                "stat", "", "New stoichiometry connections"
            ])
            model.append(enrich_iter, [
                "🔶", "Reactions Enriched",
                str(result.transitions_enriched),
                "stat", "", "Reactions with stoichiometry added"
            ])
            if result.warnings:
                warn_iter = model.append(enrich_iter, [
                    "⚠️", "Warnings",
                    f"{len(result.warnings)} issues",
                    "warnings", "", "Non-fatal warnings during enrichment"
                ])
                for warning in result.warnings[:10]:  # First 10 warnings
                    model.append(warn_iter, [
                        "⚠️", warning[:50],
                        "...",
                        "warning", "", warning
                    ])
            if result.errors:
                err_iter = model.append(enrich_iter, [
                    "❌", "Errors",
                    f"{len(result.errors)} errors",
                    "errors", "", "Errors encountered during enrichment"
                ])
                for error in result.errors[:10]:  # First 10 errors
                    model.append(err_iter, [
                        "❌", error[:50],
                        "...",
                        "error", "", error
                    ])
            # Expand the enrichment section
            path = model.get_path(enrichment_root)
            self.metadata_tree.expand_row(path, False)
            self.logger.info("Metadata inspector updated with enrichment info")
        except Exception as e:
            self.logger.warning(f"Could not update metadata tree: {e}")
    def _populate_metadata_tree(self, pathway):
        """Populate metadata tree with KEGG pathway information.
        Args:
            pathway: KEGGPathway object with all metadata
        """
        def do_populate():
            try:
                self.metadata_store.clear()
                # === PATHWAY INFO ===
                pathway_root = self.metadata_store.append(None, [
                    "🗺️", "Pathway Info", pathway.title or pathway.name,
                    "section", "", f"KEGG Pathway: {pathway.name}"
                ])
                self.metadata_store.append(pathway_root, [
                    "🔖", "Name", pathway.name,
                    "info", "", f"Pathway identifier: {pathway.name}"
                ])
                self.metadata_store.append(pathway_root, [
                    "🔖", "Title", pathway.title or "N/A",
                    "info", "", f"Pathway title: {pathway.title}"
                ])
                self.metadata_store.append(pathway_root, [
                    "🌐", "Organism", pathway.org or "N/A",
                    "info", "", f"Organism code: {pathway.org}"
                ])
                self.metadata_store.append(pathway_root, [
                    "🔢", "Number", pathway.number or "N/A",
                    "info", "", f"Pathway number: {pathway.number}"
                ])
                if pathway.link:
                    self.metadata_store.append(pathway_root, [
                        "🔗", "Link", pathway.link[:50] + "..." if len(pathway.link) > 50 else pathway.link,
                        "url", "", f"KEGG database link: {pathway.link}"
                    ])
                # === STATISTICS ===
                stats_root = self.metadata_store.append(None, [
                    "📊", "Statistics", f"{len(pathway.entries)} entries",
                    "section", "", "Pathway content statistics"
                ])
                self.metadata_store.append(stats_root, [
                    "📍", "Total Entries", str(len(pathway.entries)),
                    "stat", "", f"Total nodes in pathway"
                ])
                self.metadata_store.append(stats_root, [
                    "🔶", "Total Reactions", str(len(pathway.reactions)),
                    "stat", "", f"Metabolic reactions"
                ])
                self.metadata_store.append(stats_root, [
                    "🔗", "Total Relations", str(len(pathway.relations)),
                    "stat", "", f"Regulatory interactions"
                ])
                # Entry type breakdown
                entry_types = pathway.count_entry_types()
                types_iter = self.metadata_store.append(stats_root, [
                    "📦", "Entry Types", f"{len(entry_types)} types",
                    "section", "", "Distribution of entry types"
                ])
                for etype, count in sorted(entry_types.items()):
                    icon = self._get_entry_type_icon(etype)
                    self.metadata_store.append(types_iter, [
                        icon, etype.capitalize(), str(count),
                        "type_stat", "", f"{count} {etype} entries"
                    ])
                # === ENTRIES BY TYPE ===
                entries_root = self.metadata_store.append(None, [
                    "📦", "Entries", f"{len(pathway.entries)} items",
                    "section", "", "All pathway entries"
                ])
                # Group entries by type
                entries_by_type = pathway.group_entries_by_type()
                # Add each type group
                for etype in sorted(entries_by_type.keys()):
                    entries = entries_by_type[etype]
                    icon = self._get_entry_type_icon(etype)
                    type_root = self.metadata_store.append(entries_root, [
                        icon, f"{etype.capitalize()}s", f"{len(entries)} items",
                        "entry_type", "", f"{len(entries)} {etype} entries"
                    ])
                    # Add individual entries (limit to first 50)
                    for entry in entries[:50]:
                        display_name = entry.graphics.name if entry.graphics else entry.name
                        entry_iter = self.metadata_store.append(type_root, [
                            icon, display_name or entry.id,
                            entry.id,
                            "entry", entry.id,
                            f"{etype}: {display_name or entry.id}"
                        ])
                        # Add entry details as children
                        if entry.graphics:
                            self.metadata_store.append(entry_iter, [
                                "📍", "Position",
                                f"({entry.graphics.x:.0f}, {entry.graphics.y:.0f})",
                                "position", "", f"Canvas coordinates"
                            ])
                        if entry.reaction:
                            self.metadata_store.append(entry_iter, [
                                "🔶", "Reaction",
                                entry.reaction,
                                "reaction_ref", "", f"Associated reaction: {entry.reaction}"
                            ])
                        if entry.components:
                            comp_iter = self.metadata_store.append(entry_iter, [
                                "🔗", "Components",
                                f"{len(entry.components)} members",
                                "components", "", f"Group with {len(entry.components)} members"
                            ])
                            for comp_id in entry.components[:10]:
                                self.metadata_store.append(comp_iter, [
                                    "➜", f"Entry {comp_id}", "",
                                    "component", comp_id, f"Component entry ID: {comp_id}"
                                ])
                    if len(entries) > 50:
                        self.metadata_store.append(type_root, [
                            "⋯", f"... {len(entries) - 50} more", "",
                            "", "", f"Total: {len(entries)} entries"
                        ])
                # === REACTIONS ===
                reactions_root = self.metadata_store.append(None, [
                    "🔶", "Reactions", f"{len(pathway.reactions)} items",
                    "section", "", "Metabolic reactions"
                ])
                for rxn in pathway.reactions[:100]:  # Limit to first 100
                    rxn_type = "⇌" if rxn.is_reversible() else "→"
                    reaction_iter = self.metadata_store.append(reactions_root, [
                        "🔶", rxn.name,
                        f"{rxn_type} {rxn.type}",
                        "reaction", rxn.id,
                        f"Reaction {rxn.name} ({rxn.type})"
                    ])
                    # Substrates
                    if rxn.substrates:
                        subs_iter = self.metadata_store.append(reaction_iter, [
                            "⬅️", "Substrates",
                            f"{len(rxn.substrates)} items",
                            "substrates", "", "Reaction inputs"
                        ])
                        for sub in rxn.substrates:
                            self.metadata_store.append(subs_iter, [
                                "🧪", sub.name,
                                f"Entry {sub.id}",
                                "substrate", sub.id,
                                f"Substrate: {sub.name}"
                            ])
                    # Products
                    if rxn.products:
                        prods_iter = self.metadata_store.append(reaction_iter, [
                            "➡️", "Products",
                            f"{len(rxn.products)} items",
                            "products", "", "Reaction outputs"
                        ])
                        for prod in rxn.products:
                            self.metadata_store.append(prods_iter, [
                                "🧪", prod.name,
                                f"Entry {prod.id}",
                                "product", prod.id,
                                f"Product: {prod.name}"
                            ])
                if len(pathway.reactions) > 100:
                    self.metadata_store.append(reactions_root, [
                        "⋯", f"... {len(pathway.reactions) - 100} more", "",
                        "", "", f"Total: {len(pathway.reactions)} reactions"
                    ])
                # === RELATIONS ===
                relations_root = self.metadata_store.append(None, [
                    "🔗", "Relations", f"{len(pathway.relations)} items",
                    "section", "", "Regulatory interactions"
                ])
                # Group relations by type
                relations_by_type = pathway.group_relations_by_type()
                for rel_type in sorted(relations_by_type.keys()):
                    relations = relations_by_type[rel_type]
                    type_iter = self.metadata_store.append(relations_root, [
                        self._get_relation_type_icon(rel_type),
                        rel_type,
                        f"{len(relations)} items",
                        "relation_type", "", f"{len(relations)} {rel_type} relations"
                    ])
                    for rel in relations[:50]:  # Limit per type
                        rel_iter = self.metadata_store.append(type_iter, [
                            "🔗", f"{rel.entry1} → {rel.entry2}",
                            rel.type,
                            "relation", f"{rel.entry1}_{rel.entry2}",
                            f"{rel.type} relation: {rel.entry1} to {rel.entry2}"
                        ])
                        # Add subtypes
                        if rel.subtypes:
                            for subtype in rel.subtypes:
                                self.metadata_store.append(rel_iter, [
                                    "➜", subtype.name,
                                    subtype.value or "",
                                    "subtype", "", f"{subtype.name}: {subtype.value or 'N/A'}"
                                ])
                    if len(relations) > 50:
                        self.metadata_store.append(type_iter, [
                            "⋯", f"... {len(relations) - 50} more", "",
                            "", "", f"Total: {len(relations)} {rel_type} relations"
                        ])
                # Expand top-level nodes
                for i in range(5):  # First 5 sections
                    path = Gtk.TreePath.new_from_indices([i])
                    if path:
                        self.metadata_tree.expand_row(path, False)
            except Exception as e:
                self.logger.error(f"Error populating metadata tree: {e}", exc_info=True)
            return False
        GLib.idle_add(do_populate)
    def _update_text_summary(self, pathway):
        """Update text summary tab.
        Args:
            pathway: KEGGPathway object
        """
        def do_update():
            try:
                buffer = self.preview_text.get_buffer()
                lines = []
                lines.append("=== KEGG PATHWAY ===")
                lines.append(f"Name: {pathway.name}")
                lines.append(f"Title: {pathway.title or 'N/A'}")
                lines.append(f"Organism: {pathway.org or 'N/A'}")
                lines.append(f"Number: {pathway.number or 'N/A'}")
                lines.append("")
                lines.append("=== STATISTICS ===")
                lines.append(f"Total Entries: {len(pathway.entries)}")
                lines.append(f"Total Reactions: {len(pathway.reactions)}")
                lines.append(f"Total Relations: {len(pathway.relations)}")
                lines.append("")
                lines.append("=== ENTRY TYPES ===")
                entry_types = pathway.count_entry_types()
                for etype, count in sorted(entry_types.items()):
                    lines.append(f"  {etype.capitalize()}: {count}")
                if pathway.relations:
                    lines.append("")
                    lines.append("=== RELATION TYPES ===")
                    relation_types = pathway.count_relation_types()
                    for rtype, count in sorted(relation_types.items()):
                        lines.append(f"  {rtype}: {count}")
                lines.append("")
                lines.append("=== REACTIONS ===")
                reversible_count = sum(1 for r in pathway.reactions if r.is_reversible())
                irreversible_count = len(pathway.reactions) - reversible_count
                lines.append(f"  Reversible: {reversible_count}")
                lines.append(f"  Irreversible: {irreversible_count}")
                buffer.set_text("\n".join(lines))
            except Exception as e:
                self.logger.error(f"Error updating text summary: {e}", exc_info=True)
            return False
        GLib.idle_add(do_update)
    def _get_entry_type_icon(self, entry_type: str) -> str:
        """Get icon for entry type.
        Args:
            entry_type: Type of entry
        Returns:
            Unicode icon string
        """
        icons = {
            'compound': '🧪',
            'gene': '🧬',
            'enzyme': '⚗️',
            'ortholog': '🔬',
            'map': '🗺️',
            'group': '📦',
            'other': '📍'
        }
        return icons.get(entry_type, '📍')
    def _get_relation_type_icon(self, relation_type: str) -> str:
        """Get icon for relation type.
        Args:
            relation_type: Type of relation
        Returns:
            Unicode icon string
        """
        icons = {
            'ECrel': '⚗️',     # Enzyme-enzyme relation
            'PPrel': '🔗',     # Protein-protein interaction
            'GErel': '🧬',     # Gene expression interaction
            'PCrel': '🧪',     # Protein-compound interaction
            'maplink': '🗺️'   # Link to another map
        }
        return icons.get(relation_type, '🔗')
    def _on_metadata_row_clicked(self, tree_view, path, column):
        """Handle metadata tree row activation.
        Shows a dialog with full information about the clicked item.
        Args:
            tree_view: TreeView widget
            path: TreePath of clicked row
            column: TreeViewColumn of clicked cell
        """
        model = tree_view.get_model()
        iter_node = model.get_iter(path)
        obj_type = model.get_value(iter_node, 3)
        obj_id = model.get_value(iter_node, 4)
        tooltip = model.get_value(iter_node, 5)
        if not tooltip:
            return
        # Show info dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=model.get_value(iter_node, 1)
        )
        dialog.format_secondary_text(tooltip)
        dialog.run()
        dialog.destroy()
    def _update_metadata_tree_from_parsed(self, parsed_pathway):
        """Update KEGG metadata inspector with parsed KEGGPathway object.
        This method populates the metadata tree view during preview (before import).
        Args:
            parsed_pathway: KEGGPathway object from kgml_parser
        """
        try:
            self.logger.info("Updating KEGG metadata inspector from parsed pathway...")
            if not parsed_pathway:
                self.logger.error("No parsed pathway provided")
                return False
            self.metadata_store.clear()
            # Pathway Info section
            info_root = self.metadata_store.append(None, [
                "🅿️", "Pathway Info", "",
                "section", "", "KEGG pathway information"
            ])
            self.metadata_store.append(info_root, [
                "🅿️", "Pathway ID", parsed_pathway.name,
                "text", "", f"KEGG pathway identifier: {parsed_pathway.name}"
            ])
            self.metadata_store.append(info_root, [
                "📝", "Title", parsed_pathway.title,
                "text", "", f"Pathway title: {parsed_pathway.title}"
            ])
            self.metadata_store.append(info_root, [
                "🧬", "Organism", parsed_pathway.org,
                "text", "", f"Organism code: {parsed_pathway.org}"
            ])
            if parsed_pathway.link:
                self.metadata_store.append(info_root, [
                    "🔗", "KEGG Link", parsed_pathway.link,
                    "text", "", f"Link to KEGG database entry"
                ])
            # Entries section
            if parsed_pathway.entries:
                entries_root = self.metadata_store.append(None, [
                    "📦", "Entries", f"{len(parsed_pathway.entries)} total",
                    "section", "", "KEGG pathway entries"
                ])
                # Count entries by type
                type_counts = parsed_pathway.count_entry_types()
                for entry_type, count in type_counts.items():
                    icon = {"compound": "🧪", "gene": "🧬", "enzyme": "⚡", "map": "🗺️"}.get(entry_type, "📌")
                    self.metadata_store.append(entries_root, [
                        icon, entry_type.capitalize(), f"{count} entries",
                        "text", "", f"{count} {entry_type} entries in pathway"
                    ])
                self.logger.info(f"  Added {len(parsed_pathway.entries)} entries")
            # Reactions section
            if parsed_pathway.reactions:
                reactions_root = self.metadata_store.append(None, [
                    "⚡", "Reactions", f"{len(parsed_pathway.reactions)} total",
                    "section", "", "KEGG pathway reactions"
                ])
                for reaction in parsed_pathway.reactions:
                    reaction_name = reaction.name if hasattr(reaction, 'name') else reaction.id
                    rev = "⇌" if getattr(reaction, 'reversible', False) else "→"
                    self.metadata_store.append(reactions_root, [
                        "🔹", "Reaction", f"{reaction_name} {rev}",
                        "text", "", f"Reaction: {reaction_name}"
                    ])
                self.logger.info(f"  Added {len(parsed_pathway.reactions)} reactions")
            # Relations section  
            if parsed_pathway.relations:
                relations_root = self.metadata_store.append(None, [
                    "🔗", "Relations", f"{len(parsed_pathway.relations)} total",
                    "section", "", "KEGG pathway relations"
                ])
                # Count relations by type
                rel_type_counts = parsed_pathway.count_relation_types()
                for rel_type, count in rel_type_counts.items():
                    self.metadata_store.append(relations_root, [
                        "🔸", rel_type, f"{count} relations",
                        "text", "", f"{count} {rel_type} relations in pathway"
                    ])
                self.logger.info(f"  Added {len(parsed_pathway.relations)} relations")
            # Expand all tree rows to show the metadata
            self.metadata_tree.expand_all()
            self.logger.info("KEGG metadata inspector updated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update KEGG metadata inspector: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _update_enrichment_buttons(self):
        """Update enrichment button states based on current document.
        Separated from metadata refresh to avoid cascade issues.
        """
        # Get current document using normalized method
        document = None
        canvas_manager = self._get_canvas_manager()
        if canvas_manager:
            try:
                if hasattr(canvas_manager, 'document'):
                    document = canvas_manager.document
                elif hasattr(canvas_manager, '_document_model'):
                    document = canvas_manager._document_model
            except Exception as e:
                self.logger.warning(f"Could not get document for button update: {e}")
        
        # Update enrichment buttons based on active document
        if document:
            # Check if KEGG model
            is_kegg = False
            if hasattr(document, 'metadata') and document.metadata:
                is_kegg = (document.metadata.get('source') == 'kegg_import' or 
                          document.metadata.get('data_source') == 'kegg_import')
            
            if is_kegg:
                # Enable enrichment for KEGG models
                self.stoich_enrich_button.set_sensitive(True)
                self._check_stoich_enrichment_candidates()
            else:
                # Not a KEGG model - disable buttons
                self.stoich_enrich_button.set_sensitive(False)
                self.stoich_status_label.set_markup('<span size="small">Not a KEGG model</span>')
        else:
            # No document - disable buttons
            self.stoich_enrich_button.set_sensitive(False)
            self.stoich_status_label.set_markup('<span size="small">No model loaded</span>')
    
    def refresh_metadata_inspector(self):
        """Refresh KEGG Metadata Inspector for the currently active document.
        This method is called when the user expands the metadata inspector.
        It populates the metadata tree and summary from the current document.
        """
        # Get current document using normalized method
        document = None
        canvas_manager = self._get_canvas_manager()
        
        if canvas_manager:
            try:
                if hasattr(canvas_manager, 'document'):
                    document = canvas_manager.document
                elif hasattr(canvas_manager, '_document_model'):
                    document = canvas_manager._document_model
            except Exception as e:
                self.logger.warning(f"Could not get document for metadata refresh: {e}")
        
        # Populate metadata display based on active document
        if document:
            # Check if KEGG model
            is_kegg = False
            if hasattr(document, 'metadata') and document.metadata:
                is_kegg = (document.metadata.get('source') == 'kegg_import' or 
                          document.metadata.get('data_source') == 'kegg_import')
            
            if is_kegg:
                # Load KEGG metadata if available
                pathway_dict = document.metadata.get('kegg_pathway_data')
                if pathway_dict:
                    self._load_kegg_metadata_from_dict(pathway_dict)
                else:
                    # Clear for old KEGG models without saved metadata
                    self.metadata_store.clear()
                    buffer = self.preview_text.get_buffer()
                    buffer.set_text("KEGG model (legacy import - metadata not saved)\n\nRe-import to see full metadata.")
            else:
                # Not a KEGG model - clear metadata
                self.metadata_store.clear()
                buffer = self.preview_text.get_buffer()
                buffer.set_text("No KEGG pathway loaded.\n\nImport a KEGG pathway to see metadata.")
        else:
            # No document - clear metadata
            self.metadata_store.clear()
            buffer = self.preview_text.get_buffer()
            buffer.set_text("No model loaded.")
    
    def _load_kegg_metadata_from_dict(self, pathway_dict):
        """Load and display KEGG metadata from saved dictionary.
        Args:
            pathway_dict: Dictionary with saved KEGG pathway data
        """
        def do_update():
            try:
                self.metadata_store.clear()
                # Pathway Info section
                info_root = self.metadata_store.append(None, [
                    "🆔", "Pathway Info", "",
                    "section", "", "KEGG pathway information"
                ])
                self.metadata_store.append(info_root, [
                    "🆔", "Pathway ID", pathway_dict.get('pathway_id', 'Unknown'),
                    "text", "", f"KEGG pathway identifier: {pathway_dict.get('pathway_id', 'Unknown')}"
                ])
                self.metadata_store.append(info_root, [
                    "📝", "Name", pathway_dict.get('name', 'Unnamed'),
                    "text", "", pathway_dict.get('title', pathway_dict.get('name', 'Unnamed'))
                ])
                self.metadata_store.append(info_root, [
                    "🧠", "Organism", pathway_dict.get('organism', 'Unknown'),
                    "text", "", f"Source organism: {pathway_dict.get('organism', 'Unknown')}"
                ])
                # Statistics section
                stats_root = self.metadata_store.append(None, [
                    "📊", "Statistics", "",
                    "section", "", "Pathway component counts"
                ])
                self.metadata_store.append(stats_root, [
                    "🟢", "Entries", str(pathway_dict.get('entries_count', 0)),
                    "number", "", f"{pathway_dict.get('entries_count', 0)} KEGG entries (genes, compounds, pathways)"
                ])
                self.metadata_store.append(stats_root, [
                    "🔶", "Reactions", str(pathway_dict.get('reactions_count', 0)),
                    "number", "", f"{pathway_dict.get('reactions_count', 0)} biochemical reactions"
                ])
                self.metadata_store.append(stats_root, [
                    "➡", "Relations", str(pathway_dict.get('relations_count', 0)),
                    "number", "", f"{pathway_dict.get('relations_count', 0)} regulatory/interaction relations"
                ])
                # Conversion Info section
                conv_root = self.metadata_store.append(None, [
                    "⚙", "Conversion Info", "",
                    "section", "", "Import conversion settings"
                ])
                scale = pathway_dict.get('coordinate_scale', 2.5)
                self.metadata_store.append(conv_root, [
                    "📌", "Coordinate Scale", str(scale),
                    "number", "", f"Scaling factor applied to KGML coordinates: {scale}x"
                ])
                # Update preview text
                preview_lines = [
                    f"=== KEGG PATHWAY INFO ===",
                    f"Pathway ID: {pathway_dict.get('pathway_id', 'Unknown')}",
                    f"Name: {pathway_dict.get('name', 'Unnamed')}",
                    f"Organism: {pathway_dict.get('organism', 'Unknown')}",
                    f"",
                    f"=== STATISTICS ===",
                    f"Entries: {pathway_dict.get('entries_count', 0)}",
                    f"Reactions: {pathway_dict.get('reactions_count', 0)}",
                    f"Relations: {pathway_dict.get('relations_count', 0)}",
                    f"",
                    f"=== CONVERSION ===",
                    f"Coordinate Scale: {pathway_dict.get('coordinate_scale', 2.5)}x",
                ]
                buffer = self.preview_text.get_buffer()
                buffer.set_text("\\n".join(preview_lines))
            except Exception as e:
                self.logger.error(f"Error loading KEGG metadata: {e}")
                import traceback
                traceback.print_exc()
            return False  # Don't repeat
        from gi.repository import GLib
        GLib.idle_add(do_update)
    def _show_stochastic_warning_dialog(self, warnings):
        """Show dialog informing about reversible reactions and Skellam distribution support.
        Args:
            warnings: List of validation issues related to stochastic simulation
        Returns:
            str: User choice - 'convert_continuous', 'convert_hybrid', 'proceed_anyway', or 'cancel'
        """
        # Build message
        message = "ℹ️  REVERSIBLE REACTIONS DETECTED\n\n"
        message += "This KEGG pathway contains reversible reactions:\n\n"
        for warning in warnings:
            category = warning.get('category', 'Unknown')
            if category == 'reversible_reactions':
                reaction_count = len(warning.get('reactions', []))
                message += (
                    f"• {reaction_count} reversible reactions detected\n"
                    "  ✅ Fully supported in stochastic mode via Skellam distribution\n"
                    "  (τ-leaping automatically uses Skellam for net forward/reverse flux)\n\n"
                )
        message += "\nSIMULATION MODE OPTIONS:\n"
        message += "✓ STOCHASTIC mode: Uses Skellam distribution (recommended, accurate)\n"
        message += "✓ CONTINUOUS mode: Uses ODEs (alternative for fast reactions)\n"
        message += "✓ HYBRID mode: Combines stochastic and continuous approaches\n\n"
        message += "What would you like to do?"
        # Create dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            text="Reversible Reactions - Skellam Distribution Support"
        )
        dialog.format_secondary_text(message)
        # Add buttons (right to left order)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Use Continuous Mode", Gtk.ResponseType.YES)
        dialog.add_button("Use Hybrid Mode", Gtk.ResponseType.APPLY)
        dialog.add_button("Continue with Stochastic", Gtk.ResponseType.NO)
        # Set default to "Continue with Stochastic" (now fully supported)
        dialog.set_default_response(Gtk.ResponseType.NO)
        # Show dialog and get response
        response = dialog.run()
        dialog.destroy()
        # Map response to choice
        if response == Gtk.ResponseType.YES:
            return 'convert_continuous'
        elif response == Gtk.ResponseType.APPLY:
            return 'convert_hybrid'
        elif response == Gtk.ResponseType.NO:
            return 'proceed_anyway'
        else:
            return 'cancel'
