#!/usr/bin/env python
"""
Mammalian Paracrine Signaling Model - IL-2 System
==================================================

T cell coordination via interleukin-2 cytokine signaling.
Demonstrates 13-tuple Bio-PN formalism with signal places (Ψ).

Reference:
    Smith (1988) Science 240:1169-1176
    Ross & Cantrell (2018) Annu. Rev. Immunol. 36:411-433
"""

import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from shypn.netobjs.biopetrinet import BioPetriNet
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.engine.gillespie import GillespieEngine
from shypn.analysis.quorum_sensing import QuorumSensingDetector

# Note: Signal network visualization (plot_signal_network) is planned for Phase 3
# For now, signal place information is displayed in text format


def create_il2_model(t_cell_count=1e5, volume=1e-12):
    """
    Create mammalian IL-2 paracrine signaling Bio-PN model.
    
    Parameters
    ----------
    t_cell_count : float
        Initial T cell count (cells/mL)
    volume : float
        Cell volume (L), default 1 pL typical for T cells
        
    Returns
    -------
    BioPetriNet
        13-tuple Bio-PN with signal places
    """
    model = BioPetriNet(name="IL2_Paracrine_Signaling")
    
    # ========================================================================
    # PLACES (Molecular Species)
    # ========================================================================
    
    # IL-2 production module
    p_gene_IL2 = Place("Gene_IL2", initial_tokens=2, place_type="gene")  # Diploid
    p_mRNA_IL2 = Place("mRNA_IL2", initial_tokens=0, place_type="rna")
    p_IL2_int = Place("IL2_intracellular", initial_tokens=0, place_type="protein")
    p_IL2_ext = Place("IL2_extracellular", initial_tokens=0, place_type="protein")
    
    # IL-2 receptor module
    p_gene_IL2R = Place("Gene_IL2R", initial_tokens=2, place_type="gene")
    p_mRNA_IL2R = Place("mRNA_IL2R", initial_tokens=0, place_type="rna")
    p_IL2R_free = Place("IL2R_free", initial_tokens=50, place_type="protein")
    p_IL2R_bound = Place("IL2R_bound", initial_tokens=0, place_type="complex")
    
    # STAT5 signaling
    p_STAT5_inactive = Place("STAT5_inactive", initial_tokens=100, place_type="protein")
    p_STAT5_active = Place("STAT5_active", initial_tokens=0, place_type="protein")
    
    # FOXP3 regulatory module
    p_gene_FOXP3 = Place("Gene_FOXP3", initial_tokens=2, place_type="gene")
    p_mRNA_FOXP3 = Place("mRNA_FOXP3", initial_tokens=0, place_type="rna")
    p_FOXP3 = Place("FOXP3", initial_tokens=0, place_type="protein")
    
    # Cell response
    p_activation = Place("Activation_marker", initial_tokens=0, place_type="protein")
    p_proliferation = Place("Proliferation", initial_tokens=0, place_type="event")
    
    # Add all places
    places = [
        p_gene_IL2, p_mRNA_IL2, p_IL2_int, p_IL2_ext,
        p_gene_IL2R, p_mRNA_IL2R, p_IL2R_free, p_IL2R_bound,
        p_STAT5_inactive, p_STAT5_active,
        p_gene_FOXP3, p_mRNA_FOXP3, p_FOXP3,
        p_activation, p_proliferation
    ]
    for place in places:
        model.add_place(place)
    
    # ========================================================================
    # PARAMETERS
    # ========================================================================
    params = load_parameters()
    
    # Adjust external IL-2 based on T cell density
    N_cells = t_cell_count * volume * 1e6  # Convert mL to L
    p_IL2_ext.tokens = int(params["IL2_external_base"] * min(N_cells / 1e6, 1.0))
    
    # ========================================================================
    # TRANSITIONS (Reactions)
    # ========================================================================
    
    # --- IL-2 Production Module ---
    t_txn_IL2 = Transition(
        "t_txn_IL2",
        rate_function=f"{params['k_txn_IL2']} * Gene_IL2",
        description="IL-2 transcription"
    )
    model.add_transition(t_txn_IL2)
    model.add_arc(Arc(p_gene_IL2, t_txn_IL2, arc_type="read"))
    model.add_arc(Arc(t_txn_IL2, p_mRNA_IL2))
    
    t_trl_IL2 = Transition(
        "t_trl_IL2",
        rate_function=f"{params['k_trl']} * mRNA_IL2",
        description="IL-2 translation"
    )
    model.add_transition(t_trl_IL2)
    model.add_arc(Arc(p_mRNA_IL2, t_trl_IL2, weight=1))
    model.add_arc(Arc(t_trl_IL2, p_IL2_int))
    
    t_secretion = Transition(
        "t_secretion",
        rate_function=f"{params['k_secretion']} * IL2_intracellular",
        description="IL-2 secretion"
    )
    model.add_transition(t_secretion)
    model.add_arc(Arc(p_IL2_int, t_secretion))
    model.add_arc(Arc(t_secretion, p_IL2_ext))
    
    # --- IL-2 Receptor Module ---
    t_txn_IL2R = Transition(
        "t_txn_IL2R",
        rate_function=f"{params['k_txn_IL2R']} * Gene_IL2R",
        description="IL-2R transcription"
    )
    model.add_transition(t_txn_IL2R)
    model.add_arc(Arc(p_gene_IL2R, t_txn_IL2R, arc_type="read"))
    model.add_arc(Arc(t_txn_IL2R, p_mRNA_IL2R))
    
    t_trl_IL2R = Transition(
        "t_trl_IL2R",
        rate_function=f"{params['k_trl']} * mRNA_IL2R",
        description="IL-2R translation"
    )
    model.add_transition(t_trl_IL2R)
    model.add_arc(Arc(p_mRNA_IL2R, t_trl_IL2R, weight=1))
    model.add_arc(Arc(t_trl_IL2R, p_IL2R_free))
    
    t_binding = Transition(
        "t_binding",
        rate_function=f"{params['k_binding']} * IL2R_free * IL2_extracellular",
        description="IL-2 receptor binding"
    )
    model.add_transition(t_binding)
    model.add_arc(Arc(p_IL2R_free, t_binding))
    model.add_arc(Arc(p_IL2_ext, t_binding, arc_type="read"))  # IL-2 not consumed
    model.add_arc(Arc(t_binding, p_IL2R_bound))
    
    # --- STAT5 Signaling Module ---
    t_STAT5_activation = Transition(
        "t_STAT5_activation",
        rate_function=f"{params['k_STAT5_act']} * IL2R_bound * STAT5_inactive",
        description="STAT5 phosphorylation by JAK"
    )
    model.add_transition(t_STAT5_activation)
    model.add_arc(Arc(p_IL2R_bound, t_STAT5_activation, arc_type="read"))
    model.add_arc(Arc(p_STAT5_inactive, t_STAT5_activation))
    model.add_arc(Arc(t_STAT5_activation, p_STAT5_active))
    
    t_STAT5_deactivation = Transition(
        "t_STAT5_deactivation",
        rate_function=f"{params['k_STAT5_deact']} * STAT5_active",
        description="STAT5 dephosphorylation"
    )
    model.add_transition(t_STAT5_deactivation)
    model.add_arc(Arc(p_STAT5_active, t_STAT5_deactivation))
    model.add_arc(Arc(t_STAT5_deactivation, p_STAT5_inactive))
    
    # --- FOXP3 Module (STAT5-activated) ---
    t_txn_FOXP3 = Transition(
        "t_txn_FOXP3",
        rate_function=(
            f"({params['k_txn_FOXP3_basal']} + "
            f"{params['k_txn_FOXP3_max']} * STAT5_active / "
            f"({params['K_STAT5']} + STAT5_active)) * Gene_FOXP3"
        ),
        description="FOXP3 transcription (STAT5-dependent)"
    )
    model.add_transition(t_txn_FOXP3)
    model.add_arc(Arc(p_gene_FOXP3, t_txn_FOXP3, arc_type="read"))
    model.add_arc(Arc(p_STAT5_active, t_txn_FOXP3, arc_type="read"))
    model.add_arc(Arc(t_txn_FOXP3, p_mRNA_FOXP3))
    
    t_trl_FOXP3 = Transition(
        "t_trl_FOXP3",
        rate_function=f"{params['k_trl']} * mRNA_FOXP3",
        description="FOXP3 translation"
    )
    model.add_transition(t_trl_FOXP3)
    model.add_arc(Arc(p_mRNA_FOXP3, t_trl_FOXP3, weight=1))
    model.add_arc(Arc(t_trl_FOXP3, p_FOXP3))
    
    # --- Cell Response Module (Paracrine Signaling) ---
    # CRITICAL: This transition demonstrates signal place detection
    # IL2_extracellular is referenced but NOT connected by consumption arc
    t_activation = Transition(
        "t_activation",
        rate_function=(
            f"{params['k_activation']} * IL2R_bound * STAT5_active / "
            f"(1 + IL2_extracellular / {params['K_feedback']})"
        ),
        description="T cell activation (paracrine-mediated)"
    )
    model.add_transition(t_activation)
    model.add_arc(Arc(p_IL2R_bound, t_activation, arc_type="read"))
    model.add_arc(Arc(p_STAT5_active, t_activation, arc_type="read"))
    # NOTE: p_IL2_ext is NOT connected by arc → it's a signal place
    model.add_arc(Arc(t_activation, p_activation))
    
    t_proliferation = Transition(
        "t_proliferation",
        rate_function=f"{params['k_proliferation']} * Activation_marker",
        description="T cell proliferation"
    )
    model.add_transition(t_proliferation)
    model.add_arc(Arc(p_activation, t_proliferation, arc_type="read"))
    model.add_arc(Arc(t_proliferation, p_proliferation))
    
    return model


def load_parameters():
    """Load model parameters from JSON file or use defaults."""
    param_file = Path(__file__).parent / "parameters.json"
    
    if param_file.exists():
        with open(param_file) as f:
            return json.load(f)
    
    # Default parameters (from literature)
    return {
        # Transcription rates (molecules/min)
        "k_txn_IL2": 0.1,
        "k_txn_IL2R": 0.3,
        "k_txn_FOXP3_basal": 0.01,
        "k_txn_FOXP3_max": 2.0,
        
        # Translation rate (proteins/mRNA/min)
        "k_trl": 0.5,
        
        # IL-2 dynamics
        "k_secretion": 0.5,        # IL-2 secretion rate (1/min)
        "IL2_external_base": 10,   # Base external IL-2 (molecules)
        
        # Receptor binding
        "k_binding": 0.001,        # IL-2-IL2R binding (1/molecules/min)
        
        # STAT5 signaling
        "k_STAT5_act": 0.01,       # STAT5 phosphorylation (1/molecules/min)
        "k_STAT5_deact": 0.1,      # STAT5 dephosphorylation (1/min)
        "K_STAT5": 20.0,           # STAT5 activation threshold (molecules)
        
        # Cell response
        "k_activation": 0.5,       # Cell activation rate (1/min)
        "K_feedback": 100.0,       # Negative feedback constant (molecules)
        "k_proliferation": 0.01    # Proliferation rate (1/min)
    }


def analyze_signal_places(model):
    """Detect and display signal place annotations."""
    detector = QuorumSensingDetector(model)
    signal_network = detector.get_signal_network()
    
    print("\n" + "="*70)
    print("SIGNAL PLACE DETECTION (13-Tuple Formalism)")
    print("="*70)
    
    for trans_name, info in signal_network.items():
        if info["signal_places"]:
            print(f"\n{trans_name}:")
            print(f"  Ψ = {{{', '.join(info['signal_places'])}}}")
            print(f"  Classification: {info['classification']}")
            print(f"  Biological context: Paracrine signaling")
            print(f"  Rate formula: {info['rate_formula'][:60]}...")
    
    return signal_network


def run_simulation(model, t_max=1440, n_trajectories=1):
    """Run stochastic simulation."""
    engine = GillespieEngine(model)
    
    print(f"\n{'='*70}")
    print(f"SIMULATION")
    print(f"{'='*70}")
    print(f"Time span: 0 - {t_max} min ({t_max/60:.1f} hours)")
    print(f"Trajectories: {n_trajectories}")
    
    results = []
    for i in range(n_trajectories):
        print(f"\nTrajectory {i+1}/{n_trajectories}...", end=" ", flush=True)
        trajectory = engine.simulate(t_max=t_max, output_interval=10.0)
        results.append(trajectory)
        print(f"✓ ({len(trajectory)} time points)")
    
    return results


def plot_results(trajectories, output_dir=None):
    """Plot simulation results."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("Mammalian IL-2 Paracrine Signaling", fontsize=14, fontweight="bold")
    
    for traj in trajectories:
        t = traj["time"] / 60  # Convert to hours
        
        # Panel A: IL-2 dynamics
        ax = axes[0, 0]
        ax.plot(t, traj["IL2_intracellular"], label="IL-2 (intracellular)", alpha=0.7)
        ax.plot(t, traj["IL2_extracellular"], label="IL-2 (extracellular)", 
                alpha=0.7, linestyle="--", linewidth=2)
        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("IL-2 (molecules)")
        ax.set_title("IL-2 Cytokine Dynamics")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Panel B: IL-2R binding
        ax = axes[0, 1]
        ax.plot(t, traj["IL2R_bound"], color="purple", alpha=0.7)
        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("IL2R-bound (molecules)")
        ax.set_title("IL-2 Receptor Binding")
        ax.grid(True, alpha=0.3)
        
        # Panel C: STAT5 activation
        ax = axes[1, 0]
        ax.plot(t, traj["STAT5_active"], color="red", alpha=0.7)
        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("STAT5-P (molecules)")
        ax.set_title("STAT5 Signal Transduction")
        ax.grid(True, alpha=0.3)
        
        # Panel D: T cell response
        ax = axes[1, 1]
        ax.plot(t, traj["Activation_marker"], label="Activation (CD69)", alpha=0.7)
        ax2 = ax.twinx()
        ax2.plot(t, traj["Proliferation"], color="green", label="Proliferation", 
                alpha=0.7, linestyle=":")
        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Activation marker", color="blue")
        ax2.set_ylabel("Proliferation events", color="green")
        ax.set_title("T Cell Response")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left")
        ax2.legend(loc="upper right")
    
    plt.tight_layout()
    
    if output_dir:
        output_path = Path(output_dir) / "il2_paracrine_trajectory.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"\n✓ Trajectory plot saved: {output_path}")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Mammalian IL-2 paracrine signaling simulation"
    )
    parser.add_argument(
        "--cells", type=float, default=1e5,
        help="Initial T cell count (cells/mL), default 1e5"
    )
    parser.add_argument(
        "--time", type=float, default=1440,
        help="Simulation time (min), default 1440 (24 hours)"
    )
    parser.add_argument(
        "--trajectories", type=int, default=1,
        help="Number of trajectories, default 1"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory for plots and data"
    )
    parser.add_argument(
        "--show-network", action="store_true",
        help="Display signal network graph"
    )
    args = parser.parse_args()
    
    print("="*70)
    print("MAMMALIAN PARACRINE SIGNALING (IL-2)")
    print("="*70)
    print(f"Initial T cell density: {args.cells:.2e} cells/mL")
    
    # Create model
    model = create_il2_model(t_cell_count=args.cells)
    
    # Analyze signal places
    signal_network = analyze_signal_places(model)
    
    # Visualize signal network (TODO: Phase 3)
    if args.show_network:
        print("\n[Signal network visualization planned for Phase 3]")
        print("For now, signal place information displayed above.")
    
    # Run simulation
    trajectories = run_simulation(model, t_max=args.time, n_trajectories=args.trajectories)
    
    # Plot results
    plot_results(trajectories, output_dir=args.output)
    
    # Compute paracrine signaling metrics
    print(f"\n{'='*70}")
    print("PARACRINE SIGNALING METRICS")
    print(f"{'='*70}")
    
    for i, traj in enumerate(trajectories):
        il2_ext = traj["IL2_extracellular"]
        activation = traj["Activation_marker"]
        proliferation = traj["Proliferation"]
        
        # Find IL-2 threshold crossing
        threshold = 20  # molecules
        idx_threshold = np.where(il2_ext > threshold)[0]
        t_threshold = traj["time"][idx_threshold[0]] / 60 if len(idx_threshold) > 0 else None
        
        # Find activation onset
        onset = activation.max() * 0.1
        idx_onset = np.where(activation > onset)[0]
        t_onset = traj["time"][idx_onset[0]] / 60 if len(idx_onset) > 0 else None
        
        print(f"\nTrajectory {i+1}:")
        if t_threshold:
            print(f"  IL-2 threshold time: {t_threshold:.1f} hours")
        if t_onset:
            print(f"  T cell activation onset: {t_onset:.1f} hours")
        print(f"  Proliferation events: {int(proliferation[-1])}")
        print(f"  Max activation: {int(activation.max())} markers")
    
    print("\n✓ Simulation complete\n")


if __name__ == "__main__":
    main()
