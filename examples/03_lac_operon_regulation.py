#!/usr/bin/env python3
"""
Example 3: Lac Operon Gene Regulation

This example demonstrates regulatory control with:
- Transcription (stochastic)
- Translation (stochastic)
- Inhibitor arcs (allosteric regulation)
- Continuous enzyme activity
- Coupled stochastic/continuous dynamics

System Components:
- DNA → mRNA (transcription)
- mRNA → LacZ (translation)
- LacZ + Lactose → Products (enzyme activity)
- Glucose inhibits transcription (catabolite repression)

Key Features Demonstrated:
- Regulatory arcs (inhibitor)
- Hybrid stochastic/continuous simulation
- Gene expression dynamics
- Feedback regulation

Reference: Thesis Chapter 7, Example 4
"""

from shypn.core.biological_petri_net import BiologicalPetriNet
from shypn.simulation.hybrid_simulator import HybridSimulator
import matplotlib.pyplot as plt


def create_lac_operon_model():
    """Create a simplified lac operon regulatory model."""
    net = BiologicalPetriNet()
    
    # Places - Genetic Elements
    dna = net.add_place(
        "lac_DNA",
        marking=1,  # Single copy gene
        formula="DNA",
        is_continuous=False  # Discrete
    )
    
    mrna = net.add_place(
        "lacZ_mRNA",
        marking=0,
        formula="RNA",
        is_continuous=False
    )
    
    lacz = net.add_place(
        "LacZ_enzyme",
        marking=0.0,
        formula="ENZYME",
        is_continuous=True  # Enzyme concentration
    )
    
    # Places - Metabolites
    lactose = net.add_place(
        "Lactose",
        marking=100.0,
        formula="C12H22O11",
        is_continuous=True
    )
    
    glucose = net.add_place(
        "Glucose",
        marking=50.0,
        formula="C6H12O6",
        is_continuous=True
    )
    
    products = net.add_place(
        "Products",
        marking=0.0,
        formula="PRODUCTS",
        is_continuous=True
    )
    
    # Transition 1: Transcription (stochastic, inhibited by glucose)
    transcription = net.add_stochastic_transition(
        "Transcription",
        rate=0.1  # Basal transcription rate
    )
    net.add_arc(dna, transcription, weight=0, arc_type="test")  # DNA not consumed
    net.add_arc(transcription, mrna, weight=1)
    
    # Glucose inhibition (catabolite repression)
    net.add_arc(glucose, transcription, weight=0, arc_type="inhibitor",
                threshold=20.0)  # Inhibit if glucose > 20
    
    # Transition 2: mRNA degradation (stochastic)
    mrna_deg = net.add_stochastic_transition(
        "mRNA_degradation",
        rate=0.05
    )
    net.add_arc(mrna, mrna_deg, weight=1)
    
    # Transition 3: Translation (stochastic)
    translation = net.add_stochastic_transition(
        "Translation",
        rate=0.2
    )
    net.add_arc(mrna, translation, weight=0, arc_type="test")  # mRNA template
    net.add_arc(translation, lacz, weight=10.0)  # Produce enzyme molecules
    
    # Transition 4: Enzyme degradation (continuous)
    enzyme_deg = net.add_continuous_transition(
        "Enzyme_degradation",
        rate_function="mass_action",
        rate_constant=0.01
    )
    net.add_arc(lacz, enzyme_deg, weight=1)
    
    # Transition 5: Lactose metabolism (continuous, enzyme-catalyzed)
    metabolism = net.add_continuous_transition(
        "Lactose_metabolism",
        rate_function="michaelis_menten",
        vmax=20.0,
        km_substrates={"Lactose": 10.0}
    )
    net.add_arc(lactose, metabolism, weight=1)
    net.add_arc(lacz, metabolism, weight=0, arc_type="test")  # Enzyme catalyst
    net.add_arc(metabolism, products, weight=2)  # 2 products per lactose
    
    return net


def main():
    """Run the lac operon example."""
    print("=" * 60)
    print("Example 3: Lac Operon Gene Regulation")
    print("=" * 60)
    
    # Create model
    net = create_lac_operon_model()
    
    # Display model information
    print(f"\nModel Statistics:")
    print(f"  Places: {len(net.places)}")
    print(f"  Transitions: {len(net.transitions)}")
    print(f"    Stochastic: {sum(1 for t in net.transitions if t.is_stochastic)}")
    print(f"    Continuous: {sum(1 for t in net.transitions if t.is_continuous)}")
    print(f"  Regulatory Arcs: {sum(1 for a in net.arcs if a.arc_type in ['test', 'inhibitor'])}")
    
    # Display regulatory structure
    print(f"\nRegulatory Control:")
    for arc in net.arcs:
        if arc.arc_type == "inhibitor":
            print(f"  {arc.source.name} --| {arc.target.name} (threshold: {arc.threshold})")
        elif arc.arc_type == "test":
            print(f"  {arc.source.name} --o {arc.target.name} (catalyst)")
    
    # Run simulation
    print(f"\nRunning hybrid simulation (0-100 time units)...")
    print(f"  Initial glucose: 50.0 (transcription inhibited)")
    print(f"  Glucose will be consumed, lifting repression...")
    
    simulator = HybridSimulator(net)
    results = simulator.simulate(
        t_end=100.0,
        dt=0.5,
        stochastic_method="gillespie",  # Exact stochastic algorithm
        continuous_method="odeint"       # Continuous ODE solver
    )
    
    # Display final state
    print(f"\nFinal State:")
    components = ["lacZ_mRNA", "LacZ_enzyme", "Lactose", "Glucose", "Products"]
    for component in components:
        final_value = results.get_place_trajectory(component)[-1]
        print(f"  {component}: {final_value:.2f}")
    
    # Plot results
    print(f"\nGenerating plots...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Gene expression
    ax = axes[0, 0]
    ax.set_title("Gene Expression (Stochastic)")
    ax.plot(results.time, results.get_place_trajectory("lacZ_mRNA"),
            label="mRNA", color="blue", alpha=0.7)
    ax2 = ax.twinx()
    ax2.plot(results.time, results.get_place_trajectory("LacZ_enzyme"),
             label="LacZ Enzyme", color="red", alpha=0.7)
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("mRNA copies", color="blue")
    ax2.set_ylabel("Enzyme molecules", color="red")
    ax.grid(True, alpha=0.3)
    
    # Glucose depletion (lifts repression)
    ax = axes[0, 1]
    ax.set_title("Glucose Depletion (Catabolite Repression)")
    ax.plot(results.time, results.get_place_trajectory("Glucose"),
            color="purple", linewidth=2)
    ax.axhline(y=20.0, color="red", linestyle="--", 
               label="Inhibition threshold")
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Glucose concentration")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Lactose metabolism
    ax = axes[1, 0]
    ax.set_title("Lactose Metabolism")
    ax.plot(results.time, results.get_place_trajectory("Lactose"),
            label="Lactose (substrate)", color="green", linewidth=2)
    ax.plot(results.time, results.get_place_trajectory("Products"),
            label="Products", color="orange", linewidth=2)
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Concentration")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # System overview
    ax = axes[1, 1]
    ax.set_title("System Dynamics Overview")
    ax.plot(results.time, results.get_place_trajectory("Glucose") / 50.0,
            label="Glucose (norm)", color="purple", alpha=0.6)
    ax.plot(results.time, results.get_place_trajectory("lacZ_mRNA") / 10.0,
            label="mRNA (norm)", color="blue", alpha=0.6)
    ax.plot(results.time, results.get_place_trajectory("LacZ_enzyme") / 100.0,
            label="Enzyme (norm)", color="red", alpha=0.6)
    ax.plot(results.time, results.get_place_trajectory("Products") / 100.0,
            label="Products (norm)", color="orange", alpha=0.6)
    ax.set_xlabel("Time (a.u.)")
    ax.set_ylabel("Normalized values")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("lac_operon_simulation.pdf")
    plt.savefig("lac_operon_simulation.png", dpi=150)
    print(f"  Plots saved: lac_operon_simulation.pdf/png")
    
    print(f"\n✓ Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
