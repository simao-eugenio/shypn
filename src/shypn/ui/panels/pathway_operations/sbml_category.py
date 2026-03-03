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
from __future__ import annotations

import os
import sys
import time
import threading
import logging
from typing import Optional

try:
    import gi  # type: ignore[import-untyped]
    gi.require_version('Gtk', '3.0')
    gi.require_version('Pango', '1.0')
    from gi.repository import Gtk, GLib, Pango  # type: ignore[import-untyped]
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
    from shypn.services.sbml_compartment_module_service import SBMLCompartmentModuleService
except ImportError as e:
    print(f'Warning: SBML backend not available: {e}', file=sys.stderr)
    SBMLParser = None
    PathwayValidator = None
    PathwayPostProcessor = None
    PathwayConverter = None
    PathwayDocument = None
    SBMLCompartmentModuleService = None


class SBMLCategory(BasePathwayCategory):  # type: ignore[misc]
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
        self.controller = None  # Set via set_controller()
        self.model_canvas = None  # Set via set_model_canvas()
        
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
        
        # Preview section (metadata inspector under expander)
        preview_box = self._build_preview_section()
        main_box.pack_start(preview_box, False, False, 0)
        
        # Thermodynamic validation section (under expander)
        thermodynamic_box = self._build_thermodynamic_section()
        main_box.pack_start(thermodynamic_box, False, False, 0)
        
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
        
        # Entry with browse button for local mode
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.file_entry = Gtk.Entry()
        self.file_entry.set_placeholder_text("Path to SBML file or BioModels ID")
        self.file_entry.connect('changed', self._on_file_entry_changed)
        entry_box.pack_start(self.file_entry, True, True, 0)
        
        # Browse button (only visible in local mode)
        self.browse_button = Gtk.Button(label="Browse...")
        self.browse_button.set_no_show_all(True)  # Hidden by default
        self.browse_button.set_visible(True)  # Start visible since Local is default
        self.browse_button.connect('clicked', self._on_browse_clicked)
        entry_box.pack_start(self.browse_button, False, False, 0)
        
        box.pack_start(entry_box, False, False, 0)
        
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
        """Build preview section with metadata tree view."""
        self.metadata_expander = Gtk.Expander(label="SBML Metadata Inspector")
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
        
        # Value column (editable)
        value_renderer = Gtk.CellRendererText()
        value_renderer.set_property("family", "monospace")
        value_renderer.set_property("editable", True)
        value_renderer.connect("edited", self._on_value_edited)
        value_col = Gtk.TreeViewColumn("Value", value_renderer, text=2)
        value_col.set_resizable(True)
        value_col.set_expand(True)
        self.metadata_tree.append_column(value_col)
        
        # Type column
        type_renderer = Gtk.CellRendererText()
        type_col = Gtk.TreeViewColumn("Type", type_renderer, text=3)
        type_col.set_resizable(True)
        type_col.set_min_width(80)
        self.metadata_tree.append_column(type_col)
        
        # Connect click handler
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
            "Model summary will appear here after import...\n\n"
            "Click the 'Metadata Tree' tab to see detailed SBML information."
        )
        
        text_scroll.add(self.preview_text)
        notebook.append_page(text_scroll, Gtk.Label(label="📄 Summary"))
        
        self.metadata_expander.add(notebook)
        return self.metadata_expander
    
    def _build_thermodynamic_section(self) -> Gtk.Widget:
        """Build thermodynamic validation results section.
        
        Shows validation status for reversible reactions imported from SBML.
        Initially hidden, shown after import completes.
        """
        self.thermodynamic_expander = Gtk.Expander(label="Thermodynamic Validation")
        self.thermodynamic_expander.set_expanded(False)
        self.thermodynamic_expander.set_no_show_all(True)  # Hidden until data available
        self.thermodynamic_expander.set_visible(False)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        # Status label
        self.thermodynamic_status = Gtk.Label()
        self.thermodynamic_status.set_xalign(0)
        self.thermodynamic_status.set_line_wrap(True)
        box.pack_start(self.thermodynamic_status, False, False, 0)
        
        # Create TreeView for detailed results
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.set_max_content_height(400)
        
        # Create ListStore: status_icon, transition_id, transition_name, status, k_forward, k_reverse, k_ratio, k_eq, delta_g, deviation, message
        self.thermodynamic_store = Gtk.ListStore(
            str,    # Status icon (✅/⚠️/❌/ℹ️)
            str,    # Transition ID
            str,    # Transition name/description
            str,    # Status text
            float,  # k_forward (editable)
            float,  # k_reverse (editable)
            float,  # k_ratio (k_f/k_r)
            float,  # K_eq (thermodynamic)
            float,  # ΔG° (kJ/mol)
            float,  # Deviation (orders of magnitude)
            str     # Message
        )
        
        self.thermodynamic_tree = Gtk.TreeView(model=self.thermodynamic_store)
        self.thermodynamic_tree.set_enable_search(True)
        self.thermodynamic_tree.set_search_column(1)  # Search by transition ID
        
        # Column 0: Status icon
        renderer_icon = Gtk.CellRendererText()
        column_icon = Gtk.TreeViewColumn("", renderer_icon, text=0)
        column_icon.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.thermodynamic_tree.append_column(column_icon)
        
        # Column 1: Transition ID
        renderer_id = Gtk.CellRendererText()
        column_id = Gtk.TreeViewColumn("ID", renderer_id, text=1)
        column_id.set_sort_column_id(1)
        column_id.set_resizable(True)
        column_id.set_min_width(100)
        self.thermodynamic_tree.append_column(column_id)
        
        # Column 2: Transition name
        renderer_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Name", renderer_name, text=2)
        column_name.set_sort_column_id(2)
        column_name.set_resizable(True)
        column_name.set_min_width(150)
        self.thermodynamic_tree.append_column(column_name)
        
        # Column 3: Status
        renderer_status = Gtk.CellRendererText()
        column_status = Gtk.TreeViewColumn("Status", renderer_status, text=3)
        column_status.set_sort_column_id(3)
        column_status.set_resizable(True)
        self.thermodynamic_tree.append_column(column_status)
        
        # Column 4: k_forward (editable)
        renderer_kf = Gtk.CellRendererText()
        renderer_kf.set_property("editable", True)
        renderer_kf.connect("edited", self._on_k_forward_edited)
        column_kf = Gtk.TreeViewColumn("k_forward", renderer_kf, text=4)
        column_kf.set_sort_column_id(4)
        column_kf.set_resizable(True)
        self.thermodynamic_tree.append_column(column_kf)
        
        # Column 5: k_reverse (editable)
        renderer_kr = Gtk.CellRendererText()
        renderer_kr.set_property("editable", True)
        renderer_kr.connect("edited", self._on_k_reverse_edited)
        column_kr = Gtk.TreeViewColumn("k_reverse", renderer_kr, text=5)
        column_kr.set_sort_column_id(5)
        column_kr.set_resizable(True)
        self.thermodynamic_tree.append_column(column_kr)
        
        # Column 6: k_ratio
        renderer_ratio = Gtk.CellRendererText()
        column_ratio = Gtk.TreeViewColumn("k_f/k_r", renderer_ratio, text=6)
        column_ratio.set_sort_column_id(6)
        column_ratio.set_resizable(True)
        self.thermodynamic_tree.append_column(column_ratio)
        
        # Column 7: K_eq
        renderer_keq = Gtk.CellRendererText()
        column_keq = Gtk.TreeViewColumn("K_eq (thermo)", renderer_keq, text=7)
        column_keq.set_sort_column_id(7)
        column_keq.set_resizable(True)
        self.thermodynamic_tree.append_column(column_keq)
        
        # Column 8: ΔG°
        renderer_dg = Gtk.CellRendererText()
        column_dg = Gtk.TreeViewColumn("ΔG° (kJ/mol)", renderer_dg, text=8)
        column_dg.set_sort_column_id(8)
        column_dg.set_resizable(True)
        self.thermodynamic_tree.append_column(column_dg)
        
        # Column 9: Deviation
        renderer_dev = Gtk.CellRendererText()
        column_dev = Gtk.TreeViewColumn("Δlog", renderer_dev, text=9)
        column_dev.set_sort_column_id(9)
        column_dev.set_resizable(True)
        self.thermodynamic_tree.append_column(column_dev)
        
        # Column 10: Message (hidden by default, shown on selection)
        renderer_msg = Gtk.CellRendererText()
        renderer_msg.set_property("wrap-mode", Pango.WrapMode.WORD)
        renderer_msg.set_property("wrap-width", 400)
        column_msg = Gtk.TreeViewColumn("Details", renderer_msg, text=10)
        column_msg.set_visible(False)  # Hidden by default
        column_msg.set_resizable(True)
        self.thermodynamic_tree.append_column(column_msg)
        
        scrolled.add(self.thermodynamic_tree)
        box.pack_start(scrolled, True, True, 0)
        
        # Add button to toggle message column
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.show_details_btn = Gtk.Button(label="Show Details")
        self.show_details_btn.connect("clicked", self._on_toggle_details)
        btn_box.pack_start(self.show_details_btn, False, False, 0)
        box.pack_start(btn_box, False, False, 0)
        
        self.thermodynamic_expander.add(box)
        return self.thermodynamic_expander
    
    def _update_thermodynamic_display(self, results: dict):
        """Update thermodynamic validation display with results.
        
        Args:
            results: Dictionary with keys 'valid', 'warnings', 'violations', 'insufficient_data'
        """
        if not results:
            # No results - hide expander
            self.thermodynamic_expander.set_visible(False)
            return
        
        # Count results by category
        valid_count = len(results.get('valid', []))
        warning_count = len(results.get('warnings', []))
        violation_count = len(results.get('violations', []))
        insufficient_count = len(results.get('insufficient_data', []))
        total_count = valid_count + warning_count + violation_count + insufficient_count
        
        if total_count == 0:
            # No reversible transitions to validate
            self.thermodynamic_expander.set_visible(False)
            return
        
        # Determine status emoji and text
        if violation_count > 0:
            status_emoji = "❌"
            status_text = "Violations detected"
        elif warning_count > 0:
            status_emoji = "⚠️"
            status_text = "Warnings present"
        elif insufficient_count > 0:
            status_emoji = "ℹ️"
            status_text = "Incomplete data"
        else:
            status_emoji = "✅"
            status_text = "All valid"
        
        # Update status label with summary
        summary_text = f"{total_count} transitions: {valid_count} valid, {warning_count} warnings, {violation_count} violations, {insufficient_count} insufficient"
        self.thermodynamic_status.set_markup(
            f'<span size="large">{status_emoji}</span> <b>{status_text}</b> — {summary_text}'
        )
        
        # Clear and populate table
        self.thermodynamic_store.clear()
        
        # Helper to safely get float value
        def safe_float(value, default=0.0):
            if value is None:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # Helper to get transition rates
        def get_transition_rates(transition_name):
            """Get k_forward and k_reverse from model."""
            if not self.controller:
                return 0.0, 0.0
            for t in self.controller.model.transitions:
                if t.name == transition_name:
                    kf = getattr(t, 'rate_forward', None)
                    kr = getattr(t, 'rate_reverse', None)
                    return (safe_float(kf), safe_float(kr))
            return 0.0, 0.0
        
        # Helper to get transition details
        def get_transition_details(transition_name):
            """Get transition ID and label from model."""
            if not self.controller:
                return transition_name, transition_name
            for t in self.controller.model.transitions:
                if t.name == transition_name:
                    t_id = getattr(t, 'id', transition_name)
                    t_label = getattr(t, 'label', transition_name)
                    return t_id, t_label if t_label else transition_name
            return transition_name, transition_name
        
        # Helper to get delta_g from transition properties
        def get_delta_g(transition_name):
            """Get ΔG° from transition validation data."""
            if not self.controller:
                return 0.0
            for t in self.controller.model.transitions:
                if t.name == transition_name:
                    validation = t.properties.get('thermodynamic_validation', {})
                    return safe_float(validation.get('delta_g'))
            return 0.0
        
        # Add valid transitions
        for item in results.get('valid', []):
            transition_name = item.get('transition', 'Unknown')
            transition_id, transition_label = get_transition_details(transition_name)
            k_forward, k_reverse = get_transition_rates(transition_name)
            k_ratio = safe_float(item.get('k_ratio'), k_forward / k_reverse if k_reverse > 0 else 0)
            self.thermodynamic_store.append([
                "✅",
                transition_id,     # ID (T1, T2, etc.)
                transition_label,  # Label/description
                "Valid",
                k_forward,
                k_reverse,
                k_ratio,
                safe_float(item.get('k_eq')),
                get_delta_g(transition_name),
                safe_float(item.get('deviation')),
                "Kinetic rates consistent with thermodynamics"
            ])
        
        # Add warnings
        for item in results.get('warnings', []):
            transition_name = item.get('transition', 'Unknown')
            transition_id, transition_label = get_transition_details(transition_name)
            k_forward, k_reverse = get_transition_rates(transition_name)
            k_ratio = safe_float(item.get('k_ratio'), k_forward / k_reverse if k_reverse > 0 else 0)
            self.thermodynamic_store.append([
                "⚠️",
                transition_id,     # ID (T1, T2, etc.)
                transition_label,  # Label/description
                "Warning",
                k_forward,
                k_reverse,
                k_ratio,
                safe_float(item.get('k_eq')),
                get_delta_g(transition_name),
                safe_float(item.get('deviation')),
                item.get('message', 'Minor thermodynamic inconsistency')
            ])
        
        # Add violations
        for item in results.get('violations', []):
            transition_name = item.get('transition', 'Unknown')
            transition_id, transition_label = get_transition_details(transition_name)
            k_forward, k_reverse = get_transition_rates(transition_name)
            k_ratio = safe_float(item.get('k_ratio'), k_forward / k_reverse if k_reverse > 0 else 0)
            self.thermodynamic_store.append([
                "❌",
                transition_id,     # ID (T1, T2, etc.)
                transition_label,  # Label/description
                "Violation",
                k_forward,
                k_reverse,
                k_ratio,
                safe_float(item.get('k_eq')),
                get_delta_g(transition_name),
                safe_float(item.get('deviation')),
                item.get('message', 'Significant thermodynamic inconsistency')
            ])
        
        # Add insufficient data
        for item in results.get('insufficient_data', []):
            transition_name = item.get('transition', 'Unknown')
            transition_id, transition_label = get_transition_details(transition_name)
            k_forward, k_reverse = get_transition_rates(transition_name)
            self.thermodynamic_store.append([
                "ℹ️",
                transition_id,     # ID (T1, T2, etc.)
                transition_label,  # Label/description
                "Insufficient Data",
                k_forward,
                k_reverse,
                0.0,
                0.0,
                0.0,
                0.0,
                item.get('message', 'Cannot validate: missing thermodynamic data')
            ])
        
        # Show the frame (need both set_visible and show_all for no_show_all widgets)
        self.thermodynamic_expander.set_no_show_all(False)
        self.thermodynamic_expander.show_all()
        self.thermodynamic_expander.set_visible(True)
    
    def _on_toggle_details(self, button):
        """Toggle visibility of details column."""
        # Find the details column (index 10)
        columns = self.thermodynamic_tree.get_columns()
        if len(columns) > 10:
            details_col = columns[10]
            is_visible = details_col.get_visible()
            details_col.set_visible(not is_visible)
            button.set_label("Hide Details" if not is_visible else "Show Details")
    
    def _on_k_forward_edited(self, renderer, path, new_text):
        """Handle editing of k_forward value."""
        try:
            new_value = float(new_text)
            if new_value <= 0:
                self.logger.warning("k_forward must be positive")
                return
            
            # Update store
            iter_obj = self.thermodynamic_store.get_iter(path)
            old_kf = self.thermodynamic_store.get_value(iter_obj, 4)
            self.thermodynamic_store.set_value(iter_obj, 4, new_value)
            
            # Recalculate k_ratio
            k_reverse = self.thermodynamic_store.get_value(iter_obj, 5)
            if k_reverse > 0:
                k_ratio = new_value / k_reverse
                self.thermodynamic_store.set_value(iter_obj, 6, k_ratio)
            
            # Update transition in model
            transition_name = self.thermodynamic_store.get_value(iter_obj, 1)
            self._update_transition_rate(transition_name, 'forward', new_value)
            
            self.logger.info(f"Updated {transition_name} k_forward: {old_kf:.2e} → {new_value:.2e}")
            
            # Re-validate
            self._revalidate_transition(path)
            
        except ValueError:
            self.logger.warning(f"Invalid k_forward value: {new_text}")
    
    def _on_k_reverse_edited(self, renderer, path, new_text):
        """Handle editing of k_reverse value."""
        try:
            new_value = float(new_text)
            if new_value <= 0:
                self.logger.warning("k_reverse must be positive")
                return
            
            # Update store
            iter_obj = self.thermodynamic_store.get_iter(path)
            old_kr = self.thermodynamic_store.get_value(iter_obj, 5)
            self.thermodynamic_store.set_value(iter_obj, 5, new_value)
            
            # Recalculate k_ratio
            k_forward = self.thermodynamic_store.get_value(iter_obj, 4)
            if new_value > 0:
                k_ratio = k_forward / new_value
                self.thermodynamic_store.set_value(iter_obj, 6, k_ratio)
            
            # Update transition in model
            transition_name = self.thermodynamic_store.get_value(iter_obj, 1)
            self._update_transition_rate(transition_name, 'reverse', new_value)
            
            self.logger.info(f"Updated {transition_name} k_reverse: {old_kr:.2e} → {new_value:.2e}")
            
            # Re-validate
            self._revalidate_transition(path)
            
        except ValueError:
            self.logger.warning(f"Invalid k_reverse value: {new_text}")
    
    def _update_transition_rate(self, transition_name: str, direction: str, value: float):
        """Update rate constant in the model."""
        if not self.controller:
            self.logger.warning("No controller available to update transition")
            return
        
        # Find transition in model
        for transition in self.controller.model.transitions:
            if transition.name == transition_name:
                if direction == 'forward':
                    transition.set_rate_forward(value)
                    # Update rate_function if it exists
                    rate_func = transition.get_rate_function()
                    if rate_func:
                        # Update k_f or k_forward in the formula
                        import re
                        formula = re.sub(r'\bk_f\b', str(value), rate_func)
                        formula = re.sub(r'\bk_forward\b', str(value), formula)
                        transition.set_rate_function(formula)
                elif direction == 'reverse':
                    transition.set_rate_reverse(value)
                    # Update rate_function if it exists
                    rate_func = transition.get_rate_function()
                    if rate_func:
                        import re
                        formula = re.sub(r'\bk_r\b', str(value), rate_func)
                        formula = re.sub(r'\bk_reverse\b', str(value), formula)
                        transition.set_rate_function(formula)
                
                self.logger.debug(f"Updated {transition_name}.{direction} = {value}")
                return
        
        self.logger.warning(f"Transition {transition_name} not found in model")
    
    def _revalidate_transition(self, path: str):
        """Re-validate a transition after editing."""
        if not self.controller:
            return
        
        iter_obj = self.thermodynamic_store.get_iter(path)
        transition_name = self.thermodynamic_store.get_value(iter_obj, 1)
        k_forward = self.thermodynamic_store.get_value(iter_obj, 4)
        k_reverse = self.thermodynamic_store.get_value(iter_obj, 5)
        k_eq = self.thermodynamic_store.get_value(iter_obj, 7)
        
        if k_eq <= 0:
            # Can't validate without K_eq
            return
        
        # Calculate new ratio
        k_ratio = k_forward / k_reverse if k_reverse > 0 else 0
        
        # Calculate deviation (orders of magnitude)
        import math
        if k_ratio > 0 and k_eq > 0:
            log_deviation = abs(math.log10(k_ratio) - math.log10(k_eq))
        else:
            log_deviation = 0
        
        # Determine new status (using 1.0 order of magnitude as threshold for violations)
        tolerance = 1.0  # From validator default
        if log_deviation <= tolerance:
            status_icon = "✅"
            status_text = "Valid"
            message = f"Kinetic ratio {k_ratio:.2e} matches K_eq {k_eq:.2e}"
        elif log_deviation <= 2.0:
            status_icon = "⚠️"
            status_text = "Warning"
            message = f"Deviation {log_deviation:.2f} orders of magnitude"
        else:
            status_icon = "❌"
            status_text = "Violation"
            message = f"Large deviation {log_deviation:.2f} orders of magnitude"
        
        # Update row
        self.thermodynamic_store.set_value(iter_obj, 0, status_icon)
        self.thermodynamic_store.set_value(iter_obj, 3, status_text)
        self.thermodynamic_store.set_value(iter_obj, 6, k_ratio)
        self.thermodynamic_store.set_value(iter_obj, 9, log_deviation)
        self.thermodynamic_store.set_value(iter_obj, 10, message)
        
        self.logger.info(f"Re-validated {transition_name}: {status_text} (Δlog={log_deviation:.2f})")
    
    # Event handlers
    
    def _on_mode_changed(self, radio_button):
        """Handle mode radio button changes."""
        if not radio_button.get_active():
            return
        
        if self.local_radio.get_active():
            # Local mode
            self.file_entry.set_placeholder_text("Path to SBML file")
            self.browse_button.set_visible(True)
            self.source_info.set_markup(
                '<span size="small">Enter full path to local SBML file (.sbml or .xml)</span>'
            )
        else:
            # BioModels mode
            self.file_entry.set_placeholder_text("BioModels ID (e.g., BIOMD0000000001)")
            self.browse_button.set_visible(False)
            self.source_info.set_markup(
                '<span size="small">Enter a <a href="https://www.ebi.ac.uk/biomodels/">BioModels</a> ID</span>'
            )
    
    def _on_file_entry_changed(self, entry):
        """Handle accession entry text changes."""
        text = entry.get_text().strip()
        
        if self.local_radio.get_active():
            # Local mode - check if file exists
            file_exists = bool(text and os.path.exists(text))
            self.import_button.set_sensitive(file_exists)
            
            # Auto-parse and preview SBML file when valid file is selected
            if file_exists:
                self._parse_and_preview_sbml(text)
        else:
            # BioModels mode - check if ID is not empty
            self.import_button.set_sensitive(len(text) > 0)
        
        # Also check project state
        if not self.project:
            self.import_button.set_sensitive(False)

    def _on_browse_clicked(self, button):
        """Open SBML file chooser and populate the file entry."""
        self._open_sbml_file_dialog(self.file_entry)

    def _parse_and_preview_sbml(self, filepath):
        """Parse SBML file and show preview in metadata inspector.
        
        This provides immediate feedback when browsing files before import.
        Populates BOTH the text preview AND the metadata table.
        
        Args:
            filepath: Path to SBML file to parse
        """
        if not self.parser:
            self.logger.warning("SBML parser not available for preview")
            return
        
        def parse_in_thread():
            try:
                self.logger.info(f"Parsing SBML for preview: {filepath}")
                
                # Parse SBML file using parse_file (not parse)
                parsed_pathway = self.parser.parse_file(filepath)
                
                if parsed_pathway:
                    # Store for later use in import
                    self.current_filepath = filepath
                    self.parsed_pathway = parsed_pathway
                    
                    # Update BOTH preview text AND metadata table on main thread
                    from gi.repository import GLib
                    GLib.idle_add(self._update_preview, parsed_pathway)
                    GLib.idle_add(self._update_metadata_tree, parsed_pathway)
                    
                    # Metadata will be visible when user expands the inspector
                    
                    self.logger.info("✅ SBML preview and metadata table updated")
                else:
                    GLib.idle_add(self._show_parse_error, "Failed to parse SBML file")
                    
            except Exception as e:
                self.logger.error(f"Error parsing SBML for preview: {e}")
                import traceback
                traceback.print_exc()
                from gi.repository import GLib
                GLib.idle_add(self._show_parse_error, str(e))
        
        # Parse in background thread to avoid UI freeze
        import threading
        thread = threading.Thread(target=parse_in_thread, daemon=True)
        thread.start()
    
    def _show_parse_error(self, error_msg):
        """Show parse error in metadata inspector.
        
        Args:
            error_msg: Error message to display
        """
        self.metadata_store.clear()
        buffer = self.preview_text.get_buffer()
        buffer.set_text(f"⚠️ Error parsing SBML file:\\n\\n{error_msg}")
        return False  # Don't repeat
    
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
                "No project open. Please open or create a project first:\n"
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
        
        Workflow:
        1. Reuse cached parse if available (from preview)
        2. Otherwise parse SBML → PathwayData
        3. Post-process (layout, colors)
        4. Convert to Petri net
        5. Save to project
        6. Load to canvas
        
        Args:
            filepath: Path to SBML file
        """
        def parse_and_convert():
            try:
                # 1. Parse SBML → PathwayData (reuse cached if available)
                if (self.parsed_pathway and 
                    self.current_filepath == filepath and
                    not getattr(self.parsed_pathway, 'metadata', {}).get('modified', False)):
                    # Reuse cached parse from preview
                    self.logger.info(f"Reusing cached parse for: {filepath}")
                    parsed_pathway = self.parsed_pathway
                else:
                    # Parse fresh (file changed or was edited)
                    self.logger.info(f"Parsing SBML file: {filepath}")
                    parsed_pathway = self.parser.parse_file(filepath)
                
                # 1.5. Check for stochastic compatibility warnings and show dialog
                # Must be done on main thread (GTK requirement), so queue it
                validation_issues = parsed_pathway.metadata.get('validation_issues', [])
                stochastic_warnings = [
                    issue for issue in validation_issues
                    if issue.get('category') in ['assignment_rules', 'reversible_formulas']
                    and issue.get('severity') in ['warning', 'error']
                ]
                
                if stochastic_warnings:
                    # Show dialog on main thread and wait for user choice
                    user_choice_holder = [None]  # Mutable container for thread communication
                    
                    def show_dialog_on_main_thread():
                        user_choice = self._show_stochastic_warning_dialog(stochastic_warnings)
                        user_choice_holder[0] = user_choice
                        return False  # Don't repeat
                    
                    # Queue dialog on main thread and wait for completion
                    GLib.idle_add(show_dialog_on_main_thread)
                    
                    # Wait for user choice (with timeout)
                    timeout = 60  # 60 seconds
                    elapsed = 0
                    while user_choice_holder[0] is None and elapsed < timeout:
                        time.sleep(0.1)
                        elapsed += 0.1
                    
                    user_choice = user_choice_holder[0]
                    
                    if user_choice == 'cancel' or user_choice is None:
                        # User cancelled or timeout
                        raise ValueError("Import cancelled by user")
                    elif user_choice in ['convert_continuous', 'convert_hybrid', 'stochastic_with_reevaluation']:
                        # Store user choice in metadata for converter to apply
                        choice_map = {
                            'convert_continuous': 'continuous',
                            'convert_hybrid': 'hybrid',
                            'proceed_anyway': 'stochastic',
                            'stochastic_with_reevaluation': 'stochastic_with_reevaluation'
                        }
                        parsed_pathway.metadata['user_choice_transition_type'] = choice_map[user_choice]
                
                # 2. Post-process → ProcessedPathwayData
                self.logger.info("Post-processing pathway data...")
                postprocessor = PathwayPostProcessor(scale_factor=1.0)
                processed_pathway = postprocessor.process(parsed_pathway)
                
                # 3. Convert to Petri net → DocumentModel
                self.logger.info("Converting to Petri net...")
                document_model = self.converter.convert(processed_pathway)
                
                # 3.5: Detect and classify signal places (energy metabolites)
                if SBMLCompartmentModuleService:
                    self.logger.info("Detecting signal places...")
                    from shypn.netobjs.signal_type import SignalType
                    
                    # Auto-detect energy signals (ATP, NAD, CoA, etc.)
                    signal_count = 0
                    for place in document_model.places:
                        if hasattr(place, 'metadata') and place.metadata:
                            species_id = place.metadata.get('original_species_id', '').lower()
                            # Common energy metabolites
                            energy_markers = ['atp', 'adp', 'amp', 'nad', 'nadh', 'nadp', 'nadph', 
                                            'fad', 'fadh', 'coa', 'accoa', 'gtp', 'gdp', 'ctp', 'utp']
                            if any(marker in species_id for marker in energy_markers):
                                place.is_signal_place = True
                                place.signal_type = SignalType.ENERGY
                                signal_count += 1
                    
                    if signal_count > 0:
                        self.logger.info(f"  Detected {signal_count} energy signal places")
                
                # 3.6: Convert arcs to/from signal places to SignalFlowArcs
                signal_places = [p for p in document_model.places if getattr(p, 'is_signal_place', False)]
                if signal_places:
                    self.logger.info("Converting arcs to signal places to SignalFlowArcs...")
                    from shypn.netobjs.signal_flow_arc import SignalFlowArc
                    from shypn.netobjs.arc import Arc
                    
                    signal_place_set = set(signal_places)
                    converted_count = 0
                    new_arcs = []
                    
                    for arc in document_model.arcs:
                        # Check if arc connects to/from a signal place
                        if isinstance(arc, Arc) and not isinstance(arc, SignalFlowArc):
                            if arc.source in signal_place_set or arc.target in signal_place_set:
                                # Convert to SignalFlowArc
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
                
                # 3.7: Enforce color schema on all entities
                self.logger.info("Enforcing color schema on all entities...")
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
                
                # 4. Convert SBML compartments to modules (if service available)
                if SBMLCompartmentModuleService and document_model and processed_pathway:
                    try:
                        # Build species_id → Place mapping using metadata
                        # The original species.id is stored in place.metadata['original_species_id']
                        species_to_place = {}
                        for place in document_model.places:
                            if hasattr(place, 'metadata') and place.metadata:
                                original_species_id = place.metadata.get('original_species_id')
                                if original_species_id:
                                    species_to_place[original_species_id] = place
                        
                        # Build reaction_id → Transition mapping
                        # The original reaction.id is stored in transition.metadata['reaction_id']
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
                            validate=True
                        )
                        
                        if conversion_result and conversion_result.get('success'):
                            # Add modules to document so they're saved
                            modules = conversion_result.get('modules', [])
                            for module in modules:
                                document_model.add_module(module)
                    except Exception as e:
                        # Module conversion failed, continue without modules
                        self.logger.debug("Module conversion failed, continuing without modules: %s", e)
                
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

        Orchestrates four phases:
        1. Persist to project (``_save_to_project``)
        2. Refresh preview (``_update_preview``)
        3. Auto-load model into a fresh canvas tab (``_provision_canvas_tab``)
        4. Deferred Report Panel wiring + compound mapping

        Args:
            result: Dict with keys 'filepath', 'parsed_pathway', 'document_model'
        """
        try:
            filepath = result['filepath']
            parsed_pathway = result['parsed_pathway']
            document_model = result['document_model']

            self.logger.info("SBML import complete — pathway type: %s", type(parsed_pathway).__name__)

            # Phase 1: persist
            saved_filepath = self._save_to_project(filepath, parsed_pathway, document_model)
            if not saved_filepath:
                self._show_error("Failed to save files to project")
                self.import_button.set_sensitive(True)
                return

            # Phase 2: preview
            try:
                self._update_preview(parsed_pathway)
                self.logger.info("Preview updated")
            except Exception as preview_error:
                self.logger.error("Failed to update preview: %s", preview_error, exc_info=True)

            # Phase 3: canvas auto-load
            canvas_loader = self._get_canvas_loader()
            self.logger.info(
                "Auto-load check: model_canvas=%s, canvas_loader=%s, "
                "document_model=%s, saved_filepath=%s",
                self.model_canvas is not None, canvas_loader is not None,
                document_model is not None, saved_filepath is not None,
            )
            
            if canvas_loader and document_model and saved_filepath:
                base_name = os.path.splitext(os.path.basename(saved_filepath))[0]
                drawing_area = self._provision_canvas_tab(
                    canvas_loader, document_model, saved_filepath, base_name, parsed_pathway
                )
                if drawing_area is not None:
                    self._schedule_report_panel_refresh(
                        canvas_loader, drawing_area, base_name, saved_filepath, parsed_pathway
                    )
            else:
                reason = "model_canvas is None" if not self.model_canvas else "canvas_loader not detected"
                self.logger.info("Canvas auto-load skipped: %s", reason)
                self._show_status(
                    f"✅ Model saved successfully:\n{saved_filepath}\n\n"
                    "💡 Open from the file browser on the left to view the model",
                    error=False,
                )

            # Phase 4: trigger import-complete callbacks
            self._trigger_import_complete({
                'source':   'sbml',
                'filepath': filepath,
                'pathway':  parsed_pathway,
                'model':    document_model,
            })

            # Phase 5: compound mapping for thermodynamics
            self._map_compounds_after_import(document_model)

            self.import_button.set_sensitive(True)

        except Exception as e:
            self.logger.error("Post-import processing failed: %s", e, exc_info=True)
            self._show_error(f"Import failed: {e}")
            self.import_button.set_sensitive(True)

    # ------------------------------------------------------------------
    # Import-complete helpers (extracted from _on_sbml_import_complete)
    # ------------------------------------------------------------------

    def _provision_canvas_tab(self, canvas_loader, document_model, saved_filepath, base_name, parsed_pathway):
        """Create a fresh canvas tab, load objects, and wire state for an SBML import.

        Returns:
            GtkDrawingArea if successful, otherwise None.
        """
        try:
            self.logger.info("Creating fresh canvas tab for SBML import: %s", base_name)
            page_index, drawing_area = canvas_loader.add_document(filename="importing_temp")
            self.logger.info(
                "[SBML AUTO-LOAD] Step 1: add_document() page_index=%s, drawing_area=%s",
                page_index, id(drawing_area) if drawing_area else 'None',
            )
            if drawing_area is None:
                raise ValueError("add_document() returned None for drawing_area")

            canvas_manager = canvas_loader.get_canvas_manager(drawing_area)
            self.logger.info(
                "[SBML AUTO-LOAD] Step 2: get_canvas_manager() → %s (%s)",
                canvas_manager is not None,
                type(canvas_manager).__name__ if canvas_manager else 'None',
            )
            if not canvas_manager:
                raise ValueError("get_canvas_manager() returned None")

            self.logger.info("[SBML AUTO-LOAD] Step 3: filepath → %s", saved_filepath)
            canvas_manager.set_filepath(saved_filepath)

            self.logger.info(
                "[SBML AUTO-LOAD] Step 4: loading objects — places=%d, transitions=%d, arcs=%d",
                len(document_model.places), len(document_model.transitions), len(document_model.arcs),
            )
            try:
                canvas_manager.load_objects(
                    places=document_model.places,
                    transitions=document_model.transitions,
                    arcs=document_model.arcs,
                    modules=document_model.modules,
                )
                self.logger.info("[SBML AUTO-LOAD] Step 5: load_objects() completed")
            except Exception as e:
                raise ValueError(f"Failed to load objects to canvas: {e}") from e

            # Copy metadata
            if hasattr(canvas_manager, 'document') and hasattr(document_model, 'metadata'):
                for key, value in document_model.metadata.items():
                    canvas_manager.document.metadata[key] = value
                self.logger.info("Copied metadata (%d keys)", len(document_model.metadata))

            # Wire change callback
            if hasattr(canvas_manager, 'document_controller') and canvas_manager.document_controller:
                try:
                    canvas_manager.document_controller.set_change_callback(
                        canvas_manager._on_object_changed
                    )
                except Exception as e:
                    self.logger.warning("Failed to set change callback: %s", e)
            else:
                self.logger.warning("document_controller not available for change callback")

            canvas_manager.mark_clean()
            canvas_manager.mark_as_imported(base_name)

            if hasattr(canvas_manager, '_suppress_callbacks'):
                canvas_manager._suppress_callbacks = False

            canvas_manager.fit_to_page(
                padding_percent=15,
                deferred=True,
                horizontal_offset_percent=30,
                vertical_offset_percent=-10,
            )
            canvas_manager.mark_needs_redraw()

            if hasattr(canvas_loader, '_ensure_simulation_reset'):
                canvas_loader._ensure_simulation_reset(drawing_area)

            self.logger.info("=== SBML canvas auto-load COMPLETED ===")
            self._show_status(
                f"✅ Model loaded to canvas: {base_name}\n"
                "💡 Use View → Fit to Page (Ctrl+0) to adjust view if needed"
            )
            return drawing_area

        except Exception as load_error:
            self.logger.error("SBML canvas auto-load FAILED: %s", load_error, exc_info=True)
            self._show_status(
                f"✅ Model saved successfully:\n{saved_filepath}\n\n"
                "💡 Open from the file browser on the left to view the model"
            )
            return None

    def _schedule_report_panel_refresh(
        self, canvas_loader, drawing_area, base_name, saved_filepath, parsed_pathway
    ):
        """Schedule a deferred GLib idle callback to wire the Report Panel after import."""
        if not (
            hasattr(canvas_loader, 'overlay_managers')
            and canvas_loader.overlay_managers
            and drawing_area in canvas_loader.overlay_managers
        ):
            return

        def refresh_report_panel():
            try:
                overlay_manager = canvas_loader.overlay_managers.get(drawing_area)
                if not (overlay_manager and hasattr(overlay_manager, 'report_panel_loader')):
                    return False
                report_panel_loader = overlay_manager.report_panel_loader
                if not (report_panel_loader and hasattr(report_panel_loader, 'panel')):
                    return False

                self.logger.info("Triggering Report Panel refresh after SBML import (deferred)")
                simulation_controller = getattr(overlay_manager, 'simulation_controller', None)
                if not simulation_controller:
                    return False

                from shypn.events import EventBus
                from shypn.core.document_id import doc_id
                EventBus.emit(
                    'simulation.controller_ready',
                    {'controller': simulation_controller},
                    document_id=doc_id(drawing_area),
                )
                self.logger.info("✅ Report Panel controller notified")

                # Resolve metadata path
                if self.project and hasattr(self.project, 'get_metadata_dir'):
                    metadata_dir = self.project.get_metadata_dir()
                    if metadata_dir:
                        shypn_path = os.path.join(metadata_dir, f"{base_name}.shypn")
                    else:
                        shypn_path = saved_filepath.replace('.shy', '.shypn')
                else:
                    shypn_path = saved_filepath.replace('.shy', '.shypn')

                if hasattr(report_panel_loader.panel, 'on_file_opened'):
                    report_panel_loader.panel.on_file_opened(shypn_path)
                    self.logger.info("✅ Metadata loaded from: %s", shypn_path)

                self.refresh_metadata_inspector()
                self.logger.info("✅ SBML Metadata Inspector refreshed")
                self.set_controller(simulation_controller)
                self.logger.info("✅ SBML category controller set")

                # Option 3: assignment-rule re-evaluation
                if hasattr(parsed_pathway, 'metadata'):
                    user_choice = parsed_pathway.metadata.get('user_choice_transition_type')
                    if user_choice == 'stochastic_with_reevaluation':
                        simulation_controller.enable_assignment_rule_reevaluation = True
                        simulation_controller.initialize_assignment_rules(parsed_pathway)
                        self.logger.info("✅ Option 3: assignment-rule re-evaluation enabled")

                def run_validation():
                    try:
                        self.logger.info("Running thermodynamic validation...")
                        simulation_controller.validate_thermodynamics()
                        results = simulation_controller.thermodynamic_results
                        if results:
                            self._update_thermodynamic_display(results)
                            self.logger.info(
                                "Thermodynamic validation: %d valid, %d warnings, %d violations",
                                len(results.get('valid', [])),
                                len(results.get('warnings', [])),
                                len(results.get('violations', [])),
                            )
                        else:
                            self.logger.info("No thermodynamic results (no reversible transitions)")
                    except Exception as e:
                        self.logger.error("Thermodynamic validation failed: %s", e, exc_info=True)
                    return False

                GLib.idle_add(run_validation)

            except Exception as e:
                self.logger.warning("Failed to refresh report panel: %s", e)
            return False

        GLib.idle_add(refresh_report_panel)
        self.logger.info("Report Panel refresh scheduled (idle)")

    def _map_compounds_after_import(self, document_model):
        """Run thermodynamic compound mapping after a successful SBML import."""
        if not document_model:
            return
        try:
            from shypn.thermodynamics.mappers import CompoundMapperService
            mapper_service = CompoundMapperService()
            mappings, confidences = mapper_service.map_all_places(document_model)
            summary = mapper_service.get_mapping_summary(mappings, confidences)
            self.logger.info(
                "Thermodynamic mapping: %d/%d places mapped (avg confidence: %.0f%%)",
                summary['total_mapped'], len(document_model.places),
                summary['average_confidence'] * 100,
            )
        except Exception as e:
            self.logger.warning("Compound mapping failed (non-critical): %s", e)

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
            
            # CRITICAL: Save PathwayData for metadata inspector
            # Store serialized pathway data in metadata so it can be loaded later
            if parsed_pathway:
                try:
                    # Serialize the essential pathway data for the metadata inspector
                    pathway_dict = {
                        'name': getattr(parsed_pathway, 'name', base_name),
                        'organism': getattr(parsed_pathway, 'organism', 'Unknown'),
                        'species_count': len(getattr(parsed_pathway, 'species', [])),
                        'reactions_count': len(getattr(parsed_pathway, 'reactions', [])),
                        'parameters': getattr(parsed_pathway, 'parameters', {}),
                        'constants': list(getattr(parsed_pathway, 'constants', set())),
                        'compartments_enhanced': {
                            comp_id: {
                                'id': comp.id,
                                'name': comp.name,
                                'size': comp.size
                            }
                            for comp_id, comp in getattr(parsed_pathway, 'compartments_enhanced', {}).items()
                        } if hasattr(parsed_pathway, 'compartments_enhanced') else {},
                        'events_count': len(getattr(parsed_pathway, 'events', [])),
                        'metadata': getattr(parsed_pathway, 'metadata', {})
                    }
                    doc_model.metadata['sbml_pathway_data'] = pathway_dict
                    self.logger.info(f"Saved PathwayData to metadata: {len(pathway_dict)} keys")
                except Exception as e:
                    self.logger.warning(f"Could not serialize PathwayData: {e}")
            
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
        
        # Also update metadata tree
        self._update_metadata_tree(pathway)
    
    def _update_metadata_tree(self, pathway):
        """Update metadata tree with SBML information.
        
        Args:
            pathway: PathwayData object from parser
        """
        def do_update():
            try:
                self.metadata_store.clear()
                
                if not pathway:
                    root = self.metadata_store.append(None, [
                        "ℹ️", "No pathway data", "", "", "", ""
                    ])
                    return False
                
                # Parameters section - split into constants and variables
                all_params = getattr(pathway, 'parameters', {})
                constants_dict = {}
                variables_dict = {}
                
                # Check if pathway has explicit constant marking
                if hasattr(pathway, 'constants') and pathway.constants:
                    for param_id, param_value in all_params.items():
                        if param_id in pathway.constants:
                            constants_dict[param_id] = param_value
                        else:
                            variables_dict[param_id] = param_value
                else:
                    # Treat all as variables if not explicitly marked
                    variables_dict = all_params
                
                # Global Constants section
                if constants_dict:
                    constants_root = self.metadata_store.append(None, [
                        "🔒", "Global Constants", f"{len(constants_dict)} items",
                        "section", "", "Read-only global parameters"
                    ])
                    for param_id, param_value in constants_dict.items():
                        self.metadata_store.append(constants_root, [
                            "🔒", param_id, str(param_value), "constant",
                            param_id, f"Constant: {param_id} = {param_value} (read-only)"
                        ])
                
                # Global Variables section
                if variables_dict:
                    variables_root = self.metadata_store.append(None, [
                        "📊", "Global Variables", f"{len(variables_dict)} items",
                        "section", "", "Editable global parameters"
                    ])
                    for param_id, param_value in variables_dict.items():
                        self.metadata_store.append(variables_root, [
                            "🌐", param_id, str(param_value), "parameter",
                            param_id, f"Variable: {param_id} = {param_value}"
                        ])
                
                # All Parameters section (legacy, keep for compatibility)
                if not constants_dict and not variables_dict:
                    params_root = self.metadata_store.append(None, [
                        "📊", "Parameters", f"{len(all_params)} items",
                        "section", "", "Global and local kinetic parameters"
                    ])
                    for param_id, param_value in all_params.items():
                        self.metadata_store.append(params_root, [
                            "🌐", param_id, str(param_value), "parameter",
                            param_id, f"Global parameter: {param_id} = {param_value}"
                        ])
                
                # Compartments section
                comps = getattr(pathway, 'compartments_enhanced', {})
                comps_root = self.metadata_store.append(None, [
                    "🔷", "Compartments", f"{len(comps)} items",
                    "section", "", "Cellular compartments with volumes"
                ])
                for comp_id, comp in comps.items():
                    self.metadata_store.append(comps_root, [
                        "🔷", comp.name, f"{comp.size} L",
                        "compartment", comp_id,
                        f"Compartment: {comp.name}, Volume: {comp.size} L"
                    ])
                
                # Species section (with annotations)
                species = getattr(pathway, 'species', [])
                species_root = self.metadata_store.append(None, [
                    "🔵", "Species", f"{len(species)} items",
                    "section", "", "Metabolites and compounds"
                ])
                for s in species[:20]:  # Limit to first 20 for performance
                    species_iter = self.metadata_store.append(species_root, [
                        "🔵", s.name or s.id, 
                        f"{s.initial_concentration} mM" if s.initial_concentration else "",
                        "species", s.id,
                        f"Species: {s.name or s.id}, Compartment: {s.compartment or 'default'}"
                    ])
                    
                    # Add annotations if available
                    if hasattr(s, 'annotation') and s.annotation:
                        annot = s.annotation
                        if hasattr(annot, 'identifiers') and annot.identifiers:
                            for db, db_id in annot.identifiers.items():
                                self.metadata_store.append(species_iter, [
                                    "🏷️", db.upper(), db_id, "annotation",
                                    "", f"Database ID: {db}:{db_id}"
                                ])
                
                # Reactions section
                reactions = getattr(pathway, 'reactions', [])
                reactions_root = self.metadata_store.append(None, [
                    "🔶", "Reactions", f"{len(reactions)} items",
                    "section", "", "Biochemical reactions"
                ])
                for r in reactions[:20]:  # Limit to first 20
                    r_name = r.name or r.id
                    reaction_iter = self.metadata_store.append(reactions_root, [
                        "🔶", r_name, 
                        "reversible" if r.reversible else "irreversible",
                        "reaction", r.id,
                        f"Reaction: {r_name}"
                    ])
                    
                    # Add local parameters if available
                    if hasattr(r, 'kinetic_law') and r.kinetic_law:
                        if hasattr(r.kinetic_law, 'parameters') and r.kinetic_law.parameters:
                            params_iter = self.metadata_store.append(reaction_iter, [
                                "📊", "Local Parameters", 
                                f"{len(r.kinetic_law.parameters)} items",
                                "section", "", "Parameters specific to this reaction"
                            ])
                            for param_id, param_value in r.kinetic_law.parameters.items():
                                self.metadata_store.append(params_iter, [
                                    "🔵", param_id, str(param_value),
                                    "local_param", param_id,
                                    f"Local parameter: {param_id} = {param_value}"
                                ])
                
                # Events section
                events = getattr(pathway, 'events', [])
                events_root = self.metadata_store.append(None, [
                    "⚡", "Events", f"{len(events)} items",
                    "section", "", "Time/state-triggered perturbations"
                ])
                if events:
                    for event in events:
                        event_iter = self.metadata_store.append(events_root, [
                            "⚡", event.name or event.id,
                            event.trigger[:50] if event.trigger else "",
                            "event", event.id,
                            f"Trigger: {event.trigger}"
                        ])
                        # Add assignments
                        if hasattr(event, 'assignments') and event.assignments:
                            for var, expr in event.assignments.items():
                                self.metadata_store.append(event_iter, [
                                    "➜", var, expr[:50], "assignment",
                                    "", f"Sets {var} = {expr}"
                                ])
                else:
                    self.metadata_store.append(events_root, [
                        "", "No events", "", "", "", ""
                    ])
                
                # Function Definitions section
                metadata = getattr(pathway, 'metadata', {})
                function_count = metadata.get('function_definitions_count', 0)
                functions_root = self.metadata_store.append(None, [
                    "ƒ", "Function Definitions", f"{function_count} items",
                    "section", "", "User-defined mathematical functions"
                ])
                if function_count > 0:
                    function_names = metadata.get('function_definitions', [])
                    for func_name in function_names:
                        # Extract function name and arguments
                        if '(' in func_name:
                            name_part = func_name.split('(')[0]
                            args_part = func_name.split('(', 1)[1].rstrip(')')
                            self.metadata_store.append(functions_root, [
                                "ƒ", name_part, args_part,
                                "function", name_part,
                                f"Function: {func_name}"
                            ])
                        else:
                            self.metadata_store.append(functions_root, [
                                "ƒ", func_name, "",
                                "function", func_name,
                                f"Function: {func_name}"
                            ])
                else:
                    self.metadata_store.append(functions_root, [
                        "", "No function definitions", "", "", "", ""
                    ])
                
                # Expand all tree rows to show the metadata
                self.metadata_tree.expand_all()
                
            except Exception as e:
                self.logger.error(f"Error updating metadata tree: {e}", exc_info=True)
            
            return False
        
        GLib.idle_add(do_update)
    
    def _on_metadata_row_clicked(self, tree_view, path, column):
        """Handle metadata tree row activation.
        
        Shows a dialog with full information about the clicked item.
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
    
    def _on_value_edited(self, renderer, path, new_text):
        """Handle value editing in metadata tree.
        
        Updates the underlying pathway data and marks as modified.
        """
        try:
            model = self.metadata_store
            iter_node = model.get_iter(path)
            
            obj_type = model.get_value(iter_node, 3)  # type column
            obj_id = model.get_value(iter_node, 4)    # object_id column
            old_value = model.get_value(iter_node, 2) # current value
            
            # Check if this is a constant (read-only)
            if obj_type == 'constant':
                dialog = Gtk.MessageDialog(
                    transient_for=self.parent_window,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK,
                    text="Cannot Edit Constant"
                )
                dialog.format_secondary_text(f"{obj_id} is marked as a constant and cannot be edited.")
                dialog.run()
                dialog.destroy()
                return
            
            # Validate and parse new value
            try:
                # Try to parse as float for numeric parameters
                if obj_type in ['parameter', 'local_param', 'compartment']:
                    # Remove units if present (e.g., "1.5 L" -> 1.5)
                    numeric_part = new_text.split()[0] if ' ' in new_text else new_text
                    new_value = float(numeric_part)
                else:
                    new_value = new_text
            except ValueError:
                # If not numeric, keep as string
                new_value = new_text
            
            # Update the tree store
            model.set_value(iter_node, 2, str(new_value))
            
            # Update the underlying pathway data
            if not self.parsed_pathway:
                self.logger.warning("No parsed pathway to update")
                return
            
            if obj_type == 'parameter':
                # Update global parameter
                if hasattr(self.parsed_pathway, 'parameters'):
                    if obj_id in self.parsed_pathway.parameters:
                        self.parsed_pathway.parameters[obj_id] = new_value
                        self.logger.info(f"Updated global parameter {obj_id}: {old_value} → {new_value}")
                        self._show_status(f"✓ Updated {obj_id} = {new_value}")
            
            elif obj_type == 'compartment':
                # Update compartment size
                if hasattr(self.parsed_pathway, 'compartments_enhanced'):
                    if obj_id in self.parsed_pathway.compartments_enhanced:
                        comp = self.parsed_pathway.compartments_enhanced[obj_id]
                        comp.size = new_value
                        # Also update in parameters dict (used in formulas)
                        if hasattr(self.parsed_pathway, 'parameters'):
                            self.parsed_pathway.parameters[obj_id] = new_value
                        self.logger.info(f"Updated compartment {obj_id}: {old_value} → {new_value}")
                        self._show_status(f"✓ Updated compartment {obj_id} = {new_value} L")
            
            elif obj_type == 'local_param':
                # Update local parameter in reaction
                # Need to find the parent reaction
                parent_iter = model.iter_parent(iter_node)
                if parent_iter:
                    grandparent_iter = model.iter_parent(parent_iter)
                    if grandparent_iter:
                        reaction_id = model.get_value(grandparent_iter, 4)
                        if hasattr(self.parsed_pathway, 'reactions'):
                            for reaction in self.parsed_pathway.reactions:
                                if reaction.id == reaction_id:
                                    if hasattr(reaction, 'kinetic_law') and reaction.kinetic_law:
                                        if hasattr(reaction.kinetic_law, 'parameters'):
                                            if obj_id in reaction.kinetic_law.parameters:
                                                reaction.kinetic_law.parameters[obj_id] = new_value
                                                self.logger.info(
                                                    f"Updated local parameter {obj_id} in {reaction_id}: "
                                                    f"{old_value} → {new_value}"
                                                )
                                                self._show_status(
                                                    f"✓ Updated {obj_id} = {new_value} in {reaction_id}"
                                                )
                                                break
            
            # Mark as modified
            if hasattr(self.parsed_pathway, 'metadata'):
                if not isinstance(self.parsed_pathway.metadata, dict):
                    self.parsed_pathway.metadata = {}
                self.parsed_pathway.metadata['modified'] = True
                self.parsed_pathway.metadata['modified_time'] = time.time()
        
        except Exception as e:
            self.logger.error(f"Error editing value: {e}", exc_info=True)
            self._show_status(f"✗ Error updating value: {e}", error=True)
    
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
    
    def set_controller(self, controller):
        """Set simulation controller for thermodynamic validation.
        
        Args:
            controller: SimulationController instance
        """
        self.controller = controller
        self.logger.debug(f"Controller set for thermodynamic validation")
    
    def on_tab_switched(self):
        """Called when the user switches to a different model tab.
        
        Note: Metadata inspector refresh is deferred until user expands it.
        
        Updates the SBML panel to reflect the currently active model:
        - Refreshes button states
        - Updates status labels
        """
        self.logger.debug("Tab switched, updating SBML panel state")
    
    def refresh_metadata_inspector(self):
        """Refresh SBML Metadata Inspector for the currently active document.
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
        
        # Update buttons and metadata based on active document
        if document:
            # Check if SBML model
            is_sbml = False
            if hasattr(document, 'metadata') and document.metadata:
                is_sbml = (document.metadata.get('source') == 'sbml_import' or 
                          document.metadata.get('data_source') == 'sbml_import')
            
            if is_sbml:
                self.status_label.set_text("SBML model loaded")
                
                # CRITICAL: Load PathwayData from metadata if available
                self._load_pathway_data_from_metadata(document)
                self.logger.debug(f"Metadata inspector refreshed for SBML document: {document.metadata.get('original_file', 'unknown')}")
            else:
                self.status_label.set_markup(
                    '<span size="small">Not an SBML model</span>'
                )
                # Clear metadata tree for non-SBML models
                self.metadata_store.clear()
                buffer = self.preview_text.get_buffer()
                buffer.set_text("No SBML model loaded.\n\nImport an SBML model to see metadata.")
        else:
            # No document - disable buttons
            self.status_label.set_markup(
                '<span size="small">No model loaded</span>'
            )
            # Clear metadata tree
            self.metadata_store.clear()
            buffer = self.preview_text.get_buffer()
            buffer.set_text("No model loaded.")
    
    def _load_pathway_data_from_metadata(self, document):
        """Load and display PathwayData from document metadata.
        
        When an SBML model is loaded from disk, restore the pathway data
        that was saved during import to populate the metadata inspector.
        
        Args:
            document: DocumentModel with metadata containing sbml_pathway_data
        """
        if not hasattr(document, 'metadata') or not document.metadata:
            return
        
        pathway_dict = document.metadata.get('sbml_pathway_data')
        if not pathway_dict:
            return
        
        self.logger.info("Loading PathwayData from metadata for SBML Metadata Inspector")
        
        try:
            # Reconstruct a minimal PathwayData-like object for the inspector
            # We don't need full species/reactions lists, just summary info
            class PathwayDataStub:
                """Minimal PathwayData-compatible stub reconstructed from serialized metadata."""

                def __init__(self, data_dict):
                    self.name = data_dict.get('name', 'Unnamed')
                    self.organism = data_dict.get('organism', 'Unknown')
                    self.parameters = data_dict.get('parameters', {})
                    self.constants = set(data_dict.get('constants', []))
                    self.metadata = data_dict.get('metadata', {})
                    
                    # Reconstruct compartments
                    self.compartments_enhanced = {}
                    comps_dict = data_dict.get('compartments_enhanced', {})
                    for comp_id, comp_data in comps_dict.items():
                        comp_stub = type('Compartment', (), {})()
                        comp_stub.id = comp_data.get('id', comp_id)
                        comp_stub.name = comp_data.get('name', comp_id)
                        comp_stub.size = comp_data.get('size', 1.0)
                        self.compartments_enhanced[comp_id] = comp_stub
                    
                    # Empty lists for species/reactions/events (we only have counts)
                    self.species = []
                    self.reactions = []
                    self.events = []
                    
                    # Add counts to metadata
                    self.species_count = data_dict.get('species_count', 0)
                    self.reactions_count = data_dict.get('reactions_count', 0)
                    self.events_count = data_dict.get('events_count', 0)
            
            pathway_stub = PathwayDataStub(pathway_dict)
            
            # Update the metadata tree view
            self._update_metadata_tree_from_stub(pathway_stub)
            
            # Update preview text
            preview_lines = [
                f"=== MODEL INFO ===",
                f"Name: {pathway_stub.name}",
                f"Organism: {pathway_stub.organism}",
                f"",
                f"=== STATISTICS ===",
                f"Species: {pathway_stub.species_count}",
                f"Reactions: {pathway_stub.reactions_count}",
                f"Parameters: {len(pathway_stub.parameters)}",
                f"Compartments: {len(pathway_stub.compartments_enhanced)}",
                f"Events: {pathway_stub.events_count}",
                f"",
                f"=== SOURCE ===",
                f"Type: SBML Import",
                f"Original File: {document.metadata.get('original_file', 'Unknown')}",
            ]
            
            def update_preview():
                buffer = self.preview_text.get_buffer()
                buffer.set_text("\n".join(preview_lines))
                return False
            
            from gi.repository import GLib
            GLib.idle_add(update_preview)
            
            self.logger.info(f"✅ SBML Metadata Inspector populated from saved data")
            
        except Exception as e:
            self.logger.error(f"Failed to load PathwayData from metadata: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_metadata_tree_from_stub(self, pathway_stub):
        """Update metadata tree with limited PathwayData from disk.
        
        Similar to _update_metadata_tree but works with stub data from metadata.
        
        Args:
            pathway_stub: PathwayDataStub with limited data
        """
        def do_update():
            try:
                self.metadata_store.clear()
                
                # Global Constants section
                constants_dict = {k: v for k, v in pathway_stub.parameters.items() 
                                 if k in pathway_stub.constants}
                if constants_dict:
                    constants_root = self.metadata_store.append(None, [
                        "🔒", "Global Constants", f"{len(constants_dict)} items",
                        "section", "", "Read-only global parameters"
                    ])
                    for param_id, param_value in constants_dict.items():
                        self.metadata_store.append(constants_root, [
                            "🔒", param_id, str(param_value), "constant",
                            param_id, f"Constant: {param_id} = {param_value} (read-only)"
                        ])
                
                # Global Variables section
                variables_dict = {k: v for k, v in pathway_stub.parameters.items() 
                                 if k not in pathway_stub.constants}
                if variables_dict:
                    variables_root = self.metadata_store.append(None, [
                        "📊", "Global Variables", f"{len(variables_dict)} items",
                        "section", "", "Editable global parameters"
                    ])
                    for param_id, param_value in variables_dict.items():
                        self.metadata_store.append(variables_root, [
                            "🌐", param_id, str(param_value), "parameter",
                            param_id, f"Variable: {param_id} = {param_value}"
                        ])
                
                # Compartments section
                comps = pathway_stub.compartments_enhanced
                comps_root = self.metadata_store.append(None, [
                    "🔷", "Compartments", f"{len(comps)} items",
                    "section", "", "Cellular compartments with volumes"
                ])
                for comp_id, comp in comps.items():
                    self.metadata_store.append(comps_root, [
                        "🔷", comp.name, f"{comp.size} L",
                        "compartment", comp_id,
                        f"Compartment: {comp.name}, Volume: {comp.size} L"
                    ])
                
                # Species section (counts only, no detail)
                species_root = self.metadata_store.append(None, [
                    "🔵", "Species", f"{pathway_stub.species_count} items",
                    "section", "", "Metabolites and compounds (summary only - see Report Panel for details)"
                ])
                self.metadata_store.append(species_root, [
                    "", "(Data not available - file was loaded from disk)", "", "", "", 
                    "Full species details only available during import. See Report Panel → Models category."
                ])
                
                # Reactions section (counts only, no detail)
                reactions_root = self.metadata_store.append(None, [
                    "🔶", "Reactions", f"{pathway_stub.reactions_count} items",
                    "section", "", "Biochemical reactions (summary only - see Report Panel for details)"
                ])
                self.metadata_store.append(reactions_root, [
                    "", "(Data not available - file was loaded from disk)", "", "", "",
                    "Full reaction details only available during import. See Report Panel → Models category."
                ])
                
                # Events section (counts only, no detail)
                events_root = self.metadata_store.append(None, [
                    "⚡", "Events", f"{pathway_stub.events_count} items",
                    "section", "", "Time/state-triggered perturbations"
                ])
                if pathway_stub.events_count == 0:
                    self.metadata_store.append(events_root, [
                        "", "No events", "", "", "", ""
                    ])
                else:
                    self.metadata_store.append(events_root, [
                        "", "(Data not available - file was loaded from disk)", "", "", "",
                        "Event details only available during import."
                    ])
                
            except Exception as e:
                self.logger.error(f"Error updating metadata tree from stub: {e}")
                import traceback
                traceback.print_exc()
            
            return False  # Don't repeat
        
        from gi.repository import GLib
        GLib.idle_add(do_update)
    
    def _show_stochastic_warning_dialog(self, warnings):
        """Show dialog warning about stochastic incompatibility with user choices.
        
        Args:
            warnings: List of validation issues related to stochastic simulation
            
        Returns:
            str: User choice - 'convert_continuous', 'convert_hybrid', 'proceed_anyway', or 'cancel'
        """
        # Build message
        message = "⚠️  STOCHASTIC SIMULATION WARNING\n\n"
        message += "This SBML model contains features that may require attention:\n\n"
        
        has_assignment_rules = False
        has_reversible_formulas = False
        
        for warning in warnings:
            category = warning.get('category', 'Unknown')
            if category == 'assignment_rules':
                has_assignment_rules = True
                message += (
                    "• Assignment Rules detected\n"
                    "  May cause stale values and extreme propensities\n\n"
                )
            elif category == 'reversible_formulas':
                has_reversible_formulas = True
                message += (
                    "• Reversible reaction formulas detected\n"
                    "  ✅ Fully supported via Skellam distribution (τ-leaping)\n\n"
                )
        
        message += "\nRECOMMENDED ACTIONS:\n"
        if has_assignment_rules:
            message += "⚠️  Assignment Rules detected:\n"
            message += "   ✓ OPTION 1: CONTINUOUS mode (evaluates formulas at each step)\n"
            message += "   ✓ OPTION 2: HYBRID mode (continuous only for affected reactions)\n"
            message += "   ✓ OPTION 3: STOCHASTIC with runtime re-evaluation (~7% overhead)\n"
            message += "   ✗ STOCHASTIC without re-evaluation may fail with extreme propensities\n"
        if has_reversible_formulas and not has_assignment_rules:
            message += "✅ Reversible reactions are fully supported in stochastic mode\n"
            message += "   (Skellam distribution handles net forward/reverse flux)\n"
        message += "\nWhat would you like to do?"
        
        # Create dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            modal=True,
            message_type=Gtk.MessageType.WARNING if has_assignment_rules else Gtk.MessageType.INFO,
            text="Stochastic Simulation Compatibility" if has_assignment_rules else "Reversible Reactions Detected"
        )
        dialog.format_secondary_text(message)
        
        # Add buttons (right to left order)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        
        if has_assignment_rules:
            # Assignment rules detected - offer all 3 options
            dialog.add_button("Proceed Anyway (Stochastic)", Gtk.ResponseType.NO)
            dialog.add_button("Option 3: Stochastic + Re-eval", Gtk.ResponseType.OK)
            dialog.add_button("Option 2: Hybrid Mode", Gtk.ResponseType.APPLY)
            dialog.add_button("Option 1: Convert to Continuous", Gtk.ResponseType.YES)
            dialog.set_default_response(Gtk.ResponseType.YES)
        else:
            # Only reversible formulas - stochastic is safe with Skellam
            dialog.add_button("Convert to Continuous", Gtk.ResponseType.YES)
            dialog.add_button("Use Hybrid Mode", Gtk.ResponseType.APPLY)
            dialog.add_button("Continue with Stochastic", Gtk.ResponseType.NO)
            dialog.set_default_response(Gtk.ResponseType.NO)
        
        # Show dialog and get response
        response = dialog.run()
        dialog.destroy()
        
        # Map response to choice
        if response == Gtk.ResponseType.YES:
            return 'convert_continuous'
        elif response == Gtk.ResponseType.APPLY:
            return 'convert_hybrid'
        elif response == Gtk.ResponseType.OK:
            return 'stochastic_with_reevaluation'
        elif response == Gtk.ResponseType.NO:
            return 'proceed_anyway'
        else:
            return 'cancel'
