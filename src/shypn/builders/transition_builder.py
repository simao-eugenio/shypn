"""TransitionBuilder - Fluent interface for Transition construction.

Provides a builder pattern for creating transitions with all 5 behavioral types:
- Immediate: Zero-delay firing with priority resolution
- Timed: Deterministic delay before firing
- Stochastic: Exponential distribution of delays (Gillespie)
- Continuous: ODE-based rate functions
- Adaptive: Hybrid continuous/stochastic switching

Supports SHPN signal hierarchy with enablement thresholds θ(t).

Example:
    # Continuous transition with rate function
    t = (TransitionBuilder("glycolysis")
         .at_position(150, 200)
         .as_continuous()
         .with_rate_function("0.5 * [glucose]")
         .build())
    
    # Stochastic transition
    t = (TransitionBuilder("binding")
         .at_position(200, 150)
         .as_stochastic()
         .with_rate(10.0)
         .build())
    
    # SHPN signal-enabled transition
    t = (TransitionBuilder("commit")
         .at_position(250, 200)
         .as_immediate()
         .with_enablement_threshold(2.21)  # θ(t) = 2.21 mM ATP
         .with_priority(10)
         .build())
"""

from typing import Optional, List, Union
from shypn.netobjs.transition import Transition


class TransitionBuilder:
    """Fluent builder for Transition objects with 5 behavioral types.
    
    Supports all transition types:
    - Immediate: .as_immediate() + .with_priority()
    - Timed: .as_timed() + .with_delay()
    - Stochastic: .as_stochastic() + .with_rate()
    - Continuous: .as_continuous() + .with_rate_function()
    - Adaptive: .as_adaptive() + .with_adaptive_params()
    
    SHPN Support:
    - .with_enablement_threshold(θ): Minimum signal concentration for enablement
    - .with_signal_places([p1, p2]): Signal dependencies (quorum sensing)
    
    Module/Compartment:
    - .with_module(module_id): Modular network architecture
    
    Source/Sink:
    - .as_source(): Generates tokens without input
    - .as_sink(): Consumes tokens without output
    """
    
    def __init__(self, name: str = None, *, id_manager=None):
        """Initialize TransitionBuilder.
        
        Args:
            name: Optional transition name (defaults to auto-generated T1, T2, etc.)
            id_manager: IDManager instance from document (keyword-only, if None creates standalone)
        """
        # Identity
        self._name = name
        self._id = None
        self._label = ""
        self._id_manager = id_manager  # Use document's id_manager if provided
        
        # Position and dimensions
        self._x = 0.0
        self._y = 0.0
        self._width = None  # Use Transition.DEFAULT_WIDTH if None
        self._height = None  # Use Transition.DEFAULT_HEIGHT if None
        self._horizontal = True
        
        # Behavioral properties
        self._transition_type = 'continuous'  # Default to continuous
        self._enabled = True
        self._guard = 1  # Default: always enabled
        self._rate = 1.0  # Default rate
        self._priority = 0
        self._firing_policy = 'race'  # Default: biologically realistic
        
        # Rate functions
        self._rate_function = None
        self._rate_forward = None
        self._rate_reverse = None
        
        # SHPN signal hierarchy
        self._enablement_threshold = None  # θ(t) - minimum signal concentration
        self._signal_places = []  # Signal dependencies (quorum sensing)
        self._is_environment_aware = False
        
        # Source/sink markers
        self._is_source = False
        self._is_sink = False
        
        # Module assignment
        self._module_id = None
        
        # Custom properties and metadata
        self._properties = {}
        self._metadata = {}
    
    # ========== Position and Dimensions ==========
    
    def at_position(self, x: float, y: float) -> 'TransitionBuilder':
        """Set transition position (center coordinates).
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
        
        Returns:
            Self for method chaining
        """
        self._x = float(x)
        self._y = float(y)
        return self
    
    def with_dimensions(self, width: float, height: float) -> 'TransitionBuilder':
        """Set transition dimensions.
        
        Args:
            width: Rectangle width (horizontal) or height (vertical)
            height: Rectangle height (horizontal) or width (vertical)
        
        Returns:
            Self for method chaining
        """
        self._width = float(width)
        self._height = float(height)
        return self
    
    def as_vertical(self) -> 'TransitionBuilder':
        """Render transition as vertical bar instead of horizontal.
        
        Returns:
            Self for method chaining
        """
        self._horizontal = False
        return self
    
    def with_label(self, label: str) -> 'TransitionBuilder':
        """Set display label.
        
        Args:
            label: User-visible label (e.g., "Glycolysis", "ATP synthesis")
        
        Returns:
            Self for method chaining
        """
        self._label = str(label)
        return self
    
    # ========== Type Selection ==========
    
    def as_immediate(self) -> 'TransitionBuilder':
        """Configure as immediate transition (zero-delay).
        
        Immediate transitions fire instantly when enabled.
        Use .with_priority() for conflict resolution.
        
        Returns:
            Self for method chaining
        """
        self._transition_type = 'immediate'
        return self
    
    def as_timed(self) -> 'TransitionBuilder':
        """Configure as timed transition (deterministic delay).
        
        Timed transitions fire after a fixed delay.
        Use .with_delay() to set the delay period.
        
        Returns:
            Self for method chaining
        """
        self._transition_type = 'timed'
        return self
    
    def as_stochastic(self) -> 'TransitionBuilder':
        """Configure as stochastic transition (Gillespie algorithm).
        
        Stochastic transitions fire with exponentially distributed delays.
        Use .with_rate() to set the reaction rate constant.
        
        Returns:
            Self for method chaining
        """
        self._transition_type = 'stochastic'
        return self
    
    def as_continuous(self) -> 'TransitionBuilder':
        """Configure as continuous transition (ODE-based).
        
        Continuous transitions use rate functions for deterministic dynamics.
        Use .with_rate_function() to set the rate expression.
        
        Returns:
            Self for method chaining
        """
        self._transition_type = 'continuous'
        return self
    
    def as_adaptive(self) -> 'TransitionBuilder':
        """Configure as adaptive transition (hybrid continuous/stochastic).
        
        Adaptive transitions switch between continuous and stochastic modes
        based on population size (high population → continuous, low → stochastic).
        
        Use .with_rate_function() and .with_rate() for both modes.
        
        Returns:
            Self for method chaining
        """
        self._transition_type = 'adaptive'
        return self
    
    # ========== Rate Configuration ==========
    
    def with_rate(self, rate: float) -> 'TransitionBuilder':
        """Set constant rate for timed/stochastic transitions.
        
        Args:
            rate: Rate constant (inverse time units)
                  - Timed: 1/delay (e.g., rate=0.5 → delay=2 time units)
                  - Stochastic: reaction rate constant (Gillespie)
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If rate is negative
        """
        if rate < 0:
            raise ValueError("Rate must be non-negative")
        self._rate = float(rate)
        return self
    
    def with_delay(self, delay: float) -> 'TransitionBuilder':
        """Set deterministic delay for timed transitions (convenience method).
        
        Converts delay to rate: rate = 1/delay
        
        Args:
            delay: Time delay before firing
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If delay is non-positive
        """
        if delay <= 0:
            raise ValueError("Delay must be positive")
        self._rate = 1.0 / float(delay)
        return self
    
    def with_rate_function(self, expression: str) -> 'TransitionBuilder':
        """Set rate function for continuous/adaptive transitions.
        
        Args:
            expression: Rate function formula (e.g., "0.5 * [glucose]")
                       Can reference place markings using [place_name] syntax
        
        Returns:
            Self for method chaining
        
        Example:
            .with_rate_function("k_cat * [enzyme] * [substrate] / (K_m + [substrate])")
        """
        self._rate_function = str(expression)
        return self
    
    def with_reversible_rates(self, forward: str, reverse: str) -> 'TransitionBuilder':
        """Set forward and reverse rate functions for reversible reactions.
        
        Args:
            forward: Forward rate expression
            reverse: Reverse rate expression
        
        Returns:
            Self for method chaining
        
        Example:
            .with_reversible_rates(
                forward="k_f * [A] * [B]",
                reverse="k_r * [C]"
            )
        """
        self._rate_forward = str(forward)
        self._rate_reverse = str(reverse)
        return self
    
    # ========== Priority and Guard ==========
    
    def with_priority(self, priority: int) -> 'TransitionBuilder':
        """Set priority for conflict resolution.
        
        Higher priority transitions fire first when multiple are enabled.
        
        Args:
            priority: Priority level (higher = higher priority, default 0)
        
        Returns:
            Self for method chaining
        """
        self._priority = int(priority)
        return self
    
    def with_guard(self, guard_expression: Union[str, int, float]) -> 'TransitionBuilder':
        """Set guard condition (enables/disables transition).
        
        Args:
            guard_expression: Guard function/expression
                            - 1 (default): Always enabled
                            - 0: Always disabled
                            - String: Expression evaluated at runtime
        
        Returns:
            Self for method chaining
        
        Example:
            .with_guard("[ATP] > 5")  # Enable only when ATP > 5
        """
        self._guard = guard_expression
        return self
    
    def with_firing_policy(self, policy: str) -> 'TransitionBuilder':
        """Set firing policy for conflict resolution.
        
        Args:
            policy: Firing policy
                   - 'race': Biologically realistic (default)
                   - 'random': Random selection
                   - 'earliest': First-enabled fires
                   - 'latest': Last-enabled fires
                   - 'priority': Priority-based
                   - 'age': Oldest-enabled fires
                   - 'preemptive-priority': High-priority preempts low-priority
        
        Returns:
            Self for method chaining
        """
        valid_policies = ['race', 'random', 'earliest', 'latest', 'priority', 'age', 'preemptive-priority']
        if policy not in valid_policies:
            raise ValueError(f"Invalid firing policy: {policy}. Must be one of {valid_policies}")
        self._firing_policy = policy
        return self
    
    # ========== SHPN Signal Hierarchy ==========
    
    def with_enablement_threshold(self, threshold: float) -> 'TransitionBuilder':
        """Set enablement threshold θ(t) for SHPN signal hierarchy.
        
        The enablement condition for signal flow arcs is:
            M(p_s) ≥ θ(t) + W_s((p_s,t))
        
        Where:
        - M(p_s): Current marking of signal place
        - θ(t): Enablement threshold (this value)
        - W_s: Signal arc weight (decision quota)
        
        Commitment threshold: M_commit = θ(t) + W_s
        
        Args:
            threshold: Minimum signal concentration (θ ∈ ℝ≥⁰)
        
        Returns:
            Self for method chaining
        
        Example (B. subtilis sporulation):
            .with_enablement_threshold(2.21)  # θ = 2.21 mM ATP
        """
        if threshold < 0:
            raise ValueError("Enablement threshold must be non-negative")
        self._enablement_threshold = float(threshold)
        return self
    
    def with_signal_places(self, place_ids: List[str]) -> 'TransitionBuilder':
        """Set signal place dependencies (quorum sensing, environmental signals).
        
        Signal places are sensed by the transition without direct arc connections.
        Example: AHL concentration in bacterial quorum sensing.
        
        Args:
            place_ids: List of signal place IDs (e.g., ['P10', 'P15'])
        
        Returns:
            Self for method chaining
        """
        self._signal_places = list(place_ids)
        self._is_environment_aware = len(place_ids) > 0
        return self
    
    # ========== Source/Sink Markers ==========
    
    def as_source(self) -> 'TransitionBuilder':
        """Mark transition as source (generates tokens without input).
        
        Source transitions model boundary conditions like nutrient influx.
        
        Returns:
            Self for method chaining
        """
        self._is_source = True
        return self
    
    def as_sink(self) -> 'TransitionBuilder':
        """Mark transition as sink (consumes tokens without output).
        
        Sink transitions model boundary conditions like waste removal.
        
        Returns:
            Self for method chaining
        """
        self._is_sink = True
        return self
    
    # ========== Module/Compartment ==========
    
    def with_module(self, module_id: str) -> 'TransitionBuilder':
        """Assign transition to a module (modular network architecture).
        
        Args:
            module_id: Module identifier (e.g., "M_cytoplasm", "M_mitochondria")
        
        Returns:
            Self for method chaining
        """
        self._module_id = str(module_id)
        return self
    
    # ========== Optional Properties ==========
    
    def with_id(self, transition_id: str) -> 'TransitionBuilder':
        """Set custom transition ID.
        
        Args:
            transition_id: Unique identifier
        
        Returns:
            Self for method chaining
        """
        self._id = str(transition_id)
        return self
    
    def disabled(self) -> 'TransitionBuilder':
        """Disable transition (cannot fire).
        
        Returns:
            Self for method chaining
        """
        self._enabled = False
        return self
    
    def with_property(self, key: str, value) -> 'TransitionBuilder':
        """Set custom property (stored in properties dict).
        
        Args:
            key: Property name
            value: Property value
        
        Returns:
            Self for method chaining
        """
        self._properties[key] = value
        return self
    
    def with_metadata(self, **kwargs) -> 'TransitionBuilder':
        """Set metadata (annotations, provenance).
        
        Args:
            **kwargs: Metadata key-value pairs
        
        Returns:
            Self for method chaining
        
        Example:
            .with_metadata(source="KEGG", pathway="Glycolysis")
        """
        self._metadata.update(kwargs)
        return self
    
    # ========== Build ==========
    
    def build(self) -> Transition:
        """Construct Transition object with validation.
        
        Returns:
            Transition: Configured transition object
        
        Raises:
            ValueError: If configuration is invalid
        """
        self._validate()
        
        # Generate ID if not provided
        if self._id is None:
            if self._id_manager is None:
                # Standalone builder - create temporary id_manager
                from shypn.data.canvas.id_manager import IDManager
                self._id_manager = IDManager()
            self._id = self._id_manager.generate_transition_id()
        
        # Generate name if not provided
        if self._name is None:
            self._name = self._id  # Use ID as name
        
        # Set default rate function for continuous/adaptive if not provided
        if self._transition_type in ['continuous', 'adaptive'] and self._rate_function is None:
            self._rate_function = "1"  # Default rate function
        
        # Create transition
        transition = Transition(
            x=self._x,
            y=self._y,
            id=self._id,
            name=self._name,
            width=self._width,
            height=self._height,
            label=self._label,
            horizontal=self._horizontal
        )
        
        # Set behavioral properties
        transition.transition_type = self._transition_type
        transition.enabled = self._enabled
        transition.guard = self._guard
        transition.rate = self._rate
        transition.priority = self._priority
        transition.firing_policy = self._firing_policy
        
        # Set rate functions
        if self._rate_function is not None:
            transition.rate_function = self._rate_function
        if self._rate_forward is not None:
            transition.rate_forward = self._rate_forward
        if self._rate_reverse is not None:
            transition.rate_reverse = self._rate_reverse
        
        # Set SHPN properties
        if self._enablement_threshold is not None:
            transition.properties['enablement_threshold'] = self._enablement_threshold
        transition.signal_places = self._signal_places
        transition.is_environment_aware = self._is_environment_aware
        
        # Set source/sink markers
        transition.is_source = self._is_source
        transition.is_sink = self._is_sink
        
        # Set module
        if self._module_id is not None:
            transition.module_id = self._module_id
        
        # Set custom properties and metadata
        for key, value in self._properties.items():
            transition.properties[key] = value
        for key, value in self._metadata.items():
            transition.metadata[key] = value
        
        return transition
    
    def _validate(self):
        """Validate builder configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate transition type
        valid_types = ['immediate', 'timed', 'stochastic', 'continuous', 'adaptive']
        if self._transition_type not in valid_types:
            raise ValueError(f"Invalid transition type: {self._transition_type}. "
                           f"Must be one of {valid_types}")
        
        # Validate continuous/adaptive have rate functions
        if self._transition_type in ['continuous', 'adaptive']:
            if self._rate_function is None:
                # Will be set to default "1" in build()
                pass
        
        # Validate enablement threshold
        if self._enablement_threshold is not None and self._enablement_threshold < 0:
            raise ValueError("Enablement threshold must be non-negative")
        
        # Validate rate
        if self._rate < 0:
            raise ValueError("Rate must be non-negative")
    
    def __repr__(self) -> str:
        """Return string representation for debugging.
        
        Returns:
            str: Builder state summary
        """
        parts = [f"TransitionBuilder('{self._name or 'unnamed'}'"]
        parts.append(f"type={self._transition_type}")
        parts.append(f"pos=({self._x:.1f}, {self._y:.1f})")
        
        if self._transition_type == 'immediate':
            parts.append(f"priority={self._priority}")
        elif self._transition_type in ['timed', 'stochastic']:
            parts.append(f"rate={self._rate}")
        elif self._transition_type in ['continuous', 'adaptive']:
            if self._rate_function:
                parts.append(f"rate_fn='{self._rate_function[:20]}...'")
        
        if self._enablement_threshold is not None:
            parts.append(f"θ={self._enablement_threshold}")
        
        if self._is_source:
            parts.append("source")
        if self._is_sink:
            parts.append("sink")
        
        return ", ".join(parts) + ")"
