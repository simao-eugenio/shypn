"""
Simulation Controller for Petri Net Execution

Manages the execution of Petri net simulations, including:
    pass
- Single-step execution
- Continuous execution (run mode)
- Stop/pause functionality
- Reset to initial marking

Based on the legacy shypnpy simulation controller but adapted for
the new architecture.
"""
import random
from typing import Callable, List, Optional, Dict, Any
try:
    from gi.repository import GLib
    GLIB_AVAILABLE = True
except ImportError:
    GLIB_AVAILABLE = False
    GLib = None
from shypn.engine import behavior_factory
from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy, DEFAULT_POLICY, TYPE_PRIORITIES

class TransitionState:
    """Per-transition state tracking for time-aware behaviors.
    
    Tracks when transitions become enabled/disabled and scheduled firing times
    for stochastic transitions.
    
    Attributes:
        enablement_time: Time when transition became structurally enabled (None if disabled)
        scheduled_time: Scheduled firing time for stochastic transitions (None if not scheduled)
    """

    def __init__(self):
        """Initialize transition state."""
        self.enablement_time = None
        self.scheduled_time = None

class ModelAdapter:
    """Adapter to provide dict-like interface for behavior classes.
    
    The behavior classes expect model.places, model.arcs, etc. to be
    dictionaries keyed by ID. This adapter wraps the ModelCanvasManager
    (which uses lists) to provide that interface.
    """

    def __init__(self, canvas_manager, controller=None):
        """Initialize adapter with canvas manager.
        
        Args:
            canvas_manager: ModelCanvasManager instance
            controller: SimulationController instance (for accessing logical_time)
        """
        self.canvas_manager = canvas_manager
        self._controller = controller
        self._places_dict = None
        self._transitions_dict = None
        self._arcs_dict = None

    @property
    def places(self):
        """Get places as dictionary keyed by ID."""
        if self._places_dict is None:
            self._places_dict = {p.id: p for p in self.canvas_manager.places}
        return self._places_dict

    @property
    def transitions(self):
        """Get transitions as dictionary keyed by ID."""
        if self._transitions_dict is None:
            self._transitions_dict = {t.id: t for t in self.canvas_manager.transitions}
        return self._transitions_dict

    @property
    def arcs(self):
        """Get arcs as dictionary keyed by ID."""
        if self._arcs_dict is None:
            self._arcs_dict = {a.id: a for a in self.canvas_manager.arcs}
        return self._arcs_dict

    @property
    def logical_time(self):
        """Get current logical time from controller.
        
        Returns:
            float: Current simulation time from controller, or 0.0 if no controller
        """
        if self._controller is not None:
            return self._controller.time
        return 0.0

    def invalidate_caches(self):
        """Invalidate dict caches (call when model structure changes)."""
        self._places_dict = None
        self._transitions_dict = None
        self._arcs_dict = None

class SimulationController:
    """Controller for Petri net simulation execution.
    
    This controller manages the simulation of a Petri net model, handling
    transition firing, token movement, and simulation state.
    
    Attributes:
        model: ModelCanvasManager instance (has places, transitions, arcs lists)
        time: Current simulation time
        settings: SimulationSettings instance for timing configuration
        step_listeners: List of callbacks to notify on each step
    """

    def __init__(self, model):
        """Initialize the simulation controller.
        
        Args:
            model: ModelCanvasManager instance (has places, transitions, arcs lists)
        """
        self.model = model
        self.time = 0.0
        self.model_adapter = ModelAdapter(model, controller=self)
        self.step_listeners = []
        self._running = False
        self._stop_requested = False
        self._timeout_id = None
        self.behavior_cache = {}
        self.transition_states = {}
        self.conflict_policy = DEFAULT_POLICY
        self._round_robin_index = 0
        self.data_collector = None
        
        # Timing configuration (composition pattern)
        from shypn.engine.simulation.settings import SimulationSettings
        self.settings = SimulationSettings()

    def _get_behavior(self, transition):
        """Get or create behavior instance for a transition.
        
        Uses factory pattern with caching for efficiency. Behavior instances
        are reused across simulation steps based on transition ID.
        
        CRITICAL: Validates cache against current transition_type to handle
        dynamic type changes during simulation. If type changes, invalidates
        and recreates the behavior instance.
        
        Args:
            transition: Transition object with transition_type property
            
        Returns:
            TransitionBehavior: Behavior instance for this transition type
        """
        if transition.id in self.behavior_cache:
            cached_behavior = self.behavior_cache[transition.id]
            cached_type = cached_behavior.get_type_name()
            current_type = getattr(transition, 'transition_type', 'immediate')
            type_name_map = {'Immediate': 'immediate', 'Timed (TPN)': 'timed', 'Stochastic (FSPN)': 'stochastic', 'Continuous (SHPN)': 'continuous'}
            cached_type_normalized = type_name_map.get(cached_type, cached_type.lower())
            if cached_type_normalized != current_type:
                if hasattr(cached_behavior, 'clear_enablement'):
                    cached_behavior.clear_enablement()
                del self.behavior_cache[transition.id]
                if transition.id in self.transition_states:
                    del self.transition_states[transition.id]
        if transition.id not in self.behavior_cache:
            behavior = behavior_factory.create_behavior(transition, self.model_adapter)
            self.behavior_cache[transition.id] = behavior
        return self.behavior_cache[transition.id]

    def _get_or_create_state(self, transition) -> TransitionState:
        """Get or create state tracking for a transition.
        
        Args:
            transition: Transition object
            
        Returns:
            TransitionState: State tracking instance for this transition
        """
        if transition.id not in self.transition_states:
            self.transition_states[transition.id] = TransitionState()
        return self.transition_states[transition.id]

    def _update_enablement_states(self):
        """Update enablement tracking for all transitions.
        
        This method checks structural enablement (sufficient tokens in input places)
        for all transitions and updates their enablement times. This is needed for
        time-aware behaviors (timed, stochastic).
        
        For each transition:
            pass
        - If newly enabled: record current time as enablement_time
        - If still enabled: keep existing enablement_time
        - If disabled: clear enablement_time
        """
        for transition in self.model.transitions:
            behavior = self._get_behavior(transition)
            input_arcs = behavior.get_input_arcs()
            locally_enabled = True
            for arc in input_arcs:
                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                if kind != 'normal':
                    continue
                source_place = behavior._get_place(arc.source_id)
                if source_place is None or source_place.tokens < arc.weight:
                    locally_enabled = False
                    break
            state = self._get_or_create_state(transition)
            if locally_enabled:
                if state.enablement_time is None:
                    state.enablement_time = self.time
                    if hasattr(behavior, 'set_enablement_time'):
                        behavior.set_enablement_time(self.time)
            else:
                if state.enablement_time is not None:
                    pass
                state.enablement_time = None
                state.scheduled_time = None
                if hasattr(behavior, 'clear_enablement'):
                    behavior.clear_enablement()

    def set_conflict_policy(self, policy: ConflictResolutionPolicy):
        """Set the conflict resolution policy for transition selection.
        
        Args:
            policy: ConflictResolutionPolicy enum value
        """
        self.conflict_policy = policy
        self._round_robin_index = 0
    
    # ========== Settings Delegation Methods ==========
    
    def get_effective_dt(self) -> float:
        """Get effective time step (delegates to settings).
        
        Returns:
            float: Time step in seconds
        """
        return self.settings.get_effective_dt()
    
    def get_progress(self) -> float:
        """Get simulation progress as fraction [0.0, 1.0].
        
        Returns:
            float: Progress fraction
        """
        return self.settings.calculate_progress(self.time)
    
    def is_simulation_complete(self) -> bool:
        """Check if simulation has reached duration limit.
        
        Returns:
            bool: True if time >= duration
        """
        return self.settings.is_complete(self.time)

    def invalidate_behavior_cache(self, transition_id=None):
        """Invalidate behavior cache for a specific transition or all transitions.
        
        This forces behavior instances to be recreated on next access, useful
        when transition types are changed programmatically.
        
        Args:
            transition_id: ID of specific transition to invalidate, or None for all
        """
        if transition_id is None:
            for behavior in self.behavior_cache.values():
                if hasattr(behavior, 'clear_enablement'):
                    behavior.clear_enablement()
            self.behavior_cache.clear()
            self.transition_states.clear()
        else:
            if transition_id in self.behavior_cache:
                behavior = self.behavior_cache[transition_id]
                if hasattr(behavior, 'clear_enablement'):
                    behavior.clear_enablement()
                del self.behavior_cache[transition_id]
            if transition_id in self.transition_states:
                del self.transition_states[transition_id]

    def add_step_listener(self, callback: Callable):
        """Register a callback to be notified on each simulation step.
        
        Args:
            callback: Function to call after each step. Should accept
                     (controller, time) as arguments.
        """
        if callback not in self.step_listeners:
            self.step_listeners.append(callback)

    def remove_step_listener(self, callback: Callable):
        """Unregister a step listener callback.
        
        Args:
            callback: The callback function to remove
        """
        if callback in self.step_listeners:
            self.step_listeners.remove(callback)

    def _notify_step_listeners(self):
        """Notify all registered step listeners."""
        for callback in self.step_listeners:
            try:
                callback(self, self.time)
            except Exception as e:

                pass

    def step(self, time_step: float = None) -> bool:
        """Execute a single simulation step with hybrid (discrete + continuous) execution.
        
        This performs one iteration of the simulation:
            pass
        1. Update enablement states at CURRENT time (for discrete transitions)
        2. EXHAUST IMMEDIATE TRANSITIONS - Fire all immediate transitions in zero time
        3. Identify enabled CONTINUOUS transitions FIRST (based on initial state)
        4. Execute DISCRETE transitions (timed, stochastic):
           - Find enabled transitions
           - Select one to fire (conflict resolution)
           - Fire the transition (discrete token changes)
        5. Execute CONTINUOUS transitions (continuous):
           - Integrate all previously-identified continuous transitions
           - Use the state BEFORE discrete firing for consistency
        6. Advance simulation time
        7. Notify listeners
        
        Args:
            time_step: Time increment for this step (None = use effective dt from settings)
        
        Returns:
            bool: True if any transition fired/integrated, False if deadlocked/complete
        """
        # Use effective dt if not specified
        if time_step is None:
            time_step = self.get_effective_dt()
        
        # Validate time step is non-negative
        if time_step < 0:
            raise ValueError(f"time_step must be non-negative, got {time_step}")
        
        # Warn about potentially problematic time steps
        if time_step > 1.0:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Large time step ({time_step}s) may cause timed transitions to miss firing windows")
        
        self._update_enablement_states()
        immediate_fired_total = 0
        max_immediate_iterations = 1000
        for iteration in range(max_immediate_iterations):
            immediate_transitions = [t for t in self.model.transitions if t.transition_type == 'immediate']
            enabled_immediate = [t for t in immediate_transitions if self._is_transition_enabled(t)]
            if not enabled_immediate:
                break
            transition = self._select_transition(enabled_immediate)
            self._fire_transition(transition)
            immediate_fired_total += 1
            self._update_enablement_states()
        
        if iteration >= max_immediate_iterations - 1:
            pass  # Max iterations reached, continue to next phase
        
        # === PHASE: Handle Timed Window Crossings ===
        # Check for timed transitions whose firing windows will be crossed during this step
        # These must fire even if the window is narrow or zero-width
        window_crossing_fired = 0
        timed_transitions = [t for t in self.model.transitions if t.transition_type == 'timed']
        for transition in timed_transitions:
            behavior = self._get_behavior(transition)
            
            # Check if this transition's window will be crossed
            if hasattr(behavior, '_enablement_time') and behavior._enablement_time is not None:
                elapsed_now = self.time - behavior._enablement_time
                elapsed_after = (self.time + time_step) - behavior._enablement_time
                
                # Window crossing: currently before window, will be after window
                will_cross = (elapsed_now < behavior.earliest and 
                             elapsed_after > behavior.latest)
                
                if will_cross:
                    # Check structural enablement (tokens only, ignore timing)
                    # For sources, always structurally enabled
                    is_source = hasattr(transition, 'properties') and \
                                transition.properties.get('is_source', False)
                    
                    has_tokens = True
                    if not is_source:
                        input_arcs = behavior.get_input_arcs()
                        for arc in input_arcs:
                            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                            if kind != 'normal':
                                continue
                            source_place = self.model_adapter.places.get(arc.source_id)
                            if source_place is None or source_place.tokens < arc.weight:
                                has_tokens = False
                                break
                    
                    if has_tokens:
                        # Manual token transfer for window crossing (bypass timing checks in fire())
                        # This is necessary because fire() checks timing, but we KNOW the window is crossed
                        consumed_map = {}
                        produced_map = {}
                        
                        # Consume tokens from input places
                        if not is_source:
                            for arc in behavior.get_input_arcs():
                                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                                if kind != 'normal':
                                    continue
                                source_place = self.model_adapter.places.get(arc.source_id)
                                source_place.set_tokens(source_place.tokens - arc.weight)
                                consumed_map[arc.source_id] = arc.weight
                        
                        # Produce tokens to output places
                        is_sink = hasattr(transition, 'properties') and \
                                  transition.properties.get('is_sink', False)
                        if not is_sink:
                            for arc in behavior.get_output_arcs():
                                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                                if kind != 'normal':
                                    continue
                                target_place = self.model_adapter.places.get(arc.target_id)
                                target_place.set_tokens(target_place.tokens + arc.weight)
                                produced_map[arc.target_id] = arc.weight
                        
                        # Clear enablement state
                        state = self._get_or_create_state(transition)
                        state.enablement_time = None
                        state.scheduled_time = None
                        
                        # Notify data collector
                        if self.data_collector is not None:
                            details = {
                                'consumed': consumed_map,
                                'produced': produced_map,
                                'window_crossing': True,
                                'timing_window': [behavior.earliest, behavior.latest]
                            }
                            self.data_collector.on_transition_fired(transition, self.time, details)
                        
                        window_crossing_fired += 1
        
        continuous_transitions = [t for t in self.model.transitions if t.transition_type == 'continuous']
        continuous_to_integrate = []
        for transition in continuous_transitions:
            behavior = self._get_behavior(transition)
            can_flow, reason = behavior.can_fire()
            if can_flow:
                input_arcs = behavior.get_input_arcs()
                output_arcs = behavior.get_output_arcs()
                continuous_to_integrate.append((transition, behavior, input_arcs, output_arcs))
        discrete_transitions = [t for t in self.model.transitions if t.transition_type in ['timed', 'stochastic']]
        enabled_discrete = [t for t in discrete_transitions if self._is_transition_enabled(t)]
        discrete_fired = False
        if enabled_discrete:
            transition = self._select_transition(enabled_discrete)
            self._fire_transition(transition)
            discrete_fired = True
        
        continuous_active = 0
        for transition, behavior, input_arcs, output_arcs in continuous_to_integrate:
            success, details = behavior.integrate_step(dt=time_step, input_arcs=input_arcs, output_arcs=output_arcs)
            if success:
                continuous_active += 1
                if self.data_collector is not None:
                    self.data_collector.on_transition_fired(transition, self.time, details)
        self.time += time_step
        self._notify_step_listeners()
        
        # Check if simulation is complete (duration reached)
        if self.is_simulation_complete():
            return False  # Simulation complete
        
        if immediate_fired_total > 0 or window_crossing_fired > 0 or discrete_fired or continuous_active > 0:
            return True
        waiting_count = 0
        ready_count = 0
        for transition in discrete_transitions:
            behavior = self._get_behavior(transition)
            can_fire, reason = behavior.can_fire()
            if can_fire:
                ready_count += 1
            elif reason and 'too-early' in str(reason):
                waiting_count += 1
        
        if waiting_count > 0 or ready_count > 0:
            return True
        
        return False

    def _find_enabled_transitions(self) -> List:
        """Find all transitions that are enabled (can fire).
        
        A transition is enabled if all its input places have enough tokens
        to satisfy the arc weights.
        
        Returns:
            List of enabled Transition objects
        """
        enabled = []
        transitions = self.model.transitions
        for transition in transitions:
            if self._is_transition_enabled(transition):
                enabled.append(transition)
        return enabled

    def _is_transition_enabled(self, transition) -> bool:
        """Check if a specific transition is enabled using behavior dispatch.
        
        Uses the transition's behavior to determine if it can fire based on
        locality (input places and arc weights only).
        
        Args:
            transition: Transition object to check
            
        Returns:
            bool: True if transition can fire, False otherwise
        """
        behavior = self._get_behavior(transition)
        can_fire, reason = behavior.can_fire()
        return can_fire

    def _fire_transition(self, transition):
        """Fire a transition using behavior dispatch.
        
        Uses the transition's behavior to perform the firing, which handles
        token removal/addition based on locality (input/output arcs).
        
        Args:
            transition: Transition object to fire
        """
        behavior = self._get_behavior(transition)
        input_arcs = behavior.get_input_arcs()
        output_arcs = behavior.get_output_arcs()
        success, details = behavior.fire(input_arcs, output_arcs)
        if success:
            state = self._get_or_create_state(transition)
            state.enablement_time = None
            state.scheduled_time = None
        if self.data_collector is not None:
            self.data_collector.on_transition_fired(transition, self.time, details)

    def _select_transition(self, enabled_transitions: List) -> Any:
        """Select one transition from enabled set based on conflict resolution policy.
        
        Args:
            enabled_transitions: List of enabled Transition objects
            
        Returns:
            Selected Transition object to fire
        """
        if len(enabled_transitions) == 1:
            return enabled_transitions[0]
        if self.conflict_policy == ConflictResolutionPolicy.RANDOM:
            return random.choice(enabled_transitions)
        elif self.conflict_policy == ConflictResolutionPolicy.PRIORITY:
            return max(enabled_transitions, key=lambda t: getattr(t, 'priority', 0))
        elif self.conflict_policy == ConflictResolutionPolicy.TYPE_BASED:
            return max(enabled_transitions, key=lambda t: TYPE_PRIORITIES.get(t.transition_type, 0))
        elif self.conflict_policy == ConflictResolutionPolicy.ROUND_ROBIN:
            selected = enabled_transitions[self._round_robin_index % len(enabled_transitions)]
            self._round_robin_index += 1
            return selected
        else:
            return random.choice(enabled_transitions)

    def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
        """Start continuous simulation execution.
        
        Runs the simulation continuously using GLib timeout callbacks.
        Can be stopped by calling stop().
        
        Args:
            time_step: Time increment per step (None = use effective dt from settings)
            max_steps: Maximum number of steps to run (None = use duration-based or unlimited)
        
        Returns:
            bool: True if started successfully, False if already running
        """
        if not GLIB_AVAILABLE:
            return False
        if self._running:
            return False
        for transition in self.model.transitions:
            state = self.transition_states.get(transition.id)
            behavior = self._get_behavior(transition)
        
        # Use effective dt if not specified
        if time_step is None:
            time_step = self.get_effective_dt()
        
        # Calculate max_steps from duration if not specified
        if max_steps is None:
            estimated_steps = self.settings.estimate_step_count()
            if estimated_steps is not None:
                max_steps = estimated_steps
        
        self._running = True
        self._stop_requested = False
        self._max_steps = max_steps
        self._steps_executed = 0
        self._time_step = time_step
        
        # Calculate optimal step batching for smooth animation
        # Target: Execute multiple steps per GUI update to maintain smooth visualization
        # For small time steps (e.g., 0.002s), batch many steps together
        # For large time steps (e.g., 1.0s), execute 1 step per GUI update
        gui_interval_s = 0.1  # Fixed 100ms GUI update interval
        self._steps_per_callback = max(1, int(gui_interval_s / time_step))
        self._steps_per_callback = min(self._steps_per_callback, 100)  # Cap at 100 steps/update
        
        self._update_enablement_states()
        for transition in self.model.transitions:
            state = self.transition_states.get(transition.id)
            behavior = self._get_behavior(transition)
            if hasattr(behavior, 'get_timing_info'):
                info = behavior.get_timing_info()
            elif hasattr(behavior, 'get_stochastic_info'):
                info = behavior.get_stochastic_info()
            else:
                pass  # No timing info available
        
        self._timeout_id = GLib.timeout_add(100, self._simulation_loop)
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
        if DEBUG_LOOP:
            pass
        if self._stop_requested:
            if DEBUG_LOOP:
                pass
            self._running = False
            self._timeout_id = None
            return False
        
        # Execute a batch of simulation steps for smooth animation
        for _ in range(self._steps_per_callback):
            # Check stop conditions before each step in the batch
            if self._stop_requested:
                self._running = False
                self._timeout_id = None
                return False
            if self._max_steps is not None and self._steps_executed >= self._max_steps:
                if DEBUG_LOOP:
                    pass
                self._running = False
                self._timeout_id = None
                return False
            
            # Execute one simulation step
            success = self.step(self._time_step)
            if not success:
                self._running = False
                self._timeout_id = None
                return False
            self._steps_executed += 1
            
            if DEBUG_LOOP:
                pass
        
        # All steps in batch completed, GUI will update before next callback
        return True

    def stop(self):
        """Stop the continuous simulation.
        
        This requests the simulation to stop. The actual stop will occur
        after the current step completes.
        
        IMPORTANT: This clears enablement states so that when Run is pressed
        again, transitions start fresh with enablement time = current time.
        """
        if not self._running:
            return
        self._stop_requested = True
        for state in self.transition_states.values():
            state.enablement_time = None
            state.scheduled_time = None
        for behavior in self.behavior_cache.values():
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()

    def reset(self):
        """Reset the simulation to initial marking.
        
        This stops any running simulation and resets all places to their
        initial marking values.
        """
        if self._running:
            self.stop()
            if self._timeout_id is not None and GLIB_AVAILABLE:
                GLib.source_remove(self._timeout_id)
                self._timeout_id = None
                self._running = False
        self.time = 0.0
        if self.data_collector is not None:
            self.data_collector.clear()
        self.transition_states.clear()
        for behavior in self.behavior_cache.values():
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()
        for place in self.model.places:
            if hasattr(place, 'initial_marking'):
                place.tokens = place.initial_marking
            else:
                place.tokens = 0
        self._notify_step_listeners()

    def is_running(self) -> bool:
        """Check if simulation is currently running.
        
        Returns:
            bool: True if simulation is running, False otherwise
        """
        return self._running

    def get_state(self) -> Dict[str, Any]:
        """Get current simulation state information.
        
        Returns:
            dict: State information including time, running status, etc.
        """
        return {'time': self.time, 'running': self._running, 'enabled_transitions': len(self._find_enabled_transitions())}