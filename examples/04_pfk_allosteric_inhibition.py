#!/usr/bin/env python3
"""
Example 4: Phosphofructokinase (PFK) Allosteric Inhibition

This example demonstrates dynamic threshold regulation with:
- Allosteric enzyme with multiple effectors
- Product inhibition (feedback regulation)
- Dynamic threshold computation
- Weak independence under regulatory coupling

Reaction: Fructose-6-P + ATP → Fructose-1,6-BP + ADP
Enzyme: Phosphofructokinase (PFK, E.C. 2.7.1.11)
Regulation:
  - Activated by: AMP (low energy signal)
  - Inhibited by: ATP (high energy), Citrate (alternative pathway)

Key Features Demonstrated:
- Regulatory coupling mode
- Dynamic threshold (function of inhibitor concentration)
- Hill equation (cooperative binding)
- Feedback control

Reference: Thesis Chapter 7, Example 16 (Figure 7.4 in paper)
"""

from shypn.core.biological_petri_net import BiologicalPetriNet
from shypn.simulation.hybrid_simulator import HybridSimulator
from shypn.analysis.weak_independence import WeakIndependenceAnalyzer
import matplotlib.pyplot as plt
import numpy as np


def create_pfk_model():
    """Create PFK allosteric inhibition model."""
    net = BiologicalPetriNet()
    
    # Places - Substrates
    f6p = net.add_place(
        "Fructose-6-P",
        marking=50.0,
        formula="C6H13O9P",
        is_continuous=True
    )
    
    atp = net.add_place(
        "ATP",
        marking=100.0,
        formula="C10H16N5O13P3",
        is_continuous=True
    )
    
    # Places - Products
    fbp = net.add_place(
        "Fructose-1,6-BP",
        marking=0.0,
        formula="C6H14O12P2",
        is_continuous=True
    )
    
    adp = net.add_place(
        "ADP",
        marking=0.0,
        formula="C10H16N5O10P2",
        is_continuous=True
    )
    
    # Places - Regulatory Molecules
    amp = net.add_place(
        "AMP",
        marking=5.0,
        formula="C10H14N5O7P",
        is_continuous=True
    )
    
    citrate = net.add_place(
        "Citrate",
        marking=0.0,
        formula="C6H8O7",
        is_continuous=True
    )
    
    # Places - Enzyme
    pfk = net.add_place(
        "PFK",
        marking=10.0,
        formula="ENZYME",
        is_continuous=True
    )
    
    # Transition 1: PFK forward reaction (allosteric, Hill kinetics)
    pfk_reaction = net.add_continuous_transition(
        "PFK_reaction",
        rate_function="hill",
        vmax=15.0,
        km_substrates={"Fructose-6-P": 1.0, "ATP": 0.5},
        hill_coefficient=4.0,  # Strong cooperativity
        activators={"AMP": 0.1},  # AMP activates
        inhibitors={"ATP": 5.0, "Citrate": 2.0}  # ATP and citrate inhibit
    )
    net.add_arc(f6p, pfk_reaction, weight=1)
    net.add_arc(atp, pfk_reaction, weight=1)
    net.add_arc(pfk, pfk_reaction, weight=0, arc_type="test")
    net.add_arc(pfk_reaction, fbp, weight=1)
    net.add_arc(pfk_reaction, adp, weight=1)
    
    # Regulatory arcs with dynamic thresholds
    net.add_arc(citrate, pfk_reaction, weight=0, arc_type="inhibitor",
                threshold=lambda: 5.0 - 0.5 * amp.marking)  # Dynamic threshold
    
    # Transition 2: Citrate production (from TCA cycle, simplified)
    citrate_production = net.add_continuous_transition(
        "Citrate_production",
        rate_function="mass_action",
        rate_constant=0.05
    )
    net.add_arc(fbp, citrate_production, weight=0, arc_type="test")  # Catalyzed by FBP
    net.add_arc(citrate_production, citrate, weight=1)
    
    # Transition 3: ATP regeneration (oxidative phosphorylation, simplified)
    atp_regen = net.add_continuous_transition(
        "ATP_regeneration",
        rate_function="mass_action",
        rate_constant=0.1
    )
    net.add_arc(adp, atp_regen, weight=1)
    net.add_arc(atp_regen, atp, weight=1)
    
    # Transition 4: AMP recycling
    amp_to_atp = net.add_continuous_transition(
        "AMP_phosphorylation",
        rate_function="mass_action",
        rate_constant=0.02
    )
    net.add_arc(amp, amp_to_atp, weight=1)
    net.add_arc(amp_to_atp, atp, weight=1)
    
    return net


def main():
    """Run the PFK allosteric inhibition example."""
    print("=" * 60)
    print("Example 4: PFK Allosteric Inhibition (Dynamic Threshold)")
    print("=" * 60)
    
    # Create model
    net = create_pfk_model()
    
    # Display model information
    print(f"\nModel Statistics:")
    print(f"  Places: {len(net.places)}")
    print(f"  Transitions: {len(net.transitions)}")
    print(f"  Regulatory Arcs: {sum(1 for a in net.arcs if a.arc_type in ['test', 'inhibitor'])}")
    
    # Weak independence analysis
    print(f"\nWeak Independence Analysis:")
    analyzer = WeakIndependenceAnalyzer(net)
    results = analyzer.analyze()
    
    print(f"  Total transition pairs: {results.total_pairs}")
    print(f"  Weakly independent: {results.weak_independent} ({results.weak_percentage:.1f}%)")
    
    # Show regulatory coupling
    print(f"\n  Regulatory Coupling Modes:")
    for pair, mode in results.coupling_modes.items():
        if "REGULATORY" in mode:
            print(f"    {pair}: {mode}")
    
    # Display allosteric regulation
    print(f"\nAllosteric Regulation:")
    print(f"  Activator: AMP (low energy signal)")
    print(f"  Inhibitors: ATP (high energy), Citrate (feedback)")
    print(f"  Hill coefficient: 4.0 (strong cooperativity)")
    print(f"  Dynamic threshold: f(AMP) = 5.0 - 0.5*[AMP]")
    
    # Scenario 1: Low energy (high AMP, low ATP)
    print(f"\n" + "=" * 60)
    print("Scenario 1: Low Energy State (High AMP, Low ATP)")
    print("=" * 60)
    net_low_energy = create_pfk_model()
    net_low_energy.places["AMP"].marking = 20.0  # High AMP
    net_low_energy.places["ATP"].marking = 30.0  # Low ATP
    
    simulator = HybridSimulator(net_low_energy)
    results_low = simulator.simulate(t_end=50.0, dt=0.1)
    
    print(f"Initial: AMP=20.0, ATP=30.0")
    print(f"Final: AMP={results_low.get_place_trajectory('AMP')[-1]:.2f}, "
          f"ATP={results_low.get_place_trajectory('ATP')[-1]:.2f}")
    print(f"Product (FBP): {results_low.get_place_trajectory('Fructose-1,6-BP')[-1]:.2f}")
    
    # Scenario 2: High energy (low AMP, high ATP)
    print(f"\n" + "=" * 60)
    print("Scenario 2: High Energy State (Low AMP, High ATP)")
    print("=" * 60)
    net_high_energy = create_pfk_model()
    net_high_energy.places["AMP"].marking = 2.0   # Low AMP
    net_high_energy.places["ATP"].marking = 150.0 # High ATP
    
    simulator = HybridSimulator(net_high_energy)
    results_high = simulator.simulate(t_end=50.0, dt=0.1)
    
    print(f"Initial: AMP=2.0, ATP=150.0")
    print(f"Final: AMP={results_high.get_place_trajectory('AMP')[-1]:.2f}, "
          f"ATP={results_high.get_place_trajectory('ATP')[-1]:.2f}")
    print(f"Product (FBP): {results_high.get_place_trajectory('Fructose-1,6-BP')[-1]:.2f}")
    
    # Plot comparison
    print(f"\nGenerating comparative plots...")
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    
    # Low energy - FBP production
    ax = axes[0, 0]
    ax.set_title("Low Energy: Product Formation")
    ax.plot(results_low.time, results_low.get_place_trajectory("Fructose-1,6-BP"),
            color="green", linewidth=2)
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("FBP Concentration")
    ax.grid(True, alpha=0.3)
    
    # Low energy - Energy status
    ax = axes[0, 1]
    ax.set_title("Low Energy: Nucleotides")
    ax.plot(results_low.time, results_low.get_place_trajectory("ATP"),
            label="ATP", color="red")
    ax.plot(results_low.time, results_low.get_place_trajectory("ADP"),
            label="ADP", color="orange")
    ax.plot(results_low.time, results_low.get_place_trajectory("AMP"),
            label="AMP", color="blue")
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Concentration")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Low energy - Feedback
    ax = axes[0, 2]
    ax.set_title("Low Energy: Feedback Inhibitor")
    ax.plot(results_low.time, results_low.get_place_trajectory("Citrate"),
            color="purple", linewidth=2)
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Citrate Concentration")
    ax.grid(True, alpha=0.3)
    
    # High energy - FBP production
    ax = axes[1, 0]
    ax.set_title("High Energy: Product Formation")
    ax.plot(results_high.time, results_high.get_place_trajectory("Fructose-1,6-BP"),
            color="green", linewidth=2)
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("FBP Concentration")
    ax.grid(True, alpha=0.3)
    
    # High energy - Energy status
    ax = axes[1, 1]
    ax.set_title("High Energy: Nucleotides")
    ax.plot(results_high.time, results_high.get_place_trajectory("ATP"),
            label="ATP", color="red")
    ax.plot(results_high.time, results_high.get_place_trajectory("ADP"),
            label="ADP", color="orange")
    ax.plot(results_high.time, results_high.get_place_trajectory("AMP"),
            label="AMP", color="blue")
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Concentration")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # High energy - Feedback
    ax = axes[1, 2]
    ax.set_title("High Energy: Feedback Inhibitor")
    ax.plot(results_high.time, results_high.get_place_trajectory("Citrate"),
            color="purple", linewidth=2)
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Citrate Concentration")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("pfk_allosteric_simulation.pdf")
    plt.savefig("pfk_allosteric_simulation.png", dpi=150)
    print(f"  Plots saved: pfk_allosteric_simulation.pdf/png")
    
    print(f"\n✓ Example completed successfully!")
    print(f"\nKey Insights:")
    print(f"  - Low energy (high AMP): PFK is ACTIVATED → high FBP production")
    print(f"  - High energy (high ATP): PFK is INHIBITED → low FBP production")
    print(f"  - Dynamic threshold adjusts sensitivity to citrate based on AMP")
    print(f"  - Demonstrates weak independence under regulatory coupling")
    print("=" * 60)


if __name__ == "__main__":
    main()
