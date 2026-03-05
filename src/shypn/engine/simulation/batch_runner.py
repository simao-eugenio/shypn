#!/usr/bin/env python3
"""
Batch Simulation Runner - Execute batch mode simulations for full models

Provides batch execution functionality for running N replicates of a simulation
with selective recording of marked objects. Used by the GUI when batch mode is
enabled in simulation settings.

Key differences from ReplicateRunner:
- Selective recording: Only records marked objects (reduced memory/file size)
- Full model execution: Works on entire model, not subnet
- GUI integration: Progress callbacks and cancellation support
- Auto-save support: Returns structured data for CSV export
- Initial condition noise: Optional random perturbations for biological variability

Example:
    from shypn.engine.simulation.batch_runner import BatchSimulationRunner
    
    runner = BatchSimulationRunner()
    results = runner.run_batch(
        controller=simulation_controller,
        n_replicates=100,
        recorded_objects=['place_1', 'place_2', 'trans_1'],
        progress_callback=lambda r, t, e: print(f"Replicate {r}/{t}")
    )
    
    # Results contain only recorded objects
    for result in results:
        print(result['time_points'])
        print(result['place_data'])  # Only recorded places
        print(result['transition_data'])  # Only recorded transitions

Author: SHYpn Development Team
Date: December 2025
"""

import time
import multiprocessing as mp
import numpy as np
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from copy import deepcopy

from shypn.engine.simulation.controller import SimulationController

# ---------------------------------------------------------------------------
# Module-level state for fork-based worker (set before forking, never pickled)
# ---------------------------------------------------------------------------
_FORK_RUNNER: 'Optional[BatchSimulationRunner]' = None
_FORK_CONTROLLER: Optional[Any] = None
_FORK_INITIAL_MARKING: Optional[Dict[str, float]] = None


def _replicate_range_worker(
    args: Tuple[Any, ...]
) -> List[Dict[str, Any]]:
    """Module-level worker function executed in a forked subprocess.

    On Linux (the default multiprocessing start method is ``fork``), the child
    inherits the parent’s full memory space — including the compiled C
    accelerator, numpy arrays, and the fully-built SimulationController.  No
    pickling of the controller is required.

    Args
    ----
    args : (start, end, base_seed, recorded_objects, duration, progress_queue)
        ``start``, ``end`` — inclusive replicate range *[start, end)*
        ``base_seed``        — seed for replicate ``i`` is ``base_seed + i``
        ``recorded_objects`` — set of IDs to record
        ``duration``         — simulation duration
        ``progress_queue``   — ``mp.Queue`` to push (replicate_id,) progress
                               signals, or ``None`` to skip
    """
    start, end, base_seed, recorded_objects, duration, progress_queue = args
    runner = _FORK_RUNNER
    controller = _FORK_CONTROLLER
    initial_marking = _FORK_INITIAL_MARKING

    if runner is None or controller is None or initial_marking is None:
        return []  # Should never happen after proper fork setup

    results: List[Dict[str, Any]] = []

    for i in range(start, end):
        try:
            controller.settings.random_seed = base_seed + i

            runner._reset_model(
                controller.model,
                initial_marking,
                apply_noise=controller.settings.ic_noise_enabled,
                noise_percent=controller.settings.ic_noise_percent,
                noise_places=controller.settings.ic_noise_places,
                seed=base_seed + i,
            )

            controller.time = 0.0
            controller._event_last_triggered = {}
            controller._event_pending_assignments = []
            # Phase 5: pre-allocated numpy buffer + skip expensive rate eval
            _rec_iv = getattr(controller.data_collector, 'recording_time_interval', 0.5)
            _n_hint = (int(duration / _rec_iv) + 16) if duration and _rec_iv > 0 else None
            controller.data_collector.start_collection(n_steps_hint=_n_hint, skip_rate_eval=True)
            controller.data_collector.record_state(controller.time)

            dt = controller.settings.get_effective_dt()
            max_steps = int(duration / dt) if dt > 0 and duration is not None else 1000
            controller._update_enablement_states()

            stopped_reason = 'duration'
            for _step in range(max_steps):
                if not controller.step(time_step=dt):
                    stopped_reason = 'deadlock'
                    break

            controller.data_collector.finalize_buf()  # Phase 5: flush numpy recording buffer
            time_points = controller.data_collector.time_points.copy()
            if not recorded_objects:
                place_data = {
                    pid: d.copy()
                    for pid, d in controller.data_collector.place_data.items()
                }
                transition_data = {
                    tid: d.copy()
                    for tid, d in controller.data_collector.transition_data.items()
                }
            else:
                place_data = {
                    pid: d.copy()
                    for pid, d in controller.data_collector.place_data.items()
                    if pid in recorded_objects
                }
                transition_data = {
                    tid: d.copy()
                    for tid, d in controller.data_collector.transition_data.items()
                    if tid in recorded_objects
                }

            results.append({
                'replicate_id': i,
                'seed': base_seed + i,
                'time_points': time_points,
                'place_data': place_data,
                'transition_data': transition_data,
                'stopped_reason': stopped_reason,
                'final_time': controller.time,
                'validation_results': controller.data_collector.validation_results,
            })
        except Exception as exc:
            results.append({
                'replicate_id': i,
                'seed': base_seed + i,
                'error': str(exc),
                'stopped_reason': 'error',
            })
        finally:
            if progress_queue is not None:
                try:
                    progress_queue.put_nowait(i)
                except Exception:
                    pass

    return results


class BatchSimulationRunner:
    """Execute batch simulation runs with selective recording.
    
    This class manages the execution of multiple simulation replicates
    for the GUI batch mode feature. Key features:
    - Selective recording: Only track marked objects
    - Progress reporting: Callbacks with replicate number and ETA
    - Cancellation support: Graceful cancellation after current replicate
    - Memory efficient: Discards unrecorded object data
    """
    
    def __init__(self) -> None:
        """Initialize batch runner."""
        self.is_cancelled = False
        # Parallel execution configuration (Phase 4a).
        # multiprocessing is used only when n_replicates >= this threshold AND
        # the caller sets use_parallel=True.  Fork-based on Linux (default).
        self.parallel_threshold: int = 12
        self.max_parallel_workers: int = min(mp.cpu_count(), 16)
        
    def run_batch(
        self,
        controller: SimulationController,
        n_replicates: int,
        recorded_objects: Set[str],
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None
    ) -> List[Dict[str, Any]]:
        """Run batch of simulation replicates with selective recording.
        
        Args:
            controller: Configured SimulationController instance (will be reset for each replicate)
            n_replicates: Number of replicates to execute
            recorded_objects: Set of place/transition IDs to record (all others ignored)
            progress_callback: Optional callback(replicate_num, total_replicates, elapsed_time, eta_str)
            cancellation_check: Optional callback that returns True if cancellation requested
            
        Returns:
            List of dictionaries, one per replicate, each containing:
                - 'replicate_id': Replicate index (0 to n_replicates-1)
                - 'seed': Random seed used for this replicate
                - 'time_points': List of time values
                - 'place_data': Dict of place_id -> List[token_count] (only recorded places)
                - 'transition_data': Dict of trans_id -> List[firing_count] (only recorded transitions)
                - 'stopped_reason': Reason simulation stopped ('duration', 'deadlock', 'cancelled')
                - 'final_time': Final simulation time reached
                - 'error': Error message if replicate failed (optional)
        
        Notes:
            - Controller's model should have initial marking set before calling
            - Controller's settings should be configured (duration, tau-leaping, etc.)
            - Only objects in recorded_objects will be tracked (saves memory)
            - Random seed is incremented per replicate: base_seed + replicate_id
            - Place concentrations stored as float for biochemical accuracy
        """
        results = []
        start_time = time.time()
        self.is_cancelled = False

        # Get base configuration from controller
        settings = controller.settings
        model = controller.model
        base_seed = settings.random_seed if hasattr(settings, 'random_seed') else 42
        duration = settings.duration if hasattr(settings, 'duration') else 100.0

        # Store initial marking for reset between replicates
        initial_marking = {place.id: place.tokens for place in model.places}

        # Phase 4a: dispatch to fork-based parallel runner when it makes sense.
        # Conditions: Linux fork available, n >= threshold, and not already
        # inside a worker (nested fork would be dangerous).
        _in_worker = mp.current_process().name != 'MainProcess'
        if (
            not _in_worker
            and n_replicates >= self.parallel_threshold
            and not self.is_cancelled
        ):
            return self.run_batch_parallel(
                controller=controller,
                n_replicates=n_replicates,
                recorded_objects=recorded_objects,
                initial_marking=initial_marking,
                base_seed=base_seed,
                duration=duration,
                progress_callback=progress_callback,
                cancellation_check=cancellation_check,
                start_time=start_time,
            )
        
        # PERFORMANCE FIX: Create controller ONCE, reuse for all replicates
        # Creating 100 controllers = 100× behavior initialization overhead = 2× slowdown
        # verbose=False: No debug output
        # RecordingConfig with step_based: Record every 100th step for batch efficiency
        # For 500s simulation with dt=0.01: 50k steps → 500 data points (vs 50k with interval=1)
        # This reduces memory overhead by 100× and speeds up batch execution by ~2×
        from shypn.core.value_objects import RecordingConfig
        
        recording_config = RecordingConfig.step_based(interval=100, recorded_objects=recorded_objects)
        replicate_controller = SimulationController(model, verbose=False, recording_config=recording_config)
        
        # Copy settings from original controller (only needs to happen once)
        replicate_controller.settings = deepcopy(settings)
        
        # Update DataCollector's recorded_objects to match settings
        # If recorded_objects is empty, DataCollector will record ALL objects
        replicate_controller.data_collector.recorded_objects = recorded_objects
        
        # PERFORMANCE: Enable time-based recording for smoother data density
        # Record every 0.5 seconds of simulation time instead of every Nth step
        replicate_controller.data_collector.time_based_recording = True
        replicate_controller.data_collector.recording_time_interval = 0.5  # seconds
        
        # τ-leaping is always active (use_tau_leaping setter is a no-op by design).
        # All other settings (tau_epsilon, max_tau, use_parallel_stochastic, etc.) are
        # preserved from the user's controller settings via the deepcopy above.
        replicate_controller.settings.use_tau_leaping = True
        replicate_controller.settings.use_jit_kernel = True  # Phase 6: enable JIT in batch
        
        for i in range(n_replicates):
            # Check for cancellation before starting replicate
            if cancellation_check and cancellation_check():
                self.is_cancelled = True
                break
            
            try:
                # Set unique seed for this replicate
                replicate_controller.settings.random_seed = base_seed + i
                
                # Reset model to initial marking with optional noise
                self._reset_model(
                    model, 
                    initial_marking,
                    apply_noise=replicate_controller.settings.ic_noise_enabled,
                    noise_percent=replicate_controller.settings.ic_noise_percent,
                    noise_places=replicate_controller.settings.ic_noise_places,
                    seed=base_seed + i  # Use replicate-specific seed for noise
                )
                
                # Reset controller time to 0 for new replicate
                replicate_controller.time = 0.0

                # Reset environment-event tracking so edge-triggered events re-arm
                # in every replicate (controller is reused for performance).
                replicate_controller._event_last_triggered = {}
                replicate_controller._event_pending_assignments = []

                # Phase 5: pre-allocated numpy buffer + skip expensive rate eval
                _rec_iv = getattr(replicate_controller.data_collector, 'recording_time_interval', 0.5)
                _n_hint = (int(duration / _rec_iv) + 16) if duration and _rec_iv > 0 else None
                replicate_controller.data_collector.start_collection(
                    n_steps_hint=_n_hint, skip_rate_eval=True
                )
                replicate_controller.data_collector.record_state(replicate_controller.time)
                
                # Calculate time step (use same as real-time mode)
                dt = replicate_controller.settings.get_effective_dt()
                max_steps = int(duration / dt) if dt > 0 and duration is not None else 1000
                
                # Initialize enablement states before stepping
                replicate_controller._update_enablement_states()
                
                # Run simulation step-by-step (like real-time mode does internally)
                stopped_reason = "duration"
                for step_num in range(max_steps):
                    success = replicate_controller.step(time_step=dt)
                    if not success:
                        stopped_reason = "deadlock"
                        break
                    
                    # Check cancellation periodically
                    if step_num % 100 == 0 and cancellation_check and cancellation_check():
                        stopped_reason = "cancelled"
                        self.is_cancelled = True
                        break
                
                # Collect data - if recorded_objects is empty, include everything
                replicate_controller.data_collector.finalize_buf()  # Phase 5: flush numpy recording buffer
                time_points = replicate_controller.data_collector.time_points.copy()
                
                # If no objects specified for recording, export ALL data
                if not recorded_objects:
                    place_data = {place_id: data.copy() for place_id, data in replicate_controller.data_collector.place_data.items()}
                    transition_data = {trans_id: data.copy() for trans_id, data in replicate_controller.data_collector.transition_data.items()}
                else:
                    # Filter place data to only recorded places
                    place_data = {}
                    for place_id, data in replicate_controller.data_collector.place_data.items():
                        if place_id in recorded_objects:
                            place_data[place_id] = data.copy()
                    
                    # Filter transition data to only recorded transitions
                    transition_data = {}
                    for trans_id, data in replicate_controller.data_collector.transition_data.items():
                        if trans_id in recorded_objects:
                            transition_data[trans_id] = data.copy()
                
                # Store replicate result
                result = {
                    'replicate_id': i,
                    'seed': base_seed + i,
                    'time_points': time_points,
                    'place_data': place_data,
                    'transition_data': transition_data,
                    'stopped_reason': stopped_reason,
                    'final_time': replicate_controller.time,
                    'validation_results': replicate_controller.data_collector.validation_results
                }
                results.append(result)
                
            except Exception as e:
                # Record error but continue with other replicates
                results.append({
                    'replicate_id': i,
                    'seed': base_seed + i,
                    'error': str(e),
                    'stopped_reason': 'error'
                })
            
            # Report progress
            if progress_callback:
                elapsed = time.time() - start_time
                avg_time_per_rep = elapsed / (i + 1)
                remaining_reps = n_replicates - (i + 1)
                eta_seconds = avg_time_per_rep * remaining_reps
                
                # Format ETA string
                if eta_seconds < 60:
                    eta_str = f"{int(eta_seconds)}s"
                elif eta_seconds < 3600:
                    minutes = int(eta_seconds / 60)
                    seconds = int(eta_seconds % 60)
                    eta_str = f"{minutes}m {seconds}s"
                else:
                    hours = int(eta_seconds / 3600)
                    minutes = int((eta_seconds % 3600) / 60)
                    eta_str = f"{hours}h {minutes}m"
                
                progress_callback(i + 1, n_replicates, elapsed, eta_str)

        return results

    # ------------------------------------------------------------------
    # Phase 4a: Fork-based parallel batch runner
    # ------------------------------------------------------------------

    def run_batch_parallel(
        self,
        controller: 'SimulationController',
        n_replicates: int,
        recorded_objects: Set[str],
        initial_marking: Dict[str, float],
        base_seed: int,
        duration: float,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
        start_time: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Run batch replicates in parallel using forked subprocesses.

        Uses Linux ``fork``-based multiprocessing: child processes inherit the
        parent's compiled C accelerator, numpy arrays, and fully-built
        SimulationController without any pickling.

        Each worker receives a range [start, end) of replicate indices and
        returns a list of result dicts.  Results are merged and sorted by
        replicate_id before return.

        Progress is tracked via ``imap_unordered`` so the callback fires after
        each *worker* chunk completes (not individual replicates).

        Args:
            controller: Fully configured controller (propensity accelerator
                        will be built here if not already ready).
            n_replicates: Total number of replicates.
            recorded_objects: Set of place/transition IDs to record.
            initial_marking: Pre-computed {place_id: tokens} snapshot.
            base_seed: Seed base; replicate i uses base_seed + i.
            duration: Simulation duration.
            progress_callback: Optional callback(done, total, elapsed, eta_str).
            cancellation_check: Optional callable returning True if cancelled.
            start_time: Optional wall-clock start (defaults to time.time()).

        Returns:
            List of result dicts identical to ``run_batch`` output.
        """
        import os

        global _FORK_RUNNER, _FORK_CONTROLLER, _FORK_INITIAL_MARKING

        start_time = start_time or time.time()

        # ── Set up the single replicate controller (same as sequential path) ──
        from shypn.core.value_objects import RecordingConfig
        recording_config = RecordingConfig.step_based(
            interval=100, recorded_objects=recorded_objects
        )
        replicate_controller = SimulationController(
            controller.model, verbose=False, recording_config=recording_config
        )
        replicate_controller.settings = deepcopy(controller.settings)
        replicate_controller.data_collector.recorded_objects = recorded_objects
        replicate_controller.data_collector.time_based_recording = True
        replicate_controller.data_collector.recording_time_interval = 0.5
        replicate_controller.settings.use_tau_leaping = True
        replicate_controller.settings.use_jit_kernel = True  # Phase 6: enable JIT in batch

        # Warm up the C accelerator BEFORE forking so every child inherits the
        # compiled .so (avoids N separate compilations in parallel workers).
        if hasattr(replicate_controller, '_ensure_propensity_accelerator'):
            try:
                replicate_controller._ensure_propensity_accelerator()
            except Exception:
                pass

        # ── Publish to module-level globals (safe to read after fork) ──
        _FORK_RUNNER = self
        _FORK_CONTROLLER = replicate_controller
        _FORK_INITIAL_MARKING = initial_marking

        # ── Partition replicates across workers ───────────────────────────────
        n_workers = min(
            max(1, self.max_parallel_workers),
            n_replicates,
            os.cpu_count() or 1,
        )
        chunk = max(1, (n_replicates + n_workers - 1) // n_workers)
        ranges = [
            (start, min(start + chunk, n_replicates))
            for start in range(0, n_replicates, chunk)
        ]
        worker_args = [
            (s, e, base_seed, recorded_objects, duration, None)
            for s, e in ranges
        ]

        # ── Fork-based pool ───────────────────────────────────────────────────
        results: List[Dict[str, Any]] = []
        completed = 0
        ctx = mp.get_context('fork')
        try:
            with ctx.Pool(processes=n_workers) as pool:
                for chunk_results in pool.imap_unordered(
                    _replicate_range_worker, worker_args
                ):
                    results.extend(chunk_results)
                    completed += len(chunk_results)
                    if cancellation_check and cancellation_check():
                        pool.terminate()
                        self.is_cancelled = True
                        break
                    if progress_callback:
                        elapsed = time.time() - start_time
                        avg = elapsed / completed if completed else 0
                        eta = avg * (n_replicates - completed)
                        if eta < 60:
                            eta_str = f"{int(eta)}s"
                        elif eta < 3600:
                            eta_str = f"{int(eta/60)}m {int(eta%60)}s"
                        else:
                            eta_str = f"{int(eta/3600)}h {int((eta%3600)/60)}m"
                        progress_callback(completed, n_replicates, elapsed, eta_str)
        finally:
            # Clean up globals so the controller can be GC'd after this call
            _FORK_RUNNER = None
            _FORK_CONTROLLER = None
            _FORK_INITIAL_MARKING = None

        # Sort by replicate_id to match sequential output ordering
        results.sort(key=lambda r: r.get('replicate_id', 0))
        return results

    def cancel(self) -> None:
        """Request cancellation of batch execution.

        Cancellation will occur after the current replicate completes.
        This is a graceful cancellation - already completed replicates
        will be preserved.
        """
        self.is_cancelled = True

    def _reset_model(self, model: Any, initial_marking: Dict[str, float], apply_noise: bool = False, noise_percent: float = 20.0, noise_places: Optional[Set[str]] = None, seed: Optional[int] = None) -> None:
        """Reset model places to initial marking with optional random perturbations.
        
        Supports both discrete (int) and continuous (float) concentrations.
        When apply_noise=True, adds random perturbations to simulate biological
        cell-to-cell variability in initial molecular counts.
        
        Args:
            model: DocumentModel to reset
            initial_marking: Dict of place_id -> token_count (float for concentrations)
            apply_noise: Whether to add random perturbations to initial conditions
            noise_percent: Percentage of noise (20 = ±20% uniform noise)
            noise_places: Set of place IDs to randomize (None = all non-catalyst places)
            seed: Random seed for noise generation (ensures reproducibility per replicate)
        
        Example:
            With noise_percent=20 and base value=0.5:
            - Noise range: 0.5 * uniform(0.8, 1.2) = uniform(0.4, 0.6)
            - Ensures different initial conditions for each replicate
            - Simulates biological variability in mRNA/protein counts at infection
        """
        # Initialize random number generator with replicate-specific seed
        if apply_noise and seed is not None:
            rng = np.random.RandomState(seed)
        else:
            rng = None
        
        for place in model.places:
            if place.id in initial_marking:
                base_value = initial_marking[place.id]
                
                # Apply noise if enabled
                if apply_noise and rng is not None:
                    # Determine if this place should be randomized
                    should_randomize = False
                    
                    if noise_places and len(noise_places) > 0:
                        # Explicit list: only randomize specified places
                        should_randomize = place.id in noise_places
                    else:
                        # Default: randomize all non-catalyst places with non-zero initial values
                        is_catalyst = getattr(place, 'is_catalyst', False)
                        should_randomize = (not is_catalyst) and (base_value > 0)
                    
                    if should_randomize:
                        # Calculate noise bounds: value * uniform(1-p%, 1+p%)
                        noise_factor = noise_percent / 100.0
                        min_factor = 1.0 - noise_factor
                        max_factor = 1.0 + noise_factor
                        
                        # Sample random multiplier
                        multiplier = rng.uniform(min_factor, max_factor)
                        
                        # Apply noise while maintaining non-negativity
                        place.tokens = max(0.0, base_value * multiplier)
                    else:
                        # No noise: use exact initial value
                        place.tokens = base_value
                else:
                    # Noise disabled: use exact initial value
                    place.tokens = base_value
