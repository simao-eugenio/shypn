#!/usr/bin/env python3
"""Thermodynamic Validation category for Report Panel.

Displays thermodynamic consistency validation results for reversible reactions.
Shows violations, warnings, and statistics from automated validation during SBML import.

Refactored to use table-based layout for better data presentation and organization.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

from .base_category import BaseReportCategory


class ThermodynamicValidationCategory(BaseReportCategory):
    """Thermodynamic Validation report category.
    
    Displays validation results for reversible reactions:
    - Status indicator (✓/⚠️/❌/ℹ️)
    - Summary statistics (total, valid, warnings, violations)
    - Detailed lists of violations and warnings
    - Missing data notifications
    
    Data source: SimulationController.thermodynamic_results
    """
    
    def __init__(self, project=None, model_canvas=None, pathway_operations_panel=None):
        """Initialize thermodynamic validation category.
        
        Args:
            project: Project instance
            model_canvas: ModelCanvas instance
            pathway_operations_panel: PathwayOperationsPanel for quick access (Phase 4)
        """
        self.controller = None  # Set before super() since refresh() is called during init
        self.pathway_operations_panel = pathway_operations_panel  # Phase 4: Quick access
        
        super().__init__(
            title="THERMODYNAMIC VALIDATION",
            project=project,
            model_canvas=model_canvas,
            expanded=True  # Expand by default to show important validation info
        )
    
    def _build_content(self):
        """Build thermodynamic validation content with table-based layout."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # === QUICK ACCESS BUTTON ===
        if self.pathway_operations_panel:
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            
            quick_access_btn = Gtk.Button(label="⚙️  Configure Thermodynamics")
            quick_access_btn.set_tooltip_text("Open THERMODYNAMICS category in Pathway Operations Panel")
            quick_access_btn.connect('clicked', self._on_quick_access_clicked)
            button_box.pack_start(quick_access_btn, True, True, 0)
            
            box.pack_start(button_box, False, False, 0)
        
        # === STATUS BAR ===
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self.status_label.set_markup("<b>ℹ️ Status:</b> No validation performed yet")
        box.pack_start(self.status_label, False, False, 0)
        
        # === SUMMARY STATISTICS (Compact header style) ===
        summary_frame = Gtk.Frame()
        summary_frame.set_label("Summary")
        summary_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        summary_box.set_margin_start(12)
        summary_box.set_margin_end(12)
        summary_box.set_margin_top(6)
        summary_box.set_margin_bottom(6)
        
        self.summary_label = Gtk.Label()
        self.summary_label.set_xalign(0)
        self.summary_label.set_line_wrap(True)
        self.summary_label.set_markup("<i>No reversible reactions found</i>")
        summary_box.pack_start(self.summary_label, False, False, 0)
        
        summary_frame.add(summary_box)
        box.pack_start(summary_frame, False, False, 0)
        
        # === VALIDATION RESULTS TABLE ===
        results_expander = Gtk.Expander(label="Validation Results")
        results_expander.set_expanded(True)
        
        # Create TreeView for results
        self.results_store = Gtk.ListStore(str, str, str)  # Status icon, Transition ID, Message
        self.results_tree = Gtk.TreeView(model=self.results_store)
        self.results_tree.set_enable_search(True)
        self.results_tree.set_search_column(1)  # Search by transition ID
        
        # Status column (icon)
        status_renderer = Gtk.CellRendererText()
        status_column = Gtk.TreeViewColumn("", status_renderer, text=0)
        status_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        status_column.set_fixed_width(30)
        self.results_tree.append_column(status_column)
        
        # Transition ID column
        id_renderer = Gtk.CellRendererText()
        id_renderer.set_property("weight", Pango.Weight.BOLD)
        id_column = Gtk.TreeViewColumn("Transition", id_renderer, text=1)
        id_column.set_sort_column_id(1)
        id_column.set_resizable(True)
        id_column.set_min_width(80)
        self.results_tree.append_column(id_column)
        
        # Message column
        msg_renderer = Gtk.CellRendererText()
        msg_renderer.set_property("wrap-mode", Pango.WrapMode.WORD)
        msg_renderer.set_property("wrap-width", 400)
        msg_column = Gtk.TreeViewColumn("Details", msg_renderer, text=2)
        msg_column.set_sort_column_id(2)
        msg_column.set_resizable(True)
        msg_column.set_expand(True)
        self.results_tree.append_column(msg_column)
        
        # Add scrolled window
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        results_scroll.set_min_content_height(200)
        results_scroll.set_max_content_height(400)
        results_scroll.set_propagate_natural_height(True)
        results_scroll.add(self.results_tree)
        
        results_expander.add(results_scroll)
        box.pack_start(results_expander, True, True, 0)
        
        # === COMPOUND MAPPINGS TABLE ===
        mappings_expander = Gtk.Expander(label="Compound Mappings")
        mappings_expander.set_expanded(False)
        
        # Create TreeView for mappings (matching Pathway Operations columns)
        self.mappings_store = Gtk.ListStore(str, str, str)  # Place Label, Compound ID, Confidence
        self.mappings_tree = Gtk.TreeView(model=self.mappings_store)
        self.mappings_tree.set_enable_search(True)
        self.mappings_tree.set_search_column(0)  # Search by place label
        
        # Place column (label only, matching Pathway Operations)
        place_renderer = Gtk.CellRendererText()
        place_column = Gtk.TreeViewColumn("Place", place_renderer, text=0)
        place_column.set_sort_column_id(0)
        place_column.set_resizable(True)
        place_column.set_min_width(120)
        self.mappings_tree.append_column(place_column)
        
        # Compound ID column
        compound_renderer = Gtk.CellRendererText()
        compound_column = Gtk.TreeViewColumn("Compound ID", compound_renderer, text=1)
        compound_column.set_sort_column_id(1)
        compound_column.set_resizable(True)
        compound_column.set_expand(True)
        self.mappings_tree.append_column(compound_column)
        
        # Confidence column
        confidence_renderer = Gtk.CellRendererText()
        confidence_column = Gtk.TreeViewColumn("Confidence", confidence_renderer, text=2)
        confidence_column.set_sort_column_id(2)
        confidence_column.set_resizable(True)
        confidence_column.set_min_width(100)
        self.mappings_tree.append_column(confidence_column)
        
        # Add scrolled window
        mappings_scroll = Gtk.ScrolledWindow()
        mappings_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        mappings_scroll.set_min_content_height(150)
        mappings_scroll.set_max_content_height(300)
        mappings_scroll.set_propagate_natural_height(True)
        mappings_scroll.add(self.mappings_tree)
        
        mappings_expander.add(mappings_scroll)
        box.pack_start(mappings_expander, True, True, 0)
        
        # === SETTINGS SECTION ===
        settings_frame = Gtk.Frame()
        settings_frame.set_label("Settings")
        settings_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        settings_box.set_margin_start(12)
        settings_box.set_margin_end(12)
        settings_box.set_margin_top(6)
        settings_box.set_margin_bottom(6)
        
        self.settings_label = Gtk.Label()
        self.settings_label.set_xalign(0)
        self.settings_label.set_line_wrap(True)
        self.settings_label.set_text("Using default settings")
        settings_box.pack_start(self.settings_label, False, False, 0)
        
        settings_frame.add(settings_box)
        box.pack_start(settings_frame, False, False, 0)
        
        # Initial refresh
        self.refresh()
        
        return box
    
    def refresh(self):
        """Refresh thermodynamic validation data from controller."""
        
        if not self.controller:
            self._show_no_controller()
            return
        
        # Get validation results from controller
        results = self.controller.thermodynamic_results
        
        if results is None:
            # No validation performed yet
            self._show_no_validation()
            return
        
        # Update content from results
        violations_count = len(results.get('violations', []))
        warnings_count = len(results.get('warnings', []))
        valid_count = len(results.get('valid', []))
        
        self._update_summary(results)
        self._update_results_table(results)
        self._update_compound_mappings()
        self._update_settings()
    
    def _show_no_controller(self):
        """Show placeholder when no controller available."""
        self.status_label.set_markup("<b>⚠️ Status:</b> Simulation controller not available")
        self.summary_label.set_markup(
            "<i>Cannot retrieve thermodynamic validation data:\n"
            "Simulation controller not initialized for this model.</i>"
        )
        self.results_store.clear()
        self.mappings_store.clear()
    
    def _show_no_validation(self):
        """Show placeholder when validation not yet performed."""
        self.status_label.set_markup("<b>ℹ️ Status:</b> No validation performed yet")
        self.summary_label.set_markup(
            "<i>Thermodynamic validation runs automatically during SBML import.\n\n"
            "• Import an SBML file with reversible reactions, or\n"
            "• Run validation manually from Pathway Operations panel</i>"
        )
        self.results_store.clear()
        self._update_compound_mappings()
        self._update_settings()
    
    def _update_status(self, results):
        """Update status bar based on results."""
        summary = results.get('summary', {})
        total = summary.get('total', 0)
        violations = summary.get('violations', 0)
        warnings = summary.get('warnings', 0)
        valid = summary.get('valid', 0)
        
        if total == 0:
            status = "<b>ℹ️ Status:</b> No reversible reactions found"
        elif violations > 0:
            status = f"<b>❌ Status:</b> {violations} violation(s) detected"
        elif warnings > 0:
            status = f"<b>⚠️  Status:</b> {warnings} warning(s) - review recommended"
        elif valid == total:
            status = f"<b>✓ Status:</b> All {total} reversible reaction(s) valid"
        else:
            status = f"<b>ℹ️ Status:</b> {total} reversible reaction(s) checked"
        
        self.status_label.set_markup(status)
    
    def _update_summary(self, results):
        """Update summary statistics."""
        summary = results.get('summary', {})
        
        lines = [
            f"Total reversible reactions: {summary.get('total', 0)}",
            f"  ✓ Valid: {summary.get('valid', 0)}",
            f"  ⚠️  Warnings: {summary.get('warnings', 0)}",
            f"  ❌ Violations: {summary.get('violations', 0)}",
        ]
        
        self.summary_label.set_markup('\n'.join(lines))
    
    def _update_results_table(self, results):
        """Update results table with all validation data."""
        self.results_store.clear()
        
        # Add violations (red icon)
        for v in results.get('violations', []):
            transition = v.get('transition', 'Unknown')
            message = v.get('message', '')
            self.results_store.append(["❌", transition, message])
        
        # Add warnings (orange icon)
        for w in results.get('warnings', []):
            transition = w.get('transition', 'Unknown')
            message = w.get('message', '')
            self.results_store.append(["⚠️", transition, message])
        
        # Add valid (green icon)
        for v in results.get('valid', []):
            transition = v.get('transition', 'Unknown')
            message = v.get('message', 'Valid thermodynamic consistency')
            self.results_store.append(["✓", transition, message])
        
        # Add insufficient data (info icon)
        for i in results.get('insufficient_data', []):
            transition = i.get('transition', 'Unknown')
            message = i.get('message', 'Insufficient data for validation')
            self.results_store.append(["ℹ️", transition, message])
    
    
    def set_controller(self, controller):
        """Set simulation controller reference.
        
        Args:
            controller: SimulationController instance
        """
        self.controller = controller
        self.refresh()
    
    def _update_compound_mappings(self):
        """Update compound mappings table (matching Pathway Operations format)."""
        self.mappings_store.clear()
        
        # Get compound mappings from controller results
        if not self.controller or not self.controller.thermodynamic_results:
            return
        
        mappings = self.controller.thermodynamic_results.get('compound_mappings', {})
        
        if not mappings:
            return
        
        # Get current active model to look up place names
        document = self.get_current_model()
        
        # Populate table with all mappings (columns: Place, Compound ID, Confidence)
        for place_id, compound_id in mappings.items():
            # Get place name if document is available
            name = place_id  # Default to place_id
            if document:
                place = next((p for p in document.places if p.id == place_id), None)
                if place:
                    name = place.name if hasattr(place, 'name') and place.name else place_id
            
            # Show "Manual" confidence since these are pre-existing mappings from validation
            confidence = "Manual"
            
            self.mappings_store.append([name, compound_id, confidence])
    
    def _update_settings(self):
        """Update settings display (Phase 4)."""
        # Get current active model dynamically
        document = self.get_current_model()
        if not document:
            self.settings_label.set_text("No model loaded")
            return
        if not hasattr(document, 'thermodynamic_settings'):
            self.settings_label.set_text("Using default settings")
            return
        
        settings = document.thermodynamic_settings
        ph = settings.get('ph', 7.0)
        temp_k = settings.get('temperature', 298.15)
        temp_c = temp_k - 273.15
        ionic = settings.get('ionic_strength', 0.1)
        tolerance = settings.get('tolerance', 0.5)
        preset = settings.get('preset', 'custom')
        
        lines = [
            f"Preset: {preset.capitalize()}",
            f"pH: {ph:.1f}",
            f"Temperature: {temp_k:.1f} K ({temp_c:.1f}°C)",
            f"Ionic Strength: {ionic:.2f} M",
            f"Tolerance: {tolerance:.0%}"
        ]
        
        self.settings_label.set_text('\n'.join(lines))
    
    def _on_quick_access_clicked(self, button):
        """Handle quick access button click (Phase 4)."""
        if not self.pathway_operations_panel:
            return
        
        # Switch to THERMODYNAMICS category
        # The pathway_operations_panel should have a method to switch categories
        if hasattr(self.pathway_operations_panel, 'set_active_category'):
            self.pathway_operations_panel.set_active_category('THERMODYNAMICS')
        elif hasattr(self.pathway_operations_panel, 'show_category'):
            self.pathway_operations_panel.show_category('THERMODYNAMICS')
    
    def get_widget(self):
        """Get the widget for this category.
        
        Returns:
            CategoryFrame widget
        """
        return self.category_frame
