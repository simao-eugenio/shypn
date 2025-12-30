#!/usr/bin/env python3
"""Signal Place Classification.

This module defines the SignalType enumeration for classifying signal places
in the modular Bio-PN formalism (13-tuple with Ψ signal places).

Signal places enable information flow without mass transfer, allowing modular
architecture where biological subsystems are coupled through sensing rather
than direct material exchange.
"""

from enum import Enum


class SignalType(Enum):
    """Classification of signal places (Ψ) in modular Bio-PN.
    
    Signal places represent information channels that transitions can sense
    without consuming tokens (read-only). They enable:
    - Modular architecture (subsystems coupled via signals, not arcs)
    - Biological abstraction (environment sensing, cell communication)
    - Clean separation (no arcs cross module boundaries)
    
    Types:
        QUORUM: Cell-cell communication signals
            Examples: AHL (bacterial quorum sensing), pheromones, cytokines
            Use case: Multi-cellular systems, population-level coordination
            
        ENERGY: Metabolic state indicators
            Examples: ATP/ADP ratio, NADH/NAD+, proton gradients
            Use case: Energy-dependent reactions, metabolic regulation
            
        REGULATORY: Gene expression control signals
            Examples: Transcription factors, signaling proteins, hormones
            Use case: Regulatory cascades, signal transduction pathways
            
        SPATIAL: Compartment and location markers
            Examples: Compartment identity, positional information
            Use case: Spatial organization, compartmentalization
    """
    
    QUORUM = "quorum"
    """Cell-cell communication (AHL, pheromones, cytokines)."""
    
    ENERGY = "energy"
    """Metabolic state (ATP/ADP, NADH/NAD+, redox state)."""
    
    REGULATORY = "regulatory"
    """Gene expression control (transcription factors, signaling proteins)."""
    
    SPATIAL = "spatial"
    """Compartment sensing (location markers, positional information)."""
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        return self.value
    
    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return f"SignalType.{self.name}"
    
    @property
    def description(self) -> str:
        """Get detailed description of signal type."""
        descriptions = {
            SignalType.QUORUM: "Cell-cell communication signals",
            SignalType.ENERGY: "Metabolic state indicators",
            SignalType.REGULATORY: "Gene expression control signals",
            SignalType.SPATIAL: "Compartment and location markers"
        }
        return descriptions.get(self, "Unknown signal type")
    
    @property
    def examples(self) -> str:
        """Get example molecules/signals for this type."""
        examples = {
            SignalType.QUORUM: "AHL, pheromones, cytokines",
            SignalType.ENERGY: "ATP/ADP ratio, NADH/NAD+, proton gradients",
            SignalType.REGULATORY: "Transcription factors, signaling proteins, hormones",
            SignalType.SPATIAL: "Compartment identity, positional information"
        }
        return examples.get(self, "")
