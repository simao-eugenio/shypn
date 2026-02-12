"""
Simulation Controller for Petri Net Execution

Manages the execution of Petri net simulations, including:
- Single-step execution
- Continuous execution (run mode)
- Stop/pause functionality
- Reset to initial marking

Based on the legacy shypnpy simulation controller but adapted for
the new architecture.

╔═══════════════════════════════════════════════════════════════════════════╗
║ ARCHITECTURE NOTE: This class is intentionally large (3000+ lines)        ║
║                                                                            ║
║ REASON: Manages complex state machine for simulation execution.           ║
║         State transitions, mode switching (stochastic/deterministic/      ║
║         hybrid), validation, and UI synchronization MUST be centralized   ║
║         to prevent race conditions and inconsistent state.                ║
║                                                                            ║
║ ⚠️  DO NOT SPLIT: State machine from controller                          ║
║ ⚠️  DO NOT SPLIT: UI synchronization into different class                ║
║ ⚠️  DO NOT SPLIT: Mode switching (stochastic/deterministic) separately   ║
║                                                                            ║
║ SAFE REFACTORINGS:                                                        ║
║ ✅ Apply State Pattern (RunningState, PausedState, StoppedState)         ║
║ ✅ Extract validation orchestration (stateless coordinator)               ║
║ ✅ Create value objects (SimulationConfig, ValidationResults)             ║
║ ✅ Command Pattern (StartCommand, PauseCommand, StepCommand)              ║
║ ✅ Extract result formatting to pure functions                            ║
║                                                                            ║
║ SEE: doc/ADR-003-simulation-controller-complexity.md (when created)       ║
╚═══════════════════════════════════════════════════════════════════════════╝
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
from shypn.engine.simulation.executors import ContinuousExecutor
from shypn.engine.simulation.checkers import ViabilityChecker
# Week 1 - Phase 4: EventBus integration for progress events
from shypn.events import EventBus
# DEPRECATED: Conservation enforcement - Petri nets naturally conserve mass/energy
# from shypn.engine.conservation_enforcer import ConservationEnforcer

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
            pass
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

# ==================== Model Accessors (Property Proxies) ====================

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

    def __init__(self, model, verbose: bool = True, recording_config: 'RecordingConfig' = None):
        """Initialize the simulation controller.
        
        REFACTORED: Now uses RecordingConfig value object (reduced from 4 parameters to 2).
        
        Args:
            model: ModelCanvasManager instance (has places, transitions, arcs lists)
            verbose: If True, print debug output (disable for batch mode performance)
            recording_config: RecordingConfig for data collection (default: 20 Hz time-based, all objects)
        """
        if recording_config is None:
            from shypn.core.value_objects import RecordingConfig
            recording_config = RecordingConfig.default()
        
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
        self.verbose = verbose  # Control debug output
        
        # Week 1 - Phase 4: Document ID for scoped event emissions
        self.document_id: Optional[int] = None  # Set by ModelCanvasLoader
        
        # Data collection for simulation results
        from shypn.engine.simulation.data_collector import DataCollector
        
        # Create settings first so we can access recorded_objects
        from shypn.engine.simulation.settings import SimulationSettings
        self.settings = SimulationSettings()
        
        # Create DataCollector with RecordingConfig
        self.data_collector = DataCollector(model, controller=self, config=recording_config)
        
        # Callback for simulation complete event
        # Use private attribute with property to trace all assignments
        self._on_simulation_complete = None
        
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
        
        # Thermodynamic validation results (populated on demand)
        self.thermodynamic_results = None
        
        # Option 3: Assignment rule re-evaluation support
        self.enable_assignment_rule_reevaluation = False
        self.pathway_data = None  # Store for assignment rule initialization
        
        # Token accounting auditor (conservation validation)
        self.auditor = None  # Initialized when enabled via settings
        
        # Thermodynamic validator manager (Feb 9, 2026)
        from shypn.engine.simulation.validation import ValidatorManager
        self.validator_manager = ValidatorManager()
        
        # Continuous execution strategy (Phase 2.3.1 extraction)
        self._continuous_executor = ContinuousExecutor(self)
        
        # Viability checking strategy (Phase 2.3.2 extraction)
        self._viability_checker = ViabilityChecker(self)
        
        # Week 4 - Phase 4: Strategy Pattern for simulation algorithms
        # Enables runtime switching between different execution strategies
        self._execution_strategy = None  # HybridStrategy by default (set on first use)
        
        # DEPRECATED: Mass conservation enforcer (Feb 9, 2026)
        # Reason: Petri net semantics NATURALLY conserve mass/energy through
        # token-based firing rules. Explicit enforcement was based on misunderstanding.
        # Conservation is an inherent property of properly constructed Petri nets,
        # not an external constraint requiring enforcement.
        # See: archive/deprecated_conservation_enforcement/README.md
        
        # self.conservation_enforcer = ConservationEnforcer(model)
        self.conservation_enforcer = None  # Deprecated
        self.auto_conservation_enabled = False  # Deprecated
        
        # Register to observe model changes (for arc transformations, deletions, etc.)
        if hasattr(model, 'register_observer'):
            model.register_observer(self._on_model_changed)
    
    # ==================== Lifecycle Management ====================
    
    def reset(self):
        """Reset controller to initial state for new model load.
        
        Called when loading a new model into an existing canvas tab (File → Open,
        KEGG Import, SBML Import, etc.). Clears all cached state and reinitializes
        adapters to prevent stale references from previous model.
        
        CRITICAL FIX: This prevents simulation failures when importing models
        because the controller maintains state from the previous model:
        - behavior_cache with old transition IDs
        - transition_states with deleted transitions
        - data_collector with wrong model reference
        - time/running flags from previous simulation
        
        Without this reset, imported models fail to simulate until user manually
        creates new objects (which triggers cache invalidation as side effect).
        
        See: doc/CRITICAL_SIMULATION_INIT_IMPORT_BUG.md
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Resetting SimulationController for new model load")
        
        # Reset simulation state
        self.time = 0.0
        self._running = False
        self._stop_requested = False
        if self._timeout_id:
            import gi
            gi.require_version('GLib', '2.0')
            from gi.repository import GLib
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
        
        # Clear caches
        self.behavior_cache.clear()
        self.transition_states.clear()
        self._round_robin_index = 0
        
        # Clear thermodynamic validation results
        self.thermodynamic_results = None
        
        # Reset τ-leaping engine (if it exists)
        if hasattr(self, '_tau_leaping_engine'):
            delattr(self, '_tau_leaping_engine')
        
        # Reinitialize model adapter with current model
        from shypn.engine.simulation.model_adapter import ModelAdapter
        self.model_adapter = ModelAdapter(self.model, controller=self)
        
        # Reinitialize data collector with current model
        from shypn.engine.simulation.data_collector import DataCollector
        from shypn.core.value_objects import RecordingConfig
        
        config = RecordingConfig(
            recorded_objects=self.settings.recorded_objects if hasattr(self.settings, 'recorded_objects') else None
        )
        self.data_collector = DataCollector(self.model, controller=self, config=config)
        
        # CRITICAL: Notify any observers that data_collector changed
        # This ensures analyses panels get the new data_collector reference
        if hasattr(self, '_on_data_collector_changed'):
            try:
                self._on_data_collector_changed(self.data_collector)
            except Exception as e:
                logger.warning(f"Error notifying data_collector change: {e}")
        
        # Reset buffered settings (discard any uncommitted changes from previous model)
        if hasattr(self, 'buffered_settings'):
            self.buffered_settings.rollback()
        
        # DEPRECATED: Conservation enforcer no longer used
        # if hasattr(self, 'conservation_enforcer'):
        #     self.conservation_enforcer = ConservationEnforcer(self.model)
        
        logger.info(f"SimulationController reset complete - ready for new model")
    
    @property
    def on_simulation_complete(self):
        """Callback invoked when simulation completes."""
        return self._on_simulation_complete
    
    @on_simulation_complete.setter
    def on_simulation_complete(self, value):
        """Set callback with debug logging to trace all assignments."""
        import traceback
        import sys
        
        # Log the assignment with controller ID
        controller_id = id(self)
        if value is None:
            pass
            # print(f"[CALLBACK_TRACE] ⚠️  Controller {controller_id}: on_simulation_complete set to None (was: {self._on_simulation_complete is not None})")
        else:
            pass
            # print(f"[CALLBACK_TRACE] ✅ Controller {controller_id}: on_simulation_complete set to {value}")
        
        # Print stack trace to see WHO is setting it
        # print(f"[CALLBACK_TRACE] Stack trace:")
        for line in traceback.format_stack()[:-1]:  # Exclude this setter call
            # Only print relevant lines (skip standard library noise)
            if '/shypn/' in line and 'traceback' not in line.lower():
                pass
                # print(f"[CALLBACK_TRACE]   {line.strip()}")
        
        self._on_simulation_complete = value
    
    def validate_thermodynamics(self) -> Dict[str, Any]:
        """
        Validate thermodynamic consistency of reversible transitions.
        
        Checks all reversible transitions in the model to ensure their rate
        constants are consistent with thermodynamic equilibrium constants
        derived from Gibbs free energy.
        
        Results are cached in self.thermodynamic_results for GUI display.
        
        Returns:
            Dict with validation results:
            - 'summary': Overall summary statistics
            - 'violations': List of transitions with violations
            - 'warnings': List of transitions with warnings
            - 'valid': List of valid transitions
            - 'insufficient_data': List with missing data
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from shypn.thermodynamics.simulation_integration import ThermodynamicSimulationValidator
            
            # Initialize validator
            validator = ThermodynamicSimulationValidator()
            
            # Get reversible transitions from model
            reversible_transitions = [
                t for t in self.model.transitions
                if t.properties.get('is_reversible', False)
            ]
            
            if not reversible_transitions:
                logger.info("No reversible transitions found for thermodynamic validation")
                self.thermodynamic_results = {
                    'summary': {
                        'total': 0,
                        'valid': 0,
                        'warnings': 0,
                        'violations': 0,
                        'insufficient_data': 0,
                    },
                    'violations': [],
                    'warnings': [],
                    'valid': [],
                    'insufficient_data': [],
                }
                return self.thermodynamic_results
            
            logger.info(f"Validating {len(reversible_transitions)} reversible transitions")
            
            # Collect results from transition properties
            violations = []
            warnings = []
            valid = []
            insufficient_data = []
            
            for transition in reversible_transitions:
                # Get validation result from properties (stored during SBML import)
                validation = transition.properties.get('thermodynamic_validation')
                
                if validation is None:
                    # No validation stored - mark as insufficient data
                    insufficient_data.append({
                        'transition': transition.name,
                        'message': 'Validation not performed during import'
                    })
                    continue
                
                status = validation.get('status', 'unknown')
                
                if status == 'valid':
                    valid.append({
                        'transition': transition.name,
                        'k_ratio': validation.get('k_ratio'),
                        'k_eq': validation.get('k_eq'),
                        'deviation': validation.get('deviation'),
                    })
                elif status == 'warning':
                    warnings.append({
                        'transition': transition.name,
                        'k_ratio': validation.get('k_ratio'),
                        'k_eq': validation.get('k_eq'),
                        'deviation': validation.get('deviation'),
                        'message': validation.get('message', 'Exceeded warning threshold'),
                    })
                elif status == 'violation':
                    violations.append({
                        'transition': transition.name,
                        'k_ratio': validation.get('k_ratio'),
                        'k_eq': validation.get('k_eq'),
                        'deviation': validation.get('deviation'),
                        'message': validation.get('message', 'Exceeded violation threshold'),
                    })
                else:
                    # insufficient_data, no_rate_constants, error
                    insufficient_data.append({
                        'transition': transition.name,
                        'status': status,
                        'message': validation.get('message', 'Unknown issue'),
                    })
            
            # Build summary
            summary = {
                'total': len(reversible_transitions),
                'valid': len(valid),
                'warnings': len(warnings),
                'violations': len(violations),
                'insufficient_data': len(insufficient_data),
            }
            
            # Store results
            self.thermodynamic_results = {
                'summary': summary,
                'violations': violations,
                'warnings': warnings,
                'valid': valid,
                'insufficient_data': insufficient_data,
            }
            
            logger.info(
                f"Thermodynamic validation complete: "
                f"{summary['valid']} valid, "
                f"{summary['warnings']} warnings, "
                f"{summary['violations']} violations, "
                f"{summary['insufficient_data']} insufficient data"
            )
            
            return self.thermodynamic_results
            
        except ImportError as e:
            logger.warning(f"Thermodynamic validation not available: {e}")
            self.thermodynamic_results = None
            return None
        except Exception as e:
            logger.error(f"Thermodynamic validation failed: {e}")
            self.thermodynamic_results = None
            return None
    
    def initialize_assignment_rules(self, pathway_data: Any = None) -> None:
        """Initialize assignment rules for runtime re-evaluation (Option 3).
        
        Extracts assignment rules from pathway species and passes them to
        stochastic behaviors for runtime evaluation during τ-leaping.
        
        Called after SBML/KEGG import with enable_assignment_rule_reevaluation=True.
        
        Args:
            pathway_data: PathwayData object with species containing assignment_rule field
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if pathway_data is None:
            logger.warning("No pathway_data provided for assignment rule initialization")
            return
        
        self.pathway_data = pathway_data
        
        # Initialize assignment rules on stochastic behaviors
        stochastic_transitions = [
            t for t in self.model.transitions
            if t.transition_type == 'stochastic'
        ]
        
        if not stochastic_transitions:
            logger.info("No stochastic transitions found - assignment rule re-evaluation not applicable")
            return
        
        # Get behavior of first stochastic transition and initialize
        behavior = self._get_behavior(stochastic_transitions[0])
        if behavior and hasattr(behavior, 'initialize_assignment_rules'):
            behavior.initialize_assignment_rules(pathway_data)
            
            if behavior.assignment_rules:
                logger.info(
                    f"✅ Option 3 enabled: Runtime re-evaluation initialized for "
                    f"{len(behavior.assignment_rules)} assignment rule(s)"
                )
            else:
                logger.info("No assignment rules found in pathway data")
        else:
            logger.warning(
                "StochasticBehavior does not support assignment rule re-evaluation. "
                "Update StochasticBehavior class to add initialize_assignment_rules() method."
            )
    
    def get_thermodynamic_summary(self) -> Optional[Dict[str, int]]:
        """
        Get summary of thermodynamic validation results.
        
        Returns cached results from last validation, or performs validation
        if not yet cached.
        
        Returns:
            Dict with summary statistics or None if validation unavailable:
            - 'total': Total reversible transitions
            - 'valid': Number passing validation
            - 'warnings': Number with warnings
            - 'violations': Number with violations
            - 'insufficient_data': Number with missing data
        """
        if self.thermodynamic_results is None:
            self.validate_thermodynamics()
        
        if self.thermodynamic_results is None:
            return None
        
        return self.thermodynamic_results.get('summary')

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
            pass
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
            pass
            # If an arc was transformed, rebuild behaviors for affected transitions
            if isinstance(obj, Arc):
                pass
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
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"[OBSERVER] ✅ Enabling source transition {obj.id} at t={self.time}")
                    # Source transitions are always enabled
                    state = self.transition_states[obj.id]
                    state.enablement_time = self.time
                    if hasattr(behavior, 'set_enablement_time'):
                        behavior.set_enablement_time(self.time)
                else:
                    pass
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
        
        elif event_type == 'modified':
            # Object properties were modified
            if isinstance(obj, Transition):
                # Invalidate behavior cache (type or properties may have changed)
                if obj.id in self.behavior_cache:
                    del self.behavior_cache[obj.id]
                
                # Check if it's now a source transition and enable if needed
                is_source = getattr(obj, 'is_source', False)
                if is_source:
                    state = self._get_or_create_state(obj)
                    if state.enablement_time is None:
                        state.enablement_time = self.time
                        behavior = self._get_behavior(obj)
                        if hasattr(behavior, 'set_enablement_time'):
                            behavior.set_enablement_time(self.time)
                        import logging
                        logging.getLogger(__name__).info(f"[OBSERVER] ✅ Enabled source transition {obj.id} at t={self.time}")
    
    # ========== Token Accounting Methods ==========
    
    def enable_token_accounting(self, strict_mode=False):
        """Enable token conservation accounting.
        
        Args:
            strict_mode: If True, raise RuntimeError on violations. If False, collect violations.
        """
        try:
            from shypn.engine.accounting import TokenAccountingAuditor
            self.auditor = TokenAccountingAuditor(self.model_adapter, strict_mode=strict_mode)
            self.auditor.enable()
            
            # Enable accounting in all transition behaviors
            for transition in self.model.transitions:
                behavior = self._get_behavior(transition)
                behavior.enable_accounting()
            
            print(f"✓ Token accounting enabled (transitions: {len(self.model.transitions)})")
        except Exception as e:
            print(f"✗ Failed to enable token accounting: {e}")
            import traceback
            traceback.print_exc()
            self.auditor = None
    
    def disable_token_accounting(self):
        """Disable token conservation accounting."""
        self.auditor = None
        
        # Disable accounting in all transition behaviors
        for transition in self.model.transitions:
            behavior = self._get_behavior(transition)
            behavior.disable_accounting()
    
    def get_accounting_report(self):
        """Get token accounting report.
        
        Returns:
            dict: Accounting report with statistics and violations, or None if disabled
        """
        if self.auditor is None:
            return None
        return self.auditor.generate_report()
    
    def print_accounting_report(self):
        """Print token accounting report to console."""
        if self.auditor is not None:
            self.auditor.print_report()
    
    # ==================== Behavior Management ====================

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
            pass
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
        import logging
        logger = logging.getLogger(__name__)
        
        # Debug: Log source transitions
        source_transitions = [t for t in self.model.transitions if getattr(t, 'is_source', False)]
        if source_transitions and not hasattr(self, '_logged_source_transitions'):
            self._logged_source_transitions = True
            logger.info(f"Found {len(source_transitions)} source transition(s):")
            for t in source_transitions:
                logger.info(f"  - {t.id}: type={t.transition_type}, is_source={getattr(t, 'is_source', False)}")
        
        for transition in self.model.transitions:
            behavior = self._get_behavior(transition)
            
            # Special handling for source transitions (no input places)
            is_source = getattr(transition, 'is_source', False)
            if is_source:
                pass
                # Source transitions are always structurally enabled
                state = self._get_or_create_state(transition)
                if state.enablement_time is None:
                    state.enablement_time = self.time
                    if hasattr(behavior, 'set_enablement_time'):
                        behavior.set_enablement_time(self.time)
                    logger.debug(f"Source transition {transition.id} enabled at t={self.time}")
                # Source transitions stay enabled continuously
                continue
            
            input_arcs = behavior.get_input_arcs()
            locally_enabled = True
            
            # Import arc types and threshold evaluator
            from shypn.netobjs.inhibitor_arc import InhibitorArc
            from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
            from shypn.utils.threshold_evaluator import ThresholdEvaluator
            
            # Create threshold evaluator for dynamic threshold support
            evaluator = ThresholdEvaluator(behavior.model)
            context = {'time': self.time}
            
            for arc in input_arcs:
                # Check ALL arc types for enablement (normal, test, inhibitor)
                source_place = behavior._get_place(arc.source_id)
                if source_place is None:
                    locally_enabled = False
                    break
                
                # Evaluate effective threshold (supersedes weight if threshold is set)
                # This supports dynamic thresholds like "ATP * 0.5" (Example 16)
                effective_threshold = evaluator.evaluate(arc, context)
                
                # Test arcs (catalysts) use lower threshold for fractional enablement
                # Allows stochastic reactions to fire even with sub-unity concentrations
                # This prevents "oscillation trap" where smooth production below 1.0
                # prevents stochastic transitions from ever enabling
                if hasattr(arc, 'arc_type') and arc.arc_type == 'test':
                    # Test arcs: Catalyst presence (lower threshold for fractional concentrations)
                    effective_threshold = min(effective_threshold, 0.1)  # At least 10% of threshold
                
                # Check based on arc type
                if isinstance(arc, (InhibitorArc, CurvedInhibitorArc)):
                    # Inhibitor arcs: INVERTED check (enabled when tokens < threshold)
                    # Transition DISABLED when place has too many tokens (negative feedback)
                    if source_place.tokens >= effective_threshold:
                        locally_enabled = False
                        break
                else:
                    # Normal/Test arcs: Standard check (enabled when tokens >= threshold)
                    if source_place.tokens < effective_threshold:
                        locally_enabled = False
                        break
            state = self._get_or_create_state(transition)
            
            # Debug stochastic enablement (first time only) - removed for cleaner output
            
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
    
    def _emit_progress_event(self):
        """Emit simulation.progress event for UI updates.
        
        Week 1 - Phase 4: EventBus integration for decoupled progress tracking.
        Analyses panel and other observers subscribe to this event.
        """
        if self.document_id is None:
            return  # No document context, skip event
        
        try:
            progress = self.get_progress()
            EventBus.emit('simulation.progress', {
                'time': self.time,
                'progress': progress,
                'duration': self.settings.duration,
                'is_complete': self.is_simulation_complete()
            }, document_id=self.document_id)
        except Exception:
            pass  # Don't break simulation if event emission fails
    
    def is_simulation_complete(self) -> bool:
        """Check if simulation has reached duration limit.
        
        Returns:
            bool: True if time >= duration
        """
        return self.settings.is_complete(self.time)
    
    # ========== Strategy Pattern Methods (Week 4 - Phase 4) ==========
    
    def get_strategy(self):
        """Get current execution strategy.
        
        Returns:
            SimulationStrategy: Current strategy, or None if using default logic
        """
        return self._execution_strategy
    
    def set_strategy(self, strategy):
        """Set execution strategy for simulation.
        
        Enables runtime switching between different algorithms:
        - GillespieStrategy: Exact SSA (slow but accurate)
        - AdaptiveStrategy: Tau-leaping (fast approximation)
        - HybridStrategy: Mixed deterministic/stochastic
        - ContinuousStrategy: Pure ODE integration
        
        Args:
            strategy: SimulationStrategy instance or None for default
        
        Example:
            from shypn.engine.simulation.strategies import GillespieStrategy
            controller.set_strategy(GillespieStrategy(controller))
        """
        self._execution_strategy = strategy
    
    def auto_select_strategy(self):
        """Automatically select best strategy for current model.
        
        Selection logic:
        1. Pure continuous model → ContinuousStrategy
        2. Pure stochastic model → GillespieStrategy or AdaptiveStrategy
        3. Mixed model → HybridStrategy
        
        Returns:
            SimulationStrategy: Best strategy for this model
        """
        from shypn.engine.simulation.strategies import (
            GillespieStrategy,
            AdaptiveStrategy,
            HybridStrategy,
            ContinuousStrategy
        )
        
        # Analyze model composition
        has_continuous = False
        has_stochastic = False
        stochastic_count = 0
        
        for transition in self.model.transitions:
            if hasattr(transition, 'transition_type'):
                t_type = transition.transition_type
                if t_type in ('continuous', 'timed'):
                    has_continuous = True
                elif t_type == 'stochastic':
                    has_stochastic = True
                    stochastic_count += 1
        
        # Select strategy based on model composition
        if has_continuous and not has_stochastic:
            # Pure continuous model
            strategy = ContinuousStrategy(self)
        elif has_stochastic and not has_continuous:
            # Pure stochastic model
            if stochastic_count < 100:
                # Small model: Use exact Gillespie
                strategy = GillespieStrategy(self)
            else:
                # Large model: Use adaptive tau-leaping
                strategy = AdaptiveStrategy(self)
        else:
            # Mixed model or empty: Use hybrid strategy
            strategy = HybridStrategy(self)
        
        self._execution_strategy = strategy
        return strategy
    
    def list_available_strategies(self):
        """Get list of all available execution strategies.
        
        Returns:
            list: List of (name, description, can_execute) tuples
        """
        from shypn.engine.simulation.strategies import (
            GillespieStrategy,
            AdaptiveStrategy,
            HybridStrategy,
            ContinuousStrategy
        )
        
        strategies = [
            GillespieStrategy(self),
            AdaptiveStrategy(self),
            HybridStrategy(self),
            ContinuousStrategy(self)
        ]
        
        return [
            (s.get_name(), s.get_description(), s.can_execute())
            for s in strategies
        ]

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
    
    # ==================== Observer Pattern (Step Listeners) ====================

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
    
    def configure_conservation(
        self, 
        name: str, 
        place_ids: List[str], 
        expected_total: Optional[float] = None,
        tolerance: float = 1e-6
    ):
        """Configure mass conservation enforcement for a group of places.
        
        This addresses a fundamental limitation of Petri net formalism:
        reactions with asymmetric stoichiometry (e.g., 2 reactants → 1 product)
        create/destroy tokens when firings are imbalanced. This is mathematically
        proven, not a bug.
        
        Example:
            ATP synthesis: ADP + Pi → ATP (consumes 2 tokens, produces 1)
            ATP hydrolysis: ATP → ADP + Pi (consumes 1 token, produces 2)
            
            If synthesis fires 195× and hydrolysis fires 190×:
            Net token change = 195×(-1) + 190×(+1) = -5 tokens LOST
            
            Conservation enforcement corrects this by proportionally adjusting
            tokens to maintain the expected total (chemical reality).
        
        Args:
            name: Human-readable group name (e.g., "energy_cycle")
            place_ids: List of place IDs that should conserve mass
            expected_total: Expected sum (if None, uses current sum)
            tolerance: Allowable error before correction (default 1e-6)
        
        Example:
            controller.configure_conservation(
                name='energy_cycle',
                place_ids=['ATP_pool', 'ADP_pool', 'Pi_pool'],
                expected_total=15.0  # mM
            )
        """
        # DEPRECATED: ConservationEnforcer no longer used
        # Petri nets naturally conserve mass through token semantics
        pass
        # if self.conservation_enforcer:
        #     self.conservation_enforcer.add_conservation_group(
        #         name=name,
        #         place_ids=place_ids,
        #         expected_total=expected_total,
        #         tolerance=tolerance,
        #         auto_correct=True
        #     )
    
    def _auto_detect_conservation_groups(self):
        """Auto-detect closed cycles and configure conservation enforcement.
        
        Analyzes model structure to identify places that form closed cycles
        (no external sources/sinks) and automatically configures conservation
        groups to maintain mass balance.
        
        Called automatically at simulation start if auto_conservation_enabled=True.
        Skipped if conservation groups already manually configured.
        
        STRATEGY: Detect strongly connected components in the place-transition
        bipartite graph. Places in closed cycles should conserve total tokens.
        
        For simplicity, we use a heuristic:
        - Find all places connected through transitions (bidirectional flow)
        - Group places that participate in cycles (have both inputs and outputs)
        - Configure conservation using current token totals
        """
        # DEPRECATED: Auto-detection of conservation groups no longer used
        # Petri nets naturally conserve mass through token semantics
        return
        
        # Original implementation commented out:
        # if not self.model.places:
        #     return
        
        # import logging
        # logger = logging.getLogger(__name__)
        
        # Build connectivity graph: place -> set of connected places (via transitions)
        # place_connections = {p.id: set() for p in self.model.places}
        #
        # for transition in self.model.transitions:
        #     # Get input and output places for this transition
        #     input_places = set()
        #     output_places = set()
        #     
        #     for arc in self.model.arcs:
        #         if arc.target_id == transition.id:
        #             input_places.add(arc.source_id)
        #         elif arc.source_id == transition.id:
        #             output_places.add(arc.target_id)
        #     
        #     # Connect all input places to all output places (bidirectional cycle)
        #     for inp in input_places:
        #         for out in output_places:
        #             if inp != out:  # Avoid self-loops
        #                 place_connections[inp].add(out)
        #                 place_connections[out].add(inp)
        # 
        # # Find strongly connected components (closed cycles)
        # # Use simple DFS-based approach to find maximal connected groups
        # visited = set()
        # conservation_groups = []
        # 
        # def dfs(place_id, group):
        #     \"\"\"Depth-first search to find connected places.\"\"\"
        #     if place_id in visited:
        #         return
        #     visited.add(place_id)
        #     group.add(place_id)
        #     for connected in place_connections.get(place_id, []):
        #         dfs(connected, group)
        # 
        # # Find all maximal connected groups
        # for place in self.model.places:
        #     if place.id not in visited and place_connections.get(place.id):
        #         group = set()
        #         dfs(place.id, group)
        #         if len(group) >= 2:  # Only groups with 2+ places
        #             conservation_groups.append(group)
        # 
        # # Configure conservation for detected groups
        # if conservation_groups:
        #     logger.info(f\"[AUTO-CONSERVATION] Detected {len(conservation_groups)} closed cycle(s)\")
        #     
        #     for i, group in enumerate(conservation_groups):
        #         place_ids = list(group)
        #         
        #         # Calculate current total tokens
        #         total = sum(p.tokens for p in self.model.places if p.id in place_ids)
        #         
        #         # Only configure if total > 0 (avoid empty cycles)
        #         if total > 0:
        #             group_name = f\"auto_cycle_{i+1}\"
        #             
        #             # Get place names for logging
        #             place_names = [p.name for p in self.model.places if p.id in place_ids]
        #             
        #             self.conservation_enforcer.add_conservation_group(
        #                 name=group_name,
        #                 place_ids=place_ids,
        #                 expected_total=total,
        #                 tolerance=1e-6,
        #                 auto_correct=True
        #             )
        #             
        #             logger.info(
        #                 f\"  ✓ {group_name}: {len(place_ids)} places \"
        #                 f\"({', '.join(place_names[:3])}{'...' if len(place_names) > 3 else ''}), \"
        #                 f\"total={total:.3f}\"
        #             )
        # else:
        #     logger.info(\"[AUTO-CONSERVATION] No closed cycles detected (model may have sources/sinks)\")

    def _notify_step_listeners(self):
        """Notify all registered step listeners."""
        for callback in self.step_listeners:
            try:
                callback(self, self.time)
            except Exception as e:

                pass
    
    # ==================== Single-Step Execution (Hybrid Discrete + Continuous) ====================

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
        
        # STOICHIOMETRY FIX: Clamp time step to not exceed duration
        # This ensures the final step reaches exactly the duration, maintaining mass balance
        duration_seconds = self.settings.get_duration_seconds()
        if duration_seconds is not None:
            remaining_time = duration_seconds - self.time
            if remaining_time > 0 and time_step > remaining_time:
                # Take shortened final step to reach exactly duration
                time_step = remaining_time
        
        # Validate time step is non-negative
        if time_step < 0:
            raise ValueError(f"time_step must be non-negative, got {time_step}")
        
        # Warn about potentially problematic time steps (once per simulation)
        if time_step > 1.0:
            if not hasattr(self, '_large_timestep_warned'):
                self._large_timestep_warned = True
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Large time step ({time_step:.2f}s) may cause timed transitions to miss firing windows")
        
        # Auto-detect conservation groups on first step (if not already configured)
        # DISABLED: Conservation must emerge from arc connections, not artificial adjustments
        # if not hasattr(self, '_auto_conservation_checked'):
        #     self._auto_conservation_checked = True
        #     if self.auto_conservation_enabled and not self.conservation_enforcer.conservation_groups:
        #         self._auto_detect_conservation_groups()
        
        # PHASE 1-2 DEBUG: Print transition types once
        if not hasattr(self, '_debug_transition_types_printed'):
            self._debug_transition_types_printed = True
            type_counts = {}
            for t in self.model.transitions:
                ttype = t.transition_type
                type_counts[ttype] = type_counts.get(ttype, 0) + 1
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Model has {len(self.model.transitions)} transitions: {type_counts}")
            
            # Also log source transitions
            source_count = len([t for t in self.model.transitions if getattr(t, 'is_source', False)])
            if source_count > 0:
                logger.info(f"  - {source_count} source transition(s)")
        
        # Debug output (can be enabled for troubleshooting)
        # print(f"\n▶️  [SIMULATION_STEP] t={self.time:.3f}, dt={time_step:.3f}")
        
        # Track whether tau-leaping advanced time (to avoid double advancement)
        tau_leaping_advanced_time = False
        
        self._update_enablement_states()
        
        immediate_fired_total = 0
        max_immediate_iterations = 100  # Reduced from 1000 to prevent UI freeze
        fired_sequence = []  # Track which transitions fire to detect cycles
        
        for iteration in range(max_immediate_iterations):
            immediate_transitions = [t for t in self.model.transitions if t.transition_type == 'immediate']
            enabled_immediate = [t for t in immediate_transitions if self._is_transition_enabled(t)]
            if not enabled_immediate:
                break
            transition = self._select_transition(enabled_immediate)
            self._fire_transition(transition)
            immediate_fired_total += 1
            fired_sequence.append(transition.id)
            self._update_enablement_states()
            
            # Detect immediate livelock: if we've fired more than 20 times, check for cycles
            if immediate_fired_total > 20:
                # Check if we're in a repeating cycle (last 10 match previous 10)
                if len(fired_sequence) >= 20:
                    recent = fired_sequence[-10:]
                    previous = fired_sequence[-20:-10]
                    if recent == previous:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(
                            f"LIVELOCK DETECTED: Immediate transitions forming infinite cycle: "
                            f"{' → '.join(recent)}. "
                            f"Consider using continuous transitions or adding priorities/guards."
                        )
                        # Stop immediate phase to prevent UI freeze
                        break
        
        if iteration >= max_immediate_iterations - 1:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Immediate transition limit ({max_immediate_iterations}) reached in single step. "
                f"Fired sequence: {' → '.join(fired_sequence[-20:])}... "
                f"This may indicate a livelock. Consider using continuous transitions instead."
            )
        
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
                    pass
                    # Check structural enablement (tokens only, ignore timing)
                    # For sources, always structurally enabled
                    is_source = hasattr(transition, 'properties') and \
                                transition.properties.get('is_source', False)
                    
                    has_tokens = True
                    if not is_source:
                        input_arcs = behavior.get_input_arcs()
                        for arc in input_arcs:
                            pass
                            # Check ALL arc types (normal, test, inhibitor) for token availability
                            source_place = self.model_adapter.places.get(arc.source_id)
                            if source_place is None or source_place.tokens < arc.weight:
                                has_tokens = False
                                break
                    
                    if has_tokens:
                        pass
                        # Manual token transfer for window crossing (bypass timing checks in fire())
                        # This is necessary because fire() checks timing, but we KNOW the window is crossed
                        consumed_map = {}
                        produced_map = {}
                        
                        # Consume tokens from input places
                        if not is_source:
                            for arc in behavior.get_input_arcs():
                                # Skip inhibitor arcs and test arcs (they don't consume)
                                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                                arc_type = getattr(arc, 'arc_type', 'normal')
                                if kind != 'normal' or arc_type in ('inhibitor', 'test'):
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
                                arc_type = getattr(arc, 'arc_type', 'normal')
                                if kind != 'normal' or arc_type in ('inhibitor', 'test'):
                                    continue
                                target_place = self.model_adapter.places.get(arc.target_id)
                                target_place.set_tokens(target_place.tokens + arc.weight)
                                produced_map[arc.target_id] = arc.weight
                        
                        # Clear enablement state
                        state = self._get_or_create_state(transition)
                        state.enablement_time = None
                        state.scheduled_time = None
                        
                        # Increment firing count for statistics
                        transition.firing_count += 1
                        
                        # Notify data collector (if it has this method - old SimulationDataCollector)
                        if self.data_collector is not None and hasattr(self.data_collector, 'on_transition_fired'):
                            details = {
                                'consumed': consumed_map,
                                'produced': produced_map,
                                'window_crossing': True,
                                'timing_window': [behavior.earliest, behavior.latest]
                            }
                            self.data_collector.on_transition_fired(transition, self.time, details)
                        
                        # PHASE 1-2 FIX: Also notify step listeners if they have on_transition_fired
                        # print(f"[FIRE_NOTIFY] Window crossing: {transition.id}, notifying {len(self.step_listeners)} listeners")
                        for listener in self.step_listeners:
                            pass
                            # Check if listener is a bound method with __self__
                            listener_obj = listener.__self__ if hasattr(listener, '__self__') else listener
                            if hasattr(listener_obj, 'on_transition_fired'):
                                pass
                                # print(f"[FIRE_NOTIFY]   Notifying {type(listener_obj).__name__}")
                                details = {
                                    'consumed': consumed_map,
                                    'produced': produced_map,
                                    'window_crossing': True,
                                    'timing_window': [behavior.earliest, behavior.latest]
                                }
                                listener_obj.on_transition_fired(transition, self.time, details)
                        
                        window_crossing_fired += 1
        
        # Phase 3: Continuous transitions with conflict resolution
        # Group continuous transitions by locality conflicts and apply firing policies
        # NOTE: Include adaptive transitions ONLY if they're in continuous mode
        continuous_transitions = []
        for t in self.model.transitions:
            if t.transition_type == 'continuous':
                continuous_transitions.append(t)
            elif t.transition_type == 'adaptive':
                # Check if adaptive transition is in continuous mode
                behavior = self._get_behavior(t)
                if behavior and hasattr(behavior, 'get_current_mode'):
                    current_mode = behavior.get_current_mode()
                    # If mode not yet determined (None), call _select_mode() to determine it
                    if current_mode is None and hasattr(behavior, '_select_mode'):
                        current_mode = behavior._select_mode()
                    if current_mode == 'continuous':
                        continuous_transitions.append(t)
                elif behavior:
                    # No current_mode cached - determine mode now
                    from shypn.engine.adaptive_hybrid_behavior import AdaptiveHybridBehavior
                    if isinstance(behavior, AdaptiveHybridBehavior):
                        mode = behavior._select_mode()  # Returns mode string
                        if mode == 'continuous':
                            continuous_transitions.append(t)
        
        # DIAGNOSTIC: Log continuous phase
        adaptive_in_continuous = [t.name for t in continuous_transitions if t.transition_type == 'adaptive']
        
        continuous_enabled = []
        for transition in continuous_transitions:
            behavior = self._get_behavior(transition)
            can_flow, reason = behavior.can_fire()
            if can_flow:
                input_arcs = behavior.get_input_arcs()
                output_arcs = behavior.get_output_arcs()
                continuous_enabled.append((transition, behavior, input_arcs, output_arcs))
        
        # Apply conflict resolution for continuous transitions
        # Check if any continuous transitions share input places (conflict)
        continuous_to_integrate = self._resolve_continuous_conflicts(continuous_enabled)
        
        continuous_active = 0
        for transition, behavior, input_arcs, output_arcs in continuous_to_integrate:
            success, details = behavior.integrate_step(dt=time_step, input_arcs=input_arcs, output_arcs=output_arcs)
            if success:
                continuous_active += 1
                
                # Increment firing count for continuous transitions (for statistics/tables)
                # Firing count represents the amount of "reaction" that occurred
                # Use the rate from the integration step
                if details and 'rate' in details:
                    # Rate is the propensity/speed of the transition
                    # Firing count increment = rate × dt
                    transition.firing_count += abs(details['rate']) * time_step
                else:
                    # Fallback: evaluate rate directly
                    rate = behavior.evaluate_rate({p.id: p for p in self.model.places}, self.time)
                    transition.firing_count += abs(rate) * time_step
                
                if self.data_collector is not None and hasattr(self.data_collector, 'on_transition_fired'):
                    self.data_collector.on_transition_fired(transition, self.time, details)
                
                # PHASE 1-2 FIX: Also notify step listeners if they have on_transition_fired
                if not hasattr(self, '_debug_continuous_printed'):
                    self._debug_continuous_printed = True
                    # print(f"[FIRE_NOTIFY] Continuous: {transition.id}, notifying {len(self.step_listeners)} listeners")
                    for i, listener in enumerate(self.step_listeners):
                        # Check if listener is a bound method with __self__
                        listener_obj = listener.__self__ if hasattr(listener, '__self__') else listener
                        if hasattr(listener_obj, 'on_transition_fired'):
                            listener_obj.on_transition_fired(transition, self.time, details)
                else:
                    for listener in self.step_listeners:
                        listener_obj = listener.__self__ if hasattr(listener, '__self__') else listener
                        if hasattr(listener_obj, 'on_transition_fired'):
                            listener_obj.on_transition_fired(transition, self.time, details)
        
        # NOTE: Time advancement moved to AFTER stochastic phase (see below)
        # to prevent double advancement when tau-leaping is used
        
        # Update enablement states at current time
        self._update_enablement_states()
        
        # Handle timed and stochastic transitions with PRIORITY RULE:
        # Timed (deterministic) has PRIORITY over Stochastic (probabilistic)
        # Only fire stochastic if NO timed transitions can fire
        discrete_fired = False
        
        # Phase 2a: Timed transitions (DETERMINISTIC - PRIORITY)
        timed_transitions = [t for t in self.model.transitions if t.transition_type == 'timed']
        enabled_timed = [t for t in timed_transitions if self._is_transition_enabled(t)]
        
        if enabled_timed:
            pass
            # Select and fire one timed transition (may have conflicts among timed)
            transition = self._select_transition(enabled_timed)
            self._fire_transition(transition)
            discrete_fired = True
            self._update_enablement_states()  # Update after firing
        
        # Phase 2b: Stochastic transitions (PROBABILISTIC - LOWER PRIORITY)
        # Execute if NO timed transitions fired (timed has priority)
        # NOTE: Stochastic CAN fire alongside continuous (they operate on different time scales)
        # NOTE: Include adaptive transitions here - they may be in stochastic mode
        if not discrete_fired:  # Only if no timed fired
            stochastic_transitions = [t for t in self.model.transitions 
                                     if t.transition_type in ('stochastic', 'adaptive')]
            
            # For tau-leaping: Check structural enabling only (sufficient tokens)
            # Don't use can_fire() which requires scheduled fire time (only for exact SSA)
            enabled_stochastic = []
            for t in stochastic_transitions:
                behavior = self._get_behavior(t)
                # Check structural enabling: sufficient tokens for input arcs
                structurally_enabled = True
                input_arcs = behavior.get_input_arcs()
                for arc in input_arcs:
                    # Skip non-consuming arcs (test/inhibitor arcs)
                    kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                    arc_type = getattr(arc, 'arc_type', 'normal')
                    if kind != 'normal' or arc_type in ('inhibitor', 'test'):
                        continue
                    source_place = arc.source
                    if source_place and source_place.tokens < arc.weight:
                        structurally_enabled = False
                        break
                if structurally_enabled:
                    enabled_stochastic.append(t)
            
            # Debug output (can be enabled for troubleshooting)
            # print(f"[STOCHASTIC_PHASE] Found {len(stochastic_transitions)} stochastic, {len(enabled_stochastic)} enabled")
            
            if enabled_stochastic:
                # ALWAYS use τ-leaping for stochastic simulation (10-100× faster than exact SSA)
                # This is the correct stochastic engine for:
                # 1. Pure stochastic models (faster than Gillespie SSA)
                # 2. Hybrid models (enables continuous+stochastic concurrency)
                # 3. Parallel stochastic execution (foundation for weak independence scheduling)
                if True:  # τ-leaping is always enabled (use_parallel_stochastic controls parallelism)
                    # Use τ-leaping approximate simulation
                    from .tau_leaping import TauLeapingEngine
                    
                    if not hasattr(self, '_tau_leaping_engine'):
                        self._tau_leaping_engine = TauLeapingEngine(
                            epsilon=self.settings.tau_epsilon,
                            critical_threshold=self.settings.critical_threshold,
                            max_tau=self.settings.max_tau,
                            seed=None,  # Use default random seed
                            use_parallel=self.settings.use_parallel_stochastic,
                            verbose=self.verbose  # Pass verbose flag to suppress warnings
                        )
                        self._tau_leaping_engine.leap_selector.min_tau = self.settings.min_tau
                        # Config printed once at initialization (commented out for cleaner output)
                        # print(f"🔧 τ-leaping config: epsilon={self.settings.tau_epsilon}, max_tau={self.settings.max_tau}, min_tau={self.settings.min_tau}")
                    
                    # Debug: Print propensities before τ-leaping (commented out - working correctly)
                    # if not hasattr(self, '_tau_debug_count'):
                    #     self._tau_debug_count = 0
                    # 
                    # if self._tau_debug_count < 3:
                    #     self._tau_debug_count += 1
                    #     print(f"\n🔬 τ-leaping attempt {self._tau_debug_count} at t={self.time:.3f}:")
                    #     for t in enabled_stochastic:
                    #         behavior = self._get_behavior(t)
                    #         try:
                    #             prop = behavior._evaluate_rate_at_enablement(self.time)
                    #             print(f"   {t.name}: propensity={prop:.6f}")
                    #         except:
                    #             print(f"   {t.name}: propensity=ERROR")
                    #     print(f"   time_step={time_step}")
                    
                    # Execute τ-leaping step
                    # For hybrid models (stochastic + continuous/deterministic), clamp tau to dt
                    # For pure stochastic models, let tau-leaping control its own time step
                    is_pure_stochastic = all(
                        t.transition_type in ('stochastic', 'adaptive')
                        for t in self.model.transitions 
                        if hasattr(t, 'transition_type')
                    )
                    
                    # DIAGNOSTIC: Log hybrid detection
                    if is_pure_stochastic:
                        # Pure stochastic: tau-leaping controls time stepping
                        # Temporarily disable time advancement in tau-leaping (we'll handle it)
                        # No wait - for pure stochastic, tau-leaping SHOULD advance time
                        self._tau_leaping_engine.execute_step(self)
                        # Flag that time was already advanced by tau-leaping
                        tau_leaping_advanced_time = True
                    else:
                        # Hybrid model: clamp tau to dt to stay synchronized
                        original_max_tau = self._tau_leaping_engine.leap_selector.max_tau
                        # CRITICAL: Force tau = time_step for hybrid models to ensure
                        # continuous and stochastic operate over same time interval
                        self._tau_leaping_engine.leap_selector.max_tau = time_step
                        self._tau_leaping_engine.leap_selector.min_tau = time_step
                        
                        # CRITICAL: Temporarily prevent tau-leaping from advancing time
                        # For hybrid models, controller must be single source of time advancement
                        self._tau_leaping_engine._advance_time = False
                        self._tau_leaping_engine.execute_step(self)
                        self._tau_leaping_engine._advance_time = True
                        
                        # Restore original tau bounds
                        self._tau_leaping_engine.leap_selector.max_tau = original_max_tau
                        self._tau_leaping_engine.leap_selector.min_tau = self.settings.min_tau
                        # Hybrid models: controller will advance time by time_step
                        tau_leaping_advanced_time = False
                    
                    discrete_fired = True
                else:
                    # Pure stochastic model: Use exact SSA (can advance time freely)
                    # Find transition with earliest scheduled fire time
                    next_transition = None
                    next_fire_time = float('inf')
                    
                    for transition in enabled_stochastic:
                        behavior = self._get_behavior(transition)
                        fire_time = behavior.get_scheduled_fire_time()
                        if fire_time is not None and fire_time < next_fire_time:
                            next_fire_time = fire_time
                            next_transition = transition
                    
                    if next_transition and next_fire_time < float('inf'):
                        # Advance time to next firing (only safe in pure stochastic models)
                        self.time = next_fire_time
                        
                        # Fire the transition
                        self._fire_transition(next_transition)
                        discrete_fired = True
        
        # CRITICAL: Advance time AFTER stochastic phase
        # Skip if tau-leaping already advanced time (pure stochastic models)
        if not tau_leaping_advanced_time:
            self.time += time_step
        
        # Week 1 - Phase 4: Emit progress event for UI updates
        self._emit_progress_event()
        
        # === CONSERVATION ENFORCEMENT DISABLED ===
        # Conservation must emerge naturally from Petri net arc connections.
        # Test arcs, inhibitor arcs, and other non-consuming arcs change the
        # expected mass balance. Artificial token adjustments violate formalism.
        # Tokens should only flow through place→transition→place connections.
        # 
        # if self.conservation_enforcer and self.conservation_enforcer.conservation_groups:
        #     violations = self.conservation_enforcer.verify_and_correct()
        #     if violations and self.verbose:
        #         # Log only first few violations to avoid spam
        #         if not hasattr(self, '_conservation_violation_count'):
        #             self._conservation_violation_count = 0
        #         if self._conservation_violation_count < 5:
        #             for v in violations:
        #                 import logging
        #                 logging.getLogger(__name__).info(
        #                     f"Conservation correction '{v['group']}': "
        #                     f"{v['error']:.6f} error ({v['percent']:.3f}%)"
        #                 )
        #             self._conservation_violation_count += 1
        
        # Record state after time advancement
        if self.data_collector:
            self.data_collector.record_state(self.time)
        
        # Update thermodynamic validators
        if self.validator_manager and len(self.validator_manager) > 0:
            places_dict = {p.id: p for p in self.model.places}
            transitions_dict = {t.id: t for t in self.model.transitions}
            self.validator_manager.update(self.time, places_dict, transitions_dict)
        
        self._notify_step_listeners()
        
        # Check if simulation is complete (duration reached)
        if self.is_simulation_complete():
            import logging
            logging.getLogger(__name__).info(f"[SIMULATION] Duration reached: time={self.time}, duration={self.settings.duration}")
            return False  # Simulation complete
        
        # CRITICAL FIX: Always return True if simulation NOT complete
        # Even if no transitions fired this step, we need to continue
        # stepping until duration is reached to collect full trajectory data
        # 
        # Previous logic would return False when no transitions could fire,
        # causing premature simulation termination with only 1-2 data points
        return True

    def _find_enabled_transitions(self) -> List:
        """Find all transitions that are enabled (can fire).
        
        REFACTORED (Phase 2.3.2): Delegates to ViabilityChecker.
        
        A transition is enabled if all its input places have enough tokens
        to satisfy the arc weights.
        
        Returns:
            List of enabled Transition objects
        """
        return self._viability_checker.get_enabled_transitions()
    
    # ==================== Transition State Management ====================

    def _is_transition_enabled(self, transition) -> bool:
        """Check if a specific transition is enabled using behavior dispatch.
        
        REFACTORED (Phase 2.3.2): Delegates to ViabilityChecker.
        
        Uses the transition's behavior to determine if it can fire based on
        locality (input places and arc weights only).
        
        Args:
            transition: Transition object to check
            
        Returns:
            bool: True if transition can fire, False otherwise
        """
        return self._viability_checker.is_enabled(transition)

    def _fire_transition(self, transition):
        """Fire a transition using behavior dispatch.
        
        Uses the transition's behavior to perform the firing, which handles
        token removal/addition based on locality (input/output arcs).
        
        Args:
            transition: Transition object to fire
        """
        # Token accounting: snapshot before firing
        if self.auditor is not None:
            try:
                self.auditor.snapshot_before_fire(transition, self.time)
            except Exception as e:
                print(f"⚠️ Accounting error (before fire): {e}")
        
        behavior = self._get_behavior(transition)
        input_arcs = behavior.get_input_arcs()
        output_arcs = behavior.get_output_arcs()
        success, details = behavior.fire(input_arcs, output_arcs)
        
        # Token accounting: snapshot after firing and validate
        if self.auditor is not None and success:
            try:
                consumed = behavior.get_last_consumed()
                produced = behavior.get_last_produced()
                self.auditor.snapshot_after_fire(transition, self.time, consumed, produced)
            except Exception as e:
                print(f"⚠️ Accounting error (after fire): {e}")
                import traceback
                traceback.print_exc()
        
        if success:
            # Increment firing count for statistics
            transition.firing_count += 1
            
            # Notify console when stochastic transitions fire (first 10 times)
            if transition.transition_type == 'stochastic' and transition.firing_count <= 10:
                print(f"🔥 Stochastic {transition.name} fired at t={self.time:.3f} (count={transition.firing_count})")
            
            state = self._get_or_create_state(transition)
            state.enablement_time = None
            state.scheduled_time = None
        if self.data_collector is not None and hasattr(self.data_collector, 'on_transition_fired'):
            self.data_collector.on_transition_fired(transition, self.time, details)
        
        # PHASE 1-2 FIX: Also notify step listeners if they have on_transition_fired
        if not hasattr(self, '_debug_listeners_printed'):
            self._debug_listeners_printed = True
            # print(f"[FIRE_NOTIFY] Discrete: {transition.id}, notifying {len(self.step_listeners)} listeners")
            for i, listener in enumerate(self.step_listeners):
                # Check if listener is a bound method with __self__
                listener_obj = listener.__self__ if hasattr(listener, '__self__') else listener
                if hasattr(listener_obj, 'on_transition_fired'):
                    listener_obj.on_transition_fired(transition, self.time, details)
        else:
            for listener in self.step_listeners:
                listener_obj = listener.__self__ if hasattr(listener, '__self__') else listener
                if hasattr(listener_obj, 'on_transition_fired'):
                    listener_obj.on_transition_fired(transition, self.time, details)

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
                pass
                # Check if they share places
                if not self._are_independent(t1, t2):
                    pass
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
            pass
            # Start new group with first remaining transition
            current_id = next(iter(remaining))
            current_group = [transitions_by_id[current_id]]
            remaining.remove(current_id)
            
            # Try to add non-conflicting transitions to this group
            to_check = list(remaining)
            for tid in to_check:
                pass
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
            pass
            # Check if t is independent of ALL transitions in current set
            can_add = True
            for tid in maximal_set_ids:
                if t.id in conflict_sets[tid]:
                    pass
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
                    pass
                    # Conflict found - cannot add this transition
                    can_add = False
                    break
            
            if can_add:
                pass
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
            pass
            # Maximize parallelism - choose set with most transitions
            return max(maximal_sets, key=len)
        
        elif strategy == 'priority':
            pass
            # Maximize sum of priorities
            def total_priority(tset):
                return sum(getattr(t, 'priority', 0) for t in tset)
            return max(maximal_sets, key=total_priority)
        
        elif strategy == 'random':
            pass
            # Random for exploration
            return random.choice(maximal_sets)
        
        elif strategy == 'first':
            pass
            # Deterministic (natural order from Phase 2)
            return maximal_sets[0]
        
        else:
            pass
            # Unknown strategy - fall back to first
            return maximal_sets[0]

    def _validate_all_can_fire(self, transition_set: List) -> bool:
        """
        Check if all transitions in set are currently enabled.
        
        REFACTORED (Phase 2.3.2): Delegates to ViabilityChecker.
        
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
        return self._viability_checker.validate_all(transition_set)

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
            pass
            # PHASE 3: COMMIT (execute atomically)
            fired = []
            
            # Sort by priority for deterministic execution order
            sorted_transitions = sorted(
                transition_set, 
                key=lambda t: (getattr(t, 'priority', 0), t.id), 
                reverse=True
            )
            
            # Import arc types for proper handling
            from shypn.netobjs.inhibitor_arc import InhibitorArc
            from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
            from shypn.netobjs.test_arc import TestArc
            
            for transition in sorted_transitions:
                pass
                # Remove input tokens
                for arc in self.model.arcs:
                    if arc.target == transition:
                        pass
                        # Input arc (place → transition)
                        place = arc.source
                        
                        # Skip arcs that don't consume tokens using defensive pattern
                        kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                        arc_type = getattr(arc, 'arc_type', 'normal')
                        if kind != 'normal' or arc_type in ('inhibitor', 'test'):
                            continue  # Inhibitor and test arcs NEVER consume tokens
                        
                        # CRITICAL: ALWAYS use weight for consumption (NOT threshold!)
                        # Threshold is for enablement only, weight is for token transfer
                        tokens_consumed = getattr(arc, 'weight', 1)
                        
                        # Safety check (should not fail after validation)
                        if place.tokens < tokens_consumed:
                            raise RuntimeError(
                                f"{transition.id} cannot fire: {place.id} has "
                                f"{place.tokens} < {tokens_consumed} tokens"
                            )
                        
                        place.tokens -= tokens_consumed
                
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
                        pass
                        # Output arc (transition → place)
                        place = arc.target
                        tokens_produced = getattr(arc, 'weight', 1)
                        place.tokens += tokens_produced
                
                fired.append(transition)
            
            # SUCCESS: All transitions fired
            return (True, fired, "")
            
        except Exception as e:
            pass
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
            pass
            # Fire transition that was enabled earliest (smallest enablement time)
            return min(enabled_transitions, 
                      key=lambda t: self.transition_states[t.id].enablement_time if t.id in self.transition_states and self.transition_states[t.id].enablement_time is not None else float('inf'))
        
        elif policy == 'latest':
            pass
            # Fire transition that was enabled most recently (largest enablement time)
            return max(enabled_transitions,
                      key=lambda t: self.transition_states[t.id].enablement_time if t.id in self.transition_states and self.transition_states[t.id].enablement_time is not None else 0)
        
        elif policy == 'priority':
            pass
            # Fire highest priority transition
            return max(enabled_transitions, key=lambda t: getattr(t, 'priority', 0))
        
        elif policy == 'race':
            pass
            # Mass action kinetics - exponential race condition
            # Sample exponential delay for each, select minimum
            import numpy as np
            min_delay = float('inf')
            selected = None
            for t in enabled_transitions:
                pass
                # Use transition rate if available, otherwise default to 1.0
                # Handle legacy case where rate might be a string (should be rate_function)
                try:
                    rate_value = getattr(t, 'rate', 1.0)
                    if isinstance(rate_value, str):
                        # Legacy: rate was mistakenly set to rate_function string
                        rate = 1.0  # Use default
                    else:
                        rate = float(rate_value) if rate_value else 1.0
                except (ValueError, TypeError):
                    rate = 1.0
                
                if rate > 0:
                    delay = np.random.exponential(1.0 / rate)
                    if delay < min_delay:
                        min_delay = delay
                        selected = t
            return selected if selected else random.choice(enabled_transitions)
        
        elif policy == 'age':
            pass
            # FIFO - transition enabled longest fires first
            return min(enabled_transitions,
                      key=lambda t: self.transition_states[t.id].enablement_time if t.id in self.transition_states and self.transition_states[t.id].enablement_time is not None else float('inf'))
        
        elif policy == 'random':
            pass
            # Uniform random selection
            return random.choice(enabled_transitions)
        
        elif policy == 'preemptive-priority':
            pass
            # For now, treat same as priority (full preemption requires interrupt mechanism)
            # TODO: Implement preemption of running lower-priority transitions
            return max(enabled_transitions, key=lambda t: getattr(t, 'priority', 0))
        
        else:
            pass
            # Unknown policy - default to random
            return random.choice(enabled_transitions)

    def _resolve_continuous_conflicts(self, continuous_enabled: List) -> List:
        """Apply conflict resolution for continuous transitions using weak independence theory.
        
        Implements the refined locality theory from dependency_coupling.py:
        - **Competitive (True Conflict)**: Shared places via CONSUMING arcs → Sequential execution
        - **Regulatory (Valid Coupling)**: Shared places via TEST ARCS (read-only) → Parallel execution OK
        
        Test arcs (catalysts/enzymes) don't consume tokens, so multiple transitions can
        share the same catalyst without conflict. This is correct biological behavior:
        "Same enzyme catalyzes multiple reactions."
        
        Strategy:
        1. Identify conflict groups (transitions sharing input places via CONSUMING arcs)
        2. For each conflict group, apply firing policy to select winner(s)
        3. Non-conflicting and regulatory-coupled transitions fire in parallel
        
        Args:
            continuous_enabled: List of (transition, behavior, input_arcs, output_arcs) tuples
            
        Returns:
            List of (transition, behavior, input_arcs, output_arcs) tuples to integrate
        
        See also:
            - topology/biological/dependency_coupling.py: Weak independence theory
            - doc/foundation/BIOLOGICAL_PETRI_NET_FORMALIZATION.md: Section 3.1
        """
        if len(continuous_enabled) <= 1:
            return continuous_enabled
        
        # Build map of input places to transitions
        place_to_transitions = {}
        transition_data = {}  # Store full tuple data for each transition
        
        for trans_tuple in continuous_enabled:
            transition, behavior, input_arcs, output_arcs = trans_tuple
            transition_data[transition.id] = trans_tuple
            
            # Get input places for this transition (only consuming arcs)
            # Test arcs (catalysts) don't create conflicts → weak independence theory
            input_places = set()
            for arc in input_arcs:
                if hasattr(arc, 'source_id'):
                    # Skip non-consuming arcs (test arcs are read-only)
                    kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                    arc_type = getattr(arc, 'arc_type', 'normal')
                    if kind != 'normal' or arc_type in ('inhibitor', 'test'):
                        # Test arcs don't create conflicts → weak independence theory
                        continue
                    # Only consuming arcs create true conflicts (competitive coupling)
                    input_places.add(arc.source_id)
            
            # Map places to transitions
            for place_id in input_places:
                if place_id not in place_to_transitions:
                    place_to_transitions[place_id] = []
                place_to_transitions[place_id].append(transition)
        
        # Find conflict groups (transitions sharing at least one input place)
        conflict_groups = []
        processed = set()
        
        for transition, _, _, _ in continuous_enabled:
            if transition.id in processed:
                continue
                
            # Find all transitions that share places with this one
            conflict_group = {transition}
            to_check = [transition]
            
            while to_check:
                current = to_check.pop()
                processed.add(current.id)
                
                # Get input places for current transition
                current_tuple = transition_data[current.id]
                _, _, input_arcs, _ = current_tuple
                
                for arc in input_arcs:
                    if hasattr(arc, 'source_id'):
                        place_id = arc.source_id
                        if place_id in place_to_transitions:
                            for conflicting in place_to_transitions[place_id]:
                                if conflicting.id not in processed:
                                    conflict_group.add(conflicting)
                                    to_check.append(conflicting)
                                    processed.add(conflicting.id)
            
            if len(conflict_group) > 1:
                conflict_groups.append(list(conflict_group))
        
        # Apply conflict resolution
        selected = []
        conflicting_ids = set()
        
        for group in conflict_groups:
            if len(group) > 1:
                # Apply _select_transition to resolve conflict
                winner = self._select_transition(group)
                selected.append(transition_data[winner.id])
                conflicting_ids.update(t.id for t in group)
        
        # Add non-conflicting transitions (parallel execution)
        for trans_tuple in continuous_enabled:
            transition = trans_tuple[0]
            if transition.id not in conflicting_ids:
                selected.append(trans_tuple)
        
        return selected
    
    # ==================== Continuous Execution (Run Mode) ====================
    # REFACTORED (Phase 2.3.1): Extracted to ContinuousExecutor strategy class
    # Original implementation: ~250 lines
    # New implementation: Thin delegation layer (maintains backward compatibility)
    # Benefits: Strategy pattern for alternative executors (parallel, distributed)
    #           Testable execution logic in isolation
    #           Clear separation of concerns

    def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
        """Start continuous simulation execution.
        
        REFACTORED (Phase 2.3.1): Delegates to ContinuousExecutor strategy.
        
        Runs the simulation continuously using GLib timeout callbacks.
        Can be stopped by calling stop().
        
        Args:
            time_step: Time increment per step (None = use effective dt from settings)
            max_steps: Maximum number of steps to run (None = use duration-based or unlimited)
        
        Returns:
            bool: True if started successfully, False if already running
        """
        return self._continuous_executor.run(time_step, max_steps)

    def _simulation_loop(self) -> bool:
        """Internal simulation loop callback.
        
        REFACTORED (Phase 2.3.1): Delegates to ContinuousExecutor strategy.
        
        Executes multiple simulation steps per GUI update for smooth animation
        at all time scales. For very small time steps (e.g., 2ms), this batches
        many steps together to avoid choppy visualization.
        
        Returns:
            bool: True to continue, False to stop the timeout
        """
        return self._continuous_executor._simulation_loop()

    def stop(self):
        """Stop the continuous simulation.
        
        REFACTORED (Phase 2.3.1): Delegates to ContinuousExecutor strategy.
        
        This requests the simulation to stop. The actual stop will occur
        after the current step completes.
        
        IMPORTANT: This clears enablement states so that when Run is pressed
        again, transitions start fresh with enablement time = current time.
        """
        self._continuous_executor.stop()

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
        
        # Clear thermodynamic validation results
        self.thermodynamic_results = None
        
        # Reset firing counts for all transitions
        for transition in self.model.transitions:
            transition.reset_firing_count()
        
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
        
        # PHASE 1-2 FIX: Preserve callback before recreating data collector
        # The Report Panel's on_simulation_complete callback must survive controller reset
        saved_callback = self.on_simulation_complete
        
        # Recreate data collector with new model
        from shypn.engine.simulation.data_collector import DataCollector
        from shypn.core.value_objects import RecordingConfig
        
        # Create RecordingConfig from current settings
        config = RecordingConfig(
            recorded_objects=self.settings.recorded_objects if hasattr(self.settings, 'recorded_objects') else None
        )
        
        self.data_collector = DataCollector(
            new_model, 
            controller=self,
            config=config
        )
        
        # CRITICAL: Notify any observers that data_collector changed
        # This ensures analyses panels get the new data_collector reference
        if hasattr(self, '_on_data_collector_changed'):
            try:
                self._on_data_collector_changed(self.data_collector)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error notifying data_collector change: {e}")
        
        # PHASE 1-2 FIX: Restore callback after recreating data collector
        self.on_simulation_complete = saved_callback
        if saved_callback:
            pass
            # print(f"[RESET_MODEL] ✅ Preserved on_simulation_complete callback")
        
        # Reset data collector if exists (legacy compatibility)
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