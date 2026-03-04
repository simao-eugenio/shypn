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
        
        # Per-run isolation: one folder created at batch start, shared by all experiments in the run
        self._current_run_folder = None  # Path | None

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
            
            # Apply parameter modifications for this combination.
            # All parameters are expressed as object.property paths and routed
            # through property_overrides so apply_property_to_object resolves
            # them uniformly.  Bare IDs (no dot) are also valid: the parser
            # defaults them to their canonical property (initial_marking for
            # places, rate for transitions, weight for arcs).
            for i, param in enumerate(parameters):
                param_id = param['id']
                value = combo[i]
                snapshot.property_overrides[param_id] = value
            
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

        # Read precision settings from sweep builder
        # Note: use_tau_leaping is always True — SimulationSettings.use_tau_leaping setter is a no-op
        use_tau_leaping = True
        tau_epsilon = 0.03
        dt_manual = None

        if hasattr(self.sweep_builder, 'sweep_tau_epsilon_entry'):
            try:
                text = self.sweep_builder.sweep_tau_epsilon_entry.get_text().strip()
                if text:
                    val = float(text)
                    if 0 < val <= 1:
                        tau_epsilon = val
            except Exception as e:
                print(f"[WARNING] Failed to read tau_epsilon: {e}, using default {tau_epsilon}")

        if (hasattr(self.sweep_builder, 'sweep_dt_manual_radio') and
                hasattr(self.sweep_builder, 'sweep_dt_manual_entry') and
                self.sweep_builder.sweep_dt_manual_radio.get_active()):
            try:
                text = self.sweep_builder.sweep_dt_manual_entry.get_text().strip()
                if text:
                    val = float(text)
                    if val > 0:
                        dt_manual = val
            except Exception as e:
                print(f"[WARNING] Failed to read dt_manual: {e}, using auto")

        max_tau = 0.1
        if hasattr(self.sweep_builder, 'sweep_max_tau_entry'):
            try:
                text = self.sweep_builder.sweep_max_tau_entry.get_text().strip()
                if text:
                    val = float(text)
                    if 0 < val <= 100:
                        max_tau = val
            except Exception as e:
                print(f"[WARNING] Failed to read max_tau: {e}, using default {max_tau}")

        seed_base = 42
        if hasattr(self.sweep_builder, 'sweep_seed_entry'):
            try:
                text = self.sweep_builder.sweep_seed_entry.get_text().strip()
                if text:
                    seed_base = int(text)
            except Exception as e:
                print(f"[WARNING] Failed to read seed_base: {e}, using default {seed_base}")

        compressor_epsilon = 0.02
        if hasattr(self.sweep_builder, 'sweep_compressor_epsilon_entry'):
            try:
                text = self.sweep_builder.sweep_compressor_epsilon_entry.get_text().strip()
                if text:
                    val = float(text)
                    if 0 < val < 1:
                        compressor_epsilon = val
            except Exception as e:
                print(f"[WARNING] Failed to read compressor_epsilon: {e}, using default {compressor_epsilon}")

        compressor_min_gap = 0.0
        if hasattr(self.sweep_builder, 'sweep_compressor_min_gap_entry'):
            try:
                text = self.sweep_builder.sweep_compressor_min_gap_entry.get_text().strip()
                if text:
                    val = float(text)
                    if val >= 0:
                        compressor_min_gap = val
            except Exception as e:
                print(f"[WARNING] Failed to read compressor_min_gap: {e}, using default {compressor_min_gap}")

        compressor_max_gap = 300.0
        if hasattr(self.sweep_builder, 'sweep_compressor_max_gap_entry'):
            try:
                text = self.sweep_builder.sweep_compressor_max_gap_entry.get_text().strip()
                if text:
                    val = float(text)
                    if val > 0:
                        compressor_max_gap = val
            except Exception as e:
                print(f"[WARNING] Failed to read compressor_max_gap: {e}, using default {compressor_max_gap}")

        # Get parallel execution setting from queue view checkbox (E2 enhancement)
        use_parallel = False
        if hasattr(self.queue_view, 'parallel_checkbox'):
            use_parallel = self.queue_view.parallel_checkbox.get_active()
        
        # Zombie-detection threshold is computed by the batch executor itself
        # from the simulation duration. No computation estimate is needed here.
        
        # Clear pending updates tracking
        self._pending_updates.clear()

        # Create per-run folder — all experiments in this batch live inside it
        self._current_run_folder = None
        _run_project = self._get_project_folder()
        if _run_project:
            from pathlib import Path as _Path
            from datetime import datetime as _dt
            _run_ts = _dt.now().strftime("%Y%m%d_%H%M%S")
            _run_path = _Path(_run_project) / 'experiments' / 'results' / f'run_{_run_ts}'
            _run_path.mkdir(parents=True, exist_ok=True)
            self._current_run_folder = _run_path

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
                use_parallel=use_parallel,  # E2: Enable parallel execution if checkbox is checked
                use_tau_leaping=use_tau_leaping,
                tau_epsilon=tau_epsilon,
                max_tau=max_tau,
                dt_manual=dt_manual,
                seed_base=seed_base,
                compressor_epsilon=compressor_epsilon,
                compressor_min_gap=compressor_min_gap,
                compressor_max_gap=compressor_max_gap,
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
        """Auto-save experiment results to disk — all CSV format for easy analysis.

        Saves to: {project}/experiments/results/experiment_{name}_{timestamp}/

        Creates:
        - results.csv          : Mean + std trajectories per species over time
                                 NOTE: mixed-format (section headers + matrices) —
                                 parse with comment='#' + section-aware reader.
        - replicates.csv       : Per-replicate outcomes — standard tabular CSV.
        - config.csv           : Experiment metadata as key-value pairs.
        - names.csv            : ID → human-readable name mapping (P17 = GATA1_Protein_nuc).
        - mean_final_state.csv : Final-timepoint mean ± std per species — standard
                                 tabular CSV, directly loadable with pandas.read_csv().
        - .complete            : Zero-byte sentinel written ONLY after all files succeed.
                                 Absence means the save is partial/interrupted.

        Args:
            name: Experiment name
            result: Result dictionary with statistics and metadata
        """
        import csv as csv_mod
        import os as _os

        def _fsync(path):
            """Flush OS buffers for path to guarantee data is on disk."""
            try:
                with open(path, 'a') as fh:
                    fh.flush()
                    _os.fsync(fh.fileno())
            except OSError:
                pass

        # Determine project folder
        project_folder = self._get_project_folder()
        if not project_folder:
            return

        # Create saver — nest inside per-run folder if one was created for this batch
        if self._current_run_folder is not None:
            saver = BatchResultsSaver(
                base_path=str(self._current_run_folder),
                subfolder='',
                batch_prefix='experiment'
            )
        else:
            saver = BatchResultsSaver(
                base_path=project_folder,
                subfolder='experiments/results',
                batch_prefix='experiment'
            )

        # Create timestamped folder
        safe_name = name.replace(' ', '_').replace('/', '_')
        batch_path = saver.create_batch_folder(name_suffix=safe_name)

        save_errors = []

        # ── results.csv ── mean + std trajectories (mixed-format, section-aware)
        try:
            self._export_csv(str(batch_path / 'results.csv'), name, result)
            _fsync(batch_path / 'results.csv')
        except Exception as e:
            save_errors.append(f'results.csv: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save results.csv: {e}')

        # ── replicates.csv ── per-replicate outcomes (standard tabular)
        try:
            replicate_data = result.get('replicate_data', [])
            trajectory_summary = result.get('trajectory_summary', [])
            compressed_trajectories = result.get('compressed_trajectories', [])
            n = max(len(replicate_data), len(trajectory_summary))

            # Build {replicate_id: CompressionResult} for fast lookup
            compressed_by_id = {cr.replicate_id: cr for cr in compressed_trajectories}

            # Build id→name lookup once — reused across replicates.csv,
            # mean_final_state.csv, and replicates_trajectories/ so the
            # subnet model is queried only once per save.
            _id_to_name_early: dict = {}
            _subnet_mdl = getattr(self.parent_panel, 'subnet_model', None)
            if _subnet_mdl is not None:
                for _xp in getattr(_subnet_mdl, 'places', []):
                    _id_to_name_early[_xp.id] = getattr(_xp, 'name', _xp.id)
                for _xt in getattr(_subnet_mdl, 'transitions', []):
                    _id_to_name_early[_xt.id] = getattr(_xt, 'name', _xt.id)
            # Reverse lookup: resolve place IDs for fate-determining markers
            _name_to_pid = {v: k for k, v in _id_to_name_early.items()}
            _gata1_pid = _name_to_pid.get('GATA1_Protein_nuc', 'P17')
            _pu1_pid   = _name_to_pid.get('PU1_Protein_nuc',   'P18')

            # Determine final-state place columns (sorted for stable schema)
            final_place_ids: list = []
            if compressed_by_id:
                _sample = next(iter(compressed_by_id.values()))
                final_place_ids = _sample.sorted_place_ids()
            # Human-readable column names (fall back to place ID when no mapping)
            _final_col_names = [_id_to_name_early.get(pid, pid) for pid in final_place_ids]

            _per_rep_fates: list = []  # collected per replicate for fate_summary.csv
            with open(batch_path / 'replicates.csv', 'w', newline='') as f:
                _metadata = result.get('metadata')
                if _metadata is not None:
                    try:
                        f.write(_metadata.to_header_text())
                    except Exception:
                        pass
                writer = csv_mod.writer(f)
                base_cols = ['replicate_id', 'seed', 'n_timepoints', 'final_time',
                             'deadlocked', 'sim_duration', 'elapsed_time_s',
                             'n_kept', 'compression_ratio', 'fate_class']
                writer.writerow(base_cols + [f'final_{nm}' for nm in _final_col_names])
                for i in range(n):
                    rep = replicate_data[i] if i < len(replicate_data) else {}
                    traj = trajectory_summary[i] if i < len(trajectory_summary) else {}
                    rid = traj.get('replicate_id', i)
                    cr = compressed_by_id.get(rid)
                    final_vals = cr.final_values() if cr else {}
                    n_kept = cr.n_kept if cr else ''
                    comp_ratio = f'{cr.compression_ratio:.2f}' if cr else ''
                    # Fate classification: 1.5× GATA1_Protein_nuc vs PU1_Protein_nuc
                    try:
                        _gf = float(final_vals.get(_gata1_pid, 'nan'))
                        _pf = float(final_vals.get(_pu1_pid,   'nan'))
                        if _gf > 1.5 * _pf:   _fate = 'ery'
                        elif _pf > 1.5 * _gf: _fate = 'mye'
                        else:                  _fate = 'unc'
                    except (ValueError, TypeError):
                        _fate = ''
                    _per_rep_fates.append(_fate)
                    row = [
                        rid,
                        traj.get('seed', ''),
                        traj.get('n_timepoints', ''),
                        traj.get('final_time', ''),
                        rep.get('deadlocked', ''),
                        rep.get('duration', ''),
                        rep.get('elapsed_time', ''),
                        n_kept,
                        comp_ratio,
                        _fate,
                    ] + [final_vals.get(pid, '') for pid in final_place_ids]
                    writer.writerow(row)
            _fsync(batch_path / 'replicates.csv')
            # ── fate_summary.csv ── pre-computed population fate statistics ──
            # Eliminates re-reading all trajectory files just to count fates.
            try:
                from math import sqrt as _sqrt
                _fc = {k: _per_rep_fates.count(k) for k in ('ery', 'mye', 'unc', '')}
                _n_valid = _fc['ery'] + _fc['mye'] + _fc['unc']
                _p_ery = _fc['ery'] / _n_valid if _n_valid > 0 else 0.0
                _z = 1.96
                if _n_valid > 0:
                    _w_d = 1 + _z**2 / _n_valid
                    _w_c = (_p_ery + _z**2 / (2 * _n_valid)) / _w_d
                    _w_h = _z * _sqrt(_p_ery * (1 - _p_ery) / _n_valid + _z**2 / (4 * _n_valid**2)) / _w_d
                    _ci_lo, _ci_hi = max(0.0, _w_c - _w_h), min(1.0, _w_c + _w_h)
                else:
                    _ci_lo = _ci_hi = 0.0
                with open(batch_path / 'fate_summary.csv', 'w', newline='') as _fsf:
                    _fw = csv_mod.writer(_fsf)
                    _fw.writerow([
                        'n_total', 'n_ery', 'n_mye', 'n_unc', 'n_unknown',
                        'p_ery', 'ci_lo_95', 'ci_hi_95',
                        'fate_classifier', 'gata1_marker', 'pu1_marker',
                    ])
                    _fw.writerow([
                        _n_valid + _fc.get('', 0),
                        _fc['ery'], _fc['mye'], _fc['unc'], _fc.get('', 0),
                        round(_p_ery, 6),
                        round(_ci_lo, 6),
                        round(_ci_hi, 6),
                        'GATA1/PU1_nuc>1.5x',
                        _id_to_name_early.get(_gata1_pid, _gata1_pid),
                        _id_to_name_early.get(_pu1_pid, _pu1_pid),
                    ])
                _fsync(batch_path / 'fate_summary.csv')
            except Exception as _fse:
                print(f'[AUTO-SAVE] Warning: Failed to save fate_summary.csv: {_fse}')
        except Exception as e:
            save_errors.append(f'replicates.csv: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save replicates.csv: {e}')

        # ── config.csv ── experiment metadata as key-value pairs
        try:
            swept = result.get('swept_parameter') or {}
            subnet = result.get('subnet_structure') or {}
            stats = result.get('statistics', {})
            rows = [
                ('timestamp', saver.timestamp),
                ('experiment_name', name),
                ('snapshot_index', result.get('snapshot_index', '')),
                ('n_replicates', result.get('n_replicates', 0)),
                ('execution_time_s', result.get('duration', '')),
                ('n_replicates_stats', stats.get('n_replicates', '')),
                ('swept_param_type', swept.get('type', '')),
                ('swept_param_id', swept.get('id', '')),
                ('swept_param_name', swept.get('name', '')),
                ('swept_param_value', swept.get('value', '')),
                ('subnet_places', ','.join(subnet.get('place_ids', []))),
                ('subnet_transitions', ','.join(subnet.get('transition_ids', []))),
            ]
            with open(batch_path / 'config.csv', 'w', newline='') as f:
                _metadata = result.get('metadata')
                if _metadata is not None:
                    try:
                        f.write(_metadata.to_header_text())
                    except Exception:
                        pass
                writer = csv_mod.writer(f)
                writer.writerow(['key', 'value'])
                writer.writerows(rows)
            _fsync(batch_path / 'config.csv')
        except Exception as e:
            save_errors.append(f'config.csv: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save config.csv: {e}')

        # ── names.csv ── place/transition ID → human-readable name lookup
        # Allows analysis scripts to replace P17 → GATA1_Protein_nuc without
        # loading the full model.
        try:
            subnet_model = getattr(self.parent_panel, 'subnet_model', None)
            if subnet_model is not None:
                with open(batch_path / 'names.csv', 'w', newline='') as f:
                    writer = csv_mod.writer(f)
                    writer.writerow(['id', 'name', 'type'])
                    for p in getattr(subnet_model, 'places', []):
                        writer.writerow([p.id, getattr(p, 'name', p.id), 'place'])
                    for t in getattr(subnet_model, 'transitions', []):
                        writer.writerow([t.id, getattr(t, 'name', t.id), 'transition'])
                _fsync(batch_path / 'names.csv')
        except Exception as e:
            save_errors.append(f'names.csv: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save names.csv: {e}')

        # ── mean_final_state.csv ── flat, easily parseable final SS summary
        # Standard tabular CSV: pandas.read_csv(path, comment='#') works directly.
        # One row per species with final-timepoint mean and std.
        try:
            stats = result.get('statistics', {})
            species_stats = stats.get('species_statistics', {})
            if species_stats:
                # Reuse id→name map built during replicates.csv section
                id_to_name = _id_to_name_early

                with open(batch_path / 'mean_final_state.csv', 'w', newline='') as f:
                    _metadata = result.get('metadata')
                    if _metadata is not None:
                        try:
                            f.write(_metadata.to_header_text())
                        except Exception:
                            pass
                    writer = csv_mod.writer(f)
                    writer.writerow(['id', 'name', 'mean_final', 'std_final', 'min_final', 'max_final'])
                    for species_id, sdata in species_stats.items():
                        mean_traj = sdata.get('mean', [])
                        std_traj  = sdata.get('std', [])
                        min_traj  = sdata.get('min', [])
                        max_traj  = sdata.get('max', [])
                        mean_val = mean_traj[-1] if mean_traj else ''
                        std_val  = std_traj[-1]  if std_traj  else ''
                        min_val  = min_traj[-1]  if min_traj  else ''
                        max_val  = max_traj[-1]  if max_traj  else ''
                        writer.writerow([
                            species_id,
                            id_to_name.get(species_id, species_id),
                            mean_val, std_val, min_val, max_val
                        ])
                _fsync(batch_path / 'mean_final_state.csv')
        except Exception as e:
            save_errors.append(f'mean_final_state.csv: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save mean_final_state.csv: {e}')

        # ── replicates_trajectories/ ── one δ-compressed CSV per replicate
        # Each file is self-describing (comment header + col_schema line) so
        # analysis scripts need no external sidecar.  Skipped gracefully when
        # no compressed data is available (e.g. on error runs).
        try:
            compressed_trajectories = result.get('compressed_trajectories', [])
            if compressed_trajectories:
                from shypn.helpers.compressor import CompressedTrajectoryWriter

                # Reuse id→name map built during replicates.csv section
                _id_to_name = _id_to_name_early

                # Determine replicate status from replicate_data list
                _rep_data = result.get('replicate_data', [])
                _status_by_order: dict = {}
                for _idx, _rd in enumerate(_rep_data):
                    _status_by_order[_idx] = 'deadlocked' if _rd.get('deadlocked') else 'completed'

                traj_dir = batch_path / 'replicates_trajectories'
                traj_dir.mkdir(exist_ok=True)

                for cr in compressed_trajectories:
                    _status = _status_by_order.get(cr.replicate_id, 'completed')
                    csv_path = traj_dir / f'run_{cr.replicate_id + 1:03d}.csv'
                    CompressedTrajectoryWriter.write(
                        path=csv_path,
                        result=cr,
                        experiment_name=name,
                        status=_status,
                        id_to_name=_id_to_name or None,
                    )
                    _fsync(csv_path)
                print(f'[AUTO-SAVE] Saved {len(compressed_trajectories)} compressed trajectories → {traj_dir.name}/')
        except Exception as e:
            save_errors.append(f'replicates_trajectories/: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save replicates_trajectories/: {e}')

        # ── .complete / .partial sentinel ──────────────────────────────────
        # .complete is written ONLY when every file succeeded.
        # Its absence (or presence of .partial) means the save is incomplete.
        from datetime import datetime as _dt
        if not save_errors:
            (batch_path / '.complete').write_text(_dt.now().isoformat())
            print(f'[AUTO-SAVE] ✓ {name} → {batch_path.name}')
        else:
            (batch_path / '.partial').write_text('\n'.join(save_errors))
            print(f'[AUTO-SAVE] ⚠️  Partial save for "{name}": {save_errors}')

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
        # NOTE: _current_run_folder is intentionally NOT reset here.
        # Late-arriving experiment_result_callback idle calls must still find
        # the correct run folder.  The reset happens at the top of the next
        # batch run (_current_run_folder = None, line ~600 above).

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
                from datetime import datetime as _dt
                ts = _dt.now().strftime("%Y%m%d_%H%M%S")
                # Append timestamp to prevent silently overwriting a previous export
                # of the same sweep from an earlier run.
                safe_name = batch_name.replace(' ', '_').replace('/', '_').replace('=', '_')
                base_format = format_type.replace('_batch', '')
                filepath = f"{directory}/{safe_name}_{ts}.{base_format}"

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
        """Export results to CSV with Header Protocol preamble.

        ⚠️  MIXED-FORMAT FILE — not a standard flat CSV.
        Structure after the '#'-prefixed header block:
            [free key-value rows]         Experiment, N_Replicates, ...
            [section label row]           'Species Statistics - Mean Trajectories'
            [matrix: Time + species cols] Time, P1, P2, ..., T1, T2, ...
            [empty row]
            [section label row]           'Species Statistics - Standard Deviations'
            [same matrix shape]
            [empty row]
            [section label row]           'Trajectory Summary'
            [matrix: replicate metadata]
            [empty row]
            [section label row]           'Summary'
            [free key-value rows]

        Reading tip:
            pandas.read_csv(path, comment='#') will fail due to mixed column counts.
            Use a section-aware reader, or prefer mean_final_state.csv for steady-state
            analysis (standard tabular, pandas-safe).

        Species are identified by place/transition IDs (P1, P17, T11 ...).
        Use names.csv in the same folder for the ID → display-name mapping.

        Args:
            filepath: Output file path
            name: Experiment name
            result: Result dictionary with statistics and trajectory summary
        """
        import csv
        
        with open(filepath, 'w', newline='') as f:
            # ── Header Protocol ────────────────────────────────────────────
            metadata = result.get('metadata')
            if metadata is not None:
                try:
                    f.write(metadata.to_header_text())
                except Exception as e:
                    print(f"[CSV] Warning: Failed to write header protocol: {e}")
            # ───────────────────────────────────────────────────────────────

            writer = csv.writer(f)
            
            # Write metadata header
            writer.writerow(['Experiment', name])
            stats = result.get('statistics', {})
            writer.writerow(['N_Replicates', stats.get('n_replicates', 0)])
            # 'elapsed_time' is absent when compute_statistics() ran; use 'mean_elapsed_time'
            elapsed = stats.get('elapsed_time', stats.get('mean_elapsed_time', 0.0))
            writer.writerow(['Elapsed_Time', elapsed])
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
