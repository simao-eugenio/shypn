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
    
    def __init__(self, model=None):
        """Initialize results browser view.
        
        Args:
            model: Optional model reference for resolving IDs to names
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Results data: experiment_name -> results_dict
        self.results = {}
        
        # Model reference for ID->name resolution
        self.model = model
        
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
        print(f"[BROWSER] add_result called for '{name}'")
        print(f"[BROWSER]   Result keys: {result.keys()}")
        print(f"[BROWSER]   Statistics keys: {result.get('statistics', {}).keys()}")
        print(f"[BROWSER]   N replicates: {result.get('statistics', {}).get('n_replicates', 0)}")
        
        self.results[name] = result
        
        # Extract info
        n_replicates = result.get('statistics', {}).get('n_replicates', 0)
        duration = result.get('duration', 0.0)
        status = "error" if "error" in result else "completed"
        
        # Format duration
        duration_str = f"{duration:.2f}s"
        
        # Add to store
        self.results_store.append([name, n_replicates, duration_str, status])
        
        print(f"[BROWSER] Result '{name}' added to store: {n_replicates} replicates, {duration_str}, {status}")
        
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
        
        For transition sweeps, automatically includes connected places.
        
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
        
        # Check if this is a transition sweep - if so, add related places
        swept_param = result.get('swept_parameter')
        if swept_param and swept_param['type'] == 'transitions' and self.model:
            # Find the transition and its connected places
            transition_id = swept_param['id']
            related_place_ids = self._get_related_places_for_transition(transition_id)
            
            # Add transition firing rate to plot if not already present
            if transition_id not in species_stats:
                print(f"[PLOT] Warning: Transition {transition_id} not found in statistics")
            
            # Ensure related places are in the plot
            for place_id in related_place_ids:
                if place_id not in species_stats:
                    print(f"[PLOT] Warning: Related place {place_id} not found in statistics")
            
            # Reorder species: transition first, then related places, then others
            species_order = []
            if transition_id in species_stats:
                species_order.append(transition_id)
            species_order.extend([p for p in related_place_ids if p in species_stats])
            species_order.extend([s for s in species_stats.keys() if s not in species_order])
            
            # Rebuild species_stats in the new order (for display priority)
            species_stats = {sid: species_stats[sid] for sid in species_order}
        
        # DEBUG: Print what we received
        print(f"[PLOT_DEBUG] stats keys: {stats.keys()}")
        print(f"[PLOT_DEBUG] species_stats keys: {list(species_stats.keys())}")
        print(f"[PLOT_DEBUG] time_points length: {len(time_points)}")
        if species_stats:
            first_species = list(species_stats.keys())[0]
            print(f"[PLOT_DEBUG] first species '{first_species}' keys: {species_stats[first_species].keys()}")
            print(f"[PLOT_DEBUG] first species mean length: {len(species_stats[first_species].get('mean', []))}")
        
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
                print(f"[PLOT] Using subnet structure: {len(related_place_ids)} places from subnet")
            else:
                # Fallback: Get all place IDs from statistics (exclude the transition itself)
                related_place_ids = [
                    species_id for species_id in species_stats.keys()
                    if species_id != swept_transition_id
                ]
                print(f"[PLOT] Warning: No subnet structure, using statistics ({len(related_place_ids)} species)")
            
            # Get transition to plot (the swept one)
            related_transition_ids = [swept_transition_id] if swept_transition_id in species_stats else []
            
            print(f"[PLOT] Transition sweep detected: {swept_transition_id}")
            print(f"[PLOT] Subnet places: {related_place_ids}")
            print(f"[PLOT] Transition in stats: {swept_transition_id in species_stats}")
            
        elif swept_param and swept_param['type'] == 'places':
            # PLACE SWEEP: Show all places + transition
            swept_place_id = swept_param['id']
            
            # Get all places and transitions from subnet structure
            subnet_structure = result.get('subnet_structure')
            if subnet_structure:
                if 'place_ids' in subnet_structure:
                    related_place_ids = subnet_structure['place_ids']
                if 'transition_ids' in subnet_structure:
                    related_transition_ids = subnet_structure['transition_ids']
                print(f"[PLOT] Using subnet structure: {len(related_place_ids)} places, {len(related_transition_ids)} transitions")
            else:
                # Fallback: Get from statistics
                related_place_ids = [sid for sid in species_stats.keys() if sid.startswith('P')]
                related_transition_ids = [sid for sid in species_stats.keys() if sid.startswith('T')]
                print(f"[PLOT] Warning: No subnet structure, using statistics")
            
            print(f"[PLOT] Place sweep detected: {swept_place_id}")
            print(f"[PLOT] Subnet places: {related_place_ids}")
            print(f"[PLOT] Subnet transitions: {related_transition_ids}")
        
        print(f"[PLOT] Available species in stats: {list(species_stats.keys())}")
        
        # Check if we should create superposed plot
        create_superposed = False
        if swept_transition_id and swept_transition_id in species_stats:
            # Transition sweep with valid data
            create_superposed = True
        elif swept_place_id and (related_transition_ids or related_place_ids):
            # Place sweep with places/transitions to show
            create_superposed = True
        
        print(f"[PLOT] Create superposed: {create_superposed}")
        
        if create_superposed:
            # Create single plot with all variables superposed
            print(f"[PLOT] Creating superposed plot...")
            self._plot_superposed_sweep(
                name, result, swept_transition_id, swept_place_id,
                related_place_ids, related_transition_ids,
                species_stats, time_points, stats
            )
        else:
            # Create separate subplots for each species (original behavior)
            print(f"[PLOT] Creating separate subplots...")
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
        import matplotlib.pyplot as plt
        import numpy as np
        
        time_points_arr = np.array(time_points)
        
        # Create figure with two y-axes (left: tokens, right: firing rate)
        fig, ax1 = plt.subplots(figsize=(12, 7))
        
        # Title with sweep info
        title_text = f"Experiment: {name}\n{stats.get('n_replicates', 0)} replicates"
        swept_param = result.get('swept_parameter')
        if swept_param:
            if swept_param['type'] == 'transitions':
                title_text += f"\nSwept Transition: {swept_param['name']} = {swept_param['value']:.4g}"
            elif swept_param['type'] == 'places':
                title_text += f"\nSwept Place: {swept_param['name']} = {swept_param['value']:.4g}"
        fig.suptitle(title_text, fontsize=14, fontweight='bold')
        
        # Left y-axis: Plot places (tokens)
        ax1.set_xlabel('Time', fontsize=12)
        ax1.set_ylabel('Tokens (Places)', fontsize=12, color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        
        # Plot each place (only those with statistics)
        colors_places = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b']
        plotted_places = []
        missing_places = []
        
        for idx, place_id in enumerate(place_ids):
            if place_id not in species_stats:
                missing_places.append(place_id)
                print(f"[PLOT] Warning: Place {place_id} in subnet but not in statistics")
                continue
            
            place_data = species_stats[place_id]
            mean = np.array(place_data.get('mean', []))
            std = np.array(place_data.get('std', []))
            
            if len(mean) == 0:
                print(f"[PLOT] Warning: Place {place_id} has empty data")
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
                    line = ax1.plot(time_fine, mean_fine, color=color, 
                                  linewidth=2, label=place_name, alpha=0.8)
                    print(f"[PLOT] Smoothed {place_id}: {len(time_points_arr)} → {len(time_fine)} points")
                except Exception as e:
                    # Fallback to straight lines if smoothing fails
                    print(f"[PLOT] Smoothing failed for {place_id}: {e}")
                    line = ax1.plot(time_points_arr, mean, color=color, 
                                  linewidth=2, label=place_name, alpha=0.8)
            else:
                # Too few points, use raw data
                print(f"[PLOT] Too few points for {place_id} ({len(time_points_arr)}), using raw data")
                line = ax1.plot(time_points_arr, mean, color=color, 
                              linewidth=2, label=place_name, alpha=0.8)
            
            # Plot confidence interval (use original data, not smoothed)
            ax1.fill_between(time_points_arr, 
                           mean - 2*std, 
                           mean + 2*std, 
                           alpha=0.2, 
                           color=color)
        
        # Right y-axis: Plot transitions (firing rates)
        ax2 = ax1.twinx()
        ax2.set_ylabel('Firing Rate (firings/time)', fontsize=12, color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        
        # Plot each transition (if any)
        plotted_transitions = []
        colors_transitions = ['red', 'darkred', 'crimson', 'firebrick']
        
        for idx, transition_id in enumerate(transition_ids):
            if transition_id not in species_stats:
                print(f"[PLOT] Warning: Transition {transition_id} in subnet but not in statistics")
                continue
                
            trans_data = species_stats[transition_id]
            mean = np.array(trans_data.get('mean', []))
            std = np.array(trans_data.get('std', []))
            
            if len(mean) == 0:
                print(f"[PLOT] Warning: Transition {transition_id} has empty data")
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
                    ax2.plot(time_fine, mean_fine, color=color, 
                            linewidth=linewidth, label=label, alpha=0.8)
                    print(f"[PLOT] Smoothed transition {transition_id}: {len(time_points_arr)} → {len(time_fine)} points")
                except Exception as e:
                    print(f"[PLOT] Smoothing failed for transition {transition_id}: {e}, using raw data")
                    ax2.plot(time_points_arr, mean, color=color, 
                            linewidth=linewidth, label=label, alpha=0.8, linestyle='-', marker='')
            else:
                # Too few points, use raw data
                print(f"[PLOT] Too few points for transition {transition_id} ({len(time_points_arr)}), using raw data")
                ax2.plot(time_points_arr, mean, color=color, 
                        linewidth=linewidth, label=label, alpha=0.8, linestyle='-', marker='')
            
            # Plot confidence interval
            ax2.fill_between(time_points_arr, 
                           mean - 2*std, 
                           mean + 2*std, 
                           alpha=0.3, 
                           color=color)
        
        # Add legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, 
                  loc='best', fontsize=10, framealpha=0.9)
        
        # Grid
        ax1.grid(True, alpha=0.3)
        
        # Summary of what was plotted
        print(f"[PLOT] Superposed plot complete:")
        if swept_transition_id:
            print(f"[PLOT]   Swept transition: {swept_transition_id} ({'found' if swept_transition_id in species_stats else 'MISSING'})")
        if swept_place_id:
            print(f"[PLOT]   Swept place: {swept_place_id} ({'found' if swept_place_id in species_stats else 'MISSING'})")
        print(f"[PLOT]   Places plotted: {len(plotted_places)}/{len(place_ids)}")
        print(f"[PLOT]   Transitions plotted: {len(plotted_transitions)}/{len(transition_ids)}")
        if missing_places:
            print(f"[PLOT]   WARNING: {len(missing_places)} places from subnet missing in statistics: {missing_places}")
        
        plt.tight_layout()
        plt.show()
    
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
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Create figure with subplots for each species
        n_species = len(species_stats)
        n_cols = min(3, n_species)  # Max 3 columns
        n_rows = (n_species + n_cols - 1) // n_cols
        
        # Add subtitle for transition sweeps
        title_text = f"Experiment: {name}\n{stats.get('n_replicates', 0)} replicates"
        if swept_param and swept_param['type'] == 'transitions':
            title_text += f"\nSwept Transition: {swept_param['name']} = {swept_param['value']:.4g}"
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 4*n_rows))
        fig.suptitle(title_text, fontsize=14, fontweight='bold')
        
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
            
            # DEBUG: Check data structure
            print(f"[PLOT_DEBUG] Species {species_id}: keys = {species_data.keys()}")
            
            mean = np.array(species_data.get('mean', []))
            std = np.array(species_data.get('std', []))
            
            print(f"[PLOT_DEBUG] Species {species_id}: mean type = {type(species_data.get('mean'))}, len = {len(species_data.get('mean', []))}")
            print(f"[PLOT_DEBUG] Species {species_id}: np.array(mean) shape = {mean.shape}, dtype = {mean.dtype}")
            print(f"[PLOT_DEBUG] Species {species_id}: first few mean values = {mean[:5] if len(mean) > 0 else 'empty'}")
            print(f"[PLOT_DEBUG] time_points type = {type(time_points)}, len = {len(time_points)}")
            
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
