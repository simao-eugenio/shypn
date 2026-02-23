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
import os
import json
from datetime import datetime
from pathlib import Path

from shypn.ui.category_frame import CategoryFrame
from shypn.data.project_models import get_project_manager
from shypn.helpers.batch_results_saver import BatchResultsSaver


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
        self._idle_handler_active = False  # Flag to ensure only one idle handler runs at a time
        
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
        self.sweep_builder.viability_panel = self.parent_panel  # Set reference for auto-prediction
        self.sweep_builder.parent_category = self  # Set reference for refresh callback
        self.sweep_builder.set_generate_callback(self._on_sweep_generate)
        self.sweep_builder.set_clear_callback(lambda: self.queue_view.clear_queue())
        
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
        self.queue_view.set_pause_callback(self._on_queue_pause)  # Stage 3
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
        model = None
        if self.parent_panel:
            model = self.parent_panel._get_current_model()
        self.results_browser = ResultsBrowserView(model=model)
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
        
        # Both single and factorial modes use the selected parameter type
        # This allows users to filter by transitions/places/arcs in both modes
        param_type = self.sweep_builder.type_combo.get_active_id()
        params = []
        
        if param_type == 'transitions':
            # Get from transitions_store (TreeView data)
            if hasattr(self.parent_panel, 'transitions_store'):
                store = self.parent_panel.transitions_store
                iter = store.get_iter_first()
                while iter:
                    # Column 0 = ID (internal), Column 1 = Name (display)
                    transition_id = store.get_value(iter, 0)
                    transition_name = store.get_value(iter, 1)
                    # Column 4 = transition type (immediate, stochastic, continuous, adaptive, timed)
                    try:
                        transition_type = store.get_value(iter, 4)
                    except (ValueError, TypeError) as e:
                        # Transition type column not available
                        import logging
                        logging.getLogger(__name__).debug(f"Transition type read failed: {e}")
                        transition_type = 'stochastic'  # Fallback
                    
                    if transition_id and transition_name:
                        # Add rate property for all transitions
                        params.append((f"{transition_name} (Rate)", f"{transition_id}.rate"))
                        
                        # Add volume_threshold property only for adaptive transitions
                        if transition_type == 'adaptive':
                            params.append((f"{transition_name} (Volume Threshold)", f"{transition_id}.volume_threshold"))
                    
                    iter = store.iter_next(iter)
        
        elif param_type == 'places':
            # Get from places_store
            if hasattr(self.parent_panel, 'places_store'):
                store = self.parent_panel.places_store
                iter = store.get_iter_first()
                while iter:
                    # Column 0 = ID (internal), Column 1 = Name (display)
                    place_id = store.get_value(iter, 0)
                    place_name = store.get_value(iter, 1)
                    if place_id and place_name:
                        # Places: Only initial_marking property
                        params.append((f"{place_name}", f"{place_id}.initial_marking"))
                    iter = store.iter_next(iter)
        
        elif param_type == 'arcs':
            # Get from arcs_store
            if hasattr(self.parent_panel, 'arcs_store'):
                store = self.parent_panel.arcs_store
                iter = store.get_iter_first()
                while iter:
                    # Column 0 = arc ID, Columns 1,2 = source/target IDs
                    arc_id = store.get_value(iter, 0)
                    source_id = store.get_value(iter, 1)
                    target_id = store.get_value(iter, 2)
                    # Column 6 = arc_type (normal, inhibitor, test)
                    try:
                        arc_type = store.get_value(iter, 6)
                    except (ValueError, TypeError) as e:
                        # Arc type column not available
                        import logging
                        logging.getLogger(__name__).debug(f"Arc type read failed: {e}")
                        arc_type = 'normal'
                    
                    # Construct display name from source/target names (lookup if needed)
                    # For now, use IDs for arcs since they don't have independent names
                    if arc_id:
                        arc_name = f"{source_id}→{target_id}"
                        
                        # Arc properties: weight (always), threshold (if inhibitor/test)
                        params.append((f"{arc_name} (Weight)", f"{arc_id}.weight"))
                        
                        if arc_type in ['inhibitor', 'test']:
                            params.append((f"{arc_name} (Threshold)", f"{arc_id}.threshold"))
                    
                    iter = store.iter_next(iter)
        
        # Update sweep builder with actual parameters (name/ID pairs)
        # This works for both single and factorial design modes
        if params:
            self.sweep_builder.set_available_parameters(param_type, params)
        else:
            # Show helpful message if no subnet loaded
            self.sweep_builder.set_available_parameters(param_type, [])
            if hasattr(self.sweep_builder, 'name_combo'):
                self.sweep_builder.name_combo.append("none", "(Load subnet via right-click transition)")
                self.sweep_builder.name_combo.set_active(0)
    
    def _on_sweep_generate(self, config):
        """Handle parameter sweep generation (single or factorial).
        
        Args:
            config: Dictionary with sweep configuration.
                
                Single-parameter sweep:
                    - parameter_type: 'places', 'transitions', 'arcs'
                    - parameter_name: Name of parameter to vary
                    - values: List of values to test
                    - replicates: Number of replicates per experiment
                    - duration: Simulation duration
                
                Factorial design:
                    - design_type: 'factorial'
                    - parameters: List of parameter dicts with name, type, id, values
                    - combinations: List of tuples (value1, value2, ...)
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
        
        # CRITICAL FIX: Refresh subnet parameters from current model before generating experiments
        # This ensures TreeViews reflect any parameter changes made in the main canvas
        # since localities were first added. Without this, experiments use stale parameter values.
        if self.parent_panel and hasattr(self.parent_panel, '_refresh_subnet_parameters'):
            self.parent_panel._refresh_subnet_parameters()
        
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
            
            # Check design type
            if config.get('design_type') == 'factorial':
                # Handle factorial design
                count = self._generate_factorial_snapshots(config, base_snapshot)
            else:
                # Handle single-parameter sweep
                count = self.experiment_manager.generate_sweep_snapshots(
                    parameter_type=config['parameter_type'],
                    parameter_id=config.get('parameter_id', config['parameter_name']),  # Use ID if available
                    parameter_name=config['parameter_name'],  # Display name
                    values=config['values'],
                    base_snapshot=base_snapshot
                )
                
                # Update visual indicators in parameter tables (single-param only)
                if self.parent_panel and hasattr(self.parent_panel, 'update_sweep_indicators') and count > 0:
                    self.parent_panel.update_sweep_indicators(
                        config['parameter_type'],
                        config.get('parameter_id', config['parameter_name'])
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
    
    def _generate_factorial_snapshots(self, config, base_snapshot):
        """Generate experiment snapshots for factorial design.
        
        Args:
            config: Factorial design configuration with parameters and combinations
            base_snapshot: Base snapshot to clone for each experiment
            
        Returns:
            int: Number of snapshots created
        """
        parameters = config['parameters']
        combinations = config['combinations']
        
        count = 0
        for combo in combinations:
            # Build descriptive name from combination values
            name_parts = []
            for i, param in enumerate(parameters):
                value = combo[i]
                # Format value nicely
                if isinstance(value, float):
                    if value.is_integer():
                        value_str = str(int(value))
                    else:
                        value_str = f"{value:.2f}"
                else:
                    value_str = str(value)
                name_parts.append(f"{param['name']}={value_str}")
            
            snapshot_name = "_".join(name_parts)
            
            # Create new snapshot by cloning baseline
            snapshot = self.experiment_manager.add_snapshot(snapshot_name)
            # Copy values from base snapshot
            snapshot.place_markings = base_snapshot.place_markings.copy()
            snapshot.arc_weights = base_snapshot.arc_weights.copy()
            snapshot.transition_rates = base_snapshot.transition_rates.copy()
            snapshot.notes = base_snapshot.notes
            
            # Apply parameter modifications for this combination
            for i, param in enumerate(parameters):
                param_type = param['type']
                param_id = param['id']
                value = combo[i]
                
                # Update the appropriate parameter storage
                if param_type == 'places':
                    snapshot.place_markings[param_id] = value
                elif param_type == 'transitions':
                    snapshot.transition_rates[param_id] = value
                elif param_type == 'arcs':
                    snapshot.arc_weights[param_id] = value
            
            count += 1
        
        return count
    
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
        replicates = 3
        duration = 60.0
        termination_condition = "deadlock"  # Default
        
        if hasattr(self.sweep_builder, 'replicates_entry'):
            try:
                text = self.sweep_builder.replicates_entry.get_text().strip()
                if text:
                    replicates = int(text)
            except Exception as e:
                print(f"[WARNING] Failed to read replicates: {e}, using default: {replicates}")
        
        if hasattr(self.sweep_builder, 'duration_entry'):
            try:
                text = self.sweep_builder.duration_entry.get_text().strip()
                if text:
                    duration = float(text)
                    if duration <= 0:
                        print(f"[WARNING] Duration is {duration}s, using default 60.0s")
                        duration = 60.0
            except Exception as e:
                print(f"[WARNING] Failed to read duration: {e}, using default: {duration}s")
        
        if hasattr(self.sweep_builder, 'termination_combo'):
            try:
                termination_condition = self.sweep_builder.termination_combo.get_active_id() or "deadlock"
            except Exception as e:
                print(f"[WARNING] Failed to read termination condition: {e}, using default")
                pass
        
        # Get parallel execution setting from queue view checkbox (E2 enhancement)
        use_parallel = False
        if hasattr(self.queue_view, 'parallel_checkbox'):
            use_parallel = self.queue_view.parallel_checkbox.get_active()
        
        # Calculate expected timeout based on execution mode and replicate count
        # Sequential: 0.827s per simulated second (3×60s = 148.9s measurement)
        # Parallel: 2.41s per simulated second (1×60s = 144.762s measurement)
        #   - Parallel overhead: process creation, serialization, resource contention
        # 
        # IMPORTANT: Replicates run SEQUENTIALLY within each experiment (even in parallel batch mode)
        # to avoid ThreadPoolExecutor deadlocks in forked processes.
        # 
        # Timeout calculation:
        #   base_time = replicates × duration × empirical_factor
        #   safety_margin = 1.5x (accounts for system variations without being excessive)
        #   max_cap = 36 hours (allows very long experiments with many replicates)
        empirical_factor = 2.41 if use_parallel else 0.827
        base_timeout = replicates * duration * empirical_factor
        safety_timeout = base_timeout * 1.5  # 1.5x safety margin
        max_cap = 36 * 3600  # Maximum 36 hours
        expected_timeout = min(safety_timeout, max_cap)
        
        # Clear pending updates tracking
        self._pending_updates.clear()
        
        # Clear old results from previous batch runs
        if self.results_browser:
            self.results_browser.clear_results()
        
        # Clear batch executor results to ensure clean state
        if self.batch_executor:
            self.batch_executor.clear_results()
        
        # Update UI for running state
        self.queue_view.set_running(True)
        
        # Start batch execution with parallel option
        try:
            self.batch_executor.run_batch(
                experiments=pending_experiments,
                replicates=replicates,
                duration=duration,
                termination_condition=termination_condition,
                progress_callback=self._on_experiment_progress,
                complete_callback=self._on_batch_complete,
                experiment_result_callback=self._on_experiment_result,
                use_parallel=use_parallel  # E2: Enable parallel execution if checkbox is checked
            )
        except Exception as e:
            print(f"[ERROR] Failed to start batch: {e}")
            import traceback
            traceback.print_exc()
            self.queue_view.set_running(False)
            
            # Show detailed error to user
            error_msg = str(e)
            if "No subnet model" in error_msg:
                error_msg = ("No subnet loaded.\n\n"
                           "Please:\n"
                           "1. Right-click a transition in the model canvas\n"
                           "2. Select 'Add to Viability Analysis'\n"
                           "3. Verify the subnet appears in the Viability panel\n"
                           "4. Then generate and run experiments")
            
            self._show_error(f"Cannot start simulation:\n\n{error_msg}")
    
    def _on_queue_cancel(self):
        """Handle queue cancel request."""
        if not self.batch_executor:
            return
        
        # Cancel the batch execution
        self.batch_executor.cancel()
        
        # Update UI immediately (completion callback will be called by executor)
        if self.queue_view:
            GLib.idle_add(lambda: self.queue_view.set_running(False) or False)
    
    def _on_queue_pause(self, should_pause):
        """Handle queue pause/resume request (Stage 3).
        
        Args:
            should_pause: True to pause, False to resume
        """
        if not self.batch_executor:
            return
        
        # Toggle paused state
        self.batch_executor.set_paused(should_pause)
        
        # Update UI to reflect paused state
        if self.queue_view:
            GLib.idle_add(lambda: self.queue_view.set_running(
                is_running=True, 
                is_paused=should_pause
            ) or False)
    
    def _on_queue_cleared(self):
        """Handle queue cleared event.
        
        When user clears completed experiments from queue, we should also
        clear the corresponding results from batch executor to free memory.
        """
        
        if self.batch_executor:
            # Clear all stored results
            self.batch_executor.clear_results()
        
        # Clear pending updates
        self._pending_updates.clear()
    
    def _on_experiment_progress(self, queue_index, status, progress):
        """Handle experiment progress update from background thread.
        
        Uses a single idle handler to batch all UI updates safely.
        
        Args:
            queue_index: Index in queue (row number)
            status: New status (running/completed/failed/cancelled)
            progress: Progress string (e.g., "50%", "100%", error message)
        """
        if not self.queue_view:
            print(f"[PROGRESS] Warning: No queue_view available for index {queue_index}")
            return
        
        # Store this update as pending (replaces any previous pending update for same experiment)
        self._pending_updates[queue_index] = (status, progress)
        
        # If idle handler already running, it will pick up this update
        if self._idle_handler_active:
            return
        
        # Schedule a single idle handler to process ALL pending updates
        self._idle_handler_active = True
        
        def process_all_updates():
            """Process all pending updates in a single GTK main loop iteration."""
            try:
                # Process all pending updates (snapshot and clear)
                updates_to_process = list(self._pending_updates.items())
                self._pending_updates.clear()
                
                for idx, (s, p) in updates_to_process:
                    try:
                        self.queue_view.update_experiment_status(idx, s, p)
                    except Exception as e:
                        print(f"[PROGRESS] ERROR: Failed to update experiment {idx}: {e}")
                        import traceback
                        traceback.print_exc()
            finally:
                # Reset flag to allow next batch
                self._idle_handler_active = False
            
            return False  # Don't repeat
        
        # Schedule with HIGH_IDLE priority to not block user interactions
        GLib.idle_add(process_all_updates, priority=GLib.PRIORITY_HIGH_IDLE)
    
    def _on_experiment_result(self, name: str, result: dict):
        """Handle individual experiment result (called as each experiment completes).
        
        PHASE 3: Now includes auto-save functionality for experiment reproducibility.
        Saves to: {project}/experiments/results/experiment_{name}_{timestamp}/
        
        This allows incremental display of results without waiting for entire batch.
        Called from main thread via GLib.idle_add.
        
        Args:
            name: Experiment name
            result: Result dictionary with statistics
        """
        
        # Add to results browser (existing functionality)
        if self.results_browser:
            try:
                self.results_browser.add_result(name, result)
            except Exception as e:
                print(f"[ERROR] Failed to add result for '{name}': {e}")
                import traceback
                traceback.print_exc()
        
        # NEW: Auto-save experiment results (Phase 3 normalization)
        try:
            self._auto_save_experiment(name, result)
        except Exception as e:
            print(f"[WARNING] Failed to auto-save experiment '{name}': {e}")
            import traceback
            traceback.print_exc()
    
    def _auto_save_experiment(self, name: str, result: dict):
        """Auto-save experiment results to disk (Phase 3 normalization).
        
        Saves to: {project}/experiments/results/experiment_{name}_{timestamp}/
        
        Creates:
        - config.json: Experiment configuration and metadata
        - statistics.json: Statistical summaries across replicates
        - replicates.json: Per-replicate data (if available)
        - metadata.txt: Human-readable metadata header
        
        Args:
            name: Experiment name
            result: Result dictionary with statistics and metadata
        """
        # Determine project folder
        project_folder = self._get_project_folder()
        if not project_folder:
            print(f"[AUTO-SAVE] Warning: No project folder detected, skipping auto-save for '{name}'")
            return
        
        # Create saver with experiments/results subfolder
        saver = BatchResultsSaver(
            base_path=project_folder,
            subfolder='experiments/results',
            batch_prefix='experiment'
        )
        
        # Create timestamped folder
        safe_name = name.replace(' ', '_').replace('/', '_')
        batch_path = saver.create_batch_folder(name_suffix=safe_name)
        
        # Save configuration
        config = {
            'timestamp': saver.timestamp,
            'experiment_name': name,
            'snapshot_index': result.get('snapshot_index'),
            'n_replicates': result.get('n_replicates', 0),
            'duration': result.get('duration', 0),
            'swept_parameter': result.get('swept_parameter'),
            'subnet_structure': result.get('subnet_structure')
        }
        
        config_path = batch_path / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Save statistics
        statistics = result.get('statistics', {})
        stats_path = batch_path / 'statistics.json'
        with open(stats_path, 'w') as f:
            json.dump(statistics, f, indent=2)
        
        # Save per-replicate data if available
        replicate_data = result.get('replicate_data', [])
        if replicate_data:
            replicates_path = batch_path / 'replicates.json'
            with open(replicates_path, 'w') as f:
                json.dump(replicate_data, f, indent=2)
        
        # Save trajectory summary
        trajectory_summary = result.get('trajectory_summary', [])
        if trajectory_summary:
            summary_path = batch_path / 'trajectory_summary.json'
            with open(summary_path, 'w') as f:
                json.dump(trajectory_summary, f, indent=2)
        
        # Save metadata header if available
        metadata = result.get('metadata')
        if metadata:
            try:
                # Convert metadata header to text
                if hasattr(metadata, 'to_header_text'):
                    header_text = metadata.to_header_text()
                elif hasattr(metadata, 'sections'):
                    # Manual conversion from sections
                    lines = []
                    lines.append("# " + "="*76)
                    lines.append("# SHYPN EXPERIMENT METADATA")
                    lines.append(f"# Generated: {datetime.now().isoformat()}Z")
                    lines.append("# " + "="*76)
                    lines.append("#")
                    for section in metadata.sections:
                        lines.append(f"# [{section.name}]")
                        for key, value in section.data.items():
                            lines.append(f"# {key}: {value}")
                        lines.append("#")
                    header_text = "\n".join(lines)
                else:
                    header_text = f"# Metadata: {str(metadata)}\n"
                
                metadata_path = batch_path / 'metadata.txt'
                with open(metadata_path, 'w') as f:
                    f.write(header_text)
            except Exception as e:
                print(f"[AUTO-SAVE] Warning: Failed to save metadata: {e}")
    
    def _get_project_folder(self) -> str:
        """Get current project folder path for auto-save.
        
        Uses event-driven architecture: parent_panel.model is updated via
        document.focused events, avoiding tight coupling with model_canvas.
        
        Returns:
            Project folder path, or None if not in a project
         """
        # Try to get from project manager
        project_manager = get_project_manager()
        if project_manager.current_project:
            return project_manager.current_project.base_path
        
        # Try to get from parent panel's model (updated via EventBus)
        if self.parent_panel and hasattr(self.parent_panel, 'model'):
            model = self.parent_panel.model
            if model and hasattr(model, 'filepath') and model.filepath:
                # Extract project folder from model path
                model_path = Path(model.filepath)
                # Look for 'projects' folder in path
                parts = model_path.parts
                if 'projects' in parts:
                    projects_idx = parts.index('projects')
                    if projects_idx + 1 < len(parts):
                        # Return path up to and including project name
                        return str(Path(*parts[:projects_idx + 2]))
        
        return None
    
    def _on_batch_complete(self, cancelled=False):
        """Handle batch execution completion.
        
        Args:
            cancelled: Whether batch was cancelled by user
        """
        
        # Use GLib.idle_add for ALL UI updates from background thread
        def complete_ui_updates():
            """Complete all UI updates in main thread."""
            try:
                # Stop the running state
                if self.queue_view:
                    self.queue_view.set_running(False)
                    
                    # Force status label update
                    self.queue_view._update_status_label()
                
                # NOTE: Results are now added incrementally via _on_experiment_result
                # No need to add them again here - just handle cancellation cleanup
                if cancelled:
                    # On cancellation, results may be incomplete - already handled incrementally
                    pass
                
                # Clear pending updates
                self._pending_updates.clear()
                self._processing_updates.clear()
                
                status_msg = "cancelled" if cancelled else "completed"
                
            except Exception as e:
                print(f"[ERROR] Exception in complete_ui_updates: {e}")
                import traceback
                traceback.print_exc()
            
            return False  # Don't repeat
        
        # Schedule UI updates in main thread with DEFAULT priority
        # This ensures completion runs BEFORE any queued progress updates
        GLib.idle_add(complete_ui_updates, priority=GLib.PRIORITY_DEFAULT)
    
    def _on_export_results(self, name, result, format_type):
        """Handle export results request - supports single and batch export.
        
        Args:
            name: Experiment name
            result: Result dictionary
            format_type: 'csv', 'json', 'csv_batch', or 'json_batch'
        """
        # Check if this is a batch export
        is_batch = format_type.endswith('_batch')
        
        if is_batch:
            # Batch export - use pre-selected directory from result
            directory = result.get('_batch_export_dir')
            batch_name = result.get('_batch_export_name', name)
            
            if directory:
                # Generate safe filename
                safe_name = batch_name.replace(' ', '_').replace('/', '_').replace('=', '_')
                base_format = format_type.replace('_batch', '')
                filepath = f"{directory}/{safe_name}.{base_format}"
                
                try:
                    if base_format == 'csv':
                        self._export_csv(filepath, batch_name, result)
                    elif base_format == 'json':
                        self._export_json(filepath, batch_name, result)
                except Exception as e:
                    print(f"Batch export error for {batch_name}: {e}")
            return
        
        # Single export - show file chooser dialog
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
        
        # Set initial directory to project experiments folder if project is open
        project_manager = get_project_manager()
        if project_manager.current_project:
            experiments_dir = os.path.join(project_manager.current_project.base_path, 'experiments')
            if not os.path.exists(experiments_dir):
                try:
                    os.makedirs(experiments_dir, exist_ok=True)
                except (OSError, PermissionError) as e:
                    self.logger.debug(f"Failed to create experiments directory {experiments_dir}: {e}")
            if os.path.isdir(experiments_dir):
                dialog.set_current_folder(experiments_dir)
            else:
                dialog.set_current_folder(project_manager.current_project.base_path)
        
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
        
        # Update sweep builder's viability panel reference for auto-prediction
        if self.sweep_builder:
            self.sweep_builder.viability_panel = panel
        
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
