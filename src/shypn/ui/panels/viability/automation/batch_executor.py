#!/usr/bin/env python3
"""Batch Executor - Backend for running queued experiments.

Executes experiments sequentially, tracks progress, handles errors,
and integrates with ReplicateRunner for actual simulation execution.

Author: Simão Eugénio
Date: December 7, 2025
"""

import threading
import time
import numpy as np
from typing import Optional, Callable, Dict, Any, List


class BatchExecutor:
    """Backend for executing queued experiments with progress tracking.
    
    Features:
    - Sequential or parallel execution
    - Progress callbacks for UI updates
    - Cancellation support
    - Error handling and recovery
    """
    
    def __init__(self, experiment_manager, model_canvas=None, parent_panel=None):
        """Initialize batch executor.
        
        Args:
            experiment_manager: ExperimentManager with snapshots
            model_canvas: ModelCanvas for accessing model
            parent_panel: ViabilityPanel instance (for subnet access)
        """
        self.experiment_manager = experiment_manager
        self.model_canvas = model_canvas
        self.parent_panel = parent_panel
        
        # Execution state
        self.is_running = False
        self.is_cancelled = False
        self.current_experiment = None
        self.executor_thread = None
        
        # Results storage
        self.results = {}  # experiment_name -> results_dict
    
    def run_batch(
        self,
        experiments: List[tuple],
        replicates: int = 500,
        duration: float = 100.0,
        progress_callback: Optional[Callable] = None,
        complete_callback: Optional[Callable] = None,
        experiment_result_callback: Optional[Callable] = None
    ):
        """Run batch of experiments asynchronously.
        
        Args:
            experiments: List of (index, name, snapshot_index) tuples
            replicates: Number of replicates per experiment
            duration: Simulation duration
            progress_callback: Called with (exp_index, status, progress)
            complete_callback: Called when batch completes
            experiment_result_callback: Called with (name, result) when each experiment completes
        """
        if self.is_running:
            raise RuntimeError("Batch execution already in progress")
        
        self.is_running = True
        self.is_cancelled = False
        
        # CRITICAL: Extract model and subnet data in main thread BEFORE starting background thread
        # Accessing GTK widgets from background thread causes deadlock
        print("[EXTRACT] Starting model extraction...")
        import time as time_module
        extraction_start = time_module.time()
        
        try:
            # Step 1: Get canvas manager
            print("[EXTRACT] Getting canvas manager...")
            t1 = time_module.time()
            canvas_manager = self._get_model()
            if not canvas_manager:
                raise RuntimeError("No model available for simulation")
            print(f"[EXTRACT] Canvas manager obtained in {time_module.time()-t1:.3f}s")
            
            # Step 2: Convert to DocumentModel
            print("[EXTRACT] Converting to DocumentModel...")
            t2 = time_module.time()
            base_model = canvas_manager.to_document_model()
            print(f"[EXTRACT] DocumentModel created in {time_module.time()-t2:.3f}s")
            print(f"[EXTRACT] Model has {len(base_model.places)} places, {len(base_model.transitions)} transitions, {len(base_model.arcs)} arcs")
            
            # Step 3: Extract subnet
            print("[EXTRACT] Extracting subnet...")
            t3 = time_module.time()
            subnet_data = self._extract_subnet(canvas_manager)
            print(f"[EXTRACT] Subnet extracted in {time_module.time()-t3:.3f}s")
            
            if not subnet_data or not subnet_data['transitions']:
                raise RuntimeError("No transitions available for simulation")
            
            print(f"[EXTRACT] Total extraction time: {time_module.time()-extraction_start:.3f}s")
            print(f"[EXTRACT] Subnet: {len(subnet_data['places'])} places, {len(subnet_data['transitions'])} transitions, {len(subnet_data['arcs'])} arcs")
            
            # Save baseline parameters to reset between experiments
            print("[EXTRACT] Saving baseline parameters...")
            baseline_params = self._save_current_parameters(base_model, subnet_data)
            print(f"[EXTRACT] Baseline saved: {len(baseline_params['place_markings'])} places, {len(baseline_params['transition_rates'])} transitions")
        except Exception as e:
            self.is_running = False
            print(f"[ERROR] Failed to extract model: {e}")
            if complete_callback:
                complete_callback()
            raise
        
        # Start execution thread with pre-extracted data
        self.executor_thread = threading.Thread(
            target=self._execute_batch,
            args=(experiments, replicates, duration, progress_callback, complete_callback, experiment_result_callback, base_model, subnet_data, baseline_params),
            daemon=True
        )
        self.executor_thread.start()
    
    def cancel(self):
        """Cancel running batch execution."""
        if not self.is_running:
            return
        
        print("[DEBUG] Cancelling batch execution...")
        self.is_cancelled = True
        
        # Wait for thread to finish with timeout
        if self.executor_thread and self.executor_thread.is_alive():
            self.executor_thread.join(timeout=2.0)
            if self.executor_thread.is_alive():
                print("[WARNING] Executor thread did not terminate within timeout")
    
    def _execute_batch(
        self,
        experiments: List[tuple],
        replicates: int,
        duration: float,
        progress_callback: Optional[Callable],
        complete_callback: Optional[Callable],
        experiment_result_callback: Optional[Callable],
        base_model,  # Pre-extracted DocumentModel
        subnet_data: dict,  # Pre-extracted subnet data
        baseline_params: dict  # Baseline parameters to reset between experiments
    ):
        """Execute batch in background thread - SEQUENTIAL EXECUTION.
        
        Args:
            experiments: List of (index, name, snapshot_index) tuples
            replicates: Number of replicates per experiment
            duration: Simulation duration
            progress_callback: Callback for progress updates (queue_index, status, progress_str)
            complete_callback: Callback when complete
            experiment_result_callback: Callback for each experiment result (name, result)
            base_model: Pre-extracted DocumentModel (from main thread)
            subnet_data: Pre-extracted subnet dict (from main thread)
            baseline_params: Baseline parameter values to reset model between experiments
        """
        print(f"[BATCH] Starting batch execution: {len(experiments)} experiments, {replicates} replicates each")
        
        try:
            total = len(experiments)
            
            for i, (queue_index, name, snapshot_index) in enumerate(experiments):
                # Check cancellation BEFORE starting each experiment
                if self.is_cancelled:
                    print(f"[BATCH] Cancelled - marking remaining {total - i} experiments as cancelled")
                    # Mark remaining experiments as cancelled
                    if progress_callback:
                        progress_callback(queue_index, "cancelled", "Cancelled")
                    continue  # Skip to next experiment
                
                print(f"[BATCH] Experiment {i+1}/{total}: '{name}' (queue_index={queue_index})")
                
                # Reset model to baseline before each experiment to avoid state corruption
                print(f"[BATCH] Resetting model to baseline...")
                self._restore_parameters(base_model, subnet_data, baseline_params)
                print(f"[BATCH] Model reset complete")
                
                # CRITICAL: Set status to running BEFORE execution
                self.current_experiment = name
                if progress_callback:
                    progress_callback(queue_index, "running", "0%")
                    print(f"[BATCH] Status set to RUNNING for experiment {queue_index}")
                    
                    # Brief pause to let UI update process
                    time.sleep(0.05)  # Minimal delay for rate limiting
                
                # Execute single experiment with error handling
                try:
                    # Create progress callback with proper closure
                    # Capture queue_index by value to avoid closure bug
                    def exp_progress_callback(p, idx=queue_index):
                        """Progress callback: p is 0.0 to 1.0 float."""
                        if progress_callback and 0.0 <= p <= 1.0:
                            percentage_str = f"{int(p*100)}%"
                            progress_callback(idx, "running", percentage_str)
                    
                    # Run experiment with pre-extracted model and subnet
                    print(f"[BATCH] Running simulation for '{name}'...")
                    result = self._run_single_experiment(
                        name,
                        snapshot_index,
                        replicates,
                        duration,
                        exp_progress_callback,
                        base_model,
                        subnet_data
                    )
                    
                    # CRITICAL: Verify result is valid before storing
                    if not result:
                        raise ValueError("Simulation returned None/empty result")
                    
                    if 'error' in result:
                        raise ValueError(f"Simulation error: {result['error']}")
                    
                    # Store result BEFORE marking as completed
                    self.results[name] = result
                    print(f"[BATCH] Result stored for '{name}': {result.get('n_replicates', 0)} replicates")
                    
                    # Call result callback immediately for incremental display
                    if experiment_result_callback:
                        from gi.repository import GLib
                        # Schedule in main thread to update UI
                        GLib.idle_add(lambda n=name, r=result: experiment_result_callback(n, r) or False)
                        print(f"[BATCH] Result callback scheduled for '{name}'")
                    
                    # CRITICAL: Mark as completed ONLY after result is stored
                    if progress_callback:
                        progress_callback(queue_index, "completed", "100%")
                        print(f"[BATCH] Status set to COMPLETED for experiment {queue_index}")
                        
                        # Brief pause to let UI update process
                        # (UI updates are async via GLib.idle_add, this just prevents hammering)
                        time.sleep(0.05)  # Minimal delay for rate limiting
                    
                except Exception as e:
                    print(f"[BATCH] ERROR in experiment '{name}': {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Update status to failed
                    error_msg = str(e)[:100]  # Truncate long errors
                    if progress_callback:
                        progress_callback(queue_index, "failed", error_msg)
                        print(f"[BATCH] Status set to FAILED for experiment {queue_index}: {error_msg}")
                    
                    # Store error result
                    self.results[name] = {
                        "error": str(e),
                        "name": name,
                        "snapshot_index": snapshot_index
                    }
            
            print(f"[BATCH] Batch execution finished - {'CANCELLED' if self.is_cancelled else 'COMPLETED'}")
            
        except Exception as e:
            print(f"[BATCH] CRITICAL ERROR in batch execution: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Reset execution state
            self.is_running = False
            self.current_experiment = None
            
            print(f"[BATCH] Calling completion callback (cancelled={self.is_cancelled})")
            
            if complete_callback:
                # CRITICAL: Schedule callback in main thread - don't block background thread
                from gi.repository import GLib
                cancelled = self.is_cancelled
                GLib.idle_add(lambda: complete_callback(cancelled=cancelled), priority=GLib.PRIORITY_HIGH_IDLE)
                print("[BATCH] Completion callback scheduled in main thread")
            else:
                print("[BATCH] No completion callback provided")
    
    def _run_single_experiment(
        self,
        name: str,
        snapshot_index: int,
        replicates: int,
        duration: float,
        progress_callback: Optional[Callable] = None,
        base_model = None,  # Pre-extracted DocumentModel
        subnet_data: dict = None  # Pre-extracted subnet data
    ) -> Dict[str, Any]:
        """Run single experiment with replicates - MUST return valid result dict.
        
        Args:
            name: Experiment name
            snapshot_index: Snapshot index in ExperimentManager
            replicates: Number of replicates to run
            duration: Simulation duration
            progress_callback: Called with progress (0.0 to 1.0 float)
            base_model: Pre-extracted DocumentModel (from main thread)
            subnet_data: Pre-extracted subnet dict (from main thread)
        
        Returns:
            Dictionary with results (ALWAYS returns dict, never None):
                - name: Experiment name
                - snapshot_index: Snapshot index
                - n_replicates: Number of successful replicates
                - statistics: Summary statistics dict
                - duration: Actual execution time
                - error: Error message (if failed)
        """
        print(f"[EXPERIMENT] Running '{name}' (snapshot {snapshot_index}): {replicates} replicates, {duration}s duration")
        start_time = time.time()
        
        try:
            # Get snapshot
            if snapshot_index >= len(self.experiment_manager.snapshots):
                raise ValueError(f"Invalid snapshot index: {snapshot_index}")
            
            snapshot = self.experiment_manager.snapshots[snapshot_index]
            print(f"[EXPERIMENT] Snapshot loaded: {snapshot.name}")
            
            # CRITICAL FIX: Create a fresh DocumentModel from the subnet data
            # The subnet is extracted correctly, but we were passing the full base_model
            # to the simulator, causing it to run on wrong model structure (11 places vs 5)
            from shypn.data.canvas.document_model import DocumentModel
            
            # Create new model with only subnet elements
            model = DocumentModel()
            model.places = list(subnet_data['places'])
            model.transitions = list(subnet_data['transitions'])
            model.arcs = list(subnet_data['arcs'])
            
            print(f"[EXPERIMENT] Using subnet model: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")
            
            # Apply snapshot parameters to subnet model (pass None since model IS the subnet)
            print(f"[EXPERIMENT] Applying snapshot parameters...")
            self._apply_snapshot_to_model(snapshot, model, None)
            print(f"[EXPERIMENT] Snapshot parameters applied: {len(snapshot.place_markings)} places, {len(snapshot.transition_rates)} transitions, {len(snapshot.arc_weights)} arcs")
            
            # CRITICAL: Verify arc types are preserved (test arcs should stay test arcs)
            print(f"[EXPERIMENT] Verifying arc types after snapshot application...")
            for arc in model.arcs:
                arc_type = arc.arc_type if hasattr(arc, 'arc_type') else 'unknown'
                arc_class = arc.__class__.__name__
                print(f"[EXPERIMENT] Arc {arc.id}: type={arc_type}, class={arc_class}, weight={arc.weight}")
                # Verify test arcs haven't been corrupted
                if arc_type == 'test' and arc_class != 'TestArc':
                    print(f"[ERROR] Test arc {arc.id} has wrong class: {arc_class}!")
            
            # Report initial progress
            if progress_callback:
                progress_callback(0.0)
            
            # Run replicates using ReplicateRunner
            from shypn.engine.simulation.replicate_runner import ReplicateRunner
            
            print(f"[EXPERIMENT] Creating ReplicateRunner...")
            sim_start = time.time()
            runner = ReplicateRunner(model)
            print(f"[EXPERIMENT] ReplicateRunner created in {time.time()-sim_start:.3f}s")
            
            print(f"[EXPERIMENT] Starting simulation: {replicates} replicates x {duration}s duration")
            print(f"[EXPERIMENT] Model size: {len(model.places)} places, {len(model.transitions)} transitions")
            
            # Count arc types for debugging
            arc_types = {}
            for arc in model.arcs:
                atype = arc.arc_type if hasattr(arc, 'arc_type') else 'normal'
                arc_types[atype] = arc_types.get(atype, 0) + 1
            print(f"[EXPERIMENT] Arc types: {arc_types}")
            
            # Run all replicates (use_parallel=False for SEQUENTIAL execution)
            sim_exec_start = time.time()
            print(f"[EXPERIMENT] About to call runner.run_replicates()...")
            results = runner.run_replicates(
                n=replicates,
                use_parallel=False,  # SEQUENTIAL execution of replicates
                use_tau_leaping=True,
                duration=duration,
                seed_base=42,
                verbose=False,
                progress_callback=progress_callback
            )
            print(f"[EXPERIMENT] runner.run_replicates() completed in {time.time()-sim_exec_start:.3f}s")
            
            print(f"[EXPERIMENT] Simulation execution took {time.time()-sim_exec_start:.3f}s")
            
            print(f"[EXPERIMENT] Simulation complete: {len(results) if results else 0} successful replicates")
            
            # Report 100% progress
            if progress_callback:
                progress_callback(1.0)
            
            elapsed_time = time.time() - start_time
            
            # CRITICAL: Compute statistics
            if results and len(results) > 0:
                print(f"[EXPERIMENT] Computing statistics for {len(results)} replicates...")
                statistics = runner.compute_statistics(results)
                statistics['elapsed_time'] = elapsed_time
                statistics['n_replicates'] = len(results)
                print(f"[EXPERIMENT] Statistics computed successfully")
                print(f"[EXPERIMENT] Statistics keys: {statistics.keys()}")
                if 'species_statistics' in statistics:
                    print(f"[EXPERIMENT] Species count: {len(statistics['species_statistics'])}")
                    for species_id in list(statistics['species_statistics'].keys())[:2]:
                        species_data = statistics['species_statistics'][species_id]
                        mean_len = len(species_data.get('mean', []))
                        print(f"[EXPERIMENT]   Species '{species_id}': mean length = {mean_len}")
                if 'time_points' in statistics:
                    print(f"[EXPERIMENT] Time points length: {len(statistics['time_points'])}")
            else:
                print(f"[EXPERIMENT] WARNING: No successful replicates")
                statistics = {
                    'n_replicates': 0,
                    'elapsed_time': elapsed_time,
                    'error': 'No successful replicates'
                }
            
            # Store lightweight trajectory summary (first, last, and metadata only)
            # Full trajectories can be large - store only what's needed for visualization
            trajectory_summary = []
            if results:
                for i, traj in enumerate(results[:100]):  # Limit to 100 for memory
                    if 'error' not in traj:
                        trajectory_summary.append({
                            'replicate_id': i,
                            'seed': traj.get('seed'),
                            'n_timepoints': len(traj.get('time_points', [])),
                            'final_time': traj.get('time_points', [0])[-1] if traj.get('time_points') else 0
                        })
            
            # Return complete result dict with statistics (plottable from statistics)
            result = {
                'name': name,
                'snapshot_index': snapshot_index,
                'trajectory_summary': trajectory_summary,  # Lightweight summary
                'n_replicates': len(results) if results else 0,
                'statistics': statistics,  # Contains mean/std/percentiles for plotting
                'duration': elapsed_time
            }
            
            print(f"[EXPERIMENT] Result dict created: {result['n_replicates']} replicates, {elapsed_time:.2f}s")
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = str(e)
            print(f"[EXPERIMENT] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # CRITICAL: ALWAYS return valid dict, even on error
            return {
                'name': name,
                'snapshot_index': snapshot_index,
                'trajectory_summary': [],
                'n_replicates': 0,
                'statistics': {
                    'n_replicates': 0,
                    'elapsed_time': elapsed_time,
                    'error': error_msg
                },
                'duration': elapsed_time,
                'error': error_msg
            }
    
    def _get_model(self):
        """Get current model from parent panel.
        
        Returns:
            ModelCanvasManager (with .places, .transitions, .arcs) or None
        """
        # Use parent panel's method if available (preferred)
        if self.parent_panel and hasattr(self.parent_panel, '_get_current_model'):
            return self.parent_panel._get_current_model()
        
        # Fallback: try to get via model_canvas directly
        if not self.model_canvas:
            return None
        
        drawing_area = self.model_canvas.get_current_document()
        if not drawing_area:
            return None
        
        # Try canvas_managers dict
        if hasattr(self.model_canvas, 'canvas_managers'):
            manager = self.model_canvas.canvas_managers.get(drawing_area)
            if manager:
                return manager
        
        # Last resort: try get_canvas_manager method
        if hasattr(self.model_canvas, 'get_canvas_manager'):
            return self.model_canvas.get_canvas_manager(drawing_area)
        
        return None
    
    def _extract_subnet(self, model):
        """Extract subnet elements from parent panel's selected localities.
        
        Args:
            model: ModelCanvasManager instance (with .places, .transitions, .arcs)
        
        Returns:
            dict: Subnet with 'places', 'transitions', 'arcs' lists
        """
        if not self.parent_panel or not hasattr(self.parent_panel, 'selected_localities'):
            # No parent panel - return full model as subnet
            return {
                'places': list(model.places) if hasattr(model, 'places') else [],
                'transitions': list(model.transitions) if hasattr(model, 'transitions') else [],
                'arcs': list(model.arcs) if hasattr(model, 'arcs') else []
            }
        
        # Check if there are selected localities
        if not self.parent_panel.selected_localities:
            # No localities selected - return full model as subnet for backwards compatibility
            print("[SUBNET] No localities selected, using full model")
            return {
                'places': list(model.places) if hasattr(model, 'places') else [],
                'transitions': list(model.transitions) if hasattr(model, 'transitions') else [],
                'arcs': list(model.arcs) if hasattr(model, 'arcs') else []
            }
        
        print(f"[SUBNET] Extracting subnet from {len(self.parent_panel.selected_localities)} selected localities")
        
        # Use sets for O(1) membership checking instead of lists
        subnet_places_set = set()
        subnet_transitions_set = set()
        subnet_arcs_set = set()
        
        # Build lookup dictionaries for O(1) access (optimization for large models)
        transitions_by_id = {t.id: t for t in model.transitions}
        places_by_id = {p.id: p for p in model.places}
        arcs_by_id = {a.id: a for a in model.arcs}
        
        # Collect all elements from selected localities
        for transition_id, data in self.parent_panel.selected_localities.items():
            locality = data.get('locality')
            if not locality:
                continue
            
            # Get transition object
            trans_obj = getattr(locality, 'transition', None)
            if not trans_obj:
                trans_obj = transitions_by_id.get(transition_id)
            if trans_obj:
                subnet_transitions_set.add(trans_obj)
            
            # Get place objects (including catalyst places from test arcs)
            all_places = set(locality.input_places) | set(locality.output_places) | set(locality.catalyst_places)
            for place in all_places:
                if hasattr(place, 'id'):
                    subnet_places_set.add(place)
                else:
                    place_obj = places_by_id.get(place)
                    if place_obj:
                        subnet_places_set.add(place_obj)
            
            # Get arc objects (including catalyst arcs / test arcs)
            all_arcs = set(locality.input_arcs) | set(locality.output_arcs) | set(locality.catalyst_arcs)
            for arc in all_arcs:
                if hasattr(arc, 'id'):
                    subnet_arcs_set.add(arc)
                else:
                    arc_obj = arcs_by_id.get(arc)
                    if arc_obj:
                        subnet_arcs_set.add(arc_obj)
        
        print(f"[SUBNET] Extracted {len(subnet_places_set)} places, {len(subnet_transitions_set)} transitions, {len(subnet_arcs_set)} arcs")
        
        return {
            'places': list(subnet_places_set),
            'transitions': list(subnet_transitions_set),
            'arcs': list(subnet_arcs_set)
        }
    
    def _save_current_parameters(self, model, subnet=None):
        """Save current parameter values before applying snapshot.
        
        Args:
            model: DocumentModel with current values
            subnet: Optional subnet dict
            
        Returns:
            dict: Saved parameter values that can be restored later
        """
        # Determine which objects to save
        if subnet:
            places = subnet['places']
            transitions = subnet['transitions']
            arcs = subnet['arcs']
        else:
            places = model.places if hasattr(model, 'places') else []
            transitions = model.transitions if hasattr(model, 'transitions') else []
            arcs = model.arcs if hasattr(model, 'arcs') else []
        
        saved = {
            'place_markings': {},
            'transition_rates': {},
            'arc_weights': {}
        }
        
        # Save place markings
        for place in places:
            saved['place_markings'][place.id] = place.tokens
        
        # Save transition rates (preserve both numeric and formula types)
        for trans in transitions:
            # Save the rate as-is (could be float or string formula)
            saved['transition_rates'][trans.id] = trans.rate
        
        # Save arc weights and properties (handle all arc types)
        for arc in arcs:
            # Store all relevant arc properties
            arc_info = {
                'weight': arc.weight,
                'arc_type': arc.arc_type if hasattr(arc, 'arc_type') else 'normal',
                'threshold': getattr(arc, 'threshold', None),
                'is_curved': getattr(arc, 'is_curved', False),
                'control_offset_x': getattr(arc, 'control_offset_x', 0.0),
                'control_offset_y': getattr(arc, 'control_offset_y', 0.0),
            }
            saved['arc_weights'][arc.id] = arc_info
        
        return saved
    
    def _restore_parameters(self, model, subnet, saved_values):
        """Restore parameter values after experiment.
        
        Args:
            model: DocumentModel to restore
            subnet: Optional subnet dict
            saved_values: Dictionary returned by _save_current_parameters
        """
        # Determine which objects to restore
        if subnet:
            places = subnet['places']
            transitions = subnet['transitions']
            arcs = subnet['arcs']
        else:
            places = model.places if hasattr(model, 'places') else []
            transitions = model.transitions if hasattr(model, 'transitions') else []
            arcs = model.arcs if hasattr(model, 'arcs') else []
        
        # Restore place markings
        for place_id, marking in saved_values['place_markings'].items():
            place = next((p for p in places if p.id == place_id), None)
            if place:
                place.tokens = int(marking)
                if hasattr(place, 'marking'):
                    place.marking = int(marking)
        
        # Restore transition rates (handle both numeric and formula types)
        for trans_id, rate in saved_values['transition_rates'].items():
            trans = next((t for t in transitions if t.id == trans_id), None)
            if trans:
                # Preserve the type - don't convert formulas to float
                trans.rate = rate
        
        # Restore arc weights and properties (handle all arc types)
        for arc_id, arc_info in saved_values['arc_weights'].items():
            arc = next((a for a in arcs if a.id == arc_id), None)
            if arc:
                # Handle both old format (int/dict with only weight) and new format (full dict)
                if isinstance(arc_info, dict):
                    arc.weight = float(arc_info.get('weight', 1.0))
                    # Restore threshold if present
                    if 'threshold' in arc_info and arc_info['threshold'] is not None:
                        arc.threshold = arc_info['threshold']
                    # Restore curve properties if present
                    if 'is_curved' in arc_info:
                        arc.is_curved = arc_info['is_curved']
                    if 'control_offset_x' in arc_info:
                        arc.control_offset_x = arc_info['control_offset_x']
                    if 'control_offset_y' in arc_info:
                        arc.control_offset_y = arc_info['control_offset_y']
                else:
                    # Old format - just weight
                    arc.weight = float(arc_info)
    
    def _apply_snapshot_to_model(self, snapshot, model, subnet=None):
        """Apply snapshot parameter values to model (subnet-aware).
        
        Args:
            snapshot: ExperimentSnapshot with parameter values
            model: DocumentModel to update (with .places, .transitions, .arcs)
            subnet: Optional subnet dict (if None, applies to full model)
        """
        # Determine which objects to update
        if subnet:
            places = subnet['places']
            transitions = subnet['transitions']
            arcs = subnet['arcs']
        else:
            places = model.places if hasattr(model, 'places') else []
            transitions = model.transitions if hasattr(model, 'transitions') else []
            arcs = model.arcs if hasattr(model, 'arcs') else []
        
        # Apply place markings (only to subnet places)
        for place_id, marking in snapshot.place_markings.items():
            place = next((p for p in places if p.id == place_id), None)
            if place:
                place.tokens = int(marking)
                place.marking = int(marking)
        
        # Apply transition rates (only to subnet transitions)
        # Handle both numeric rates and kinetic formulas
        for trans_id, rate in snapshot.transition_rates.items():
            trans = next((t for t in transitions if t.id == trans_id), None)
            if trans:
                # Check if rate is numeric or a formula string
                if isinstance(rate, str):
                    # It's a kinetic formula - keep as string
                    trans.rate = rate
                else:
                    # It's numeric - convert to float
                    try:
                        trans.rate = float(rate)
                    except (ValueError, TypeError) as e:
                        print(f"[WARNING] Could not convert rate for {trans_id}: {rate} - {e}")
                        # Keep the value as-is if conversion fails
                        trans.rate = rate
        
        # Apply arc weights (handle all arc types: normal, curved, inhibitor, test, curved_inhibitor)
        for arc_id, weight in snapshot.arc_weights.items():
            arc = next((a for a in arcs if a.id == arc_id), None)
            if arc:
                try:
                    # Weight is the primary property for all arc types
                    arc.weight = float(weight)
                    
                    # For inhibitor/test arcs, weight acts as threshold
                    # No special handling needed - weight is used directly in simulation
                    
                except (ValueError, TypeError) as e:
                    arc_type = arc.arc_type if hasattr(arc, 'arc_type') else 'unknown'
                    print(f"[WARNING] Could not set weight for arc {arc_id} (type={arc_type}): {weight} - {e}")
                    # Keep existing weight if conversion fails
    
    def get_result(self, experiment_name: str) -> Optional[Dict[str, Any]]:
        """Get results for completed experiment.
        
        Args:
            experiment_name: Name of experiment
        
        Returns:
            Results dictionary or None if not found
        """
        return self.results.get(experiment_name)
    
    def get_all_results(self) -> Dict[str, Dict[str, Any]]:
        """Get all experiment results.
        
        Returns:
            Dictionary mapping experiment names to results
        """
        return self.results.copy()
    
    def clear_results(self):
        """Clear all stored results."""
        self.results.clear()
    
    def reset(self):
        """Reset executor to initial state."""
        print("[DEBUG] Resetting batch executor...")
        self.is_running = False
        self.is_cancelled = False
        self.current_experiment = None
        self.executor_thread = None
        self.results.clear()
