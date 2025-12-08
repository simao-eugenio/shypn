#!/usr/bin/env python3
"""Results Browser View - Display and analyze experiment results.

Shows completed experiments with statistics, visualizations, and export options.
Integrates with BatchExecutor for retrieving results.

Author: Simão Eugénio
Date: December 7, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class ResultsBrowserView(Gtk.Box):
    """Widget for browsing and analyzing experiment results.
    
    Features:
    - TreeView listing completed experiments
    - Statistics display (mean, stddev, confidence intervals)
    - Export to CSV/JSON
    - Integration with Report panel
    """
    
    def __init__(self):
        """Initialize results browser view."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Results data: experiment_name -> results_dict
        self.results = {}
        
        # Callbacks
        self.on_export_callback = None
        self.on_report_callback = None
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build results browser UI."""
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Experiment Results</b>")
        title_label.set_xalign(0)
        self.pack_start(title_label, False, False, 0)
        
        # Results TreeView in ScrolledWindow
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 150)
        
        # Create ListStore: name, replicates, duration, status
        # Columns: 0=name (str), 1=n_replicates (int), 2=duration (str), 3=status (str)
        self.results_store = Gtk.ListStore(str, int, str, str)
        
        # Create TreeView
        self.results_tree = Gtk.TreeView(model=self.results_store)
        self.results_tree.set_headers_visible(True)
        
        # Column 1: Experiment Name
        renderer_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Experiment", renderer_name, text=0)
        column_name.set_expand(True)
        self.results_tree.append_column(column_name)
        
        # Column 2: Replicates
        renderer_reps = Gtk.CellRendererText()
        column_reps = Gtk.TreeViewColumn("Replicates", renderer_reps, text=1)
        column_reps.set_min_width(80)
        self.results_tree.append_column(column_reps)
        
        # Column 3: Duration
        renderer_dur = Gtk.CellRendererText()
        column_dur = Gtk.TreeViewColumn("Duration", renderer_dur, text=2)
        column_dur.set_min_width(80)
        self.results_tree.append_column(column_dur)
        
        # Column 4: Status
        renderer_status = Gtk.CellRendererText()
        column_status = Gtk.TreeViewColumn("Status", renderer_status, text=3)
        column_status.set_min_width(80)
        self.results_tree.append_column(column_status)
        
        # Connect selection changed
        selection = self.results_tree.get_selection()
        selection.connect("changed", self._on_selection_changed)
        
        scrolled.add(self.results_tree)
        self.pack_start(scrolled, True, True, 0)
        
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
        self.pack_start(stats_frame, False, False, 0)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Export CSV button
        self.export_csv_button = Gtk.Button(label="Export CSV")
        self.export_csv_button.set_tooltip_text("Export selected results to CSV")
        self.export_csv_button.set_sensitive(False)
        self.export_csv_button.connect("clicked", self._on_export_csv_clicked)
        button_box.pack_start(self.export_csv_button, False, False, 0)
        
        # Export JSON button
        self.export_json_button = Gtk.Button(label="Export JSON")
        self.export_json_button.set_tooltip_text("Export selected results to JSON")
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
        
        self.pack_start(button_box, False, False, 0)
    
    def add_result(self, name, result):
        """Add experiment result to browser.
        
        Args:
            name: Experiment name
            result: Results dictionary from BatchExecutor
        """
        self.results[name] = result
        
        # Extract info
        n_replicates = result.get('statistics', {}).get('n_replicates', 0)
        duration = result.get('duration', 0.0)
        status = "error" if "error" in result else "completed"
        
        # Format duration
        duration_str = f"{duration:.2f}s"
        
        # Add to store
        self.results_store.append([name, n_replicates, duration_str, status])
        
        self._update_status_label()
    
    def clear_results(self):
        """Clear all results."""
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
            name = model.get_value(iter, 0)
            return name, self.results.get(name)
        return None, None
    
    def _update_status_label(self):
        """Update status label with result count."""
        total = len(self.results_store)
        if total == 0:
            self.status_label.set_markup("<i>No results</i>")
        else:
            # Count completed vs errors
            completed = 0
            errors = 0
            iter = self.results_store.get_iter_first()
            while iter:
                status = self.results_store.get_value(iter, 3)
                if status == "completed":
                    completed += 1
                elif status == "error":
                    errors += 1
                iter = self.results_store.iter_next(iter)
            
            text = f"{total} results"
            if errors > 0:
                text += f" (<span foreground='red'>{errors} errors</span>)"
            self.status_label.set_markup(text)
    
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
        else:
            # Disable action buttons
            self.export_csv_button.set_sensitive(False)
            self.export_json_button.set_sensitive(False)
            self.plot_button.set_sensitive(False)
            self.report_button.set_sensitive(False)
            
            self.stats_label.set_markup("<i>Select an experiment to view statistics</i>")
    
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
        """Handle Export CSV button click."""
        name, result = self.get_selected_result()
        if name and result and self.on_export_callback:
            self.on_export_callback(name, result, "csv")
    
    def _on_export_json_clicked(self, button):
        """Handle Export JSON button click."""
        name, result = self.get_selected_result()
        if name and result and self.on_export_callback:
            self.on_export_callback(name, result, "json")
    
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
        """Handle Plot button click - show trajectory plot."""
        name, result = self.get_selected_result()
        if name and result:
            self._plot_trajectories(name, result)
    
    def _plot_trajectories(self, name, result):
        """Plot mean trajectories with confidence intervals.
        
        Args:
            name: Experiment name
            result: Result dictionary with statistics
        """
        try:
            import matplotlib
            matplotlib.use('TkAgg')  # Use TkAgg backend for popup windows
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Matplotlib not available"
            )
            dialog.format_secondary_text(
                "Install matplotlib to use plotting: pip install matplotlib"
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
        
        # Create figure with subplots for each species
        n_species = len(species_stats)
        n_cols = min(3, n_species)  # Max 3 columns
        n_rows = (n_species + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 4*n_rows))
        fig.suptitle(f"Experiment: {name}\\n{stats.get('n_replicates', 0)} replicates", 
                     fontsize=14, fontweight='bold')
        
        # Flatten axes for easy iteration
        if n_species == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes.tolist()
        else:
            axes = axes.flatten()
        
        # Plot each species
        for idx, (species_id, species_data) in enumerate(species_stats.items()):
            ax = axes[idx]
            
            mean = np.array(species_data.get('mean', []))
            std = np.array(species_data.get('std', []))
            
            if len(mean) == 0 or len(time_points) == 0:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                ax.set_title(species_id)
                continue
            
            # Plot mean trajectory
            ax.plot(time_points, mean, 'b-', linewidth=2, label='Mean')
            
            # Plot confidence interval (mean ± 2*std ≈ 95% CI)
            ax.fill_between(time_points, 
                           mean - 2*std, 
                           mean + 2*std, 
                           alpha=0.3, 
                           color='blue',
                           label='95% CI')
            
            # Plot percentiles if available
            percentiles = species_data.get('percentiles', {})
            if '50' in percentiles:
                median = np.array(percentiles['50'])
                ax.plot(time_points, median, 'r--', linewidth=1, alpha=0.7, label='Median')
            
            ax.set_xlabel('Time')
            ax.set_ylabel('Tokens')
            ax.set_title(species_id)
            ax.legend(loc='best', fontsize=8)
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for idx in range(n_species, len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        plt.show()
    
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
