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
import logging
import os
import json
import threading
from datetime import datetime
from pathlib import Path

from shypn.ui.category_frame import CategoryFrame
from shypn.data.project_models import get_project_manager
from shypn.helpers.batch_results_saver import BatchResultsSaver

logger = logging.getLogger(__name__)


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

        # Remote sweep dispatcher (lazy init). Owns SSH/ControlMaster +
        # the results proxy used by the lazy-fetch results browser. Set
        # by the remote controller's ``.underlying`` after dispatch
        # starts; kept separate from ``_controller`` so result-browsing
        # code can keep using the SSH dispatcher even after the
        # controller's lifecycle has completed.
        self._remote_dispatcher = None

        # Active dispatch controller (local or remote). None when idle.
        # Single source of truth for in-flight sweep state — the legacy
        # ``_remote_dispatcher`` attribute is kept as a read-only alias
        # below for callers that haven't migrated yet.
        self._controller = None  # type: Optional[SweepDispatchController]

        # Single source of truth for whether a sweep dispatch is in flight
        # (local or remote). Drives Cancel button sensitivity so row-level
        # status updates can't accidentally disable Cancel mid-sweep.
        self._dispatch_active = False

        # Track pending UI updates to prevent queue overflow
        self._pending_updates = {}  # Dict: queue_index -> latest (status, progress) to process
        self._processing_updates = set()  # Set of queue_index currently being processed
        self._idle_handler_active = False  # Flag to ensure only one idle handler runs at a time

        # Limit concurrent auto-save I/O threads so disk writes don't compete
        # with worker processes for CPU/IO.  At most 2 save threads run at once;
        # extras block until a slot is free (they are daemon threads so they
        # never prevent the app from exiting).
        import threading as _threading
        self._auto_save_semaphore = _threading.Semaphore(2)
        
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
        # Full sweep-plan clear: empty the queue AND wipe the activity log so
        # no leftover from a previous or cancelled sweep can mislead the next
        # run. The sweep_builder's own _on_clear_clicked has already reset its
        # parameter lists, design mode, and solver settings before this fires.
        # If a remote dispatcher is still alive (running OR stuck in a stale
        # is_running state), cancel it first so the next dispatch isn't
        # blocked by the "previous dispatch still marked as running" dialog.
        def _on_sweep_plan_cleared():
            ctrl = getattr(self, '_controller', None)
            if ctrl is not None and ctrl.is_active:
                try:
                    ctrl.cancel()
                except Exception:
                    pass
            self._controller = None
            disp = getattr(self, '_remote_dispatcher', None)
            if disp is not None:
                try:
                    if getattr(disp, 'is_running', False):
                        disp.cancel()
                except Exception:
                    pass
                self._remote_dispatcher = None
            self._dispatch_active = False
            self.queue_view.clear_queue()
            try:
                self.queue_view.clear_status()
            except Exception:
                pass
        self.sweep_builder.set_clear_callback(_on_sweep_plan_cleared)
        
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
        self.queue_view.set_run_remote_callback(self._on_queue_run_remote)
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
        self.results_browser.on_reload_callback = self._scan_local_run_dirs
        self.content_box.pack_start(self.results_browser, True, True, 0)
    
    def _on_object_type_changed(self, combo):
        """Handle object type change - clear queue and refresh parameters.

        Only clears when the type *actually* changes. Programmatic combo
        refreshes (e.g. after refresh_parameters()) used to fire 'changed'
        with the same active item, silently wiping the user's queue.

        Also refuses to clear while a dispatch is in flight — the user
        cannot have switched type meaningfully under a running sweep, so
        treat it as a spurious re-fire and skip the destructive action.
        """
        try:
            new_type = combo.get_active_text()
        except Exception:
            new_type = None

        # Spurious / programmatic re-fire on the same type → no-op.
        if new_type is not None and getattr(self, '_last_object_type', None) == new_type:
            return
        # Don't wipe queue mid-dispatch.
        if getattr(self, '_dispatch_active', False):
            self._last_object_type = new_type
            return

        self._last_object_type = new_type

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
            # Build a quick lookup of which place IDs are flagged as
            # Environment-Panel parameter places so we can surface them
            # at the top of the dropdown with a [param] tag.
            param_place_ids: set = set()
            try:
                _src_model = (
                    getattr(self.parent_panel, 'subnet_model', None)
                    or self.parent_panel._get_current_model()
                )
                if _src_model is not None:
                    for _p in getattr(_src_model, 'places', []) or []:
                        if getattr(_p, 'is_parameter_place', False):
                            param_place_ids.add(_p.id)
            except Exception:
                param_place_ids = set()

            # Get from places_store
            if hasattr(self.parent_panel, 'places_store'):
                store = self.parent_panel.places_store
                _params_top: list = []
                _params_rest: list = []
                iter = store.get_iter_first()
                while iter:
                    # Column 0 = ID (internal), Column 1 = Name (display)
                    place_id = store.get_value(iter, 0)
                    place_name = store.get_value(iter, 1)
                    if place_id and place_name:
                        # Places: Only initial_marking property
                        if place_id in param_place_ids:
                            _params_top.append(
                                (f"[param] {place_name}", f"{place_id}.initial_marking")
                            )
                        else:
                            _params_rest.append(
                                (f"{place_name}", f"{place_id}.initial_marking")
                            )
                    iter = store.iter_next(iter)
                # Parameter places first, then biological species
                params.extend(_params_top)
                params.extend(_params_rest)
        
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

        # Re-populate the fixed-overrides section (▢ parameter places)
        # whenever the model topology changes — same trigger as the main
        # parameter list refresh.
        if hasattr(self.sweep_builder, 'refresh_fixed_overrides'):
            try:
                self.sweep_builder.refresh_fixed_overrides()
            except Exception as exc:
                import logging as _lg
                _lg.getLogger(__name__).warning(
                    "refresh_fixed_overrides failed: %s", exc
                )
    
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
        
        # Always re-sync the baseline from the current TreeViews before generating.
        # This ensures any parameter changes made in the viability panel (e.g. GCSF)
        # after the initial baseline capture are picked up.
        base_snapshot = self.experiment_manager.get_active_snapshot()
        if base_snapshot:
            if self.parent_panel and hasattr(self.parent_panel, 'places_store'):
                base_snapshot.capture_from_treeviews(
                    self.parent_panel.places_store,
                    self.parent_panel.transitions_store,
                    self.parent_panel.arcs_store
                )
        
        try:
            # Clear previously generated sweep snapshots (keep only the
            # first baseline) so that clicking "Generate Experiments"
            # multiple times doesn't accumulate duplicate conditions.
            if len(self.experiment_manager.snapshots) > 1:
                del self.experiment_manager.snapshots[1:]
                self.experiment_manager.swept_parameters = {
                    k: v for k, v in self.experiment_manager.swept_parameters.items()
                    if k == 0
                }
            if self.queue_view:
                self.queue_view.clear_queue()

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
                        # Use up to 6 significant figures to avoid naming collisions
                        # (e.g. 0.449 and 0.450 must not both map to "0.45")
                        value_str = f"{value:.6g}"
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
        termination_condition = "time_only"  # Default — see parameter_sweep_builder.py rationale
        
        if hasattr(self.sweep_builder, 'replicates_entry'):
            try:
                text = self.sweep_builder.replicates_entry.get_text().strip()
                if text:
                    replicates = int(text)
                    if replicates <= 0:
                        print(f"[WARNING] Replicates is {replicates}, using default 3")
                        replicates = 3
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
                termination_condition = self.sweep_builder.termination_combo.get_active_id() or "time_only"
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

        compressor_min_gap = 5.0
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
    
    def _on_queue_run_remote(self, pending_experiments):
        """Handle Run Remote button — dispatch sweep to remote server via SSH.

        Thin orchestration: validates prerequisites, shows the SSH
        confirmation dialog, builds a typed ``DispatchRequest``, then
        hands off to ``RemoteSweepDispatchController``. All progress /
        completion handling now lives in the controller + observer
        methods (``on_status``, ``on_row_started``, ``on_row_completed``,
        ``on_dispatch_complete``) on this class.
        """
        from .remote_sweep_dispatcher import RemoteSweepSettings
        from .dispatch import (
            RemoteSweepDispatchController,
            DispatchRequest,
            DispatchAlreadyActive,
            DispatchValidationError,
        )

        if self._remote_dispatcher and self._remote_dispatcher.is_running:
            # Thread is alive — but it can be stuck (e.g. SSH fallback
            # blocked on a password prompt that never surfaced after
            # `ControlMaster exited early`). Offer a forced reset so
            # the operator isn't permanently locked out without having
            # to restart the GUI.
            dialog = Gtk.MessageDialog(
                transient_for=self.sweep_builder.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.NONE,
                text="A previous remote dispatch is still marked as running.",
            )
            dialog.format_secondary_text(
                "If the server fans are silent and no progress is being\n"
                "reported, the SSH thread is likely stuck (e.g. waiting\n"
                "on a password prompt after a ControlMaster fallback).\n\n"
                "Choose:\n"
                "  • Cancel & Reset — kill the stuck dispatcher and start fresh\n"
                "  • Wait — keep the existing dispatch (do nothing)"
            )
            dialog.add_button("Wait", Gtk.ResponseType.CANCEL)
            reset_btn = dialog.add_button("Cancel & Reset", Gtk.ResponseType.OK)
            reset_btn.get_style_context().add_class("destructive-action")
            response = dialog.run()
            dialog.destroy()
            if response != Gtk.ResponseType.OK:
                return
            # Forced reset: ask the dispatcher to cancel (which sends a
            # remote pkill and tears down the local SSH stream), abandon
            # the thread reference, and reset the UI buttons.
            try:
                self._remote_dispatcher.cancel()
            except Exception:
                pass
            self._remote_dispatcher = None
            self._controller = None
            self._dispatch_active = False
            if self.queue_view:
                self.queue_view.set_running(False)

        # ── Validate prerequisites ───────────────────────────────────
        project_folder = self._get_project_folder()
        if not project_folder:
            self._show_error(
                "No project open.\n"
                "Remote sweep requires a project folder so results land\n"
                "in &lt;project&gt;/experiments/results/."
            )
            return

        model_filepath = None
        if self.parent_panel:
            # _get_current_model() returns the ModelCanvasManager for this
            # document — it owns the .filepath property.
            canvas_mgr = self.parent_panel._get_current_model()
            if canvas_mgr and hasattr(canvas_mgr, 'filepath'):
                model_filepath = canvas_mgr.filepath
        if not model_filepath:
            self._show_error("Cannot determine model file path.\n"
                             "Please save the model first.")
            return

        if not self.experiment_manager or not self.experiment_manager.snapshots:
            self._show_error("No experiment snapshots — generate experiments first.")
            return

        # ── Load / show settings dialog ──────────────────────────────
        from shypn.workspace_settings import WorkspaceSettings
        ws = WorkspaceSettings()
        settings = RemoteSweepSettings(ws)

        # Read simulation params from sweep builder (same logic as _on_queue_run)
        sim_params = self._collect_sim_params()

        # Build confirmation dialog
        confirmed, settings, ssh_password = self._show_remote_sweep_dialog(
            settings, sim_params, len(pending_experiments))
        if not confirmed:
            return

        settings.save()

        # ── Collect events + fixed overrides + run collision detector ──
        # Layer C: catches silent-superposition cases (sweep target ==
        # event assignment target) before bytes leave the box.
        try:
            fixed_overrides = self.sweep_builder.get_fixed_overrides() \
                if self.sweep_builder else {}
        except ValueError as exc:
            self._show_error(f"Invalid fixed-override value:\n\n{exc}")
            return

        events = self._collect_model_events()
        if self.sweep_builder is not None:
            issues = self.sweep_builder.detect_sweep_event_collisions(
                snapshots=self.experiment_manager.snapshots,
                events=events,
                fixed_overrides=fixed_overrides,
            )
        else:
            issues = []
        errors = [i for i in issues if i.get('severity') == 'error']
        warnings = [i for i in issues if i.get('severity') == 'warning']
        if errors or warnings:
            allow = self._confirm_sweep_event_collisions(errors, warnings)
            if not allow:
                return

        # ── Build typed request + hand off to controller ─────────────
        from .dispatch import SimulationParams as _SP
        request = DispatchRequest(
            experiments=list(pending_experiments),
            sim_params=_SP(**sim_params),
            model_filepath=model_filepath,
            project_folder=project_folder,
            events=events or [],
            fixed_overrides=fixed_overrides or {},
            ssh_password=ssh_password or None,
        )

        controller = RemoteSweepDispatchController(
            observer=self,
            settings=settings,
            experiment_manager=self.experiment_manager,
        )
        # Keep ``_remote_dispatcher`` pointing at the underlying SSH
        # dispatcher so existing results-browser / proxy code still
        # works unchanged.
        self._remote_dispatcher = controller.underlying
        self._controller = controller

        # UI feedback. Use set_running() so all four buttons (Run, Run
        # Remote, Pause, Cancel) move together; this keeps Cancel
        # enabled regardless of subsequent row-status updates.
        self._dispatch_active = True
        if self.queue_view:
            self.queue_view.set_running(True)
            self.queue_view.status_label.set_markup(
                "<span foreground='blue'><b>Remote sweep dispatching...</b></span>"
            )
            # Mark all queue rows as 'pending' before dispatch — the
            # controller will flip them to 'running' as the CLI emits
            # per-condition progress lines.
            for i in range(len(pending_experiments)):
                self.queue_view.update_experiment_status(i, 'pending', '—')

        try:
            controller.start(request)
        except DispatchAlreadyActive as exc:
            self._show_error(f"Cannot start dispatch:\n\n{exc}")
        except DispatchValidationError as exc:
            # Controller already emitted on_dispatch_complete → idle UI restored.
            self._show_error(f"Invalid dispatch request:\n\n{exc}")
        except Exception as exc:
            # Controller already emitted on_dispatch_complete → idle UI restored.
            self._show_error(f"Remote dispatch failed to start:\n\n{exc}")

    # ── DispatchObserver implementation ──────────────────────────────
    # All methods are called on the GTK main thread by the active
    # controller. They are the *only* place the queue view gets updated
    # in response to dispatch events — keeping this surface tight
    # prevents the local/remote drift that bit us before.

    def on_status(self, message: str, level: str = 'info') -> None:
        """Activity-log line from the active controller."""
        if not self.queue_view:
            return
        colour = {
            'success': 'green',
            'warning': '#ce5c00',
            'error': 'red',
        }.get(level, 'blue')
        try:
            self.queue_view.status_label.set_markup(
                f"<span foreground='{colour}'><b>Sweep:</b> "
                f"{GLib.markup_escape_text(str(message))}</span>"
            )
        except Exception:
            pass

    def on_row_started(self, row_index: int) -> None:
        if self.queue_view:
            try:
                self.queue_view.update_experiment_status(
                    row_index, 'running', 'running…')
            except Exception:
                pass

    def on_row_completed(
        self, row_index: int, ok_replicates: int,
        error_replicates: int, wall_seconds: float,
    ) -> None:
        if not self.queue_view:
            return
        status = 'completed' if error_replicates == 0 else 'failed'
        prog = f"{ok_replicates} ok, {error_replicates} err — {wall_seconds:.1f}s"
        try:
            self.queue_view.update_experiment_status(row_index, status, prog)
        except Exception:
            pass

    def on_dispatch_complete(
        self, success: bool, results_dir, message: str,
    ) -> None:
        # Drop dispatch state so the next sweep can launch.
        self._dispatch_active = False
        self._controller = None
        if self.queue_view:
            self.queue_view.set_running(False)
            # Reconcile any rows the progress parser missed (last row
            # without a 'done in Xs' line, or local cancellation).
            try:
                store = self.queue_view.queue_store
                terminal = 'completed' if success else 'failed'
                for i in range(len(store)):
                    it = store.get_iter(i)
                    st = store.get_value(it, 1)
                    if st in ('running', 'pending'):
                        store.set_value(it, 1, terminal)
                        if not store.get_value(it, 2):
                            store.set_value(
                                it, 2, 'done' if success else 'no result')
                self.queue_view._update_status_label()
            except Exception:
                pass
            try:
                colour = 'green' if success else 'red'
                glyph = '✓' if success else '✗'
                self.queue_view.status_label.set_markup(
                    f"<span foreground='{colour}'><b>{glyph}</b> "
                    f"{GLib.markup_escape_text(str(message))}</span>"
                )
            except Exception:
                pass
        if success and results_dir:
            self._load_remote_results(results_dir)

    def _collect_model_events(self) -> list:
        """Serialise the current model's environment events for dispatch.

        Events are defined by the user on the Environment Panel and live
        on ``model.events`` (list of ``shypn.data.pathway.pathway_data.Event``).
        Returns a list of plain dicts suitable for embedding in the sweep
        config JSON.  Empty list if no events or model unavailable.
        """
        import logging as _lg
        _log = _lg.getLogger(__name__)
        if not self.parent_panel:
            _log.warning("[EVENT_DISPATCH] no parent_panel; events=[]")
            return []
        canvas_mgr = self.parent_panel._get_current_model()
        if canvas_mgr is None:
            _log.warning("[EVENT_DISPATCH] _get_current_model returned None; events=[]")
            return []
        events = getattr(canvas_mgr, 'events', None) or []
        try:
            payload = [e.to_dict() for e in events if hasattr(e, 'to_dict')]
        except Exception as exc:
            _log.exception("[EVENT_DISPATCH] serialisation failed: %s", exc)
            return []
        _log.info(
            "[EVENT_DISPATCH] captured %d event(s) from model %r: %s",
            len(payload), getattr(canvas_mgr, 'filepath', '?'),
            [e.get('id') + '@' + e.get('trigger', '') for e in payload],
        )
        return payload

    def _collect_sim_params(self) -> dict:
        """Read simulation parameters from sweep builder widgets.

        Thin wrapper around :class:`WidgetParamCollector` — kept for
        backward compatibility with callers that still expect a
        plain dict (e.g. the remote-dispatch confirmation dialog).
        """
        from .dispatch import WidgetParamCollector
        return WidgetParamCollector.collect(self.sweep_builder).to_dict()

    def _show_remote_sweep_dialog(self, settings, sim_params, n_experiments):
        """Show a GTK dialog to confirm/edit remote sweep settings.

        Returns:
            (confirmed: bool, settings: RemoteSweepSettings)
        """
        parent_window = None
        if self.parent_panel:
            parent_window = self.parent_panel.get_toplevel()
            if not isinstance(parent_window, Gtk.Window):
                parent_window = None

        dialog = Gtk.Dialog(
            title="Run Sweep on Remote Server",
            transient_for=parent_window,
            modal=True,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Dispatch", Gtk.ResponseType.OK,
        )
        dialog.set_default_size(420, -1)

        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)

        # Summary
        summary = Gtk.Label()
        summary.set_markup(
            f"<b>Dispatch {n_experiments} experiment(s) to remote server</b>\n"
            f"Replicates: {sim_params['replicates']}  |  "
            f"Duration: {sim_params['duration']}s  |  "
            f"Termination: {sim_params['termination']}"
        )
        summary.set_xalign(0)
        summary.set_line_wrap(True)
        content.pack_start(summary, False, False, 0)

        # SSH Settings grid
        grid = Gtk.Grid()
        grid.set_column_spacing(8)
        grid.set_row_spacing(6)

        row = 0
        grid.attach(Gtk.Label(label="SSH Host:", xalign=0), 0, row, 1, 1)
        host_entry = Gtk.Entry()
        host_entry.set_text(settings.ssh_host)
        host_entry.set_tooltip_text("SSH config alias or user@host")
        grid.attach(host_entry, 1, row, 1, 1)

        row += 1
        grid.attach(Gtk.Label(label="Remote Repo:", xalign=0), 0, row, 1, 1)
        repo_entry = Gtk.Entry()
        repo_entry.set_text(settings.remote_repo)
        repo_entry.set_tooltip_text("Absolute path to shypn repo on remote")
        repo_entry.set_hexpand(True)
        grid.attach(repo_entry, 1, row, 1, 1)

        row += 1
        grid.attach(Gtk.Label(label="Python:", xalign=0), 0, row, 1, 1)
        venv_entry = Gtk.Entry()
        venv_entry.set_text(settings.remote_venv)
        venv_entry.set_tooltip_text("Path to Python interpreter (relative to remote repo)")
        grid.attach(venv_entry, 1, row, 1, 1)

        row += 1
        grid.attach(Gtk.Label(label="Workers:", xalign=0), 0, row, 1, 1)
        workers_spin = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(value=settings.workers, lower=0, upper=128,
                                      step_increment=1, page_increment=4, page_size=0)
        )
        workers_spin.set_tooltip_text("0 = auto-detect on remote")
        grid.attach(workers_spin, 1, row, 1, 1)

        row += 1
        grid.attach(Gtk.Label(label="Password:", xalign=0), 0, row, 1, 1)
        password_entry = Gtk.Entry()
        password_entry.set_visibility(False)  # mask input
        password_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        password_entry.set_tooltip_text(
            "SSH password (optional — leave blank for key-based auth)."
            " Not saved to disk."
        )
        password_entry.set_placeholder_text("leave blank for key auth")
        grid.attach(password_entry, 1, row, 1, 1)

        content.pack_start(grid, False, False, 0)

        # Pipeline description
        desc = Gtk.Label()
        desc.set_markup(
            "<small>"
            "Pipeline: upload model + config → SSH run CLI → fetch results\n"
            "Results land in &lt;project&gt;/experiments/results/"
            "</small>"
        )
        desc.set_xalign(0)
        desc.set_line_wrap(True)
        content.pack_start(desc, False, False, 0)

        dialog.show_all()
        response = dialog.run()

        ssh_password = ''
        if response == Gtk.ResponseType.OK:
            settings.ssh_host = host_entry.get_text().strip()
            settings.remote_repo = repo_entry.get_text().strip()
            settings.remote_venv = venv_entry.get_text().strip()
            settings.workers = int(workers_spin.get_value())
            ssh_password = password_entry.get_text()  # never persisted

        dialog.destroy()
        return (response == Gtk.ResponseType.OK, settings, ssh_password)

    def _load_remote_results(self, local_results_dir: str) -> None:
        """Load results from a remote sweep run into the ResultsBrowserView.

        If a ``RemoteResultsProxy`` is available (SUMMARY_ONLY mode),
        conditions are registered as remote-only and will be fetched
        on demand when the user requests plots or exports.

        Args:
            local_results_dir: Local path to the run directory containing
                at minimum ``summary.csv``.
        """
        if not self.results_browser or not local_results_dir:
            return

        results_path = Path(local_results_dir)
        if not results_path.is_dir():
            return

        summary_csv = results_path / 'summary.csv'
        if not summary_csv.exists():
            return

        # Attach proxy if dispatcher used SUMMARY_ONLY mode
        proxy = (self._remote_dispatcher.results_proxy
                 if self._remote_dispatcher else None)

        # Optional primary-observable reduction (config.json + model_snapshot.shy
        # land alongside summary.csv in the run dir).
        from shypn.ui.panels.viability.automation.primary_observables import (
            compute_observables, load_place_name_to_id, load_run_config,
            load_project_observables_fallback,
        )
        run_cfg = load_run_config(results_path)
        obs_cfg = (run_cfg or {}).get('primary_observables') or {}
        if not obs_cfg:
            obs_cfg = load_project_observables_fallback(results_path)
        name_to_id = load_place_name_to_id(results_path) if obs_cfg else {}
        if obs_cfg:
            self._configure_observable_columns(obs_cfg)

        # Parse summary.csv and load each condition as a result entry
        import csv
        condition_names: list[str] = []
        try:
            with open(summary_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    condition = row.get('condition', 'unknown')
                    ok = int(row.get('replicates_ok', 0))
                    errors = int(row.get('replicates_error', 0))
                    wall = float(row.get('wall_seconds', 0))

                    condition_names.append(condition)

                    cond_dir = (
                        results_path /
                        f'condition_{condition.replace("=", "_eq_")}'
                    )
                    obs = (compute_observables(cond_dir, obs_cfg, name_to_id)
                           if obs_cfg else {})

                    # Create a minimal result dict for the browser
                    result = {
                        'name': condition,
                        'replicates': ok,
                        'errors': errors,
                        'wall_seconds': wall,
                        'source': 'remote',
                        'results_dir': str(cond_dir),
                        'remote_only': proxy is not None,
                        'primary_observables': obs,
                    }
                    self.results_browser.add_result(condition, result)

            # Register conditions on the proxy for on-demand fetching
            if proxy and condition_names:
                proxy.register_conditions(condition_names)
                # Store proxy on browser for on-demand access
                self.results_browser.set_results_proxy(proxy)

        except Exception as e:
            logger.warning("Failed to load remote results: %s", e)

    # ── Local run-dir scanning ───────────────────────────────────────

    def _configure_observable_columns(self, obs_cfg: dict) -> None:
        """Push observable column titles to the Results Browser.

        Idempotent — repeated calls just refresh the headers, so it is
        safe to call once per loaded run dir.
        """
        if not self.results_browser:
            return
        ep_cfg = obs_cfg.get('endpoint_place')
        ep_label = obs_cfg.get('endpoint_label') if ep_cfg else None
        if ep_cfg and not ep_label:
            ep_label = f'{ep_cfg} (final)'
        fc_cfg = obs_cfg.get('first_crossing') or {}
        fc_label = fc_cfg.get('label')
        if fc_cfg and not fc_label:
            unit = fc_cfg.get('time_unit', 's')
            fc_label = f"t1 {fc_cfg.get('place', '?')} ({unit})"
        try:
            self.results_browser.set_observable_headers(ep_label, fc_label)
        except AttributeError:
            # Older browser without observable columns
            pass

    def _scan_local_run_dirs(self, latest_only: bool = False) -> None:
        """Walk ``<project>/experiments/results/`` and load sweep runs into the browser.

        The Results Browser is otherwise event-driven (live sweeps +
        pending-dispatch recovery), so historical runs and manually
        rsynced run dirs would never appear.  This method bridges that
        gap by treating each ``run_*/summary.csv`` like a remote
        summary and pushing condition rows through the same
        ``_load_remote_results`` path.

        Condition names are prefixed with the run-dir name so multiple
        runs can coexist in the browser without name collisions.

        Args:
            latest_only: If True, load only the most recently modified
                run directory (typical startup behaviour). If False,
                load every run dir found (manual Reload).
        """
        if not self.results_browser:
            return
        try:
            from shypn.data.project_models import get_project_manager
            project = get_project_manager().current_project
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Local run-dir scan skipped (no project): %s", exc)
            return
        if project is None or not getattr(project, 'base_path', None):
            return

        results_root = Path(project.base_path) / 'experiments' / 'results'
        if not results_root.is_dir():
            return

        run_dirs = [
            d for d in results_root.iterdir()
            if d.is_dir() and d.name.startswith('run_')
            and (d / 'summary.csv').is_file()
        ]
        if not run_dirs:
            logger.debug("No on-disk sweep runs under %s", results_root)
            return

        run_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
        if latest_only:
            run_dirs = run_dirs[:1]

        loaded = 0
        for run_dir in run_dirs:
            try:
                self._load_local_run_dir(run_dir)
                loaded += 1
            except Exception as exc:
                logger.warning("Failed to load run dir %s: %s", run_dir, exc)
        logger.info(
            "Local run-dir scan: loaded %d/%d run(s) from %s",
            loaded, len(run_dirs), results_root,
        )

    def _load_local_run_dir(self, run_dir: Path) -> None:
        """Load one ``run_*`` directory's conditions into the browser.

        Reads ``summary.csv`` and registers each condition as a local
        result whose ``results_dir`` points at the per-condition folder
        on disk.  Condition keys are prefixed with the run-dir name so
        multiple runs coexist without overwriting each other.

        Args:
            run_dir: Absolute path to a ``run_<timestamp>/`` directory
                containing at minimum ``summary.csv``.
        """
        import csv

        from shypn.ui.panels.viability.automation.primary_observables import (
            compute_observables, load_place_name_to_id, load_run_config,
            load_project_observables_fallback,
        )

        summary_csv = run_dir / 'summary.csv'
        run_label = run_dir.name  # e.g. "run_20260510_002345"

        run_cfg = load_run_config(run_dir)
        obs_cfg = (run_cfg or {}).get('primary_observables') or {}
        if not obs_cfg:
            # Older runs were dispatched before the block existed; let
            # the user retroactively see observables by reading from the
            # project's live sweep_config*.json.
            obs_cfg = load_project_observables_fallback(run_dir)
        name_to_id = load_place_name_to_id(run_dir) if obs_cfg else {}
        if obs_cfg:
            self._configure_observable_columns(obs_cfg)

        with summary_csv.open() as f:
            for row in csv.DictReader(f):
                condition = row.get('condition', 'unknown')
                ok = int(row.get('replicates_ok') or 0)
                errors = int(row.get('replicates_error') or 0)
                wall = float(row.get('wall_seconds') or 0.0)

                cond_dir_name = (
                    f'condition_{condition.replace("=", "_eq_")}'
                )
                cond_dir = run_dir / cond_dir_name

                obs = (compute_observables(cond_dir, obs_cfg, name_to_id)
                       if obs_cfg else {})

                # Composite key keeps runs disambiguated in the browser
                browser_key = f'{run_label} / {condition}'
                result = {
                    'name': browser_key,
                    'replicates': ok,
                    'errors': errors,
                    'wall_seconds': wall,
                    'source': 'disk',
                    'results_dir': str(cond_dir),
                    'remote_only': False,
                    'run_dir': str(run_dir),
                    'primary_observables': obs,
                }
                self.results_browser.add_result(browser_key, result)

    # ── Pending-dispatch recovery ────────────────────────────────────

    def _schedule_pending_dispatch_recovery(self) -> None:
        """Resume any unfinished remote sweeps in the background.

        Reads ``<project>/experiments/.pending_dispatches.json`` and,
        for each entry, ensures ``summary.csv`` + ``config.json`` are
        present locally and the corresponding rows appear in the
        Experiment Results browser.  Each entry is processed in its
        own daemon thread so a slow or dead server cannot stall the
        UI; results are marshalled back via ``GLib.idle_add``.

        Idempotent: re-invocation is harmless because successful
        recovery removes the registry entry, and entries already
        loaded into the browser are simply re-added (same key).
        """
        try:
            from shypn.data.project_models import get_project_manager
            project = get_project_manager().current_project
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Pending-dispatch recovery skipped (no project): %s", exc)
            return
        if project is None or not getattr(project, 'base_path', None):
            return

        from .dispatch_registry import DispatchRegistry
        registry = DispatchRegistry(project.base_path)
        entries = registry.pending()
        if not entries:
            return

        logger.info(
            "Pending-dispatch recovery: %d unresolved sweep(s) for project %s",
            len(entries), project.base_path,
        )
        for entry in entries:
            t = threading.Thread(
                target=self._recover_one_dispatch,
                args=(entry, registry),
                name=f"DispatchRecovery-{Path(entry.run_dir_local).name}",
                daemon=True,
            )
            t.start()

    def _recover_one_dispatch(self, entry, registry) -> None:
        """Fetch summary for a single pending dispatch (background thread).

        On success the result is loaded into the browser via the GTK
        main loop and the registry entry is removed.  On failure the
        entry is left in place so a future attempt can retry.

        Args:
            entry: A ``PendingDispatch`` instance.
            registry: The owning ``DispatchRegistry``.
        """
        from .remote_results_proxy import RemoteResultsProxy

        local_run_dir = Path(entry.run_dir_local)
        summary_path = local_run_dir / 'summary.csv'

        try:
            if not summary_path.exists():
                # Need to pull summary.csv + config.json from the server.
                # Recovery uses key-based SSH only (no password is persisted).
                proxy = RemoteResultsProxy(
                    remote_run_dir=entry.run_dir_remote,
                    local_run_dir=str(local_run_dir),
                    ssh_host=entry.ssh_host,
                )
                proxy.fetch_summary()
            else:
                # Summary already on disk (e.g. partial recovery from a
                # prior session).  Still attach a proxy so on-demand
                # condition fetches keep working.
                proxy = RemoteResultsProxy(
                    remote_run_dir=entry.run_dir_remote,
                    local_run_dir=str(local_run_dir),
                    ssh_host=entry.ssh_host,
                )
        except Exception as exc:
            logger.warning(
                "Recovery failed for %s (%s): %s",
                local_run_dir.name, entry.ssh_host, exc,
            )
            return

        # Marshal the browser update onto the GTK main thread.
        def _hydrate():
            # Temporarily swap _last_proxy so _load_remote_results
            # picks it up (the method already reads from
            # self._remote_dispatcher.results_proxy).  We use a tiny
            # adapter to avoid mutating live dispatcher state.
            class _ProxyHolder:
                results_proxy = proxy
            saved = self._remote_dispatcher
            self._remote_dispatcher = _ProxyHolder()
            try:
                self._load_remote_results(str(local_run_dir))
            finally:
                self._remote_dispatcher = saved
            registry.unregister(str(local_run_dir))
            logger.info(
                "Recovered remote sweep: %s", local_run_dir.name)
            return False  # one-shot idle handler

        GLib.idle_add(_hydrate)

    def _on_queue_cancel(self):
        """Handle queue cancel request.

        Routes through the active dispatch controller when one exists
        (covers both local and remote uniformly). Falls back to legacy
        direct-cancel paths for any controller-less code path.
        """
        # Preferred: ask the active controller to cancel itself. The
        # controller will emit on_dispatch_complete(False, ...) which
        # restores idle UI and reconciles row statuses.
        ctrl = getattr(self, '_controller', None)
        if ctrl is not None and ctrl.is_active:
            ctrl.cancel()
            return

        # Legacy fallbacks (no controller in use, e.g. local dispatch
        # not yet migrated). Cancel the SSH dispatcher and the
        # in-process batch executor directly.
        if self._remote_dispatcher and self._remote_dispatcher.is_running:
            self._remote_dispatcher.cancel()

        if not self.batch_executor:
            return

        self.batch_executor.cancel()

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
        
        # ── RAM-safe heavy-data extraction ────────────────────────────────────
        # Extract compressed_trajectories and species_statistics from the result
        # dict HERE, on the GTK main thread, BEFORE adding to the results browser
        # or spawning the auto-save thread.
        #
        # Why this matters: up to 10 experiments can complete almost
        # simultaneously (one batch of 10 workers finishing together).  Each
        # result dict holds ~140 MB (compressed_trajectories ~120 MB +
        # species_statistics ~20 MB).  The Semaphore(2) only lets 2 saves run
        # at once, so the remaining 8 dicts would sit in memory waiting — up to
        # 8 × 140 MB = 1.1 GB of RAM held idle.  Extracting here ensures that
        # as soon as this callback returns both BatchExecutor.results[name] and
        # ResultsBrowserView.results[name] hold only the ~few-KB trimmed version,
        # and only the 2 active save threads hold the heavy data at any time.
        _compressed_traj = result.pop('compressed_trajectories', [])
        _stats_obj = result.get('statistics') or {}
        _ss_full   = _stats_obj.pop('species_statistics', {})
        _tp_full   = _stats_obj.pop('time_points', [])
        if _ss_full:
            # Keep a tiny final-value-only summary in the in-memory result so
            # get_result() calls still return useful data for downstream display.
            _stats_obj['species_statistics'] = {
                _sid: {
                    'mean_final': (d.get('mean') or [None])[-1],
                    'std_final':  (d.get('std')  or [None])[-1],
                    'min_final':  (d.get('min')  or [None])[-1],
                    'max_final':  (d.get('max')  or [None])[-1],
                }
                for _sid, d in _ss_full.items()
            }

        # Add to results browser (existing functionality) — result is already tiny
        if self.results_browser:
            try:
                self.results_browser.add_result(name, result)
            except Exception as e:
                print(f"[ERROR] Failed to add result for '{name}': {e}")
                import traceback
                traceback.print_exc()
        
        # Auto-save experiment results (Phase 3 normalization).
        # CRITICAL: run in a background thread so disk I/O never blocks the
        # GTK main thread (blocking caused the app to be killed by the session
        # manager when 600 fsyncs accumulated in the GTK loop).
        #
        # GTK IS NOT THREAD-SAFE.  All GObject / widget accesses MUST happen
        # here (GTK main thread) BEFORE the thread starts.  The thread only
        # receives plain Python values (strings, dicts, Path) — it never
        # touches self.parent_panel or calls self._get_project_folder().
        import threading as _threading
        _run_folder_snapshot = self._current_run_folder          # Path or None
        _project_folder_snapshot = self._get_project_folder()   # str or None
        _id_to_name_snapshot: dict = {}
        _names_csv_rows_snapshot: list = []
        _subnet_mdl = getattr(self.parent_panel, 'subnet_model', None)
        if _subnet_mdl is not None:
            for _xp in getattr(_subnet_mdl, 'places', []):
                _id_to_name_snapshot[_xp.id] = getattr(_xp, 'name', _xp.id)
                _names_csv_rows_snapshot.append(
                    (_xp.id, getattr(_xp, 'name', _xp.id), 'place')
                )
            for _xt in getattr(_subnet_mdl, 'transitions', []):
                _id_to_name_snapshot[_xt.id] = getattr(_xt, 'name', _xt.id)
                _names_csv_rows_snapshot.append(
                    (_xt.id, getattr(_xt, 'name', _xt.id), 'transition')
                )
        _sem = self._auto_save_semaphore
        # Output granularity tier (G0..G5) snapshotted on the GTK main thread
        # so the background save thread never touches BatchExecutor live state.
        # Default G3 preserves legacy behaviour when the executor predates the
        # tier plumbing (defensive getattr).
        _output_tier_snapshot = getattr(self.batch_executor, '_output_tier', 'G3')

        def _throttled_save():
            _sem.acquire()
            try:
                self._auto_save_experiment(
                    name, result, _run_folder_snapshot,
                    _project_folder_snapshot, _id_to_name_snapshot,
                    _names_csv_rows_snapshot,
                    compressed_trajectories=_compressed_traj,
                    species_statistics_full=_ss_full,
                    time_points_full=_tp_full,
                    output_tier=_output_tier_snapshot,
                )
            finally:
                _sem.release()

        _save_thread = _threading.Thread(
            target=_throttled_save,
            args=(),
            daemon=True,
            name=f'auto-save-{name[:40]}',
        )
        _save_thread.start()
    
    def _auto_save_experiment(
        self,
        name: str,
        result: dict,
        run_folder=None,
        project_folder: str = None,
        id_to_name: dict = None,
        names_csv_rows: list = None,
        compressed_trajectories=None,
        species_statistics_full=None,
        time_points_full=None,
        output_tier: str = 'G3',
    ):
        """Auto-save experiment results to disk — all CSV format for easy analysis.

        Saves to: {project}/experiments/results/experiment_{name}_{timestamp}/

        THREAD-SAFETY: this method is called from a background thread.
        It must never access self.parent_panel or any GTK/GObject attribute.
        All GTK-owned data (project_folder, id_to_name, names_csv_rows) must
        be passed in as plain Python values captured in the GTK main thread.

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
            run_folder: Per-run Path captured in GTK thread.
            project_folder: Project base path string captured in GTK thread.
            id_to_name: {id: name} dict captured in GTK thread.
            names_csv_rows: List of (id, name, type) tuples for names.csv.
        """
        import csv as csv_mod
        import os as _os

        if id_to_name is None:
            id_to_name = {}
        if names_csv_rows is None:
            names_csv_rows = []

        # Output-tier gating (G0..G5) — single canonical authority shared with
        # the CLI / remote sweep path (shypn.cli.sweep_runner). Falls back to
        # G3 (legacy "everything") on any malformed tier string so callers
        # cannot accidentally lose data via a typo.
        try:
            from shypn.cli.sweep_config import OutputOptions as _OutputOptions
            _opts = _OutputOptions.from_dict({'tier': output_tier})
        except Exception:
            from shypn.cli.sweep_config import OutputOptions as _OutputOptions
            _opts = _OutputOptions()  # default G3
        _tier = _opts.tier
        # Tier predicates for the local writer:
        #   results.csv (full per-step mean/std trajectories) → G3+ only
        #   replicates.csv (per-replicate scalars)            → G1+
        #   fate_summary.csv (population fate stats)          → G1+ (paired with replicates.csv)
        #   mean_final_state.csv (endpoint stats)             → G2+
        #   replicates_trajectories/run_NNN.csv               → G4+
        #   config.csv, names.csv, .complete sentinel         → always
        _write_results_csv     = _tier >= 'G3'
        _write_replicates_csv  = _opts.write_replicates_csv          # G1+
        _write_endpoint_stats  = _opts.write_statistics_json         # G2+
        _write_per_rep_traj    = _opts.write_per_replicate_trajectories  # G4+
        _write_covariance      = _opts.write_covariance              # G5+

        # Sentinel raised inside a write block to signal a tier-gated skip.
        # Lets each existing try/except keep its current shape (the only
        # alternative would be a wholesale 12-space reindent of every block).
        class _TierSkip(Exception):
            pass

        def _fsync(path):
            """Flush write buffers for path.  No OS-level fsync to avoid
            blocking the save thread (and stalling CPU/IO) when many
            experiments complete in parallel.  The OS page cache writes
            data within seconds anyway; the .complete sentinel already
            guarantees that absence = partial save."""
            try:
                with open(path, 'a') as fh:
                    fh.flush()
            except OSError:
                pass

        # project_folder is passed in (captured in GTK thread — NOT safe to
        # call self._get_project_folder() here because it touches GTK objects).
        if not project_folder:
            return

        # run_folder is also passed in; no self attribute access needed.
        effective_run_folder = run_folder  # already captured; may be None

        # Create saver — nest inside per-run folder if one was created for this batch
        if effective_run_folder is not None:
            saver = BatchResultsSaver(
                base_path=str(effective_run_folder),
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
        # G3+ only: this is the full per-step time-series export.
        try:
            if not _write_results_csv:
                raise _TierSkip()
            # _export_csv needs the full species_statistics and time_points.
            # Both were extracted by the GTK main thread and passed in as params;
            # build a temporary enriched view of result for this call only.
            if species_statistics_full or time_points_full:
                _stats_for_export = dict(result.get('statistics') or {})
                if species_statistics_full:
                    _stats_for_export['species_statistics'] = species_statistics_full
                if time_points_full:
                    _stats_for_export['time_points'] = time_points_full
                _result_for_export = dict(result)
                _result_for_export['statistics'] = _stats_for_export
            else:
                _result_for_export = result
            self._export_csv(str(batch_path / 'results.csv'), name, _result_for_export)
            _fsync(batch_path / 'results.csv')
        except _TierSkip:
            pass
        except Exception as e:
            save_errors.append(f'results.csv: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save results.csv: {e}')

        # ── replicates.csv ── per-replicate outcomes (standard tabular)
        # G1+ only. At G0 the entire per-replicate scalar export is skipped
        # (along with fate_summary.csv which lives inside the same try-block).
        try:
            if not _write_replicates_csv:
                raise _TierSkip()
            replicate_data = result.get('replicate_data', [])
            trajectory_summary = result.get('trajectory_summary', [])
            # Use the explicitly-passed compressed_trajectories (extracted on GTK
            # main thread to keep peak RAM bounded at Semaphore(2) × ~140 MB).
            _compressed = compressed_trajectories if compressed_trajectories is not None else []
            n = max(len(replicate_data), len(trajectory_summary))

            # Build {replicate_id: CompressionResult} for fast lookup
            compressed_by_id = {cr.replicate_id: cr for cr in _compressed}

            # id→name mapping was captured before this thread started (GTK main
            # thread); use it directly — do NOT access self.parent_panel here.
            _id_to_name_early: dict = id_to_name
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
        except _TierSkip:
            pass
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
        # loading the full model.  Data captured in GTK thread (names_csv_rows).
        try:
            if names_csv_rows:
                with open(batch_path / 'names.csv', 'w', newline='') as f:
                    writer = csv_mod.writer(f)
                    writer.writerow(['id', 'name', 'type'])
                    writer.writerows(names_csv_rows)
                _fsync(batch_path / 'names.csv')
        except Exception as e:
            save_errors.append(f'names.csv: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save names.csv: {e}')

        # ── mean_final_state.csv ── flat, easily parseable final SS summary
        # Standard tabular CSV: pandas.read_csv(path, comment='#') works directly.
        # One row per species with final-timepoint mean and std.
        # G2+ only (endpoint statistics tier).
        try:
            if not _write_endpoint_stats:
                raise _TierSkip()
            stats = result.get('statistics', {})
            species_stats = species_statistics_full if species_statistics_full is not None else stats.get('species_statistics', {})
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
        except _TierSkip:
            pass
        except Exception as e:
            save_errors.append(f'mean_final_state.csv: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save mean_final_state.csv: {e}')

        # ── replicates_trajectories/ ── one δ-compressed CSV per replicate
        # Each file is self-describing (comment header + col_schema line) so
        # analysis scripts need no external sidecar.  Skipped gracefully when
        # no compressed data is available (e.g. on error runs).
        # G4+ only (per-replicate trajectory tier).
        try:
            if not _write_per_rep_traj:
                raise _TierSkip()
            compressed_trajectories_data = compressed_trajectories if compressed_trajectories is not None else []
            if compressed_trajectories_data:
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

                for cr in compressed_trajectories_data:
                    _status = _status_by_order.get(cr.replicate_id, 'completed')
                    csv_path = traj_dir / f'run_{cr.replicate_id + 1:03d}.csv'
                    CompressedTrajectoryWriter.write(
                        path=csv_path,
                        result=cr,
                        experiment_name=name,
                        status=_status,
                        id_to_name=_id_to_name or None,
                    )
                    # NOTE: No per-file fsync here — 200 fsyncs in the main/save
                    # thread would block for tens of seconds on Hyper-V virtual
                    # disks, causing the app to appear frozen and be killed.
                    # The OS page-cache flushes these files within seconds anyway.
                print(f'[AUTO-SAVE] Saved {len(compressed_trajectories_data)} compressed trajectories → {traj_dir.name}/')
        except _TierSkip:
            pass
        except Exception as e:
            save_errors.append(f'replicates_trajectories/: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save replicates_trajectories/: {e}')

        # ── covariance.json ── G5+ — mean / cov / corr over per-replicate
        # final-state place values. Schema matches the CLI/remote writer
        # (SweepOutputManager._write_covariance) so downstream analysis is
        # path-agnostic. Skipped when fewer than 2 replicates have usable
        # final values.
        try:
            if not _write_covariance:
                raise _TierSkip()
            _ct = compressed_trajectories if compressed_trajectories is not None else []
            if len(_ct) < 2:
                raise _TierSkip()
            import numpy as _np
            # Stable column order: union of keys across replicates, sorted.
            _all_pids: set = set()
            for _cr in _ct:
                _all_pids.update(_cr.final_values().keys())
            _pids = sorted(_all_pids)
            if not _pids:
                raise _TierSkip()
            _N = len(_ct)
            _P = len(_pids)
            _finals = _np.full((_N, _P), _np.nan, dtype=float)
            for _ri, _cr in enumerate(_ct):
                _fv = _cr.final_values()
                for _ci, _pid in enumerate(_pids):
                    _v = _fv.get(_pid)
                    if _v is not None:
                        try:
                            _finals[_ri, _ci] = float(_v)
                        except (TypeError, ValueError):
                            pass
            _valid = ~_np.isnan(_finals).any(axis=1)
            _clean = _finals[_valid]
            if _clean.shape[0] < 2:
                raise _TierSkip()
            _mean = _clean.mean(axis=0)
            _cov = _np.atleast_2d(_np.cov(_clean, rowvar=False, ddof=1))
            _std = _np.sqrt(_np.diag(_cov))
            with _np.errstate(divide='ignore', invalid='ignore'):
                _denom = _np.outer(_std, _std)
                _corr = _np.where(_denom > 0, _cov / _denom, _np.nan)

            import json as _json_cov
            _payload = {
                'n_replicates': int(_clean.shape[0]),
                'n_replicates_dropped': int((~_valid).sum()),
                'place_ids': _pids,
                'place_names': [
                    (locals().get('_id_to_name_early') or id_to_name).get(_pid, _pid)
                    for _pid in _pids
                ],
                'mean': [float(v) for v in _mean],
                'covariance': [[float(v) for v in row] for row in _cov],
                'correlation': [
                    [None if _np.isnan(v) else float(v) for v in row]
                    for row in _corr
                ],
            }
            with open(batch_path / 'covariance.json', 'w', encoding='utf-8') as _cf:
                _json_cov.dump(_payload, _cf, indent=2)
            _fsync(batch_path / 'covariance.json')
        except _TierSkip:
            pass
        except Exception as e:
            save_errors.append(f'covariance.json: {e}')
            print(f'[AUTO-SAVE] Warning: Failed to save covariance.json: {e}')

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

        # Heavy fields (compressed_trajectories, species_statistics, time_points)
        # were already extracted and stripped by _on_experiment_result on the GTK
        # main thread before this function was called — no cleanup needed here.

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

    def _confirm_sweep_event_collisions(self, errors, warnings) -> bool:
        """Show a modal explaining sweep / event collisions.

        Returns ``True`` if the operator chooses to dispatch anyway
        (errors are demoted to a warning recorded in the config as
        ``superposition_intent: 'complexity_reduction'``), ``False`` if
        they cancel.

        Pure errors must be acknowledged with a separate explicit
        "Dispatch anyway" button so a casual click on "OK" cannot bypass
        the safety check.

        The detail text is rendered in a selectable, copy-able TextView
        and **also** logged to the Python logger at WARNING level so the
        operator can scroll back through the launching terminal even
        after dismissing the dialog.
        """
        import logging as _lg
        _log = _lg.getLogger(__name__)

        # ── Plain-text payload (logged + clipboard-copyable) ─────────
        plain_lines = []
        if errors:
            plain_lines.append('ERRORS (would silently superimpose two writers):')
            for it in errors:
                plain_lines.append(
                    f"  [{it.get('code', '')}] "
                    f"path={it.get('path', '?')}: {it.get('message', '')}"
                )
            plain_lines.append('')
        if warnings:
            plain_lines.append('WARNINGS:')
            for it in warnings:
                plain_lines.append(
                    f"  [{it.get('code', '')}] "
                    f"path={it.get('path', '?')}: {it.get('message', '')}"
                )
            plain_lines.append('')
        if errors:
            plain_lines.append(
                'Recommended actions: change the sweep target, or '
                'remove/disable the colliding event(s).  Click '
                "'Dispatch anyway' only if the superposition is "
                'genuinely intentional — it will be recorded in the '
                'sweep config.'
            )
        plain_text = '\n'.join(plain_lines)

        # Persist to the launching terminal so the user can review later.
        for it in errors:
            _log.warning("[COLLISION/%s] %s",
                         it.get('code'), it.get('message'))
        for it in warnings:
            _log.warning("[COLLISION/%s] %s",
                         it.get('code'), it.get('message'))

        # ── Build the dialog with a selectable TextView ──────────────
        dialog = Gtk.Dialog(
            title=('Sweep / event collision detected'
                   if errors else 'Sweep / event configuration warnings'),
            transient_for=(self.get_widget().get_toplevel()
                           if self.get_widget() else None),
            flags=Gtk.DialogFlags.MODAL,
        )
        dialog.set_default_size(640, 360)

        # Header row with icon + summary
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.set_margin_start(12)
        header.set_margin_end(12)
        header.set_margin_top(12)
        header.set_margin_bottom(6)
        icon_name = 'dialog-error' if errors else 'dialog-warning'
        header.pack_start(
            Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG),
            False, False, 0,
        )
        summary = Gtk.Label()
        summary.set_xalign(0)
        n_e, n_w = len(errors), len(warnings)
        summary.set_markup(
            f"<b>{n_e} error(s) and {n_w} warning(s) detected</b>\n"
            "Details below are <i>selectable / copyable</i>; the same "
            "text was also logged to the launching terminal."
        )
        summary.set_line_wrap(True)
        header.pack_start(summary, True, True, 0)
        dialog.get_content_area().pack_start(header, False, False, 0)

        # Scrollable selectable detail view
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_margin_start(12)
        scroller.set_margin_end(12)
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)

        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(True)
        text_view.set_monospace(True)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.get_buffer().set_text(plain_text)
        scroller.add(text_view)
        dialog.get_content_area().pack_start(scroller, True, True, 0)

        # Buttons
        copy_btn = dialog.add_button('Copy to clipboard', 1)
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        if errors:
            dialog.add_button('Dispatch anyway', Gtk.ResponseType.OK)
        else:
            dialog.add_button('Continue', Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)

        def _on_copy(_btn):
            try:
                from gi.repository import Gdk
                clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clip.set_text(plain_text, -1)
                copy_btn.set_label('Copied ✓')
            except Exception as exc:
                _log.warning("clipboard copy failed: %s", exc)
        copy_btn.connect('clicked', _on_copy)

        dialog.show_all()
        # Loop until the user picks a non-Copy button (Copy returns 1
        # but should not close the dialog).
        while True:
            response = dialog.run()
            if response != 1:
                break
        dialog.destroy()
        return response == Gtk.ResponseType.OK
    
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

        # Resume any remote sweeps whose summary fetch was interrupted
        # (GUI close / reset / SSH drop).  The server-side run is
        # already complete; we just need to pull summary.csv +
        # config.json so the Experiment Results browser can list it.
        # Runs in a daemon thread so the UI stays responsive.
        self._schedule_pending_dispatch_recovery()

        # Auto-load the most recent on-disk sweep run so the Results
        # browser is populated when a project is opened (without
        # requiring a sweep to be in flight or a manual reload).
        self._scan_local_run_dirs(latest_only=True)
    
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
