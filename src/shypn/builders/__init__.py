"""Builder pattern implementations for Petri net object construction.

This module provides fluent builder interfaces for constructing Petri net objects
with clean, readable syntax. Part of Phase 3 quality improvements.

Available builders:
- PlaceBuilder: Fluent interface for Place construction with signal place support
- ArcBuilder: Fluent interface for all 7 arc types (normal, curved, inhibitor, test, signal flow)
- TransitionBuilder: Fluent interface for 5 transition behavior types
- PetriNetBuilder: Fluent interface for complete model construction
- SimulationConfigBuilder: Fluent interface for simulation configuration

Example:
    from shypn.builders import PlaceBuilder, TransitionBuilder, ArcBuilder
    
    # Create signal place for ATP (SHPN formalism)
    atp = (PlaceBuilder("ATP")
           .with_tokens(100)
           .at_position(150, 200)
           .as_signal_place("ENERGY")
           .with_layer(0)  # Metabolic layer
           .build())
    
    # Create continuous transition with rate function
    hexokinase = (TransitionBuilder("hexokinase")
                  .as_continuous()
                  .with_rate_function("michaelis_menten(ATP, vmax=10, km=5)")
                  .with_enablement_threshold(2.21)  # ATP threshold for commitment
                  .build())
    
    # Create signal flow arc (consumptive commitment semantics)
    arc = (ArcBuilder()
           .from_place("ATP")
           .to_transition("commit")
           .as_signal_flow()
           .with_signal_weight(0.17)  # Decision quota W_s
           .build())

See doc/PHASE_3_QUALITY_PLAN.md for full implementation details.
See doc/SIGNAL_HIERARCHICAL_FORMALISM.md for SHPN theoretical foundations.
"""

from shypn.builders.place_builder import PlaceBuilder
from shypn.builders.arc_builder import ArcBuilder
from shypn.builders.transition_builder import TransitionBuilder
from shypn.builders.petri_net_builder import PetriNetBuilder
from shypn.builders.simulation_config_builder import SimulationConfigBuilder

__all__ = [
    'PlaceBuilder',
    'ArcBuilder',
    'TransitionBuilder',
    'PetriNetBuilder',
    'SimulationConfigBuilder',
]

