#!/usr/bin/env python3
"""Results Browser View - Display and analyze experiment results.

Shows completed experiments with statistics, visualizations, and export options.
Integrates with BatchExecutor for retrieving results.

REFACTORED: Now inherits from BaseResultsView (OOP architecture compliance).

Author: Simão Eugénio
Date: January 22, 2026 (Refactored to BaseResultsView)
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os
import matplotlib
matplotlib.use('GTK3Agg')
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3
from matplotlib.figure import Figure
from .base_results_view import BaseResultsView
from .gtk_widgets import SearchableComboBox
from shypn.data.project_models import get_project_manager


class ResultsBrowserView(BaseResultsView):
    """Widget for browsing and analyzing experiment results.
    
    Inherits from BaseResultsView to provide:
    - TreeView listing completed experiments
    - Statistics display (mean, stddev, confidence intervals)
    - Export to CSV/JSON (single and batch)
    - Embedded matplotlib plotting
    - Integration with Report panel
    
    Features:
    - Multi-select checkboxes for batch export (click header to toggle all)
    - Notebook with Results List and Plot View tabs
    """
    
    def __init__(self, model=None):
        """Initialize results browser view.
        
        Args:
            model: Optional model reference for resolving IDs to names
        """
        # Matplotlib components for embedded plotting
        self.figure = None
        self.canvas = None
        self.toolbar = None
        
        # TreeView components (initialized in setup_ui)
        self.results_store = None
        self.results_tree = None
        self.notebook = None
        
        # Status label
        self.status_label = None
        
        # Call parent constructor (which calls setup_ui)
        super().__init__(model)
    
    
    def setup_ui(self):
        """Build results browser UI with notebook for list/plot views.
        
        Implements abstract method from BaseResultsView.
        Creates TreeView with multi-select checkboxes and matplotlib plot view.
        """
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Experiment Results</b>")
        title_label.set_xalign(0)
        self.pack_start(title_label, False, False, 0)
        
        # Create notebook with two pages: Results List and Plot View
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(True)
        
        # === PAGE 1: Results List ===
        list_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Results TreeView in ScrolledWindow
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 150)
        
        # Create ListStore: selected (bool), name, replicates, duration, status, error_msg
        # Columns: 0=selected (bool), 1=name (str), 2=n_replicates (int), 3=duration (str), 4=status (str), 5=error_msg (str)
        self.results_store = Gtk.ListStore(bool, str, int, str, str, str)
        
        # Create TreeView with sortable columns
        self.results_tree = Gtk.TreeView(model=self.results_store)
        self.results_tree.set_headers_visible(True)
        self.results_tree.set_headers_clickable(True)  # Enable column header clicking for sorting
        
        # Column 0: Checkbox for multi-selection (clickable header for select/deselect all)
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.set_activatable(True)
        renderer_toggle.connect("toggled", self._on_row_toggled)
        column_select = Gtk.TreeViewColumn("☐", renderer_toggle, active=0)
        column_select.set_min_width(40)
        column_select.set_resizable(True)
        column_select.set_clickable(True)
        column_select.connect("clicked", self._on_checkbox_header_clicked)
        self.results_tree.append_column(column_select)
        self.checkbox_column = column_select
        self._all_selected = False
        
        # Column 1: Experiment Name (sortable)
        renderer_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Experiment", renderer_name, text=1)
        column_name.set_expand(True)
        column_name.set_sort_column_id(1)  # Sort by column 1 (name)
        column_name.set_resizable(True)
        self.results_tree.append_column(column_name)
        
        # Column 2: Replicates (sortable)
        renderer_reps = Gtk.CellRendererText()
        column_reps = Gtk.TreeViewColumn("Replicates", renderer_reps, text=2)
        column_reps.set_min_width(80)
        column_reps.set_sort_column_id(2)  # Sort by column 2 (replicates)
        column_reps.set_resizable(True)
        self.results_tree.append_column(column_reps)
        
        # Column 3: Elapsed time per replicate (sortable)
        renderer_dur = Gtk.CellRendererText()
        column_dur = Gtk.TreeViewColumn("Elapsed", renderer_dur, text=3)
        column_dur.set_min_width(80)
        column_dur.set_sort_column_id(3)  # Sort by column 3 (elapsed time)
        column_dur.set_resizable(True)
        self.results_tree.append_column(column_dur)
        
        # Column 4: Status (sortable, with error tooltip)
        renderer_status = Gtk.CellRendererText()
        column_status = Gtk.TreeViewColumn("Status", renderer_status, text=4)
        column_status.set_min_width(80)
        column_status.set_sort_column_id(4)  # Sort by column 4 (status)
        column_status.set_resizable(True)
        self.results_tree.append_column(column_status)
        self.results_tree.set_tooltip_column(5)  # Column 5 = error message
        
        # Connect selection changed
        selection = self.results_tree.get_selection()
        selection.connect("changed", self._on_selection_changed)
        
        scrolled.add(self.results_tree)
        list_page.pack_start(scrolled, True, True, 0)
        
        # Statistics display
        stats_frame = Gtk.Frame()
        stats_frame.set_label("Statistics")
        
        self.stats_label = Gtk.Label()
        self.stats_label.set_markup("<i>Select an experiment to view statistics</i>")
        self.stats_label.set_xalign(0)
        self.stats_label.set_yalign(0)
        self.stats_label.set_margin_start(12)
        self.stats_label.set_margin_end(12)
        self.stats_label.set_margin_top(6)
        self.stats_label.set_margin_bottom(6)
        
        stats_frame.add(self.stats_label)
        list_page.pack_start(stats_frame, False, False, 0)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Export CSV button (single or batch)
        self.export_csv_button = Gtk.Button(label="Export CSV")
        self.export_csv_button.set_tooltip_text("Export selected result(s) to CSV (batch if multiple checked)")
        self.export_csv_button.set_sensitive(False)
        self.export_csv_button.connect("clicked", self._on_export_csv_clicked)
        button_box.pack_start(self.export_csv_button, False, False, 0)
        
        # Export JSON button (single or batch)
        self.export_json_button = Gtk.Button(label="Export JSON")
        self.export_json_button.set_tooltip_text("Export selected result(s) to JSON (batch if multiple checked)")
        self.export_json_button.set_sensitive(False)
        self.export_json_button.connect("clicked", self._on_export_json_clicked)
        button_box.pack_start(self.export_json_button, False, False, 0)
        
        # Statistical Tests button (E5 enhancement)
        self.stats_test_button = Gtk.Button(label="📈 Statistical Tests")
        self.stats_test_button.set_tooltip_text("Run ANOVA and post-hoc tests on selected experiments")
        self.stats_test_button.set_sensitive(False)
        self.stats_test_button.connect("clicked", self._on_statistical_tests_clicked)
        button_box.pack_start(self.stats_test_button, False, False, 0)
        
        # Compare Selected button (E6 enhancement)
        self.compare_button = Gtk.Button(label="📊 Compare Selected")
        self.compare_button.set_tooltip_text("Overlay trajectories of checked experiments")
        self.compare_button.set_sensitive(False)
        self.compare_button.connect("clicked", self._on_compare_selected_clicked)
        button_box.pack_start(self.compare_button, False, False, 0)
        
        # Sensitivity Analysis button (E7 enhancement)
        self.sensitivity_button = Gtk.Button(label="🎯 Sensitivity (PRCC)")
        self.sensitivity_button.set_tooltip_text("Compute PRCC from LHS parameter sweep results")
        self.sensitivity_button.set_sensitive(False)
        self.sensitivity_button.connect("clicked", self._on_sensitivity_analysis_clicked)
        button_box.pack_start(self.sensitivity_button, False, False, 0)
        
        # Add to Report button
        self.report_button = Gtk.Button(label="Add to Report")
        self.report_button.set_tooltip_text("Add selected results to Report panel")
        self.report_button.set_sensitive(False)
        self.report_button.connect("clicked", self._on_report_clicked)
        button_box.pack_start(self.report_button, False, False, 0)
        
        # Clear All button
        clear_button = Gtk.Button(label="Clear All")
        clear_button.set_tooltip_text("Clear all results")
        clear_button.connect("clicked", self._on_clear_clicked)
        button_box.pack_start(clear_button, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>No results</i>")
        self.status_label.set_xalign(1)
        self.status_label.set_hexpand(True)
        button_box.pack_start(self.status_label, True, True, 0)
        
        list_page.pack_start(button_box, False, False, 0)
        
        # === PAGE 2: Plot View ===
        plot_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Plot mode controls (E4 enhancement)
        plot_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        plot_controls.set_margin_start(12)
        plot_controls.set_margin_end(12)
        plot_controls.set_margin_top(8)
        plot_controls.set_margin_bottom(8)
        
        # Plot mode selector
        mode_label = Gtk.Label(label="Plot Mode:")
        mode_label.set_margin_end(6)
        plot_controls.pack_start(mode_label, False, False, 0)
        
        self.plot_mode_combo = Gtk.ComboBoxText()
        self.plot_mode_combo.append("trajectory", "Trajectory Plot")
        self.plot_mode_combo.append("heatmap", "Heatmap (2D Factorial)")
        self.plot_mode_combo.set_active(0)
        self.plot_mode_combo.set_tooltip_text("Select visualization mode")
        self.plot_mode_combo.set_margin_end(18)
        plot_controls.pack_start(self.plot_mode_combo, False, False, 0)
        
        # Response metric selector (for heatmap)
        response_label = Gtk.Label(label="Response Metric:")
        response_label.set_margin_end(6)
        plot_controls.pack_start(response_label, False, False, 0)
        
        self.heatmap_response_combo = Gtk.ComboBoxText()
        self.heatmap_response_combo.append("deadlock_rate", "Deadlock Rate (%)")
        self.heatmap_response_combo.append("viable_rate", "Viability Rate (%)")
        self.heatmap_response_combo.append("mean_tokens", "Mean Token Count")
        self.heatmap_response_combo.set_active(0)
        self.heatmap_response_combo.set_tooltip_text("Metric to display in heatmap")
        self.heatmap_response_combo.set_margin_end(18)
        plot_controls.pack_start(self.heatmap_response_combo, False, False, 0)
        
        # Generate button
        generate_plot_button = Gtk.Button(label="📊 Generate Plot")
        generate_plot_button.connect("clicked", self._on_generate_plot_clicked)
        generate_plot_button.set_tooltip_text("Generate selected plot type from all results")
        plot_controls.pack_start(generate_plot_button, False, False, 0)
        
        plot_page.pack_start(plot_controls, False, False, 0)
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        # Wrap canvas in a layout to manage size properly
        canvas_layout = Gtk.Layout()
        canvas_layout.put(self.canvas, 0, 0)
        
        # Wrap layout in scrolled window to handle large plots
        scrolled_plot = Gtk.ScrolledWindow()
        scrolled_plot.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_plot.set_hexpand(True)
        scrolled_plot.set_vexpand(True)
        scrolled_plot.add(canvas_layout)
        
        # Navigation toolbar
        self.toolbar = NavigationToolbar2GTK3(self.canvas)
        plot_page.pack_start(self.toolbar, False, False, 0)
        plot_page.pack_start(scrolled_plot, True, True, 0)
        
        # Connect to canvas draw event to update size
        self.canvas.mpl_connect('draw_event', self._on_canvas_draw)
        
        # Store layout reference for size updates
        self.canvas_layout = canvas_layout
        
        # Add pages to notebook
        self.notebook.append_page(list_page, Gtk.Label(label="Results List"))
        self.notebook.append_page(plot_page, Gtk.Label(label="Plot View"))
        
        # === PAGE 3: Dose-Response Analysis (E3 enhancement) ===
        dr_page = self._build_dose_response_page()
        self.notebook.append_page(dr_page, Gtk.Label(label="Dose-Response"))
        
        # === PAGE 4: Metadata View ===
        metadata_page = self._build_metadata_page()
        self.notebook.append_page(metadata_page, Gtk.Label(label="Metadata"))
        
        self.pack_start(self.notebook, True, True, 0)
    
    def _show_error(self, message):
        """Display error message dialog.
        
        Args:
            message: Error message to display
        """
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _on_canvas_draw(self, event):
        """Update canvas size request when figure is drawn.
        
        This ensures the scrolled window knows the actual size of the plot,
        enabling proper scrolling behavior.
        
        Args:
            event: Matplotlib draw event
        """
        if not self.figure:
            return
        
        # Get figure size in pixels
        width_inches, height_inches = self.figure.get_size_inches()
        dpi = self.figure.get_dpi()
        
        width_px = int(width_inches * dpi)
        height_px = int(height_inches * dpi)
        
        # Update canvas size request to match figure size
        self.canvas.set_size_request(width_px, height_px)
        
        # Update the layout size to accommodate the canvas
        if hasattr(self, 'canvas_layout'):
            self.canvas_layout.set_size(width_px, height_px)
    
    def _build_dose_response_page(self):
        """Build dose-response analysis page (E3 enhancement).
        
        Returns:
            Gtk.Box: Page widget with dose-response fitting UI
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>Dose-Response Analysis</b>\n"
            "Select experiments with varying dose parameter (e.g., ATP concentration sweep).\n"
            "Fits 4-parameter logistic (Hill equation) to calculate IC50/EC50."
        )
        instructions.set_xalign(0)
        instructions.set_margin_start(6)
        instructions.set_margin_end(6)
        instructions.set_margin_top(6)
        page.pack_start(instructions, False, False, 0)
        
        # Parameter selection
        param_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        param_box.set_margin_start(12)
        param_box.set_margin_end(12)
        param_box.set_margin_top(8)
        param_box.set_margin_bottom(8)
        
        param_label = Gtk.Label(label="Dose Parameter:")
        param_label.set_margin_end(6)
        param_box.pack_start(param_label, False, False, 0)
        
        # Combo to select which parameter is the "dose" (auto-detect from sweep)
        self.dr_param_combo = SearchableComboBox(
            tooltip_text="Select which parameter represents the dose/concentration"
        )
        self.dr_param_combo.set_margin_end(18)
        param_box.pack_start(self.dr_param_combo, False, False, 0)
        
        # Response metric selection
        response_label = Gtk.Label(label="Response Metric:")
        response_label.set_margin_end(6)
        param_box.pack_start(response_label, False, False, 0)
        
        self.dr_response_combo = Gtk.ComboBoxText()
        self.dr_response_combo.append("deadlock_rate", "Deadlock Rate (%)")
        self.dr_response_combo.append("viable_rate", "Viability Rate (%)")
        self.dr_response_combo.append("mean_tokens", "Mean Token Count")
        self.dr_response_combo.set_active(0)
        self.dr_response_combo.set_tooltip_text("Select response metric to analyze")
        self.dr_response_combo.set_margin_end(18)
        param_box.pack_start(self.dr_response_combo, False, False, 0)
        
        # Analyze button
        analyze_button = Gtk.Button(label="📈 Analyze Dose-Response")
        analyze_button.connect("clicked", self._on_analyze_dose_response)
        param_box.pack_start(analyze_button, False, False, 0)
        
        page.pack_start(param_box, False, False, 0)
        
        # Results display area (figure + statistics)
        results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Matplotlib figure for dose-response curve
        self.dr_figure = Figure(figsize=(8, 5), dpi=80)
        self.dr_canvas = FigureCanvas(self.dr_figure)
        self.dr_canvas.set_size_request(600, 350)
        
        # Navigation toolbar
        self.dr_toolbar = NavigationToolbar2GTK3(self.dr_canvas)
        results_box.pack_start(self.dr_toolbar, False, False, 0)
        results_box.pack_start(self.dr_canvas, True, True, 0)
        
        # Statistics frame
        stats_frame = Gtk.Frame()
        stats_frame.set_label("Fit Parameters")
        stats_frame.set_margin_start(6)
        stats_frame.set_margin_end(6)
        stats_frame.set_margin_bottom(6)
        
        self.dr_stats_label = Gtk.Label()
        self.dr_stats_label.set_markup("<i>No analysis performed yet</i>")
        self.dr_stats_label.set_xalign(0)
        self.dr_stats_label.set_margin_start(12)
        self.dr_stats_label.set_margin_end(12)
        self.dr_stats_label.set_margin_top(6)
        self.dr_stats_label.set_margin_bottom(6)
        
        stats_frame.add(self.dr_stats_label)
        results_box.pack_start(stats_frame, False, False, 0)
        
        page.pack_start(results_box, True, True, 0)
        
        return page
    
    def _build_metadata_page(self):
        """Build metadata view page.
        
        Returns:
            Gtk.Box: Page widget displaying metadata fields in a tree view
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Title and instructions
        title = Gtk.Label()
        title.set_markup(
            "<b>Experiment Metadata</b>\n"
            "Complete provenance and parametrization information for the selected experiment."
        )
        title.set_xalign(0)
        title.set_margin_start(6)
        title.set_margin_end(6)
        title.set_margin_top(6)
        page.pack_start(title, False, False, 0)
        
        # TreeView for metadata display
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_margin_start(6)
        scrolled.set_margin_end(6)
        scrolled.set_margin_bottom(6)
        
        # Create TreeStore: section (str), field (str), value (str)
        self.metadata_store = Gtk.TreeStore(str, str, str)
        
        # Create TreeView
        self.metadata_tree = Gtk.TreeView(model=self.metadata_store)
        self.metadata_tree.set_headers_visible(True)
        
        # Column 0: Section
        renderer_section = Gtk.CellRendererText()
        renderer_section.set_property("weight", 700)  # Bold
        column_section = Gtk.TreeViewColumn("Section", renderer_section, text=0)
        column_section.set_resizable(True)
        column_section.set_min_width(200)
        self.metadata_tree.append_column(column_section)
        
        # Column 1: Field
        renderer_field = Gtk.CellRendererText()
        column_field = Gtk.TreeViewColumn("Field", renderer_field, text=1)
        column_field.set_resizable(True)
        column_field.set_min_width(200)
        self.metadata_tree.append_column(column_field)
        
        # Column 2: Value
        renderer_value = Gtk.CellRendererText()
        column_value = Gtk.TreeViewColumn("Value", renderer_value, text=2)
        column_value.set_resizable(True)
        column_value.set_min_width(300)
        self.metadata_tree.append_column(column_value)
        
        scrolled.add(self.metadata_tree)
        page.pack_start(scrolled, True, True, 0)
        
        # Status label
        self.metadata_status_label = Gtk.Label()
        self.metadata_status_label.set_markup("<i>Select an experiment to view metadata</i>")
        self.metadata_status_label.set_xalign(0)
        self.metadata_status_label.set_margin_start(12)
        self.metadata_status_label.set_margin_end(12)
        self.metadata_status_label.set_margin_bottom(6)
        page.pack_start(self.metadata_status_label, False, False, 0)
        
        return page
    
    def _on_analyze_dose_response(self, button):
        """Analyze dose-response relationship from sweep data (E3 enhancement).
        
        Fits 4-parameter logistic curve to dose-response data and displays
        IC50/EC50, Hill slope, and curve plot.
        """
        from .dose_response_analyzer import DoseResponseAnalyzer
        import numpy as np
        
        # Get dose parameter from combo
        dose_param_name = self.dr_param_combo.get_active_text()
        if not dose_param_name:
            self._show_error("Please select a dose parameter first")
            return
        
        # Get response metric
        response_metric = self.dr_response_combo.get_active_id()
        if not response_metric:
            response_metric = "deadlock_rate"
        
        # Collect dose-response data from all results
        doses = []
        responses = []
        
        for row in self.results_store:
            name = row[1]  # Column 1 = name
            if name not in self.results:
                continue
            
            result = self.results[name]
            
            # Extract dose value from experiment name
            # Format: "param_name=value" or "param1=val1_param2=val2_..."
            dose_value = None
            for part in name.split('_'):
                if '=' in part:
                    key, val = part.split('=', 1)
                    if key == dose_param_name:
                        try:
                            dose_value = float(val)
                            break
                        except ValueError:
                            continue
            
            if dose_value is None:
                continue
            
            # Extract response value
            stats = result.get('statistics', {})
            if response_metric == 'deadlock_rate':
                response_value = stats.get('deadlock_rate', 0.0) * 100  # Convert to %
            elif response_metric == 'viable_rate':
                response_value = (1 - stats.get('deadlock_rate', 0.0)) * 100  # Viability %
            elif response_metric == 'mean_tokens':
                species_stats = stats.get('species_statistics', {})
                # Average mean tokens across all places
                mean_token_values = [
                    sp_stats.get('mean', 0.0)
                    for sp_id, sp_stats in species_stats.items()
                    if sp_id.startswith('P')  # Places only
                ]
                response_value = np.mean(mean_token_values) if mean_token_values else 0.0
            else:
                continue
            
            doses.append(dose_value)
            responses.append(response_value)
        
        # Check if we have enough data
        if len(doses) < 4:
            self._show_error(f"Need at least 4 dose-response points for curve fitting (found {len(doses)})")
            return
        
        # Perform dose-response analysis
        try:
            analyzer = DoseResponseAnalyzer(doses, responses)
            analyzer.fit()
            
            # Generate smooth curve for plotting
            doses_smooth, responses_smooth = analyzer.generate_smooth_curve(n_points=100)
            
            # Plot dose-response curve
            self.dr_figure.clear()
            ax = self.dr_figure.add_subplot(111)
            
            # Plot data points
            ax.scatter(doses, responses, s=100, alpha=0.7, color='#2E86AB', 
                      label='Experimental Data', zorder=3)
            
            # Plot fitted curve
            ax.plot(doses_smooth, responses_smooth, '-', color='#A23B72', linewidth=2,
                   label='4PL Fit', zorder=2)
            
            # Mark IC50 with vertical line
            ic50_response = analyzer.bottom + (analyzer.top - analyzer.bottom) / 2
            ax.axvline(analyzer.ic50, color='#F18F01', linestyle='--', linewidth=1.5,
                      label=f'IC50 = {analyzer.ic50:.2e}', zorder=1)
            ax.axhline(ic50_response, color='#F18F01', linestyle=':', linewidth=1,
                      alpha=0.5, zorder=1)
            
            # Styling
            ax.set_xlabel(f'{dose_param_name} (log scale)', fontsize=11)
            ax.set_ylabel(f'{self.dr_response_combo.get_active_text()}', fontsize=11)
            ax.set_title(f'Dose-Response Curve (R² = {analyzer.r_squared:.4f})', 
                        fontsize=12, fontweight='bold')
            ax.set_xscale('log')
            ax.grid(True, alpha=0.3, linestyle=':')
            ax.legend(frameon=True, shadow=True)
            
            self.dr_canvas.draw()
            
            # Update statistics display
            summary = analyzer.get_summary()
            ic50_lower, ic50_upper = summary['ic50_ci']
            hill_lower, hill_upper = summary['hill_slope_ci']
            
            stats_text = (
                f"<b>Fit Parameters</b>\n\n"
                f"<b>IC50:</b> {summary['ic50']:.3e} (95% CI: {ic50_lower:.3e} - {ic50_upper:.3e})\n"
                f"<b>Hill Slope:</b> {summary['hill_slope']:.3f} (95% CI: {hill_lower:.3f} - {hill_upper:.3f})\n"
                f"<b>Top:</b> {summary['top']:.2f}\n"
                f"<b>Bottom:</b> {summary['bottom']:.2f}\n"
                f"<b>R²:</b> {summary['r_squared']:.4f}\n"
                f"<b>Data Points:</b> {summary['n_points']}"
            )
            self.dr_stats_label.set_markup(stats_text)
            
            # Switch to dose-response tab
            self.notebook.set_current_page(2)  # Page 2 = Dose-Response tab
            
        except Exception as e:
            self._show_error(f"Dose-response analysis failed:\n\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _on_generate_plot_clicked(self, button):
        """Generate plot based on selected mode (E4 enhancement).
        
        Handles both trajectory plots and factorial heatmaps.
        """
        plot_mode = self.plot_mode_combo.get_active_id()
        
        if plot_mode == "trajectory":
            # Use existing trajectory plot functionality
            name, result = self.get_selected_result()
            if name and result:
                self.notebook.set_current_page(1)  # Switch to plot page
                try:
                    self._plot_trajectories(name, result)
                except Exception as e:
                    self._show_error(f"Trajectory plotting failed:\n\n{str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                self._show_error("Please select an experiment from the Results List first")
        
        elif plot_mode == "heatmap":
            # Generate 2D factorial heatmap
            self._generate_heatmap()
        
        else:
            self._show_error(f"Unknown plot mode: {plot_mode}")
    
    def _generate_heatmap(self):
        """Generate 2D heatmap for factorial experiment data (E4 enhancement).
        
        Detects if results form a 2D factorial grid and creates a heatmap
        showing parameter interactions.
        """
        import numpy as np
        
        # Get response metric
        response_metric = self.heatmap_response_combo.get_active_id()
        if not response_metric:
            response_metric = "deadlock_rate"
        
        # Extract factorial data from all results
        # Format: experiment names like "param1=val1_param2=val2"
        factorial_data = []
        
        for row in self.results_store:
            name = row[1]  # Column 1 = name
            if name not in self.results:
                continue
            
            result = self.results[name]
            
            # Parse parameter values from name
            params = {}
            for part in name.split('_'):
                if '=' in part:
                    key, val = part.split('=', 1)
                    try:
                        params[key] = float(val)
                    except ValueError:
                        continue
            
            # Extract response value
            stats = result.get('statistics', {})
            if response_metric == 'deadlock_rate':
                response_value = stats.get('deadlock_rate', 0.0) * 100  # Convert to %
            elif response_metric == 'viable_rate':
                response_value = (1 - stats.get('deadlock_rate', 0.0)) * 100  # Viability %
            elif response_metric == 'mean_tokens':
                species_stats = stats.get('species_statistics', {})
                # Average mean tokens across all places
                mean_token_values = [
                    sp_stats.get('mean', 0.0)
                    for sp_id, sp_stats in species_stats.items()
                    if sp_id.startswith('P')  # Places only
                ]
                response_value = np.mean(mean_token_values) if mean_token_values else 0.0
            else:
                continue
            
            params['_response'] = response_value
            factorial_data.append(params)
        
        if len(factorial_data) < 4:
            self._show_error(f"Need at least 4 data points for heatmap (found {len(factorial_data)})")
            return
        
        # Detect parameter names (exclude _response)
        param_names = sorted(set(
            key for data in factorial_data for key in data.keys()
            if key != '_response'
        ))
        
        if len(param_names) < 2:
            self._show_error(
                f"Heatmap requires 2D factorial data (2+ parameters).\n"
                f"Found only {len(param_names)} parameter(s): {param_names}"
            )
            return
        
        # Use first two parameters for heatmap axes
        param_x = param_names[0]
        param_y = param_names[1]
        
        if len(param_names) > 2:
            # Warn user we're only plotting first 2 parameters
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="3D+ Factorial Data Detected"
            )
            dialog.format_secondary_text(
                f"Found {len(param_names)} parameters: {', '.join(param_names)}\n\n"
                f"Displaying 2D heatmap for: {param_x} × {param_y}\n"
                f"(Additional parameters averaged)"
            )
            dialog.run()
            dialog.destroy()
        
        # Extract unique values for each parameter
        x_values = sorted(set(d[param_x] for d in factorial_data if param_x in d))
        y_values = sorted(set(d[param_y] for d in factorial_data if param_y in d))
        
        # Create 2D grid
        z_matrix = np.full((len(y_values), len(x_values)), np.nan)
        
        # Fill grid with response values
        for data in factorial_data:
            if param_x not in data or param_y not in data:
                continue
            
            try:
                x_idx = x_values.index(data[param_x])
                y_idx = y_values.index(data[param_y])
                
                # If multiple values for same (x, y) coordinate, average them
                if np.isnan(z_matrix[y_idx, x_idx]):
                    z_matrix[y_idx, x_idx] = data['_response']
                else:
                    z_matrix[y_idx, x_idx] = (z_matrix[y_idx, x_idx] + data['_response']) / 2
            except ValueError:
                continue
        
        # Check if grid has enough data
        valid_points = np.sum(~np.isnan(z_matrix))
        if valid_points < 4:
            self._show_error(f"Insufficient 2D grid data (only {valid_points} valid points)")
            return
        
        # Generate heatmap
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Create pcolormesh
            # Need to create mesh grid coordinates for edges
            # Handle edge cases for arrays with < 2 elements
            if len(x_values) >= 2:
                x_edges = np.append(x_values, x_values[-1] + (x_values[-1] - x_values[-2]))
            else:
                x_edges = np.array([x_values[0] - 0.5, x_values[0] + 0.5]) if len(x_values) > 0 else np.array([0, 1])
            
            if len(y_values) >= 2:
                y_edges = np.append(y_values, y_values[-1] + (y_values[-1] - y_values[-2]))
            else:
                y_edges = np.array([y_values[0] - 0.5, y_values[0] + 0.5]) if len(y_values) > 0 else np.array([0, 1])
            
            X, Y = np.meshgrid(x_edges, y_edges)
            
            # Plot heatmap
            im = ax.pcolormesh(X, Y, z_matrix, shading='flat', cmap='RdYlGn_r')
            
            # Add colorbar
            cbar = self.figure.colorbar(im, ax=ax)
            cbar.set_label(self.heatmap_response_combo.get_active_text(), fontsize=10)
            
            # Annotate cells with values
            for i, y in enumerate(y_values):
                for j, x in enumerate(x_values):
                    value = z_matrix[i, j]
                    if not np.isnan(value):
                        text_color = 'white' if value > np.nanmedian(z_matrix) else 'black'
                        ax.text(x, y, f'{value:.1f}', 
                               ha='center', va='center',
                               color=text_color, fontsize=9, fontweight='bold')
            
            # Styling
            ax.set_xlabel(param_x, fontsize=11, fontweight='bold')
            ax.set_ylabel(param_y, fontsize=11, fontweight='bold')
            ax.set_title(f'Factorial Heatmap: {param_x} × {param_y}', 
                        fontsize=12, fontweight='bold')
            
            # Set ticks to parameter values
            ax.set_xticks(x_values)
            ax.set_yticks(y_values)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            # Switch to plot page
            self.notebook.set_current_page(1)
            
        except Exception as e:
            self._show_error(f"Heatmap generation failed:\n\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _on_statistical_tests_clicked(self, button):
        """Run statistical tests on checked experiments (E5 enhancement).
        
        Performs one-way ANOVA if 3+ groups selected, or t-test if 2 groups.
        If ANOVA is significant, runs Tukey HSD post-hoc tests.
        """
        from .statistical_comparator import StatisticalComparator, TTestComparator
        import numpy as np
        
        # Get checked experiments
        checked = self.get_checked_results()
        
        if len(checked) < 2:
            self._show_error("Please check at least 2 experiments for statistical comparison")
            return
        
        # Select response metric to compare
        metric_dialog = Gtk.Dialog(
            title="Select Response Metric",
            transient_for=self.get_toplevel(),
            flags=0
        )
        metric_dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content = metric_dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        
        label = Gtk.Label(label="Select the metric to compare across experiments:")
        label.set_xalign(0)
        content.pack_start(label, False, False, 6)
        
        metric_combo = Gtk.ComboBoxText()
        metric_combo.append("deadlock_rate", "Deadlock Rate (%)")
        metric_combo.append("viable_rate", "Viability Rate (%)")
        metric_combo.append("mean_tokens", "Mean Token Count")
        metric_combo.append("mean_duration", "Mean Simulation Duration")
        metric_combo.set_active(0)
        content.pack_start(metric_combo, False, False, 6)
        
        metric_dialog.show_all()
        response = metric_dialog.run()
        metric_id = metric_combo.get_active_id()
        metric_dialog.destroy()
        
        if response != Gtk.ResponseType.OK or not metric_id:
            return
        
        # Extract data for each experiment
        groups = {}
        
        for name, result in checked:
            stats = result.get('statistics', {})
            
            # Get metric value (use replicate-level data if available)
            if metric_id == 'deadlock_rate':
                # Try to get per-replicate deadlock status
                replicate_data = result.get('replicate_data', [])
                if replicate_data:
                    values = [1.0 if rep.get('deadlocked', False) else 0.0 for rep in replicate_data]
                else:
                    # Fallback to aggregate rate
                    values = [stats.get('deadlock_rate', 0.0)]
                values = [v * 100 for v in values]  # Convert to %
            
            elif metric_id == 'viable_rate':
                replicate_data = result.get('replicate_data', [])
                if replicate_data:
                    values = [0.0 if rep.get('deadlocked', False) else 1.0 for rep in replicate_data]
                else:
                    values = [1.0 - stats.get('deadlock_rate', 0.0)]
                values = [v * 100 for v in values]  # Convert to %
            
            elif metric_id == 'mean_tokens':
                # Average token count across all places
                species_stats = stats.get('species_statistics', {})
                mean_values = [
                    sp_stats.get('mean', 0.0)
                    for sp_id, sp_stats in species_stats.items()
                    if sp_id.startswith('P')
                ]
                values = [np.mean(mean_values)] if mean_values else [0.0]
            
            elif metric_id == 'mean_duration':
                replicate_data = result.get('replicate_data', [])
                if replicate_data:
                    values = [rep.get('duration', 0.0) for rep in replicate_data]
                else:
                    values = [stats.get('mean_duration', 0.0)]
            
            else:
                continue
            
            # Check if we have enough values per group
            if len(values) < 2:
                self._show_error(
                    f"Insufficient replicate data for '{name}'.\n\n"
                    f"Statistical tests require at least 2 replicates per group.\n"
                    f"Please re-run experiments with multiple replicates."
                )
                return
            
            groups[name] = values
        
        # Check if we have valid data
        if len(groups) < 2:
            self._show_error("Insufficient data for statistical comparison")
            return
        
        # Perform statistical test
        try:
            if len(groups) == 2:
                # Two-sample t-test
                group_names = list(groups.keys())
                result_stats = TTestComparator.independent_ttest(
                    groups[group_names[0]],
                    groups[group_names[1]],
                    equal_var=True
                )
                
                # Format results
                results_text = (
                    f"<b>Two-Sample t-Test</b>\n\n"
                    f"<b>Groups:</b>\n"
                    f"  • {group_names[0]} (n={result_stats['n1']})\n"
                    f"  • {group_names[1]} (n={result_stats['n2']})\n\n"
                    f"<b>Test Statistics:</b>\n"
                    f"  t-statistic: {result_stats['t_statistic']:.4f}\n"
                    f"  p-value: {result_stats['p_value']:.4f}"
                )
                
                if result_stats['p_value'] < 0.001:
                    results_text += " ***"
                elif result_stats['p_value'] < 0.01:
                    results_text += " **"
                elif result_stats['p_value'] < 0.05:
                    results_text += " *"
                else:
                    results_text += " (ns)"
                
                results_text += (
                    f"\n  df: {result_stats['df']}\n\n"
                    f"<b>Effect Size:</b>\n"
                    f"  Mean Difference: {result_stats['mean_diff']:.3f}\n"
                    f"  Cohen's d: {result_stats['cohens_d']:.3f}\n"
                    f"  95% CI: [{result_stats['ci_lower']:.3f}, {result_stats['ci_upper']:.3f}]\n\n"
                    f"<b>Interpretation:</b>\n"
                )
                
                if result_stats['significant']:
                    results_text += "  <span foreground='green'>✓ Significant difference detected (p &lt; 0.05)</span>"
                else:
                    results_text += "  <span foreground='orange'>✗ No significant difference (p ≥ 0.05)</span>"
            
            else:
                # One-way ANOVA with Tukey HSD
                comparator = StatisticalComparator(groups)
                summary = comparator.get_summary(include_posthoc=True)
                
                anova = summary['anova']
                
                results_text = (
                    f"<b>One-Way ANOVA</b>\n\n"
                    f"<b>Groups ({len(groups)}):</b>\n"
                )
                
                group_parts = []
                for name in groups.keys():
                    n = anova['group_ns'][name]
                    mean = anova['group_means'][name]
                    std = anova['group_stds'][name]
                    group_parts.append(f"  • {name}: {mean:.2f} ± {std:.2f} (n={n})\n")
                results_text += "".join(group_parts)
                
                results_text += (
                    f"\n<b>ANOVA Results:</b>\n"
                    f"  F-statistic: {anova['f_statistic']:.4f}\n"
                    f"  p-value: {anova['p_value']:.4f}"
                )
                
                if anova['p_value'] < 0.001:
                    results_text += " ***"
                elif anova['p_value'] < 0.01:
                    results_text += " **"
                elif anova['p_value'] < 0.05:
                    results_text += " *"
                else:
                    results_text += " (ns)"
                
                results_text += (
                    f"\n  df: ({anova['df_between']}, {anova['df_within']})\n\n"
                )
                
                if anova['significant']:
                    results_text += "<b><span foreground='green'>✓ Significant differences detected (p &lt; 0.05)</span></b>\n\n"
                    
                    # Show Tukey HSD results
                    if 'tukey' in summary:
                        results_text += "<b>Tukey HSD Post-Hoc Tests:</b>\n"
                        tukey = summary['formatted_comparisons']
                        
                        comparison_parts = []
                        for comparison, stats in tukey.items():
                            sig_marker = "***" if stats['p_value'] < 0.001 else "**" if stats['p_value'] < 0.01 else "*" if stats['p_value'] < 0.05 else "ns"
                            comparison_parts.append(
                                f"  • {comparison}:\n"
                                f"    Δμ = {stats['mean_diff']:.3f}, "
                                f"p = {stats['p_value']:.4f} {sig_marker}\n"
                            )
                        results_text += "".join(comparison_parts)
                else:
                    results_text += "<b><span foreground='orange'>✗ No significant differences (p ≥ 0.05)</span></b>"
            
            # Display results in dialog
            results_dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Statistical Test Results"
            )
            
            # Use scrolled window for long results
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_size_request(500, 400)
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            
            results_label = Gtk.Label()
            results_label.set_markup(results_text)
            results_label.set_xalign(0)
            results_label.set_yalign(0)
            results_label.set_line_wrap(True)
            results_label.set_selectable(True)
            results_label.set_margin_start(12)
            results_label.set_margin_end(12)
            results_label.set_margin_top(12)
            results_label.set_margin_bottom(12)
            
            scrolled.add(results_label)
            
            content_area = results_dialog.get_content_area()
            content_area.pack_start(scrolled, True, True, 0)
            
            results_dialog.show_all()
            results_dialog.run()
            results_dialog.destroy()
            
        except ValueError as e:
            # Handle insufficient replicates gracefully
            error_msg = str(e)
            if "at least 2" in error_msg.lower() or "value(s)" in error_msg:
                self._show_error(
                    "Insufficient Replicate Data\n\n"
                    "Statistical tests require at least 2 replicates per experimental condition.\n\n"
                    "Your results appear to be from experiments run with a single replicate only.\n"
                    "Please re-run experiments with 2 or more replicates to enable statistical comparison.\n\n"
                    f"Technical details: {error_msg}"
                )
            else:
                self._show_error(f"Statistical test failed:\n\n{error_msg}")
        except Exception as e:
            self._show_error(f"Statistical test failed:\n\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _on_compare_selected_clicked(self, button):
        """Overlay trajectories of checked experiments (E6 enhancement).
        
        Creates a single plot with multiple trajectories, color-coded by
        experiment name or swept parameter value.
        """
        import numpy as np
        
        # Get checked experiments
        checked = self.get_checked_results()
        
        if len(checked) < 2:
            self._show_error("Please check at least 2 experiments to compare")
            return
        
        if len(checked) > 10:
            # Warn about too many comparisons
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Many Experiments Selected"
            )
            dialog.format_secondary_text(
                f"You've selected {len(checked)} experiments. This may create a cluttered plot.\n\n"
                "Continue anyway?"
            )
            response = dialog.run()
            dialog.destroy()
            
            if response != Gtk.ResponseType.YES:
                return
        
        # Select species to plot
        species_dialog = Gtk.Dialog(
            title="Select Species to Compare",
            transient_for=self.get_toplevel(),
            flags=0
        )
        species_dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content = species_dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        
        label = Gtk.Label(label="Select species (place/transition) to compare:")
        label.set_xalign(0)
        content.pack_start(label, False, False, 6)
        
        # Get all available species from first experiment
        first_name, first_result = checked[0]
        species_stats = first_result.get('statistics', {}).get('species_statistics', {})
        
        species_combo = SearchableComboBox(
            tooltip_text="Type to search, or scroll to browse all species"
        )
        for species_id in sorted(species_stats.keys()):
            display_name = self._resolve_species_name(species_id)
            species_combo.append(species_id, display_name)
        
        if len(species_stats) > 0:
            species_combo.set_active(0)
        
        content.pack_start(species_combo, False, False, 6)
        
        species_dialog.show_all()
        response = species_dialog.run()
        species_id = species_combo.get_active_id()
        species_dialog.destroy()
        
        if response != Gtk.ResponseType.OK or not species_id:
            return
        
        # Generate comparison plot
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Color palette for experiments
            colors = [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ]
            
            legend_entries = []
            
            for idx, (name, result) in enumerate(checked):
                stats = result.get('statistics', {})
                species_stats = stats.get('species_statistics', {})
                time_points = stats.get('time_points', [])
                
                if species_id not in species_stats or not time_points:
                    continue
                
                species_data = species_stats[species_id]
                mean_trajectory = species_data.get('mean', [])
                std_trajectory = species_data.get('std', [])
                
                if not mean_trajectory:
                    continue
                
                # Trajectories should already be flat lists from statistics computation
                # Just verify length matches time_points
                if len(mean_trajectory) != len(time_points):
                    print(f"Warning: Trajectory length mismatch for {name}: {len(mean_trajectory)} vs {len(time_points)} time points")
                    continue
                
                # Verify we have valid numeric data
                if not all(isinstance(x, (int, float)) for x in mean_trajectory):
                    print(f"Warning: mean_trajectory for {name} contains non-numeric data")
                    continue
                
                # Plot mean trajectory
                color = colors[idx % len(colors)]
                lines = ax.plot(time_points, mean_trajectory, color=color, linewidth=2, label=name)
                legend_entries.append((name, lines[0]))
                
                # Add confidence interval (mean ± std)
                if std_trajectory and len(std_trajectory) == len(mean_trajectory):
                    try:
                        lower_bound = [m - s for m, s in zip(mean_trajectory, std_trajectory)]
                        upper_bound = [m + s for m, s in zip(mean_trajectory, std_trajectory)]
                        ax.fill_between(time_points, lower_bound, upper_bound, 
                                        color=color, alpha=0.2)
                    except TypeError as e:
                        print(f"Warning: Could not compute confidence interval for {name}: {e}")
            
            # Styling
            species_display = self._resolve_species_name(species_id)
            ax.set_xlabel('Time', fontsize=11)
            ax.set_ylabel(f'{species_display}', fontsize=11)
            ax.set_title(f'Experiment Comparison: {species_display}', 
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle=':')
            
            # Legend with experiment names
            if len(legend_entries) <= 10:
                ax.legend(frameon=True, shadow=True, loc='best')
            else:
                # Too many for legend, just show in title
                ax.set_title(f'Experiment Comparison: {species_display}\n({len(legend_entries)} experiments)', 
                            fontsize=12, fontweight='bold')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            # Switch to plot page
            self.notebook.set_current_page(1)
            
        except Exception as e:
            self._show_error(f"Comparison plot failed:\n\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _on_sensitivity_analysis_clicked(self, button):
        """Perform sensitivity analysis on all results (E7 enhancement).
        
        Computes Partial Rank Correlation Coefficients (PRCC) from experiment
        results to identify which parameters most strongly influence outputs.
        Assumes experiments were generated using Latin Hypercube Sampling or
        cover a representative range of parameter values.
        """
        from .sensitivity_analyzer import SensitivityAnalyzer
        import numpy as np
        
        # Need at least 10 experiments for meaningful PRCC
        if len(self.results) < 10:
            self._show_error(
                f"Need at least 10 experiments for sensitivity analysis (found {len(self.results)})\n\n"
                "Sensitivity analysis works best with:\n"
                "• Latin Hypercube Sampling (LHS) parameter sweep\n"
                "• Factorial design with multiple parameters\n"
                "• At least 10 × n_parameters experiments"
            )
            return
        
        # Select output metric
        metric_dialog = Gtk.Dialog(
            title="Select Output Metric",
            transient_for=self.get_toplevel(),
            flags=0
        )
        metric_dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content = metric_dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        
        label = Gtk.Label(label="Select the output metric for sensitivity analysis:")
        label.set_xalign(0)
        content.pack_start(label, False, False, 6)
        
        metric_combo = Gtk.ComboBoxText()
        metric_combo.append("deadlock_rate", "Deadlock Rate (%)")
        metric_combo.append("viable_rate", "Viability Rate (%)")
        metric_combo.append("mean_tokens", "Mean Token Count")
        metric_combo.append("mean_duration", "Mean Simulation Duration")
        metric_combo.set_active(0)
        content.pack_start(metric_combo, False, False, 6)
        
        metric_dialog.show_all()
        response = metric_dialog.run()
        metric_id = metric_combo.get_active_id()
        metric_name = metric_combo.get_active_text()
        metric_dialog.destroy()
        
        if response != Gtk.ResponseType.OK or not metric_id:
            return
        
        # Extract parameter values and outputs from experiment names and results
        # Parse experiment names: "param1=val1_param2=val2_..."
        all_params = {}
        outputs = []
        valid_experiments = []
        
        for name, result in self.results.items():
            # Parse parameters from name
            params = {}
            for part in name.split('_'):
                if '=' in part:
                    key, val = part.split('=', 1)
                    try:
                        params[key] = float(val)
                    except ValueError:
                        continue
            
            if not params:
                continue
            
            # Extract output value
            stats = result.get('statistics', {})
            
            if metric_id == 'deadlock_rate':
                output_value = stats.get('deadlock_rate', 0.0) * 100
            elif metric_id == 'viable_rate':
                output_value = (1.0 - stats.get('deadlock_rate', 0.0)) * 100
            elif metric_id == 'mean_tokens':
                species_stats = stats.get('species_statistics', {})
                mean_values = [
                    sp_stats.get('mean', 0.0)
                    for sp_id, sp_stats in species_stats.items()
                    if sp_id.startswith('P')
                ]
                output_value = np.mean(mean_values) if mean_values else 0.0
            elif metric_id == 'mean_duration':
                output_value = stats.get('mean_duration', 0.0)
            else:
                continue
            
            # Store parameter values
            for param_name, param_value in params.items():
                if param_name not in all_params:
                    all_params[param_name] = []
                all_params[param_name].append(param_value)
            
            outputs.append(output_value)
            valid_experiments.append(name)
        
        # Check if we have enough data
        if len(valid_experiments) < 10:
            self._show_error(
                f"Only {len(valid_experiments)} experiments have parseable parameter values.\n\n"
                "Experiment names must follow format: param1=value1_param2=value2_..."
            )
            return
        
        # Verify all parameters have consistent data
        param_names = []
        samples = {}
        
        for param_name, values in all_params.items():
            if len(values) == len(outputs):
                param_names.append(param_name)
                samples[param_name] = np.array(values)
        
        if len(param_names) < 2:
            self._show_error(
                f"Need at least 2 parameters for sensitivity analysis (found {len(param_names)})\n\n"
                "Parameters detected: " + ", ".join(param_names) if param_names else "None"
            )
            return
        
        # Compute PRCC
        try:
            # Determine parameter ranges from data
            param_ranges = {
                name: (np.min(values), np.max(values))
                for name, values in samples.items()
            }
            
            analyzer = SensitivityAnalyzer(param_ranges, n_samples=len(outputs))
            prcc_results = analyzer.compute_prcc(samples, outputs, output_name=metric_name)
            
            # Generate tornado plot
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            plot_data = analyzer.get_tornado_plot_data(prcc_results, top_n=10)
            
            # Create horizontal bar chart (tornado plot)
            y_pos = np.arange(len(plot_data['param_names']))
            
            bars = ax.barh(y_pos, plot_data['prcc_values'], color=plot_data['colors'], alpha=0.8)
            
            # Add significance markers
            for i, (name, prcc, sig) in enumerate(zip(
                plot_data['param_names'],
                plot_data['prcc_values'],
                plot_data['significant']
            )):
                if sig:
                    # Add star for significant
                    x_pos = prcc + (0.05 if prcc > 0 else -0.05)
                    ax.text(x_pos, i, '★', ha='left' if prcc > 0 else 'right',
                           va='center', fontsize=12, color='black')
            
            # Vertical line at zero
            ax.axvline(0, color='black', linewidth=1, linestyle='-', alpha=0.5)
            
            # Styling
            ax.set_yticks(y_pos)
            ax.set_yticklabels(plot_data['param_names'])
            ax.set_xlabel('PRCC (Partial Rank Correlation Coefficient)', fontsize=11)
            ax.set_title(f'Sensitivity Analysis: {metric_name}\n'
                        f'({len(outputs)} experiments, {len(param_names)} parameters)',
                        fontsize=12, fontweight='bold')
            ax.set_xlim(-1, 1)
            ax.grid(True, axis='x', alpha=0.3, linestyle=':')
            
            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='#2ca02c', label='Positive (↑ param → ↑ output)'),
                Patch(facecolor='#d62728', label='Negative (↑ param → ↓ output)'),
                Patch(facecolor='#999999', label='Not significant (p ≥ 0.05)')
            ]
            ax.legend(handles=legend_elements, loc='best', frameon=True, shadow=True)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            # Switch to plot page
            self.notebook.set_current_page(1)
            
            # Show detailed statistics in dialog
            stats_text = analyzer.format_prcc_results(prcc_results, include_insignificant=True)
            
            stats_dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Sensitivity Analysis Results (PRCC)"
            )
            
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_size_request(600, 400)
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            
            stats_label = Gtk.Label()
            stats_label.set_text(stats_text)
            stats_label.set_xalign(0)
            stats_label.set_yalign(0)
            stats_label.set_selectable(True)
            stats_label.set_margin_start(12)
            stats_label.set_margin_end(12)
            stats_label.set_margin_top(12)
            stats_label.set_margin_bottom(12)
            
            scrolled.add(stats_label)
            
            content_area = stats_dialog.get_content_area()
            content_area.pack_start(scrolled, True, True, 0)
            
            stats_dialog.show_all()
            stats_dialog.run()
            stats_dialog.destroy()
            
        except Exception as e:
            self._show_error(f"Sensitivity analysis failed:\n\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def display_result(self, result_data):
        """Display a result in the TreeView.
        
        Implements abstract method from BaseResultsView.
        Adds result to TreeView with default unchecked state.
        
        Args:
            result_data (dict): Result dictionary with keys:
                - name (str): Experiment name
                - statistics (dict): Contains n_replicates
                - duration (float): Execution time in seconds
                - status or error indicator
        """
        name = result_data.get('name', 'Unknown')
        
        # Extract info
        statistics = result_data.get('statistics', {})
        n_replicates = statistics.get('n_replicates', 0)
        
        # Use mean elapsed time per replicate if available, else batch duration
        mean_elapsed = statistics.get('mean_elapsed_time')
        if mean_elapsed is not None and mean_elapsed > 0:
            duration_str = f"{mean_elapsed:.3f}s"
        else:
            # Fallback to total duration
            duration = result_data.get('duration', 0.0)
            duration_str = f"{duration:.2f}s"
        
        error_msg = result_data.get('error', '')
        status = "✗ Error" if error_msg else "✓ Completed"
        
        # Add to store (default: not selected)
        # Include full error message in column 5 for tooltip
        self.results_store.append([False, name, n_replicates, duration_str, status, error_msg])
        
        self._update_status_label()
    
    def add_result(self, name, result):
        """Add experiment result to browser.
        
        Overrides BaseResultsView.add_result to inject name into result_data.
        
        Args:
            name (str): Experiment name
            result (dict): Results dictionary from BatchExecutor
        """
        # Inject name into result data for display_result
        result_with_name = result.copy()
        result_with_name['name'] = name
        
        # Store and display using parent method
        super().add_result(name, result_with_name)
        
        # Auto-detect sweep parameters for dose-response analysis (E3)
        self._update_dose_response_parameters()
    
    
    def clear_results(self):
        """Clear all results.
        
        Implements abstract method from BaseResultsView.
        Clears TreeView store, results dictionary, and resets status label.
        """
        self.results.clear()
        self.results_store.clear()
        self.stats_label.set_markup("<i>Select an experiment to view statistics</i>")
        self._update_status_label()
    
    def get_selected_result(self):
        """Get currently selected result.
        
        Returns:
            tuple: (name, result_dict) or (None, None) if no selection
        """
        selection = self.results_tree.get_selection()
        model, iter = selection.get_selected()
        if iter:
            name = model.get_value(iter, 1)  # Column 1 is name (0 is checkbox)
            return name, self.results.get(name)
        return None, None
    
    def get_checked_results(self):
        """Get all checked results for batch operations.
        
        Returns:
            list: List of (name, result_dict) tuples for checked rows
        """
        checked = []
        iter = self.results_store.get_iter_first()
        while iter:
            is_checked = self.results_store.get_value(iter, 0)
            if is_checked:
                name = self.results_store.get_value(iter, 1)
                result = self.results.get(name)
                if result:
                    checked.append((name, result))
            iter = self.results_store.iter_next(iter)
        return checked
    
    def _update_status_label(self):
        """Update status label with result count and selection count."""
        total = len(self.results_store)
        if total == 0:
            self.status_label.set_markup("<i>No results</i>")
        else:
            # Count completed vs errors and checked items
            completed = 0
            errors = 0
            checked_count = 0
            iter = self.results_store.get_iter_first()
            while iter:
                is_checked = self.results_store.get_value(iter, 0)
                status = self.results_store.get_value(iter, 4)  # Column 4 is status
                if is_checked:
                    checked_count += 1
                if status == "completed":
                    completed += 1
                elif status == "error":
                    errors += 1
                iter = self.results_store.iter_next(iter)
            
            text = f"{total} results"
            if checked_count > 0:
                text += f" (<b>{checked_count} selected</b>)"
            if errors > 0:
                text += f" (<span foreground='red'>{errors} errors</span>)"
            self.status_label.set_markup(text)
            
            # Enable/disable export buttons based on selection
            has_checked = checked_count > 0
            self.export_csv_button.set_sensitive(has_checked or self.get_selected_result()[0] is not None)
            self.export_json_button.set_sensitive(has_checked or self.get_selected_result()[0] is not None)
            
            # Enable statistical tests button if 2+ experiments checked (E5 enhancement)
            self.stats_test_button.set_sensitive(checked_count >= 2)
            
            # Enable compare button if 2+ experiments checked (E6 enhancement)
            self.compare_button.set_sensitive(checked_count >= 2)
            
            # Enable sensitivity analysis if 10+ total experiments (E7 enhancement)
            self.sensitivity_button.set_sensitive(total >= 10)
    
    def _on_selection_changed(self, selection):
        """Handle result selection change."""
        name, result = self.get_selected_result()
        
        if result:
            # Enable action buttons
            self.export_csv_button.set_sensitive(True)
            self.export_json_button.set_sensitive(True)
            self.report_button.set_sensitive(True)
            
            # Display statistics
            self._display_statistics(name, result)
            
            # Display metadata
            self._display_metadata(result)
            
            # Auto-refresh plot if currently viewing plot tab
            if self.notebook.get_current_page() == 1:
                # User is on plot view - update plot automatically
                self._plot_trajectories(name, result)
        else:
            # Disable action buttons
            self.export_csv_button.set_sensitive(False)
            self.export_json_button.set_sensitive(False)
            self.report_button.set_sensitive(False)
            
            self.stats_label.set_markup("<i>Select an experiment to view statistics</i>")
            
            # Clear metadata display
            if hasattr(self, 'metadata_store'):
                self.metadata_store.clear()
                self.metadata_status_label.set_markup("<i>Select an experiment to view metadata</i>")
            
            # Clear plot if on plot view
            if self.notebook.get_current_page() == 1 and self.figure:
                self.figure.clear()
                self.canvas.draw()
    
    def _display_statistics(self, name, result):
        """Display statistics for selected result.
        
        Args:
            name: Experiment name
            result: Result dictionary
        """
        if "error" in result:
            self.stats_label.set_markup(
                f"<b>{name}</b>\n\n"
                f"<span foreground='red'>Error: {result['error']}</span>"
            )
            return
        
        stats = result.get('statistics', {})
        n_reps = stats.get('n_replicates', 0)
        elapsed = result.get('duration', 0.0)
        
        # Build statistics text
        text = f"<b>{name}</b>\n\n"
        text += "<b>Execution:</b>\n"
        text += f"  Replicates: {n_reps}\n"
        text += f"  Execution Time: {elapsed:.2f}s\n\n"
        
        # Display species statistics if available
        species_stats = stats.get('species_statistics', {})
        if species_stats:
            text += "<b>Species Statistics:</b>\n"
            # Show first few species as examples
            species_list = list(species_stats.keys())[:3]
            for species_id in species_list:
                species_data = species_stats[species_id]
                mean_traj = species_data.get('mean', [])
                if len(mean_traj) > 0:
                    final_mean = mean_traj[-1]
                    # Handle case where final_mean is a list/array - take first element
                    if isinstance(final_mean, (list, tuple)):
                        final_mean = final_mean[0] if len(final_mean) > 0 else 0.0
                    
                    std_traj = species_data.get('std', [])
                    final_std = std_traj[-1] if std_traj else 0.0
                    # Handle case where final_std is a list/array - take first element
                    if isinstance(final_std, (list, tuple)):
                        final_std = final_std[0] if len(final_std) > 0 else 0.0
                    
                    text += f"  {species_id}: {final_mean:.2f} ± {final_std:.2f}\n"
            
            if len(species_stats) > 3:
                text += f"  ... and {len(species_stats) - 3} more species\n"
        else:
            text += "<i>Computing statistics...</i>"
        
        self.stats_label.set_markup(text)
    
    def _display_metadata(self, result):
        """Display metadata for selected result.
        
        Args:
            result: Result dictionary (may contain 'metadata' key)
        """
        # Check if metadata widgets exist
        if not hasattr(self, 'metadata_store') or not hasattr(self, 'metadata_status_label'):
            print("⚠️ Metadata widgets not initialized")
            return
        
        # Clear existing metadata
        self.metadata_store.clear()
        
        # Add Results Summary section first (synthetic - not from metadata header)
        name = result.get('name', 'Unknown')
        stats = result.get('statistics', {})
        
        summary_iter = self.metadata_store.append(None, ["Results Summary", "", ""])
        self.metadata_store.append(summary_iter, ["", "Experiment_Name", name])
        
        n_reps = stats.get('n_replicates', 0)
        self.metadata_store.append(summary_iter, ["", "Total_Replicates", str(n_reps)])
        
        mean_elapsed = stats.get('mean_elapsed_time', 0.0)
        if mean_elapsed > 0:
            self.metadata_store.append(summary_iter, ["", "Mean_Time_Per_Replicate", f"{mean_elapsed:.3f}s"])
        
        # Show swept parameter if present
        swept_param = result.get('swept_parameter')
        if swept_param and isinstance(swept_param, dict):
            param_name = swept_param.get('name', 'Unknown')
            param_value = swept_param.get('value', 'N/A')
            if isinstance(param_value, (int, float)):
                self.metadata_store.append(summary_iter, ["", f"Swept_{param_name}", f"{param_value:.4g}"])
            else:
                self.metadata_store.append(summary_iter, ["", f"Swept_{param_name}", str(param_value)])
        
        # Show deadlock statistics if available
        replicate_data = result.get('replicate_data', [])
        if replicate_data:
            deadlock_count = sum(1 for r in replicate_data if r.get('deadlocked', False))
            deadlock_rate = (deadlock_count / len(replicate_data) * 100) if replicate_data else 0
            self.metadata_store.append(summary_iter, ["", "Deadlock_Rate", f"{deadlock_rate:.1f}%"])
        
        # Show summary of final species values
        species_stats = stats.get('species_statistics', {})
        if species_stats:
            self.metadata_store.append(summary_iter, ["", "Tracked_Species_Count", str(len(species_stats))])
            
            # Show first 3 species final values
            for i, (species_id, species_data) in enumerate(list(species_stats.items())[:3]):
                mean_traj = species_data.get('mean', [])
                if mean_traj and len(mean_traj) > 0:
                    final_val = mean_traj[-1]
                    if isinstance(final_val, (list, tuple)) and len(final_val) > 0:
                        final_val = final_val[0]
                    self.metadata_store.append(summary_iter, ["", f"{species_id}_Final", f"{final_val:.4g}"])
        
        # Expand summary section
        path = self.metadata_store.get_path(summary_iter)
        self.metadata_tree.expand_row(path, False)
        
        # Check if result has metadata header
        metadata_header = result.get('metadata')
        if not metadata_header:
            self.metadata_status_label.set_markup(
                "<i>Showing results summary only (no detailed metadata)</i>"
            )
            return
        
        # Display metadata sections
        if hasattr(metadata_header, 'sections'):
            for section in metadata_header.sections:
                if not hasattr(section, '_fields') or not section._fields:
                    continue
                
                # Add section as parent row
                section_name = getattr(section, 'section_name', section.__class__.__name__)
                parent_iter = self.metadata_store.append(None, [section_name, "", ""])
                
                # Add fields as child rows
                for field_name, field_value in section._fields.items():
                    # Format value for display
                    if isinstance(field_value, (list, tuple)):
                        if len(field_value) > 5:
                            display_value = f"[{len(field_value)} items]"
                        else:
                            display_value = ", ".join(str(v) for v in field_value)
                    elif isinstance(field_value, dict):
                        display_value = f"{{...}} ({len(field_value)} keys)"
                    elif hasattr(field_value, 'isoformat'):
                        # datetime object
                        display_value = field_value.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        display_value = str(field_value)
                    
                    self.metadata_store.append(parent_iter, ["", field_name, display_value])
                
                # Expand section by default
                path = self.metadata_store.get_path(parent_iter)
                self.metadata_tree.expand_row(path, False)
            
            self.metadata_status_label.set_markup(
                f"<i>1 results summary + {len(metadata_header.sections)} metadata sections</i>"
            )
        else:
            self.metadata_status_label.set_markup(
                "<i>Invalid metadata format</i>"
            )
    
    def _on_export_csv_clicked(self, button):
        """Handle Export CSV button click - supports batch export if multiple checked."""
        checked_results = self.get_checked_results()
        
        if len(checked_results) > 1:
            # Batch export - export all checked results
            self._batch_export_csv(checked_results)
        elif len(checked_results) == 1:
            # Single checked result
            name, result = checked_results[0]
            if self.on_export_callback:
                self.on_export_callback(name, result, "csv")
        else:
            # No checked results - use current selection
            name, result = self.get_selected_result()
            if name and result and self.on_export_callback:
                self.on_export_callback(name, result, "csv")
    
    def _on_export_json_clicked(self, button):
        """Handle Export JSON button click - supports batch export if multiple checked."""
        checked_results = self.get_checked_results()
        
        if len(checked_results) > 1:
            # Batch export - export all checked results
            self._batch_export_json(checked_results)
        elif len(checked_results) == 1:
            # Single checked result
            name, result = checked_results[0]
            if self.on_export_callback:
                self.on_export_callback(name, result, "json")
        else:
            # No checked results - use current selection
            name, result = self.get_selected_result()
            if name and result and self.on_export_callback:
                self.on_export_callback(name, result, "json")
    
    def _batch_export_csv(self, checked_results):
        """Export multiple checked results to CSV files in one batch operation.
        
        Args:
            checked_results: List of (name, result) tuples
        """
        # Choose directory for batch export
        dialog = Gtk.FileChooserDialog(
            title="Choose Directory for Batch CSV Export",
            transient_for=self.get_toplevel(),
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Select", Gtk.ResponseType.OK
        )
        
        # Set initial directory to project experiments folder if project is open
        project_manager = get_project_manager()
        if project_manager.current_project:
            experiments_dir = os.path.join(project_manager.current_project.base_path, 'experiments')
            if not os.path.exists(experiments_dir):
                try:
                    os.makedirs(experiments_dir, exist_ok=True)
                except OSError as e:
                    self.logger.warning("Could not create experiments directory: %s", e)
            if os.path.isdir(experiments_dir):
                dialog.set_current_folder(experiments_dir)
            else:
                dialog.set_current_folder(project_manager.current_project.base_path)
        
        response = dialog.run()
        directory = dialog.get_filename()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and directory:
            # Export each checked result to the selected directory
            success_count = 0
            for name, result in checked_results:
                if self.on_export_callback:
                    # Call export callback with directory prefix
                    result_with_dir = result.copy()
                    result_with_dir['_batch_export_dir'] = directory
                    result_with_dir['_batch_export_name'] = name
                    self.on_export_callback(name, result_with_dir, "csv_batch")
                    success_count += 1
            
            # Show completion message
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Batch Export Complete"
            )
            dialog.format_secondary_text(
                f"Exported {success_count} CSV files to:\n{directory}"
            )
            dialog.run()
            dialog.destroy()
    
    def _batch_export_json(self, checked_results):
        """Export multiple checked results to JSON files in one batch operation.
        
        Args:
            checked_results: List of (name, result) tuples
        """
        # Choose directory for batch export
        dialog = Gtk.FileChooserDialog(
            title="Choose Directory for Batch JSON Export",
            transient_for=self.get_toplevel(),
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Select", Gtk.ResponseType.OK
        )
        
        # Set initial directory to project experiments folder if project is open
        project_manager = get_project_manager()
        if project_manager.current_project:
            experiments_dir = os.path.join(project_manager.current_project.base_path, 'experiments')
            if not os.path.exists(experiments_dir):
                try:
                    os.makedirs(experiments_dir, exist_ok=True)
                except OSError as e:
                    self.logger.warning("Could not create experiments directory: %s", e)
            if os.path.isdir(experiments_dir):
                dialog.set_current_folder(experiments_dir)
            else:
                dialog.set_current_folder(project_manager.current_project.base_path)
        
        response = dialog.run()
        directory = dialog.get_filename()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and directory:
            # Export each checked result to the selected directory
            success_count = 0
            for name, result in checked_results:
                if self.on_export_callback:
                    # Call export callback with directory prefix
                    result_with_dir = result.copy()
                    result_with_dir['_batch_export_dir'] = directory
                    result_with_dir['_batch_export_name'] = name
                    self.on_export_callback(name, result_with_dir, "json_batch")
                    success_count += 1
            
            # Show completion message
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Batch Export Complete"
            )
            dialog.format_secondary_text(
                f"Exported {success_count} JSON files to:\n{directory}"
            )
            dialog.run()
            dialog.destroy()
    
    def _on_row_toggled(self, renderer, path):
        """Handle checkbox toggle in results list.
        
        Args:
            renderer: CellRendererToggle that was clicked
            path: TreePath of the toggled row
        """
        iter = self.results_store.get_iter(path)
        current_value = self.results_store.get_value(iter, 0)
        self.results_store.set_value(iter, 0, not current_value)
        self._update_status_label()
        
        # Update header icon based on selection state
        self._update_checkbox_header()
    
    def _on_checkbox_header_clicked(self, column):
        """Handle click on checkbox column header to select/deselect all.
        
        Toggles between selecting all rows and deselecting all rows.
        Updates header icon to show current state (☐ = none selected, ☑ = all selected).
        """
        # Toggle state
        self._all_selected = not self._all_selected
        
        # Update all rows
        iter = self.results_store.get_iter_first()
        while iter:
            self.results_store.set_value(iter, 0, self._all_selected)
            iter = self.results_store.iter_next(iter)
        
        # Update header icon
        if self._all_selected:
            column.set_title("☑")
        else:
            column.set_title("☐")
        
        # Update status label
        self._update_status_label()
    
    def _update_checkbox_header(self):
        """Update checkbox header icon based on current selection state."""
        # Count selected rows
        selected_count = 0
        total_count = 0
        iter = self.results_store.get_iter_first()
        while iter:
            if self.results_store.get_value(iter, 0):
                selected_count += 1
            total_count += 1
            iter = self.results_store.iter_next(iter)
        
        # Update header icon and internal state
        if selected_count == 0:
            self.checkbox_column.set_title("☐")
            self._all_selected = False
        elif selected_count == total_count:
            self.checkbox_column.set_title("☑")
            self._all_selected = True
        else:
            # Partially selected - show empty box
            self.checkbox_column.set_title("☐")
            self._all_selected = False

    
    def _on_report_clicked(self, button):
        """Handle Add to Report button click."""
        name, result = self.get_selected_result()
        if name and result and self.on_report_callback:
            self.on_report_callback(name, result)
    
    def _on_clear_clicked(self, button):
        """Handle Clear All button click."""
        # Confirm dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Clear all results?"
        )
        dialog.format_secondary_text(
            "This will remove all experiment results from the browser. "
            "This action cannot be undone."
        )
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.clear_results()
    
    def _plot_trajectories(self, name, result):
        """Plot mean trajectories with confidence intervals in embedded canvas.
        
        For transition sweeps, automatically includes connected places.
        
        Args:
            name: Experiment name
            result: Result dictionary with statistics
        """
        try:
            import numpy as np
        except ImportError:
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="NumPy not available"
            )
            dialog.format_secondary_text(
                "Install numpy to use plotting: pip install numpy"
            )
            dialog.run()
            dialog.destroy()
            return
        
        # Check for error
        if "error" in result:
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Cannot plot failed experiment"
            )
            dialog.format_secondary_text(f"Error: {result['error']}")
            dialog.run()
            dialog.destroy()
            return
        
        stats = result.get('statistics', {})
        species_stats = stats.get('species_statistics', {})
        time_points = stats.get('time_points', [])
        
        # Check if this is a transition sweep - if so, add related places
        swept_param = result.get('swept_parameter')
        if swept_param and swept_param['type'] == 'transitions' and self.model:
            # Find the transition and its connected places
            transition_id = swept_param['id']
            related_place_ids = self._get_related_places_for_transition(transition_id)
            
            # Add transition firing rate to plot if not already present
            
            # Ensure related places are in the plot
            
            # Reorder species: transition first, then related places, then others
            species_order = []
            if transition_id in species_stats:
                species_order.append(transition_id)
            species_order.extend([p for p in related_place_ids if p in species_stats])
            species_order.extend([s for s in species_stats.keys() if s not in species_order])
            
            # Rebuild species_stats in the new order (for display priority)
            species_stats = {sid: species_stats[sid] for sid in species_order}
        
        if not species_stats or not time_points:
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="No trajectory data available"
            )
            dialog.format_secondary_text("Statistics do not contain plottable data.")
            dialog.run()
            dialog.destroy()
            return
        
        # Determine if this is a sweep that should be superposed
        swept_transition_id = None
        swept_place_id = None
        related_place_ids = []
        related_transition_ids = []
        
        if swept_param and swept_param['type'] == 'transitions':
            # TRANSITION SWEEP: Show transition + all places
            swept_transition_id = swept_param['id']
            
            # Get place IDs from subnet structure (the actual subnet composition)
            subnet_structure = result.get('subnet_structure')
            if subnet_structure and 'place_ids' in subnet_structure:
                # Use the actual subnet places
                related_place_ids = subnet_structure['place_ids']
            else:
                # Fallback: Get all place IDs from statistics (exclude the transition itself)
                related_place_ids = [
                    species_id for species_id in species_stats.keys()
                    if species_id != swept_transition_id
                ]
            
            # Get transition to plot (the swept one)
            related_transition_ids = [swept_transition_id] if swept_transition_id in species_stats else []
            
        elif swept_param and swept_param['type'] == 'places':
            # PLACE SWEEP: Show all places + transitions (to see how initial marking affects dynamics)
            swept_place_id = swept_param['id']
            
            # Get all places and transitions from subnet structure
            subnet_structure = result.get('subnet_structure')
            if subnet_structure:
                if 'place_ids' in subnet_structure:
                    related_place_ids = subnet_structure['place_ids']
                if 'transition_ids' in subnet_structure:
                    related_transition_ids = subnet_structure['transition_ids']
            else:
                # Fallback: Get from statistics
                related_place_ids = [sid for sid in species_stats.keys() if sid.startswith('P')]
                related_transition_ids = [sid for sid in species_stats.keys() if sid.startswith('T')]
                
        elif swept_param and swept_param['type'] == 'arcs':
            # ARC SWEEP: Show places (token dynamics) only, exclude transitions (flat lines)
            # Arc weight affects transition firing rate calculation, but we want to see
            # the effect on token dynamics in places, not the constant rate values
            
            # Get all places from subnet structure
            subnet_structure = result.get('subnet_structure')
            if subnet_structure and 'place_ids' in subnet_structure:
                related_place_ids = subnet_structure['place_ids']
            else:
                # Fallback: Get from statistics
                related_place_ids = [sid for sid in species_stats.keys() if sid.startswith('P')]
            
            # Don't include transitions for arc sweeps (they'll be flat lines)
            related_transition_ids = []
        
        # Check if we should create superposed plot
        create_superposed = False
        if swept_transition_id and swept_transition_id in species_stats:
            # Transition sweep with valid data
            create_superposed = True
        elif swept_place_id and (related_transition_ids or related_place_ids):
            # Place sweep with places/transitions to show
            create_superposed = True
        
        if create_superposed:
            # Create single plot with all variables superposed
            self._plot_superposed_sweep(
                name, result, swept_transition_id, swept_place_id,
                related_place_ids, related_transition_ids,
                species_stats, time_points, stats
            )
        else:
            # Create separate subplots for each species (original behavior)
            self._plot_separate_subplots(
                name, result, swept_param, species_stats, time_points, stats
            )
    
    def _plot_superposed_sweep(self, name, result, swept_transition_id, swept_place_id,
                               place_ids, transition_ids, species_stats, time_points, stats):
        """Plot places and transitions superposed on same axes with dual y-axes.
        
        Handles both transition sweeps (transition + places) and place sweeps (places + transition).
        
        Args:
            name: Experiment name
            result: Result dictionary
            swept_transition_id: ID of swept transition (or None)
            swept_place_id: ID of swept place (or None)
            place_ids: List of place IDs to plot
            transition_ids: List of transition IDs to plot
            species_stats: Species statistics dict
            time_points: Time points array
            stats: Full statistics dict
        """
        import numpy as np
        
        time_points_arr = np.array(time_points)
        
        # Clear previous plot
        self.figure.clear()
        
        # Create axes with two y-axes (left: firing rate, right: tokens)
        ax1 = self.figure.add_subplot(111)
        
        # Title with sweep info
        title_text = f"Experiment: {name}\n{stats.get('n_replicates', 0)} replicates"
        swept_param = result.get('swept_parameter')
        if swept_param:
            if swept_param['type'] == 'transitions':
                title_text += f"\nSwept Transition: {swept_param['name']} = {swept_param['value']:.4g}"
            elif swept_param['type'] == 'places':
                title_text += f"\nSwept Place: {swept_param['name']} = {swept_param['value']:.4g}"
        self.figure.suptitle(title_text, fontsize=14, fontweight='bold')
        
        # Left y-axis: Plot transitions (firing rates) - INVERTED
        ax1.set_xlabel('Time', fontsize=12)
        ax1.set_ylabel('Firing Rate (Transitions)', fontsize=12, color='red')
        ax1.tick_params(axis='y', labelcolor='red')
        
        # Plot each transition (if any)
        plotted_transitions = []
        colors_transitions = ['red', 'darkred', 'crimson', 'firebrick']
        
        for idx, transition_id in enumerate(transition_ids):
            if transition_id not in species_stats:
                continue
                
            trans_data = species_stats[transition_id]
            mean = np.array(trans_data.get('mean', []))
            std = np.array(trans_data.get('std', []))
            
            # Ensure arrays are 1D
            if mean.ndim > 1:
                mean = mean.flatten()
            if std.ndim > 1:
                std = std.flatten()
            
            if len(mean) == 0:
                continue
            
            plotted_transitions.append(transition_id)
            color = colors_transitions[idx % len(colors_transitions)]
            trans_name = self._resolve_species_name(transition_id)
            
            # Emphasize if this is the swept transition
            is_swept = (transition_id == swept_transition_id)
            linewidth = 3 if is_swept else 2
            label = f'⚡ {trans_name}' if is_swept else trans_name
            
            # Plot firing rates directly from statistics (computed per-replicate then aggregated)
            from scipy.interpolate import make_interp_spline
            
            if len(time_points_arr) > 50:
                try:
                    # Subsample for cleaner spline (same as places)
                    indices = np.linspace(0, len(time_points_arr)-1, min(500, len(time_points_arr)), dtype=int)
                    time_smooth = time_points_arr[indices]
                    mean_smooth = mean[indices]
                    
                    # Create spline
                    spl = make_interp_spline(time_smooth, mean_smooth, k=min(3, len(time_smooth)-1))
                    
                    # Generate extra smooth points
                    time_fine = np.linspace(time_points_arr[0], time_points_arr[-1], 1000)
                    mean_fine = spl(time_fine)
                    
                    # Plot smooth transition
                    ax1.plot(time_fine, mean_fine, color=color, 
                            linewidth=linewidth, label=label, alpha=0.8)
                except Exception as e:
                    ax1.plot(time_points_arr, mean, color=color, 
                            linewidth=linewidth, label=label, alpha=0.8, linestyle='-', marker='')
            else:
                # Too few points, use raw data
                ax1.plot(time_points_arr, mean, color=color, 
                        linewidth=linewidth, label=label, alpha=0.8, linestyle='-', marker='')
            
            # Plot confidence interval
            ax1.fill_between(time_points_arr, 
                           mean - 2*std, 
                           mean + 2*std, 
                           alpha=0.3, 
                           color=color)
        
        # Right y-axis: Plot places (tokens) - INVERTED
        ax2 = ax1.twinx()
        ax2.set_ylabel('Tokens (Places)', fontsize=12, color='blue')
        ax2.tick_params(axis='y', labelcolor='blue')
        
        # Plot each place (only those with statistics)
        colors_places = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b']
        plotted_places = []
        missing_places = []
        
        for idx, place_id in enumerate(place_ids):
            if place_id not in species_stats:
                missing_places.append(place_id)
                continue
            
            place_data = species_stats[place_id]
            mean = np.array(place_data.get('mean', []))
            std = np.array(place_data.get('std', []))
            
            # Ensure arrays are 1D
            if mean.ndim > 1:
                mean = mean.flatten()
            if std.ndim > 1:
                std = std.flatten()
            
            if len(mean) == 0:
                continue
            
            plotted_places.append(place_id)
            color = colors_places[idx % len(colors_places)]
            place_name = self._resolve_species_name(place_id)
            
            # Smooth the curves for better visualization
            from scipy.interpolate import make_interp_spline
            
            # Use more aggressive smoothing for cleaner curves
            if len(time_points_arr) > 50:  # Lower threshold
                # Create smooth curve using spline interpolation
                try:
                    # Use more points for very smooth curves
                    indices = np.linspace(0, len(time_points_arr)-1, min(500, len(time_points_arr)), dtype=int)
                    time_smooth = time_points_arr[indices]
                    mean_smooth = mean[indices]
                    
                    # Create spline with k=3 (cubic)
                    spl = make_interp_spline(time_smooth, mean_smooth, k=min(3, len(time_smooth)-1))
                    
                    # Generate extra smooth points
                    time_fine = np.linspace(time_points_arr[0], time_points_arr[-1], 1000)
                    mean_fine = spl(time_fine)
                    
                    # Plot smooth mean line
                    line = ax2.plot(time_fine, mean_fine, color=color, 
                                  linewidth=2, label=place_name, alpha=0.8)
                except Exception as e:
                    # Fallback to straight lines if smoothing fails
                    line = ax2.plot(time_points_arr, mean, color=color, 
                                  linewidth=2, label=place_name, alpha=0.8)
            else:
                # Too few points, use raw data
                line = ax2.plot(time_points_arr, mean, color=color, 
                              linewidth=2, label=place_name, alpha=0.8)
            
            # Plot confidence interval (use original data, not smoothed)
            ax2.fill_between(time_points_arr, 
                           mean - 2*std, 
                           mean + 2*std, 
                           alpha=0.2, 
                           color=color)
        
        # Add legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, 
                  loc='best', fontsize=10, framealpha=0.9)
        
        # Grid
        ax1.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _plot_separate_subplots(self, name, result, swept_param, 
                                species_stats, time_points, stats):
        """Plot each species in separate subplots (original behavior).
        
        Args:
            name: Experiment name
            result: Result dictionary
            swept_param: Swept parameter info (or None)
            species_stats: Species statistics dict
            time_points: Time points array
            stats: Full statistics dict
        """
        import numpy as np
        
        # Clear previous plot
        self.figure.clear()
        
        # Create subplots for each species
        n_species = len(species_stats)
        n_cols = min(3, n_species)  # Max 3 columns
        n_rows = (n_species + n_cols - 1) // n_cols
        
        # Calculate figure size based on subplot count
        # Each subplot should be approximately 4x3 inches for good visibility
        subplot_width = 4.5  # inches per subplot
        subplot_height = 3.5  # inches per subplot
        
        # Add margins for title, labels, and padding
        fig_width = n_cols * subplot_width + 1.5
        fig_height = n_rows * subplot_height + 2.0  # Extra space for suptitle
        
        # Set reasonable bounds (don't make it too huge)
        fig_width = min(fig_width, 20.0)  # Max 20 inches wide
        fig_height = min(fig_height, 24.0)  # Max 24 inches tall
        
        # Apply the calculated size
        self.figure.set_size_inches(fig_width, fig_height, forward=True)
        
        # Add subtitle for transition sweeps
        title_text = f"Experiment: {name}\n{stats.get('n_replicates', 0)} replicates"
        if swept_param and swept_param['type'] == 'transitions':
            title_text += f"\nSwept Transition: {swept_param['name']} = {swept_param['value']:.4g}"
        
        axes = self.figure.subplots(n_rows, n_cols)
        self.figure.suptitle(title_text, fontsize=14, fontweight='bold')
        
        # Flatten axes for easy iteration
        if n_species == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes.tolist()
        else:
            axes = axes.flatten()
        
        # Determine which species is the swept transition (for visual distinction)
        swept_transition_id = None
        if swept_param and swept_param['type'] == 'transitions':
            swept_transition_id = swept_param['id']
        
        # Plot each species
        for idx, (species_id, species_data) in enumerate(species_stats.items()):
            ax = axes[idx]
            
            # Check if this is the swept transition
            is_swept_transition = (species_id == swept_transition_id)
            
            mean = np.array(species_data.get('mean', []))
            std = np.array(species_data.get('std', []))
            
            # Ensure arrays are 1D (flatten if needed)
            if mean.ndim > 1:
                mean = mean.flatten()
            if std.ndim > 1:
                std = std.flatten()
            
            if len(mean) == 0 or len(time_points) == 0:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                ax.set_title(species_id)
                continue
            
            # Convert to numpy arrays if needed
            time_points_arr = np.array(time_points)
            if time_points_arr.ndim > 1:
                time_points_arr = time_points_arr.flatten()
            
            # Ensure arrays have same length
            min_len = min(len(time_points_arr), len(mean), len(std))
            time_points_arr = time_points_arr[:min_len]
            mean = mean[:min_len]
            std = std[:min_len]
            
            # Use different colors for transition vs places
            if is_swept_transition:
                color = 'red'  # Swept transition in red
                linewidth = 2.5
            else:
                color = 'blue'  # Places in blue
                linewidth = 2
            
            # Plot mean trajectory
            ax.plot(time_points_arr, mean, color=color, linestyle='-', 
                   linewidth=linewidth, label='Mean')
            
            # Plot confidence interval (mean ± 2*std ≈ 95% CI)
            ax.fill_between(time_points_arr, 
                           mean - 2*std, 
                           mean + 2*std, 
                           alpha=0.3, 
                           color=color,
                           label='95% CI')
            
            # Plot percentiles if available
            percentiles = species_data.get('percentiles', {})
            if '50' in percentiles:
                median = np.array(percentiles['50'])
                if median.ndim > 1:
                    median = median.flatten()
                median = median[:min_len]
                ax.plot(time_points_arr, median, color=color, linestyle='--', 
                       linewidth=1, alpha=0.7, label='Median')
            
            ax.set_xlabel('Time')
            
            # Set ylabel based on species type
            if is_swept_transition:
                ax.set_ylabel('Firing Rate')
            else:
                ax.set_ylabel('Tokens')
            
            # Use name if available, otherwise ID - add type indicator
            species_display = self._resolve_species_name(species_id)
            if is_swept_transition:
                species_display = f"⚡ {species_display} (TRANSITION)"
            
            ax.set_title(species_display, fontweight='bold' if is_swept_transition else 'normal')
            ax.legend(loc='best', fontsize=8)
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for idx in range(n_species, len(axes)):
            axes[idx].set_visible(False)
        
        # Apply tight_layout with padding to prevent overlap
        try:
            self.figure.tight_layout(pad=1.5, h_pad=2.0, w_pad=2.0)
        except Exception as e:
            # Fallback to subplots_adjust if tight_layout fails
            try:
                self.figure.subplots_adjust(left=0.08, right=0.95, top=0.92, 
                                           bottom=0.08, hspace=0.4, wspace=0.3)
            except (ValueError, AttributeError) as layout_err:
                self.logger.debug(f"Failed to adjust matplotlib subplots layout: {layout_err}")
        
        self.canvas.draw()
    
    def set_export_callback(self, callback):
        """Set callback for export actions.
        
        Args:
            callback: Function(name, result, format) to call for export
        """
        self.on_export_callback = callback
    
    def set_report_callback(self, callback):
        """Set callback for add to report action.
        
        Args:
            callback: Function(name, result) to call for report
        """
        self.on_report_callback = callback
    
    def set_model(self, model):
        """Set model reference for ID->name resolution.
        
        Args:
            model: Model with places/transitions for name lookup
        """
        self.model = model
    
    def _resolve_species_name(self, species_id):
        """Resolve species ID to human-readable name.
        
        Args:
            species_id: Place or transition ID
            
        Returns:
            str: Name if found, otherwise ID
        """
        if not self.model:
            return species_id
        
        # Try places first (most common for species)
        if hasattr(self.model, 'places'):
            for place in self.model.places:
                if place.id == species_id:
                    name = getattr(place, 'name', None)
                    if name and name != species_id:
                        return f"{name} ({species_id})"
                    return species_id
        
        # Try transitions
        if hasattr(self.model, 'transitions'):
            for trans in self.model.transitions:
                if trans.id == species_id:
                    name = getattr(trans, 'name', None)
                    if name and name != species_id:
                        return f"{name} ({species_id})"
                    return species_id
        
        return species_id
    
    def _get_related_places_for_transition(self, transition_id):
        """Get all places connected to a transition via arcs.
        
        Args:
            transition_id: Transition ID
            
        Returns:
            list: List of place IDs (inputs, outputs, catalysts)
        """
        if not self.model or not hasattr(self.model, 'arcs'):
            return []
        
        related_places = set()
        
        for arc in self.model.arcs:
            # Check if arc involves this transition
            source_id = getattr(arc.source, 'id', None)
            target_id = getattr(arc.target, 'id', None)
            
            # Place → Transition (input place)
            if target_id == transition_id:
                if source_id:
                    related_places.add(source_id)
            
            # Transition → Place (output place)
            elif source_id == transition_id:
                if target_id:
                    related_places.add(target_id)
        
        return sorted(list(related_places))  # Sort for consistent ordering
    
    def _update_dose_response_parameters(self):
        """Auto-detect sweep parameters from experiment names (E3 enhancement).
        
        Parses experiment names to find varying parameters and populates
        the dose parameter combo box for dose-response analysis.
        """
        # Extract all parameters from experiment names
        # Format: "param1=val1_param2=val2_..."
        all_params = set()
        
        for row in self.results_store:
            name = row[1]  # Column 1 = name
            for part in name.split('_'):
                if '=' in part:
                    param_name = part.split('=', 1)[0]
                    all_params.add(param_name)
        
        # Update combo if parameters found
        if all_params and hasattr(self, 'dr_param_combo'):
            # Store current selection
            current_selection = self.dr_param_combo.get_active_text()
            
            # Clear and repopulate
            self.dr_param_combo.remove_all()
            for param in sorted(all_params):
                self.dr_param_combo.append_text(param)
            
            # Restore selection if still valid, otherwise select first
            if current_selection and current_selection in all_params:
                self.dr_param_combo.set_active_id(current_selection)
            elif len(all_params) > 0:
                self.dr_param_combo.set_active(0)
