#!/usr/bin/env python
"""
Vibrio fischeri Quorum Sensing Model
=====================================

Bacterial quorum sensing using the LuxI/LuxR autoinducer system.
Demonstrates 13-tuple Bio-PN formalism with signal places (Ψ).

Reference:
    Waters & Bassler (2005) Annu. Rev. Cell Dev. Biol. 21:319-346
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


def create_vfischeri_model(cell_density=1e8, volume=1e-15):
    """
    Create V. fischeri quorum sensing Bio-PN model.
    
    Parameters
    ----------
    cell_density : float
        Initial cell density (cells/mL)
    volume : float
        Cell volume (L), default 1 fL typical for V. fischeri
        
    Returns
    -------
    BioPetriNet
        13-tuple Bio-PN with signal places
    """
    model = BioPetriNet(name="V_fischeri_QS")
    
    # ========================================================================
    # PLACES (Molecular Species)
    # ========================================================================
    
    # LuxI module (AHL synthesis)
    p_gene_luxI = Place("Gene_luxI", initial_tokens=1, place_type="gene")
    p_mRNA_luxI = Place("mRNA_luxI", initial_tokens=0, place_type="rna")
    p_LuxI = Place("LuxI", initial_tokens=0, place_type="protein")
    
    # LuxR module (AHL reception)
    p_gene_luxR = Place("Gene_luxR", initial_tokens=1, place_type="gene")
    p_mRNA_luxR = Place("mRNA_luxR", initial_tokens=0, place_type="rna")
    p_LuxR = Place("LuxR", initial_tokens=10, place_type="protein")
    
    # AHL (autoinducer)
    p_AHL_int = Place("AHL_internal", initial_tokens=0, place_type="metabolite")
    p_AHL_ext = Place("AHL_external", initial_tokens=0, place_type="metabolite")
    
    # LuxR-AHL complex
    p_LuxR_AHL = Place("LuxR_AHL", initial_tokens=0, place_type="complex")
    
    # LuxAB module (bioluminescence)
    p_gene_luxAB = Place("Gene_luxAB", initial_tokens=1, place_type="gene")
    p_mRNA_luxAB = Place("mRNA_luxAB", initial_tokens=0, place_type="rna")
    p_LuxAB = Place("LuxAB", initial_tokens=0, place_type="protein")
    p_Light = Place("Light", initial_tokens=0, place_type="metabolite")
    
    # Add all places
    places = [
        p_gene_luxI, p_mRNA_luxI, p_LuxI,
        p_gene_luxR, p_mRNA_luxR, p_LuxR,
        p_AHL_int, p_AHL_ext, p_LuxR_AHL,
        p_gene_luxAB, p_mRNA_luxAB, p_LuxAB, p_Light
    ]
    for place in places:
        model.add_place(place)
    
    # ========================================================================
    # PARAMETERS
    # ========================================================================
    params = load_parameters()
    
    # Adjust external AHL based on cell density
    # Assumption: Linear scaling with density up to saturation
    N_cells = cell_density * volume * 1e6  # Convert mL to L
    p_AHL_ext.tokens = int(params["AHL_external_base"] * min(N_cells / 1e9, 1.0))
    
    # ========================================================================
    # TRANSITIONS (Reactions)
    # ========================================================================
    
    # --- LuxI Module ---
    t_txn_luxI = Transition(
        "t_txn_luxI",
        rate_function=f"{params['k_txn_luxI']} * Gene_luxI",
        description="Transcription of luxI"
    )
    model.add_transition(t_txn_luxI)
    model.add_arc(Arc(p_gene_luxI, t_txn_luxI, arc_type="read"))
    model.add_arc(Arc(t_txn_luxI, p_mRNA_luxI))
    
    t_trl_luxI = Transition(
        "t_trl_luxI",
        rate_function=f"{params['k_trl']} * mRNA_luxI",
        description="Translation of LuxI"
    )
    model.add_transition(t_trl_luxI)
    model.add_arc(Arc(p_mRNA_luxI, t_trl_luxI, weight=1))
    model.add_arc(Arc(t_trl_luxI, p_LuxI))
    
    t_synth_AHL = Transition(
        "t_synth_AHL",
        rate_function=f"{params['k_synth_AHL']} * LuxI",
        description="AHL synthesis"
    )
    model.add_transition(t_synth_AHL)
    model.add_arc(Arc(p_LuxI, t_synth_AHL, arc_type="read"))
    model.add_arc(Arc(t_synth_AHL, p_AHL_int))
    
    t_export_AHL = Transition(
        "t_export_AHL",
        rate_function=f"{params['k_export']} * AHL_internal",
        description="AHL diffusion out"
    )
    model.add_transition(t_export_AHL)
    model.add_arc(Arc(p_AHL_int, t_export_AHL))
    model.add_arc(Arc(t_export_AHL, p_AHL_ext))
    
    # --- LuxR Module ---
    t_txn_luxR = Transition(
        "t_txn_luxR",
        rate_function=f"{params['k_txn_luxR']} * Gene_luxR",
        description="Transcription of luxR"
    )
    model.add_transition(t_txn_luxR)
    model.add_arc(Arc(p_gene_luxR, t_txn_luxR, arc_type="read"))
    model.add_arc(Arc(t_txn_luxR, p_mRNA_luxR))
    
    t_trl_luxR = Transition(
        "t_trl_luxR",
        rate_function=f"{params['k_trl']} * mRNA_luxR",
        description="Translation of LuxR"
    )
    model.add_transition(t_trl_luxR)
    model.add_arc(Arc(p_mRNA_luxR, t_trl_luxR, weight=1))
    model.add_arc(Arc(t_trl_luxR, p_LuxR))
    
    t_binding = Transition(
        "t_binding",
        rate_function=f"{params['k_binding']} * LuxR * AHL_internal",
        description="LuxR-AHL binding"
    )
    model.add_transition(t_binding)
    model.add_arc(Arc(p_LuxR, t_binding))
    model.add_arc(Arc(p_AHL_int, t_binding))
    model.add_arc(Arc(t_binding, p_LuxR_AHL))
    
    # --- LuxAB Module (Quorum Sensing Activated) ---
    # CRITICAL: This transition demonstrates signal place detection
    # AHL_external is referenced but NOT connected by arcs → signal place
    t_txn_luxAB = Transition(
        "t_txn_luxAB",
        rate_function=(
            f"({params['k_txn_luxAB_basal']} + "
            f"{params['k_txn_luxAB_max']} * LuxR_AHL / "
            f"({params['K_luxR']} + LuxR_AHL)) / "
            f"(1 + AHL_external / {params['K_inhibit']})"
        ),
        description="Transcription of luxAB (QS-activated)"
    )
    model.add_transition(t_txn_luxAB)
    model.add_arc(Arc(p_gene_luxAB, t_txn_luxAB, arc_type="read"))
    model.add_arc(Arc(p_LuxR_AHL, t_txn_luxAB, arc_type="read"))
    # NOTE: p_AHL_ext is NOT connected by arc → it's a signal place
    model.add_arc(Arc(t_txn_luxAB, p_mRNA_luxAB))
    
    t_trl_luxAB = Transition(
        "t_trl_luxAB",
        rate_function=f"{params['k_trl']} * mRNA_luxAB",
        description="Translation of luciferase"
    )
    model.add_transition(t_trl_luxAB)
    model.add_arc(Arc(p_mRNA_luxAB, t_trl_luxAB, weight=1))
    model.add_arc(Arc(t_trl_luxAB, p_LuxAB))
    
    t_light = Transition(
        "t_light",
        rate_function=f"{params['k_light']} * LuxAB",
        description="Bioluminescence"
    )
    model.add_transition(t_light)
    model.add_arc(Arc(p_LuxAB, t_light, arc_type="read"))
    model.add_arc(Arc(t_light, p_Light))
    
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
        "k_txn_luxI": 0.5,
        "k_txn_luxR": 0.3,
        "k_txn_luxAB_basal": 0.01,
        "k_txn_luxAB_max": 10.0,
        
        # Translation rate (proteins/mRNA/min)
        "k_trl": 1.0,
        
        # AHL dynamics
        "k_synth_AHL": 0.2,        # AHL synthesis rate (molecules/LuxI/min)
        "k_export": 0.1,           # Diffusion rate (1/min)
        "AHL_external_base": 100,  # Base external AHL (molecules)
        
        # Binding
        "k_binding": 0.01,         # LuxR-AHL binding (1/molecules/min)
        "K_luxR": 50.0,            # LuxR-AHL activation threshold (molecules)
        "K_inhibit": 1000.0,       # External AHL inhibition constant (molecules)
        
        # Bioluminescence
        "k_light": 100.0           # Light emission rate (photons/LuxAB/min)
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
            print(f"  Rate formula: {info['rate_formula'][:60]}...")
    
    return signal_network


def run_simulation(model, t_max=600, n_trajectories=1):
    """Run stochastic simulation."""
    engine = GillespieEngine(model)
    
    print(f"\n{'='*70}")
    print(f"SIMULATION")
    print(f"{'='*70}")
    print(f"Time span: 0 - {t_max} min")
    print(f"Trajectories: {n_trajectories}")
    
    results = []
    for i in range(n_trajectories):
        print(f"\nTrajectory {i+1}/{n_trajectories}...", end=" ", flush=True)
        trajectory = engine.simulate(t_max=t_max, output_interval=1.0)
        results.append(trajectory)
        print(f"✓ ({len(trajectory)} time points)")
    
    return results


def plot_results(trajectories, output_dir=None):
    """Plot simulation results."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("V. fischeri Quorum Sensing Dynamics", fontsize=14, fontweight="bold")
    
    for traj in trajectories:
        t = traj["time"]
        
        # Panel A: AHL dynamics
        ax = axes[0, 0]
        ax.plot(t, traj["AHL_internal"], label="AHL internal", alpha=0.7)
        ax.plot(t, traj["AHL_external"], label="AHL external", alpha=0.7, linestyle="--")
        ax.set_xlabel("Time (min)")
        ax.set_ylabel("AHL (molecules)")
        ax.set_title("Autoinducer Dynamics")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Panel B: LuxR-AHL complex
        ax = axes[0, 1]
        ax.plot(t, traj["LuxR_AHL"], color="purple", alpha=0.7)
        ax.set_xlabel("Time (min)")
        ax.set_ylabel("LuxR-AHL (molecules)")
        ax.set_title("Active Receptor Complex")
        ax.grid(True, alpha=0.3)
        
        # Panel C: Bioluminescence
        ax = axes[1, 0]
        ax.plot(t, traj["Light"], color="gold", alpha=0.7)
        ax.set_xlabel("Time (min)")
        ax.set_ylabel("Light (photons)")
        ax.set_title("Bioluminescence Output")
        ax.grid(True, alpha=0.3)
        
        # Panel D: Phase portrait
        ax = axes[1, 1]
        ax.plot(traj["AHL_external"], traj["Light"], alpha=0.6)
        ax.set_xlabel("AHL external (molecules)")
        ax.set_ylabel("Light (photons)")
        ax.set_title("Phase Portrait")
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_dir:
        output_path = Path(output_dir) / "vfischeri_quorum_sensing_trajectory.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"\n✓ Trajectory plot saved: {output_path}")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="V. fischeri quorum sensing simulation"
    )
    parser.add_argument(
        "--cells", type=float, default=1e8,
        help="Initial cell density (cells/mL), default 1e8"
    )
    parser.add_argument(
        "--time", type=float, default=600,
        help="Simulation time (min), default 600"
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
    print("V. FISCHERI QUORUM SENSING MODEL")
    print("="*70)
    print(f"Initial cell density: {args.cells:.2e} cells/mL")
    
    # Create model
    model = create_vfischeri_model(cell_density=args.cells)
    
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
    
    # Compute quorum sensing metrics
    print(f"\n{'='*70}")
    print("QUORUM SENSING METRICS")
    print(f"{'='*70}")
    
    for i, traj in enumerate(trajectories):
        ahl_ext = traj["AHL_external"]
        light = traj["Light"]
        
        # Find threshold crossing time
        threshold = 500  # molecules
        idx_threshold = np.where(ahl_ext > threshold)[0]
        t_threshold = traj["time"][idx_threshold[0]] if len(idx_threshold) > 0 else None
        
        # Find bioluminescence onset
        onset = light.max() * 0.1
        idx_onset = np.where(light > onset)[0]
        t_onset = traj["time"][idx_onset[0]] if len(idx_onset) > 0 else None
        
        print(f"\nTrajectory {i+1}:")
        if t_threshold:
            print(f"  AHL threshold time: {t_threshold:.1f} min")
        if t_onset:
            print(f"  Bioluminescence onset: {t_onset:.1f} min")
        print(f"  Max light output: {light.max():.2e} photons")
    
    print("\n✓ Simulation complete\n")


if __name__ == "__main__":
    main()
