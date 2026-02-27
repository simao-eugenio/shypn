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

from typing import Optional, Dict, Any, Tuple
try:
    from gi.repository import GLib
    GLIB_AVAILABLE = True
except ImportError:
    GLIB_AVAILABLE = False
    GLib = None

# Import ChangeListener for atomic settings awareness
try:
    from shypn.engine.simulation.buffered.base import ChangeListener
except ImportError:
    ChangeListener = object  # Fallback if not available


class ContinuousExecutor(ChangeListener):
    """Execute simulations continuously with GUI updates.
    
    This class implements continuous simulation execution using GLib timeout
    callbacks for smooth GUI updates. It adaptively batches simulation steps
    to maintain responsive visualization at all time scales.
    
    Implements ChangeListener to be notified of atomic settings commits.
    
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
    
    def __init__(self, controller: Any):
        """Initialize continuous executor.
        
        Args:
            controller: SimulationController instance
        """
        self.controller = controller
        
        # Register as listener for atomic settings changes
        # This ensures we're notified immediately when settings commit
        if hasattr(controller, 'buffered_settings') and controller.buffered_settings:
            controller.buffered_settings.add_listener(self)
    
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
        
        # Calculate initial step batching based on current time_scale
        self._recalculate_batching(time_step)
        
        # CRITICAL: Initialize all stochastic transitions before simulation starts
        # This ensures they have valid scheduled firing times
        self.controller._update_enablement_states()
        
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
                        logger.debug(
                            f"  ○ {transition.name} (ID={transition.id}): enabled but rate=0 "
                            f"(normal homeostatic state — will fire when rate becomes positive)"
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
    
    def _recalculate_batching(self, time_step: float) -> None:
        """Recalculate step batching based on current time_scale.
        
        This is called both at simulation start and when settings change
        during a running simulation to make playback speed adjustments
        take effect immediately.
        
        Args:
            time_step: Time increment per step
        """
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
        # Example: model_time=1.0s (10x speed), time_step=0.1s → 10 steps per GUI update
        calculated_steps = max(1, int(model_time_per_gui_update / time_step))
        
        # Safety cap: Prevent UI freeze on extreme time_scale values
        # Cap at 1000 steps per GUI update (allows up to ~10000x speedup with dt=0.001)
        # This is the ONLY cap - removed the overly restrictive 3-step cap that broke playback
        self.controller._steps_per_callback = min(calculated_steps, 1000)
        
        # Debug logging for playback speed verification
        import logging
        logger = logging.getLogger(__name__)
        
        # Log when batching is capped (indicates extreme speed)
        if calculated_steps != self.controller._steps_per_callback:
            logger.info(
                f"⚡ Extreme speed: Batching capped at {self.controller._steps_per_callback} steps/callback "
                f"(requested {calculated_steps} for {self.controller.settings.time_scale}x speed, dt={time_step}s). "
                f"Simulation will complete very quickly!"
            )
        elif self.controller.settings.time_scale >= 100:
            # Log high speed settings for user awareness
            model_time_per_callback = self.controller._steps_per_callback * time_step
            logger.info(
                f"⚡ High speed mode: {self.controller.settings.time_scale}x playback "
                f"= {model_time_per_callback:.1f}s model time per 100ms real time "
                f"({self.controller._steps_per_callback} steps/callback)"
            )
    
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
        
        # Recalculate batching dynamically to respond to time_scale changes
        # This makes playback speed changes take effect immediately
        self._recalculate_batching(self.controller._time_step)
        
        # Calculate visual update frequency within batch for smooth animation
        # Balance between smooth rendering and performance
        steps_per_batch = self.controller._steps_per_callback
        
        # Update ~20 times per batch for smooth token movement and progress bar
        # Cap at minimum interval of 5 steps (don't update TOO frequently)
        visual_update_interval = max(5, steps_per_batch // 20)
        
        # Execute a batch of simulation steps for smooth animation
        for step_idx in range(self.controller._steps_per_callback):
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
            
            # For batches with 20+ steps, update visual display periodically
            # This ensures smooth token rendering and progress bar movement
            if steps_per_batch >= 20 and (step_idx + 1) % visual_update_interval == 0:
                if GLIB_AVAILABLE:
                    context = GLib.MainContext.default()
                    # Process pending GTK events to update canvas and progress display
                    # This allows smooth token movement and progress bar updates at high speeds
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
                
                # Emit simulation.completed event via EventBus (for Report Panel integration)
                try:
                    from shypn.events import EventBus
                    document_id = None
                    if hasattr(self.controller, 'model') and hasattr(self.controller.model, 'drawing_area') and self.controller.model.drawing_area:
                        document_id = id(self.controller.model.drawing_area)
                    EventBus.emit('simulation.completed', {
                        'controller': self.controller,
                        'time_points': len(self.controller.data_collector.time_points) if self.controller.data_collector else 0
                    }, document_id=document_id)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to emit simulation.completed event: {e}")
                
                # Notify completion callback (deferred to avoid blocking UI)
                if self.controller.on_simulation_complete:
                    def deferred_callback() -> bool:
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
        
        # PERFORMANCE: Process GTK events at END of batch (final cleanup)
        # For batches with 20+ steps, we also process events ~20 times within the batch
        # to maintain smooth token animation and progress bar updates (see periodic updates above)
        if GLIB_AVAILABLE:
            context = GLib.MainContext.default()
            while context.pending():
                context.iteration(False)
        
        # All steps in batch completed, GUI will update before next callback
        return True
    
    def stop(self) -> None:
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
        
        # Emit simulation.completed event via EventBus (for Report Panel integration)
        try:
            from shypn.events import EventBus
            document_id = None
            if hasattr(self.controller, 'model') and hasattr(self.controller.model, 'drawing_area') and self.controller.model.drawing_area:
                document_id = id(self.controller.model.drawing_area)
            EventBus.emit('simulation.completed', {
                'controller': self.controller,
                'time_points': len(self.controller.data_collector.time_points) if self.controller.data_collector else 0
            }, document_id=document_id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to emit simulation.completed event: {e}")
        
        # Notify completion callback (deferred to avoid blocking)
        if self.controller.on_simulation_complete and GLIB_AVAILABLE:
            def deferred_callback() -> bool:
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
    
    # ========== ChangeListener Interface (Atomic Settings Awareness) ==========
    
    def on_parameter_changed(self, parameter_name: str, old_value: Any, new_value: Any) -> None:
        """Called when a single parameter changes.
        
        Note: Not used in buffered mode (changes are batched and committed atomically).
        
        Args:
            parameter_name: Name of parameter that changed
            old_value: Previous value
            new_value: New value
        """
        pass  # Not used - we only react to atomic commits
    
    def on_changes_committed(self, changes: Dict[str, Tuple[Any, Any]]) -> None:
        """Called when buffered changes are committed atomically.
        
        This is the key method for atomic settings awareness. When settings
        are committed (all validated and applied together), we are notified
        immediately and can react to specific changes.
        
        The executor reads settings directly from controller.settings on every
        loop iteration (every 100ms), so changes take effect automatically.
        This notification allows us to log and potentially optimize reactions.
        
        Args:
            changes: Dict mapping parameter names to (old_value, new_value) tuples
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Log atomic commit for debugging
        if changes:
            logger.debug(f"✓ ContinuousExecutor notified of atomic settings commit: {list(changes.keys())}")
        
        # React to specific changes
        if 'time_scale' in changes:
            old_scale, new_scale = changes['time_scale']
            logger.info(f"✓ Playback speed changed atomically: {old_scale}x → {new_scale}x")
            
            # If simulation is running, note that batching will update on next loop
            if self.controller._running:
                logger.debug("  Simulation running - batching updates automatically on next iteration (≤100ms)")
        
        # React to duration/time_units changes
        if 'duration' in changes or 'time_units' in changes:
            logger.debug("✓ Duration/time_units changed atomically")
            # Components observing settings will update (e.g., plot axes)
        
        # React to dt_auto/dt_manual changes
        if 'dt_auto' in changes or 'dt_manual' in changes:
            logger.debug("✓ Time step mode/value changed atomically")
            # Next loop iteration will use new dt calculation
    
    def on_changes_rolled_back(self, changes: Dict[str, Tuple[Any, Any]]) -> None:
        """Called when buffered changes are rolled back.
        
        This happens when validation fails or user cancels changes.
        
        Args:
            changes: Dict mapping parameter names to (old_value, new_value) tuples
        """
        import logging
        if changes:
            logging.getLogger(__name__).debug(f"⚠ Settings changes rolled back: {list(changes.keys())}")
