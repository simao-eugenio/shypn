#!/usr/bin/env python3
"""SignalFlowArc - Dual-role arc in hierarchical Bio-PNs.

Signal flow arcs behave like normal arcs in terms of token flow: they consume
tokens from the source place and produce tokens at the target place on every
firing (weight Ws). Their additional role is to act as an information channel
over the normal arc: because they connect to or from signal places (Ψ), the
firing event and the current marking of those signal places are visible to the
vertical decision layers of the signal hierarchy. This allows upper layers to
read the state of lower-layer processes and issue preemptive regulatory actions
without interfering with the underlying token dynamics.

Theoretical Foundation:
- Signal Hierarchy Theory (Simão 2025)
- 13-tuple Bio-PN formalism with Ψ signal places
- Hierarchical preemption mechanism

References:
- doc/foundation/SIGNAL_FLOW_ARCS_SPECIFICATION.md
- doc/signal_hierarchy/SIGNAL_HIERARCHY_THEORY.md
"""

from shypn.netobjs.arc import Arc


# ─────────────────────────────────────────────────────────────────────────────
# Arc type comparison (13-tuple Bio-PN formalism)
#
#   Normal arc       │ Consumes tokens  │ Produces tokens  │ Hierarchy-visible? NO
#   Test arc         │ Does NOT consume │ Does NOT produce │ Hierarchy-visible? NO
#   Signal flow arc  │ Consumes tokens  │ Produces tokens  │ Hierarchy-visible? YES
#
# Signal flow arcs are topologically identical to normal arcs (same consume /
# produce semantics, same weight Ws ∈ ℝ⁺), but they connect to signal places
# (Ψ, is_signal_place=True).  That connection makes the marking of those
# places observable by the vertical decision layers of the signal hierarchy,
# allowing upper layers to sense lower-layer state and issue preemptive
# regulatory actions without altering the token dynamics themselves.
# ─────────────────────────────────────────────────────────────────────────────
class SignalFlowArc(Arc):
    """Signal flow arc with light gray color."""
    
    # Default styling for signal flow arcs
    DEFAULT_COLOR = (0.7, 0.7, 0.7)  # Light gray for signal communication
    """Arc with dual role: normal token flow + vertical information channel.

    Signal flow arcs have two simultaneous roles:

    1. **Token flow (like a normal arc)** — on every firing, Ws tokens are
       consumed from the source place and Ws tokens are produced at the target
       place.  The underlying stoichiometry is identical to a normal arc.

    2. **Vertical information channel** — because at least one endpoint is a
       signal place (Ψ, is_signal_place=True), the marking of that place and
       the fact that it participates in a firing are sensed by the vertical
       decision layers of the signal hierarchy.  Upper layers can observe the
       state of lower-layer signal places through these arcs and issue
       preemptive regulatory actions (e.g., inhibit, boost, branch) without
       altering the token dynamics themselves.

    Distinction from related types:
    - Normal arc      : token flow only; not visible to signal hierarchy.
    - Test arc        : no token flow; presence check only (non-consuming).
    - Signal flow arc : token flow (consume + produce) AND hierarchy-visible.

    Properties:
    - Connects to at least one signal place (is_signal_place=True)
    - Consumes Ws tokens from source place on firing
    - Produces Ws tokens at target place on firing
    - Marking of connected signal place(s) is readable by vertical layers
    - Rendered as light-gray arc (visually distinct from black normal arcs)

    Biological Examples:
    - EPO_external → T5_EPOR_binding  (cytokine layer signals receptor layer)
    - ATP → T15_translation           (metabolic layer signals synthesis layer)
    - GTP → T13_mRNA_export           (energy layer signals export layer)

    Usage:
        >>> signal_place = Place("P1", "EPO_external", is_signal_place=True)
        >>> transition = Transition("T5", "EPOR_binding")
        >>> arc = SignalFlowArc(signal_place, transition, "A1", "A1", weight=1.0)
        >>> arc.arc_type
        'signal_flow'
        >>> arc.consumes_tokens()   # True — tokens are consumed
        True
        >>> arc.produces_tokens()   # True — tokens are produced at target
        True
        >>> arc.is_information_arc()  # True — also sensed by hierarchy layers
        True
    """
    
    def __init__(self, source, target, id: str, name: str, weight: float = 1):
        """Initialize a signal flow arc.
        
        Args:
            source: Source object (Place or Transition)
            target: Target object (Transition or Place)
            id: Unique identifier
            name: Unique name (e.g., "A1", "A2")
            weight: Arc weight (default 1.0, can be formula)
            
        Raises:
            ValueError: If neither source nor target is a signal place
            ValueError: If weight is 0 (use TestArc for non-consuming)
        """
        super().__init__(source, target, id, name, weight)

        # Enforce semantic color via ColorSchemaManager (light gray for signal flow)
        # The base Arc.__init__ already calls CSM, but we call it again after
        # the subclass is fully initialized so the isinstance check is reliable.
        from shypn.utils.color_schema_manager import ColorSchemaManager
        ColorSchemaManager.reset_arc_color(self)

        # Enforce that every Place endpoint is a signal place (Ψ).
        # Signal flow arcs MUST connect to signal places — this is the one
        # structural restriction of the formalism.
        self._validate_signal_connection()

        # Validate weight is positive (formalism requires Ws ∈ ℝ⁺)
        self._validate_positive_weight()
    
    def _validate_signal_connection(self):
        """Verify arc connects to at least one signal place.
        
        Signal flow arcs MUST connect to signal places (Ψ) to be semantically
        valid according to the 13-tuple Bio-PN formalism.
        
        Raises:
            ValueError: If neither source nor target is a signal place
        """
        from shypn.netobjs.place import Place
        
        is_source_signal = (isinstance(self.source, Place) and 
                           getattr(self.source, 'is_signal_place', False))
        is_target_signal = (isinstance(self.target, Place) and 
                           getattr(self.target, 'is_signal_place', False))
        
        if not (is_source_signal or is_target_signal):
            raise ValueError(
                f"SignalFlowArc {self.id} must connect to at least one signal place. "
                f"Source: {self.source.name} (is_signal_place={is_source_signal}), "
                f"Target: {self.target.name} (is_signal_place={is_target_signal}). "
                f"Use normal Arc for mass transfer or TestArc for catalytic read."
            )
    
    def _validate_positive_weight(self):
        """Verify signal arc weight is positive per formalism (Ws ∈ ℝ⁺).
        
        Signal flow arcs MUST have positive weights according to the 13-tuple
        Bio-PN formalism: Ws: Fs → ℝ⁺. Weight=0 violates formalism.
        Use TestArc for non-consuming catalytic observation instead.
        
        Raises:
            ValueError: If weight is 0 or negative
        """
        # Check if weight is numeric (not formula)
        try:
            numeric_weight = float(self.weight)
            if numeric_weight <= 0:
                raise ValueError(
                    f"SignalFlowArc {self.id} has invalid weight={numeric_weight}. "
                    f"Formalism requires Ws ∈ ℝ⁺ (positive reals). "
                    f"For non-consuming catalysis (weight=0), use TestArc instead. "
                    f"For consumptive regulation, use weight > 0."
                )
        except (TypeError, ValueError) as e:
            # Weight is formula string - skip validation (will be checked at runtime)
            if "invalid weight" in str(e):
                raise  # Re-raise weight validation errors
            pass
    
    def consumes_tokens(self) -> bool:
        """Check if arc consumes tokens from source place.
        
        Signal flow arcs consume tokens to model signal depletion, distinguishing
        them from test arcs (non-consuming catalytic read).
        
        Returns:
            bool: Always True for signal flow arcs
        """
        return True
    
    def is_information_arc(self) -> bool:
        """Check if arc serves as an information channel to vertical hierarchy layers.

        Signal flow arcs have a dual role: they carry out normal token flow
        (consume from source, produce at target) AND additionally make the
        connected signal place(s) visible to the vertical decision layers of
        the signal hierarchy.  Upper layers sense the marking of these signal
        places to coordinate preemptive regulatory actions.

        This is what distinguishes a signal_flow arc from a plain normal arc:
        the normal arc moves tokens; the signal_flow arc moves tokens AND
        informs the hierarchy.

        Returns:
            bool: Always True for signal flow arcs
        """
        return True

    def produces_tokens(self) -> bool:
        """Check if arc produces tokens at target place.

        Signal flow arcs produce tokens at their target on firing, symmetrically
        with consuming tokens from their source. Both sides follow the weight Ws.

        Returns:
            bool: Always True for signal flow arcs
        """
        return True
    
    def get_semantic_role(self) -> str:
        """Get biological semantic role of this arc.
        
        Returns:
            str: "information_transfer" for signal flow arcs
        """
        return "information_transfer"
    
    def to_dict(self) -> dict:
        """Serialize signal flow arc to dictionary for persistence.
        
        Returns:
            dict: Dictionary containing all arc properties with arc_type='signal_flow'
        """
        data = super().to_dict()
        # Ensure color is always the correct light gray for signal flow arcs
        # This prevents black color from being saved and restored
        data['color'] = list(self.DEFAULT_COLOR)
        # Explicitly record consume/produce semantics (formalism: Ws ∈ ℝ⁺)
        # Symmetric with test arcs which write consumes=False
        data['consumes'] = True
        data['produces'] = True
        return data
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"SignalFlowArc(id={self.id}, {self.source.name} → {self.target.name}, "
                f"weight={self.weight}, information_transfer)")
