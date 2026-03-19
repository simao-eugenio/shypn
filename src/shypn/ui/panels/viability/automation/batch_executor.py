#!/usr/bin/env python3
"""Batch Executor - Backend for running queued experiments.

Executes experiments sequentially, tracks progress, handles errors,
and integrates with ReplicateRunner for actual simulation execution.

Author: Simão Eugénio
Date: December 7, 2025
"""

import threading
import time
import multiprocessing
import os
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime, timezone


# Module-level queue injected into each worker via Pool initializer.
# Using the initializer pattern (instead of passing the queue in the args dict)
# is required when the multiprocessing context is 'forkserver' or 'spawn':
# in those contexts, args passed to apply_async() are pickled, but a plain
# multiprocessing.Queue (OS pipe) is not picklable.  The initializer runs
# inside the freshly forked worker before any task, so the queue is inherited
# via the OS fork rather than serialised.
_worker_progress_queue = None


def _worker_pool_initializer(q) -> None:
    """Called once in each worker process right after it is spawned.

    Sets the module-level _worker_progress_queue so that _worker_run_experiment
    can use it without the queue appearing in the pickled args dict.
    """
    global _worker_progress_queue
    _worker_progress_queue = q


def _worker_run_experiment(args: dict) -> Dict[str, Any]:
    """Worker function to run a single experiment in parallel process.
    
    This function must be at module level for multiprocessing to pickle it.
    
    Args:
        args: Dictionary with experiment parameters
    
    Returns:
        Result dictionary
    """
    # Limit numpy/BLAS internal thread count to 1 per worker process.
    # Without this, each worker spawns BLAS threads equal to cpu_count, so
    # (cpu_count-1) workers × cpu_count BLAS threads = N² thread explosion
    # that saturates all cores and makes the app unresponsive at ~60%.
    # Force-assign (not setdefault) so parent env vars inherited at higher
    # values are overridden — the parent's UI/VS Code threads must not
    # propagate their BLAS concurrency into forked sweep workers.
    import os as _os
    _os.environ["OMP_NUM_THREADS"] = "1"
    _os.environ["OPENBLAS_NUM_THREADS"] = "1"
    _os.environ["MKL_NUM_THREADS"] = "1"
    _os.environ["NUMEXPR_NUM_THREADS"] = "1"
    try:
        import numpy as _np
        _np.set_num_threads(1)  # NumPy 2.0+; silently ignored on older versions
    except (AttributeError, ImportError):
        pass

    from shypn.data.canvas.document_model import DocumentModel
    from shypn.engine.simulation.replicate_runner import ReplicateRunner
    
    start_time = time.time()
    
    # Progress queue is injected at worker spawn via Pool initializer
    # (cannot be passed via args dict with forkserver/spawn contexts because
    # multiprocessing.Queue is not picklable).
    global _worker_progress_queue
    progress_queue = _worker_progress_queue
    queue_index = args.get('queue_index')
    
    # Define progress callback that sends updates to queue
    def worker_progress_callback(progress_fraction):
        if progress_queue is not None and queue_index is not None:
            try:
                # Send progress update: (queue_index, progress_fraction)
                progress_queue.put((queue_index, progress_fraction))
            except (OSError, ValueError) as e:
                # Queue communication error (non-fatal)
                import logging
                logging.getLogger(__name__).debug(f"Progress queue error: {e}")
                pass  # Ignore queue errors (non-fatal)
    
    try:
        # Send an immediate heartbeat so the zombie-silence clock resets to the
        # moment this worker actually starts executing, not the submission time.
        # Without this, conditions that spent time queued in the pool's task
        # queue (waiting for a free worker slot) would accumulate "silent" time
        # counted from submission, falsely triggering zombie detection before
        # any replicate has a chance to run.
        worker_progress_callback(0.0)

        # Extract arguments
        name = args['name']
        snapshot = args['snapshot']
        replicates = args['replicates']
        duration = args['duration']
        import os as _os
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
        
        # Restore environment events so _evaluate_environment_events fires them
        from shypn.data.pathway.pathway_data import Event as _WorkerEvent
        model.events = [_WorkerEvent.from_dict(e) for e in subnet_data.get('events', [])]
        
        # Apply snapshot parameters
        _apply_snapshot_to_worker_model(snapshot, model, baseline_params)
        
        # Extract precision settings (with safe defaults)
        use_tau_leaping = args.get('use_tau_leaping', True)
        tau_epsilon = args.get('tau_epsilon', 0.03)
        max_tau = args.get('max_tau', 0.1)
        dt_manual = args.get('dt_manual', None)
        seed_base = args.get('seed_base', 42)

        # Run replicates
        runner = ReplicateRunner(model)
        results = runner.run_replicates(
            n=replicates,
            use_parallel=True,   # Safe in forked workers: Phase 4b replaced ThreadPoolExecutor with vectorised numpy (no deadlock risk)
            use_tau_leaping=use_tau_leaping,
            duration=duration,
            termination_condition=termination_condition,
            epsilon=tau_epsilon,
            max_tau=max_tau,
            time_step=dt_manual,
            seed_base=seed_base,
            verbose=False,
            progress_callback=worker_progress_callback  # Report progress back to main thread
        )
        
        elapsed_time = time.time() - start_time
        
        # Compute statistics
        if results and len(results) > 0:
            statistics = runner.compute_statistics(results)
            # Don't overwrite elapsed_time - preserve per-replicate timing from compute_statistics
            statistics['n_replicates'] = len(results)
            
            # Generate metadata for this experiment
            metadata_header = None
            try:
                from shypn.metadata import SweepHeaderGenerator
                
                # Extract experiment-specific parameter values from snapshot
                experiment_params = {}
                if isinstance(snapshot, dict):
                    # Get place markings
                    if 'place_markings' in snapshot:
                        experiment_params['place_markings'] = snapshot['place_markings']
                    # Get transition rates
                    if 'transition_rates' in snapshot:
                        experiment_params['transition_rates'] = snapshot['transition_rates']
                    # Get arc weights
                    if 'arc_weights' in snapshot:
                        experiment_params['arc_weights'] = snapshot['arc_weights']
                elif hasattr(snapshot, 'place_markings'):
                    experiment_params['place_markings'] = snapshot.place_markings
                    experiment_params['transition_rates'] = getattr(snapshot, 'transition_rates', {})
                    experiment_params['arc_weights'] = getattr(snapshot, 'arc_weights', {})

                # Overlay property_overrides onto place_markings so config.csv reflects
                # the effective values actually used in simulation, not the baseline.
                # property_overrides uses full paths like "P2.initial_marking"; strip the
                # dot-suffix to match bare place/transition/arc IDs in the legacy dicts.
                _prop_overrides = (
                    snapshot.get('property_overrides', {}) if isinstance(snapshot, dict)
                    else getattr(snapshot, 'property_overrides', {})
                )
                if _prop_overrides:
                    _eff_markings = dict(experiment_params.get('place_markings', {}))
                    _eff_rates = dict(experiment_params.get('transition_rates', {}))
                    _eff_weights = dict(experiment_params.get('arc_weights', {}))
                    for _path, _val in _prop_overrides.items():
                        _obj_id = _path.split('.')[0]
                        if _obj_id in _eff_markings:
                            _eff_markings[_obj_id] = _val
                        elif _obj_id in _eff_rates:
                            _eff_rates[_obj_id] = _val
                        elif _obj_id in _eff_weights:
                            _eff_weights[_obj_id] = _val
                    experiment_params['place_markings'] = _eff_markings
                    experiment_params['transition_rates'] = _eff_rates
                    experiment_params['arc_weights'] = _eff_weights

                # Prepare trajectory data for validation checks
                trajectory_data = {}
                warnings = []
                errors = []
                
                if statistics and 'species_statistics' in statistics:
                    species_stats = statistics['species_statistics']
                    for species_id, species_data in species_stats.items():
                        mean_traj = species_data.get('mean', [])
                        if mean_traj:
                            # Convert to list of values (flatten if needed)
                            if isinstance(mean_traj, list) and len(mean_traj) > 0:
                                if isinstance(mean_traj[0], (list, tuple)):
                                    trajectory_data[species_id] = [v[0] if isinstance(v, (list, tuple)) else v for v in mean_traj]
                                else:
                                    trajectory_data[species_id] = mean_traj
                
                # Determine execution status
                execution_status = 'SUCCESS'
                error_count = sum(1 for r in results if 'error' in r)
                if error_count > 0:
                    errors.append(f"{error_count}/{len(results)} replicates failed")
                    execution_status = 'WARNING' if error_count < len(results) else 'FAILED'
                
                # Convert DocumentModel to dict format for metadata generator
                # Metadata sections expect dict with 'places', 'transitions', 'arcs' keys
                model_dict = model.to_dict() if hasattr(model, 'to_dict') else {
                    'places': [p.to_dict() if hasattr(p, 'to_dict') else {} for p in getattr(model, 'places', [])],
                    'transitions': [t.to_dict() if hasattr(t, 'to_dict') else {} for t in getattr(model, 'transitions', [])],
                    'arcs': [a.to_dict() if hasattr(a, 'to_dict') else {} for a in getattr(model, 'arcs', [])],
                    'formalism': 'Signal_Hierarchical_Petri_Net',
                    'metadata': {}
                }
                
                metadata_context = {
                    'model': model_dict,
                    'model_path': getattr(model, 'filepath', None),  # None for snapshots - ModelMetadata will be skipped
                    'n_replicates': replicates,
                    'experiment_index': args['snapshot_index'],
                    'experiment_name': name,
                    'experiment_parameters': experiment_params,
                    'simulation_config': {
                        'duration': duration,
                        'time_span': (0, duration),
                        'time_units': 'second',
                        'n_replicates': replicates,
                        'random_seed': seed_base,
                        'solver': 'TauLeaping_SSA',
                        'timestep': f'dt={dt_manual:.4g}' if dt_manual else 'adaptive (auto-dt)',
                        'use_tau_leaping': True,
                        'tau_epsilon': tau_epsilon,
                        'max_tau': max_tau,
                    },
                    'experiment_start_time': datetime.fromtimestamp(start_time, tz=timezone.utc),
                    'elapsed_time': elapsed_time,
                    'phase': snapshot.get('name', name) if isinstance(snapshot, dict) else name,
                    'swept_parameter': snapshot.get('swept_parameter') if isinstance(snapshot, dict) else None,
                    'property_overrides': (
                        snapshot.get('property_overrides', {}) if isinstance(snapshot, dict)
                        else getattr(snapshot, 'property_overrides', {})
                    ),
                    # Validation data
                    'trajectory_data': trajectory_data,
                    'warnings': warnings,
                    'errors': errors,
                    'execution_status': execution_status
                }
                
                generator = SweepHeaderGenerator()
                generator.set_context(metadata_context)
                generator.generate()
                metadata_header = generator.header
            except Exception as e:
                print(f"⚠️ Warning: Worker failed to generate metadata for {name}: {e}")
                metadata_header = None

            # Build trajectory_summary (lightweight per-replicate metadata)
            trajectory_summary = []
            for i, traj in enumerate(results[:100]):
                if 'error' not in traj:
                    trajectory_summary.append({
                        'replicate_id': traj.get('replicate_id', i),
                        'seed': traj.get('seed'),
                        'n_timepoints': len(traj.get('time_points', [])),
                        'final_time': traj.get('time_points', [0])[-1] if traj.get('time_points') else 0
                    })

            # Build replicate_data (per-replicate outcomes for replicates.csv)
            replicate_data = []
            for rep in results:
                if 'error' not in rep:
                    replicate_data.append({
                        'deadlocked': rep.get('deadlocked', False),
                        'duration': rep.get('time_points', [0])[-1] if rep.get('time_points') else 0.0,
                        'elapsed_time': rep.get('elapsed_time', 0.0)
                    })

            # Extract swept parameter and subnet structure for config.csv
            swept_param = snapshot.get('swept_parameter') if isinstance(snapshot, dict) else None
            subnet_structure = {
                'place_ids': [p['id'] for p in subnet_data.get('places', [])],
                'transition_ids': [t['id'] for t in subnet_data.get('transitions', [])],
                'arc_ids': [a['id'] for a in subnet_data.get('arcs', [])]
            }

            # Compress raw trajectories with δ-filter before discarding raw data.
            # min_gap default: 5.0 s — on a 0.72 s SSA step almost every step
            # triggers the delta-filter (discrete token changes hit the 2% threshold
            # at molecule-scale); a 5 s minimum gap lifts compression from ~2× to
            # ~7×, reducing compressed_trajectories size before IPC pickle.
            worker_compressed: list = []
            _n_replicates_count = len(results)  # save before del
            try:
                from shypn.helpers.compressor import DeltaFilterCompressor
                _cmp = DeltaFilterCompressor(
                    epsilon=args.get('compressor_epsilon', 0.02),
                    max_gap=args.get('compressor_max_gap', 300.0),
                    min_gap=args.get('compressor_min_gap', 5.0),
                )
                worker_compressed = _cmp.compress_batch(results)
            except Exception as _ce:
                print(f'[WORKER] Warning: trajectory compression failed: {_ce}')

            # Free raw trajectory data (~100–250 MB) before building the return
            # dict, which is pickled for IPC.  Without this explicit delete the
            # raw results list stays in scope during pickling, doubling peak RAM.
            del results
            import gc as _worker_gc; _worker_gc.collect()

            return {
                'name': name,
                'snapshot_index': args['snapshot_index'],
                'statistics': statistics,
                'n_replicates': _n_replicates_count,
                'duration': elapsed_time,
                'elapsed_time': elapsed_time,
                'status': 'success',
                'metadata': metadata_header,
                'trajectory_summary': trajectory_summary,
                'compressed_trajectories': worker_compressed,
                'replicate_data': replicate_data,
                'swept_parameter': swept_param,
                'subnet_structure': subnet_structure,
            }
        else:
            return {
                'name': name,
                'snapshot_index': args['snapshot_index'],
                'error': 'No successful replicates',
                'elapsed_time': elapsed_time,
                'status': 'failed',
                'metadata': None  # No metadata for failed experiments
            }
    
    except Exception as e:
        import traceback
        import os as _os
        tb_str = traceback.format_exc()
        # Write traceback to debug file (stdout is unreliable in forked workers)
        _dlog = _os.path.expanduser("~/sweep_debug.log")
        with open(_dlog, 'a') as _f:
            _f.write(f"\n[WORKER EXCEPTION] {args.get('name', 'unknown')}: {type(e).__name__}: {e}\n")
            _f.write(tb_str)
        return {
            'name': args.get('name', 'unknown'),
            'error': f"{type(e).__name__}: {str(e)}",
            'traceback': tb_str,
            'status': 'failed'
        }


def _apply_snapshot_to_worker_model(snapshot, model, baseline_params):
    """Apply snapshot parameters to model (simplified version for worker).
    
    Args:
        snapshot: ExperimentSnapshot object or dict with parameters
        model: DocumentModel with places, transitions, arcs
        baseline_params: Baseline parameter values dict
    """
    # Import property path parser
    from .property_path_parser import parse_property_path, apply_property_to_object, resolve_object
    
    if not snapshot:
        return
    
    # Handle both ExperimentSnapshot objects and dict format
    if isinstance(snapshot, dict):
        # Dict format (used in parallel mode) - newer format with direct keys
        if 'place_markings' in snapshot:
            # New dict format from parallel execution
            place_markings = snapshot['place_markings']
            transition_rates = snapshot['transition_rates']
            arc_weights = snapshot['arc_weights']
            property_overrides = snapshot.get('property_overrides', {})  # NEW
            swept_param = snapshot.get('swept_parameter')
        elif 'parameters' in snapshot:
            # Old dict format - convert to place/transition/arc mappings
            place_markings = {}
            transition_rates = {}
            arc_weights = {}
            property_overrides = {}
            
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
            
            swept_param = None  # Old format doesn't have swept_parameter
        else:
            # No valid dict format — skip silently
            return
    elif hasattr(snapshot, 'place_markings'):
        # ExperimentSnapshot object - use its attributes
        place_markings = snapshot.place_markings
        transition_rates = snapshot.transition_rates
        arc_weights = snapshot.arc_weights
        property_overrides = getattr(snapshot, 'property_overrides', {})  # NEW
        swept_param = getattr(snapshot, 'swept_parameter', None)
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
    
    # Apply property overrides (takes precedence over legacy dicts)
    # This enables explicit property paths like "T5.volume_threshold", "A3.threshold"
    if property_overrides:
        for prop_path, value in property_overrides.items():
            try:
                obj_id, prop_name = parse_property_path(prop_path)
                obj = resolve_object(model, obj_id)
                if obj:
                    apply_property_to_object(obj, prop_name, value)
            except Exception:
                pass  # Silently skip invalid property paths


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
        n_workers: Optional[int] = None,
        timeout_per_experiment: Optional[float] = None,
        use_tau_leaping: bool = True,
        tau_epsilon: float = 0.03,
        max_tau: float = 0.1,
        dt_manual: Optional[float] = None,
        seed_base: int = 42,
        compressor_epsilon: float = 0.02,
        compressor_min_gap: float = 5.0,
        compressor_max_gap: float = 300.0,
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
        
        if replicates <= 0:
            raise ValueError(f"replicates must be >= 1, got {replicates}")
        
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
                'arcs': [a.to_dict() for a in subnet_model.arcs],
                # Serialize environment events so worker processes can reconstruct them
                'events': [e.to_dict() for e in getattr(subnet_model, 'events', []) if hasattr(e, 'to_dict')],
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
            args=(experiments, replicates, duration, termination_condition, progress_callback, complete_callback, experiment_result_callback, subnet_model, subnet_data, baseline_params, use_parallel, n_workers, timeout_per_experiment, use_tau_leaping, tau_epsilon, max_tau, dt_manual, seed_base, compressor_epsilon, compressor_min_gap, compressor_max_gap),
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
        n_workers: Optional[int] = None,
        timeout_per_experiment: Optional[float] = None,
        use_tau_leaping: bool = True,
        tau_epsilon: float = 0.03,
        max_tau: float = 0.1,
        dt_manual: Optional[float] = None,
        seed_base: int = 42,
        compressor_epsilon: float = 0.02,
        compressor_min_gap: float = 5.0,
        compressor_max_gap: float = 300.0,
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
                base_model, subnet_data, baseline_params, n_workers, timeout_per_experiment,
                use_tau_leaping, tau_epsilon, max_tau, dt_manual, seed_base,
                compressor_epsilon, compressor_min_gap, compressor_max_gap,
            )
        else:
            self._execute_batch_sequential(
                experiments, replicates, duration, termination_condition,
                progress_callback, complete_callback, experiment_result_callback,
                base_model, subnet_data, baseline_params,
                use_tau_leaping, tau_epsilon, max_tau, dt_manual, seed_base,
                compressor_epsilon, compressor_min_gap, compressor_max_gap,
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
        baseline_params: dict,  # Baseline parameters to reset between experiments
        use_tau_leaping: bool = True,
        tau_epsilon: float = 0.03,
        max_tau: float = 0.1,
        dt_manual: Optional[float] = None,
        seed_base: int = 42,
        compressor_epsilon: float = 0.02,
        compressor_min_gap: float = 5.0,
        compressor_max_gap: float = 300.0,
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
                        subnet_data,
                        use_tau_leaping=use_tau_leaping,
                        tau_epsilon=tau_epsilon,
                        max_tau=max_tau,
                        dt_manual=dt_manual,
                        seed_base=seed_base,
                        compressor_epsilon=compressor_epsilon,
                        compressor_min_gap=compressor_min_gap,
                        compressor_max_gap=compressor_max_gap,
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

            # Run a GC pass to reclaim per-experiment objects (model, runner,
            # numpy temporaries) that Python's reference counter may not have
            # released yet due to cycles in the statistics/compressor code.
            import gc as _seq_gc; _seq_gc.collect()

            if complete_callback:
                # CRITICAL: Schedule callback in main thread - don't block background thread
                # Use PRIORITY_LOW (300) so all pending experiment_result_callback calls
                # (scheduled at DEFAULT priority 200) drain first — prevents the run-folder
                # being reset before the last save callbacks execute.
                from gi.repository import GLib
                cancelled = self.is_cancelled
                GLib.idle_add(lambda: complete_callback(cancelled=cancelled), priority=GLib.PRIORITY_LOW)
    
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
        n_workers: Optional[int] = None,
        timeout_per_experiment: Optional[float] = None,
        use_tau_leaping: bool = True,
        tau_epsilon: float = 0.03,
        max_tau: float = 0.1,
        dt_manual: Optional[float] = None,
        seed_base: int = 42,
        compressor_epsilon: float = 0.02,
        compressor_min_gap: float = 5.0,
        compressor_max_gap: float = 300.0,
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
                # Reserve 2 logical cores for the GTK UI thread, VS Code, OS
                # scheduler, and auto-save I/O threads; give the rest to sweep
                # workers.  On a 12-logical-core machine this yields 10 workers
                # while keeping the app responsive.
                n_workers = max(1, multiprocessing.cpu_count() - 2)

            # Cap concurrent workers to prevent RAM exhaustion at large N.
            # Each worker accumulates all N replicate trajectory arrays in RAM
            # before returning: empirical peak ≈ N × 4 MB (float32 place
            # buffers + overhead).  Limit workers so total in-flight data
            # stays under ~4 GB regardless of N.
            # Examples: N=200 → 5 workers (5×800 MB = 4 GB)
            #           N=100 → 10 workers (cap not binding at ≤ cpu_count-2)
            _ram_limit_mb = 4096
            _mb_per_worker = max(200, replicates * 4)
            _ram_cap = max(1, _ram_limit_mb // _mb_per_worker)
            n_workers = min(n_workers, _ram_cap)

            # Use 'forkserver' context: workers are forked from a clean server
            # process that was started before GTK/Numba were loaded, so they
            # inherit no GTK file-descriptors, event-loop handles, or partially
            # JIT-compiled Numba state.  This is safer and leaner than the
            # default 'fork' (which copies the entire parent address space,
            # including all loaded GTK shared-memory segments).
            _mp_ctx = multiprocessing.get_context('forkserver')

            # Create shared progress queue for workers to report back.
            # Use a plain multiprocessing.Queue (OS pipe) rather than a
            # manager.Queue() proxy.  manager.Queue() requires a separate
            # Manager server process; if that process is OOM-killed the
            # workers silently lose the ability to send heartbeats, causing
            # false zombie timeouts after ZOMBIE_SILENCE_S.  A plain Queue
            # survives as long as either end is alive.
            progress_queue = _mp_ctx.Queue(maxsize=0)  # unbounded
            
            # Prepare experiment arguments for workers
            experiment_args = []
            for queue_index, name, snapshot_index in experiments:
                # Get snapshot
                if snapshot_index >= len(self.experiment_manager.snapshots):
                    continue
                
                snapshot = self.experiment_manager.snapshots[snapshot_index]
                
                # Extract only picklable data from snapshot (avoid GTK/Builder objects)
                # CRITICAL: property_overrides must be included — it carries factorial sweep values
                # (e.g. {"P1.initial_marking": 150.0, "P2.initial_marking": 50.0}).
                # Omitting it causes all parallel factorial conditions to run with baseline values.
                snapshot_data = {
                    'name': snapshot.name,
                    'place_markings': snapshot.place_markings.copy(),
                    'arc_weights': snapshot.arc_weights.copy(),
                    'transition_rates': snapshot.transition_rates.copy(),
                    'swept_parameter': snapshot.swept_parameter,
                    'property_overrides': getattr(snapshot, 'property_overrides', {}).copy()
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
                    'baseline_params': baseline_params,
                    'use_tau_leaping': use_tau_leaping,
                    'tau_epsilon': tau_epsilon,
                    'max_tau': max_tau,
                    'dt_manual': dt_manual,
                    'seed_base': seed_base,
                    'compressor_epsilon': compressor_epsilon,
                    'compressor_min_gap': compressor_min_gap,
                    'compressor_max_gap': compressor_max_gap,
                })
            
            # Create process pool and execute
            total = len(experiment_args)
            completed = 0
            # NOTE: No computation-based timeout. Workers are killed only when they go
            # SILENT (no progress heartbeat) for ZOMBIE_SILENCE_S seconds, computed
            # inside the polling loop from `duration`. Legitimate slow runs are never
            # interrupted.
            
            with _mp_ctx.Pool(
                processes=n_workers,
                maxtasksperchild=1,  # forkserver + maxtasksperchild=1: clean workers, no GTK/Numba state inherited
                initializer=_worker_pool_initializer,
                initargs=(progress_queue,),
            ) as _initial_pool:
                pool = _initial_pool  # may be replaced after zombie restart
                # Submit all experiments with start time tracking.
                # The first n_workers slots are picked up immediately; the rest
                # wait in the pool's internal task queue.  Reflect that in the
                # UI: mark the first n_workers as "running" and the remainder
                # as "queued".  They are promoted to "running" on first heartbeat.
                async_results = []
                already_started: set = set()
                # Tracks experiments that have emitted at least one actual heartbeat
                # from inside a worker.  Zombie silence is only measured from the
                # first heartbeat; before that the experiment is still pending in the
                # pool's task queue and must not be timed-out.
                heartbeat_received: set = set()
                for i, args in enumerate(experiment_args):
                    async_result = pool.apply_async(_worker_run_experiment, (args,))
                    start_time = time.time()
                    async_results.append((args['queue_index'], args['name'], async_result, start_time))

                    if progress_callback:
                        if i < n_workers:
                            progress_callback(args['queue_index'], "running", "0%")
                            already_started.add(args['queue_index'])
                        else:
                            progress_callback(args['queue_index'], "pending", "pending")

                # Zombie detection: kill a worker only when it goes SILENT, not merely slow.
                # A legitimate computation that takes longer than any estimate must not be
                # interrupted.  We classify a worker as a zombie only when it has produced
                # no progress heartbeat for ZOMBIE_SILENCE_S seconds.
                #
                # Threshold: at least 30 min, or 3× the time one single replicate should
                # take at the sequential empirical rate (0.827 s / simulated-s).  This
                # ensures a legitimate but slow replicate has 3 chances to complete
                # before we declare it hung.
                single_replicate_estimate = duration * 0.827
                ZOMBIE_SILENCE_S = max(30 * 60, single_replicate_estimate * 3)

                # last_heartbeat[queue_index] = wall-clock time of last progress message
                # Initialised to submission time so a worker that never sends a message
                # is caught after ZOMBIE_SILENCE_S from the moment it was submitted.
                last_heartbeat = {args['queue_index']: time.time() for args in experiment_args}

                # Poll for completion with zombie detection
                while async_results and not self.is_cancelled:
                    time.sleep(0.1)  # Check every 100ms

                    current_time = time.time()

                    # Process progress updates from workers — each message resets the
                    # heartbeat clock for that worker.
                    # NOTE: progress_queue.empty() itself can raise ConnectionResetError
                    # (subclass of OSError) when the Manager server process has exited
                    # (e.g. all workers finished and the Manager was GC'd before this
                    # polling loop checks one last time).  Wrap the entire drain block.
                    try:
                        while not progress_queue.empty():
                            try:
                                queue_idx, progress_fraction = progress_queue.get_nowait()
                                heartbeat_received.add(queue_idx)  # worker has actually started
                                last_heartbeat[queue_idx] = current_time  # worker is alive
                                if progress_callback:
                                    # First heartbeat from a queued experiment → promote to running
                                    if queue_idx not in already_started:
                                        already_started.add(queue_idx)
                                        progress_callback(queue_idx, "running", "0%")
                                    progress_pct = int(progress_fraction * 100)
                                    progress_callback(queue_idx, "running", f"{progress_pct}%")
                            except (OSError, EOFError, ValueError) as e:
                                import logging
                                logging.getLogger(__name__).debug(f"Progress queue read failed: {e}")
                                break
                    except (OSError, EOFError) as e:
                        import logging
                        logging.getLogger(__name__).debug(f"Progress queue unavailable (manager exited): {e}")

                    # Check completed experiments and detect zombies
                    still_running = []
                    zombie_detected = False
                    for queue_index, name, async_result, start_time in async_results:
                        elapsed = current_time - start_time

                        # Experiments that have not yet been dispatched to a worker
                        # (still waiting in the pool's task queue) must never be
                        # counted as zombies.  Their last_heartbeat was stamped at
                        # submission time; keep it fresh so silence stays at zero
                        # until the worker actually starts and emits its first 0%
                        # progress message.
                        if queue_index not in heartbeat_received:
                            last_heartbeat[queue_index] = current_time

                        silence = current_time - last_heartbeat.get(queue_index, current_time)

                        if silence > ZOMBIE_SILENCE_S:
                            # ZOMBIE DETECTED: worker has been silent too long.
                            # Kill both the hung worker process (releasing its RAM
                            # and CPU) and the pool so remaining pending experiments
                            # can be dispatched to fresh workers.
                            zombie_detected = True
                            print(
                                f"[BATCH] ⚠️ ZOMBIE: {name} silent for {silence:.0f}s "
                                f"(threshold {ZOMBIE_SILENCE_S:.0f}s, total elapsed {elapsed:.0f}s)"
                            )
                            # Attempt to SIGKILL individual worker process.
                            # multiprocessing.pool does not expose per-task PIDs
                            # directly, but the worker's OS pid is accessible via
                            # pool._pool list.  As a robust fallback we terminate the
                            # whole pool; it gets recreated below.
                            try:
                                import os as _os, signal as _signal
                                for _w in pool._pool:
                                    try:
                                        _os.kill(_w.pid, _signal.SIGKILL)
                                    except (ProcessLookupError, PermissionError):
                                        pass
                            except (AttributeError, OSError):
                                pass

                            zombie_msg = (
                                f"No heartbeat for {silence:.0f}s "
                                f"(zombie threshold {ZOMBIE_SILENCE_S:.0f}s)"
                            )
                            if progress_callback:
                                progress_callback(queue_index, "failed", zombie_msg)

                            self.results[name] = {
                                "error": zombie_msg,
                                "name": name,
                                "timeout": True,
                                "elapsed_time": elapsed
                            }
                            completed += 1
                            continue  # Don't add to still_running

                        if async_result.ready():
                            try:
                                result = async_result.get(timeout=0.1)

                                self.results[name] = result

                                # Check if worker returned an error result
                                if 'error' in result and result.get('status') == 'failed':
                                    # Worker raised an exception — log traceback to debug file
                                    tb = result.get('traceback', '')
                                    print(f"[PARALLEL] Worker error for '{name}': {result['error']}")
                                    if tb:
                                        print(f"[PARALLEL] Worker traceback:\n{tb}")
                                    import os as _os
                                    _dlog = _os.path.expanduser("~/sweep_debug.log")
                                    with open(_dlog, 'a') as _f:
                                        _f.write(f"\n[PARALLEL ERROR] {name}: {result['error']}\n")
                                        if tb:
                                            _f.write(tb)
                                    if progress_callback:
                                        progress_callback(queue_index, "failed", result['error'][:100])
                                else:
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
                            still_running.append((queue_index, name, async_result, start_time))

                    async_results = still_running

                    # If zombies were killed above, the pool's worker processes are
                    # gone.  The pool object itself is now broken and will never
                    # dispatch the remaining async_results.  Terminate it cleanly,
                    # restart with fresh workers, and re-submit the still-pending
                    # experiments so they get a chance to complete.
                    if zombie_detected and async_results and not self.is_cancelled:
                        print(
                            f"[BATCH] Restarting pool after zombie kill "
                            f"({len(async_results)} experiments remain)"
                        )
                        try:
                            pool.terminate()
                            pool.join()
                        except Exception:
                            pass
                        pool = _mp_ctx.Pool(
                            processes=n_workers,
                            maxtasksperchild=1,
                            initializer=_worker_pool_initializer,
                            initargs=(progress_queue,),
                        )
                        # Re-submit remaining experiments to the fresh pool.
                        resubmitted = []
                        for queue_index, name, _old_result, start_time in async_results:
                            matching = [a for a in experiment_args if a['queue_index'] == queue_index]
                            if matching:
                                new_result = pool.apply_async(_worker_run_experiment, (matching[0],))
                                last_heartbeat[queue_index] = time.time()  # reset silence clock
                                resubmitted.append((queue_index, name, new_result, time.time()))
                        async_results = resubmitted
                
                # Handle cancellation
                if self.is_cancelled:
                    pool.terminate()
                    pool.join()
                    
                    # Mark remaining as cancelled
                    for queue_index, name, async_result, start_time in async_results:
                        if progress_callback:
                            progress_callback(queue_index, "cancelled", "Cancelled")

            # If pool was replaced after a zombie restart, the new pool was not
            # managed by the `with` block; terminate it now.
            if pool is not _initial_pool:
                try:
                    pool.terminate()
                    pool.join()
                except Exception:
                    pass
        
        except Exception as e:
            import traceback
            traceback.print_exc()
        
        finally:
            # Reset execution state
            self.is_running = False
            self.current_experiment = None

            # Prompt Python to release memory accumulated during the batch.
            # self.results entries have already been forwarded to the UI via
            # experiment_result_callback and heavy fields stripped by the
            # auto-save thread; a GC pass here reclaims any residual objects
            # (numpy temporaries, closed-over lambda refs, etc.).
            import gc as _batch_gc; _batch_gc.collect()

            if complete_callback:
                from gi.repository import GLib
                cancelled = self.is_cancelled
                # Use PRIORITY_LOW so pending result callbacks drain first (see sequential path).
                GLib.idle_add(lambda: complete_callback(cancelled=cancelled), priority=GLib.PRIORITY_LOW)
    
    def _run_single_experiment(
        self,
        name: str,
        snapshot_index: int,
        replicates: int,
        duration: float,
        termination_condition: str,
        progress_callback: Optional[Callable] = None,
        base_model = None,  # Pre-extracted DocumentModel
        subnet_data: dict = None,  # Pre-extracted subnet data
        use_tau_leaping: bool = True,
        tau_epsilon: float = 0.03,
        max_tau: float = 0.1,
        dt_manual: Optional[float] = None,
        seed_base: int = 42,
        compressor_epsilon: float = 0.02,
        compressor_min_gap: float = 0.0,
        compressor_max_gap: float = 300.0,
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
            from shypn.netobjs.place import Place
            from shypn.netobjs.transition import Transition
            from shypn.netobjs.arc import Arc
            
            # Create new model with INDEPENDENT COPIES of subnet elements
            # CRITICAL: Must copy to prevent modifying canvas objects during simulation
            # subnet_data already contains serialized dicts from run_batch()
            model = DocumentModel()
            
            # Step 1: Reconstruct places and transitions from serialized dicts
            model.places = [Place.from_dict(p_dict) for p_dict in subnet_data['places']]
            model.transitions = [Transition.from_dict(t_dict) for t_dict in subnet_data['transitions']]
            
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
            
            # Step 3: Reconstruct arcs from serialized dicts (they need references to the copied places and transitions)
            model.arcs = [Arc.from_dict(a_dict, places_dict, transitions_dict) 
                          for a_dict in subnet_data['arcs']]
            
            # Step 4: Restore environment events so _evaluate_environment_events fires them
            from shypn.data.pathway.pathway_data import Event as _ModelEvent
            model.events = [_ModelEvent.from_dict(e) for e in subnet_data.get('events', [])]
            
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
            
            # Calculate timeout threshold for SEQUENTIAL mode (for warning purposes only)
            # Empirical factor: 0.827 seconds wall-clock per 1s simulated
            #   (from 3 replicates × 60s = 148.9s measurement)
            # Updated timeout calculation to match parallel mode:
            #   base_time = replicates × duration × empirical_factor
            #   safety_margin = 1.5x (accounts for system variations)
            #   max_cap = 36 hours (allows very long experiments)
            expected_time_per_replicate = duration * 0.827  # Sequential: ~83% of simulated time
            expected_experiment_time = replicates * expected_time_per_replicate
            timeout_threshold = min(expected_experiment_time * 1.5, 36 * 3600)  # Max 36 hours, 1.5x safety
            
            # print(f"[EXPERIMENT] About to call runner.run_replicates()...")
            # print(f"[EXPERIMENT] Timeout threshold: {timeout_threshold:.1f}s")
            results = runner.run_replicates(
                n=replicates,
                use_parallel=True,  # Enable stochastic parallelism in main thread (safe, 2-4× faster)
                use_tau_leaping=use_tau_leaping,
                duration=duration,
                termination_condition=termination_condition,
                epsilon=tau_epsilon,
                max_tau=max_tau,
                time_step=dt_manual,
                seed_base=seed_base,
                verbose=False,
                progress_callback=progress_callback
            )
            sim_elapsed = time.time() - sim_exec_start
            # print(f"[EXPERIMENT] runner.run_replicates() completed in {sim_elapsed:.3f}s")
            
            # Check if execution exceeded timeout
            if sim_elapsed > timeout_threshold:
                print(f"[EXPERIMENT] ⚠️ WARNING: Execution took {sim_elapsed:.1f}s (threshold: {timeout_threshold:.1f}s)")
                # Note: We still process results if they exist, just warn about slow execution
            
            # print(f"[EXPERIMENT] Simulation execution took {sim_elapsed:.3f}s")
            # print(f"[EXPERIMENT] Simulation complete: {len(results) if results else 0} successful replicates")
            
            # Report 100% progress
            if progress_callback:
                progress_callback(1.0)
            
            elapsed_time = time.time() - start_time
            
            # CRITICAL: Compute statistics
            if results and len(results) > 0:
                # print(f"[EXPERIMENT] Computing statistics for {len(results)} replicates...")
                statistics = runner.compute_statistics(results)
                # Don't overwrite elapsed_time - preserve per-replicate timing from compute_statistics
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

            # Compress raw trajectories with δ-filter (generic, no model knowledge).
            # Results are stored in the output dict and consumed by _auto_save_experiment
            # to write replicates_trajectories/run_NNN.csv files.
            compressed_trajectories: List[Any] = []
            try:
                from shypn.helpers.compressor import DeltaFilterCompressor
                _compressor = DeltaFilterCompressor(
                    epsilon=compressor_epsilon,
                    max_gap=compressor_max_gap,
                    min_gap=compressor_min_gap,
                )
                if results:
                    compressed_trajectories = _compressor.compress_batch(results)
            except Exception as _comp_err:
                print(f'[EXPERIMENT] Warning: trajectory compression failed: {_comp_err}')

            # Include swept parameter metadata from snapshot
            swept_param = getattr(snapshot, 'swept_parameter', None)
            
            # Include subnet structure for accurate plotting
            # subnet_data contains serialized dicts, so use dict access
            subnet_structure = {
                'place_ids': [p['id'] for p in subnet_data['places']],
                'transition_ids': [t['id'] for t in subnet_data['transitions']],
                'arc_ids': [a['id'] for a in subnet_data['arcs']]
            }
            
            # Extract replicate-level data for statistical tests
            replicate_data = []
            if results:
                for rep in results:
                    if 'error' not in rep:
                        replicate_data.append({
                            'deadlocked': rep.get('deadlocked', False),
                            'duration': rep.get('time_points', [0])[-1] if rep.get('time_points') else 0.0,
                            'elapsed_time': rep.get('elapsed_time', 0.0)  # Wall-clock time
                        })

            # Capture scalar summaries before freeing raw trajectory data.
            # `results` holds ~200 MB (100 replicates × all place trajectories);
            # releasing it here instead of at function-return drops peak RSS by
            # ~200 MB per experiment — critical for multi-condition sweeps.
            _n_replicates_count = len(results) if results else 0
            _error_count = sum(1 for r in results if 'error' in r) if results else 0
            del results

            # Release the per-experiment model object (places/transitions/arcs
            # built from subnet_data dicts) and the ReplicateRunner that holds
            # a reference to it — neither is needed past this point.
            del runner, model
            
            # Generate metadata for this experiment
            from shypn.metadata import SweepHeaderGenerator
            
            # Extract experiment-specific parameter values from snapshot
            experiment_params = {}
            if hasattr(snapshot, 'place_markings'):
                experiment_params['place_markings'] = snapshot.place_markings
                experiment_params['transition_rates'] = getattr(snapshot, 'transition_rates', {})
                experiment_params['arc_weights'] = getattr(snapshot, 'arc_weights', {})
            
            # Prepare trajectory data for validation checks
            # Use mean trajectories from statistics
            trajectory_data = {}
            warnings = []
            errors = []
            
            if statistics and 'species_statistics' in statistics:
                species_stats = statistics['species_statistics']
                for species_id, species_data in species_stats.items():
                    mean_traj = species_data.get('mean', [])
                    if mean_traj:
                        # Convert to list of values (flatten if needed)
                        if isinstance(mean_traj, list) and len(mean_traj) > 0:
                            if isinstance(mean_traj[0], (list, tuple)):
                                trajectory_data[species_id] = [v[0] if isinstance(v, (list, tuple)) else v for v in mean_traj]
                            else:
                                trajectory_data[species_id] = mean_traj
            
            # Determine execution status
            execution_status = 'SUCCESS'
            if _n_replicates_count > 0:
                # Count errors in replicates
                if _error_count > 0:
                    errors.append(f"{_error_count}/{_n_replicates_count} replicates failed")
                    execution_status = 'WARNING' if _error_count < _n_replicates_count else 'FAILED'
                
                # Check for deadlocks
                deadlock_count = sum(1 for r in replicate_data if r.get('deadlocked', False))
                if deadlock_count > 0:
                    deadlock_rate = (deadlock_count / len(replicate_data) * 100) if replicate_data else 0
                    if deadlock_rate > 50:
                        warnings.append(f"High deadlock rate: {deadlock_rate:.1f}%")
            
            # Convert DocumentModel to dict format for metadata generator
            # Metadata sections expect dict with 'places', 'transitions', 'arcs' keys
            model_dict = model.to_dict() if hasattr(model, 'to_dict') else {
                'places': [p.to_dict() if hasattr(p, 'to_dict') else {} for p in getattr(model, 'places', [])],
                'transitions': [t.to_dict() if hasattr(t, 'to_dict') else {} for t in getattr(model, 'transitions', [])],
                'arcs': [a.to_dict() if hasattr(a, 'to_dict') else {} for a in getattr(model, 'arcs', [])],
                'formalism': 'Signal_Hierarchical_Petri_Net',
                'metadata': {}
            }
            
            # Get model filepath if available (None for experiment snapshots)
            # ModelMetadata section will be skipped if model_path is None
            model_filepath = getattr(model, 'filepath', None)
            
            metadata_context = {
                'model': model_dict,
                'model_path': model_filepath,  # None for snapshots - ModelMetadata will be skipped
                'n_replicates': replicates,
                'experiment_index': snapshot_index,
                'experiment_name': name,
                'experiment_parameters': experiment_params,
                'simulation_config': {
                    'duration': duration,
                    'time_span': (0, duration),
                    'time_units': 'second',
                    'n_replicates': replicates,
                    'random_seed': seed_base,
                    'solver': 'TauLeaping_SSA',
                    'timestep': f'dt={dt_manual:.4g}' if dt_manual else 'adaptive (auto-dt)',
                    'use_tau_leaping': True,
                    'tau_epsilon': tau_epsilon,
                    'max_tau': max_tau,
                },
                'experiment_start_time': datetime.fromtimestamp(start_time, tz=timezone.utc),
                'elapsed_time': elapsed_time,
                'phase': snapshot.name if hasattr(snapshot, 'name') else name,
                'swept_parameter': swept_param,
                # Validation data
                'trajectory_data': trajectory_data,
                'warnings': warnings,
                'errors': errors,
                'execution_status': execution_status
            }
            
            # Generate metadata header (store for CSV export and display)
            try:
                generator = SweepHeaderGenerator()
                generator.set_context(metadata_context)
                generator.generate()
                metadata_header = generator.header
            except Exception as e:
                metadata_header = None
            
            # Return complete result dict with statistics (plottable from statistics)
            result = {
                'name': name,
                'snapshot_index': snapshot_index,
                'trajectory_summary': trajectory_summary,  # Lightweight summary
                'compressed_trajectories': compressed_trajectories,  # δ-filtered per-replicate data
                'n_replicates': _n_replicates_count,
                'statistics': statistics,  # Contains mean/std/percentiles for plotting
                'duration': elapsed_time,
                'swept_parameter': swept_param,  # Include swept parameter info for smart plotting
                'subnet_structure': subnet_structure,  # Include actual subnet composition
                'replicate_data': replicate_data,  # Per-replicate outcomes for statistical tests
                'metadata': metadata_header  # Metadata header for display and CSV export
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
            return {
                'places': list(model.places) if hasattr(model, 'places') else [],
                'transitions': list(model.transitions) if hasattr(model, 'transitions') else [],
                'arcs': list(model.arcs) if hasattr(model, 'arcs') else []
            }
        
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

        # Apply property_overrides — these carry swept values for BOTH single-param and factorial
        # experiments. They take precedence over the legacy dicts above because they are set
        # AFTER copying place_markings/transition_rates/arc_weights from the baseline snapshot.
        # Without this block, sequential mode silently runs all conditions at baseline values.
        property_overrides = getattr(snapshot, 'property_overrides', {})
        if property_overrides:
            from .property_path_parser import parse_property_path, apply_property_to_object, resolve_object
            import logging
            _logger = logging.getLogger(__name__)
            for prop_path, value in property_overrides.items():
                try:
                    obj_id, prop_name = parse_property_path(prop_path)
                    obj = resolve_object(model, obj_id)
                    if obj:
                        apply_property_to_object(obj, prop_name, value)
                    else:
                        _logger.warning(f"[SEQUENTIAL] Object not found for override: {obj_id}")
                except Exception as e:
                    _logger.warning(f"[SEQUENTIAL] Failed to apply override {prop_path}={value}: {e}")

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
