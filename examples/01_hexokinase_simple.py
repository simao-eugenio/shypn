#!/usr/bin/env python3
"""
Example 1: Simple Hexokinase Reaction

This example demonstrates the basic Extended Biological Petri Net formalism
with a simple enzyme-catalyzed reaction: Hexokinase phosphorylates glucose
to produce glucose-6-phosphate.

Reaction: Glucose + ATP → Glucose-6-Phosphate + ADP
Enzyme: Hexokinase (E.C. 2.7.1.1)

Key Features Demonstrated:
- Continuous transitions with Michaelis-Menten kinetics
- Test arcs (enzyme not consumed)
- Mass balance validation via atomic formulas
- Basic simulation and plotting

Reference: Thesis Chapter 4, Example 1
"""

from shypn.core.biological_petri_net import BiologicalPetriNet
from shypn.simulation.hybrid_simulator import HybridSimulator
import matplotlib.pyplot as plt


def create_hexokinase_model():
    """Create a simple hexokinase reaction model."""
    net = BiologicalPetriNet()
    
    # Places (Chemical Species)
    glucose = net.add_place(
        "Glucose",
        marking=100.0,
        formula="C6H12O6",
        is_continuous=True
    )
    
    atp = net.add_place(
        "ATP",
        marking=50.0,
        formula="C10H16N5O13P3",
        is_continuous=True
    )
    
    hexokinase = net.add_place(
        "Hexokinase",
        marking=10.0,
        formula="ENZYME",  # Enzyme (catalyst)
        is_continuous=True
    )
    
    g6p = net.add_place(
        "Glucose-6-Phosphate",
        marking=0.0,
        formula="C6H13O9P",
        is_continuous=True
    )
    
    adp = net.add_place(
        "ADP",
        marking=0.0,
        formula="C10H16N5O10P2",
        is_continuous=True
    )
    
    # Transition (Biochemical Reaction)
    phosphorylation = net.add_continuous_transition(
        "Phosphorylation",
        rate_function="michaelis_menten",
        vmax=5.0,  # Maximum reaction rate
        km_substrates={"Glucose": 0.1, "ATP": 0.5}  # Michaelis constants
    )
    
    # Arcs (Stoichiometry)
    # Input substrates
    net.add_arc(glucose, phosphorylation, weight=1, arc_type="normal")
    net.add_arc(atp, phosphorylation, weight=1, arc_type="normal")
    
    # Enzyme as catalyst (test arc - not consumed)
    net.add_arc(hexokinase, phosphorylation, weight=0, arc_type="test")
    
    # Output products
    net.add_arc(phosphorylation, g6p, weight=1, arc_type="normal")
    net.add_arc(phosphorylation, adp, weight=1, arc_type="normal")
    
    return net


def main():
    """Run the hexokinase example."""
    print("=" * 60)
    print("Example 1: Hexokinase Reaction")
    print("=" * 60)
    
    # Create model
    net = create_hexokinase_model()
    
    # Display model information
    print(f"\nModel Statistics:")
    print(f"  Places: {len(net.places)}")
    print(f"  Transitions: {len(net.transitions)}")
    print(f"  Arcs: {len(net.arcs)}")
    
    # Validate mass balance
    print(f"\n Checking atomic mass balance...")
    is_balanced = net.validate_mass_balance()
    print(f"  Mass balanced: {'✓ Yes' if is_balanced else '✗ No'}")
    
    # Run simulation
    print(f"\nRunning simulation (0-10 time units)...")
    simulator = HybridSimulator(net)
    results = simulator.simulate(t_end=10.0, dt=0.1)
    
    # Display final concentrations
    print(f"\nFinal Concentrations:")
    for place_name in ["Glucose", "ATP", "Glucose-6-Phosphate", "ADP", "Hexokinase"]:
        final_value = results.get_place_trajectory(place_name)[-1]
        print(f"  {place_name}: {final_value:.2f}")
    
    # Plot results
    print(f"\nGenerating plots...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Substrates
    ax1.set_title("Substrates (Consumed)")
    ax1.plot(results.time, results.get_place_trajectory("Glucose"), 
             label="Glucose", color="blue")
    ax1.plot(results.time, results.get_place_trajectory("ATP"),
             label="ATP", color="red")
    ax1.set_xlabel("Time (arbitrary units)")
    ax1.set_ylabel("Concentration (arbitrary units)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Products
    ax2.set_title("Products (Produced)")
    ax2.plot(results.time, results.get_place_trajectory("Glucose-6-Phosphate"),
             label="Glucose-6-P", color="green")
    ax2.plot(results.time, results.get_place_trajectory("ADP"),
             label="ADP", color="orange")
    ax2.set_xlabel("Time (arbitrary units)")
    ax2.set_ylabel("Concentration (arbitrary units)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("hexokinase_simulation.pdf")
    plt.savefig("hexokinase_simulation.png", dpi=150)
    print(f"  Plots saved: hexokinase_simulation.pdf/png")
    
    print(f"\n✓ Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
