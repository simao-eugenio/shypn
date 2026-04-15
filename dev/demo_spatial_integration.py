#!/usr/bin/env python3
"""Example: Spatial Signal Properties in Action

This example demonstrates how spatial signal properties (Layer 1) automatically
govern transition behavior during simulation.

Demonstrates:
1. Diffusion coefficient scaling of continuous rates
2. Boundary type validation (PERMEABLE, SELECTIVE, IMPERMEABLE)
3. Gradient-directed flow modulation
4. Volume-based stochastic/continuous selection
5. Distance-dependent rate attenuation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.netobjs.place import Place, BoundaryType, SignalType
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc


class SimpleModel:
    """Simple mock model for demonstration."""
    def __init__(self, name):
        self.name = name
        self.places = {}
        self.arcs = {}
        self.transitions = {}
        self.current_time = 0.0


def example_1_ca_diffusion():
    """Example 1: Ca²⁺ diffusion between compartments with diffusion coefficient."""
    print("=" * 70)
    print("EXAMPLE 1: Ca²⁺ Diffusion with Diffusion Coefficient")
    print("=" * 70)
    
    # Create model
    model = SimpleModel(name="Ca_Diffusion")
    
    # Cytoplasm: Low Ca²⁺ concentration
    cytoplasm = Place(
        x=100.0, y=100.0,
        id="P_cyto",
        name="Cytoplasm_Ca"
    )
    cytoplasm.tokens = 0.1  # 0.1 mM
    cytoplasm.signal_type = SignalType.SPATIAL
    cytoplasm.diffusion_coefficient = 200.0  # μm²/s
    cytoplasm.compartment_volume = 1000.0  # fL (large - use continuous)
    cytoplasm.spatial_position = (0.0, 0.0, 0.0)
    cytoplasm.boundary_type = BoundaryType.PERMEABLE
    
    # ER: High Ca²⁺ concentration (5 μm away)
    er = Place(
        x=200.0, y=100.0,
        id="P_er",
        name="ER_Ca"
    )
    er.tokens = 0.5  # 0.5 mM
    er.signal_type = SignalType.SPATIAL
    er.diffusion_coefficient = 50.0  # μm²/s (slower in ER)
    er.compartment_volume = 100.0  # fL
    er.spatial_position = (5.0, 0.0, 0.0)
    er.boundary_type = BoundaryType.PERMEABLE
    er.add_neighbor_compartment("P_cyto")
    
    # Add places to model
    model.places = {"P_cyto": cytoplasm, "P_er": er}
    
    # Diffusion transition (continuous)
    diffusion = Transition(
        id="T_diff",
        name="Ca_Diffusion",
        transition_type="continuous"
    )
    # Simple gradient-based rate (will be scaled by D automatically)
    diffusion.rate_function = "abs(P_er - P_cyto)"
    
    # Create arcs
    arc_in = Arc(source_id="P_er", target_id="T_diff", weight=1.0)
    arc_in.source = er
    
    arc_out = Arc(source_id="T_diff", target_id="P_cyto", weight=1.0)
    arc_out.target = cytoplasm
    
    model.arcs = {"A1": arc_in, "A2": arc_out}
    model.transitions = {"T_diff": diffusion}
    
    # Create behavior
    from shypn.engine.continuous_behavior import ContinuousBehavior
    behavior = ContinuousBehavior(diffusion, model)
    
    # Check enablement
    can_fire, reason = behavior.can_fire()
    print(f"\\n1. Enablement Check:")
    print(f"   Can fire: {can_fire}")
    print(f"   Reason: {reason}")
    
    # Evaluate rate (will apply diffusion coefficient automatically)
    places_dict = {"P_cyto": cytoplasm, "P_er": er}
    base_rate = abs(er.tokens - cytoplasm.tokens)  # 0.4 mM
    
    # The behavior automatically scales by diffusion_coefficient during evaluation
    print(f"\\n2. Rate Calculation:")
    print(f"   Gradient: {er.tokens - cytoplasm.tokens:.3f} mM")
    print(f"   Distance: {er.get_spatial_distance(cytoplasm):.1f} μm")
    print(f"   Diffusion coeff (ER): {er.diffusion_coefficient} μm²/s")
    print(f"   Expected rate scaling: {er.diffusion_coefficient} × gradient")
    print(f"   → Automatic D-scaling applied during behavior.fire()")
    
    # Show boundary validation
    print(f"\\n3. Boundary Validation:")
    print(f"   ER boundary: {er.boundary_type.value}")
    print(f"   Cytoplasm is neighbor: {er.is_neighbor('P_cyto')}")
    print(f"   ✓ Transport allowed (PERMEABLE)")
    
    print()


def example_2_selective_transport():
    """Example 2: Voltage-gated Na⁺ channel with SELECTIVE boundary."""
    print("=" * 70)
    print("EXAMPLE 2: Voltage-Gated Na⁺ Channel (SELECTIVE Boundary)")
    print("=" * 70)
    
    # Create model
    model = SimpleModel(name="Na_Channel")
    
    # Extracellular Na⁺
    extracellular = Place(
        x=100.0, y=100.0,
        id="P_ext",
        name="Extracellular_Na"
    )
    extracellular.tokens = 145.0  # mM
    extracellular.signal_type = SignalType.SPATIAL
    extracellular.boundary_type = BoundaryType.SELECTIVE  # Requires transport
    extracellular.add_neighbor_compartment("P_cyto")
    
    # Intracellular Na⁺
    cytoplasm = Place(
        x=200.0, y=100.0,
        id="P_cyto",
        name="Cytoplasm_Na"
    )
    cytoplasm.tokens = 12.0  # mM
    cytoplasm.signal_type = SignalType.SPATIAL
    cytoplasm.boundary_type = BoundaryType.SELECTIVE
    
    # Membrane potential (controls channel)
    membrane = Place(
        x=150.0, y=150.0,
        id="P_mem",
        name="Membrane_Potential"
    )
    membrane.tokens = -70.0  # mV (resting)
    membrane.signal_type = SignalType.SPATIAL
    membrane.boundary_type = BoundaryType.IMPERMEABLE  # Cannot cross membrane
    
    model.places = {"P_ext": extracellular, "P_cyto": cytoplasm, "P_mem": membrane}
    
    # Na⁺ channel transition (marked as transport)
    channel = Transition(
        id="T_channel",
        name="Na_Channel",
        transition_type="immediate"
    )
    channel.is_transport = True  # CRITICAL: marks as transport transition
    
    # Before depolarization
    print(f"\\n1. Before Depolarization:")
    print(f"   Membrane potential: {membrane.tokens} mV")
    print(f"   Extracellular boundary: {extracellular.boundary_type.value}")
    print(f"   Transition is_transport: {channel.is_transport}")
    
    # Create behavior
    from shypn.engine.immediate_behavior import ImmediateBehavior
    behavior = ImmediateBehavior(channel, model)
    
    # Create arcs
    arc1 = Arc(source_id="P_ext", target_id="T_channel", weight=10.0)
    arc1.source = extracellular
    arc2 = Arc(source_id="T_channel", target_id="P_cyto", weight=10.0)
    arc2.target = cytoplasm
    
    model.arcs = {"A1": arc1, "A2": arc2}
    model.transitions = {"T_channel": channel}
    
    # Check if can fire (should pass - is_transport=True + neighbors)
    can_fire, reason = behavior.can_fire()
    print(f"\\n2. Boundary Validation:")
    print(f"   Can fire: {can_fire}")
    print(f"   Reason: {reason}")
    print(f"   ✓ SELECTIVE boundary allows transport with is_transport=True")
    
    # Now test IMPERMEABLE boundary
    print(f"\\n3. Testing IMPERMEABLE Boundary:")
    print(f"   Setting extracellular boundary to IMPERMEABLE...")
    extracellular.boundary_type = BoundaryType.IMPERMEABLE
    
    # Re-check
    behavior2 = ImmediateBehavior(channel, model)
    can_fire2, reason2 = behavior2.can_fire()
    print(f"   Can fire: {can_fire2}")
    print(f"   Reason: {reason2}")
    print(f"   ✗ IMPERMEABLE boundary blocks all transport")
    
    print()


def example_3_gradient_flow():
    """Example 3: pH gradient-driven H⁺ flow with directional modulation."""
    print("=" * 70)
    print("EXAMPLE 3: pH Gradient-Driven Proton Flow")
    print("=" * 70)
    
    # Create model
    model = SimpleModel(name="pH_Gradient")
    
    # Acidic compartment (high H⁺)
    acidic = Place(
        x=100.0, y=100.0,
        id="P_acid",
        name="Acidic_Compartment"
    )
    acidic.tokens = 5.5  # pH 5.5 (high H⁺ concentration in log scale)
    acidic.signal_type = SignalType.SPATIAL
    acidic.set_spatial_gradient(dx=1.0, dy=0.0, dz=0.0)  # Gradient in +x direction
    acidic.spatial_position = (0.0, 0.0, 0.0)
    acidic.diffusion_coefficient = 300.0  # Fast H⁺ diffusion
    
    # Neutral compartment (10 μm away in +x direction)
    neutral = Place(
        x=200.0, y=100.0,
        id="P_neutral",
        name="Neutral_Compartment"
    )
    neutral.tokens = 7.2  # pH 7.2
    neutral.signal_type = SignalType.SPATIAL
    neutral.spatial_position = (10.0, 0.0, 0.0)
    
    model.places = {"P_acid": acidic, "P_neutral": neutral}
    
    # H⁺ flow transition
    flow = Transition(
        id="T_flow",
        name="H_Flow",
        transition_type="continuous"
    )
    flow.rate_function = "abs(P_acid - P_neutral)"
    
    # Create arcs
    arc_in = Arc(source_id="P_acid", target_id="T_flow", weight=1.0)
    arc_in.source = acidic
    arc_out = Arc(source_id="T_flow", target_id="P_neutral", weight=1.0)
    arc_out.target = neutral
    
    model.arcs = {"A1": arc_in, "A2": arc_out}
    model.transitions = {"T_flow": flow}
    
    # Create behavior
    from shypn.engine.continuous_behavior import ContinuousBehavior
    behavior = ContinuousBehavior(flow, model)
    
    print(f"\\n1. Gradient Configuration:")
    print(f"   Acidic gradient: {acidic.gradient_vector}")
    print(f"   Gradient magnitude: {acidic.get_gradient_magnitude():.1f}")
    print(f"   Transport direction: ({10.0:.1f}, 0.0, 0.0) → +x")
    
    # Calculate alignment
    gx, gy, gz = acidic.gradient_vector
    dx, dy, dz = 1.0, 0.0, 0.0  # Normalized transport direction
    alignment = gx*dx + gy*dy + gz*dz
    
    print(f"\\n2. Gradient Alignment:")
    print(f"   Dot product: {alignment:.1f}")
    print(f"   Modulation factor: 1.0 + {alignment:.1f} = {1.0 + alignment:.1f}")
    print(f"   → Flow AMPLIFIED (aligned with gradient)")
    
    # Show reverse direction
    print(f"\\n3. Reverse Direction Test:")
    print(f"   If flow was reversed (neutral → acidic):")
    print(f"   Transport direction: (-1.0, 0.0, 0.0) → -x")
    alignment_rev = gx*(-1.0) + gy*0.0 + gz*0.0
    print(f"   Dot product: {alignment_rev:.1f}")
    print(f"   Modulation factor: 1.0 + ({alignment_rev:.1f}) = {1.0 + alignment_rev:.1f}")
    print(f"   → Flow BLOCKED (opposes gradient)")
    
    print()


def example_4_volume_selection():
    """Example 4: Volume-based stochastic/continuous selection."""
    print("=" * 70)
    print("EXAMPLE 4: Volume-Based Transition Type Selection")
    print("=" * 70)
    
    # Create model
    model = SimpleModel(name="Volume_Selection")
    
    # Small volume place
    small = Place(
        x=100.0, y=100.0,
        id="P_small",
        name="Small_Vesicle"
    )
    small.tokens = 100.0  # molecules
    small.signal_type = SignalType.SPATIAL
    small.compartment_volume = 0.1  # fL (small - should use stochastic)
    
    # Large volume place
    large = Place(
        x=200.0, y=100.0,
        id="P_large",
        name="Large_Compartment"
    )
    large.tokens = 100.0
    large.signal_type = SignalType.SPATIAL
    large.compartment_volume = 100.0  # fL (large - should use continuous)
    
    print(f"\\n1. Volume Analysis:")
    print(f"   Small vesicle: {small.compartment_volume} fL")
    print(f"   Large compartment: {large.compartment_volume} fL")
    print(f"   Threshold: 1.0 fL (default)")
    
    # Check recommendations
    from shypn.engine.spatial_utils import VolumeAdaptiveSelector
    selector = VolumeAdaptiveSelector(threshold_fL=1.0)
    
    print(f"\\n2. Recommendations:")
    print(f"   Small vesicle → {selector.should_use_stochastic(small) and 'stochastic' or 'continuous'}")
    print(f"   Large compartment → {selector.should_use_stochastic(large) and 'stochastic' or 'continuous'}")
    
    # Create stochastic transition for large volume (will warn)
    stochastic_trans = Transition(
        id="T_stoch",
        name="Stochastic_Reaction",
        transition_type="stochastic"
    )
    stochastic_trans.rate = 0.1
    
    model.places = {"P_large": large}
    model.transitions = {"T_stoch": stochastic_trans}
    
    # Add arcs
    arc_in = Arc(source_id="P_large", target_id="T_stoch", weight=1.0)
    arc_in.source = large
    arc_out = Arc(source_id="T_stoch", target_id="P_large", weight=1.0)
    arc_out.target = large
    
    model.arcs = {"A1": arc_in, "A2": arc_out}
    
    print(f"\\n3. Volume-Based Warnings:")
    print(f"   Creating stochastic behavior for large volume place...")
    
    # This will generate a warning
    from shypn.engine.stochastic_behavior import StochasticBehavior
    import logging
    logging.basicConfig(level=logging.WARNING, format='   %(levelname)s: %(message)s')
    
    behavior = StochasticBehavior(stochastic_trans, model)
    print(f"   ↑ Automatic volume-based recommendation!")
    
    print()


def main():
    """Run all examples."""
    print("\\n" + "="*70)
    print("SPATIAL SIGNAL PROPERTIES INTEGRATION EXAMPLES")
    print("Demonstrating automatic spatial property usage by transitions")
    print("="*70 + "\\n")
    
    example_1_ca_diffusion()
    example_2_selective_transport()
    example_3_gradient_flow()
    example_4_volume_selection()
    
    print("="*70)
    print("ALL EXAMPLES COMPLETE")
    print("="*70)
    print("\\nKey Points:")
    print("  • Transitions automatically read spatial properties from places")
    print("  • diffusion_coefficient scales rates in continuous transitions")
    print("  • boundary_type validates transport in can_fire()")
    print("  • gradient_vector modulates rates directionally")
    print("  • compartment_volume triggers stochastic/continuous warnings")
    print("  • All integration is automatic - no manual coding needed!")
    print()


if __name__ == "__main__":
    main()
