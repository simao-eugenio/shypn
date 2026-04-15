"""ArcBuilder - Fluent interface for Arc construction.

Provides clean, readable API for constructing all 7 arc types with full
Signal Hierarchical Petri Net (SHPN) support.

Arc Types (7 total):
1. Arc - Normal mass transfer arc (horizontal stoichiometry)
2. CurvedArc - Curved normal arc with bezier path
3. InhibitorArc - Inverted logic arc (Place → Transition only)
4. CurvedInhibitorArc - Curved inhibitor arc
5. TestArc - Non-consuming catalyst arc (read-only)
6. SignalFlowArc - Consumptive information arc (SHPN vertical broadcast)
7. CurvedSignalFlowArc - Curved signal flow arc

Features:
- Type-safe fluent API with validation
- Dual weight support (W for normal, W_s for signal)
- Control point configuration for curved arcs
- Deferred source/target resolution (by ID or object)
- Comprehensive error checking

Example - Normal arc:
    arc = (ArcBuilder()
           .from_place("glucose")
           .to_transition("glycolysis")
           .with_weight(1)
           .build())

Example - Signal flow arc (SHPN):
    arc = (ArcBuilder()
           .from_place("ATP")
           .to_transition("commit")
           .as_signal_flow()
           .with_signal_weight(0.17)  # W_s (decision quota)
           .build())

Example - Curved inhibitor arc:
    arc = (ArcBuilder()
           .from_place("inhibitor")
           .to_transition("reaction")
           .as_inhibitor()
           .as_curved()
           .with_threshold(10)
           .with_control_points([(160, 180), (170, 190)])
           .build())

See doc/PHASE_3_QUALITY_PLAN.md for design rationale.
See doc/SIGNAL_HIERARCHICAL_FORMALISM.md for SHPN arc semantics.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Tuple, Union, Any, Dict
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition


if TYPE_CHECKING:
    from shypn.netobjs.arc import Arc


class ArcBuilder:
    """Fluent builder for Arc objects (all 7 types).
    
    Supports normal, curved, inhibitor, test, and signal flow arcs with
    comprehensive configuration options and validation.
    
    Attributes:
        All internal attributes are prefixed with _ to indicate builder state.
        Use build() to construct the final Arc subclass instance.
    """
    
    def __init__(self):
        """Initialize empty arc builder.
        
        Source and target must be set via .from_*() and .to_*() methods.
        """
        # Required: source and target (can be ID strings or objects)
        self._source: Optional[Union[str, Place, Transition]] = None
        self._target: Optional[Union[str, Place, Transition]] = None
        
        # Weights (SHPN dual arc semantics)
        self._weight: float = 1.0  # Normal weight W (stoichiometry, horizontal)
        self._signal_weight: Optional[float] = None  # Signal weight W_s (commitment quota, vertical)
        
        # Arc type flags (mutually exclusive except curved+type combinations)
        self._is_inhibitor = False
        self._is_test = False
        self._is_signal_flow = False
        self._is_curved = False
        
        # Configuration
        self._threshold: Optional[float] = None  # For inhibitor arcs
        self._control_points: Optional[List[Tuple[float, float]]] = None  # For curved arcs
        self._control_offset_x: float = 0.0  # Alternative: offset from midpoint
        self._control_offset_y: float = 0.0
        
        # Optional properties
        self._id: Optional[str] = None
        self._name: Optional[str] = None
        self._label: Optional[str] = None
        self._color: Optional[Tuple[float, float, float]] = None
        
        # Thermodynamic constraint tuple Γ = (K, n, ε)
        self._michaelis_K: Optional[float] = None
        self._hill_n: Optional[float] = None
        self._suppression_epsilon: Optional[float] = None
        
        # Arrhenius temperature dependence
        self._activation_energy: Optional[float] = None
        self._reference_temperature: Optional[float] = None
        
        # Lifecycle tracking (optional)
        self._id_manager: Optional[Any] = None
        
        # Custom properties and metadata
        self._properties: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
    
    # ========== Source and Target Configuration ==========
    
    def from_place(self, place: Union[str, Place]) -> 'ArcBuilder':
        """Set source as place (by ID string or Place object).
        
        Args:
            place: Place ID (e.g., "ATP", "P1") or Place object instance
        
        Returns:
            Self for method chaining
        
        Example:
            .from_place("ATP")  # By ID (resolved during build)
            .from_place(atp_place)  # By object
        """
        self._source = place
        return self
    
    def from_transition(self, transition: Union[str, Transition]) -> 'ArcBuilder':
        """Set source as transition (by ID string or Transition object).
        
        Args:
            transition: Transition ID (e.g., "T1", "glycolysis") or Transition object
        
        Returns:
            Self for method chaining
        
        Example:
            .from_transition("glycolysis")
        """
        self._source = transition
        return self
    
    def to_place(self, place: Union[str, Place]) -> 'ArcBuilder':
        """Set target as place (by ID string or Place object).
        
        Args:
            place: Place ID (e.g., "pyruvate", "P2") or Place object instance
        
        Returns:
            Self for method chaining
        
        Example:
            .to_place("pyruvate")
        """
        self._target = place
        return self
    
    def to_transition(self, transition: Union[str, Transition]) -> 'ArcBuilder':
        """Set target as transition (by ID string or Transition object).
        
        Args:
            transition: Transition ID (e.g., "T2", "commit") or Transition object
        
        Returns:
            Self for method chaining
        
        Example:
            .to_transition("commit")
        """
        self._target = transition
        return self
    
    # ========== Arc Type Selection ==========
    
    def as_inhibitor(self) -> 'ArcBuilder':
        """Configure as inhibitor arc (inverted enablement logic).
        
        Inhibitor arcs have inverted semantics:
        - Transition enabled when M(p) < threshold (instead of ≥)
        - Only valid for Place → Transition direction
        - Rendered with hollow circle endpoint
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: During build() if source is not a Place
        
        Example:
            .as_inhibitor().with_threshold(10)
        
        See:
            doc/SIGNAL_HIERARCHICAL_FORMALISM.md - "Arc Semantics" section
        """
        self._is_inhibitor = True
        return self
    
    def as_test(self) -> 'ArcBuilder':
        """Configure as test arc (non-consuming catalyst).
        
        Test arcs implement catalysis without token consumption:
        - Enablement: M(p) ≥ W_t (tokens required)
        - Firing: M'(p) = M(p) (no change, read-only)
        - Use case: Enzyme catalysis, regulatory proteins
        
        Distinction from signal flow arcs:
        - Test arc: Non-consuming (catalysis)
        - Signal flow arc: Consuming (commitment)
        
        Returns:
            Self for method chaining
        
        Example:
            .as_test().with_weight(1)  # Requires 1 enzyme present
        
        See:
            doc/SIGNAL_HIERARCHICAL_FORMALISM.md - "Arc Semantics" table
        """
        self._is_test = True
        return self
    
    def as_signal_flow(self) -> 'ArcBuilder':
        """Configure as signal flow arc (SHPN vertical information broadcast).
        
        Signal flow arcs implement consumptive commitment semantics:
        - Must connect to signal place (is_signal_place=True)
        - Enablement: M(p_s) ≥ θ(t) + W_s (threshold + quota)
        - Firing: M'(p_s) = M(p_s) - W_s (consumes decision quota)
        - Creates: Basin boundaries, irreversibility, threshold predictability
        
        Use with .with_signal_weight(W_s) to set commitment quota.
        
        Returns:
            Self for method chaining
        
        Example:
            # ATP gating sporulation (B. subtilis case study)
            .from_place("ATP")
            .to_transition("commit")
            .as_signal_flow()
            .with_signal_weight(0.17)  # W_s = 0.17 mM (decision quota)
        
        See:
            doc/SIGNAL_HIERARCHICAL_FORMALISM.md - "Signal Flow Arcs" section
            Section on commitment threshold formula: M_commit = θ + W_s
        """
        self._is_signal_flow = True
        return self
    
    def as_curved(self) -> 'ArcBuilder':
        """Configure as curved arc (bezier path rendering).
        
        Curved arcs use bezier curves for visual clarity when multiple arcs
        connect the same nodes. Can be combined with any arc type.
        
        Use with:
        - .with_control_points([(x1,y1), (x2,y2)]) for explicit control points
        - .with_control_offset(dx, dy) for midpoint offset
        
        Returns:
            Self for method chaining
        
        Example:
            .as_curved().with_control_points([(160, 180)])
        
        Compatible with all types:
        - Normal curved: .as_curved()
        - Curved inhibitor: .as_inhibitor().as_curved()
        - Curved signal flow: .as_signal_flow().as_curved()
        """
        self._is_curved = True
        return self
    
    # ========== Weights (Dual Arc Semantics for SHPN) ==========
    
    def with_weight(self, weight: float) -> 'ArcBuilder':
        """Set normal arc weight W (stoichiometric coefficient).
        
        Normal weight represents horizontal mass transfer:
        - Consumption: tokens consumed from place
        - Production: tokens produced to place
        - Stoichiometry: biochemical reaction coefficients
        
        For signal flow arcs, W represents normal mass participation while
        W_s (set via with_signal_weight) represents signal commitment quota.
        
        Args:
            weight: Arc weight (typically positive integer, can be float for
                   continuous/hybrid models)
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If weight < 0
        
        Example:
            .with_weight(2)  # Consume 2 tokens
        
        See:
            doc/SIGNAL_HIERARCHICAL_FORMALISM.md - "Dual Arc Semantics"
        """
        if weight < 0:
            raise ValueError(f"Arc weight must be non-negative, got {weight}")
        self._weight = float(weight)
        return self
    
    def with_gamma(self, K: float, n: float = 1.0, epsilon: float = 0.0) -> 'ArcBuilder':
        """Set thermodynamic constraint tuple Γ = (K, n, ε).
        
        Γ replaces the static commitment threshold θ with enzyme-kinetic
        parameters from which θ_eff emerges:
            θ_eff = K · (ε / (1 - ε))^(1/n)
        
        Only meaningful on signal flow arcs. When ε = 0, θ_eff = 0
        (backward compatible default).
        
        Args:
            K: Michaelis constant (mM). Half-saturation concentration.
            n: Hill coefficient (dimensionless, default 1.0).
            epsilon: Rate suppression threshold ε ∈ [0, 1). Fraction of
                    V_max below which the transition is effectively off.
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If K < 0, n <= 0, or ε ∉ [0, 1)
        
        Example - B. subtilis sporulation:
            .from_place("ATP")
            .to_transition("commit")
            .as_signal_flow()
            .with_signal_weight(0.17)
            .with_gamma(K=2.04, n=1.0, epsilon=0.52)
            # → θ_eff ≈ 2.21 mM, M_commit ≈ 2.38 mM
        """
        if K < 0:
            raise ValueError(f"Michaelis constant K must be non-negative, got {K}")
        if n <= 0:
            raise ValueError(f"Hill coefficient n must be positive, got {n}")
        if not (0.0 <= epsilon < 1.0):
            raise ValueError(f"Suppression epsilon must be in [0, 1), got {epsilon}")
        self._michaelis_K = float(K)
        self._hill_n = float(n)
        self._suppression_epsilon = float(epsilon)
        return self
    
    def with_arrhenius(self, activation_energy: float,
                       reference_temperature: float = 298.15) -> 'ArcBuilder':
        """Set Arrhenius temperature dependence for K(T).
        
        When activation_energy > 0, K becomes temperature-dependent:
            K(T) = K_ref · exp(−E_a/R · (1/T − 1/T_ref))
        
        Requires with_gamma() to be called first or afterwards.
        Only meaningful on signal flow arcs.
        
        Args:
            activation_energy: Activation energy E_a in kJ/mol.
                Must be non-negative.
            reference_temperature: Reference temperature T_ref in Kelvin
                (default 298.15 K = 25°C). Must be positive.
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If activation_energy < 0 or reference_temperature <= 0
        """
        if activation_energy < 0:
            raise ValueError(
                f"Activation energy must be non-negative, got {activation_energy}")
        if reference_temperature <= 0:
            raise ValueError(
                f"Reference temperature must be positive, got {reference_temperature}")
        self._activation_energy = float(activation_energy)
        self._reference_temperature = float(reference_temperature)
        return self
    
    def with_signal_weight(self, signal_weight: float) -> 'ArcBuilder':
        """Set signal arc weight W_s (commitment quota, SHPN).
        
        Signal weight represents vertical information broadcast:
        - Decision quota consumed on firing
        - Creates basin boundaries via M_commit = θ + W_s
        - Enables first-principles threshold prediction
        - Distinct from normal weight W (stoichiometry)
        
        Dual arc semantics:
        - Place with both normal and signal arcs:
          M'(p) = M(p) - W - W_s + W_out + W_s_out
        
        Args:
            signal_weight: Signal arc weight W_s (commitment quota in concentration
                          units, must be positive)
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If signal_weight <= 0
        
        Example - B. subtilis sporulation:
            .from_place("ATP")  # Signal place at Layer 0
            .to_transition("commit")  # θ(commit) = 2.21 mM
            .as_signal_flow()
            .with_signal_weight(0.17)  # W_s = 0.17 mM
            # → M_commit(ATP) = 2.21 + 0.17 = 2.38 mM
        
        See:
            doc/SIGNAL_HIERARCHICAL_FORMALISM.md - Sections:
            - "Dual Arc Semantics"
            - "Commitment Thresholds"
            - "B. subtilis Validation Example"
        """
        if signal_weight <= 0:
            raise ValueError(f"Signal weight must be positive (W_s ∈ ℝ⁺), got {signal_weight}")
        self._signal_weight = float(signal_weight)
        return self
    
    # ========== Configuration ==========
    
    def with_threshold(self, threshold: float) -> 'ArcBuilder':
        """Set inhibitor arc threshold (for inverted enablement logic).
        
        Inhibitor arc enablement:
        - Enabled when: M(p) < threshold (below threshold)
        - Disabled when: M(p) ≥ threshold (at or above threshold)
        
        Args:
            threshold: Token count threshold for inhibition
        
        Returns:
            Self for method chaining
        
        Example:
            .as_inhibitor().with_threshold(10)
            # → Enabled when place has < 10 tokens
        """
        self._threshold = float(threshold)
        return self
    
    def with_control_points(self, points: List[Tuple[float, float]]) -> 'ArcBuilder':
        """Set bezier control points for curved arcs.
        
        Control points define the bezier curve path between source and target.
        Typically 1-2 control points for quadratic/cubic bezier.
        
        Args:
            points: List of (x, y) control point coordinates
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If used without .as_curved()
        
        Example:
            .as_curved()
            .with_control_points([(160, 180), (170, 190)])
        """
        self._control_points = points
        return self
    
    def with_control_offset(self, offset_x: float, offset_y: float) -> 'ArcBuilder':
        """Set control point offset from arc midpoint (alternative to explicit points).
        
        Generates control point at: midpoint + (offset_x, offset_y)
        Simpler than explicit control points for symmetric curves.
        
        Args:
            offset_x: X offset from midpoint
            offset_y: Y offset from midpoint
        
        Returns:
            Self for method chaining
        
        Example:
            .as_curved().with_control_offset(20, 30)
        """
        self._control_offset_x = float(offset_x)
        self._control_offset_y = float(offset_y)
        return self
    
    # ========== Optional Properties ==========
    
    def with_id(self, arc_id: str) -> 'ArcBuilder':
        """Set arc ID (otherwise auto-generated during build).
        
        Args:
            arc_id: Unique arc identifier
        
        Returns:
            Self for method chaining
        
        Example:
            .with_id("A_ATP_to_commit")
        """
        self._id = arc_id
        return self
    
    def with_name(self, name: str) -> 'ArcBuilder':
        """Set arc name (otherwise auto-generated during build).
        
        Args:
            name: Arc name (often same as ID)
        
        Returns:
            Self for method chaining
        """
        self._name = name
        return self
    
    def with_label(self, label: str) -> 'ArcBuilder':
        """Set arc label (displayed on canvas near arc).
        
        Args:
            label: User-visible label text
        
        Returns:
            Self for method chaining
        
        Example:
            .with_label("ATP → Commitment")
        """
        self._label = label
        return self
    
    def with_color(self, r: float, g: float, b: float) -> 'ArcBuilder':
        """Set arc color (RGB 0.0-1.0).
        
        Note: Arc colors are typically managed by ColorSchemaManager.
        This method overrides automatic coloring.
        
        Args:
            r: Red component (0.0-1.0)
            g: Green component (0.0-1.0)
            b: Blue component (0.0-1.0)
        
        Returns:
            Self for method chaining
        
        Example:
            .with_color(0.7, 0.7, 0.7)  # Light gray
        """
        self._color = (float(r), float(g), float(b))
        return self
    
    # ========== Custom Properties and Metadata ==========
    
    def with_property(self, key: str, value: Any) -> 'ArcBuilder':
        """Set custom property.
        
        Args:
            key: Property key
            value: Property value
        
        Returns:
            Self for method chaining
        
        Example:
            .with_property("formula", "2*[ATP]")
        """
        self._properties[key] = value
        return self
    
    def with_metadata(self, **kwargs) -> 'ArcBuilder':
        """Set metadata (annotations, provenance).
        
        Args:
            **kwargs: Metadata key-value pairs
        
        Returns:
            Self for method chaining
        
        Example:
            .with_metadata(
                source="KEGG",
                reaction_id="R00200",
                reversible=False
            )
        """
        self._metadata.update(kwargs)
        return self
    
    # ========== Build ==========
    
    def build(self, resolve_refs: Optional[Dict[str, Any]] = None) -> 'Arc':
        """Construct the arc with all configured properties.
        
        Args:
            resolve_refs: Optional dictionary mapping IDs to Place/Transition objects.
                         If source/target are ID strings, they will be resolved from
                         this dict. If None, source/target must already be objects.
        
        Returns:
            Appropriate Arc subclass instance (Arc, InhibitorArc, TestArc, etc.)
        
        Raises:
            ValueError: If configuration is invalid
            TypeError: If source/target types are incompatible
        
        Example:
            # With object references
            arc = ArcBuilder().from_place(atp).to_transition(commit).build()
            
            # With ID resolution
            refs = {"ATP": atp_place, "commit": commit_transition}
            arc = ArcBuilder().from_place("ATP").to_transition("commit").build(refs)
        """
        # Validate configuration
        self._validate()
        
        # Resolve source and target
        source = self._resolve_reference(self._source, resolve_refs)
        target = self._resolve_reference(self._target, resolve_refs)
        
        # Generate ID and name if not provided
        arc_id = self._id or self._generate_id(source, target)
        arc_name = self._name or arc_id
        
        # Determine arc class based on type flags
        arc_class = self._determine_arc_class()
        
        # Create arc
        # For signal flow arcs, weight = W_s (signal weight / commitment quota)
        build_weight = self._weight
        if self._is_signal_flow and self._signal_weight is not None:
            build_weight = self._signal_weight
        arc = arc_class(source, target, arc_id, arc_name, weight=build_weight)
        
        # Set optional properties
        if self._threshold is not None:
            arc.threshold = self._threshold
        
        if self._signal_weight is not None:
            # Store signal weight in properties (SignalFlowArc may not have attribute yet)
            if hasattr(arc, 'signal_weight'):
                arc.signal_weight = self._signal_weight
            else:
                arc.properties['signal_weight'] = self._signal_weight
        
        if self._control_points:
            arc.control_points = self._control_points.copy()
        
        if self._control_offset_x != 0.0 or self._control_offset_y != 0.0:
            arc.control_offset_x = self._control_offset_x
            arc.control_offset_y = self._control_offset_y
        
        # Apply Γ parameters to signal flow arcs
        if self._michaelis_K is not None and hasattr(arc, 'michaelis_K'):
            arc.michaelis_K = self._michaelis_K
            arc.hill_n = self._hill_n if self._hill_n is not None else 1.0
            arc.suppression_epsilon = self._suppression_epsilon if self._suppression_epsilon is not None else 0.0
        
        # Apply Arrhenius parameters
        if self._activation_energy is not None and hasattr(arc, 'activation_energy'):
            arc.activation_energy = self._activation_energy
        if self._reference_temperature is not None and hasattr(arc, 'reference_temperature'):
            arc.reference_temperature = self._reference_temperature
        
        if self._label:
            arc.label = self._label
        
        if self._color:
            arc.color = self._color
        
        # Custom properties and metadata
        if self._properties:
            arc.properties.update(self._properties)
        
        if self._metadata:
            arc.metadata.update(self._metadata)
        
        # Lifecycle tracking (Week 2 - Phase 4)
        # Register object with IDManager for lifecycle observation
        if self._id_manager and hasattr(self._id_manager, 'register_object'):
            try:
                self._id_manager.register_object(arc, obj_type='arc')
            except (AttributeError, TypeError, RuntimeError) as e:
                # Lifecycle tracking optional, don't break build
                from shypn.utils.logging import get_logger
                logger = get_logger(__name__)
                logger.debug(f"Failed to register arc with lifecycle ID manager: {e}")
        
        return arc
    
    # ========== Internal Helper Methods ==========
    
    def _validate(self):
        """Validate builder configuration before construction.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if self._source is None:
            raise ValueError("Arc must have a source (use .from_place() or .from_transition())")
        
        if self._target is None:
            raise ValueError("Arc must have a target (use .to_place() or .to_transition())")
        
        # Validate inhibitor arc direction (must be Place → Transition)
        if self._is_inhibitor:
            # Check if source is place-like (has tokens attribute or is string ending in place pattern)
            source_is_place = self._looks_like_place(self._source)
            if not source_is_place:
                raise ValueError(
                    "Inhibitor arcs must go from Place to Transition. "
                    f"Got source={self._source} which appears to be a Transition."
                )
        
        # Validate mutually exclusive arc types
        type_count = sum([self._is_inhibitor, self._is_test, self._is_signal_flow])
        if type_count > 1:
            raise ValueError(
                "Arc types are mutually exclusive. Cannot combine: "
                "inhibitor, test, and signal_flow. "
                "(Curved can be combined with any type.)"
            )
        
        # Validate control points require curved flag
        if self._control_points and not self._is_curved:
            raise ValueError(
                "Control points require .as_curved() to be called"
            )
        
        # Validate Γ requires signal flow arc
        if self._michaelis_K is not None and not self._is_signal_flow:
            raise ValueError(
                "Γ parameters (with_gamma) require .as_signal_flow() — "
                "thermodynamic constraints only apply to signal flow arcs."
            )
        
        # Validate Arrhenius requires signal flow arc
        if self._activation_energy is not None and not self._is_signal_flow:
            raise ValueError(
                "Arrhenius parameters (with_arrhenius) require .as_signal_flow() — "
                "temperature dependence only applies to signal flow arcs."
            )
    
    def _looks_like_place(self, obj: Any) -> bool:
        """Heuristic to determine if object is a Place.
        
        Args:
            obj: Object or string ID to check
        
        Returns:
            True if likely a Place, False otherwise
        """
        if isinstance(obj, str):
            # String ID - cannot determine type definitively, assume valid
            return True
        
        # Check if it's actually a Place instance
        return isinstance(obj, Place)
    
    def _resolve_reference(self, ref: Union[str, Any], resolve_refs: Optional[Dict[str, Any]]) -> Any:
        """Resolve ID string to object or return object as-is.
        
        Args:
            ref: Reference (ID string or object)
            resolve_refs: Dictionary mapping IDs to objects
        
        Returns:
            Resolved object
        
        Raises:
            ValueError: If ID string cannot be resolved
        """
        if isinstance(ref, str):
            if resolve_refs is None:
                raise ValueError(
                    f"Cannot resolve ID '{ref}' without resolve_refs dictionary. "
                    "Either pass object instances instead of IDs, or provide resolve_refs."
                )
            
            if ref not in resolve_refs:
                raise ValueError(
                    f"Cannot resolve ID '{ref}'. Not found in resolve_refs dictionary. "
                    f"Available IDs: {list(resolve_refs.keys())}"
                )
            
            return resolve_refs[ref]
        
        return ref
    
    def _determine_arc_class(self):
        """Determine appropriate Arc subclass based on type flags.
        
        Returns:
            Arc subclass (Arc, InhibitorArc, TestArc, etc.)
        """
        from shypn.netobjs.arc import Arc
        from shypn.netobjs.curved_arc import CurvedArc
        from shypn.netobjs.inhibitor_arc import InhibitorArc
        from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
        from shypn.netobjs.test_arc import TestArc
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        from shypn.netobjs.curved_signal_flow_arc import CurvedSignalFlowArc
        
        # Determine class based on type flags
        if self._is_test:
            return TestArc
        elif self._is_inhibitor and self._is_curved:
            return CurvedInhibitorArc
        elif self._is_inhibitor:
            return InhibitorArc
        elif self._is_signal_flow and self._is_curved:
            return CurvedSignalFlowArc
        elif self._is_signal_flow:
            return SignalFlowArc
        elif self._is_curved:
            return CurvedArc
        else:
            return Arc  # Default: normal arc
    
    def _generate_id(self, source: Any, target: Any) -> str:
        """Generate arc ID from source and target.
        
        Args:
            source: Source object
            target: Target object
        
        Returns:
            Generated ID string
        """
        try:
            from shypn.data.canvas.id_manager import IDManager
            return IDManager.get_instance().generate_arc_id()
        except (ImportError, AttributeError, RuntimeError) as e:
            # Fallback if IDManager not available or fails
            import logging


            logging.getLogger(__name__).debug(f"IDManager unavailable, using fallback ID generation: {e}")
            source_id = getattr(source, 'id', str(source))
            target_id = getattr(target, 'id', str(target))
            return f"A_{source_id}_to_{target_id}"
    
    # ========== Convenience Methods ==========
    
    def __repr__(self) -> str:
        """String representation for debugging.
        
        Returns:
            Descriptive string
        """
        source_str = getattr(self._source, 'id', str(self._source)) if self._source else "?"
        target_str = getattr(self._target, 'id', str(self._target)) if self._target else "?"
        
        arc_type = "normal"
        if self._is_inhibitor:
            arc_type = "inhibitor"
        elif self._is_test:
            arc_type = "test"
        elif self._is_signal_flow:
            arc_type = "signal_flow"
        
        if self._is_curved:
            arc_type = f"curved_{arc_type}"
        
        weight_info = f", W={self._weight}"
        if self._signal_weight is not None:
            weight_info += f", W_s={self._signal_weight}"
        if self._michaelis_K is not None:
            weight_info += f", Γ=(K={self._michaelis_K}, n={self._hill_n}, ε={self._suppression_epsilon})"
        if self._activation_energy is not None:
            weight_info += f", E_a={self._activation_energy} kJ/mol, T_ref={self._reference_temperature} K"
        
        return (f"ArcBuilder({source_str} → {target_str}, "
                f"type={arc_type}{weight_info})")

