#!/usr/bin/env python3
"""Experiment Automation Category for Viability Panel.

Provides batch experiment automation capabilities:
- Parameter sweep configuration
- Experiment queue management
- Batch execution with progress tracking
- Results browser with statistics and plotting

Architecture:
- Phase 1: Empty skeleton (current implementation)
- Phase 2: Parameter sweep builder
- Phase 3: Experiment queue and batch executor
- Phase 4: Results browser and export

Author: Simão Eugénio
Date: December 7, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.ui.category_frame import CategoryFrame


class ExperimentAutomationCategory:
    """Experiment automation category for batch parameter testing.
    
    This category provides tools for automating parameter exploration:
    1. Parameter Sweep Configuration - Define ranges/lists for batch testing
    2. Experiment Queue - Manage and execute batch experiments
    3. Results Browser - View statistics, plots, and export results
    
    Integration:
    - Uses existing ExperimentManager for snapshot management
    - Uses existing SubnetSimulator for execution
    - Uses ReplicateRunner for batch simulation
    """
    
    def __init__(self, model_canvas=None, experiment_manager=None, expanded=False):
        """Initialize experiment automation category.
        
        Args:
            model_canvas: ModelCanvas instance for accessing model
            experiment_manager: ExperimentManager for snapshot management
            expanded: Whether category starts expanded (default: False)
        """
        self.model_canvas = model_canvas
        self.experiment_manager = experiment_manager
        self.parent_panel = None  # Will be set by ViabilityPanel
        
        # UI Components (to be built in phases)
        self.category_frame = None
        self.content_box = None
        
        # Phase 2 components (Parameter Sweep)
        self.sweep_builder = None
        
        # Phase 3 components (Queue Management)
        self.queue_view = None
        self.batch_executor = None
        
        # Phase 4 components (Results Browser)
        self.results_browser = None
        
        # Track pending UI updates to prevent queue overflow
        self._pending_updates = {}  # Dict: queue_index -> latest (status, progress) to process
        self._processing_updates = set()  # Set of queue_index currently being processed
        
        # Build UI
        self._build_frame(expanded)
    
    def _build_frame(self, expanded):
        """Build category frame with collapsible expander.
        
        Args:
            expanded: Whether to start expanded
        """
        # Create category frame (matches Topology/Report pattern)
        self.category_frame = CategoryFrame(
            title="EXPERIMENT AUTOMATION",
            expanded=expanded
        )
        
        # Main content box
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_margin_start(12)
        self.content_box.set_margin_end(12)
        self.content_box.set_margin_top(6)
        self.content_box.set_margin_bottom(6)
        
        # Build sweep builder content (Phase 2)
        self._build_placeholder_content()
        
        # Add content to category frame
        self.category_frame.set_content(self.content_box)
        
        # Ensure all widgets are visible when expanded
        if expanded:
            self.content_box.show_all()
    
    def _build_placeholder_content(self):
        """Build parameter sweep builder content (Phase 2).
        
        Replaces Phase 1 placeholder with functional sweep configuration UI.
        """
        from .parameter_sweep_builder import ParameterSweepBuilder
        
        # Create sweep builder
        self.sweep_builder = ParameterSweepBuilder()
        self.sweep_builder.set_generate_callback(self._on_sweep_generate)
        
        # Connect type change to parameter refresh AND clear queue
        self.sweep_builder.type_combo.connect("changed", self._on_object_type_changed)
        
        # Add to content box
        self.content_box.pack_start(self.sweep_builder, False, False, 0)
        
        # Initial parameter population (will be called again when parent_panel is set)
        GLib.idle_add(self.refresh_parameters)
        
        # Separator before future Phase 3/4 components
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(12)
        sep.set_margin_bottom(12)
        self.content_box.pack_start(sep, False, False, 0)
        
        # === PHASE 3: EXPERIMENT QUEUE ===
        from .experiment_queue_view import ExperimentQueueView
        from .batch_executor import BatchExecutor
        
        # Create queue view
        self.queue_view = ExperimentQueueView()
        self.queue_view.set_run_callback(self._on_queue_run)
        self.queue_view.set_cancel_callback(self._on_queue_cancel)
        self.queue_view.set_clear_callback(self._on_queue_cleared)
        self.content_box.pack_start(self.queue_view, True, True, 0)
        
        # Create batch executor
        self.batch_executor = BatchExecutor(
            experiment_manager=self.experiment_manager,
            model_canvas=self.model_canvas,
            parent_panel=self.parent_panel  # Pass parent panel for subnet access
        )
        
        # === PHASE 4: RESULTS BROWSER ===
        from .results_browser_view import ResultsBrowserView
        
        # Separator before results
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep2.set_margin_top(12)
        sep2.set_margin_bottom(12)
        self.content_box.pack_start(sep2, False, False, 0)
        
        # Create results browser
        self.results_browser = ResultsBrowserView()
        self.results_browser.set_export_callback(self._on_export_results)
        self.results_browser.set_report_callback(self._on_add_to_report)
        self.content_box.pack_start(self.results_browser, True, True, 0)
    
    def _on_object_type_changed(self, combo):
        """Handle object type change - clear queue and refresh parameters.
        
        When switching between places, transitions, arcs, the old experiments
        are no longer valid, so clear the queue.
        """
        # Clear experiment queue
        if hasattr(self, 'queue_view'):
            self.queue_view.clear_queue()
        
        # Clear results browser
        if hasattr(self, 'results_browser'):
            self.results_browser.clear_results()
        
        # Refresh parameters for new object type
        self.refresh_parameters()
    
    def refresh_parameters(self):
        """Refresh available parameters from parent panel state.
        
        Called when viability panel loads a subnet or updates parameters.
        Pulls actual parameter names from the subnet TreeViews.
        """
        if not self.parent_panel or not self.sweep_builder:
            return
        
        # Get current parameter type
        param_type = self.sweep_builder.type_combo.get_active_id()
        
        # Pull parameters from parent panel's TreeViews
        params = []
        
        if param_type == 'transitions':
            # Get from transitions_store (TreeView data)
            if hasattr(self.parent_panel, 'transitions_store'):
                store = self.parent_panel.transitions_store
                iter = store.get_iter_first()
                while iter:
                    # Column 0 is transition ID
                    transition_id = store.get_value(iter, 0)
                    if transition_id:
                        params.append(transition_id)
                    iter = store.iter_next(iter)
        
        elif param_type == 'places':
            # Get from places_store
            if hasattr(self.parent_panel, 'places_store'):
                store = self.parent_panel.places_store
                iter = store.get_iter_first()
                while iter:
                    # Column 0 is place ID
                    place_id = store.get_value(iter, 0)
                    if place_id:
                        params.append(place_id)
                    iter = store.iter_next(iter)
        
        elif param_type == 'arcs':
            # Get from arcs_store
            if hasattr(self.parent_panel, 'arcs_store'):
                store = self.parent_panel.arcs_store
                iter = store.get_iter_first()
                while iter:
                    # Column 0 is arc ID (or construct from source/target)
                    arc_id = store.get_value(iter, 0)
                    if not arc_id:
                        # Construct from source → target
                        source = store.get_value(iter, 1)  # Column 1 might be source
                        target = store.get_value(iter, 2)  # Column 2 might be target
                        if source and target:
                            arc_id = f"{source}→{target}"
                    if arc_id:
                        params.append(arc_id)
                    iter = store.iter_next(iter)
        
        # Update sweep builder with actual parameters
        if params:
            self.sweep_builder.set_available_parameters(param_type, params)
        else:
            # Show helpful message if no subnet loaded
            self.sweep_builder.set_available_parameters(param_type, [])
            if hasattr(self.sweep_builder, 'name_combo'):
                self.sweep_builder.name_combo.append("none", "(Load subnet via right-click transition)")
                self.sweep_builder.name_combo.set_active(0)
    
    def _on_sweep_generate(self, config):
        """Handle parameter sweep generation.
        
        Args:
            config: Dictionary with sweep configuration:
                - parameter_type: 'places', 'transitions', 'arcs'
                - parameter_name: Name of parameter to vary
                - values: List of values to test
                - replicates: Number of replicates per experiment
                - duration: Simulation duration
        """
        if self.experiment_manager is None:
            self._show_error("ExperimentManager not available. Please ensure a model is loaded in Viability Panel.")
            return
        
        # Check if subnet is loaded (selected localities exist)
        if self.parent_panel and hasattr(self.parent_panel, 'selected_localities'):
            if not self.parent_panel.selected_localities:
                self._show_error("No subnet loaded. Please right-click a transition and select 'Add to Viability Analysis' first.")
                return
        
        # Check if there's at least one snapshot (baseline)
        if len(self.experiment_manager.snapshots) == 0:
            # Create a baseline snapshot from current viability panel state
            if self.parent_panel and hasattr(self.parent_panel, 'places_store'):
                baseline = self.experiment_manager.add_snapshot("Baseline")
                # Capture current subnet state from TreeViews
                baseline.capture_from_treeviews(
                    self.parent_panel.places_store,
                    self.parent_panel.transitions_store,
                    self.parent_panel.arcs_store
                )
            else:
                self._show_error("No baseline experiment. Please load a subnet via right-click transition first.")
                return
        
        # Ensure we have a valid baseline with data
        base_snapshot = self.experiment_manager.get_active_snapshot()
        if base_snapshot:
            # Check if baseline is empty (no parameters captured)
            if (not base_snapshot.place_markings and 
                not base_snapshot.transition_rates and 
                not base_snapshot.arc_weights):
                # Recapture from current TreeViews
                if self.parent_panel and hasattr(self.parent_panel, 'places_store'):
                    base_snapshot.capture_from_treeviews(
                        self.parent_panel.places_store,
                        self.parent_panel.transitions_store,
                        self.parent_panel.arcs_store
                    )
        
        try:
            # Store baseline snapshot count
            baseline_count = len(self.experiment_manager.snapshots)
            
            # Generate sweep snapshots
            count = self.experiment_manager.generate_sweep_snapshots(
                parameter_type=config['parameter_type'],
                parameter_name=config['parameter_name'],
                values=config['values'],
                base_snapshot=base_snapshot
            )
            
            # Update preview
            if hasattr(self.sweep_builder, 'preview_label'):
                self.sweep_builder.preview_label.set_markup(
                    f"<span foreground='green'>✓ Generated {count} experiment snapshots</span>"
                )
            
            # Auto-add generated experiments to queue
            if self.queue_view and count > 0:
                new_snapshots = self.experiment_manager.snapshots[baseline_count:]
                experiments = [
                    (snapshot.name, baseline_count + i)
                    for i, snapshot in enumerate(new_snapshots)
                ]
                self.queue_view.add_experiments(experiments)
            
            # Notify parent panel to refresh experiment combo
            if self.parent_panel and hasattr(self.parent_panel, 'refresh_experiment_combo'):
                self.parent_panel.refresh_experiment_combo()
            
        except Exception as e:
            self._show_error(f"Sweep generation failed: {str(e)}")
    
    def _on_queue_run(self, pending_experiments):
        """Handle queue run request.
        
        Args:
            pending_experiments: List of (index, name, snapshot_index) tuples
        """
        if not self.batch_executor or not self.queue_view:
            return
        
        # Don't allow running if already running
        if self.batch_executor.is_running:
            print("[WARNING] Batch execution already in progress")
            return
        
        # Get replicates and duration from sweep builder
        replicates = 500
        duration = 100.0
        if hasattr(self.sweep_builder, 'replicates_entry'):
            try:
                replicates = int(self.sweep_builder.replicates_entry.get_text())
            except:
                pass
        if hasattr(self.sweep_builder, 'duration_entry'):
            try:
                duration = float(self.sweep_builder.duration_entry.get_text())
            except:
                pass
        
        # Clear pending updates tracking
        self._pending_updates.clear()
        
        # Clear old results from previous batch runs
        if self.results_browser:
            print("[DEBUG] Clearing old results from browser")
            self.results_browser.clear_results()
        
        # Update UI for running state
        self.queue_view.set_running(True)
        
        print(f"[DEBUG] Starting batch with {len(pending_experiments)} experiments")
        
        # Start batch execution
        try:
            self.batch_executor.run_batch(
                experiments=pending_experiments,
                replicates=replicates,
                duration=duration,
                progress_callback=self._on_experiment_progress,
                complete_callback=self._on_batch_complete,
                experiment_result_callback=self._on_experiment_result
            )
        except Exception as e:
            print(f"[ERROR] Failed to start batch: {e}")
            self.queue_view.set_running(False)
            self._show_error(f"Failed to start batch: {str(e)}")
    
    def _on_queue_cancel(self):
        """Handle queue cancel request."""
        if not self.batch_executor:
            return
        
        print("[DEBUG] Cancel requested by user")
        
        # Cancel the batch execution
        self.batch_executor.cancel()
        
        # Update UI immediately (completion callback will be called by executor)
        if self.queue_view:
            GLib.idle_add(lambda: self.queue_view.set_running(False) or False)
    
    def _on_queue_cleared(self):
        """Handle queue cleared event.
        
        When user clears completed experiments from queue, we should also
        clear the corresponding results from batch executor to free memory.
        """
        print("[DEBUG] Queue cleared by user")
        
        if self.batch_executor:
            # Clear all stored results
            self.batch_executor.clear_results()
        
        # Clear pending updates
        self._pending_updates.clear()
    
    def _on_experiment_progress(self, queue_index, status, progress):
        """Handle experiment progress update from background thread.
        
        Args:
            queue_index: Index in queue (row number)
            status: New status (running/completed/failed/cancelled)
            progress: Progress string (e.g., "50%", "100%", error message)
        """
        if not self.queue_view:
            print(f"[PROGRESS] Warning: No queue_view available for index {queue_index}")
            return
        
        # Determine criticality: completed/failed/cancelled are critical, running only at 0%
        is_terminal_status = status in ["completed", "failed", "cancelled"]
        is_running_start = status == "running" and progress == "0%"
        is_critical = is_terminal_status or is_running_start
        
        # Check if we already have an update pending/processing for this experiment
        already_scheduled = queue_index in self._pending_updates or queue_index in self._processing_updates
        
        # Store this update as pending (replaces any previous pending update)
        self._pending_updates[queue_index] = (status, progress)
        
        # If already scheduled, just update the value and return (coalescing)
        # Exception: critical updates always schedule immediately to ensure they're visible
        if already_scheduled and not is_critical:
            # The already-scheduled update will pick up this new value
            print(f"[PROGRESS] Coalescing update for experiment {queue_index}: {status} - {progress}")
            return
        
        print(f"[PROGRESS] Scheduling update for experiment {queue_index}: {status} - {progress} (critical={is_critical})")
        
        # Schedule UI update
        def update_ui():
            try:
                # Get the latest update for this experiment (may have changed since scheduling)
                if queue_index not in self._pending_updates:
                    return False  # Update was cancelled/processed
                
                s, p = self._pending_updates.pop(queue_index)
                self._processing_updates.add(queue_index)
                
                self.queue_view.update_experiment_status(queue_index, s, p)
            except Exception as e:
                print(f"[PROGRESS] ERROR: Failed to update experiment {queue_index} status: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Remove from processing
                self._processing_updates.discard(queue_index)
            return False  # Don't repeat
        
        # Use DEFAULT priority for critical updates, HIGH_IDLE for progress
        if is_critical:
            GLib.idle_add(update_ui, priority=GLib.PRIORITY_DEFAULT)
        else:
            GLib.idle_add(update_ui, priority=GLib.PRIORITY_HIGH_IDLE)
    
    def _on_experiment_result(self, name: str, result: dict):
        """Handle individual experiment result (called as each experiment completes).
        
        This allows incremental display of results without waiting for entire batch.
        Called from main thread via GLib.idle_add.
        
        Args:
            name: Experiment name
            result: Result dictionary with statistics
        """
        print(f"[RESULT] Adding result for '{name}' incrementally")
        
        if self.results_browser:
            try:
                self.results_browser.add_result(name, result)
                print(f"[RESULT] Successfully added '{name}' to results browser")
            except Exception as e:
                print(f"[RESULT] ERROR adding result for '{name}': {e}")
                import traceback
                traceback.print_exc()
    
    def _on_batch_complete(self, cancelled=False):
        """Handle batch execution completion.
        
        Args:
            cancelled: Whether batch was cancelled by user
        """
        if cancelled:
            print("[DEBUG] _on_batch_complete called (CANCELLED)")
        else:
            print("[DEBUG] _on_batch_complete called (COMPLETED)")
        
        # Use GLib.idle_add for ALL UI updates from background thread
        def complete_ui_updates():
            """Complete all UI updates in main thread."""
            print("[DEBUG] complete_ui_updates executing in main thread")
            try:
                # Stop the running state
                if self.queue_view:
                    print("[DEBUG] Calling set_running(False)")
                    self.queue_view.set_running(False)
                    print("[DEBUG] Queue view running state set to False")
                    
                    # Force status label update
                    print("[DEBUG] Forcing status label update")
                    self.queue_view._update_status_label()
                    print("[DEBUG] Status label updated")
                
                # NOTE: Results are now added incrementally via _on_experiment_result
                # No need to add them again here - just handle cancellation cleanup
                if cancelled:
                    # On cancellation, results may be incomplete - already handled incrementally
                    print("[DEBUG] Batch cancelled - incremental results already displayed")
                
                # Clear pending updates
                self._pending_updates.clear()
                self._processing_updates.clear()
                
                status_msg = "cancelled" if cancelled else "complete"
                print(f"[DEBUG] Batch execution {status_msg} - UI ready for next run")
                
            except Exception as e:
                print(f"[ERROR] Exception in complete_ui_updates: {e}")
                import traceback
                traceback.print_exc()
            
            print("[DEBUG] complete_ui_updates finished")
            return False  # Don't repeat
        
        # Schedule UI updates in main thread with DEFAULT priority
        # This ensures completion runs BEFORE any queued progress updates
        print("[DEBUG] Scheduling complete_ui_updates via GLib.idle_add")
        result = GLib.idle_add(complete_ui_updates, priority=GLib.PRIORITY_DEFAULT)
        print(f"[DEBUG] GLib.idle_add returned: {result}")
    
    def _on_export_results(self, name, result, format_type):
        """Handle export results request.
        
        Args:
            name: Experiment name
            result: Result dictionary
            format_type: 'csv' or 'json'
        """
        # Get parent window for dialog
        parent_window = None
        if self.parent_panel:
            parent_window = self.parent_panel.get_toplevel()
            if not isinstance(parent_window, Gtk.Window):
                parent_window = None
        
        # Show file chooser dialog (use transient_for instead of deprecated parent)
        dialog = Gtk.FileChooserDialog(
            title=f"Export {name} as {format_type.upper()}",
            transient_for=parent_window,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        # Set default filename
        safe_name = name.replace(' ', '_').replace('/', '_')
        dialog.set_current_name(f"{safe_name}.{format_type}")
        
        response = dialog.run()
        filepath = dialog.get_filename()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and filepath:
            try:
                if format_type == 'csv':
                    self._export_csv(filepath, name, result)
                elif format_type == 'json':
                    self._export_json(filepath, name, result)
                
                # Show success message
                if hasattr(self.results_browser, 'stats_label'):
                    self.results_browser.stats_label.set_markup(
                        f"<span foreground='green'>✓ Exported to {filepath}</span>"
                    )
            except Exception as e:
                self._show_error(f"Export failed: {str(e)}")
    
    def _export_csv(self, filepath, name, result):
        """Export results to CSV.
        
        Args:
            filepath: Output file path
            name: Experiment name
            result: Result dictionary with statistics and trajectory summary
        """
        import csv
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write metadata header
            writer.writerow(['Experiment', name])
            stats = result.get('statistics', {})
            writer.writerow(['N_Replicates', stats.get('n_replicates', 0)])
            writer.writerow(['Elapsed_Time', stats.get('elapsed_time', 0.0)])
            writer.writerow(['Snapshot_Index', result.get('snapshot_index', '')])
            writer.writerow([])
            
            # Write species statistics (mean trajectories)
            writer.writerow(['Species Statistics - Mean Trajectories'])
            time_points = stats.get('time_points', [])
            species_stats = stats.get('species_statistics', {})
            
            if time_points and species_stats:
                # Header row: Time, Species1, Species2, ...
                header = ['Time'] + list(species_stats.keys())
                writer.writerow(header)
                
                # Data rows: time_point, mean_species1, mean_species2, ...
                for i, t in enumerate(time_points):
                    row = [t]
                    for species_id, species_data in species_stats.items():
                        mean = species_data.get('mean', [])
                        row.append(mean[i] if i < len(mean) else '')
                    writer.writerow(row)
                
                writer.writerow([])
                
                # Write standard deviations
                writer.writerow(['Species Statistics - Standard Deviations'])
                writer.writerow(header)
                for i, t in enumerate(time_points):
                    row = [t]
                    for species_id, species_data in species_stats.items():
                        std = species_data.get('std', [])
                        row.append(std[i] if i < len(std) else '')
                    writer.writerow(row)
            
            # Write trajectory summary
            writer.writerow([])
            writer.writerow(['Trajectory Summary'])
            writer.writerow(['Replicate_ID', 'Seed', 'N_TimePoints', 'Final_Time'])
            
            trajectory_summary = result.get('trajectory_summary', [])
            for traj in trajectory_summary:
                writer.writerow([
                    traj.get('replicate_id', ''),
                    traj.get('seed', ''),
                    traj.get('n_timepoints', ''),
                    traj.get('final_time', '')
                ])
            
            # Add summary statistics at the end
            writer.writerow([])
            writer.writerow(['Summary'])
            writer.writerow(['Total Replicates', stats.get('n_replicates', 0)])
            writer.writerow(['Execution Time (s)', result.get('duration', 0.0)])
    
    def _export_json(self, filepath, name, result):
        """Export results to JSON.
        
        Args:
            filepath: Output file path
            name: Experiment name
            result: Result dictionary with full experiment data
        """
        import json
        from datetime import datetime
        
        # Prepare comprehensive export data
        export_data = {
            'experiment_name': name,
            'export_timestamp': datetime.now().isoformat(),
            'snapshot_index': result.get('snapshot_index'),
            'statistics': result.get('statistics', {}),
            'execution_time_seconds': result.get('duration', 0.0),
            'n_replicates': result.get('n_replicates', 0),
            'trajectory_summary': result.get('trajectory_summary', [])
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def _on_add_to_report(self, name, result):
        """Handle add to report request.
        
        Args:
            name: Experiment name
            result: Result dictionary with trajectories and statistics
        """
        # Try to access report panel through overlay manager structure
        report_panel = None
        
        if self.parent_panel:
            # Get the drawing_area from parent panel
            drawing_area = getattr(self.parent_panel, 'drawing_area', None)
            
            if drawing_area:
                # Navigate up to find model_canvas_loader
                main_window = self.parent_panel.get_toplevel()
                model_canvas_loader = None
                
                # Look for model_canvas_loader in main window children
                if hasattr(main_window, 'model_canvas_loader'):
                    model_canvas_loader = main_window.model_canvas_loader
                
                # Access report panel through overlay_manager (per-document instance)
                if model_canvas_loader and hasattr(model_canvas_loader, 'overlay_managers'):
                    overlay_manager = model_canvas_loader.overlay_managers.get(drawing_area)
                    if overlay_manager and hasattr(overlay_manager, 'report_panel_loader'):
                        report_loader = overlay_manager.report_panel_loader
                        if report_loader and hasattr(report_loader, 'panel'):
                            report_panel = report_loader.panel
        
        if report_panel:
            # Find the DynamicAnalysesCategory in report panel
            dynamic_category = None
            if hasattr(report_panel, 'categories'):
                for category in report_panel.categories:
                    if category.__class__.__name__ == 'DynamicAnalysesCategory':
                        dynamic_category = category
                        break
            
            if dynamic_category and hasattr(dynamic_category, 'add_experiment_result'):
                # Add the experiment result
                dynamic_category.add_experiment_result(name, result)
                
                # Show success feedback
                if hasattr(self.results_browser, 'stats_label'):
                    self.results_browser.stats_label.set_markup(
                        f"<span foreground='green'>✓ Added '{name}' to Report panel</span>"
                    )
                
                # Expand the category to show the new data
                if hasattr(dynamic_category, 'category_frame') and hasattr(dynamic_category.category_frame, 'set_expanded'):
                    dynamic_category.category_frame.set_expanded(True)
                
                # Switch to Report panel to show the user where the data was added
                if model_canvas_loader and hasattr(model_canvas_loader, 'left_dock_stack'):
                    left_dock_stack = model_canvas_loader.left_dock_stack
                    if left_dock_stack:
                        # Make stack visible and switch to report panel
                        left_dock_stack.set_visible(True)
                        left_dock_stack.set_visible_child_name('report')
                        
                        # Also set the master palette button active if available
                        main_window = self.parent_panel.get_toplevel()
                        if hasattr(main_window, 'master_palette'):
                            main_window.master_palette.set_active('report', True)
            else:
                self._show_error("Could not find Dynamic Analyses category in Report panel")
        else:
            self._show_error("Report panel not available. Please ensure a document is loaded.")
    
    def _show_error(self, message):
        """Show error message in UI.
        
        Args:
            message: Error message to display
        """
        if hasattr(self.sweep_builder, 'preview_label'):
            self.sweep_builder.preview_label.set_markup(
                f"<span foreground='red'>Error: {message}</span>"
            )
    
    def get_widget(self):
        """Get the category widget for packing into parent panel.
        
        Returns:
            Gtk.Widget: The category frame widget (self.category_frame)
        """
        return self.category_frame
    
    def set_parent_panel(self, panel):
        """Set reference to parent ViabilityPanel.
        
        Args:
            panel: Parent ViabilityPanel instance
        """
        self.parent_panel = panel
        
        # Update batch executor's parent panel reference
        if self.batch_executor:
            self.batch_executor.parent_panel = panel
        
        # Refresh parameters now that parent is available
        self.refresh_parameters()
    
    def set_model_canvas(self, model_canvas):
        """Update model canvas reference.
        
        Args:
            model_canvas: New ModelCanvas instance
        """
        self.model_canvas = model_canvas
    
    def set_experiment_manager(self, experiment_manager):
        """Update experiment manager reference.
        
        Args:
            experiment_manager: ExperimentManager instance
        """
        self.experiment_manager = experiment_manager
    
    def refresh(self):
        """Refresh category content (currently no-op in Phase 1)."""
        pass
    
    def cleanup(self):
        """Clean up resources when category is destroyed."""
        # Phase 1: Nothing to clean up yet
        # Phase 3+: Will stop any running batch executions
        pass
    
    # ========================================================================
    # PHASE 2+ METHODS (To be implemented)
    # ========================================================================
    
    def _build_parameter_sweep_section(self):
        """Build parameter sweep configuration UI (Phase 2)."""
        # TODO: Implement in Phase 2
        pass
    
    def _build_queue_section(self):
        """Build experiment queue management UI (Phase 3)."""
        # TODO: Implement in Phase 3
        pass
    
    def _build_results_section(self):
        """Build results browser UI (Phase 4)."""
        # TODO: Implement in Phase 4
        pass
    
    def generate_parameter_sweep(self, parameter_name, values):
        """Generate experiment snapshots for parameter sweep (Phase 2).
        
        Args:
            parameter_name: Parameter to vary (e.g., 'T1.rate')
            values: List of values to test
        """
        # TODO: Implement in Phase 2
        pass
    
    def run_batch_experiments(self, experiments, n_replicates=500):
        """Execute batch experiments with progress tracking (Phase 3).
        
        Args:
            experiments: List of ExperimentSnapshot instances
            n_replicates: Number of replicates per experiment
        """
        # TODO: Implement in Phase 3
        pass
    
    def export_results(self, format='csv'):
        """Export completed experiment results (Phase 4).
        
        Args:
            format: Export format ('csv', 'json', 'report')
        """
        # TODO: Implement in Phase 4
        pass
