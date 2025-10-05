"""
Simulation Controller for Petri Net Execution

Manages the execution of Petri net simulations, including:
- Single-step execution
- Continuous execution (run mode)
- Stop/pause functionality
- Reset to initial marking

Based on the legacy shypnpy simulation controller but adapted for
the new architecture.
"""

import random
from typing import Callable, List, Optional, Dict, Any

# GLib is optional - only needed for continuous run mode
try:
    from gi.repository import GLib
    GLIB_AVAILABLE = True
except ImportError:
    GLIB_AVAILABLE = False
    GLib = None

from shypn.engine import behavior_factory
from shypn.engine.simulation.conflict_policy import (
    ConflictResolutionPolicy,
    DEFAULT_POLICY,
    TYPE_PRIORITIES
)


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
        self.enablement_time = None  # When locally enabled
        self.scheduled_time = None   # For stochastic only


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
        self._controller = controller  # Reference to controller for time access
        
        # Create lazy-loaded dict caches
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
        step_listeners: List of callbacks to notify on each step
    """
    
    def __init__(self, model):
        """Initialize the simulation controller.
        
        Args:
            model: ModelCanvasManager instance (has places, transitions, arcs lists)
        """
        self.model = model
        self.time = 0.0
        self.model_adapter = ModelAdapter(model, controller=self)  # Pass self for time access
        self.step_listeners = []
        self._running = False
        self._stop_requested = False
        self._timeout_id = None
        
        # Behavior cache: maps transition id -> TransitionBehavior instance
        self.behavior_cache = {}
        
        # Transition state tracking: maps transition id -> TransitionState
        self.transition_states = {}
        
        # Conflict resolution policy
        self.conflict_policy = DEFAULT_POLICY
        self._round_robin_index = 0  # For ROUND_ROBIN policy
        
        # Optional data collector for analysis/plotting
        self.data_collector = None
    
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
        # Check if we have a cached behavior
        if transition.id in self.behavior_cache:
            cached_behavior = self.behavior_cache[transition.id]
            
            # CRITICAL: Check if transition type has changed
            # Compare current type with cached behavior's type
            cached_type = cached_behavior.get_type_name()
            current_type = getattr(transition, 'transition_type', 'immediate')
            
            # Map type names to string types for comparison
            type_name_map = {
                'Immediate': 'immediate',
                'Timed (TPN)': 'timed',
                'Stochastic (FSPN)': 'stochastic',
                'Continuous (SHPN)': 'continuous'
            }
            
            cached_type_normalized = type_name_map.get(cached_type, cached_type.lower())
            
            # If type changed, invalidate cache and recreate
            if cached_type_normalized != current_type:
                print(f"⚠️  [BEHAVIOR CHANGE] {transition.name} type changed: {cached_type_normalized} → {current_type}")
                print(f"   Invalidating cached behavior and creating new {current_type} behavior")
                
                # Clear old behavior's state
                if hasattr(cached_behavior, 'clear_enablement'):
                    cached_behavior.clear_enablement()
                
                # Remove from cache (will be recreated below)
                del self.behavior_cache[transition.id]
                
                # Clear transition state so it re-enables fresh
                if transition.id in self.transition_states:
                    del self.transition_states[transition.id]
        
        # Create new behavior if not in cache (or was just invalidated)
        if transition.id not in self.behavior_cache:
            # Create new behavior using factory (pass model adapter)
            behavior = behavior_factory.create_behavior(transition, self.model_adapter)
            self.behavior_cache[transition.id] = behavior
            
            print(f"✅ [BEHAVIOR CREATED] {transition.name}: {behavior.get_type_name()}")
        
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
        - If newly enabled: record current time as enablement_time
        - If still enabled: keep existing enablement_time
        - If disabled: clear enablement_time
        """
        for transition in self.model.transitions:
            behavior = self._get_behavior(transition)
            
            # Check LOCALITY enablement (structural - do input places have enough tokens?)
            input_arcs = behavior.get_input_arcs()
            locally_enabled = True
            
            for arc in input_arcs:
                # Skip inhibitor arcs for structural enablement check
                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                if kind != 'normal':
                    continue
                
                source_place = behavior._get_place(arc.source_id)
                if source_place is None or source_place.tokens < arc.weight:
                    locally_enabled = False
                    break
            
            state = self._get_or_create_state(transition)
            
            if locally_enabled:
                # Newly enabled: record time
                if state.enablement_time is None:
                    state.enablement_time = self.time
                    
                    # Debug: Show re-enablement
                    DEBUG_ENABLEMENT = True  # Set to True for debugging
                    if DEBUG_ENABLEMENT:
                        print(f"[Enablement] {transition.name} (type={transition.transition_type}) ENABLED at t={self.time:.3f}")
                    
                    # Notify behavior (for stochastic sampling and timed tracking)
                    if hasattr(behavior, 'set_enablement_time'):
                        behavior.set_enablement_time(self.time)
                        if DEBUG_ENABLEMENT and hasattr(behavior, 'get_stochastic_info'):
                            info = behavior.get_stochastic_info()
                            print(f"  → Stochastic: scheduled_fire={info.get('scheduled_fire_time'):.3f}, burst={info.get('sampled_burst')}")
                        elif DEBUG_ENABLEMENT and hasattr(behavior, 'get_timing_info'):
                            info = behavior.get_timing_info()
                            print(f"  → Timed: earliest={behavior.earliest}, latest={behavior.latest}")
            else:
                # Disabled: clear state
                if state.enablement_time is not None:
                    pass  # State cleared below
                
                state.enablement_time = None
                state.scheduled_time = None  # Clear stochastic schedule
                
                if hasattr(behavior, 'clear_enablement'):
                    behavior.clear_enablement()
    
    def set_conflict_policy(self, policy: ConflictResolutionPolicy):
        """Set the conflict resolution policy for transition selection.
        
        Args:
            policy: ConflictResolutionPolicy enum value
        """
        self.conflict_policy = policy
        self._round_robin_index = 0  # Reset round-robin counter
    
    def invalidate_behavior_cache(self, transition_id=None):
        """Invalidate behavior cache for a specific transition or all transitions.
        
        This forces behavior instances to be recreated on next access, useful
        when transition types are changed programmatically.
        
        Args:
            transition_id: ID of specific transition to invalidate, or None for all
        """
        if transition_id is None:
            # Invalidate all
            print(f"[Controller] Invalidating all behavior caches ({len(self.behavior_cache)} transitions)")
            
            # Clear enablement states for all
            for behavior in self.behavior_cache.values():
                if hasattr(behavior, 'clear_enablement'):
                    behavior.clear_enablement()
            
            self.behavior_cache.clear()
            self.transition_states.clear()
        else:
            # Invalidate specific transition
            if transition_id in self.behavior_cache:
                print(f"[Controller] Invalidating behavior cache for transition {transition_id}")
                
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
                print(f"[SimulationController] Error in step listener: {e}")
    
    def step(self, time_step: float = 0.1) -> bool:
        """Execute a single simulation step with hybrid (discrete + continuous) execution.
        
        This performs one iteration of the simulation:
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
            time_step: Time increment for this step (default: 0.1)
        
        Returns:
            bool: True if any transition fired/integrated, False if deadlocked
        """
        # Update enablement states at current time (before any execution)
        self._update_enablement_states()
        
        # === PHASE 0: IMMEDIATE TRANSITIONS (exhaust all in zero time) ===
        # Following legacy semantics: immediate transitions fire instantly
        # Loop until no immediate transitions are enabled
        immediate_fired_total = 0
        max_immediate_iterations = 1000  # Safety limit to prevent infinite loops
        
        for iteration in range(max_immediate_iterations):
            # Find all enabled immediate transitions
            immediate_transitions = [t for t in self.model.transitions 
                                    if t.transition_type == 'immediate']
            
            enabled_immediate = [t for t in immediate_transitions 
                               if self._is_transition_enabled(t)]
            
            if not enabled_immediate:
                break  # No more immediate transitions to fire
            
            # Select highest priority immediate transition
            transition = self._select_transition(enabled_immediate)
            self._fire_transition(transition)
            immediate_fired_total += 1
            
            print(f"⚡ [IMMEDIATE] {transition.name} fired instantly at t={self.time:.3f}")
            
            # Update enablement states after firing (for next iteration)
            self._update_enablement_states()
        
        if iteration >= max_immediate_iterations - 1:
            print(f"⚠️  [WARNING] Immediate transition loop limit reached ({max_immediate_iterations} iterations)")
            print(f"   This may indicate an infinite firing loop in your model!")
        if iteration >= max_immediate_iterations - 1:
            print(f"⚠️  [WARNING] Immediate transition loop limit reached ({max_immediate_iterations} iterations)")
            print(f"   This may indicate an infinite firing loop in your model!")
        
        # === PHASE 1: IDENTIFY CONTINUOUS TRANSITIONS (before state changes) ===
        continuous_transitions = [t for t in self.model.transitions 
                                 if t.transition_type == 'continuous']
        
        DEBUG_CONTINUOUS = True  # Enable continuous transition debugging
        if DEBUG_CONTINUOUS and continuous_transitions:
            print(f"[CONTINUOUS] Found {len(continuous_transitions)} continuous transitions")
        
        # Determine which continuous transitions can flow based on INITIAL state
        continuous_to_integrate = []
        for transition in continuous_transitions:
            behavior = self._get_behavior(transition)
            can_flow, reason = behavior.can_fire()
            if DEBUG_CONTINUOUS:
                print(f"[CONTINUOUS] {transition.name}: can_flow={can_flow}, reason={reason}")
            if can_flow:
                input_arcs = behavior.get_input_arcs()
                output_arcs = behavior.get_output_arcs()
                continuous_to_integrate.append((transition, behavior, input_arcs, output_arcs))
        
        # === PHASE 2: DISCRETE TRANSITIONS (timed, stochastic - NOT immediate) ===
        # Note: Immediate transitions already exhausted in Phase 0
        discrete_transitions = [t for t in self.model.transitions 
                               if t.transition_type in ['timed', 'stochastic']]
        
        enabled_discrete = [t for t in discrete_transitions 
                           if self._is_transition_enabled(t)]
        
        # Debug: Show discrete transition status (minimal output)
        DEBUG_CONTROLLER = True  # Set to True to enable detailed step logging
        if DEBUG_CONTROLLER and discrete_transitions:
            print(f"\n[Controller] Step at t={self.time:.3f}:")
            for t in discrete_transitions:
                behavior = self._get_behavior(t)
                state = self._get_or_create_state(t)
                can_fire, reason = behavior.can_fire()
                status = "CAN FIRE" if can_fire else f"BLOCKED: {reason}"
                print(f"  - {t.name} (type={t.transition_type}): {status}, enablement_time={state.enablement_time}")
        
        discrete_fired = False
        if enabled_discrete:
            # Select and fire one discrete transition (conflict resolution)
            transition = self._select_transition(enabled_discrete)
            self._fire_transition(transition)
            discrete_fired = True
            
            # Always show when a transition fires (important event!)
            print(f"🔥 [FIRED] {transition.name} at t={self.time:.3f}")
            
            if DEBUG_CONTROLLER:
                print(f"  >>> FIRED: {transition.name}")
        elif DEBUG_CONTROLLER:
            print(f"  >>> No timed/stochastic transitions fired this step")
        
        # === PHASE 3: CONTINUOUS TRANSITIONS (integrate all pre-identified) ===
        continuous_active = 0
        for transition, behavior, input_arcs, output_arcs in continuous_to_integrate:
            # Integrate (continuous flow over time_step)
            success, details = behavior.integrate_step(
                dt=time_step,
                input_arcs=input_arcs,
                output_arcs=output_arcs
            )
            
            if success:
                continuous_active += 1
                
                if DEBUG_CONTINUOUS:
                    print(f"[CONTINUOUS] ✓ {transition.name} integrated at t={self.time:.3f}")
                    print(f"[CONTINUOUS]   consumed: {details.get('consumed', {})}")
                    print(f"[CONTINUOUS]   produced: {details.get('produced', {})}")
                    print(f"[CONTINUOUS]   rate: {details.get('rate', 0.0):.3f}")
                
                # Notify data collector about continuous transition activity
                if self.data_collector is not None:
                    self.data_collector.on_transition_fired(transition, self.time, details)
                    if DEBUG_CONTINUOUS:
                        print(f"[CONTINUOUS]   data_collector notified")
                else:
                    if DEBUG_CONTINUOUS:
                        print(f"[CONTINUOUS]   ⚠️ NO data_collector attached!")
        
        if DEBUG_CONTINUOUS and continuous_to_integrate:
            print(f"[CONTINUOUS] Total active: {continuous_active}/{len(continuous_to_integrate)}")
        
        # Advance time
        self.time += time_step
        
        # Notify listeners
        self._notify_step_listeners()
        
        # Return True if:
        # 1. Something fired/integrated this step (immediate, discrete, or continuous), OR
        # 2. There are enabled transitions waiting for their timing window (timed/stochastic)
        # This prevents premature deadlock detection when timed transitions are waiting
        if immediate_fired_total > 0 or discrete_fired or continuous_active > 0:
            return True
        
        # Check if any timed/stochastic transitions are waiting OR can fire now
        waiting_count = 0
        ready_count = 0
        
        for transition in discrete_transitions:
            behavior = self._get_behavior(transition)
            can_fire, reason = behavior.can_fire()
            
            if DEBUG_CONTROLLER:
                print(f"  [Deadlock check] {transition.name}: can_fire={can_fire}, reason='{reason}'")
            
            if can_fire:
                # Transition is ready to fire (will fire next step)
                ready_count += 1
                if DEBUG_CONTROLLER:
                    print(f"  -> {transition.name} is READY to fire")
            elif reason and 'too-early' in str(reason):
                # Transition is waiting for time (not permanently blocked)
                waiting_count += 1
                if DEBUG_CONTROLLER:
                    print(f"  -> {transition.name} is WAITING (too-early)")
        
        if waiting_count > 0 or ready_count > 0:
            if DEBUG_CONTROLLER:
                print(f"  -> {waiting_count} waiting + {ready_count} ready = NOT DEADLOCKED")
            return True  # Transitions are waiting or ready, not deadlocked
        
        # True deadlock: nothing fired and nothing is waiting
        if DEBUG_CONTROLLER:
            print(f"  -> TRUE DEADLOCK: No transitions fired and none waiting")
        return False
    
    def _find_enabled_transitions(self) -> List:
        """Find all transitions that are enabled (can fire).
        
        A transition is enabled if all its input places have enough tokens
        to satisfy the arc weights.
        
        Returns:
            List of enabled Transition objects
        """
        enabled = []
        
        # Get all transitions from the model manager
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
        # Get behavior and delegate to can_fire()
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
        # Get behavior and delegate to fire()
        behavior = self._get_behavior(transition)
        
        # Get arcs for this transition
        input_arcs = behavior.get_input_arcs()
        output_arcs = behavior.get_output_arcs()
        
        # Fire using behavior
        success, details = behavior.fire(input_arcs, output_arcs)
        
        # Clear controller's state after successful firing
        # This allows the transition to be re-enabled and fire again
        if success:
            state = self._get_or_create_state(transition)
            state.enablement_time = None
            state.scheduled_time = None
        
        # Notify data collector if attached (pass details for consistency)
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
            # Random selection (default)
            return random.choice(enabled_transitions)
        
        elif self.conflict_policy == ConflictResolutionPolicy.PRIORITY:
            # Select highest priority transition
            # Default priority is 0 if not set
            return max(enabled_transitions, key=lambda t: getattr(t, 'priority', 0))
        
        elif self.conflict_policy == ConflictResolutionPolicy.TYPE_BASED:
            # Select based on transition type priority
            # immediate > timed > stochastic > continuous
            return max(enabled_transitions, 
                      key=lambda t: TYPE_PRIORITIES.get(t.transition_type, 0))
        
        elif self.conflict_policy == ConflictResolutionPolicy.ROUND_ROBIN:
            # Fair round-robin selection
            selected = enabled_transitions[self._round_robin_index % len(enabled_transitions)]
            self._round_robin_index += 1
            return selected
        
        else:
            # Fallback to random if unknown policy
            return random.choice(enabled_transitions)
    
    def run(self, time_step: float = 0.1, max_steps: Optional[int] = None) -> bool:
        """Start continuous simulation execution.
        
        Runs the simulation continuously using GLib timeout callbacks.
        Can be stopped by calling stop().
        
        Args:
            time_step: Time increment per step (default: 0.1)
            max_steps: Maximum number of steps to run (None = unlimited)
        
        Returns:
            bool: True if started successfully, False if already running
        """
        if not GLIB_AVAILABLE:
            print("[Controller.run] ERROR: GLib not available!")
            return False
        
        if self._running:
            print("[Controller.run] Already running, ignoring duplicate run request")
            return False
        
        print(f"\n▶️  [RUN] Starting simulation at t={self.time:.3f}")
        print(f"[RUN] Checking initial transition states...")
        
        # Show initial state BEFORE enablement update
        for transition in self.model.transitions:
            state = self.transition_states.get(transition.id)
            behavior = self._get_behavior(transition)
            print(f"  {transition.name} (type={transition.transition_type}): enablement_time={state.enablement_time if state else 'None'}")
        
        self._running = True
        self._stop_requested = False
        self._max_steps = max_steps
        self._steps_executed = 0
        self._time_step = time_step
        
        # CRITICAL: Initialize enablement states BEFORE starting the loop
        # This ensures timed transitions know when they were enabled at t=0
        print(f"[RUN] Calling _update_enablement_states()...")
        self._update_enablement_states()
        
        # Show state AFTER enablement update
        print(f"[RUN] After enablement update:")
        for transition in self.model.transitions:
            state = self.transition_states.get(transition.id)
            behavior = self._get_behavior(transition)
            
            # Get timing info for timed/stochastic
            if hasattr(behavior, 'get_timing_info'):
                info = behavior.get_timing_info()
                print(f"  {transition.name}: enablement={state.enablement_time if state else 'None'}, {info}")
            elif hasattr(behavior, 'get_stochastic_info'):
                info = behavior.get_stochastic_info()
                print(f"  {transition.name}: scheduled={info.get('scheduled_fire_time')}, burst={info.get('sampled_burst')}")
            else:
                print(f"  {transition.name}: enablement={state.enablement_time if state else 'None'}")
        
        # Start the simulation loop using GLib timeout
        self._timeout_id = GLib.timeout_add(100, self._simulation_loop)
        print(f"[RUN] Simulation loop started\n")
        
        return True
    
    def _simulation_loop(self) -> bool:
        """Internal simulation loop callback.
        
        Returns:
            bool: True to continue, False to stop the timeout
        """
        DEBUG_LOOP = False  # Set to True for verbose loop debugging
        
        if DEBUG_LOOP:
            print(f"[Controller._simulation_loop] CALLED at t={self.time:.3f}, _running={self._running}, _stop_requested={self._stop_requested}")
        
        # Check if we should stop
        if self._stop_requested:
            if DEBUG_LOOP:
                print(f"[Controller._simulation_loop] Stop requested - halting")
            self._running = False
            self._timeout_id = None
            return False
        
        # Check max steps
        if self._max_steps is not None and self._steps_executed >= self._max_steps:
            if DEBUG_LOOP:
                print(f"[Controller._simulation_loop] Max steps reached - halting")
            self._running = False
            self._timeout_id = None
            return False
        
        # Execute one step
        success = self.step(self._time_step)
        
        if not success:
            # Deadlock detected - stop simulation
            print(f"⏸️  [DEADLOCK] Simulation stopped at t={self.time:.3f} - no enabled transitions")
            self._running = False
            self._timeout_id = None
            return False
        
        self._steps_executed += 1
        
        if DEBUG_LOOP:
            print(f"[Controller._simulation_loop] Step {self._steps_executed} complete, continuing...")
        
        # Continue the loop
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
        
        print(f"⏸️  [STOP] Stopping simulation at t={self.time:.3f}")
        self._stop_requested = True
        
        # Clear enablement states when stopping so that restarting gives fresh times
        for state in self.transition_states.values():
            state.enablement_time = None
            state.scheduled_time = None
        
        # Also clear behavior enablement times
        for behavior in self.behavior_cache.values():
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()
    
    def reset(self):
        """Reset the simulation to initial marking.
        
        This stops any running simulation and resets all places to their
        initial marking values.
        """
        # Stop if running
        if self._running:
            self.stop()
            # Wait for stop to complete
            if self._timeout_id is not None and GLIB_AVAILABLE:
                GLib.source_remove(self._timeout_id)
                self._timeout_id = None
                self._running = False
        
        # Reset time
        self.time = 0.0
        
        # Clear data collector if attached
        if self.data_collector is not None:
            self.data_collector.clear()
            print("[SimulationController] Data collector cleared on reset")
        
        # Clear transition states (Phase 3: Time-Aware Behaviors)
        self.transition_states.clear()
        
        # Clear behavior caches to ensure fresh start
        for behavior in self.behavior_cache.values():
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()
        
        # Reset all places to initial marking
        for place in self.model.places:
            if hasattr(place, 'initial_marking'):
                place.tokens = place.initial_marking
            else:
                place.tokens = 0
        
        # Notify listeners
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
        return {
            'time': self.time,
            'running': self._running,
            'enabled_transitions': len(self._find_enabled_transitions())
        }
