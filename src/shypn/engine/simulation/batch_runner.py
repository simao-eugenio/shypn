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
import numpy as np
from typing import Dict, List, Optional, Any, Callable, Set
from copy import deepcopy

from shypn.engine.simulation.controller import SimulationController


class BatchSimulationRunner:
    """Execute batch simulation runs with selective recording.
    
    This class manages the execution of multiple simulation replicates
    for the GUI batch mode feature. Key features:
    - Selective recording: Only track marked objects
    - Progress reporting: Callbacks with replicate number and ETA
    - Cancellation support: Graceful cancellation after current replicate
    - Memory efficient: Discards unrecorded object data
    """
    
    def __init__(self):
        """Initialize batch runner."""
        self.is_cancelled = False
        
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
        
        for i in range(n_replicates):
            # Check for cancellation before starting replicate
            if cancellation_check and cancellation_check():
                self.is_cancelled = True
                break
            
            try:
                # Create fresh controller for this replicate
                # verbose=False: No debug output
                # recording_interval=1: Record every step for smooth stochastic trajectories
                replicate_controller = SimulationController(model, verbose=False, recording_interval=1)
                
                # Copy settings from original controller
                replicate_controller.settings = deepcopy(settings)
                
                # CRITICAL: Ensure stochastic/continuous mode with tau-leaping
                replicate_controller.settings.use_tau_leaping = True
                replicate_controller.settings.use_parallel_stochastic = True
                replicate_controller.settings.tau_epsilon = 0.03
                replicate_controller.settings.max_tau = 0.01
                replicate_controller.settings.critical_threshold = 0.01
                
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
                
                # Start data collection (will track all objects initially)
                replicate_controller.data_collector.start_collection()
                replicate_controller.data_collector.record_state(replicate_controller.time)
                
                # Calculate time step (use same as real-time mode)
                dt = replicate_controller.settings.get_effective_dt()
                max_steps = int(duration / dt) if dt > 0 else 1000
                
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
                
                # Collect data - but only for recorded objects
                time_points = replicate_controller.data_collector.time_points.copy()
                
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
                    'final_time': replicate_controller.time
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
    
    def _reset_model(
        self, 
        model, 
        initial_marking: Dict[str, float],
        apply_noise: bool = False,
        noise_percent: float = 20.0,
        noise_places: Set[str] = None,
        seed: int = None
    ):
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
    
    def cancel(self):
        """Request cancellation of batch execution.
        
        Cancellation will occur after the current replicate completes.
        This is a graceful cancellation - already completed replicates
        will be preserved.
        """
        self.is_cancelled = True
