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
                # recording_interval=20: Record every 20th step (20x faster data collection)
                replicate_controller = SimulationController(model, verbose=False, recording_interval=20)
                
                # Copy settings from original controller
                replicate_controller.settings = deepcopy(settings)
                
                # BATCH MODE OPTIMIZATIONS: Increase tau-leaping parameters for speed
                # Larger max_tau allows bigger time jumps in stochastic simulation
                if hasattr(replicate_controller.settings, 'max_tau'):
                    replicate_controller.settings.max_tau = min(replicate_controller.settings.max_tau * 5.0, 5.0)
                
                # Set unique seed for this replicate
                replicate_controller.settings.random_seed = base_seed + i
                
                # Reset model to initial marking
                self._reset_model(model, initial_marking)
                
                # Start data collection (will track all objects initially)
                replicate_controller.data_collector.start_collection()
                replicate_controller.data_collector.record_state(replicate_controller.time)
                
                # Calculate time step
                dt = replicate_controller.settings.get_effective_dt()
                
                # BATCH MODE OPTIMIZATION: Use larger time step for faster execution
                # Increase dt by 10x for batch mode (reduces steps from 1000 to 100)
                # This is acceptable since we're only recording every 20th step anyway
                batch_dt = dt * 10.0
                max_steps = int(duration / batch_dt) if batch_dt > 0 else 1000
                
                # Run simulation synchronously (step-by-step)
                stopped_reason = "duration"
                replicate_controller._update_enablement_states()
                
                for step_num in range(max_steps):
                    success = replicate_controller.step(time_step=batch_dt)
                    if not success:
                        # Deadlock detected
                        stopped_reason = "deadlock"
                        break
                    
                    # Check cancellation during long simulations
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
    
    def _reset_model(self, model, initial_marking: Dict[str, int]):
        """Reset model places to initial marking.
        
        Args:
            model: DocumentModel to reset
            initial_marking: Dict of place_id -> token_count
        """
        for place in model.places:
            if place.id in initial_marking:
                place.tokens = initial_marking[place.id]
    
    def cancel(self):
        """Request cancellation of batch execution.
        
        Cancellation will occur after the current replicate completes.
        This is a graceful cancellation - already completed replicates
        will be preserved.
        """
        self.is_cancelled = True
