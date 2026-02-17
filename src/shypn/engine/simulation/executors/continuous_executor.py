"""Continuous execution strategy for simulation runs.

This module implements the Strategy pattern for continuous simulation execution,
extracted from SimulationController as part of Phase 2 quality improvements.

The ContinuousExecutor handles:
- Continuous run mode with GLib timeout callbacks
- Adaptive step batching for smooth visualization
- Stop condition management
- Data collection coordination
- Thermodynamic validation on completion
"""

from typing import Optional
try:
    from gi.repository import GLib
    GLIB_AVAILABLE = True
except ImportError:
    GLIB_AVAILABLE = False
    GLib = None


class ContinuousExecutor:
    """Execute simulations continuously with GUI updates.
    
    This class implements continuous simulation execution using GLib timeout
    callbacks for smooth GUI updates. It adaptively batches simulation steps
    to maintain responsive visualization at all time scales.
    
    Design Pattern: Strategy (execution mode)
    
    Key Features:
    - Adaptive step batching based on time scale
    - Smooth animation with 100ms GUI updates
    - Stop condition management (max_steps, duration)
    - Stochastic transition initialization verification
    - Automatic data collection coordination
    - Thermodynamic validation on completion
    
    Usage:
        executor = ContinuousExecutor(controller)
        if executor.run(time_step=0.1, max_steps=1000):
            print("Simulation started")
        # Later...
        executor.stop()
    
    Attributes:
        controller: SimulationController instance providing model and state access
    """
    
    def __init__(self, controller):
        """Initialize continuous executor.
        
        Args:
            controller: SimulationController instance
        """
        self.controller = controller
    
    def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
        """Start continuous simulation execution.
        
        Runs the simulation continuously using GLib timeout callbacks.
        Can be stopped by calling stop().
        
        Args:
            time_step: Time increment per step (None = use effective dt from settings)
            max_steps: Maximum number of steps to run (None = use duration-based or unlimited)
        
        Returns:
            bool: True if started successfully, False if already running or GLib unavailable
        """
        if not GLIB_AVAILABLE:
            return False
        if self.controller._running:
            return False
        
        # Use effective dt if not specified
        if time_step is None:
            time_step = self.controller.get_effective_dt()
        
        # Calculate max_steps from duration if not specified
        # For stochastic simulations using τ-leaping: Use much higher step limit
        # because τ-leaping takes adaptive (often large) steps but still counts
        # each step() call. We use 100× the normal estimate as a safety limit
        # while relying primarily on time-based termination.
        if max_steps is None:
            estimated_steps = self.controller.settings.estimate_step_count()
            if estimated_steps is not None:
                has_stochastic = any(
                    t.transition_type == 'stochastic' 
                    for t in self.controller.model.transitions
                )
                if has_stochastic:
                    # Stochastic: 100× safety limit (relies on time-based termination)
                    max_steps = estimated_steps * 100
                else:
                    # Deterministic: Use normal step count
                    max_steps = estimated_steps
        
        self.controller._running = True
        self.controller._stop_requested = False
        self.controller._max_steps = max_steps
        self.controller._steps_executed = 0
        self.controller._time_step = time_step
        
        # Start data collection
        if self.controller.data_collector:
            self.controller.data_collector.start_collection()
            # Record initial state
            self.controller.data_collector.record_state(self.controller.time)
        
        # Calculate optimal step batching for smooth animation with time scale
        # Target: Execute multiple steps per GUI update to maintain smooth visualization
        # For small time steps (e.g., 0.002s), batch many steps together
        # For large time steps (e.g., 1.0s), execute 1 step per GUI update
        # Time scale: Controls playback speed (1.0 = real-time, 60.0 = 60x faster)
        
        gui_interval_s = 0.1  # Fixed 100ms GUI update interval (real-world playback time)
        
        # Calculate how much MODEL time should pass per GUI update
        # time_scale = model_seconds / real_seconds
        # Example: time_scale=60.0 means 60 seconds of model time per 1 second of real time
        model_time_per_gui_update = gui_interval_s * self.controller.settings.time_scale
        
        # Calculate how many simulation steps needed to cover that model time
        # Example: model_time=6.0s, time_step=1.0s → 6 steps per GUI update
        # PERFORMANCE FIX: Limit batch size to prevent UI freeze
        # Large batches (e.g., 10+ steps) block GTK event loop too long
        calculated_steps = max(1, int(model_time_per_gui_update / time_step))
        self.controller._steps_per_callback = min(calculated_steps, 3)  # Cap at 3 steps max
        
        # Safety cap: Prevent UI freeze on extreme time_scale values
        # Cap at 1000 steps per GUI update (allows up to ~10000x speedup with dt=0.001)
        if self.controller._steps_per_callback > 1000:
            self.controller._steps_per_callback = 1000
        else:
            self.controller._steps_per_callback = min(self.controller._steps_per_callback, 1000)
        
        # CRITICAL: Initialize all stochastic transitions before simulation starts
        # This ensures they have valid scheduled firing times
        self.controller._update_enablement_states()
        
        # Auto-detect and configure conservation groups (enabled by default)
        # DISABLED: Conservation must emerge from arc connections, not artificial adjustments
        # if self.controller.auto_conservation_enabled and not self.controller.conservation_enforcer.conservation_groups:
        #     self.controller._auto_detect_conservation_groups()
        
        # Verify stochastic transitions are properly scheduled
        stochastic_transitions = [
            t for t in self.controller.model.transitions 
            if t.transition_type == 'stochastic'
        ]
        if stochastic_transitions:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Initializing {len(stochastic_transitions)} stochastic transition(s)")
            
            for transition in stochastic_transitions:
                behavior = self.controller._get_behavior(transition)
                state = self.controller.transition_states.get(transition.id)
                
                # Log initialization status
                if state and state.enablement_time is not None:
                    scheduled_time = (
                        behavior.get_scheduled_fire_time() 
                        if hasattr(behavior, 'get_scheduled_fire_time') 
                        else None
                    )
                    if scheduled_time is not None:
                        logger.info(
                            f"  ✓ {transition.name} (ID={transition.id}): enabled, "
                            f"scheduled to fire at t={scheduled_time:.3f}"
                        )
                    else:
                        logger.warning(
                            f"  ⚠ {transition.name} (ID={transition.id}): enabled but NOT scheduled "
                            f"(rate may be 0 or evaluation failed)"
                        )
                else:
                    logger.info(
                        f"  ○ {transition.name} (ID={transition.id}): not enabled "
                        f"(insufficient tokens)"
                    )
        
        # Check for timing info (used for debugging, but not critical)
        for transition in self.controller.model.transitions:
            state = self.controller.transition_states.get(transition.id)
            behavior = self.controller._get_behavior(transition)
            if hasattr(behavior, 'get_timing_info'):
                info = behavior.get_timing_info()
            elif hasattr(behavior, 'get_stochastic_info'):
                info = behavior.get_stochastic_info()
            else:
                pass  # No timing info available
        
        self.controller._timeout_id = GLib.timeout_add(100, self._simulation_loop)
        return True
    
    def _simulation_loop(self) -> bool:
        """Internal simulation loop callback.
        
        Executes multiple simulation steps per GUI update for smooth animation
        at all time scales. For very small time steps (e.g., 2ms), this batches
        many steps together to avoid choppy visualization.
        
        Returns:
            bool: True to continue, False to stop the timeout
        """
        DEBUG_LOOP = False
        
        if self.controller._stop_requested:
            self.controller._running = False
            self.controller._timeout_id = None
            return False
        
        # Execute a batch of simulation steps for smooth animation
        for _ in range(self.controller._steps_per_callback):
            # Check stop conditions before each step in the batch
            if self.controller._stop_requested:
                self.controller._running = False
                self.controller._timeout_id = None
                return False
                
            if (self.controller._max_steps is not None and 
                self.controller._steps_executed >= self.controller._max_steps):
                import logging
                logging.getLogger(__name__).info(
                    f"[LOOP] Stopping: steps_executed={self.controller._steps_executed} "
                    f">= max_steps={self.controller._max_steps}"
                )
                self.controller._running = False
                self.controller._timeout_id = None
                return False
            
            # Execute one simulation step
            success = self.controller.step(self.controller._time_step)
            
            # CRITICAL: Yield to GTK event loop to keep UI responsive
            # Process pending GUI events (mouse, keyboard, window updates)
            # This prevents UI freeze during long-running simulations
            if GLIB_AVAILABLE:
                context = GLib.MainContext.default()
                while context.pending():
                    context.iteration(False)
            
            if not success:
                import logging
                logging.getLogger(__name__).info(
                    f"[LOOP] step() returned False at time={self.controller.time}, "
                    f"steps_executed={self.controller._steps_executed}"
                )
                # Simulation completed (duration reached)
                self.controller._running = False
                self.controller._timeout_id = None
                
                # Record final state before stopping collection (force=True to bypass interval check)
                if (self.controller.data_collector and 
                    self.controller.data_collector.is_collecting):
                    self.controller.data_collector.record_state(
                        self.controller.time, 
                        force=True
                    )
                
                # Finalize thermodynamic validation
                if (self.controller.validator_manager and 
                    len(self.controller.validator_manager) > 0):
                    places_dict = {p.id: p for p in self.controller.model.places}
                    transitions_dict = {t.id: t for t in self.controller.model.transitions}
                    self.controller.validator_manager.validate_all()
                    
                    # Store validation summary in data_collector for export
                    if self.controller.data_collector:
                        self.controller.data_collector.validation_results = (
                            self.controller.validator_manager.get_summary()
                        )
                
                # Stop data collection
                if self.controller.data_collector:
                    self.controller.data_collector.stop_collection()
                
                # Token accounting report will be exported via Report Panel if user exports CSV
                # No terminal output needed - keeps terminal clean
                
                # Notify completion callback (deferred to avoid blocking UI)
                if self.controller.on_simulation_complete:
                    def deferred_callback():
                        try:
                            self.controller.on_simulation_complete()
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).exception(
                                f"[ERROR] Exception in on_simulation_complete callback: {e}"
                            )
                            import traceback
                            traceback.print_exc()
                        return False  # Don't repeat
                    GLib.idle_add(deferred_callback)
                
                return False
            
            self.controller._steps_executed += 1
        
        # All steps in batch completed, GUI will update before next callback
        return True
    
    def stop(self):
        """Stop the continuous simulation.
        
        This requests the simulation to stop. The actual stop will occur
        after the current step completes.
        
        IMPORTANT: This clears enablement states so that when Run is pressed
        again, transitions start fresh with enablement time = current time.
        """
        if not self.controller._running:
            return
        
        self.controller._stop_requested = True
        
        # Stop data collection
        if self.controller.data_collector:
            self.controller.data_collector.stop_collection()
        
        # Notify completion callback (deferred to avoid blocking)
        if self.controller.on_simulation_complete and GLIB_AVAILABLE:
            def deferred_callback():
                try:
                    self.controller.on_simulation_complete()
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).exception(
                        f"Exception in on_simulation_complete callback: {e}"
                    )
                return False  # Don't repeat
            GLib.idle_add(deferred_callback)
        
        # Clear enablement states for fresh restart
        for state in self.controller.transition_states.values():
            state.enablement_time = None
            state.scheduled_time = None
        for behavior in self.controller.behavior_cache.values():
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()
