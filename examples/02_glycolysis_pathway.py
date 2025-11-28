#!/usr/bin/env python3
"""
Example 2: Glycolysis Pathway (First 3 Steps)

This example demonstrates a multi-step metabolic pathway with:
- Sequential reactions
- Shared intermediates (weak independence)
- Multiple enzymes
- ATP consumption and regeneration

Reactions:
1. Glucose + ATP → Glucose-6-P + ADP  (Hexokinase)
2. Glucose-6-P ⇌ Fructose-6-P          (Phosphoglucose Isomerase)
3. Fructose-6-P + ATP → Fructose-1,6-BP + ADP (Phosphofructokinase)

Key Features Demonstrated:
- Multi-step pathways
- Reversible reactions
- Weak independence analysis
- Competitive coupling (shared ATP)

Reference: Thesis Chapter 5, Example 2
"""

from shypn.core.biological_petri_net import BiologicalPetriNet
from shypn.simulation.hybrid_simulator import HybridSimulator
from shypn.analysis.weak_independence import WeakIndependenceAnalyzer
import matplotlib.pyplot as plt


def create_glycolysis_model():
    """Create the first 3 steps of glycolysis."""
    net = BiologicalPetriNet()
    
    # Places (Metabolites)
    glucose = net.add_place("Glucose", marking=100.0, formula="C6H12O6", is_continuous=True)
    g6p = net.add_place("Glucose-6-P", marking=0.0, formula="C6H13O9P", is_continuous=True)
    f6p = net.add_place("Fructose-6-P", marking=0.0, formula="C6H13O9P", is_continuous=True)
    fbp = net.add_place("Fructose-1,6-BP", marking=0.0, formula="C6H14O12P2", is_continuous=True)
    
    atp = net.add_place("ATP", marking=100.0, formula="C10H16N5O13P3", is_continuous=True)
    adp = net.add_place("ADP", marking=0.0, formula="C10H16N5O10P2", is_continuous=True)
    
    # Enzymes (catalysts)
    hexokinase = net.add_place("Hexokinase", marking=10.0, formula="ENZYME", is_continuous=True)
    pgi = net.add_place("PGI", marking=10.0, formula="ENZYME", is_continuous=True)
    pfk = net.add_place("PFK", marking=10.0, formula="ENZYME", is_continuous=True)
    
    # Transition 1: Hexokinase (irreversible)
    t1_forward = net.add_continuous_transition(
        "HK_forward",
        rate_function="michaelis_menten",
        vmax=10.0,
        km_substrates={"Glucose": 0.1, "ATP": 0.5}
    )
    net.add_arc(glucose, t1_forward, weight=1)
    net.add_arc(atp, t1_forward, weight=1)
    net.add_arc(hexokinase, t1_forward, weight=0, arc_type="test")
    net.add_arc(t1_forward, g6p, weight=1)
    net.add_arc(t1_forward, adp, weight=1)
    
    # Transition 2: Phosphoglucose Isomerase (reversible)
    t2_forward = net.add_continuous_transition(
        "PGI_forward",
        rate_function="michaelis_menten",
        vmax=15.0,
        km_substrates={"Glucose-6-P": 0.2}
    )
    net.add_arc(g6p, t2_forward, weight=1)
    net.add_arc(pgi, t2_forward, weight=0, arc_type="test")
    net.add_arc(t2_forward, f6p, weight=1)
    
    t2_reverse = net.add_continuous_transition(
        "PGI_reverse",
        rate_function="michaelis_menten",
        vmax=10.0,
        km_substrates={"Fructose-6-P": 0.3}
    )
    net.add_arc(f6p, t2_reverse, weight=1)
    net.add_arc(pgi, t2_reverse, weight=0, arc_type="test")
    net.add_arc(t2_reverse, g6p, weight=1)
    
    # Transition 3: Phosphofructokinase (irreversible, allosteric)
    t3_forward = net.add_continuous_transition(
        "PFK_forward",
        rate_function="hill",  # Cooperative binding
        vmax=8.0,
        km_substrates={"Fructose-6-P": 0.5, "ATP": 1.0},
        hill_coefficient=2.0  # Positive cooperativity
    )
    net.add_arc(f6p, t3_forward, weight=1)
    net.add_arc(atp, t3_forward, weight=1)
    net.add_arc(pfk, t3_forward, weight=0, arc_type="test")
    net.add_arc(t3_forward, fbp, weight=1)
    net.add_arc(t3_forward, adp, weight=1)
    
    return net


def main():
    """Run the glycolysis example."""
    print("=" * 60)
    print("Example 2: Glycolysis Pathway (First 3 Steps)")
    print("=" * 60)
    
    # Create model
    net = create_glycolysis_model()
    
    # Display model information
    print(f"\nModel Statistics:")
    print(f"  Places: {len(net.places)}")
    print(f"  Transitions: {len(net.transitions)}")
    print(f"  Arcs: {len(net.arcs)}")
    
    # Weak independence analysis
    print(f"\nWeak Independence Analysis:")
    analyzer = WeakIndependenceAnalyzer(net)
    results = analyzer.analyze()
    
    print(f"  Total transition pairs: {results.total_pairs}")
    print(f"  Strongly independent: {results.strong_independent} ({results.strong_percentage:.1f}%)")
    print(f"  Weakly independent: {results.weak_independent} ({results.weak_percentage:.1f}%)")
    print(f"  Dependent: {results.dependent} ({results.dependent_percentage:.1f}%)")
    
    # Show coupling modes
    print(f"\n  Coupling Modes:")
    for transition_pair, mode in results.coupling_modes.items():
        print(f"    {transition_pair}: {mode}")
    
    # Run simulation
    print(f"\nRunning simulation (0-20 time units)...")
    simulator = HybridSimulator(net)
    sim_results = simulator.simulate(t_end=20.0, dt=0.1)
    
    # Display final concentrations
    print(f"\nFinal Concentrations:")
    metabolites = ["Glucose", "Glucose-6-P", "Fructose-6-P", "Fructose-1,6-BP", "ATP", "ADP"]
    for metabolite in metabolites:
        final_value = sim_results.get_place_trajectory(metabolite)[-1]
        print(f"  {metabolite}: {final_value:.2f}")
    
    # Plot results
    print(f"\nGenerating plots...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Glucose consumption
    ax = axes[0, 0]
    ax.set_title("Glucose Consumption")
    ax.plot(sim_results.time, sim_results.get_place_trajectory("Glucose"), 
            color="blue", linewidth=2)
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Concentration (a.u.)")
    ax.grid(True, alpha=0.3)
    
    # Intermediates
    ax = axes[0, 1]
    ax.set_title("Pathway Intermediates")
    ax.plot(sim_results.time, sim_results.get_place_trajectory("Glucose-6-P"),
            label="Glucose-6-P", color="green")
    ax.plot(sim_results.time, sim_results.get_place_trajectory("Fructose-6-P"),
            label="Fructose-6-P", color="orange")
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Concentration (a.u.)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Product (Fructose-1,6-BP)
    ax = axes[1, 0]
    ax.set_title("Product Formation")
    ax.plot(sim_results.time, sim_results.get_place_trajectory("Fructose-1,6-BP"),
            color="red", linewidth=2)
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Concentration (a.u.)")
    ax.grid(True, alpha=0.3)
    
    # ATP/ADP ratio
    ax = axes[1, 1]
    ax.set_title("Energy Balance (ATP/ADP)")
    ax.plot(sim_results.time, sim_results.get_place_trajectory("ATP"),
            label="ATP", color="purple", linewidth=2)
    ax.plot(sim_results.time, sim_results.get_place_trajectory("ADP"),
            label="ADP", color="brown", linewidth=2)
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Concentration (a.u.)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("glycolysis_simulation.pdf")
    plt.savefig("glycolysis_simulation.png", dpi=150)
    print(f"  Plots saved: glycolysis_simulation.pdf/png")
    
    print(f"\n✓ Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
