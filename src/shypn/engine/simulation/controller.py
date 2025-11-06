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
        """Get arcs as dictionary keyed by ID.
        
        WARNING: Arc IDs may not be unique in models (especially imported ones).
        Using ID as dict key can cause arcs to be lost. Behaviors should iterate
        over arcs directly, not use this dict for lookup.
        
        Returns a dict for API compatibility, but keyed by object id() to ensure uniqueness.
        """
        if self._arcs_dict is None:
            # Use Python object ID as key to avoid duplicate arc ID issues
            # This ensures all arcs are accessible even if they have duplicate IDs
            self._arcs_dict = {id(a): a for a in self.canvas_manager.arcs}
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
    
    Implements StateProvider interface for state detection system.
    
    Attributes:
        model: ModelCanvasManager instance (has places, transitions, arcs lists)
        time: Current simulation time
        settings: SimulationSettings instance for timing configuration
        step_listeners: List of callbacks to notify on each step
        state_detector: SimulationStateDetector for context-aware state queries
        buffered_settings: BufferedSimulationSettings for atomic parameter updates
        interaction_guard: InteractionGuard for permission-based UI control
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
        
        # === NEW: Mode elimination architecture ===
        # State detection replaces explicit mode checks
        from shypn.engine.simulation.state import SimulationStateDetector
        self.state_detector = SimulationStateDetector(self)
        
        # Buffered settings for atomic parameter updates
        from shypn.engine.simulation.buffered import BufferedSimulationSettings
        self.buffered_settings = BufferedSimulationSettings(self.settings)
        
        # Interaction guard for permission-based UI control
        from shypn.ui.interaction import InteractionGuard
        self.interaction_guard = InteractionGuard(self.state_detector)
        
        # Register to observe model changes (for arc transformations, deletions, etc.)
        if hasattr(model, 'register_observer'):
            model.register_observer(self._on_model_changed)

    def _on_model_changed(self, event_type: str, obj, old_value=None, new_value=None):
        """Handle model change notifications.
        
        Responds to model structure changes to keep simulation state consistent:
        - Deleted transitions: Remove from behavior cache and state tracking
        - Transformed arcs: Invalidate behaviors for affected transitions
        - Created/deleted arcs: Invalidate model adapter caches
        
        Args:
            event_type: 'created' | 'deleted' | 'modified' | 'transformed'
            obj: The affected object (Place, Transition, or Arc)
            old_value: Previous value (for transformed events)
            new_value: New value (for transformed events)
        """
        from shypn.netobjs.transition import Transition
        from shypn.netobjs.arc import Arc
        
        if event_type == 'deleted':
            # If a transition was deleted, remove it from our caches
            if isinstance(obj, Transition):
                if obj.id in self.behavior_cache:
                    del self.behavior_cache[obj.id]
                if obj.id in self.transition_states:
                    del self.transition_states[obj.id]
            
            # If an arc was deleted, invalidate model adapter caches
            if isinstance(obj, Arc):
                self.model_adapter.invalidate_caches()
        
        elif event_type == 'transformed':
            # If an arc was transformed, rebuild behaviors for affected transitions
            if isinstance(obj, Arc):
                # Invalidate model adapter caches (arc dicts changed)
                self.model_adapter.invalidate_caches()
                
                # Invalidate behavior cache for source and target transitions
                # (they need to rebuild their input/output arc lists)
                from shypn.netobjs.transition import Transition
                if isinstance(obj.source, Transition):
                    if obj.source.id in self.behavior_cache:
                        del self.behavior_cache[obj.source.id]
                if isinstance(obj.target, Transition):
                    if obj.target.id in self.behavior_cache:
                        del self.behavior_cache[obj.target.id]
                
                pass  # Behaviors rebuilt for affected transitions
        
        elif event_type == 'created':
            # New object created (place, transition, or arc)
            # Invalidate model adapter caches to include the new object
            from shypn.netobjs.place import Place
            if isinstance(obj, (Place, Transition, Arc)):
                self.model_adapter.invalidate_caches()
            
            # If a new transition was created, initialize its state and enablement
            if isinstance(obj, Transition):
                if obj.id not in self.transition_states:
                    self.transition_states[obj.id] = TransitionState()
                
                # Immediately update enablement for the new transition
                # This ensures source transitions are immediately ready to fire
                behavior = self._get_behavior(obj)
                is_source = getattr(obj, 'is_source', False)
                
                if is_source:
                    # Source transitions are always enabled
                    state = self.transition_states[obj.id]
                    state.enablement_time = self.time
                    if hasattr(behavior, 'set_enablement_time'):
                        behavior.set_enablement_time(self.time)
                else:
                    # Check if transition is structurally enabled (has enough input tokens)
                    input_arcs = behavior.get_input_arcs()
                    locally_enabled = True
                    for arc in input_arcs:
                        source_place = behavior._get_place(arc.source_id)
                        if source_place is None or source_place.tokens < arc.weight:
                            locally_enabled = False
                            break
                    
                    if locally_enabled:
                        state = self.transition_states[obj.id]
                        state.enablement_time = self.time
                        if hasattr(behavior, 'set_enablement_time'):
                            behavior.set_enablement_time(self.time)

    def _get_behavior(self, transition):
        """Get or create behavior instance for a transition.
        
        Uses factory pattern with caching for efficiency. Behavior instances
        are reused across simulation steps based on transition ID.
        
        CRITICAL: Validates cache against current transition_type to handle
        dynamic type changes during simulation. If type changes, invalidates
        and recreates the behavior instance.
        
        Cache invalidation strategy:
        - Type mismatch: Invalidates and recreates behavior (handles type changes)
        - reset(): Clears entire cache (prevents stale state across model reloads)
        - _on_model_changed: Removes specific transition behaviors (handles deletions)
        
        Args:
            transition: Transition object with transition_type property
            
        Returns:
            TransitionBehavior: Behavior instance for this transition type
        """
        if transition.id in self.behavior_cache:
            cached_behavior = self.behavior_cache[transition.id]
            cached_type = cached_behavior.get_type_name()
            current_type = getattr(transition, 'transition_type', 'continuous')
            type_name_map = {'Immediate': 'immediate', 'Timed (TPN)': 'timed', 'Stochastic (FSPN)': 'stochastic', 'Continuous (SHPN)': 'continuous'}
            cached_type_normalized = type_name_map.get(cached_type, cached_type.lower())
            if cached_type_normalized != current_type:
                if hasattr(cached_behavior, 'clear_enablement'):
                    cached_behavior.clear_enablement()
                del self.behavior_cache[transition.id]
                if transition.id in self.transition_states:
                    del self.transition_states[transition.id]
        if transition.id not in self.behavior_cache:
            # Create behavior instance
            # IMPORTANT: This method ONLY creates behaviors, it does NOT initialize
            # their enablement state. Initialization is handled EXCLUSIVELY by 
            # _update_enablement_states() to ensure consistent behavior for both
            # manually created and imported/loaded models.
            #
            # This eliminates the dual initialization problem where:
            # - _get_behavior() would initialize during type switch
            # - _update_enablement_states() would also initialize
            # - This caused double-sampling in stochastic transitions
            # - Created timing race conditions
            #
            # Now: Single responsibility = creation only, no initialization
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
            
            # Special handling for source transitions (no input places)
            is_source = getattr(transition, 'is_source', False)
            if is_source:
                # Source transitions are always structurally enabled
                state = self._get_or_create_state(transition)
                if state.enablement_time is None:
                    state.enablement_time = self.time
                    if hasattr(behavior, 'set_enablement_time'):
                        behavior.set_enablement_time(self.time)
                # Source transitions stay enabled continuously
                continue
            
            input_arcs = behavior.get_input_arcs()
            locally_enabled = True
            for arc in input_arcs:
                # Check ALL arc types for enablement (normal, test, inhibitor)
                # Test arcs check presence but don't consume (catalysts)
                # Inhibitor arcs check surplus and do consume (cooperation)
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
                            # Check ALL arc types (normal, test, inhibitor) for token availability
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
                                # Skip test arcs - they check enablement but don't consume tokens
                                if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
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
        
        continuous_active = 0
        for transition, behavior, input_arcs, output_arcs in continuous_to_integrate:
            success, details = behavior.integrate_step(dt=time_step, input_arcs=input_arcs, output_arcs=output_arcs)
            if success:
                continuous_active += 1
                if self.data_collector is not None:
                    self.data_collector.on_transition_fired(transition, self.time, details)
        
        # Advance time BEFORE checking discrete transitions
        # This ensures timed transitions are evaluated at the correct time
        self.time += time_step
        
        # Now check discrete transitions at the NEW time
        # This allows timed transitions to fire when entering their window mid-step
        self._update_enablement_states()
        
        # Handle timed and stochastic transitions with PRIORITY RULE:
        # Timed (deterministic) has PRIORITY over Stochastic (probabilistic)
        # Only fire stochastic if NO timed transitions can fire
        discrete_fired = False
        
        # Phase 2a: Timed transitions (DETERMINISTIC - PRIORITY)
        timed_transitions = [t for t in self.model.transitions if t.transition_type == 'timed']
        enabled_timed = [t for t in timed_transitions if self._is_transition_enabled(t)]
        
        if enabled_timed:
            # Select and fire one timed transition (may have conflicts among timed)
            transition = self._select_transition(enabled_timed)
            self._fire_transition(transition)
            discrete_fired = True
            self._update_enablement_states()  # Update after firing
        
        # Phase 2b: Stochastic transitions (PROBABILISTIC - LOWER PRIORITY)
        # Only execute if NO timed transitions fired (timed has priority)
        elif not discrete_fired:  # Changed: only if no timed fired
            stochastic_transitions = [t for t in self.model.transitions if t.transition_type == 'stochastic']
            enabled_stochastic = [t for t in stochastic_transitions if self._is_transition_enabled(t)]
            if enabled_stochastic:
                # Select and fire one stochastic transition (may have conflicts among stochastic)
                transition = self._select_transition(enabled_stochastic)
                self._fire_transition(transition)
                discrete_fired = True
        
        self._notify_step_listeners()
        
        # Check if simulation is complete (duration reached)
        if self.is_simulation_complete():
            return False  # Simulation complete
        
        if immediate_fired_total > 0 or window_crossing_fired > 0 or discrete_fired or continuous_active > 0:
            return True
        
        # Check for waiting discrete transitions
        stochastic_transitions = [t for t in self.model.transitions if t.transition_type == 'stochastic']
        all_discrete = timed_transitions + stochastic_transitions
        waiting_count = 0
        ready_count = 0
        for transition in all_discrete:
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

    # ============================================================================
    # Phase 1: Locality Independence Detection (Place-Sharing Analysis)
    # ============================================================================
    
    def _get_all_places_for_transition(self, transition) -> set:
        """Get all places (input and output) involved in a transition's locality.
        
        This extracts the complete neighborhood of a transition:
        - Input places: •t (places that provide tokens TO transition)
        - Output places: t• (places that receive tokens FROM transition)
        
        **Locality patterns recognized:**
        - Normal: Pn → T → Pm  (locality = •t ∪ t•, both inputs and outputs)
        - Source: T → Pm       (locality = t•, only outputs, no inputs)
        - Sink: Pn → T         (locality = •t, only inputs, no outputs)
        - Multiple-source: T1 → P ← T2 (shared places allowed)
        
        Args:
            transition: Transition object to analyze
            
        Returns:
            Set of place IDs involved in this locality
            
        Examples:
            Normal: P1 → T1 → P2  →  {P1.id, P2.id}
            Source: T1 → P2       →  {P2.id} (only output)
            Sink:   P1 → T1       →  {P1.id} (only input)
        """
        behavior = self._get_behavior(transition)
        place_ids = set()
        
        # Get input places (•t)
        for arc in behavior.get_input_arcs():
            if hasattr(arc, 'source_id'):
                place_ids.add(arc.source_id)
            elif hasattr(arc, 'source') and hasattr(arc.source, 'id'):
                place_ids.add(arc.source.id)
        
        # Get output places (t•)
        for arc in behavior.get_output_arcs():
            if hasattr(arc, 'target_id'):
                place_ids.add(arc.target_id)
            elif hasattr(arc, 'target') and hasattr(arc.target, 'id'):
                place_ids.add(arc.target.id)
        
        return place_ids
    
    def _are_independent(self, t1, t2) -> bool:
        """Check if two transitions are independent (don't share places).
        
        Two transitions are independent if their localities don't overlap:
        - They don't share input places (no conflict for tokens)
        - They don't share output places (no conflict for production)
        
        Mathematical definition:
            t1 ⊥ t2  ⟺  (•t1 ∪ t1•) ∩ (•t2 ∪ t2•) = ∅
        
        **Source/Sink Independence:**
        - Two source transitions: Independent unless they share output places
          Example: T1(source)→P1, T2(source)→P2  →  Independent
                   T1(source)→P1, T2(source)→P1  →  Dependent (same output)
        
        - Two sink transitions: Independent unless they share input places
          Example: P1→T1(sink), P2→T2(sink)  →  Independent
                   P1→T1(sink), P1→T2(sink)  →  Dependent (same input)
        
        - Source and sink: Always independent (no place overlap)
          Example: T1(source)→P1, P2→T2(sink)  →  Independent
        
        - Source/sink with normal: Independent unless they share places
          Example: T1(source)→P1, P1→T2→P2  →  Dependent (share P1)
        
        Independent transitions CAN fire in parallel (maximal step semantics).
        Dependent transitions MUST fire sequentially (conflict resolution needed).
        
        Args:
            t1: First transition
            t2: Second transition
            
        Returns:
            True if transitions don't share ANY places, False otherwise
            
        Examples:
            Normal: P1→T1→P2, P3→T2→P4  →  Independent (no shared places)
            Normal: P1→T1→P2, P1→T2→P3  →  Dependent (share P1)
            Source: T1→P1, T2→P2        →  Independent (different outputs)
            Sink:   P1→T1, P2→T2        →  Independent (different inputs)
        """
        # Get all places for each transition (respects source/sink structure)
        places_t1 = self._get_all_places_for_transition(t1)
        places_t2 = self._get_all_places_for_transition(t2)
        
        # Check for intersection (shared places)
        shared_places = places_t1 & places_t2
        
        # Independent if NO shared places
        return len(shared_places) == 0
    
    def _compute_conflict_sets(self, transitions: List) -> Dict[str, set]:
        """Build conflict graph showing which transitions share places.
        
        A conflict graph represents dependencies between transitions:
        - Nodes: Transitions
        - Edges: Conflicts (transitions that share at least one place)
        
        Two transitions conflict if they share ANY place (input or output).
        Conflicting transitions CANNOT fire simultaneously.
        
        This is the foundation for computing maximal concurrent sets
        (Phase 2 implementation).
        
        Args:
            transitions: List of Transition objects to analyze
            
        Returns:
            Dictionary mapping transition ID to set of conflicting transition IDs
            
        Example:
            Network:
                P1 → T1 → P2
                P1 → T2 → P3  (shares P1 with T1)
                P4 → T3 → P5  (independent)
            
            Result:
                {
                    'T1': {'T2'},      # T1 conflicts with T2
                    'T2': {'T1'},      # T2 conflicts with T1
                    'T3': set()        # T3 has no conflicts
                }
        """
        # Initialize empty conflict sets
        conflict_sets = {t.id: set() for t in transitions}
        
        # Compare each pair of transitions
        for i, t1 in enumerate(transitions):
            for t2 in transitions[i+1:]:
                # Check if they share places
                if not self._are_independent(t1, t2):
                    # They share places → Conflict!
                    conflict_sets[t1.id].add(t2.id)
                    conflict_sets[t2.id].add(t1.id)
        
        return conflict_sets
    
    def _get_independent_transitions(self, transitions: List) -> List[List]:
        """Group transitions into independent sets (no place sharing within groups).
        
        This partitions transitions into groups where transitions within
        each group are mutually independent (pairwise non-conflicting).
        
        This is useful for visualizing/debugging locality independence.
        
        Args:
            transitions: List of Transition objects
            
        Returns:
            List of lists, where each inner list contains independent transitions
            
        Example:
            Network:
                P1 → T1 → P2
                P1 → T2 → P3  (conflicts with T1)
                P4 → T3 → P5  (independent)
                P4 → T4 → P6  (conflicts with T3)
            
            Result:
                [
                    [T1, T3],  # Group 1: T1 and T3 are independent
                    [T2, T4]   # Group 2: T2 and T4 are independent
                ]
        """
        if not transitions:
            return []
        
        conflict_sets = self._compute_conflict_sets(transitions)
        independent_groups = []
        remaining = set(t.id for t in transitions)
        transitions_by_id = {t.id: t for t in transitions}
        
        while remaining:
            # Start new group with first remaining transition
            current_id = next(iter(remaining))
            current_group = [transitions_by_id[current_id]]
            remaining.remove(current_id)
            
            # Try to add non-conflicting transitions to this group
            to_check = list(remaining)
            for tid in to_check:
                # Check if this transition is independent of ALL in current group
                independent_of_all = True
                for group_transition in current_group:
                    if tid in conflict_sets[group_transition.id]:
                        independent_of_all = False
                        break
                
                if independent_of_all:
                    current_group.append(transitions_by_id[tid])
                    remaining.remove(tid)
            
            independent_groups.append(current_group)
        
        return independent_groups

    # ==================================================================================
    # PHASE 2: MAXIMAL CONCURRENT SET COMPUTATION
    # ==================================================================================
    # These methods find maximal sets of transitions that can fire together.
    # A maximal concurrent set is a set of independent transitions that cannot
    # be extended without introducing conflicts.
    #
    # Algorithm: Hybrid approach using multiple greedy strategies to find diverse
    # maximal sets. This provides good coverage without exponential complexity.
    #
    # Dependencies: Uses Phase 1 methods (_compute_conflict_sets, _are_independent)
    # ==================================================================================

    def _find_maximal_concurrent_sets(self, enabled_transitions: List, max_sets: int = 5) -> List[List]:
        """
        Find maximal concurrent sets of enabled transitions.
        
        A maximal concurrent set is a set of transitions where:
        1. All transitions are mutually independent (don't share places)
        2. Cannot add any more transitions without creating conflicts
        
        Uses hybrid approach with multiple greedy strategies to find diverse
        maximal sets without exponential complexity.
        
        Args:
            enabled_transitions: List of enabled Transition objects
            max_sets: Maximum number of maximal sets to return (default: 5)
            
        Returns:
            List of lists, each inner list is a maximal concurrent set of
            Transition objects
            
        Example:
            enabled = [T1, T2, T3, T4]
            conflicts: T1↔T2 (share P1), T3↔T4 (share P5)
            
            Result: [[T1, T3], [T2, T4], [T1, T4], [T2, T3]]
            Each is maximal (cannot add more without conflict)
            
        Complexity:
            Time: O(k × n²) where k = max_sets, n = |enabled|
            Space: O(n²) for conflict sets
        """
        if not enabled_transitions:
            return []
        
        if len(enabled_transitions) == 1:
            return [[enabled_transitions[0]]]
        
        # Build conflict graph using Phase 1
        conflict_sets = self._compute_conflict_sets(enabled_transitions)
        
        maximal_sets = []
        seen_sets = set()  # Track unique sets using frozenset of IDs
        
        # Strategy 1: Standard greedy from natural order
        maximal_set = self._greedy_maximal_set(
            enabled_transitions, conflict_sets, start_index=0
        )
        if maximal_set:
            set_key = frozenset(t.id for t in maximal_set)
            seen_sets.add(set_key)
            maximal_sets.append(maximal_set)
        
        # Strategy 2: Try different starting points (rotation)
        # This explores different orderings to find diverse maximal sets
        for start_idx in range(1, min(len(enabled_transitions), max_sets)):
            maximal_set = self._greedy_maximal_set(
                enabled_transitions, conflict_sets, start_index=start_idx
            )
            if maximal_set:
                set_key = frozenset(t.id for t in maximal_set)
                if set_key not in seen_sets:
                    seen_sets.add(set_key)
                    maximal_sets.append(maximal_set)
                    if len(maximal_sets) >= max_sets:
                        break
        
        # Strategy 3: Prioritize transitions with MOST conflicts
        # Handles constrained transitions first
        if len(maximal_sets) < max_sets:
            ordered = self._sort_by_conflict_degree(
                enabled_transitions, conflict_sets, ascending=False
            )
            maximal_set = self._greedy_maximal_set(
                ordered, conflict_sets, start_index=0
            )
            if maximal_set:
                set_key = frozenset(t.id for t in maximal_set)
                if set_key not in seen_sets:
                    seen_sets.add(set_key)
                    maximal_sets.append(maximal_set)
        
        # Strategy 4: Prioritize transitions with LEAST conflicts
        # Maximizes set size by starting with least constrained
        if len(maximal_sets) < max_sets:
            ordered = self._sort_by_conflict_degree(
                enabled_transitions, conflict_sets, ascending=True
            )
            maximal_set = self._greedy_maximal_set(
                ordered, conflict_sets, start_index=0
            )
            if maximal_set:
                set_key = frozenset(t.id for t in maximal_set)
                if set_key not in seen_sets:
                    seen_sets.add(set_key)
                    maximal_sets.append(maximal_set)
        
        return maximal_sets

    def _greedy_maximal_set(self, transitions: List, conflict_sets: dict, 
                           start_index: int = 0) -> List:
        """
        Build one maximal concurrent set using greedy algorithm.
        
        Starting from a given position, greedily adds transitions that are
        independent of all transitions already in the set.
        
        Args:
            transitions: List of Transition objects to consider
            conflict_sets: Dict mapping transition IDs to sets of conflicting IDs
            start_index: Index to start greedy selection (for rotation)
            
        Returns:
            List of Transition objects forming a maximal concurrent set
            
        Algorithm:
            1. Start with transition at start_index
            2. For each remaining transition:
                - Check if independent of ALL in current set
                - If yes, add to set
            3. Result is maximal (cannot extend further)
            
        Complexity:
            Time: O(n²) where n = |transitions|
            Space: O(n)
        """
        if not transitions:
            return []
        
        # Rotate list to start from different position
        ordered = transitions[start_index:] + transitions[:start_index]
        
        # Initialize with first transition
        maximal_set = [ordered[0]]
        maximal_set_ids = {ordered[0].id}
        
        # Try to add each remaining transition
        for t in ordered[1:]:
            # Check if t is independent of ALL transitions in current set
            can_add = True
            for tid in maximal_set_ids:
                if t.id in conflict_sets[tid]:
                    # Conflict found - cannot add
                    can_add = False
                    break
            
            if can_add:
                maximal_set.append(t)
                maximal_set_ids.add(t.id)
        
        return maximal_set

    def _sort_by_conflict_degree(self, transitions: List, conflict_sets: dict,
                                 ascending: bool = True) -> List:
        """
        Sort transitions by number of conflicts (degree in conflict graph).
        
        Transitions with more conflicts are more "constrained" and may need
        priority handling. Transitions with fewer conflicts are more "flexible".
        
        Args:
            transitions: List of Transition objects
            conflict_sets: Dict mapping transition IDs to sets of conflicting IDs
            ascending: If True, sort by least conflicts first (flexible first)
                      If False, sort by most conflicts first (constrained first)
            
        Returns:
            Sorted list of Transition objects
            
        Example:
            T1 conflicts with 3 transitions
            T2 conflicts with 1 transition
            T3 conflicts with 2 transitions
            
            ascending=True:  [T2, T3, T1] (least conflicts first)
            ascending=False: [T1, T3, T2] (most conflicts first)
        """
        def conflict_degree(t):
            return len(conflict_sets.get(t.id, set()))
        
        return sorted(transitions, key=conflict_degree, reverse=not ascending)

    def _is_concurrent_set_maximal(self, concurrent_set: List, 
                                   all_enabled: List, conflict_sets: dict) -> bool:
        """
        Check if a concurrent set is maximal (cannot be extended).
        
        A set is maximal if there is no transition outside the set that is
        independent of all transitions in the set.
        
        Args:
            concurrent_set: List of Transition objects in the set to check
            all_enabled: List of all enabled Transition objects
            conflict_sets: Dict mapping transition IDs to sets of conflicting IDs
            
        Returns:
            True if the set is maximal, False if it can be extended
            
        Example:
            concurrent_set = [T1, T3]
            all_enabled = [T1, T2, T3, T4]
            
            If T2 conflicts with T1 AND T4 conflicts with T3:
                → Cannot add T2 or T4 → Maximal ✅
            
            If T4 is independent of both T1 and T3:
                → Can add T4 → Not maximal ❌
        """
        set_ids = {t.id for t in concurrent_set}
        
        # Try to add each transition not in the set
        for t in all_enabled:
            if t.id in set_ids:
                continue  # Already in set, skip
            
            # Check if t is independent of ALL transitions in the set
            can_add = True
            for tid in set_ids:
                if t.id in conflict_sets[tid]:
                    # Conflict found - cannot add this transition
                    can_add = False
                    break
            
            if can_add:
                # Found a transition we can add - not maximal!
                return False
        
        # Cannot add any transition - is maximal!
        return True

    # ========================================================================
    # PHASE 3: MAXIMAL STEP EXECUTION
    # ========================================================================
    # Atomic execution of maximal concurrent sets with rollback guarantees
    # Methods: select, validate, snapshot, restore, execute
    # ========================================================================

    def _select_maximal_set(self, maximal_sets: List[List], 
                           strategy: str = 'largest') -> List:
        """
        Select which maximal concurrent set to execute.
        
        Args:
            maximal_sets: List of maximal concurrent sets from Phase 2
            strategy: Selection strategy
                - 'largest': Fire most transitions (maximize parallelism)
                - 'priority': Fire highest priority transitions
                - 'random': Random selection (for exploration)
                - 'first': First set found (deterministic)
                
        Returns:
            Selected maximal concurrent set (List of Transition objects)
            Empty list if no sets provided
            
        Example:
            maximal_sets = [[T1, T3], [T2, T3], [T2]]
            
            strategy='largest': → [T1, T3] or [T2, T3] (both size 2)
            strategy='priority': → Based on sum of priorities
            strategy='random': → Any set randomly
            strategy='first': → [T1, T3] (first in list)
        """
        if not maximal_sets:
            return []
        
        if strategy == 'largest':
            # Maximize parallelism - choose set with most transitions
            return max(maximal_sets, key=len)
        
        elif strategy == 'priority':
            # Maximize sum of priorities
            def total_priority(tset):
                return sum(getattr(t, 'priority', 0) for t in tset)
            return max(maximal_sets, key=total_priority)
        
        elif strategy == 'random':
            # Random for exploration
            return random.choice(maximal_sets)
        
        elif strategy == 'first':
            # Deterministic (natural order from Phase 2)
            return maximal_sets[0]
        
        else:
            # Unknown strategy - fall back to first
            return maximal_sets[0]

    def _validate_all_can_fire(self, transition_set: List) -> bool:
        """
        Check if all transitions in set are currently enabled.
        
        Pre-flight validation before snapshot to avoid rollback overhead.
        
        Args:
            transition_set: List of Transition objects to validate
            
        Returns:
            True if all transitions can fire, False otherwise
            
        Checks:
            1. All input places have sufficient tokens
            2. All guards evaluate to True (if present)
            3. All arc thresholds are met (if applicable)
            
        Example:
            T1: P1(2) --[weight=1]--> T1 ---> P2
            T2: P3(0) --[weight=1]--> T2 ---> P4
            
            validate([T1, T2]) → False (P3 has 0 < 1 tokens)
            validate([T1]) → True (P1 has 2 >= 1 tokens)
        """
        for transition in transition_set:
            # Find input arcs for this transition
            for arc in self.model.arcs:
                if arc.target == transition:
                    # This is an input arc (place → transition)
                    place = arc.source
                    
                    # Get weight/threshold
                    tokens_needed = getattr(arc, 'weight', 1)
                    if hasattr(arc, 'threshold') and arc.threshold is not None:
                        tokens_needed = arc.threshold
                    
                    # Check sufficient tokens
                    if place.tokens < tokens_needed:
                        return False  # Not enough tokens
            
            # Check guard condition (if any)
            if hasattr(transition, 'guard') and transition.guard is not None:
                try:
                    if not transition.guard.evaluate():
                        return False  # Guard prevents firing
                except Exception:
                    return False  # Guard evaluation failed
        
        return True  # All transitions can fire

    def _snapshot_marking(self) -> dict:
        """
        Create snapshot of current marking for rollback.
        
        Returns:
            Dictionary mapping place_id → token_count
            
        Used for atomic execution: If any transition fails, we can
        restore to this snapshot.
        
        Example:
            Before: {P1: 2, P2: 0, P3: 1}
            Snapshot: {'P1': 2, 'P2': 0, 'P3': 1}
            
            (Used later for rollback if execution fails)
        """
        # Handle both dict and list for places
        places = self.model.places if hasattr(self.model, 'places') else []
        if isinstance(places, dict):
            return {place.id: place.tokens for place in places.values()}
        else:
            return {place.id: place.tokens for place in places}

    def _restore_marking(self, snapshot: dict) -> None:
        """
        Restore marking from snapshot (rollback).
        
        Args:
            snapshot: Dictionary from _snapshot_marking()
            
        Restores all place token counts to snapshotted values.
        Used when maximal step execution fails partway through.
        
        Example:
            snapshot = {'P1': 2, 'P2': 0, 'P3': 1}
            
            After partial execution: {P1: 1, P2: 1, P3: 1}
            After restore: {P1: 2, P2: 0, P3: 1}  # Reverted ✓
        """
        # Handle both dict and list for places
        places = self.model.places if hasattr(self.model, 'places') else []
        if isinstance(places, dict):
            places = places.values()
        
        for place in places:
            if place.id in snapshot:
                place.tokens = snapshot[place.id]

    def _execute_maximal_step(self, transition_set: List) -> tuple:
        """
        Execute all transitions in set atomically with rollback guarantee.
        
        Uses three-phase commit protocol:
        1. VALIDATE: Check all transitions can fire
        2. PREPARE: Create snapshot for rollback
        3. COMMIT: Execute all transitions (rollback on failure)
        
        Args:
            transition_set: List of Transition objects to fire atomically
            
        Returns:
            Tuple of (success: bool, fired_transitions: List, error: str)
            - success: True if all transitions fired, False if any failed
            - fired_transitions: List of transitions that fired (empty on failure)
            - error: Error message (empty on success)
            
        Guarantees:
            - Atomicity: All fire or none fire
            - Consistency: Net state remains valid
            - Isolation: No partial states visible
            
        Example:
            Success case:
                execute([T1, T3]) → (True, [T1, T3], "")
                
            Failure case:
                execute([T1, T3]) → (False, [], "T3 failed: insufficient tokens")
                (Net state rolled back to before attempt)
        """
        if not transition_set:
            return (False, [], "Empty transition set")
        
        # PHASE 1: VALIDATE
        if not self._validate_all_can_fire(transition_set):
            return (False, [], "Pre-condition failed: Not all transitions enabled")
        
        # PHASE 2: PREPARE (snapshot for rollback)
        snapshot = self._snapshot_marking()
        
        try:
            # PHASE 3: COMMIT (execute atomically)
            fired = []
            
            # Sort by priority for deterministic execution order
            sorted_transitions = sorted(
                transition_set, 
                key=lambda t: (getattr(t, 'priority', 0), t.id), 
                reverse=True
            )
            
            for transition in sorted_transitions:
                # Remove input tokens
                for arc in self.model.arcs:
                    if arc.target == transition:
                        # Input arc (place → transition)
                        place = arc.source
                        
                        # Get weight/threshold
                        tokens_needed = getattr(arc, 'weight', 1)
                        if hasattr(arc, 'threshold') and arc.threshold is not None:
                            tokens_needed = arc.threshold
                        
                        # Safety check (should not fail after validation)
                        if place.tokens < tokens_needed:
                            raise RuntimeError(
                                f"{transition.id} cannot fire: {place.id} has "
                                f"{place.tokens} < {tokens_needed} tokens"
                            )
                        
                        place.tokens -= tokens_needed
                
                # Execute transition behavior (if any)
                if hasattr(transition, 'behavior') and transition.behavior is not None:
                    try:
                        transition.behavior.execute()
                    except Exception as e:
                        raise RuntimeError(
                            f"{transition.id} behavior failed: {e}"
                        )
                
                # Add output tokens
                for arc in self.model.arcs:
                    if arc.source == transition:
                        # Output arc (transition → place)
                        place = arc.target
                        tokens_produced = getattr(arc, 'weight', 1)
                        place.tokens += tokens_produced
                
                fired.append(transition)
            
            # SUCCESS: All transitions fired
            return (True, fired, "")
            
        except Exception as e:
            # ROLLBACK: Restore snapshot
            self._restore_marking(snapshot)
            return (False, [], f"Execution failed: {e}, rolled back")

    def _select_transition(self, enabled_transitions: List) -> Any:
        """Select one transition from enabled set based on conflict resolution policy.
        
        Uses per-transition firing_policy attribute to determine selection strategy.
        Falls back to global conflict_policy if firing_policy not set.
        
        Args:
            enabled_transitions: List of enabled Transition objects
            
        Returns:
            Selected Transition object to fire
        """
        if len(enabled_transitions) == 1:
            return enabled_transitions[0]
        
        # Use first transition's firing policy (assume homogeneous set)
        # In hybrid cases, 'priority' policy takes precedence
        policy = getattr(enabled_transitions[0], 'firing_policy', None)
        
        # If no per-transition policy, use global conflict policy
        if not policy:
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
        
        # Per-transition firing policies
        if policy == 'earliest':
            # Fire transition that was enabled earliest (smallest enablement time)
            return min(enabled_transitions, 
                      key=lambda t: self.transition_states[t.id].enablement_time if t.id in self.transition_states and self.transition_states[t.id].enablement_time is not None else float('inf'))
        
        elif policy == 'latest':
            # Fire transition that was enabled most recently (largest enablement time)
            return max(enabled_transitions,
                      key=lambda t: self.transition_states[t.id].enablement_time if t.id in self.transition_states and self.transition_states[t.id].enablement_time is not None else 0)
        
        elif policy == 'priority':
            # Fire highest priority transition
            return max(enabled_transitions, key=lambda t: getattr(t, 'priority', 0))
        
        elif policy == 'race':
            # Mass action kinetics - exponential race condition
            # Sample exponential delay for each, select minimum
            import numpy as np
            min_delay = float('inf')
            selected = None
            for t in enabled_transitions:
                # Use transition rate if available, otherwise default to 1.0
                rate = float(getattr(t, 'rate', 1.0)) if hasattr(t, 'rate') and t.rate else 1.0
                if rate > 0:
                    delay = np.random.exponential(1.0 / rate)
                    if delay < min_delay:
                        min_delay = delay
                        selected = t
            return selected if selected else random.choice(enabled_transitions)
        
        elif policy == 'age':
            # FIFO - transition enabled longest fires first
            return min(enabled_transitions,
                      key=lambda t: self.transition_states[t.id].enablement_time if t.id in self.transition_states and self.transition_states[t.id].enablement_time is not None else float('inf'))
        
        elif policy == 'random':
            # Uniform random selection
            return random.choice(enabled_transitions)
        
        elif policy == 'preemptive-priority':
            # For now, treat same as priority (full preemption requires interrupt mechanism)
            # TODO: Implement preemption of running lower-priority transitions
            return max(enabled_transitions, key=lambda t: getattr(t, 'priority', 0))
        
        else:
            # Unknown policy - default to random
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
        
        # Calculate optimal step batching for smooth animation with time scale
        # Target: Execute multiple steps per GUI update to maintain smooth visualization
        # For small time steps (e.g., 0.002s), batch many steps together
        # For large time steps (e.g., 1.0s), execute 1 step per GUI update
        # Time scale: Controls playback speed (1.0 = real-time, 60.0 = 60x faster)
        
        gui_interval_s = 0.1  # Fixed 100ms GUI update interval (real-world playback time)
        
        # Calculate how much MODEL time should pass per GUI update
        # time_scale = model_seconds / real_seconds
        # Example: time_scale=60.0 means 60 seconds of model time per 1 second of real time
        model_time_per_gui_update = gui_interval_s * self.settings.time_scale
        
        # Calculate how many simulation steps needed to cover that model time
        # Example: model_time=6.0s, time_step=1.0s → 6 steps per GUI update
        self._steps_per_callback = max(1, int(model_time_per_gui_update / time_step))
        
        # Safety cap: Prevent UI freeze on extreme time_scale values
        # Cap at 1000 steps per GUI update (allows up to ~10000x speedup with dt=0.001)
        if self._steps_per_callback > 1000:
            effective_max_scale = 1000 * time_step / gui_interval_s
            self._steps_per_callback = 1000
        else:
            self._steps_per_callback = min(self._steps_per_callback, 1000)
        
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
        initial marking values. Also clears the behavior cache to prevent
        stale state from persisting across model reloads.
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
        
        # Clear behavior cache to prevent stale state across model reloads
        # This fixes the issue where cached behaviors from a previous model
        # (with same transition IDs) persist and cause transitions not to fire
        for behavior in self.behavior_cache.values():
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()
        self.behavior_cache.clear()
        
        for place in self.model.places:
            if hasattr(place, 'initial_marking'):
                place.tokens = place.initial_marking
            else:
                place.tokens = 0
        # Schedule time-dependent transitions (timed/stochastic) after reset
        self._update_enablement_states()
        self._notify_step_listeners()
    
    def reset_for_new_model(self, new_model):
        """Reset controller for a completely new model (File→Open, Import, etc.).
        
        This is more comprehensive than reset() - it recreates all internal
        components with the new model reference, ensuring no stale state from
        the previous model persists.
        
        Called when:
        - Loading a file (File→Open)
        - Importing a pathway (KEGG, SBML)
        - Reusing a canvas tab for a new document
        
        This ensures:
        - Model adapter is recreated with new model reference
        - All caches are cleared (behaviors, states, transitions)
        - State detector gets fresh model reference
        - Interaction guard is reset
        - No cross-contamination between old and new models
        
        Args:
            new_model: The new ModelCanvasManager instance
        """
        # Stop any running simulation first
        if self._running:
            self.stop()
            if self._timeout_id is not None and GLIB_AVAILABLE:
                GLib.source_remove(self._timeout_id)
                self._timeout_id = None
                self._running = False
        
        # Update model reference
        self.model = new_model
        
        # Recreate model adapter with new model
        self.model_adapter = ModelAdapter(new_model, controller=self)
        
        # Clear all state and caches
        self.time = 0.0
        self.behavior_cache.clear()
        self.transition_states.clear()
        self._round_robin_index = 0
        
        # Reset data collector if exists
        if self.data_collector is not None:
            self.data_collector.clear()
        
        # State detector already has reference to self (controller)
        # so it will automatically use the new self.model reference
        # But we invalidate any cached state
        if hasattr(self.state_detector, '_cached_states'):
            self.state_detector._cached_states = {}
        
        # Interaction guard already has reference to state_detector
        # which has reference to self, so it will use new model automatically
        
        # Re-register observer for new model
        if hasattr(new_model, 'register_observer'):
            new_model.register_observer(self._on_model_changed)
        
        # CRITICAL: Restore initial marking for all places
        # This was missing and caused all loaded models to have zero tokens!
        for place in self.model.places:
            if hasattr(place, 'initial_marking'):
                place.tokens = place.initial_marking
            else:
                place.tokens = 0
        
        # CRITICAL: Initialize transition states after model reset
        # This populates self.transition_states with enablement tracking
        # Without this, transitions won't have state and simulation won't run
        self._update_enablement_states()
        
        # Show first 5 transition states
        for t_id in list(self.transition_states.keys())[:5]:
            print(f"[RESET_FOR_NEW_MODEL] transition_states[{t_id}] = {self.transition_states[t_id]}")
        
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
    
    # ========== StateProvider Interface (for state detection) ==========
    
    @property
    def running(self) -> bool:
        """Check if simulation is running (StateProvider interface property).
        
        Returns:
            bool: True if simulation is running, False otherwise
        """
        return self._running
    
    @property
    def duration(self) -> Optional[float]:
        """Get simulation duration (StateProvider interface property).
        
        Returns:
            float or None: Duration in seconds, or None if not set
        """
        return self.settings.get_duration_seconds()