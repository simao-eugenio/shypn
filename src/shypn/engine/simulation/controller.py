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
import logging
import math
import random
import threading
import traceback
from typing import Callable, cast, List, Optional, Dict, Tuple, Any, Set
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
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.place import Place
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
from shypn.utils.threshold_evaluator import ThresholdEvaluator
from shypn.engine.simulation.abstract_controller import AbstractSimulationController


class TimescaleMismatchError(RuntimeError):
    """TMD-1: raised when ``RecordingConfig.timescale_check == "error"``
    and the init-time audit found at least one transition with
    ``τ < safety_factor · dt``.

    See ``checkers/timescale_auditor.py`` for codes C20/C21/C22.
    """


class TransitionState:
    """Per-transition state tracking for time-aware behaviors.
    
    Tracks when transitions become enabled/disabled and scheduled firing times
    for stochastic transitions.
    
    Attributes:
        enablement_time: Time when transition became structurally enabled (None if disabled)
        scheduled_time: Scheduled firing time for stochastic transitions (None if not scheduled)
    """

    def __init__(self) -> None:
        """Initialize transition state."""
        self.enablement_time: Optional[float] = None
        self.scheduled_time: Optional[float] = None

class ModelAdapter:
    """Adapter to provide dict-like interface for behavior classes.
    
    The behavior classes expect model.places, model.arcs, etc. to be
    dictionaries keyed by ID. This adapter wraps the ModelCanvasManager
    (which uses lists) to provide that interface.
    """

    def __init__(self, canvas_manager: Any, controller: Any=None):
        """Initialize adapter with canvas manager.
        
        Args:
            canvas_manager: ModelCanvasManager instance
            controller: SimulationController instance (for accessing logical_time)
        """
        self.canvas_manager = canvas_manager
        self._controller = controller
        self._places_dict: Optional[Dict[Any, Any]] = None
        self._transitions_dict: Optional[Dict[Any, Any]] = None
        self._arcs_dict: Optional[Dict[Any, Any]] = None

    @property
    def places(self) -> Dict[Any, Any]:
        """Get places as dictionary keyed by ID."""
        if self._places_dict is None:
            self._places_dict = {p.id: p for p in self.canvas_manager.places}
        return self._places_dict

    @property
    def transitions(self) -> Dict[Any, Any]:
        """Get transitions as dictionary keyed by ID."""
        if self._transitions_dict is None:
            self._transitions_dict = {t.id: t for t in self.canvas_manager.transitions}
        return self._transitions_dict

    @property
    def arcs(self) -> Dict[Any, Any]:
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
    def logical_time(self) -> float:
        """Get current logical time from controller.
        
        Returns:
            float: Current simulation time from controller, or 0.0 if no controller
        """
        if self._controller is not None:
            return float(self._controller.time)
        return 0.0

    @property
    def thermodynamic_settings(self) -> Dict[str, Any]:
        """Get thermodynamic settings from canvas manager.
        
        Returns:
            dict: Thermodynamic settings (T, pH, ionic_strength, etc.) or defaults
        """
        if hasattr(self.canvas_manager, 'thermodynamic_settings'):
            return cast(Dict[str, Any], self.canvas_manager.thermodynamic_settings)
        # Return defaults if not available
        return {
            'temperature': 298.15,
            'ph': 7.0,
            'ionic_strength': 0.1
        }

    def invalidate_caches(self) -> None:
        """Invalidate dict caches (call when model structure changes)."""
        self._places_dict = None
        self._transitions_dict = None
        self._arcs_dict = None

# ==================== Model Accessors (Property Proxies) ====================

class SimulationController(AbstractSimulationController):  # type: ignore[misc]
    """Controller for Petri net simulation execution.  Sprint 23: implements AbstractSimulationController.
    
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

    def __init__(self, model: Any, document_id: int = 0, verbose: bool = True, recording_config: Optional[Any] = None, data_collector_factory: Any=None, viability_checker_factory: Any=None):
        """Initialize the simulation controller.
        
        REFACTORED: Now uses RecordingConfig value object (reduced from 4 parameters to 2).
        
        Args:
            model: ModelCanvasManager instance (has places, transitions, arcs lists)
            verbose: If True, print debug output (disable for batch mode performance)
            recording_config: RecordingConfig for data collection (default: 20 Hz time-based, all objects)
            data_collector_factory: Optional callable(model, controller, config) -> DataCollector.
                Inject a custom factory for testing or subclassing. Default: DataCollector.
            viability_checker_factory: Optional callable(controller) -> ViabilityChecker.
                Inject a custom factory for testing or subclassing. Default: ViabilityChecker.
        """
        if recording_config is None:
            from shypn.core.value_objects import RecordingConfig
            recording_config = RecordingConfig.default()
        
        self.model = model
        self.time = 0.0
        self.model_adapter = ModelAdapter(model, controller=self)
        self.step_listeners: List[Any] = []
        self.data_collector_listeners: List[Callable[..., Any]] = []  # notified when data_collector is replaced
        self._running = False
        self._stop_requested = False
        self._timeout_id = None
        self.behavior_cache: Dict[Any, Any] = {}
        self.transition_states: Dict[Any, Any] = {}
        self.conflict_policy = DEFAULT_POLICY
        self._round_robin_index = 0
        self.verbose = verbose  # Control debug output
        # Dirty-place index: accelerates per-step enabled-transition scan (Finding #10)
        self._dirty_since_last_check: Set[str] = set()      # accumulated per-step in _fire_transition
        self._place_to_input_transitions: Dict[str, List[Any]] = {}  # place_id → [transitions]
        self._source_transitions: List[Any] = []            # transitions with no input places
        
        # Phase 4: Document ID for scoped event emissions (passed at construction)
        self.document_id: int = document_id
        
        # Data collection for simulation results
        from shypn.engine.simulation.data_collector import DataCollector
        
        # Create settings first so we can access recorded_objects
        from shypn.engine.simulation.settings import SimulationSettings
        self.settings = SimulationSettings()
        
        # Create DataCollector with RecordingConfig (injectable for testing)
        _dc_factory = data_collector_factory or DataCollector
        self.data_collector = _dc_factory(model, controller=self, config=recording_config)
        
        # Callback for simulation complete event
        # Use private attribute with property to trace all assignments
        self._on_simulation_complete = None
        
        # === NEW: Mode elimination architecture ===
        # State detection replaces explicit mode checks
        from shypn.engine.simulation.state import SimulationStateDetector
        self.state_detector = SimulationStateDetector(self)
        
        # Buffered settings for atomic parameter updates
        from shypn.engine.simulation.buffered import BufferedSimulationSettings
        # Pass model's document for settings persistence (settings saved next to .shy file)
        document_model = getattr(model, 'document', None) or getattr(model, '_document_model', None)
        self.buffered_settings = BufferedSimulationSettings(self.settings, model=document_model)
        
        # Interaction guard for permission-based UI control
        from shypn.ui.interaction import InteractionGuard
        self.interaction_guard = InteractionGuard(self.state_detector)
        
        # Thermodynamic validation results (populated on demand)
        self.thermodynamic_results: Optional[Dict[str, Any]] = None
        
        # Option 3: Assignment rule re-evaluation support
        self.enable_assignment_rule_reevaluation = False
        self.pathway_data = None  # Store for assignment rule initialization
        
        # Token accounting auditor (conservation validation)
        self.auditor: Optional[Any] = None  # Initialized when enabled via settings
        
        # Thermodynamic validator manager (Feb 9, 2026)
        from shypn.engine.simulation.validation import ValidatorManager
        self.validator_manager = ValidatorManager()
        
        # Continuous execution strategy (Phase 2.3.1 extraction)
        self._continuous_executor = ContinuousExecutor(self)

        # Viability checking strategy (Phase 2.3.2 extraction, injectable for testing)
        _vc_factory = viability_checker_factory or ViabilityChecker
        self._viability_checker = _vc_factory(self)
        
        # Phase 6 extraction: ConflictResolver manages maximal-step conflict logic
        from shypn.engine.simulation.conflict_resolver import ConflictResolver
        self._conflict_resolver = ConflictResolver(
            model=self.model,
            viability_checker=self._viability_checker,
            get_places_fn=self._get_all_places_for_transition,
        )
        
        # Week 4 - Phase 4: Strategy Pattern for simulation algorithms
        # Enables runtime switching between different execution strategies
        self._execution_strategy: Optional[Any] = None  # HybridStrategy by default (set on first use)
        
        # Register to observe model changes (for arc transformations, deletions, etc.)
        if hasattr(model, 'register_observer'):
            model.register_observer(self._on_model_changed)
        # Build place→transition index for incremental enablement checking
        self._rebuild_place_index()

        # Load-time structural audit (AGENT_RULES.md §8 — arc-type misuse).
        # Non-blocking: emits WARNING-level log entries only.
        try:
            from shypn.engine.simulation.checkers import audit_arc_types
            audit_arc_types(self.model)
        except Exception:  # pragma: no cover - audit must never break load
            logging.getLogger(__name__).debug(
                "arc_type audit skipped due to exception", exc_info=True
            )

        # TMD-1 init-time integration-step adequacy audit.
        # Non-blocking unless RecordingConfig.timescale_check == "error".
        # Last assessment is cached on ``self.last_timescale_profile`` for
        # the UI / sweep aggregator to surface.
        self.last_timescale_profile: Optional[Any] = None
        self._timescale_check_mode: str = getattr(
            recording_config, "timescale_check", "warn"
        )
        self._timescale_safety_factor: float = float(
            getattr(recording_config, "timescale_dt_safety_factor", 0.1)
        )
        try:
            self._run_timescale_audit()
        except Exception:  # pragma: no cover - audit must never break load
            logging.getLogger(__name__).debug(
                "timescale audit skipped due to exception", exc_info=True
            )
    
    # ==================== Lifecycle Management ====================
    
    def _run_timescale_audit(self) -> None:
        """TMD-1 init-time integration-step adequacy audit.

        Evaluates each continuous/adaptive transition's local timescale
        ``τ = M / (W · r(M₀))`` against the configured ``dt`` and emits
        warnings (or raises, depending on ``recording_config.timescale_check``)
        for transitions whose τ < ``safety_factor · dt``.

        The full TimescaleProfile is cached on
        ``self.last_timescale_profile`` for downstream consumers
        (UI panel, sweep summary, replicate engine_stats).

        Skipped silently when ``timescale_check == "off"``.

        See:
            * ``checkers/timescale_auditor.py`` for codes C20/C21/C22.
            * ``workspace/projects/canabidiol/docs/engine_time_and_stiffness.md``
              for the full TMD design and rationale.
        """
        if self._timescale_check_mode == "off":
            return

        # Resolve effective dt — settings.get_effective_dt() if available,
        # else fall back to the conservative default.
        try:
            dt = float(self.settings.get_effective_dt())
        except Exception:  # noqa: BLE001
            dt = 1.0
        if dt <= 0:
            return

        from shypn.engine.simulation.checkers import audit_timescales
        profile = audit_timescales(
            self.model, dt=dt, safety_factor=self._timescale_safety_factor
        )
        self.last_timescale_profile = profile

        # Emit a one-shot EventBus notification so the GUI status bar /
        # notification panel can surface a "⚠ TMD: N findings" badge
        # without having to poll the controller. Only emit when we have
        # a real document_id (GUI canvas path); skip for sweep / headless
        # controllers — they run on background threads and their findings
        # are surfaced via provenance.json + summary.csv instead.
        if self.document_id:
            try:
                EventBus.emit(
                    'simulation.timescale_audit',
                    {
                        'profile': profile.to_dict(),
                        'n_findings': len(profile.findings),
                        'critical_transitions': list(profile.critical_transitions),
                        'mode': self._timescale_check_mode,
                    },
                    document_id=self.document_id,
                )
            except Exception:  # pragma: no cover - never break load
                logging.getLogger(__name__).debug(
                    "EventBus emit for timescale_audit failed", exc_info=True
                )

        critical = profile.critical_transitions
        if not critical:
            return

        if self._timescale_check_mode == "error":
            tids = ", ".join(critical[:5]) + ("…" if len(critical) > 5 else "")
            raise TimescaleMismatchError(
                f"Timescale mismatch: {len(critical)} transition(s) "
                f"violate τ < {self._timescale_safety_factor} · dt "
                f"({tids}). Recommended dt ≤ {profile.recommended_dt:.3g}s. "
                f"See log for per-transition decision recipes."
            )

        # mode == "warn" (default): emit one summary RuntimeWarning so it
        # surfaces in `python -W error`/CI without spamming per-transition.
        # Per-transition messages are already logged by the auditor.
        import warnings
        warnings.warn(
            f"[TMD] Timescale mismatch: {len(critical)} transition(s) "
            f"violate τ < {self._timescale_safety_factor} · dt={dt:.3g}s. "
            f"Recommended dt ≤ {profile.recommended_dt:.3g}s. See log for "
            f"per-transition recipes.",
            RuntimeWarning,
            stacklevel=3,
        )

    def reset(self) -> None:
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
        logger = logging.getLogger(__name__)
        logger.info("Resetting SimulationController for new model load")
        
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
        
        # Reset per-run one-shot warning flags
        self._livelock_warned = False
        if hasattr(self, '_large_timestep_warned'):
            del self._large_timestep_warned
        
        # Clear thermodynamic validation results
        self.thermodynamic_results = None
        
        # Reset τ-leaping engine (if it exists)
        if hasattr(self, '_tau_leaping_engine'):
            delattr(self, '_tau_leaping_engine')

        # Reinitialize model adapter with current model
        self.model_adapter = ModelAdapter(self.model, controller=self)
        # Reset dirty-place state and rebuild place-transition index for new model
        self._dirty_since_last_check = set()
        self._rebuild_place_index()
        
        # Reinitialize data collector with current model
        from shypn.engine.simulation.data_collector import DataCollector
        from shypn.core.value_objects import RecordingConfig
        
        config = RecordingConfig(
            recorded_objects=self.settings.recorded_objects if hasattr(self.settings, 'recorded_objects') else None
        )
        self.data_collector = DataCollector(self.model, controller=self, config=config)
        
        # CRITICAL: Notify any observers that data_collector changed
        # This ensures analyses panels get the new data_collector reference
        for _cb in self.data_collector_listeners:
            try:
                _cb(self.data_collector)
            except Exception as e:
                logger.warning(f"Error in data_collector listener: {e}")
        
        # Reset buffered settings (discard any uncommitted changes from previous model)
        if hasattr(self, 'buffered_settings'):
            self.buffered_settings.rollback()
        
        logger.info("SimulationController reset complete - ready for new model")
    
    @property
    def on_simulation_complete(self) -> Optional[Any]:
        """Callback invoked when simulation completes."""
        return self._on_simulation_complete
    
    @on_simulation_complete.setter
    def on_simulation_complete(self, value: Any) -> None:
        """Set simulation complete callback."""
        self._on_simulation_complete = value
    
    def validate_thermodynamics(self) -> Optional[Dict[str, Any]]:
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
        except (AttributeError, ValueError, KeyError, TypeError) as e:
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

    def _on_model_changed(self, event_type: str, obj: Any, old_value: Any=None, new_value: Any=None) -> None:
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
        if event_type == 'deleted':
            pass
            # If a transition was deleted, remove it from our caches
            if isinstance(obj, Transition):
                self.behavior_cache.pop(id(obj), None)
                self.transition_states.pop(id(obj), None)
            
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
                if isinstance(obj.source, Transition):
                    self.behavior_cache.pop(id(obj.source), None)
                if isinstance(obj.target, Transition):
                    self.behavior_cache.pop(id(obj.target), None)
                
                pass  # Behaviors rebuilt for affected transitions
        
        elif event_type == 'created':
            # New object created (place, transition, or arc)
            # Invalidate model adapter caches to include the new object
            if isinstance(obj, (Place, Transition, Arc)):
                self.model_adapter.invalidate_caches()
            
            # If a new transition was created, initialize its state and enablement
            if isinstance(obj, Transition):
                state = self._get_or_create_state(obj)
                
                # Immediately update enablement for the new transition
                # This ensures source transitions are immediately ready to fire
                behavior = self._get_behavior(obj)
                is_source = getattr(obj, 'is_source', False)
                
                if is_source:
                    logger = logging.getLogger(__name__)
                    logger.info(f"[OBSERVER] ✅ Enabling source transition {obj.id} at t={self.time}")
                    # Source transitions are always enabled
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
                        state.enablement_time = self.time
                        if hasattr(behavior, 'set_enablement_time'):
                            behavior.set_enablement_time(self.time)
        
        elif event_type == 'modified':
            # Object properties were modified
            if isinstance(obj, Transition):
                # Invalidate behavior cache (type or properties may have changed)
                self.behavior_cache.pop(id(obj), None)
                
                # Check if it's now a source transition and enable if needed
                is_source = getattr(obj, 'is_source', False)
                if is_source:
                    state = self._get_or_create_state(obj)
                    if state.enablement_time is None:
                        state.enablement_time = self.time
                        behavior = self._get_behavior(obj)
                        if hasattr(behavior, 'set_enablement_time'):
                            behavior.set_enablement_time(self.time)
                        logging.getLogger(__name__).info(f"[OBSERVER] ✅ Enabled source transition {obj.id} at t={self.time}")
        
        # Rebuild place-transition index on any structural topology change
        if event_type in ('created', 'deleted', 'transformed'):
            self._rebuild_place_index()
    
    # ========== Token Accounting Methods ==========

    def _rebuild_place_index(self) -> None:
        """Build place_id → [input transitions] and source-transition list.

        Called after reset() and on structural model changes.  Used by
        get_enabled_transitions() to skip transitions whose input places did
        not change in the most recent firing step.
        """
        idx: Dict[str, List[Any]] = {}
        sources: List[Any] = []
        try:
            for transition in self.model.transitions:
                if getattr(transition, 'is_source', False):
                    sources.append(transition)
            for arc in self.model.arcs:
                src = getattr(arc, 'source', None)
                tgt = getattr(arc, 'target', None)
                if isinstance(src, Place) and isinstance(tgt, Transition):
                    pid = getattr(src, 'id', None)
                    if pid:
                        idx.setdefault(pid, []).append(tgt)
        except Exception:
            pass  # incomplete model during init — index stays empty, fall back to full scan
        self._place_to_input_transitions = idx
        self._source_transitions = sources

    def get_enabled_transitions(self, dirty_places: Optional[Set[str]] = None) -> List[Any]:
        """Return currently enabled transitions, using the dirty-place index when possible.

        When dirty_places is a non-empty set and the place-transition index has
        been built, only transitions connected to those places are re-evaluated.
        Falls back to a full O(T) scan when dirty_places is None/empty (first
        step after reset, or index not yet built).

        Source transitions (no input places) are always included as candidates.

        Args:
            dirty_places: Set of place IDs whose token counts changed in the
                          most recent firing.  Pass None/empty to force full scan.
        Returns:
            List of Transition objects that are currently enabled.
        """
        if dirty_places and self._place_to_input_transitions:
            candidates: List[Any] = list(self._source_transitions)
            seen: Set[int] = {id(t) for t in candidates}
            for pid in dirty_places:
                for t in self._place_to_input_transitions.get(pid, ()):
                    if id(t) not in seen:
                        candidates.append(t)
                        seen.add(id(t))
        else:
            candidates = list(self.model.transitions)
        return [t for t in candidates if self._viability_checker.is_enabled(t)]

    
    def enable_token_accounting(self, strict_mode: Any = False) -> None:
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
            traceback.print_exc()
            self.auditor = None
    
    def disable_token_accounting(self) -> None:
        """Disable token conservation accounting."""
        self.auditor = None
        
        # Disable accounting in all transition behaviors
        for transition in self.model.transitions:
            behavior = self._get_behavior(transition)
            behavior.disable_accounting()
    
    def get_accounting_report(self) -> Optional[Any]:
        """Get token accounting report.
        
        Returns:
            dict: Accounting report with statistics and violations, or None if disabled
        """
        if self.auditor is None:
            return None
        return self.auditor.generate_report()
    
    def print_accounting_report(self) -> None:
        """Print token accounting report to console."""
        if self.auditor is not None:
            self.auditor.print_report()
    
    # ==================== Behavior Management ====================

    def _get_behavior(self, transition: Any) -> Any:
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
        _tid = id(transition)
        if _tid in self.behavior_cache:
            cached_behavior = self.behavior_cache[_tid]
            cached_type = cached_behavior.get_type_name()
            current_type = getattr(transition, 'transition_type', 'continuous')
            type_name_map = {'Immediate': 'immediate', 'Timed (TPN)': 'timed', 'Stochastic (FSPN)': 'stochastic', 'Continuous (SHPN)': 'continuous', 'Adaptive Hybrid (ODE/Stochastic)': 'adaptive'}
            cached_type_normalized = type_name_map.get(cached_type, cached_type.lower())
            if cached_type_normalized != current_type:
                if hasattr(cached_behavior, 'clear_enablement'):
                    cached_behavior.clear_enablement()
                self.behavior_cache.pop(_tid, None)
                self.transition_states.pop(_tid, None)
        if _tid not in self.behavior_cache:
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
            self.behavior_cache[_tid] = behavior
        
        return self.behavior_cache[_tid]

    def _get_or_create_state(self, transition: Any) -> TransitionState:
        """Get or create state tracking for a transition.
        
        Args:
            transition: Transition object
            
        Returns:
            TransitionState: State tracking instance for this transition
        """
        _tid = id(transition)
        if _tid not in self.transition_states:
            self.transition_states[_tid] = TransitionState()
        return cast(TransitionState, self.transition_states[_tid])

    def _update_enablement_states(self) -> None:
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
        logger = logging.getLogger(__name__)

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
            
            # Create threshold evaluator for dynamic threshold support
            evaluator = ThresholdEvaluator(behavior.model)
            context = {'time': self.time}

            # Hybrid PN semantics: discrete transitions (immediate, timed, stochastic)
            # operate on integer token counts — use floor(tokens) so fractional
            # concentrations in continuous places are treated as whole-unit counts.
            # Continuous transitions keep using raw float values for ODE integration.
            is_discrete_trans = getattr(transition, 'transition_type', 'continuous') in (
                'immediate', 'timed', 'stochastic'
            )

            for arc in input_arcs:
                # Check ALL arc types for enablement (normal, test, inhibitor)
                source_place = behavior._get_place(arc.source_id)
                if source_place is None:
                    locally_enabled = False
                    break

                # Evaluate effective threshold (τ_t / threshold supersedes weight if set)
                effective_threshold = evaluator.evaluate(arc, context)

                # Test arc sensing threshold semantics (τ_t vs W_t separation).
                # For continuous/adaptive transitions:
                #   - If arc.threshold is explicitly set → evaluator already returned it → use it
                #   - If arc.threshold is None → default τ_t = 0 (presence check, scale-invariant)
                #     The weight W_t is a kinetic parameter for Φ(t), NOT an enablement floor.
                # For discrete transitions (stochastic, timed, immediate): integer count semantics
                #   → evaluator falls back to arc.weight, which is the correct integer minimum.
                # See doc/foundation/TEST_ARC_SENSING_THRESHOLD_SEPARATION.md for derivation.
                if hasattr(arc, 'arc_type') and arc.arc_type == 'test' and not is_discrete_trans:
                    if getattr(arc, 'threshold', None) is None:
                        effective_threshold = 1e-15  # default τ_t = 0, presence check

                # Hybrid PN: compute tokens visible to this transition type
                check_tokens = math.floor(source_place.tokens) if is_discrete_trans else source_place.tokens

                # Check based on arc type
                if isinstance(arc, (InhibitorArc, CurvedInhibitorArc)):
                    # Inhibitor arcs: INVERTED check (enabled when tokens < threshold)
                    # Transition DISABLED when place has too many tokens (negative feedback)
                    if check_tokens >= effective_threshold:
                        locally_enabled = False
                        break
                else:
                    # Normal/Test arcs: Standard check (enabled when tokens >= threshold)
                    if check_tokens < effective_threshold:
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

    def set_conflict_policy(self, policy: ConflictResolutionPolicy) -> None:
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
        return float(self.settings.get_effective_dt())

    def get_progress(self) -> float:
        """Get simulation progress as fraction [0.0, 1.0].
        
        Returns:
            float: Progress fraction
        """
        return float(self.settings.calculate_progress(self.time))

    def _emit_progress_event(self) -> None:
        """Emit simulation.progress event for UI updates.
        
        Week 1 - Phase 4: EventBus integration for decoupled progress tracking.
        Analyses panel and other observers subscribe to this event.
        """
        if not self.document_id:  # None or 0 (default) → no real UI context
            return  # No document context, skip event
        
        try:
            progress = self.get_progress()
            event_data = {
                'time': self.time,
                'progress': progress,
                'duration': self.settings.duration,
                'is_complete': self.is_simulation_complete()
            }
            doc_id = self.document_id
            if threading.current_thread() is not threading.main_thread():
                try:
                    from gi.repository import GLib
                    GLib.idle_add(lambda: EventBus.emit('simulation.progress', event_data, document_id=doc_id) or False)
                except ImportError:
                    EventBus.emit('simulation.progress', event_data, document_id=doc_id)
            else:
                EventBus.emit('simulation.progress', event_data, document_id=doc_id)
        except (TypeError, AttributeError, RuntimeError) as e:
            logging.getLogger(__name__).debug(f"Event emission failed during simulation: {e}")
    
    def is_simulation_complete(self) -> bool:
        """Check if simulation has reached duration limit.
        
        Returns:
            bool: True if time >= duration
        """
        return bool(self.settings.is_complete(self.time))
    
    # ========== Strategy Pattern Methods (Week 4 - Phase 4) ==========
    
    def get_strategy(self) -> Optional[Any]:
        """Get current execution strategy.
        
        Returns:
            SimulationStrategy: Current strategy, or None if using default logic
        """
        return self._execution_strategy
    
    def set_strategy(self, strategy: Any) -> None:
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
    
    def auto_select_strategy(self) -> Any:
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
        strategy: Any
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
    
    def list_available_strategies(self) -> List[Any]:
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

    def invalidate_behavior_cache(self, transition_id: Any = None) -> None:
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

    def add_step_listener(self, callback: Callable[..., Any]) -> None:
        """Register a callback to be notified on each simulation step.
        
        Args:
            callback: Function to call after each step. Should accept
                     (controller, time) as arguments.
        """
        if callback not in self.step_listeners:
            self.step_listeners.append(callback)

    def remove_step_listener(self, callback: Callable[..., Any]) -> None:
        """Unregister a step listener callback.
        
        Args:
            callback: The callback function to remove
        """
        if callback in self.step_listeners:
            self.step_listeners.remove(callback)
    
    def _notify_step_listeners(self) -> None:
        """Notify all registered step listeners."""
        for callback in self.step_listeners:
            try:
                callback(self, self.time)
            except Exception as e:
                logging.getLogger(__name__).debug(f"Step listener callback failed: {e}")
                pass
    
    # ==================== Single-Step Execution (Hybrid Discrete + Continuous) ====================

    def step(self, time_step: Optional[float] = None) -> bool:
        """Execute a single simulation step with hybrid (discrete + continuous) execution.
        
        REFACTORED (Sprint 2): Extracted helper methods to reduce complexity.
        Original complexity: 69 → New complexity: <20
        
        This performs one iteration of the simulation:
        1. Update enablement states at CURRENT time (for discrete transitions)
        2. EXHAUST IMMEDIATE TRANSITIONS - Fire all immediate transitions in zero time
        3. Handle timed window crossings - transitions whose windows are crossed
        4. Execute CONTINUOUS transitions (integrate over time step)
        5. Execute DISCRETE transitions (timed, stochastic)
        6. Advance simulation time
        7. Notify listeners
        
        Args:
            time_step: Time increment for this step (None = use effective dt from settings)
        
        Returns:
            bool: True if any transition fired/integrated, False if deadlocked/complete
        """
        # === PHASE 0: Initialization and validation ===
        # Use effective dt if not specified
        if time_step is None:
            time_step = float(self.get_effective_dt())
        
        # STOICHIOMETRY FIX: Clamp time step to not exceed duration
        duration_seconds = self.settings.get_duration_seconds()
        if duration_seconds is not None:
            remaining_time = float(duration_seconds) - self.time
            if remaining_time > 0 and time_step > remaining_time:
                time_step = remaining_time
        
        
        # Validate time step is non-negative
        if time_step < 0:
            raise ValueError(f"time_step must be non-negative, got {time_step}")
        
        # Warn about potentially problematic time steps (once per simulation).
        # Threshold is relative: warn when the step would produce fewer than
        # 1 000 samples for the full simulation duration.  For short (<1 000 s)
        # simulations the absolute floor of 1.0 s still applies.
        _warn_threshold = max(1.0, float(duration_seconds or 0) / 1000.0)
        if time_step > _warn_threshold:
            if not hasattr(self, '_large_timestep_warned'):
                self._large_timestep_warned = True
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Large time step ({time_step:.2f}s) may cause timed transitions "
                    f"to miss firing windows (threshold: {_warn_threshold:.2f}s)"
                )

        # Update enablement states
        self._update_enablement_states()

        # === PHASE 0b: Evaluate environment events ===
        self._evaluate_environment_events()

        # === PHASE 1: Execute immediate transitions ===
        immediate_fired = self._exhaust_immediate_transitions()
        
        # === PHASE 2: Handle timed window crossings ===
        window_crossings = self._handle_timed_window_crossings(time_step)
        
        # === PHASE 3: Execute continuous transitions ===
        continuous_active = self._execute_continuous_transitions(time_step)
        
        # === PHASE 4: Execute discrete transitions (timed, stochastic) ===
        discrete_fired, tau_leaping_advanced_time = self._execute_discrete_transitions(time_step)
        
        # === PHASE 5: Finalize step (time advancement, notifications) ===
        should_continue = self._finalize_step(time_step, tau_leaping_advanced_time)
        
        return should_continue

    def _evaluate_environment_events(self) -> None:
        """Evaluate user-defined environment events and fire assignments.

        Runs once per simulation step (Phase 0b, after enablement update).

        Event semantics:
        - Trigger: Python expression evaluated in namespace where model place names
          are bound to their current token count, and ``t`` is the simulation time.
        - Edge-triggered: fires exactly once per True→False→True transition of
          the trigger condition; uses ``self._event_last_triggered`` dict.
        - Assignments: each key is a place name or id; value is a Python expression
          giving the new token count (floats allowed for continuous places).
        - Delay: if > 0, assignment is deferred by ``delay`` time units via
          ``self._event_pending_assignments`` list.

        Gracefully skips any event whose trigger or assignment fails to evaluate.
        """
        # Gather all events from model.events (user-defined) plus pathway_data.events (SBML imports)
        all_events: List[Any] = []
        if hasattr(self.model, 'events'):
            all_events.extend(self.model.events)
        pd = getattr(self, 'pathway_data', None)
        if pd is not None and hasattr(pd, 'events'):
            all_events.extend(pd.events)

        if not all_events:
            return

        # Lazy-init tracking dicts
        if not hasattr(self, '_event_last_triggered'):
            self._event_last_triggered: Dict[Any, bool] = {}
        if not hasattr(self, '_event_pending_assignments'):
            self._event_pending_assignments: List[Tuple[float, Dict[str, Any]]] = []  # [(fire_at_time, {place_name: expr})]

        lg = logging.getLogger(__name__)

        # Build evaluation namespace: place names/ids → current tokens, 't' → time
        ns: Dict[str, Any] = {'t': self.time}
        for p in self.model.places:
            val = float(p.tokens) if hasattr(p, 'tokens') else 0.0
            ns[p.name] = val
            ns[str(p.id)] = val

        # --- Process pending deferred assignments ---
        remaining = []
        for fire_at, assignments in self._event_pending_assignments:
            if self.time >= fire_at:
                self._apply_event_assignments(assignments, ns, lg)
            else:
                remaining.append((fire_at, assignments))
        self._event_pending_assignments = remaining

        # --- Evaluate active event triggers ---
        for event in all_events:
            trigger_expr = getattr(event, 'trigger', '')
            if not trigger_expr:
                continue

            # Footgun guard: warn once if the trigger is a constant numeric/string
            # literal (e.g. "0.0", "1", "'true'") rather than a boolean expression.
            # Such a trigger is constant-False (e.g. 0.0) or constant-True every
            # step — almost always a user mistake. Edge-triggered semantics mean
            # constant-False never fires; constant-True fires once at t=0 and
            # never again. Suggest a real predicate like ``t < 1e-9`` for a
            # one-shot at t=0, or ``t >= some_time`` for a delayed one-shot.
            if not hasattr(self, '_event_trigger_warned'):
                self._event_trigger_warned: set = set()
            if event.id not in self._event_trigger_warned:
                try:
                    import ast as _ast
                    parsed = _ast.parse(trigger_expr.strip(), mode='eval')
                    body = parsed.body
                    is_constant_literal = (
                        isinstance(body, _ast.Constant)
                        and not isinstance(body.value, bool)
                    )
                    if is_constant_literal:
                        lg.warning(
                            f"[ENV_EVENT] event {event.id!r}: trigger {trigger_expr!r} "
                            f"is a bare constant ({body.value!r}), not a boolean expression. "
                            f"This evaluates to {bool(body.value)} every step and will "
                            f"{'fire once at t=0 then never again' if bool(body.value) else 'NEVER fire'}. "
                            f"Use 't < 1e-9' for a one-shot at t=0, or 't >= <time>' for a delayed one-shot."
                        )
                except (SyntaxError, ValueError):
                    pass
                self._event_trigger_warned.add(event.id)

            try:
                fired = bool(eval(trigger_expr, {"__builtins__": {}}, ns))  # noqa: S307
            except Exception as exc:
                lg.debug(f"[ENV_EVENT] trigger eval failed for event {event.id!r}: {exc}")
                continue

            prev = self._event_last_triggered.get(event.id, False)
            self._event_last_triggered[event.id] = fired

            if fired and not prev:
                # Rising edge → schedule or immediately apply assignments
                delay = float(getattr(event, 'delay', 0.0))
                assignments = dict(getattr(event, 'assignments', {}))
                if delay > 0.0:
                    self._event_pending_assignments.append((self.time + delay, assignments))
                    lg.debug(f"[ENV_EVENT] event {event.id!r} triggered, deferred by {delay}")
                else:
                    self._apply_event_assignments(assignments, ns, lg)
                    lg.debug(f"[ENV_EVENT] event {event.id!r} triggered, applied immediately")

    def _apply_event_assignments(self, assignments: Dict[str, Any], ns: Dict[str, Any], lg: Any) -> None:
        """Apply a set of event assignments to place tokens.

        Args:
            assignments: Dict mapping place name/id → value expression string
            ns: Evaluation namespace (place names → values, 't' → time)
            lg: Logger instance
        """
        place_by_name = {p.name: p for p in self.model.places}
        place_by_id = {str(p.id): p for p in self.model.places}

        # Safe math namespace for event RHS expressions. Without this, the
        # ``__builtins__: {}`` sandbox strips ``max``, ``min``, ``abs``,
        # ``round`` — which are routinely used in Pattern A bridge formulas
        # (e.g. ``max(0, 7.0 - PH)`` for ``pH_acidosis``). Numeric helpers
        # from ``math`` are also exposed for kinetic Q10/Arrhenius formulas.
        import math as _math
        safe_builtins = {
            'max': max, 'min': min, 'abs': abs, 'round': round,
            'pow': pow, 'int': int, 'float': float, 'bool': bool,
        }
        for _name in ('exp', 'log', 'log10', 'sqrt', 'sin', 'cos',
                      'tan', 'pi', 'e', 'floor', 'ceil'):
            if hasattr(_math, _name):
                safe_builtins[_name] = getattr(_math, _name)

        for target, expr in assignments.items():
            # Resolve target place
            place = place_by_name.get(target) or place_by_id.get(str(target))
            if place is None:
                lg.debug(f"[ENV_EVENT] assignment target {target!r} not found in model")
                continue
            try:
                new_val = float(eval(str(expr), {"__builtins__": safe_builtins}, ns))  # noqa: S307
                place.tokens = new_val
                # Update namespace so later assignments in same event see the change
                ns[place.name] = new_val
                ns[str(place.id)] = new_val
            except Exception as exc:
                lg.warning(
                    f"[ENV_EVENT] assignment eval failed for {target!r}={expr!r}: {exc}"
                )

    def _exhaust_immediate_transitions(self) -> int:
        """Execute all enabled immediate transitions in zero time.
        
        Immediate transitions fire iteratively until none are enabled,
        with protections against infinite loops and livelocks.
        
        Returns:
            int: Number of immediate transitions fired
        """
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
            
            # Detect immediate livelock: if we've fired more than 20 times, check for cycles.
            # A true livelock requires ≥ 2 distinct transitions forming a cycle that
            # restores tokens.  A single transition draining its own input place will
            # always produce a "T1 → T1 → …" sequence but will naturally terminate
            # once the place is empty — that is NOT a livelock.
            if immediate_fired_total > 20:
                # Check if we're in a repeating cycle (last 10 match previous 10)
                if len(fired_sequence) >= 20:
                    recent = fired_sequence[-10:]
                    previous = fired_sequence[-20:-10]
                    if recent == previous and len(set(recent)) >= 2:
                        # Only log once per simulation run to avoid console spam
                        if not getattr(self, '_livelock_warned', False):
                            self._livelock_warned = True
                            logger = logging.getLogger(__name__)
                            logger.error(
                                f"LIVELOCK DETECTED: Immediate transitions forming infinite cycle: "
                                f"{' → '.join(recent)}. "
                                f"Consider using continuous transitions or adding priorities/guards."
                            )
                        # Stop immediate phase to prevent UI freeze
                        break
        
        if iteration >= max_immediate_iterations - 1:
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Immediate transition limit ({max_immediate_iterations}) reached in single step. "
                f"Fired sequence: {' → '.join(fired_sequence[-20:])}... "
                f"This may indicate a livelock. Consider using continuous transitions instead."
            )
        
        return immediate_fired_total

    def _handle_timed_window_crossings(self, time_step: float) -> int:
        """Handle timed transitions whose firing windows are crossed during this step.
        
        Args:
            time_step: The time increment for this step
            
        Returns:
            int: Number of transitions that fired due to window crossing
        """
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
                    is_source = hasattr(transition, 'properties') and \
                                transition.properties.get('is_source', False)
                    
                    has_tokens = True
                    if not is_source:
                        input_arcs = behavior.get_input_arcs()
                        for arc in input_arcs:
                            source_place = self.model_adapter.places.get(arc.source_id)
                            if source_place is None or source_place.tokens < arc.weight:
                                has_tokens = False
                                break
                    
                    if has_tokens:
                        # Manual token transfer for window crossing
                        consumed_map = {}
                        produced_map = {}
                        
                        # Consume tokens from input places
                        if not is_source:
                            for arc in behavior.get_input_arcs():
                                arc_type = getattr(arc, 'arc_type', 'normal')
                                if arc_type == 'test':
                                    continue
                                source_place = self.model_adapter.places.get(arc.source_id)
                                if source_place is not None:
                                    source_place.set_tokens(source_place.tokens - arc.weight)
                                    consumed_map[arc.source_id] = arc.weight
                        
                        # Produce tokens to output places
                        is_sink = hasattr(transition, 'properties') and \
                                  transition.properties.get('is_sink', False)
                        if not is_sink:
                            for arc in behavior.get_output_arcs():
                                target_place = self.model_adapter.places.get(arc.target_id)
                                if target_place is not None:
                                    target_place.set_tokens(target_place.tokens + arc.weight)
                                    produced_map[arc.target_id] = arc.weight
                        
                        # Clear enablement state (delay clock must restart after firing)
                        state = self._get_or_create_state(transition)
                        state.enablement_time = None
                        state.scheduled_time = None
                        if hasattr(behavior, 'clear_enablement'):
                            behavior.clear_enablement()
                        
                        # Increment firing count for statistics
                        transition.firing_count += 1
                        
                        # Notify listeners
                        details = {
                            'consumed': consumed_map,
                            'produced': produced_map,
                            'window_crossing': True,
                            'timing_window': [behavior.earliest, behavior.latest]
                        }
                        
                        if self.data_collector is not None and hasattr(self.data_collector, 'on_transition_fired'):
                            self.data_collector.on_transition_fired(transition, self.time, details)
                        
                        for listener in self.step_listeners:
                            listener_obj = listener.__self__ if hasattr(listener, '__self__') else listener
                            if hasattr(listener_obj, 'on_transition_fired'):
                                listener_obj.on_transition_fired(transition, self.time, details)
                        
                        window_crossing_fired += 1
        
        return window_crossing_fired

    def _execute_continuous_transitions(self, time_step: float) -> int:
        """Execute continuous transitions with conflict resolution.

        Args:
            time_step: The time increment for this step

        Returns:
            int: Number of continuous transitions that successfully integrated
        """  # noqa: D401
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
        
        continuous_enabled = []
        for transition in continuous_transitions:
            behavior = self._get_behavior(transition)
            can_flow, reason = behavior.can_fire()
            if can_flow:
                input_arcs = behavior.get_input_arcs()
                output_arcs = behavior.get_output_arcs()
                continuous_enabled.append((transition, behavior, input_arcs, output_arcs))
        
        # Apply conflict resolution for continuous transitions
        continuous_solo, continuous_preemptive_groups = self._resolve_continuous_conflicts(continuous_enabled)

        continuous_active = 0

        # --- Sequential (solo) transitions ---
        for transition, behavior, input_arcs, output_arcs in continuous_solo:
            success, details = behavior.integrate_step(dt=time_step, input_arcs=input_arcs, output_arcs=output_arcs)
            if success:
                continuous_active += 1
                if details and 'rate' in details:
                    transition.firing_count += abs(details['rate']) * time_step
                else:
                    if hasattr(behavior, 'evaluate_rate'):
                        rate = behavior.evaluate_rate({p.id: p for p in self.model.places}, self.time)
                    elif hasattr(behavior, '_evaluate_rate_at_enablement'):
                        rate = behavior._evaluate_rate_at_enablement(self.time)
                    else:
                        rate = 0.0
                    transition.firing_count += abs(rate) * time_step
                if self.data_collector is not None and hasattr(self.data_collector, 'on_transition_fired'):
                    self.data_collector.on_transition_fired(transition, self.time, details)
                for listener in self.step_listeners:
                    listener_obj = listener.__self__ if hasattr(listener, '__self__') else listener
                    if hasattr(listener_obj, 'on_transition_fired'):
                        listener_obj.on_transition_fired(transition, self.time, details)

        # --- Preemptive groups: snapshot/apply atomic simultaneous execution ---
        for group in continuous_preemptive_groups:
            group_results = self._integrate_preemptive_group(group, dt=time_step)
            for transition, success, details in group_results:
                if success:
                    continuous_active += 1
                    if details and 'rate' in details:
                        transition.firing_count += abs(details['rate']) * time_step
                    else:
                        if hasattr(self._get_behavior(transition), 'evaluate_rate'):
                            rate = self._get_behavior(transition).evaluate_rate(
                                {p.name: p for p in self.model.places}, self.time)
                        else:
                            rate = 0.0
                        transition.firing_count += abs(rate) * time_step
                    if self.data_collector is not None and hasattr(self.data_collector, 'on_transition_fired'):
                        self.data_collector.on_transition_fired(transition, self.time, details)
                    for listener in self.step_listeners:
                        listener_obj = listener.__self__ if hasattr(listener, '__self__') else listener
                        if hasattr(listener_obj, 'on_transition_fired'):
                            listener_obj.on_transition_fired(transition, self.time, details)

        return continuous_active

    def _execute_discrete_transitions(self, time_step: float) -> Tuple[bool, bool]:
        """Execute timed and stochastic transitions.
        
        Timed (deterministic) has PRIORITY over Stochastic (probabilistic).
        Only fire stochastic if NO timed transitions can fire.
        
        Args:
            time_step: The time increment for this step
            
        Returns:
            tuple: (discrete_fired: bool, tau_leaping_advanced_time: bool)
        """
        discrete_fired = False
        tau_leaping_advanced_time = False
        
        # Phase 2a: Timed transitions (DETERMINISTIC - PRIORITY)
        timed_transitions = [t for t in self.model.transitions if t.transition_type == 'timed']
        enabled_timed = [t for t in timed_transitions if self._is_transition_enabled(t)]
        
        if enabled_timed:
            # Select and fire one timed transition
            transition = self._select_transition(enabled_timed)
            self._fire_transition(transition)
            discrete_fired = True
            # Reset the delay clock so the transition must wait another [earliest, latest]
            # interval before it can fire again.  Without this, state.enablement_time
            # stays at the original value and elapsed keeps growing, so can_fire()
            # returns True on every subsequent step — identical to continuous behaviour.
            _tid = id(transition)
            if _tid in self.transition_states:
                self.transition_states[_tid].enablement_time = None
                self.transition_states[_tid].scheduled_time = None
            _behavior = self.behavior_cache.get(_tid)
            if _behavior is not None and hasattr(_behavior, 'clear_enablement'):
                _behavior.clear_enablement()
            self._update_enablement_states()
        
        # Phase 2b: Stochastic transitions (PROBABILISTIC - LOWER PRIORITY)
        if not discrete_fired:
            # Build stochastic list: include `stochastic` transitions always, but
            # include `adaptive` transitions ONLY when they are in stochastic mode.
            # Adaptive transitions currently in continuous mode are already fired by
            # the ODE phase (Phase 3); re-including them here would double-count their
            # effect (ODE integrate_step + Poisson sample), producing incorrect dynamics.
            stochastic_transitions = []
            for _t in self.model.transitions:
                if _t.transition_type == 'stochastic':
                    stochastic_transitions.append(_t)
                elif _t.transition_type == 'adaptive':
                    _beh = self._get_behavior(_t)
                    if _beh is not None:
                        _mode = getattr(_beh, '_current_mode', None)
                        if _mode is None and hasattr(_beh, '_select_mode'):
                            _mode = _beh._select_mode()
                        if _mode == 'stochastic':
                            stochastic_transitions.append(_t)
            
            # Check enabling — use the appropriate semantics per type.
            # Pure stochastic: discrete structural check (tokens >= weight).
            # Adaptive-in-stochastic-mode: rate-function propensity > 0,
            # because the arc weight is a stoichiometric coefficient for
            # continuous-valued places, NOT a discrete token threshold.
            # (HPN formalism: adaptive transitions bridge continuous and
            # discrete domains — the rate function encodes enabling.)
            enabled_stochastic = []
            for t in stochastic_transitions:
                behavior = self._get_behavior(t)
                if t.transition_type == 'adaptive':
                    # ── F1 fix: rate-based enabling for adaptive transitions ──
                    # Evaluate the rate function; if rate > 0 the transition
                    # is enabled.  This avoids the discrete tokens>=weight
                    # check that permanently blocks adaptive transitions
                    # connected to continuous-valued places.
                    try:
                        places_dict = {p.name: p for p in self.model.places}
                        rate = behavior.evaluate_rate(places_dict, self.time)
                        if rate > 0:
                            enabled_stochastic.append(t)
                    except Exception:
                        pass  # skip on eval error
                else:
                    input_arcs = behavior.get_input_arcs()
                    structurally_enabled = True
                    for arc in input_arcs:
                        arc_type = getattr(arc, 'arc_type', 'normal')
                        if arc_type == 'test':
                            continue
                        source_place = arc.source
                        if source_place and source_place.tokens < arc.weight:
                            structurally_enabled = False
                            break
                    if structurally_enabled:
                        enabled_stochastic.append(t)
            
            if enabled_stochastic:
                # Use τ-leaping for stochastic simulation
                from .tau_leaping import TauLeapingEngine
                
                if not hasattr(self, '_tau_leaping_engine'):
                    self._tau_leaping_engine = TauLeapingEngine(
                        epsilon=self.settings.tau_epsilon,
                        critical_threshold=self.settings.critical_threshold,
                        max_tau=self.settings.max_tau,
                        seed=None,
                        use_parallel=self.settings.use_parallel_stochastic,
                        verbose=self.verbose,
                        n_critical=getattr(self.settings, 'n_critical', 10),
                    )
                    self._tau_leaping_engine.leap_selector.min_tau = self.settings.min_tau
                
                # Determine if this is a pure stochastic model.
                # A model is "pure stochastic" when every transition is either
                # stochastic or adaptive-in-stochastic-mode (i.e., no continuous ODE
                # transitions exist).  Adaptive transitions currently in continuous mode
                # do NOT count as stochastic for this decision.
                is_pure_stochastic = all(
                    t.transition_type == 'stochastic' or (
                        t.transition_type == 'adaptive' and
                        t in stochastic_transitions  # already filtered to stochastic-mode adaptives
                    )
                    for t in self.model.transitions
                    if hasattr(t, 'transition_type')
                )
                
                if is_pure_stochastic:
                    # Pure stochastic: tau-leaping controls time stepping
                    self._tau_leaping_engine.execute_step(self)
                    tau_leaping_advanced_time = True
                else:
                    # ── Hybrid operator splitting (F5 fix, 2026-05-04) ──
                    # Old behaviour fired exactly ONE τ-leap per master dt
                    # window, regardless of how small the chosen τ was. With
                    # user max_tau ≪ dt (e.g. 0.1 s vs 5 s) this silently
                    # discarded ~98 % of the stochastic time inside each
                    # window — the documented F5 trap.
                    #
                    # Correct semantics (Haseltine–Rawlings / Salis–
                    # Kaznessis hybrid): the ODE phase has already advanced
                    # the continuous state by `time_step`. Now repeatedly
                    # fire τ-leaps inside the same [t, t+dt] window until
                    # the window is exhausted, no stochastic transition is
                    # enabled, or the engine refuses to make further
                    # progress.
                    #
                    # Correctness invariants:
                    #   • The user-configured max_tau (Cao leap-validity
                    #     bound) is preserved — never widened to dt.
                    #   • Each inner leap is additionally capped at the
                    #     remaining window so the loop never overshoots.
                    #   • τ-leap advances controller.time inside the loop
                    #     (_advance_time=True), so the finalize phase must
                    #     NOT re-add `time_step` (signal that via
                    #     tau_leaping_advanced_time=True).
                    #   • Defensive guards prevent infinite loops when the
                    #     engine returns False or selects τ ≈ 0.
                    user_max_tau = self._tau_leaping_engine.leap_selector.max_tau
                    t_target = self.time + time_step
                    # 1 ns relative tolerance keeps the loop from spinning on
                    # floating-point residue at the window boundary.
                    eps_done = max(1e-12, 1e-9 * abs(time_step))
                    self._tau_leaping_engine._advance_time = True
                    n_inner_leaps = 0
                    max_inner_leaps = max(
                        16,
                        int(time_step / max(user_max_tau, 1e-12)) + 8,
                    )
                    try:
                        while self.time + eps_done < t_target:
                            remaining = t_target - self.time
                            # Cap each leap at min(user_max_tau, remaining
                            # window). The latter prevents overshoot; the
                            # former preserves the Cao validity bound.
                            self._tau_leaping_engine.leap_selector.max_tau = min(
                                user_max_tau, remaining
                            )
                            t_before = self.time
                            cont = self._tau_leaping_engine.execute_step(self)
                            n_inner_leaps += 1
                            # Engine signalled "no stochastic transitions"
                            # — nothing more to fire in this window.
                            if cont is False:
                                break
                            # Progress guard: if τ-leap fell back to exact
                            # SSA with no firing or otherwise stalled, give
                            # up rather than spin.
                            if self.time - t_before < eps_done:
                                break
                            # Hard cap on inner iterations as a final
                            # safety net (should never trigger under
                            # well-behaved propensities).
                            if n_inner_leaps >= max_inner_leaps:
                                if self.verbose:
                                    self.logger.warning(
                                        "Hybrid τ-leap inner loop hit "
                                        "max_inner_leaps=%d at t=%.6g "
                                        "(window dt=%.6g, user max_tau=%.6g); "
                                        "advancing to t_target. Consider "
                                        "raising max_tau or lowering dt.",
                                        max_inner_leaps, self.time,
                                        time_step, user_max_tau,
                                    )
                                break
                    finally:
                        # Always restore user max_tau, even on exception.
                        self._tau_leaping_engine.leap_selector.max_tau = user_max_tau

                    # Snap to the exact target if any residue remains. This
                    # keeps the master clock aligned with the recording grid
                    # and ensures the finalize phase sees a fully-consumed
                    # window.
                    if self.time < t_target:
                        self.time = t_target
                    tau_leaping_advanced_time = True

                discrete_fired = True
        
        return discrete_fired, tau_leaping_advanced_time

    def _finalize_step(self, time_step: float, tau_leaping_advanced_time: bool) -> bool:
        """Finalize the simulation step: advance time and notify listeners.
        
        Args:
            time_step: The time increment for this step
            tau_leaping_advanced_time: Whether tau-leaping already advanced time
            
        Returns:
            bool: True if simulation should continue, False if complete
        """
        # Advance time AFTER stochastic phase
        if not tau_leaping_advanced_time:
            self.time += time_step
        
        # Emit progress event for UI updates
        self._emit_progress_event()
        
        # Record state after time advancement
        if self.data_collector:
            self.data_collector.record_state(self.time)
        
        # Update thermodynamic validators
        if self.validator_manager and len(self.validator_manager) > 0:
            places_dict = {p.id: p for p in self.model.places}
            transitions_dict = {t.id: t for t in self.model.transitions}
            self.validator_manager.update(self.time, places_dict, transitions_dict)
        
        self._notify_step_listeners()
        
        # Check if simulation is complete
        if self.is_simulation_complete():
            logging.getLogger(__name__).info(f"[SIMULATION] Duration reached: time={self.time}, duration={self.settings.duration}")
            return False
        
        return True

    def _find_enabled_transitions(self) -> List[Any]:
        """Find all transitions that are enabled (can fire).
        
        REFACTORED (Phase 2.3.2): Delegates to ViabilityChecker.
        
        A transition is enabled if all its input places have enough tokens
        to satisfy the arc weights (and arc type rules + guard conditions).
        
        Returns:
            List: All transition objects currently enabled.
        """
        return [t for t in self.model.transitions if self._viability_checker.is_enabled(t)]

    def _is_transition_enabled(self, transition: Any) -> bool:
        """Check whether a single transition is currently enabled.
        
        Delegates to ViabilityChecker which checks token availability,
        arc-type rules (normal, signal_flow, inhibitor, test) and guards.
        
        Args:
            transition: Transition object to check.
            
        Returns:
            bool: True if the transition can fire right now.
        """
        return bool(self._viability_checker.is_enabled(transition))

    def _fire_transition(self, transition: Any) -> None:
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
            # Track dirty places for incremental enabled-transition scan
            _dirty: Set[str] = set()
            for _arc in input_arcs:
                _pid = getattr(_arc, 'source_id', None)
                if _pid:
                    _dirty.add(_pid)
            for _arc in output_arcs:
                _pid = getattr(_arc, 'target_id', None)
                if _pid:
                    _dirty.add(_pid)
            self._dirty_since_last_check |= _dirty
        if self.data_collector is not None and hasattr(self.data_collector, 'on_transition_fired'):
            self.data_collector.on_transition_fired(transition, self.time, details)
        
        # PHASE 1-2 FIX: Also notify step listeners if they have on_transition_fired
        for listener in self.step_listeners:
            listener_obj = listener.__self__ if hasattr(listener, '__self__') else listener
            if hasattr(listener_obj, 'on_transition_fired'):
                listener_obj.on_transition_fired(transition, self.time, details)

    # ============================================================================
    # Phase 1: Locality Independence Detection (Place-Sharing Analysis)
    # ============================================================================
    
    def _get_all_places_for_transition(self, transition: Any) -> Set[Any]:
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
    
    def _are_independent(self, t1: Any, t2: Any) -> bool:
        """Delegate to ConflictResolver."""
        return bool(self._conflict_resolver.are_independent(t1, t2))
    
    def _compute_conflict_sets(self, transitions: List[Any]) -> Dict[str, Set[Any]]:
        """Delegate to ConflictResolver."""
        return cast(Dict[str, Set[Any]], self._conflict_resolver.compute_conflict_sets(transitions))
    
    def _get_independent_transitions(self, transitions: List[Any]) -> List[List[Any]]:
        """Delegate to ConflictResolver."""
        return cast(List[List[Any]], self._conflict_resolver.get_independent_groups(transitions))

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

    def _find_maximal_concurrent_sets(self, enabled_transitions: List[Any], max_sets: int = 5) -> List[List[Any]]:
        """Delegate to ConflictResolver."""
        return cast(List[List[Any]], self._conflict_resolver.find_maximal_concurrent_sets(enabled_transitions, max_sets))

    def _greedy_maximal_set(self, transitions: List[Any], conflict_sets: Dict[Any, Any],
                           start_index: int = 0) -> List[Any]:
        """Delegate to ConflictResolver."""
        return cast(List[Any], self._conflict_resolver._greedy_maximal_set(transitions, conflict_sets, start_index))

    def _sort_by_conflict_degree(self, transitions: List[Any], conflict_sets: Dict[Any, Any],
                                 ascending: bool = True) -> List[Any]:
        """Delegate to ConflictResolver."""
        return cast(List[Any], self._conflict_resolver._sort_by_conflict_degree(transitions, conflict_sets, ascending))

    def _is_concurrent_set_maximal(self, concurrent_set: List[Any], 
                                   all_enabled: List[Any], conflict_sets: Dict[Any, Any]) -> bool:
        """Delegate to ConflictResolver."""
        return bool(self._conflict_resolver.is_concurrent_set_maximal(concurrent_set, all_enabled, conflict_sets))

    # ========================================================================
    # PHASE 3: MAXIMAL STEP EXECUTION
    # ========================================================================
    # Atomic execution of maximal concurrent sets with rollback guarantees
    # Methods: select, validate, snapshot, restore, execute
    # ========================================================================

    def _select_maximal_set(self, maximal_sets: List[List[Any]], 
                           strategy: str = 'largest') -> List[Any]:
        """Delegate to ConflictResolver."""
        return cast(List[Any], self._conflict_resolver.select_maximal_set(maximal_sets, strategy))

    def _validate_all_can_fire(self, transition_set: List[Any]) -> bool:
        """Delegate to ConflictResolver."""
        return bool(self._conflict_resolver.validate_all_can_fire(transition_set))

    def _snapshot_marking(self) -> Dict[Any, Any]:
        """Delegate to ConflictResolver."""
        return cast(Dict[Any, Any], self._conflict_resolver._snapshot_marking())

    def _restore_marking(self, snapshot: Dict[Any, Any]) -> None:
        """Delegate to ConflictResolver."""
        self._conflict_resolver._restore_marking(snapshot)

    def _execute_maximal_step(self, transition_set: List[Any]) -> Tuple[Any, ...]:
        """Delegate to ConflictResolver."""
        return cast(Tuple[Any, ...], self._conflict_resolver.execute_maximal_step(transition_set))

    def _select_transition(self, enabled_transitions: List[Any]) -> Any:
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
            if self.conflict_policy == ConflictResolutionPolicy.PREEMPTIVE:
                # Rate-proportional selection: anti-monopolization fallback.
                # (All-preemptive groups are handled upstream in
                # _resolve_continuous_conflicts; this covers any stray call.)
                import numpy as np
                rates = []
                for t in enabled_transitions:
                    try:
                        r = float(t.rate) if hasattr(t, 'rate') and t.rate is not None else 1.0
                    except Exception:
                        r = 1.0
                    rates.append(max(r, 1e-12))
                total = sum(rates)
                probs = [r / total for r in rates]
                idx = int(np.random.choice(len(enabled_transitions), p=probs))
                return enabled_transitions[idx]
            elif self.conflict_policy == ConflictResolutionPolicy.RANDOM:
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
                # Evaluate rate dynamically for all transition types with rate_function
                # - Continuous: uses evaluate_rate()
                # - Stochastic/Adaptive: uses _evaluate_rate_at_enablement()
                # - Others (timed/immediate): use scalar rate attribute
                
                if t.transition_type == 'continuous':
                    # Continuous transitions: evaluate rate_function at current state
                    behavior = self._get_behavior(t)
                    if behavior and hasattr(behavior, 'evaluate_rate'):
                        # Get all places for rate evaluation
                        places_dict = {}
                        if hasattr(self.model, 'places'):
                            if isinstance(self.model.places, dict):
                                places_dict = self.model.places
                            elif isinstance(self.model.places, list):
                                for place in self.model.places:
                                    places_dict[place.id] = place
                        # Evaluate actual rate at current state
                        rate = abs(behavior.evaluate_rate(places_dict, self.time))
                    else:
                        # Fallback to rate attribute
                        rate = float(getattr(t, 'rate', 1.0))
                
                elif t.transition_type in ('stochastic', 'adaptive'):
                    # Stochastic/Adaptive transitions: may have rate_function too!
                    behavior = self._get_behavior(t)
                    if behavior and hasattr(behavior, '_evaluate_rate_at_enablement'):
                        try:
                            # Evaluate rate_function at current time
                            rate = abs(behavior._evaluate_rate_at_enablement(self.time))
                        except Exception:
                            # Fallback if evaluation fails
                            rate = float(getattr(t, 'rate', 1.0))
                    else:
                        # No rate_function - use scalar rate
                        try:
                            rate_value = getattr(t, 'rate', 1.0)
                            if isinstance(rate_value, str):
                                # Legacy: rate was mistakenly set to rate_function string
                                rate = 1.0  # Use default
                            else:
                                rate = float(rate_value) if rate_value else 1.0
                        except (ValueError, TypeError):
                            rate = 1.0
                
                else:
                    # Timed/Immediate: use rate attribute (no rate_function support)
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
        
        elif policy == 'preemptive':
            # Rate-proportional selection: anti-monopolization interrupt mechanism.
            #
            # Each competing transition fires with probability rate_i / Σrate_j.
            # This prevents any single transition from permanently monopolizing a
            # shared substrate: faster reactions dominate probabilistically but
            # slower ones are never permanently blocked.
            #
            # Over many steps this reproduces ODE semantics where all parallel
            # reactions consume from the shared pool simultaneously, proportional
            # to their intrinsic kinetics — without explicit stoichiometric splitting.
            import numpy as np
            rates = []
            for t in enabled_transitions:
                if t.transition_type == 'continuous':
                    behavior = self._get_behavior(t)
                    if behavior and hasattr(behavior, 'evaluate_rate'):
                        places_dict = {}
                        if hasattr(self.model, 'places'):
                            for place in (self.model.places.values() if isinstance(self.model.places, dict) else self.model.places):
                                places_dict[place.id] = place
                        rate = abs(behavior.evaluate_rate(places_dict, self.time))
                    else:
                        rate = float(getattr(t, 'rate', 1.0))
                elif t.transition_type in ('stochastic', 'adaptive'):
                    behavior = self._get_behavior(t)
                    if behavior and hasattr(behavior, '_evaluate_rate_at_enablement'):
                        try:
                            rate = abs(behavior._evaluate_rate_at_enablement(self.time))
                        except Exception:
                            rate = float(getattr(t, 'rate', 1.0))
                    else:
                        rate = float(getattr(t, 'rate', 1.0))
                else:
                    try:
                        rate = float(getattr(t, 'rate', 1.0))
                    except (ValueError, TypeError):
                        rate = 1.0
                rates.append(max(rate, 1e-12))   # floor to avoid zero-weight starvation
            total = sum(rates)
            probs = [r / total for r in rates]
            idx = np.random.choice(len(enabled_transitions), p=probs)
            return enabled_transitions[idx]

        elif policy == 'preemptive-priority':
            # Priority-based preemption: highest-priority transition interrupts others.
            return max(enabled_transitions, key=lambda t: getattr(t, 'priority', 0))

        elif policy == 'single':
            # Single-fire: this transition always wins the conflict group outright.
            # Select the first member carrying the 'single' policy; fall back to
            # the first enabled if none explicitly carries it.
            for t in enabled_transitions:
                if getattr(t, 'firing_policy', '') == 'single':
                    return t
            return enabled_transitions[0]

        else:
            pass
            # Unknown policy - default to random
            return random.choice(enabled_transitions)

    def _resolve_continuous_conflicts(self, continuous_enabled: List[Any]) -> Tuple[List[Any], List[Any]]:
        """Resolve continuous transition conflicts using LocalityDetector.

        Two transitions belong to the same conflict group when their localities
        share at least one place (input OR output, excluding test/catalyst arcs).

        Locality L(T) = input_places ∪ output_places  (consuming arcs only)

        Groups are formed by BFS over the locality footprints:
          - Node = transition
          - Edge = shared footprint place between two transitions

        Within each group the firing policy decides execution mode:
          - All preemptive (or global PREEMPTIVE policy): snapshot/apply atomic
          - Otherwise: sequential winner selection

        Args:
            continuous_enabled: List of (transition, behavior, input_arcs, output_arcs)

        Returns:
            (solo, preemptive_groups) where:
              - solo:              list of (transition, behavior, input_arcs, output_arcs)
              - preemptive_groups: list of lists of the same tuples
        """
        if len(continuous_enabled) <= 1:
            return continuous_enabled, []

        from shypn.diagnostic.locality_detector import LocalityDetector

        detector = LocalityDetector(self.model)
        enabled_ids = {trans_tuple[0].id for trans_tuple in continuous_enabled}
        transition_data = {trans_tuple[0].id: trans_tuple for trans_tuple in continuous_enabled}

        # Build footprint per transition and reverse map place → transitions.
        # Locality.input_places + output_places already excludes catalyst/test arcs.
        trans_footprint: Dict[Any, Any] = {}   # transition_id → list of place objects
        place_to_trans: Dict[Any, Any] = {}    # place_id → set of transition_ids

        for trans_tuple in continuous_enabled:
            tid = trans_tuple[0].id
            locality = detector.get_locality_for_transition(trans_tuple[0])
            footprint = locality.input_places + locality.output_places
            trans_footprint[tid] = footprint
            for place in footprint:
                pid = place.id
                if pid not in place_to_trans:
                    place_to_trans[pid] = set()
                place_to_trans[pid].add(tid)

        # BFS: form conflict groups from shared footprint places
        visited = set()
        conflict_groups = []

        for trans_tuple in continuous_enabled:
            start_id = trans_tuple[0].id
            if start_id in visited:
                continue

            bfs_group: Set[Any] = set()
            queue = [start_id]
            while queue:
                cur = queue.pop()
                if cur in bfs_group:
                    continue
                bfs_group.add(cur)
                visited.add(cur)
                for place in trans_footprint.get(cur, []):
                    for nbr in place_to_trans.get(place.id, set()):
                        if nbr not in bfs_group and nbr in enabled_ids:
                            queue.append(nbr)

            if len(bfs_group) > 1:
                conflict_groups.append([transition_data[tid][0] for tid in bfs_group])

        # Apply conflict resolution policy within each group
        solo = []
        preemptive_groups = []
        conflicting_ids: Set[Any] = set()

        for group in conflict_groups:
            all_preemptive = (
                all(getattr(t, 'firing_policy', '') == 'preemptive' for t in group)
                or self.conflict_policy == ConflictResolutionPolicy.PREEMPTIVE
            )
            if all_preemptive:
                preemptive_groups.append([transition_data[t.id] for t in group])
            else:
                winner = self._select_transition(group)
                solo.append(transition_data[winner.id])
            conflicting_ids.update(t.id for t in group)

        # Non-conflicting transitions fire individually
        for trans_tuple in continuous_enabled:
            if trans_tuple[0].id not in conflicting_ids:
                solo.append(trans_tuple)

        return solo, preemptive_groups

    def _integrate_preemptive_group(self, group: List[Any], dt: float) -> List[Any]:
        """Fire a preemptive conflict group with snapshot/apply atomics.

        All transitions in *group* evaluate and consume from a shared token
        snapshot taken before any transition fires.  Each transition's delta
        is computed independently, then all deltas are summed and applied as
        one atomic update — reproducing true ODE parallel-reaction semantics
        without order-of-execution drift.

        Phase 1 — snapshot: record current tokens for all places touched by
                  any transition in the group.
        Phase 2 — evaluate: for each transition, restore snapshot, call
                  integrate_step, record the per-place delta, then restore
                  snapshot again so the next transition also sees pristine values.
        Phase 3 — commit: apply summed deltas to live tokens, clamped at 0.

        Args:
            group: list of (transition, behavior, input_arcs, output_arcs)
            dt:    integration time step

        Returns:
            List of (transition, success, details) for the caller to record.
        """
        # Build a fast place-id → place map scoped to this model.
        places_map: Dict[str, Any] = {p.id: p for p in self.model.places}

        # Collect every place that any member of this group touches.
        # Bug-fix 2026-05-04: this set was previously initialised empty and
        # never populated, so the snapshot/restore/commit phases below were
        # all no-ops — group transitions silently fired sequentially on
        # live state, breaking the documented parallel-reaction semantics.
        touched_ids: Set[Any] = set()
        for _t, _beh, _in_arcs, _out_arcs in group:
            for _arc in _in_arcs:
                _pid = getattr(_arc, 'source_id', None)
                if _pid is not None and _pid in places_map:
                    touched_ids.add(_pid)
            for _arc in _out_arcs:
                _pid = getattr(_arc, 'target_id', None)
                if _pid is not None and _pid in places_map:
                    touched_ids.add(_pid)

        # Phase 1: snapshot
        snapshot: Dict[str, float] = {pid: places_map[pid].tokens for pid in touched_ids}

        # Phase 2: evaluate each transition against the pristine snapshot
        deltas: Dict[str, float] = {pid: 0.0 for pid in touched_ids}
        results: List[Any] = []

        for transition, behavior, input_arcs, output_arcs in group:
            # Restore snapshot so this transition sees pre-step values
            for pid, val in snapshot.items():
                places_map[pid].tokens = val

            success, details = behavior.integrate_step(
                dt=dt, input_arcs=input_arcs, output_arcs=output_arcs
            )

            if success:
                # Accumulate this transition's contribution to the delta
                for pid in touched_ids:
                    deltas[pid] += places_map[pid].tokens - snapshot[pid]

            results.append((transition, success, details))

        # Phase 3: commit — restore snapshot first, then apply summed deltas
        for pid, val in snapshot.items():
            places_map[pid].tokens = val
        for pid, delta in deltas.items():
            places_map[pid].tokens = max(0.0, snapshot[pid] + delta)

        return results
    
    # ==================== Continuous Execution (Run Mode) ====================
    # REFACTORED (Phase 2.3.1): Extracted to ContinuousExecutor strategy class
    # Original implementation: ~250 lines
    # New implementation: Thin delegation layer (maintains backward compatibility)
    # Benefits: Strategy pattern for alternative executors (parallel, distributed)
    #           Testable execution logic in isolation
    #           Clear separation of concerns

    def run(self, time_step: Optional[float] = None, max_steps: Optional[int] = None) -> bool:
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
        # TMD-1: re-run the timescale audit at simulation-start. The
        # __init__ pass may have fired against a still-empty model
        # (canvas constructed before the .shy load completed), leaving
        # ``last_timescale_profile`` with ``n_transitions_assessed=0``.
        # By the time run() is invoked the model is fully populated and
        # the configured dt is final, so the audit produces actionable
        # numbers and the EventBus notification reaches the activity log
        # right when the user presses Run.
        try:
            self._run_timescale_audit()
        except TimescaleMismatchError:
            raise  # 'error' mode — propagate to caller
        except Exception:  # pragma: no cover - audit must never break run
            logging.getLogger(__name__).debug(
                "pre-run timescale audit skipped due to exception", exc_info=True
            )

        return bool(self._continuous_executor.run(time_step, max_steps))

    def _simulation_loop(self) -> bool:
        """Internal simulation loop callback.
        
        REFACTORED (Phase 2.3.1): Delegates to ContinuousExecutor strategy.
        
        Executes multiple simulation steps per GUI update for smooth animation
        at all time scales. For very small time steps (e.g., 2ms), this batches
        many steps together to avoid choppy visualization.
        
        Returns:
            bool: True to continue, False to stop the timeout
        """
        return bool(self._continuous_executor._simulation_loop())

    def stop(self) -> None:
        """Stop the continuous simulation.
        
        REFACTORED (Phase 2.3.1): Delegates to ContinuousExecutor strategy.
        
        This requests the simulation to stop. The actual stop will occur
        after the current step completes.
        
        IMPORTANT: This clears enablement states so that when Run is pressed
        again, transitions start fresh with enablement time = current time.
        """
        self._continuous_executor.stop()

    def reset(self) -> None:  # type: ignore[no-redef]
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

        # Reset tau-leaping engine's dirty-flag so the next run's first step
        # does a full y[] sync from model (update_y_from_model) instead of a
        # partial sync that may miss places whose initial_marking was changed
        # by the user between runs (e.g. GCSF_external edited via dialog).
        if hasattr(self, '_tau_leaping_engine'):
            self._tau_leaping_engine._changed_place_ids = None

        # Schedule time-dependent transitions (timed/stochastic) after reset
        self._update_enablement_states()
        self._notify_step_listeners()
    
    def reset_for_new_model(self, new_model: Any) -> None:
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
        for _cb in self.data_collector_listeners:
            try:
                _cb(self.data_collector)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Error in data_collector listener: {e}")

        # PHASE 1-2 FIX: Restore callback after recreating data collector
        self.on_simulation_complete = saved_callback
        
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
        return cast(Optional[float], self.settings.get_duration_seconds())