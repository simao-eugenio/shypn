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
import matplotlib
matplotlib.use('GTK3Agg')
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3
from matplotlib.figure import Figure
from .base_results_view import BaseResultsView


class ResultsBrowserView(BaseResultsView):
    """Widget for browsing and analyzing experiment results.
    
    Inherits from BaseResultsView to provide:
    - TreeView listing completed experiments
    - Statistics display (mean, stddev, confidence intervals)
    - Export to CSV/JSON (single and batch)
    - Embedded matplotlib plotting
    - Integration with Report panel
    
    Features:
    - Multi-select checkboxes for batch export
    - Select All / Deselect All buttons
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
        
        # Create ListStore: selected (bool), name, replicates, duration, status
        # Columns: 0=selected (bool), 1=name (str), 2=n_replicates (int), 3=duration (str), 4=status (str)
        self.results_store = Gtk.ListStore(bool, str, int, str, str)
        
        # Create TreeView
        self.results_tree = Gtk.TreeView(model=self.results_store)
        self.results_tree.set_headers_visible(True)
        
        # Column 0: Checkbox for multi-selection
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.set_activatable(True)
        renderer_toggle.connect("toggled", self._on_row_toggled)
        column_select = Gtk.TreeViewColumn("☑", renderer_toggle, active=0)
        column_select.set_min_width(40)
        self.results_tree.append_column(column_select)
        
        # Column 1: Experiment Name
        renderer_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Experiment", renderer_name, text=1)
        column_name.set_expand(True)
        self.results_tree.append_column(column_name)
        
        # Column 2: Replicates
        renderer_reps = Gtk.CellRendererText()
        column_reps = Gtk.TreeViewColumn("Replicates", renderer_reps, text=2)
        column_reps.set_min_width(80)
        self.results_tree.append_column(column_reps)
        
        # Column 3: Duration
        renderer_dur = Gtk.CellRendererText()
        column_dur = Gtk.TreeViewColumn("Duration", renderer_dur, text=3)
        column_dur.set_min_width(80)
        self.results_tree.append_column(column_dur)
        
        # Column 4: Status
        renderer_status = Gtk.CellRendererText()
        column_status = Gtk.TreeViewColumn("Status", renderer_status, text=4)
        column_status.set_min_width(80)
        self.results_tree.append_column(column_status)
        
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
        
        # Select All / Deselect All buttons
        select_all_button = Gtk.Button(label="☑ Select All")
        select_all_button.set_tooltip_text("Select all results for batch export")
        select_all_button.connect("clicked", self._on_select_all_clicked)
        button_box.pack_start(select_all_button, False, False, 0)
        
        deselect_all_button = Gtk.Button(label="☐ Deselect All")
        deselect_all_button.set_tooltip_text("Deselect all results")
        deselect_all_button.connect("clicked", self._on_deselect_all_clicked)
        button_box.pack_start(deselect_all_button, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        button_box.pack_start(separator, False, False, 4)
        
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
        
        # Plot button
        self.plot_button = Gtk.Button(label="📊 Plot")
        self.plot_button.set_tooltip_text("Plot mean trajectories with confidence intervals")
        self.plot_button.set_sensitive(False)
        self.plot_button.connect("clicked", self._on_plot_clicked)
        button_box.pack_start(self.plot_button, False, False, 0)
        
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
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6), dpi=80)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.set_size_request(600, 400)
        
        # Navigation toolbar
        self.toolbar = NavigationToolbar2GTK3(self.canvas)
        plot_page.pack_start(self.toolbar, False, False, 0)
        plot_page.pack_start(self.canvas, True, True, 0)
        
        # Add pages to notebook
        self.notebook.append_page(list_page, Gtk.Label(label="Results List"))
        self.notebook.append_page(plot_page, Gtk.Label(label="Plot View"))
        
        self.pack_start(self.notebook, True, True, 0)
    
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
        n_replicates = result_data.get('statistics', {}).get('n_replicates', 0)
        duration = result_data.get('duration', 0.0)
        status = "error" if "error" in result_data else "completed"
        
        # Format duration
        duration_str = f"{duration:.2f}s"
        
        # Add to store (default: not selected)
        self.results_store.append([False, name, n_replicates, duration_str, status])
        
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
    
    def _on_selection_changed(self, selection):
        """Handle result selection change."""
        name, result = self.get_selected_result()
        
        if result:
            # Enable action buttons
            self.export_csv_button.set_sensitive(True)
            self.export_json_button.set_sensitive(True)
            self.plot_button.set_sensitive(True)
            self.report_button.set_sensitive(True)
            
            # Display statistics
            self._display_statistics(name, result)
            
            # Auto-refresh plot if currently viewing plot tab
            if self.notebook.get_current_page() == 1:
                # User is on plot view - update plot automatically
                self._plot_trajectories(name, result)
        else:
            # Disable action buttons
            self.export_csv_button.set_sensitive(False)
            self.export_json_button.set_sensitive(False)
            self.plot_button.set_sensitive(False)
            self.report_button.set_sensitive(False)
            
            self.stats_label.set_markup("<i>Select an experiment to view statistics</i>")
            
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
        text += f"<b>Execution:</b>\n"
        text += f"  Replicates: {n_reps}\n"
        text += f"  Execution Time: {elapsed:.2f}s\n\n"
        
        # Display species statistics if available
        species_stats = stats.get('species_statistics', {})
        if species_stats:
            text += f"<b>Species Statistics:</b>\n"
            # Show first few species as examples
            species_list = list(species_stats.keys())[:3]
            for species_id in species_list:
                species_data = species_stats[species_id]
                mean_traj = species_data.get('mean', [])
                if len(mean_traj) > 0:
                    final_mean = mean_traj[-1]
                    final_std = species_data.get('std', [])[-1] if species_data.get('std') else 0
                    text += f"  {species_id}: {final_mean:.2f} ± {final_std:.2f}\n"
            
            if len(species_stats) > 3:
                text += f"  ... and {len(species_stats) - 3} more species\n"
        else:
            text += "<i>Computing statistics...</i>"
        
        self.stats_label.set_markup(text)
    
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
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Select", Gtk.ResponseType.OK
        )
        
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
                text=f"Batch Export Complete"
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
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Select", Gtk.ResponseType.OK
        )
        
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
                text=f"Batch Export Complete"
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
    
    def _on_select_all_clicked(self, button):
        """Select all results for batch operations."""
        iter = self.results_store.get_iter_first()
        while iter:
            self.results_store.set_value(iter, 0, True)
            iter = self.results_store.iter_next(iter)
        self._update_status_label()
    
    def _on_deselect_all_clicked(self, button):
        """Deselect all results."""
        iter = self.results_store.get_iter_first()
        while iter:
            self.results_store.set_value(iter, 0, False)
            iter = self.results_store.iter_next(iter)
        self._update_status_label()
    
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
    
    def _on_plot_clicked(self, button):
        """Handle Plot button click - show trajectory plot in embedded canvas."""
        name, result = self.get_selected_result()
        if name and result:
            # Switch to plot view tab
            self.notebook.set_current_page(1)
            # Render plot in embedded canvas
            self._plot_trajectories(name, result)
    
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
            
            if len(mean) == 0 or len(time_points) == 0:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                ax.set_title(species_id)
                continue
            
            # Convert to numpy arrays if needed
            time_points_arr = np.array(time_points)
            
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
        
        self.figure.tight_layout()
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
