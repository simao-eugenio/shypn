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
import multiprocessing
import os
from typing import Optional, Callable, Dict, Any, List


def _worker_run_experiment(args: dict) -> Dict[str, Any]:
    """Worker function to run a single experiment in parallel process.
    
    This function must be at module level for multiprocessing to pickle it.
    
    Args:
        args: Dictionary with experiment parameters
    
    Returns:
        Result dictionary
    """
    from shypn.data.canvas.document_model import DocumentModel
    from shypn.engine.simulation.replicate_runner import ReplicateRunner
    
    start_time = time.time()
    
    try:
        # Extract arguments
        name = args['name']
        snapshot = args['snapshot']
        replicates = args['replicates']
        duration = args['duration']
        termination_condition = args['termination_condition']
        subnet_data = args['subnet_data']
        baseline_params = args['baseline_params']
        
        # Create fresh DocumentModel from subnet data (dicts from to_dict())
        model = DocumentModel()
        
        # Reconstruct places and transitions from serialized dicts
        from shypn.netobjs.place import Place
        from shypn.netobjs.transition import Transition
        from shypn.netobjs.arc import Arc
        
        model.places = [Place.from_dict(p_dict) for p_dict in subnet_data['places']]
        model.transitions = [Transition.from_dict(t_dict) for t_dict in subnet_data['transitions']]
        
        # Normalize transition types
        type_name_map = {
            'Immediate': 'immediate',
            'Timed (TPN)': 'timed',
            'Stochastic (FSPN)': 'stochastic',
            'Continuous (SHPN)': 'continuous'
        }
        for t in model.transitions:
            if hasattr(t, 'transition_type') and t.transition_type in type_name_map:
                t.transition_type = type_name_map[t.transition_type]
        
        # Build ID lookup dictionaries
        places_dict = {p.id: p for p in model.places}
        transitions_dict = {t.id: t for t in model.transitions}
        
        # Reconstruct arcs from serialized dicts
        model.arcs = [Arc.from_dict(a_dict, places_dict, transitions_dict)
                      for a_dict in subnet_data['arcs']]
        
        # Apply snapshot parameters
        _apply_snapshot_to_worker_model(snapshot, model, baseline_params)
        
        # Run replicates
        runner = ReplicateRunner(model)
        results = runner.run_replicates(
            n=replicates,
            use_parallel=False,
            use_tau_leaping=True,
            duration=duration,
            termination_condition=termination_condition,
            seed_base=hash(name) % (2**31),  # Unique seed per experiment
            verbose=False,
            progress_callback=None  # No progress in worker
        )
        
        elapsed_time = time.time() - start_time
        
        # Compute statistics
        if results and len(results) > 0:
            statistics = runner.compute_statistics(results)
            statistics['elapsed_time'] = elapsed_time
            statistics['n_replicates'] = len(results)
            
            return {
                'name': name,
                'snapshot_index': args['snapshot_index'],
                'statistics': statistics,
                'n_replicates': len(results),
                'elapsed_time': elapsed_time,
                'status': 'success'
            }
        else:
            return {
                'name': name,
                'snapshot_index': args['snapshot_index'],
                'error': 'No successful replicates',
                'elapsed_time': elapsed_time,
                'status': 'failed'
            }
    
    except Exception as e:
        import traceback
        return {
            'name': args.get('name', 'unknown'),
            'error': f"{type(e).__name__}: {str(e)}",
            'traceback': traceback.format_exc(),
            'status': 'failed'
        }


def _apply_snapshot_to_worker_model(snapshot, model, baseline_params):
    """Apply snapshot parameters to model (simplified version for worker).
    
    Args:
        snapshot: ExperimentSnapshot object or dict with parameters
        model: DocumentModel with places, transitions, arcs
        baseline_params: Baseline parameter values dict
    """
    if not snapshot:
        return
    
    # Handle both ExperimentSnapshot objects and dict format
    if hasattr(snapshot, 'place_markings'):
        # ExperimentSnapshot object - use its attributes
        place_markings = snapshot.place_markings
        transition_rates = snapshot.transition_rates
        arc_weights = snapshot.arc_weights
    elif isinstance(snapshot, dict) and 'parameters' in snapshot:
        # Old dict format - convert to place/transition/arc mappings
        place_markings = {}
        transition_rates = {}
        arc_weights = {}
        
        for param in snapshot['parameters']:
            obj_type = param.get('obj_type')
            obj_id = param.get('obj_id')
            attr_name = param.get('attr')
            new_value = param.get('value')
            
            if obj_type == 'place' and attr_name in ('marking', 'tokens'):
                place_markings[obj_id] = new_value
            elif obj_type == 'transition' and attr_name == 'rate':
                transition_rates[obj_id] = new_value
            elif obj_type == 'arc' and attr_name == 'weight':
                arc_weights[obj_id] = new_value
    else:
        # No valid snapshot format
        return
    
    # Apply place markings
    for place_id, marking in place_markings.items():
        place = next((p for p in model.places if p.id == place_id), None)
        if place:
            place.tokens = float(marking)
    
    # Apply transition rates (handle both numeric and formula strings)
    for trans_id, rate in transition_rates.items():
        trans = next((t for t in model.transitions if t.id == trans_id), None)
        if trans:
            if not hasattr(trans, 'properties') or trans.properties is None:
                trans.properties = {}
            
            # Check if rate is numeric or a formula string
            if isinstance(rate, str):
                # Try to parse as number first
                try:
                    numeric_rate = float(rate)
                    # It's a numeric string - store as number
                    trans.rate = numeric_rate
                    trans.properties['rate'] = numeric_rate
                except ValueError:
                    # It's a formula string - store in properties for evaluation
                    trans.properties['rate_function'] = rate
                    trans.rate = rate  # Store formula string
            else:
                # It's numeric - convert to float
                trans.rate = float(rate)
                trans.properties['rate'] = float(rate)
    
    # Apply arc weights
    for arc_id, weight in arc_weights.items():
        arc = next((a for a in model.arcs if a.id == arc_id), None)
        if arc:
            arc.weight = float(weight)


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
        self.is_paused = False  # Stage 3
        self.current_experiment = None
        self.executor_thread = None
        
        # Results storage
        self.results = {}  # experiment_name -> results_dict
    
    def run_batch(
        self,
        experiments: List[tuple],
        replicates: int = 500,
        duration: float = 100.0,
        termination_condition: str = "deadlock",
        progress_callback: Optional[Callable] = None,
        complete_callback: Optional[Callable] = None,
        experiment_result_callback: Optional[Callable] = None,
        use_parallel: bool = False,
        n_workers: Optional[int] = None
    ):
        """Run batch of experiments asynchronously.
        
        Args:
            experiments: List of (index, name, snapshot_index) tuples
            replicates: Number of replicates per experiment
            duration: Simulation duration
            termination_condition: When to stop ("time_only", "deadlock", "steady_state")
            progress_callback: Called with (exp_index, status, progress)
            use_parallel: Enable parallel execution across multiple CPU cores
            n_workers: Number of worker processes (None = auto-detect CPU count)
            complete_callback: Called when batch completes
            experiment_result_callback: Called with (name, result) when each experiment completes
        """
        if self.is_running:
            raise RuntimeError("Batch execution already in progress")
        
        self.is_running = True
        self.is_cancelled = False
        
        # CRITICAL: Extract model and subnet data in main thread BEFORE starting background thread
        # Accessing GTK widgets from background thread causes deadlock
        import time as time_module
        extraction_start = time_module.time()
        
        try:
            # Use pre-built subnet model from viability panel (created when user adds localities)
            if not hasattr(self.parent_panel, 'subnet_model') or self.parent_panel.subnet_model is None:
                raise RuntimeError("No subnet model available. Please add transitions to viability analysis first.")
            
            subnet_model = self.parent_panel.subnet_model
            
            # Convert subnet elements to dict format for pickling (GObjects can't be pickled)
            # Serialize to dicts for multiprocessing, will be reconstructed in worker
            subnet_data = {
                'places': [p.to_dict() for p in subnet_model.places],
                'transitions': [t.to_dict() for t in subnet_model.transitions],
                'arcs': [a.to_dict() for a in subnet_model.arcs]
            }
            
            if not subnet_data['transitions']:
                raise RuntimeError("No transitions in subnet model")
            
            # Save baseline parameters to reset between experiments
            # Use subnet_model (objects) not subnet_data (dicts) for parameter extraction
            baseline_params = self._save_current_parameters(subnet_model, subnet=None)
        except Exception as e:
            self.is_running = False
            if complete_callback:
                complete_callback()
            raise
        
        # Start execution thread with pre-extracted data
        self.executor_thread = threading.Thread(
            target=self._execute_batch,
            args=(experiments, replicates, duration, termination_condition, progress_callback, complete_callback, experiment_result_callback, subnet_model, subnet_data, baseline_params, use_parallel, n_workers),
            daemon=True
        )
        self.executor_thread.start()
    
    def cancel(self):
        """Cancel running batch execution."""
        if not self.is_running:
            return
        
        self.is_cancelled = True
        
        # Wait for thread to finish with timeout
        if self.executor_thread and self.executor_thread.is_alive():
            self.executor_thread.join(timeout=2.0)
    
    def set_paused(self, should_pause):
        """Set paused state for batch execution (Stage 3).
        
        Args:
            should_pause: True to pause, False to resume
        """
        self.is_paused = should_pause
    
    def _execute_batch(
        self,
        experiments: List[tuple],
        replicates: int,
        duration: float,
        termination_condition: str,
        progress_callback: Optional[Callable],
        complete_callback: Optional[Callable],
        experiment_result_callback: Optional[Callable],
        base_model,  # Pre-extracted DocumentModel
        subnet_data: dict,  # Pre-extracted subnet data
        baseline_params: dict,  # Baseline parameters to reset between experiments
        use_parallel: bool = False,
        n_workers: Optional[int] = None
    ):
        """Execute batch in background thread - SEQUENTIAL or PARALLEL execution.
        
        Args:
            experiments: List of (index, name, snapshot_index) tuples
            replicates: Number of replicates per experiment
            duration: Simulation duration
            termination_condition: When to stop ("time_only", "deadlock", "steady_state")
            progress_callback: Callback for progress updates (queue_index, status, progress_str)
            complete_callback: Callback when complete
            experiment_result_callback: Callback for each experiment result (name, result)
            base_model: Pre-extracted DocumentModel (from main thread)
            subnet_data: Pre-extracted subnet dict (from main thread)
            baseline_params: Baseline parameter values to reset model between experiments
            use_parallel: Enable parallel execution
            n_workers: Number of worker processes (None = auto-detect)
        """
        if use_parallel:
            self._execute_batch_parallel(
                experiments, replicates, duration, termination_condition,
                progress_callback, complete_callback, experiment_result_callback,
                base_model, subnet_data, baseline_params, n_workers
            )
        else:
            self._execute_batch_sequential(
                experiments, replicates, duration, termination_condition,
                progress_callback, complete_callback, experiment_result_callback,
                base_model, subnet_data, baseline_params
            )
    
    def _execute_batch_sequential(
        self,
        experiments: List[tuple],
        replicates: int,
        duration: float,
        termination_condition: str,
        progress_callback: Optional[Callable],
        complete_callback: Optional[Callable],
        experiment_result_callback: Optional[Callable],
        base_model,  # Pre-extracted DocumentModel
        subnet_data: dict,  # Pre-extracted subnet data
        baseline_params: dict  # Baseline parameters to reset between experiments
    ):
        """Execute batch sequentially in background thread.
        
        Args:
            experiments: List of (index, name, snapshot_index) tuples
            replicates: Number of replicates per experiment
            duration: Simulation duration
            termination_condition: When to stop ("time_only", "deadlock", "steady_state")
            progress_callback: Callback for progress updates (queue_index, status, progress_str)
            complete_callback: Callback when complete
            experiment_result_callback: Callback for each experiment result (name, result)
            base_model: Pre-extracted DocumentModel (from main thread)
            subnet_data: Pre-extracted subnet dict (from main thread)
            baseline_params: Baseline parameter values to reset model between experiments
        """
        try:
            total = len(experiments)
            
            for i, (queue_index, name, snapshot_index) in enumerate(experiments):
                # Check cancellation BEFORE starting each experiment
                if self.is_cancelled:
                    # Mark remaining experiments as cancelled
                    if progress_callback:
                        progress_callback(queue_index, "cancelled", "Cancelled")
                    continue  # Skip to next experiment
                
                # Check pause state (Stage 3)
                while self.is_paused and not self.is_cancelled:
                    time.sleep(0.1)  # Wait for resume or cancel
                
                # Recheck cancellation after pause
                if self.is_cancelled:
                    if progress_callback:
                        progress_callback(queue_index, "cancelled", "Cancelled")
                    continue
                
                # print(f"[BATCH] Experiment {i+1}/{total}: '{name}' (queue_index={queue_index})")
                
                # Reset model to baseline before each experiment to avoid state corruption
                # print(f"[BATCH] Resetting model to baseline...")
                # Use base_model (objects) not subnet_data (dicts) for parameter restoration
                self._restore_parameters(base_model, subnet=None, saved_values=baseline_params)
                # print(f"[BATCH] Model reset complete")
                
                # CRITICAL: Set status to running BEFORE execution
                self.current_experiment = name
                if progress_callback:
                    progress_callback(queue_index, "running", "0%")
                    # print(f"[BATCH] Status set to RUNNING for experiment {queue_index}")
                
                # Execute single experiment with error handling
                try:
                    # Time throttling for progress updates
                    last_progress_time = [0.0]  # Use list for mutable closure
                    
                    # Create progress callback with proper closure
                    # Capture queue_index by value to avoid closure bug
                    def exp_progress_callback(p, idx=queue_index):
                        """Progress callback: p is 0.0 to 1.0 float."""
                        if progress_callback and 0.0 <= p <= 1.0:
                            current_time = time.time()
                            # Only update if 0.1 seconds passed or it's 100%
                            if (current_time - last_progress_time[0]) >= 0.1 or p >= 1.0:
                                last_progress_time[0] = current_time
                                percentage_str = f"{int(p*100)}%"
                                progress_callback(idx, "running", percentage_str)
                    
                    # Run experiment with pre-extracted model and subnet
                    # print(f"[BATCH] Running simulation for '{name}'...")
                    result = self._run_single_experiment(
                        name,
                        snapshot_index,
                        replicates,
                        duration,
                        termination_condition,
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
                    
                    # Call result callback immediately for incremental display
                    if experiment_result_callback:
                        from gi.repository import GLib
                        # Schedule in main thread to update UI
                        GLib.idle_add(lambda n=name, r=result: experiment_result_callback(n, r) or False)
                    
                    # CRITICAL: Mark as completed ONLY after result is stored
                    if progress_callback:
                        progress_callback(queue_index, "completed", "100%")
                        # print(f"[BATCH] Status set to COMPLETED for experiment {queue_index}")
                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    
                    # Update status to failed
                    error_msg = str(e)[:100]  # Truncate long errors
                    if progress_callback:
                        progress_callback(queue_index, "failed", error_msg)
                    
                    # Store error result
                    self.results[name] = {
                        "error": str(e),
                        "name": name,
                        "snapshot_index": snapshot_index
                    }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
        finally:
            # Reset execution state
            self.is_running = False
            self.current_experiment = None
            
            if complete_callback:
                # CRITICAL: Schedule callback in main thread - don't block background thread
                from gi.repository import GLib
                cancelled = self.is_cancelled
                GLib.idle_add(lambda: complete_callback(cancelled=cancelled), priority=GLib.PRIORITY_HIGH_IDLE)
    
    def _execute_batch_parallel(
        self,
        experiments: List[tuple],
        replicates: int,
        duration: float,
        termination_condition: str,
        progress_callback: Optional[Callable],
        complete_callback: Optional[Callable],
        experiment_result_callback: Optional[Callable],
        base_model,
        subnet_data: dict,
        baseline_params: dict,
        n_workers: Optional[int] = None
    ):
        """Execute batch in parallel using multiprocessing.
        
        Args:
            experiments: List of (index, name, snapshot_index) tuples
            replicates: Number of replicates per experiment
            duration: Simulation duration
            termination_condition: When to stop
            progress_callback: Callback for progress updates
            complete_callback: Callback when complete
            experiment_result_callback: Callback for each experiment result
            base_model: Pre-extracted DocumentModel
            subnet_data: Pre-extracted subnet dict
            baseline_params: Baseline parameter values
            n_workers: Number of worker processes (None = CPU count)
        """
        try:
            # Determine number of workers
            if n_workers is None:
                n_workers = max(1, multiprocessing.cpu_count() - 1)  # Leave 1 core free
            
            # Prepare experiment arguments for workers
            experiment_args = []
            for queue_index, name, snapshot_index in experiments:
                # Get snapshot
                if snapshot_index >= len(self.experiment_manager.snapshots):
                    continue
                
                snapshot = self.experiment_manager.snapshots[snapshot_index]
                
                # Extract only picklable data from snapshot (avoid GTK/Builder objects)
                snapshot_data = {
                    'name': snapshot.name,
                    'place_markings': snapshot.place_markings.copy(),
                    'arc_weights': snapshot.arc_weights.copy(),
                    'transition_rates': snapshot.transition_rates.copy(),
                    'swept_parameter': snapshot.swept_parameter
                }
                
                # Serialize all data for pickling
                experiment_args.append({
                    'queue_index': queue_index,
                    'name': name,
                    'snapshot_index': snapshot_index,
                    'snapshot': snapshot_data,  # Use extracted dict, not snapshot object
                    'replicates': replicates,
                    'duration': duration,
                    'termination_condition': termination_condition,
                    'subnet_data': subnet_data,
                    'baseline_params': baseline_params
                })
            
            # Create process pool and execute
            total = len(experiment_args)
            completed = 0
            
            with multiprocessing.Pool(processes=n_workers) as pool:
                # Submit all experiments
                async_results = []
                for args in experiment_args:
                    async_result = pool.apply_async(_worker_run_experiment, (args,))
                    async_results.append((args['queue_index'], args['name'], async_result))
                    
                    # Set initial running status when experiment is submitted
                    if progress_callback:
                        progress_callback(args['queue_index'], "running", "0%")
                
                # Poll for completion
                while async_results and not self.is_cancelled:
                    time.sleep(0.1)  # Check every 100ms
                    
                    # Check completed experiments
                    still_running = []
                    for queue_index, name, async_result in async_results:
                        if async_result.ready():
                            try:
                                result = async_result.get(timeout=0.1)
                                
                                # Store result
                                self.results[name] = result
                                
                                # Update UI via callbacks
                                if progress_callback:
                                    progress_callback(queue_index, "completed", "100%")
                                
                                if experiment_result_callback:
                                    from gi.repository import GLib
                                    GLib.idle_add(lambda n=name, r=result: experiment_result_callback(n, r) or False)
                                
                                completed += 1
                                
                            except Exception as e:
                                import traceback
                                traceback.print_exc()
                                
                                error_msg = str(e)[:100]
                                if progress_callback:
                                    progress_callback(queue_index, "failed", error_msg)
                                
                                self.results[name] = {
                                    "error": str(e),
                                    "name": name
                                }
                        else:
                            still_running.append((queue_index, name, async_result))
                    
                    async_results = still_running
                
                # Handle cancellation
                if self.is_cancelled:
                    pool.terminate()
                    pool.join()
                    
                    # Mark remaining as cancelled
                    for queue_index, name, async_result in async_results:
                        if progress_callback:
                            progress_callback(queue_index, "cancelled", "Cancelled")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
        
        finally:
            # Reset execution state
            self.is_running = False
            self.current_experiment = None
            
            if complete_callback:
                from gi.repository import GLib
                cancelled = self.is_cancelled
                GLib.idle_add(lambda: complete_callback(cancelled=cancelled), priority=GLib.PRIORITY_HIGH_IDLE)
    
    def _run_single_experiment(
        self,
        name: str,
        snapshot_index: int,
        replicates: int,
        duration: float,
        termination_condition: str,
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
            termination_condition: When to stop ("time_only", "deadlock", "steady_state")
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
        start_time = time.time()
        
        try:
            # Get snapshot
            if snapshot_index >= len(self.experiment_manager.snapshots):
                raise ValueError(f"Invalid snapshot index: {snapshot_index}")
            
            snapshot = self.experiment_manager.snapshots[snapshot_index]
            
            # CRITICAL FIX: Create a fresh DocumentModel from the subnet data
            # The subnet is extracted correctly, but we were passing the full base_model
            # to the simulator, causing it to run on wrong model structure (11 places vs 5)
            from shypn.data.canvas.document_model import DocumentModel
            
            # Create new model with INDEPENDENT COPIES of subnet elements
            # CRITICAL: Must copy to prevent modifying canvas objects during simulation
            # Use serialization/deserialization for clean copies (avoids GObject issues)
            model = DocumentModel()
            
            # Step 1: Copy places and transitions (they don't have dependencies)
            model.places = [type(p).from_dict(p.to_dict()) for p in subnet_data['places']]
            model.transitions = [type(t).from_dict(t.to_dict()) for t in subnet_data['transitions']]
            
            # CRITICAL FIX: Normalize transition types for simulation controller
            # UI stores as "Continuous (SHPN)", but controller expects "continuous"
            type_name_map = {
                'Immediate': 'immediate', 
                'Timed (TPN)': 'timed', 
                'Stochastic (FSPN)': 'stochastic', 
                'Continuous (SHPN)': 'continuous'
            }
            for t in model.transitions:
                if hasattr(t, 'transition_type'):
                    # Normalize type name for controller
                    if t.transition_type in type_name_map:
                        t.transition_type = type_name_map[t.transition_type]
            
            # Step 2: Build ID lookup dictionaries for arc deserialization
            places_dict = {p.id: p for p in model.places}
            transitions_dict = {t.id: t for t in model.transitions}
            
            # Step 3: Copy arcs (they need references to the copied places and transitions)
            model.arcs = [type(a).from_dict(a.to_dict(), places_dict, transitions_dict) 
                          for a in subnet_data['arcs']]
            
            # Apply snapshot parameters to subnet model (pass None since model IS the subnet)
            self._apply_snapshot_to_model(snapshot, model, None)
            
            # CRITICAL: Verify arc types are preserved (test arcs should stay test arcs)
            # Disabled for performance - this per-arc loop is VERY slow
            # print(f"[EXPERIMENT] Verifying arc types after snapshot application...")
            # for arc in model.arcs:
            #     arc_type = arc.arc_type if hasattr(arc, 'arc_type') else 'unknown'
            #     arc_class = arc.__class__.__name__
            #     print(f"[EXPERIMENT] Arc {arc.id}: type={arc_type}, class={arc_class}, weight={arc.weight}")
            #     # Verify test arcs haven't been corrupted
            #     if arc_type == 'test' and arc_class != 'TestArc':
            #         print(f"[ERROR] Test arc {arc.id} has wrong class: {arc_class}!")
            
            # Report initial progress
            if progress_callback:
                progress_callback(0.0)
            
            # Run replicates using ReplicateRunner
            from shypn.engine.simulation.replicate_runner import ReplicateRunner
            
            # print(f"[EXPERIMENT] Creating ReplicateRunner...")
            # sim_start = time.time()
            runner = ReplicateRunner(model)
            # print(f"[EXPERIMENT] ReplicateRunner created in {time.time()-sim_start:.3f}s")
            
            # print(f"[EXPERIMENT] Starting simulation: {replicates} replicates x {duration}s duration")
            # print(f"[EXPERIMENT] Model size: {len(model.places)} places, {len(model.transitions)} transitions")
            
            # Count arc types for debugging (disabled for performance)
            # arc_types = {}
            # for arc in model.arcs:
            #     arc_type = getattr(arc, 'arc_type', 'normal')
            #     arc_types[arc_type] = arc_types.get(arc_type, 0) + 1
            # print(f"[EXPERIMENT] Arc types: {arc_types}")
            
            # Run all replicates (use_parallel=False for SEQUENTIAL execution)
            sim_exec_start = time.time()
            # print(f"[EXPERIMENT] About to call runner.run_replicates()...")
            results = runner.run_replicates(
                n=replicates,
                use_parallel=False,  # SEQUENTIAL execution of replicates
                use_tau_leaping=True,
                duration=duration,
                termination_condition=termination_condition,
                seed_base=42,
                verbose=False,
                progress_callback=progress_callback
            )
            # print(f"[EXPERIMENT] runner.run_replicates() completed in {time.time()-sim_exec_start:.3f}s")
            # print(f"[EXPERIMENT] Simulation execution took {time.time()-sim_exec_start:.3f}s")
            # print(f"[EXPERIMENT] Simulation complete: {len(results) if results else 0} successful replicates")
            
            # Report 100% progress
            if progress_callback:
                progress_callback(1.0)
            
            elapsed_time = time.time() - start_time
            
            # CRITICAL: Compute statistics
            if results and len(results) > 0:
                # print(f"[EXPERIMENT] Computing statistics for {len(results)} replicates...")
                statistics = runner.compute_statistics(results)
                statistics['elapsed_time'] = elapsed_time
                statistics['n_replicates'] = len(results)
                # print(f"[EXPERIMENT] Statistics computed successfully")
                # print(f"[EXPERIMENT] Statistics keys: {statistics.keys()}")
            else:
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
            
            # Include swept parameter metadata from snapshot
            swept_param = getattr(snapshot, 'swept_parameter', None)
            
            # Include subnet structure for accurate plotting
            subnet_structure = {
                'place_ids': [p.id for p in subnet_data['places']],
                'transition_ids': [t.id for t in subnet_data['transitions']],
                'arc_ids': [a.id for a in subnet_data['arcs']]
            }
            
            # Extract replicate-level data for statistical tests
            replicate_data = []
            if results:
                for rep in results:
                    if 'error' not in rep:
                        replicate_data.append({
                            'deadlocked': rep.get('deadlocked', False),
                            'duration': rep.get('time_points', [0])[-1] if rep.get('time_points') else 0.0
                        })
            
            # Return complete result dict with statistics (plottable from statistics)
            result = {
                'name': name,
                'snapshot_index': snapshot_index,
                'trajectory_summary': trajectory_summary,  # Lightweight summary
                'n_replicates': len(results) if results else 0,
                'statistics': statistics,  # Contains mean/std/percentiles for plotting
                'duration': elapsed_time,
                'swept_parameter': swept_param,  # Include swept parameter info for smart plotting
                'subnet_structure': subnet_structure,  # Include actual subnet composition
                'replicate_data': replicate_data  # Per-replicate outcomes for statistical tests
            }
            
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = str(e)
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
        
        # Debug: Show first few elements
        print(f"[SUBNET] First 3 places: {[p.id for p in list(subnet_places_set)[:3]]}")
        print(f"[SUBNET] First 3 transitions: {[t.id for t in list(subnet_transitions_set)[:3]]}")
        
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
                place.tokens = float(marking)
        
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
        
        CRITICAL FIX: Only apply non-zero values from snapshot to preserve baseline.
        The automation captures a baseline snapshot, but non-swept parameters 
        might be zeroed in the TreeViews. This function now only applies values
        that are explicitly set (non-zero or explicitly swept).
        
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
        # CRITICAL: Always apply swept parameter values (even zero)
        # Skip zero values only for non-swept parameters to preserve baseline
        applied_markings = 0
        skipped_zeros = 0
        swept_place_id = None
        if hasattr(snapshot, 'swept_parameter') and snapshot.swept_parameter:
            if snapshot.swept_parameter.get('type') == 'places':
                swept_place_id = snapshot.swept_parameter.get('id')
        
        for place_id, marking in snapshot.place_markings.items():
            place = next((p for p in places if p.id == place_id), None)
            if place:
                marking_float = float(marking)
                # Always apply if this is the swept parameter (even zero values)
                # For non-swept parameters, skip zeros to preserve baseline
                if place_id == swept_place_id or marking_float != 0.0:
                    place.tokens = marking_float
                    applied_markings += 1
                else:
                    # Keep baseline value from model (don't overwrite with zero)
                    skipped_zeros += 1
        
        # Apply transition rates (only to subnet transitions)
        # Handle both numeric rates and kinetic formulas
        applied_rates = 0
        for trans_id, rate in snapshot.transition_rates.items():
            trans = next((t for t in transitions if t.id == trans_id), None)
            if trans:
                # Ensure properties dict exists
                if not hasattr(trans, 'properties') or trans.properties is None:
                    trans.properties = {}
                
                # Check if rate is numeric or a formula string
                if isinstance(rate, str):
                    # Try to parse as number first
                    try:
                        numeric_rate = float(rate)
                        # It's a numeric string - store as number
                        trans.rate = numeric_rate
                    except ValueError:
                        # It's a formula string - store in properties for behavior factory to evaluate dynamically
                        trans.properties['rate_function'] = rate
                        trans.rate = rate  # Also store as string in rate attribute for behavior factory
                else:
                    # It's numeric - convert to float
                    try:
                        trans.rate = float(rate)
                    except (ValueError, TypeError) as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Could not convert rate for {trans_id}: {rate} - {e}")
                        # Keep the value as-is if conversion fails
                        trans.rate = rate
                applied_rates += 1
        
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
        self.is_running = False
        self.is_cancelled = False
        self.current_experiment = None
        self.executor_thread = None
        self.results.clear()
