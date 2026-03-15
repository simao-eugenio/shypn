#!/usr/bin/env python3
"""
Replicate Runner - High-level API for running simulation replicates

Provides a convenient facade for running multiple stochastic simulation
replicates with different random seeds. Designed for CLI tools and
experimental validation workflows.

Example:
    from shypn.engine.simulation.replicate_runner import ReplicateRunner
    
    runner = ReplicateRunner(model)
    results = runner.run_replicates(
        n=1000,
        use_parallel=True,
        use_tau_leaping=True,
        duration=100.0
    )
    
    # Get statistics
    stats = runner.compute_statistics(results)
    
    # Export to CSV
    runner.export_trajectories_csv(results, "trajectories.csv")
"""
import json
import time
import numpy as np
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any, Union

from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings
from shypn.utils.time_utils import TimeUnits


class ReplicateRunner:
    """High-level API for running simulation replicates.
    
    This class provides a convenient interface for:
    - Running n independent stochastic simulations
    - Managing random seeds for reproducibility
    - Computing statistics across replicates
    - Exporting trajectory data
    
    Attributes:
        model: DocumentModel instance to simulate
        default_settings: Default SimulationSettings to use
    """
    
    def __init__(self, model: Any, settings: Optional[SimulationSettings] = None):
        """Initialize replicate runner.
        
        Args:
            model: DocumentModel instance
            settings: Optional default settings (will be copied for each replicate)
        """
        self.model = model
        self.default_settings = settings or SimulationSettings()
        
    def run_replicates(
        self,
        n: int = 1000,
        use_parallel: bool = True,
        use_tau_leaping: bool = True,
        duration: float = 100.0,
        termination_condition: str = "deadlock",
        time_step: Optional[float] = None,
        epsilon: float = 0.03,
        max_tau: float = 0.1,
        seed_base: int = 42,
        time_units: TimeUnits = TimeUnits.SECONDS,
        verbose: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        """Run n independent stochastic simulation replicates.
        
        Each replicate uses a different random seed (seed_base + i) for
        reproducibility while ensuring statistical independence.
        
        Args:
            n: Number of replicates to run
            use_parallel: Use parallel stochastic execution
            use_tau_leaping: Use tau-leaping algorithm
            duration: Simulation duration in time_units (maximum time limit)
            termination_condition: When to stop ("time_only", "deadlock", "steady_state")
                - "time_only": Run until duration is reached
                - "deadlock": Stop when deadlock occurs OR duration is reached
                - "steady_state": Stop when steady state detected OR duration is reached
            time_step: Time step for recording (None = auto)
            epsilon: Tau-leaping epsilon parameter
            max_tau: Maximum leap size for tau-leaping (smaller = more accurate)
            seed_base: Base random seed (replicate i uses seed_base + i)
            time_units: Time units for duration
            verbose: Print progress messages
            progress_callback: Optional callback called with progress (0.0-1.0) after each replicate
            
        Returns:
            List of dictionaries, one per replicate, each containing:
                - 'replicate_id': Replicate index (0 to n-1)
                - 'seed': Random seed used
                - 'time_points': List of time points
                - 'place_data': Dict mapping place_id to token counts over time
                - 'transition_data': Dict mapping transition_id to firing counts
                - 'final_marking': Dict of place_id -> final token count
                - 'total_firings': Dict of transition_id -> total firings
                - 'stopped_reason': Why simulation stopped ("duration", "deadlock", "steady_state")
        """
        if verbose:
            print(f"Running {n} replicates...")
            print(f"  Parallel: {use_parallel}")
            print(f"  Tau-leaping: {use_tau_leaping}")
            print(f"  Duration: {duration} {time_units.value}")
        
        results = []
        last_callback_time = time.time()  # Initialize with current time
        
        # Report initial 0% progress
        if progress_callback:
            progress_callback(0.0)

        # ── Create ONE controller for all replicates ────────────────────
        # PERFORMANCE: building a fresh SimulationController per replicate
        # caused N× ctypes.CDLL loads of the compiled C accelerator .so.
        # Instead we create it once, configure all settings, and only reset
        # the model marking / time / data-collector between replicates — the
        # same pattern used by batch_runner.py.
        controller = SimulationController(self.model)
        controller.settings.use_parallel_stochastic = use_parallel
        controller.settings.use_tau_leaping = use_tau_leaping
        controller.settings.tau_epsilon = epsilon
        controller.settings.max_tau = max_tau
        controller.settings.duration = duration
        controller.settings.time_units = time_units
        if time_step is not None:
            controller.settings.dt_auto = False
            controller.settings.dt_manual = time_step

        # Pre-calculate dt / max_steps (constant across replicates)
        dt = time_step if time_step else controller.settings.get_effective_dt()
        max_steps = int(duration / dt)

        # Snapshot the initial model marking so we can restore it each replicate
        initial_marking = {p.id: p.tokens for p in self.model.places}
        # ────────────────────────────────────────────────────────────────

        for i in range(n):
            # Track wall-clock time for this replicate
            replicate_start_time = time.time()
            
            if verbose and (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{n} replicates")
            
            # Progress reporting: update at 1% boundaries to show smooth progress
            # With batched UI updates, this is now safe and won't flood GTK
            if progress_callback and i > 0:
                current_pct = int((i / n) * 100)
                prev_pct = int(((i - 1) / n) * 100)
                
                # Only call callback when percentage changes (every 1%)
                at_boundary = current_pct > prev_pct
                is_last = (i == n - 1)
                
                if at_boundary or is_last:
                    progress_callback(i / n)
                    last_callback_time = time.time()
            
            # ── Reset state for this replicate (controller is reused) ──────
            # Unique seed for reproducible but independent replicates
            controller.settings.random_seed = seed_base + i

            # Restore model to initial marking
            for place in self.model.places:
                place.tokens = initial_marking.get(place.id, place.tokens)
            for transition in self.model.transitions:
                transition.firing_count = 0

            # Reset controller time and one-shot event state
            controller.time = 0.0
            controller._event_last_triggered = {}
            controller._event_pending_assignments = []
            # ────────────────────────────────────────────────────────────────

            # Reset model to initial marking (for any place not in initial_marking)
            self._reset_model(self.model)
            
            # Start data collection — Phase 5 fast path: pre-allocated float32
            # numpy buffer (max_steps+1 rows) + skip expensive per-transition
            # rate evaluation (propensities are already computed by the C
            # accelerator inside the tau-leaping engine).
            # Buffer path is disabled for steady_state termination because
            # the mid-loop convergence check reads place_data directly before
            # finalize_buf() converts the buffer to the dict format.
            _use_buf = termination_condition != "steady_state"
            controller.data_collector.start_collection(
                n_steps_hint=max_steps + 1 if _use_buf else None,
                skip_rate_eval=True,
            )
            # Record initial state at t=0
            controller.data_collector.record_state(controller.time)
            
            # Calculate max_steps from duration (already computed above; kept for clarity)
            # dt and max_steps are constant across replicates
            
            # Run simulation synchronously (step-by-step) for background execution
            # controller.run() uses GLib callbacks which don't work in threads
            stopped_reason = "duration"  # Default: ran to completion
            try:
                # Initialize enablement states before simulation
                controller._update_enablement_states()
                
                # Execute simulation steps synchronously
                for step_num in range(max_steps):
                    success = controller.step(time_step=dt)
                    if not success:
                        # Simulation stopped (deadlock)
                        if termination_condition in ["deadlock", "steady_state"]:
                            stopped_reason = "deadlock"
                            break  # Early termination allowed
                        elif termination_condition == "time_only":
                            # Time-only mode: ignore deadlock, continue (this shouldn't happen but handle it)
                            pass
                    
                    # Check for steady state (simple heuristic: no token changes for N steps)
                    if termination_condition == "steady_state" and step_num > 100:
                        # Check if token counts haven't changed in last 50 steps.
                        # Data is stored as (time, tokens) tuples — extract just the
                        # token component so the time field doesn't prevent detection.
                        recent_data = controller.data_collector.place_data
                        if recent_data and len(list(recent_data.values())[0]) >= 50:
                            # Check last 50 time points for all places
                            all_stable = True
                            for place_id, data in recent_data.items():
                                if len(data) >= 50:
                                    last_50 = [
                                        v[1] if isinstance(v, tuple) else v
                                        for v in data[-50:]
                                    ]
                                    if not all(v == last_50[0] for v in last_50):
                                        all_stable = False
                                        break
                            
                            if all_stable:
                                stopped_reason = "steady_state"
                                break
            except Exception as e:
                import traceback as _tb
                import os as _os
                _err_tb = _tb.format_exc()
                if verbose:
                    print(f"  ERROR in replicate {i}: {e}")
                # Always log the first replicate failure to the debug file
                if i == 0:
                    _dlog = _os.path.expanduser("~/sweep_debug.log")
                    with open(_dlog, 'a') as _f:
                        _f.write(f"[REPLICATE 0 ERROR] {type(e).__name__}: {e}\n")
                        _f.write(_err_tb)
                # Store error but continue (include elapsed time even for errors)
                replicate_elapsed = time.time() - replicate_start_time
                results.append({
                    'replicate_id': i,
                    'seed': seed_base + i,
                    'elapsed_time': replicate_elapsed,
                    'error': str(e)
                })
                continue
            
            # Flush Phase 5 fast-path numpy buffer into place_data before
            # harvesting the result dict (no-op if buffer path wasn't used).
            controller.data_collector.stop_collection()

            # Calculate elapsed wall-clock time for this replicate
            replicate_elapsed = time.time() - replicate_start_time
            
            # Collect results
            result = {
                'replicate_id': i,
                'seed': seed_base + i,
                'time_points': controller.data_collector.time_points.copy(),
                'place_data': {
                    pid: data.copy() 
                    for pid, data in controller.data_collector.place_data.items()
                },
                'transition_data': {
                    tid: data.copy()
                    for tid, data in controller.data_collector.transition_data.items()
                },
                'transition_rates': {
                    tid: data.copy()
                    for tid, data in controller.data_collector.transition_rates.items()
                },
                'final_marking': {
                    p.id: p.tokens for p in self.model.places
                },
                'total_firings': {
                    t.id: getattr(t, 'firing_count', 0)
                    for t in self.model.transitions
                },
                'stopped_reason': stopped_reason,
                'elapsed_time': replicate_elapsed  # Wall-clock time in seconds
            }
            
            results.append(result)
        
        # Report final 100% progress
        if progress_callback:
            progress_callback(1.0)
        
        if verbose:
            successful = sum(1 for r in results if 'error' not in r)
            print(f"✓ Completed: {successful}/{n} successful replicates")
        
        return results
    
    def compute_statistics(
        self,
        results: List[Dict[str, Any]],
        percentiles: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Compute statistics across replicates.
        
        Computes mean, std, min, max, CV (coefficient of variation),
        and optionally percentiles for each species (places and transitions) at each time point.
        
        Args:
            results: List of replicate results from run_replicates()
            percentiles: Optional list of percentiles to compute (e.g., [25, 50, 75])
            
        Returns:
            Dictionary containing:
                - 'n_replicates': Number of successful replicates
                - 'time_points': Common time points
                - 'species_statistics': Dict mapping place_id OR transition_id to statistics dict
                    Each statistics dict contains:
                    - 'mean': Mean trajectory (tokens for places, firing counts for transitions)
                    - 'std': Standard deviation
                    - 'min': Minimum trajectory
                    - 'max': Maximum trajectory
                    - 'cv': Coefficient of variation
                    - 'percentiles': Dict of percentile -> trajectory (if requested)
        """
        if percentiles is None:
            percentiles = [25, 50, 75]
        
        # Filter out failed replicates
        successful = [r for r in results if 'error' not in r]
        n_replicates = len(successful)
        
        if n_replicates == 0:
            raise ValueError("No successful replicates to compute statistics")
        
        # Get common time points (assume all replicates have same times)
        time_points = successful[0]['time_points']
        if isinstance(time_points, np.ndarray):
            time_points = time_points.tolist()
        
        # Get all place IDs
        place_ids = list(successful[0]['place_data'].keys())
        
        # Get all transition IDs (if available)
        transition_ids = []
        if 'transition_data' in successful[0]:
            transition_ids = list(successful[0]['transition_data'].keys())
        
        statistics = {
            'n_replicates': n_replicates,
            'time_points': time_points,
            'species_statistics': {}
        }
        
        # Compute elapsed time statistics (wall-clock time per replicate)
        elapsed_times = [r.get('elapsed_time', 0.0) for r in successful]
        if elapsed_times:
            statistics['mean_elapsed_time'] = float(np.mean(elapsed_times))
            statistics['std_elapsed_time'] = float(np.std(elapsed_times))
            statistics['min_elapsed_time'] = float(np.min(elapsed_times))
            statistics['max_elapsed_time'] = float(np.max(elapsed_times))
        
        # Compute statistics for each place
        for place_id in place_ids:
            # Stack trajectories into matrix (replicates × time_points)
            # Extract only token values (second element) from (time, tokens) tuples
            trajectories: Any = []
            for r in successful:
                place_values = r['place_data'][place_id]
                # Handle numpy arrays (fast-path buffer), (time, tokens) tuples, and flat lists
                if isinstance(place_values, np.ndarray):
                    trajectories.append(place_values)
                elif len(place_values) > 0 and isinstance(place_values[0], tuple):
                    trajectories.append([tokens for time, tokens in place_values])
                else:
                    trajectories.append(place_values)
            
            trajectories = np.array(trajectories)
            
            # Compute statistics
            mean = np.mean(trajectories, axis=0)
            std = np.std(trajectories, axis=0)
            min_traj = np.min(trajectories, axis=0)
            max_traj = np.max(trajectories, axis=0)
            
            # Coefficient of variation (handle divide by zero)
            cv = np.zeros_like(mean)
            nonzero_mask = mean > 0
            cv[nonzero_mask] = std[nonzero_mask] / mean[nonzero_mask]
            
            # Percentiles
            percentile_data = {
                p: np.percentile(trajectories, p, axis=0)
                for p in percentiles
            }
            
            statistics['species_statistics'][place_id] = {
                'mean': mean.tolist(),
                'std': std.tolist(),
                'min': min_traj.tolist(),
                'max': max_traj.tolist(),
                'cv': cv.tolist(),
                'percentiles': {
                    p: data.tolist()
                    for p, data in percentile_data.items()
                }
            }
        
        # Compute statistics for each transition (use instantaneous rates from simulation).
        # transition_rates is empty ({}) when skip_rate_eval=True (fast-path / batch mode);
        # in that case skip rate statistics gracefully rather than KeyError.
        has_rates = bool(successful[0].get('transition_rates'))
        if not has_rates:
            transition_ids = []  # nothing to iterate
        for transition_id in transition_ids:
            # Stack rate trajectories into matrix (replicates × time_points)
            # Extract only rate values (second element) from (time, rate) tuples
            rate_trajectories: Any = []
            for r in successful:
                rate_values = r['transition_rates'][transition_id]
                # Handle numpy arrays (fast-path buffer), (time, rate) tuples, and flat lists
                if isinstance(rate_values, np.ndarray):
                    rate_trajectories.append(rate_values)
                elif len(rate_values) > 0 and isinstance(rate_values[0], tuple):
                    rate_trajectories.append([rate for time, rate in rate_values])
                else:
                    rate_trajectories.append(rate_values)
            
            rate_trajectories = np.array(rate_trajectories)
            
            # Compute statistics on instantaneous rates (no derivatives needed!)
            mean = np.mean(rate_trajectories, axis=0)
            std = np.std(rate_trajectories, axis=0)
            min_traj = np.min(rate_trajectories, axis=0)
            max_traj = np.max(rate_trajectories, axis=0)
            
            # Coefficient of variation (handle divide by zero)
            cv = np.zeros_like(mean)
            nonzero_mask = mean > 0
            cv[nonzero_mask] = std[nonzero_mask] / mean[nonzero_mask]
            
            # Percentiles
            percentile_data = {
                p: np.percentile(rate_trajectories, p, axis=0)
                for p in percentiles
            }
            
            statistics['species_statistics'][transition_id] = {
                'mean': mean.tolist(),
                'std': std.tolist(),
                'min': min_traj.tolist(),
                'max': max_traj.tolist(),
                'cv': cv.tolist(),
                'percentiles': {
                    p: data.tolist()
                    for p, data in percentile_data.items()
                }
            }
        
        return statistics
    
    def export_trajectories_csv(
        self,
        results: List[Dict[str, Any]],
        filepath: Union[str, Path],
        format: str = 'wide',
        include_transitions: bool = False
    ) -> None:
        """Export trajectory data to CSV.
        
        Args:
            results: List of replicate results from run_replicates()
            filepath: Output CSV file path
            format: 'wide' (one column per species) or 'long' (tidy format)
            include_transitions: Include transition firing counts
        """
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Filter successful replicates
        successful = [r for r in results if 'error' not in r]
        
        if len(successful) == 0:
            raise ValueError("No successful replicates to export")
        
        if format == 'wide':
            self._export_wide(successful, filepath, include_transitions)
        elif format == 'long':
            self._export_long(successful, filepath, include_transitions)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def _export_wide(
        self,
        results: List[Dict[str, Any]],
        filepath: Path,
        include_transitions: bool
    ) -> None:
        """Export in wide format (one row per time point per replicate)."""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            # Determine columns
            place_ids = sorted(results[0]['place_data'].keys())
            
            if include_transitions:
                transition_ids = sorted(results[0]['transition_data'].keys())
                columns = ['replicate', 'time'] + place_ids + transition_ids
            else:
                columns = ['replicate', 'time'] + place_ids
            
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            # Write data for each replicate
            for result in results:
                time_points = result['time_points']
                replicate_id = result['replicate_id']
                
                for t_idx, time in enumerate(time_points):
                    row = {
                        'replicate': replicate_id,
                        'time': time
                    }
                    
                    # Add place data
                    for place_id in place_ids:
                        row[place_id] = result['place_data'][place_id][t_idx]
                    
                    # Add transition data if requested
                    if include_transitions:
                        for trans_id in transition_ids:
                            row[trans_id] = result['transition_data'][trans_id][t_idx]
                    
                    writer.writerow(row)
    
    def _export_long(
        self,
        results: List[Dict[str, Any]],
        filepath: Path,
        include_transitions: bool
    ) -> None:
        """Export in long/tidy format (one row per observation)."""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            columns = ['replicate', 'time', 'entity_type', 'entity_id', 'value']
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for result in results:
                time_points = result['time_points']
                replicate_id = result['replicate_id']
                
                for t_idx, time in enumerate(time_points):
                    # Export place data
                    for place_id, data in result['place_data'].items():
                        writer.writerow({
                            'replicate': replicate_id,
                            'time': time,
                            'entity_type': 'place',
                            'entity_id': place_id,
                            'value': data[t_idx]
                        })
                    
                    # Export transition data if requested
                    if include_transitions:
                        for trans_id, data in result['transition_data'].items():
                            writer.writerow({
                                'replicate': replicate_id,
                                'time': time,
                                'entity_type': 'transition',
                                'entity_id': trans_id,
                                'value': data[t_idx]
                            })
    
    def export_statistics_json(
        self,
        statistics: Dict[str, Any],
        filepath: Union[str, Path]
    ) -> None:
        """Export statistics to JSON.
        
        Args:
            statistics: Statistics dict from compute_statistics()
            filepath: Output JSON file path
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(statistics, f, indent=2)
    
    def _reset_model(self, model: Any) -> None:
        """Reset model to initial marking.
        
        Args:
            model: DocumentModel to reset
        """
        # Reset place tokens to initial marking
        for place in model.places:
            if hasattr(place, 'initial_tokens'):
                place.tokens = place.initial_tokens
            else:
                # If no initial_tokens stored, keep current (assume it's initial)
                place.initial_tokens = place.tokens
        
        # Reset transition firing counts
        for transition in model.transitions:
            transition.firing_count = 0
