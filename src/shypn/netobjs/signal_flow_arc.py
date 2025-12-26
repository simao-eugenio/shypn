#!/usr/bin/env python3
"""SignalFlowArc - Information transfer arc in hierarchical Bio-PNs.

Signal flow arcs transmit regulatory information with token consumption,
enabling hierarchical control through signal depletion. They connect to
signal places (Ψ) and are visually distinct from mass transfer (normal arcs)
and catalytic read (test arcs).

Theoretical Foundation:
- Signal Hierarchy Theory (Simão 2025)
- 13-tuple Bio-PN formalism with Ψ signal places
- Hierarchical preemption mechanism

References:
- doc/foundation/SIGNAL_FLOW_ARCS_SPECIFICATION.md
- doc/signal_hierarchy/SIGNAL_HIERARCHY_THEORY.md
"""

from shypn.netobjs.arc import Arc


class SignalFlowArc(Arc):
    """Arc transmitting information with token consumption.
    
    Signal flow arcs represent information channels in hierarchical control
    systems. Unlike normal arcs (mass transfer) and test arcs (catalytic read),
    signal flow arcs consume tokens to model signal depletion - a key mechanism
    in hierarchical preemption.
    
    Properties:
    - Connects to signal places (is_signal_place=True)
    - Consumes tokens (unlike test arcs)
    - Transmits information (not mass)
    - Rendered as dashed line with angled arrowhead
    
    Biological Examples:
    - CII_Protein → CI_Transcription (integration layer signal)
    - RecA_Active → CI_Cleavage (hierarchical override signal)
    - Metabolic_Health → CII_Production (environmental signal)
    
    Usage:
        >>> signal_place = Place("P1", "CII_Protein", is_signal_place=True)
        >>> transition = Transition("T1", "CI_Transcription")
        >>> arc = SignalFlowArc(signal_place, transition, "A1", "A1", weight=1.0)
        >>> arc.arc_type  # Returns "signal_flow"
        'signal_flow'
        >>> arc.consumes_tokens()  # Returns True (unlike test arcs)
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
        """
        super().__init__(source, target, id, name, weight)
        
        # Validate that at least one endpoint is a signal place
        self._validate_signal_connection()
    
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
    
    def consumes_tokens(self) -> bool:
        """Check if arc consumes tokens from source place.
        
        Signal flow arcs consume tokens to model signal depletion, distinguishing
        them from test arcs (non-consuming catalytic read).
        
        Returns:
            bool: Always True for signal flow arcs
        """
        return True
    
    def is_information_arc(self) -> bool:
        """Check if arc transfers information (not mass).
        
        Signal flow arcs represent information channels enabling hierarchical
        control without mass transfer.
        
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
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"SignalFlowArc(id={self.id}, {self.source.name} → {self.target.name}, "
                f"weight={self.weight}, information_transfer)")
