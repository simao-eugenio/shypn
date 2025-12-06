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
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from copy import deepcopy

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
    
    def __init__(self, model, settings: Optional[SimulationSettings] = None):
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
        time_step: Optional[float] = None,
        epsilon: float = 0.03,
        seed_base: int = 42,
        time_units: TimeUnits = TimeUnits.SECONDS,
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """Run n independent stochastic simulation replicates.
        
        Each replicate uses a different random seed (seed_base + i) for
        reproducibility while ensuring statistical independence.
        
        Args:
            n: Number of replicates to run
            use_parallel: Use parallel stochastic execution
            use_tau_leaping: Use tau-leaping algorithm
            duration: Simulation duration in time_units
            time_step: Time step for recording (None = auto)
            epsilon: Tau-leaping epsilon parameter
            seed_base: Base random seed (replicate i uses seed_base + i)
            time_units: Time units for duration
            verbose: Print progress messages
            
        Returns:
            List of dictionaries, one per replicate, each containing:
                - 'replicate_id': Replicate index (0 to n-1)
                - 'seed': Random seed used
                - 'time_points': List of time points
                - 'place_data': Dict mapping place_id to token counts over time
                - 'transition_data': Dict mapping transition_id to firing counts
                - 'final_marking': Dict of place_id -> final token count
                - 'total_firings': Dict of transition_id -> total firings
        """
        if verbose:
            print(f"Running {n} replicates...")
            print(f"  Parallel: {use_parallel}")
            print(f"  Tau-leaping: {use_tau_leaping}")
            print(f"  Duration: {duration} {time_units.value}")
        
        results = []
        
        for i in range(n):
            if verbose and (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{n} replicates")
            
            # Create fresh controller for this replicate
            controller = SimulationController(self.model)
            
            # Configure settings
            controller.settings.use_parallel_stochastic = use_parallel
            controller.settings.use_tau_leaping = use_tau_leaping
            controller.settings.tau_epsilon = epsilon
            controller.settings.duration = duration
            controller.settings.time_units = time_units
            controller.settings.random_seed = seed_base + i
            
            if time_step is not None:
                controller.settings.dt_auto = False
                controller.settings.dt_manual = time_step
            
            # Reset model to initial marking
            self._reset_model(self.model)
            
            # Start data collection
            controller.data_collector.start_collection()
            
            # Run simulation
            try:
                controller.run(
                    duration=duration,
                    time_step=time_step if time_step else controller.settings.get_effective_dt()
                )
            except Exception as e:
                if verbose:
                    print(f"  ERROR in replicate {i}: {e}")
                # Store error but continue
                results.append({
                    'replicate_id': i,
                    'seed': seed_base + i,
                    'error': str(e)
                })
                continue
            
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
                'final_marking': {
                    p.id: p.tokens for p in self.model.places
                },
                'total_firings': {
                    t.id: getattr(t, 'firing_count', 0)
                    for t in self.model.transitions
                }
            }
            
            results.append(result)
        
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
        and optionally percentiles for each species at each time point.
        
        Args:
            results: List of replicate results from run_replicates()
            percentiles: Optional list of percentiles to compute (e.g., [25, 50, 75])
            
        Returns:
            Dictionary containing:
                - 'n_replicates': Number of successful replicates
                - 'time_points': Common time points
                - 'species_statistics': Dict mapping place_id to statistics dict
                    Each statistics dict contains:
                    - 'mean': Mean trajectory
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
        
        # Get all place IDs
        place_ids = list(successful[0]['place_data'].keys())
        
        statistics = {
            'n_replicates': n_replicates,
            'time_points': time_points,
            'species_statistics': {}
        }
        
        # Compute statistics for each place
        for place_id in place_ids:
            # Stack trajectories into matrix (replicates × time_points)
            trajectories = np.array([
                r['place_data'][place_id]
                for r in successful
            ])
            
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
        
        return statistics
    
    def export_trajectories_csv(
        self,
        results: List[Dict[str, Any]],
        filepath: Union[str, Path],
        format: str = 'wide',
        include_transitions: bool = False
    ):
        """Export trajectory data to CSV.
        
        Args:
            results: List of replicate results from run_replicates()
            filepath: Output CSV file path
            format: 'wide' (one column per species) or 'long' (tidy format)
            include_transitions: Include transition firing counts
        """
        import csv
        
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
    ):
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
    ):
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
    ):
        """Export statistics to JSON.
        
        Args:
            statistics: Statistics dict from compute_statistics()
            filepath: Output JSON file path
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(statistics, f, indent=2)
    
    def _reset_model(self, model):
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
